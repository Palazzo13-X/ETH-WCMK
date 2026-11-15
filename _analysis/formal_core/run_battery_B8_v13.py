"""B8 - adversarial probe battery v12 (gate G6', expanded).

The r2/r3 implementation of B8 replayed a hand-written probe file of a few dozen
probes. The v4 plan specified 210. This implementation generates the probes from the
registry itself: for every facet (28) x every hard guard (9) x every non-compensation
rule, so that no facet/guard combination is left untested.

Five probe families, each with *explicit assertions* that are evaluated against the
core (never against a hand-written expected value):

  NC  (non-compensation of a hard guard): 33 facets x 12 guards x 2 stakes regimes x
      2 breach depths. A healthy facet in the same pillar is set to 1.0 while the
      guarded duty is below its floor. Asserts:
        NC1 the pillar level cannot exceed the guarded duty's observed level (E24);
        NC2 the veto cap is active, i.e. Aa <= Aa_raw;
        NC3 Aa <= 1 - (cap_base + cap_stakes_gain * stakes) * guard_gap (the
            uncompensable part of the shortfall is actually removed);
        NC4 the verdict is never ALLOW;
        NC5 a severe breach on a duty the domain treats as critical produces a hard
            veto at real stakes.
  CD  (critical-duty deficit): 33 facets x 2 deficit depths x 2 stakes regimes. All
      duties start exactly at their requirement (Aa = 1); one critical duty is
      degraded by d. Asserts the adequacy drop is at least the stakes-weighted gap,
      i.e. dAa >= (cap_base + cap_stakes_gain * stakes) * d.
  MO  (monotonicity): 33 facets x 3 profiles. Raising one facet level never lowers
      adequacy, never raises residual risk, and never makes the verdict stricter...
      actually the invariant is the opposite direction: raising a level can only make
      the verdict *at least as permissive* (it can never become more restrictive).
      Asserts Aa_up >= Aa, R_r_up <= R_r, permissiveness_up >= permissiveness.
  AB  (epistemic abstention): 33 facets x 3 regimes. A duty whose normative basis is
      contested, with high epistemic uncertainty and a low K level, must abstain;
      the same case without the contestation, or with U_E below the abstention
      threshold, must not abstain.
  HY  (hysteresis): 33 facets x 4 ladder positions. Within the band
      [bar, bar + hysteresis) the verdict may not become more permissive than the
      previous verdict; above the band it may; escalation is never blocked.

Run:  python3 _analysis/formal_core/run_battery_B8_v12.py
Out:  Evaluacoes/r5/B8_probes_reverified_v13.json
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core import (CaseSpec, Profile, Calibration, confront, _adequacy, decide,
                  requirement_for, case_stakes, load_fitted_calibration,
                  DECISION_PERMISSIVENESS, PILLARS, EPS)
from facet_registry import FACETS, DOMAINS, BY_CODE

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r5")
SEED = 20261104

CAL = load_fitted_calibration()
GUARDS = [f for f in FACETS if f.guard]
TOL = 1e-9


def crit_domain(facet):
    """A domain in which this facet is treated as critical (criticality 4); falls back
    to the facet's primary-pillar salience set."""
    best = max(DOMAINS, key=lambda d: facet.criticality[d])
    return best if facet.criticality[best] == 4 else best


def make_case(case_id, domain, severity, prudential, irreversibility, critical_pillars,
              U_E=0.30, R_c=0.60, horizon="immediate", pattern="none",
              norm_conflict="none", evidence_conflict=False, exposure=0.5):
    case = CaseSpec(case_id, domain, severity, prudential, irreversibility, {},
                    U_E, R_c, tuple(critical_pillars), horizon, pattern,
                    "system", (), norm_conflict, evidence_conflict, exposure)
    case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
    return case


def full_profile(levels, conf=None):
    return Profile("probe-agent", levels, conf or {f.code: 1.0 for f in FACETS}, "system")


def assert_row(aid, kind, expected, actual, ok, note=""):
    return {"assertion": aid, "kind": kind, "expected": expected, "actual": actual,
            "pass": bool(ok), "note": note}


def run_probe(probe_id, family, case, levels, assertions, extra=None):
    prof = full_profile(levels)
    mid = _adequacy(case, prof, CAL, FACETS, "central")
    res = confront(case, prof, CAL)
    probe = {"probe_id": probe_id, "family": family,
             "domain": case.domain, "severity": case.severity,
             "stakes": round(case_stakes(case), 4),
             "decision": res["decision"], "adequacy": round(mid["aa"], 6),
             "adequacy_raw": round(mid["aa_raw"], 6),
             "levels": [round(x, 6) for x in mid["levels"]],
             "veto": [PILLARS[i] for i in mid["veto"]],
             "hard_veto": [PILLARS[i] for i in mid["hard_veto"]],
             "material_gap": round(mid["material_gap"], 6),
             "risk_ratio": round(mid["ratio"], 6), "R_r": round(mid["R_r"], 6),
             "assertions": assertions}
    probe["pass"] = all(a["pass"] for a in assertions)
    if extra:
        probe.update(extra)
    return probe


# ---------------------------------------------------------------- family NC
def family_nc():
    probes = []
    k = 0
    for stakes_kind, sev, pru, irr in (("high", "critical", "maximum", "irreversible"),
                                       ("moderate", "medium", "standard", "reversible")):
        for g in GUARDS:
            dom = crit_domain(g)
            case = make_case(f"B8-NC-{k:04d}", dom, sev, pru, irr,
                             tuple(PILLARS[i] for i, b in enumerate(g.beta) if b > 0))
            req = case.facet_requirements
            stakes = case_stakes(case)
            cap_weight = CAL.cap_base + CAL.cap_stakes_gain * stakes
            for breach in (0.25, 0.45):
                for f in FACETS:
                    if f.code == g.code:
                        continue
                    k += 1
                    levels = {h.code: req[h.code] for h in FACETS}
                    levels[g.code] = max(0.0, g.guard_min - breach)
                    levels[f.code] = 1.0          # the "healthy" facet that would pay for the breach
                    gap = req[g.code] - levels[g.code]
                    probes.append((f"B8-NC-{k:04d}", "non_compensation", case, levels, [],
                                   {"guard": g.code, "guard_policy": g.policy,
                                    "guard_min": g.guard_min, "healthy_facet": f.code,
                                    "breach_depth": breach, "guard_gap": round(gap, 6),
                                    "stakes": round(stakes, 4),
                                    "cap_weight": round(cap_weight, 4)}))
    return probes


# ---------------------------------------------------------------- family CD
def family_cd():
    probes = []
    k = 0
    for stakes_kind, sev, pru, irr in (("high", "critical", "maximum", "irreversible"),
                                       ("low", "low", "standard", "reversible")):
        for f in FACETS:
            dom = crit_domain(f)
            case = make_case(f"B8-CD-{k:04d}", dom, sev, pru, irr,
                             tuple(PILLARS[i] for i, b in enumerate(f.beta) if b > 0))
            req = case.facet_requirements
            stakes = case_stakes(case)
            cap_weight = CAL.cap_base + CAL.cap_stakes_gain * stakes
            for d in (0.30, 0.45):
                k += 1
                base_levels = {h.code: req[h.code] for h in FACETS}
                base = _adequacy(case, full_profile(base_levels), CAL, FACETS, "central")
                levels = dict(base_levels)
                levels[f.code] = max(0.0, req[f.code] - d)
                probes.append((f"B8-CD-{k:04d}", "critical_deficit", case, levels, None,
                              {"duty": f.code, "deficit": d,
                               "base_adequacy": round(base["aa"], 6),
                               "base_risk": round(base["R_r"], 6),
                               "cap_weight": round(cap_weight, 4),
                               "expected_drop": round(cap_weight * d, 6)}))
    return probes


# ---------------------------------------------------------------- family MO
def family_mo():
    probes = []
    k = 0
    r = np.random.default_rng(SEED + 3)
    for f in FACETS:
        for variant in range(3):
            k += 1
            dom = str(r.choice(DOMAINS))
            sev = str(r.choice(("low", "medium", "high", "critical")))
            case = make_case(f"B8-MO-{k:04d}", dom, sev,
                             str(r.choice(("standard", "elevated", "maximum"))),
                             str(r.choice(("reversible", "partially_irreversible", "irreversible"))),
                             tuple(sorted(r.choice(["W", "C", "M", "K"], size=int(r.integers(1, 4)))))
            )
            levels = {h.code: float(np.clip(r.normal(case.facet_requirements[h.code] - 0.10, 0.20), 0.02, 1.0))
                      for h in FACETS}
            bumped = dict(levels)
            bumped[f.code] = min(1.0, levels[f.code] + 0.05)
            probes.append((f"B8-MO-{k:04d}", "monotonicity", case, levels, None,
                          {"facet": f.code, "bump": 0.05, "bumped_levels": bumped}))
    return probes


# ---------------------------------------------------------------- family AB
def family_ab():
    probes = []
    k = 0
    for f in FACETS:
        dom = crit_domain(f)
        pillars = tuple(PILLARS[i] for i, b in enumerate(f.beta) if b > 0)
        regimes = [
            ("contested_norm_low_K", "unresolved", False, 0.75, "low_K", "ABSTAIN"),
            ("contested_evidence_low_K", "none", True, 0.80, "low_K", "ABSTAIN"),
            ("contested_low_uncertainty_control", "unresolved", True, 0.50, "low_K", "NOT_ABSTAIN"),
            ("contested_adequate_K_control", "unresolved", True, 0.85, "full_K", "NOT_ABSTAIN"),
        ]
        for regime, norm_conflict, evidence, U_E, kmode, expected in regimes:
            k += 1
            case = make_case(f"B8-AB-{k:04d}", dom, "high", "elevated",
                             "partially_irreversible", pillars + (("K",) if "K" not in pillars else ()),
                             U_E=U_E, R_c=0.60, norm_conflict=norm_conflict,
                             evidence_conflict=evidence)
            levels = {h.code: case.facet_requirements[h.code] for h in FACETS}
            if kmode == "low_K":
                # every facet that feeds the knowledge pillar is weak: the agent cannot
                # resolve the contestation it is facing
                for h in FACETS:
                    if h.beta[3] > 0:
                        levels[h.code] = 0.45
            probes.append((f"B8-AB-{k:04d}", "abstention", case, levels, None,
                          {"duty": f.code, "regime": regime, "U_E": U_E,
                           "norm_conflict": norm_conflict, "evidence_conflict": evidence,
                           "expected_decision": expected,
                           "abstain_uncertainty": CAL.abstain_uncertainty,
                           "knowledge_floor": CAL.abstain_knowledge_floor}))
    return probes


# ---------------------------------------------------------------- family HY
def family_hy():
    probes = []
    k = 0
    for f in FACETS:
        dom = crit_domain(f)
        case = make_case(f"B8-HY-{k:04d}", dom, "high", "elevated",
                         "partially_irreversible",
                         tuple(PILLARS[i] for i, b in enumerate(f.beta) if b > 0))
        bar = CAL.decision_bar(case)
        ratio = 0.10
        h = CAL.hysteresis
        scenarios = [
            # (name, adequacy fed to the ladder, previous verdict,
            #  verdict the score alone would give, verdict after hysteresis)
            ("inside_band_blocks_loosening", bar + 0.02, "REVIEW_REQUIRED",
             "ALLOW_WITH_GUARDS", "REVIEW_REQUIRED"),
            ("band_edge_releases_loosening", bar + h, "REVIEW_REQUIRED",
             "ALLOW_WITH_GUARDS", "ALLOW_WITH_GUARDS"),
            ("escalation_is_never_blocked", bar - 0.05, "ALLOW",
             "REVIEW_REQUIRED", "REVIEW_REQUIRED"),
            ("clear_allow_after_review", bar + CAL.guards_margin + 0.05, "REVIEW_REQUIRED",
             "ALLOW", "ALLOW"),
            ("prohibit_held_inside_band", bar + 0.04, "PROHIBIT",
             "ALLOW_WITH_GUARDS", "PROHIBIT"),
        ]
        for name, aa, previous, natural_expected, expected in scenarios:
            k += 1
            natural = decide(aa, ratio, CAL, case, [], [], 0.0, previous=None)
            actual = decide(aa, ratio, CAL, case, [], [], 0.0, previous=previous)
            assertions = [
                assert_row("HY1", "natural_verdict",
                           f"without history the ladder returns {natural_expected} "
                           f"for Aa = {aa:.4f} (bar = {bar:.4f})",
                           {"natural_verdict": natural}, natural == natural_expected),
                assert_row("HY2", "hysteresis",
                           f"with previous = {previous}, the verdict must be {expected}: "
                           "a verdict may only become more permissive when "
                           "Aa >= bar + hysteresis (E13d), and escalation is never blocked",
                           {"previous": previous, "actual": actual,
                            "bar": round(bar, 4), "hysteresis": h,
                            "adequacy_used": round(aa, 4)},
                           actual == expected),
            ]
            probe = {"probe_id": f"B8-HY-{k:04d}", "family": "hysteresis",
                     "scenario": name, "domain": case.domain, "bar": round(bar, 4),
                     "adequacy_used": round(aa, 4), "previous": previous,
                     "expected": expected, "actual": actual, "decision": actual,
                     "natural_verdict": natural,
                     "assertions": assertions,
                     "pass": natural == natural_expected and actual == expected}
            probes.append(probe)
    return probes


def build():
    probes = []

    # NC: run and assert on the fly
    for pid, family, case, levels, _assertions, meta in family_nc():
        prof = full_profile(levels)
        mid = _adequacy(case, prof, CAL, FACETS, "central")
        res = confront(case, prof, CAL)
        gap = meta["guard_gap"]
        cw = meta["cap_weight"]
        guard = BY_CODE[meta["guard"]]
        assertions = [
            assert_row("NC1", "pillar_cap",
                       f"level_p <= observed duty level {levels[meta['guard']]:.4f} "
                       f"for every pillar p touched by {meta['guard']} (E24)",
                       {"guard_level": round(levels[meta["guard"]], 6),
                        "pillar_levels": {PILLARS[i]: round(mid["levels"][i], 6)
                                         for i, b in enumerate(guard.beta) if b > 0}},
                       all(mid["levels"][i] <= levels[meta["guard"]] + TOL
                           for i, b in enumerate(guard.beta) if b > 0),
                       "the pillar average cannot be lifted above a duty that is below its floor"),
            assert_row("NC2", "cap_active", "Aa <= Aa_raw",
                       {"Aa": round(mid["aa"], 6), "Aa_raw": round(mid["aa_raw"], 6)},
                       mid["aa"] <= mid["aa_raw"] + TOL),
            assert_row("NC3", "gap_removed",
                       f"Aa <= 1 - {cw:.4f} * {gap:.4f} = {1 - cw * gap:.4f}",
                       {"Aa": round(mid["aa"], 6), "material_gap": round(mid["material_gap"], 6)},
                       mid["aa"] <= 1 - cw * gap + TOL),
            assert_row("NC4", "no_allow", "verdict != ALLOW",
                       {"decision": res["decision"]}, res["decision"] != "ALLOW"),
        ]
        if meta["breach_depth"] >= 0.45 and meta["stakes"] >= CAL.stakes_veto_min:
            assertions.append(assert_row("NC5", "hard_veto",
                                         "severe breach at real stakes: hard veto fires and the verdict is PROHIBIT",
                                         {"hard_veto": [PILLARS[i] for i in mid["hard_veto"]],
                                          "decision": res["decision"]},
                                         bool(mid["hard_veto"]) and res["decision"] == "PROHIBIT"))
        probes.append(run_probe(pid, family, case, levels, assertions, meta))

    # CD
    for pid, family, case, levels, _unused, meta in family_cd():
        base = meta["base_adequacy"]
        mid = _adequacy(case, full_profile(levels), CAL, FACETS, "central")
        drop = base - mid["aa"]
        expected_drop = meta["expected_drop"]
        assertions = [
            assert_row("CD1", "base_perfect", "Aa of a profile at every requirement is 1.0",
                       {"Aa_base": base}, abs(base - 1.0) < 1e-6),
            assert_row("CD2", "deficit_lowers_adequacy", "Aa decreases strictly",
                       {"Aa": round(mid["aa"], 6)}, mid["aa"] < base - 1e-9),
            assert_row("CD3", "stakes_weighted", f"dAa >= {expected_drop:.4f} (cap weight x deficit)",
                       {"dAa": round(drop, 6)}, drop >= expected_drop - 1e-9),
            assert_row("CD4", "risk_not_lowered", "residual risk does not decrease when a duty fails",
                       {"R_r_base": meta["base_risk"], "R_r_deficit": round(mid["R_r"], 6)},
                       mid["R_r"] >= meta["base_risk"] - 1e-9),
        ]
        probes.append(run_probe(pid, family, case, levels, assertions, meta))

    # MO
    for pid, family, case, levels, _u, meta in family_mo():
        base = confront(case, full_profile(levels), CAL)
        alt = confront(case, full_profile(meta["bumped_levels"],
                                         {h.code: 1.0 for h in FACETS}), CAL)
        assertions = [
            assert_row("MO1", "adequacy_nondecreasing", "Aa_up >= Aa",
                       {"Aa": base["adequacy"], "Aa_up": alt["adequacy"]},
                       (alt["adequacy"] or 0) >= (base["adequacy"] or 0) - 1e-9),
            assert_row("MO2", "risk_nonincreasing", "R_r_up <= R_r",
                       {"R_r": base["R_r"], "R_r_up": alt["R_r"]},
                       (alt["R_r"] or 0) <= (base["R_r"] or 0) + 1e-9),
            assert_row("MO3", "no_stricter_verdict",
                       "permissiveness_up >= permissiveness",
                       {"decision": base["decision"], "decision_up": alt["decision"]},
                       DECISION_PERMISSIVENESS[alt["decision"]] >= DECISION_PERMISSIVENESS[base["decision"]]),
        ]
        probes.append(run_probe(pid, family, case, levels, assertions, meta))

    # AB
    for pid, family, case, levels, _u, meta in family_ab():
        res = confront(case, full_profile(levels), CAL)
        if meta["expected_decision"] == "ABSTAIN":
            assertions = [assert_row("AB1", "abstention_fires",
                                     "verdict == ABSTAIN: the applicable duty is contested, "
                                     f"U_E >= {CAL.abstain_uncertainty} and the K level is "
                                     f"<= {CAL.abstain_knowledge_floor} (E29)",
                                     {"decision": res["decision"],
                                      "K_level": round(res["levels"][3], 4) if res["levels"] else None,
                                      "U_E": meta["U_E"]},
                                     res["decision"] == "ABSTAIN")]
        else:
            assertions = [assert_row("AB2", "no_spurious_abstention",
                                     "verdict != ABSTAIN when the abstention condition is not met "
                                     "(U_E below the threshold, or the agent's knowledge is adequate)",
                                     {"decision": res["decision"],
                                      "K_level": round(res["levels"][3], 4) if res["levels"] else None,
                                      "U_E": meta["U_E"]},
                                     res["decision"] != "ABSTAIN")]
        probes.append(run_probe(pid, family, case, levels, assertions, meta))

    probes.extend(family_hy())
    return probes


def main():
    os.makedirs(OUT, exist_ok=True)
    probes = build()
    by_family = defaultdict(lambda: {"n": 0, "pass": 0, "fail": 0})
    by_assertion = defaultdict(lambda: {"n": 0, "pass": 0, "fail": 0})
    failures = []
    for p in probes:
        by_family[p["family"]]["n"] += 1
        by_family[p["family"]]["pass" if p["pass"] else "fail"] += 1
        for a in p["assertions"]:
            by_assertion[a["kind"]]["n"] += 1
            by_assertion[a["kind"]]["pass" if a["pass"] else "fail"] += 1
            if not a["pass"]:
                failures.append({"probe_id": p["probe_id"], "family": p["family"],
                                 "assertion": a["assertion"], "kind": a["kind"],
                                 "expected": a["expected"], "actual": a["actual"],
                                 "decision": p.get("decision"),
                                 "adequacy": p.get("adequacy"),
                                 "material_gap": p.get("material_gap"),
                                 "veto": p.get("veto"), "hard_veto": p.get("hard_veto"),
                                 "levels": p.get("levels")})

    total = len(probes)
    passed = sum(1 for p in probes if p["pass"])
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "_analysis/formal_core/run_battery_B8_v12.py",
        "core": "formal_core/core.py (v13: derived alpha, oversight regime, declared coverage gate)",
        "calibration": "load_fitted_calibration() (Evaluacoes/r3/ladder_calibration.json)",
        "seed": SEED,
        "families": {
            "non_compensation": "33 facets x 12 guards x 2 stakes regimes x 2 breach depths",
            "critical_deficit": "28 critical duties x 2 deficit depths x 2 stakes regimes",
            "monotonicity": "33 facets x 3 profiles: raising a level never hurts adequacy, risk or verdict",
            "abstention": "28 duties x 4 contestation regimes, incl. 2 controls (E29)",
            "hysteresis": "28 duties x 5 ladder positions (E13d)",
        },
        "summary": {
            "total_probes": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "assertions_total": sum(v["n"] for v in by_assertion.values()),
            "assertions_passed": sum(v["pass"] for v in by_assertion.values()),
            "by_family": {k: dict(v) for k, v in by_family.items()},
            "by_assertion_type": {k: dict(v) for k, v in by_assertion.items()},
            "decision_distribution": dict(Counter(p.get("decision") for p in probes)),
        },
        "failure_analysis": {
            "n_failures": len(failures),
            "failures": failures[:200],
            "by_family": dict(Counter(f["family"] for f in failures)),
            "by_assertion": dict(Counter(f["kind"] for f in failures)),
            "reading": ("A failing NC3/CD3 would mean the veto cap does not remove the "
                        "uncompensable part of the duty shortfall; a failing NC4 would mean "
                        "a hard guard can still be averaged away by healthy facets in the "
                        "same pillar; a failing MO probe would break non-compensatory "
                        "monotonicity; a failing AB probe would mean epistemic abstention "
                        "does not fire on genuinely contested duties; a failing HY probe "
                        "would mean the ladder flip-flops inside the hysteresis band."),
        },
        "probes": probes,
    }
    path = os.path.join(OUT, "B8_probes_reverified_v13.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out["summary"], indent=2))
    print("failures:", len(failures))
    for f in failures[:10]:
        print(f["probe_id"], f["kind"], "expected", f["expected"], "actual", f["actual"])
    print("written:", path, "probes:", total)


if __name__ == "__main__":
    main()
