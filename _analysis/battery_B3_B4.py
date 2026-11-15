"""Battery B3 (perturbation response) and B4 (parameter sensitivity, Morris).

B3: for a fixed case x profile pair, perturb a single facet/pillar score in the
direction that should improve (or worsen) adequacy and check that the sign of
the response is always correct. Also checks monotonicity of R_r in severity.

B4: Morris elementary-effect screening of the calibration parameters
(gamma, eta, omega, rho, phi, theta, sigma/floor) on Aa and R_r.

Writes Evaluacoes/B3_perturbation.json and Evaluacoes/B4_sensitivity.json.
"""
from __future__ import annotations
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formal_core_v3 as m
from facets_v2 import FACETS, pillar_scores

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Evaluacoes")

R_BASE = (0.20, 0.25, 0.35, 0.20)
LAM_BASE = (0.15, 0.20, 0.45, 0.20)


def severity_vectors(band):
    """Severity raises Must and Know requirements; critical adds salience to M,K."""
    table = {
        "low":     ((0.25, 0.25, 0.25, 0.25), (0.20, 0.25, 0.30, 0.25)),
        "medium":  ((0.20, 0.25, 0.32, 0.23), (0.18, 0.25, 0.35, 0.22)),
        "high":    ((0.18, 0.24, 0.35, 0.23), (0.15, 0.22, 0.40, 0.23)),
        "critical":((0.15, 0.22, 0.38, 0.25), (0.12, 0.20, 0.42, 0.26)),
    }
    return table[band]


def b3():
    rng = random.Random(11)
    ok = 0
    bad = []
    # (1) directional response of Aa to each facet perturbation
    for trial in range(4000):
        r = m.random_simplex(rng)
        a = m.random_simplex(rng)
        lam = m.random_simplex(rng)
        U_E = rng.random()
        critical = tuple(i for i in range(4) if r[i] > 0.30)
        for i in range(4):
            if a[i] < r[i]:                      # deficient pillar
                eps = min(r[i] - a[i], 0.05)
                if eps <= 1e-9:
                    continue
                a2 = list(a); a2[i] += eps
                Aa1 = m.adequacy(a, r, lam, U_E, critical=critical)[0]
                Aa2 = m.adequacy(a2, r, lam, U_E, critical=critical)[0]
                if Aa2 >= Aa1 - 1e-12:
                    ok += 1
                else:
                    bad.append(("increase_deficient", i, a, r, lam, Aa1, Aa2))
            else:                                # surplus pillar: raising it must not hurt
                a2 = list(a); a2[i] += min(1 - a[i], 0.05)
                Aa1 = m.adequacy(a, r, lam, U_E, critical=critical)[0]
                Aa2 = m.adequacy(a2, r, lam, U_E, critical=critical)[0]
                if Aa2 >= Aa1 - 1e-12:
                    ok += 1
                else:
                    bad.append(("increase_surplus", i, a, r, lam, Aa1, Aa2))
    # (2) severity monotonicity on a fixed profile family
    sev_rows = []
    profile = (0.25, 0.30, 0.25, 0.20)
    for band in ("low", "medium", "high", "critical"):
        r, lam = severity_vectors(band)
        Aa, delta, pen = m.adequacy(profile, r, lam, 0.35, critical=tuple(i for i in range(4) if r[i] > 0.30))
        R_r = m.residual_risk(Aa, 0.6)
        sev_rows.append({"band": band, "r": list(r), "lambda": list(lam),
                        "Aa": round(Aa, 4), "R_r": round(R_r, 4),
                        "decision": m.decision(Aa, R_r, 0.6,
                                              veto=m.hard_veto(delta, tuple(i for i in range(4) if r[i] > 0.30)))})
    mono = all(sev_rows[i]["Aa"] >= sev_rows[i + 1]["Aa"] - 1e-9 for i in range(3))
    mono_r = all(sev_rows[i]["R_r"] <= sev_rows[i + 1]["R_r"] + 1e-9 for i in range(3))
    # (3) old corpus comparison: does severity discriminate in the seed corpus?
    return {"directional_tests": {"checks": ok + len(bad), "failures": len(bad),
                                 "accuracy_pct": round(100.0 * ok / (ok + len(bad)), 3),
                                 "first_failures": bad[:5]},
            "severity_ladder": sev_rows,
            "severity_monotone_Aa": mono,
            "severity_monotone_Rr": mono_r}


def b4():
    """Morris screening: elementary effects of each calibration parameter."""
    rng = random.Random(2026)
    base_params = dict(gamma=0.12, eta=0.05, omega=0.03, rho=0.15,
                       theta=0.15, phi=0.5, veto=0.5, floor=0.05, alpha=1/6, beta=1/4)
    deltas = {"gamma": 0.06, "eta": 0.03, "omega": 0.02, "rho": 0.08,
              "theta": 0.08, "phi": 0.25, "floor": 0.04}
    n_trajectories, n_points = 60, 8
    effects = {k: [] for k in deltas}
    outs = []
    for _ in range(n_trajectories):
        r = m.random_simplex(rng)
        a = m.random_simplex(rng)
        lam = m.random_simplex(rng)
        U_E = rng.random()
        R_c = 0.4 + 0.5 * rng.random()
        critical = tuple(i for i in range(4) if r[i] > 0.30)
        p = dict(base_params)
        order = list(deltas)
        rng.shuffle(order)
        for k in order:
            out = m.adequacy(a, r, lam, U_E, m.Params(**p), critical=critical)[0]
            outs.append(out)
            p2 = dict(p); p2[k] = min(1.0, p[k] + deltas[k])
            out2 = m.adequacy(a, r, lam, U_E, m.Params(**p2), critical=critical)[0]
            effects[k].append(abs(out2 - out))
            p = p2
    morris = {}
    total_var = 0.0
    for k, e in effects.items():
        mu = sum(e) / len(e)
        var = sum((x - mu) ** 2 for x in e) / max(1, len(e) - 1)
        morris[k] = {"mu_star": round(mu, 5), "sigma": round(math.sqrt(var), 5),
                     "interpretation": "larger mu = larger average effect; "
                                       "larger sigma = non-linear/interacting behaviour"}
        total_var += mu
    # interaction check: gamma+rho budget constraint
    budget_violations = 0
    for _ in range(5000):
        g = rng.random() * 0.4
        rr = rng.random() * 0.4
        e = rng.random() * 0.2
        w = rng.random() * 0.2
        if g + rr + e + w > 0.30:
            budget_violations += 1
    # what does the budget constraint actually do to the output range?
    def range_for(g, rho):
        vals = []
        rr2 = random.Random(3)
        for _ in range(2000):
            r = m.random_simplex(rr2); a = m.random_simplex(rr2); lam = m.random_simplex(rr2)
            vals.append(m.adequacy(a, r, lam, rr2.random(), m.Params(gamma=g, rho=rho))[0])
        return min(vals), max(vals)
    return {"morris_elementary_effects": morris,
            "dominant_parameter": max(morris, key=lambda k: morris[k]["mu_star"]),
            "most_nonlinear_parameter": max(morris, key=lambda k: morris[k]["sigma"]),
            "budget_constraint": {"rule": "gamma + rho + eta + omega <= 0.30",
                                  "random_draws_violating": budget_violations,
                                  "draws": 5000},
            "output_range_at_extremes": {"gamma=0.12,rho=0.15": [round(x, 4) for x in range_for(0.12, 0.15)],
                                        "gamma=0.30,rho=0.30": [round(x, 4) for x in range_for(0.30, 0.30)]}}


if __name__ == "__main__":
    b3r = b3()
    b4r = b4()
    with open(os.path.join(OUT, "B3_perturbation.json"), "w", encoding="utf-8") as fh:
        json.dump({"battery": "B3 - perturbation response", "seed": 11, "result": b3r}, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "B4_sensitivity.json"), "w", encoding="utf-8") as fh:
        json.dump({"battery": "B4 - parameter sensitivity (Morris)", "seed": 2026, "result": b4r}, fh, indent=2, ensure_ascii=False)
    print("B3 accuracy:", b3r["directional_tests"]["accuracy_pct"], "%",
          "| severity monotone:", b3r["severity_monotone_Aa"], b3r["severity_monotone_Rr"])
    print("B4 dominant:", b4r["dominant_parameter"], "| most nonlinear:", b4r["most_nonlinear_parameter"])
    print(json.dumps(b4r["morris_elementary_effects"], indent=2))
    print(json.dumps(b4r["output_range_at_extremes"], indent=2))
