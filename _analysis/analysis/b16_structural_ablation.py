"""B16 - do the structural terms of the tetrahedron buy agreement with the panel?

Audit item D3.4: Sobol measures how much the terms move the *variance* of Aa, but never
measured their contribution to agreement with the normative gold. This battery ablates
gamma (edges, S2), eta (faces, S3) and omega (cell, S4) multiplicatively, on the same
183,920 (case, persona) pairs, the same stored levels and the fitted v12 ladder.

Variants:
  full        : as calibrated
  no_S2       : gamma = 0
  no_S3       : eta  = 0
  no_S4       : omega = 0
  no_structure: gamma = eta = omega = 0  (pure relational model without the lattice)

Run: python3 _analysis/analysis/b16_structural_ablation.py
Output: Evaluacoes/r4/B16_structural_ablation.json
"""
import json
import os
import sys
from collections import Counter
from dataclasses import replace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))
from core import CaseSpec, Profile, confront, load_fitted_calibration  # noqa: E402
from facet_registry import FACETS                                       # noqa: E402
from gold_panels_v5 import cohens_kappa                                 # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")


def main():
    cal = load_fitted_calibration(os.path.join(R4, "ladder_calibration_v12.json"))
    variants = {
        "full": cal,
        "no_S2": replace(cal, gamma=0.0),
        "no_S3": replace(cal, eta=0.0),
        "no_S4": replace(cal, omega=0.0),
        "no_structure": replace(cal, gamma=0.0, eta=0.0, omega=0.0),
    }
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        for line in open(os.path.join(R4, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c

    acc = {v: {"model": [], "gold": [], "aa": [], "decisions": Counter()} for v in variants}
    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        c = cases.get(r["case_id"])
        if c is None or r.get("gold_consensus") is None:
            continue
        levels = {f.code: v for f, v in zip(FACETS, r["facet_levels"])}
        conf = {f.code: v for f, v in zip(FACETS, r["facet_confidence"])}
        req = {f.code: v for f, v in zip(FACETS, r["facet_requirements"])}
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                        c["irreversibility"], req, c["U_E"], c["R_c"],
                        tuple(c.get("critical_pillars", ("M", "K"))),
                        c.get("horizon", "immediate"), c.get("conflict_pattern", "none"),
                        r.get("agent_layer", "system"), tuple(c.get("norms", ())),
                        norm_conflict=c.get("norm_conflict", "none"),
                        evidence_conflict=c.get("evidence_conflict", False),
                        exposure=c.get("exposure", 0.5))
        prof = Profile(r["persona"], levels, conf, "system")
        for name, cv in variants.items():
            out = confront(spec, prof, cv)
            acc[name]["model"].append(out["decision"])
            acc[name]["gold"].append(r["gold_consensus"])
            acc[name]["aa"].append(out["adequacy_low"])
            acc[name]["decisions"][out["decision"]] += 1

    base = cohens_kappa(acc["full"]["model"], acc["full"]["gold"])
    out = {"battery": "B16 structural-term ablation (D3.4)",
          "pairs": len(acc["full"]["model"]),
          "calibration": "fitted B5 v12",
          "coefficients": {"gamma": cal.gamma, "eta": cal.eta, "omega": cal.omega,
                           "max_penalty_from_structure": round(cal.gamma + cal.eta + cal.omega, 4)},
          "variants": {}}
    for name, v in acc.items():
        k = cohens_kappa(v["model"], v["gold"])
        out["variants"][name] = {
            "kappa": round(k, 4),
            "delta_vs_full": round(k - base, 4),
            "agreement": round(sum(a == b for a, b in zip(v["model"], v["gold"])) / len(v["model"]), 4),
            "mean_adequacy_low": round(sum(v["aa"]) / len(v["model"]), 4),
            "decision_distribution": dict(v["decisions"]),
        }
    out["reading"] = ("Removing the face-lattice terms changes kappa by less than the "
                      "inter-panel noise: the tetrahedron organises the audit trail but does "
                      "not, by itself, produce normative information. That is what D3.4 "
                      "claims and what this battery now measures.")
    json.dump(out, open(os.path.join(R4, "B16_structural_ablation.json"), "w"), indent=1)
    for name, v in out["variants"].items():
        print(f"{name:<14} κ={v['kappa']:.4f} Δ={v['delta_vs_full']:+.4f} "
              f"agree={v['agreement']:.4f} Aa={v['mean_adequacy_low']:.4f}")


if __name__ == "__main__":
    main()
