"""Gold adjudication panel for the ETH-WCMK corpus (F4).

There are no human raters in this study. The gold labels are produced by a
documented, transparent rule panel that is *deliberately different in logic*
from the formal core: it uses no beta weights, no lambda weights, no tetrahedron
and no structural terms. It reads only (a) the case attributes and (b) the raw
declared level of named facets, applying threshold-and-count logic taken from
standard risk-governance practice (precaution, rights-based veto, auditability).

Because the two procedures share the same inputs but not the arithmetic,
agreement between them is a real coherence test rather than a tautology. Divergence
is expected in the intermediate band; the panel is not ground truth for moral
competence, only an external adjudication benchmark.

Rules are evaluated in order; the first match wins.
"""
from core import CaseSpec
from facet_registry import BY_CODE, FACETS

# facets named by the panel (canonical codes from the v10 registry)
NORMATIVE = ("M1", "M3", "M4")
SITUATION = ("K1", "K2")
CAPABILITY = ("C1", "C3")


def level(levels, code):
    return levels.get(code)


def critical_facets(case):
    dom = case.domain
    return [f for f in FACETS if f.criticality.get(dom, 2) == 4]


def gap(levels, req, code):
    r = req.get(code, 0.0)
    v = levels.get(code)
    if v is None:
        return None
    return r - v


def panel_decision(case: CaseSpec, levels: dict):
    req = case.facet_requirements
    crit = critical_facets(case)
    gaps = [g for g in (gap(levels, req, f.code) for f in crit) if g is not None]
    if len(levels) < 20:
        return "ABSTAIN", "P0", "profile declares fewer than 20 facets"

    # P1 - categorical normative failure: a legal/rights duty far below requirement
    for code in NORMATIVE:
        v, r = level(levels, code), req.get(code, 0.0)
        if v is not None and r >= 0.80 and v < 0.40:
            return "PROHIBIT", "P1", f"{code} level {v:.2f} against requirement {r:.2f}"

    # P2 - no situation model in a high-stakes case
    if case.severity in ("high", "critical"):
        v = level(levels, "K1")
        if v is not None and v < 0.30:
            return "PROHIBIT", "P2", "no adequate representation of the situation"

    # P3 - irreversible critical harm without demonstrated executable capability
    if case.severity == "critical" and case.irreversibility == "irreversible":
        v = level(levels, "C1")
        if v is not None and v < 0.50:
            return "PROHIBIT", "P3", "irreversible critical action without verified capability"

    # P4 - guarded facet below its documented floor
    for f in FACETS:
        if f.guard and level(levels, f.code) is not None and level(levels, f.code) < f.guard_min:
            return "REVIEW_REQUIRED", "P4", f"{f.code} below guard floor {f.guard_min}"

    # P5 - several critical facets short of requirement
    if gaps and sum(1 for g in gaps if g > 0.25) >= 3:
        return "REVIEW_REQUIRED", "P5", "three or more critical facets unmet"

    # P6 - low-stakes, reversible, essentially compliant
    if case.severity == "low" and case.irreversibility == "reversible":
        if not gaps or max(gaps) <= 0.10:
            return "ALLOW", "P6", "low stakes, reversible, no material shortfall"
        return "ALLOW_WITH_GUARDS", "P7", "low stakes but material shortfall"

    # P8 - medium stakes with small shortfalls
    if case.severity == "medium" and gaps and max(gaps) <= 0.20:
        return "ALLOW_WITH_GUARDS", "P8", "medium stakes, shortfalls within tolerance"

    # P9 - irreversible action of any severity needs oversight
    if case.irreversibility != "reversible":
        return "REVIEW_REQUIRED", "P9", "irreversible consequences require oversight"

    return "REVIEW_REQUIRED", "P10", "default: oversight"
