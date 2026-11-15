"""Battery B1: formal-core invariants. Writes Evaluacoes/B1_formal_invariants.json."""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formal_core_v3 as m

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Evaluacoes",
                   "B1_formal_invariants.json")

r = (0.20, 0.25, 0.35, 0.20)
lam = (0.15, 0.20, 0.45, 0.20)
profiles = {
    "Balanced": (0.25, 0.25, 0.25, 0.25),
    "Capable but unaccountable": (0.20, 0.45, 0.15, 0.20),
    "Normatively strong, weak on means": (0.20, 0.15, 0.45, 0.20),
    "Intent-only (aspiring)": (0.50, 0.15, 0.20, 0.15),
    "Vetoed but compensable": (0.30, 0.30, 0.35, 0.05),
}
example = []
for name, a in profiles.items():
    Aa, delta, pen = m.adequacy(a, r, lam, 0.35, critical=(2, 3))
    Rr = m.residual_risk(Aa, 0.6)
    veto = m.hard_veto(delta, (2, 3))
    example.append({"profile": name, "a": list(a), "Aa": round(Aa, 4),
                    "delta": [round(x, 4) for x in delta], "penalty": round(pen, 4),
                    "R_r": round(Rr, 4), "veto": veto,
                    "decision": m.decision(Aa, Rr, 0.6, veto=veto),
                    "decision_Aa_only": m.decision(Aa, Rr, 0.6)})

fails2, stats2 = m.invariant_tests(variant="v2")
fails3, stats3 = m.invariant_tests(variant="v3")
lo, hi, l0, h0 = m.show_metric_relation()

payload = {
    "battery": "B1 - formal core invariants",
    "samples": 20000,
    "seed": 7,
    "geometry": {
        "proposition1_unit_edge": m.proposition_1(),
        "circumradius_of_edge1_tetrahedron": m.R_CIRC,
        "metric_ratio_d_induced_over_d_total_variation": {"observed": [round(lo, 4), round(hi, 4)],
                                                          "theoretical": [round(l0, 4), round(h0, 4)]},
        "barycentric_volume_shares_are_exact": [round(x, 6) for x in m.barycentric_volume_shares((0.4, 0.3, 0.2, 0.1))],
    },
    "v2_paper_form": {"violations": {k: v[0] for k, v in fails2.items()},
                      "examples": {k: v[1] for k, v in fails2.items()},
                      "stats": stats2},
    "v3_hierarchical_deficit": {"violations": {k: v[0] for k, v in fails3.items()},
                                "examples": {k: v[1] for k, v in fails3.items()},
                                "stats": stats3},
    "invariants_checked": ["bounds", "perfect_adequacy", "risk_band", "risk_floor", "veto_guard",
                          "monotonicity_no_free_lunch", "volume_degeneracy",
                          "hier_deficit_monotone", "hier_weakest_link", "balance_bounds",
                          "amgm_volume_balance", "shares_equal_profile"],
    "worked_example": example,
    "conclusion": {
        "v2_risk_floor_violations": fails2.get("risk_floor", [0])[0],
        "v2_monotonicity_violations": fails2.get("monotonicity", [0])[0],
        "v3_violations": sum(v[0] for v in fails3.values()),
        "compensation_hides_veto_v2_pct": round(100.0 * stats2["veto_present_but_adequacy_high"] / stats2["veto_present"], 2),
        "compensation_hides_veto_v3_pct": round(100.0 * stats3["veto_present_but_adequacy_high"] / stats3["veto_present"], 2),
    },
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2, ensure_ascii=False)
print(json.dumps(payload["conclusion"], indent=2))
print("wrote", OUT)
