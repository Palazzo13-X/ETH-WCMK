def emit_invalid():
    out = [head("fixtures/invalid_examples.ttl - deliberately broken individuals, "
                "each one attributable to a named shape")]
    expectations = []

    def bad(iri, types, props, shape, defect):
        individual(out, iri, types, props)
        expectations.append({"iri": iri, "shape": shape, "defect": defect})

    base_facet = {"rdfs:label": '"bad facet"', "eth:code": '"W9"',
                  "eth:betaW": "1.0", "eth:betaC": "0.0", "eth:betaM": "0.0", "eth:betaK": "0.0",
                  "eth:betaSum": "1.0", "eth:nPillars": "1", "eth:minNonZeroBeta": "1.0",
                  "eth:primaryPillar": "eth:pillar_W", "eth:sharesPillar": "eth:pillar_W",
                  "eth:aggregationPolicy": "eth:Policy_weighted_mean",
                  "eth:hardGuard": "false", "eth:guardMin": "0.0", "eth:weight": "1.0",
                  "eth:observable": '"audit trail recorded in the log"',
                  "eth:criticalityStatement": CRIT_13}
    bad("fac:bad_facet_beta_sum", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:betaSum": "0.9"}), "sh:FacetShape", "beta sum != 1")
    bad("fac:bad_facet_beta_token", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:betaW": "0.60", "eth:betaC": "0.30", "eth:betaM": "0.10",
                          "eth:nPillars": "3", "eth:minNonZeroBeta": "0.10"}),
        "sh:FacetShape", "beta token smaller than 0.15")
    bad("fac:bad_facet_four_pillars", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:betaW": "0.40", "eth:betaC": "0.20", "eth:betaM": "0.20",
                          "eth:betaK": "0.20", "eth:nPillars": "4"}),
        "sh:FacetShape", "facet spread over four pillars")
    bad("fac:bad_facet_guard_without_floor", ["eth:Facet", "eth:WantFacet", "eth:GuardedFacet"],
        merge(base_facet, {"eth:hardGuard": "true", "eth:guardMin": "0.0"}),
        "sh:FacetShape", "hard guard declared with guard floor 0")
    bad("fac:bad_facet_no_observable", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:observable": None}), "sh:FacetShape", "no observable declared")
    bad("fac:bad_facet_12_domains", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:criticalityStatement":
                          bnode_list([[f"a eth:CriticalityStatement",
                                       f"eth:criticalityDomain eth:domain_{d}",
                                       "eth:criticalityLevel 3"] for d in DOMAINS[:12]])}),
        "sh:FacetShape", "criticality missing for the 13th domain")
    bad("fac:bad_facet_weight_out_of_range", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:weight": "2.5"}), "sh:FacetShape", "facet weight above 1")
    bad("fac:bad_facet_no_primary_pillar", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:primaryPillar": None}),
        "sh:FacetShape", "no primary pillar declared")
    bad("fac:bad_facet_unknown_policy", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:aggregationPolicy": "eth:Policy_max_of"}),
        "sh:FacetShape", "aggregation policy not in the declared set")
    bad("fac:bad_facet_negative_beta", ["eth:Facet", "eth:WantFacet"],
        merge(base_facet, {"eth:betaW": "-0.2", "eth:betaSum": "0.8"}),
        "sh:FacetShape", "negative beta")

    base_slot = {"rdfs:label": '"bad slot"', "eth:slotKind": '"edge"', "eth:incidence": '"W,C"',
                 "eth:belongsToTerm": "eth:term_S2", "eth:structuralWeight": "0.16666666666666666"}
    bad("eth:bad_slot_weight_out_of_range", ["eth:LatticeSlot"],
        merge(base_slot, {"eth:structuralWeight": "1.5"}),
        "sh:LatticeSlotShape", "slot weight above 1")
    bad("eth:bad_slot_no_term", ["eth:LatticeSlot"], merge(base_slot, {"eth:belongsToTerm": None}),
        "sh:LatticeSlotShape", "slot attached to no structural term")
    bad("eth:bad_slot_unknown_kind", ["eth:LatticeSlot"], merge(base_slot, {"eth:slotKind": '"corner"'}),
        "sh:LatticeSlotShape", "unknown lattice slot kind")
    bad("eth:bad_term_unnormalised", ["eth:StructuralTerm"],
        {"rdfs:label": '"S2 term whose weights do not sum to 1'", "eth:termCoefficient": "0.12",
         "eth:termWeightSum": "2.03", "eth:hasSlot": "eth:slot_eWC , eth:slot_eWM"},
        "sh:StructuralTermShape", "term weights do not sum to 1")

    base_cal = {"rdfs:label": '"bad calibration"', "eth:calibrationSource": '"manual"',
                "eth:lamW": "0.30", "eth:lamC": "0.25", "eth:lamM": "0.25", "eth:lamK": "0.20",
                "eth:lamSum": "1.0", "eth:muW": "0.15", "eth:muC": "0.40", "eth:muM": "0.20",
                "eth:muK": "0.25", "eth:muSum": "1.0", "eth:thetaW": "0.65", "eth:thetaC": "0.60",
                "eth:thetaM": "0.60", "eth:thetaK": "0.65", "eth:gamma": "0.12", "eth:eta": "0.05",
                "eth:omega": "0.03", "eth:rho": "0.10", "eth:delta": "0.05", "eth:penaltySum": "0.35",
                "eth:hardVetoDelta": "0.25", "eth:materialGap": "0.25", "eth:criticalProhibitGap": "0.35",
                "eth:barBase": "0.55", "eth:hysteresis": "0.05", "eth:abstainUncertainty": "0.60",
                "eth:abstainKnowledgeFloor": "0.65", "eth:stakeWeightSeverity": "0.45",
                "eth:stakeWeightIrreversibility": "0.30", "eth:stakeWeightPrudential": "0.15",
                "eth:stakeWeightHorizon": "0.10", "eth:stakeWeightSum": "1.0",
                "eth:usesLattice": "eth:term_D , eth:term_S2 , eth:term_S3 , eth:term_S4"}
    bad("cal:bad_calibration_lam_sum", ["eth:Calibration"],
        merge(base_cal, {"eth:lamW": "0.20", "eth:lamSum": "0.90"}),
        "sh:CalibrationShape", "pillar weights do not sum to 1")
    bad("cal:bad_calibration_mu_sum", ["eth:Calibration"],
        merge(base_cal, {"eth:muW": "0.55", "eth:muSum": "1.55"}),
        "sh:CalibrationShape", "failure probabilities mu do not sum to 1")
    bad("cal:bad_calibration_budget", ["eth:Calibration"],
        merge(base_cal, {"eth:gamma": "0.40", "eth:penaltySum": "0.63"}),
        "sh:CalibrationShape", "penalty budget exceeded")
    bad("cal:bad_calibration_theta", ["eth:Calibration"], merge(base_cal, {"eth:thetaW": "1.40"}),
        "sh:CalibrationShape", "veto threshold above 1")
    bad("cal:bad_calibration_negative_hysteresis", ["eth:Calibration"],
        merge(base_cal, {"eth:hysteresis": "-0.05"}), "sh:CalibrationShape", "negative hysteresis")
    bad("cal:bad_calibration_abstain_floor", ["eth:Calibration"],
        merge(base_cal, {"eth:abstainUncertainty": "1.60"}),
        "sh:CalibrationShape", "abstention threshold above 1")
    bad("cal:bad_calibration_stake_weights", ["eth:Calibration"],
        merge(base_cal, {"eth:stakeWeightHorizon": "0.00", "eth:stakeWeightSum": "0.90"}),
        "sh:CalibrationShape", "stakes coefficients do not sum to 1")
    bad("cal:bad_calibration_missing_lattice", ["eth:Calibration"],
        merge(base_cal, {"eth:usesLattice": "eth:term_D , eth:term_S2"}),
        "sh:CalibrationShape", "calibration does not use the four structural terms")

    base_case = {"rdfs:label": '"bad case"', "eth:caseId": '"BAD-0001"', "eth:corpusLayer": '"A"',
                 "eth:scenario": '"a deployment under review"', "eth:archetype": '"risk_based"',
                 "eth:designIntent": "eth:Decision_REVIEW_REQUIRED", "eth:domain": "eth:domain_SA",
                 "eth:severity": "eth:Severity_high", "eth:prudentialMode": "eth:Prudential_elevated",
                 "eth:reversibility": "eth:Reversibility_reversible", "eth:horizon": "eth:Horizon_medium",
                 "eth:conflictPattern": "eth:Pattern_none", "eth:agentLayer": "eth:Layer_system",
                 "eth:epistemicUncertainty": "0.40", "eth:consequenceMass": "0.80",
                 "eth:exposureScale": "0.50", "eth:criticalPillar": "eth:pillar_W , eth:pillar_C",
                 "eth:criticalPillarDeclaredCount": "2", "eth:normConflictStatus": '"none"',
                 "eth:evidenceConflict": "false",
                 "eth:hasNorm": "norm:UDHR_Art3_O1 , norm:UDHR_Art3_P1 , norm:UDHR_Art3_P2",
                 "eth:hasObligation": "norm:UDHR_Art3_O1", "eth:hasProhibition": "norm:UDHR_Art3_P1",
                 "eth:hasPermission": "norm:UDHR_Art3_P2",
                 "eth:caseResolutionStrategy": "eth:Strategy_priority",
                 "eth:hasReviewBody": '"the standing review board"',
                 "eth:declaredProfile": "cse:bad_profile_001", "eth:hasRequirement": REQ_ALL}
    bad("cse:bad_case_no_domain", ["eth:EthicalCase"], merge(base_case, {"eth:domain": None}),
        "sh:EthicalCaseShape", "case with no domain")
    bad("cse:bad_case_no_severity", ["eth:EthicalCase"], merge(base_case, {"eth:severity": None}),
        "sh:EthicalCaseShape", "case with no severity band")
    bad("cse:bad_case_no_prudential", ["eth:EthicalCase"],
        merge(base_case, {"eth:prudentialMode": None}),
        "sh:EthicalCaseShape", "case with no prudential mode")
    bad("cse:bad_case_no_horizon", ["eth:EthicalCase"], merge(base_case, {"eth:horizon": None}),
        "sh:EthicalCaseShape", "case with no horizon")
    bad("cse:bad_case_no_reversibility", ["eth:EthicalCase"],
        merge(base_case, {"eth:reversibility": None}), "sh:EthicalCaseShape", "case with no reversibility")
    bad("cse:bad_case_unknown_severity", ["eth:EthicalCase"],
        merge(base_case, {"eth:severity": "eth:Severity_extreme"}),
        "sh:EthicalCaseShape", "severity band outside the declared set")
    bad("cse:bad_case_uncertainty_above_one", ["eth:EthicalCase"],
        merge(base_case, {"eth:epistemicUncertainty": "1.20"}),
        "sh:EthicalCaseShape", "epistemic uncertainty above 1")
    bad("cse:bad_case_zero_consequence", ["eth:EthicalCase"],
        merge(base_case, {"eth:consequenceMass": "0.0"}),
        "sh:EthicalCaseShape", "consequence mass of zero")
    bad("cse:bad_case_exposure_above_one", ["eth:EthicalCase"],
        merge(base_case, {"eth:exposureScale": "1.40"}), "sh:EthicalCaseShape", "exposure scale above 1")
    bad("cse:bad_case_single_critical_pillar", ["eth:EthicalCase"],
        merge(base_case, {"eth:criticalPillar": "eth:pillar_W", "eth:criticalPillarDeclaredCount": "1"}),
        "sh:EthicalCaseShape", "fewer than two declared critical pillars")
    bad("cse:bad_case_unresolved_without_conflict", ["eth:EthicalCase"],
        merge(base_case, {"eth:normConflictStatus": '"unresolved"', "eth:hasNormConflict": None}),
        "sh:EthicalCaseShape", "status unresolved with no conflict attached")
    bad("cse:bad_case_unknown_status", ["eth:EthicalCase"],
        merge(base_case, {"eth:normConflictStatus": '"maybe"'}),
        "sh:EthicalCaseShape", "conflict status outside the declared set")
    bad("cse:bad_case_no_norms", ["eth:EthicalCase"],
        merge(base_case, {"eth:hasNorm": None, "eth:hasObligation": None,
                          "eth:hasProhibition": None, "eth:hasPermission": None}),
        "sh:EthicalCaseShape", "case engaging no norm")
    bad("cse:bad_case_27_requirements", ["eth:EthicalCase"],
        merge(base_case, {"eth:hasRequirement":
                          bnode_list([[f"a eth:FacetRequirement", f"eth:requirementFacet fac:{f.code}",
                                       "eth:requirementValue 0.60"] for f in FACETS[:27]])}),
        "sh:EthicalCaseShape", "case with 27 instead of 28 facet requirements")

    base_profile = {"rdfs:label": '"bad profile"', "eth:profileId": '"BAD-PROFILE-1"',
                    "eth:layerOfProfile": "eth:Layer_model", "eth:coverage": "1.0",
                    "eth:basedOnAgent": "ag:bad_agent_1", "eth:hasObservation": OBS_ALL}
    bad("cse:bad_profile_no_layer", ["eth:Profile"], merge(base_profile, {"eth:layerOfProfile": None}),
        "sh:ProfileShape", "profile with no agency layer")
    bad("cse:bad_profile_coverage_above_one", ["eth:Profile"], merge(base_profile, {"eth:coverage": "1.5"}),
        "sh:ProfileShape", "coverage above 1")
    bad("cse:bad_profile_no_observation", ["eth:Profile"], merge(base_profile, {"eth:hasObservation": None}),
        "sh:ProfileShape", "profile with no facet observation")
    bad("cse:bad_observation_value_above_one", ["eth:FacetObservation"],
        {"eth:observedFacet": "fac:W1", "eth:observedValue": "1.20", "eth:observationConfidence": "0.90"},
        "sh:FacetObservationShape", "observed level above 1")
    bad("cse:bad_observation_no_facet", ["eth:FacetObservation"],
        {"eth:observedValue": "0.50", "eth:observationConfidence": "0.90"},
        "sh:FacetObservationShape", "observation with no facet")
    bad("cse:bad_requirement_below_floor", ["eth:FacetRequirement"],
        {"eth:requirementFacet": "fac:W1", "eth:requirementValue": "0.20"},
        "sh:FacetRequirementShape", "requirement below the canonical floor")

    base_conf = {"rdfs:label": '"bad confrontation"', "eth:confrontationId": '"BAD-CONF-1"',
                 "eth:confrontationCase": "cse:bad_case_ok", "eth:confrontationProfile": "cse:bad_profile_001",
                 "eth:appliedCalibration": "cal:default_v12",
                 "eth:levelW": "0.70", "eth:levelC": "0.60", "eth:levelM": "0.80", "eth:levelK": "0.50",
                 "eth:requirementW": "0.80", "eth:requirementC": "0.75", "eth:requirementM": "0.90",
                 "eth:requirementK": "0.85", "eth:deficitW": "0.10", "eth:deficitC": "0.15",
                 "eth:deficitM": "0.10", "eth:deficitK": "0.35",
                 "eth:structuralTermS2": "0.10", "eth:structuralTermS3": "0.10",
                 "eth:structuralTermS4": "0.10",
                 "eth:slackS3minusS4": "0.0", "eth:slackS2minusS3": "0.0",
                 "eth:slackMaxDeficitMinusS2": "0.25", "eth:weightedDeficit": "0.15",
                 "eth:adequacy": "0.70", "eth:adequacyLow": "0.65", "eth:adequacyHigh": "0.75",
                 "eth:adequacyBand": "0.10", "eth:decision": "eth:Decision_REVIEW_REQUIRED",
                 "eth:decisionBar": "0.60", "eth:stakesWeighted": "0.70", "eth:declaredStakesSum": "1.60",
                 "eth:sigmaFloor": "0.10", "eth:failureProbability": "0.60", "eth:residualRisk": "0.40",
                 "eth:riskAttenuation": "0.40", "eth:guardFailureCount": "0", "eth:coverage": "1.0"}
    bad("cse:bad_conf_adequacy_above_one", ["eth:Confrontation"], merge(base_conf, {"eth:adequacy": "1.20"}),
        "sh:ConfrontationShape", "adequacy above 1")
    bad("cse:bad_conf_adequacy_negative", ["eth:Confrontation"], merge(base_conf, {"eth:adequacy": "-0.20"}),
        "sh:ConfrontationShape", "negative adequacy")
    bad("cse:bad_conf_no_decision", ["eth:Confrontation"], merge(base_conf, {"eth:decision": None}),
        "sh:ConfrontationShape", "confrontation without a verdict")
    bad("cse:bad_conf_two_decisions", ["eth:Confrontation"],
        merge(base_conf, {"eth:decision": "eth:Decision_REVIEW_REQUIRED , eth:Decision_PROHIBIT"}),
        "sh:ConfrontationShape", "two verdicts for one confrontation")
    bad("cse:bad_conf_unknown_decision", ["eth:Confrontation"],
        merge(base_conf, {"eth:decision": "eth:Decision_MAYBE"}),
        "sh:ConfrontationShape", "verdict outside the ladder")
    bad("cse:bad_conf_level_above_one", ["eth:Confrontation"], merge(base_conf, {"eth:levelW": "1.20"}),
        "sh:ConfrontationShape", "pillar level above 1")
    bad("cse:bad_conf_no_case", ["eth:Confrontation"], merge(base_conf, {"eth:confrontationCase": None}),
        "sh:ConfrontationShape", "confrontation not linked to a case")
    bad("cse:bad_conf_no_calibration", ["eth:Confrontation"], merge(base_conf, {"eth:appliedCalibration": None}),
        "sh:ConfrontationShape", "confrontation without a calibration")
    bad("cse:bad_conf_negative_deficit", ["eth:Confrontation"], merge(base_conf, {"eth:deficitW": "-0.10"}),
        "sh:ConfrontationShape", "negative pillar deficit")
    bad("cse:bad_conf_S4_above_S3", ["eth:Confrontation"],
        merge(base_conf, {"eth:structuralTermS3": "0.05", "eth:slackS3minusS4": "-0.05"}),
        "sh:ConfrontationShape", "cell term exceeds the face term")
    bad("cse:bad_conf_sigma_above_max", ["eth:Confrontation"], merge(base_conf, {"eth:sigmaFloor": "0.45"}),
        "sh:ConfrontationShape", "prudential floor above the declared maximum")
    bad("cse:bad_conf_risk_increases", ["eth:Confrontation"], merge(base_conf, {"eth:riskAttenuation": "-0.10"}),
        "sh:ConfrontationShape", "residual risk above the consequence mass")
    bad("cse:bad_conf_low_coverage", ["eth:Confrontation"], merge(base_conf, {"eth:coverage": "0.40"}),
        "sh:ConfrontationShape", "profile covers less than 70% of the facets")
    bad("cse:bad_conf_failure_probability", ["eth:Confrontation"],
        merge(base_conf, {"eth:failureProbability": "0.99"}),
        "sh:ConfrontationShape", "failure probability above the clamped maximum")
    bad("cse:bad_conf_no_guard_count", ["eth:Confrontation"], merge(base_conf, {"eth:guardFailureCount": None}),
        "sh:ConfrontationShape", "no guard-failure count recorded")

    bad("norm:bad_norm_no_pillar", ["eth:Norm", "eth:Obligation"],
        {"rdfs:label": '"bad norm"', "eth:normLabel": '"internal memo"',
         "eth:normStatement": '"document the rationale for every automated decision"',
         "eth:normClass": '"internal_policy"', "eth:anchorsFacet": "fac:W1",
         "eth:appliesToDomain": "eth:domain_GP", "eth:priorityEngine": "eth:Priority_3",
         "eth:defeasibility": "eth:Def_scope", "eth:instrument": "norm:inst_OECD_public_integrity",
         "eth:isAbsolute": "false", "eth:hasUnresolvedConflict": "false", "eth:dutyStrength": "0.7"},
        "sh:NormShape", "norm that targets no pillar")
    bad("norm:bad_norm_no_instrument", ["eth:Norm", "eth:Obligation"],
        {"rdfs:label": '"bad norm 2"', "eth:normLabel": '"internal memo"',
         "eth:normStatement": '"document the rationale for every automated decision"',
         "eth:normClass": '"internal_policy"', "eth:targetsPillar": "eth:pillar_K",
         "eth:anchorsFacet": "fac:K3", "eth:appliesToDomain": "eth:domain_GP",
         "eth:priorityEngine": "eth:Priority_3", "eth:defeasibility": "eth:Def_scope",
         "eth:isAbsolute": "false", "eth:hasUnresolvedConflict": "false", "eth:dutyStrength": "0.7"},
        "sh:NormShape", "obligation with no instrument behind it")
    bad("norm:bad_prohibition_no_defeasibility", ["eth:Norm", "eth:Prohibition"],
        {"rdfs:label": '"bad prohibition"', "eth:normLabel": '"internal memo"',
         "eth:normStatement": '"do not deploy a model that has not been evaluated"',
         "eth:normClass": '"internal_policy"', "eth:targetsPillar": "eth:pillar_M",
         "eth:anchorsFacet": "fac:M1", "eth:appliesToDomain": "eth:domain_TS",
         "eth:priorityEngine": "eth:Priority_1", "eth:isAbsolute": "true",
         "eth:hasUnresolvedConflict": "false",
         "eth:breachConsequence": '"the deployment is suspended"'},
        "sh:NormShape", "prohibition with no defeasibility declared")
    bad("norm:bad_prohibition_no_consequence", ["eth:Norm", "eth:Prohibition"],
        {"rdfs:label": '"bad prohibition 2"', "eth:normLabel": '"internal memo"',
         "eth:normStatement": '"do not deploy a model that has not been evaluated"',
         "eth:normClass": '"internal_policy"', "eth:targetsPillar": "eth:pillar_M",
         "eth:anchorsFacet": "fac:M1", "eth:appliesToDomain": "eth:domain_TS",
         "eth:priorityEngine": "eth:Priority_1", "eth:defeasibility": "eth:Def_none",
         "eth:instrument": "norm:inst_OECD_public_integrity", "eth:isAbsolute": "true",
         "eth:hasUnresolvedConflict": "false"},
        "sh:ProhibitionShape", "prohibition with no declared consequence")
    bad("norm:bad_permission_no_scope", ["eth:Norm", "eth:Permission"],
        {"rdfs:label": '"bad permission"', "eth:normLabel": '"internal memo"',
         "eth:normStatement": '"automate decisions that are necessary for the contract"',
         "eth:normClass": '"internal_policy"', "eth:targetsPillar": "eth:pillar_W",
         "eth:anchorsFacet": "fac:W1", "eth:appliesToDomain": "eth:domain_FI",
         "eth:priorityEngine": "eth:Priority_3", "eth:defeasibility": "eth:Def_conflict",
         "eth:instrument": "norm:inst_GDPR_Art22", "eth:isAbsolute": "false",
         "eth:hasUnresolvedConflict": "false"},
        "sh:PermissionShape", "permission with no scope")
    bad("norm:bad_conflict_one_norm", ["eth:NormConflict"],
        {"rdfs:label": '"conflict with a single norm"',
         "eth:conflictPatternClass": "eth:Pattern_legal_ethical",
         "eth:firstNorm": "norm:UDHR_Art3_O1", "eth:appliesToDomain": "eth:domain_SA",
         "eth:resolutionStrategy": "eth:Strategy_priority", "eth:conflictPriority": "eth:Priority_1",
         "eth:conflictSeverity": "0.45", "eth:conflictResolved": "true", "eth:conflictStatus": '"resolved"',
         "eth:conflictAffectsPillar": "eth:pillar_M"},
        "sh:NormConflictShape", "conflict with only one norm in the pair")
    bad("norm:bad_conflict_no_resolution", ["eth:NormConflict"],
        {"rdfs:label": '"conflict with no way out"', "eth:conflictPatternClass": "eth:Pattern_short_long",
         "eth:firstNorm": "norm:UDHR_Art3_O1", "eth:secondNorm": "norm:UDHR_Art3_P1",
         "eth:appliesToDomain": "eth:domain_SA", "eth:conflictSeverity": "0.45",
         "eth:conflictResolved": "false", "eth:conflictStatus": '"unresolved_escalation"',
         "eth:conflictAffectsPillar": "eth:pillar_W"},
        "sh:NormConflictShape", "conflict with neither a strategy nor a priority")
    bad("norm:bad_conflict_unknown_status", ["eth:NormConflict"],
        {"rdfs:label": '"conflict with an undefined status"',
         "eth:conflictPatternClass": "eth:Pattern_autonomy_benefit",
         "eth:firstNorm": "norm:UDHR_Art3_O1", "eth:secondNorm": "norm:UDHR_Art3_P1",
         "eth:appliesToDomain": "eth:domain_SA", "eth:resolutionStrategy": "eth:Strategy_priority",
         "eth:conflictPriority": "eth:Priority_2", "eth:conflictSeverity": "0.45",
         "eth:conflictResolved": "true", "eth:conflictStatus": '"pending"',
         "eth:conflictAffectsPillar": "eth:pillar_W"},
        "sh:NormConflictShape", "conflict status outside the declared set")

    bad("ag:bad_agent_no_layer", ["eth:Agent"],
        {"rdfs:label": '"agent with no layer"', "eth:agentId": '"AGENT-BAD-1"',
         "eth:personaType": '"guard_fragile"', "eth:attainmentFactorW": "1.0",
         "eth:attainmentFactorC": "1.0", "eth:attainmentFactorM": "1.0", "eth:attainmentFactorK": "1.0",
         "eth:jitter": "0.0", "eth:confidenceMean": "0.85", "eth:fallbackPolicy": "eth:Fallback_human_review"},
        "sh:DelegationShape", "agent placed in no agency layer")
    bad("ag:bad_agent_factor_above_two", ["eth:Agent"],
        {"rdfs:label": '"agent claiming more than the requirement"', "eth:agentId": '"AGENT-BAD-2"',
         "eth:personaType": '"recoverable_failure"', "eth:agentLayer": "eth:Layer_model",
         "eth:attainmentFactorW": "2.5", "eth:attainmentFactorC": "1.0", "eth:attainmentFactorM": "1.0",
         "eth:attainmentFactorK": "1.0", "eth:jitter": "0.0", "eth:confidenceMean": "0.85",
         "eth:fallbackPolicy": "eth:Fallback_human_review"},
        "sh:DelegationShape", "attainment factor above 2")
    bad("ag:bad_agent_no_fallback", ["eth:Agent"],
        {"rdfs:label": '"agent with no fallback"', "eth:agentId": '"AGENT-BAD-3"',
         "eth:personaType": '"declared"', "eth:agentLayer": "eth:Layer_operator",
         "eth:attainmentFactorW": "1.0", "eth:attainmentFactorC": "1.0", "eth:attainmentFactorM": "1.0",
         "eth:attainmentFactorK": "1.0", "eth:jitter": "0.0", "eth:confidenceMean": "0.85"},
        "sh:DelegationShape", "agent with no fallback policy")
    bad("cse:bad_link_delegates_forbidden_duty", ["eth:ChainLink"],
        {"eth:delegatingAgent": "ag:bad_agent_1", "eth:delegateAgent": "ag:bad_agent_2",
         "eth:delegatedPillar": "eth:pillar_M", "eth:delegationConsistent": "false"},
        "sh:ChainLinkShape", "duty delegated to an agent forbidden to carry it")
    bad("ag:bad_chain_no_root", ["eth:DelegationChain"],
        {"rdfs:label": '"chain with no root"', "eth:delegationChainOf": "cse:bad_case_ok",
         "eth:chainLink": "cse:bad_link_delegates_forbidden_duty",
         "eth:fallbackForChain": "eth:Fallback_escalate_prohibited"},
        "sh:DelegationChainShape", "delegation chain with no root agent")
    bad("cse:bad_chain_no_weakest_link", ["eth:ConfrontationChain"],
        {"rdfs:label": '"chain without a weakest link"', "eth:chainCase": "cse:bad_case_ok",
         "eth:chainDecision": "eth:Decision_REVIEW_REQUIRED", "eth:chainAdequacyLow": "0.60",
         "eth:chainResidualRisk": "0.40", "eth:fallbackForChain": "eth:Fallback_human_review",
         "eth:layerResult": bnode_list([[f"a eth:ChainLayerResult", "eth:resultLayer eth:Layer_model",
                                        "eth:resultAdequacyLow 0.60",
                                        "eth:resultDecision eth:Decision_REVIEW_REQUIRED",
                                        "eth:resultResidualRisk 0.40"] for _ in range(3)])},
        "sh:ConfrontationChainShape", "layered chain without a weakest link")

    bad("eth:bad_drift_no_pillar", ["eth:DriftProfile"],
        {"rdfs:label": '"drift with no pillar"', "eth:driftRate": "0.03", "eth:driftSteps": "8",
         "eth:driftDirection": '"degrading"', "eth:observedFlips": "1", "eth:hysteresisApplies": "true"},
        "sh:DriftProfileShape", "drift profile with no pillar")
    bad("eth:bad_drift_rate_out_of_range", ["eth:DriftProfile"],
        {"rdfs:label": '"impossible drift"', "eth:driftPillar": "eth:pillar_K", "eth:driftRate": "2.0",
         "eth:driftSteps": "8", "eth:driftDirection": '"improving"', "eth:observedFlips": "0",
         "eth:hysteresisApplies": "true"},
        "sh:DriftProfileShape", "drift rate outside [-1, 1]")

    return "\n".join(out) + "\n", expectations


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "shapes"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "fixtures"), exist_ok=True)

    cases, personas = load_corpus()
    deontic_text, conflicts = emit_deontic()
    instances_text, stats, decisions = emit_instances(cases, personas, conflicts)
    invalid_text, expectations = emit_invalid()
    cal = default_calibration()

    files = {
        "01_core.ttl": emit_core(),
        "02_facets.ttl": emit_facets(),
        "03_deontic.ttl": deontic_text,
        "04_agency.ttl": emit_agency(),
        "05_dynamics.ttl": emit_dynamics(),
        "06_calibration.ttl": emit_calibration(cal, "core.default_calibration + B5' ladder fit"),
        "shapes/ontology_shapes.ttl": emit_shapes(),
        "fixtures/instances.ttl": instances_text,
        "fixtures/invalid_examples.ttl": invalid_text,
    }
    for name, text in files.items():
        with open(os.path.join(OUT, name), "w") as fh:
            fh.write(text)
    with open(os.path.join(OUT, "fixtures", "invalid_expectations.json"), "w") as fh:
        json.dump({"expectations": expectations}, fh, indent=2)

    report = {
        "generator": "_analysis/ontology/gen_ontology_v4.py",
        "version": VERSION,
        "files": {name: os.path.getsize(os.path.join(OUT, name)) for name in files},
        "counts": stats,
        "norm_conflicts": len(conflicts),
        "decision_distribution": decisions,
        "layers": {"cases_A": sum(1 for c in cases if c["layer"] == "A"),
                   "cases_B": sum(1 for c in cases if c["layer"] == "B")},
        "invalid_fixtures": len(expectations),
        "registry_check": validate_registry(),
    }
    with open(os.path.join(OUT, "generation_report.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
