"""B6 - variance-based sensitivity of the v11 core (gate G6').

No scipy/SALib is available, so the indices are computed with a stratified
(Latin-hypercube) Monte-Carlo estimator:

  first-order Sobol index   S1_i = Var(E[Y | x_i]) / Var(Y)
    estimated by binning the N samples of x_i into K strata and correcting the
    bin-mean variance for sampling inflation:  Var_bins_corrected = Var_bins - sigma^2/K

  total-order screening     Morris elementary effects (EE_i = f(x + h e_i) - f(x)),
    reported as mu_star = mean|EE| and sigma = std(EE). Interaction presence is
    indicated by sigma > 0.

Output is the sensitivity of the *mean adequacy over a fixed scenario panel* with
respect to the 14 calibration parameters.

Run:  python3 _analysis/analysis/sobol_morris_v11.py
Out:  Evaluacoes/r3/B6_sensitivity_v11.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "formal_core"))
from core import (CaseSpec, Profile, Calibration, confront, requirement_for,
                  DECISION_PERMISSIVENESS)
from facet_registry import FACETS, DOMAINS

N = 8192          # parameter samples (gate requirement: >= 8192)
K_BINS = 16
N_PANEL = 60
MORRIS_TRAJECTORIES = 400
MORRIS_STEPS = 13
MORRIS_DELTA = 0.05
SEED = 20261102

# name -> (low, high) of the sampling range
PARAMS = [
    ("lam_W", 0.15, 0.45), ("lam_C", 0.15, 0.40), ("lam_M", 0.15, 0.40),
    ("gamma", 0.00, 0.25), ("eta", 0.00, 0.12), ("omega", 0.00, 0.10),
    ("rho", 0.00, 0.25), ("delta", 0.00, 0.15),
    ("theta_W", 0.45, 0.80), ("theta_C", 0.45, 0.80),
    ("theta_M", 0.45, 0.80), ("theta_K", 0.45, 0.80),
    ("bar_base", 0.35, 0.65), ("bar_severity", 0.00, 0.35),
]
D = len(PARAMS)


def latin_hypercube(rng, n, d):
    """Standard LHS: one point per stratum in each dimension, randomly paired."""
    out = np.empty((n, d))
    for j in range(d):
        perm = rng.permutation(n)
        out[:, j] = (perm + rng.random(n)) / n
    return out


def make_panel(seed=SEED, n=N_PANEL):
    r = np.random.default_rng(seed + 7)
    panel = []
    for i in range(n):
        domain = str(r.choice(DOMAINS))
        case = CaseSpec(f"SEN-{i:04d}", domain,
                        str(r.choice(("low", "medium", "high", "critical"))),
                        str(r.choice(("standard", "elevated", "maximum"))),
                        str(r.choice(("reversible", "partially_irreversible", "irreversible"))),
                        {}, float(r.random()), float(0.3 + 0.7 * r.random()),
                        tuple(sorted(r.choice(["W", "C", "M", "K"], size=int(r.integers(1, 4))))),
                        str(r.choice(("immediate", "short", "medium", "long"))),
                        "none")
        case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
        scores = {}
        conf = {}
        for f in FACETS:
            crit = f.criticality.get(domain, 2)
            scores[f.code] = float(np.clip(r.normal(case.facet_requirements[f.code] - 0.10, 0.18), 0.05, 1.0))
            conf[f.code] = float(np.clip(r.normal(0.85, 0.10), 0.4, 1.0))
        panel.append((case, Profile(f"sen-{i:04d}", scores, conf)))
    return panel


def build_cal(vec):
    lam_w, lam_c, lam_m = vec[0], vec[1], vec[2]
    lam_k = 0.20
    total = lam_w + lam_c + lam_m + lam_k
    lam = tuple(v / total for v in (lam_w, lam_c, lam_m, lam_k))
    # the declared calibration coherence rule caps gamma+eta+omega+rho+delta at 0.35,
    # so sampled weights are rescaled onto that budget: the sweep explores the
    # *relative* share of each structural term, not an unbounded absolute magnitude.
    BUDGET = 0.35
    raw = [vec[3], vec[4], vec[5], vec[6], vec[7]]
    s = sum(raw)
    if s > BUDGET:
        raw = [v * BUDGET / s for v in raw]
    return Calibration(lam=lam, alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                       gamma=raw[0], eta=raw[1], omega=raw[2], rho=raw[3], delta=raw[4],
                       theta=(vec[8], vec[9], vec[10], vec[11]),
                       bar_base=vec[12], bar_severity=vec[13],
                       bar_irreversibility=0.05, bar_prudential=0.02, bar_horizon=0.03)


def evaluate(vec, panel):
    """Return (mean adequacy, mean decision permissiveness, veto firing rate,
    mean residual risk) for a parameter vector. A tuple, not None, unless the
    calibration is incoherent."""
    cal = build_cal(vec)
    if cal.is_valid():        # is_valid() returns the list of coherence errors
        return None
    res = [confront(c, p, cal) for c, p in panel]
    adq = [r["adequacy"] for r in res if r.get("adequacy") is not None]
    perm = [DECISION_PERMISSIVENESS[r["decision"]] for r in res if r.get("decision")]
    veto = [1.0 if r.get("veto") else 0.0 for r in res]
    hard = [1.0 if r.get("hard_veto") else 0.0 for r in res]
    risk = [r["R_r"] for r in res if r.get("R_r") is not None]
    if not adq:
        return None
    return (float(np.mean(adq)), float(np.mean(perm)), float(np.mean(veto)),
            float(np.mean(hard)), float(np.mean(risk)))


def scale(vec):
    return [lo + vec[j] * (hi - lo) for j, (_, lo, hi) in enumerate(PARAMS)]


def main():
    panel = make_panel()
    rng = np.random.default_rng(SEED)
    U = latin_hypercube(rng, N, D)
    X = np.array([scale(u) for u in U])
    E = [evaluate(x, panel) for x in X]
    E = [e for e in E if e is not None]
    OUTPUT_NAMES = ("mean_adequacy", "mean_permissiveness", "veto_rate", "hard_veto_rate",
                    "mean_residual_risk")
    Ys = {name: np.array([e[i] for e in E]) for i, name in enumerate(OUTPUT_NAMES)}
    Y = Ys["mean_adequacy"]
    sigma2 = float(np.var(Y))

    def first_order(Yv):
        sig = float(np.var(Yv))
        if sig <= 0:
            return {n: 0.0 for n, _, _ in PARAMS}, 0.0
        out = {}
        for j, (name, lo, hi) in enumerate(PARAMS):
            bins = np.floor(U[:, j] * K_BINS).astype(int)
            means = [float(np.mean(Yv[bins == b])) for b in range(K_BINS) if (bins == b).sum() > 1]
            var_bins = float(np.var(means)) - sig / max(1, len(means))
            out[name] = float(max(0.0, var_bins) / sig)
        return out, float(sum(out.values()))

    sobol = {}
    for name, Yv in Ys.items():
        idx, total = first_order(Yv)
        sobol[name] = {"mean": float(np.mean(Yv)), "sd": float(np.sqrt(np.var(Yv))),
                       "first_order": idx, "first_order_sum": total}
    s1 = sobol["mean_adequacy"]["first_order"]
    s1_sum = sobol["mean_adequacy"]["first_order_sum"]

    # Morris screening: elementary effects along random one-parameter moves
    delta = MORRIS_DELTA
    m = MORRIS_STEPS
    ee = {name: [] for name, _, _ in PARAMS}
    ee_dec = {name: [] for name, _, _ in PARAMS}
    evals = 0
    for t in range(MORRIS_TRAJECTORIES):
        # grid point in [0, 1-delta] for every parameter
        base = rng.integers(0, m - 1, size=D) / (m - 1)
        y0 = evaluate(scale(base), panel)
        if y0 is None:
            continue
        evals += 1
        order = list(range(D))
        rng.shuffle(order)
        for j in order:
            nb = list(base)
            nb[j] = min(1.0, nb[j] + delta)
            y1 = evaluate(scale(nb), panel)
            evals += 1
            if y1 is not None:
                ee[PARAMS[j][0]].append(abs(y1[0] - y0[0]) / delta)
                ee_dec[PARAMS[j][0]].append(abs(y1[1] - y0[1]) / delta)
    morris = {}
    morris_dec = {}
    for name, vals in ee.items():
        if vals:
            arr = np.array(vals)
            morris[name] = {"mu_star": float(np.mean(arr)), "sigma": float(np.std(arr)),
                           "n_evals": len(arr)}
        else:
            morris[name] = {"mu_star": 0.0, "sigma": 0.0, "n_evals": 0}
    for name, vals in ee_dec.items():
        if vals:
            arr = np.array(vals)
            morris_dec[name] = {"mu_star": float(np.mean(arr)), "sigma": float(np.std(arr)),
                                "n_evals": len(arr)}
        else:
            morris_dec[name] = {"mu_star": 0.0, "sigma": 0.0, "n_evals": 0}

    out = {
        "method": "Latin-hypercube Monte-Carlo, first-order Sobol by corrected conditional variance; Morris screening for total-order/interaction",
        "n_samples": int(N), "bins": K_BINS, "panel_size": N_PANEL,
        "seed": SEED,
        "mean_adequacy_across_samples": float(np.mean(Y)),
        "sd_adequacy": float(np.sqrt(sigma2)),
        "outputs": sobol,
        "first_order": s1,
        "first_order_sum": s1_sum,
        "unexplained_share": float(max(0.0, 1.0 - s1_sum)),
        "morris_elementary_effects_adequacy": morris,
        "morris_elementary_effects_decision": morris_dec,
        "ranking_by_S1": sorted(s1.items(), key=lambda kv: -kv[1]),
    }
    path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                        "Evaluacoes", "r3", "B6_sensitivity_v11.json"))
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2)[:2500])
    print("written:", path)


if __name__ == "__main__":
    main()
