"""Independent check of the two ablation findings that matter most for the design:

 (1) does the shared-beta rule (a duty feeding several pillars) dilute the model's
     discrimination, or does it add power?
 (2) is the model's advantage over the trivial "worst duty gap" rule real?

Variants compared against the gold consensus on the whole r4 corpus v5:
  A  full v12 model (guard caps + shared beta)
  B  one-hot beta: each facet feeds only its primary pillar
  C  "concentrated-deficit floor": beta shared as usual, but any facet whose gap
     (requirement - observed) exceeds the material gap floors its pillar, i.e. the
     non-compensatory rule is extended from the 9 hard guards to every duty that is
     materially breached.
  D  baseline rule "worst duty gap only" (no tetrahedral structure at all):
     PROHIBIT if max_f (r_f - x_f) >= 0.35, REVIEW if >= 0.20, ALLOW_WITH_GUARDS if
     >= 0.10, else ALLOW - thresholds chosen to reproduce its observed marginals.

Writes Evaluacoes/r4/ablation_beta_check.json.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))

from facet_registry import FACETS, DOMAINS                                   # noqa: E402
from core import (CaseSpec, Profile, confront, load_fitted_calibration,      # noqa: E402
                  band_value, effective_value, EPS, PILLARS)                 # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
CLASSES = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")
IDX = {c: i for i, c in enumerate(CLASSES)}
PRIMARY = {f.code: f.code[0] for f in FACETS}


def kappa(pairs):
    m = [[0] * 5 for _ in range(5)]
    for a, b in pairs:
        if a in IDX and b in IDX:
            m[IDX[a]][IDX[b]] += 1
    n = sum(sum(r) for r in m)
    if not n:
        return float("nan")
    po = sum(m[i][i] for i in range(5)) / n
    row = [sum(m[i]) / n for i in range(5)]
    col = [sum(m[i][j] for i in range(5)) / n for j in range(5)]
    pe = sum(r * c for r, c in zip(row, col))
    return (po - pe) / (1 - pe) if 1 - pe > 1e-12 else 0.0


def band3(pred):
    """Collapse to 3 normative bands: permissive / conditional / prohibitive."""
    return {"ALLOW": "PERMISSIVE", "ALLOW_WITH_GUARDS": "CONDITIONAL",
            "REVIEW_REQUIRED": "CONDITIONAL", "PROHIBIT": "PROHIBITIVE",
            "ABSTAIN": "CONDITIONAL"}.get(pred, "CONDITIONAL")


def project_variant(values, facets, cal, variant, confidence, domain):
    """Reimplement E2/E24 for the variants, so we do not touch core.py."""
    num = [0.0] * 4
    den = [0.0] * 4
    conf = confidence or {}
    for f in facets:
        v = values.get(f.code)
        if v is None:
            continue
        v = effective_value(f, v, conf.get(f.code, 1.0), "central")
        if variant == "one_hot_beta":
            i = PILLARS.index(PRIMARY[f.code])
            num[i] += f.weight * v
            den[i] += f.weight
        else:
            for i, b in enumerate(f.beta):
                if b > 0:
                    num[i] += b * f.weight * v
                    den[i] += b * f.weight
    level = [num[i] / den[i] if den[i] > EPS else 0.0 for i in range(4)]
    for f in facets:
        v = values.get(f.code)
        if v is None:
            continue
        capped = band_value(v, conf.get(f.code, 1.0), "central")
        if variant == "full":
            if f.guard and v < f.guard_min:
                for i, b in enumerate(f.beta):
                    if b > 0:
                        level[i] = min(level[i], capped)
        elif variant == "critical_floor":
            req = 1.0  # filled by caller through values? we use the requirement dict
        elif variant == "one_hot_beta":
            if f.guard and v < f.guard_min:
                i = PILLARS.index(PRIMARY[f.code])
                level[i] = min(level[i], capped)
    return level


def main():
    cal = load_fitted_calibration()
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        with open(os.path.join(R4, fn)) as fh:
            for line in fh:
                c = json.loads(line)
                cases[c["case_id"]] = c
    personas = []
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_personas.jsonl")) as fh:
        for line in fh:
            personas.append(json.loads(line))

    gold = {}
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_gold.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            gold[(r["case_id"], r["persona"])] = r["consensus"]

    results = {v: {"pairs": 0, "conf": Counter(), "aa": 0.0} for v in
               ("full", "one_hot_beta", "critical_floor", "worst_gap_rule")}
    pairs = {v: [] for v in results}
    aa_stats = {v: [] for v in results}
    decision_stats = {v: Counter() for v in results}
    rank3 = {v: [] for v in results}

    def level_for(values, beta_mode, guard_rule):
        num = [0.0] * 4
        den = [0.0] * 4
        for f in FACETS:
            v = values[f.code]
            for i, b in enumerate(f.beta):
                if b <= 0:
                    continue
                num[i] += b * f.weight * v
                den[i] += b * f.weight
        level = [num[i] / den[i] if den[i] > EPS else 0.0 for i in range(4)]
        if guard_rule == "hard_guards":
            for f in FACETS:
                if f.guard and values[f.code] < f.guard_min:
                    for i, b in enumerate(f.beta):
                        if b > 0:
                            level[i] = min(level[i], values[f.code])
        elif guard_rule == "critical_floor":
            for f in FACETS:
                if f.beta and values[f.code] < 0.35:      # concentrated deficit floor
                    for i, b in enumerate(f.beta):
                        if b > 0:
                            level[i] = min(level[i], values[f.code])
        return tuple(level)

    n = 0
    for cid, c in cases.items():
        spec = CaseSpec(cid, c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                        c["facet_requirements"], c["U_E"], c["R_c"], tuple(c["critical_pillars"]),
                        c["horizon"], c["conflict_pattern"], "system", tuple(c.get("norms", ())),
                        norm_conflict=c.get("norm_conflict", "none"),
                        evidence_conflict=c.get("evidence_conflict", False),
                        exposure=c.get("exposure", 0.5))
        for p in personas:
            levels = {f.code: min(1.0, c["facet_requirements"][f.code] *
                                  (p["factors"].get(f.code, p["default_factor"])) *
                                  (1 + p["jitter"])) for f in FACETS}
            conf = {f.code: p["confidence_mu"] for f in FACETS}
            key = (cid, p["profile_id"])
            g = gold.get(key)
            if g is None:
                continue
            n += 1
            prof = Profile(p["profile_id"], levels, conf, p["layer"])
            r = confront(spec, prof, cal)
            if r and r.get("adequacy") is not None:
                pairs["full"].append((r["decision"], g))
                decision_stats["full"][r["decision"]] += 1
                aa_stats["full"].append(r["adequacy"])
                rank3["full"].append((band3(r["decision"]), band3(g)))

            # one-hot beta: rebuild the facet list with one-hot beta
            from facet_registry import FacetDef
            facets1 = [FacetDef(f.code, f.label,
                                tuple(1.0 if PILLARS[i] == PRIMARY[f.code] else 0.0 for i in range(4)),
                                f.policy, f.guard, f.guard_min, f.weight,
                                source=f.source, observable=f.observable,
                                criticality=f.criticality) for f in FACETS]
            r2 = confront(spec, prof, cal, facets=facets1)
            if r2 and r2.get("adequacy") is not None:
                pairs["one_hot_beta"].append((r2["decision"], g))
                decision_stats["one_hot_beta"][r2["decision"]] += 1
                aa_stats["one_hot_beta"].append(r2["adequacy"])
                rank3["one_hot_beta"].append((band3(r2["decision"]), band3(g)))

            # critical/concentrated floor: same beta, floor extended to every facet
            # whose delivered level is below 0.35 of its requirement
            levels2 = dict(levels)
            facetsC = []
            for f in FACETS:
                req = c["facet_requirements"][f.code]
                newguard_min = min(f.guard_min, 0.35 * req) if req > 0 else f.guard_min
                facetsC.append(FacetDef(f.code, f.label, f.beta, "guarded_weighted_mean",
                                        True, max(newguard_min, 0.0), f.weight,
                                        source=f.source, observable=f.observable,
                                        criticality=f.criticality))
            r3 = confront(spec, prof, cal, facets=facetsC)
            if r3 and r3.get("adequacy") is not None:
                pairs["critical_floor"].append((r3["decision"], g))
                decision_stats["critical_floor"][r3["decision"]] += 1
                aa_stats["critical_floor"].append(r3["adequacy"])
                rank3["critical_floor"].append((band3(r3["decision"]), band3(g)))

            # trivial rule: worst duty gap only
            gaps = [max(0.0, c["facet_requirements"][f.code] - levels[f.code]) for f in FACETS]
            w = max(gaps)
            dec = ("PROHIBIT" if w >= 0.35 else "REVIEW_REQUIRED" if w >= 0.20
                   else "ALLOW_WITH_GUARDS" if w >= 0.10 else "ALLOW")
            pairs["worst_gap_rule"].append((dec, g))
            decision_stats["worst_gap_rule"][dec] += 1

    out = {
        "pairs": n,
        "variants": {},
        "three_band_kappa": {v: kappa(rank3[v]) for v in results if v != "worst_gap_rule"},
    }
    for v in results:
        out["variants"][v] = {
            "kappa_vs_gold": round(kappa(pairs[v]), 4),
            "agreement": round(sum(1 for a, b in pairs[v] if a == b) / len(pairs[v]), 4),
            "decisions": dict(decision_stats[v]),
        }
        if v != "worst_gap_rule":
            out["variants"][v]["mean_adequacy"] = round(sum(aa_stats[v]) / len(aa_stats[v]), 4)
    with open(os.path.join(R4, "ablation_beta_check.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2)[:1800])


if __name__ == "__main__":
    main()