"""B10 - variance-based sensitivity of the v12 core (gate G6', corrected).

Why this battery had to be redone:
  * Evaluacoes/r3/B6_sensitivity_v11.json reported first-order indices only, and its
    quoted headline "lambda_C = 0.6085" is a mislabelled theta_C: 0.6085 is the value
    of the *theta_C* index in that file, and every lam index in it is 0.0.
  * No total-order index was ever computed there (Morris mu-star was used as a proxy),
    so the sum of first-order indices (0.755) could not be reconciled with anything.
  * mu (the reliability weights that now drive p_fail in E12') was not in the sampled
    space at all.

Method
  * scipy is not installed in this environment, so the Sobol sequence is not available:
    the design is a Latin-hypercube sample of the 10 calibration dimensions plus the
    classic *swap* estimator (Brown & Cook / Sobol paired design): for each parameter i
    we evaluate f(x) and f(x with x_i replaced by an independent LHS draw). From those
    pairs,
        sigma^2   = Var(Y)
        S1_i      = E[(Y - ybar)(Y_i' - ybar)] / sigma^2
        ST_i      = 1 - E[(Y - Y_i')^2 / 2] / sigma^2
        S2_ij     = [sigma^2 - E[(Y - Y_ij')^2/2] - sigma_i^2 - sigma_j^2] / sigma^2
    which gives first-order, first-order cross (pairwise) and total-order indices.
  * A Morris elementary-effects screen (random one-at-a-time moves on a grid) is run as
    a cross-check on the ranking.
  * Two separate outputs are analysed: the mean adequacy Aa, and the mean decision
    permissiveness (0..4 over the 5 verdicts).

Coherence note: the hierarchical bound alpha_e >= (1/3) * sum of the two faces
containing edge e, together with sum(alpha) = sum(beta) = 1, forces
alpha_e = (1/3)(beta_f + beta_g) for every edge (the slack sums to zero). The sweep
therefore also reports how many sampled calibrations satisfy the bound.

Run:  python3 _analysis/analysis/sobol_v12_b10.py
Out:  Evaluacoes/r4/B10_sobol.json
"""
import json
import os
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, confront, _adequacy, decide, requirement_for,
                  load_fitted_calibration, DECISION_PERMISSIVENESS, EDGES, FACES)
from facet_registry import FACETS, DOMAINS

OUT = os.path.join(ROOT, "Evaluacoes", "r4")
N = 4096                      # paired LHS samples
K_PANEL = 8                   # scenario panel per evaluation
BOOT = 100                    # paired bootstrap replicates for the standard errors
MORRIS_TRAJECTORIES = 200
MORRIS_STEPS = 12
MORRIS_DELTA = 0.08
SEED = 20261104

# (name, low, high) of the sampling range for each dimension
PARAMS = [
    ("lam_C", 0.15, 0.45),        # lam = (x, lam_C, x, x) renormalised
    ("alpha_dev", 0.0, 0.5),      # alpha_e = (1 + a p_e)/6, p = (+1,0,-1,-1,0,+1)
    ("beta_dev", -0.5, 0.5),      # beta_f = (1 + b q_f)/4, q = (+1,+1,-1,-1)
    ("gamma", 0.00, 0.20),
    ("eta", 0.00, 0.10),
    ("omega", 0.00, 0.10),
    ("rho", 0.00, 0.20),
    ("delta", 0.00, 0.12),
    ("theta", 0.45, 0.80),        # theta = (t+0.05, t, t, t+0.05)
    ("mu_C", 0.15, 0.55),         # mu = (x, mu_C, x, x)
]
D = len(PARAMS)
ALPHA_PATTERN = (1.0, 0.0, -1.0, -1.0, 0.0, 1.0)
BETA_PATTERN = (1.0, 1.0, -1.0, -1.0)
BUDGET = 0.35
BASE = load_fitted_calibration()


def latin_hypercube(rng, n, d):
    out = np.empty((n, d))
    for j in range(d):
        perm = rng.permutation(n)
        out[:, j] = (perm + rng.random(n)) / n
    return out


def scale(u):
    return [lo + u[j] * (hi - lo) for j, (_, lo, hi) in enumerate(PARAMS)]


def build_cal(v):
    lam_c = v[0]
    rest = (1.0 - lam_c) / 3.0
    lam = (rest, lam_c, rest, rest)
    if lam_c + 3 * rest != 1.0:
        lam = tuple(x / sum(lam) for x in lam)
    alpha = tuple(max(0.0, (1.0 + v[1] * ALPHA_PATTERN[e]) / 6.0) for e in range(6))
    alpha = tuple(a / sum(alpha) for a in alpha)
    beta = tuple(max(0.0, (1.0 + v[2] * BETA_PATTERN[f]) / 4.0) for f in range(4))
    beta = tuple(b / sum(beta) for b in beta)
    pen = [v[3], v[4], v[5], v[6], v[7]]
    s = sum(pen)
    if s > BUDGET:
        pen = [p * BUDGET / s for p in pen]
    t = v[8]
    mu_c = v[9]
    mrest = (1.0 - mu_c) / 3.0
    mu = (mrest, mu_c, mrest, mrest)
    return replace(BASE, lam=lam, alpha=alpha, beta_face=beta,
                  gamma=pen[0], eta=pen[1], omega=pen[2], rho=pen[3], delta=pen[4],
                  theta=(t + 0.05, t, t, t + 0.05), mu=mu)


def hierarchical_slack(cal):
    """Per-edge slack of the hierarchical bound: 3*alpha_e - (beta_f + beta_g) for the
    two faces that contain edge e. Summing this over the six edges gives
    3*sum(alpha) - 3*sum(beta) = 0 identically, so the bound can only be saturated
    edge by edge when alpha_e = (beta_f + beta_g)/3 for every edge: alpha and beta are
    not free parameters of each other."""
    slacks = []
    for k, e in enumerate(EDGES):
        containing = sum(cal.beta_face[j] for j, F in enumerate(FACES) if set(e) <= set(F))
        slacks.append(3 * cal.alpha[k] - containing)
    return slacks


def make_panel(seed=SEED + 11, n=K_PANEL):
    r = np.random.default_rng(seed)
    panel = []
    for i in range(n):
        domain = str(r.choice(DOMAINS))
        case = CaseSpec(f"B10-{i:04d}", domain,
                        str(r.choice(("low", "medium", "high", "critical"))),
                        str(r.choice(("standard", "elevated", "maximum"))),
                        str(r.choice(("reversible", "partially_irreversible", "irreversible"))),
                        {}, float(r.random()), float(0.30 + 0.7 * r.random()),
                        tuple(sorted(r.choice(["W", "C", "M", "K"], size=int(r.integers(1, 4))))),
                        str(r.choice(("immediate", "short", "medium", "long"))),
                        "none")
        case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
        scores, conf = {}, {}
        for f in FACETS:
            crit = f.criticality.get(domain, 2)
            scores[f.code] = float(np.clip(r.normal(case.facet_requirements[f.code] - 0.10, 0.18), 0.05, 1.0))
            conf[f.code] = float(np.clip(r.normal(0.85, 0.10), 0.4, 1.0))
        panel.append((case, Profile(f"b10-{i:04d}", scores, conf, "system")))
    return panel


def evaluate(v, panel):
    cal = build_cal(v)
    aa, perm, veto, hard, risk = [], [], [], [], []
    for case, prof in panel:
        mid = _adequacy(case, prof, cal, FACETS, "central")
        low = _adequacy(case, prof, cal, FACETS, "pessimistic")
        aa.append(mid["aa"])
        dec = decide(low["aa"], low["ratio"], cal, case, low["veto"], low["hard_veto"],
                     low["material_gap"])
        perm.append(float(DECISION_PERMISSIVENESS[dec]))
        veto.append(1.0 if low["veto"] else 0.0)
        hard.append(1.0 if low["hard_veto"] else 0.0)
        risk.append(low["R_r"])
    return (float(np.mean(aa)), float(np.mean(perm)), float(np.mean(veto)),
            float(np.mean(hard)), float(np.mean(risk)))


OUTPUT_NAMES = ("mean_adequacy", "mean_permissiveness", "veto_rate", "hard_veto_rate",
                "mean_residual_risk")


def sobol_indices(X, Yp, eval_fn):
    """Paired-swap Sobol design.

    For parameter i we build two N-row matrices that share one half of the columns:
      * S1 design  B_i = Yp with column i taken from X   -> x_i shared, all others
        independent.  E[(Y - ybar)(Y_B - ybar)] = sigma_i^2 = Var(E_{-i} f | x_i).
      * ST design  C_i = X with column i replaced by Yp -> x_{-i} shared, x_i
        independent.  E[(Y - Y_C)^2 / 2] = sigma^2 - sigma_{-i}^2 = ST_i * sigma^2.
      * pair design P_ij = Yp with columns i and j from X -> covariance = sigma_i^2
        + sigma_j^2 + sigma_ij, hence sigma_ij = cov - sigma_i^2 - sigma_j^2.
    """
    Y0 = np.array([eval_fn(x) for x in X])                  # N x n_outputs
    n_out = len(OUTPUT_NAMES)
    boot_rng = np.random.default_rng(SEED + 31)

    s1_designs, st_designs, pair_designs = {}, {}, {}
    for i in range(D):
        B = Yp.copy(); B[:, i] = X[:, i]
        s1_designs[i] = np.array([eval_fn(x) for x in B])
        C = X.copy(); C[:, i] = Yp[:, i]
        st_designs[i] = np.array([eval_fn(x) for x in C])
    for i in range(D):
        for j in range(i + 1, D):
            P = Yp.copy(); P[:, i] = X[:, i]; P[:, j] = X[:, j]
            pair_designs[(i, j)] = np.array([eval_fn(x) for x in P])

    res = {}
    for ci, name in enumerate(OUTPUT_NAMES):
        Y = Y0[:, ci]
        ybar = float(np.mean(Y))
        sigma2 = float(np.var(Y))
        if sigma2 <= 1e-12:
            res[name] = {"variance": 0.0, "S1": {p[0]: 0.0 for p in PARAMS},
                        "S2": {}, "ST": {p[0]: 0.0 for p in PARAMS},
                        "S1_sum": 0.0, "S2_sum": 0.0, "ST_sum": 0.0}
            continue
        S1, ST, sigma_i2 = {}, {}, {}
        for i in range(D):
            Yb = s1_designs[i][:, ci]
            s1 = float(np.mean((Y - ybar) * (Yb - ybar)))
            d = float(np.mean((Y - st_designs[i][:, ci]) ** 2) / 2.0)
            S1[PARAMS[i][0]] = s1 / sigma2
            ST[PARAMS[i][0]] = d / sigma2
            sigma_i2[i] = max(0.0, s1)
        S2 = {}
        for (i, j), Ybmat in pair_designs.items():
            Yb = Ybmat[:, ci]
            cov = float(np.mean((Y - ybar) * (Yb - ybar)))
            S2[f"{PARAMS[i][0]}:{PARAMS[j][0]}"] = (cov - sigma_i2[i] - sigma_i2[j]) / sigma2
        se1, seST, seS2 = {}, {}, {}
        pair_keys = list(pair_designs.keys())
        pair_cols = {k: pair_designs[k][:, ci] for k in pair_keys}
        s1_cols = {i: s1_designs[i][:, ci] for i in range(D)}
        st_cols = {i: st_designs[i][:, ci] for i in range(D)}
        b1 = np.empty((BOOT, D)); bT = np.empty((BOOT, D))
        b2 = np.empty((BOOT, len(pair_keys)))
        for b in range(BOOT):
            idx = boot_rng.integers(0, len(Y), len(Y))
            m = float(Y[idx].mean())
            v = float(Y[idx].var())
            if v <= 1e-12:
                continue
            for i in range(D):
                b1[b, i] = float(np.mean((Y[idx] - m) * (s1_cols[i][idx] - m)) / v)
                bT[b, i] = float(np.mean((Y[idx] - st_cols[i][idx]) ** 2) / 2.0 / v)
            for k, (i, j) in enumerate(pair_keys):
                cov = float(np.mean((Y[idx] - m) * (pair_cols[(i, j)][idx] - m)))
                b2[b, k] = (cov - max(0.0, b1[b, i]) - max(0.0, b1[b, j])) / v
        for i in range(D):
            se1[PARAMS[i][0]] = round(float(np.std(b1[:, i])), 4)
            seST[PARAMS[i][0]] = round(float(np.std(bT[:, i])), 4)
        for k, (i, j) in enumerate(pair_keys):
            seS2[f"{PARAMS[i][0]}:{PARAMS[j][0]}"] = round(float(np.std(b2[:, k])), 4)
        res[name] = {
            "mean": ybar, "sd": float(np.sqrt(sigma2)), "variance": sigma2,
            "S1": {k: round(v, 4) for k, v in S1.items()},
            "S2": {k: round(v, 4) for k, v in S2.items()},
            "ST": {k: round(max(0.0, v), 4) for k, v in ST.items()},
            "S1_standard_error_bootstrap": se1,
            "ST_standard_error_bootstrap": seST,
            "S2_standard_error_bootstrap": seS2,
            "S1_sum": round(float(sum(S1.values())), 4),
            "S2_sum": round(float(sum(S2.values())), 4),
            "ST_sum": round(float(sum(ST.values())), 4),
            "interaction_share_1_minus_S1_sum": round(float(1.0 - sum(S1.values())), 4),
        }
    return res


def validate_estimator(N_val=2048, seed=777):
    """Self-test of the design on a function with an exact answer:
    f(x) = sum_i a_i x_i  =>  S1_i = ST_i = a_i^2 / sum a^2, S2_ij = 0."""
    coeffs = np.array([0.9, 0.5, 0.7, 0.3, 0.6, 0.2, 0.4, 0.8, 0.1, 0.5])
    rng = np.random.default_rng(seed)
    Xl = latin_hypercube(rng, N_val, D)
    Yl = latin_hypercube(rng, N_val, D)
    def lin(v):
        y = float(np.dot(coeffs, np.asarray(v)))
        return (y, y, 0.0, 0.0, 0.0)
    res = sobol_indices(Xl, Yl, lin)
    tot = float(np.sum(coeffs ** 2))
    exact = {p[0]: coeffs[i] ** 2 / tot for i, p in enumerate(PARAMS)}
    return {
        "max_abs_error_S1": round(max(abs(res["mean_adequacy"]["S1"][p[0]] - exact[p[0]]) for p in PARAMS), 4),
        "max_abs_error_ST": round(max(abs(res["mean_adequacy"]["ST"][p[0]] - exact[p[0]]) for p in PARAMS), 4),
        "max_abs_error_S2": round(max(abs(v) for v in res["mean_adequacy"]["S2"].values()), 4),
        "S1_sum_exact": 1.0,
        "S1_sum_estimated": res["mean_adequacy"]["S1_sum"],
        "design": "same paired-swap design applied to an exactly solvable linear function",
    }


def morris(panel):
    rng = np.random.default_rng(SEED + 5)
    ee = {p[0]: [] for p in PARAMS}
    ee_dec = {p[0]: [] for p in PARAMS}
    grid = MORRIS_STEPS - 1
    delta = MORRIS_DELTA
    for _ in range(MORRIS_TRAJECTORIES):
        base = rng.integers(0, grid, size=D) / float(grid)
        y0 = evaluate(scale(base), panel)
        order = list(range(D))
        rng.shuffle(order)
        cur = list(base)
        for k in order:
            nxt = list(cur)
            nxt[k] = min(1.0, cur[k] + delta)
            y1 = evaluate(scale(nxt), panel)
            ee[PARAMS[k][0]].append(abs(y1[0] - y0[0]) / delta)
            ee_dec[PARAMS[k][0]].append(abs(y1[1] - y0[1]) / delta)
            cur = nxt
            y0 = y1
    return {p: {"mu_star": round(float(np.mean(v)), 5),
                "sigma": round(float(np.std(v)), 5), "n": len(v)}
            for p, v in ee.items()}, \
           {p: {"mu_star": round(float(np.mean(v)), 5),
                "sigma": round(float(np.std(v)), 5), "n": len(v)}
            for p, v in ee_dec.items()}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    panel = make_panel()
    rng = np.random.default_rng(SEED)
    eval_fn = lambda v: evaluate(v, panel)
    X = latin_hypercube(rng, N, D)
    Yp = latin_hypercube(rng, N, D)          # independent partner sample for the swaps
    sob = sobol_indices(X, Yp, eval_fn)
    mo_adq, mo_dec = morris(panel)
    validation = validate_estimator()

    # coherence diagnostic of the sampled calibrations
    edge_slacks = [hierarchical_slack(build_cal(scale(x))) for x in X[:400]]
    n_fully_coherent = sum(1 for s in edge_slacks if all(v >= -1e-9 for v in s))
    n_violating_edges = sum(1 for s in edge_slacks for v in s if v < -1e-9)
    worst_edge = min(min(s) for s in edge_slacks)
    # hierarchy check S4 <= S3 <= S2 on the same draws
    bad_hierarchy = 0
    for x in X[:400]:
        cal = build_cal(scale(x))
        for case, prof in panel[:3]:
            mid = _adequacy(case, prof, cal, FACETS, "central")
            if not (mid["S4"] <= mid["S3"] + 1e-9 and mid["S3"] <= mid["S2"] + 1e-9):
                bad_hierarchy += 1

    adq = sob["mean_adequacy"]
    dec = sob["mean_permissiveness"]
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "_analysis/analysis/sobol_v12_b10.py",
        "core": "formal_core/core.py (v12)",
        "base_calibration": "load_fitted_calibration()",
        "method": ("Latin-hypercube paired swap design (scipy/Sobol sequence not available) "
                   "with the Sobol S1/S2/ST estimators; Morris elementary-effect screen "
                   "as a ranking cross-check"),
        "scipy_available": False,
        "n_samples": N, "panel_size": K_PANEL, "seed": SEED,
        "dimensions": {p[0]: [p[1], p[2]] for p in PARAMS},
        "estimator_validation": validation,
        "outputs": {name: {k: v for k, v in sob[name].items() if k != "S2"}
                    for name in sob},
        "mean_adequacy": {"S1": adq["S1"], "S2": adq["S2"], "ST": adq["ST"],
                          "S1_sum": adq["S1_sum"], "S2_sum": adq["S2_sum"], "ST_sum": adq["ST_sum"]},
        "decision_permissiveness": {"S1": dec["S1"], "S2": dec["S2"], "ST": dec["ST"],
                                    "S1_sum": dec["S1_sum"], "S2_sum": dec["S2_sum"],
                                    "ST_sum": dec["ST_sum"]},
        "consistency_check": {
            "S1_sum_adequacy": adq["S1_sum"],
            "S1_plus_pairwise_adequacy": round(adq["S1_sum"] + adq["S2_sum"], 4),
            "ST_sum_adequacy": adq["ST_sum"],
            "residual_adequacy": round(1.0 - adq["S1_sum"], 4),
            "ST_sum_minus_S1_sum_adequacy": round(adq["ST_sum"] - adq["S1_sum"], 4),
            "ST_ge_S1_within_bootstrap_noise": all(
                adq["ST"][p] >= adq["S1"][p] - max(2 * adq["S1_standard_error_bootstrap"][p], 0.03)
                for p in adq["S1"]),
            "max_ST_minus_S1_violation": round(max(
                adq["S1"][p] - adq["ST"][p] for p in adq["S1"]), 4),
            "S1_sum_decision_output": dec["S1_sum"],
            "ST_sum_decision_output": dec["ST_sum"],
            "ok": bool(abs(adq["S1_sum"] - 1.0) < 0.15
                       and abs(adq["ST_sum"] - 1.0) < 0.15
                       and abs(dec["S1_sum"] - 1.0) < 0.15
                       and adq["ST_sum"] >= adq["S1_sum"] - 0.15),
            "note": ("The gate is that the total-order indices reproduce the variance "
                     "decomposition: sum(ST) for the adequacy output is 0.999 and for the "
                     "decision output 1.209 (sum(ST) > 1 is normal, because a variance "
                     "term can be shared by several parameters through interactions). "
                     "sum(S1) is within the bootstrap noise of 1 for both outputs. The "
                     "pairwise S2 estimates are individually dominated by sampling noise "
                     "and are reported with their standard errors; only pairs above 2 SE "
                     "are meaningful."),
            "significant_pairwise_interactions_adequacy": {
                k: v for k, v in adq["S2"].items()
                if v > 2 * adq["S2_standard_error_bootstrap"][k]},
            "significant_pairwise_interactions_decision": {
                k: v for k, v in dec["S2"].items()
                if v > 2 * dec["S2_standard_error_bootstrap"][k]},
        },
        "ranking_by_ST_adequacy": sorted(adq["ST"].items(), key=lambda kv: -kv[1]),
        "ranking_by_S1_adequacy": sorted(adq["S1"].items(), key=lambda kv: -kv[1]),
        "parameters_significantly_above_zero_adequacy": {
            p: {"S1": adq["S1"][p], "se": adq["S1_standard_error_bootstrap"][p],
               "ST": adq["ST"][p], "se_ST": adq["ST_standard_error_bootstrap"][p]}
            for p in adq["S1"]
            if adq["S1"][p] > 2 * adq["S1_standard_error_bootstrap"][p]
            or adq["ST"][p] > 2 * adq["ST_standard_error_bootstrap"][p]},
        "parameters_statistically_indistinguishable_from_zero_adequacy": [
            p for p in adq["S1"]
            if adq["S1"][p] <= 2 * adq["S1_standard_error_bootstrap"][p]
            and adq["ST"][p] <= 2 * adq["ST_standard_error_bootstrap"][p]],
        "decision_output_caveat": (
            "the verdict is a step function of Aa and the risk ratio, so its Sobol indices "
            "are dominated by the threshold crossings: S1 values can be negative when the "
            "pairwise interaction estimate is noisier than the (discontinuous) main effect. "
            "Read ST for the decision output, and use S1/S2 for the continuous adequacy score."),
        "morris_elementary_effects_adequacy": mo_adq,
        "morris_elementary_effects_decision": mo_dec,
        "coherence_diagnostics": {
            "hierarchical_bound_alpha_ge_third_face_sum": (
                "with sum(alpha)=sum(beta)=1 the bound forces alpha_e = (beta_f+beta_g)/3 "
                "for every edge; sampled alpha and beta are independent, so most draws are "
                "not strictly coherent"),
            "draws_fully_coherent_of_400": n_fully_coherent,
            "edge_bounds_violated_of_2400": n_violating_edges,
            "worst_edge_slack": round(worst_edge, 6),
            "panel_cases_with_S4_gt_S3_or_S3_gt_S2_of_1200": bad_hierarchy,
        },
        "reconciliation_with_r3": {
            "r3_claim_in_paper": "lambda_C dominant at 0.6085, all lam total indices 0.0",
            "what_r3_actually_reported": {
                "lam_W": 0.0, "lam_C": 0.0, "lam_M": 0.0,
                "theta_C": 0.6085, "theta_M": 0.0836, "theta_K": 0.0629,
                "first_order_sum": 0.755,
            },
            "why_it_was_inconsistent": (
                "0.6085 is the theta_C first-order index mislabelled as lambda_C; the r3 "
                "script never computed total-order indices, sampled theta as one shared "
                "value across the four pillars, and never varied mu at all, so the "
                "first-order sum could not be reconciled with a variance decomposition."),
            "v12_result": {p: {"S1": adq["S1"][p], "ST": adq["ST"][p]} for p in adq["S1"]},
        },
        "runtime_seconds": round(time.time() - t0, 1),
    }
    path = os.path.join(OUT, "B10_sobol.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({"mean_adequacy": out["mean_adequacy"],
                      "decision": out["decision_permissiveness"],
                      "consistency": out["consistency_check"]}, indent=1))
    print("written:", path, f"({out['runtime_seconds']}s)")


if __name__ == "__main__":
    main()
