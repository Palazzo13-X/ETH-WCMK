"""B11-procedural: does adding the five procedural facets (M8 notice, M9 human review,
M10 consent/participation, C8 data minimisation, K9 review/sunset) actually buy
agreement with the normative panel, or is it ontology decoration?

Same cases, same personas, same facts, same gold - only the facet set changes.
Deterministic subsample: every 4th persona (30 of 120) x 1,520 cases = 45,600 pairs.

Run: python3 _analysis/analysis/procedural_facet_ablation.py
Output: Evaluacoes/r4/procedural_facet_ablation.json
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))
from facet_registry import FACETS, BY_CODE                                        # noqa: E402
from core import CaseSpec, Profile, confront, load_fitted_calibration             # noqa: E402
from gold_panels_v5 import cohens_kappa                                           # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
NEW = ["M8", "M9", "M10", "C8", "K9"]


def kappa_bins(pairs):
    return cohens_kappa([a for a, _ in pairs], [b for _, b in pairs])


def main():
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        for line in open(os.path.join(R4, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c
    cal = load_fitted_calibration()

    variants = {
        "full_33": FACETS,
        "procedural_facets_removed_28": [f for f in FACETS if f.code not in NEW],
    }
    for code in NEW:
        variants[f"only_{code}_removed_32"] = [f for f in FACETS if f.code != code]

    results = {k: {"pairs": 0, "decisions": Counter(), "gold": [], "model": [],
                   "sum_aa": 0.0, "n_aa": 0} for k in variants}

    n = 0
    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        c = cases.get(r["case_id"])
        if c is None or r.get("gold_consensus") is None:
            continue
        persona_idx = int(r["persona"].split("-")[-1]) if r["persona"].split("-")[-1].isdigit() else 0
        if persona_idx % 4:
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
        for name, facets in variants.items():
            res = confront(spec, Profile(r["persona"], levels, conf, "system"), cal, facets=facets)
            dec = res["decision"]
            results[name]["pairs"] += 1
            results[name]["decisions"][dec] += 1
            results[name]["model"].append(dec)
            results[name]["gold"].append(r["gold_consensus"])
            if res["adequacy_low"] is not None:
                results[name]["sum_aa"] += res["adequacy_low"]
                results[name]["n_aa"] += 1
        n += 1

    out = {"pairs_sampled": n, "calibration": "fitted (B5 v12)",
           "gold_distribution": dict(Counter(results["full_33"]["gold"])),
           "variants": {}}
    base = results["full_33"]
    for name, v in results.items():
        k = kappa_bins(list(zip(v["model"], v["gold"])))
        out["variants"][name] = {
            "pairs": v["pairs"], "kappa": round(k, 4),
            "agreement": round(sum(a == b for a, b in zip(v["model"], v["gold"])) / v["pairs"], 4),
            "mean_adequacy_low": round(v["sum_aa"] / v["n_aa"], 4),
            "decision_distribution": dict(v["decisions"]),
            "delta_kappa_vs_full": round(k - cohens_kappa(base["model"], base["gold"]), 4),
        }
    out["reading"] = ("If kappa falls when the procedural facets are removed, the five new "
                      "facets are carrying normative content the panel was already applying "
                      "through its procedural rules; if it does not, they are decoration.")
    with open(os.path.join(R4, "procedural_facet_ablation.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    for name, v in out["variants"].items():
        print(f"{name:<32} kappa={v['kappa']:.4f} agreement={v['agreement']:.4f} "
              f"Δκ={v['delta_kappa_vs_full']:+.4f} meanAa={v['mean_adequacy_low']:.4f}")


if __name__ == "__main__":
    main()
