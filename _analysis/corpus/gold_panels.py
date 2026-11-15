"""Independent adjudication panels for the ETHCASE gold standard (F4/F5, G6/G7).

Design (deliberate, and documented in the paper):

  * The three panels share a *normative kernel*: the same observable facts
    (guard breaches, worst shortfall in a domain-critical facet, stake-weighted
    mean shortfall, stake level). Without a shared kernel no comparison is
    meaningful - the panels would simply be measuring different quantities.
  * Each panel then applies its own lens on top of the kernel:
      A - deontological: categorical triggers can only escalate (duties are not
          traded away); the panel never de-escalates.
      B - prudential/consequentialist: escalates when the expected-harm budget is
          exceeded, de-escalates when the harm is bounded and reversible.
      C - instrument-anchored: escalates when named external instruments
          (GDPR, Belmont/Helsinki, precaution, ILO, ACM/IEEE) are violated.
  * Consensus = the middle rank; if two ranks are more than one apart apart,
    the precautionary (less permissive) verdict wins.

Traceability: every verdict carries a rule code and a rationale string.
No panel uses beta weights, lambda, the tetrahedron, the veto cap or the
structural terms - i.e. none of the model's own arithmetic.
"""
from facet_registry import FACETS, BY_CODE

RANK = {"ABSTAIN": 0, "PROHIBIT": 1, "REVIEW_REQUIRED": 2, "ALLOW_WITH_GUARDS": 3, "ALLOW": 4}
LABELS = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
SEV_VAL = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.00}
IRR_VAL = {"reversible": 0.0, "partially_irreversible": 0.5, "irreversible": 1.0}
PRU_VAL = {"standard": 0.0, "elevated": 0.05, "maximum": 0.10}
GUARD = tuple(f.code for f in FACETS if f.guard)

try:
    import json, os
    _p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "..", "Evaluacoes", "r3", "gold_rubric_calibration.json")
    PARAMS = json.load(open(_p))["params"] if os.path.exists(_p) else {}
except Exception:
    PARAMS = {}

P = {
    "K_prohibit_crit": PARAMS.get("K_prohibit_crit", 0.50), "K_guard_gap": PARAMS.get("K_guard_gap", 0.20),
    "K_crit": PARAMS.get("K_crit", 0.40), "K_allow": PARAMS.get("K_allow", 0.05),
    "A_guard_gap": PARAMS.get("A_guard_gap", 0.30), "A_stakes": PARAMS.get("A_stakes", 0.60),
    "A_crit_gap": PARAMS.get("A_crit_gap", 0.40), "A_crit_count": PARAMS.get("A_crit_count", 3),
    "B_b0": PARAMS.get("B_b0", 0.08), "B_b1": PARAMS.get("B_b1", 0.18),
    "B_r0": PARAMS.get("B_r0", 0.40), "B_r1": PARAMS.get("B_r1", 0.15),
    "B_trivial": PARAMS.get("B_trivial", 0.04),
    "C_m1": PARAMS.get("C_m1", 0.30), "C_c7": PARAMS.get("C_c7", 0.30),
    "C_m7": PARAMS.get("C_m7", 0.30), "C_m2": PARAMS.get("C_m2", 0.30),
    "C_prohibit": PARAMS.get("C_prohibit", 2), "C_allow": PARAMS.get("C_allow", 0.08),
}


def _gaps(case, levels):
    out = {}
    for f in FACETS:
        req = case.facet_requirements.get(f.code)
        lev = levels.get(f.code)
        if req is None or lev is None:
            continue
        out[f.code] = max(0.0, req - lev)
    return out


def _observables(case, gaps):
    stakes = 0.5 * SEV_VAL[case.severity] + 0.3 * IRR_VAL[case.irreversibility] \
        + 0.2 * (PRU_VAL[case.prudential] / 0.10)
    crit = [g for c, g in gaps.items() if BY_CODE[c].criticality.get(case.domain, 2) == 4]
    guards = {c: g for c, g in gaps.items() if c in GUARD}
    return {
        "stakes": stakes,
        "mean_gap": sum(gaps.values()) / len(gaps),
        "max_gap": max(gaps.values()),
        "crit_max": max(crit) if crit else 0.0,
        "crit_count": sum(1 for g in crit if g > 0.20),
        # A guard is "breached" only when the shortfall is material: a level a
        # hair below the requirement is a shortfall, not a breach of a duty.
        "guard_breaches": [c for c, g in guards.items() if g > P["K_guard_gap"]],
        "guard_worst": max(guards.values()) if guards else 0.0,
        "k1": gaps.get("K1", 0.0), "c7": gaps.get("C7", 0.0),
        "m7": gaps.get("M7", 0.0), "m1": gaps.get("M1", 0.0), "m2": gaps.get("M2", 0.0),
    }


def kernel(case, gaps):
    """Shared normative anchor: identical for all three panels.

    Every lens starts from this verdict and applies only its own correction.
    A lens that ignored the kernel would not be a different perspective on the
    same case, it would be a different question.
    """
    o = _observables(case, gaps)
    if o["crit_max"] > P["K_prohibit_crit"] and o["stakes"] >= 0.60:
        return RANK["PROHIBIT"], "K0", f"worst critical shortfall {o['crit_max']:.3f} at stakes {o['stakes']:.2f}"
    if o["guard_breaches"] or o["crit_max"] > P["K_crit"]:
        return RANK["REVIEW_REQUIRED"], "K1", f"guard breached {o['guard_breaches']} or critical shortfall {o['crit_max']:.3f}"
    if o["max_gap"] <= P["K_allow"]:
        return RANK["ALLOW"], "K2", "no facet falls materially below its requirement"
    return RANK["ALLOW_WITH_GUARDS"], "K3", f"largest residual shortfall {o['max_gap']:.3f}"


def _shift(rank, delta):
    return max(1, min(4, rank + delta))


def panel_A(case, levels):
    """Deontological lens: categorical duty triggers escalate the kernel verdict.

    Duties are not traded against consequences, so this lens never de-escalates;
    it can only make a verdict stricter than the kernel.
    """
    if len(levels) < 20:
        return "ABSTAIN", "A0", "fewer than 20 facets declared"
    gaps = _gaps(case, levels)
    o = _observables(case, gaps)
    rank, code, why = kernel(case, gaps)
    triggers = []
    if o["guard_breaches"] and o["guard_worst"] > P["A_guard_gap"] and o["stakes"] >= P["A_stakes"]:
        triggers.append("A1 duty guard breached materially at high stakes")
    if o["stakes"] >= 0.70 and o["k1"] > 0.40:
        triggers.append("A2 high-stakes action taken without situational knowledge")
    if o["crit_max"] > P["A_crit_gap"] and o["crit_count"] >= P["A_crit_count"]:
        triggers.append("A3 several domain-critical duties unmet")
    if triggers:
        rank, code, why = _shift(rank, -1), "A4", "; ".join(triggers)
    return LABELS[rank], code, why


def panel_B(case, levels):
    """Prudential lens: an expected-harm budget and a red line on the worst shortfall.

    Consequences can be bounded, so this lens is the only one allowed to
    de-escalate, and only when the harm is small, reversible and no guard is
    breached.
    """
    if len(levels) < 20:
        return "ABSTAIN", "B0", "fewer than 20 facets declared"
    gaps = _gaps(case, levels)
    o = _observables(case, gaps)
    rank, code, why = kernel(case, gaps)
    budget = P["B_b0"] + P["B_b1"] * o["stakes"]
    red_line = P["B_r0"] + P["B_r1"] * (1.0 - o["stakes"])
    if o["crit_max"] > red_line and rank > RANK["PROHIBIT"]:
        rank, code, why = RANK["PROHIBIT"], "B1", f"worst critical shortfall {o['crit_max']:.3f} above red line {red_line:.3f}"
    elif o["mean_gap"] > budget and rank > RANK["REVIEW_REQUIRED"]:
        rank, code, why = RANK["REVIEW_REQUIRED"], "B2", f"expected shortfall {o['mean_gap']:.3f} above stake budget {budget:.3f}"
    elif o["mean_gap"] <= P["B_trivial"] and not o["guard_breaches"] and rank >= RANK["ALLOW_WITH_GUARDS"]:
        rank, code, why = RANK["ALLOW"], "B3", f"shortfall {o['mean_gap']:.3f} negligible against budget {budget:.3f}"
    return LABELS[rank], code, why


INSTRUMENT_RULES = (
    ("C1", "data minimisation / purpose limitation (GDPR Art. 5, 25) unmet", "m1",
     {"PD", "FI", "GP", "TB", "IM", "RS", "DS"}),
    ("C2", "precautionary principle (Rio Principle 1): action without containment capacity", "c7",
     {"IC", "MA", "TS", "SA", "DS", "JS"}),
    ("C3", "proportionality and redress (ACM/IEEE 1.5) unmet", "m7",
     {"SA", "JS", "IC", "FI", "PD", "GP", "IM", "ED", "TB", "MA", "TS", "RS", "DS"}),
    ("C4", "human review of automated decision (GDPR Art. 22, ILO) unmet", "m2",
     {"TB", "FI", "GP", "ED", "JS", "SA", "RS"}),
)


def panel_C(case, levels):
    """Instrument-anchored lens: which named instruments the case actually breaches.

    A rule is only applied in the domains the instrument governs; firing it
    outside its scope would be a category error, not an ethical judgement.
    """
    if len(levels) < 20:
        return "ABSTAIN", "C0", "fewer than 20 facets declared"
    gaps = _gaps(case, levels)
    o = _observables(case, gaps)
    rank, code, why = kernel(case, gaps)
    fired = []
    thr = {"m1": P["C_m1"], "c7": P["C_c7"], "m7": P["C_m7"], "m2": P["C_m2"]}
    for rid, text, key, scope in INSTRUMENT_RULES:
        if case.domain not in scope:
            continue
        gap = {"m1": o["m1"], "c7": o["c7"], "m7": o["m7"], "m2": o["m2"]}[key]
        if gap > thr[key]:
            fired.append((rid, text))
    if len(fired) >= P["C_prohibit"]:
        rank, code, why = RANK["PROHIBIT"], "C5", "; ".join(t for _, t in fired)
    elif fired and rank > RANK["REVIEW_REQUIRED"]:
        rank, code, why = RANK["REVIEW_REQUIRED"], "C6", "; ".join(t for _, t in fired)
    elif not fired and o["mean_gap"] <= P["C_allow"] and o["stakes"] <= 0.55 \
            and rank >= RANK["ALLOW_WITH_GUARDS"]:
        rank, code, why = RANK["ALLOW"], "C7", "no instrument trigger; residual shortfall within tolerance"
    return LABELS[rank], code, why


def consensus(*verdicts):
    ranks = [RANK[v] for v in verdicts]
    if len(ranks) == 2:
        if abs(ranks[0] - ranks[1]) <= 1:
            return LABELS[(ranks[0] + ranks[1]) // 2]
        return verdicts[0] if ranks[0] < ranks[1] else verdicts[1]
    lo, mid, hi = sorted(ranks)
    if hi - lo >= 2:
        return LABELS[lo]          # precautionary tie-break
    return LABELS[mid]


def cohens_kappa(a, b):
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa = {c: a.count(c) / n for c in cats}
    pb = {c: b.count(c) / n for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats)
    return 1.0 if pe >= 1 - 1e-12 else (po - pe) / (1 - pe)


def adjudicate(case, levels):
    a, ra, wa = panel_A(case, levels)
    b, rb, wb = panel_B(case, levels)
    c, rc, wc = panel_C(case, levels)
    g = consensus(a, b, c)
    return {"panelA": a, "ruleA": ra, "rationaleA": wa,
            "panelB": b, "ruleB": rb, "rationaleB": wb,
            "panelC": c, "ruleC": rc, "rationaleC": wc,
            "consensus": g, "panels_agree": a == b == c,
            "spread": max(RANK[x] for x in (a, b, c)) - min(RANK[x] for x in (a, b, c))}
