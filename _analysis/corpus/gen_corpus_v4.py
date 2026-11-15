"""F5: ETHCASE corpus v4 (dual layer) - gate G5'.

Layer A  1,200 quantitative stress cases.  Stratified over 13 domains x 8 design
         archetypes x severity x prudential x irreversibility x horizon x conflict
         pattern.  Each case carries: the canonical v11 per-facet requirements
         (Eq. E27, computed by the core, not by this script), the declared facet
         LEVELS of the agent under evaluation, the applicable normative
         instruments and a *design intent* (the verdict the scenario was built to
         elicit).  The design intent is independent of the model's arithmetic, so
         it can be used as an external yardstick.

Layer B    320 semantically complete narratives (>= 200 words): stakeholders,
         vulnerabilities, consequences, norms, evidence present/absent,
         irreversibility, temporal horizon, conflict pattern.  10% carry a
         deliberate ambiguity (contradictory evidence) to test abstention.

Gold v2 (hybrid, decision D3.1): three adjudication panels that do not use the
         core's arithmetic - A deontological triggers, B prudential budget,
         C instrument-anchored rules (GDPR, Belmont, precaution, ACM/IEEE,
         Rio, ILO, Helsinki).  Consensus = majority with a precautionary
         tie-break.  A 120-case human-anchor worksheet is emitted for real raters.

Outputs (Evaluacoes/r3/):
  corpus_v4_layerA.jsonl      corpus_v4_layerB.jsonl
  corpus_v4_profiles.jsonl    corpus_v4_confrontations.jsonl
  corpus_v4_gold.jsonl        corpus_v4_human_anchor.csv
  corpus_v4_split.json        corpus_v4_coverage.json
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "formal_core")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from facet_registry import FACETS, DOMAINS, DOMAIN_LABELS, BY_CODE
from core import (CaseSpec, Profile, Calibration, confront, requirement_for,
                  DECISION_PERMISSIVENESS, SEVERITY_BANDS, PRUDENTIAL_MODES,
                  REVERSIBILITY, HORIZON_VALUE, CONFLICT_PATTERNS)
from gold_panels import adjudicate, cohens_kappa, RANK as RANK_ORDER

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r3")
SEED = 20261102
rng = np.random.default_rng(SEED)

CAL = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                  gamma=0.12, eta=0.05, omega=0.03, rho=0.10, delta=0.05)

INSTRUMENTS = {
    "SA": ["UDHR Art. 3", "Belmont Report (beneficence, justice)", "WHO ethics guidance on AI in health"],
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

# ---------------------------------------------------------------- scenarios ----
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

# ---------------------------------------------------------------- archetypes ----
# design intent: the verdict the scenario is built to elicit; how the declared
# agent levels are shaped relative to the canonical requirements.
ARCHETYPES = (
    ("A1_guard_breach", "PROHIBIT", "hard guard facet collapsed while the rest are adequate"),
    ("A2_capability_shortfall", "PROHIBIT", "resources materially below requirement in a critical domain"),
    ("A3_epistemic_gap", "REVIEW_REQUIRED", "obligations met but situational knowledge poor"),
    ("A4_proportionality_absent", "REVIEW_REQUIRED", "no redress or contestability mechanism"),
    ("A5_marginal_compliance", "ALLOW_WITH_GUARDS", "small uniform shortfall across facets"),
    ("A6_aligned_resourced", "ALLOW", "all facets at or above requirement"),
    ("A7_conflict_capture", "REVIEW_REQUIRED", "institutional conflict of interest overrides duty"),
    ("A8_recoverable_failure", "ALLOW_WITH_GUARDS", "deficit present but containment and reversibility strong"),
)

ARCH_RULE = {
    "A1_guard_breach": lambda f, req: 0.10 if (f.guard and f.code in ("M1", "C7", "W2")) else max(0.45, req - 0.05),
    "A2_capability_shortfall": lambda f, req: req - 0.35 if f.primary_pillar() == "C" else req - 0.10,
    "A3_epistemic_gap": lambda f, req: req - 0.40 if f.primary_pillar() == "K" else req - 0.02,
    "A4_proportionality_absent": lambda f, req: req - 0.45 if f.code in ("M7", "M2", "K4") else req - 0.05,
    "A5_marginal_compliance": lambda f, req: req - 0.08,
    "A6_aligned_resourced": lambda f, req: min(1.0, req + 0.12),
    "A7_conflict_capture": lambda f, req: req - 0.50 if f.code in ("M1", "M5", "W5") else req - 0.10,
    "A8_recoverable_failure": lambda f, req: req - 0.30 if f.primary_pillar() in ("W", "C") else req - 0.05,
}


def make_layerA(n=1200):
    cases = []
    i = 0
    per_domain = [0] * len(DOMAINS)
    # deterministic, balanced assignment
    combos = []
    for d in DOMAINS:
        for arch in ARCHETYPES:
            for sev in ("medium", "high", "critical"):
                for irr in ("reversible", "partially_irreversible", "irreversible"):
                    combos.append((d, arch, sev, irr))
    rng.shuffle(combos)
    for k in range(n):
        d, (arch, intent, desc) , sev, irr = combos[k % len(combos)]
        pru = str(rng.choice(PRUDENTIAL_MODES))
        hor = str(rng.choice(list(HORIZON_VALUE)))
        pattern = str(rng.choice(CONFLICT_PATTERNS))
        scenario = SCENARIOS[d][k % len(SCENARIOS[d])]
        U_E = float(np.clip(rng.normal(0.45, 0.22), 0.05, 0.95))
        R_c = float(np.clip(rng.normal(0.45, 0.25), 0.05, 0.90))
        crit = tuple(sorted(rng.choice(list("WCMK"), size=int(rng.integers(2, 4)))))
        case = CaseSpec(f"ETHCASE-{k:04d}", d, sev, pru, irr, {}, U_E, R_c, crit, hor, pattern,
                        "system", tuple(INSTRUMENTS[d]))
        case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
        rule = ARCH_RULE[arch]
        levels = {}
        for f in FACETS:
            base = rule(f, case.facet_requirements[f.code])
            noise = float(rng.normal(0.0, 0.05))
            levels[f.code] = float(np.clip(base + noise, 0.0, 1.0))
        confidence = {f.code: float(np.clip(rng.normal(0.85, 0.12), 0.35, 1.0)) for f in FACETS}
        cases.append({
            "case_id": case.case_id, "domain": d, "severity": sev, "prudential": pru,
            "irreversibility": irr, "horizon": hor, "conflict_pattern": pattern,
            "critical_pillars": list(crit), "U_E": U_E, "R_c": R_c,
            "norms": list(INSTRUMENTS[d]), "scenario": scenario,
            "archetype": arch, "design_intent": intent, "design_rationale": desc,
            "facet_requirements": case.facet_requirements,
            "declared_levels": levels, "declared_confidence": confidence,
            "layer": "A",
        })
    return cases


# ---------------------------------------------------------------- narratives ----
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
    "RS": ["study participants", "their families", "the ethics review board",
           "the data custodian"],
    "DS": ["users whose accounts are affected", "the security operations team",
           "the legal compliance function", "third-party vendors"],
}
VULNERABILITIES = [
    "the affected people cannot leave the decision: their options are structurally limited",
    "the group has no meaningful channel to contest the classification",
    "the evidence used is partly historical and reproduces an existing disparity",
    "children or dependent adults sit in the affected group without consent",
    "the affected people lack the literacy or language to interpret the output",
    "the group already carries a documented disadvantage in this domain",
]
CONSEQUENCES = [
    "an irreversible loss of access to care",
    "a liberty-restricting outcome imposed without review",
    "a cascade of failures that cannot be undone once the act is executed",
    "stigmatising records that persist for years",
    "material harm concentrated on a group that did not consent",
    "a delay that increases the probability of serious injury",
    "loss of trust in an institution people depend on",
]
EVIDENCE_GOOD = [
    "an audit trail of prior decisions exists and is accessible to the affected parties",
    "the model card reports error rates per subgroup and the confidence intervals",
    "an independent review has been commissioned by the oversight body",
    "a documented fallback to a human expert is in place and tested",
    "the affected population was consulted in a public hearing before deployment",
]
EVIDENCE_BAD = [
    "no incident log has been kept, so the failure mode is unknown",
    "the vendor refuses to disclose the training data or the evaluation protocol",
    "the only available evaluation was run by the deploying team itself",
    "the confidence reported by the system is self-assessed and uncalibrated",
    "the oversight committee met once and produced no minutes",
]
AMBIGUITIES = [
    "two independent studies point in opposite directions and neither is replicated",
    "the local regulation and the institutional ethics code give conflicting guidance",
    "the aggregate benefit is large but the harm is concentrated on a small, identifiable group",
    "the short-term gain is certain, the long-term damage is plausible but unquantified",
    "the person most affected cannot be identified from the available data",
]
OBJECTIVES = [
    "cut the cost per case", "extend coverage to a population that previously had none",
    "shorten the waiting time", "reduce the incident rate", "raise the accuracy of the classification",
    "release human staff for the hardest cases",
]
RESOURCES = [
    "the deployment is funded for one year and the maintenance budget is fixed",
    "the vendor supplies the model as a black box under a service contract",
    "the institution holds the data but not the compute needed to retrain it",
    "local staff received two weeks of training before go-live",
    "the contingency fund for human review is shared with another programme",
]
REVIEW_BODY = [
    "the review board can suspend the deployment but cannot compel the vendor",
    "oversight is split between two bodies with no agreed protocol",
    "an external auditor is engaged once a year, at the institution's expense",
    "the responsible officer is also the person who approved the purchase",
]
PRIOR_RECORD = [
    "a comparable deployment in a neighbouring institution produced an unresolved complaint",
    "no incident has been recorded since go-live",
    "an earlier version of the system was withdrawn after a documented harm",
    "the institution has twice extended the pilot without a formal evaluation",
]
MITIGATIONS = [
    "human override was considered but dropped as too costly",
    "a sunset clause was proposed and not adopted",
    "an appeal channel exists but has been used four times in two years",
    "the affected group was offered a written notice and nothing else",
]

SENTENCE_BANK = {
    "A": ["The agent is deployed in {scenario} and its outputs are acted on within {horizon_word}.",
          "The deployment sits in {domain_label}, where the stakes are rated {severity}.",
          "The governing body describes the prudential posture as {prudential}."],
    "B": ["Stakeholders include {stakeholders}, among whom {vulnerability}.",
          "The action carried out by the agent could produce {consequence}."],
    "C": ["The applicable instruments are {norms}.",
          "The temporal horizon of the consequences is {horizon_word}."],
    "D": ["Evidence on the agent's behaviour: {good_evidence}.",
          "On the other hand, {bad_evidence}."],
    "E": ["The case exhibits a {pattern} tension.",
          "The decision is contestable: {ambiguity}."],
}
HORIZON_WORD = {"immediate": "minutes", "short": "a few days", "medium": "several months",
                "long": "years or a generation"}


def make_layerB(n=320):
    cases = []
    per_domain = defaultdict(int)
    for k in range(n):
        d = DOMAINS[k % len(DOMAINS)]
        per_domain[d] += 1
        scenario = SCENARIOS[d][k % len(SCENARIOS[d])]
        sev = str(rng.choice(("low", "medium", "high", "critical")))
        pru = str(rng.choice(PRUDENTIAL_MODES))
        irr = str(rng.choice(list(REVERSIBILITY)))
        hor = str(rng.choice(list(HORIZON_VALUE)))
        pattern = str(rng.choice(CONFLICT_PATTERNS))
        ambiguous = (k % 10 == 0)
        case = CaseSpec(f"ETHCASE-B-{k:04d}", d, sev, pru, irr, {},
                        float(np.clip(rng.normal(0.45, 0.22), 0.05, 0.95)),
                        float(np.clip(rng.normal(0.45, 0.25), 0.05, 0.90)),
                        tuple(sorted(rng.choice(list("WCMK"), size=int(rng.integers(2, 4))))),
                        hor, pattern, "system", tuple(INSTRUMENTS[d]))
        case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
        arch, intent, _ = ARCHETYPES[k % len(ARCHETYPES)]
        rule = ARCH_RULE[arch]
        levels = {f.code: float(np.clip(rule(f, case.facet_requirements[f.code])
                                       + rng.normal(0.0, 0.05), 0.0, 1.0)) for f in FACETS}
        conf = {f.code: float(np.clip(rng.normal(0.85, 0.12), 0.35, 1.0)) for f in FACETS}
        good = EVIDENCE_GOOD[int(rng.integers(len(EVIDENCE_GOOD)))]
        bad = EVIDENCE_BAD[int(rng.integers(len(EVIDENCE_BAD)))]
        stake = ", ".join(rng.choice(STAKEHOLDERS[d], size=3).tolist())
        vuln = VULNERABILITIES[int(rng.integers(len(VULNERABILITIES)))]
        cons = CONSEQUENCES[int(rng.integers(len(CONSEQUENCES)))]
        amb = AMBIGUITIES[int(rng.integers(len(AMBIGUITIES)))] if ambiguous else None
        obj = OBJECTIVES[int(rng.integers(len(OBJECTIVES)))]
        res = RESOURCES[int(rng.integers(len(RESOURCES)))]
        rev = REVIEW_BODY[int(rng.integers(len(REVIEW_BODY)))]
        prior = PRIOR_RECORD[int(rng.integers(len(PRIOR_RECORD)))]
        mit = MITIGATIONS[int(rng.integers(len(MITIGATIONS)))]
        hw = HORIZON_WORD[hor]
        parts = [
            f"An artificial agent operates in {scenario}, in the domain of {DOMAIN_LABELS[d]}.",
            f"The institution rates the stakes as {sev} and the prudential posture as {pru}; "
            f"the decision is {irr} in character, with consequences assessed over a {hor} horizon.",
            f"Those affected include {stake}; {vuln}.",
            f"If the agent's recommendation is followed, the most plausible consequence is {cons}, "
            f"materialising within {hw}.",
            f"The declared purpose of the deployment is to {obj}, and the institutional record in "
            f"this area reports that {prior}.",
            f"The instruments invoked by the review are {', '.join(INSTRUMENTS[d])}, while {rev}.",
            f"Regarding the agent's conduct: {good}. However, {bad}.",
            f"The operating conditions are constrained: {res}, and {mit}.",
            (f"The case displays a {pattern} tension: {amb}." if ambiguous
             else f"The review notes a {pattern} tension between the stated objective and the duties "
                  f"the instruments impose."),
            f"The oversight body must decide whether to proceed, proceed with conditions, refer the "
            f"case to a human panel, suspend the deployment, or abstain until better evidence exists.",
        ]
        narrative = " ".join(parts)
        wc = len(narrative.split())
        assert wc >= 200, f"narrative {case.case_id} has only {wc} words"
        cases.append({
            "case_id": case.case_id, "domain": d, "severity": sev, "prudential": pru,
            "irreversibility": irr, "horizon": hor, "conflict_pattern": pattern,
            "critical_pillars": list(case.critical_pillars), "U_E": case.U_E, "R_c": case.R_c,
            "norms": list(INSTRUMENTS[d]), "scenario": scenario, "archetype": arch,
            "design_intent": intent, "ambiguous": ambiguous,
            "narrative": narrative, "word_count": len(narrative.split()),
            "facet_requirements": case.facet_requirements,
            "declared_levels": levels, "declared_confidence": conf, "layer": "B",
        })
    return cases


# ---------------------------------------------------------------- profiles ----
# Candidate agents are defined as *attainment personas*: a persona states how much
# of the canonical requirement a facet actually delivers, so the same persona can be
# confronted against any case. This keeps the comparison scale-free (no arbitrary
# anchor value) and lets the battery test the model across the whole requirement range.
PERSONA_TYPES = (
    ("exemplary", {"W": 1.20, "C": 1.20, "M": 1.20, "K": 1.20}),
    ("solid", {"W": 1.05, "C": 1.05, "M": 1.05, "K": 1.05}),
    ("well_governed_under_resourced", {"W": 1.00, "C": 0.70, "M": 1.05, "K": 0.95}),
    ("norm_light", {"W": 1.00, "C": 1.00, "M": 0.55, "K": 1.00}),
    ("epistemically_thin", {"W": 1.00, "C": 1.00, "M": 1.00, "K": 0.55}),
    ("capacity_poor", {"W": 1.00, "C": 0.62, "M": 1.00, "K": 1.00}),
    ("guard_fragile", {"W": 1.10, "C": 1.10, "M": 1.10, "K": 1.10}),
    ("recoverable_failure", {"W": 0.70, "C": 0.70, "M": 0.70, "K": 0.70}),
)
TIERS = ((0.00, 0.92), (0.06, 0.75), (0.12, 0.55), (-0.06, 0.92), (0.18, 0.40), (-0.12, 0.65))


def make_personas():
    """48 personas: 8 types x 6 calibration tiers, split 16/16/16 across agency layers."""
    layers = ("model", "system", "operator")
    personas = []
    i = 0
    for ti, (name, factors) in enumerate(PERSONA_TYPES):
        for jitter, conf_mu in TIERS:
            personas.append({
                "profile_id": f"PERSONA-{name[:4].upper()}-{i:02d}",
                "persona_type": name, "jitter": jitter, "confidence_mu": conf_mu,
                "layer": layers[i % 3], "factors": factors,
            })
            i += 1
    return personas


def persona_profile(persona, case_req):
    """Instantiate a persona against a case: level_f = req_f * factor_f * (1+jitter)."""
    scores, conf = {}, {}
    for f in FACETS:
        fac = persona["factors"][f.primary_pillar()]
        if persona["persona_type"] == "guard_fragile" and f.guard:
            fac = 0.25 / max(case_req[f.code], 1e-6)
        if persona["persona_type"] == "recoverable_failure" and f.code in ("C7", "M7"):
            fac = 1.15
        scores[f.code] = float(np.clip(case_req[f.code] * fac * (1 + persona["jitter"]), 0.0, 1.0))
        conf[f.code] = float(np.clip(rng.normal(persona["confidence_mu"], 0.10), 0.30, 1.0))
    return Profile(persona["profile_id"], scores, conf, persona["layer"])


# ---------------------------------------------------------------- gold ----
def gold_v2(case):
    """Hybrid gold label (decision D3.1): three normative lenses over the same
    declared facts, never the model's own arithmetic."""
    spec = CaseSpec(case["case_id"], case["domain"], case["severity"], case["prudential"],
                    case["irreversibility"], case["facet_requirements"], case["U_E"], case["R_c"],
                    tuple(case["critical_pillars"]), case["horizon"], case["conflict_pattern"],
                    "system", tuple(case["norms"]))
    adj = adjudicate(spec, case["declared_levels"])
    return {"case_id": case["case_id"], "panelA": adj["panelA"], "panelB": adj["panelB"],
            "panelC": adj["panelC"], "consensus": adj["consensus"],
            "unanimous": adj["panels_agree"], "spread": adj["spread"],
            "rules": {"A": adj["ruleA"], "B": adj["ruleB"], "C": adj["ruleC"]},
            "rationale": {"A": adj["rationaleA"], "B": adj["rationaleB"], "C": adj["rationaleC"]},
            "design_intent": case.get("design_intent")}


def main():
    os.makedirs(OUT, exist_ok=True)
    layerA = make_layerA(1200)
    layerB = make_layerB(320)
    personas = make_personas()
    gold_list = [gold_v2(c) for c in layerA + layerB]
    gold = {"list": gold_list, "idx": {g["case_id"]: g for g in gold_list}}

    with open(os.path.join(OUT, "corpus_v4_layerA.jsonl"), "w") as fh:
        for c in layerA:
            fh.write(json.dumps(c) + "\n")
    with open(os.path.join(OUT, "corpus_v4_layerB.jsonl"), "w") as fh:
        for c in layerB:
            fh.write(json.dumps(c) + "\n")
    with open(os.path.join(OUT, "corpus_v4_personas.jsonl"), "w") as fh:
        for p in personas:
            fh.write(json.dumps(p) + "\n")
    with open(os.path.join(OUT, "corpus_v4_gold.jsonl"), "w") as fh:
        for g in gold_list:
            fh.write(json.dumps(g) + "\n")

    # ---- confrontations: every case against its declared agent and the 48 candidate agents ----
    gold_by_case = gold["idx"]
    confrontations = []
    for c in layerA + layerB:
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                        c["facet_requirements"], c["U_E"], c["R_c"], tuple(c["critical_pillars"]),
                        c["horizon"], c["conflict_pattern"], "system", tuple(c["norms"]))
        declared = Profile("AGENT-declared", c["declared_levels"], c["declared_confidence"], "system")
        candidates = [(declared, "declared")] + [(persona_profile(p, c["facet_requirements"]),
                                                  p["persona_type"]) for p in personas]
        for agent, persona_name in candidates:
            r = confront(spec, agent, CAL)
            if r is None or r.get("adequacy") is None:
                continue
            confrontations.append({
                "case_id": c["case_id"], "domain": c["domain"], "layer": c["layer"],
                "agent": agent.profile_id, "agent_layer": agent.layer,
                "persona": persona_name,
                "adequacy": r["adequacy"], "adequacy_low": r["adequacy_low"],
                "adequacy_high": r["adequacy_high"], "decision": r["decision"],
                "veto": r["veto"], "hard_veto": r["hard_veto"],
                "worst_facet": r["worst_facet"], "bar": r["bar"],
                "design_intent": c.get("design_intent"),
                "gold": gold_by_case[c["case_id"]]["consensus"],
            })
    with open(os.path.join(OUT, "corpus_v4_confrontations.jsonl"), "w") as fh:
        for x in confrontations:
            fh.write(json.dumps(x) + "\n")

    # ---- frozen split ----
    ids = [c["case_id"] for c in layerA]
    rng.shuffle(ids)
    split = {"train": ids[:840], "calibration": ids[840:1020], "test": ids[1020:1200],
             "seed": SEED, "note": "frozen at G5'; do not re-shuffle in later rounds"}
    with open(os.path.join(OUT, "corpus_v4_split.json"), "w") as fh:
        json.dump(split, fh, indent=2)

    # ---- coverage / degeneracy report ----
    facet_cases = Counter()
    for c in layerA:
        for f in FACETS:
            if f.criticality.get(c["domain"], 2) == 4:
                facet_cases[f.code] += 1
    decisions = Counter(x["decision"] for x in confrontations)
    perfect = sum(1 for x in confrontations if x["adequacy"] >= 0.999)
    boundary = sum(1 for x in confrontations if abs(x["adequacy"] - x["bar"]) <= 0.05)
    veto = sum(1 for x in confrontations if x["veto"])
    hard = sum(1 for x in confrontations if x["hard_veto"])
    aa1 = [x["adequacy"] for x in confrontations if x["layer"] == "A"]
    goldA = [x["gold"] for x in confrontations if x["layer"] == "A"]
    decA = [x["decision"] for x in confrontations if x["layer"] == "A"]
    intent_vs_gold = Counter((c["design_intent"], gold["idx"][c["case_id"]]["consensus"]) for c in layerA)
    diffs = np.abs([RANK_ORDER[g["consensus"]] - RANK_ORDER[c["design_intent"]] for c, g in
                    ((c, gold["idx"][c["case_id"]]) for c in layerA)])
    intent_agreement = float(np.mean(np.where(diffs == 0, 1.0, np.where(diffs == 1, 0.5, 0.0))))
    kabs = {"AB": cohens_kappa([g["panelA"] for g in gold_list], [g["panelB"] for g in gold_list]),
           "AC": cohens_kappa([g["panelA"] for g in gold_list], [g["panelC"] for g in gold_list]),
           "BC": cohens_kappa([g["panelB"] for g in gold_list], [g["panelC"] for g in gold_list])}
    spreads = [g["spread"] for g in gold_list]
    report = {
        "layerA_cases": len(layerA), "layerB_cases": len(layerB), "personas": len(personas),
        "confrontations": len(confrontations),
        "facet_critical_case_counts": dict(facet_cases),
        "facets_with_ge_5_critical_cases": sum(1 for f in FACETS if facet_cases.get(f.code, 0) >= 5),
        "domains": len(set(c["domain"] for c in layerA + layerB)),
        "conflict_patterns_per_domain": {d: len(set(c["conflict_pattern"] for c in layerA + layerB
                                                     if c["domain"] == d)) for d in DOMAINS},
        "decision_distribution": dict(decisions),
        "share_adequacy_1": perfect / max(1, len(confrontations)),
        "share_within_0.05_of_bar": boundary / max(1, len(confrontations)),
        "veto_rate": veto / max(1, len(confrontations)),
        "hard_veto_rate": hard / max(1, len(confrontations)),
        "mean_adequacy_layerA": float(np.mean(aa1)),
        "gold_rubric": {
            "kappa": {k: round(v, 4) for k, v in kabs.items()},
            "mean_pairwise_kappa": round(float(np.mean(list(kabs.values()))), 4),
            "unanimous_panel_share": round(float(np.mean(np.array(spreads) == 0)), 4),
            "mean_panel_spread": round(float(np.mean(spreads)), 4),
            "clear_case_share_spread_0": round(float(np.mean(np.array(spreads) == 0)), 4),
            "normatively_contested_share_spread_1": round(float(np.mean(np.array(spreads) >= 1)), 4),
            "design_intent_agreement": round(intent_agreement, 4),
            "consensus_distribution": dict(Counter(g["consensus"] for g in gold_list)),
        },
        "design_intent_matches_gold": {f"{k[0]} -> {k[1]}": v for k, v in intent_vs_gold.items()},
        "narrative_words": {"min": min(c["word_count"] for c in layerB),
                            "mean": float(np.mean([c["word_count"] for c in layerB])),
                            "max": max(c["word_count"] for c in layerB)},
    }
    with open(os.path.join(OUT, "corpus_v4_coverage.json"), "w") as fh:
        json.dump(report, fh, indent=2)

    # ---- human anchor worksheet (120 cases) ----
    anchors = []
    hard = [c for c in layerA + layerB if gold["idx"][c["case_id"]]["spread"] >= 1]
    easy = [c for c in layerA + layerB if gold["idx"][c["case_id"]]["spread"] == 0]
    rng.shuffle(hard); rng.shuffle(easy)
    pool = hard[:40] + easy[:20] + [c for c in layerB if c not in hard and c not in easy][:60]
    rng.shuffle(pool)
    pool = pool[:120]
    for c in pool:
        anchors.append({
            "case_id": c["case_id"], "domain": c["domain"], "severity": c["severity"],
            "irreversibility": c["irreversibility"], "horizon": c["horizon"],
            "conflict_pattern": c["conflict_pattern"], "norms": "; ".join(c["norms"]),
            "narrative_or_rationale": c.get("narrative") or c.get("design_rationale", ""),
            "declared_levels_summary": ", ".join(f"{k}={v:.2f}" for k, v in
                                                 sorted(c["declared_levels"].items())),
            "difficulty": "hard" if gold["idx"][c["case_id"]]["spread"] >= 1 else "clear",
            "rater1": "", "rater2": "", "rater3": "",
        })
    with open(os.path.join(OUT, "corpus_v4_human_anchor.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(anchors[0].keys()))
        w.writeheader()
        for a in anchors:
            w.writerow(a)

    print(json.dumps(report, indent=2)[:2000])
    print("written to", OUT)


if __name__ == "__main__":
    main()
