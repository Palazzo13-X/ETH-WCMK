"""B7 - baseline comparison battery (gate G7').

Question: does the tetrahedral model (deficits + face-lattice structural terms +
facet-level veto + stakes-aware bar + hysteresis) buy decision agreement over
simpler decision rules, or is one threshold on a weighted average enough?

Every baseline has at most one free threshold, fitted on the frozen TRAIN split by
maximising Cohen's kappa against the gold consensus. The comparison is therefore
"best achievable simple rule" vs "the model, whose ladder was fitted on the same
split", both evaluated on the frozen TEST split.

Rules compared (per the v4 plan):
  (a) the model itself, through core.confront with the fitted v12 ladder, and with
      the declared v10 defaults (unfitted) for reference;
  (b) a naive always-REVIEW_REQUIRED classifier;
  (c) a single-pillar rule (M only);
  (d) a magnitude-only rule (sum of the four pillar levels against a fixed bar);
  (e) a severity-only rule (severity band -> verdict, agent-blind).
Plus the earlier ablation-flavoured baselines (weakest pillar, fraction of unmet
duties, worst duty gap, WCMK without veto, without structural terms, two-level).

Reference labels: Evaluacoes/r3/corpus_v4_gold.jsonl (panel consensus), frozen.

Run:  python3 _analysis/analysis/b7_baselines.py
Out:  Evaluacoes/r4/B7_baselines.json
"""
import json
import os
import sys
from collections import Counter

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R3 = os.path.join(ROOT, "Evaluacoes", "r3")
OUT = os.path.join(ROOT, "Evaluacoes", "r4")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, Calibration, _adequacy, decide, case_stakes,
                  confront, load_fitted_calibration, default_calibration,
                  DECISION_PERMISSIVENESS)
from facet_registry import FACETS

ORDER = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]


def load_jsonl(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def kappa(a, b):
    vals = sorted(set(a) | set(b))
    idx = {v: i for i, v in enumerate(vals)}
    n = len(a)
    if n == 0:
        return 0.0
    m = np.zeros((len(vals), len(vals)))
    for x, y in zip(a, b):
        m[idx[x], idx[y]] += 1
    po = np.trace(m) / n
    pe = (m.sum(axis=0) * m.sum(axis=1)).sum() / n ** 2
    return 0.0 if pe >= 1 else float((po - pe) / (1 - pe))


def entropy(labels):
    _, counts = np.unique(np.array(labels), return_counts=True)
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


def make_spec(c):
    return CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                    c["irreversibility"], c["facet_requirements"], c["U_E"], c["R_c"],
                    tuple(c.get("critical_pillars", ("M", "K"))), c.get("horizon", "immediate"),
                    c.get("conflict_pattern", "none"), c.get("agent_layer", "system"),
                    tuple(c.get("norms", ())))


def rows_for(cases, gold):
    """One row per case: the quantities every baseline needs, all computed with the
    v12 core so that model and baselines read the same numbers."""
    cal = load_fitted_calibration()
    rows = []
    for c in cases:
        spec = make_spec(c)
        prof = Profile(c["case_id"] + "-declared", c["declared_levels"],
                       c.get("declared_confidence", {}), c.get("agent_layer", "system"))
        low = _adequacy(spec, prof, cal, FACETS, "pessimistic")
        mid = _adequacy(spec, prof, cal, FACETS, "central")
        unmet = sum(1 for f in FACETS
                    if c["facet_requirements"][f.code] > c["declared_levels"].get(f.code, 0.0))
        rows.append({
            "case_id": c["case_id"], "gold": gold[c["case_id"]],
            "domain": c["domain"], "severity": c["severity"],
            "irreversibility": c["irreversibility"],
            "design": c.get("design_intent"),
            "levels": low["levels"], "requirements": low["requirements"],
            "deficits": low["deficits"], "dguard": low["guarded_deficits"],
            "aa_raw": low["aa_raw"], "aa": low["aa"],
            "aa_mid": mid["aa"], "ratio": low["ratio"], "sigma": low["sigma"],
            "S2": low["S2"], "S3": low["S3"], "S4": low["S4"],
            "cal_gamma": cal.gamma, "cal_eta": cal.eta, "cal_omega": cal.omega,
            "cal_rho": cal.rho, "cal_delta": cal.delta, "u": low["u"], "phi": low["phi"],
            "veto": bool(low["veto"]), "hard": bool(low["hard_veto"]),
            "material": low["material_gap"], "stakes": case_stakes(spec),
            "bar": cal.decision_bar(spec),
            "sum_levels": float(sum(low["levels"])),
            "mean_level": float(np.mean(low["levels"])),
            "min_level": float(np.min(low["levels"])),
            "M_level": low["levels"][2], "M_req": low["requirements"][2],
            "M_deficit": low["deficits"][2],
            "unmet_duties": unmet / len(FACETS),
            "worst_facet_gap": float(max((c["facet_requirements"][f.code]
                                          - c["declared_levels"].get(f.code, 0.0)) for f in FACETS)),
        })
    return rows


def collapse(dec):
    if dec in ("ALLOW", "ALLOW_WITH_GUARDS"):
        return "PERMISSIVE"
    if dec == "REVIEW_REQUIRED":
        return "DELIBERATIVE"
    return "RESTRICTIVE"


def metrics(decisions, golds, designs=None):
    intent = None
    if designs:
        stop = {"PROHIBIT", "REVIEW_REQUIRED"}
        intent = round(float(np.mean([(d in stop) == (g in stop)
                                     for d, g in zip(decisions, designs)])), 4)
    return {"kappa": round(kappa(decisions, golds), 4),
            "exact": round(float(np.mean([a == b for a, b in zip(decisions, golds)])), 4),
            "three_band_kappa": round(kappa([collapse(d) for d in decisions],
                                           [collapse(g) for g in golds]), 4),
            "intent_agreement": intent,
            "class_entropy": round(entropy(decisions), 4),
            "distribution": {v: decisions.count(v) for v in ORDER if decisions.count(v)}}


# ------------------------------------------------------------------ rules
# Each rule takes a row and returns a verdict. `t` is the single free threshold.
RULES = {
    "BL0 magnitude: mean pillar level vs bar":
        lambda v, t: "PROHIBIT" if v["mean_level"] <= t else "ALLOW",
    "BL1 weakest pillar vs bar":
        lambda v, t: "PROHIBIT" if v["min_level"] <= t else "ALLOW",
    "BL2 fraction of unmet duties":
        lambda v, t: "PROHIBIT" if v["unmet_duties"] >= t else "ALLOW",
    "BL3 worst duty gap (max over all facets)":
        lambda v, t: "PROHIBIT" if v["worst_facet_gap"] >= t else "ALLOW",
    "BL4 worst critical-duty gap only":
        lambda v, t: "PROHIBIT" if v["material"] >= t else "ALLOW",
    "BL5 adequacy without the veto cap (ablation)":
        lambda v, t: "PROHIBIT" if v["aa_raw"] <= t else "ALLOW",
    "BL6 adequacy without structural terms (ablation)":
        lambda v, t: "PROHIBIT" if min(v["aa_raw"] + v["cal_gamma"] * v["S2"]
                                      + v["cal_eta"] * v["S3"] + v["cal_omega"] * v["S4"], 1.0) <= t
        else "ALLOW",
    "BL7 two-level model (prohibit / allow only)":
        lambda v, t: "PROHIBIT" if v["aa"] <= t else "ALLOW",
    "BL8 single pillar M only (deficit vs threshold)":
        lambda v, t: "PROHIBIT" if v["M_deficit"] >= t else "ALLOW",
    "BL9 magnitude only: sum of the four levels vs a fixed bar":
        lambda v, t: "PROHIBIT" if v["sum_levels"] <= t else "ALLOW",
    "BL10 M-pillar level only vs a fixed bar":
        lambda v, t: "PROHIBIT" if v["M_level"] <= t else "ALLOW",
}

# Rules with no free parameter: they are what they are.
FIXED_RULES = {
    "BL11 severity only (agent-blind)": lambda v: (
        "PROHIBIT" if v["severity"] == "critical"
        else "REVIEW_REQUIRED" if v["severity"] == "high"
        else "ALLOW_WITH_GUARDS" if v["severity"] == "medium" else "ALLOW"),
    "BL12 severity + irreversibility only": lambda v: (
        "PROHIBIT" if (v["severity"] == "critical" or
                       (v["severity"] == "high" and v["irreversibility"] == "irreversible"))
        else "REVIEW_REQUIRED" if v["severity"] == "high"
        else "ALLOW_WITH_GUARDS" if v["severity"] == "medium" else "ALLOW"),
    "BL13 naive single class: always REVIEW_REQUIRED": lambda v: "REVIEW_REQUIRED",
}


def fit_and_eval(name, rule, train, test, grid):
    scored = []
    for t in grid:
        dec = [rule(v, t) for v in train]
        if len(set(dec)) < 2:
            continue
        scored.append((kappa(dec, [v["gold"] for v in train]), float(t)))
    if not scored:
        return {"baseline": name, "error": "rule produced a single class on the train split"}
    best_k, best_t = max(scored)
    dec_test = [rule(v, best_t) for v in test]
    return {"baseline": name, "threshold_fit_train": round(best_t, 4),
            "train_kappa": round(best_k, 4),
            "test": metrics(dec_test, [v["gold"] for v in test],
                            [v["design"] for v in test])}


def model_decisions(cases, cal):
    dec = []
    for c in cases:
        spec = make_spec(c)
        prof = Profile(c["case_id"], c["declared_levels"],
                       c.get("declared_confidence", {}), c.get("agent_layer", "system"))
        dec.append(confront(spec, prof, cal)["decision"])
    return dec


def main():
    os.makedirs(OUT, exist_ok=True)
    A = load_jsonl(os.path.join(R3, "corpus_v4_layerA.jsonl"))
    B = load_jsonl(os.path.join(R3, "corpus_v4_layerB.jsonl"))
    gold = {g["case_id"]: g["consensus"] for g in load_jsonl(os.path.join(R3, "corpus_v4_gold.jsonl"))}
    split = json.load(open(os.path.join(R3, "corpus_v4_split.json")))
    train_ids = set(split["train"])
    test_ids = set(split["test"])

    rows = rows_for(A + B, gold)
    train = [r for r in rows if r["case_id"] in train_ids]
    test = [r for r in rows if r["case_id"] in test_ids]
    gold_test = [r["gold"] for r in test]

    results = []

    # (a) the model, run through the canonical v12 decision function.
    for label, cal in (("model: v12 core + fitted ladder (B5 fit)", load_fitted_calibration()),
                       ("model: v12 core + declared default ladder", default_calibration())):
        test_cases = [c for c in (A + B) if c["case_id"] in test_ids]
        dec = model_decisions(test_cases, cal)
        results.append({"baseline": label,
                        "calibration_repr": {k: getattr(cal, k) for k in
                                            ("lam", "alpha", "beta_face", "gamma", "eta", "omega",
                                             "rho", "delta", "theta", "mu", "bar_base",
                                             "bar_severity", "prohibit_margin", "guards_margin",
                                             "ratio_prohibit", "ratio_review", "ratio_guards",
                                             "material_gap", "critical_prohibit_gap", "hysteresis")},
                        "test": metrics(dec, gold_test, [r["design"] for r in test])})

    # baselines with one fitted threshold
    grid = np.linspace(0.10, 0.95, 86)
    for name, rule in RULES.items():
        results.append(fit_and_eval(name, rule, train, test, grid))

    # fixed rules (no free threshold)
    for name, rule in FIXED_RULES.items():
        dec = [rule(v) for v in test]
        results.append({"baseline": name, "test": metrics(dec, gold_test,
                                                          [r["design"] for r in test])})

    out = {
        "generated_from": "Evaluacoes/r3 (frozen) + core.py v12 (load_fitted_calibration)",
        "n_train": len(train), "n_test": len(test),
        "gold_distribution_test": dict(Counter(gold_test)),
        "gold_class_entropy": round(entropy(gold_test), 4),
        "results": results,
        "headline": {
            "model_kappa": results[0]["test"]["kappa"],
            "best_baseline_kappa": max((r["test"]["kappa"] for r in results[1:]
                                       if "test" in r)),
            "naive_review_required_kappa": next(r["test"]["kappa"] for r in results
                                                if "naive" in r["baseline"]),
            "severity_only_kappa": next(r["test"]["kappa"] for r in results
                                        if r["baseline"].startswith("BL11")),
        },
    }
    path = os.path.join(OUT, "B7_baselines.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"n_train={len(train)} n_test={len(test)} gold_entropy={out['gold_class_entropy']}")
    for r in results:
        if "test" not in r:
            print(f"{r['baseline']:<55}  {r.get('error', '')}")
            continue
        t = r["test"]
        print(f"{r['baseline']:<55} kappa={t['kappa']:<7} exact={t['exact']:<7} "
              f"entropy={t['class_entropy']}  {t['distribution']}")
    print("written:", path)


if __name__ == "__main__":
    main()
