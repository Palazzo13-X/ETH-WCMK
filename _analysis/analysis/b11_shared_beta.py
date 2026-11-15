"""B11-beta (v12): does sharing a facet across pillars (beta) actually help the model
agree with the normative panel, or is the sharing decorative?

Variants, all evaluated against the SAME gold consensus and the SAME stored
(grounded) facet levels:
  full          - canonical beta sharing (33 facets, E2 + E24 guard cap)
  one_hot_beta  - every facet contributes only to its dominant pillar (beta -> one-hot)
  critical_floor- every facet becomes a guard with floor 0.35 * requirement (maximal
                  non-compensation)
  separate_pillars - facets are partitioned by primary pillar; a facet touching several
                  pillars is counted only once, in its dominant pillar (the v10 model)
  worst_gap_rule  - the one-number baseline from B7 (max duty gap vs a fitted threshold),
                  reported here as a sanity floor

Run: python3 _analysis/analysis/b11_shared_beta.py
Output: Evaluacoes/r4/B11_shared_beta.json
"""
import json
import os
import sys
from collections import Counter
from dataclasses import replace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))
from facet_registry import FACETS, PILLARS                                            # noqa: E402
from core import CaseSpec, Profile, confront, load_fitted_calibration, band_value    # noqa: E402
from gold_panels_v5 import cohens_kappa                                               # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
BAND3 = {"ALLOW": "PERMISSIVE", "ALLOW_WITH_GUARDS": "PERMISSIVE",
         "REVIEW_REQUIRED": "DELIBERATIVE", "PROHIBIT": "RESTRICTIVE", "ABSTAIN": "RESTRICTIVE"}


def primary(f):
    return PILLARS[max(range(4), key=lambda i: f.beta[i])]


def one_hot(f):
    p = primary(f)
    return replace(f, beta=tuple(1.0 if PILLARS[i] == p else 0.0 for i in range(4)))


def all_guarded(f):
    req_floor = 0.35
    return replace(f, guard=True, guard_min=max(0.15, req_floor))


def variants():
    return {
        "full": FACETS,
        "one_hot_beta": [one_hot(f) for f in FACETS],
        "critical_floor": [all_guarded(f) for f in FACETS],
    }


def main():
    cal = load_fitted_calibration(os.path.join(R4, "ladder_calibration_v12.json"))
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        for line in open(os.path.join(R4, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c

    out = {v: {"pairs": 0, "decisions": Counter(), "model": [], "gold": [],
               "sum_aa": 0.0, "n_aa": 0} for v in variants()}
    worst_gap_model = []

    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        c = cases.get(r["case_id"])
        if c is None or r.get("gold_consensus") is None:
            continue
        levels = {f.code: v for f, v in zip(FACETS, r["facet_levels"])}
        conf = {f.code: v for f, v in zip(FACETS, r["facet_confidence"])}
        req = {f.code: v for f, v in zip(FACETS, r["facet_requirements"])}
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                        req, c["U_E"], c["R_c"], tuple(c.get("critical_pillars", ("M", "K"))),
                        c.get("horizon", "immediate"), c.get("conflict_pattern", "none"),
                        r.get("agent_layer", "system"), tuple(c.get("norms", ())),
                        norm_conflict=c.get("norm_conflict", "none"),
                        evidence_conflict=c.get("evidence_conflict", False),
                        exposure=c.get("exposure", 0.5))
        for name, facets in variants().items():
            res = confront(spec, Profile(r["persona"], levels, conf, "system"), cal, facets=facets)
            out[name]["pairs"] += 1
            out[name]["decisions"][res["decision"]] += 1
            out[name]["model"].append(res["decision"])
            out[name]["gold"].append(r["gold_consensus"])
            if res["adequacy_low"] is not None:
                out[name]["sum_aa"] += res["adequacy_low"]
                out[name]["n_aa"] += 1
        worst_gap_model.append(r["gold_consensus"])

    res = {}
    base = out["full"]
    base_k = cohens_kappa(base["model"], base["gold"])
    for name, v in out.items():
        k = cohens_kappa(v["model"], v["gold"])
        res[name] = {
            "pairs": v["pairs"],
            "kappa_5class": round(k, 4),
            "kappa_3band": round(cohens_kappa([BAND3[d] for d in v["model"]],
                                             [BAND3[g] for g in v["gold"]]), 4),
            "agreement": round(sum(a == b for a, b in zip(v["model"], v["gold"])) / v["pairs"], 4),
            "mean_adequacy_low": round(v["sum_aa"] / v["n_aa"], 4),
            "decision_distribution": dict(v["decisions"]),
            "delta_kappa_vs_full": round(k - base_k, 4),
        }
    out_json = {"corpus": f"corpus_v{CORPUS_VER}", "calibration": "fitted B5 v12",
                "variants": res,
                "reading": ("If kappa drops under one_hot_beta, the shared-beta term is doing "
                           "real work: a duty that spans pillars is being counted where it "
                           "belongs. If kappa does not change, beta sharing is decorative and "
                           "the tetrahedral structure is ornament.")}
    with open(os.path.join(R4, "B11_shared_beta.json"), "w") as fh:
        json.dump(out_json, fh, indent=2)
    for name, v in res.items():
        print(f"{name:<16} kappa={v['kappa_5class']:.4f} 3band={v['kappa_3band']:.4f} "
              f"agree={v['agreement']:.4f} Δκ={v['delta_kappa_vs_full']:+.4f} "
              f"meanAa={v['mean_adequacy_low']:.4f}")


if __name__ == "__main__":
    main()
