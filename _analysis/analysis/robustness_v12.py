"""B9 (noise) and B12 (temporal stability) rerun on corpus v6 with the v12 canon.

B9  Each (case, persona) pair is re-evaluated under Gaussian level noise of
    increasing sigma and under confidence decay. We record how often the verdict
    flips, how much Aa_low moves, whether the model becomes MORE conservative as
    observation quality degrades (it should), and how kappa with the panel decays.

B12 Each case is tracked over 8 time steps with a learning or degradation
    trajectory on the facets; we count verdict flips, hysteresis blocks (E13d) and
    oscillations (A -> B -> A), which is the property the hysteresis rule exists to
    prevent.

Run: python3 _analysis/analysis/robustness_v12.py
Output: Evaluacoes/r4/B9_noise_v12.json, Evaluacoes/r4/B12_temporal_v12.json
"""
import json
import os
import sys
from collections import Counter

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "corpus"))
from facet_registry import FACETS                                                   # noqa: E402
from core import (CaseSpec, Profile, confront, load_fitted_calibration,
                  DECISION_PERMISSIVENESS)                                          # noqa: E402
from gold_panels_v5 import cohens_kappa                                             # noqa: E402

CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
CAL = load_fitted_calibration(os.path.join(R4, "ladder_calibration_v12.json"))
STEPS = 8


def load_sample(every=9):
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        for line in open(os.path.join(R4, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c
    rows = []
    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        c = cases.get(r["case_id"])
        if c is None or r.get("gold_consensus") is None:
            continue
        rows.append((c, r))
    return rows[::every]


def spec_of(c, r):
    return CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                    {f.code: v for f, v in zip(FACETS, r["facet_requirements"])},
                    c["U_E"], c["R_c"], tuple(c.get("critical_pillars", ("M", "K"))),
                    c.get("horizon", "immediate"), c.get("conflict_pattern", "none"),
                    r.get("agent_layer", "system"), tuple(c.get("norms", ())),
                    norm_conflict=c.get("norm_conflict", "none"),
                    evidence_conflict=c.get("evidence_conflict", False),
                    exposure=c.get("exposure", 0.5))


def run_b9(sample, rng):
    out = {}
    sigmas = [0.02, 0.05, 0.10, 0.20]
    for sigma in sigmas:
        flips = 0
        more_permissive = 0
        more_restrictive = 0
        aa_delta = []
        dec, gold = [], []
        aa_mean = 0.0
        n_aa = 0
        for c, r in sample:
            base = confront(spec_of(c, r), Profile(r["persona"],
                                   {f.code: v for f, v in zip(FACETS, r["facet_levels"])},
                                   {f.code: v for f, v in zip(FACETS, r["facet_confidence"])},
                                   "system"), CAL)
            noisy = np.clip(np.array(r["facet_levels"]) + rng.normal(0, sigma, len(FACETS)), 0.0, 1.0)
            conf = np.clip(np.array(r["facet_confidence"]) * (1 - min(0.6, 3 * sigma)), 0.05, 1.0)
            res = confront(spec_of(c, r),
                           Profile(r["persona"], {f.code: float(v) for f, v in zip(FACETS, noisy)},
                                   {f.code: float(v) for f, v in zip(FACETS, conf)}, "system"), CAL)
            if res["decision"] != base["decision"]:
                flips += 1
            if DECISION_PERMISSIVENESS[res["decision"]] > DECISION_PERMISSIVENESS[base["decision"]]:
                more_permissive += 1
            elif DECISION_PERMISSIVENESS[res["decision"]] < DECISION_PERMISSIVENESS[base["decision"]]:
                more_restrictive += 1
            if res["adequacy_low"] is not None and base["adequacy_low"] is not None:
                aa_delta.append(res["adequacy_low"] - base["adequacy_low"])
                aa_mean += res["adequacy_low"]
                n_aa += 1
            dec.append(res["decision"]); gold.append(r["gold_consensus"])
        out[f"sigma_{sigma}"] = {
            "pairs": len(sample),
            "verdict_flip_rate": round(flips / len(sample), 4),
"became_more_permissive_rate": round(more_permissive / len(sample), 4),
            "became_more_restrictive_rate": round(more_restrictive / len(sample), 4),
            "mean_abs_aa_shift": round(float(np.mean(np.abs(aa_delta))), 4),
            "mean_aa_shift": round(float(np.mean(aa_delta)), 4),
            "mean_adequacy": round(aa_mean / n_aa, 4),
            "kappa_vs_panel": round(cohens_kappa(dec, gold), 4),
        }
    return {"sample": len(sample), "calibration": "fitted B5 v12", "noise": out,
            "reading": "kappa and verdict stability decay with observation noise. The test is whether "
                       "degraded observations ever make the model MORE permissive: the guard cap "
                       "and the pessimistic band should make that rare."}


def run_b12(sample, rng):
    trajectories = []
    flips = oscillations = hysteresis_blocks = 0
    per_step = Counter()
    for c, r in sample:
        direction = 1 if rng.random() < 0.5 else -1
        start = np.array(r["facet_levels"], dtype=float)
        prev = None
        seq = []
        for t in range(STEPS):
            drift = direction * 0.05 * t
            levels = np.clip(start + drift + rng.normal(0, 0.03, len(FACETS)), 0.0, 1.0)
            res = confront(spec_of(c, r),
                           Profile(r["persona"], {f.code: float(v) for f, v in zip(FACETS, levels)},
                                   {f.code: v for f, v in zip(FACETS, r["facet_confidence"])}, "system"),
                           CAL, previous_decision=prev)
            seq.append(res["decision"])
            if prev is not None and res["decision"] != prev:
                flips += 1
                if DECISION_PERMISSIVENESS[res["decision"]] > DECISION_PERMISSIVENESS[prev]:
                    hysteresis_blocks += 1
            per_step[res["decision"]] += 1
            prev = res["decision"]
        for i in range(len(seq) - 2):
            if seq[i] == seq[i + 2] and seq[i] != seq[i + 1]:
                oscillations += 1
        trajectories.append(seq)
    return {"cases_tracked": len(sample), "steps": STEPS,
            "verdict_changes_total": flips,
            "changes_per_case": round(flips / len(sample), 3),
            "permissive_transitions_blocked_by_hysteresis_note": hysteresis_blocks,
            "A_B_A_oscillations": oscillations,
            "final_verdict_distribution": dict(per_step),
            "sample_first_5_trajectories": trajectories[:5]}


def main():
    rng = np.random.default_rng(20261107)
    sample = load_sample(every=9)
    b9 = run_b9(sample, rng)
    b12 = run_b12(sample, np.random.default_rng(777))
    json.dump(b9, open(os.path.join(R4, "B9_noise_v12.json"), "w"), indent=2)
    json.dump(b12, open(os.path.join(R4, "B12_temporal_v12.json"), "w"), indent=2)
    print(json.dumps({"sample_pairs": len(sample),
                      "noise_kappa": {k: v["kappa_vs_panel"] for k, v in b9["noise"].items()},
                      "flip_rates": {k: v["verdict_flip_rate"] for k, v in b9["noise"].items()},
                      "temporal": {k: v for k, v in b12.items() if isinstance(v, (int, float, dict)) and k != "sample_first_5_trajectories"}},
                     indent=2))


if __name__ == "__main__":
    main()
