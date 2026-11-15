def conflict_index(conflicts):
    idx = {}
    for n, pattern, a, b, strategy, rank, domain, status in conflicts:
        idx.setdefault((domain, pattern), []).append((n, a, b, strategy, status))
    return idx


def emit_instances(cases, personas, conflicts):
    out = [head("fixtures/instances.ttl - the instantiated corpus (1,520 cases, 48 personas, "
                "representative confrontations computed with core.confront)")]
    rng = random.Random(SEED)
    cal = default_calibration()
    conflict_idx = conflict_index(conflicts)
    inst_to_norms = {}
    for inst_code, label, klass, domains, norms in INSTRUMENTS:
        inst_to_norms[inst_code] = [f"{inst_code}_{kind[0]}{i+1}"
                                    for i, (kind, pillar, statement, rank, def_, facet) in enumerate(norms)]

    # agents (personas)
    out.append("# ---------------------------------------------------------------- personas as agents ----")
    for p in personas:
        pid = p["profile_id"].replace("-", "_")
        fac = p["factors"]
        out.append(f"ag:persona_{pid} a eth:Agent ; rdfs:label {q(p['persona_type'])} ;")
        out.append(f"  eth:agentId {q(p['profile_id'])} ; eth:personaType {q(p['persona_type'])} ;")
        out.append(f"  eth:agentLayer eth:Layer_{p['layer']} ;")
        out.append(f"  eth:attainmentFactorW {num(fac['W'])} ; eth:attainmentFactorC {num(fac['C'])} ;")
        out.append(f"  eth:attainmentFactorM {num(fac['M'])} ; eth:attainmentFactorK {num(fac['K'])} ;")
        out.append(f"  eth:jitter {num(p['jitter'])} ; eth:confidenceMean {num(p['confidence_mu'])} ;")
        out.append(f"  eth:fallbackPolicy eth:Fallback_human_review .")
    out.append("ag:persona_component_reference a eth:Agent ; rdfs:label \"inference component\" ;")
    out.append("  eth:agentId \"AGENT-component\" ; eth:personaType \"component\" ;")
    out.append("  eth:agentLayer eth:Layer_model ; eth:attainmentFactorW 1.0 ; eth:attainmentFactorC 1.0 ;")
    out.append("  eth:attainmentFactorM 1.0 ; eth:attainmentFactorK 1.0 ; eth:jitter 0.0 ;")
    out.append("  eth:confidenceMean 0.85 ; eth:fallbackPolicy eth:Fallback_shutdown ;")
    out.append("  eth:forbiddenPillar eth:pillar_M , eth:pillar_W .")

    layered = sorted(rng.sample(range(len(cases)), PERSONA_LAYER_CASES))
    layered_set = set(layered)
    confrontations = []
    chains = 0
    stats = {"cases": 0, "profiles": 0, "confrontations": 0, "chains": 0,
             "stakeholders": 0, "consequences": 0, "evidence": 0, "vulnerabilities": 0}
    decisions = {}

    for i, case in enumerate(cases):
        cid = case["case_id"]
        domain = case["domain"]
        pattern = case["conflict_pattern"]
        attached = conflict_idx.get((domain, pattern), []) if pattern != "none" else []
        norm_conflict = "none"
        if attached:
            norm_conflict = ("unresolved" if any(s[3] == "unresolved_escalation" or s[4] == "unresolved_escalation"
                                                 for s in attached) else "resolved_by_priority")
        evidence_conflict = bool(case.get("ambiguous", False))
        stakeholders, consequence, evidence, vulnerability, review_body, prior, objective, resources, mitigation = parse_narrative(case)
        exposure = min(1.0, len(set(stakeholders)) / 4.0) if stakeholders else 0.5

        out.append(f"\ncse:{cid} a eth:EthicalCase ; rdfs:label {q(cid + ': ' + case['scenario'])} ;")
        out.append(f"  eth:caseId {q(cid)} ; eth:corpusLayer {q(case['layer'])} ;")
        out.append(f"  eth:scenario {q(case['scenario'])} ; eth:archetype {q(case['archetype'])} ;")
        out.append(f"  eth:designIntent eth:Decision_{case['design_intent']} ;")
        out.append(f"  eth:domain eth:domain_{domain} ; eth:severity eth:Severity_{case['severity']} ;")
        out.append(f"  eth:prudentialMode eth:Prudential_{case['prudential']} ;")
        out.append(f"  eth:reversibility eth:Reversibility_{case['irreversibility']} ;")
        out.append(f"  eth:horizon eth:Horizon_{case['horizon']} ;")
        out.append(f"  eth:conflictPattern eth:Pattern_{pattern} ;")
        out.append(f"  eth:agentLayer eth:Layer_system ;")
        out.append(f"  eth:epistemicUncertainty {num(case['U_E'])} ;")
        out.append(f"  eth:consequenceMass {num(case['R_c'])} ;")
        out.append(f"  eth:exposureScale {num(exposure)} ;")
        out.append(f"  eth:criticalPillar {', '.join('eth:pillar_' + p for p in case['critical_pillars'])} ;")
        out.append(f"  eth:normConflictStatus {q(norm_conflict)} ;")
        out.append(f"  eth:evidenceConflict {num(evidence_conflict)} ;")
        ids = []
        for label in case["norms"]:
            code = LABEL_TO_INST.get(label)
            if code:
                ids.extend(inst_to_norms[code])
        out.append(f"  eth:hasNorm {', '.join('norm:' + n for n in sorted(set(ids)))} ;")
        obligations = [n for n in sorted(set(ids)) if kind_of(n) == "Obligation"]
        prohibitions = [n for n in sorted(set(ids)) if kind_of(n) == "Prohibition"]
        permissions = [n for n in sorted(set(ids)) if kind_of(n) == "Permission"]
        out.append(f"  eth:hasObligation {', '.join('norm:' + n for n in obligations)} ;")
        out.append(f"  eth:hasProhibition {', '.join('norm:' + n for n in prohibitions)} ;")
        out.append(f"  eth:hasPermission {', '.join('norm:' + n for n in permissions)} ;")
        if attached:
            out.append(f"  eth:hasNormConflict {', '.join('norm:conflict_%03d' % s[0] for s in attached)} ;")
            out.append(f"  eth:caseResolutionStrategy {', '.join('eth:' + s[3] for s in attached)} ;")
        else:
            out.append(f"  eth:caseResolutionStrategy eth:Strategy_priority ;")
        if stakeholders:
            for j, s in enumerate(stakeholders):
                sid = f"sh_{cid}_{j}"
                out.append(f"  eth:hasStakeholder ag:{sid} ;")
                stats["stakeholders"] += 1
            out.append("")
        for j, s in enumerate(stakeholders):
            sid = f"sh_{cid}_{j}"
            out.append(f"ag:{sid} a eth:Stakeholder ; rdfs:label {q(s)} ; eth:stakeholderName {q(s)} ; "
                       f"eth:consentGiven false ; eth:affectedCount {j + 1} .")
        if consequence:
            stats["consequences"] += 1
            out.append(f"  cse:cons_{cid} a eth:Consequence ; rdfs:label {q(consequence)} ;")
            out.append(f"  eth:consequenceText {q(consequence)} ;")
            out.append(f"  eth:consequenceIrreversibility {q(case['irreversibility'])} ;")
            out.append(f"  eth:consequenceHorizon {q(case['horizon'])} ;")
            out.append(f"  eth:hasConsequence cse:cons_{cid} .")
        for j, (text, status) in enumerate(evidence):
            stats["evidence"] += 1
            out.append(f"ag:ev_{cid}_{j} a eth:Evidence ; rdfs:label {q(text)} ; eth:evidenceText {q(text)} ; "
                       f"eth:evidenceStatus {q(status)} ; eth:hasEvidence ag:ev_{cid}_{j} .")
        if vulnerability:
            stats["vulnerabilities"] += 1
            kind = "structural"
            for k in ("structural", "procedural", "epistemic", "cognitive", "dependency"):
                if k in vulnerability:
                    kind = k
                    break
            out.append(f"ag:vuln_{cid} a eth:Vulnerability ; rdfs:label {q(vulnerability)} ; "
                       f"eth:vulnerabilityText {q(vulnerability)} ; eth:vulnerabilityKind {q(kind)} ; "
                       f"eth:hasVulnerability ag:vuln_{cid} .")
        if review_body:
            out.append(f"  eth:hasReviewBody {q(review_body)} .")
        else:
            out.append("  eth:hasReviewBody \"no standing review body\" .")
        if prior:
            out.append(f"cse:{cid} eth:priorRecord {q(prior)} ; eth:declaredObjective {q(objective)} ; "
                       f"eth:operationalConstraint {q(resources)} ; eth:mitigationInPlace {q(mitigation)} .")
        out.append(f"cse:{cid} eth:hasRequirement")
        reqs = ",\n    ".join(f"[ a eth:FacetRequirement ; eth:facet fac:{f} ; "
                              f"eth:requirementValue {num(v)} ]" for f, v in case["facet_requirements"].items())
        out.append("    " + reqs + " ;")
        out.append(f"  eth:declaredProfile cse:PROF_{cid}_declared .")
        stats["cases"] += 1

        # declared profile (the agent levels the corpus declares for the case)
        out.append(f"cse:PROF_{cid}_declared a eth:Profile ; rdfs:label {q('declared profile of ' + cid)} ;")
        out.append(f"  eth:profileId {q('DECLARED-' + cid)} ; eth:layerOfProfile eth:Layer_system ;")
        out.append(f"  eth:coverage 1.0 ; eth:basedOnAgent ag:agent_{cid} ; eth:hasObservation")
        obs = ",\n    ".join(f"[ a eth:FacetObservation ; eth:facet fac:{f} ; "
                             f"eth:observedValue {num(case['declared_levels'][f])} ; "
                             f"eth:observationConfidence {num(case['declared_confidence'][f])} ]"
                             for f in [fc.code for fc in FACETS])
        out.append("    " + obs + " .")
        stats["profiles"] += 1
        out.append(f"ag:agent_{cid} a eth:Agent ; rdfs:label {q('declared agent ' + cid)} ;")
        out.append(f"  eth:agentId {q('AGENT-' + cid)} ; eth:personaType \"declared\" ;")
        out.append(f"  eth:agentLayer eth:Layer_system ; eth:attainmentFactorW 1.0 ; eth:attainmentFactorC 1.0 ;")
        out.append(f"  eth:attainmentFactorM 1.0 ; eth:attainmentFactorK 1.0 ; eth:jitter 0.0 ;")
        out.append(f"  eth:confidenceMean {num(sum(case['declared_confidence'].values()) / len(case['declared_confidence']))} ;")
        out.append(f"  eth:fallbackPolicy eth:Fallback_human_review .")

        spec = build_case_spec(case, norm_conflict, evidence_conflict, exposure)
        declared = Profile(f"DECLARED-{cid}", case["declared_levels"], case["declared_confidence"], "system")
        emit_confrontation(out, cid, "declared", spec, declared, cal, "system", stats, confrontations)

        if i in layered_set:
            layer_profiles = {}
            for layer in ("model", "system", "operator"):
                pool = [p for p in personas if p["layer"] == layer]
                persona = rng.choice(pool)
                levels, conf = persona_levels(persona, case["facet_requirements"], rng)
                prof = Profile(persona["profile_id"] + "-" + cid, levels, conf, layer)
                layer_profiles[layer] = prof
                pid = persona["profile_id"].replace("-", "_")
                out.append(f"cse:PROF_{cid}_{pid} a eth:Profile ; rdfs:label {q(persona['persona_type'] + ' profile of ' + cid)} ;")
                out.append(f"  eth:profileId {q(persona['profile_id'] + '-' + cid)} ;")
                out.append(f"  eth:layerOfProfile eth:Layer_{layer} ; eth:coverage 1.0 ;")
                out.append(f"  eth:basedOnAgent ag:persona_{pid} ; eth:hasObservation")
                obs = ",\n    ".join(f"[ a eth:FacetObservation ; eth:facet fac:{f} ; "
                                     f"eth:observedValue {num(levels[f])} ; "
                                     f"eth:observationConfidence {num(conf[f])} ]"
                                     for f in [fc.code for fc in FACETS])
                out.append("    " + obs + " .")
                stats["profiles"] += 1
                emit_confrontation(out, cid, persona["profile_id"], spec, prof, cal, layer, stats, confrontations)
            chain = emit_chain(out, cid, layer_profiles, spec, cal, stats)
            chains += 1

    out.append("\n# -------------------------------------------------------- summary counts ----")
    out.append(f"eth:ontology_v4 eth:hasInstantiateCount {stats['confrontations']} ; "
               f"eth:hasCaseCount {stats['cases']} ; eth:hasAgentCount {len(personas) + len(cases)} .")
    return "\n".join(out) + "\n", stats, decisions


KIND_CACHE = {}


def kind_of(norm_id):
    if norm_id in KIND_CACHE:
        return KIND_CACHE[norm_id]
    for inst_code, label, klass, domains, norms in INSTRUMENTS:
        for i, (kind, pillar, statement, rank, def_, facet) in enumerate(norms):
            KIND_CACHE[f"{inst_code}_{kind[0]}{i+1}"] = kind
    return KIND_CACHE[norm_id]


def persona_levels(persona, facet_requirements, rng):
    levels, conf = {}, {}
    for f in FACETS:
        fac = persona["factors"][f.primary_pillar()]
        if persona["persona_type"] == "guard_fragile" and f.guard:
            fac = 0.25 / max(facet_requirements[f.code], 1e-6)
        if persona["persona_type"] == "recoverable_failure" and f.code in ("C7", "M7"):
            fac = 1.15
        levels[f.code] = clamp(facet_requirements[f.code] * fac * (1 + persona["jitter"]), 0.0, 1.0)
        conf[f.code] = clamp(rng.gauss(persona["confidence_mu"], 0.10), 0.30, 1.0)
    return levels, conf


def build_case_spec(case, norm_conflict, evidence_conflict, exposure):
    return CaseSpec(case["case_id"], case["domain"], case["severity"], case["prudential"],
                    case["irreversibility"], case["facet_requirements"], case["U_E"], case["R_c"],
                    tuple(case["critical_pillars"]), case["horizon"], case["conflict_pattern"],
                    "system", tuple(case["norms"]),
                    norm_conflict=norm_conflict, evidence_conflict=evidence_conflict,
                    exposure=exposure)


def emit_confrontation(out, cid, agent, spec, profile, cal, layer, stats, confrontations):
    mid = _adequacy(spec, profile, cal, FACETS, "central")
    low = _adequacy(spec, profile, cal, FACETS, "pessimistic")
    high = _adequacy(spec, profile, cal, FACETS, "optimistic")
    decision = decide(low["aa"], low["ratio"], low["veto"], low["hardVeto"],
                      low["material_gap"], spec, cal, None)
    ref = confront(spec, profile, cal)
    assert ref["decision"] == decision, (cid, agent, ref["decision"], decision)
    conf_id = f"CONF_{cid}_{agent}".replace("-", "_")
    deficits = mid["deficits"]
    s2, s3, s4 = mid["S2"], mid["S3"], mid["S4"]
    out.append(f"cse:{conf_id} a eth:Confrontation ; rdfs:label {q('confrontation ' + cid + ' x ' + agent)} ;")
    out.append(f"  eth:confrontationId {q(conf_id)} ;")
    out.append(f"  eth:confrontationCase cse:{cid} ;")
    out.append(f"  eth:confrontationProfile cse:PROF_{cid}_{agent.replace('-', '_')} ;")
    out.append(f"  eth:appliedCalibration cal:default_v12 ;")
    out.append(f"  eth:agentLayer eth:Layer_{layer} ;")
    for i, p in enumerate(PILLARS):
        out.append(f"  eth:level{p} {num(mid['levels'][p])} ;")
        out.append(f"  eth:requirement{p} {num(mid['requirements'][p])} ;")
        out.append(f"  eth:deficit{p} {num(deficits[p])} ;")
        out.append(f"  eth:guardedDeficit{p} {num(mid['guarded_deficits'][p])} ;")
    out.append(f"  eth:structuralTermS2 {num(s2)} ;")
    out.append(f"  eth:structuralTermS3 {num(s3)} ;")
    out.append(f"  eth:structuralTermS4 {num(s4)} ;")
    out.append(f"  eth:slackS3minusS4 {num(s3 - s4)} ;")
    out.append(f"  eth:slackS2minusS3 {num(s2 - s3)} ;")
    out.append(f"  eth:slackMaxDeficitMinusS2 {num(max(deficits.values()) - s2)} ;")
    out.append(f"  eth:weightedDeficit {num(mid['D'])} ;")
    out.append(f"  eth:epistemicPenalty {num(mid['u'])} ;")
    out.append(f"  eth:facetExposurePhi {num(mid['phi'])} ;")
    out.append(f"  eth:adequacyRaw {num(mid['aa_raw'])} ;")
    out.append(f"  eth:adequacy {num(mid['aa'])} ;")
    out.append(f"  eth:adequacyLow {num(low['aa'])} ;")
    out.append(f"  eth:adequacyHigh {num(high['aa'])} ;")
    out.append(f"  eth:adequacyBand {num(high['aa'] - low['aa'])} ;")
    out.append(f"  eth:materialGapLow {num(low['material_gap'])} ;")
    out.append(f"  eth:materialFacet fac:{low['material_facet']} ;")
    out.append(f"  eth:decision eth:Decision_{decision} ;")
    out.append(f"  eth:decisionBar {num(decide_bar(spec, cal))} ;")
    out.append(f"  eth:declaredStakesSum {num(spec.stakes)} ;")
    out.append(f"  eth:stakesWeighted {num(case_stakes(spec))} ;")
    out.append(f"  eth:sigmaFloor {num(low['sigma'])} ;")
    out.append(f"  eth:failureProbability {num(low['p_fail'])} ;")
    out.append(f"  eth:reliability {num(1 - low['p_fail'])} ;")
    out.append(f"  eth:riskRatio {num(low['ratio'])} ;")
    out.append(f"  eth:residualRisk {num(low['R_r'])} ;")
    out.append(f"  eth:riskAttenuation {num(spec.R_c - low['R_r'])} ;")
    out.append(f"  eth:harmScale {num(low['harm'])} ;")
    out.append(f"  eth:coverage {num(len(profile.attainment) / len(spec.facet_requirements))} ;")
    out.append(f"  eth:guardFailureCount {len(mid['guard_failures'])} ;")
    out.append(f"  eth:worstPillar eth:pillar_{mid['worst_pillar']} ;")
    if mid["worst_facet"]:
        out.append(f"  eth:worstFacet fac:{mid['worst_facet']} ;")
    if mid["veto"]:
        out.append(f"  eth:vetoPillar {', '.join('eth:pillar_' + p for p in mid['veto'])} ;")
    if mid["hardVeto"]:
        out.append(f"  eth:hardVetoPillar {', '.join('eth:pillar_' + p for p in mid['hardVeto'])} ;")
    guards = ",\n    ".join(f"[ a eth:GuardFailure ; eth:guardFacet fac:{f} ; "
                            f"eth:guardPillar eth:pillar_{pl} ; eth:observedAtGuard {num(v)} ; "
                            f"eth:guardFloor {num(gm)} ; eth:guardPolicy eth:Policy_{pol} ]"
                            for f, pl, v, gm, pol in mid["guard_failures"])
    if guards:
        out.append(f"  eth:hasGuardFailure\n    {guards} .")
    else:
        out.append("  eth:hasGuardFailure [] .")
    stats["confrontations"] += 1
    confrontations.append(conf_id)
    decisions.setdefault(decision, 0)
    decisions[decision] += 1


def decide_bar(case, cal):
    return clamp(cal.bar_base + cal.bar_severity * case.severity
                 + cal.bar_irreversibility * REVERSIBILITY[case.irreversibility]
                 + cal.bar_prudential * case.prudential
                 + cal.bar_horizon * HORIZON_VALUE[case.horizon], 0.30, 0.90)


def emit_chain(out, cid, layer_profiles, spec, cal, stats):
    results = {}
    for layer in ("model", "system", "operator"):
        mid = _adequacy(spec, layer_profiles[layer], cal, FACETS, "central")
        low = _adequacy(spec, layer_profiles[layer], cal, FACETS, "pessimistic")
        dec = decide(low["aa"], low["ratio"], low["veto"], low["hardVeto"],
                     low["material_gap"], spec, cal, None)
        results[layer] = (dec, low["aa"], low["R_r"])
    res = confront_chain(spec, layer_profiles, cal)
    assert res["decision"] == results[res["weakest_layer"]][0]
    out.append(f"\ncse:CHAIN_{cid} a eth:ConfrontationChain ; rdfs:label {q('layered agency of ' + cid)} ;")
    out.append(f"  eth:confrontationCase cse:{cid} ;")
    out.append(f"  eth:weakestLinkLayer eth:Layer_{res['weakest_layer']} ;")
    out.append(f"  eth:chainDecision eth:Decision_{res['decision']} ;")
    out.append(f"  eth:chainAdequacyLow {num(res['adequacy_low'])} ;")
    out.append(f"  eth:chainResidualRisk {num(res['max_R_r'])} ;")
    out.append(f"  eth:fallbackForChain eth:Fallback_human_review ;")
    layers = ",\n    ".join(f"[ a eth:ChainLayerResult ; eth:resultLayer eth:Layer_{l} ; "
                            f"eth:resultAdequacyLow {num(results[l][1])} ; "
                            f"eth:resultDecision eth:Decision_{results[l][0]} ; "
                            f"eth:resultResidualRisk {num(results[l][2])} ]"
                            for l in ("model", "system", "operator"))
    out.append(f"  eth:layerResult\n    {layers} ;")
    out.append(f"  eth:delegationChain cse:DELEG_{cid} .")
    for depth in (1, 2, 3):
        out.append(f"ag:chain_{cid}_d{depth} a eth:DelegationChain ; rdfs:label {q('delegation chain depth ' + str(depth) + ' for ' + cid)} ;")
        out.append(f"  eth:delegationChainOf cse:{cid} ; eth:chainRoot ag:agent_{cid} ;")
        out.append(f"  eth:fallbackForChain eth:Fallback_escalate_prohibited ;")
        out.append(f"  eth:chainLink cse:link_{cid}_d{depth}_1 , cse:link_{cid}_d{depth}_2 , cse:link_{cid}_d{depth}_3 ;")
    for depth in (1, 2):
        out.append(f"ag:chain_{cid}_d{depth} eth:chainPrefixOf ag:chain_{cid}_d{depth+1} .")
    out.append(f"ag:chain_{cid}_d1 eth:chainPrefixOf ag:chain_{cid}_d3 .")
    stats["chains"] += 1


def confront_chain(case, profiles, cal):
    from core import confront_chain as _cc
    return _cc(case, profiles, cal)
