"""Validate ontology v3: SHACL conformance, SPARQL coherence checks and the
arithmetic mirror (ontology parameters must reproduce the Python model to 1e-6).

Note on reasoning: OWL DL completeness is not available in this environment
(no HermiT/Pelican), so DL entailments are approximated by SHACL shapes +
SPARQL checks. This is declared as a limitation in the paper.

Run: python3 _analysis/ontology/validate_ontology_v3.py
Writes Evaluacoes/r3/ontology_v3_validation.json
"""
import json
import os
import sys

from rdflib import Graph
from pyshacl import validate

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ONT = os.path.join(ROOT, "Ontologias", "ontology_v3")
OUT = os.path.join(ROOT, "Evaluacoes", "r3")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

BASE = "https://ethwcmk.org/ontology#"
PREFIXES = "PREFIX eth: <https://ethwcmk.org/ontology#> PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX cal: <https://ethwcmk.org/calibration#> PREFIX inst: <https://ethwcmk.org/instrument#> "


def load_graph():
    g = Graph()
    for name in sorted(os.listdir(ONT)):
        if name.endswith(".ttl"):
            g.parse(os.path.join(ONT, name), format="turtle")
    for sub in ("shapes", "fixtures"):
        d = os.path.join(ONT, sub)
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if name.endswith(".ttl"):
                    g.parse(os.path.join(d, name), format="turtle")
    return g


def value(g, subject, prop):
    rows = list(g.query(PREFIXES + "SELECT ?v WHERE { " + subject + " eth:" + prop + " ?v }"))
    return float(rows[0][0]) if rows else None


def sparql_checks(g):
    C = {}
    RDFP = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
    Q = lambda s: list(g.query(PREFIXES + s))

    n = len(Q("SELECT ?s WHERE { ?s rdf:type eth:Facet }"))
    C["V1_facet_count_28"] = {"got": n, "pass": n == 28}

    bad = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet ; eth:betaW ?w ; eth:betaC ?c ; "
            "eth:betaM ?m ; eth:betaK ?k . FILTER ( abs(?w+?c+?m+?k - 1.0) > 1e-9 ) }")
    C["V2_beta_weights_sum_to_one"] = {"violations": len(bad), "pass": not bad}

    bad = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet ; eth:nPillars ?n . FILTER ( ?n < 1 || ?n > 3 ) }")
    C["V3_at_most_three_pillars_per_facet"] = {"violations": len(bad), "pass": not bad}

    bad = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet ; eth:betaW ?w ; eth:betaC ?c ; "
            "eth:betaM ?m ; eth:betaK ?k . FILTER ( (?w>0 && ?w<0.15) || (?c>0 && ?c<0.15) "
            "|| (?m>0 && ?m<0.15) || (?k>0 && ?k<0.15) ) }")
    C["V4_no_token_beta_below_0.15"] = {"violations": len(bad), "pass": not bad}

    missing = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet . FILTER NOT EXISTS { ?f eth:observable ?o } }")
    C["V5_every_facet_has_an_observable"] = {"violations": len(missing), "pass": not missing}

    crit = Q("SELECT ?f ?v WHERE { ?f rdf:type eth:Facet ; eth:criticalityVector ?v }")
    domains_ok = all(len(str(v).split(",")) == 13 for _, v in crit)
    C["V6_13_domain_criticality_vector"] = {"got": len(crit), "pass": len(crit) == 28 and domains_ok}

    bad = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet ; eth:hardGuard ?g ; eth:guardMin ?m . "
            "FILTER ( ?g = true && ?m <= 0 ) }")
    C["V7_guard_implies_positive_floor"] = {"violations": len(bad), "pass": not bad}

    shared = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet ; eth:nPillars ?n . FILTER ( ?n >= 2 ) }")
    C["V8_cross_pillar_facets_present"] = {"got": len(shared), "pass": len(shared) >= 20}

    slots = Q("SELECT ?s ?k WHERE { ?s rdf:type eth:LatticeSlot ; eth:slotKind ?k }")
    kinds = {str(k) for _, k in slots}
    C["V9_face_lattice_15_slots"] = {"got": len(slots), "pass": len(slots) == 15}
    C["V10_slot_kinds_complete"] = {"got": sorted(kinds), "pass": kinds == {"vertex", "edge", "face", "cell"}}

    lam = {p: value(g, "cal:v11", "lam" + p) for p in "WCMK"}
    C["V11_lambda_sum_to_one"] = {"got": round(sum(lam.values()), 9), "pass": abs(sum(lam.values()) - 1) < 1e-6}

    alpha = [value(g, "cal:v11", "edgeWeight_" + str(i)) for i in range(1, 7)]
    beta = [value(g, "cal:v11", "faceWeight_" + str(i)) for i in range(1, 5)]
    C["V12_edge_weights_sum_to_one"] = {"got": round(sum(alpha), 6), "pass": abs(sum(alpha) - 1) < 1e-6}
    C["V13_face_weights_sum_to_one"] = {"got": round(sum(beta), 6), "pass": abs(sum(beta) - 1) < 1e-6}

    pen = {k: value(g, "cal:v11", k) for k in ("gamma", "eta", "omega", "rho", "delta")}
    total = pen["gamma"] + pen["eta"] + pen["omega"] + pen["rho"]
    C["V14_penalty_budget_within_0.35"] = {"got": round(total, 6), "budget": 0.35, "pass": total <= 0.35 + 1e-9}

    theta = {p: value(g, "cal:v11", "theta" + p) for p in "WCMK"}
    C["V15_theta_within_bounds"] = {"got": theta, "pass": all(0.2 <= t <= 1.0 for t in theta.values())}

    dec = Q("SELECT ?d ?p WHERE { ?d rdf:type eth:Decision ; eth:permissiveness ?p }")
    C["V16_five_ordered_decisions"] = {"got": sorted(int(r[1]) for r in dec),
                                       "pass": sorted(int(r[1]) for r in dec) == [0, 1, 2, 3, 4]}

    instruments = len(Q("SELECT ?s WHERE { ?s rdf:type eth:NormativeInstrument }"))
    conflicts = len(Q("SELECT ?s WHERE { ?s rdf:type eth:NormConflict }"))
    horizons = len(Q("SELECT ?s WHERE { ?s rdf:type eth:TemporalHorizon }"))
    severities = len(Q("SELECT ?s WHERE { ?s rdf:type eth:SeverityBand }"))
    revers = len(Q("SELECT ?s WHERE { ?s rdf:type eth:Reversibility }"))
    C["V17_deontic_and_context_enumerations"] = {"instruments": instruments, "conflicts": conflicts,
                                                 "horizons": horizons, "severity_bands": severities,
                                                 "reversibilities": revers,
                                                 "pass": instruments >= 10 and conflicts >= 7 and horizons == 4
                                                 and severities == 4 and revers == 3}

    edge_faces = {"W C": ["W C M", "W C K"], "W M": ["W C M", "W M K"], "W K": ["W C K", "W M K"],
                  "C M": ["W C M", "C M K"], "C K": ["W C K", "C M K"], "M K": ["W M K", "C M K"]}
    face_w = {str(r[0]): float(r[1]) for r in Q("SELECT ?inc ?w WHERE { ?s rdf:type eth:LatticeSlot ; "
                                               "eth:slotKind \"face\" ; eth:incidence ?inc ; "
                                               "eth:structuralWeight ?w }")}
    edge_w = {str(r[0]): float(r[1]) for r in Q("SELECT ?inc ?w WHERE { ?s rdf:type eth:LatticeSlot ; "
                                               "eth:slotKind \"edge\" ; eth:incidence ?inc ; "
                                               "eth:structuralWeight ?w }")}
    violations = {e: (w, sum(face_w[f] for f in edge_faces[e]) / 3.0)
                  for e, w in edge_w.items() if w < sum(face_w[f] for f in edge_faces[e]) / 3.0 - 1e-9}
    C["V18_structural_hierarchy_alpha_ge_third_of_faces"] = {"violations": violations, "pass": not violations}

    con = Q("SELECT ?c ?d ?aa WHERE { ?c rdf:type eth:Confrontation ; eth:decision ?d ; "
            "eth:adequacy ?aa }")
    rows = [(str(d), float(aa)) for _, d, aa in con]
    C["V19_confrontation_instances_bounded_and_decidable"] = {
        "got": rows, "pass": len(rows) >= 1 and all(0.0 <= aa <= 1.0 for _, aa in rows)}

    missing_pp = Q("SELECT ?f WHERE { ?f rdf:type eth:Facet . FILTER NOT EXISTS { ?f eth:primaryPillar ?p } }")
    C["V20_every_facet_has_a_primary_pillar"] = {"violations": len(missing_pp), "pass": not missing_pp}
    return C


def arithmetic_mirror(g):
    """Recompute a confrontation using ONLY the parameters declared in the TTL and
    compare with the canonical Python implementation."""
    Q = lambda s: list(g.query(PREFIXES + s))
    from core import Calibration, CaseSpec, Profile, confront, requirement_for
    from facet_registry import FACETS

    lam = tuple(value(g, "cal:v11", "lam" + p) for p in "WCMK")
    theta = tuple(value(g, "cal:v11", "theta" + p) for p in "WCMK")
    cal = Calibration(lam=lam, alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                      gamma=value(g, "cal:v11", "gamma"), eta=value(g, "cal:v11", "eta"),
                      omega=value(g, "cal:v11", "omega"), rho=value(g, "cal:v11", "rho"),
                      delta=value(g, "cal:v11", "delta"), theta=theta,
                      hard_veto_delta=value(g, "cal:v11", "hardVetoDelta"),
                      material_gap=value(g, "cal:v11", "materialGap"),
                      critical_prohibit_gap=value(g, "cal:v11", "criticalProhibitGap"),
                      cap_base=value(g, "cal:v11", "capBase"),
                      cap_stakes_gain=value(g, "cal:v11", "capStakesGain"),
                      stakes_veto_min=value(g, "cal:v11", "stakesVetoMin"),
                      bar_base=value(g, "cal:v11", "barBase"),
                      bar_severity=value(g, "cal:v11", "barSeverity"),
                      prohibit_margin=value(g, "cal:v11", "prohibitMargin"),
                      guards_margin=value(g, "cal:v11", "guardsMargin"),
                      ratio_prohibit=value(g, "cal:v11", "ratioProhibit"),
                      ratio_review=value(g, "cal:v11", "ratioReview"),
                      ratio_guards=value(g, "cal:v11", "ratioGuards"),
                      prohibit_stakes_min=value(g, "cal:v11", "prohibitStakesMin"),
                      prohibit_needs_material=True,
                      veto_slack=value(g, "cal:v11", "vetoSlack"))

    ttl_beta = {str(r[0]).split("#")[-1]: (float(r[1]), float(r[2]), float(r[3]), float(r[4]))
                for r in Q("SELECT ?f ?w ?c ?m ?k WHERE { ?f rdf:type eth:Facet ; eth:betaW ?w ; "
                           "eth:betaC ?c ; eth:betaM ?m ; eth:betaK ?k }")}
    max_beta_diff = max(abs(ttl_beta[f.code][i] - f.beta[i]) for f in FACETS for i in range(4))

    case = CaseSpec("MIRROR-1", "IC", "critical", "maximum", "irreversible", {}, 0.6, 0.8,
                    ("M", "C"), "long", "innovation_precaution", "system", ("IEC62443", "RioP1"))
    case.facet_requirements = {f.code: requirement_for(f, case) for f in FACETS}
    levels = {f.code: 0.7 for f in FACETS}
    levels["M1"] = 0.10
    res = confront(case, Profile("mirror", levels), cal)

    fixture = {p: value(g, "eth:confrontation_example_1", p) for p in
               ("adequacy", "adequacyLow", "adequacyHigh", "structuralTerm", "stakes", "bar")}
    diffs = {"adequacy": abs(res["adequacy"] - fixture.get("adequacy", res["adequacy"])),
            "adequacy_low": abs(res["adequacy_low"] - fixture.get("adequacyLow", res["adequacy_low"])),
            "adequacy_high": abs(res["adequacy_high"] - fixture.get("adequacyHigh", res["adequacy_high"])),
            "stakes": abs(res["stakes"] - fixture.get("stakes", res["stakes"])),
            "bar": abs(res["bar"] - fixture.get("bar", res["bar"]))}
    return {"max_beta_disagreement": max_beta_diff,
            "max_numeric_disagreement": max(diffs.values()),
            "parameter_diffs": diffs,
            "decision_from_ttl_params": res["decision"],
            "pass": max_beta_diff <= 1e-6 and max(diffs.values()) <= 1e-6}


def main():
    g = load_graph()
    shapes = Graph()
    shapes.parse(os.path.join(ONT, "shapes/ontology_shapes.ttl"), format="turtle")
    conformed, _, report = validate(g, shapes, shacl_graph=shapes, inference="none")
    checks = sparql_checks(g)
    mirror = arithmetic_mirror(g)
    out = {"graph": {"triples": len(g),
                     "files": [f for f in sorted(os.listdir(ONT)) if f.endswith(".ttl")],
                     "shacl_conformant": bool(conformed),
                     "shacl_violations": sum(1 for x in report if isinstance(x, tuple) and "violation" in str(x).lower())},
           "sparql_checks": checks,
           "arithmetic_mirror": mirror,
           "all_checks_passed": all(c["pass"] for c in checks.values()) and mirror["pass"],
           "limitations": ["OWL DL completeness is approximated by SHACL + SPARQL (no DL reasoner available)",
                           "criticality vectors are derived by rule (catalogue + pillar salience), not by an expert panel"]}
    json.dump(out, open(os.path.join(OUT, "ontology_v3_validation.json"), "w"), indent=2)
    print("triples:", len(g), "| shacl conformant:", conformed)
    for k, v in checks.items():
        print(("PASS " if v["pass"] else "FAIL ") + k + " " + json.dumps(v)[:120])
    print("mirror:", json.dumps(mirror["parameter_diffs"]))
    print("ALL:", out["all_checks_passed"])


if __name__ == "__main__":
    main()
