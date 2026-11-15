"""E30 - Fact grounding of declared facet levels (decision D4.21, v12).

The model's input is a *declared* profile: levels the agent or its operator reports for
each facet. A verifiable fact about the case is an observation that constrains the level
a facet can have, independently of what the agent reports. Without this rule, 75.8% of
the prohibitions the normative panel issues (Evaluacoes/r4/corpus_v5_confusion_analysis.json)
are invisible to the arithmetic: the panel sees "no audit trail", the model sees an
accountability level of 0.9 because the persona declared it.

Rule:
    ell_f = min(ell_f, q_f * c(fact))
where c(fact) is the compliance factor declared below. The mapping is exhaustive for the
procedural facts carried by the corpus; facts without a facet anchor are listed in
UNANCHORED_FACTS and are the reason the panel and the model diverge.

`strength` is a sensitivity knob used in the calibration sweep: strength = 1 applies the
declared compliance factors; strength = 0 reproduces the ungrounded v11 behaviour.
"""
from facet_registry import BY_CODE

# fact -> (facet code, compliance if the fact is satisfied, compliance if not)
FACT_MAP = {
    "logs_available":        ("M6", 1.00, 0.25),
    "independent_audit":     ("M6", 1.00, 0.55),
    "notice_given":          ("M8", 1.00, 0.30),
    "human_review_channel":  ("M9", 1.00, 0.30),
    "appeal_channel":        ("M9", 1.00, 0.40),   # an appeal route is a review channel
    "remedy_days":           ("M7", 1.00, 0.20),   # handled by remedy_factor()
    "consent_obtained":      ("M10", 1.00, 0.30),
    "data_minimised":        ("C8", 1.00, 0.45),
    "sunset_review":         ("K9", 1.00, 0.50),
    "containment_exercised": ("C7", 1.00, 0.30),
    "worker_consulted":      ("M10", 1.00, 0.60),
    "affected_can_exit":     ("C3", 1.00, 0.50),
    "prior_incident":        ("C6", 0.70, 1.00),   # a past incident lowers safe executability
    "affected_include_minors": ("M10", 1.00, 1.00),  # only raises the requirement, see below
}

# Facts that carry normative weight in the panel but have no facet to anchor them.
UNANCHORED_FACTS = {
    "affected_people": "scale of those affected enters only through the exposure term E12'",
}


def remedy_factor(days):
    if days == 0:
        return 0.20
    if days > 30:
        return 0.50
    return 0.85


def fact_compliance(fact, value):
    if fact == "remedy_days":
        return remedy_factor(value)
    _code, sat, unsat = FACT_MAP[fact]
    return sat if value else unsat


def grounded_levels(facts, requirements, levels, strength=1.0):
    """Apply E30. Returns (levels, list of (fact, facet, cap) for the caps that bite)."""
    out = dict(levels)
    applied = []
    for fact, (code, _sat, _unsat) in FACT_MAP.items():
        if fact not in facts or code not in BY_CODE:
            continue
        c = fact_compliance(fact, facts[fact])
        cap = requirements[code] * (1.0 - strength * (1.0 - c))
        # E26': a facet the agent never reported has no level to cap; the absence is
        # recorded as missing coverage, not as a grounded zero.
        if code in out and out[code] > cap:
            out[code] = cap
            applied.append((fact, code, round(cap, 4)))
    return out, applied
