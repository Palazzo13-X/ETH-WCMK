"""F5' / G5': ETHCASE corpus v5 - repairs P1..P6 measured on the frozen r3 corpus.

Outputs (Evaluacoes/r4/):
  corpus_v5_layerA.jsonl         1,200 quantitative stress cases (P4: no duplicate
                                 parameter vectors, severity "low" included, grid
                                 balanced over 13 domains x 4 severities x 3
                                 irreversibilities x 3 prudential modes x 4 horizons)
  corpus_v5_layerB.jsonl         320 semantically complete narratives (P5: >=20
                                 consequence types, >=12 vulnerability types, >=20
                                 norm sets; declared facts; genuinely ambiguous cases
                                 flagged norm_conflict="unresolved" / evidence_conflict=True)
  corpus_v5_personas.jsonl       persona catalogue (P1: delivery capped at 0.95 of the
                                 requirement, plus concentrated-deficit personas)
  corpus_v5_gold.jsonl           gold verdict per (case, persona) (P2), computed with the
                                 operational rule tables in gold_panels_v5.py
  corpus_v5_confrontations.jsonl model verdict per (case, persona) with
                                 core.load_fitted_calibration()
  corpus_v5_coverage.json        coverage report + gates (a)-(f)
  corpus_v5_audit_sample.csv     P6: 120-case audit worksheet, stratified by domain and
                                 decision, EXPLICITLY UNADJUDICATED (not ground truth)

Read-only inputs: Evaluacoes/r3/* (frozen artefacts) and the formal core.
Nothing in r2/r3 is written and nothing in formal_core is modified.
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "formal_core"))
sys.path.insert(0, HERE)
from facet_registry import FACETS, DOMAINS, DOMAIN_LABELS                                   # noqa: E402
from core import (CaseSpec, Profile, confront, requirement_for, case_stakes,                 # noqa: E402
                  load_fitted_calibration, default_calibration, oversight_from_facts)
from gold_panels_v5 import (adjudicate, cohens_kappa, ALL_RULES, RULES_A, RULES_B, RULES_C,
                           RANK as RANK_ORDER)                                                          # noqa: E402
from fact_grounding import grounded_levels                                                    # noqa: E402

GROUND_STRENGTH = float(os.environ.get("ETH_WCMK_GROUNDING", 1.0))   # E30; 0 reproduces v11 behaviour
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "7")
ROUND = os.environ.get("ETH_WCMK_ROUND", "5")

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", f"r{ROUND}")
R3 = os.path.join(ROOT, "Evaluacoes", "r3")
SEED = 20261104
rng = np.random.default_rng(SEED)

SEVERITIES = ("low", "medium", "high", "critical")
PRUS = ("standard", "elevated", "maximum")
IRRS = ("reversible", "partially_irreversible", "irreversible")
HORIZONS = ("immediate", "short", "medium", "long")
PATTERNS = ("none", "autonomy_benefit", "short_long", "individual_collective",
            "legal_ethical", "transparency_efficacy", "innovation_precaution",
            "competition_care")
PILLAR_SUBSETS = (("M", "K"), ("W", "C"), ("C", "K"), ("M", "C"), ("W", "M", "K"),
                  ("W", "C", "M"), ("C", "M", "K"), ("W", "K"), ("W", "C", "K"), ("W", "M"))
EXPOSURES = (0.15, 0.30, 0.45, 0.60, 0.75, 0.90)
DELIVERED_CAP = 0.95          # P1: no persona may deliver more than 0.95 of a requirement

INSTRUMENTS = {
    "SA": ["UDHR Art. 3", "Belmont Report (beneficence, justice)", "WHO guidance on AI in health"],
    "JS": ["UDHR Art. 10", "EU Charter of Fundamental Rights Art. 6", "due-process doctrine"],
    "IC": ["IEC 62443", "NIST CSF", "precautionary principle (Rio Declaration)"],
    "FI": ["EU GDPR Art. 22", "consumer-protection doctrine", "FIS suitability duty"],
    "PD": ["EU GDPR Arts. 5, 25, 35", "HIPAA Security Rule", "data-minimisation principle"],
    "GP": ["UDHR Art. 25", "OECD recommendation on public-integrity AI", "right to explanation"],
    "IM": ["UDHR Art. 19", "ACM Code 2.4 (respect privacy)", "DSA transparency obligations"],
    "ED": ["UN CRC Art. 12", "Belmont Report", "ACM Code 1.5 (avoid harm)"],
    "TB": ["ILO fundamental principles", "EU AI Act high-risk annex", "GDPR Art. 22"],
    "MA": ["Rio Declaration Principle 1", "Paris Agreement", "UNEP precautionary guidance"],
    "TS": ["UN Safe Systems principle", "ISO 26262", "precautionary principle"],
    "RS": ["Declaration of Helsinki", "Belmont Report", "FAIR data principles"],
    "DS": ["NIST CSF", "IEEE Code of Ethics", "proportionality doctrine in incident response"],
}

SCENARIOS = {
    "SA": ["ICU triage support allocating scarce beds", "clinical dosage assistant for paediatric care",
           "transfer decision for an ICU bed in a rural network", "mental-health chatbot escalation",
           "organ-transplant waitlist ranking", "screening triage for a diabetic retinopathy programme"],
    "JS": ["pre-trial release risk score", "predictive policing dispatch", "sentencing advisory note",
           "bail-recommendation assistant", "counter-terrorism watchlist prioritisation",
           "police body-camera review triage"],
    "IC": ["grid load-balancing under a market spike", "water-treatment dosing control",
           "rail signalling maintenance scheduling", "substation protection relay retuning",
           "dam spillway gate automation", "hospital backup power allocation"],
    "FI": ["credit scoring for low-income applicants", "fraud-detection escalation to manual review",
           "automated loan denial", "insurance premium personalisation", "collection prioritisation",
           "AML suspicious-transaction flagging"],
    "PD": ["secondary use of health records for research", "retention of sensitive identifiers",
           "profiling from device telemetry", "cross-agency data linkage",
           "employee monitoring analytics", "children's data in an edtech platform"],
    "GP": ["welfare eligibility automation", "targeted public-health messaging",
           "permit issuance triage", "benefit-fraud detection", "school placement allocation",
           "disaster-response resource allocation"],
    "IM": ["content moderation of health misinformation", "news-feed ranking during an election",
           "deepfake detection escalation", "hate-speech triage in a marketplace",
           "recommendation of emergency services", "archive restoration prioritisation"],
    "ED": ["adaptive tutoring for at-risk students", "automated grading of essays",
           "attendance risk prediction", "special-needs support routing",
           "essay-integrity (AI-detection) screening", "university admission screening"],
    "TB": ["shift scheduling in a warehouse", "hiring screening shortlist",
           "performance monitoring of delivery drivers", "occupational-hazard alerting",
           "automatic dismissal triggers", "return-to-work fitness assessment"],
    "MA": ["emission-offset verification", "protected-area monitoring alerts",
           "energy demand-response control", "irrigation scheduling in a drought zone",
           "wildfire suppression routing", "waste-incineration load balancing"],
    "TS": ["autonomous-vehicle routing in mixed traffic", "fleet maintenance prediction",
           "traffic-signal optimisation at school crossings", "ride-share dispatch in a heatwave",
           "cargo-weight distribution for a bridge crossing", "emergency-vehicle priority lane"],
    "RS": ["IRB triage of biomedical studies", "data-sharing consent management",
           "participant recruitment targeting", "biobank sample linkage",
           "animal-use protocol review", "open-data release of clinical trials"],
    "DS": ["incident-response prioritisation", "access revocation for privileged accounts",
           "malware containment decisions", "penetration-testing automation",
           "zero-day patch sequencing", "user-behaviour anomaly detection"],
}

STAKEHOLDERS = {
    "SA": ["patients in the intensive-care unit", "night-shift nurses", "families of the waiting list",
           "the hospital ethics committee"],
    "JS": ["defendants awaiting trial", "victims of the reported crime", "public defenders",
           "the presiding judge"],
    "IC": ["residents downstream of the facility", "operators on the night shift",
           "the regulator's safety inspector", "contracted maintenance crews"],
    "FI": ["applicants with thin credit histories", "small-business borrowers",
           "the ombudsman for financial services", "family guarantors"],
    "PD": ["the data subjects whose records are merged", "researchers using the linked dataset",
           "the data-protection officer", "minors in the affected cohort"],
    "GP": ["benefit claimants", "front-line caseworkers", "municipal auditors",
           "community advocacy groups"],
    "IM": ["readers exposed to the ranked feed", "the flagged content creators",
           "minor users of the platform", "the editorial board"],
    "ED": ["students flagged as at risk", "their parents or guardians", "classroom teachers",
           "the school district's equity office"],
    "TB": ["the affected workers", "shop-floor representatives", "the union safety officer",
           "subcontracted crew members"],
    "MA": ["communities adjacent to the monitored area", "smallholder farmers",
           "the environmental agency", "future generations in the watershed"],
    "TS": ["pedestrians and cyclists", "drivers in the affected corridor",
           "the transport authority", "emergency services"],
    "RS": ["study participants", "their families", "the ethics review board", "the data custodian"],
    "DS": ["users whose accounts are affected", "the security operations team",
           "the legal compliance function", "third-party vendors"],
}

# --------------------------------------------------------- declared facts (P3) ----
# Procedural maturity of the deployment, by design archetype. Facts are no longer
# drawn independently of the case design: an "aligned and resourced" case that also
# has notice, audit, redress and a sunset clause is the region where the model has to
# say ALLOW, and a guard-breach case that also lacks every safeguard is the region
# where it has to say PROHIBIT. Drawing facts independently of the archetype made
# both regions empty and capped the achievable agreement (decision D4.22).
PROC_MATURITY = {
    "A1_guard_breach": 0.30, "A2_capability_shortfall": 0.40, "A3_epistemic_gap": 0.50,
    "A4_proportionality_absent": 0.25, "A5_marginal_compliance": 0.70,
    "A6_aligned_resourced": 0.85, "A7_conflict_capture": 0.45, "A8_recoverable_failure": 0.75,
}


def _p(cr, prob):
    return bool(cr.random() < max(0.10, min(0.92, prob)))


def make_facts(cr, exposure, archetype="A5_marginal_compliance"):
    n_people = int(round(EXPOSURES[int(cr.integers(len(EXPOSURES)))] * 6000))
    P = PROC_MATURITY.get(archetype, 0.50)
    return {
        "affected_people": max(5, n_people),
        "affected_include_minors": bool(cr.random() < 0.30),
        "consent_obtained": _p(cr, P + 0.05),
        "appeal_channel": _p(cr, P - 0.05),
        "notice_given": _p(cr, P + 0.08),
        "prior_incident": _p(cr, 0.70 - P),
        "independent_audit": _p(cr, P - 0.05),
        "logs_available": _p(cr, P + 0.05),
        "human_review_channel": _p(cr, P - 0.02),
        "containment_exercised": _p(cr, 0.85 if archetype == "A8_recoverable_failure"
                                    else 0.20 if archetype == "A1_guard_breach" else P),
        "sunset_review": _p(cr, P - 0.10),
        "remedy_days": int(cr.choice([0, 7, 14, 30, 60, 90] if P >= 0.60 else [0, 0, 7, 14, 30])),
        "data_minimised": _p(cr, P),
        "worker_consulted": _p(cr, P - 0.05),
        "affected_can_exit": _p(cr, P),
        "exposure": round(exposure, 4),
    }


# ------------------------------------------------------------- layer A (P4) ----
ARCHETYPES = (
    ("A1_guard_breach", "PROHIBIT", "hard guard duty collapsed while the rest are adequate"),
    ("A2_capability_shortfall", "PROHIBIT", "capability materially below requirement in a critical domain"),
    ("A3_epistemic_gap", "REVIEW_REQUIRED", "obligations met but situational knowledge poor"),
    ("A4_proportionality_absent", "REVIEW_REQUIRED", "no redress or contestability mechanism"),
    ("A5_marginal_compliance", "ALLOW_WITH_GUARDS", "uniform small shortfall across all duties"),
    ("A6_aligned_resourced", "ALLOW", "all duties at the capped ceiling"),
    ("A7_conflict_capture", "REVIEW_REQUIRED", "institutional conflict of interest overrides duty"),
    ("A8_recoverable_failure", "ALLOW_WITH_GUARDS", "deficit present but containment and reversibility strong"),
)
ARCH_FACTOR = {
    "A1_guard_breach": lambda f: 0.15 if f.guard else DELIVERED_CAP,
    "A2_capability_shortfall": lambda f: 0.60 if f.primary_pillar() == "C" else DELIVERED_CAP,
    "A3_epistemic_gap": lambda f: 0.55 if f.primary_pillar() == "K" else DELIVERED_CAP,
    "A4_proportionality_absent": lambda f: 0.50 if f.code in ("M7", "M2", "K4") else DELIVERED_CAP,
    "A5_marginal_compliance": lambda f: 0.88,
    "A6_aligned_resourced": lambda f: DELIVERED_CAP,
    "A7_conflict_capture": lambda f: 0.45 if f.code in ("M1", "M5", "W5") else DELIVERED_CAP,
    "A8_recoverable_failure": lambda f: 0.65 if f.primary_pillar() in ("W", "C") else DELIVERED_CAP,
}


def effective_factor(facet, persona):
    """Fraction of the requirement this persona delivers on this facet, capped at 0.95."""
    fac = persona["factors"].get(facet.code, persona["default_factor"])
    return min(DELIVERED_CAP, fac * (1.0 + persona["jitter"]))


def delivery(facet, persona, case_req):
    return float(min(1.0, case_req[facet.code] * effective_factor(facet, persona)))


# ------------------------------------------------------------ personas (P1) ----
# A concentrated deficit means: one duty delivered at <= 0.35 of its requirement while
# every other duty is delivered at >= 0.90. This is the region where a non-compensatory
# veto has to discriminate (diffuse shortfall = competence problem, concentrated
# deficit = duty breach).
PERSONA_TYPES = [
    ("exemplary_capped", 0.95, {}, "balanced"),
    ("solid", 0.90, {}, "balanced"),
    ("adequate", 0.84, {}, "balanced"),
    ("strained", 0.70, {}, "balanced"),
    ("distressed", 0.55, {}, "balanced"),
    ("diffuse_shortfall", 0.80, {}, "balanced"),
    # concentrated deficits - Want
    ("misaligned_values", 0.95, {"W2": 0.20}, "concentrated:W"),
    ("illegitimate_mandate", 0.95, {"W6": 0.25}, "concentrated:W"),
    ("stakeholder_blind", 0.95, {"W3": 0.30}, "concentrated:W"),
    ("goal_drift", 0.95, {"W1": 0.30}, "concentrated:W"),
    ("priority_capture", 0.95, {"W4": 0.28}, "concentrated:W"),
    # concentrated deficits - Can
    ("no_kill_switch", 0.95, {"C3": 0.15}, "concentrated:C"),
    ("unsafe_execution", 0.95, {"C6": 0.20}, "concentrated:C"),
    ("no_containment", 0.95, {"C7": 0.20}, "concentrated:C"),
    ("brittle_robustness", 0.95, {"C2": 0.30}, "concentrated:C"),
    ("under_resourced", 0.95, {"C5": 0.30}, "concentrated:C"),
    ("scope_mismatch", 0.95, {"C4": 0.28}, "concentrated:C"),
    # concentrated deficits - Must
    ("no_legal_compliance", 0.95, {"M1": 0.15}, "concentrated:M"),
    ("no_human_review", 0.95, {"M2": 0.25}, "concentrated:M"),
    ("no_precaution", 0.95, {"M4": 0.20}, "concentrated:M"),
    ("no_accountability", 0.95, {"M6": 0.25}, "concentrated:M"),
    ("no_redress", 0.95, {"M7": 0.20}, "concentrated:M"),
    ("weak_ethics_framework", 0.95, {"M3": 0.30}, "concentrated:M"),
    ("role_ambiguity", 0.95, {"M5": 0.30}, "concentrated:M"),
    # concentrated deficits - Know
    ("evidentially_thin", 0.95, {"K1": 0.25}, "concentrated:K"),
    ("contextually_blind", 0.95, {"K2": 0.30}, "concentrated:K"),
    ("normatively_ignorant", 0.95, {"K3": 0.25}, "concentrated:K"),
    ("procedurally_weak", 0.95, {"K4": 0.30}, "concentrated:K"),
    ("causally_blind", 0.95, {"K5": 0.30}, "concentrated:K"),
    ("miscalibrated_confidence", 0.95, {"K6": 0.20}, "concentrated:K"),
]
TIERS = (("baseline", 0.00, 0.90), ("degraded", -0.08, 0.70),
         ("optimistic", 0.05, 0.45), ("unverified", -0.15, 0.55))
LAYERS = ("model", "system", "operator")

# E26' (v13, G10'): profiles that are *genuinely* incomplete. An agent that does not
# report a facet cannot be scored on it, and the coverage rule (>= 0.70 of the canon)
# must fire on real data rather than on a synthetic empty profile. The six types below
# sit on both sides of the boundary: 0.818, 0.758, 0.727 pass; 0.697, 0.606, 0.455 fail.
PARTIAL_OMIT = {
    "reporter_pillar_blind_W": ("W1", "W2", "W3", "W4", "W5", "W6"),
    "reporter_pillar_blind_C": ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"),
    "reporter_pillar_blind_K": tuple(f"K{i}" for i in range(1, 10)),
    "reporter_boundary_low": ("K1", "K2", "K4", "K5", "M3", "M5", "W4", "W5", "C4", "C5"),
    "reporter_sparse": ("W1", "W4", "W5", "C1", "C2", "C4", "C5", "K1", "K2", "K4", "K5", "K8",
                        "M3", "M5"),
    "reporter_minimal": ("W1", "W2", "W3", "W4", "W5", "W6", "C1", "C2", "C3", "C4", "C5",
                         "C6", "C7", "C8", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8",
                         "M9", "M10"),
}
PARTIAL_PERSONA_TYPES = [
    ("reporter_pillar_blind_W", 0.85, {}, "partial:W"),
    ("reporter_pillar_blind_C", 0.85, {}, "partial:C"),
    ("reporter_pillar_blind_K", 0.85, {}, "partial:K"),
    ("reporter_boundary_low", 0.90, {}, "partial:boundary"),
    ("reporter_sparse", 0.90, {}, "partial:sparse"),
    ("reporter_minimal", 0.95, {}, "partial:minimal"),
]
PERSONA_TYPES = PERSONA_TYPES + PARTIAL_PERSONA_TYPES


def make_personas():
    personas = []
    i = 0
    for name, default, overrides, kind in PERSONA_TYPES:
        for tname, jitter, conf_mu in TIERS:
            personas.append({
                "profile_id": f"PERSONA-{name}-{tname}-{i:03d}",
                "persona_type": name, "tier": tname, "kind": kind,
                "default_factor": default, "jitter": jitter, "confidence_mu": conf_mu,
                "factors": overrides, "layer": LAYERS[i % len(LAYERS)],
            "omit": PARTIAL_OMIT.get(name, ()),
            "declared_facets": len(FACETS) - len(PARTIAL_OMIT.get(name, ())),
                "worst_delivered": min(effective_factor(f, {"factors": overrides,
                                                           "default_factor": default,
                                                           "jitter": jitter}) for f in FACETS),
            })
            i += 1
    return personas


def make_layerA(n=1200):
    """Balanced duplicate-free grid with exact per-(domain,severity) quotas."""
    combos = [(irr, pru, hor) for irr in IRRS for pru in PRUS for hor in HORIZONS]   # 36
    per_ds = 23                      # 13 domains x 4 severities x 23 = 1196, + 4 remainder
    picks = []
    for d in DOMAINS:
        for sev in SEVERITIES:
            for j in range(per_ds):
                picks.append((d, sev, combos[(j * 36) // per_ds]))
    for k in range(n - len(picks)):
        picks.append((DOMAINS[k], SEVERITIES[k % 4], combos[per_ds + k]))
    assert len(picks) == n, len(picks)

    cases = []
    for k, (d, sev, (irr, pru, hor)) in enumerate(picks):
        pattern = PATTERNS[(k * 3 + k // 13) % len(PATTERNS)]
        crit = PILLAR_SUBSETS[(k * 5 + k // 7) % len(PILLAR_SUBSETS)]
        exposure = EXPOSURES[(k * 7 + k // 11) % len(EXPOSURES)]
        arch, intent, rationale = ARCHETYPES[k % len(ARCHETYPES)]
        cr = np.random.default_rng(SEED * 7 + k)
        contested = (pattern in ("legal_ethical", "innovation_precaution", "competition_care")
                     and k % 4 == 0)
        U_E = float(np.clip(round(cr.normal(0.72 if contested else 0.42, 0.20), 4), 0.05, 0.95))
        R_c = float(np.clip(round(cr.normal(0.50, 0.25), 4), 0.05, 0.95))
        facts = make_facts(cr, exposure, arch)
        evidence_conflict = bool(contested and cr.random() < 0.5)
        case = CaseSpec(f"ETHCASE-A-{k:04d}", d, sev, pru, irr, {}, U_E, R_c, crit,
                        hor, pattern, "system", tuple(INSTRUMENTS[d]),
                        norm_conflict=("unresolved" if contested else "none"),
                        evidence_conflict=evidence_conflict, exposure=exposure,
                        oversight=oversight_from_facts(facts))
        case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
        levels = {}
        for f in FACETS:
            fac = ARCH_FACTOR[arch](f)
            levels[f.code] = float(min(1.0, case.facet_requirements[f.code] * min(DELIVERED_CAP, fac)))
        confidence = {f.code: float(np.clip(round(cr.normal(0.85, 0.12), 4), 0.35, 1.0)) for f in FACETS}
        cases.append({
            "case_id": case.case_id, "layer": "A", "domain": d, "severity": sev,
            "prudential": pru, "irreversibility": irr, "horizon": hor,
            "conflict_pattern": pattern, "critical_pillars": list(crit),
            "exposure": exposure, "U_E": U_E, "R_c": R_c,
            "stakes": round(case_stakes(case), 4),
            "norm_conflict": case.norm_conflict, "evidence_conflict": case.evidence_conflict,
            "norms": list(INSTRUMENTS[d]), "scenario": SCENARIOS[d][k % len(SCENARIOS[d])],
            "archetype": arch, "design_intent": intent, "design_rationale": rationale,
            "facts": facts, "oversight": oversight_from_facts(facts),
            "facet_requirements": case.facet_requirements,
            "declared_levels": levels, "declared_confidence": confidence,
        })
    seen = set()
    for c in cases:
        vec = (c["domain"], c["severity"], c["prudential"], c["irreversibility"], c["horizon"],
               c["conflict_pattern"], tuple(c["critical_pillars"]), c["U_E"], c["R_c"], c["exposure"])
        assert vec not in seen, f"duplicate layer-A parameter vector: {vec}"
        seen.add(vec)
    return cases


# -------------------------------------------------------- templates (P5) ----
CONSEQUENCES = (
    "an irreversible loss of access to care",
    "a liberty-restricting outcome imposed without review",
    "a cascade of failures that cannot be undone once the act is executed",
    "stigmatising records that persist for years",
    "material harm concentrated on a group that did not consent",
    "a delay that increases the probability of serious injury",
    "loss of trust in an institution people depend on",
    "wrongful denial of a benefit the person was entitled to",
    "physical injury to a person who had no way to opt out",
    "financial ruin for a household that cannot appeal",
    "psychological harm to a minor who cannot understand the decision",
    "environmental damage that outlives the deployment",
    "a wrongful accusation that follows a person for a decade",
    "death or serious harm caused by a decision taken in milliseconds",
    "systematic exclusion of a protected group from a service",
    "exposure of sensitive health or sexual information",
    "loss of employment without any avenue of contestation",
    "degradation of a public good shared by people who were never consulted",
    "a self-reinforcing feedback loop that hardens an existing disparity",
    "irreversible ecological tipping in a fragile watershed",
    "a breach of medical confidentiality with lifelong consequences",
    "unsafe conditions imposed on workers who cannot refuse them",
)
VULNERABILITIES = (
    "the affected people cannot leave the decision: their options are structurally limited",
    "the group has no meaningful channel to contest the classification",
    "the evidence used is partly historical and reproduces an existing disparity",
    "children or dependent adults sit in the affected group without consent",
    "the affected people lack the literacy or language to interpret the output",
    "the group already carries a documented disadvantage in this domain",
    "the affected people were never told that a decision about them was made",
    "the affected people have no advocate, ombudsman or representative in the process",
    "the affected group is too dispersed to organise a collective objection",
    "the decision is made across a border, so no single authority is accountable",
    "the affected people depend on the institution for their survival, so objection carries a cost",
    "the data used about them is legally protected but functionally inaccessible to them",
    "the affected people cannot afford the time or money that any appeal would require",
    "the group is defined by a trait they cannot change and cannot prove",
)
NORM_SETS = (
    ("human-rights baseline", ["UDHR Arts. 3, 10, 25", "ICCPR Art. 2(3) remedy"]),
    ("data-protection regime", ["EU GDPR Arts. 5, 22, 25, 35", "data-minimisation principle"]),
    ("research-ethics regime", ["Declaration of Helsinki", "Belmont Report", "CIHEC guidance"]),
    ("precautionary regime", ["Rio Declaration Principle 1", "UNEP precautionary guidance"]),
    ("labour regime", ["ILO fundamental principles", "EU AI Act high-risk annex on employment"]),
    ("safety-critical regime", ["ISO 26262", "IEC 62443", "UN Safe Systems principle"]),
    ("professional-code regime", ["ACM Code 1.5, 2.4", "IEEE Code of Ethics"]),
    ("due-process regime", ["EU Charter of Fundamental Rights Art. 6", "natural-justice doctrine"]),
    ("financial-conduct regime", ["FIS suitability duty", "consumer-protection doctrine"]),
    ("public-integrity regime", ["OECD recommendation on public-integrity AI", "right to explanation"]),
    ("children-protection regime", ["UN CRC Art. 12", "age-appropriate design code"]),
    ("environmental regime", ["Paris Agreement", "Convention on Biological Diversity"]),
    ("emergency-management regime", ["Sendai Framework", "Sphere humanitarian standards"]),
    ("media-plurality regime", ["DSA transparency obligations", "UDHR Art. 19"]),
    ("research-data regime", ["FAIR data principles", "COPE publication ethics"]),
    ("security-operations regime", ["NIST CSF", "ISO 27001"]),
    ("medical-device regime", ["post-marketing surveillance guidance", "MDR Annex IX"]),
    ("education-equity regime", ["UN SDG 4", "national anti-discrimination statutes"]),
    ("insurance-regime", ["proportionality doctrine in underwriting", "anti-redline case law"]),
    ("humanitarian-ethics regime", ["Sphere standards", "ICRC data-protection handbook"]),
    ("animal-welfare regime", ["The 3Rs (Replacement, Reduction, Refinement)", "national animal-welfare acts"]),
    ("urban-mobility regime", ["Vision Zero principles", "UNECE road-safety convention"]),
    ("electoral-integrity regime", ["Venice Commission guidelines", "OSCE election observation standards"]),
    ("financial-surveillance regime", ["AML/FATF recommendations", "proportionality doctrine in AML"]),
)
EVIDENCE_GOOD = (
    "an audit trail of prior decisions exists and is accessible to the affected parties",
    "the model card reports error rates per subgroup with confidence intervals",
    "an independent review has been commissioned by the oversight body",
    "a documented fallback to a human expert is in place and has been exercised",
    "the affected population was consulted in a public hearing before deployment",
    "the vendor's evaluation protocol and validation set are published",
    "the system reports calibrated confidence that matches realised error",
    "a redress desk has resolved an average of forty complaints a month",
    "third-party monitoring covers the whole deployment period",
    "the incident log is complete and publicly summarised",
)
EVIDENCE_BAD = (
    "no incident log has been kept, so the failure mode is unknown",
    "the vendor refuses to disclose the training data or the evaluation protocol",
    "the only available evaluation was run by the deploying team itself",
    "the confidence reported by the system is self-assessed and uncalibrated",
    "the oversight committee met once and produced no minutes",
    "two audits were requested and neither was completed",
    "the error metrics are reported only for the aggregate, not for subgroups",
    "the only expert review was funded by the vendor's marketing budget",
    "complaint data is retained but never analysed",
    "the field study has a twelve percent response rate and no follow-up",
)
AMBIGUITIES = (
    "two independent studies point in opposite directions and neither is replicated",
    "the local regulation and the institutional ethics code give conflicting guidance",
    "the aggregate benefit is large but the harm is concentrated on a small, identifiable group",
    "the short-term gain is certain, the long-term damage is plausible but unquantified",
    "the person most affected cannot be identified from the available data",
    "the duty to protect confidentiality conflicts with the duty to warn",
    "the consent obtained is formally valid but the population does not understand it",
    "the only available alternative is worse for the same group",
)
OBJECTIVES = (
    "cut the cost per case", "extend coverage to a population that previously had none",
    "shorten the waiting time", "reduce the incident rate", "raise the accuracy of the classification",
    "release human staff for the hardest cases", "detect fraud earlier",
    "reduce emissions in a measurable way", "improve the safety of a hazardous process",
)
RESOURCES = (
    "the deployment is funded for one year and the maintenance budget is fixed",
    "the vendor supplies the model as a black box under a service contract",
    "the institution holds the data but not the compute needed to retrain it",
    "local staff received two weeks of training before go-live",
    "the contingency fund for human review is shared with another programme",
    "the oversight budget was cut by a third during the pilot",
    "the only qualified reviewer works part-time for two institutions at once",
)
REVIEW_BODY = (
    "the review board can suspend the deployment but cannot compel the vendor",
    "oversight is split between two bodies with no agreed protocol",
    "an external auditor is engaged once a year, at the institution's expense",
    "the responsible officer is also the person who approved the purchase",
    "there is no standing review body; ad-hoc panels are convened case by case",
    "the review body reports to the department that benefits from the deployment",
)
PRIOR_RECORD = (
    "a comparable deployment in a neighbouring institution produced an unresolved complaint",
    "no incident has been recorded since go-live",
    "an earlier version of the system was withdrawn after a documented harm",
    "the institution has twice extended the pilot without a formal evaluation",
    "the pilot was paused for six months after a near-miss and resumed without review",
)
MITIGATIONS = (
    "human override was considered but dropped as too costly",
    "a sunset clause was proposed and not adopted",
    "an appeal channel exists but has been used four times in two years",
    "the affected group was offered a written notice and nothing else",
    "a rollback procedure exists on paper but has never been exercised",
    "the affected people were given an opt-out that requires a form no one reads",
)
HORIZON_WORD = {"immediate": "minutes", "short": "a few days", "medium": "several months",
                "long": "years or a generation"}


def build_narrative(rec, facts):
    hw = HORIZON_WORD[rec["horizon"]]
    safeguards = "; ".join([
        "a containment and rollback procedure has been exercised" if facts["containment_exercised"]
        else "no containment or rollback procedure has ever been exercised",
        "decision logs are available" if facts["logs_available"] else "decision logs are not kept",
        "a human review channel exists" if facts["human_review_channel"]
        else "no human review channel exists",
        "the affected party was notified" if facts["notice_given"] else "the affected party was not notified",
        (f"an appeal channel exists, redress taking about {facts['remedy_days']} days"
         if facts["remedy_days"] > 0 else "no appeal or redress channel exists at all"),
        "a sunset review is scheduled" if facts["sunset_review"] else "no sunset or periodic review is planned",
        "data collection is minimised to what the task needs" if facts["data_minimised"]
        else "data collection is broader than the task requires",
        "workers in the affected group were consulted" if facts["worker_consulted"]
        else "workers in the affected group were not consulted",
        "the affected people can leave the service" if facts["affected_can_exit"]
        else "the affected people cannot leave the service",
    ])
    consent = ("Minors or dependent adults are among the affected and consent was not obtained."
               if facts["affected_include_minors"] and not facts["consent_obtained"]
               else ("Consent was obtained from the affected adults." if facts["consent_obtained"]
                     else "Consent was never sought from the affected group."))
    parts = [
        f"An autonomous agent operates in {rec['scenario']}, in the domain of "
        f"{DOMAIN_LABELS[rec['domain']]}. The institution rates the stakes as {rec['severity']} "
        f"and the prudential posture as {rec['prudential']}; the action is {rec['irreversibility']} "
        f"in character and is assessed over a {rec['horizon']} horizon, with roughly "
        f"{facts['affected_people']} people exposed.",
        f"Those affected include {', '.join(rec['stakeholders'])}. Within that group, "
        f"{rec['vulnerability']}. {consent}",
        f"If the agent's recommendation is followed, the most plausible consequence is "
        f"{rec['consequence']}, materialising within {hw}. The declared purpose of the deployment "
        f"is to {rec['objective']}.",
        f"The instruments invoked by the review are {', '.join(rec['norms'])}. The oversight "
        f"arrangement is that {rec['review_body']}, and {rec['resource']}. The operating record "
        f"shows that {rec['prior_record']}, and the mitigations on the table are such that "
        f"{rec['mitigation']}.",
        f"Regarding the agent's conduct: {rec['good_evidence']}. However, {rec['bad_evidence']}.",
        f"Operational safeguards: {safeguards}.",
        f"The case displays a {rec['conflict_pattern']} tension: {rec['ambiguity']}.",
        "The oversight body must decide whether to proceed, proceed with conditions, refer the case "
        "to a human panel, suspend the deployment, or abstain until better evidence exists.",
    ]
    return " ".join(" ".join(parts).split())


def make_layerB(n=320):
    cases = []
    for k in range(n):
        d = DOMAINS[k % len(DOMAINS)]
        sev = SEVERITIES[(k // 13) % 4]
        pru = PRUS[(k * 3 + k // 13) % 3]
        irr = IRRS[(k * 5 + k // 13) % 3]
        hor = HORIZONS[(k * 7 + k // 13) % 4]
        pattern = PATTERNS[(k * 11 + k // 13) % len(PATTERNS)]
        cr = np.random.default_rng(SEED * 11 + k)
        ambiguous = (k % 5 == 0)                     # 64 of 320 genuinely contested cases
        exposure = EXPOSURES[(k * 3 + k // 13) % len(EXPOSURES)]
        arch, intent, _ = ARCHETYPES[k % len(ARCHETYPES)]
        facts = make_facts(cr, exposure, arch)
        facts["affected_people"] = max(5, int(round(exposure * 6000)))
        nset1 = NORM_SETS[k % len(NORM_SETS)]
        nset2 = NORM_SETS[(k * 3 + 5) % len(NORM_SETS)]
        norms = tuple(list(nset1[1]) + list(nset2[1]))
        U_E = float(np.clip(round(cr.normal(0.72 if ambiguous else 0.45, 0.20), 4), 0.05, 0.95))
        R_c = float(np.clip(round(cr.normal(0.50, 0.25), 4), 0.05, 0.95))
        case = CaseSpec(f"ETHCASE-B-{k:04d}", d, sev, pru, irr, {}, U_E, R_c,
                        PILLAR_SUBSETS[(k * 3 + 1) % len(PILLAR_SUBSETS)],
                        hor, pattern, "system", norms,
                        norm_conflict=("unresolved" if ambiguous else "none"),
                        evidence_conflict=ambiguous, exposure=exposure,
                        oversight=oversight_from_facts(facts))
        case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
        rec = {
            "case_id": case.case_id, "layer": "B", "domain": d, "severity": sev,
            "prudential": pru, "irreversibility": irr, "horizon": hor,
            "conflict_pattern": pattern, "critical_pillars": list(case.critical_pillars),
            "exposure": round(exposure, 4), "U_E": U_E, "R_c": R_c,
            "stakes": round(case_stakes(case), 4),
            "norm_conflict": case.norm_conflict, "evidence_conflict": case.evidence_conflict,
            "norms": list(norms), "norm_sets": [nset1[0], nset2[0]],
            "scenario": SCENARIOS[d][k % len(SCENARIOS[d])], "archetype": arch,
            "design_intent": intent, "ambiguous": ambiguous, "facts": facts,
            "oversight": oversight_from_facts(facts),
            "stakeholders": list(rng.choice(STAKEHOLDERS[d], size=3).tolist()),
            "vulnerability": VULNERABILITIES[(k * 3 + 3) % len(VULNERABILITIES)],
            "consequence": CONSEQUENCES[(k * 5 + 2) % len(CONSEQUENCES)],
            "objective": OBJECTIVES[(k * 2 + 1) % len(OBJECTIVES)],
            "resource": RESOURCES[(k * 4 + 2) % len(RESOURCES)],
            "review_body": REVIEW_BODY[(k * 5 + 4) % len(REVIEW_BODY)],
            "prior_record": PRIOR_RECORD[(k * 6 + 1) % len(PRIOR_RECORD)],
            "good_evidence": EVIDENCE_GOOD[(k * 3 + 3) % len(EVIDENCE_GOOD)],
            "bad_evidence": EVIDENCE_BAD[(k * 3 + 2) % len(EVIDENCE_BAD)],
            "mitigation": MITIGATIONS[(k * 7 + 1) % len(MITIGATIONS)],
            "ambiguity": AMBIGUITIES[(k * 3 + 2) % len(AMBIGUITIES)] if ambiguous
                          else ("the stated objective and the duties the instruments impose pull in "
                               "the same direction, with the residual risk confined to implementation"),
            "facet_requirements": case.facet_requirements,
            "declared_levels": {f.code: float(min(1.0, case.facet_requirements[f.code]
                                                 * min(DELIVERED_CAP, ARCH_FACTOR[arch](f))))
                                for f in FACETS},
            "declared_confidence": {f.code: float(np.clip(round(cr.normal(0.85, 0.12), 4), 0.35, 1.0))
                                    for f in FACETS},
        }
        rec["narrative"] = build_narrative(rec, facts)
        rec["word_count"] = len(rec["narrative"].split())
        assert rec["word_count"] >= 200, f"{rec['case_id']} has only {rec['word_count']} words"
        cases.append(rec)
    return cases


def case_spec(c):
    return CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                    c["facet_requirements"], c["U_E"], c["R_c"], tuple(c["critical_pillars"]),
                    c["horizon"], c["conflict_pattern"], "system", tuple(c["norms"]),
                    norm_conflict=c["norm_conflict"], evidence_conflict=c["evidence_conflict"],
                    exposure=c["exposure"], oversight=c.get("oversight", "unspecified"))


# ------------------------------------------------------------- r3 baseline ----
def r3_baseline():
    """Read-only measurement of the frozen r3 artefacts (for the before/after table)."""
    out = {}
    try:
        layerA = [json.loads(l) for l in open(os.path.join(R3, "corpus_v4_layerA.jsonl"))]
        vecs = {(c["domain"], c["severity"], c["prudential"], c["irreversibility"], c["horizon"])
                for c in layerA}
        out["layerA_cases"] = len(layerA)
        out["layerA_distinct_design_vectors"] = len(vecs)
        out["layerA_duplicate_design_vectors"] = len(layerA) - len(vecs)
        out["layerA_severity_counts"] = dict(Counter(c["severity"] for c in layerA))
        pers = [json.loads(l) for l in open(os.path.join(R3, "corpus_v4_personas.jsonl"))]
        out["persona_types_r3"] = sorted({p["persona_type"] for p in pers})
        out["persona_types_with_factor_ge_1"] = sorted({p["persona_type"] for p in pers
                                                       if any(v >= 1.0 for v in p["factors"].values())})
        out["max_factor_by_persona_type_r3"] = {p["persona_type"]: max(p["factors"].values()) for p in pers}
        tot = aa1 = abst = 0
        dd = Counter()
        for line in open(os.path.join(R3, "corpus_v4_confrontations.jsonl")):
            r = json.loads(line)
            tot += 1
            if r.get("adequacy") is not None and r["adequacy"] >= 0.999:
                aa1 += 1
            dd[r["decision"]] += 1
            if r["decision"] == "ABSTAIN":
                abst += 1
        out["confrontations"] = tot
        out["share_adequacy_ge_0.999"] = round(aa1 / max(1, tot), 6)
        out["decision_distribution"] = dict(dd)
        out["abstain_count"] = abst
        anchors = list(csv.DictReader(open(os.path.join(R3, "corpus_v4_human_anchor.csv"))))
        out["human_anchor_rows"] = len(anchors)
        out["human_anchor_empty_rater_cells"] = sum(1 for a in anchors
                                                    for f in ("rater1", "rater2", "rater3") if not a[f])
    except Exception as e:
        out["error"] = str(e)
    return out


# ------------------------------------------------------------ main run ----
def main():
    os.makedirs(OUT, exist_ok=True)
    cal = load_fitted_calibration()
    dcal = default_calibration()
    print(f"calibration: fitted bar_base={cal.bar_base}, prohibit_stakes_min={cal.prohibit_stakes_min}, "
          f"critical_prohibit_gap={cal.critical_prohibit_gap}, hysteresis={cal.hysteresis} "
          f"(defaults: bar_base={dcal.bar_base}, stakes_min={dcal.prohibit_stakes_min})")

    layerA = make_layerA(1200)
    layerB = make_layerB(320)
    personas = make_personas()
    cases = layerA + layerB

    with open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_layerA.jsonl"), "w") as fh:
        for c in layerA:
            fh.write(json.dumps(c) + "\n")
    with open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_layerB.jsonl"), "w") as fh:
        for c in layerB:
            fh.write(json.dumps(c) + "\n")
    with open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_personas.jsonl"), "w") as fh:
        for p in personas:
            fh.write(json.dumps(p) + "\n")

    pairs = 0
    aa_hist = Counter()
    aa_list = []
    aa_gold_rank_seq = []
    model_seq = []            # per-pair sequences, so kappa is computed on aligned pairs
    gold_seq = []
    gold_rank_seq = []
    comp_seq = []
    oversight_seq = []
    incomplete_model, incomplete_gold_defer, incomplete_gold_breach = [], [], []
    rank_gap = []
    confusion = Counter()
    decisions = Counter()
    gold_dist = Counter()
    abstain_count = epistemic_abstain = coverage_abstain = 0
    unanimous = kernel_only = 0
    spread_ge1 = 0
    rule_fired = Counter()
    rule_applied = Counter()
    rule_case_ids = defaultdict(set)          # distinct cases each rule fires on
    panel_pairs = {"AB": [[], []], "AC": [[], []], "BC": [[], []]}
    grounding_events = 0
    cap_by_facet = Counter()
    gold_by_pair = {}
    by_type = defaultdict(lambda: {"model": [], "gold": [], "aa": [], "abstain": 0,
                                   "decisions": Counter()})
    veto_count = hard_count = 0
    intent_agree = 0

    with open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_gold.jsonl"), "w") as fg, \
         open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_confrontations.jsonl"), "w") as fc:
        for c in cases:
            spec = case_spec(c)
            req = c["facet_requirements"]
            agents = [({"profile_id": "AGENT-declared", "persona_type": "declared",
                       "tier": "declared", "kind": c["archetype"], "jitter": 0.0,
                       "default_factor": DELIVERED_CAP, "factors": {}, "layer": "system"},
                      c["declared_levels"], c["declared_confidence"])]
            for p in personas:
                declared = [f for f in FACETS if f.code not in p.get("omit", ())]
                levels = {f.code: delivery(f, p, req) for f in declared}
                conf = {f.code: float(np.clip(round(rng.normal(p["confidence_mu"], 0.10), 4), 0.30, 1.0))
                        for f in declared}
                agents.append((p, levels, conf))
            for persona, levels, conf in agents:
                levels, caps = grounded_levels(c["facts"], req, levels, GROUND_STRENGTH)
                grounding_events += len(caps)
                for _fact, code, _cap in caps:
                    cap_by_facet[code] += 1
                g = adjudicate(spec, levels, c["facts"])
                g_alt = (adjudicate(spec, levels, c["facts"], mode="assume_breach")
                         if len(levels) < len(FACETS) else None)
                for rid, fired in rule_stats_for(spec, levels, c["facts"]).items():
                    if fired:
                        rule_fired[rid] += 1
                        rule_case_ids[rid].add(c["case_id"])
                for rid in g["rules_applied"]:
                    rule_applied[rid] += 1
                if g["kernel_only"]:
                    kernel_only += 1
                if g["unanimous"]:
                    unanimous += 1
                if g["spread"] >= 1:
                    spread_ge1 += 1
                gold_dist[g["consensus"]] += 1

                prof = Profile(persona["profile_id"], levels, conf, persona["layer"])
                r = confront(spec, prof, cal)
                if r is None:
                    continue
                aa = r.get("adequacy")
                pairs += 1
                if aa is not None:
                    aa_list.append(aa)
                    aa_gold_rank_seq.append(RANK_ORDER[g["consensus"]])
                    aa_hist[round(aa * 20) / 20.0] += 1
                decisions[r["decision"]] += 1
                if r["decision"] == "ABSTAIN":
                    abstain_count += 1
                    if r.get("epistemic_abstention"):
                        epistemic_abstain += 1
                    elif aa is None:
                        coverage_abstain += 1
                if r.get("veto"):
                    veto_count += 1
                if r.get("hard_veto"):
                    hard_count += 1
                if r["decision"] == g["consensus"]:
                    intent_agree += 1
                model_seq.append(r["decision"])
                gold_seq.append(g["consensus"])
                confusion[(r["decision"], g["consensus"])] += 1
                rank_gap.append(abs(RANK_ORDER[r["decision"]] - RANK_ORDER[g["consensus"]]))
                gold_rank_seq.append(RANK_ORDER[g["consensus"]])
                comp_seq.append(round(r["completeness"], 4))
                oversight_seq.append(c.get("oversight", "unspecified"))
                if g_alt is not None:
                    incomplete_model.append(r["decision"])
                    incomplete_gold_defer.append(g["consensus"])
                    incomplete_gold_breach.append(g_alt["consensus"])
                t = persona["persona_type"]
                by_type[t]["model"].append(r["decision"])
                by_type[t]["gold"].append(g["consensus"])
                if aa is not None:
                    by_type[t]["aa"].append(aa)
                by_type[t]["decisions"][r["decision"]] += 1
                if r["decision"] == "ABSTAIN":
                    by_type[t]["abstain"] += 1
                panel_pairs["AB"][0].append(g["panelA"]); panel_pairs["AB"][1].append(g["panelB"])
                panel_pairs["AC"][0].append(g["panelA"]); panel_pairs["AC"][1].append(g["panelC"])
                panel_pairs["BC"][0].append(g["panelB"]); panel_pairs["BC"][1].append(g["panelC"])
                gold_by_pair[(c["case_id"], persona["profile_id"])] = g["consensus"]
                fg.write(json.dumps({
                    "case_id": c["case_id"], "layer": c["layer"], "domain": c["domain"],
                    "persona": persona["profile_id"], "persona_type": persona["persona_type"],
                    "tier": persona["tier"], "kind": persona.get("kind", "declared"),
                    "kernel": g["kernel"], "kernel_rule": g["kernel_rule"],
                    "panelA": g["panelA"], "panelB": g["panelB"], "panelC": g["panelC"],
                    "consensus": g["consensus"], "spread": g["spread"],
                    "unanimous": g["unanimous"], "kernel_only": g["kernel_only"],
                    "rules_fired": g["rules_fired"], "rules_applied": g["rules_applied"],
                    "duties_below_floor": g["duties_below_floor"],
                    "coverage": g.get("coverage", 1.0),
                    "stakes": g["stakes"], "expected_harm": g["expected_harm"]}) + "\n")
                fc.write(json.dumps({
                    "case_id": c["case_id"], "layer": c["layer"], "domain": c["domain"],
                    "severity": c["severity"], "horizon": c["horizon"],
                    "persona": persona["profile_id"], "persona_type": persona["persona_type"],
                    "tier": persona["tier"], "kind": persona.get("kind", "declared"),
                    "agent_layer": persona["layer"],
                    "adequacy": r.get("adequacy"), "adequacy_low": r.get("adequacy_low"),
                    "adequacy_high": r.get("adequacy_high"), "bar": r.get("bar"),
                    "stakes": r.get("stakes", c.get("stakes")),
                    "risk_ratio": r.get("risk_ratio"), "R_r": r.get("R_r"),
                    "veto": r.get("veto", []), "hard_veto": r.get("hard_veto", []),
                    "material_gap": r.get("material_gap", 0.0),
                    "material_facet": r.get("material_facet"),
                    "worst_facet": r.get("worst_facet"), "decision": r["decision"],
                    "oversight": c.get("oversight", "unspecified"),
                    "review_need": r.get("review_need"),
                    "cross_pillar_duty": r.get("cross_pillar_duty"),
                    "salience_case": r.get("salience_case"),
                    "completeness": round(r["completeness"], 4),
                    "declared_facets": len(levels),
                    "epistemic_abstention": r.get("epistemic_abstention", False),
                    "gold_consensus": g["consensus"],
                    "gold_panels": [g["panelA"], g["panelB"], g["panelC"]],
                    "agree": r["decision"] == g["consensus"],
                    "grounding_strength": GROUND_STRENGTH,
                    "grounding_caps": [{"fact": f, "facet": fc_, "cap": cap} for f, fc_, cap in caps],
                    "facet_levels": [round(levels[f.code], 4) if f.code in levels else None for f in FACETS],
                    "facet_requirements": [round(req[f.code], 4) for f in FACETS],
                    "facet_confidence": [round(conf[f.code], 4) if f.code in conf else None for f in FACETS],
                    "pillar_levels": [round(x, 4) for x in r.get("levels", [])],
                    "deficits": [round(x, 4) for x in r.get("deficits", [])],
                    "guarded_deficits": [round(x, 4) for x in r.get("guarded_deficits", [])],
                    "aa_raw": r.get("adequacy_raw"), "S2": r.get("S2"),
                    "S3": r.get("S3"), "S4": r.get("S4"),
                    "phi": r.get("facet_exposure"), "u": r.get("epistemic_penalty"),
                    "sigma": r.get("sigma"),
                    "design_intent": c.get("design_intent")}) + "\n")

    all_model = model_seq
    all_gold = gold_seq
    kappa_overall = cohens_kappa(all_model, all_gold)
    kappa_by_type = {t: round(cohens_kappa(v["model"], v["gold"]), 4) for t, v in by_type.items()}
    kappa_panel = {k: round(cohens_kappa(a, b), 4) for k, (a, b) in panel_pairs.items()}
    mean_rank_gap = round(float(np.mean(rank_gap)), 4)
    partial_credit = round(sum(1 for g in rank_gap if g <= 1) / len(rank_gap), 4)
    model_stricter = round(sum(n for (m, g), n in confusion.items()
                               if RANK_ORDER[m] < RANK_ORDER[g]) / pairs, 4)
    model_looser = round(sum(n for (m, g), n in confusion.items()
                             if RANK_ORDER[m] > RANK_ORDER[g]) / pairs, 4)
    spearman = round(float(np.corrcoef(np.argsort(aa_list), np.argsort(aa_gold_rank_seq))[0, 1]), 4)

    deficit_types_per_pillar = defaultdict(set)
    for p in personas:
        if p["kind"].startswith("concentrated:"):
            deficit_types_per_pillar[p["kind"].split(":")[1]].add(p["persona_type"])

    distinct_vectors = set()
    for c in layerA:
        distinct_vectors.add((c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                              c["horizon"], c["conflict_pattern"], tuple(c["critical_pillars"]),
                              c["U_E"], c["R_c"], c["exposure"]))
    design_vectors = Counter((c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                              c["horizon"]) for c in layerA)
    facet_critical = Counter()
    for c in cases:
        for f in FACETS:
            if f.criticality.get(c["domain"], 2) == 4:
                facet_critical[f.code] += 1

    max_delivered = max(p["worst_delivered"] for p in personas)

    # ---- P6 audit worksheet (built before the report so the report can describe it) ----
    audit = build_audit_sample(cases, cal, target=120)
    with open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_audit_sample.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["case_id", "layer", "domain", "severity", "irreversibility", "horizon",
                    "conflict_pattern", "norm_conflict", "evidence_conflict", "norms",
                    "scenario_or_narrative", "declared_levels_summary",
                    "model_decision_declared_agent", "gold_consensus_declared_agent",
                    "adjudication_status", "rater_1_verdict", "rater_2_verdict",
                    "rater_3_verdict", "rater_notes"])
        for c, dec, gold in audit:
            w.writerow([c["case_id"], c["layer"], c["domain"], c["severity"], c["irreversibility"],
                        c["horizon"], c["conflict_pattern"], c["norm_conflict"],
                        str(c["evidence_conflict"]), "; ".join(c["norms"]),
                        (c.get("narrative") or c.get("design_rationale", ""))[:1400],
                        ", ".join(f"{k}={v:.2f}" for k, v in sorted(c["declared_levels"].items())),
                        dec, gold,
                        "UNADJUDICATED - no human raters were used (decision D4.5: the adjudicating "
                        "panel is a heterogeneous LLM panel, declared as a limitation); this "
                        "worksheet is for a future human audit and is NOT ground truth",
                        "", "", "", ""])

    report = {
        "generator": "gen_corpus_v5.py", "seed": SEED,
        "calibration": {"bar_base": cal.bar_base, "prohibit_stakes_min": cal.prohibit_stakes_min,
                        "critical_prohibit_gap": cal.critical_prohibit_gap,
                        "hysteresis": cal.hysteresis,
                        "abstain_uncertainty": cal.abstain_uncertainty,
                        "abstain_knowledge_floor": cal.abstain_knowledge_floor,
                        "source": "core.load_fitted_calibration() (Evaluacoes/r4 then r3 ladder_calibration.json)"},
        "cases": {"layerA": len(layerA), "layerB": len(layerB), "total": len(cases)},
        "personas": {"types": len(PERSONA_TYPES), "instances": len(personas),
                     "partial_declaration_types": sum(1 for t in PERSONA_TYPES
                                                      if t[3].startswith("partial")),
                     "partial_declaration_instances": sum(1 for p in personas
                                                          if p["kind"].startswith("partial")),
                     "declared_facets_range": [min(p["declared_facets"] for p in personas),
                                              max(p["declared_facets"] for p in personas)],
                     "concentrated_deficit_types": sum(1 for t in PERSONA_TYPES
                                                       if t[3].startswith("concentrated")),
                     "concentrated_deficit_instances": sum(1 for p in personas
                                                           if p["kind"].startswith("concentrated")),
                     "deficit_types_per_pillar": {p: sorted(v) for p, v in deficit_types_per_pillar.items()},
                     "max_effective_delivery": round(max_delivered, 4),
                     "personas_exceeding_cap": sum(1 for p in personas if p["worst_delivered"] > DELIVERED_CAP)},
        "pairs_adjudicated": pairs,
        "cases_by_layer": dict(Counter(c["layer"] for c in cases)),
        "cases_by_domain": dict(Counter(c["domain"] for c in cases)),
        "cases_by_layer_domain": dict(Counter(f"{c['layer']}/{c['domain']}" for c in cases)),
        "cases_by_severity": dict(Counter(c["severity"] for c in cases)),
        "cases_by_layer_severity": dict(Counter(f"{c['layer']}/{c['severity']}" for c in cases)),
        "cases_by_horizon": dict(Counter(c["horizon"] for c in cases)),
        "cases_by_irreversibility": dict(Counter(c["irreversibility"] for c in cases)),
        "cases_by_prudential": dict(Counter(c["prudential"] for c in cases)),
        "cases_by_conflict_pattern": dict(Counter(c["conflict_pattern"] for c in cases)),
        "distinct_layerA_parameter_vectors": len(distinct_vectors),
        "distinct_layerA_design_vectors": len(design_vectors),
        "layerA_duplicate_vectors": len(layerA) - len(distinct_vectors),
        "max_design_vector_multiplicity": max(design_vectors.values()),
        "coverage_gate_counts_both_layers": True,
        "facet_critical_case_counts": dict(facet_critical),
        "facets_with_ge_5_critical_cases": sum(1 for f in FACETS if facet_critical.get(f.code, 0) >= 5),
        "ambiguity": {"norm_conflict_unresolved": sum(1 for c in cases if c["norm_conflict"] != "none"),
                      "evidence_conflict": sum(1 for c in cases if c["evidence_conflict"])},
        "template_diversity": {"consequence_types": len(set(c["consequence"] for c in layerB)),
                               "vulnerability_types": len(set(c["vulnerability"] for c in layerB)),
                               "norm_sets": len(set(x for c in layerB for x in c["norm_sets"])),
                               "distinct_instrument_strings": len(set(x for c in cases for x in c["norms"]))},
        "adequacy": {"n": len(aa_list), "mean": round(float(np.mean(aa_list)), 4),
                     "min": round(min(aa_list), 4), "max": round(max(aa_list), 4),
                     "p50": round(float(np.median(aa_list)), 4),
                     "histogram_0.05": {f"{k:.2f}": v for k, v in sorted(aa_hist.items())},
                     "share_ge_0.999": round(sum(1 for x in aa_list if x >= 0.999) / len(aa_list), 6),
                     "share_ge_0.99": round(sum(1 for x in aa_list if x >= 0.99) / len(aa_list), 6)},
        "decision_distribution": dict(decisions),
        "abstain": {"total": abstain_count, "epistemic_E29": epistemic_abstain,
                    "coverage_E26": coverage_abstain,
                    "coverage_gate": abstain_count - epistemic_abstain,
                    "share": round(abstain_count / max(1, pairs), 6)},
        "oversight_regimes": dict(Counter(oversight_seq)),
        "coverage_strata": {
            "full_canon_33": sum(1 for x in comp_seq if x >= 1.0),
            "partial_23_to_32": sum(1 for x in comp_seq if 0.70 <= x < 1.0),
            "below_gate_lt_0.70": sum(1 for x in comp_seq if x < 0.70)},
        "kappa_by_coverage": {
            "full": round(cohens_kappa([m for m, c in zip(model_seq, comp_seq) if c >= 1.0],
                                       [g for g, c in zip(gold_seq, comp_seq) if c >= 1.0]), 4),
            "partial": round(cohens_kappa([m for m, c in zip(model_seq, comp_seq) if 0.70 <= c < 1.0],
                                         [g for g, c in zip(gold_seq, comp_seq) if 0.70 <= c < 1.0]), 4),
            "below_gate": round(cohens_kappa([m for m, c in zip(model_seq, comp_seq) if c < 0.70],
                                            [g for g, c in zip(gold_seq, comp_seq) if c < 0.70]), 4)},
        "criticality_mass_by_domain": {d: sum(f.criticality.get(d, 2) for f in FACETS) for d in DOMAINS},
        "verification_gap_D5_8": {
            "pairs_with_incomplete_declaration": len(incomplete_model),
            "model_verdict_mix": dict(Counter(incomplete_model)),
            "kappa_defer_rule_on": round(cohens_kappa(incomplete_model, incomplete_gold_defer), 4),
            "kappa_if_missing_duties_count_as_zero": round(cohens_kappa(incomplete_model, incomplete_gold_breach), 4),
            "gold_mix_defer": dict(Counter(incomplete_gold_defer)),
            "gold_mix_assume_breach": dict(Counter(incomplete_gold_breach)),
        },
        "veto_rate": round(veto_count / pairs, 4), "hard_veto_rate": round(hard_count / pairs, 4),
        "gold": {"consensus_distribution": dict(gold_dist),
                 "unanimous_share": round(unanimous / pairs, 4),
                 "contested_share_spread_ge_1": round(spread_ge1 / pairs, 4),
                 "kernel_only_count": kernel_only,
                 "kernel_only_share": round(kernel_only / pairs, 6),
                 "kernel_only_gate_max_0.40": (kernel_only / pairs) <= 0.40,
                 "panel_kappa": kappa_panel,
                 "model_gold_agreement": round(intent_agree / pairs, 4),
                 "rules": [{"id": rid, "instrument": ins, "condition": cond,
                            "fired_pairs": rule_fired[rid],
                            "fired_distinct_cases": len(rule_case_ids[rid]),
                            "changed_panel_verdict_pairs": rule_applied[rid]}
                           for rid, ins, cond, *_ in ALL_RULES],
                 "rules_firing_ge_50_pairs": sum(1 for rid in rule_fired if rule_fired[rid] >= 50),
                 "rules_firing_on_ge_50_cases": sum(1 for rid in rule_case_ids
                                                    if len(rule_case_ids[rid]) >= 50),
                 "rules_total": len(ALL_RULES)},
        "kappa_model_vs_gold": {"overall": round(kappa_overall, 4), "by_persona_type": kappa_by_type},
        "model_vs_gold": {"exact_match_rate": round(intent_agree / pairs, 4),
                          "within_one_step_rate": partial_credit,
                          "mean_rank_gap": mean_rank_gap,
                          "model_stricter_than_gold_rate": model_stricter,
                          "model_looser_than_gold_rate": model_looser,
                          "spearman_Aa_vs_gold_rank": spearman,
                          "confusion": {f"{m} -> {g}": n for (m, g), n in
                                        sorted(confusion.items(), key=lambda x: -x[1])},
                          "r3_reference_kappa_full_grid": 0.0092},
        "decision_distribution_by_persona_type": {t: dict(v["decisions"]) for t, v in by_type.items()},
        "audit_sample": {"rows": len(audit),
                         "stratified_by": "decision class x domain",
                         "decision_composition": dict(Counter(d for _, d, _ in audit)),
                         "domain_composition": dict(Counter(c["domain"] for c, _, _ in audit)),
                         "adjudication_status": "UNADJUDICATED - no human raters; not ground truth",
                         "empty_rater_cells": sum(3 for _ in audit)},
        "baseline_r3": r3_baseline(),
        "gates": {},
    }
    report["gates"] = {
        "a_no_duplicate_layerA_parameter_vectors": len(distinct_vectors) == len(layerA),
        "b_share_adequacy_ge_0.999_below_0.05": report["adequacy"]["share_ge_0.999"] < 0.05,
        "c_concentrated_deficit_persona_type_per_pillar": (
            all(len(v) >= 1 for v in deficit_types_per_pillar.values())
            and report["personas"]["concentrated_deficit_types"] >= 15),
        "d_at_least_15_rules_firing_on_50_plus_cases": report["gold"]["rules_firing_on_ge_50_cases"] >= 15,
        "e_abstain_fires_on_some_cases": abstain_count > 0,
        "f_all_artefacts_written_to_r4": all(
            os.path.exists(os.path.join(OUT, f)) for f in (
                f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl", f"corpus_v{CORPUS_VER}_personas.jsonl",
                f"corpus_v{CORPUS_VER}_gold.jsonl", f"corpus_v{CORPUS_VER}_confrontations.jsonl",
                f"corpus_v{CORPUS_VER}_coverage.json", f"corpus_v{CORPUS_VER}_audit_sample.csv")),
        "gold_kernel_only_share_below_0.40": (kernel_only / pairs) <= 0.40,
        "severity_low_used_in_layerA": design_vectors_count_low(layerA) > 0,
        "all_13_domains_covered": len({c["domain"] for c in cases}) == len(DOMAINS),
    }
    with open(os.path.join(OUT, f"corpus_v{CORPUS_VER}_coverage.json"), "w") as fh:
        json.dump(report, fh, indent=2)

    # ---- calibration sensitivity: what the verdicts look like under the r4 v12 ladder fit ----
    v12_path = os.path.join(OUT, "ladder_calibration_v12.json")
    sensitivity = None
    if os.path.exists(v12_path):
        cal12 = load_fitted_calibration(v12_path)
        dec12, aa12, agree12 = Counter(), [], 0
        seq_m, seq_g = [], []
        for c in cases:
            spec = case_spec(c)
            for p in personas:
                levels = {f.code: delivery(f, p, c["facet_requirements"]) for f in FACETS}
                conf = c.get("declared_confidence", {f.code: 0.85 for f in FACETS}) \
                    if p["persona_type"] == "declared" else {f.code: 0.85 for f in FACETS}
                r = confront(spec, Profile(p["profile_id"], levels, conf, p["layer"]), cal12)
                dec12[r["decision"]] += 1
                aa12.append(r["adequacy"])
                seq_m.append(r["decision"])
                seq_g.append(gold_by_pair.get((c["case_id"], p["profile_id"]), r["decision"]))
        sensitivity = {"calibration_source": v12_path,
                       "bar_base": cal12.bar_base, "ratio_prohibit": cal12.ratio_prohibit,
                       "critical_prohibit_gap": cal12.critical_prohibit_gap,
                       "decision_distribution": dict(dec12),
                       "share_adequacy_ge_0.999": round(sum(1 for x in aa12 if x >= 0.999) / len(aa12), 6),
                       "kappa_vs_gold_consensus": round(cohens_kappa(seq_m, seq_g), 4)}
    report["calibration_sensitivity_r4_v12_fit"] = sensitivity
    report["fact_grounding_E30"] = {"strength": GROUND_STRENGTH, "caps_applied": grounding_events,
                                    "pairs": pairs, "caps_per_pair": round(grounding_events / pairs, 3),
                                    "by_facet": dict(cap_by_facet)}

    print_summary(report, by_type, kappa_by_type)
    return report


def design_vectors_count_low(layerA):
    return sum(1 for c in layerA if c["severity"] == "low")


def build_audit_sample(cases, cal, target=120):
    """120 cases stratified by decision class and domain, explicitly unadjudicated.

    P6 / decision D4.5: there are no human raters. The worksheet is a *future* audit
    instrument: every row carries the model verdict and the rubric consensus for the
    record, but the rater columns are empty and the status field says UNADJUDICATED.
    It must never be read as ground truth.
    """
    scored = []
    for c in cases:
        spec = case_spec(c)
        prof = Profile("AGENT-declared", c["declared_levels"], c["declared_confidence"], "system")
        r = confront(spec, prof, cal)
        g = adjudicate(spec, c["declared_levels"], c["facts"])
        scored.append((c, r["decision"], g["consensus"]))

    buckets = defaultdict(list)
    for c, dec, gold in scored:
        buckets[dec].append((c, dec, gold))
    pool = []
    n_dec = len(buckets)
    quota = max(1, target // n_dec)
    for dec in sorted(buckets):
        items = sorted(buckets[dec], key=lambda x: (x[0]["domain"], x[0]["case_id"]))
        dom = defaultdict(int)
        chosen = []
        for c, d, g in items:
            if dom[c["domain"]] >= 2:            # spread the sample across domains
                continue
            chosen.append((c, d, g))
            dom[c["domain"]] += 1
            if len(chosen) >= quota:
                break
        pool.extend(chosen[:quota])
    # top-up, keeping domain balance
    dom_used = Counter(c["domain"] for c, _, _ in pool)
    for c, d, g in scored:
        if len(pool) >= target:
            break
        if any(p[0]["case_id"] == c["case_id"] for p in pool):
            continue
        if dom_used[c["domain"]] < 10:
            pool.append((c, d, g))
            dom_used[c["domain"]] += 1
    return pool[:target]


def print_summary(report, by_type, kappa_by_type):
    print("\n" + "=" * 80)
    print("ETHCASE corpus v5 (Evaluacoes/r4) - run summary")
    print("=" * 80)
    p = report
    print(f"cases: layerA={p['cases']['layerA']}  layerB={p['cases']['layerB']}  "
          f"personas={p['personas']['instances']} (types={p['personas']['types']}, "
          f"concentrated-deficit types={p['personas']['concentrated_deficit_types']})")
    print(f"(case, persona) pairs confronted and adjudicated: {p['pairs_adjudicated']}")
    print(f"layerA distinct parameter vectors: {p['distinct_layerA_parameter_vectors']} "
          f"/ {p['cases']['layerA']}  (duplicates: {p['layerA_duplicate_vectors']})")
    print(f"severities: {p['cases_by_severity']}")
    print(f"Aa: mean={p['adequacy']['mean']} median={p['adequacy']['p50']} "
          f"min={p['adequacy']['min']} max={p['adequacy']['max']} "
          f"share>=0.999={p['adequacy']['share_ge_0.999']}")
    print(f"decisions: {p['decision_distribution']}")
    print(f"ABSTAIN: total={p['abstain']['total']} (epistemic E29={p['abstain']['epistemic_E29']}, "
          f"coverage gate={p['abstain']['coverage_gate']})")
    print(f"gold consensus: {p['gold']['consensus_distribution']}  "
          f"kernel-only share={p['gold']['kernel_only_share']} (gate <= 0.40)")
    print(f"model-gold agreement rate: {p['gold']['model_gold_agreement']}")
    print(f"kappa model vs gold: overall={p['kappa_model_vs_gold']['overall']}")
    print(f"panel kappa (A-B, A-C, B-C): {p['gold']['panel_kappa']}")
    print(f"normative rules: {p['gold']['rules_total']} declared, "
          f"{p['gold']['rules_firing_on_ge_50_cases']} firing on >=50 distinct cases")
    print("\nGates:")
    for k, v in p["gates"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("\nPer persona type:")
    print(f"  {'persona type':<24} {'n':>6} {'mean Aa':>8} {'kappa':>7} {'ABSTAIN':>8}  verdict mix")
    abbrev = {"ABSTAIN": "ABS", "PROHIBIT": "PRO", "REVIEW_REQUIRED": "REV",
              "ALLOW_WITH_GUARDS": "AWG", "ALLOW": "ALL"}
    for t, k in sorted(kappa_by_type.items()):
        v = by_type[t]
        decs = " ".join(f"{abbrev[d]}:{n}" for d, n in sorted(v["decisions"].items()))
        print(f"  {t:<24} {len(v['model']):>6} {float(np.mean(v['aa'])):>8.4f} {k:>7.4f} "
              f"{v['abstain']:>8}  {decs}")
    print("\nBaseline (frozen r3, measured read-only):")
    b = report["baseline_r3"]
    for k, v in b.items():
        if isinstance(v, dict):
            print(f"  {k}: {json.dumps(v)[:160]}")
        else:
            print(f"  {k}: {v}")
    print("\nfiles written to", OUT)


def rule_stats_for(spec, levels, facts):
    from gold_panels_v5 import rule_stats
    return rule_stats(spec, levels, facts)


if __name__ == "__main__":
    main()
