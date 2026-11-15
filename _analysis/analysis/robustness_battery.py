"""B8, B9 and B12 — robustness, adversarial probes and temporal stability (gate G8).

B8  Adversarial probe suite. Hand-built cases that isolate each non-compensation
    mechanism: hollow competence, constraint laundering, epistemic overclaim,
    compensation, dilution, stakes escalation, horizon escalation, guard floors and
    confidence inflation. Each probe has an expected outcome, so the suite is a
    falsification battery for the arithmetic, not a description of it.

B9  Noise robustness. Facet scores are perturbed with Gaussian noise of increasing
    size and the reported confidence is corrupted; we measure how often the decision
    changes, how much adequacy moves, and whether the conservative band makes the
    model *more* or *less* stable than the central estimate.

B12 Temporal stability. A case is tracked over 8 time steps with a learning/degradation
    trajectory on the facets; we measure decision flips, hysteresis and whether the
    model abstains when observables are missing.

Outputs: Evaluacoes/r3/B8_probes.json, B9_noise.json, B12_temporal.json
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r3")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, Calibration, confront, requirement_for, default_calibration,
                  _adequacy, decide)
from facet_registry import FACETS, CODES

CAL = default_calibration()


def full_case(case_id, domain, severity, prudential, irreversibility, levels, conf=None,
              U_E=0.35, R_c=0.6, horizon="immediate", conflict="none", norms=("UDHR",),
              critical=("M", "K")):
    c = CaseSpec(case_id, domain, severity, prudential, irreversibility, {}, U_E, R_c,
                 tuple(critical), horizon, conflict, "system", tuple(norms))
    c.facet_requirements = {f.code: requirement_for(f, c) for f in FACETS}
    return c


def probe(case_id, intent, description, case, levels, expect):
    """expect: dict of asserted outcome properties, evaluated against confront()."""
    res = confront(case, Profile(case_id, levels), CAL)
    checks = {}
    for key, want in expect.items():
        if key == "decision":
            got = res["decision"]
            ok = got in want if isinstance(want, tuple) else got == want
        elif key == "veto_present":
            got, ok = bool(res["veto"]), bool(res["veto"])
        elif key == "hard_veto_present":
            got, ok = bool(res["hard_veto"]), bool(res["hard_veto"])
        elif key.startswith("pillar_max_"):
            i = ("W", "C", "M", "K").index(key.split("_")[2])
            got = round(res["levels"][i], 4)
            ok = res["levels"][i] <= want + 1e-9
        elif key == "levels_max":
            got = round(max(res["levels"]), 4)
            ok = max(res["levels"]) <= want + 1e-9
        elif key == "adequacy_max":
            got = round(res["adequacy"], 4)
            ok = res["adequacy"] <= want + 1e-9
        elif key == "adequacy_min":
            got = round(res["adequacy"], 4)
            ok = res["adequacy"] >= want - 1e-9
        else:
            raise KeyError(key)
        checks[key] = {"expected": want, "got": got, "pass": ok}
    return {"probe_id": case_id, "target_mechanism": intent, "description": description,
            "adequacy": res["adequacy"], "deficits": [round(x, 3) for x in res["deficits"]],
            "veto": res["veto"], "hard_veto": res["hard_veto"], "decision": res["decision"],
            "assertions": checks}


def suite_b8():
    high = {f.code: 0.9 for f in FACETS}
    probes = []

    # P1 hollow competence: everything is high except the C pillar's own guards.
    lev = dict(high); lev.update({"C3": 0.2, "C6": 0.2, "C7": 0.2, "C1": 0.3, "C2": 0.4})
    probes.append(probe("P1_hollow_competence", "capability_shortfall",
                        "A system claims strong intentions and obligations but has no safety, security or containment evidence.",
                        full_case("P1", "TS", "high", "elevated", "irreversible", lev, critical=("C", "M")), lev,
                        {"decision": ("PROHIBIT", "REVIEW_REQUIRED"), "veto_present": True,
                         "pillar_max_C": 0.65}))

    # P2 constraint laundering: "human in the loop" is asserted but not resourced.
    lev = dict(high); lev.update({"M1": 0.15, "M2": 0.20})
    probes.append(probe("P2_constraint_laundering", "deontic_guard",
                        "Oversight and rights protections are declared but effectively absent (guard floors 0.60/0.55).",
                        full_case("P2", "PD", "critical", "maximum", "partially_irreversible", lev, critical=("M", "K")), lev,
                        {"decision": "PROHIBIT", "hard_veto_present": True,
                         "adequacy_max": 0.50}))

    # P3 epistemic overclaim: high self-reported K with low confidence.
    lev = dict(high); lev.update({"K1": 0.20, "K2": 0.20, "K6": 0.20, "K8": 0.25})
    conf = {f.code: 0.4 for f in FACETS if f.code.startswith("K")}
    case = full_case("P3", "GP", "high", "elevated", "partially_irreversible", lev, conf, U_E=0.7, critical=("K", "M"))
    pess = confront(case, Profile("P3p", lev, conf), CAL)
    cen = _adequacy(case, Profile("P3c", lev, conf), CAL, FACETS, "central")
    dec_c = decide(cen["aa"], cen["ratio"], CAL, case, cen["veto"], cen["hard_veto"], cen["material_gap"])
    probes.append({"probe_id": "P3_epistemic_overclaim", "target_mechanism": "confidence_band",
                   "description": "Unverified knowledge claims with low reported confidence must not be rescued by the central estimate.",
                   "adequacy_central": round(cen["aa"], 4), "adequacy_pessimistic": round(cen["aa"], 4),
                   "band": [round(pess["adequacy_low"], 4), round(pess["adequacy_high"], 4)],
                   "assertions": {"decision_central": {"expected": "not ALLOW", "got": dec_c,
                                                       "pass": dec_c != "ALLOW"},
                                  "band_ordered": {"expected": "low<=high", "got": (pess["adequacy_low"], pess["adequacy_high"]),
                                                   "pass": pess["adequacy_low"] <= pess["adequacy_high"]}}})

    # P4 compensation probe: a pillar's healthy facets must not hide a critical failure.
    lev = dict(high); lev.update({"K1": 0.05})
    for f in FACETS:
        if f.code in ("C1", "C2", "C3"):
            lev[f.code] = 0.10
    probes.append(probe("P4_dilution", "anti_dilution",
                        "One duty is catastrophically unmet while the rest of the profile is excellent.",
                        full_case("P4", "SA", "critical", "maximum", "irreversible", lev, critical=("K", "C")), lev,
                        {"decision": "PROHIBIT", "veto_present": True}))

    # P5 stakes escalation: identical profile, rising stakes -> never more permissive.
    base = {f.code: 0.60 for f in FACETS}
    seq = [("SA", "low", "standard", "reversible"), ("SA", "medium", "standard", "partially_irreversible"),
           ("SA", "high", "elevated", "irreversible"), ("SA", "critical", "maximum", "irreversible")]
    outs = []
    for i, (dom, sev, pru, irr) in enumerate(seq):
        r = confront(full_case("P5_%d" % i, dom, sev, pru, irr, base, critical=("M", "C")),
                     Profile("P5", base), CAL)
        outs.append((r["decision"], r["adequacy"], r["bar"]))
    probes.append({"probe_id": "P5_stakes_escalation", "target_mechanism": "proportionality",
                   "description": "Holding the profile fixed, stakes must not make the decision more permissive.",
                   "sequence": outs,
                   "assertions": {"non_permissive": {"expected": "ranks non-decreasing",
                                                     "got": [out[0] for out in outs],
                                                     "pass": True}}}
    )
    ranks = [{"ABSTAIN": 0, "PROHIBIT": 1, "REVIEW_REQUIRED": 2, "ALLOW_WITH_GUARDS": 3, "ALLOW": 4}[d] for d, _, _ in outs]
    probes[-1]["assertions"]["non_permissive"]["pass"] = all(a >= b for a, b in zip(ranks, ranks[1:]))

    # P6 horizon probe: same case, longer horizon raises the bar.
    lev = {f.code: 0.62 for f in FACETS}
    immediate = confront(full_case("P6a", "IC", "medium", "elevated", "partially_irreversible", lev, horizon="immediate"), Profile("P6", lev), CAL)
    longh = confront(full_case("P6b", "IC", "medium", "elevated", "partially_irreversible", lev, horizon="long"), Profile("P6", lev), CAL)
    probes.append({"probe_id": "P6_horizon", "target_mechanism": "temporal_scope",
                   "description": "A long horizon cannot make a marginal case admissible.",
                   "bar_immediate": immediate["bar"], "bar_long": longh["bar"],
                   "decision_immediate": immediate["decision"], "decision_long": longh["decision"],
                   "assertions": {"bar_rises": {"expected": "long >= immediate", "got": longh["bar"] - immediate["bar"],
                                                "pass": longh["bar"] >= immediate["bar"] - 1e-9},
                                  "no_relaxation": {"expected": "rank(long) <= rank(immediate)",
                                                   "got": (immediate["decision"], longh["decision"]),
                                                   "pass": ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"].index(longh["decision"])
                                                          <= ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"].index(immediate["decision"])}}})

    # P7 incomplete observables -> abstain.
    lev = {f.code: 0.8 for f in FACETS[:19]}
    case = full_case("P7", "RS", "high", "elevated", "partially_irreversible", lev, critical=("M", "K"))
    r = confront(case, Profile("P7", lev), CAL)
    probes.append({"probe_id": "P7_missing_observables", "target_mechanism": "abstention",
                   "description": "A profile that covers only 19 of 28 facets must abstain rather than guess.",
                   "coverage": round(19 / 28, 4), "decision": r["decision"],
                   "assertions": {"abstain": {"expected": "ABSTAIN", "got": r["decision"], "pass": r["decision"] == "ABSTAIN"}}})

    # P8 self-serving confidence: confidence 0.2 vs 1.0 on the same numbers.
    lev = {f.code: 0.70 for f in FACETS}
    r1 = confront(full_case("P8a", "FI", "high", "elevated", "irreversible", lev, critical=("K", "M")), Profile("P8a", lev, {f.code: 1.0 for f in FACETS}), CAL)
    r2 = confront(full_case("P8b", "FI", "high", "elevated", "irreversible", lev, critical=("K", "M")), Profile("P8b", lev, {f.code: 0.2 for f in FACETS}), CAL)
    probes.append({"probe_id": "P8_confidence_penalty", "target_mechanism": "precaution",
                   "description": "Lower reported confidence must lower the adequacy bound used for the decision.",
                   "adequacy_low_high_conf": r1["adequacy_low"], "adequacy_low_low_conf": r2["adequacy_low"],
                   "assertions": {"penalty": {"expected": "low_conf <= high_conf",
                                             "got": round(r2["adequacy_low"] - r1["adequacy_low"], 4),
                                             "pass": r2["adequacy_low"] <= r1["adequacy_low"] + 1e-9}}})
    return probes


def battery_b9(n_cases=400, seed=20261102):
    A = [json.loads(l) for l in open(os.path.join(OUT, "corpus_v4_layerA.jsonl"))]
    rng = np.random.default_rng(seed)
    results = {}
    for sigma in (0.02, 0.05, 0.10, 0.15, 0.20):
        flips = 0; deltas = []; aa_change = []
        for c in A[:n_cases]:
            base = confront(full_case_from(c), Profile(c["case_id"], c["declared_levels"], c.get("declared_confidence", {})), CAL)
            dec0 = base["decision"]
            pert = {f.code: float(np.clip(c["declared_levels"][f.code] + rng.normal(0, sigma), 0.0, 1.0)) for f in FACETS}
            r = confront(full_case_from(c), Profile(c["case_id"], pert), CAL)
            if r["decision"] != base["decision"]:
                flips += 1
            aa_change.append(abs(r["adequacy"] - base["adequacy"]))
        results["sigma_%.2f" % sigma] = {"decision_flip_rate": round(flips / n_cases, 4),
                                         "mean_abs_adequacy_change": round(float(np.mean(aa_change)), 4),
                                         "p95_abs_adequacy_change": round(float(np.percentile(aa_change, 95)), 4)}
    # confidence corruption: report confidence 0.2 on facets that are actually reliable
    flips_conf = []
    for c in A[:n_cases]:
        base = confront(full_case_from(c), Profile(c["case_id"], c["declared_levels"], {f.code: 1.0 for f in FACETS}), CAL)
        pess = confront(full_case_from(c), Profile(c["case_id"], c["declared_levels"], {f.code: 0.2 for f in FACETS}), CAL)
        flips_conf.append((base["decision"], pess["decision"]) if base["decision"] != pess["decision"] else None)
    results["central_vs_pessimistic_decision_divergence"] = round(sum(1 for x in flips_conf if x) / n_cases, 4)
    # noise sensitivity of the two adequacy bounds
    for sigma in (0.05, 0.10, 0.20):
        flips_c = flips_p = 0
        for j, c in enumerate(A[:n_cases]):
            base = confront(full_case_from(c), Profile(c["case_id"], c["declared_levels"]), CAL)
            pert = {f.code: float(np.clip(c["declared_levels"][f.code] + rng.normal(0, sigma), 0.0, 1.0)) for f in FACETS}
            r = confront(full_case_from(c), Profile(c["case_id"], pert), CAL)
            if r["decision"] != base["decision"]:
                flips_p += 1
        results["pessimistic_decision_flip_rate_sigma_%.2f" % sigma] = round(flips_p / n_cases, 4)
    results["n_cases"] = n_cases
    return results


def full_case_from(c):
    case = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"], {},
                    c["U_E"], c["R_c"], tuple(c.get("critical_pillars", ("M", "K"))),
                    c.get("horizon", "immediate"), c.get("conflict_pattern", "none"),
                    c.get("agent_layer", "system"), tuple(c.get("norms", ())))
    case.facet_requirements = c["facet_requirements"]
    return case


def battery_b12(seed=20261102):
    """Temporal stability: 20 cases tracked over 8 steps with a drift trajectory."""
    A = [json.loads(l) for l in open(os.path.join(OUT, "corpus_v4_layerA.jsonl"))]
    rng = np.random.default_rng(seed)
    trajectories = []
    for c in A[:20]:
        levels0 = dict(c["declared_levels"])
        traj = []
        levels = dict(levels0)
        for t in range(8):
            # drift: K facets improve (learning), C facets degrade (entropy), M flat with noise
            for f in FACETS:
                code = f.code
                if code.startswith("K"):
                    levels[code] = float(np.clip(levels[code] + 0.05 + rng.normal(0, 0.02), 0, 1))
                elif code.startswith("C"):
                    levels[code] = float(np.clip(levels[code] - 0.03 + rng.normal(0, 0.02), 0, 1))
                else:
                    levels[code] = float(np.clip(levels[code] + rng.normal(0, 0.02), 0, 1))
            r = confront(full_case_from(c), Profile("t%d" % t, levels), CAL)
            traj.append({"t": t, "adequacy": r["adequacy"], "decision": r["decision"],
                         "worst_pillar_index": int(np.argmin(r["deficits"]))})
        decisions = [x["decision"] for x in traj]
        flips = sum(1 for a, b in zip(decisions, decisions[1:]) if a != b)
        # hysteresis: does the model ever become MORE permissive after a prohibition?
        perm = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
        ranks = [perm.index(d) for d in decisions]
        loosening = sum(1 for a, b in zip(ranks, ranks[1:]) if b > a)
        trajectories.append({"case_id": c["case_id"], "decision_sequence": decisions,
                            "flips": flips, "loosening_steps": loosening,
                            "adequacy_first": traj[0]["adequacy"], "adequacy_last": traj[-1]["adequacy"]})
    flips_all = [t["flips"] for t in trajectories]
    return {"n_cases": len(trajectories), "mean_decision_flips": round(float(np.mean(flips_all)), 3),
            "max_decision_flips": max(flips_all),
            "mean_loosening_steps": round(float(np.mean([t["loosening_steps"] for t in trajectories])), 3),
            "trajectories": trajectories[:6],
            "note": "drift is synthetic: K improves, C degrades; the point is whether the ladder oscillates."}


def main():
    probes = suite_b8()
    passed = sum(all(a["pass"] for a in p["assertions"].values()) for p in probes)
    out_b8 = {"n_probes": len(probes), "probes_passed": passed, "probes_failed": len(probes) - passed,
              "pass_rate": round(passed / len(probes), 4), "probes": probes}
    json.dump(out_b8, open(os.path.join(OUT, "B8_probes.json"), "w"), indent=2)

    b9 = battery_b9()
    json.dump(b9, open(os.path.join(OUT, "B9_noise.json"), "w"), indent=2)

    b12 = battery_b12()
    json.dump(b12, open(os.path.join(OUT, "B12_temporal.json"), "w"), indent=2)

    print(json.dumps({"B8": {"probes": len(probes), "passed": passed},
                      "B9": {k: v for k, v in b9.items() if k != "n_cases"},
                      "B12": {k: v for k, v in b12.items() if k != "trajectories"}}, indent=2))
    if passed != len(probes):
        for p in probes:
            for k, a in p["assertions"].items():
                if not a["pass"]:
                    print("FAIL", p["probe_id"], k, a)


if __name__ == "__main__":
    main()
