"""B23 (Rodada 5, gate G14') - variance-based sensitivity of the v13 core.

B10 measured the v12 parameter space. v13 added four knobs that the paper claims are
"declared, not assumed": zeta (cross-pillar duty term), s (case-adaptive salience),
the coverage gate (E26') and the oversight attenuation (E11c'). Two of them are set to
zero by fiat in the canon. If a parameter set to zero is genuinely inert, its total-order
Sobol index must be zero; if it is not, the canon has an undeclared dependency. That is
the falsifiable claim this battery tests.

Method (no scipy in this environment, exactly as in B10):
  * paired Latin-hypercube swap design gives
      S1_i = E[(Y - ybar)(Y_B - ybar)] / Var(Y)      (first order)
      ST_i = 1 - E[(Y - Y_C)^2 / 2] / Var(Y)         (total order)
  * a Morris elementary-effects screen (p = 4 levels per parameter, random trajectories)
    gives mu_star (mean absolute elementary effect) and sigma (its dispersion), a cheap
    order/ranking check that must agree with the Sobol ranking.

Run:  python3 _analysis/analysis/sobol_v13_b23.py
Out:  Evaluacoes/r5/B23_sobol_v13.json
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
sys.path.insert(0, os.path.join(ROOT, "_analysis", "corpus"))

from core import (Calibration, Profile, confront, load_fitted_calibration,
                  DECISION_PERMISSIVENESS, oversight_from_facts)            # noqa: E402
from facet_registry import FACETS, DOMAINS                                  # noqa: E402
from fact_grounding import grounded_levels                                  # noqa: E402
from gen_corpus_v5 import delivery                                          # noqa: E402

R5 = os.path.join(ROOT, "Evaluacoes", "r" + os.environ.get("ETH_WCMK_ROUND", "5"))
BASE = load_fitted_calibration()

PARAMS = [
    ("zeta", 0.0, 0.10),
    ("salience_adaptation", 0.0, 2.0),
    ("coverage_gate", 0.55, 0.90),
    ("oversight_attenuation", 0.0, 1.0),
    ("gamma", 0.0, 0.30),
    ("eta", 0.0, 0.15),
    ("omega", 0.0, 0.10),
    ("rho", 0.0, 0.25),
    ("delta", 0.0, 0.15),
    ("lam_C", 0.10, 0.45),
    ("mu_C", 0.05, 0.55),
    ("theta_base", 0.45, 0.75),
]
D = len(PARAMS)
N = 1024
PANEL = 12
BOOT = 100
MORRIS_TRAJ = 200
MORRIS_P = 4
SEED = 20261109


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def build_cal(v):
    lam_c = v[9]
    lam = ((1.0 - lam_c) / 3.0, lam_c, (1.0 - lam_c) / 3.0, (1.0 - lam_c) / 3.0)
    mu_c = v[10]
    mu = ((1.0 - mu_c) / 3.0, mu_c, (1.0 - mu_c) / 3.0, (1.0 - mu_c) / 3.0)
    t = v[11]
    # the declared budget constraint is gamma+eta+omega+rho+delta+zeta <= 0.45.
    # zeta is kept at its sampled value (that is what the sweep is about); the other
    # five are rescaled so the total lands exactly on the budget.
    pen = [v[4], v[5], v[6], v[7], v[8]]
    headroom = BASE.total_penalty_budget - v[0]
    sp = sum(pen)
    if sp > headroom:
        pen = [p * headroom / sp for p in pen]
    return replace(BASE, lam=lam, mu=mu, theta=(t + 0.05, t, t, t + 0.05),
                   gamma=pen[0], eta=pen[1], omega=pen[2], rho=pen[3], delta=pen[4],
                   zeta=v[0], salience_adaptation=v[1], coverage_gate=v[2],
                   oversight_attenuation=v[3])


def make_panel(seed=SEED + 17, n=PANEL):
    """Twelve real cases from corpus v7, each paired with a persona whose level
    delivery is produced by the corpus generator itself, so the sensitivity sweep is
    run on inputs the model actually sees."""
    rng = np.random.default_rng(seed)
    cases = list(read_jsonl(os.path.join(R5, "corpus_v7_layerA.jsonl")))
    personas = [p for p in read_jsonl(os.path.join(R5, "corpus_v7_personas.jsonl"))]
    by_domain = {}
    for c in cases:
        by_domain.setdefault(c["domain"], []).append(c)
    panel = []
    for i in range(n):
        domain = DOMAINS[i % len(DOMAINS)]
        pool = by_domain[domain]
        c = pool[int(rng.integers(len(pool)))]
        p = personas[int(rng.integers(len(personas)))]
        req = c["facet_requirements"]
        declared = {f.code: delivery(f, p, req)
                    for f in FACETS if f.code not in p.get("omit", ())}
        conf = {code: float(np.clip(rng.normal(p["confidence_mu"], 0.10), 0.30, 1.0))
                for code in declared}
        panel.append((c, declared, conf))
    return panel


def _spec(c):
    from core import CaseSpec
    return CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                    c["irreversibility"], c["facet_requirements"], c["U_E"], c["R_c"],
                    tuple(c["critical_pillars"]), c["horizon"], c["conflict_pattern"],
                    "system", tuple(c["norms"]), norm_conflict=c["norm_conflict"],
                    evidence_conflict=c["evidence_conflict"], exposure=c["exposure"],
                    oversight=c.get("oversight", oversight_from_facts(c["facts"])))


OUTPUT_NAMES = ("mean_adequacy", "mean_permissiveness", "abstention_rate",
                "veto_rate", "hard_veto_rate", "mean_residual_risk", "mean_review_need")


def evaluate(v, panel):
    cal = build_cal(v)
    if cal.is_valid():
        return (0.0,) * len(OUTPUT_NAMES)
    aa, perm, abst, veto, hard, risk, review = [], [], [], [], [], [], []
    for c, declared, conf in panel:
        case = _spec(c)
        levels, _ = grounded_levels(c["facts"], c["facet_requirements"], declared, 1.0)
        r = confront(case, Profile("b23", levels, conf, "system"), cal, FACETS)
        aa.append(r["adequacy"] if r["adequacy"] is not None else 0.0)
        perm.append(float(DECISION_PERMISSIVENESS[r["decision"]]))
        abst.append(1.0 if r["decision"] == "ABSTAIN" else 0.0)
        veto.append(1.0 if r.get("veto") else 0.0)
        hard.append(1.0 if r.get("hard_veto") else 0.0)
        risk.append(float(r.get("R_r") or 0.0))
        review.append(float(r.get("review_need") or 0.0))
    return (float(np.mean(aa)), float(np.mean(perm)), float(np.mean(abst)),
            float(np.mean(veto)), float(np.mean(hard)), float(np.mean(risk)),
            float(np.mean(review)))


def scale(u):
    return [lo + u[j] * (hi - lo) for j, (_, lo, hi) in enumerate(PARAMS)]


def latin_hypercube(rng, n, d):
    out = np.empty((n, d))
    for j in range(d):
        perm = rng.permutation(n)
        out[:, j] = (perm + rng.random(n)) / n
    return out


def sobol_indices(X, Yp, panel):
    Y0 = np.array([evaluate(scale(x), panel) for x in X])
    n_out = len(OUTPUT_NAMES)
    s1_design, st_design = {}, {}
    for i in range(D):
        B = Yp.copy(); B[:, i] = X[:, i]
        s1_design[i] = np.array([evaluate(scale(x), panel) for x in B])
        C = X.copy(); C[:, i] = Yp[:, i]
        st_design[i] = np.array([evaluate(scale(x), panel) for x in C])
    res = {}
    for ci, name in enumerate(OUTPUT_NAMES):
        Y = Y0[:, ci]
        ybar = float(np.mean(Y))
        sigma2 = float(np.var(Y))
        if sigma2 <= 1e-12:
            res[name] = {"variance": 0.0,
                        "S1": {p[0]: 0.0 for p in PARAMS},
                        "ST": {p[0]: 0.0 for p in PARAMS},
                        "S1_sum": 0.0, "ST_sum": 0.0,
                        "top_ST": [p[0] for p in PARAMS[:4]]}
            continue
        S1, ST = {}, {}
        for i in range(D):
            S1[PARAMS[i][0]] = float(np.mean((Y - ybar) * (s1_design[i][:, ci] - ybar)) / sigma2)
            ST[PARAMS[i][0]] = float(1.0 - np.mean((Y - st_design[i][:, ci]) ** 2) / 2.0 / sigma2)
        S1 = {k: max(0.0, min(1.0, v)) for k, v in S1.items()}
        ST = {k: max(0.0, min(1.0, v)) for k, v in ST.items()}
        res[name] = {"variance": round(sigma2, 6),
                    "S1": {k: round(v, 4) for k, v in S1.items()},
                    "ST": {k: round(v, 4) for k, v in ST.items()},
                    "S1_sum": round(sum(S1.values()), 4),
                    "ST_sum": round(sum(ST.values()), 4),
                    "top_ST": sorted(ST, key=lambda k: -ST[k])[:4]}
    return res, [float(x) for x in np.mean(Y0, axis=0)]


def morris(panel):
    rng = np.random.default_rng(SEED + 5)
    effects = {p[0]: [] for p in PARAMS}
    for _ in range(MORRIS_TRAJ):
        levels = rng.integers(0, MORRIS_P, size=D)
        x = [lo + (hi - lo) * lv / (MORRIS_P - 1) for (_n, lo, hi), lv in zip(PARAMS, levels)]
        y0 = evaluate(x, panel)
        for i in range(D):
            lo, hi = PARAMS[i][1], PARAMS[i][2]
            nxt = (levels[i] + 1) % MORRIS_P
            x2 = list(x); x2[i] = lo + (hi - lo) * nxt / (MORRIS_P - 1)
            y1 = evaluate(x2, panel)
            effects[PARAMS[i][0]].append([(a - b) / (hi - lo) for a, b in zip(y1, y0)])
    out = {}
    for i, name in enumerate(OUTPUT_NAMES):
        rows = {p[0]: [e[i] for e in effects[p[0]]] for p in PARAMS}
        out[name] = {k: {"mu_star": round(float(np.mean(np.abs(v))), 4),
                         "sigma": round(float(np.std(v)), 4)} for k, v in rows.items()}
    return out


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    X = latin_hypercube(rng, N, D)
    Yp = latin_hypercube(rng, N, D)
    panel = make_panel()
    indices, mean_outputs = sobol_indices(X, Yp, panel)
    mor = morris(panel)
    # Canonical point: the actual declared calibration, for the reference output values.
    cal_named = {"zeta": BASE.zeta, "salience_adaptation": BASE.salience_adaptation,
                 "coverage_gate": BASE.coverage_gate, "oversight_attenuation": BASE.oversight_attenuation,
                 "gamma": BASE.gamma, "eta": BASE.eta, "omega": BASE.omega, "rho": BASE.rho,
                 "delta": BASE.delta, "lam_C": BASE.lam[1], "mu_C": BASE.mu[1],
                 "theta_base": BASE.theta[1]}
    canonical_vector = [cal_named[name] for name, _, _ in PARAMS]
    canonical_point = evaluate(canonical_vector, panel)

    out = {
        "battery": "B23",
        "question": "which v13 parameters actually move the model, and is the set-to-zero canon inert?",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "design": {"N": N, "D": D, "panel_cases": PANEL, "morris_trajectories": MORRIS_TRAJ,
                   "estimator": "paired Latin-hypercube swap (no scipy available)",
                   "parameters": [{"name": n, "lo": lo, "hi": hi,
                                   "canonical": cal_named[n]} for n, lo, hi in PARAMS]},
        "mean_outputs_at_canonical": {n: round(v, 4) for n, v in zip(OUTPUT_NAMES, canonical_point)},
        "mean_outputs_over_design": {n: round(v, 4) for n, v in zip(OUTPUT_NAMES, mean_outputs)},
        "sobol": indices,
        "morris": mor,
        "inert_check": {
            "zeta_total_order": {n: indices[n]["ST"]["zeta"] for n in OUTPUT_NAMES},
            "salience_total_order": {n: indices[n]["ST"]["salience_adaptation"] for n in OUTPUT_NAMES},
            "note": "the canon sets zeta = 0 and s = 0; ST_i measures the variance attributable "
                    "to the parameter across its declared range, not at the canonical point. "
                    "A parameter with ST > 0 is not inert in principle, only inert at the "
                    "declared value - which is why the value has to be declared, not assumed."},
        "runtime_seconds": round(time.time() - t0, 2),
    }
    with open(os.path.join(R5, "B23_sobol_v13.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({"mean_outputs_at_canonical": out["mean_outputs_at_canonical"],
                      "ST_top_by_output": {n: indices[n]["top_ST"] for n in OUTPUT_NAMES},
                      "zeta_ST": {n: indices[n]["ST"]["zeta"] for n in OUTPUT_NAMES},
                      "s_ST": {n: indices[n]["ST"]["salience_adaptation"] for n in OUTPUT_NAMES}},
                     indent=2))


if __name__ == "__main__":
    main()
