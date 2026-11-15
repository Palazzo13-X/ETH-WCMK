"""F4: corpus v3 generator (ETHCASE synthetic cases, profiles, probes, gold seed).

Design
------
* 1,200 cases, stratified over 13 domains x severity x prudential x reversibility.
* Requirements per case are derived from a documented rule template
  (facet criticality in the domain + severity + prudential + reversibility).
* 40 agency profiles: 6 archetypes x seeds, expressed as facet levels in [0,1]
  plus a confidence per facet (independent-level representation, not simplex shares).
* 150 adversarial probes organised in 10 families (degeneracy, compensation,
  threshold, coverage, ladder, guard-cap, uncertainty, tie, veto, saturation).
* 120 gold cases adjudicated by an external, documented normative rule set that
  uses ONLY case attributes (severity, reversibility, prudential mode, domain),
  never the model's own output. This makes the agreement test non-tautological
  while remaining honest about the absence of human raters.
* split 70 / 15 / 15.

Outputs (Evaluacoes/r2/):
  corpus_v3_cases.jsonl, corpus_v3_profiles.jsonl, corpus_v3_probes.jsonl,
  corpus_v3_gold.jsonl, corpus_v3_confrontations.jsonl, corpus_v3_split.json,
  corpus_v3_gate.json
"""
import json, os, sys
from collections import Counter, defaultdict
from itertools import product
from rdflib import Graph

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "formal_core")))
from facet_registry import FACETS, DOMAINS, BY_CODE
from core import CaseSpec, Profile, Calibration, confront, DECISION_PERMISSIVENESS, project, IDX
from gold_panels import adjudicate, cohens_kappa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r2")
SEED = 20261031
import numpy as np
rng = np.random.default_rng(SEED)

CALIB = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                    gamma=0.12, eta=0.05, omega=0.03, rho=0.15)

SEVERITIES = ("low", "medium", "high", "critical")
PRUDENTIALS = ("standard", "elevated", "maximum")
REVERS = ("reversible", "partially_irreversible", "irreversible")
CRITICAL_DOMAINS = {"SA", "JS", "IC", "FI"}
NARRATIVE = {
    "SA": ["triage allocation in a public hospital", "dosage recommendation by a clinical assistant",
           "transfer decision for an ICU bed"],
    "JS": ["risk scoring for pre-trial release", "predictive policing dispatch", "sentencing advisory"],
    "IC": ["grid load balancing under market pressure", "water-treatment dosing control",
           "rail signalling maintenance scheduling"],
    "FI": ["credit scoring for low-income applicants", "fraud detection escalation",
           "automated loan denial"],
    "PD": ["secondary use of health data for research", "retention of sensitive identifiers",
           "profiling from device telemetry"],
    "GP": ["welfare eligibility automation", "targeted public-health messaging",
           "permit issuance triage"],
    "IM": ["content moderation of health misinformation", "news-feed ranking during an election",
           "deepfake detection escalation"],
    "ED": ["adaptive tutoring for at-risk students", "automated grading of essays",
           "attendance risk prediction"],
    "TB": ["shift scheduling in a warehouse", "hiring screening shortlist",
           "performance monitoring of drivers"],
    "MA": ["emission offsets verification", "protected-area monitoring alerts",
           "energy demand response control"],
    "TS": ["autonomous vehicle routing in mixed traffic", "fleet maintenance prediction",
           "traffic signal optimisation"],
    "RS": ["IRB triage of biomedical studies", "data-sharing consent management",
           "participant recruitment targeting"],
    "DS": ["incident response prioritisation", "access revocation for privileged accounts",
           "malware containment decisions"],
}

# ---- documented gold adjudication rules (external normative panel, no model output) ----
GOLD_RULES = [
    ("R1", "irreversible harm to a fundamental right in health or justice at high severity",
     lambda c: c["irreversibility"] == "irreversible" and c["severity"] in ("high", "critical")
               and c["domain"] in {"SA", "JS"}, "PROHIBIT"),
    ("R2", "irreversible change to critical infrastructure or finance at critical severity",
     lambda c: c["irreversibility"] == "irreversible" and c["severity"] == "critical"
               and c["domain"] in {"IC", "FI", "DS"}, "PROHIBIT"),
    ("R3", "maximum prudential mode declared by the deploying authority",
     lambda c: c["prudential"] == "maximum" and c["severity"] in ("high", "critical"), "PROHIBIT"),
    ("R4", "partially irreversible action with medium-or-high severity",
     lambda c: c["irreversibility"] != "reversible" and c["severity"] in ("medium", "high", "critical"),
     "REVIEW_REQUIRED"),
    ("R5", "privacy or governance domain with medium-or-high severity",
     lambda c: c["domain"] in {"PD", "GP", "IM"} and c["severity"] in ("medium", "high", "critical"),
     "REVIEW_REQUIRED"),
    ("R6", "high severity but fully reversible",
     lambda c: c["severity"] == "high" and c["irreversibility"] == "reversible", "REVIEW_REQUIRED"),
    ("R7", "medium severity, reversible",
     lambda c: c["severity"] == "medium", "ALLOW_WITH_GUARDS"),
    ("R8", "low severity",
     lambda c: c["severity"] == "low", "ALLOW"),
]


def gold_decision(case):
    for rid, rationale, pred, dec in GOLD_RULES:
        if pred(case):
            return dec, rid, rationale
    return "ABSTAIN", "R0", "no rule applies"


def requirement_for(facet, case):
    """Documented rule template. Levels are anchored to the normative weight of the facet
    in the domain (criticality), to severity, to prudential mode and to reversibility."""
    crit = facet.criticality[case["domain"]]
    base = {4: 0.85, 3: 0.70, 2: 0.55}[crit]
    base += {"low": -0.10, "medium": 0.0, "high": 0.08, "critical": 0.12}[case["severity"]]
    base += {"standard": 0.0, "elevated": 0.03, "maximum": 0.06}[case["prudential"]]
    base += {"reversible": 0.0, "partially_irreversible": 0.04, "irreversible": 0.08}[case["irreversibility"]]
    # pillar-level anchoring: normative and epistemic requirements rise with criticality
    pillar = facet.primary_pillar()
    if pillar == "M" and crit == 4:
        base += 0.05
    if pillar == "K" and crit == 4:
        base += 0.04
    return float(np.clip(base, 0.30, 0.95))


def make_case(idx, domain, severity, prudential, irreversibility, shared_u_e, narrative, family):
    case = {"case_id": f"{domain}-{idx:04d}", "domain": domain, "severity": severity,
            "prudential": prudential, "irreversibility": irreversibility,
            "narrative": narrative,
            "family_id": f"{domain}-{prudential}-{irreversibility}-{family}",
            "contextual_risk": float(np.clip({"low": 0.30, "medium": 0.55, "high": 0.78,
                                             "critical": 0.92}[severity]
                                            + {"standard": 0.0, "elevated": 0.04, "maximum": 0.08}[prudential]
                                            + {"reversible": 0.0, "partially_irreversible": 0.05,
                                               "irreversible": 0.10}[irreversibility], 0.20, 1.00)),
            "epistemic_uncertainty": float(shared_u_e)}
    case["critical_pillars"] = [p for p in ("M", "K") if any(
        f.primary_pillar() == p and f.criticality[domain] == 4 for f in FACETS)] or ["M", "K"]
    case["requirements"] = {f.code: round(requirement_for(f, case), 3) for f in FACETS}
    return case


def build_cases():
    """Cases are built in matched families: one family shares domain, prudential mode,
    reversibility, narrative and epistemic uncertainty, and varies only in severity band.
    This makes the severity-monotonicity test exact rather than statistical."""
    families = list(product(DOMAINS, PRUDENTIALS, REVERS))
    target = 1200
    per_family = target // (len(families) * 4)
    extra = target - per_family * len(families) * 4
    cases, idx = [], 1
    for k, (d, p, r) in enumerate(families):
        reps = per_family + (1 if k < extra // 4 else 0)
        for _ in range(reps):
            narrative = rng.choice(NARRATIVE[d])
            u_e = round(float(rng.uniform(0.15, 0.55)), 3)
            family = f"{d}-{p}-{r}-{k}-{_}"
            for sev in SEVERITIES:
                cases.append(make_case(idx, d, sev, p, r, u_e, narrative, family))
                idx += 1
    return cases


ARCHETYPES = {
    # archetype: (mean level per pillar), plus a facet-level bias vector
    "compliance_strong_capability_weak": {"W": 0.70, "C": 0.45, "M": 0.75, "K": 0.50},
    "capability_rich_normatively_thin": {"W": 0.65, "C": 0.80, "M": 0.40, "K": 0.55},
    "well_intended_under_resourced": {"W": 0.85, "C": 0.40, "M": 0.60, "K": 0.45},
    "opaque_high_performance": {"W": 0.55, "C": 0.75, "M": 0.55, "K": 0.35},
    "balanced_mature": {"W": 0.75, "C": 0.75, "M": 0.75, "K": 0.72},
    "adversarial_overconfident": {"W": 0.45, "C": 0.60, "M": 0.30, "K": 0.25},
    "governance_mature_strong": {"W": 0.88, "C": 0.82, "M": 0.86, "K": 0.80},
    "emerging_but_supervised": {"W": 0.55, "C": 0.50, "M": 0.68, "K": 0.55},
}


def build_profiles(n=40):
    profiles = []
    names = list(ARCHETYPES)
    for i in range(n):
        arch = names[i % len(names)]
        mean = ARCHETYPES[arch]
        levels = {}
        for f in FACETS:
            m = mean[f.primary_pillar()]
            # facet-specific deviation; critical facets deviate more strongly
            crit = f.criticality[DOMAINS[i % len(DOMAINS)]]
            sd = 0.12 if crit == 4 else 0.18
            levels[f.code] = float(round(np.clip(m + rng.normal(0, sd), 0.05, 0.99), 3))
        profiles.append({"profile_id": f"agent-{i:03d}", "archetype": arch,
                        "levels": levels, "confidence": float(round(rng.uniform(0.55, 0.90), 3))})
    return profiles


def probe_families():
    """150 adversarial probes: 10 families x 15 variants, each carrying explicit
    assertions that battery B8 evaluates against the formal core."""
    probes = []
    pid = 0
    base_req = {f.code: 0.70 for f in FACETS}
    THETA = CALIB.theta

    def add(kind, case, profile, asserts, note):
        nonlocal pid
        probes.append({"probe_id": f"PRB-{pid:03d}", "kind": kind, "case": case,
                       "profile_levels": profile, "asserts": asserts, "note": note})
        pid += 1

    def pillar_deficit(pillar, req, lev):
        lv, _ = project(lev, FACETS, cap_guards=True)
        q, _ = project(req, FACETS, cap_guards=False)
        return q[IDX[pillar]] - lv[IDX[pillar]]

    def levels_for_pillar_deficit(pillar, req, base_level, target):
        """Set every facet that contributes to `pillar` to a common level L so that the
        pillar deficit is exactly `target`. A single facet cannot reach a large pillar
        deficit because beta-weighted averaging dilutes it (itself a finding)."""
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            trial = dict(base_level)
            for f in FACETS:
                if f.beta[IDX[pillar]] > 0:
                    trial[f.code] = mid
            dd = pillar_deficit(pillar, req, trial)
            if dd < target:      # need a lower level to raise the deficit
                hi = mid
            else:
                lo = mid
        L = round((lo + hi) / 2.0, 5)
        out = dict(base_level)
        for f in FACETS:
            if f.beta[IDX[pillar]] > 0:
                out[f.code] = L
        return out

    for i in range(15):
        # 1. coverage degeneracy: fewer than 18 of 26 facets declared -> ABSTAIN
        req = dict(base_req)
        drop = list(rng.choice([f.code for f in FACETS], 9, replace=False))
        for c in drop:
            req.pop(c)
        add("coverage_degeneracy", {"case_id": f"PRB-COV-{i}", "domain": "IC", "severity": "high",
                                    "prudential": "elevated", "irreversibility": "irreversible",
                                    "contextual_risk": 0.8, "epistemic_uncertainty": 0.3,
                                    "critical_pillars": ["M", "K"], "requirements": req},
            {c: 0.8 for c in req},
            [{"kind": "decision", "value": "ABSTAIN"}],
            "coverage below 0.70 must abstain rather than produce a score")

        # 2. perfect compliance: adequacy is 1, but the prudential floor still bites
        add("saturation", {"case_id": f"PRB-SAT-{i}", "domain": "SA", "severity": "critical",
                           "prudential": "maximum", "irreversibility": "irreversible",
                           "contextual_risk": 0.95, "epistemic_uncertainty": 0.10,
                           "critical_pillars": ["M", "K"], "requirements": dict(base_req)},
            {c: 1.0 for c in base_req},
            [{"kind": "adequacy", "value": 1.0, "tol": 1e-4},
             {"kind": "veto_empty"},
             {"kind": "decision", "value": "ALLOW_WITH_GUARDS"},
             {"kind": "risk_floor_positive"}],
            "no deficit anywhere, yet a critical irreversible case can never be unconditionally ALLOW")

        # 3. compensation attempt: surplus in W/C/K cannot mask a normative collapse
        req = dict(base_req)
        for c in ("M1", "M3", "M4"):
            req[c] = 0.95
        lev = {c: 0.95 for c in base_req}
        lev["M1"] = 0.05
        lev["M3"] = 0.10
        add("compensation_attempt", {"case_id": f"PRB-CMP-{i}", "domain": "FI", "severity": "high",
                                     "prudential": "elevated", "irreversibility": "irreversible",
                                     "contextual_risk": 0.85, "epistemic_uncertainty": 0.35,
                                     "critical_pillars": ["M"], "requirements": req}, lev,
            [{"kind": "decision", "value": "PROHIBIT"},
             {"kind": "veto", "contains": ["M"]},
             {"kind": "adequacy_raw_at_least", "value": 0.55},
             {"kind": "deficit", "pillar": "M", "op": "ge", "value": THETA[2]}],
            "a compensatory aggregate would have looked acceptable; the veto overrides it")

        # 4. threshold edge: Must pillar deficit just below vs just above theta_M
        for side in (0, 1):
            target = THETA[2] - 0.001 if side == 0 else THETA[2] + 0.001
            lev = levels_for_pillar_deficit("M", dict(base_req),
                                           {c: 0.70 for c in base_req}, target)
            add("threshold_edge", {"case_id": f"PRB-THR-{i}-{side}", "domain": "JS", "severity": "high",
                                   "prudential": "standard", "irreversibility": "partially_irreversible",
                                   "contextual_risk": 0.7, "epistemic_uncertainty": 0.30,
                                   "critical_pillars": ["M"], "requirements": dict(base_req)}, lev,
                [{"kind": "deficit", "pillar": "M", "op": "approx", "value": target, "tol": 1e-3},
                 {"kind": "veto_empty"} if side == 0 else {"kind": "veto", "contains": ["M"]}],
                "the veto boundary is reproducible from either side without hysteresis")

        # 5. guard-cap exploitation: one facet far below its guard, everything else high
        lev = {c: 0.95 for c in base_req}
        lev["W2"] = 0.20
        add("guard_cap", {"case_id": f"PRB-GC-{i}", "domain": "PD", "severity": "medium",
                          "prudential": "elevated", "irreversibility": "partially_irreversible",
                          "contextual_risk": 0.6, "epistemic_uncertainty": 0.35,
                          "critical_pillars": ["W"], "requirements": dict(base_req)}, lev,
            [{"kind": "guard_failures_include", "value": ["W2"]},
             {"kind": "decision_not", "value": ["ALLOW"]},
             {"kind": "deficit", "pillar": "W", "op": "ge", "value": 0.45}],
            "the guarded facet caps its pillar: surrounding surplus cannot compensate")

        # 6. epistemic degeneracy: no metacognition at all
        lev = {c: 0.90 for c in base_req}
        for c in ("K1", "K2", "K5", "K6"):
            lev[c] = 0.0
        add("epistemic_blank", {"case_id": f"PRB-EP-{i}", "domain": "IM", "severity": "high",
                                "prudential": "elevated", "irreversibility": "partially_irreversible",
                                "contextual_risk": 0.75, "epistemic_uncertainty": 0.60,
                                "critical_pillars": ["K"], "requirements": dict(base_req)}, lev,
            [{"kind": "decision", "value": "PROHIBIT"},
             {"kind": "deficit", "pillar": "K", "op": "ge", "value": THETA[3]},
             {"kind": "risk_floor_positive"}],
            "absence of metacognition bounds residual risk away from zero")

        # 7. severity ladder: identical agency, four severity bands
        for sev in SEVERITIES:
            add("severity_ladder", {"case_id": f"PRB-SL-{i}-{sev}", "domain": "TB", "severity": sev,
                                    "prudential": "standard", "irreversibility": "partially_irreversible",
                                    "contextual_risk": {"low": 0.35, "medium": 0.6, "high": 0.8,
                                        "critical": 0.92}[sev], "epistemic_uncertainty": 0.30,
                                    "critical_pillars": ["M", "K"],
                                    "requirements": {f.code: round(0.65 + 0.05 * f.criticality["TB"], 3)
                                                     for f in FACETS}},
                {c: 0.70 for c in base_req},
                [{"kind": "ladder_monotone"}],
                "adequacy must not rise with severity for the same agency")

        # 8. tie between two pillars (identical deficits)
        req = dict(base_req)
        lev = {c: 0.70 for c in base_req}
        add("pillar_tie", {"case_id": f"PRB-TIE-{i}", "domain": "GP", "severity": "medium",
                           "prudential": "standard", "irreversibility": "reversible",
                           "contextual_risk": 0.5, "epistemic_uncertainty": 0.30,
                           "critical_pillars": ["C", "K"], "requirements": req}, lev,
            [{"kind": "deficit", "pillar": "C", "op": "approx", "value": 0.0, "tol": 1e-3},
             {"kind": "deficit", "pillar": "K", "op": "approx", "value": 0.0, "tol": 1e-3}],
            "equal deficits on distinct pillars give identical adequacy (permutation invariance)")

        # 9. veto with surplus: capability alone cannot satisfy normative duty
        req = dict(base_req)
        for f in FACETS:
            if f.beta[2] > 0:
                req[f.code] = 0.95
        lev = {c: 1.0 for c in base_req}
        for f in FACETS:
            if f.beta[2] > 0:
                lev[f.code] = 0.10
        add("veto_isolation", {"case_id": f"PRB-VET-{i}", "domain": "MA", "severity": "high",
                               "prudential": "elevated", "irreversibility": "irreversible",
                               "contextual_risk": 0.85, "epistemic_uncertainty": 0.25,
                               "critical_pillars": ["M"], "requirements": req}, lev,
            [{"kind": "decision", "value": "PROHIBIT"},
             {"kind": "deficit", "pillar": "M", "op": "ge", "value": THETA[2]},
             {"kind": "veto", "contains": ["M"]}],
            "capability at maximum cannot compensate a normative vacuum")

        # 10. near-saturation with a diluted single epistemic deficit
        lev = {c: 0.99 for c in base_req}
        lev["K7"] = 0.40
        add("near_saturation", {"case_id": f"PRB-NS-{i}", "domain": "RS", "severity": "medium",
                                "prudential": "standard", "irreversibility": "reversible",
                                "contextual_risk": 0.5, "epistemic_uncertainty": 0.20,
                                "critical_pillars": ["K"], "requirements": dict(base_req)}, lev,
            [{"kind": "adequacy_range", "lo": 0.90, "hi": 1.0},
             {"kind": "adequacy_less_than", "value": 1.0},
             {"kind": "deficit", "pillar": "K", "op": "approx", "value": 0.0, "tol": 1e-6},
             {"kind": "facet_exposure_at_least", "value": 0.01}],
            "an isolated facet gap is diluted by pillar averaging but still registers "
            "through the criticality-weighted exposure term")
    return probes


def run():
    cases = build_cases()
    profiles = build_profiles(40)
    probes = probe_families()
    gold = []
    for c in cases[:120]:
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                        c["irreversibility"], c["requirements"], c["epistemic_uncertainty"],
                        c["contextual_risk"], tuple(c["critical_pillars"]))
        for pr in profiles[:12]:
            adj = adjudicate(spec, pr["levels"])
            gold.append({"case_id": c["case_id"], "profile_id": pr["profile_id"],
                        "domain": c["domain"], "severity": c["severity"],
                        "irreversibility": c["irreversibility"], "prudential": c["prudential"],
                        "gold_decision": adj["consensus"],
                        "panelA": adj["panelA"], "panelB": adj["panelB"],
                        "panels_agree": adj["panels_agree"],
                        "ruleA": adj["ruleA"], "ruleB": adj["ruleB"],
                        "rationaleA": adj["rationaleA"], "rationaleB": adj["rationaleB"]})

    confrontations = []
    for c in cases:
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                        c["irreversibility"], c["requirements"], c["epistemic_uncertainty"],
                        c["contextual_risk"], tuple(c["critical_pillars"]))
        for pr in profiles[:12]:
            res = confront(spec, Profile(pr["profile_id"], pr["levels"], pr["confidence"]), CALIB)
            confrontations.append({"case_id": c["case_id"], "profile_id": pr["profile_id"],
                                   "domain": c["domain"], "severity": c["severity"],
                                   "levels": list(res["levels"]), "deficits": list(res["deficits"]),
                                   "S2": round(res["S2"], 4), "S3": round(res["S3"], 4),
                                   "S4": round(res["S4"], 4), "adequacy": round(res["adequacy"], 4),
                                   "adequacy_raw": round(res["adequacy_raw"], 4),
                                   "risk_floor": round(res["sigma"] * res["R_c"], 4),
                                   "residual_risk": round(res["R_r"], 4),
                                   "risk_ratio": round(res["risk_ratio"], 4),
                                   "veto": res["veto"], "hard_veto": res["hard_veto"],
                                   "guard_failures": res["guard_failures"],
                                   "decision": res["decision"], "completeness": round(res["completeness"], 4)})

    # TTL export of the corpus (cases only) so the ontology and the corpus stay linked
    from rdflib.namespace import RDF, RDFS
    from rdflib import BNode
    tg = Graph()
    tg.bind("eth", "https://ethwcmk.org/ontology/eth/")
    tg.bind("facet", "https://ethwcmk.org/ontology/facet/")
    tg.bind("domain", "https://ethwcmk.org/ontology/domain/")
    tg.bind("xsd", "http://www.w3.org/2001/XMLSchema#")
    from rdflib import URIRef, Literal
    for c in cases[:200]:
        ci = URIRef(f"https://ethwcmk.org/ontology/case/{c['case_id']}")
        tg.add((ci, RDF.type, URIRef("https://ethwcmk.org/ontology/eth/EthicalCase")))
        tg.add((ci, URIRef("https://ethwcmk.org/ontology/eth/hasDomain"),
                URIRef(f"https://ethwcmk.org/ontology/domain/{c['domain']}")))
        tg.add((ci, URIRef("https://ethwcmk.org/ontology/eth/hasSeverity"),
                URIRef(f"https://ethwcmk.org/ontology/severity/{c['severity']}")))
        tg.add((ci, URIRef("https://ethwcmk.org/ontology/eth/hasPrudentialMode"),
                URIRef(f"https://ethwcmk.org/ontology/prudential/{c['prudential']}")))
        tg.add((ci, URIRef("https://ethwcmk.org/ontology/eth/hasReversibility"),
                URIRef(f"https://ethwcmk.org/ontology/reversibility/{c['irreversibility']}")))
        tg.add((ci, URIRef("https://ethwcmk.org/ontology/eth/contextualRisk"),
                Literal(c["contextual_risk"], datatype=URIRef("http://www.w3.org/2001/XMLSchema#decimal"))))
        tg.add((ci, URIRef("https://ethwcmk.org/ontology/eth/epistemicUncertainty"),
                Literal(c["epistemic_uncertainty"], datatype=URIRef("http://www.w3.org/2001/XMLSchema#decimal"))))
        for code, val in c["requirements"].items():
            bn = BNode()
            tg.add((bn, RDF.type, URIRef("https://ethwcmk.org/ontology/eth/FacetRequirement")))
            tg.add((bn, URIRef("https://ethwcmk.org/ontology/eth/requirementForCase"), ci))
            tg.add((bn, URIRef("https://ethwcmk.org/ontology/eth/requiresFacet"),
                    URIRef(f"https://ethwcmk.org/ontology/facet/{code}")))
            tg.add((bn, URIRef("https://ethwcmk.org/ontology/eth/requirementValue"),
                    Literal(val, datatype=URIRef("http://www.w3.org/2001/XMLSchema#decimal"))))
    tg.serialize(os.path.join(OUT, "corpus_v3_cases_sample.ttl"), format="turtle")

    n = len(cases)
    idx = list(range(n))
    rng.shuffle(idx)
    split = {"train": [cases[i]["case_id"] for i in idx[:int(0.70 * n)]],
             "calibration": [cases[i]["case_id"] for i in idx[int(0.70 * n):int(0.85 * n)]],
             "test": [cases[i]["case_id"] for i in idx[int(0.85 * n):]]}

    def write(name, rows):
        with open(os.path.join(OUT, name), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    write("corpus_v3_cases.jsonl", cases)
    write("corpus_v3_profiles.jsonl", profiles)
    write("corpus_v3_probes.jsonl", probes)
    write("corpus_v3_gold.jsonl", gold)
    write("corpus_v3_confrontations.jsonl", confrontations)
    with open(os.path.join(OUT, "corpus_v3_split.json"), "w") as fh:
        json.dump(split, fh, indent=2)

    # ---- non-degeneracy gate ----
    perfect = sum(1 for x in confrontations if x["adequacy"] >= 0.9999)
    critical = [x for x in confrontations if x["severity"] == "critical"]
    veto_in_critical = sum(1 for x in critical if x["veto"])
    decisions = Counter(x["decision"] for x in confrontations)
    dec_dist = {k: round(v / len(confrontations), 4) for k, v in decisions.items()}
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    by_case = {x["case_id"]: x for x in confrontations}
    case_family = {c["case_id"]: c["family_id"] for c in cases}
    families = defaultdict(dict)
    for c in cases:
        key = (c["family_id"], c["severity"])
        families[c["family_id"]][c["severity"]] = c
    mono_pairs = mono_fail = 0
    for pr in profiles[:12]:
        for fam, sevmap in families.items():
            if len(sevmap) != 4:
                continue
            seq = sorted((order[s] for s in sevmap))
            vals = [by_case[sevmap[s]["case_id"]]["adequacy"] for s in
                    sorted(sevmap, key=lambda s: order[s])]
            for a, b in zip(vals, vals[1:]):
                mono_pairs += 1
                if b > a + 1e-9:
                    mono_fail += 1
    veto_by_sev = {}
    for sev in SEVERITIES:
        rows = [x for x in confrontations if x["severity"] == sev]
        veto_by_sev[sev] = round(sum(1 for x in rows if x["veto"]) / len(rows), 4)
    overall_veto = round(sum(1 for x in confrontations if x["veto"]) / len(confrontations), 4)
    gate = {
        "cases": len(cases), "profiles": len(profiles), "probes": len(probes),
        "gold_cases": len(gold), "confrontations": len(confrontations),
        "adequacy_1_share": round(perfect / len(confrontations), 4),
        "gate_adequacy_1_below_3pct": perfect / len(confrontations) < 0.03,
        "veto_share_by_severity": veto_by_sev,
        "veto_share_overall": overall_veto,
        "gate_veto_monotone_in_severity": all(veto_by_sev[a] <= veto_by_sev[b]
                                             for a, b in zip(SEVERITIES, SEVERITIES[1:])),
        "gate_veto_share_overall_in_15_60pct": 0.15 <= overall_veto <= 0.60,
        "severity_monotonicity_pairs": mono_pairs,
        "severity_monotonicity_failures": mono_fail,
        "severity_monotonicity_rate": round(1 - mono_fail / max(1, mono_pairs), 4),
        "gate_monotonicity_above_95pct": (1 - mono_fail / max(1, mono_pairs)) >= 0.95,
        "decision_distribution": dec_dist,
        "gold_consensus_distribution": dict(Counter(g["gold_decision"] for g in gold)),
        "panelA_distribution": dict(Counter(g["panelA"] for g in gold)),
        "panelB_distribution": dict(Counter(g["panelB"] for g in gold)),
        "panel_agreement_rate": round(sum(1 for g in gold if g["panels_agree"]) / len(gold), 4),
        "inter_panel_kappa": round(cohens_kappa([g["panelA"] for g in gold],
                                               [g["panelB"] for g in gold]), 4),
        "gold_rule_hits_A": dict(Counter(g["ruleA"] for g in gold)),
        "gold_rule_hits_B": dict(Counter(g["ruleB"] for g in gold)),
        "domains": dict(Counter(c["domain"] for c in cases)),
        "severities": dict(Counter(c["severity"] for c in cases)),
        "split_sizes": {k: len(v) for k, v in split.items()},
    }
    with open(os.path.join(OUT, "corpus_v3_gate.json"), "w") as fh:
        json.dump(gate, fh, indent=2, ensure_ascii=False)
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
