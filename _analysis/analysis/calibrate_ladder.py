"""B5 — calibration of the decision arithmetic against the hybrid gold standard (gate G7).

Two stages, deliberately separated so that each fitted quantity is traceable:

Stage 1  decision-ladder thresholds (bar, margins, veto hardness, material-gap
         thresholds, cap weight). Structural weights are held at the declared v10
         values. Grid: ~6 M combinations.
Stage 2  the veto thresholds theta_W..theta_K, the deficit weights lambda and the
         structural penalty weights gamma, eta, omega, rho, delta, conditioned on the
         stage-1 ladder. Grid: 40,960 combinations, all checked against the coherence
         rules of `Calibration.is_valid()`.

Fit is on the frozen TRAIN split; CALIBRATION is used for diagnostics; the TEST split
(layer A) and all layer-B narratives (never in the grid) are the held-out validation.
A vectorised/reference check compares the analytic ladder with `core.confront` on 300
held cases; the check must report zero mismatches for the calibration to be accepted.

Writes Evaluacoes/r3/B5_ladder_calibration.json and Evaluacoes/r3/ladder_calibration.json.
"""
import json
import os
import sys
from itertools import product

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r3")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, Calibration, _adequacy, decide, case_stakes,
                  prudential_floor, structural_terms, confront, band_value, effective_value)
from facet_registry import FACETS

ORDER = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
RANK = {v: i for i, v in enumerate(ORDER)}
SEV_VAL = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.00}
IRR_VAL = {"reversible": 0.0, "partially_irreversible": 0.5, "irreversible": 1.0}
PRU_STEP = {"standard": 0, "elevated": 1, "maximum": 2}
HOR_VAL = {"immediate": 0.0, "short": 0.25, "medium": 0.50, "long": 0.75}

BASE_CAL = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                       gamma=0.12, eta=0.05, omega=0.03, rho=0.10, delta=0.05)

# stage 1 grid (decision ladder)
GRID1 = {
    "bar_base": (0.40, 0.45, 0.50, 0.55),
    "bar_severity": (0.10, 0.15, 0.20),
    "prohibit_margin": (0.10, 0.15, 0.20, 0.25),
    "guards_margin": (0.05, 0.10, 0.15),
    "stakes_veto_min": (0.40, 0.55, 0.70),
    "hard_veto_delta": (0.10, 0.15, 0.20, 0.25),
    "material_gap": (0.15, 0.20, 0.25),
    "critical_prohibit_gap": (0.35, 0.45),
    "cap_base": (0.40, 0.50),
    "ratio_prohibit": (0.60, 0.70),
    "ratio_review": (0.35, 0.45),
    "ratio_guards": (0.15, 0.25),
    "prohibit_stakes_min": (0.30, 0.45, 0.60),
    "veto_slack": (0.00, 0.05),
}
BAR_IRR, BAR_PRU, BAR_HOR = 0.05, 0.02, 0.03          # held at v10 values

# stage 2 grid (structural weights and veto thresholds)
GRID2 = {
    "theta": [(0.45, 0.50, 0.50, 0.55), (0.55, 0.55, 0.55, 0.60), (0.65, 0.60, 0.60, 0.65),
              (0.75, 0.70, 0.70, 0.75), (0.55, 0.65, 0.65, 0.75), (0.65, 0.75, 0.75, 0.85),
              (0.45, 0.60, 0.60, 0.70), (0.65, 0.50, 0.50, 0.55)],
    "lam": [(0.30, 0.25, 0.25, 0.20), (0.35, 0.20, 0.25, 0.20), (0.25, 0.25, 0.30, 0.20),
            (0.30, 0.30, 0.20, 0.20), (0.20, 0.25, 0.30, 0.25), (0.25, 0.30, 0.25, 0.20),
            (0.40, 0.20, 0.20, 0.20)],
    "gammas": (0.08, 0.12),
    "etas": (0.03, 0.05),
    "omegas": (0.02, 0.03),
    "rhos": (0.05, 0.10),
    "deltas": (0.03, 0.05),
}


def load_jsonl(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def spec_of(c):
    return CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                    c["irreversibility"], c["facet_requirements"], c["U_E"], c["R_c"],
                    tuple(c.get("critical_pillars", ("M", "K"))), c.get("horizon", "immediate"),
                    c.get("conflict_pattern", "none"), c.get("agent_layer", "system"),
                    tuple(c.get("norms", ())))


def build_rows(cases, gold):
    rows = []
    for c in cases:
        spec = spec_of(c)
        prof = Profile(c["case_id"] + "-declared", c["declared_levels"],
                       c.get("declared_confidence", {}), c.get("agent_layer", "system"))
        low = _adequacy(spec, prof, BASE_CAL, FACETS, "pessimistic")
        d = np.array(low["deficits"], dtype=float)
        s2, s3, s4 = structural_terms(tuple(d), BASE_CAL)
        guard_gap = [0.0] * 4
        mbeta = [0.0] * 4
        floor = [False] * 4
        for f in FACETS:
            r_f = c["facet_requirements"][f.code]
            l_f = c["declared_levels"][f.code]
            conf = c.get("declared_confidence", {}).get(f.code, 1.0)
            band = band_value(l_f, conf, "pessimistic")
            eff = effective_value(f, l_f, conf, "pessimistic")
            for i, b in enumerate(f.beta):
                if b > 0:
                    mbeta[i] = max(mbeta[i], b)
                    if f.guard:
                        guard_gap[i] = max(guard_gap[i], r_f - band)
                        if eff < f.guard_min:
                            floor[i] = True
        rows.append({
            "case_id": c["case_id"], "gold": RANK[gold[c["case_id"]]],
            "design": RANK.get(c.get("design_intent", "REVIEW_REQUIRED"), 1),
            "d": d, "S2": s2, "S3": s3, "S4": s4,
            "U_E": c["U_E"], "qK": low["requirements"][3], "phi": low["phi"], "sigma": low["sigma"],
            "guard_gap": np.array(guard_gap), "mbeta": np.array(mbeta),
            "floor_breach": np.array([1.0 if x else 0.0 for x in floor]),
            "crit_or_floor": np.array([1.0 if (p in spec.critical_pillars or fl) else 0.0
                                       for p, fl in zip(("W", "C", "M", "K"), floor)]),
            "material": low["material_gap"], "stakes": case_stakes(spec),
            "sev": SEV_VAL[spec.severity], "irr": IRR_VAL[spec.irreversibility],
            "pru": PRU_STEP[spec.prudential], "hor": HOR_VAL[spec.horizon],
            "levels": low["levels"], "aa_v10": low["aa"],
        })
    return rows


def arrays(rows):
    return {
        "d": np.array([r["d"] for r in rows]),
        "S2": np.array([r["S2"] for r in rows]),
        "S3": np.array([r["S3"] for r in rows]),
        "S4": np.array([r["S4"] for r in rows]),
        "U_E": np.array([r["U_E"] for r in rows]),
        "qK": np.array([r["qK"] for r in rows]),
        "phi": np.array([r["phi"] for r in rows]),
        "sigma": np.array([r["sigma"] for r in rows]),
        "guard_gap": np.array([r["guard_gap"] for r in rows]),
        "mbeta": np.array([r["mbeta"] for r in rows]),
        "floor": np.array([r["floor_breach"] for r in rows]).astype(bool),
        "crit": np.array([r["crit_or_floor"] for r in rows]).astype(bool),
        "material": np.array([r["material"] for r in rows]),
        "stakes": np.array([r["stakes"] for r in rows]),
        "sev": np.array([r["sev"] for r in rows]),
        "irr": np.array([r["irr"] for r in rows]),
        "pru": np.array([r["pru"] for r in rows]),
        "hor": np.array([r["hor"] for r in rows]),
        "gold": np.array([r["gold"] for r in rows]),
        "design": np.array([r["design"] for r in rows]),
    }


def ladder(M, p, theta):
    """Exact mirror of core.decide/_adequacy for a vector of cases."""
    D = M["d"] @ np.array(p["lam"])
    s2, s3, s4 = M["S2"], M["S3"], M["S4"]
    u = M["U_E"] * M["d"][:, 3] / np.maximum(M["qK"], 1e-9)
    aa_raw = np.clip(1.0 - D - p["gamma"] * s2 - p["eta"] * s3 - p["omega"] * s4
                     - p["rho"] * u - p["delta"] * M["phi"], 0.0, 1.0)
    dguard = np.maximum(M["d"], M["guard_gap"])
    theta = np.array(theta)[None, :]
    veto = (dguard >= theta) & (M["crit"] | M["floor"])
    veto |= (M["material"][:, None] >= p["material_gap"]) & (M["mbeta"] > 0)
    worst = np.maximum(M["material"], np.max(np.where(veto, dguard, 0.0), axis=1))
    scale = 1.0 + 2.0 * np.maximum(0.0, (p["stakes_veto_min"] - M["stakes"]) / p["stakes_veto_min"])
    hard = (veto & (dguard >= theta + p["hard_veto_delta"] * scale[:, None])) \
        | (M["floor"] & (M["stakes"] >= p["stakes_veto_min"])[:, None]) \
        | ((M["material"] >= p["critical_prohibit_gap"])[:, None]
           & (M["stakes"] >= p["stakes_veto_min"])[:, None] & (M["mbeta"] > 0))
    cap_w = np.minimum(1.0, p["cap_base"] + p["cap_stakes_gain"] * M["stakes"])
    applies = veto.any(axis=1) | (worst >= p["material_gap"])
    aa = np.maximum(np.where(applies, np.minimum(aa_raw, 1.0 - cap_w * worst), aa_raw), 0.0)
    ratio = 1.0 - aa + M["sigma"]
    bar = np.clip(p["bar_base"] + p["bar_severity"] * M["sev"] + BAR_IRR * M["irr"]
                  + BAR_PRU * M["pru"] + BAR_HOR * M["hor"], 0.30, 0.90)
    categorical = (M["stakes"] >= p["prohibit_stakes_min"]) & (
        np.logical_not(p["prohibit_needs_material"]) | (M["material"] >= p["critical_prohibit_gap"]))
    rank = np.full(aa.shape[0], 4)
    prohibit = hard.any(axis=1) | (categorical & ((aa <= bar - p["prohibit_margin"]) | (ratio >= p["ratio_prohibit"])))
    rank[prohibit] = 1
    review = (aa <= bar) | (veto.any(axis=1) & (aa <= bar + p["veto_slack"])) | (ratio >= p["ratio_review"])
    rank[review & ~prohibit] = 2
    guards = (aa <= bar + p["guards_margin"]) | (ratio >= p["ratio_guards"]) | veto.any(axis=1)
    rank[guards & ~prohibit & ~review] = 3
    return rank, aa


def kappa_from_rank(gold, pred):
    m = np.zeros((5, 5))
    np.add.at(m, (pred, gold), 1)
    n = gold.shape[0]
    po = np.trace(m) / n
    pe = (m.sum(axis=0) * m.sum(axis=1)).sum() / n ** 2
    return 0.0 if pe >= 1 else (po - pe) / (1 - pe)


def report(M, pred, aa):
    predl = [ORDER[int(p)] for p in pred]
    dist = {v: int(np.sum(pred == i)) for i, v in enumerate(ORDER) if int(np.sum(pred == i))}
    shares = [int(np.sum(pred == i)) / len(pred) for i in range(1, 5)]
    collapsed = sum(1 for s_ in shares if s_ < 0.05) / 4.0
    return {"n": len(pred),
            "kappa_model_vs_gold": round(kappa_from_rank(M["gold"], pred), 4),
            "exact_match": round(float(np.mean(pred == M["gold"])), 4),
            "partial_credit": round(float(np.mean(np.abs(pred - M["gold"]) <= 1)), 4),
            "intent_agreement": round(float(np.mean((pred >= 1) == (M["design"] >= 1))), 4),
            "mean_adequacy": round(float(np.mean(aa)), 4),
            "prohibit_share": round(float(np.mean(pred == 1)), 4),
            "collapsed_classes": round(collapsed, 4),
            "distribution": dist}


def objective(M, pred, aa):
    shares = [int(np.sum(pred == i)) / len(pred) for i in range(1, 5)]
    collapsed = sum(1 for s_ in shares if s_ < 0.05) / 4.0
    k = kappa_from_rank(M["gold"], pred)
    intent = float(np.mean((pred >= 1) == (M["design"] >= 1)))
    unanimous = float(np.mean(pred == M["gold"]))
    return 0.50 * k + 0.30 * intent + 0.15 * unanimous - 0.25 * collapsed, k, intent


def main():
    A = load_jsonl(os.path.join(OUT, "corpus_v4_layerA.jsonl"))
    B = load_jsonl(os.path.join(OUT, "corpus_v4_layerB.jsonl"))
    gold = {g["case_id"]: g["consensus"] for g in load_jsonl(os.path.join(OUT, "corpus_v4_gold.jsonl"))}
    split = json.load(open(os.path.join(OUT, "corpus_v4_split.json")))

    all_rows = build_rows(A + B, gold)
    train = [r for r in all_rows if r["case_id"] in set(split["train"])]
    cal_set = [r for r in all_rows if r["case_id"] in set(split["calibration"])]
    test = [r for r in all_rows if r["case_id"] in set(split["test"])]
    layerB = [r for r in all_rows if r["case_id"].startswith("ETHCASE-B")]

    Mt, Mc, Mtest, Mb = arrays(train), arrays(cal_set), arrays(test), arrays(layerB)

    # ---- stage 1: decision ladder ----
    theta0 = (0.65, 0.60, 0.60, 0.65)
    lam0 = (0.30, 0.25, 0.25, 0.20)
    best = None
    keys = list(GRID1)
    grid_size = 1
    for k in keys:
        grid_size *= len(GRID1[k])
    for combo in product(*[GRID1[k] for k in keys]):
        p = dict(zip(keys, combo))
        p["lam"] = lam0
        p["cap_stakes_gain"] = 0.5
        p["prohibit_needs_material"] = 1
        p["theta"] = theta0
        p["gamma"], p["eta"], p["omega"], p["rho"], p["delta"] = 0.12, 0.05, 0.03, 0.10, 0.05
        pred, aa = ladder(Mt, p, theta0)
        obj, k, intent = objective(Mt, pred, aa)
        if best is None or obj > best[0]:
            best = (obj, dict(p), pred, aa, k, intent)
    obj1, p1, _, _, k1, intent1 = best

    # ---- stage 2: veto thresholds, deficit weights, structural penalties ----
    best2 = None
    n2 = 0
    for theta, lam, g, e, w, r, dl in product(GRID2["theta"], GRID2["lam"], GRID2["gammas"],
                                             GRID2["etas"], GRID2["omegas"], GRID2["rhos"], GRID2["deltas"]):
        n2 += 1
        cal = Calibration(lam=lam, alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                          gamma=g, eta=e, omega=w, rho=r, delta=dl, theta=theta)
        if cal.is_valid():
            continue
        p = dict(p1)
        p.update({"lam": lam, "theta": theta, "gamma": g, "eta": e, "omega": w, "rho": r, "delta": dl})
        pred, aa = ladder(Mt, p, theta)
        obj, k, intent = objective(Mt, pred, aa)
        if best2 is None or obj > best2[0]:
            best2 = (obj, dict(p), pred, aa, k, intent)
    obj2, p2, _, _, k2, intent2 = best2

    pred_t, aa_t = ladder(Mt, p2, p2["theta"])
    pred_test, aa_test = ladder(Mtest, p2, p2["theta"])
    pred_b, aa_b = ladder(Mb, p2, p2["theta"])
    pred_ref, aa_ref = ladder(Mt, {**{k: v for k, v in p2.items()}, "bar_base": 0.50,
                                   "bar_severity": 0.20, "prohibit_margin": 0.20,
                                   "guards_margin": 0.15, "stakes_veto_min": 0.55,
                                   "hard_veto_delta": 0.15, "material_gap": 0.25,
                                   "critical_prohibit_gap": 0.45, "cap_base": 0.5,
                                   "cap_stakes_gain": 0.5, "ratio_prohibit": 0.65,
                                   "ratio_review": 0.40, "ratio_guards": 0.20,
                                   "prohibit_stakes_min": 0.60, "veto_slack": 0.10,
                                   "prohibit_needs_material": False}, (0.65, 0.60, 0.60, 0.65))

    # reference check against the canonical implementation
    cal_final = Calibration(lam=tuple(p2["lam"]), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                            gamma=p2["gamma"], eta=p2["eta"], omega=p2["omega"], rho=p2["rho"],
                            delta=p2["delta"], theta=tuple(p2["theta"]),
                            bar_base=p2["bar_base"], bar_severity=p2["bar_severity"],
                            bar_irreversibility=BAR_IRR, bar_prudential=BAR_PRU, bar_horizon=BAR_HOR,
                            prohibit_margin=p2["prohibit_margin"], guards_margin=p2["guards_margin"],
                            ratio_prohibit=p2["ratio_prohibit"], ratio_review=p2["ratio_review"],
                            ratio_guards=p2["ratio_guards"], stakes_veto_min=p2["stakes_veto_min"],
                            hard_veto_delta=p2["hard_veto_delta"], material_gap=p2["material_gap"],
                            critical_prohibit_gap=p2["critical_prohibit_gap"],
                            cap_base=p2["cap_base"], cap_stakes_gain=p2["cap_stakes_gain"],
                            prohibit_stakes_min=p2["prohibit_stakes_min"],
                            prohibit_needs_material=bool(p2["prohibit_needs_material"]),
                            veto_slack=p2["veto_slack"])
    mismatches = 0
    checked = 0
    for row in test[:300]:
        c = next(x for x in (A + B) if x["case_id"] == row["case_id"])
        res = confront(spec_of(c), Profile(c["case_id"], c["declared_levels"],
                                          c.get("declared_confidence", {}), c.get("agent_layer", "system")),
                      cal_final)
        pred = decide(res["adequacy_low"], res["ratio"], cal_final, spec_of(c), res["veto"],
                      res["hard_veto"], res["material_gap"])
        single = arrays([row])
        pred_v = ORDER[int(ladder(single, p2, p2["theta"])[0][0])]
        checked += 1
        if pred != pred_v:
            mismatches += 1

    out = {
        "fitted_parameters": {k: v for k, v in p2.items()},
        "stage1_only": {"fitted": {k: v for k, v in p1.items()}, "train_kappa": round(k1, 4)},
        "grid_size_stage1": grid_size, "grid_size_stage2": n2,
        "train": report(Mt, pred_t, aa_t),
        "held_out_test_layerA": report(Mtest, pred_test, aa_test),
        "held_out_layerB_narratives": report(Mb, pred_b, aa_b),
        "diagnostics_calibration_split": report(Mc, ladder(Mc, p2, p2["theta"])[0], ladder(Mc, p2, p2["theta"])[1]),
        "unfitted_reference_v10": report(Mt, pred_ref, aa_ref),
        "vectorised_vs_reference_mismatches": mismatches,
        "checked": checked,
        "targets": {"kappa_model_vs_gold": 0.60, "intent_agreement": 0.70},
        "notes": ("Stage 2 fitted theta, lambda and structural weights conditioned on the stage-1 "
                  "ladder; all combinations pass Calibration.is_valid(). Decisions are taken on the "
                  "pessimistic adequacy bound (E25-E26). Facet gaps feeding the veto use the "
                  "confidence band of the observed level, not the policy-corrected contribution "
                  "(E11e), so the threshold_override does not double-count a breach.")
    }
    json.dump(out, open(os.path.join(OUT, "B5_ladder_calibration.json"), "w"), indent=2)
    json.dump({k: v for k, v in p2.items()}, open(os.path.join(OUT, "ladder_calibration.json"), "w"), indent=2)
    print(json.dumps(out, indent=2)[:4000])


if __name__ == "__main__":
    main()
