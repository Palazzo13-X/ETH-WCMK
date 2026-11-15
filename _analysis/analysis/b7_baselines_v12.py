"""B7 (v12): the model against fourteen trivial baselines, per (case, persona) pair,
against the gold consensus of corpus v6.

Everything the baselines need is read from the corpus rows themselves, so the model
and the baselines consume exactly the same numbers - the "arithmetic mirror" property
the ontology gate also checks.

Split: by domain (train = SA, JS, IC, FI, PD, GP, IM, ED, MA; test = TB, TS, RS, DS),
identical to the ladder fit, so baselines and the model are compared on the same split.

Run: python3 _analysis/analysis/b7_baselines_v12.py
Output: Evaluacoes/r4/B7_baselines_v12.json
"""
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
from core import (CaseSpec, Profile, confront, default_calibration, load_fitted_calibration,  # noqa: E402
                  case_stakes, DECISION_PERMISSIVENESS)
from facet_registry import FACETS                                                        # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
ORDER = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")
TRAIN = {"SA", "JS", "IC", "FI", "PD", "GP", "IM", "ED", "MA"}
TEST = {"TB", "TS", "RS", "DS"}


def kappa(a, b):
    classes = sorted(set(a) | set(b))
    idx = {c: i for i, c in enumerate(classes)}
    m = np.zeros((len(classes), len(classes)))
    for x, y in zip(a, b):
        m[idx[x], idx[y]] += 1
    n = m.sum()
    if n == 0:
        return 0.0
    po = np.trace(m) / n
    pe = (m.sum(axis=0) * m.sum(axis=1)).sum() / n ** 2
    return 0.0 if pe >= 1 else float((po - pe) / (1 - pe))


def collapse(dec):
    if dec in ("ALLOW", "ALLOW_WITH_GUARDS"):
        return "PERMISSIVE"
    if dec == "REVIEW_REQUIRED":
        return "DELIBERATIVE"
    return "RESTRICTIVE"


def metrics(dec, gold):
    counts = np.array(list(Counter(dec).values())) / len(dec)
    ent = 0.0 if len(counts) < 2 else float(-(counts * np.log(counts)).sum())
    return {"kappa": round(kappa(dec, gold), 4),
            "exact": round(sum(a == b for a, b in zip(dec, gold)) / len(gold), 4),
            "three_band_kappa": round(kappa([collapse(d) for d in dec], [collapse(g) for g in gold]), 4),
            "distribution": {v: dec.count(v) for v in ORDER if dec.count(v)},
            "entropy": round(ent, 4)}


def load_rows():
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
        lev = r["pillar_levels"]
        req = r["facet_requirements"]
        fl = r["facet_levels"]
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                        {f.code: q for f, q in zip(FACETS, req)}, c["U_E"], c["R_c"],
                        tuple(c.get("critical_pillars", ("M", "K"))), c.get("horizon", "immediate"),
                        c.get("conflict_pattern", "none"), r.get("agent_layer", "system"),
                        tuple(c.get("norms", ())),
                        norm_conflict=c.get("norm_conflict", "none"),
                        evidence_conflict=c.get("evidence_conflict", False),
                        exposure=c.get("exposure", 0.5))
        rows.append({
            "case_id": r["case_id"], "persona": r["persona"], "domain": r["domain"],
            "severity": r["severity"], "irreversibility": c["irreversibility"],
            "gold": r["gold_consensus"], "design": c.get("design_intent"),
            "model_decision": r["decision"], "aa_low": r["adequacy_low"],
            "levels": lev, "requirements": req, "deficits": r["deficits"],
            "facet_levels": fl, "facet_confidence": r["facet_confidence"],
            "dguard": r["guarded_deficits"], "aa_raw": r["aa_raw"],
            "S2": r["S2"], "S3": r["S3"], "S4": r["S4"], "phi": r["phi"], "u": r["u"],
            "sigma": r["sigma"], "ratio": r["risk_ratio"], "material": r["material_gap"],
            "veto": bool(r["veto"]), "hard": bool(r["hard_veto"]), "stakes": r["stakes"],
            "spec": spec,
            "mean_level": float(np.mean(lev)), "min_level": float(min(lev)),
            "sum_levels": float(sum(lev)), "M_level": lev[2], "M_deficit": r["deficits"][2],
            "unmet_duties": sum(1 for q, v in zip(req, fl) if q > v) / len(FACETS),
            "worst_facet_gap": max(q - v for q, v in zip(req, fl)),
        })
    return rows


RULES = {
    "BL0 magnitude: mean pillar level vs bar": lambda v, t: "PROHIBIT" if v["mean_level"] <= t else "ALLOW",
    "BL1 weakest pillar vs bar": lambda v, t: "PROHIBIT" if v["min_level"] <= t else "ALLOW",
    "BL2 fraction of unmet duties": lambda v, t: "PROHIBIT" if v["unmet_duties"] >= t else "ALLOW",
    "BL3 worst duty gap (max over all facets)": lambda v, t: "PROHIBIT" if v["worst_facet_gap"] >= t else "ALLOW",
    "BL4 worst critical-duty gap only": lambda v, t: "PROHIBIT" if v["material"] >= t else "ALLOW",
    "BL5 adequacy without the veto cap (ablation)": lambda v, t: "PROHIBIT" if v["aa_raw"] <= t else "ALLOW",
    "BL6 adequacy without structural terms (ablation)": lambda v, t: (
        "PROHIBIT" if min(v["aa_raw"] + 0.12 * v["S2"] + 0.05 * v["S3"] + 0.03 * v["S4"], 1.0) <= t else "ALLOW"),
    "BL7 two-level model (prohibit / allow only)": lambda v, t: "PROHIBIT" if v["aa_low"] <= t else "ALLOW",
    "BL8 single pillar M only (deficit vs threshold)": lambda v, t: "PROHIBIT" if v["M_deficit"] >= t else "ALLOW",
    "BL9 magnitude only: sum of levels vs bar": lambda v, t: "PROHIBIT" if v["sum_levels"] <= t else "ALLOW",
    "BL10 M-pillar level only vs bar": lambda v, t: "PROHIBIT" if v["M_level"] <= t else "ALLOW",
    "BL14 risk ratio only (no adequacy at all)": lambda v, t: "PROHIBIT" if v["ratio"] >= t else "ALLOW",
}
FIXED = {
    "BL11 severity only (agent-blind)": lambda v: (
        "PROHIBIT" if v["severity"] == "critical" else "REVIEW_REQUIRED" if v["severity"] == "high"
        else "ALLOW_WITH_GUARDS" if v["severity"] == "medium" else "ALLOW"),
    "BL12 severity + irreversibility only": lambda v: (
        "PROHIBIT" if (v["severity"] == "critical" or
                       (v["severity"] == "high" and v["irreversibility"] == "irreversible"))
        else "REVIEW_REQUIRED" if v["severity"] == "high"
        else "ALLOW_WITH_GUARDS" if v["severity"] == "medium" else "ALLOW"),
    "BL13 always REVIEW_REQUIRED": lambda v: "REVIEW_REQUIRED",
}


def main():
    rows = load_rows()
    train = [r for r in rows if r["domain"] in TRAIN]
    test = [r for r in rows if r["domain"] in TEST]
    gold_test = [r["gold"] for r in test]

    results = []
    for label, cal in (("model: v12 core + ladder fitted on TRAIN domains (B5, r4)",
                       load_fitted_calibration(os.path.join(R4, "ladder_calibration_v12.json"))),
                       ("model: v12 core + frozen r3 ladder (the one the corpus was built with)",
                       load_fitted_calibration()),
                       ("model: v12 core + declared (uncalibrated) ladder", default_calibration())):
        dec = []
        for r in test:
            levels = {f.code: lv for f, lv in zip(FACETS, r["facet_levels"])}
            conf = {f.code: cv for f, cv in zip(FACETS, r["facet_confidence"])}
            dec.append(confront(r["spec"], Profile(r["persona"], levels, conf, "system"), cal)["decision"])
        results.append({"baseline": label, "n_test": len(test), "recompute_check": True,
                        **metrics(dec, gold_test)})
        results[-1]["note"] = "decision recomputed from the stored case spec, not from the stored row"

    grid = [i / 100.0 for i in range(1, 100)]
    for name, rule in RULES.items():
        best, best_t = None, None
        for t in grid:
            d = [rule(v, t) for v in train]
            if len(set(d)) < 2:
                continue
            k = kappa(d, [v["gold"] for v in train])
            if best is None or k > best:
                best, best_t = k, t
        if best is None:
            results.append({"baseline": name, "error": "single class on train"})
            continue
        dec = [rule(v, best_t) for v in test]
        results.append({"baseline": name, "threshold_fit_train": round(best_t, 4),
                        "train_kappa": round(best, 4), **metrics(dec, gold_test)})
    for name, rule in FIXED.items():
        dec = [rule(v) for v in test]
        results.append({"baseline": name, **metrics(dec, gold_test)})

    results.sort(key=lambda r: -r.get("kappa", -1))
    model_rows = [r for r in results if r["baseline"].startswith("model")]
    best_baseline = max((r for r in results if not r["baseline"].startswith("model")
                        and "kappa" in r), key=lambda r: r["kappa"])
    out = {"corpus": f"corpus_v{CORPUS_VER}", "n_pairs": len(rows),
           "train_pairs": len(train), "test_pairs": len(test),
           "split": "by domain: train SA JS IC FI PD GP IM ED MA / test TB TS RS DS",
           "gold_test_distribution": dict(Counter(gold_test)),
           "results": results,
           "model_vs_best_baseline": {"model_best": max(r["kappa"] for r in model_rows),
                                      "best_baseline": best_baseline["baseline"],
                                      "best_baseline_kappa": best_baseline["kappa"],
                                      "margin": round(max(r["kappa"] for r in model_rows) -
                                                     best_baseline["kappa"], 4)},
           "stored_model_kappa_test": round(kappa([r["model_decision"] for r in test], gold_test), 4)}
    with open(os.path.join(R4, "B7_baselines_v12.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out["model_vs_best_baseline"], indent=2))
    for r in results[:12]:
        print(f"{r['baseline']:<58} kappa={r.get('kappa')} exact={r.get('exact')} 3band={r.get('three_band_kappa')}")


if __name__ == "__main__":
    main()
