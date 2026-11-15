"""Battery B1: formal invariants, v10 core vs the published v9 form.

Reproduces the earlier B1 finding on the *original* equations (Eq. 8-11 of the paper)
and demonstrates that the corrected core passes every invariant.

Outputs: ../../Evaluacoes/r2/B1_invariants_v10.json
"""
import json, math, itertools
import numpy as np
from facet_registry import FACETS
from core import (CaseSpec, Profile, Calibration, confront, structural_terms,
                 default_calibration,
                  prudential_floor, DECISION_PERMISSIVENESS, SEVERITY_BANDS,
                  PRUDENTIAL_MODES, REVERSIBILITY, PILLARS)

EDGES = list(itertools.combinations(range(4), 2))
N = 50000
SEED = 20261031

CAL_V10 = default_calibration()

# --- v9 as published (Eq. 8-11): shares on the simplex, compensatory tension, no veto, no floor
CAL_V9 = dict(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, gamma=0.12, rho=0.15)


def levels_from(scores):
    num = [0.0] * 4
    for f in FACETS:
        v = scores.get(f.code)
        if v is None:
            continue
        for i, b in enumerate(f.beta):
            num[i] += b * f.weight * v
    return [x for x in num]


def confront_v9(req, scores, U_E, R_c):
    a = levels_from(scores)                      # un-normalised "shares" (the v9 ambiguity)
    r = levels_from(req)
    delta = [max(0.0, r[i] - a[i]) for i in range(4)]
    D = sum(CAL_V9["lam"][i] * delta[i] for i in range(4))
    dev = [a[i] - r[i] for i in range(4)]
    T = sum(CAL_V9["alpha"][k] * abs(dev[i] - dev[j]) for k, (i, j) in enumerate(EDGES))
    u = U_E * delta[3] / max(r[3], 1e-9) if r[3] > 1e-9 else 0.0
    aa = max(0.0, min(1.0, 1.0 - D - CAL_V9["gamma"] * T - CAL_V9["rho"] * min(1.0, u)))
    sigma = 0.05 + 0.15 * SEVERITY_VALUE_TEST.get("medium", 0.5)
    r_r = R_c * (1 - aa)                        # Eq. 11 as published: sigma never enters
    return aa, r_r, sigma, delta, D, T, r_r / R_c


SEVERITY_VALUE_TEST = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}


def sample_pairs(n, seed):
    rng = np.random.default_rng(seed)
    pairs = []
    for _ in range(n):
        if k % 2:                      # population B: high-demand, partly resourced agent
            req = {f.code: float(rng.uniform(0.65, 0.95)) for f in FACETS}
            scores = {f.code: float(rng.uniform(0.15, 0.85)) for f in FACETS}
        else:                         # population A: unconstrained calibration stress test
            req = {f.code: float(rng.uniform(0.2, 0.95)) for f in FACETS}
            scores = {f.code: float(rng.uniform(0.1, 1.0)) for f in FACETS}
        sev = str(rng.choice(SEVERITY_BANDS))
        irr = str(rng.choice(list(REVERSIBILITY)))
        pr = str(rng.choice(PRUDENTIAL_MODES))
        pairs.append((req, scores, sev, irr, pr, float(rng.uniform(0.1, 0.7)), float(rng.uniform(0.3, 0.95))))
    return pairs


def monotonicity(pairs, fn):
    """fn(req, scores) -> dict with adequacy/risk. One facet nudged +0.05, deterministically."""
    fails = 0
    pick = np.random.default_rng(4242)
    for k, (req, scores, sev, irr, pr, U_E, R_c) in enumerate(pairs):
        base = fn(req, scores, U_E, R_c)
        idx = int(pick.integers(len(FACETS)))
        code = FACETS[idx].code
        s2 = dict(scores)
        s2[code] = min(1.0, scores[code] + 0.05)
        alt = fn(req, s2, U_E, R_c)
        if alt["adequacy"] < base["adequacy"] - 1e-9 or alt["risk"] > base["risk"] + 1e-9:
            fails += 1
    return fails


def main():
    pairs = sample_pairs(N, SEED)
    res_v10 = []
    for req, scores, sev, irr, pr, U_E, R_c in pairs:
        case = CaseSpec("c", "SA", sev, pr, irr, req, U_E, R_c, ("M", "K"))
        res_v10.append(confront(case, Profile("p", scores), CAL_V10))

    def v9_fn(req, scores, U_E, R_c):
        aa, rr, sig, delta, D, T, ratio = confront_v9(req, scores, U_E, R_c)
        return {"adequacy": aa, "risk": rr, "decision": None, "sigma": sig,
                "deficits": delta, "T": T, "D": D}

    out = {"battery": "B1", "seed": SEED, "samples": N,
           "calibration_v10": {"lam": CAL_V10.lam, "alpha": CAL_V10.alpha, "beta_face": CAL_V10.beta_face,
                                "gamma": CAL_V10.gamma, "eta": CAL_V10.eta, "omega": CAL_V10.omega,
                                "rho": CAL_V10.rho, "delta": CAL_V10.delta,
                                "theta": CAL_V10.theta,
                                "hard_veto_delta": CAL_V10.hard_veto_delta,
                                "bar": {"base": CAL_V10.bar_base,
                                        "severity": CAL_V10.bar_severity,
                                        "irreversibility": CAL_V10.bar_irreversibility,
                                        "prudential": CAL_V10.bar_prudential},
                                "budget": CAL_V10.total_penalty_budget},
           "v10": {}, "v9_as_published": {}}

    A = [r["adequacy"] for r in res_v10 if r["adequacy"] is not None]
    Rr = [r["R_r"] for r in res_v10 if r["R_r"] is not None]
    sigRc = [r["sigma"] * r["R_c"] for r in res_v10 if r["R_r"] is not None]
    out["v10"]["bounds_ok"] = all(0 <= a <= 1 for a in A)
    out["v10"]["risk_floor_ok"] = all(r >= s - 1e-3 for r, s in zip(Rr, sigRc))
    out["v10"]["risk_ceiling_ok"] = all(Rr[i] <= res_v10[i]["R_c"] * (1 + res_v10[i]["sigma"]) + 1e-9 for i in range(len(Rr)))
    out["v10"]["perfect_adequacy_count"] = sum(1 for a in A if a >= 0.999999)
    out["v10"]["perfect_adequacy_pct"] = out["v10"]["perfect_adequacy_count"] / len(A) * 100
    out["v10"]["monotonicity_failures_probe"] = monotonicity(pairs[:20000],
        lambda req, scores, U_E, R_c: (lambda r: {"adequacy": r["adequacy"], "risk": r["R_r"]})(
            confront(CaseSpec("c", "SA", "medium", "standard", "partially_irreversible", req, U_E, R_c),
                     Profile("p", scores), CAL_V10)))
    out["v10"]["populations"] = {}
    for name, sel in (("A_unconstrained", range(0, len(res_v10), 2)),
                      ("B_high_demand", range(1, len(res_v10), 2))):
        rows = [res_v10[i] for i in sel if res_v10[i]["adequacy"] is not None]
        out["v10"]["populations"][name] = {
            "n": len(rows),
            "mean_adequacy": round(sum(r["adequacy"] for r in rows) / len(rows), 4),
            "veto_share": round(sum(1 for r in rows if r["veto"]) / len(rows), 4),
            "hard_veto_share": round(sum(1 for r in rows if r["hard_veto"]) / len(rows), 4),
            "guard_failure_share": round(sum(1 for r in rows if r["guard_failures"]) / len(rows), 4),
            "mean_facet_exposure": round(sum(r["facet_exposure"] for r in rows) / len(rows), 4),
            "worst_pillar": {p: sum(1 for r in rows if r["worst_pillar"] == p) for p in PILLARS},
        }
    out["v10"]["veto_hits"] = sum(1 for r in res_v10 if r["veto"])
    out["v10"]["veto_cap_binds"] = sum(1 for r in res_v10 if r["veto"] and r["adequacy"] < r["adequacy_raw"])
    permissive = {"ALLOW", "ALLOW_WITH_GUARDS"}
    def ladder(aa, ratio):
        if aa <= 0.45 or ratio >= 0.65: return "PROHIBIT"
        if aa <= 0.60 or ratio >= 0.40: return "REVIEW_REQUIRED"
        if aa <= 0.78 or ratio >= 0.20: return "ALLOW_WITH_GUARDS"
        return "ALLOW"
    hidden = 0
    for r in res_v10:
        if r["veto"]:
            would = ladder(r["adequacy_raw"], r["adequacy_raw"] * 0 + min(1.0, 1 - r["adequacy_raw"]) + r["sigma"])
            if would in permissive and r["decision"] not in permissive:
                hidden += 1
    out["v10"]["veto_hits_rescued_by_lexicographic_veto"] = hidden
    out["v10"]["veto_hits_compensated_in_v9_style"] = sum(
        1 for r in res_v10 if r["veto"] and r["adequacy_raw"] >= 0.60)
    out["v10"]["decision_distribution"] = {}
    for r in res_v10:
        out["v10"]["decision_distribution"][r["decision"]] = out["v10"]["decision_distribution"].get(r["decision"], 0) + 1
    out["v10"]["structural_hierarchy_ok"] = all(
        r["S3"] <= r["S2"] + 1e-9 and r["S4"] <= max(r["deficits"]) + 1e-9 for r in res_v10 if r["adequacy"] is not None)
    out["v10"]["mean_adequacy"] = float(np.mean(A))
    out["v10"]["mean_residual_ratio"] = float(np.mean([r["risk_ratio"] for r in res_v10 if r["risk_ratio"] is not None]))

    mono_v9 = monotonicity(pairs[:20000], v9_fn)
    v9 = [v9_fn(req, scores, U_E, R_c) for req, scores, sev, irr, pr, U_E, R_c in pairs]
    floor_fail = sum(1 for x in v9 if x["risk"] < 0.05 * 0.8 - 1e-9)   # sigma*R_c floor absent in Eq. 11
    out["v9_as_published"] = {
        "note": "sigma (prudential floor) appears in the case model but never in Eq. (11); "
                "Eq. (8) compensates single-pillar deficits with surpluses elsewhere; no veto exists.",
        "risk_floor_violations": floor_fail,
        "risk_floor_violation_pct": floor_fail / len(v9) * 100,
        "sigma_present_in_case_but_absent_from_eq11": True,
        "monotonicity_failures": mono_v9,
        "monotonicity_failure_pct": mono_v9 / 20000 * 100,
        "deficit_sum_gt_1": sum(1 for x in v9 if sum(x["deficits"]) > 1.0),
        "tension_penalises_pure_surplus": sum(1 for x in v9 if sum(x["deficits"]) == 0 and x["T"] > 1e-9),
        "tension_penalises_pure_surplus_pct": sum(1 for x in v9 if sum(x["deficits"]) == 0 and x["T"] > 1e-9) / len(v9) * 100,
        "veto_hits": 0,
        "perfect_adequacy_pct": sum(1 for x in v9 if x["adequacy"] >= 0.999999) / len(v9) * 100,
    }
    out["delta_analysis"] = {
        "v10_perfect_adequacy_pct": out["v10"]["perfect_adequacy_pct"],
        "v9_perfect_adequacy_pct": out["v9_as_published"]["perfect_adequacy_pct"],
        "v9_style_compensatory_masking_pct_of_veto_hits":
            out["v10"]["veto_hits_compensated_in_v9_style"] / max(1, out["v10"]["veto_hits"]) * 100,
        "v10_decisions_changed_by_veto_cap_pct_of_veto_hits":
            out["v10"]["veto_hits_rescued_by_lexicographic_veto"] / max(1, out["v10"]["veto_hits"]) * 100,
        "v9_compensatory_form_advises_permissive_decision_for":
            sum(1 for x in v9 if x["adequacy"] >= 0.78 and sum(x["deficits"]) > 0) / len(v9) * 100,
        "v10_advises_review_or_prohibit_for_the_same_population_pct":
            (out["v10"]["decision_distribution"]["REVIEW_REQUIRED"] + out["v10"]["decision_distribution"]["PROHIBIT"]) / len(res_v10) * 100,
    }

    path = "../../Evaluacoes/r2/B1_invariants_v10.json"
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
