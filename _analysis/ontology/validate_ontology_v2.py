"""F3 validation harness: SHACL conformance + SPARQL coherence checks (V1-V14).

Run:  python3 _analysis/ontology/validate_ontology_v2.py
Writes: Evaluacoes/r2/ontology_v2_validation.json
"""
import json, os
from collections import Counter
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
from pyshacl import validate

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ONT = os.path.join(ROOT, "Ontologias", "ontology_v2")
LEGACY = os.path.join(ROOT, "Ontologias")
BASE = "https://ethwcmk.org/ontology/"
SH = Namespace("http://www.w3.org/ns/shacl#")
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "formal_core")))
from facet_registry import DOMAINS


def load(paths, root=ONT):
    G = Graph()
    for p in paths:
        G.parse(os.path.join(root, p), format="turtle")
    return G


def n_results(report_graph):
    return len(list(report_graph.subjects(RDF.type, SH["ValidationResult"]))), [
        {"path": str(report_graph.value(r, SH["path"])),
         "focus": str(report_graph.value(r, SH["focusNode"])),
         "value": str(report_graph.value(r, SH["value"]))}
        for r in report_graph.subjects(RDF.type, SH["ValidationResult"])]


def main():
    data = load(MODULES := ["01_core.ttl", "02_facets.ttl", "03_domains_context.ttl",
                            "04_pillars_lattice.ttl", "05_calibration.ttl", "06_decisions.ttl"]
                ) + load(["fixtures/instance_valid.ttl"])
    shapes = load(["shapes/facet_and_context_shapes.ttl"])
    report = {"battery": "V-ontology",
              "triples": {m: len(load([m])) for m in MODULES + ["shapes/facet_and_context_shapes.ttl"]},
              "data_triples_valid": len(data)}

    conf, rep, _ = validate(data, shacl_graph=shapes)
    cnt, items = n_results(rep)
    report["shacl_valid_instance"] = {"conformant": conf, "violations": cnt}

    bad = load(MODULES) + load(["fixtures/instance_invalid.ttl"])
    conf2, rep2, _ = validate(bad, shacl_graph=shapes)
    cnt2, items2 = n_results(rep2)
    report["shacl_invalid_instance"] = {"conformant": conf2, "violations": cnt2, "detected": items2}

    checks = []

    def sparql(name, query, expect=0):
        rows = list(data.query(query))
        checks.append({"id": name, "bad_rows": len(rows), "expected": expect,
                       "pass": len(rows) == expect, "sample": [str(r) for r in rows[:4]]})

    sparql("V1_beta_sum_equals_1", """
        SELECT ?f WHERE { ?f eth:betaWant ?w. ?f eth:betaCan ?c.
                          ?f eth:betaMust ?m. ?f eth:betaKnow ?k.
        FILTER ( ?w + ?c + ?m + ?k > 1.000001 || ?w + ?c + ?m + ?k < 0.999999 ) }""")

    for p in ("Want", "Can", "Must", "Know"):
        n = len(list(data.query(f"SELECT ?f WHERE {{ pillar:{p} eth:contributedBy ?f }}")))
        checks.append({"id": f"V2_pillar_{p}_has_facets", "n_facets": n, "pass": n >= 1})

    n_facets = len(list(data.query("SELECT ?f WHERE { ?f a eth:Facet }")))
    n_ind = len(list(data.query("SELECT ?f WHERE { ?f a owl:NamedIndividual }")))
    n_classes = len(list(data.query("SELECT ?c WHERE { ?c a owl:Class }"))
    )
    checks.append({"id": "V3_facets_are_individuals_not_classes", "facets": n_facets,
                   "named_individuals": n_ind, "declared_classes": n_classes,
                   "pass": n_facets == 26 and n_ind >= 26})

    codes = [str(r[0]) for r in data.query("SELECT ?c WHERE { ?f eth:facetCode ?c }")]
    checks.append({"id": "V4_facet_codes_unique", "n": len(codes), "distinct": len(set(codes)),
                   "pass": len(codes) == 26 and len(set(codes)) == 26})

    slots = list(data.query("SELECT ?s ?a WHERE { ?s eth:slotArity ?a }"))
    arities = Counter(int(a) for _, a in slots)
    checks.append({"id": "V5_face_lattice_complete", "slots": len(slots), "by_arity": dict(arities),
                   "pass": len(slots) == 15 and arities[1] == 4 and arities[2] == 6
                           and arities[3] == 4 and arities[4] == 1})

    guards_bad = len(list(data.query("""
        SELECT ?f WHERE { ?f eth:hasGuard true. ?f eth:guardMin ?g.
        FILTER ( ?g < 0.30 || ?g > 0.90 ) }""")))
    guard_missing = len(list(data.query("""
        SELECT ?f WHERE { ?f eth:hasGuard true. FILTER NOT EXISTS { ?f eth:guardMin ?g } }""")))
    guard_spurious = len(list(data.query("""
        SELECT ?f WHERE { ?f eth:hasGuard false. ?f eth:guardMin ?g }""")))
    checks.append({"id": "V6_guard_consistency", "bad_values": guards_bad,
                   "missing_threshold": guard_missing,
                   "threshold_on_unguarded_facet": guard_spurious,
                   "pass": guards_bad == 0 and guard_missing == 0 and guard_spurious == 0})

    decisions = list(data.query("SELECT ?d ?r WHERE { ?d eth:permissivenessRank ?r }"))
    ranks = sorted(int(r) for _, r in decisions)
    checks.append({"id": "V7_decision_vocabulary_closed_ordered", "n": len(decisions),
                   "ranks": ranks, "pass": ranks == [0, 1, 2, 3, 4]})

    lam_bad = len(list(data.query("""
        SELECT ?c WHERE { ?c cal:lambdaWant ?a. ?c cal:lambdaCan ?b.
                          ?c cal:lambdaMust ?d. ?c cal:lambdaKnow ?e.
        FILTER ( ?a + ?b + ?d + ?e > 1.000001 ) }""")))
    budget_bad = len(list(data.query("""
        SELECT ?c WHERE { ?c cal:gamma ?g. ?c cal:eta ?e. ?c cal:omega ?o.
                          ?c cal:rho ?r. ?c cal:penaltyBudget ?b.
        FILTER ( ?g + ?e + ?o + ?r > ?b + 0.000001 ) }""")))
    checks.append({"id": "V8_calibration_normalisation", "lambda_sum_not_1": lam_bad,
                   "budget_exceeded": budget_bad, "pass": lam_bad == 0 and budget_bad == 0})

    arith = list(data.query("SELECT ?c ?a ?r ?f WHERE { ?c eth:adequacy ?a. "
                            "?c eth:residualRisk ?r. ?c eth:riskFloor ?f }"))
    bad_arith = [str(c) for c, a, r, f in arith
                 if abs(float(r) - (0.82 * (1 - float(a)) + float(f))) > 1e-3]
    checks.append({"id": "V9_risk_arithmetic_recomputable", "confrontations": len(arith),
                   "inconsistent": len(bad_arith), "pass": len(bad_arith) == 0,
                   "formula": "R_r = R_c(1 - Aa) + sigma * R_c"})

    veto_bad = len(list(data.query("""
        SELECT ?c WHERE { ?c eth:vetoPillar ?p. ?c eth:pillarDeficit ?d.
        FILTER ( ?d < 0.40 ) }""")))
    checks.append({"id": "V10_veto_pillars_qualify", "violations": veto_bad, "pass": veto_bad == 0})

    domains = len(list(data.query("SELECT ?d WHERE { ?d a eth:Domain }")))
    cells = len(list(data.query("SELECT ?x WHERE { ?x a eth:FacetDomainCriticality }")))
    per_domain = {d: len(list(data.query(
        f"SELECT ?x WHERE {{ ?x eth:criticalityInDomain domain:{d}. "
        f"?x eth:criticalityLevel ?l FILTER (?l = 4) }}"))) for d in DOMAINS}
    checks.append({"id": "V11_domain_coverage_complete", "domains": domains, "cells": cells,
                   "expected_cells": 26 * 13,
                   "domains_without_level4_facets": [d for d, n in per_domain.items() if n == 0],
                   "pass": domains == 13 and cells == 26 * 13 and all(n > 0 for n in per_domain.values())})

    dangling = len(list(data.query("""
        SELECT ?x ?f WHERE { ?x eth:requiresFacet ?f.
        FILTER NOT EXISTS { ?f a eth:Facet } }""")))
    dangling2 = len(list(data.query("""
        SELECT ?x ?f WHERE { ?x eth:levelOfFacet ?f.
        FILTER NOT EXISTS { ?f a eth:Facet } }""")))
    checks.append({"id": "V12_no_dangling_facet_references", "bad_requirements": dangling,
                   "bad_levels": dangling2, "pass": dangling == 0 and dangling2 == 0})

    req_codes = set(str(r[0]) for r in data.query(
        "SELECT ?c WHERE { ?x eth:requiresFacet ?f. ?f eth:facetCode ?c }"))
    checks.append({"id": "V13_requirement_coverage", "distinct_facets": len(req_codes),
                   "coverage": round(len(req_codes) / 26, 4), "pass": len(req_codes) == 26})

    shape_bad = len(list(data.query("""
        SELECT ?p WHERE { ?p eth:shapeWant ?a. ?p eth:shapeCan ?b.
                          ?p eth:shapeMust ?c. ?p eth:shapeKnow ?d.
        FILTER ( ?a + ?b + ?c + ?d > 1.000001 || ?a + ?b + ?c + ?d < 0.999999 ) }""")))
    checks.append({"id": "V14_profile_shape_normalised", "violations": shape_bad,
                   "pass": shape_bad == 0})

    # V15 - penalty-budget closure: gamma+eta+omega+rho+delta <= declared budget
    q15 = """
    SELECT ?c ?g ?e ?o ?r ?d ?b
    WHERE {
      ?c a eth:Calibration ; eth:gamma ?g ; eth:eta ?e ; eth:omega ?o ;
         eth:rho ?r ; eth:delta ?d ; eth:penaltyBudget ?b .
    }
    """
    bad_budget = []
    for row in data.query(q15):
        tot = sum(float(x) for x in (row.g, row.e, row.o, row.r, row.d))
        if tot > float(row.b) + 1e-9:
            bad_budget.append({"calibration": str(row.c), "total": round(tot, 4),
                              "budget": float(row.b)})
    checks.append({"id": "V15_penalty_budget_closure", "violations": bad_budget,
                   "pass": not bad_budget})

    # V16 - veto thresholds are in [0,1] and the hard-veto delta is positive
    q16 = """
    SELECT ?c ?tw ?tc ?tm ?tk ?hd
    WHERE { ?c a eth:Calibration ; eth:vetoThresholdWant ?tw ; eth:vetoThresholdCan ?tc ;
             eth:vetoThresholdMust ?tm ; eth:vetoThresholdKnow ?tk ; eth:hardVetoDelta ?hd . }
    """
    bad_veto = []
    for row in data.query(q16):
        vals = [float(x) for x in (row.tw, row.tc, row.tm, row.tk, row.hd)]
        if any(v < 0 or v > 1 for v in vals[:4]) or vals[4] <= 0:
            bad_veto.append({"calibration": str(row.c), "values": vals})
    checks.append({"id": "V16_veto_thresholds_valid", "violations": bad_veto,
                   "pass": not bad_veto})

    # V17 - the decision bar is monotone in stakes (coefficients non-negative)
    q17 = """
    SELECT ?c ?b0 ?bs ?bi ?bp WHERE {
      ?c a eth:Calibration ; eth:barBase ?b0 ; eth:barSeverity ?bs ;
         eth:barIrreversibility ?bi ; eth:barPrudential ?bp . }
    """
    bar_rows = list(data.query(q17))
    bar_ok = all(all(float(x) >= 0 for x in (r.b0, r.bs, r.bi, r.bp)) for r in bar_rows)
    checks.append({"id": "V17_decision_bar_declared_and_non_negative",
                   "n_calibrations": len(bar_rows), "pass": bar_ok and len(bar_rows) >= 1})

    report["validations"] = checks
    report["all_validations_pass"] = all(c.get("pass") for c in checks)
    report["negative_fixture_detected"] = (not conf2) and cnt2 > 0

    legacy = []
    pairs = [("eth_extracted/eth/ethcase-facet-requirements.ttl",
              "eth_extracted/eth/ethcase-facet-requirements.shacl.ttl",
              "eth_extracted/eth/ethcase-facet-requirements-example-invalid.ttl"),
             ("wcmk_extracted/wcmk/bridge-wcmkplus.ttl",
              "wcmk_extracted/wcmk/wcmk-facets.shacl.ttl",
              "wcmk_extracted/wcmk/bridge-wcmkplus-scoring-example-invalid.ttl")]
    pairs += [("wcmk_extracted/wcmk/bridge-wcmkplus-scoring-example-invalid.ttl",
               "wcmk_extracted/wcmk/wcmk-assessment.shacl.ttl", None),
              ("wcmk_extracted/wcmk/bridge-wcmkplus-scoring-example-invalid.ttl",
               "wcmk_extracted/wcmk/wcmk-profile.shacl.ttl", None),
              ("wcmk_extracted/wcmk/bridge-wcmkplus-scoring-example-valid.ttl",
               "wcmk_extracted/wcmk/wcmk-assessment.shacl.ttl", None)]
    for dfile, sfile, extra in pairs:
        try:
            files = [dfile] + ([extra] if extra else [])
            D = load(files, root=LEGACY)
            S = load([sfile], root=LEGACY)
            ok, rep, _ = validate(D, shacl_graph=S)
            cnt, _items = n_results(rep)
            legacy.append({"data": dfile, "shapes": sfile, "conformant": ok, "violations": cnt})
        except Exception as exc:
            legacy.append({"data": dfile, "error": str(exc)})
    report["legacy_v1_reproduction"] = legacy

    out = os.path.join(ROOT, "Evaluacoes", "r2", "ontology_v2_validation.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print("valid instance:", report["shacl_valid_instance"])
    print("invalid instance:", report["shacl_invalid_instance"]["violations"], "violations")
    print("all validations pass:", report["all_validations_pass"])
    for c in checks:
        print(" ", c["id"], "->", c["pass"])
    print("legacy:", report["legacy_v1_reproduction"])
    print("wrote", out)


if __name__ == "__main__":
    main()
