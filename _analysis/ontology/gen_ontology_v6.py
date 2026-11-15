#!/usr/bin/env python3
"""Regenerate Ontologias/ontology_v4 from Evaluacoes/r4/corpus_v7_* (33 facets, E30).

Decision D4.20/D4.21 moved the facet canon from 28 to 33 facets and added fact grounding
(E30): every procedural fact is an observation of the facet it names and caps the level
that facet may be credited,  ell_f = min(ell_f, q_f * c(fact)).

Emitted artefacts
  01_core.ttl .. 06_calibration.ttl        schema rebuilt from facet_registry.py (33 facets)
  07_grounding.ttl                         E30 vocabulary (FactGrounding, declared levels)
  shapes/ontology_shapes.ttl               the v4 shapes (facet count read from registry)
  shapes/ontology_shapes_v6.ttl           shapes for the E30 structure
  fixtures/instances.ttl                   all 1,520 cases, all 120 personas and
                                         the stratified sample of confrontations
                                         (decision D9) that SHACL and the mirror load
  fixtures/invalid_examples.ttl            the v4 fixtures
  fixtures/invalid_examples_v6.ttl         the E30 fixtures
  fixtures/invalid_examples.ttl            the v4 fixtures plus the E30 fixtures

Every derived number written into the graph is recomputed here with core.py from the very
literals that are written, so the RDF is internally consistent and the SPARQL mirror can
reproduce it to machine precision.

Run:  python3 _analysis/ontology/gen_ontology_v5.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_ontology_v4 as G  # noqa: E402

sys.path.insert(0, G.CORE_DIR)
from facet_registry import FACETS  # noqa: E402
from fact_grounding import FACT_MAP, fact_compliance, grounded_levels  # noqa: E402
from core import (CaseSpec, Profile, _adequacy, confront, case_stakes, review_need,  # noqa: E402
                  load_fitted_calibration, SEVERITY_VALUE, REVERSIBILITY,
                  PRUDENTIAL_VALUE, HORIZON_VALUE)

ROOT = G.ROOT
ONT = os.path.join(ROOT, "Ontologias", "ontology_v4_2")
ROUND = os.environ.get("ETH_WCMK_ROUND", "5")
R5 = os.path.join(ROOT, "Evaluacoes", "r" + ROUND)
VERSION = "4.2.0"
GROUND_STRENGTH = 1.0            # E30 as run for corpus_v7
SAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_selection.json")
SAMPLE = set(json.load(open(SAMPLE_PATH))["chosen"])   # stratified confrontation sample (D9)
PILLARS = ("W", "C", "M", "K")
CALIB_ID = "cal:ladder_fit_v12"
NFACETS = len(FACETS)

TRIPLES = {"instances": 0}

# Properties that only exist when the confrontation actually produced an adequacy
# estimate. A profile whose declared coverage is below the E26' gate abstains before
# any adequacy is computed, so the graph must not carry those literals for it.
_ADEQUACY_PROPS = {"eth:levelW", "eth:levelC", "eth:levelM", "eth:levelK",
                   "eth:requirementW", "eth:requirementC", "eth:requirementM", "eth:requirementK",
                   "eth:deficitW", "eth:deficitC", "eth:deficitM", "eth:deficitK",
                   "eth:guardedDeficitW", "eth:guardedDeficitC", "eth:guardedDeficitM",
                   "eth:guardedDeficitK", "eth:structuralTermS2", "eth:structuralTermS3",
                   "eth:structuralTermS4", "eth:slackS3minusS4", "eth:slackS2minusS3",
                   "eth:slackMaxDeficitMinusS2", "eth:weightedDeficit", "eth:epistemicPenalty",
                   "eth:facetExposurePhi", "eth:adequacyRaw", "eth:adequacy", "eth:adequacyLow",
                   "eth:adequacyHigh", "eth:adequacyBand", "eth:materialGapLow",
                   "eth:sigmaFloor", "eth:failureProbability", "eth:reliability", "eth:riskRatio",
                   "eth:residualRisk", "eth:riskAttenuation", "eth:harmScale", "eth:worstPillar",
                   "eth:worstFacet", "eth:crossPillarDuty", "eth:crossPillarDutyEdge",
                   "eth:crossPillarDutyFace", "eth:caseSalienceW", "eth:caseSalienceC",
                   "eth:caseSalienceM", "eth:caseSalienceK"}


def bnode_string(items):
    return ",\n    ".join("[ " + " ; ".join(it) + " ]" for it in items)


def emit_node(targets, iri, types, props):
    """targets: list of (buffer, counter_key). Counts triples exactly as they are written."""
    props = [(p, o) for p, o in props if o not in ("", None, [])]
    n = len(types)
    rendered = []
    for p, o in props:
        if isinstance(o, list):
            n += len(o) + sum(len(inner) for inner in o)   # one link per blank node
            rendered.append((p, bnode_string(o)))
        else:
            n += len(set(v.strip() for v in o.split(",")))   # rdflib collapses duplicates
            rendered.append((p, o))
    body = [f"{iri} a {', '.join(types)}"] + [f"  {p} {o}" for p, o in rendered]
    line = " ;\n".join(body) + " ."
    for buf, key in targets:
        buf.append(line)
        TRIPLES[key] += n


def emit_pred(targets, iri, pred, values):
    if not values:
        return
    line = f"{iri} {pred} " + " , ".join(values) + " ."
    for buf, key in targets:
        buf.append(line)
        TRIPLES[key] += len(values)


def emit_plain(targets, line, n):
    for buf, key in targets:
        buf.append(line)
        TRIPLES[key] += n


def grounding_nodes(cid, facts, requirements):
    nodes = []
    for fact, value in sorted(facts.items()):
        if fact not in FACT_MAP:
            continue
        code = FACT_MAP[fact][0]
        c = fact_compliance(fact, value)
        cap = requirements[code] * (1.0 - GROUND_STRENGTH * (1.0 - c))
        if fact == "remedy_days":
            val = str(int(value))
        elif isinstance(value, bool):
            val = "true" if value else "false"
        else:
            val = G.num(value)
        nodes.append(["a eth:FactGrounding",
                      f"eth:groundingId {G.q(cid + '/' + fact)}",
                      f"eth:factName {G.q(fact)}",
                      f"eth:factValue {val}",
                      f"eth:anchorsFacet fac:{code}",
                      f"eth:complianceValue {G.num(c)}",
                      f"eth:capValue {G.num(cap)}",
                      f"eth:groundingStrength {G.num(GROUND_STRENGTH)}"])
    return nodes


def load_corpus():
    cases = []
    for name in ("corpus_v7_layerA.jsonl", "corpus_v7_layerB.jsonl"):
        with open(os.path.join(R5, name)) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    cases.append(json.loads(line))
    with open(os.path.join(R5, "corpus_v7_personas.jsonl")) as fh:
        personas = [json.loads(l) for l in fh if l.strip()]
    return cases, personas


def emit_instances(cases, personas, conflicts):
    cal = load_fitted_calibration()
    cidx = G.conflict_index(conflicts)
    codes = [f.code for f in FACETS]
    stats = {"cases": 0, "profiles": 0, "confrontations": 0,
             "chains": 0, "agents": 0, "stakeholders": 0, "consequences": 0,
             "evidence": 0, "vulnerabilities": 0, "requirements": 0,
             "observations": 0, "grounded_facts": 0, "guard_failure_records": 0}
    decisions = {}
    full_buf = [G.head("fixtures/instances.ttl - corpus_v7 instantiated per decision D9: "
                       f"all {len(cases)} cases and their E30 grounding facts, all "
                       f"{len(personas)} personas, and a stratified sample of {len(SAMPLE)} "
                       f"of the {len(cases) * (len(personas) + 1)} confrontations "
                       "(see _analysis/ontology/select_sample.py)")]
    ONE = [(full_buf, "instances")]
    fh_full = open(os.path.join(ONT, "fixtures", "instances.ttl"), "w")

    def flush():
        if full_buf:
            fh_full.write("\n".join(full_buf) + "\n")
            full_buf.clear()

    for p in personas:
        pid = p["profile_id"].replace("-", "_")
        fac = p["factors"]
        emit_node(ONE, "ag:persona_" + pid, ["eth:Agent"],
                  [("rdfs:label", G.q(p["persona_type"])),
                   ("eth:agentId", G.q(p["profile_id"])),
                   ("eth:personaType", G.q(p["persona_type"])),
                   ("eth:agentLayer", "eth:Layer_" + p["layer"]),
                   ("eth:attainmentFactorW", G.num(fac.get("W", 1.0))),
                   ("eth:attainmentFactorC", G.num(fac.get("C", 1.0))),
                   ("eth:attainmentFactorM", G.num(fac.get("M", 1.0))),
                   ("eth:attainmentFactorK", G.num(fac.get("K", 1.0))),
                   ("eth:jitter", G.num(p["jitter"])),
                   ("eth:confidenceMean", G.num(p["confidence_mu"])),
                   ("eth:fallbackPolicy", "eth:Fallback_human_review")])
        stats["agents"] += 1

    first_by_layer = {}
    for p in personas:
        first_by_layer.setdefault(p["layer"], p["profile_id"])

    fh_rows = open(os.path.join(R5, "corpus_v7_confrontations.jsonl"))
    row_total = 0
    for case in cases:
        cid = case["case_id"]
        pattern = case["conflict_pattern"]
        attached = cidx.get((case["domain"], pattern), []) if pattern != "none" else []
        status = "none"
        if attached:
            status = ("unresolved" if any(a[7] == "unresolved_escalation" for a in attached)
                     else "resolved_by_priority")
        evidence_conflict = bool(case.get("ambiguous", False))
        stakeholders, consequence, evidence, vulnerability, review_body, prior, objective, \
            resources, mitigation = G.parse_narrative(case)
        exposure = min(1.0, len(set(stakeholders)) / 4.0) if stakeholders else 0.5
        norms = G.norm_ids_of_instruments(case["norms"])
        obligations = [n for n in norms if G.kind_of(n) == "Obligation"]
        prohibitions = [n for n in norms if G.kind_of(n) == "Prohibition"]
        permissions = [n for n in norms if G.kind_of(n) == "Permission"]
        props = [("eth:caseId", G.q(cid)),
                 ("eth:corpusLayer", G.q(case["layer"])),
                 ("eth:scenario", G.q(case["scenario"])),
                 ("eth:archetype", G.q(case["archetype"])),
                 ("eth:designIntent", "eth:Decision_" + case["design_intent"]),
                 ("eth:domain", "eth:domain_" + case["domain"]),
                 ("eth:severity", "eth:Severity_" + case["severity"]),
                 ("eth:prudentialMode", "eth:Prudential_" + case["prudential"]),
                 ("eth:reversibility", "eth:Reversibility_" + case["irreversibility"]),
                 ("eth:horizon", "eth:Horizon_" + case["horizon"]),
                 ("eth:oversightRegime", "eth:Oversight_" + case.get("oversight", "unspecified")),
                 ("eth:conflictPattern", "eth:Pattern_" + pattern),
                 ("eth:agentLayer", "eth:Layer_system"),
                 ("eth:epistemicUncertainty", G.num(case["U_E"])),
                 ("eth:consequenceMass", G.num(case["R_c"])),
                 ("eth:exposureScale", G.num(exposure)),
                 ("eth:criticalPillar", ", ".join("eth:pillar_" + p
                                                 for p in dict.fromkeys(case["critical_pillars"]))),
                 ("eth:criticalPillarDeclaredCount", str(len(case["critical_pillars"]))),
                 ("eth:normConflictStatus", G.q(status)),
                 ("eth:evidenceConflict", G.num(evidence_conflict)),
                 ("eth:hasNorm", ", ".join("norm:" + n for n in norms)),
                 ("eth:hasObligation", ", ".join("norm:" + n for n in obligations)),
                 ("eth:hasProhibition", ", ".join("norm:" + n for n in prohibitions)),
                 ("eth:hasPermission", ", ".join("norm:" + n for n in permissions)),
                 ("eth:hasNormConflict", ", ".join("norm:conflict_%03d" % a[0] for a in attached)),
                 ("eth:caseResolutionStrategy", ", ".join("eth:" + a[3] for a in attached)),
                 ("eth:hasReviewBody", G.q(review_body or "no standing review body")),
                 ("eth:declaredProfile", "cse:PROF_" + cid + "_declared")]
        if prior:
            props += [("eth:priorRecord", G.q(prior)), ("eth:declaredObjective", G.q(objective)),
                      ("eth:operationalConstraint", G.q(resources)),
                      ("eth:mitigationInPlace", G.q(mitigation))]
        if consequence:
            props.append(("eth:hasConsequence", "cse:cons_" + cid))
        if stakeholders:
            props.append(("eth:hasStakeholder",
                          ", ".join(f"ag:sh_{cid}_{j}" for j in range(len(stakeholders)))))
        if evidence:
            props.append(("eth:hasEvidence", ", ".join(f"ag:ev_{cid}_{j}" for j in range(len(evidence)))))
        if vulnerability:
            kind = "structural"
            for k in ("structural", "procedural", "epistemic", "cognitive", "dependency"):
                if k in vulnerability:
                    kind = k
                    break
            props.append(("eth:hasVulnerability", "ag:vuln_" + cid))
            emit_node(ONE, "ag:vuln_" + cid, ["eth:Vulnerability"],
                      [("rdfs:label", G.q(vulnerability)),
                       ("eth:vulnerabilityText", G.q(vulnerability)),
                       ("eth:vulnerabilityKind", G.q(kind))])
            stats["vulnerabilities"] += 1
        props.append(("eth:hasRequirement",
                      [["a eth:FacetRequirement",
                        f"eth:requirementFacet fac:{f}",
                        f"eth:requirementValue {G.num(case['facet_requirements'][f])}"]
                       for f in codes]))
        facts = grounding_nodes(cid, case["facts"], case["facet_requirements"])
        props.append(("eth:groundedByFact", facts))
        emit_node(ONE, "cse:" + cid, ["eth:EthicalCase"], props)
        stats["cases"] += 1
        stats["requirements"] += NFACETS
        stats["grounded_facts"] += len(facts)
        for j, name in enumerate(stakeholders):
            emit_node(ONE, f"ag:sh_{cid}_{j}", ["eth:Stakeholder"],
                      [("rdfs:label", G.q(name)), ("eth:stakeholderName", G.q(name)),
                       ("eth:consentGiven", "false"), ("eth:affectedCount", str(j + 1))])
            stats["stakeholders"] += 1
        if consequence:
            emit_node(ONE, "cse:cons_" + cid, ["eth:Consequence"],
                      [("rdfs:label", G.q(consequence)), ("eth:consequenceText", G.q(consequence)),
                       ("eth:consequenceIrreversibility", G.q(case["irreversibility"])),
                       ("eth:consequenceHorizon", G.q(case["horizon"]))])
            stats["consequences"] += 1
        for j, (text, st) in enumerate(evidence):
            emit_node(ONE, f"ag:ev_{cid}_{j}", ["eth:Evidence"],
                      [("rdfs:label", G.q(text)), ("eth:evidenceText", G.q(text)),
                       ("eth:evidenceStatus", G.q(st))])
            stats["evidence"] += 1

        spec = CaseSpec(cid, case["domain"], case["severity"], case["prudential"],
                        case["irreversibility"], case["facet_requirements"], case["U_E"],
                        case["R_c"], tuple(case["critical_pillars"]), case["horizon"],
                        case["conflict_pattern"], "system", tuple(case["norms"]),
                        norm_conflict=status, evidence_conflict=evidence_conflict,
                        exposure=exposure,
                        oversight=case.get("oversight", "unspecified"))

        # The declared agent's own profile is read from the corpus row that instantiates it,
        # so that the Profile individual and the Confrontation that references it carry
        # exactly the same levels (defect fixed in v4.1: the two were emitted separately and
        # diverged in the 5th decimal).
        rows = [json.loads(fh_rows.readline()) for _ in range(len(personas) + 1)]
        decl = next((r for r in rows if r["persona"] == "AGENT-declared"), None)
        if decl is not None:
            d_levels = {c: v for c, v in zip(codes, decl["facet_levels"]) if v is not None}
            d_conf = {c: v for c, v in zip(codes, decl["facet_confidence"]) if v is not None}
        else:
            d_levels, _ = grounded_levels(case["facts"], case["facet_requirements"],
                                         dict(case["declared_levels"]), GROUND_STRENGTH)
            d_conf = dict(case["declared_confidence"])
        emit_node(ONE, "cse:PROF_" + cid + "_declared", ["eth:Profile"],
                  [("rdfs:label", G.q("declared profile of " + cid)),
                   ("eth:profileId", G.q("DECLARED-" + cid)),
                   ("eth:layerOfProfile", "eth:Layer_system"),
                   ("eth:coverage", "1.0"),
                   ("eth:basedOnAgent", "ag:agent_" + cid),
                   ("eth:hasObservation", [["a eth:FacetObservation", f"eth:observedFacet fac:{f}",
                                            f"eth:observedValue {G.num(d_levels[f])}",
                                            f"eth:observationConfidence {G.num(d_conf[f])}"]
                                           for f in codes])])
        emit_node(ONE, "ag:agent_" + cid, ["eth:Agent"],
                  [("rdfs:label", G.q("declared agent " + cid)),
                   ("eth:agentId", G.q("AGENT-" + cid)),
                   ("eth:personaType", G.q("declared")),
                   ("eth:agentLayer", "eth:Layer_system"),
                   ("eth:attainmentFactorW", "1.0"), ("eth:attainmentFactorC", "1.0"),
                   ("eth:attainmentFactorM", "1.0"), ("eth:attainmentFactorK", "1.0"),
                   ("eth:jitter", "0.0"),
                   ("eth:confidenceMean", G.num(sum(d_conf.values()) / len(d_conf))),
                   ("eth:fallbackPolicy", "eth:Fallback_human_review")])
        stats["profiles"] += 1
        stats["observations"] += NFACETS
        stats["agents"] += 1

        profiles = {}
        for row in rows:
            row_total += 1
            decisions[row["decision"]] = decisions.get(row["decision"], 0) + 1
            tag = row["persona"].replace("-", "_")
            conf_id = f"CONF_{cid}_{tag}"
            if conf_id not in SAMPLE:
                continue
            declared_row = row["persona"] == "AGENT-declared"
            iri = "cse:PROF_" + cid + ("_declared" if declared_row else "_" + tag)
            agent_iri = "ag:agent_" + cid if declared_row else "ag:persona_" + tag
            levels = {c: v for c, v in zip(codes, row["facet_levels"]) if v is not None}
            conf = {c: v for c, v in zip(codes, row["facet_confidence"]) if v is not None}
            prof = Profile(row["persona"] + "-" + cid, levels, conf, row["agent_layer"])
            profiles[iri] = prof
            targets = ONE
            obs = [["a eth:FacetObservation", f"eth:observedFacet fac:{f}",
                    f"eth:observedValue {G.num(levels[f])}",
                    f"eth:observationConfidence {G.num(conf[f])}"] for f in codes if f in levels]
            if not declared_row:
                emit_node(targets, iri, ["eth:Profile"],
                          [("rdfs:label", G.q(row["persona_type"] + " profile of " + cid)),
                           ("eth:profileId", G.q(row["persona"] + "-" + cid)),
                           ("eth:layerOfProfile", "eth:Layer_" + row["agent_layer"]),
                           ("eth:coverage", "1.0"),
                           ("eth:basedOnAgent", agent_iri),
                           ("eth:hasObservation", obs)])
                stats["profiles"] += 1
                stats["observations"] += NFACETS

            mid = _adequacy(spec, prof, cal, FACETS, "central")
            low = _adequacy(spec, prof, cal, FACETS, "pessimistic")
            high = _adequacy(spec, prof, cal, FACETS, "optimistic")
            ref = confront(spec, prof, cal, FACETS)
            verdict = ref["decision"]
            d = mid["deficits"]
            worst = max(range(4), key=lambda i: mid["lam_case"][i] * d[i])
            facet_deficits = sorted(((f.code, max(0.0, spec.facet_requirements.get(f.code, 0.0)
                                                  - prof.facet_scores.get(f.code, 0.0)))
                                     for f in FACETS), key=lambda x: -x[1])
            conf_id = f"CONF_{cid}_{tag}"
            derived = [(f"eth:level{PILLARS[i]}", G.num(mid["levels"][i])) for i in range(4)]
            derived += [(f"eth:requirement{PILLARS[i]}", G.num(mid["requirements"][i]))
                        for i in range(4)]
            derived += [(f"eth:deficit{PILLARS[i]}", G.num(d[i])) for i in range(4)]
            derived += [(f"eth:guardedDeficit{PILLARS[i]}", G.num(mid["guarded_deficits"][i]))
                        for i in range(4)]
            derived += [("eth:structuralTermS2", G.num(mid["S2"])),
                        ("eth:structuralTermS3", G.num(mid["S3"])),
                        ("eth:structuralTermS4", G.num(mid["S4"])),
                        ("eth:slackS3minusS4", G.num(mid["S3"] - mid["S4"])),
                        ("eth:slackS2minusS3", G.num(mid["S2"] - mid["S3"])),
                        ("eth:slackMaxDeficitMinusS2", G.num(max(d) - mid["S2"])),
                        ("eth:weightedDeficit", G.num(mid["D"])),
                        ("eth:epistemicPenalty", G.num(mid["u"])),
                        ("eth:facetExposurePhi", G.num(mid["phi"])),
                        ("eth:adequacyRaw", G.num(mid["aa_raw"])),
                        ("eth:adequacy", G.num(mid["aa"])),
                        ("eth:adequacyLow", G.num(low["aa"])),
                        ("eth:adequacyHigh", G.num(high["aa"])),
                        ("eth:adequacyBand", G.num(high["aa"] - low["aa"])),
                        ("eth:materialGapLow", G.num(low["material_gap"])),
                        ("eth:decision", "eth:Decision_" + verdict),
                        ("eth:decisionBar", G.num(cal.decision_bar(spec))),
                        ("eth:declaredStakesSum", G.num(SEVERITY_VALUE[spec.severity]
                                                       + REVERSIBILITY[spec.irreversibility]
                                                       + PRUDENTIAL_VALUE[spec.prudential])),
                        ("eth:stakesWeighted", G.num(case_stakes(spec))),
                        ("eth:sigmaFloor", G.num(low["sigma"])),
                        ("eth:failureProbability", G.num(low["p_fail"])),
                        ("eth:reliability", G.num(1 - low["p_fail"])),
                        ("eth:riskRatio", G.num(low["ratio"])),
                        ("eth:residualRisk", G.num(low["R_r"])),
                        ("eth:riskAttenuation", G.num(spec.R_c - low["R_r"])),
                        ("eth:harmScale", G.num(low["harm"])),
                        ("eth:coverage", G.num(prof.completeness())),
                        ("eth:reviewNeed", G.num(review_need(low["aa"], high["aa"], cal.decision_bar(spec),
                                       low["u"], prof.completeness(), cal))),  # full precision, like every other literal
                        ("eth:crossPillarDuty", G.num(mid["psi"])),
                        ("eth:crossPillarDutyEdge", G.num(mid["psi_edge"])),
                        ("eth:crossPillarDutyFace", G.num(mid["psi_face"])),
                        ("eth:caseSalienceW", G.num(mid["lam_case"][0])),
                        ("eth:caseSalienceC", G.num(mid["lam_case"][1])),
                        ("eth:caseSalienceM", G.num(mid["lam_case"][2])),
                        ("eth:caseSalienceK", G.num(mid["lam_case"][3])),
                        ("eth:guardFailureCount", str(len(mid["guard_failures"]))),
                        ("eth:worstPillar", "eth:pillar_" + PILLARS[worst]),
                        ("eth:worstFacet", "fac:" + facet_deficits[0][0]),
                        ("eth:epistemicAbstention", G.num(bool(ref["epistemic_abstention"]))),
                        ("eth:groundingStrength", G.num(GROUND_STRENGTH))]
            if low["material_facet"]:
                derived.append(("eth:materialFacet", "fac:" + low["material_facet"]))
            if low["veto"]:
                derived.append(("eth:vetoPillar", ", ".join("eth:pillar_" + PILLARS[i]
                                                           for i in low["veto"])))
            if low["hard_veto"]:
                derived.append(("eth:hardVetoPillar", ", ".join("eth:pillar_" + PILLARS[i]
                                                               for i in low["hard_veto"])))
            if mid["guard_failures"]:
                derived.append(("eth:hasGuardFailure",
                                [["a eth:GuardFailure",
                                  f"eth:guardFacet fac:{g['facet']}",
                                  f"eth:guardPillar eth:pillar_{g['pillar']}",
                                  f"eth:observedAtGuard {G.num(g['observed'])}",
                                  f"eth:guardFloor {G.num(g['guard'])}",
                                  f"eth:guardPolicy eth:Policy_{g['policy']}"]
                                 for g in mid["guard_failures"]]))
                stats["guard_failure_records"] += len(mid["guard_failures"])
            if ref.get("adequacy") is None:          # E26': the profile is not auditable
                derived = [t for t in derived if t[0] not in _ADEQUACY_PROPS]
                stats.setdefault("coverage_abstentions", 0)
                stats["coverage_abstentions"] += 1
            emit_node(targets, "cse:" + conf_id, ["eth:Confrontation"],
                      [("rdfs:label", G.q("confrontation " + cid + " x " + row["persona"])),
                       ("eth:confrontationId", G.q(conf_id)),
                      ("eth:confrontationCase", "cse:" + cid),
                      ("eth:confrontationProfile", iri),
                      ("eth:appliedCalibration", CALIB_ID),
                      ("eth:agentLayer", "eth:Layer_" + row["agent_layer"]),
                      ("eth:personaType", G.q(row["persona_type"]))] + derived)
            stats["confrontations"] += 1
            if row_total % 2000 == 0:
                flush()

        # layered agency chain for the case
        order = ("model", "system", "operator")
        per_layer = []
        # the corpus already stores the per-layer evaluation; the persona profiles are
        # only instantiated for the sampled confrontations
        by_persona = {r["persona"]: r for r in rows}
        for layer in order:
            r = by_persona[first_by_layer[layer]]
            per_layer.append({"layer": layer, "decision": r["decision"],
                             "adequacy_low": r["adequacy_low"], "R_r": r["R_r"],
                             "abstention": bool(r["epistemic_abstention"])})
        weakest = min(per_layer, key=lambda x: round(x["adequacy_low"], 4))
        emit_node(ONE, "cse:CHAIN_" + cid, ["eth:ConfrontationChain"],
                  [("rdfs:label", G.q("layered agency of " + cid)),
                   ("eth:chainCase", "cse:" + cid),
                   ("eth:weakestLinkLayer", "eth:Layer_" + weakest["layer"]),
                   ("eth:chainDecision", "eth:Decision_" + weakest["decision"]),
                   ("eth:chainAdequacyLow", G.num(weakest["adequacy_low"])),
                   ("eth:chainResidualRisk", G.num(max(x["R_r"] for x in per_layer))),
                   ("eth:chainEpistemicAbstention", G.num(all(x["abstention"] for x in per_layer))),
                   ("eth:fallbackForChain", "eth:Fallback_human_review"),
                   ("eth:delegationChain", "ag:chain_" + cid + "_d3"),
                   ("eth:layerResult", [["a eth:ChainLayerResult",
                                        "eth:resultLayer eth:Layer_" + x["layer"],
                                        f"eth:resultAdequacyLow {G.num(x['adequacy_low'])}",
                                        "eth:resultDecision eth:Decision_" + x["decision"],
                                        f"eth:resultResidualRisk {G.num(x['R_r'])}"]
                                       for x in per_layer])])
        pillars = list(dict.fromkeys(spec.critical_pillars))
        sys_a, mod_a, comp_a = (f"ag:agent_sys_{cid}", f"ag:agent_mod_{cid}", f"ag:agent_comp_{cid}")
        # the declared agent (ag:agent_<cid>) was emitted with the case; here we add the
        # three institutional layers it delegates to
        for iri, layer, forbidden in ((sys_a, "system", ()),
                                      (mod_a, "model", ("M", "W")),
                                      (comp_a, "model", ("M", "W"))):
            agent_props = [("rdfs:label", G.q(iri.split(":")[1])),
                           ("eth:agentId", G.q(iri.split(":")[1])),
                           ("eth:personaType", G.q("institutional")),
                           ("eth:agentLayer", "eth:Layer_" + layer),
                           ("eth:attainmentFactorW", "1.0"), ("eth:attainmentFactorC", "1.0"),
                           ("eth:attainmentFactorM", "1.0"), ("eth:attainmentFactorK", "1.0"),
                           ("eth:jitter", "0.0"), ("eth:confidenceMean", "0.90"),
                           ("eth:fallbackPolicy", "eth:Fallback_human_review")]
            agent_props += [("eth:forbiddenPillar", "eth:pillar_" + p) for p in forbidden]
            emit_node(ONE, iri, ["eth:Agent"], agent_props)
            stats["agents"] += 1
        for depth, (a, b) in enumerate(((f"ag:agent_{cid}", sys_a), (sys_a, mod_a),
                                        (mod_a, comp_a)), start=1):
            # E28: a layer can only carry the pillars it is not forbidden to carry. The
            # operational set is therefore the pillars the delegate is entitled to exercise;
            # the critical duty of the case is delegated only when it lies inside that set.
            # (v4.1 defect fixed: the previous rule emitted an empty delegated set whenever
            # the critical pillars were all non-delegable, which made the link a dangling
            # delegation and violated the ChainLink shape.)
            carried = ("W", "C", "M", "K") if depth == 1 else ("C", "K")
            delegated = [p for p in pillars if p in carried]
            emit_node(ONE, f"cse:link_{cid}_{depth}", ["eth:ChainLink"],
                      [("eth:delegatingAgent", a), ("eth:delegateAgent", b),
                       ("eth:delegatedPillar", ", ".join("eth:pillar_" + p for p in carried)),
                       ("eth:criticalDutyDelegated", "true" if delegated else "false"),
                       ("eth:retainedPillar", ", ".join("eth:pillar_" + p for p in pillars
                                                        if p not in carried)
                        if any(p not in carried for p in pillars) else ""),
                       ("eth:delegationConsistent", "true")])
        for line in (f"ag:agent_{cid} eth:delegatesTo {sys_a} .",
                     f"{sys_a} eth:delegatesTo {mod_a} .",
                     f"{mod_a} eth:delegatesTo {comp_a} ."):
            emit_plain(ONE, line, 1)
        for depth in (1, 2, 3):
            links = ", ".join(f"cse:link_{cid}_{k}" for k in range(1, depth + 1))
            emit_node(ONE, f"ag:chain_{cid}_d{depth}", ["eth:DelegationChain"],
                      [("rdfs:label", G.q("delegation chain depth " + str(depth) + " for " + cid)),
                       ("eth:delegationChainOf", "cse:" + cid),
                       ("eth:chainRoot", "ag:agent_" + cid),
                       ("eth:fallbackForChain", "eth:Fallback_escalate_prohibited"),
                       ("eth:chainLink", links)])
        for line in (f"ag:chain_{cid}_d1 eth:chainPrefixOf ag:chain_{cid}_d2 .",
                     f"ag:chain_{cid}_d2 eth:chainPrefixOf ag:chain_{cid}_d3 .",
                     f"ag:chain_{cid}_d1 eth:chainPrefixOf ag:chain_{cid}_d3 ."):
            emit_plain(ONE, line, 1)
        stats["chains"] += 1
        flush()

    fh_rows.close()
    flush()
    fh_full.close()

    return stats, decisions


GROUNDING_TTL = """
# 07_grounding.ttl - E30: fact grounding of declared facet levels.
# Every procedural fact carried by a case is an observation of the facet it names and caps
# the level that facet can be credited:  ell_f = min(ell_f, q_f * c(fact)).
"""


def emit_grounding_module():
    out = [G.head("07_grounding - the E30 vocabulary (FactGrounding, declared levels)")]
    out.append(G.prop("groundedByFact", "object", "EthicalCase", "FactGrounding",
                      "a verifiable fact of the case, anchored to a facet"))
    out.append(G.prop("groundingId", "data", "FactGrounding", "string", "case/fact identifier"))
    out.append(G.prop("factName", "data", "FactGrounding", "string",
                      "the fact as recorded in the corpus"))
    out.append(G.prop("factValue", "data", "FactGrounding", "xsd:double",
                      "the value of the fact (boolean or number)"))
    out.append(G.prop("anchorsFacet", "object", "FactGrounding", "Facet",
                      "the facet this fact is evidence about"))
    out.append(G.prop("complianceValue", "data", "FactGrounding", "xsd:double",
                      "compliance factor c(fact) in [0,1]"))
    out.append(G.prop("capValue", "data", "FactGrounding", "xsd:double",
                      "q_f * c(fact): the ceiling E30 puts on the declared level"))
    out.append(G.prop("groundingStrength", "data", "FactGrounding", "xsd:double",
                      "E30 sensitivity knob; 1.0 applies the declared compliance factors"))
    out.append(G.pcls("FactGrounding", "a verifiable fact anchoring a facet", "Entity"))
    out.append(G.prop("declaredLevelOf", "data", "Confrontation", "Facet",
                      "the level the confronting profile reports for a facet, after E30"))
    out.append(G.prop("declaredConfidenceOf", "data", "Confrontation", "Facet",
                      "the confidence the profile attaches to that level"))
    out.append(G.prop("requirementOf", "data", "EthicalCase", "Facet",
                      "the canonical requirement q_f of a facet for this case"))
    out.append(f"eth:rule_fact_grounding a eth:Rule ; rdfs:label \"E30 fact grounding\" ; "
              f"eth:appliesToClass eth:FactGrounding ; "
              f"eth:ruleStatement \"every declared level is capped by min(level, q_f * c(fact))\" .")
    return "\n".join(out) + "\n"


def emit_extra_shapes():
    n = NFACETS
    lines = [G.head("shapes/ontology_shapes_v6.ttl - v4.2 shapes: E30 fact grounding, the case's "
                    "grounded facts, the prudential values a confrontation must carry, E11c' "
                    "oversight (D5.4), E32 ReviewNeed (D5.6) and the E26' coverage gate (D5.8)")]
    lines.append(f"""
sh:GroundedFactShape a sh:NodeShape ; sh:targetClass eth:FactGrounding ;
  sh:property [ sh:path eth:factName ; sh:minCount 1 ; sh:maxCount 1 ] ;
  sh:property [ sh:path eth:anchorsFacet ; sh:minCount 1 ; sh:maxCount 1 ; sh:class eth:Facet ] ;
  sh:property [ sh:path eth:complianceValue ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:capValue ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:groundingStrength ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] .

sh:GroundingCaseShape a sh:NodeShape ; sh:targetClass eth:EthicalCase ;
  sh:property [ sh:path eth:groundedByFact ; sh:minCount 1 ; sh:maxCount 40 ] .

sh:ConfrontationGroundingShape a sh:NodeShape ; sh:targetClass eth:Confrontation ;
  sh:property [ sh:path eth:groundingStrength ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:adequacyLow ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:materialGapLow ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:structuralTermS2 ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:structuralTermS3 ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:structuralTermS4 ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:vetoPillar ; sh:maxCount 4 ] ;
  sh:property [ sh:path eth:hardVetoPillar ; sh:maxCount 4 ] ;
  sh:property [ sh:path eth:epistemicAbstention ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:boolean ] .

sh:OversightCaseShape a sh:NodeShape ; sh:targetClass eth:EthicalCase ;
  sh:property [ sh:path eth:oversightRegime ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:in (eth:Oversight_unspecified eth:Oversight_none eth:Oversight_out_of_loop
                       eth:Oversight_on_the_loop eth:Oversight_in_the_loop) ] .

sh:ReviewNeedShape a sh:NodeShape ; sh:targetClass eth:Confrontation ;
  sh:property [ sh:path eth:reviewNeed ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:crossPillarDuty ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:coverage ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] .

sh:SalienceShape a sh:NodeShape ; sh:targetClass eth:Confrontation ;
  sh:property [ sh:path eth:caseSalienceW ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:caseSalienceC ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:caseSalienceM ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:caseSalienceK ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] .

eth:rule_verification_gap a eth:Rule ; rdfs:label "E26' verification gap (D5.8)" ;
  eth:appliesToClass eth:Profile ;
  eth:ruleStatement "a profile declaring fewer than 70% of the canon duties is not auditable: the case decision is ABSTAIN and the rubric defers (V1_verification_gap)" .

sh:GroundedObservationShape a sh:NodeShape ; sh:targetClass eth:FacetObservation ;
  sh:property [ sh:path eth:observedValue ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.0"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] ;
  sh:property [ sh:path eth:observationConfidence ; sh:minCount 1 ; sh:maxCount 1 ;
                sh:datatype xsd:double ; sh:minInclusive "0.30"^^xsd:double ; sh:maxInclusive "1.0"^^xsd:double ] .""")
    return "\n".join(lines) + "\n"


def emit_e30_fixtures():
    """Deliberately broken E30 individuals; each trips exactly one v6 shape."""
    ok_conf = ('eth:adequacyLow "0.60"^^xsd:double ; eth:materialGapLow "0.30"^^xsd:double ; '
               'eth:structuralTermS2 "0.10"^^xsd:double ; eth:structuralTermS3 "0.10"^^xsd:double ; '
               'eth:structuralTermS4 "0.10"^^xsd:double ; '
               'eth:epistemicAbstention false')
    lines = [G.head("fixtures/invalid_examples_v6.ttl - broken fact-grounding individuals (E30), "
                    "each attributable to exactly one shape")]
    expectations = [
        ("cse:bad_fact_compliance_above_one", "sh:GroundedFactShape",
         "compliance factor above 1"),
        ("cse:bad_fact_no_facet", "sh:GroundedFactShape", "fact anchored to no facet"),
        ("cse:bad_fact_no_compliance", "sh:GroundedFactShape", "fact with no compliance value"),
        ("cse:bad_fact_no_strength", "sh:GroundedFactShape", "fact with no E30 strength"),
        ("cse:bad_fact_negative_cap", "sh:GroundedFactShape", "negative grounding cap"),
        ("cse:bad_case_no_grounding", "sh:GroundingCaseShape", "case with no grounded facts"),
        ("cse:bad_conf_no_grounding_strength", "sh:ConfrontationGroundingShape",
         "confrontation without an E30 grounding strength"),
        ("cse:bad_conf_grounding_above_one", "sh:ConfrontationGroundingShape",
         "grounding strength above 1"),
        ("cse:bad_conf_negative_material_gap", "sh:ConfrontationGroundingShape",
         "negative material gap in the pessimistic mode"),
        ("cse:bad_conf_two_strengths", "sh:ConfrontationGroundingShape",
         "two grounding strengths for one confrontation"),
        ("cse:bad_observation_low_confidence", "sh:GroundedObservationShape",
         "facet observation with confidence below 0.30"),
        ("cse:bad_observation_level_above_one", "sh:GroundedObservationShape",
         "facet observation with a level above 1"),
        ("cse:bad_conf_abstention_not_boolean", "sh:ConfrontationGroundingShape",
         "E29 abstention flag emitted as a string instead of a boolean"),
    ]
    lines.append(f"""
cse:bad_fact_compliance_above_one a eth:FactGrounding ;
  eth:groundingId "BAD-E30-1" ; eth:factName "independent_audit" ;
  eth:factValue true ; eth:anchorsFacet fac:M6 ;
  eth:complianceValue "1.40"^^xsd:double ; eth:capValue "0.80"^^xsd:double ;
  eth:groundingStrength "1.0"^^xsd:double .

cse:bad_fact_no_facet a eth:FactGrounding ;
  eth:groundingId "BAD-E30-2" ; eth:factName "notice_given" ;
  eth:factValue false ; eth:complianceValue "0.30"^^xsd:double ;
  eth:capValue "0.20"^^xsd:double ; eth:groundingStrength "1.0"^^xsd:double .

cse:bad_fact_no_compliance a eth:FactGrounding ;
  eth:groundingId "BAD-E30-3" ; eth:factName "logs_available" ;
  eth:factValue false ; eth:anchorsFacet fac:M6 ;
  eth:capValue "0.40"^^xsd:double ; eth:groundingStrength "1.0"^^xsd:double .

cse:bad_fact_no_strength a eth:FactGrounding ;
  eth:groundingId "BAD-E30-4" ; eth:factName "appeal_channel" ;
  eth:factValue true ; eth:anchorsFacet fac:M9 ;
  eth:complianceValue "1.00"^^xsd:double ; eth:capValue "0.90"^^xsd:double .

cse:bad_fact_negative_cap a eth:FactGrounding ;
  eth:groundingId "BAD-E30-5" ; eth:factName "containment_exercised" ;
  eth:factValue false ; eth:anchorsFacet fac:C7 ;
  eth:complianceValue "0.30"^^xsd:double ; eth:capValue "-0.20"^^xsd:double ;
  eth:groundingStrength "1.0"^^xsd:double .

cse:bad_case_no_grounding a eth:EthicalCase ;
  eth:caseId "BAD-E30-CASE" ; eth:scenario "a deployment with no verifiable facts" ;
  eth:domain eth:domain_TS ; eth:severity eth:Severity_high .

cse:bad_conf_no_grounding_strength a eth:Confrontation ;
  eth:confrontationId "BAD-E30-CONF-1" ; eth:confrontationCase cse:bad_case_ok ;
  eth:confrontationProfile cse:bad_profile_001 ; eth:appliedCalibration cal:ladder_fit_v12 ;
  eth:agentLayer eth:Layer_model ;
  {ok_conf} ; eth:decision eth:Decision_ALLOW ; eth:adequacy "0.70"^^xsd:double .

cse:bad_conf_grounding_above_one a eth:Confrontation ;
  eth:confrontationId "BAD-E30-CONF-2" ; eth:confrontationCase cse:bad_case_ok ;
  eth:confrontationProfile cse:bad_profile_001 ; eth:appliedCalibration cal:ladder_fit_v12 ;
  eth:agentLayer eth:Layer_model ; eth:groundingStrength "1.50"^^xsd:double ;
  {ok_conf} ; eth:decision eth:Decision_ALLOW ; eth:adequacy "0.70"^^xsd:double .

cse:bad_conf_negative_material_gap a eth:Confrontation ;
  eth:confrontationId "BAD-E30-CONF-3" ; eth:confrontationCase cse:bad_case_ok ;
  eth:confrontationProfile cse:bad_profile_001 ; eth:appliedCalibration cal:ladder_fit_v12 ;
  eth:agentLayer eth:Layer_model ; eth:groundingStrength "1.0"^^xsd:double ;
  eth:adequacyLow "-0.10"^^xsd:double ; eth:materialGapLow "-0.30"^^xsd:double ;
  eth:structuralTermS2 "0.10"^^xsd:double ; eth:structuralTermS3 "0.10"^^xsd:double ;
  eth:structuralTermS4 "0.10"^^xsd:double ; eth:epistemicAbstention false ;
  eth:decision eth:Decision_ALLOW ; eth:adequacy "0.70"^^xsd:double .

cse:bad_conf_two_strengths a eth:Confrontation ;
  eth:confrontationId "BAD-E30-CONF-4" ; eth:confrontationCase cse:bad_case_ok ;
  eth:confrontationProfile cse:bad_profile_001 ; eth:appliedCalibration cal:ladder_fit_v12 ;
  eth:agentLayer eth:Layer_model ;
  eth:groundingStrength "1.0"^^xsd:double , "0.50"^^xsd:double ;
  {ok_conf} ; eth:decision eth:Decision_ALLOW ; eth:adequacy "0.70"^^xsd:double .

cse:bad_conf_abstention_not_boolean a eth:Confrontation ;
  eth:confrontationId "BAD-E30-CONF-5" ; eth:confrontationCase cse:bad_case_ok ;
  eth:confrontationProfile cse:bad_profile_001 ; eth:appliedCalibration cal:ladder_fit_v12 ;
  eth:agentLayer eth:Layer_model ; eth:groundingStrength "1.0"^^xsd:double ;
  eth:adequacyLow "0.60"^^xsd:double ; eth:materialGapLow "0.30"^^xsd:double ;
  eth:structuralTermS2 "0.10"^^xsd:double ; eth:structuralTermS3 "0.10"^^xsd:double ;
  eth:structuralTermS4 "0.10"^^xsd:double ; eth:epistemicAbstention "maybe" ;
  eth:decision eth:Decision_ALLOW ; eth:adequacy "0.70"^^xsd:double .

cse:bad_observation_low_confidence a eth:FacetObservation ;
  eth:observedFacet fac:W1 ; eth:observedValue "0.50"^^xsd:double ;
  eth:observationConfidence "0.10"^^xsd:double .

cse:bad_observation_level_above_one a eth:FacetObservation ;
  eth:observedFacet fac:M6 ; eth:observedValue "1.20"^^xsd:double ;
  eth:observationConfidence "0.90"^^xsd:double .""")
    return "\n".join(lines) + "\n", [{"iri": iri, "shape": shape, "defect": defect}
                                     for iri, shape, defect in expectations]


def emit_oversight_classes():
    """v4.2 (D5.4): the oversight regime is a declared, enumerable dimension of a case,
    not prose. Each regime carries the value the arithmetic actually uses."""
    return """
# ---------------- oversight regimes (E11c', v13) ----------------
eth:OversightRegime a owl:Class ; rdfs:label "OversightRegime" ;
  rdfs:comment "how much a human can still intervene in the decision the agent takes (D5.4)" .
eth:Oversight_unspecified a eth:OversightRegime ; rdfs:label "unspecified" ;
  eth:oversightValue "0.0"^^xsd:double ;
  rdfs:comment "the corpus declares nothing about review: the v12 behaviour is preserved" .
eth:Oversight_none a eth:OversightRegime ; rdfs:label "none" ;
  eth:oversightValue "0.0"^^xsd:double ;
  rdfs:comment "no review, no appeal: the demand on the agent's own review channel (M9) rises" .
eth:Oversight_out_of_loop a eth:OversightRegime ; rdfs:label "out_of_loop" ;
  eth:oversightValue "0.2"^^xsd:double .
eth:Oversight_on_the_loop a eth:OversightRegime ; rdfs:label "on_the_loop" ;
  eth:oversightValue "0.5"^^xsd:double .
eth:Oversight_in_the_loop a eth:OversightRegime ; rdfs:label "in_the_loop" ;
  eth:oversightValue "0.8"^^xsd:double ;
  rdfs:comment "human review AND independent audit: the effective irreversibility is attenuated" .
eth:oversightValue a owl:DatatypeProperty ; rdfs:domain eth:OversightRegime ; rdfs:range xsd:double .
eth:oversightRegime a owl:ObjectProperty ; rdfs:domain eth:EthicalCase ; rdfs:range eth:OversightRegime .
eth:crossPillarCoefficient a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:salienceAdaptation a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:oversightAttenuation a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:missingOversightRequirement a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:reviewNeedWeightBand a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:reviewNeedWeightMaterialGap a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:reviewNeedWeightEpistemic a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:reviewNeedWeightNearBar a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:coverageGate a owl:DatatypeProperty ; rdfs:domain eth:Calibration ; rdfs:range xsd:double .
eth:reviewNeed a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:crossPillarDuty a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:crossPillarDutyEdge a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:crossPillarDutyFace a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:caseSalienceW a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:caseSalienceC a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:caseSalienceM a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
eth:caseSalienceK a owl:DatatypeProperty ; rdfs:domain eth:Confrontation ; rdfs:range xsd:double .
"""


def emit_v42_calibration_addendum(cal_id, with_rules=True):
    """v4.2 (D5.1, D5.3, D5.4, D5.6): the coefficients the v13 core actually reads, declared
    as graph literals so the arithmetic mirror can reproduce them from the RDF alone.
    Emitted for every declared calibration individual, so no individual can be read with
    implicit (undeclared) v13 parameters."""
    head = """
# ---------------- v13 coefficients (declared, not assumed) ----------------
%s eth:crossPillarCoefficient "0.0"^^xsd:double ;
         eth:salienceAdaptation "0.0"^^xsd:double ;
         eth:oversightAttenuation "0.45"^^xsd:double ;
         eth:missingOversightRequirement "0.08"^^xsd:double ;
         eth:reviewNeedWeightBand "0.30"^^xsd:double ;
         eth:reviewNeedWeightMaterialGap "0.25"^^xsd:double ;
         eth:reviewNeedWeightEpistemic "0.20"^^xsd:double ;
         eth:reviewNeedWeightNearBar "0.25"^^xsd:double ;
         eth:coverageGate "0.70"^^xsd:double ."""
    head = head % cal_id
    if not with_rules:
        return head
    return head + """

eth:rule_lattice_marginal_alpha a eth:Rule ; rdfs:label "Proposition 1 (D5.1)" ;
  eth:appliesToClass eth:LatticeSlot ;
  eth:ruleStatement "alpha_e = (1/3) * sum over the faces containing edge e of beta_f: the edge weights are derived, not free. For beta_f = 1/4 this yields alpha_e = 1/6, the exact v10-v12 calibration" .

eth:rule_cross_pillar_exposure a eth:Rule ; rdfs:label "E7' (D5.3)" ;
  eth:appliesToClass eth:Confrontation ;
  eth:ruleStatement "psi = sum_f sigma_f * gap_f / sum_f sigma_f over duties spanning >= 2 pillars, sigma_f = 1 - max_p beta_fp; zeta is 0 by default, so psi is a diagnostic and cannot change a verdict" .

eth:rule_review_need a eth:Rule ; rdfs:label "E32 (D5.6)" ;
  eth:appliesToClass eth:Confrontation ;
  eth:ruleStatement "reviewNeed = 0.30*band + 0.25*materialGapLow + 0.20*epistemicPenalty + 0.25*(1 - coverage), clamped to [0,1]: it orders cases sharing a verdict by how much external review they demand" .

eth:rule_coverage_gate a eth:Rule ; rdfs:label "E26' (D5.8)" ;
  eth:appliesToClass eth:Profile ;
  eth:ruleStatement "a profile declaring fewer than 70% of the canon duties is unauditable: the confrontation abstains and carries no adequacy literal" .
"""

def main():
    t0 = time.time()
    os.makedirs(os.path.join(ONT, "shapes"), exist_ok=True)
    os.makedirs(os.path.join(ONT, "fixtures"), exist_ok=True)
    limit = int(os.environ.get("ETH_WCMK_CASE_LIMIT", "0"))
    cases, personas = load_corpus()
    if limit:
        cases = cases[:limit]
    deontic_text, conflicts = G.emit_deontic()
    stats, decisions = emit_instances(cases, personas, conflicts)
    invalid_v4, expectations_v4 = G.emit_invalid()
    invalid_v6, expectations_v6 = emit_e30_fixtures()

    files = {
        "01_core.ttl": G.emit_core() + emit_oversight_classes(),
        "02_facets.ttl": G.emit_facets(),
        "03_deontic.ttl": deontic_text,
        "04_agency.ttl": G.emit_agency(),
        "05_dynamics.ttl": G.emit_dynamics(),
        "06_calibration.ttl": (G.emit_calibration(G.CALIB, "core.default_calibration + B5' ladder fit")
                       + emit_v42_calibration_addendum("cal:default_v12", with_rules=False)
                       + emit_v42_calibration_addendum("cal:ladder_fit_v12")),
        "07_grounding.ttl": emit_grounding_module(),
        "shapes/ontology_shapes.ttl": G.emit_shapes().replace("%NFACETS%", str(NFACETS)),
        "shapes/ontology_shapes_v6.ttl": emit_extra_shapes(),
        "fixtures/invalid_examples.ttl": invalid_v4,
        "fixtures/invalid_examples_v6.ttl": invalid_v6,
    }
    for name, text in files.items():
        with open(os.path.join(ONT, name), "w") as fh:
            fh.write(text)
    with open(os.path.join(ONT, "fixtures", "invalid_expectations.json"), "w") as fh:
        json.dump({"expectations": expectations_v4 + expectations_v6,
                   "v4_fixtures": len(expectations_v4),
                   "e30_fixtures": len(expectations_v6)}, fh, indent=2)

    report = {
        "generator": "_analysis/ontology/gen_ontology_v5.py",
        "version": VERSION,
        "corpus_source": "Evaluacoes/r5/corpus_v7_*",
        "facets_in_registry": NFACETS,
        "files": {name: os.path.getsize(os.path.join(ONT, name)) for name in files},
        "instances_triples": TRIPLES["instances"],
        "counts": stats,
        "norm_conflicts": len(conflicts),
        "decision_distribution": decisions,
        "layers": {"cases_A": sum(1 for c in cases if c["layer"] == "A"),
                   "cases_B": sum(1 for c in cases if c["layer"] == "B")},
        "registry_check": G.validate_registry(),
        "seconds": round(time.time() - t0, 2),
    }
    with open(os.path.join(ONT, "generation_report.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
