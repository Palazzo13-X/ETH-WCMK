"""B26 (v13): how much of kappa is the model, and how much is the rubric's own priors?

The ground truth of ETH-WCMK is an operational rubric (shared kernel + three lenses),
not human raters. That makes kappa partly a measure of agreement between the model and
normative choices we wrote down. This battery perturbs those choices, recomputing BOTH
the model's verdict (when the perturbation touches the model) and the rubric's verdict,
and measures what survives:

  V0  baseline rubric (floors as declared, HARD_DUTIES as declared, gate 0.70, "defer")
  V1  every duty floor scaled x1.10   (instruments read more demanding)
  V2  every duty floor scaled x0.90   (instruments read more permissive)
  V3  categorical ("non-tradeable") set reduced to 3 duties (M1, M2, M7)
  V4  every declared duty treated as categorical
  V5  consensus replaced by lens A alone
  V6  consensus replaced by lens B alone
  V7  consensus replaced by lens C alone
  V8  coverage gate 0.70 -> 0.80 (kernel and rubric)
  V9  coverage gate 0.70 -> 0.60 (kernel and rubric)
  V10 gap mode "assume_breach" (an unreported duty counts as 0)

For each: kappa(model, consensus) with a paired-bootstrap CI on a 30.000-pair subsample
of the same pairs, the consensus distribution, the unanimity share, and the model's mean
adequacy as a control.

Run:  python3 _analysis/analysis/b26_rubric_sensitivity.py [--cases N]
Out:  Evaluacoes/r5/B26_rubric_sensitivity.json
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
R5 = os.path.join(ROOT, "Evaluacoes", "r5")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "corpus"))

from core import CaseSpec, Profile, confront, load_fitted_calibration      # noqa: E402
from facet_registry import FACETS                                          # noqa: E402
import gold_panels_v5 as GP                                                # noqa: E402

CODES = [f.code for f in FACETS]
LABELS = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
IDX = {l: i for i, l in enumerate(LABELS)}


def kappa_from_codes(a, b):
    n = len(a)
    po = float((a == b).mean())
    ca = np.bincount(a, minlength=5) / n
    cb = np.bincount(b, minlength=5) / n
    pe = float((ca * cb).sum())
    return (po - pe) / (1 - pe) if (1 - pe) != 0 else 0.0


def bootstrap_ci(a, b, n_boot=200, rng=None, size=30000):
    rng = rng or np.random.default_rng(12345)
    n = len(a)
    size = min(size, n)
    ks = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size)
        ks.append(kappa_from_codes(a[idx], b[idx]))
    ks = np.array(ks)
    return float(ks.min()), float(ks.max()), float(ks.std())


def spec_of(case):
    req = dict(case["facet_requirements"])
    return CaseSpec(case["case_id"], case["domain"], case["severity"], case["prudential"],
                    case["irreversibility"], req, case["U_E"], case["R_c"],
                    tuple(case.get("critical_pillars", ("M", "K"))), case.get("horizon", "immediate"),
                    case.get("conflict_pattern", "none"), "system", tuple(case.get("norms", ())),
                    norm_conflict=case.get("norm_conflict", "none"),
                    evidence_conflict=case.get("evidence_conflict", False),
                    exposure=case.get("exposure", 0.5),
                    oversight=case.get("oversight", "unspecified"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=0)
    args = ap.parse_args()

    t0 = time.time()
    cal = load_fitted_calibration()
    cases = {}
    for fn in ("corpus_v7_layerA.jsonl", "corpus_v7_layerB.jsonl"):
        for line in open(os.path.join(R5, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c

    rows = []
    for line in open(os.path.join(R5, "corpus_v7_confrontations.jsonl")):
        r = json.loads(line)
        if args.cases and r["case_id"] not in cases:
            continue
        rows.append(r)
    if args.cases:
        wanted = set(list(cases)[:args.cases])
        rows = [r for r in rows if r["case_id"] in wanted]

    # precompute specs and profiles once (they do not depend on the rubric variant)
    specs = {}
    for cid, c in cases.items():
        specs[cid] = spec_of(c)

    base_floors = dict(GP.DUTY_FLOORS)
    base_hard = tuple(GP.HARD_DUTIES)

    variants = [
        ("V0 baseline rubric", base_floors, base_hard, "defer", 0.70, None),
        ("V1 floors x1.10", {k: min(0.95, v * 1.10) for k, v in base_floors.items()}, base_hard, "defer", 0.70, None),
        ("V2 floors x0.90", {k: v * 0.90 for k, v in base_floors.items()}, base_hard, "defer", 0.70, None),
        ("V3 categorical set = 3 duties", base_floors, ("M1", "M2", "M7"), "defer", 0.70, None),
        ("V4 every duty categorical", base_floors, tuple(base_floors.keys()), "defer", 0.70, None),
        ("V5 consensus = lens A only", base_floors, base_hard, "defer", 0.70, "A"),
        ("V6 consensus = lens B only", base_floors, base_hard, "defer", 0.70, "B"),
        ("V7 consensus = lens C only", base_floors, base_hard, "defer", 0.70, "C"),
        ("V8 coverage gate 0.80", base_floors, base_hard, "defer", 0.80, None),
        ("V9 coverage gate 0.60", base_floors, base_hard, "defer", 0.60, None),
        ("V10 gap mode assume_breach", base_floors, base_hard, "assume_breach", 0.70, None),
    ]

    results = []
    rng = np.random.default_rng(20261109)
    for name, floors, hard, mode, gate, lens in variants:
        cal.coverage_gate = gate
        GP.DUTY_FLOORS = floors
        GP.HARD_DUTIES = hard
        GP.GAP_THRESHOLD = gate
        model_codes = np.empty(len(rows), dtype=np.int8)
        cons_codes = np.empty(len(rows), dtype=np.int8)
        cons_counter = Counter()
        unanimous = 0
        spread = 0
        aa = 0.0
        naa = 0
        for i, r in enumerate(rows):
            case = cases[r["case_id"]]
            levels = {code: v for code, v in zip(CODES, r["facet_levels"]) if v is not None}
            conf = {code: v for code, v in zip(CODES, r.get("facet_confidence", [])) if v is not None}
            res = confront(specs[r["case_id"]], Profile(r["persona"], levels, conf, "model"), cal)
            g = GP.adjudicate(specs[r["case_id"]], levels, case.get("facts", {}), mode=mode)
            v = g["consensus"] if lens is None else g["panel" + lens]
            model_codes[i] = IDX[res["decision"]]
            cons_codes[i] = IDX[v]
            cons_counter[v] += 1
            unanimous += 1 if g["unanimous"] else 0
            spread += 1 if g["spread"] >= 1 else 0
            a = res["adequacy"]
            if a is not None:
                aa += a
                naa += 1
        k = kappa_from_codes(model_codes, cons_codes)
        lo, hi, se = bootstrap_ci(model_codes, cons_codes, rng=rng)
        results.append({
            "variant": name,
            "pairs": len(rows),
            "kappa": round(k, 4),
            "ci95_paired_bootstrap": [round(lo, 4), round(hi, 4)],
            "boot_se": round(se, 4),
            "consensus_distribution": dict(cons_counter),
            "unanimous_share": round(unanimous / len(rows), 4),
            "spread_ge_1_share": round(spread / len(rows), 4),
            "mean_adequacy_model": round(aa / naa, 4),
        })
    GP.DUTY_FLOORS = base_floors
    GP.HARD_DUTIES = base_hard

    base = results[0]["kappa"]
    for r in results:
        r["delta_kappa_vs_baseline"] = round(r["kappa"] - base, 4)

    out = {
        "battery": "B26",
        "question": "how much of kappa is the model and how much is the rubric's own normative priors?",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": round(time.time() - t0, 1),
        "cases": len(cases),
        "variants": results,
        "reading": "",
    }
    json.dump(out, open(os.path.join(R5, "B26_rubric_sensitivity.json"), "w"), indent=1)
    print(json.dumps({"runtime_s": out["runtime_seconds"], "pairs": results[0]["pairs"],
                      "variants": [(r["variant"], r["kappa"], r["delta_kappa_vs_baseline"]) for r in results]},
                     indent=1))


if __name__ == "__main__":
    main()
