#!/usr/bin/env python3
"""Calibration sensitivity of the corpus verdicts.

The corpus was confronted with the ladder parameters from
Evaluacoes/r3/ladder_calibration.json (core.load_fitted_calibration() looks for
ladder_calibration.json in r4 first; r4 has no file with that name yet).
Battery B5 then fitted a ladder on this corpus and wrote
Evaluacoes/r4/ladder_calibration_v12.json. This script re-runs the same
(case, persona) pairs against that v12 fit and reports how the verdicts move.

Confidence values are taken at their persona mean (confidence_mu) rather than the
seeded draws used in the main run; the adequacy interval shifts by <0.01 in tests,
and the verdict counts are reported with that caveat.

Writes Evaluacoes/r4/corpus_v5_calibration_sensitivity.json.
"""

import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "formal_core"))

from core import confront, load_fitted_calibration, Profile               # noqa: E402
from facet_registry import FACETS                                          # noqa: E402
from gen_corpus_v5 import (make_layerA, make_layerB, make_personas, case_spec,
                           delivery, DELIVERED_CAP)                        # noqa: E402
from gold_panels_v5 import cohens_kappa, RANK                              # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r4")


def decisions_for(cal, cases, personas):
    dec = Counter()
    seq, gold_seq = [], []
    aa = []
    for c in cases:
        spec = case_spec(c)
        req = c["facet_requirements"]
        for p in personas:
            levels = {f.code: delivery(f, p, req) for f in FACETS}
            conf = {f.code: p["confidence_mu"] for f in FACETS}
            r = confront(spec, Profile(p["profile_id"], levels, conf, p["layer"]), cal)
            dec[r["decision"]] += 1
            aa.append(r["adequacy"])
            seq.append(r["decision"])
            gold_seq.append(gold_by_key[(c["case_id"], p["profile_id"])]["consensus"])
    return dec, aa, seq, gold_seq


gold_by_key = {(g["case_id"], g["persona"]): g
               for g in (json.loads(l) for l in
                         open(os.path.join(OUT, "corpus_v5_gold.jsonl")))}

def main():
    layerA = make_layerA(1200)
    layerB = make_layerB(320)
    cases = layerA + layerB
    personas = make_personas()

    cal_r3 = load_fitted_calibration()
    v12_path = os.path.join(OUT, "ladder_calibration_v12.json")
    cal_v12 = load_fitted_calibration(v12_path)

    dec_r3, aa_r3, seq_r3, gold_seq = decisions_for(cal_r3, cases, personas)
    dec_v12, aa_v12, seq_v12, _ = decisions_for(cal_v12, cases, personas)
    kappa_r3 = round(cohens_kappa(seq_r3, gold_seq), 4)
    kappa_v12 = round(cohens_kappa(seq_v12, gold_seq), 4)
    rev_pro_r3 = sum(1 for m, g in zip(seq_r3, gold_seq) if m == "REVIEW_REQUIRED" and g == "PROHIBIT")
    rev_pro_v12 = sum(1 for m, g in zip(seq_v12, gold_seq) if m == "REVIEW_REQUIRED" and g == "PROHIBIT")
    moved = sum(1 for a, b in zip(seq_r3, seq_v12) if a != b)

    out = {
        "note": "verdicts recomputed on the same (case, persona) pairs with two ladders; "
                "confidence fixed at the persona mean (approximation, stated in the report)",
        "r3_fitted_parameters": {"bar_base": cal_r3.bar_base, "prohibit_margin": cal_r3.prohibit_margin,
                                 "ratio_prohibit": cal_r3.ratio_prohibit, "ratio_review": cal_r3.ratio_review,
                                 "prohibit_stakes_min": cal_r3.prohibit_stakes_min,
                                 "critical_prohibit_gap": cal_r3.critical_prohibit_gap,
                                 "stakes_veto_min": cal_r3.stakes_veto_min},
        "r4_v12_fitted_parameters": {"bar_base": cal_v12.bar_base, "prohibit_margin": cal_v12.prohibit_margin,
                                     "ratio_prohibit": cal_v12.ratio_prohibit, "ratio_review": cal_v12.ratio_review,
                                     "prohibit_stakes_min": cal_v12.prohibit_stakes_min,
                                     "critical_prohibit_gap": cal_v12.critical_prohibit_gap,
                                     "stakes_veto_min": cal_v12.stakes_veto_min},
        "decision_distribution_r3_fit": dict(dec_r3),
        "decision_distribution_r4_v12_fit": dict(dec_v12),
        "pairs": len(seq_r3),
        "pairs_whose_verdict_changes": moved,
        "share_pairs_whose_verdict_changes": round(moved / len(seq_r3), 4),
        "kappa_model_vs_gold_r3_fit": kappa_r3,
        "kappa_model_vs_gold_v12_fit": kappa_v12,
        "REVIEW_model_vs_PROHIBIT_gold_r3_fit": rev_pro_r3,
        "REVIEW_model_vs_PROHIBIT_gold_v12_fit": rev_pro_v12,
        "mean_adequacy_r3_fit": round(float(np.mean(aa_r3)), 4),
        "mean_adequacy_v12_fit": round(float(np.mean(aa_v12)), 4),
    }
    with open(os.path.join(OUT, "corpus_v5_calibration_sensitivity.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
