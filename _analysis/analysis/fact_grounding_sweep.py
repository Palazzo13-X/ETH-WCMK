"""Sensitivity of the concordance with the normative panel to how strongly case facts
ground the declared facet levels (gate G6', P2).

A verifiable procedural fact (no audit trail, no appeal channel, no containment
exercised, ...) is an observation of the facet it names:

    ell_f = min(ell_f, q_f * (1 - s * (1 - c_fact)))

where c_fact is the compliance implied by the fact (1.0 when satisfied, otherwise the
unsatisfied factor declared in FACT_MAP) and s in [0,1] is the grounding strength.
s = 0 reproduces the v12 corpus exactly; s = 1 is the hard cap used in the first run.

For each s we report kappa and agreement against (a) the panel recomputed on the same
grounded observations (internally consistent comparison) and (b) the stored panel
verdicts (the corpus as it stands today).

Deterministic sample: every 4th persona (30 of 120), all 1.520 cases -> 45.600 pairs.

Writes Evaluacoes/r4/fact_grounding_sweep.json.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))

from facet_registry import FACETS                                          # noqa: E402
from core import CaseSpec, Profile, confront, load_fitted_calibration      # noqa: E402
from gold_panels_v5 import adjudicate, cohens_kappa                        # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")

from fact_grounding_v12 import FACT_MAP, compliance                        # noqa: E402
SCALE = 0.5


def grounded_levels(case, base, req, s):
    out = dict(base)
    facts = case.get("facts", {})
    applied = []
    for fact, (facet, _sat, _unsat) in FACT_MAP.items():
        if fact not in facts:
            continue
        c = compliance(fact, facts[fact])
        cap = req[facet] * (1.0 - s * (1.0 - c))
        if out[facet] > cap:
            out[facet] = cap
            applied.append((fact, facet, round(cap, 4)))
    return out, applied


def main():
    cal = load_fitted_calibration()
    cases = []
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        with open(os.path.join(R4, fn)) as fh:
            cases.extend(json.loads(l) for l in fh)
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_personas.jsonl")) as fh:
        personas = [json.loads(l) for l in fh][::4]
    stored_gold = {}
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_gold.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            stored_gold[(r["case_id"], r["persona"])] = r["consensus"]

    out = {"sample_personas": len(personas), "cases": len(cases),
           "pairs": len(personas) * len(cases), "results": {}}
    for s in (0.0, 0.25, 0.50, 0.75, 1.00):
        seq_m, seq_g_ground, seq_g_stored = [], [], []
        dec = Counter()
        aa = []
        for c in cases:
            spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                            c["irreversibility"], c["facet_requirements"], c["U_E"], c["R_c"],
                            tuple(c["critical_pillars"]), c["horizon"], c["conflict_pattern"],
                            "system", tuple(c.get("norms", ())),
                            norm_conflict=c.get("norm_conflict", "none"),
                            evidence_conflict=c.get("evidence_conflict", False),
                            exposure=c.get("exposure", 0.5))
            req = c["facet_requirements"]
            for p in personas:
                base = {f.code: min(1.0, req[f.code] *
                                    min(0.95, p["factors"].get(f.code, p["default_factor"])
                                        * (1.0 + p["jitter"])))
                        for f in FACETS}
                conf = {f.code: p.get("confidence_mu", 0.85) for f in FACETS}
                levels, _ = grounded_levels(c, base, req, s)
                r = confront(spec, Profile(p["profile_id"], levels, conf, p["layer"]), cal)
                g = adjudicate(spec, levels, c.get("facts", {}))["consensus"]
                seq_m.append(r["decision"])
                seq_g_ground.append(g)
                seq_g_stored.append(stored_gold.get((c["case_id"], p["profile_id"]), g))
                dec[r["decision"]] += 1
                aa.append(r["adequacy"])
        out["results"][str(s)] = {
            "kappa_vs_panel_on_same_observations": round(cohens_kappa(seq_m, seq_g_ground), 4),
            "kappa_vs_stored_panel": round(cohens_kappa(seq_m, seq_g_stored), 4),
            "agreement_vs_panel_same_obs": round(sum(1 for a, b in zip(seq_m, seq_g_ground) if a == b) / len(seq_m), 4),
            "mean_adequacy": round(sum(aa) / len(aa), 4),
            "decisions": dict(dec),
        }
    with open(os.path.join(R4, "fact_grounding_sweep.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2)[:2500])


if __name__ == "__main__":
    main()