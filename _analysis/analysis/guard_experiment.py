"""D4.15 / D4.18 experiment: does adding epistemic guards (K1, K3) change agreement
with the normative panel, and does rebalancing criticality in TB/TS/IM change it?

Variants, evaluated against the same gold and the same stored (grounded) levels:
  full                         canonical v12
  guards_K1_K3                 K1 and K3 become guards with floor 0.50
  guards_all_K                 every K facet becomes a guard with floor 0.50
  no_K9                        K9 removed (the ablation says it is inert)
  rebalanced_criticality       criticality in TB, TS, IM raised to the SA/JS level

Run: python3 _analysis/analysis/guard_experiment.py
Output: Evaluacoes/r4/guard_experiment.json
"""
import json
import os
import sys
from collections import Counter
from dataclasses import replace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))
from facet_registry import FACETS                                                # noqa: E402
from core import CaseSpec, Profile, confront, load_fitted_calibration, requirement_for  # noqa: E402
from gold_panels_v5 import cohens_kappa                                           # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")


def guarded(f, floor=0.50):
    return replace(f, guard=True, guard_min=floor,
                   policy="guarded_weighted_mean")


def variants():
    k_facets = [f for f in FACETS if f.code.startswith("K")]
    return {
        "full": FACETS,
        "guards_K1_K3": [guarded(f) if f.code in ("K1", "K3") else f for f in FACETS],
        "guards_all_K": [guarded(f) for f in k_facets],
        "no_K9": [f for f in FACETS if f.code != "K9"],
        "rebalanced_criticality": FACETS,   # handled via requirements below
    }


def main():
    cal = load_fitted_calibration(os.path.join(R4, "ladder_calibration_v12.json"))
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        for line in open(os.path.join(R4, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c

    res = {v: {"pairs": 0, "model": [], "gold": [], "decisions": Counter(),
               "sum_aa": 0.0, "n_aa": 0} for v in variants()}

    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        c = cases.get(r["case_id"])
        if c is None or r.get("gold_consensus") is None:
            continue
        levels = {f.code: v for f, v in zip(FACETS, r["facet_levels"])}
        conf = {f.code: v for f, v in zip(FACETS, r["facet_confidence"])}
        base_req = {f.code: v for f, v in zip(FACETS, r["facet_requirements"])}
        for name, facets in variants().items():
            req = base_req
            if name == "rebalanced_criticality" and c["domain"] in ("TB", "TS", "IM"):
                # raise the requirement of every facet touching the domain to the
                # mean requirement observed in SA/JS cases of the same tier
                req = {k: min(1.0, v + 0.10) for k, v in base_req.items()}
            spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                            req, c["U_E"], c["R_c"], tuple(c.get("critical_pillars", ("M", "K"))),
                            c.get("horizon", "immediate"), c.get("conflict_pattern", "none"),
                            r.get("agent_layer", "system"), tuple(c.get("norms", ())),
                            norm_conflict=c.get("norm_conflict", "none"),
                            evidence_conflict=c.get("evidence_conflict", False),
                            exposure=c.get("exposure", 0.5))
            out = confront(spec, Profile(r["persona"], levels, conf, "system"), cal, facets=facets)
            res[name]["pairs"] += 1
            res[name]["model"].append(out["decision"])
            res[name]["gold"].append(r["gold_consensus"])
            res[name]["decisions"][out["decision"]] += 1
            if out["adequacy_low"] is not None:
                res[name]["sum_aa"] += out["adequacy_low"]
                res[name]["n_aa"] += 1

    base_k = cohens_kappa(res["full"]["model"], res["full"]["gold"])
    out = {"corpus": f"corpus_v{CORPUS_VER}", "calibration": "fitted B5 v12",
           "pairs": res["full"]["pairs"], "variants": {}}
    for name, v in res.items():
        k = cohens_kappa(v["model"], v["gold"])
        out["variants"][name] = {
            "kappa": round(k, 4),
            "delta_vs_full": round(k - base_k, 4),
            "agreement": round(sum(a == b for a, b in zip(v["model"], v["gold"])) / v["pairs"], 4),
            "mean_adequacy_low": round(v["sum_aa"] / v["n_aa"], 4),
            "decision_distribution": dict(v["decisions"]),
        }
    out["reading"] = ("A variant that does not improve kappa should not be added to the "
                      "model: guards and criticality weights are normative claims and must "
                      "pay for themselves in agreement, not in intuition.")
    json.dump(out, open(os.path.join(R4, "guard_experiment.json"), "w"), indent=2)
    for name, v in out["variants"].items():
        print(f"{name:<24} κ={v['kappa']:.4f} Δ={v['delta_vs_full']:+.4f} "
              f"agree={v['agreement']:.4f} meanAa={v['mean_adequacy_low']:.4f}")


if __name__ == "__main__":
    main()
