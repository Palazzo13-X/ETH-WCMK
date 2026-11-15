"""B1 - invariants of E30, the fact-grounding rule (decisions D4.21, D4.22).

Run with:  python3 -m pytest tests/test_fact_grounding.py -q
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from facet_registry import FACETS, BY_CODE
from fact_grounding import FACT_MAP, grounded_levels, remedy_factor
from core import CaseSpec, Profile, Calibration, confront, requirement_for

CAL = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                  gamma=0.12, eta=0.05, omega=0.03, rho=0.10, delta=0.05)
rng = np.random.default_rng(2026)


def mk_case(domain="SA", severity="high", prudential="elevated", irr="irreversible"):
    probe = CaseSpec("probe", domain, severity, prudential, irr, {}, 0.4, 0.6, ("M", "K"))
    req = {f.code: requirement_for(f, probe) for f in FACETS}
    return CaseSpec(f"G-{domain}", domain, severity, prudential, irr, req, 0.4, 0.6, ("M", "K"))


def test_G1_grounding_never_raises_a_level():
    for _ in range(4000):
        facts = {f: bool(rng.random() < 0.5) for f in FACT_MAP if f != "remedy_days"}
        facts["remedy_days"] = int(rng.choice([0, 7, 14, 30, 60, 90]))
        case = mk_case()
        levels = {f.code: float(rng.uniform(0.05, 1.0)) for f in FACETS}
        out, caps = grounded_levels(facts, case.facet_requirements, levels)
        assert all(out[c] <= levels[c] + 1e-12 for c in levels), "grounding raised a level"
        assert all(f in facts and code in BY_CODE for f, code, _cap in caps)


def test_G2_satisfied_fact_is_neutral():
    """A fact whose declared compliance is 1.0 introduces no cap of its own: the only
    thing grounding can do through such a fact is the requirement ceiling itself."""
    case = mk_case()
    req = case.facet_requirements
    levels = {f.code: min(0.40, req[f.code]) for f in FACETS}      # below every requirement
    facts = {f: True for f in FACT_MAP if f != "remedy_days"}
    facts["remedy_days"] = 14
    out, caps = grounded_levels(facts, req, levels, strength=1.0)
    neutral = [f for f, (c, sat, _u) in FACT_MAP.items() if sat == 1.0 and f != "prior_incident"]
    for f in neutral:
        assert out[FACT_MAP[f][0]] == levels[FACT_MAP[f][0]]
    assert out["C6"] <= levels["C6"]          # a past incident is not neutral


def test_G3_strength_is_monotone():
    case = mk_case()
    levels = {f.code: 0.90 for f in FACETS}
    facts = {f: False for f in FACT_MAP if f != "remedy_days"}
    facts["remedy_days"] = 0
    req = case.facet_requirements
    prev = None
    for s in (0.0, 0.25, 0.50, 0.75, 1.0):
        out, _ = grounded_levels(facts, req, levels, s)
        tot = sum(out.values())
        assert s == 0.0 or tot <= prev + 1e-9
        prev = tot
    assert abs(sum(grounded_levels(facts, req, levels, 0.0)[0].values()) - 0.90 * len(FACETS)) < 1e-9


def test_G4_grounding_can_only_lower_adequacy():
    case = mk_case()
    levels = {f.code: 0.95 for f in FACETS}
    conf = {f.code: 0.85 for f in FACETS}
    facts = {f: False for f in FACT_MAP if f != "remedy_days"}
    facts["remedy_days"] = 0
    a0 = confront(case, Profile("p", levels, conf, "system"), CAL)["adequacy"]
    grounded, _ = grounded_levels(facts, case.facet_requirements, levels, 1.0)
    a1 = confront(case, Profile("p", grounded, conf, "system"), CAL)["adequacy"]
    assert a1 <= a0
    assert a1 < a0


def test_G5_missing_procedural_fact_trips_the_new_guards():
    """M8 notice, M9 human review and M10 consent are guarded at 0.5: a case that
    declares 0.9 accountability but has no notice, no reviewer and no consent must be
    capped below the guard floor and vetoed."""
    case = mk_case()
    levels = {f.code: 0.90 for f in FACETS}
    conf = {f.code: 0.9 for f in FACETS}
    facts = {"notice_given": False, "human_review_channel": False, "consent_obtained": False,
            "appeal_channel": False, "logs_available": True, "independent_audit": True,
            "remedy_days": 30, "data_minimised": True, "sunset_review": True,
            "containment_exercised": True, "worker_consulted": True,
            "affected_can_exit": True, "prior_incident": False,
            "affected_include_minors": False, "affected_people": 100}
    grounded, caps = grounded_levels(facts, case.facet_requirements, levels, 1.0)
    for code in ("M8", "M9", "M10"):
        assert grounded[code] < 0.50, f"{code} not capped below its guard floor"
    res = confront(case, Profile("p", grounded, conf, "system"), CAL)
    assert res["veto"], "no guard veto raised"
    assert "M" in res["veto"]
    assert res["decision"] in ("PROHIBIT", "REVIEW_REQUIRED", "ABSTAIN")
    # the ungrounded profile of the same case would have passed every guard
    res0 = confront(case, Profile("p", levels, conf, "system"), CAL)
    assert not res0["veto"]


def test_G6_remedy_factor_is_ordered():
    """No redress is worst; a slow redress window is better than none but worse than a prompt one."""
    assert remedy_factor(0) < remedy_factor(60) < remedy_factor(14) <= 1.0
    assert remedy_factor(0) == 0.20


def test_G7_every_corpus_fact_has_an_anchor_or_is_declared_unanchored():
    corpus_facts = {"affected_people", "affected_include_minors", "consent_obtained",
                    "appeal_channel", "notice_given", "prior_incident", "independent_audit",
                    "logs_available", "human_review_channel", "containment_exercised",
                    "sunset_review", "remedy_days", "data_minimised", "worker_consulted",
                    "affected_can_exit", "exposure"}
    anchored = set(FACT_MAP)
    declared = {"exposure", "affected_people", "affected_include_minors"}
    assert corpus_facts - anchored - declared == set()
    assert all(f in FACT_MAP for f in corpus_facts - declared)
    for _f, (code, _a, _b) in FACT_MAP.items():
        assert code in BY_CODE, f"{_f} anchored to a facet that does not exist ({code})"
