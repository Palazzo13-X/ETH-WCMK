"""B11 - structural ablation battery v12 (gate G6').

The r3 run of this battery ablated only the face-lattice terms S2, S3, S4, the
epistemic penalty and the facet-exposure term. It never tested the four mechanisms
that the v12 core actually claims to be load-bearing:

  1. THE VETO (E11b/E11d/E11e): the facet-level cap and the veto-aware ladder. Without
     it the model degenerates into a compensatory weighted average.
  2. THE SHARED-BETA RULE (E2, registry R2/R3): a facet that genuinely contributes to
     more than one pillar. Ablating it means assigning each facet to its primary pillar
     only.
  3. THE RISK FLOOR sigma (E12'): attenuation without erasure. Without it the residual
     risk can be driven to zero by a sufficiently high adequacy.
  4. THE CORRECTED S4 TERM (E5c): the cell term as the Goedel min. The v11 geometric
     mean is not monotone in arity, so the hierarchy S4 <= S3 <= S2 fails.

For every ablation we measure, over a grid of >= 5,000 confrontations built from the
frozen Evaluacoes/r3/corpus_v4_layerA.jsonl cases and the 48 personas:
  (i)  the change in the adequacy distribution (mean, sd, quantiles, mean |dAa|, KS);
  (ii) the change in the decision distribution and the decision flip matrix;
  (iii) the agreement with the gold panel consensus (Cohen's kappa, exact match) for
        the declared profile of every case (layer A + layer B, 1,520 cases).

Run:  python3 _analysis/analysis/ablation_structural.py
Out:  Evaluacoes/r4/B11_ablation.json
"""
import json
import os
import sys
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R3 = os.path.join(ROOT, "Evaluacoes", "r3")
OUT = os.path.join(ROOT, "Evaluacoes", "r4")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, Calibration, confront, _adequacy, decide,
                  load_fitted_calibration, requirement_for, band_value, effective_value,
                  structural_terms, case_stakes, clamp, PILLARS, EPS,
                  DECISION_PERMISSIVENESS, CONFLICT_PATTERNS, SEVERITY_BANDS,
                  PRUDENTIAL_MODES, REVERSIBILITY, HORIZON_VALUE, DOMAIN_SET,
                  failure_probability, prudential_floor)
from facet_registry import FACETS, DOMAINS, FacetDef

SEED = 20261104
ORDER = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]

BASE = load_fitted_calibration()


def avg_rank(x):
    order = np.argsort(x)
    ranks = np.empty(len(x), dtype=float)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return ranks


def spearman(a, b):
    ra, rb = avg_rank(np.asarray(a)), avg_rank(np.asarray(b))
    ra, rb = ra - ra.mean(), rb - rb.mean()
    den = np.sqrt((ra * ra).sum() * (rb * rb).sum())
    return float((ra * rb).sum() / den) if den > 0 else 1.0


def cohens_kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    idx = {l: i for i, l in enumerate(labels)}
    obs = np.zeros((len(labels), len(labels)))
    ca, cb = Counter(a), Counter(b)
    for x, y in zip(a, b):
        obs[idx[x], idx[y]] += 1
    po = obs.trace() / n
    pe = sum((ca[l] / n) * (cb[l] / n) for l in labels)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def ks_stat(a, b):
    """Two-sample Kolmogorov-Smirnov statistic (numpy only, no scipy)."""
    xs = np.sort(np.asarray(a))
    ys = np.sort(np.asarray(b))
    grid = np.sort(np.concatenate([xs, ys]))
    cx = np.searchsorted(xs, grid, side="right") / len(xs)
    cy = np.searchsorted(ys, grid, side="right") / len(ys)
    return float(np.max(np.abs(cx - cy)))


def one_hot_facets():
    """Shared-beta rule removed: every facet feeds only its primary pillar."""
    out = []
    for f in FACETS:
        p = f.primary_pillar()
        beta = tuple(1.0 if PILLARS[i] == p else 0.0 for i in range(4))
        out.append(FacetDef(f.code, f.label, beta, f.policy, f.guard, f.guard_min,
                            f.weight, f.source, f.observable, f.criticality))
    return out


ONE_HOT = one_hot_facets()


def variant_confront(case, prof, variant):
    """confront() under an ablated model. Mirrors core.confront exactly, changing only
    the mechanism under test. Returns (central adequacy, decision, low-pass dict)."""
    cal = variant_cal(BASE, variant)
    if variant == "full":
        r = confront(case, prof, cal, FACETS)
        return r["adequacy"], r["decision"], r
    if variant == "no_shared_beta":
        r = confront(case, prof, cal, ONE_HOT)
        return r["adequacy"], r["decision"], r

    mid = _adequacy(case, prof, cal, FACETS, "central")
    low = _adequacy(case, prof, cal, FACETS, "pessimistic")
    ratio = low["ratio"]
    comp = len(prof.facet_scores) / len(FACETS)
    if comp < 0.70:
        return None, "ABSTAIN", low

    if variant == "no_veto":
        # E11b/E11d/E11e removed: no cap on the score, no veto, no hard veto.
        aa_c, aa_l = mid["aa_raw"], low["aa_raw"]
        veto, hard, gap = [], [], 0.0
    elif variant == "no_risk_floor":
        # E12' sigma removed: attenuation without erasure disappears.
        aa_c, aa_l = mid["aa"], low["aa"]
        ratio = low["p_fail"]
        veto, hard, gap = low["veto"], low["hard_veto"], low["material_gap"]
    elif variant == "s4_geometric":
        # the v11 cell term: geometric mean of the four pillar deficits, with the
        # same veto cap the v12 core applies
        stakes = case_stakes(case)
        cap_weight = cal.cap_base + cal.cap_stakes_gain * stakes

        def aa_with(mode_dict):
            d = mode_dict["deficits"]
            geo = float(np.prod(d)) ** 0.25 if all(x > 0 for x in d) else 0.0
            raw = clamp(1.0 - mode_dict["D"] - cal.gamma * mode_dict["S2"]
                        - cal.eta * mode_dict["S3"] - cal.omega * geo
                        - cal.rho * mode_dict["u"] - cal.delta * mode_dict["phi"])
            if mode_dict["veto"] or mode_dict["cap_gap"] >= cal.material_gap:
                return max(0.0, min(raw, 1.0 - cap_weight * mode_dict["cap_gap"]))
            return max(0.0, raw)

        aa_c, aa_l = aa_with(mid), aa_with(low)
        veto, hard, gap = low["veto"], low["hard_veto"], low["material_gap"]
        ratio = low["ratio"]
    else:
        aa_c, aa_l = mid["aa"], low["aa"]
        ratio = low["ratio"]
        veto, hard, gap = low["veto"], low["hard_veto"], low["material_gap"]

    if variant == "no_risk_floor":
        ratio = low["p_fail"]

    epistemic_abstain = ((case.norm_conflict != "none" or case.evidence_conflict)
                         and case.U_E >= cal.abstain_uncertainty
                         and mid["levels"][2] <= cal.abstain_knowledge_floor)
    decision = "ABSTAIN" if epistemic_abstain else decide(aa_l, ratio, cal, case,
                                                          veto, hard, gap)
    return aa_c, decision, low


VARIANTS = {
    "full": "the v12 model as specified",
    "no_veto": "ablate the veto: Aa = Aa_raw, no cap, no veto, no hard veto",
    "no_shared_beta": "ablate the shared-beta rule: each facet feeds only its primary pillar",
    "no_risk_floor": "ablate the risk floor: ratio = p_fail, R_r = R_c * p_fail (sigma = 0)",
    "s4_geometric": "revert S4 to the v11 geometric mean of the four deficits",
    "no_S2": "zero the edge term gamma (structural ablation, for completeness)",
    "no_S3": "zero the face term eta (structural ablation, for completeness)",
    "no_S4": "zero the cell term omega (structural ablation, for completeness)",
    "no_exposure": "zero the facet-exposure term delta (structural ablation)",
    "no_epistemic": "zero the uncertainty penalty rho (structural ablation)",
}


def variant_cal(base, variant):
    if variant in ("no_S2", "no_S3", "no_S4", "no_exposure", "no_epistemic"):
        field = {"no_S2": "gamma", "no_S3": "eta", "no_S4": "omega",
                 "no_exposure": "delta", "no_epistemic": "rho"}[variant]
        return replace(base, **{field: 0.0})
    return base


def persona_profile(persona, req):
    scores, conf = {}, {}
    for f in FACETS:
        fac = persona["factors"][f.primary_pillar()]
        if persona["persona_type"] == "guard_fragile" and f.guard:
            fac = 0.25 / max(req[f.code], 1e-6)
        if persona["persona_type"] == "recoverable_failure" and f.code in ("C7", "M7"):
            fac = 1.15
        scores[f.code] = max(0.0, min(1.0, req[f.code] * fac * (1 + persona["jitter"])))
        conf[f.code] = persona["confidence_mu"]
    return Profile(persona["profile_id"], scores, conf, persona["layer"])


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def spec_of(row):
    return CaseSpec(row["case_id"], row["domain"], row["severity"], row["prudential"],
                    row["irreversibility"], row["facet_requirements"], row["U_E"], row["R_c"],
                    tuple(row.get("critical_pillars", ("M", "K"))),
                    row.get("horizon", "immediate"), row.get("conflict_pattern", "none"),
                    row.get("agent_layer", "system"), tuple(row.get("norms", ())))


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = [spec_of(r) for r in read_jsonl(os.path.join(R3, "corpus_v4_layerA.jsonl"))]
    declared = {c.case_id: Profile(c.case_id, r["declared_levels"],
                                   r.get("declared_confidence", {}), "system")
                for c, r in zip(cases, read_jsonl(os.path.join(R3, "corpus_v4_layerA.jsonl")))}
    cases_b = [spec_of(r) for r in read_jsonl(os.path.join(R3, "corpus_v4_layerB.jsonl"))]
    declared_b = {c.case_id: Profile(c.case_id, r["declared_levels"],
                                     r.get("declared_confidence", {}), "system")
                  for c, r in zip(cases_b, read_jsonl(os.path.join(R3, "corpus_v4_layerB.jsonl")))}
    personas = list(read_jsonl(os.path.join(R3, "corpus_v4_personas.jsonl")))
    gold = {g["case_id"]: g["consensus"] for g in read_jsonl(os.path.join(R3, "corpus_v4_gold.jsonl"))}

    grid = [(case, persona_profile(p, case.facet_requirements))
            for case in cases for p in personas]
    n_grid = len(grid)

    # ---- one pass per variant over the whole grid
    results = {}
    for variant in VARIANTS:
        aa_l, dec_l = [], []
        for case, prof in grid:
            a, d, _ = variant_confront(case, prof, variant)
            aa_l.append(a if a is not None else 0.0)
            dec_l.append(d)
        results[variant] = (np.array(aa_l, dtype=float), dec_l)
    full_aa, full_dec = results["full"]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "_analysis/analysis/ablation_structural.py",
        "core": "formal_core/core.py (v12)",
        "calibration": "load_fitted_calibration()",
        "n_confrontations": n_grid,
        "n_cases": len(cases),
        "n_personas": len(personas),
        "n_gold_pairs": len(gold),
        "seed": SEED,
        "ablations": VARIANTS,
        "reference": {
            "mean_adequacy": float(np.mean(full_aa)),
            "sd_adequacy": float(np.std(full_aa)),
            "p10": float(np.percentile(full_aa, 10)),
            "p50": float(np.percentile(full_aa, 50)),
            "p90": float(np.percentile(full_aa, 90)),
            "decision_counts": dict(Counter(full_dec)),
        },
        "variants": {},
    }

    for variant in VARIANTS:
        aa, dec = results[variant]
        delta = aa - full_aa
        flips = Counter((f, d) for f, d in zip(full_dec, dec) if f != d)
        report["variants"][variant] = {
            "adequacy": {"mean": float(np.mean(aa)), "sd": float(np.std(aa)),
                         "p10": float(np.percentile(aa, 10)),
                         "p50": float(np.percentile(aa, 50)),
                         "p90": float(np.percentile(aa, 90)),
                         "mean_delta": round(float(np.mean(delta)), 6),
                         "mean_abs_delta": round(float(np.mean(np.abs(delta))), 6),
                         "max_abs_delta": round(float(np.max(np.abs(delta))), 6),
                         "share_abs_delta_ge_0.01": round(float(np.mean(np.abs(delta) >= 0.01)), 4),
                         "share_abs_delta_ge_0.05": round(float(np.mean(np.abs(delta) >= 0.05)), 4),
                         "ks_statistic_vs_full": round(ks_stat(aa, full_aa), 4)},
            "decisions": {"counts": dict(Counter(dec)),
                          "flip_rate": round(float(np.mean([a != b for a, b in zip(full_dec, dec)])), 4),
                          "top_flips": {f"{a}->{b}": c for (a, b), c in flips.most_common(8)},
                          "kappa_vs_full_model": round(cohens_kappa(full_dec, dec), 4),
                          "mean_permissiveness": round(float(np.mean([DECISION_PERMISSIVENESS[d] for d in dec])), 4),
                          "mean_permissiveness_delta_vs_full": round(
                              float(np.mean([DECISION_PERMISSIVENESS[d] for d in dec]) -
                                    np.mean([DECISION_PERMISSIVENESS[d] for d in full_dec])), 4),
                          "spearman_adequacy_ranking_vs_full": round(spearman(full_aa, aa), 6)},
        }

    # ---- agreement with the gold consensus, on the declared profile of every case
    gold_cases = list(cases) + list(cases_b)
    gold_profiles = {c.case_id: declared.get(c.case_id) or declared_b.get(c.case_id) for c in gold_cases}
    agreement = {}
    for variant in VARIANTS:
        decs = []
        for c in gold_cases:
            prof = gold_profiles[c.case_id]
            decs.append(variant_confront(c, prof, variant)[1])
        g = [gold[c.case_id] for c in gold_cases]
        agreement[variant] = {"n": len(g), "kappa_vs_gold": round(cohens_kappa(decs, g), 4),
                              "exact_match": round(float(np.mean([a == b for a, b in zip(decs, g)])), 4),
                              "decision_counts": dict(Counter(decs))}
    report["gold_agreement"] = agreement
    report["headline_deltas"] = {
        v: {"delta_mean_adequacy": report["variants"][v]["adequacy"]["mean_delta"],
           "flip_rate": report["variants"][v]["decisions"]["flip_rate"],
           "delta_kappa_vs_gold": round(agreement[v]["kappa_vs_gold"] - agreement["full"]["kappa_vs_gold"], 4)}
        for v in VARIANTS if v != "full"
    }

    path = os.path.join(OUT, "B11_ablation.json")
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report["headline_deltas"], indent=1))
    print(json.dumps(report["gold_agreement"], indent=1))
    for v, r in report["variants"].items():
        print(f"{v:<16} meanAa={r['adequacy']['mean']:.4f} mean|dAa|={r['adequacy']['mean_abs_delta']:.4f} "
              f"flips={r['decisions']['flip_rate']*100:.2f}% kappa_full={r['decisions']['kappa_vs_full_model']:.4f} "
              "kappa_gold=" + str(agreement[v]["kappa_vs_gold"]))
    print("written:", path)


if __name__ == "__main__":
    main()
