"""Fit the decision-ladder thresholds of the v12 core to the gold consensus of
corpus v5, with a train/test split by domain.

The ladder is fully determined, for a given (case, persona) confrontation, by
    aa (the lower adequacy bound), ratio (residual-risk ratio), stakes,
    veto flag, material gap, hard-veto flag
plus the case attributes that enter the bar (severity, irreversibility, prudential
mode, horizon). So the fit can be done vectorially over stored fields instead of
re-running the whole arithmetic for every candidate - the fit is exact for the
threshold parameters, and deliberately does not touch the guard/cap parameters,
which are fixed by the invariant tests.

Outputs:
  Evaluacoes/r4/ladder_calibration_v12.json   fitted parameters + provenance
  Evaluacoes/r4/B5_ladder_fit_v12.json        results, clause attribution, structural variants

Run: python3 _analysis/analysis/fit_ladder_v12.py
"""
import json
import os
import sys
from collections import Counter
from itertools import product

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
from core import Calibration, SEVERITY_VALUE, PRUDENTIAL_VALUE, HORIZON_VALUE, REVERSIBILITY  # noqa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
CLASSES = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")
IDX = {c: i for i, c in enumerate(CLASSES)}
TRAIN_DOMAINS = ("SA", "JS", "IC", "FI", "PD", "GP", "IM", "ED", "MA")
TEST_DOMAINS = ("TB", "TS", "RS", "DS")


def load_pairs():
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        with open(os.path.join(R4, fn)) as fh:
            for line in fh:
                c = json.loads(line)
                cases[c["case_id"]] = c
    aa, ratio, stakes, veto, mat, hard, gold, dom, ptype, sev, irr, prud, hor, abst = ([] for _ in range(14))
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            case = cases.get(r["case_id"])
            if case is None or r.get("gold_consensus") is None:
                continue
            aa.append(r["adequacy_low"])
            ratio.append(r["risk_ratio"])
            stakes.append(r["stakes"])
            veto.append(1.0 if r["veto"] else 0.0)
            mat.append(r["material_gap"])
            hard.append(1.0 if r["hard_veto"] else 0.0)
            gold.append(r["gold_consensus"])
            dom.append(r["domain"])
            ptype.append(r.get("persona_type", "unknown"))
            sev.append(SEVERITY_VALUE[case["severity"]])
            irr.append(REVERSIBILITY[case["irreversibility"]])
            prud.append(PRUDENTIAL_VALUE[case["prudential"]])
            hor.append(HORIZON_VALUE[case["horizon"]])
            abst.append(1.0 if r.get("epistemic_abstention") else 0.0)
    A = dict(aa=np.array(aa), ratio=np.array(ratio), stakes=np.array(stakes),
             veto=np.array(veto), mat=np.array(mat), hard=np.array(hard),
             abst=np.array(abst),
             dom=np.array(dom), ptype=np.array(ptype), gold=np.array(gold),
             sev=np.array(sev), irr=np.array(irr), prud=np.array(prud), hor=np.array(hor))
    return A


def kappa(pred, truth):
    n = len(pred)
    if n == 0:
        return float("nan")
    p = np.zeros((len(CLASSES), len(CLASSES)))
    for a, b in zip(pred, truth):
        p[IDX[a], IDX[b]] += 1
    po = p.sum()
    obs = np.trace(p) / po
    row = p.sum(axis=1) / po
    col = p.sum(axis=0) / po
    exp = float((row * col).sum())
    if 1 - exp <= 1e-12:
        return 0.0
    return (obs - exp) / (1 - exp)


def bar_of(P, A):
    return np.clip(P["bar_base"] + P["bar_severity"] * A["sev"]
                   + P["bar_irreversibility"] * A["irr"]
                   + P["bar_prudential"] * A["prud"]
                   + P["bar_horizon"] * A["hor"], 0.30, 0.90)


def ladder(P, A, variant="base"):
    """Reproduce decide() for the stored quantities (no hysteresis: each pair is
    evaluated in isolation, which is the worst case for stability)."""
    bar = bar_of(P, A)
    out = np.empty(len(A["aa"]), dtype=object)
    out[A["abst"] > 0] = "ABSTAIN"          # E29 fires before the ladder
    stop = A["abst"] > 0
    categorical = (A["stakes"] >= P["prohibit_stakes_min"]) & \
                  ((not P["prohibit_needs_material"]) or (A["mat"] >= P["critical_prohibit_gap"]))
    prohib = ((A["hard"] > 0) | (categorical & ((A["aa"] <= bar - P["prohibit_margin"]) |
                                                (A["ratio"] >= P["ratio_prohibit"])))) & ~stop
    out[prohib] = "PROHIBIT"
    rest = ~prohib & ~stop
    if variant == "base":
        review = (A["aa"] <= bar) | ((A["veto"] > 0) & (A["aa"] <= bar + P["veto_slack"])) | \
                 (A["ratio"] >= P["ratio_review"])
    elif variant == "veto_needs_material":
        review = (A["aa"] <= bar) | ((A["veto"] > 0) & (A["mat"] >= P["material_gap"]) &
                                     (A["aa"] <= bar + P["veto_slack"])) | (A["ratio"] >= P["ratio_review"])
    elif variant == "stakes_band":
        # a veto at low stakes de-escalates to ALLOW_WITH_GUARDS instead of REVIEW
        low_stakes = (A["veto"] > 0) & (A["stakes"] < P["stakes_veto_min"])
        review = (A["aa"] <= bar) | ((A["veto"] > 0) & ~low_stakes & (A["aa"] <= bar + P["veto_slack"])) | \
                 (A["ratio"] >= P["ratio_review"])
        out[rest & review] = "REVIEW_REQUIRED"
        guarded = rest & ~review & ((A["aa"] <= bar + P["guards_margin"]) |
                                    (A["ratio"] >= P["ratio_guards"]) | (A["veto"] > 0))
        out[rest & ~review & guarded] = "ALLOW_WITH_GUARDS"
        out[rest & ~review & ~guarded] = "ALLOW"
        return out
    out[rest & review] = "REVIEW_REQUIRED"
    guarded = rest & ~review & ((A["aa"] <= bar + P["guards_margin"]) |
                                (A["ratio"] >= P["ratio_guards"]) | (A["veto"] > 0))
    out[rest & ~review & guarded] = "ALLOW_WITH_GUARDS"
    out[rest & ~review & ~guarded] = "ALLOW"
    return out


def attribution(P, A):
    """How many REVIEW verdicts each ladder clause is responsible for, in ladder order."""
    bar = bar_of(P, A)
    stop = A["abst"] > 0
    categorical = (A["stakes"] >= P["prohibit_stakes_min"]) & \
                  ((not P["prohibit_needs_material"]) or (A["mat"] >= P["critical_prohibit_gap"]))
    prohib = ((A["hard"] > 0) | (categorical & ((A["aa"] <= bar - P["prohibit_margin"]) |
                                                (A["ratio"] >= P["ratio_prohibit"])))) & ~stop
    rest = ~prohib & ~stop
    c1 = rest & (A["aa"] <= bar)
    c2 = rest & ~c1 & (A["veto"] > 0) & (A["aa"] <= bar + P["veto_slack"])
    c3 = rest & ~c1 & ~c2 & (A["ratio"] >= P["ratio_review"])
    return {"abstention_E29": int(stop.sum()),
           "prohibit_hard": int((A["hard"] > 0).sum()),
           "prohibit_bar_route": int((categorical & (A["aa"] <= bar - P["prohibit_margin"])).sum()),
           "prohibit_ratio_route": int((categorical & (A["ratio"] >= P["ratio_prohibit"]) &
                                        (A["aa"] > bar - P["prohibit_margin"])).sum()),
           "review_baa_below_bar": int(c1.sum()),
           "review_veto_clause": int(c2.sum()),
           "review_ratio_clause": int(c3.sum()),
           "total_review": int(c1.sum() + c2.sum() + c3.sum())}


BASE = dict(bar_base=0.55, bar_severity=0.10, bar_irreversibility=0.05, bar_prudential=0.02,
            bar_horizon=0.03, prohibit_margin=0.25, guards_margin=0.05, stakes_veto_min=0.70,
            hard_veto_delta=0.25, material_gap=0.25, critical_prohibit_gap=0.35,
            cap_base=0.40, cap_stakes_gain=0.40, prohibit_stakes_min=0.30,
            prohibit_needs_material=0, veto_slack=0.10, ratio_prohibit=0.70,
            ratio_review=0.45, ratio_guards=0.25, hysteresis=0.05)

SEARCH = {
    "bar_base": (0.30, 0.75),
    "bar_severity": (0.00, 0.25),
    "bar_irreversibility": (0.00, 0.15),
    "bar_prudential": (0.00, 0.10),
    "bar_horizon": (0.00, 0.10),
    "prohibit_margin": (0.05, 0.40),
    "guards_margin": (0.00, 0.30),
    "veto_slack": (0.00, 0.30),
    "ratio_prohibit": (0.40, 0.95),
    "ratio_review": (0.20, 0.75),
    "ratio_guards": (0.05, 0.50),
    "prohibit_stakes_min": (0.05, 0.70),
    "critical_prohibit_gap": (0.26, 0.60),
}


def main():
    A = load_pairs()
    train = np.isin(A["dom"], TRAIN_DOMAINS)
    test = np.isin(A["dom"], TEST_DOMAINS)
    print(f"pairs={len(A['aa'])} train={train.sum()} test={test.sum()}")

    At, Atst = {k: A[k][train] for k in A}, {k: A[k][test] for k in A}

    def score(P, data, variant="base"):
        pred = ladder(P, data, variant=variant)
        return kappa(pred, data["gold"]), Counter(pred)

    base_k_tr, dist = score(BASE, At)
    base_k_te, _ = score(BASE, Atst)
    print(f"baseline kappa: train={base_k_tr:.4f} test={base_k_te:.4f} dist={dict(dist)}")

    rng = np.random.default_rng(12345)
    best = dict(BASE)
    best_k = base_k_tr
    for _ in range(120):
        P = dict(BASE)
        for k, (lo, hi) in SEARCH.items():
            P[k] = float(rng.uniform(lo, hi))
        if P["critical_prohibit_gap"] <= P["material_gap"]:
            continue          # E13c validity: a categorical gate must be stricter than the material gap
        k, _ = score(P, At)
        if k > best_k:
            best_k, best = k, P

    # coordinate refinement
    grids = {
        "bar_base": np.arange(0.30, 0.76, 0.02),
        "bar_severity": np.arange(0.0, 0.26, 0.02),
        "bar_irreversibility": np.arange(0.0, 0.16, 0.02),
        "bar_prudential": np.arange(0.0, 0.11, 0.01),
        "bar_horizon": np.arange(0.0, 0.11, 0.01),
        "prohibit_margin": np.arange(0.05, 0.41, 0.02),
        "guards_margin": np.arange(0.0, 0.31, 0.02),
        "veto_slack": np.arange(0.0, 0.31, 0.02),
        "ratio_prohibit": np.arange(0.40, 0.96, 0.02),
        "ratio_review": np.arange(0.20, 0.76, 0.02),
        "ratio_guards": np.arange(0.05, 0.51, 0.02),
        "prohibit_stakes_min": np.arange(0.05, 0.71, 0.02),
        "critical_prohibit_gap": np.arange(0.26, 0.61, 0.02),
    }
    for _ in range(4):
        for k, vals in grids.items():
            cand = [(float(v), score({**best, k: float(v)}, At)[0]) for v in vals]
            v, kk = max(cand, key=lambda x: x[1])
            if kk > best_k:
                best[k] = v
                best_k = kk

    k_tr, dist_tr = score(best, At)
    k_te, dist_te = score(best, Atst)
    print(f"fitted kappa: train={k_tr:.4f} test={k_te:.4f} dist={dict(dist_tr)}")

    variants = {}
    base_tr = ladder(best, At, variant="base")
    base_te = ladder(best, Atst, variant="base")
    for v in ("base", "veto_needs_material", "stakes_band"):
        dec_tr = ladder(best, At, variant=v)
        dec_te = ladder(best, Atst, variant=v)
        variants[v] = {
            "train_kappa": round(kappa(dec_tr, At["gold"]), 4),
            "test_kappa": round(kappa(dec_te, Atst["gold"]), 4),
            "verdict_flips_vs_base_train": int(sum(a != b for a, b in zip(dec_tr, base_tr))),
            "verdict_flips_vs_base_test": int(sum(a != b for a, b in zip(dec_te, base_te))),
        }
    print("structural variants:", json.dumps(variants))

    per_domain = {}
    for d in sorted(set(A["dom"])):
        m = A["dom"] == d
        per_domain[d] = {"pairs": int(m.sum()),
                        "kappa_baseline": kappa(ladder(BASE, {k: A[k][m] for k in A}), A["gold"][m]),
                        "kappa_fitted": kappa(ladder(best, {k: A[k][m] for k in A}), A["gold"][m])}
    per_persona = {}
    for p in sorted(set(A["ptype"])):
        m = A["ptype"] == p
        if m.sum() >= 100:
            per_persona[p] = {"pairs": int(m.sum()),
                              "kappa_fitted": kappa(ladder(best, {k: A[k][m] for k in A}), A["gold"][m])}

    out = {
        "provenance": {
            "corpus": "Evaluacoes/r4/corpus_v5_confrontations.jsonl + corpus_v5_gold.jsonl",
            "pairs": int(len(A["aa"])),
            "train_domains": list(TRAIN_DOMAINS), "test_domains": list(TEST_DOMAINS),
            "search": "120 random draws over the ladder space + 4 coordinate passes",
            "seed": 12345,
            "note": "cap/guard parameters (cap_base, cap_stakes_gain, hard_veto_delta, theta) are NOT fitted: they are fixed by the invariant suite (I18, I33).",
        },
        "baseline_parameters": BASE,
        "baseline_kappa": {"train": base_k_tr, "test": base_k_te},
        "fitted_parameters": best,
        "fitted_kappa": {"train": k_tr, "test": k_te},
        "decision_distribution": {"baseline_train": dict(dist), "fitted_train": dict(dist_tr),
                                  "fitted_test": dict(dist_te)},
        "clause_attribution": attribution(best, At),
        "structural_variants": variants,
        "kappa_by_domain": per_domain,
        "kappa_by_persona_type": per_persona,
        "gold_distribution_train": dict(Counter(At["gold"])),
        "gold_distribution_test": dict(Counter(Atst["gold"])),
    }
    with open(os.path.join(R4, "ladder_calibration_v12.json"), "w") as fh:
        json.dump(out["fitted_parameters"], fh, indent=2)
    with open(os.path.join(R4, "B5_ladder_fit_v12.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: out[k] for k in ("baseline_kappa", "fitted_kappa", "clause_attribution",
                                         "structural_variants")}, indent=2))


if __name__ == "__main__":
    main()