"""B20/B21 (Rodada 5) - variant evaluation harness for the v13 canon.

Question: the v13 core adds mechanisms that are *inert by default* (D5.1 lattice marginal,
D5.2 case-adaptive salience s, D5.3 cross-pillar duty term zeta, D5.4 oversight regime,
D5.5 facet-beta revision). Do they actually improve agreement with the normative panels,
or are they another decorative clause? Nothing enters the canon without this measurement.

Method. A stratified sample of cases from corpus v6 is rebuilt from the generator's own
objects - persona factors, case requirements, declared facts and the stored observation
confidences - exactly as `mirror_full_corpus.py` does. For every variant we recompute:
  * the requirement vector r_f (requirement_for), which depends on domain criticality and,
    from v13, on the oversight regime;
  * the persona levels implied by those requirements, then the E30 fact-grounding caps;
  * the model verdict with core.confront;
  * the panel verdicts with the same gold rubric (gold_panels_v5.adjudicate) applied to the
    same levels and facts, so the ground truth follows the case, not the model.
Cohen's kappa is reported overall, by consensus stratum (the split declared in D4.32), by
domain, and against each panel individually.

Run:
  python3 _analysis/analysis/b20_variant_eval.py --cases 300 --seed 42
Writes Evaluacoes/r5/B20_variant_eval.json
"""
import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import fields as dataclass_fields, replace

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "corpus"))

from core import (CaseSpec, Profile, confront, requirement_for, load_fitted_calibration,   # noqa: E402
                  Calibration)
from facet_registry import FACETS                                                          # noqa: E402
from fact_grounding import grounded_levels                                                  # noqa: E402
from gold_panels_v5 import adjudicate, cohens_kappa                                        # noqa: E402

DELIVERED_CAP = 0.95
GROUND_STRENGTH = 1.0
R4 = os.path.join(ROOT, "Evaluacoes", "r4")


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def stratified_cases(rows, n, rng):
    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["domain"], r["layer"])].append(r)
    keys = sorted(by_key)
    out = []
    per = max(1, n // len(keys))
    for k in keys:
        pool = by_key[k]
        take = min(len(pool), per + (1 if rng.random() < 0.5 else 0))
        idx = rng.choice(len(pool), size=min(take, len(pool)), replace=False)
        out.extend(pool[int(i)] for i in idx)
    return out


def build_case(raw, oversight):
    return CaseSpec(raw["case_id"], raw["domain"], raw["severity"], raw["prudential"],
                    raw["irreversibility"], raw["facet_requirements"], raw["U_E"], raw["R_c"],
                    tuple(raw["critical_pillars"]), raw["horizon"], raw["conflict_pattern"],
                    raw.get("agent_layer", "system"), tuple(raw["norms"]),
                    norm_conflict=raw["norm_conflict"], evidence_conflict=raw["evidence_conflict"],
                    exposure=raw["exposure"], oversight=oversight)


def derive_oversight(facts):
    """E11c': the regime is inferred from declared facts, never invented."""
    review = bool(facts.get("human_review_channel", False))
    audit = bool(facts.get("independent_audit", False))
    appeal = bool(facts.get("appeal_channel", False))
    if review and audit:
        return "in_the_loop"
    if review or appeal:
        return "on_the_loop"
    return "none"


def evaluate(cases, personas, rows_by_case, conf_map, variant, cal):
    facets = list(FACETS)
    if variant.get("beta_overrides"):
        bo = variant["beta_overrides"]
        facets = [replace(f, beta=tuple(bo[f.code])) if f.code in bo else f for f in facets]
    if variant.get("guard_off"):
        codes = {f.code for f in FACETS if f.guard} if variant["guard_off"] == "ALL" \
            else set(variant["guard_off"])
        facets = [replace(f, guard=False) if f.code in codes else f for f in facets]
    if variant.get("beta_primary"):
        pillars = ("W", "C", "M", "K")
        facets = [replace(f, beta=tuple(1.0 if i == pillars.index(f.code[0]) else 0.0
                       for i in range(4))) if f.n_pillars() > 1 else f for f in facets]
    if variant.get("criticality_overrides"):
        co = variant["criticality_overrides"]
        facets = [replace(f, criticality={**f.criticality, **co.get(f.code, {})})
                  if f.code in co else f for f in facets]
    cal = Calibration(**{**{f.name: getattr(cal, f.name) for f in dataclass_fields(Calibration)},
                         **variant.get("cal_overrides", {})})
    errs = cal.is_valid()
    if errs:
        return {"name": variant["name"], "error": errs}

    pairs, strata, panels, domains = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    dec, review_need = Counter(), defaultdict(list)
    aa_sum = aa_n = 0.0
    psi_sum = 0.0
    t0 = time.time()
    for raw in cases:
        oversight = (derive_oversight(raw["facts"]) if variant.get("oversight") == "derived"
                     else variant.get("oversight", "unspecified"))
        neutral = build_case(raw, "unspecified")
        reqs = {f.code: requirement_for(f, neutral) for f in facets}
        case = build_case(raw, oversight)
        case.facet_requirements = reqs
        for row in rows_by_case[raw["case_id"]]:
            persona = personas.get(row["persona"])
            if row["persona"] == "AGENT-declared":
                levels = dict(raw["declared_levels"])
            else:
                levels = {f.code: float(min(1.0, reqs[f.code] * min(DELIVERED_CAP,
                            persona["factors"].get(f.code, persona["default_factor"])
                            * (1.0 + persona["jitter"])))) for f in facets}
            levels, _ = grounded_levels(raw["facts"], reqs, levels, GROUND_STRENGTH)
            conf = conf_map.get((raw["case_id"], row["persona"]), {})
            res = confront(case, Profile(row["persona"], levels, conf, row["agent_layer"]),
                           cal, facets)
            gold = adjudicate(case, levels, raw["facts"])
            verdict = res["decision"]
            dec[verdict] += 1
            pairs["overall"].append((verdict, gold["consensus"]))
            stratum = ("unanimous" if gold["unanimous"] else
                       "contested" if gold["spread"] >= 2 else "majority")
            strata[stratum].append((verdict, gold["consensus"]))
            for p in ("A", "B", "C"):
                panels[p].append((verdict, gold[f"panel{p}"]))
            domains[raw["domain"]].append((verdict, gold["consensus"]))
            if res.get("adequacy") is not None:
                aa_sum += res["adequacy"]
                aa_n += 1
                psi_sum += res["cross_pillar_duty"]
                review_need[verdict].append(res["review_need"])
    return {
        "name": variant["name"],
        "variant": {k: v for k, v in variant.items() if k != "cal_overrides"},
        "n_pairs": len(pairs["overall"]),
        "verdicts": [v for v, _ in pairs["overall"]],
        "gold": [g for _, g in pairs["overall"]],
        "kappa_overall": round(cohens_kappa([a for a, _ in pairs["overall"]],
                                           [b for _, b in pairs["overall"]]), 4),
        "kappa_by_stratum": {s: round(cohens_kappa([a for a, _ in v], [b for _, b in v]), 4)
                             for s, v in sorted(strata.items())},
        "pairs_by_stratum": {s: len(v) for s, v in sorted(strata.items())},
        "kappa_vs_panel": {p: round(cohens_kappa([a for a, _ in panels[p]],
                                                [b for _, b in panels[p]]), 4) for p in ("A", "B", "C")},
        "kappa_by_domain": {d: round(cohens_kappa([a for a, _ in v], [b for _, b in v]), 4)
                            for d, v in sorted(domains.items())},
        "mean_adequacy": round(aa_sum / aa_n, 4) if aa_n else None,
        "mean_cross_pillar_duty": round(psi_sum / aa_n, 4) if aa_n else None,
        "decision_distribution": dict(dec),
        "mean_review_need_by_decision": {d: round(sum(v) / len(v), 4) for d, v in review_need.items()},
        "runtime_seconds": round(time.time() - t0, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--registry", default=None, help="JSON {code: beta} overrides to test")
    ap.add_argument("--beta", default=None, help="JSON {code: beta} overrides (facet canon revision)")
    ap.add_argument("--crit", default=None, help="JSON {code: {domain: criticality}} overrides")
    ap.add_argument("--out", default=os.path.join(ROOT, "Evaluacoes", "r5", "B20_variant_eval.json"))
    ap.add_argument("--oversight-only", action="store_true")
    ap.add_argument("--store", action="store_true", help="keep the per-pair verdict arrays in the output")
    ap.add_argument("--guards-ablation", action="store_true",
                    help="B21: run guard-removal ablations (all 12 guarded facets, one at a time)")
    ap.add_argument("--beta-primary", action="store_true",
                    help="B21: collapse every multi-pillar duty onto its primary pillar")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    rows = list(read_jsonl(os.path.join(R4, "corpus_v6_layerA.jsonl")))
    rows += list(read_jsonl(os.path.join(R4, "corpus_v6_layerB.jsonl")))
    rng = np.random.default_rng(args.seed)
    cases = stratified_cases(rows, args.cases, rng)
    case_ids = {c["case_id"] for c in cases}
    rows_by_case = defaultdict(list)
    conf_map = {}
    for r in read_jsonl(os.path.join(R4, "corpus_v6_confrontations.jsonl")):
        if r["case_id"] in case_ids:
            rows_by_case[r["case_id"]].append(r)
            conf_map[(r["case_id"], r["persona"])] = dict(zip([f.code for f in FACETS],
                                                             r["facet_confidence"]))
    personas = {p["profile_id"]: p for p in read_jsonl(os.path.join(R4, "corpus_v6_personas.jsonl"))}
    cal = load_fitted_calibration()

    variants = [
        {"name": "v13_baseline", "oversight": "unspecified"},
        {"name": "lambda(E) s=0.5", "oversight": "unspecified", "cal_overrides": {"salience_adaptation": 0.5}},
        {"name": "lambda(E) s=1.0", "oversight": "unspecified", "cal_overrides": {"salience_adaptation": 1.0}},
        {"name": "lambda(E) s=2.0", "oversight": "unspecified", "cal_overrides": {"salience_adaptation": 2.0}},
        {"name": "cross-pillar zeta=0.05", "oversight": "unspecified", "cal_overrides": {"zeta": 0.05}},
        {"name": "cross-pillar zeta=0.10", "oversight": "unspecified", "cal_overrides": {"zeta": 0.10}},
        {"name": "oversight from facts", "oversight": "derived"},
        {"name": "oversight from facts + zeta=0.05", "oversight": "derived",
         "cal_overrides": {"zeta": 0.05}},
    ]
    beta = json.load(open(args.beta)) if args.beta else None
    crit = json.load(open(args.crit)) if args.crit else None
    if isinstance(crit, dict) and "overrides" in crit:
        crit = crit["overrides"]
    if args.registry:
        with open(args.registry) as fh:
            beta = json.load(fh)
    if beta:
        variants.append({"name": "revised beta canon", "oversight": "unspecified",
                        "beta_overrides": beta})
        variants.append({"name": "revised beta + oversight", "oversight": "derived",
                        "beta_overrides": beta})
    if crit:
        variants.append({"name": "criticality rebalance", "oversight": "unspecified",
                        "criticality_overrides": crit})
        variants.append({"name": "criticality rebalance + oversight", "oversight": "derived",
                        "criticality_overrides": crit})
    if beta and crit:
        variants.append({"name": "beta + criticality + oversight", "oversight": "derived",
                        "beta_overrides": beta, "criticality_overrides": crit})
    if args.guards_ablation:
        guarded = [f.code for f in FACETS if f.guard]
        variants.append({"name": "all guards removed", "oversight": "unspecified",
                        "guard_off": "ALL"})
        for code in guarded:
            variants.append({"name": f"guard removed: {code}", "oversight": "unspecified",
                            "guard_off": [code]})
    if args.beta_primary:
        variants.append({"name": "duties collapsed to primary pillar",
                        "oversight": "unspecified", "beta_primary": True})

    results = []
    for v in variants:
        r = evaluate(cases, personas, rows_by_case, conf_map, v, cal)
        results.append(r)
        if "error" in r:
            print(f"{v['name']:38s} INVALID: {r['error']}")
        else:
            print(f"{v['name']:38s} kappa={r['kappa_overall']}  n={r['n_pairs']}  "
                  f"meanAa={r['mean_adequacy']}  ({r['runtime_seconds']}s)")

    # paired bootstrap: resample the SAME pairs for baseline and variant, so the
    # difference is measured on matched data rather than two independent samples.
    base = next(r for r in results if r["name"] == "v13_baseline")
    if "verdicts" in base:
        rng = np.random.default_rng(11)
        n = len(base["verdicts"])
        for r in results:
            if r["name"] == "v13_baseline" or "error" in r:
                continue
            deltas = []
            for _ in range(200):
                idx = rng.integers(0, n, n)
                k0 = cohens_kappa([base["verdicts"][i] for i in idx], [base["gold"][i] for i in idx])
                k1 = cohens_kappa([r["verdicts"][i] for i in idx], [r["gold"][i] for i in idx])
                deltas.append(k1 - k0)
            deltas.sort()
            r["delta_kappa_vs_baseline"] = round(r["kappa_overall"] - base["kappa_overall"], 4)
            r["delta_ci95_bootstrap"] = [round(deltas[int(0.025 * len(deltas))], 4),
                                         round(deltas[int(0.975 * len(deltas))], 4)]
            print(f"   Δκ {r['name']:34s} {r['delta_kappa_vs_baseline']:+.4f} "
                  f"CI95 {r['delta_ci95_bootstrap']}")
    if not args.store:
        for r in results:
            r.pop("verdicts", None)
            r.pop("gold", None)
    with open(args.out, "w") as fh:
        json.dump({"battery": "B20",
                   "question": "which of the v13 mechanisms change agreement with the panels?",
                   "n_cases_sampled": len(cases),
                   "n_personas": len(personas),
                   "calibration": "frozen r3 ladder (the convention declared in the manifest)",
                   "results": results}, fh, indent=2)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
