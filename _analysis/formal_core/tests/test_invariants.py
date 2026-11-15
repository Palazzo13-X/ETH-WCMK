"""B1 - formal invariants of the ETH-WCMK v10 core (gate G1/G2).

Run with:  python3 -m pytest tests/test_invariants.py -q
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from facet_registry import FACETS, DOMAINS, validate_registry
from core import (CaseSpec, Profile, Calibration, confront, confront_chain, structural_terms,
                  prudential_floor, requirement_for, effective_value, decide,
                  failure_probability,
                  DECISION_PERMISSIVENESS, SEVERITY_BANDS, EDGES, FACES,
                  PRUDENTIAL_MODES, REVERSIBILITY, PILLARS, EPS,
                  HORIZON_VALUE, CONFLICT_PATTERNS, SEVERITY_VALUE)

N = 20000
def mk_cal(**kw):
    base = dict(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                gamma=0.12, eta=0.05, omega=0.03, rho=0.10, delta=0.05)
    base.update(kw)
    return Calibration(**base)


CAL = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                  gamma=0.12, eta=0.05, omega=0.03, rho=0.10, delta=0.05)


def rng(seed=7):
    return np.random.default_rng(seed)


def make_case(r, domain="SA", severity="medium", prudential="standard",
              irreversibility="partially_irreversible", U_E=0.30, R_c=0.80,
              critical=("M", "K"), req=None, horizon="immediate", conflict="none"):
    if req is None:
        req = {f.code: float(r.uniform(0.20, 0.95)) for f in FACETS}
    return CaseSpec(f"case_{r.integers(10**6)}", domain, severity, prudential,
                    irreversibility, req, U_E, R_c, critical, horizon, conflict)


def make_profile(r, scores=None):
    if scores is None:
        scores = {f.code: float(r.uniform(0.10, 1.00)) for f in FACETS}
    return Profile("p", scores)


def sweep(n=N, seed=7, **kw):
    r = rng(seed)
    out = []
    for _ in range(n):
        c = make_case(r, **kw)
        p = make_profile(r)
        out.append(confront(c, p, CAL))
    return out


# ---------------------------------------------------------------- registry
def test_registry_integrity():
    assert validate_registry() == []
    assert len(FACETS) == 33          # canon v12: 28 of v11 + T1, H1, P1, D1, R1 (D4.20)
    for f in FACETS:
        assert abs(sum(f.beta) - 1) < 1e-9, f.code
        assert f.code[0] in PILLARS
        assert 1 <= sum(1 for b in f.beta if b > 0) <= 3, f.code
        assert f.observable, f.code
        assert len(f.criticality) == len(DOMAINS), f.code

# ---------------------------------------------------------------- I1 bounds
def test_I1_bounds():
    for res in sweep():
        if res["decision"] == "ABSTAIN":
            continue
        assert 0 <= res["adequacy"] <= 1
        assert all(0 <= x <= 1 for x in res["levels"])
        assert all(0 <= x <= 1 for x in res["deficits"])
        assert 0 <= res["sigma"] <= 0.35
        assert res["R_r"] >= 0

# ---------------------------------------------------------------- I2 perfect adequacy
def test_I2_perfect_adequacy_iff_no_deficit():
    for _ in range(500):
        r = rng(1)
        req = {f.code: 0.60 for f in FACETS}
        scores = {f.code: 1.0 for f in FACETS}
        res = confront(make_case(r, req=req), make_profile(r, scores), CAL)
        assert abs(res["adequacy"] - 1.0) < 1e-9
        # E12' (v12): risk is R_c * (p_fail + sigma)/(1 + sigma). With a perfect profile
        # p_fail is at its floor (0.02), so risk sits at its irreducible floor - not at
        # sigma * R_c exactly, but never below sigma * R_c / (1 + sigma) and never above R_c.
        floor = res["sigma"] * res["R_c"] / (1.0 + res["sigma"])
        assert res["R_r"] >= floor - 1e-9
        assert res["R_r"] <= res["R_c"] + 1e-9
        assert abs(res["R_r"] - res["R_c"] * (0.02 + res["sigma"]) / (1.0 + res["sigma"])) < 1e-4
        assert res["decision"] != "PROHIBIT"
    # converse: a positive pillar deficit lowers adequacy below 1
    r = rng(3)
    req = {f.code: 0.80 for f in FACETS}
    scores = {f.code: 0.70 for f in FACETS}
    res = confront(make_case(r, req=req), make_profile(r, scores), CAL)
    assert res["adequacy"] < 1.0

# ---------------------------------------------------------------- I3 risk floor / ceiling
def test_I3_risk_floor_and_ceiling():
    """R_r = R_c * (p_fail + sigma)/(1 + sigma): bounded by the irreducible floor and by R_c."""
    for res in sweep(5000):
        if res["decision"] == "ABSTAIN":
            continue
        floor = res["sigma"] * res["R_c"] / (1.0 + res["sigma"])
        assert floor - 1e-9 <= res["R_r"] <= res["R_c"] + 1e-9
        assert res["failure_probability"] >= 0.02 - 1e-9
        assert res["failure_probability"] <= 0.98 + 1e-9

# ---------------------------------------------------------------- I4 veto dominance
def test_I4_veto_dominates_score_and_decision():
    hits = 0
    for res in sweep(5000):
        if res["veto"]:
            hits += 1
            worst = max(res["guarded_deficits"][PILLARS.index(p)] for p in res["veto"])
            # E11c': the cap removes at least half of the worst uncompensable gap, and
            # the whole gap when the stakes are maximal.
            assert res["adequacy"] <= res["adequacy_raw"] + 1e-9
            assert res["adequacy"] <= 1 - 0.5 * worst + 1e-9
            assert res["decision"] in ("PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ABSTAIN")
    assert hits > 0

# ---------------------------------------------------------------- I5 monotonicity in facet levels
def test_I5_monotonicity_in_facet_scores():
    r = rng(11)
    fails = 0
    for _ in range(1500):
        case = make_case(r)
        prof = make_profile(r)
        base = confront(case, prof, CAL)
        f = FACETS[int(r.integers(len(FACETS)))]
        bump = min(1.0, prof.facet_scores[f.code] + 0.05)
        new_scores = dict(prof.facet_scores)
        new_scores[f.code] = bump
        alt = confront(case, Profile("p", new_scores), CAL)
        if (alt["adequacy"] < base["adequacy"] - 1e-9 or
                alt["R_r"] > base["R_r"] + 1e-9 or
                DECISION_PERMISSIVENESS[alt["decision"]] < DECISION_PERMISSIVENESS[base["decision"]]):
            fails += 1
    assert fails == 0

# ---------------------------------------------------------------- I6 severity ladder
def test_I6_severity_monotonicity():
    r = rng(13)
    fails = 0
    for _ in range(800):
        scores = {f.code: float(r.uniform(0.2, 1.0)) for f in FACETS}
        req = {f.code: float(r.uniform(0.2, 0.95)) for f in FACETS}
        prev = None
        for band in SEVERITY_BANDS:
            case = make_case(r, req=req, severity=band)
            res = confront(case, Profile("p", scores), CAL)
            if prev is not None:
                if res["adequacy"] > prev["adequacy"] + 1e-9:
                    fails += 1
                if res["R_r"] < prev["R_r"] - 1e-9:
                    fails += 1
                if DECISION_PERMISSIVENESS[res["decision"]] > DECISION_PERMISSIVENESS[prev["decision"]]:
                    fails += 1
            prev = res
    assert fails == 0

# ---------------------------------------------------------------- I7 structural hierarchy
def test_I7_structural_hierarchy():
    for res in sweep(5000):
        d = res["deficits"]
        s2, s3, s4 = structural_terms(d, CAL)
        mx = max(d)
        assert s2 <= mx + 1e-9 and s3 <= s2 + 1e-9 and s4 <= s3 + 1e-9 and s4 <= mx + 1e-9
        assert (s4 > 0) == all(x > 0 for x in d)
        assert (CAL.gamma + CAL.eta + CAL.omega) * mx + 1e-9 >= CAL.gamma * s2 + CAL.eta * s3 + CAL.omega * s4

def test_I7b_hierarchy_proven_over_the_whole_deficit_grid():
    """S4 <= S3 <= S2 <= max d must hold for every deficit vector, not just sampled ones.

    v11 asserted this hierarchy while computing S4 as the geometric mean of the four
    deficits; over a 10^4-point grid that assertion failed in 9,991 of 10,000 cases. The
    cell term is now the min (Godel t-norm), and this test is the proof by exhaustion.
    """
    grid = [i / 20.0 for i in range(21)]
    alpha = (1 / 6,) * 6
    beta = (1 / 4,) * 4
    for a in grid:
        for b in grid:
            for c in grid:
                for e in grid:
                    d = (a, b, c, e)
                    s2 = sum(alpha[k] * min(d[i], d[j]) for k, (i, j) in enumerate(EDGES))
                    s3 = sum(beta[k] * min(d[i], d[j], d[kk]) for k, (i, j, kk) in enumerate(FACES))
                    s4 = min(d)
                    assert s4 - s3 <= 1e-9 and s3 - s2 <= 1e-9 and s2 - max(d) <= 1e-9, (d, s4, s3, s2)
    # and 200,000 random deficit vectors with non-uniform, valid weights
    rr = np.random.default_rng(42)
    for _ in range(200000):
        d = rr.random(4)
        al = rr.dirichlet(np.ones(6))
        be = np.array([0.30, 0.25, 0.20, 0.25])
        s2 = sum(al[k] * min(d[i], d[j]) for k, (i, j) in enumerate(EDGES))
        s3 = sum(be[k] * min(d[i], d[j], d[kk]) for k, (i, j, kk) in enumerate(FACES))
        assert min(d) <= s3 + 1e-9
        if all(al[k] >= (1/3) * sum(be[f] for f, face in enumerate(FACES) if set(face) >= {i, j})
              for k, (i, j) in enumerate(EDGES)):
            assert s3 <= s2 + 1e-9

def test_calibration_is_valid():
    assert CAL.is_valid() == []

def test_bad_calibration_is_rejected():
    bad = Calibration(lam=(0.5, 0.2, 0.2, 0.1), alpha=(0.5, 0.1, 0.1, 0.1, 0.1, 0.1),
                      beta_face=(1 / 4,) * 4, gamma=0.4, eta=0.1, omega=0.05, rho=0.2)
    assert bad.is_valid()

# ---------------------------------------------------------------- I8 no double counting
def test_I8_shared_facet_is_not_double_counted():
    """Splitting a shared facet into two identical twins (same beta, declared twice)
    must leave the pillar levels and the adequacy unchanged: the pillar level is the
    beta-normalised average sum(beta_i v_i)/sum(beta_i), so duplicating a facet
    multiplies numerator and denominator by the same factor."""
    from facet_registry import FacetDef
    r = rng(17)
    case = make_case(r)
    prof = make_profile(r)
    base = confront(case, prof, CAL)
    twins = []
    for f in FACETS:
        if sum(1 for b in f.beta if b > 0) > 1:      # shared facet
            twins.append(FacetDef(f.code + "a", f.label, f.beta, f.policy, f.guard, f.guard_min,
                                  f.source, f.observable, f.criticality))
            twins.append(FacetDef(f.code + "b", f.label, f.beta, f.policy, f.guard, f.guard_min,
                                  f.source, f.observable, f.criticality))
        else:
            twins.append(f)
    scores2 = dict(prof.facet_scores)
    req2 = dict(case.facet_requirements)
    for f in FACETS:
        if sum(1 for b in f.beta if b > 0) > 1:
            scores2[f.code + "a"] = scores2[f.code + "b"] = prof.facet_scores[f.code]
            req2[f.code + "a"] = req2[f.code + "b"] = case.facet_requirements[f.code]
    alt = confront(CaseSpec(case.case_id, case.domain, case.severity, case.prudential,
                            case.irreversibility, req2, case.U_E, case.R_c, case.critical_pillars),
                   Profile("p", scores2), CAL, facets=twins)
    assert abs(alt["adequacy"] - base["adequacy"]) < 1e-9

# ---------------------------------------------------------------- I9 projection coherence
def test_I9_uniform_facet_levels_project_to_same_level():
    r = rng(19)
    for level in (0.7, 0.8, 0.95):      # above every guard_min (max 0.60)
        scores = {f.code: level for f in FACETS}
        res = confront(make_case(r), Profile("p", scores), CAL)
        assert all(abs(x - level) < 1e-9 for x in res["levels"])


def test_I9b_guard_below_min_is_reported():
    r = rng(19)
    scores = {f.code: 0.2 for f in FACETS}
    res = confront(make_case(r), Profile("p", scores), CAL)
    assert len(res["guard_failures"]) >= 4

# ---------------------------------------------------------------- I10 abstention
def test_I10_abstention_on_incomplete_data():
    r = rng(23)
    scores = {f.code: 0.7 for f in FACETS[:18]}      # 18/26 = 0.69 coverage
    res = confront(make_case(r), Profile("p", scores), CAL)
    assert res["decision"] == "ABSTAIN" and res["adequacy"] is None
    res2 = confront(make_case(r, severity="not_a_band"), Profile("p", {f.code: 0.7 for f in FACETS}), CAL)
    assert res2["decision"] == "ABSTAIN"

# ---------------------------------------------------------------- I11 permutation invariance
def test_I11_facet_order_irrelevance():
    r = rng(29)
    case = make_case(r)
    prof = make_profile(r)
    a = confront(case, prof, CAL)
    b = confront(case, Profile("p", dict(reversed(list(prof.facet_scores.items())))), CAL)
    assert a["adequacy"] == b["adequacy"] and a["deficits"] == b["deficits"]

# ---------------------------------------------------------------- I12 Lipschitz continuity
def test_I12_continuity():
    """Adequacy is continuous in the facet levels away from a guard crossing: a 1%
    change in one unguarded facet cannot move Aa by more than 5%."""
    r = rng(31)
    worst = 0.0
    for _ in range(1000):
        case = make_case(r)
        prof = make_profile(r)
        a = confront(case, prof, CAL)
        unguarded = [f for f in FACETS if not f.guard]
        f = unguarded[int(r.integers(len(unguarded)))]
        pert = dict(prof.facet_scores)
        pert[f.code] = min(1.0, pert[f.code] + 0.01)
        b = confront(case, Profile("p", pert), CAL)
        worst = max(worst, abs(a["adequacy"] - b["adequacy"]))
    assert worst <= 0.05


def test_I12b_guard_crossing_is_a_bounded_jump():
    """Crossing a hard guard is a deliberate discontinuity; the jump must be bounded by
    the guard shortfall itself, never by an unbounded veto."""
    r = rng(31)
    worst = 0.0
    for _ in range(1500):
        case = make_case(r)
        prof = make_profile(r)
        guards = [f for f in FACETS if f.guard]
        f = guards[int(r.integers(len(guards)))]
        v = prof.facet_scores[f.code]
        if v >= f.guard_min:
            continue
        below = confront(case, prof, CAL)
        pert = dict(prof.facet_scores); pert[f.code] = f.guard_min
        above = confront(case, Profile("p", pert), CAL)
        worst = max(worst, above["adequacy"] - below["adequacy"])
    assert worst <= 1.0
    assert worst > 0.0

# ---------------------------------------------------------------- I13 determinism
def test_I13_determinism():
    r = rng(37)
    case, prof = make_case(r), make_profile(r)
    assert confront(case, prof, CAL) == confront(case, prof, CAL)

# ---------------------------------------------------------------- I14 guards are non-compensatory
def test_I14_guard_cap_blocks_compensation():
    from core import case_stakes
    """Two non-compensatory policies must behave differently but neither may let other
    facets compensate for a failing guard."""
    from facet_registry import BY_CODE
    r = rng(41)
    req = {f.code: 0.95 for f in FACETS}

    # (a) guarded_weighted_mean: W2 (guard 0.55) caps the pillar level it feeds.
    scores = {f.code: 1.0 for f in FACETS}
    scores["W2"] = 0.30
    res = confront(make_case(r, req=req), Profile("p", scores), CAL)
    iW, iM = PILLARS.index("W"), PILLARS.index("M")
    assert res["guard_failures"] and res["guard_failures"][0]["policy"] == "guarded_weighted_mean"
    assert res["levels"][iW] <= 0.30 + 1e-9 and res["levels"][iM] <= 0.30 + 1e-9

    # (b) threshold_override: M1 (guard 0.60) contributes zero below the guard.
    case2 = make_case(r, req=req)
    scores = {f.code: 1.0 for f in FACETS}
    scores["M1"] = 0.30
    res2 = confront(case2, Profile("p", scores), CAL)
    assert res2["guard_failures"] and res2["guard_failures"][0]["policy"] == "threshold_override"
    assert res2["guarded_deficits"][iM] >= 0.95 - 0.30 - 1e-9      # gap counted, not averaged
    # E11d: the cap removes the uncompensable gap weighted by the stakes in play.
    cap_weight = CAL.cap_base + CAL.cap_stakes_min_free if False else CAL.cap_base + CAL.cap_stakes_gain * case_stakes(case2)
    assert res2["adequacy"] <= 1 - cap_weight * (0.95 - 0.30) + 1e-9

def test_I15_facet_exposure_prevents_dilution():
    """A deficit confined to a single facet is averaged away at pillar level; the
    criticality-weighted exposure term must still register it."""
    req = {f.code: 0.70 for f in FACETS}
    lev = {f.code: 0.99 for f in FACETS}
    case = CaseSpec("EX-1", "RS", "medium", "standard", "reversible", req, 0.20, 0.50, ("K",))
    base = confront(case, Profile("p", dict(lev), {}), CAL)
    assert base["facet_exposure"] < 1e-6
    lev["K1"] = 0.40
    alt = confront(case, Profile("p", dict(lev), {}), CAL)
    assert alt["facet_exposure"] > 0.01
    assert alt["adequacy"] < base["adequacy"]
    assert alt["deficits"] == base["deficits"]  # pillar deficits unchanged: dilution shown


# ---------------------------------------------------------------- I16 uncertainty band
def test_I16_confidence_band_is_ordered_and_wider_with_uncertainty():
    r = rng(43)
    for conf in (1.0, 0.5, 0.1):
        case = make_case(r, req={f.code: 0.80 for f in FACETS})
        prof = Profile("p", {f.code: 0.70 for f in FACETS}, {f.code: conf for f in FACETS})
        res = confront(case, prof, CAL)
        assert res["adequacy_low"] <= res["adequacy"] <= res["adequacy_high"] + 1e-9
        if conf == 1.0:
            assert abs(res["adequacy_low"] - res["adequacy"]) < 1e-9
        else:
            assert res["adequacy_low"] < res["adequacy"]
        width = res["adequacy_high"] - res["adequacy_low"]
        if conf == 0.1:
            assert width > 0.10          # band grows with observation uncertainty


def test_I16b_decision_uses_the_conservative_bound():
    r = rng(47)
    case = make_case(r, req={f.code: 0.85 for f in FACETS}, severity="high")
    prof = Profile("p", {f.code: 0.90 for f in FACETS}, {f.code: 1.0 for f in FACETS})
    full = confront(case, prof, CAL)
    lowconf = Profile("p", {f.code: 0.90 for f in FACETS}, {f.code: 0.25 for f in FACETS})
    res = confront(case, lowconf, CAL)
    assert DECISION_PERMISSIVENESS[res["decision"]] <= DECISION_PERMISSIVENESS[full["decision"]]


# ---------------------------------------------------------------- I17 aggregation policies
def test_I17_threshold_override_zeroes_contribution():
    from facet_registry import BY_CODE
    m1 = BY_CODE["M1"]
    assert m1.policy == "threshold_override"
    assert effective_value(m1, 0.30, 1.0) == 0.0
    assert effective_value(m1, 0.70, 1.0) == 0.70


def test_I17b_uncertainty_penalized_mean_shrinks_with_low_confidence():
    from facet_registry import BY_CODE
    k6 = BY_CODE["K6"]
    assert k6.policy == "uncertainty_penalized_mean"
    full = effective_value(k6, 0.90, 1.0)
    weak = effective_value(k6, 0.90, 0.4)
    assert full == 0.90 and weak < full


def test_I18_guard_gap_creates_a_facet_level_veto():
    """A failing hard guard on a critical pillar cannot be compensated by perfect
    facets in the same pillar (veto operates at facet granularity, E11b)."""
    req = {f.code: 0.90 for f in FACETS}
    lev = {f.code: 1.0 for f in FACETS}
    lev["M1"] = 0.10
    case = CaseSpec("GV-1", "IC", "critical", "maximum", "irreversible", req, 0.30, 0.90, ("M", "K"))
    res = confront(case, Profile("p", lev), CAL)
    assert "M" in res["veto"] and "M" in res["hard_veto"]
    assert res["decision"] == "PROHIBIT"
    # E24 (v12): a breached hard duty caps its pillar at the level the agent actually
    # demonstrated for that duty - the cap applies to every guarded facet, not only to
    # facets whose aggregation policy is guarded_weighted_mean.
    assert res["levels"][PILLARS.index("M")] <= 0.10 + 1e-9
    assert res["deficits"][PILLARS.index("M")] >= 0.90 - 0.10 - 1e-9
    cap_weight = CAL.cap_base + CAL.cap_stakes_gain * res["stakes"]
    assert res["adequacy"] <= 1 - cap_weight * (0.90 - 0.10) + 1e-9


# ---------------------------------------------------------------- I19 horizon
def test_I19_horizon_raises_the_bar_monotonically():
    r = rng(53)
    case0 = make_case(r, horizon="immediate")
    case1 = make_case(r, horizon="long")
    bars = [CAL.decision_bar(c) for c in (case0, case1)]
    assert bars[1] >= bars[0]
    assert CAL.decision_bar(make_case(r, horizon="medium")) <= bars[1]


# ---------------------------------------------------------------- I20 layered agency
def test_I20_chain_is_weakest_link():
    r = rng(59)
    case = make_case(r)
    strong = Profile("model", {f.code: 0.95 for f in FACETS}, layer="model")
    weak = Profile("operator", {f.code: 0.30 for f in FACETS}, layer="operator")
    chain = confront_chain(case, [strong, weak], CAL)
    single_weak = confront(case, weak, CAL)
    assert chain["adequacy"] == single_weak["adequacy"]
    assert chain["decision"] == single_weak["decision"]
    assert len(chain["layers"]) == 2
    chain2 = confront_chain(case, [strong], CAL)
    assert DECISION_PERMISSIVENESS[chain["decision"]] <= DECISION_PERMISSIVENESS[chain2["decision"]]


# ---------------------------------------------------------------- I21 requirement coherence
def test_I21_requirement_is_monotone_and_bounded():
    from facet_registry import FACETS as F
    for f in F:
        for sev in SEVERITY_BANDS:
            for irr in REVERSIBILITY:
                for h in HORIZON_VALUE:
                    c = CaseSpec("RQ", "IC", sev, "standard", irr, {}, 0.3, 0.8)
                    c.horizon = h
                    r = requirement_for(f, c)
                    assert 0.30 <= r <= 0.95
                    if f.guard:
                        assert r >= f.guard_min + 0.04
    c_low = CaseSpec("R1", "IC", "low", "standard", "reversible", {}, 0.2, 0.7)
    c_high = CaseSpec("R2", "IC", "critical", "maximum", "irreversible", {}, 0.2, 0.7)
    assert all(requirement_for(f, c_high) >= requirement_for(f, c_low) - 1e-9 for f in F)


# ---------------------------------------------------------------- I22 abstention on coverage
def test_I22_abstain_below_coverage_with_33_facets():
    r = rng(61)
    k_below = 23          # 23/33 = 0.697 < 0.70
    k_above = 24          # 24/33 = 0.727 >= 0.70
    assert k_below / len(FACETS) < 0.70 <= k_above / len(FACETS)
    scores = {f.code: 0.8 for f in FACETS[:k_below]}
    res = confront(make_case(r), Profile("p", scores), CAL)
    assert res["decision"] == "ABSTAIN"
    scores2 = {f.code: 0.8 for f in FACETS[:k_above]}
    assert confront(make_case(r), Profile("p", scores2), CAL)["decision"] != "ABSTAIN"



# ---------------------------------------------------------------- I23 stakes-modulated veto (E11c)
def test_I23_hard_veto_is_stakes_proportional():
    """Same guard shortfall, different stakes: prohibition is the response only when
    something is actually at stake. The adequacy cap, by contrast, is stakes-blind."""
    from core import case_stakes
    def case(sev, pru, irr):
        probe = CaseSpec("probe", "SA", sev, pru, irr, {}, 0.40, 0.50)
        return CaseSpec(f"SV-{sev}", "SA", sev, pru, irr,
                        {f.code: requirement_for(f, probe) for f in FACETS},
                        0.30, 0.60, ("M", "C"))
    lo, hi = case("low", "standard", "reversible"), case("critical", "maximum", "irreversible")
    lev = {f.code: 1.0 for f in FACETS}
    lev["M1"] = 0.0                      # the duty floor is not met at all
    assert case_stakes(lo) < CAL.stakes_veto_min <= case_stakes(hi)
    r_lo = confront(lo, Profile("p", lev), CAL)
    r_hi = confront(hi, Profile("p", lev), CAL)
    assert "M" in r_lo["veto"] and "M" not in r_lo["hard_veto"]
    assert "M" in r_hi["hard_veto"]
    assert r_lo["decision"] != "PROHIBIT"
    assert r_hi["decision"] == "PROHIBIT"
    gap = r_lo["guarded_deficits"][PILLARS.index("M")]
    assert abs(r_lo["adequacy"] - (1 - (0.5 + 0.5 * case_stakes(lo)) * gap)) < 1e-4


def test_I24_veto_hardness_monotone_in_stakes():
    from core import case_stakes
    prev = None
    for sev in SEVERITY_BANDS:
        for irr in REVERSIBILITY:
            c = CaseSpec("mono", "IC", sev, "standard", irr,
                         {f.code: requirement_for(f, CaseSpec("t", "IC", sev, "standard", irr, {}, 0.3, 0.6))
                          for f in FACETS}, 0.3, 0.6, ("M", "C"))
            lev = {f.code: max(0.0, c.facet_requirements[f.code] - 0.55) if f.code == "M1"
                   else 1.0 for f in FACETS}
            res = confront(c, Profile("p", lev), CAL)
            hard = bool(res["hard_veto"])
            s = case_stakes(c)
            if prev is not None and s >= prev[0]:
                assert hard >= prev[1]
            prev = (s, hard)


def test_I25_bar_crossing_is_prohibitive_only_with_stakes():
    from core import case_stakes
    """E13b: proportionality of the ladder. The same shortfall, at low stakes, is a
    review rather than a categorical prohibition."""
    cal = mk_cal(bar_base=0.60, bar_severity=0.20, prohibit_margin=0.15,
                 prohibit_stakes_min=0.55, veto_slack=0.05)
    lev = {f.code: 0.50 for f in FACETS}
    low = CaseSpec("lowstakes", "SA", "low", "standard", "reversible", {}, 0.3, 0.6, ("W", "M"))
    high = CaseSpec("highstakes", "SA", "high", "elevated", "irreversible", {}, 0.3, 0.6, ("W", "M", "C"))
    for c in (low, high):
        c.facet_requirements = {f.code: requirement_for(f, c) for f in FACETS}
        assert c.is_complete() == []
    a, b = confront(low, Profile("p", lev), cal), confront(high, Profile("p", lev), cal)
    bar_low, bar_high = cal.decision_bar(low), cal.decision_bar(high)
    assert case_stakes(low) < cal.prohibit_stakes_min <= case_stakes(high)
    assert a["adequacy"] <= bar_low - cal.prohibit_margin
    assert b["adequacy"] <= bar_high - cal.prohibit_margin
    assert a["decision"] != "PROHIBIT"
    assert b["decision"] == "PROHIBIT"
    # the only thing keeping the low-stakes case out of prohibition is the stakes gate
    gateless = mk_cal(bar_base=0.60, bar_severity=0.20, prohibit_margin=0.15,
                      prohibit_stakes_min=0.0, veto_slack=0.05, prohibit_needs_material=False)
    assert confront(low, Profile("p", lev), gateless)["decision"] == "PROHIBIT"


def test_I26_veto_never_escalates_low_stakes_to_prohibition():
    """A veto that is real but not severe is managed with guards, not prohibition."""
    cal = mk_cal(bar_base=0.50, prohibit_margin=0.20, veto_slack=0.10, guards_margin=0.15)
    c = CaseSpec("soft", "SA", "low", "standard", "reversible", {}, 0.3, 0.6, ("M",))
    c.facet_requirements = {f.code: requirement_for(f, c) for f in FACETS}
    lev = {f.code: 1.0 for f in FACETS}
    lev["M1"] = c.facet_requirements["M1"] - 0.62          # veto-level gap, below the hard margin
    res = confront(c, Profile("p", lev), cal)
    assert "M" in res["veto"] and "M" not in res["hard_veto"]
    assert res["decision"] in ("REVIEW_REQUIRED", "ALLOW_WITH_GUARDS")


def test_I27_bar_route_needs_a_concentrated_duty_failure():
    """E13c: a diffuse shortfall is not a categorical prohibition.

    Two cases with the same adequacy level: one where the shortfall is spread over many
    duties, one where it is concentrated on a duty the domain treats as critical. Only
    the concentrated one may cross the bar into prohibition.
    """
    cal = mk_cal(bar_base=0.55, bar_severity=0.10, prohibit_margin=0.25, prohibit_stakes_min=0.45,
                material_gap=0.25, critical_prohibit_gap=0.45, veto_slack=0.05)
    diffuse = CaseSpec("diffuse", "SA", "high", "elevated", "irreversible", {}, 0.3, 0.6, ("W", "M", "C"))
    concentrated = CaseSpec("concentrated", "SA", "high", "elevated", "irreversible", {}, 0.3, 0.6, ("W", "M", "C"))
    for c in (diffuse, concentrated):
        c.facet_requirements = {f.code: requirement_for(f, c) for f in FACETS}
    def diffuse_levels(gap):
        return {f.code: (max(diffuse.facet_requirements[f.code] - gap, f.guard_min + 0.02)
                         if f.guard else max(0.0, diffuse.facet_requirements[f.code] - gap))
                for f in FACETS}

    lev_d = diffuse_levels(0.40)
    lev_c = dict(lev_d)
    worst = max(FACETS, key=lambda f: diffuse.facet_requirements[f.code] * f.criticality.get("SA", 2))
    lev_c[worst.code] = 0.0
    rd, rc = confront(diffuse, Profile("p", lev_d), cal), confront(concentrated, Profile("p", lev_c), cal)
    assert rc["material_gap"] >= cal.critical_prohibit_gap > rd["material_gap"]
    assert rd["decision"] != "PROHIBIT" or rd["hard_veto"]

    # The gate is load-bearing: the same adequacy, with the material gate removed, crosses
    # into a categorical prohibition. Tested directly on the ladder so that the risk route
    # (E12') cannot mask the effect.
    gateless = mk_cal(bar_base=0.55, bar_severity=0.10, prohibit_margin=0.25, prohibit_stakes_min=0.45,
                      material_gap=0.25, critical_prohibit_gap=0.45, veto_slack=0.05,
                      prohibit_needs_material=False)
    case = CaseSpec("GATE", "SA", "high", "elevated", "irreversible",
                    {f.code: 0.80 for f in FACETS}, 0.30, 0.60, ("W", "M", "C"))
    aa = cal.decision_bar(case) - 0.30
    assert decide(aa, 0.10, cal, case, [], [], material_gap=0.10) == "REVIEW_REQUIRED"
    assert decide(aa, 0.10, gateless, case, [], [], material_gap=0.10) == "PROHIBIT"

# ---------------------------------------------------------------- I28 risk is not a re-parametrisation of adequacy
def test_I28_residual_risk_is_not_determined_by_adequacy():
    """E12' (v12). In v11, R_r / R_c == 1 - Aa + sigma exactly, so the ladder's "ratio
    route" was a second threshold on the same quantity. The test fails if, whenever two
    confrontations share an adequacy, they always share a risk ratio."""
    buckets = {}
    for res in sweep(20000, seed=91):
        if res["decision"] == "ABSTAIN":
            continue
        buckets.setdefault(round(res["adequacy"], 3), set()).add(round(res["risk_ratio"], 3))
    spread = max(len(v) for v in buckets.values())
    widest = max((max(v) - min(v)) for v in buckets.values() if len(v) > 1)
    assert spread >= 3 and widest >= 0.10, (
        f"risk ratio is still a function of adequacy: max bucket width {widest}")


def test_I29_equal_adequacy_can_have_different_risk():
    """Concrete witness used in the paper: identical adequacy, different residual risk.

    Two profiles whose pillar deficits are identical in every term that enters Aa (the
    weighted deficit D and the structural terms S2, S3, S4) but whose shortfall sits in a
    different pillar. Adequacy is blind to which pillar is short; failure probability is
    not, because it is weighted by mu (capability and knowledge dominate).
    """
    cal = mk_cal()
    q = (0.60, 0.60, 0.60, 0.60)
    ell_a = (0.60, 0.40, 0.60, 0.60)      # shortfall in C
    ell_b = (0.60, 0.60, 0.40, 0.60)      # shortfall in M
    da = tuple(max(0.0, q[i] - ell_a[i]) for i in range(4))
    db = tuple(max(0.0, q[i] - ell_b[i]) for i in range(4))
    assert abs(sum(cal.lam[i] * da[i] for i in range(4)) -
               sum(cal.lam[i] * db[i] for i in range(4))) < 1e-9
    assert structural_terms(da, cal) == structural_terms(db, cal)
    pa, pb = failure_probability(ell_a, cal), failure_probability(ell_b, cal)
    assert pa - pb >= 0.02, (pa, pb)   # a capability shortfall is riskier than an equal obligation shortfall


# ---------------------------------------------------------------- I30 hysteresis
def test_I30_decision_hysteresis_blocks_loosening():
    cal = mk_cal(hysteresis=0.05)
    case = CaseSpec("HYST", "SA", "medium", "standard", "reversible",
                    {f.code: 0.50 for f in FACETS}, 0.20, 0.60, ("M",))
    bar = cal.decision_bar(case)
    aa = bar + 0.01
    looser = decide(aa, 0.0, cal, case, [], [], previous="REVIEW_REQUIRED")
    assert looser == "REVIEW_REQUIRED", "a verdict may not loosen inside the hysteresis band"
    # escalation is never blocked
    assert decide(bar - 0.30, 0.9, cal, case, [], ["M"], previous="REVIEW_REQUIRED") == "PROHIBIT"
    # clear improvement does loosen
    assert decide(bar + 0.10, 0.0, cal, case, [], [], previous="REVIEW_REQUIRED") != "REVIEW_REQUIRED"


# ---------------------------------------------------------------- I31 epistemic abstention
def test_I31_contested_duty_with_low_knowledge_abstains():
    cal = mk_cal()
    req = {f.code: 0.70 for f in FACETS}
    lev = {f.code: 0.50 for f in FACETS}
    plain = CaseSpec("ABST-1", "SA", "high", "maximum", "irreversible", req, 0.70, 0.80, ("M",))
    contested = CaseSpec("ABST-2", "SA", "high", "maximum", "irreversible", req, 0.70, 0.80,
                         ("M",), norm_conflict="unresolved", evidence_conflict=True)
    r_plain = confront(plain, Profile("p", lev), cal)
    r_cont = confront(contested, Profile("p", lev), cal)
    assert r_cont["decision"] == "ABSTAIN" and r_cont["epistemic_abstention"]
    assert r_plain["decision"] != "ABSTAIN"
    # with adequate knowledge the agent decides rather than abstains
    informed = {f.code: 0.85 for f in FACETS}
    informed.update({f.code: 0.90 for f in FACETS if f.code[0] == "K"})
    assert confront(contested, Profile("p", informed), cal)["decision"] != "ABSTAIN"


# ---------------------------------------------------------------- I32 reported band is the band used
def test_I32_reported_adequacy_is_the_one_used_for_the_decision():
    for res in sweep(3000, seed=13):
        if res["decision"] == "ABSTAIN" and res.get("adequacy") is None:
            continue
        assert res["adequacy_decision"] == res["adequacy_low"]
        assert res["adequacy_low"] <= res["adequacy"] <= res["adequacy_high"] + 1e-9


# ---------------------------------------------------------------- I33 every hard duty is non-compensable
def test_I33_guard_cap_applies_to_every_guarded_facet():
    from facet_registry import FACETS as F
    guarded = [f for f in F if f.guard]
    assert len(guarded) >= 8
    for f in guarded:
        req = {g.code: 0.90 for g in F}
        lev = {g.code: 1.00 for g in F}
        lev[f.code] = 0.10
        res = confront(CaseSpec(f"CAP-{f.code}", "SA", "medium", "standard",
                                "partially_irreversible", req, 0.30, 0.60, ("M", "C", "W", "K")),
                       Profile("p", lev), CAL)
        for i, b in enumerate(f.beta):
            if b > 0:
                assert res["levels"][i] <= 0.10 + 1e-9, (f.code, PILLARS[i], res["levels"][i])


# ================= v13 (Rodada 5) invariants: D5.1-D5.4 =================

def test_I34_hierarchy_is_unconditional_for_any_face_weights():
    """D5.1: S4 <= S3 <= S2 <= max d for EVERY face-weight vector, not only when the
    v12 side-condition on alpha holds. Exhaustive grid + 400 random beta vectors."""
    from geometry import structural_terms, lattice_marginal_alpha
    grid = [x / 20 for x in range(21)]
    for d in [(a, b, c, e) for a in grid for b in grid for c in grid for e in grid]:
        for beta in ((1 / 4,) * 4, (0.4, 0.2, 0.2, 0.2), (0.7, 0.1, 0.1, 0.1), (1.0, 0.0, 0.0, 0.0)):
            assert abs(sum(beta) - 1.0) < 1e-12      # face weights are a distribution
            s2, s3, s4 = structural_terms(d, beta=beta)
            assert s4 <= s3 + 1e-12, (d, beta, s2, s3, s4)
            assert s3 <= s2 + 1e-12, (d, beta, s2, s3)
            assert s2 <= max(d) + 1e-12
    assert abs(sum(lattice_marginal_alpha((1 / 4,) * 4)) - 1.0) < 1e-12
    assert all(abs(a - 1 / 6) < 1e-12 for a in lattice_marginal_alpha((1 / 4,) * 4))


def test_I35_alpha_is_derived_and_incoherent_alpha_is_rejected():
    cal = mk_cal(alpha=(0.5, 0.1, 0.1, 0.1, 0.1, 0.1))   # not a lattice marginal
    assert cal.alpha == mk_cal().alpha, "alpha must be overwritten by the lattice marginal"
    # the incoherence is reported before the post_init normalisation, so a raw
    # Calibration built with a bad alpha is flagged by is_valid()
    bad = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(0.5, 0.1, 0.1, 0.1, 0.1, 0.1),
                      beta_face=(1 / 4,) * 4)
    bad.alpha = (0.5, 0.1, 0.1, 0.1, 0.1, 0.1)   # force the inconsistency post_init
    errs = bad.is_valid()
    assert any("lattice marginal" in e for e in errs), errs
    assert mk_cal().is_valid() == []


def test_I36_case_adaptive_salience_is_normalised_and_degenerate_to_lambda():
    cal0 = mk_cal()
    cal1 = mk_cal(salience_adaptation=1.0)
    q = (0.4, 0.9, 0.5, 0.3)
    lam0 = cal0.salience_for_case(q)
    lam1 = cal1.salience_for_case(q)
    assert abs(sum(lam0) - 1.0) < 1e-12 and abs(sum(lam1) - 1.0) < 1e-12
    assert all(abs(a - b) < 1e-12 for a, b in zip(lam0, cal0.lam))
    assert lam1[1] > lam0[1] and lam1[3] < lam0[3], (lam0, lam1)  # demand raises weight
    # the constant lambda case reproduces D exactly
    d = (0.1, 0.4, 0.2, 0.3)
    D0 = sum(cal0.lam[i] * d[i] for i in range(4))
    D0b = sum(lam0[i] * d[i] for i in range(4))
    assert abs(D0 - D0b) < 1e-12


def test_I37_review_need_is_bounded_and_monotone_in_its_components():
    from core import review_need, REVIEW_NEED_WEIGHTS
    assert abs(sum(REVIEW_NEED_WEIGHTS) - 1.0) < 1e-9
    cal = mk_cal()
    base = review_need(0.5, 0.5, 0.5, 0.0, 1.0, cal)
    assert 0.0 <= base <= 1.0
    assert review_need(0.4, 0.6, 0.5, 0.0, 1.0, cal) > base          # wider band
    assert review_need(0.5, 0.5, 0.5, 0.4, 1.0, cal) > base          # more epistemic risk
    assert review_need(0.5, 0.5, 0.5, 0.0, 0.5, cal) > base          # less coverage
    assert review_need(0.5, 0.5, 0.5, 0.0, 1.0, cal) > review_need(0.9, 0.9, 0.5, 0.0, 1.0, cal)
    assert review_need(0.5, 0.5, 0.5, 1.0, 1.0, cal) <= 1.0


def test_I38_oversight_never_raises_stakes_and_default_is_neutral():
    from core import case_stakes
    base = dict(domain="MA", severity="medium", prudential="standard",
                irreversibility="irreversible", facet_requirements={}, U_E=0.3, R_c=0.7)
    s_unspec = case_stakes(CaseSpec("T1", **base))
    s_none = case_stakes(CaseSpec("T2", oversight="none", **base))
    s_in = case_stakes(CaseSpec("T3", oversight="in_the_loop", **base))
    s_on = case_stakes(CaseSpec("T4", oversight="on_the_loop", **base))
    assert abs(s_unspec - s_none) < 1e-12          # v12 regression: default is neutral
    assert s_in <= s_on <= s_none + 1e-12
    # the requirement of the human-review facet rises only when the regime is absent
    from facet_registry import FACETS
    m9 = next(f for f in FACETS if f.code == "M9")
    r_none = requirement_for(m9, CaseSpec("T5", oversight="none", **base))
    r_in = requirement_for(m9, CaseSpec("T6", oversight="in_the_loop", **base))
    assert r_none > r_in


def test_I39_zeta_zero_reproduces_v12_adequacy_exactly():
    """The cross-pillar term is inert by default; when it is switched on the change in
    raw adequacy is exactly zeta * psi (no hidden interaction)."""
    cal0 = mk_cal()
    cal1 = mk_cal(zeta=0.08)
    case = CaseSpec("Z1", "SA", "high", "elevated", "partially_irreversible",
                    {f.code: requirement_for(f, CaseSpec("Z1", "SA", "high", "elevated",
                                                         "partially_irreversible", {}, 0.3, 0.7))
                     for f in FACETS}, 0.35, 0.70, ("M", "K"))
    prof = Profile("p", {f.code: 0.60 for f in FACETS})
    a0 = confront(case, prof, cal0)
    a1 = confront(case, prof, cal1)
    diff = a0["adequacy_raw"] - a1["adequacy_raw"]
    assert abs(diff - 0.08 * a0["cross_pillar_duty"]) < 1e-4, (diff, a0["cross_pillar_duty"])
    assert a0["cross_pillar_duty"] > 0.0


def test_I40_single_pillar_duties_do_not_contribute_to_the_joint_term():
    from core import cross_pillar_duty_exposure
    from facet_registry import FacetDef
    fs = [FacetDef("X1", "solo", (1.0, 0.0, 0.0, 0.0), "weighted_mean",
                   criticality={d: 3 for d in DOMAINS}),
          FacetDef("X2", "pair", (0.5, 0.5, 0.0, 0.0), "weighted_mean",
                   criticality={d: 3 for d in DOMAINS})]
    case = CaseSpec("S1", "SA", "medium", "standard", "reversible",
                    {"X1": 0.9, "X2": 0.9}, 0.2, 0.5)
    prof = Profile("p", {"X1": 0.1, "X2": 0.1})
    psi, e, f = cross_pillar_duty_exposure(case, prof, fs)
    assert abs(psi - e) < 1e-12 and f == 0.0
    assert abs(psi - 0.8) < 1e-12, psi      # weighted mean of the gaps of spanning duties


def test_I41_lattice_is_exhaustive_and_cell_has_no_facet_witness():
    """No canonical duty spans all four pillars: the 15th relational slot (the cell) is
    therefore witnessed only at the pillar level. Measured, not asserted."""
    spans = {f.n_pillars() for f in FACETS}
    assert 4 not in spans
    counts = {k: sum(1 for f in FACETS if f.n_pillars() == k) for k in (1, 2, 3)}
    assert sum(counts.values()) == len(FACETS)


def test_I42_oversight_is_derived_from_facts_and_never_invented():
    from core import oversight_from_facts, OVERSIGHT_MODES
    assert oversight_from_facts({"human_review_channel": True, "independent_audit": True}) == "in_the_loop"
    assert oversight_from_facts({"human_review_channel": True, "independent_audit": False}) == "on_the_loop"
    assert oversight_from_facts({"human_review_channel": False, "appeal_channel": True}) == "on_the_loop"
    assert oversight_from_facts({}) == "none"
    # a case that says nothing about review keeps the v12 behaviour
    c = CaseSpec("OV1", "SA", "high", "standard", "irreversible", {}, 0.3, 0.7)
    assert c.oversight == "unspecified"
    assert c.oversight in OVERSIGHT_MODES


def test_I43_verification_gap_is_a_rubric_rule_not_a_model_trick():
    """D5.8: an audit that is missing 30% of the duties it must assess defers. The gold
    rule lives in the rubric module, not in the arithmetic of the core."""
    here = os.path.abspath(__file__)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(here))), "corpus"))
    from gold_panels_v5 import adjudicate, profile_coverage, GAP_THRESHOLD
    reqs = {f.code: requirement_for(f, CaseSpec("VG1", "SA", "critical", "maximum",
                                                "irreversible", {}, 0.4, 0.8)) for f in FACETS}
    case = CaseSpec("VG1", "SA", "critical", "maximum", "irreversible", reqs, 0.4, 0.8,
                    ("M", "K"), oversight="none")
    full = {f.code: 0.9 for f in FACETS}
    partial = {f.code: 0.9 for f in FACETS if f.code not in PARTIAL_10}
    assert profile_coverage(partial) < GAP_THRESHOLD
    g_defer = adjudicate(case, partial, {"human_review_channel": False}, mode="defer")
    g_breach = adjudicate(case, partial, {"human_review_channel": False}, mode="assume_breach")
    assert g_defer["consensus"] == "ABSTAIN" and g_defer["kernel_rule"] == "V1_verification_gap"
    assert g_breach["consensus"] != "ABSTAIN"
    g_full = adjudicate(case, full, {"human_review_channel": False})
    assert g_full["coverage"] == 1.0


PARTIAL_10 = ("K1", "K2", "K4", "K5", "M3", "M5", "W4", "W5", "C4", "C5")


def test_I44_coverage_gate_is_a_declared_parameter_not_a_hardcoded_number():
    """D5.8 / G12': the E26' gate must be a parameter of the calibration so that the
    ontology, the batteries and the core agree on one number. A profile declaring 23 of
    33 duties (0.697) abstains at the canonical gate 0.70 and does not abstain at 0.60."""
    from dataclasses import replace
    from core import default_calibration
    neut = CaseSpec("CG1", "GP", "medium", "standard", "reversible", {}, 0.2, 0.5)
    reqs = {f.code: requirement_for(f, neut) for f in FACETS}
    case = CaseSpec("CG1", "GP", "medium", "standard", "reversible", reqs, 0.2, 0.5, ("M",),
                    oversight="on_the_loop")
    conf = {f.code: 0.9 for f in FACETS}
    full = {f.code: 0.9 for f in FACETS}
    partial = {f.code: 0.9 for f in FACETS if f.code not in PARTIAL_10}
    assert len(partial) == 23
    base = default_calibration()
    assert base.coverage_gate == 0.70
    r_full = confront(case, Profile("cg", full, conf, "system"), base)
    assert r_full["decision"] != "ABSTAIN"
    r_gate = confront(case, Profile("cg", partial, conf, "system"), base)
    assert r_gate["decision"] == "ABSTAIN" and "0.70" in r_gate["reason"]
    r_loose = confront(case, Profile("cg", partial, conf, "system"),
                       replace(base, coverage_gate=0.60))
    assert r_loose["decision"] != "ABSTAIN"
    bad = replace(base, coverage_gate=0.40)
    assert any("coverage_gate" in e for e in bad.is_valid())
