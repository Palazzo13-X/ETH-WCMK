"""B13 - transfer of the fitted decision ladder to held-out domains and archetypes.

The ladder in Evaluacoes/r3/ladder_calibration.json was fitted on the frozen TRAIN
split of the v4 corpus (840 layer-A cases). Everything else - the 180-case TEST split
and the 320 layer-B narrative cases - was never in the fitting grid. This battery
answers the only question that matters for a calibration: does it transfer?

For every held-out group we report, side by side:
  * the verdict produced with the fitted ladder;
  * the verdict produced with the declared default ladder (the "without the fitted
    parameters" control);
  * Cohen's kappa and exact agreement against the panel consensus;
  * the abstention rate and the mean adequacy, so that a failure of transfer can be
    attributed either to the score (structure) or to the ladder (thresholds).

Groups:
  - by domain (13 domains);
  - by conflict_pattern (8 conflict patterns);
  - by archetype (8 case archetypes);
  - by severity band (4);
  plus the in-sample TRAIN split as the overfitting reference.

Run:  python3 _analysis/analysis/b13_transfer.py
Out:  Evaluacoes/r4/B13_transfer.json
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R3 = os.path.join(ROOT, "Evaluacoes", "r3")
OUT = os.path.join(ROOT, "Evaluacoes", "r4")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, confront, default_calibration,
                  load_fitted_calibration, DECISION_PERMISSIVENESS)
from facet_registry import FACETS

ORDER = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
THREE_BAND = {"ABSTAIN": "RESTRICTIVE", "PROHIBIT": "RESTRICTIVE",
              "REVIEW_REQUIRED": "DELIBERATIVE", "ALLOW_WITH_GUARDS": "PERMISSIVE",
              "ALLOW": "PERMISSIVE"}


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return 0.0
    idx = {l: i for i, l in enumerate(labels)}
    obs = np.zeros((len(labels), len(labels)))
    ca, cb = Counter(a), Counter(b)
    for x, y in zip(a, b):
        obs[idx[x], idx[y]] += 1
    po = obs.trace() / n
    pe = sum((ca[l] / n) * (cb[l] / n) for l in labels)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def exact(a, b):
    return float(np.mean([x == y for x, y in zip(a, b)]))


def partial(a, b):
    rank = {v: i for i, v in enumerate(ORDER)}
    return float(np.mean([1.0 if x == y else (0.5 if abs(rank[x] - rank[y]) == 1 else 0.0)
                         for x, y in zip(a, b)]))


def run(cases, cal):
    dec, aa, abstain = [], [], 0
    for c, prof, _row in cases:
        r = confront(c, prof, cal)
        dec.append(r["decision"])
        aa.append(r["adequacy"] if r["adequacy"] is not None else 0.0)
        abstain += 1 if r["decision"] == "ABSTAIN" else 0
    return dec, aa, abstain / max(1, len(cases))


def group_stats(dec_f, dec_d, gold, aa_f, aa_d, meta):
    return {
        "n": len(gold),
        "kappa_fitted": round(kappa(dec_f, gold), 4),
        "kappa_default": round(kappa(dec_d, gold), 4),
        "delta_kappa_fitted_minus_default": round(kappa(dec_f, gold) - kappa(dec_d, gold), 4),
        "exact_fitted": round(exact(dec_f, gold), 4),
        "exact_default": round(exact(dec_d, gold), 4),
        "partial_credit_fitted": round(partial(dec_f, gold), 4),
        "three_band_kappa_fitted": round(kappa([THREE_BAND[d] for d in dec_f],
                                              [THREE_BAND[g] for g in gold]), 4),
        "three_band_kappa_default": round(kappa([THREE_BAND[d] for d in dec_d],
                                                [THREE_BAND[g] for g in gold]), 4),
        "agreement_between_ladders": round(exact(dec_f, dec_d), 4),
        "mean_adequacy_fitted": round(float(np.mean(aa_f)), 4),
        "mean_adequacy_default": round(float(np.mean(aa_d)), 4),
        "abstain_rate_fitted": round(abstain_f, 4) if "abstain_f" in dir() else None,
        "verdict_distribution_fitted": dict(Counter(dec_f)),
        "verdict_distribution_default": dict(Counter(dec_d)),
        "gold_distribution": dict(Counter(gold)),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    split = json.load(open(os.path.join(R3, "corpus_v4_split.json")))
    train_ids, test_ids, calib_ids = (set(split["train"]), set(split["test"]),
                                      set(split.get("calibration", [])))
    gold = {g["case_id"]: g["consensus"] for g in read_jsonl(os.path.join(R3, "corpus_v4_gold.jsonl"))}

    cases = []
    for row in read_jsonl(os.path.join(R3, "corpus_v4_layerA.jsonl")):
        spec = CaseSpec(row["case_id"], row["domain"], row["severity"], row["prudential"],
                        row["irreversibility"], row["facet_requirements"], row["U_E"], row["R_c"],
                        tuple(row.get("critical_pillars", ("M", "K"))),
                        row.get("horizon", "immediate"), row.get("conflict_pattern", "none"),
                        row.get("agent_layer", "system"), tuple(row.get("norms", ())))
        cases.append((spec, Profile(spec.case_id, row["declared_levels"],
                                    row.get("declared_confidence", {}), "system"), row))
    for row in read_jsonl(os.path.join(R3, "corpus_v4_layerB.jsonl")):
        spec = CaseSpec(row["case_id"], row["domain"], row["severity"], row["prudential"],
                        row["irreversibility"], row["facet_requirements"], row["U_E"], row["R_c"],
                        tuple(row.get("critical_pillars", ("M", "K"))),
                        row.get("horizon", "immediate"), row.get("conflict_pattern", "none"),
                        "system", tuple(row.get("norms", ())))
        cases.append((spec, Profile(spec.case_id, row["declared_levels"],
                                    row.get("declared_confidence", {}), "system"), row))

    cal_fit = load_fitted_calibration()
    cal_def = default_calibration()

    held = [c for c in cases if c[0].case_id in test_ids or c[0].case_id.startswith("ETHCASE-B")]
    in_sample = [c for c in cases if c[0].case_id in train_ids]
    calibration_split = [c for c in cases if c[0].case_id in calib_ids]

    def block(group_cases):
        dec_f, aa_f, ab_f = run(group_cases, cal_fit)
        dec_d, aa_d, ab_d = run(group_cases, cal_def)
        g = [gold[c[0].case_id] for c in group_cases]
        stats = {
            "n": len(g),
            "kappa_fitted": round(kappa(dec_f, g), 4),
            "kappa_default": round(kappa(dec_d, g), 4),
            "delta_kappa_fitted_minus_default": round(kappa(dec_f, g) - kappa(dec_d, g), 4),
            "exact_fitted": round(exact(dec_f, g), 4),
            "exact_default": round(exact(dec_d, g), 4),
            "partial_credit_fitted": round(partial(dec_f, g), 4),
            "partial_credit_default": round(partial(dec_d, g), 4),
            "three_band_kappa_fitted": round(kappa([THREE_BAND[d] for d in dec_f],
                                                   [THREE_BAND[x] for x in g]), 4),
            "three_band_kappa_default": round(kappa([THREE_BAND[d] for d in dec_d],
                                                    [THREE_BAND[x] for x in g]), 4),
            "agreement_between_ladders": round(exact(dec_f, dec_d), 4),
            "mean_adequacy_fitted": round(float(np.mean(aa_f)), 4),
            "mean_adequacy_default": round(float(np.mean(aa_d)), 4),
            "abstain_rate_fitted": round(ab_f, 4),
            "abstain_rate_default": round(ab_d, 4),
            "verdict_distribution_fitted": dict(Counter(dec_f)),
            "verdict_distribution_default": dict(Counter(dec_d)),
            "gold_distribution": dict(Counter(g)),
        }
        return stats, dec_f, dec_d

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "_analysis/analysis/b13_transfer.py",
        "core": "formal_core/core.py (v12)",
        "fitted_ladder_source": "Evaluacoes/r3/ladder_calibration.json",
        "fitted_parameters": {k: getattr(cal_fit, k) for k in
                              ("bar_base", "bar_severity", "prohibit_margin", "guards_margin",
                               "ratio_prohibit", "ratio_review", "ratio_guards", "material_gap",
                               "critical_prohibit_gap", "cap_base", "cap_stakes_gain",
                               "stakes_veto_min", "hard_veto_delta", "prohibit_stakes_min",
                               "veto_slack", "hysteresis", "lam", "alpha", "beta_face",
                               "gamma", "eta", "omega", "rho", "delta", "theta", "mu")},
        "default_parameters": {k: getattr(cal_def, k) for k in
                               ("bar_base", "bar_severity", "prohibit_margin", "guards_margin",
                                "ratio_prohibit", "ratio_review", "ratio_guards", "material_gap",
                                "critical_prohibit_gap", "cap_base", "cap_stakes_gain",
                                "stakes_veto_min", "hard_veto_delta", "prohibit_stakes_min",
                                "veto_slack", "hysteresis", "lam", "alpha", "beta_face",
                                "gamma", "eta", "omega", "rho", "delta", "theta", "mu")},
        "held_out_definition": {
            "test_split_layerA": len(test_ids),
            "layerB_narratives": sum(1 for c in held if c[0].case_id.startswith("ETHCASE-B")),
            "total_held_out_cases": len(held),
            "in_sample_train_cases": len(in_sample),
            "calibration_split_cases": len(calibration_split),
            "note": "the ladder was fitted on the 840 TRAIN cases; TEST and layer B were never "
                    "in the fitting grid, so they are genuine held-out transfer groups.",
        },
        "overall": block(held)[0],
        "in_sample_reference": block(in_sample)[0],
        "calibration_split": block(calibration_split)[0],
        "transfer_gap_kappa": round(block(in_sample)[0]["kappa_fitted"]
                                    - block(held)[0]["kappa_fitted"], 4),
        "by_domain": {},
        "by_conflict_pattern": {},
        "by_archetype": {},
        "by_severity": {},
        "by_layer": {},
    }

    for key, getter in (("by_domain", lambda r: r["domain"]),
                        ("by_conflict_pattern", lambda r: r["conflict_pattern"]),
                        ("by_archetype", lambda r: r["archetype"]),
                        ("by_severity", lambda r: r["severity"]),
                        ("by_layer", lambda r: "layerB" if r["case_id"].startswith("ETHCASE-B")
                                              else "layerA_test")):
        groups = defaultdict(list)
        for c in held:
            groups[getter(c[2])].append(c)
        out[key] = {g: block(cs)[0] for g, cs in sorted(groups.items())}

    worst = sorted(out["by_domain"].items(), key=lambda kv: kv[1]["kappa_fitted"])[:3]
    out["headline"] = {
        "held_out_kappa_fitted": out["overall"]["kappa_fitted"],
        "held_out_kappa_default": out["overall"]["kappa_default"],
        "in_sample_kappa_fitted": out["in_sample_reference"]["kappa_fitted"],
        "transfer_gap": out["transfer_gap_kappa"],
        "weakest_domains_by_fitted_kappa": [(d, s["kappa_fitted"], s["n"]) for d, s in worst],
        "domains_where_fitted_is_worse_than_default": [
            d for d, s in out["by_domain"].items()
            if s["delta_kappa_fitted_minus_default"] < 0],
    }

    path = os.path.join(OUT, "B13_transfer.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out["headline"], indent=1))
    print(json.dumps(out["overall"], indent=1))
    for d, s in sorted(out["by_domain"].items()):
        print(f"{d:<4} n={s['n']:>4} kappa_fit={s['kappa_fitted']:>7} kappa_def={s['kappa_default']:>7} "
              f"delta={s['delta_kappa_fitted_minus_default']:>7}")
    for p, s in sorted(out["by_conflict_pattern"].items()):
        print(f"{p:<22} n={s['n']:>4} kappa_fit={s['kappa_fitted']:>7} kappa_def={s['kappa_default']:>7}")
    print("written:", path)


if __name__ == "__main__":
    main()
