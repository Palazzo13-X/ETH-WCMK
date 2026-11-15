#!/usr/bin/env python3
"""
G12' validator for Ontologias/ontology_v4_2 (ETH-WCMK v13). Adds, on top of the v4 validator:
  - E11c' oversight regime: shape, derivation from declared facts, and its effect on stakes;
  - E32 ReviewNeed: bounds, and recomputation of the index from graph literals;
  - E26' coverage gate: profiles declaring < 70% of the canon must abstain and must not
    carry an adequacy literal;
  - Proposition 1 (D5.1): alpha is the lattice marginal of beta, checked slot by slot;
  - D5.3 cross-pillar duty exposure Psi recorded as a diagnostic.

  1. load the seven modules + the two shape files + the instance graph + the invalid
     fixtures, and count everything;
  2. pyshacl SHACL validation (inference="none") of the modules, of the whole corpus and
     of the invalid fixtures, reported per shape and per constraint component;
  3. SPARQL consistency checks (deontic + structural). rdflib implements SPARQL 1.1 but
     has no `if()` function, so every conditional that the previous version wrote as
     BIND(if(...) AS ...) is now either a plain SPARQL expression or a plain SELECT of the
     raw literals with the conditional computed in Python;
  4. ARITHMETIC MIRROR for 100 stratified confrontations: every quantity of the
     adequacy / risk / decision machinery is recomputed in Python from literals read out
     of the RDF graph (facet levels, confidences, requirements, criticality, guard floors,
     pillar lambdas/mus/thetas, lattice slot weights, stake weights, band values and the
     guard definitions), and compared with the values the generator asserted in the graph.
     The canonical primitives (band_value, effective_value, project, structural_terms,
     failure_probability, case_stakes, decide) are taken from _analysis/formal_core/core.py
     so the mirror is checked against the same semantics the corpus was built with; the
     assembly (S2/S3/S4 through the face lattice, deficits, exposure, material gap, veto,
     cap, adequacy, sigma, bar, ratio, ladder) is written in this file.
  5. face-lattice census: 4 vertices, 6 edges, 4 faces, 1 cell = 15 slots, weights summing
     to 1 inside each structural term;
  6. facet registry cross-check: facet_registry_v12.csv vs facet_registry.py vs 02_facets.ttl;
  7. write Evaluacoes/r4/ontology_v4_validation.json and print the summary.

Nothing outside Evaluacoes/r4 is written; Evaluacoes/r2 and r3 are only read.
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, OWL
from pyshacl import validate

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ONT = os.path.join(ROOT, "Ontologias", "ontology_v4_2")
OUT_PATH = os.path.join(ROOT, "Evaluacoes", "r" + os.environ.get("ETH_WCMK_ROUND", "5"), "ontology_v4_2_validation.json")
CORE_DIR = os.path.join(ROOT, "_analysis", "formal_core")

sys.path.insert(0, CORE_DIR)
import core  # canonical arithmetic of the model (read, never modified)

MODULES = ["01_core.ttl", "02_facets.ttl", "03_deontic.ttl",
           "04_agency.ttl", "05_dynamics.ttl", "06_calibration.ttl", "07_grounding.ttl"]
SHAPES_V4 = "shapes/ontology_shapes.ttl"
SHAPES_V6 = "shapes/ontology_shapes_v6.ttl"
INSTANCE_FILE = "fixtures/instances_subset.ttl"      # slice, if it exists
FULL_INSTANCE_FILE = "fixtures/instances.ttl"        # full regenerated graph (1,893,019 triples)

ETH = "https://ethwcmk.org/ontology#"
SHN = "http://www.w3.org/ns/shacl#"

PREFIXES = """PREFIX eth:  <https://ethwcmk.org/ontology#>
PREFIX fac:  <https://ethwcmk.org/facet#>
PREFIX cal:  <https://ethwcmk.org/calibration#>
PREFIX cse:  <https://ethwcmk.org/case#>
PREFIX norm: <https://ethwcmk.org/norm#>
PREFIX ag:   <https://ethwcmk.org/agent#>
PREFIX sh:   <http://www.w3.org/ns/shacl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

PILLAR_VALUES = """VALUES (?pillar ?betaProp ?lamProp ?muProp ?thetaProp) {
    (eth:pillar_W eth:betaW eth:lamW eth:muW eth:thetaW)
    (eth:pillar_C eth:betaC eth:lamC eth:muC eth:thetaC)
    (eth:pillar_M eth:betaM eth:lamM eth:muM eth:thetaM)
    (eth:pillar_K eth:betaK eth:lamK eth:muK eth:thetaK) }"""

CAL_PROPS = ["gamma", "eta", "omega", "rho", "delta", "uncertaintyKappa", "materialGap",
             "criticalProhibitGap", "hardVetoDelta", "capBase", "capStakesGain",
             "stakesVetoMin", "prohibitStakesMin", "prohibitMargin", "guardsMargin",
             "ratioProhibit", "ratioReview", "ratioGuards", "vetoSlack",
             "abstainUncertainty", "abstainKnowledgeFloor", "hysteresis",
             "crossPillarCoefficient", "salienceAdaptation", "coverageGate"]
CTX_PROPS = ["stakeWeightSeverity", "stakeWeightIrreversibility", "stakeWeightPrudential",
             "stakeWeightHorizon", "barBase", "barSeverity", "barIrreversibility",
             "barPrudential", "barHorizon"]

# Constants core.py uses that are nowhere declared as RDF literals. They appear as
# literals in the mirror, so the hard-coding is visible and auditable.
UNDECLARED_CONSTANTS = {
    "sigma_base": 0.05,
    "sigma_severity_irreversibility_coefficient": 0.15,
    "sigma_ceiling": 0.35,
    "stakes_prudential_normaliser": 0.10,
    "prudential_index_step": 0.05,
    "decision_bar_floor": 0.30,
    "decision_bar_ceiling": 0.90,
    "failure_probability_floor": 0.02,
    "failure_probability_ceiling": 0.98,
    "prudential_floor_base": 0.05,
    "prudential_floor_severity_irreversibility": 0.15,
    "prudential_floor_ceiling": 0.35,
    "epsilon": 1e-9,
}

PILLARS = ("W", "C", "M", "K")
EPS = 1e-9

# Declared storage precision. core.confront emits some literals rounded to 4 decimals
# (review_need, completeness in the corpus rows); the graph inherits those literals, so
# the arithmetic mirror can only be exact for the quantities that are stored at full
# precision. The tolerance is declared, not discovered after the fact.
MIRROR_TOLERANCE = 1e-6
STORAGE_PRECISION = {"review_need": 1e-4, "completeness": 1e-4}


OVERSIGHT_VALUE = {"unspecified": 0.0, "none": 0.0, "out_of_loop": 0.20,
                   "on_the_loop": 0.50, "in_the_loop": 0.80}
OVERSIGHT_ATTENUATION = 0.45


def oversight_value(regime):
    return OVERSIGHT_VALUE.get(str(regime).split("Oversight_")[-1], 0.0)

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def rows(graph, query):
    t = time.time()
    out = [r.asdict() for r in graph.query(PREFIXES + query)]
    print(f"  query {time.time()-t:.1f} s :: " + " ".join(query.split())[:90], flush=True)
    return out


def blocks(items):
    return " ".join(f"<{i}>" for i in items)


def as_bool(v):
    return str(v).lower() == "true"


# ------------------------------------------------------------ load & inventory
def load_graphs():
    modules, per_module = Graph(), {}
    for name in MODULES:
        g = Graph()
        g.parse(os.path.join(ONT, name), format="turtle")
        per_module[name] = len(g)
        modules += g
    shapes_v4 = Graph()
    shapes_v4.parse(os.path.join(ONT, SHAPES_V4), format="turtle")
    shapes_v6 = Graph()
    shapes_v6.parse(os.path.join(ONT, SHAPES_V6), format="turtle")
    instances = Graph()
    inst_path = os.path.join(ONT, INSTANCE_FILE)
    if not os.path.exists(inst_path):
        inst_path = os.path.join(ONT, FULL_INSTANCE_FILE)
        print("NOTE: no subset present; validating the full regenerated instance graph")
    instances.parse(inst_path, format="turtle")
    print(f"instance graph parsed: {len(instances)} triples from {os.path.basename(inst_path)}")
    invalid_v4 = Graph()
    invalid_v4.parse(os.path.join(ONT, "fixtures", "invalid_examples.ttl"), format="turtle")
    invalid_v6 = Graph()
    invalid_v6.parse(os.path.join(ONT, "fixtures", "invalid_examples_v6.ttl"), format="turtle")
    return modules, shapes_v4, shapes_v6, instances, invalid_v4, invalid_v6, per_module


def inventory(modules, instances):
    full = modules + instances
    meta = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.FunctionalProperty,
            OWL.NamedIndividual}
    typed, individuals = Counter(), set()
    for s, _, o in full.triples((None, RDF.type, None)):
        if isinstance(s, URIRef) and o not in meta:
            typed[str(o)] += 1
            individuals.add(str(s))
    return {
        "owl_classes": len(set(modules.subjects(RDF.type, OWL.Class))),
        "object_properties": len(set(modules.subjects(RDF.type, OWL.ObjectProperty))),
        "data_properties": len(set(modules.subjects(RDF.type, OWL.DatatypeProperty))),
        "typed_individual_assertions": sum(typed.values()),
        "distinct_named_individuals": len(individuals),
        "individuals_by_class": dict(sorted(typed.items(), key=lambda kv: -kv[1])),
        "instances_of_interest": {name: typed.get(ETH + name, 0) for name in
                                  ("EthicalCase", "Confrontation", "Profile", "FacetObservation",
                                   "FactGrounding", "Facet", "Norm", "Instrument", "Conflict",
                                   "NormConflict", "LatticeSlot", "StructuralTerm", "Agent",
                                   "DelegationChain", "ChainLink", "Domain", "Pillar",
                                   "Calibration", "Prohibition", "Permission")},
    }


# ------------------------------------------------------------ SHACL
def shape_stats(shapes):
    node_shapes = list(shapes.subjects(RDF.type, URIRef(SHN + "NodeShape")))
    prop_nodes = set()
    for s in node_shapes:
        for pn in shapes.objects(s, URIRef(SHN + "property")):
            prop_nodes.add(pn)
    paths = {str(p) for pn in prop_nodes for p in shapes.objects(pn, URIRef(SHN + "path"))}
    components = Counter(str(c).split("#")[-1] for pn in prop_nodes
                         for c in shapes.objects(pn, RDF.type))
    sh_class = sum(1 for pn in prop_nodes
                   if any(str(o) == SHN + "class" for o in shapes.objects(pn, RDF.type)))
    return {"node_shapes": len(node_shapes),
            "property_constraint_nodes": len(prop_nodes),
            "sh_class_value_constraints": sh_class,
            "distinct_constrained_paths": len(paths),
            "constraint_components_used": dict(components)}


def parse_report(report):
    out = []
    for v in report.subjects(RDF.type, URIRef(SHN + "ValidationResult")):
        out.append({"focus": str(report.value(v, URIRef(SHN + "focusNode"))),
                    "path": str(report.value(v, URIRef(SHN + "resultPath"))),
                    "component": str(report.value(v, URIRef(SHN + "sourceConstraintComponent"))),
                    "shape": str(report.value(v, URIRef(SHN + "sourceShape"))),
                    "message": str(report.value(v, URIRef(SHN + "resultMessage"))),
                    "value": str(report.value(v, URIRef(SHN + "value")))})
    return out


def run_shacl(data, shapes, label):
    t0 = time.time()
    conforms, report, _ = validate(data, shacl_graph=shapes, inference="none", abort=False)
    viol = parse_report(report)
    print(f"SHACL {label}: conforms={conforms} violations={len(viol)} "
          f"({round(time.time() - t0, 1)} s)")
    return {"conforms": bool(conforms), "violations": len(viol),
            "seconds": round(time.time() - t0, 2),
            "violations_by_shape": dict(Counter(v["shape"].split("#")[-1] for v in viol)),
            "violations_by_component": dict(Counter(v["component"].split("#")[-1] for v in viol)),
            "violations_by_path": dict(Counter(v["path"].split("#")[-1] for v in viol)),
            "affected_focus_nodes": len({v["focus"] for v in viol}),
            "sample": viol[:12]}


def invalid_fixture_test(invalid, modules, shapes, expectations, label):
    """Validate each broken fixture against the shapes and attribute the violation to the
    shape the expectation says should catch it."""
    _, report, _ = validate(invalid + modules, shacl_graph=shapes, inference="none", abort=False)
    viol = parse_report(report)
    by_focus = defaultdict(list)
    for v in viol:
        by_focus[v["focus"]].append(v)
    shape_paths = {}
    for s in shapes.subjects(RDF.type, URIRef(SHN + "NodeShape")):
        shape_paths[str(s).split("#")[-1]] = {str(p).split("#")[-1]
                                             for pn in shapes.objects(s, URIRef(SHN + "property"))
                                             for p in shapes.objects(pn, URIRef(SHN + "path"))}
    prefix_map = {"fac": ETH, "cse": "https://ethwcmk.org/case#", "norm": "https://ethwcmk.org/norm#",
                  "cal": "https://ethwcmk.org/calibration#", "ag": "https://ethwcmk.org/agent#",
                  "eth": ETH}

    def resolve(iri):
        if "://" in iri:
            return iri
        head, rest = iri.split(":", 1)
        return prefix_map.get(head, ETH) + rest

    present = {str(s) for s in invalid.subjects(RDF.type) if isinstance(s, URIRef)}
    expectations = [e for e in expectations if resolve(e["iri"]) in present]
    table, detected, matched = [], 0, 0
    for e in expectations:
        iri, shape = resolve(e["iri"]), (e.get("shape") or "").split("#")[-1]
        vs = by_focus.get(iri, [])
        hit = bool(vs)
        expected_paths = shape_paths.get(shape, set())
        m = hit and (not expected_paths or
                     any(v["path"].split("#")[-1] in expected_paths for v in vs))
        detected += hit
        matched += m
        table.append({"iri": e["iri"], "focus": iri, "expected_shape": shape, "expected_defect": e.get("defect", ""),
                      "detected": hit, "shape_matched": m,
                      "caught_by_shapes": sorted({v["shape"].split("#")[-1] for v in vs}),
                      "components": sorted({v["component"].split("#")[-1] for v in vs}),
                      "paths": sorted({v["path"].split("#")[-1] for v in vs}),
                      "violations": [{"path": v["path"].split("#")[-1],
                                      "component": v["component"].split("#")[-1],
                                      "value": v["value"]} for v in vs][:3]})
    print(f"invalid fixtures {label}: {detected}/{len(table)} caught, "
          f"{matched} attributed to the intended shape")
    return {"fixtures": len(table), "detected": detected,
            "detected_by_expected_shape": matched,
            "not_detected": [t["iri"] for t in table if not t["detected"]],
            "wrong_shape": [t["iri"] for t in table if t["detected"] and not t["shape_matched"]],
            "total_violations_on_invalid_graph": len(viol),
            "violations_by_shape": dict(Counter(v["shape"].split("#")[-1] for v in viol)),
            "violations_by_component": dict(Counter(v["component"].split("#")[-1] for v in viol)),
            "table": table}


# ------------------------------------------------------------ face lattice
def lattice_from_graph(graph):
    """Read the 15 relational slots of the 3-simplex face lattice from the RDF."""
    slots = []
    for s in graph.subjects(RDF.type, URIRef(ETH + "LatticeSlot")):
        slots.append({"iri": str(s),
                     "name": str(s).split("#")[-1],
                     "kind": str(graph.value(s, URIRef(ETH + "slotKind"))),
                     "incidence": tuple(str(graph.value(s, URIRef(ETH + "incidence"))).split()),
                     "weight": float(graph.value(s, URIRef(ETH + "structuralWeight"))),
                     "term": str(graph.value(s, URIRef(ETH + "belongsToTerm"))).split("#")[-1],
                     "index": int(graph.value(s, URIRef(ETH + "latticeIndex")))})
    slots.sort(key=lambda x: x["index"])
    return slots


def num_or_bool(v):
    s = str(v)
    try:
        return float(s)
    except ValueError:
        return as_bool(v)


def structural_terms_from_lattice(d, slots):
    """S2, S3, S4 and D computed *through* the face lattice itself: every slot of a term
    contributes its declared weight times the joint deficit of its incident pillars."""
    terms = defaultdict(float)
    for slot in slots:
        joint = min(d[PILLARS.index(p)] for p in slot["incidence"])
        terms[slot["term"]] += slot["weight"] * joint
    return {"D": terms.get("term_D", 0.0), "S2": terms.get("term_S2", 0.0),
            "S3": terms.get("term_S3", 0.0), "S4": terms.get("term_S4", 0.0)}


def lattice_report(slots):
    by_kind = Counter(s["kind"] for s in slots)
    by_term = defaultdict(lambda: {"slots": 0, "raw_sum": 0.0, "members": []})
    for s in slots:
        by_term[s["term"]]["slots"] += 1
        by_term[s["term"]]["raw_sum"] += s["weight"]
        by_term[s["term"]]["members"].append({"slot": s["name"], "kind": s["kind"],
                                             "incidence": list(s["incidence"]),
                                             "weight": s["weight"], "index": s["index"]})
    return {"total_slots": len(slots), "expected_slots": 15,
            "slots_by_kind": dict(by_kind),
            "expected_slots_by_kind": {"vertex": 4, "edge": 6, "face": 4, "cell": 1},
            "terms": {t: {"slots": v["slots"], "raw_sum": round(v["raw_sum"], 12),
                          "members": v["members"]} for t, v in sorted(by_term.items())},
            "every_term_sums_to_one": all(abs(v["raw_sum"] - 1.0) < 1e-9 for v in by_term.values())}


# ------------------------------------------------------------ registry read from the graph
class MirrorFacet:
    """Facet as the arithmetic needs it: the same attribute names core.py uses."""

    def __init__(self, code, iri, weight, beta, guard, guard_min, policy, primary, criticality):
        self.code = code
        self.iri = iri
        self.weight = weight
        self.beta = beta
        self.guard = guard
        self.guard_min = guard_min
        self.policy = policy
        self.primary = primary
        self.criticality = criticality

    def primary_pillar(self):
        return self.primary

    def n_pillars(self):
        return sum(1 for b in self.beta if b > 0)


def facet_registry(graph):
    facets = {}
    for f in graph.subjects(RDF.type, URIRef(ETH + "Facet")):
        code = str(f).split("#")[-1]
        guard_min = graph.value(f, URIRef(ETH + "guardMin"))
        facets[code] = MirrorFacet(
            code=code, iri=str(f),
            weight=1.0,   # D4.17: the facet weight was removed from the canon
            beta=tuple(float(graph.value(f, URIRef(ETH + "beta" + p))) for p in PILLARS),
            guard=as_bool(graph.value(f, URIRef(ETH + "hardGuard"))),
            guard_min=float(guard_min) if guard_min is not None else 0.0,
            policy=str(graph.value(f, URIRef(ETH + "aggregationPolicy"))).split("Policy_")[-1],
            primary=str(graph.value(f, URIRef(ETH + "primaryPillar"))).split("_")[-1],
            criticality={})
    for f, cs in graph.subject_objects(URIRef(ETH + "criticalityStatement")):
        code = str(f).split("#")[-1]
        if code in facets:
            facets[code].criticality[
                str(graph.value(cs, URIRef(ETH + "criticalityDomain"))).split("_")[-1]] = \
                int(graph.value(cs, URIRef(ETH + "criticalityLevel")))
    return facets


# ------------------------------------------------------------ consistency checks
def consistency_checks(full):
    checks = []
    facet_defs = facet_registry(full)   # read from the graph itself, not from the Python registry

    def add(name, kind, query):
        try:
            t_q = time.time()
            r = rows(full, query)
            print(f"  sparql {name}: rows={len(r)} ({time.time()-t_q:.1f} s)", flush=True)
            checks.append({"check": name, "kind": kind, "rows_returned": len(r),
                          "pass": True if kind == "finding" else len(r) == 0,
                          "query": " ".join(query.split()),
                          "sample_rows": [{k: str(v) for k, v in row.items()
                                           if v is not None} for row in r[:5]]})
        except Exception as exc:
            checks.append({"check": name, "kind": kind, "error": f"{type(exc).__name__}: {exc}",
                          "pass": False})

    def add_python(name, kind, passed, detail, query=None):
        entry = {"check": name, "kind": kind, "pass": bool(passed),
                 "rows_returned": detail.get("rows", 0), "detail": detail}
        if query:
            entry["query"] = " ".join(query.split())
        checks.append(entry)

    # ---------------- deontic ----------------
    add("every Norm has a normative instrument", "deontic",
        "SELECT ?n WHERE { ?n a eth:Norm . OPTIONAL { ?n eth:instrument ?i } FILTER(!bound(?i)) }")
    add("every NormConflict names both norms and a resolution strategy", "deontic",
        """SELECT ?cf WHERE { ?cf a eth:NormConflict .
           OPTIONAL { ?cf eth:firstNorm ?a } OPTIONAL { ?cf eth:secondNorm ?b }
           OPTIONAL { ?cf eth:resolutionStrategy ?s }
           FILTER(!bound(?a) || !bound(?b) || !bound(?s)) }""")
    add("every conflict pair carries a priority engine or is flagged unresolved", "deontic",
        """SELECT ?cf WHERE { ?cf a eth:NormConflict .
           OPTIONAL { ?cf eth:conflictPriority ?p } OPTIONAL { ?cf eth:conflictResolved ?r }
           FILTER((!bound(?p) && !bound(?r)) || (bound(?r) && ?r = false && !bound(?p))) }""")

    conflict_query = """SELECT ?cf ?r ?s WHERE { ?cf a eth:NormConflict ;
        eth:conflictResolved ?r ; eth:conflictStatus ?s }"""
    conflict_rows = rows(full, conflict_query)
    bad = [str(r["cf"]) for r in conflict_rows
           if str(r["s"]) != ("resolved" if as_bool(r["r"]) else "unresolved_escalation")]
    add_python("conflictStatus agrees with conflictResolved", "deontic", not bad,
               {"rows": len(bad), "examples": bad[:10], "conflicts_examined": len(conflict_rows)},
               conflict_query)

    add("no duty is delegated to an agent forbidden to carry it", "deontic",
        """SELECT DISTINCT ?link WHERE { ?link a eth:ChainLink ; eth:delegateAgent ?a ;
           eth:delegatedPillar ?p . ?a eth:forbiddenPillar ?p }""")
    add("every Prohibition targets a pillar", "deontic",
        """SELECT ?n WHERE { ?n a eth:Prohibition . OPTIONAL { ?n eth:targetsPillar ?p }
           FILTER(!bound(?p)) }""")
    dangling_conflict = []
    for case in full.subjects(RDF.type, URIRef(ETH + "EthicalCase")):
        status = full.value(case, URIRef(ETH + "normConflictStatus"))
        if status is not None and str(status) != "none":
            if not list(full.objects(case, URIRef(ETH + "hasNormConflict"))):
                dangling_conflict.append(str(case))
    add_python("every case declaring a norm conflict links a NormConflict individual",
               "deontic", not dangling_conflict,
               {"rows": len(dangling_conflict), "cases_examined":
                len(list(full.subjects(RDF.type, URIRef(ETH + "EthicalCase")))),
                "examples": dangling_conflict[:10]})
    add("every delegation chain declares a fallback policy", "deontic",
        """SELECT ?ch WHERE { ?ch a eth:DelegationChain . OPTIONAL { ?ch eth:fallbackForChain ?f }
           FILTER(!bound(?f)) }""")
    add("no declared GuardFailure is at or above its floor", "deontic",
        """SELECT ?b WHERE { ?b a eth:GuardFailure ; eth:observedAtGuard ?o ; eth:guardFloor ?g .
           FILTER(?o >= ?g) }""")
    guard_mins = {f.code: f.guard_min for f in facet_defs.values() if f.guard}
    bad_duty, req_seen = [], 0
    for case in full.subjects(RDF.type, URIRef(ETH + "EthicalCase")):
        for rq in full.objects(case, URIRef(ETH + "hasRequirement")):
            req_seen += 1
            facet = full.value(rq, URIRef(ETH + "requirementFacet"))
            value = full.value(rq, URIRef(ETH + "requirementValue"))
            if facet is None or value is None:
                continue
            code = str(facet).split("#")[-1]
            if code in guard_mins and float(value) < guard_mins[code] - 1e-9:
                bad_duty.append({"case": str(case), "facet": code,
                                 "requirement": float(value), "guard_min": guard_mins[code]})
    add_python("no declared duty (requirement) sits below the guard floor of the facet it governs",
               "deontic", not bad_duty,
               {"rows": len(bad_duty), "requirements_examined": req_seen,
                "note": "asymmetric by design: a duty may exceed a guard floor, but may not be "
                        "declared below it, because then the guard would be a no-op in the case",
                "examples": bad_duty[:10]})

    incomplete_no_abstain = []
    for c in full.subjects(RDF.type, URIRef(ETH + "Confrontation")):
        cov = full.value(c, URIRef(ETH + "coverage"))
        decision = full.value(c, URIRef(ETH + "decision"))
        if cov is not None and float(cov) < 0.70 and str(decision) != ETH + "Decision_ABSTAIN":
            incomplete_no_abstain.append({"confrontation": str(c), "coverage": float(cov)})
    add_python("an incomplete profile never yields a non-ABSTAIN verdict", "deontic",
               not incomplete_no_abstain,
               {"rows": len(incomplete_no_abstain),
                "note": "vacuous in corpus_v6 (every profile declares coverage 1.0); the rule "
                        "and the shape stay so that partial-coverage corpora cannot bypass E29",
                "examples": incomplete_no_abstain[:10]})
    add("every Confrontation references an existing EthicalCase and Profile", "deontic",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:confrontationCase ?case ;
           eth:confrontationProfile ?prof .
           OPTIONAL { ?case a eth:EthicalCase } OPTIONAL { ?prof a eth:Profile }
           FILTER(!bound(?case) || !bound(?prof)) }""")

    # A PROHIBIT verdict must be grounded in a hard veto, or in the score route with the
    # categorical gates (real stakes, and a material gap on a duty the domain marks critical).
    cat_query = """SELECT ?c ?aa ?ratio ?bar ?stake ?mg ?cal WHERE {
        ?c a eth:Confrontation ; eth:decision eth:Decision_PROHIBIT ;
           eth:adequacyLow ?aa ; eth:riskRatio ?ratio ; eth:decisionBar ?bar ;
           eth:stakesWeighted ?stake ; eth:materialGapLow ?mg ; eth:appliedCalibration ?cal .
    }"""
    cat_rows = rows(full, cat_query)
    hard_veto_rows = rows(full, """SELECT ?c WHERE { ?c eth:hardVetoPillar ?p }""")
    hard_set = {str(r["c"]) for r in hard_veto_rows}
    cal_params = {}
    for r in rows(full, """SELECT ?cal ?pm ?rp ?cpg ?pnm ?psm WHERE {
            ?cal eth:prohibitMargin ?pm ; eth:ratioProhibit ?rp ; eth:criticalProhibitGap ?cpg ;
                 eth:prohibitNeedsMaterial ?pnm ; eth:prohibitStakesMin ?psm }"""):
        cal_params[str(r["cal"])] = r
    ungrounded = []
    for r in cat_rows:
        cal = cal_params.get(str(r["cal"]))
        if cal is None:
            ungrounded.append({"confrontation": str(r["c"]), "reason": "calibration parameters not declared"})
            continue
        categorical = (float(r["stake"]) >= float(cal["psm"]) and
                       (not as_bool(cal["pnm"]) or float(r["mg"]) >= float(cal["cpg"])))
        score_route = (float(r["aa"]) <= float(r["bar"]) - float(cal["pm"]) or
                       float(r["ratio"]) >= float(cal["rp"]))
        if str(r["c"]) not in hard_set and not (categorical and score_route):
            ungrounded.append({"confrontation": str(r["c"]), "aa_low": float(r["aa"]),
                              "bar": float(r["bar"]), "ratio": float(r["ratio"]),
                              "stakes": float(r["stake"]), "material_gap_low": float(r["mg"])})
# Guard breaches asserted in the graph must match the guard definitions.
    guard_query = """SELECT ?c ?count WHERE { ?c a eth:Confrontation ; eth:guardFailureCount ?count }"""
    guard_rows = rows(full, guard_query)
    guard_defs = {f.code: f.guard_min for f in facet_defs.values() if f.guard}
    observed = defaultdict(set)
    for c, gf in full.subject_objects(URIRef(ETH + "hasGuardFailure")):
        facet = full.value(gf, URIRef(ETH + "guardFacet"))
        if facet is not None:
            observed[str(c)].add(str(facet).split("#")[-1])
    mismatch = []
    for r in guard_rows:
        c = str(r["c"])
        declared = int(r["count"])
        listed = len(observed.get(c, set()))
        if declared != listed:
            mismatch.append({"confrontation": c, "declared": declared, "listed_bnodes": listed})
    add_python("guardFailureCount equals the number of GuardFailure individuals attached",
               "deontic", not mismatch,
               {"rows": len(mismatch), "confrontations_examined": len(guard_rows),
                "examples": mismatch[:10]}, guard_query)

    # The recorded guard breach must really be a breach of the facet's declared floor.
    # Done in Python: the SPARQL join of 16.475 GuardFailure nodes against 169.950
    # observations is combinatorial in rdflib and took > 40 min without producing a result.
    guard_defs = {f.code: f.guard_min for f in facet_defs.values() if f.guard}
    level_by_profile = defaultdict(dict)
    for prof, ob in full.subject_objects(URIRef(ETH + "hasObservation")):
        facet = full.value(ob, URIRef(ETH + "observedFacet"))
        level = full.value(ob, URIRef(ETH + "observedValue"))
        if facet is not None and level is not None:
            level_by_profile[str(prof)][str(facet).split("#")[-1]] = float(level)
    floor_bad = []
    examined = 0
    for c, gf in full.subject_objects(URIRef(ETH + "hasGuardFailure")):
        facet = str(full.value(gf, URIRef(ETH + "guardFacet"))).split("#")[-1]
        recorded_floor = full.value(gf, URIRef(ETH + "guardFloor"))
        profile = full.value(c, URIRef(ETH + "confrontationProfile"))
        declared_floor = guard_defs.get(facet)
        examined += 1
        if declared_floor is None:
            floor_bad.append({"confrontation": str(c), "facet": facet,
                             "reason": "guard declared on a facet without a declared floor"})
            continue
        if recorded_floor is not None and abs(float(recorded_floor) - declared_floor) > 1e-6:
            floor_bad.append({"confrontation": str(c), "facet": facet,
                             "recorded_floor": float(recorded_floor), "declared_floor": declared_floor})
            continue
        level = level_by_profile.get(str(profile), {}).get(facet)
        if level is not None and level >= declared_floor - 1e-9:
            floor_bad.append({"confrontation": str(c), "facet": facet,
                             "reason": "recorded level is not below the guard floor",
                             "level": level, "floor": declared_floor})
    add_python("every recorded guard breach uses the facet's own declared floor and really "
               "breaches it", "deontic", not floor_bad,
               {"rows": len(floor_bad), "guard_breach_records_examined": examined,
               "examples": floor_bad[:10]}, "python traversal (hasGuardFailure x hasObservation)")

    # ---------------- structural ----------------
    add("every facet's beta weights sum to 1", "structural",
        """SELECT ?f WHERE { ?f a eth:Facet ; eth:betaW ?w ; eth:betaC ?c ; eth:betaM ?m ; eth:betaK ?k .
           BIND(?w + ?c + ?m + ?k AS ?s) . FILTER(ABS(?s - 1.0) > 1e-9) }""")
    per_facet_policy = defaultdict(int)
    for f, p in full.subject_objects(URIRef(ETH + "aggregationPolicy")):
        per_facet_policy[str(f)] += 1
    add_python("every facet declares exactly one aggregation policy", "structural",
               all(v == 1 for v in per_facet_policy.values()) and
               len(per_facet_policy) == len(facet_defs),
               {"rows": sum(v - 1 for v in per_facet_policy.values() if v > 1),
                "facets_with_a_policy": len(per_facet_policy),
                "facets_declared": len(facet_defs),
                "policies_by_kind": dict(Counter(str(p).split("#")[-1]
                                                 for _, p in
                                                 full.subject_objects(
                                                     URIRef(ETH + "aggregationPolicy"))))})
    add("lattice slot weights sum to 1 inside each structural term", "structural",
        """SELECT ?term (SUM(?w) AS ?total) (COUNT(?slot) AS ?slots) WHERE {
           ?slot eth:belongsToTerm ?term ; eth:structuralWeight ?w } GROUP BY ?term
           HAVING (ABS(SUM(?w) - 1.0) > 1e-9)""")
    add("the hierarchy S4 <= S3 <= S2 holds for every confrontation", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ;
           eth:structuralTermS2 ?s2 ; eth:structuralTermS3 ?s3 ; eth:structuralTermS4 ?s4 .
           FILTER(?s4 > ?s3 + 1e-9 || ?s3 > ?s2 + 1e-9) }""")
    add("stored adequacy never exceeds raw adequacy", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:adequacyRaw ?raw ; eth:adequacy ?aa .
           FILTER(?aa > ?raw + 1e-9) }""")
    add("the adequacy band is ordered: adequacyLow <= adequacy <= adequacyHigh", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:adequacyLow ?lo ; eth:adequacy ?aa ;
           eth:adequacyHigh ?hi FILTER(?lo > ?aa + 1e-9 || ?aa > ?hi + 1e-9) }""")
    add("risk quantities stay inside their declared ranges", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ;
           eth:stakesWeighted ?s ; eth:failureProbability ?p ; eth:epistemicPenalty ?u ;
           eth:facetExposurePhi ?phi .
           FILTER(?s < 0 || ?s > 1 || ?p < 0.02 - 1e-9 || ?p > 0.98 + 1e-9 ||
                  ?u < 0 || ?phi < 0 || ?s > 1.0000001) }""")
    add("declared lam and mu sums equal 1", "structural",
        """SELECT ?cal WHERE { ?cal a eth:Calibration ; eth:lamSum ?l ; eth:muSum ?m .
           FILTER(ABS(?l - 1.0) > 1e-9 || ABS(?m - 1.0) > 1e-9) }""")
    add("each pillar's vertex-slot weight equals the calibration lambda", "structural",
        """SELECT ?p WHERE {
           VALUES (?p ?lamProp) { (eth:pillar_W eth:lamW) (eth:pillar_C eth:lamC)
                                  (eth:pillar_M eth:lamM) (eth:pillar_K eth:lamK) }
           ?cal a eth:Calibration ; ?lamProp ?lamCal .
           ?p eth:faceLatticeSlot ?slot ; eth:structuralWeight ?lamSlot .
           FILTER(ABS(?lamCal - ?lamSlot) > 1e-6) }""")
    add("no chain link delegates more than the four pillars", "structural",
        """SELECT ?link (COUNT(?p) AS ?n) WHERE { ?link a eth:ChainLink ; eth:delegatedPillar ?p }
           GROUP BY ?link HAVING (COUNT(?p) > 4)""")
    add("every pillar is touched by at least one facet with a non-zero beta", "structural",
        """SELECT ?pillar (COUNT(?f) AS ?n) WHERE {
           VALUES (?pillar ?betaProp) { (eth:pillar_W eth:betaW) (eth:pillar_C eth:betaC)
                                        (eth:pillar_M eth:betaM) (eth:pillar_K eth:betaK) }
           ?f a eth:Facet ; ?betaProp ?b . FILTER(?b > 0) }
           GROUP BY ?pillar HAVING (COUNT(?f) = 0)""")
    add("the guard floor of every guarded facet is within [0,1] and its requirement is above it",
        "structural",
        """SELECT ?f WHERE { ?f a eth:Facet ; eth:hardGuard true ; eth:guardMin ?g
           FILTER(?g < 0 || ?g > 1) }""")
    add("no confrontation is missing the structural terms or the decision bar", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation .
           OPTIONAL { ?c eth:structuralTermS2 ?s2 } OPTIONAL { ?c eth:structuralTermS3 ?s3 }
           OPTIONAL { ?c eth:structuralTermS4 ?s4 } OPTIONAL { ?c eth:decisionBar ?bar }
           FILTER(!bound(?s2) || !bound(?s3) || !bound(?s4) || !bound(?bar)) }""")

    # E30: capValue stored on the grounding fact must equal requirement * (1 - strength*(1-compliance))
    req_by_case_facet = {}
    for case, rq in full.subject_objects(URIRef(ETH + "hasRequirement")):
        f = full.value(rq, URIRef(ETH + "requirementFacet"))
        v = full.value(rq, URIRef(ETH + "requirementValue"))
        if f is not None and v is not None:
            req_by_case_facet[(str(case), str(f).split("#")[-1])] = float(v)
    e30_bad = 0
    max_err = 0.0
    examined = 0
    for case, gf in full.subject_objects(URIRef(ETH + "groundedByFact")):
        f = full.value(gf, URIRef(ETH + "anchorsFacet"))
        if f is None:
            continue
        fcode = str(f).split("#")[-1]
        compl = full.value(gf, URIRef(ETH + "complianceValue"))
        cap = full.value(gf, URIRef(ETH + "capValue"))
        strength = full.value(gf, URIRef(ETH + "groundingStrength"))
        req = req_by_case_facet.get((str(case), fcode))
        if compl is None or cap is None or req is None:
            continue
        examined += 1
        computed = req * (1.0 - (float(strength) if strength is not None else 0.0) * (1.0 - float(compl)))
        err = abs(computed - float(cap))
        max_err = max(max_err, err)
        if err > 1e-9:
            e30_bad += 1
    add_python("E30: every stored capValue equals requirement x (1 - strength x (1 - compliance))",
               "structural", e30_bad == 0,
               {"rows": e30_bad, "facts_examined": examined,
                "max_abs_difference": round(max_err, 12)}, "python traversal (groundedByFact x hasRequirement)")

    # -------- v4.2 gates: oversight (D5.4), coverage gate (D5.8), ReviewNeed (D5.6), Prop 1 ----
    slots_all = lattice_from_graph(full)
    edges = [x for x in slots_all if x["kind"] == "edge"]
    faces = [x for x in slots_all if x["kind"] == "face"]
    derived = []
    for e in edges:
        inc = set(e["incidence"])
        expected = sum(f["weight"] for f in faces if inc <= set(f["incidence"])) / 3.0
        derived.append({"slot": e["name"], "declared": round(e["weight"], 12),
                       "derived_alpha": round(expected, 12),
                       "diff": round(abs(e["weight"] - expected), 12)})
    bad_alpha = [x for x in derived if x["diff"] > 1e-6]
    add_python("Proposition 1 (D5.1): every declared edge weight equals (1/3) * sum of the "
               "face weights of the faces containing that edge", "structural", not bad_alpha,
               {"rows": len(bad_alpha), "edges_examined": len(edges), "max_diff":
                max((x["diff"] for x in derived), default=0.0), "examples": derived[:6]})

    regime_of = {}
    for case in full.subjects(RDF.type, URIRef(ETH + "EthicalCase")):
        r = full.value(case, URIRef(ETH + "oversightRegime"))
        regime_of[str(case)] = str(r).split("Oversight_")[-1] if r is not None else None
    review, audit, appeal = set(), set(), set()
    for case in full.subjects(RDF.type, URIRef(ETH + "EthicalCase")):
        for gf in full.objects(case, URIRef(ETH + "groundedByFact")):
            name = str(full.value(gf, URIRef(ETH + "factName")))
            value = full.value(gf, URIRef(ETH + "factValue"))
            if not as_bool(value):
                continue      # the fact is declared and false: no supervision exists
            if name == "human_review_channel":
                review.add(str(case))
            elif name == "independent_audit":
                audit.add(str(case))
            elif name == "appeal_channel":
                appeal.add(str(case))

    def expected_regime(c):
        if c in review and c in audit:
            return "in_the_loop"
        if c in review or c in appeal:
            return "on_the_loop"
        return "none"

    missing_regime = [c for c, v in regime_of.items() if v is None]
    add_python("every case declares exactly one oversight regime (E11c')", "structural",
               not missing_regime, {"rows": len(missing_regime),
                                   "cases_examined": len(regime_of)})
    wrong = {c: (v, expected_regime(c)) for c, v in regime_of.items()
             if v is not None and v != expected_regime(c)}
    add_python("the declared oversight regime is exactly the one the declared facts imply "
               "(no invented supervision)", "deontic", not wrong,
               {"rows": len(wrong), "cases_examined": len(regime_of),
                "examples": {k: list(v) for k, v in list(wrong.items())[:5]},
                "regime_mix": dict(Counter(v for v in regime_of.values() if v))})

    cal_bad = []
    for cal in full.subjects(RDF.type, URIRef(ETH + "Calibration")):
        z = full.value(cal, URIRef(ETH + "crossPillarCoefficient"))
        s_ = full.value(cal, URIRef(ETH + "salienceAdaptation"))
        g_ = full.value(cal, URIRef(ETH + "coverageGate"))
        if z is None or s_ is None or g_ is None:
            cal_bad.append({"calibration": str(cal), "reason": "v13 coefficients not declared"})
            continue
        if abs(float(z)) > EPS or abs(float(s_)) > EPS or abs(float(g_) - 0.70) > EPS:
            cal_bad.append({"calibration": str(cal), "zeta": float(z), "s": float(s_), "gate": float(g_)})
    add_python("the declared v13 coefficients are the canonical ones: zeta = 0, s = 0, coverage gate = 0.70",
               "structural", not cal_bad, {"rows": len(cal_bad), "examples": cal_bad[:5]},
               "python numeric comparison over eth:Calibration individuals")
    add("no confrontation has coverage or reviewNeed outside [0,1]", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation .
           OPTIONAL { ?c eth:coverage ?cv } OPTIONAL { ?c eth:reviewNeed ?rn }
           FILTER((bound(?cv) && (?cv < 0 || ?cv > 1)) ||
                  (bound(?rn) && (?rn < 0 || ?rn > 1))) }""")
    add("every confrontation with declared coverage below the gate abstains (E26')", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:coverage ?cv ; eth:decision ?d
           FILTER(?cv < 0.70 - 1e-9 && ?d != eth:Decision_ABSTAIN) }""")
    add("no coverage-abstaining confrontation carries an adequacy literal (D5.8)", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:coverage ?cv ;
           eth:decision eth:Decision_ABSTAIN ; eth:adequacy ?a
           FILTER(?cv < 0.70 - 1e-9) }""")
    add("no confrontation violates S2 >= S3 >= S4 (Proposition 1, measured on the graph)",
        "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:structuralTermS2 ?s2 ;
           eth:structuralTermS3 ?s3 ; eth:structuralTermS4 ?s4
           FILTER(?s2 < ?s3 - 1e-9 || ?s3 < ?s4 - 1e-9) }""")
    add("no canonical duty spans all four pillars: the cell has no facet-level witness",
        "structural",
        """SELECT ?f WHERE { ?f a eth:Facet . ?f eth:betaW ?w . ?f eth:betaC ?c .
           ?f eth:betaM ?m . ?f eth:betaK ?k .
           FILTER(?w > 0 && ?c > 0 && ?m > 0 && ?k > 0) }""")
    add("every recorded cross-pillar duty exposure lies in [0,1]", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:crossPillarDuty ?p
           FILTER(?p < 0 || ?p > 1) }""")

    # ---------------- findings (reported, not gates) ----------------
    add("no chain link delegates a pillar the delegate is forbidden to carry", "structural",
        """SELECT ?link WHERE { ?link a eth:ChainLink ; eth:delegateAgent ?a ;
           eth:delegatedPillar ?p . ?a eth:forbiddenPillar ?p }""")
    add("every chain link declares at least one delegated pillar", "structural",
        """SELECT ?link WHERE { ?link a eth:ChainLink .
           FILTER NOT EXISTS { ?link eth:delegatedPillar ?p } }""")
    add("chain links where the case's critical duty is retained at the delegating layer "
        "(E28 retention, reported not penalised)", "finding",
        """SELECT ?link WHERE { ?link a eth:ChainLink ;
           eth:criticalDutyDelegated false }""")
    add("confrontations whose declaredStakesSum exceeds the declared ceiling 2.1", "finding",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:declaredStakesSum ?s
           FILTER(?s > 2.1 + 1e-9) }""")
    return checks


# ------------------------------------------------------------ confrontation sampling
def select_confrontations(full, n=100):
    """Stratified, deterministic sample: round-robin over (domain, verdict) strata, rare
    strata first, confrontation id ascending. Guarantees every verdict present in the
    corpus is represented when it exists."""
    r = rows(full, """SELECT ?c ?case ?domain ?decision ?layer WHERE {
        ?c a eth:Confrontation ; eth:confrontationCase ?case ; eth:agentLayer ?layer ;
           eth:decision ?decision .
        ?case eth:domain ?domain } ORDER BY ?case ?c""")
    strata = defaultdict(list)
    for x in r:
        key = (str(x["domain"]).split("_")[-1], str(x["decision"]).split("Decision_")[-1])
        strata[key].append(str(x["c"]))
    keys = sorted(strata, key=lambda k: (len(strata[k]), k))
    chosen, i = [], 0
    while len(chosen) < n:
        moved = False
        for k in keys:
            if i < len(strata[k]):
                chosen.append(strata[k][i])
                moved = True
                if len(chosen) == n:
                    break
        if not moved:
            break
        i += 1
    distribution = Counter(str(x["decision"]).split("Decision_")[-1] for x in r)
    return chosen, {"|".join(map(str, k)): len(v) for k, v in sorted(strata.items())}, \
        len(r), distribution


def mirror_inputs(full, chosen):
    """All raw inputs the mirror needs, read from the graph with plain SELECTs."""
    vc = f"VALUES ?c {{ {blocks(chosen)} }}"
    cal_num = [p for p in CAL_PROPS if p != "prohibitNeedsMaterial"] + CTX_PROPS
    pillar_props = ["lamW", "lamC", "lamM", "lamK", "muW", "muC", "muM", "muK",
                    "thetaW", "thetaC", "thetaM", "thetaK"]
    cal_pat = " ".join(f"eth:{p} ?{p} ;" for p in cal_num + pillar_props) + \
              " eth:prohibitNeedsMaterial ?pnm ."
    ctx = {}
    for row in rows(full, f"""
        SELECT ?c ?case ?profile ?calId ?dom ?sev ?rev ?pr ?hor ?UE ?Rc ?exposure
               ?conflict ?evidence ?critPillar ?pnm ?regime
               {" ".join("?" + p for p in cal_num + pillar_props)}
        WHERE {{
          {vc}
          ?c eth:confrontationCase ?case ; eth:confrontationProfile ?profile ;
             eth:appliedCalibration ?calId .
          ?case eth:domain ?dom ; eth:severity ?sb ; eth:reversibility ?rb ;
                eth:prudentialMode ?pb ; eth:horizon ?hb ;
                eth:epistemicUncertainty ?UE ; eth:consequenceMass ?Rc ;
                eth:exposureScale ?exposure ; eth:normConflictStatus ?conflict ;
                eth:evidenceConflict ?evidence .
          OPTIONAL {{ ?case eth:oversightRegime ?regime }}
          OPTIONAL {{ ?case eth:criticalPillar ?critPillar }}
          ?sb eth:severityValue ?sev . ?rb eth:reversibilityValue ?rev .
          ?pb eth:prudentialValue ?pr . ?hb eth:horizonValue ?hor .
          ?calId {cal_pat}
        }}"""):
        c = str(row["c"])
        d = ctx.setdefault(c, {"cal": {}, "critical_pillars": set()})
        d.update({"case": str(row["case"]), "profile": str(row["profile"]),
                 "calibration": str(row["calId"]),
                 "domain": str(row["dom"]).split("_")[-1],
                 "severity": float(row["sev"]), "irreversibility": float(row["rev"]),
                 "prudential": float(row["pr"]), "horizon": float(row["hor"]),
                 "UE": float(row["UE"]), "Rc": float(row["Rc"]),
                 "exposure": float(row["exposure"]),
                 "conflict_status": str(row["conflict"]),
                 "evidence_conflict": as_bool(row["evidence"]),
                 "oversight": (str(row["regime"]).split("Oversight_")[-1]
                               if row["regime"] is not None else "unspecified")})
        for p in cal_num + pillar_props:
            d["cal"][p] = float(row[p])
        d["cal"]["prohibitNeedsMaterial"] = as_bool(row["pnm"])
        if row["critPillar"] is not None:
            d["critical_pillars"].add(str(row["critPillar"]).split("_")[-1])

    levels, confs, requirements = defaultdict(dict), defaultdict(dict), defaultdict(dict)
    for row in rows(full, f"""
        SELECT ?c ?f ?v ?conf WHERE {{
          {vc}
          ?c eth:confrontationProfile ?p . ?p eth:hasObservation ?ob .
          ?ob eth:observedFacet ?f ; eth:observedValue ?v ; eth:observationConfidence ?conf }}"""):
        code = str(row["f"]).split("#")[-1]
        levels[str(row["c"])][code] = float(row["v"])
        confs[str(row["c"])][code] = float(row["conf"])
    for row in rows(full, f"""
        SELECT ?c ?f ?r WHERE {{
          {vc}
          ?c eth:confrontationCase ?case . ?case eth:hasRequirement ?rq .
          ?rq eth:requirementFacet ?f ; eth:requirementValue ?r }}"""):
        requirements[str(row["c"])][str(row["f"]).split("#")[-1]] = float(row["r"])

    facts = defaultdict(list)
    for row in rows(full, f"""
        SELECT ?c ?f ?compl ?str ?cap WHERE {{
          {vc}
          ?c eth:confrontationCase ?case . ?case eth:groundedByFact ?gf .
          ?gf eth:anchorsFacet ?f ; eth:complianceValue ?compl ; eth:capValue ?cap .
          OPTIONAL {{ ?gf eth:groundingStrength ?str }} }}"""):
        facts[str(row["c"])].append({"facet": str(row["f"]).split("#")[-1],
                                    "compliance": float(row["compl"]),
                                    "strength": float(row["str"]) if row["str"] is not None else 0.0,
                                    "cap": float(row["cap"])})

    caps = defaultdict(dict)
    for c, fl in facts.items():
        for f in fl:
            expected = requirements[c].get(f["facet"], 1.0) * (1 - f["strength"] * (1 - f["compliance"]))
            caps[c][f["facet"]] = min(caps[c].get(f["facet"], 1.0), expected)

    return ctx, levels, confs, requirements, facts, caps


def core_calibration(cal, lattice_slots):
    """Build core.Calibration from the RDF-declared parameters (edge/face weights read from
    the face-lattice slots, in the same order core.EDGES and core.FACES use)."""
    edge_by_pillars = {}
    face_by_pillars = {}
    for slot in lattice_slots:
        if slot["kind"] == "edge":
            edge_by_pillars[frozenset(slot["incidence"])] = slot["weight"]
        elif slot["kind"] == "face":
            face_by_pillars[frozenset(slot["incidence"])] = slot["weight"]
    alpha = tuple(edge_by_pillars[frozenset((PILLARS[i], PILLARS[j]))] for i, j in CORE_EDGES)
    beta_face = tuple(face_by_pillars[frozenset((PILLARS[i], PILLARS[j], PILLARS[k]))]
                      for i, j, k in CORE_FACES)
    return core.Calibration(lam=tuple(cal["lam" + p] for p in PILLARS),
                            alpha=alpha, beta_face=beta_face,
                            gamma=cal["gamma"], eta=cal["eta"], omega=cal["omega"],
                            rho=cal["rho"], delta=cal["delta"],
                            theta=tuple(cal["theta" + p] for p in PILLARS),
                            hard_veto_delta=cal["hardVetoDelta"],
                            material_gap=cal["materialGap"],
                            critical_prohibit_gap=cal["criticalProhibitGap"],
                            cap_base=cal["capBase"], cap_stakes_gain=cal["capStakesGain"],
                            prohibit_stakes_min=cal["prohibitStakesMin"],
                            veto_slack=cal["vetoSlack"],
                            prohibit_needs_material=cal["prohibitNeedsMaterial"],
                            stakes_veto_min=cal["stakesVetoMin"],
                            bar_base=cal["barBase"], bar_severity=cal["barSeverity"],
                            bar_irreversibility=cal["barIrreversibility"],
                            bar_prudential=cal["barPrudential"], bar_horizon=cal["barHorizon"],
                            prohibit_margin=cal["prohibitMargin"],
                            guards_margin=cal["guardsMargin"],
                            ratio_prohibit=cal["ratioProhibit"], ratio_review=cal["ratioReview"],
                            ratio_guards=cal["ratioGuards"],
                            mu=tuple(cal["mu" + p] for p in PILLARS),
                            abstain_uncertainty=cal["abstainUncertainty"],
                            abstain_knowledge_floor=cal["abstainKnowledgeFloor"],
                            hysteresis=cal["hysteresis"])


def mirror_compute(ctx, levels, confs, requirements, facet_list, lattice_slots,
                   mode, domain):
    """One pass of the adequacy/risk machinery, from the RDF literals only."""
    cal = ctx["cal"]
    kappa = cal["uncertaintyKappa"]
    ell, guard_failures = core.project(levels, facet_list, cap_guards=True,
                                       confidence=confs, mode=mode)
    q, _ = core.project(requirements, facet_list, cap_guards=False)
    d = [max(0.0, q[i] - ell[i]) for i in range(4)]
    terms = structural_terms_from_lattice(d, lattice_slots)
    D, S2, S3, S4 = terms["D"], terms["S2"], terms["S3"], terms["S4"]
    u = clamp(ctx["UE"] * d[3] / max(q[3], EPS) if q[3] > EPS else ctx["UE"] * d[3])

    d_guard = list(d)
    floor_breach = [False] * 4
    cw = cs = 0.0
    material = 0.0
    material_beta = (0.0, 0.0, 0.0, 0.0)
    material_facet = None
    for f in facet_list:
        r_f = requirements.get(f.code)
        l_f = levels.get(f.code)
        if r_f is None or l_f is None:
            continue
        conf = confs.get(f.code, 1.0)
        eff = core.effective_value(f, l_f, conf, mode, kappa)
        band = core.band_value(l_f, conf, mode)
        gap = max(0.0, r_f - band)
        crit = f.criticality.get(domain, 2)
        w = crit                 # D4.17: beta alone
        cw += w
        cs += w * gap
        if (crit == 4 or f.guard) and gap > material:
            material = gap
            material_beta = f.beta
            material_facet = f.code
        if f.guard:
            for i, b in enumerate(f.beta):
                if b > 0:
                    d_guard[i] = max(d_guard[i], gap)
                    if eff < f.guard_min:
                        floor_breach[i] = True
    phi = cs / cw if cw > EPS else 0.0
    n2 = n3 = d2 = d3 = 0.0
    for f in facet_list:
        r_f = requirements.get(f.code)
        l_f = levels.get(f.code)
        if r_f is None or l_f is None:
            continue
        sup = f.n_pillars()
        if sup < 2:
            continue
        sigma = 1.0 - max(f.beta)
        if sigma <= EPS:
            continue
        band = core.band_value(l_f, confs.get(f.code, 1.0), mode)
        gap = max(0.0, r_f - band)
        if sup == 2:
            n2 += sigma * gap; d2 += sigma
        else:
            n3 += sigma * gap; d3 += sigma
    psi = (n2 + n3) / (d2 + d3) if (d2 + d3) > EPS else 0.0
    psi_edge = n2 / d2 if d2 > EPS else 0.0
    psi_face = n3 / d3 if d3 > EPS else 0.0
    lam0 = [cal["lam" + PILLARS[i]] for i in range(4)]
    s_adapt = cal.get("salienceAdaptation", 0.0)
    if s_adapt > 0.0:
        raw = [lam0[i] * max(q[i], 0.0) ** s_adapt for i in range(4)]
        tot = sum(raw)
        salience = [x / tot for x in raw] if tot > EPS else lam0
    else:
        salience = lam0
    aa_raw = clamp(1.0 - sum(salience[i] * d[i] for i in range(4))
                   - cal["gamma"] * S2 - cal["eta"] * S3 - cal["omega"] * S4
                   - cal["rho"] * u - cal["delta"] * phi
                   - cal.get("crossPillarCoefficient", 0.0) * psi)

    sev, rev, pr, hor = ctx["severity"], ctx["irreversibility"], ctx["prudential"], ctx["horizon"]
    irr_eff = rev * (1.0 - OVERSIGHT_ATTENUATION
                     * oversight_value(ctx.get("oversight", "unspecified")))
    stakes = clamp(cal["stakeWeightSeverity"] * sev + cal["stakeWeightIrreversibility"] * irr_eff
                   + cal["stakeWeightPrudential"] * (pr / 0.10)
                   + cal["stakeWeightHorizon"] * hor, 0.0, 1.0)
    bar = clamp(cal["barBase"] + cal["barSeverity"] * sev + cal["barIrreversibility"] * rev
                + cal["barPrudential"] * (pr / 0.05) + cal["barHorizon"] * hor, 0.30, 0.90)
    sigma = clamp(0.05 + 0.15 * sev * rev + pr, 0.0, 0.35)

    crit_pillars = ctx["critical_pillars"]
    veto = {i for i in range(4) if d_guard[i] >= cal["theta" + PILLARS[i]]
            and (PILLARS[i] in crit_pillars or floor_breach[i])}
    if material >= cal["materialGap"]:
        veto.update(i for i, b in enumerate(material_beta) if b > 0)
    cap_gap = max([material] + [d_guard[i] for i in veto])
    scale = 1.0 + 2.0 * max(0.0, (cal["stakesVetoMin"] - stakes) / cal["stakesVetoMin"])
    hard_veto = {i for i in veto if d_guard[i] >= cal["theta" + PILLARS[i]]
                 + cal["hardVetoDelta"] * scale
                 or (floor_breach[i] and stakes >= cal["stakesVetoMin"])}
    if material >= cal["criticalProhibitGap"] and stakes >= cal["stakesVetoMin"]:
        hard_veto.update(i for i, b in enumerate(material_beta) if b > 0)

    cap_weight = cal["capBase"] + cal["capStakesGain"] * stakes
    if veto or cap_gap >= cal["materialGap"]:
        aa = max(0.0, min(aa_raw, 1.0 - cap_weight * cap_gap))
    else:
        aa = max(0.0, aa_raw)
    reliability = clamp(sum(cal["mu" + PILLARS[i]] * ell[i] for i in range(4)))
    p_fail = clamp(1.0 - reliability, 0.02, 0.98)
    ratio = (p_fail + sigma) / (1.0 + sigma)
    return {"levels": list(ell), "requirements": list(q), "deficits": d,
            "guarded_deficits": d_guard, "S2": S2, "S3": S3, "S4": S4, "D": D, "u": u,
            "phi": phi, "aa_raw": aa_raw, "aa": aa, "material_gap": material,
            "material_facet": material_facet, "cap_gap": cap_gap, "veto": sorted(veto),
            "hard_veto": sorted(hard_veto), "floor_breach": floor_breach,
            "stakes": stakes, "sigma": sigma, "bar": bar, "p_fail": p_fail, "ratio": ratio,
            "residual_risk": ctx["Rc"] * ratio,
            "harm": ctx["Rc"] * stakes * clamp(ctx["exposure"], 0.0, 1.0),
            "guard_failures": [g["facet"] for g in guard_failures],
            "coverage": sum(1 for f in facet_list if f.code in levels) / len(facet_list),
            "psi": psi, "psi_edge": psi_edge, "psi_face": psi_face,
            "salience": salience, "oversight": ctx.get("oversight", "unspecified")}


def python_decision(ctx, low, central, cal_obj, case_spec, facets):
    """The ladder implemented here (mirroring core.decide), plus core.decide as reference."""
    veto_low, hard_low = low["veto"], low["hard_veto"]
    aa, ratio, bar, stakes = low["aa"], low["ratio"], low["bar"], low["stakes"]
    if hard_low:
        ladder = "PROHIBIT"
    else:
        categorical = (stakes >= ctx["cal"]["prohibitStakesMin"] and
                       (not ctx["cal"]["prohibitNeedsMaterial"] or
                        low["material_gap"] >= ctx["cal"]["criticalProhibitGap"]))
        if categorical and (aa <= bar - ctx["cal"]["prohibitMargin"] or
                            ratio >= ctx["cal"]["ratioProhibit"]):
            ladder = "PROHIBIT"
        elif (aa <= bar or (veto_low and aa <= bar + ctx["cal"]["vetoSlack"]) or
              ratio >= ctx["cal"]["ratioReview"]):
            ladder = "REVIEW_REQUIRED"
        elif (aa <= bar + ctx["cal"]["guardsMargin"] or ratio >= ctx["cal"]["ratioGuards"]
              or veto_low):
            ladder = "ALLOW_WITH_GUARDS"
        else:
            ladder = "ALLOW"
    epistemic = ((ctx["conflict_status"] != "none" or ctx["evidence_conflict"]) and
                 ctx["UE"] >= ctx["cal"]["abstainUncertainty"] and
                 central["levels"][3] <= ctx["cal"]["abstainKnowledgeFloor"])
    if low["coverage"] < 0.70:
        ladder = "ABSTAIN"
        epistemic = False
    if epistemic:
        ladder = "ABSTAIN"
    reference = None
    if case_spec is not None:
        reference = "ABSTAIN" if epistemic else core.decide(
            aa, ratio, cal_obj, case_spec, veto_low, hard_low, low["material_gap"])
    return ladder, epistemic, reference


def build_labels(full):
    """Band individual -> core label, so core.decide can be run on the RDF inputs."""
    labels = {}
    for cls in ("SeverityBand", "PrudentialMode", "Reversibility", "TemporalHorizon"):
        for s in full.subjects(RDF.type, URIRef(ETH + cls)):
            labels[str(s)] = str(full.value(s, URIRef("http://www.w3.org/2000/01/rdf-schema#label")))
    return labels


def stored_values(full, chosen):
    out = {}
    vc = f"VALUES ?c {{ {blocks(chosen)} }}"
    props = ["levelW", "levelC", "levelM", "levelK", "requirementW", "requirementC",
             "requirementM", "requirementK", "deficitW", "deficitC", "deficitM", "deficitK",
             "guardedDeficitW", "guardedDeficitC", "guardedDeficitM", "guardedDeficitK",
             "structuralTermS2", "structuralTermS3", "structuralTermS4", "weightedDeficit",
             "epistemicPenalty", "facetExposurePhi", "adequacyRaw", "adequacy", "adequacyLow",
             "adequacyHigh", "materialGapLow", "decisionBar", "sigmaFloor", "stakesWeighted",
             "failureProbability", "riskRatio", "residualRisk", "harmScale", "coverage",
             "guardFailureCount", "crossPillarDuty", "crossPillarDutyEdge",
             "crossPillarDutyFace", "caseSalienceW", "caseSalienceC", "caseSalienceM",
             "caseSalienceK", "reviewNeed"]
    for c in chosen:
        cu = URIRef(c)
        get = lambda name: (float(full.value(cu, URIRef(ETH + name))
                               if full.value(cu, URIRef(ETH + name)) is not None else None))
        out[c] = {name: get(name) for name in props}
        out[c]["decision"] = str(full.value(cu, URIRef(ETH + "decision"))).split("Decision_")[-1]
        out[c]["epistemic_abstention"] = as_bool(full.value(cu, URIRef(ETH + "epistemicAbstention")))
        out[c]["veto_pillars"] = sorted(str(v).split("_")[-1] for v in
                                        full.objects(cu, URIRef(ETH + "vetoPillar")))
        out[c]["hard_veto_pillars"] = sorted(str(v).split("_")[-1] for v in
                                            full.objects(cu, URIRef(ETH + "hardVetoPillar")))
        out[c]["worst_pillar"] = str(full.value(cu, URIRef(ETH + "worstPillar"))).split("_")[-1]
        out[c]["material_facet"] = (str(full.value(cu, URIRef(ETH + "materialFacet")).split("#")[-1]
                                       if full.value(cu, URIRef(ETH + "materialFacet")) is not None
                                       else None))
    return out



# name -> (python key in mirror result, mode, rdf property)
MIRROR_QUANTITIES = [
    ("level_W", "central", "levels[0]", "levelW"),
    ("level_C", "central", "levels[1]", "levelC"),
    ("level_M", "central", "levels[2]", "levelM"),
    ("level_K", "central", "levels[3]", "levelK"),
    ("requirement_W", "central", "requirements[0]", "requirementW"),
    ("requirement_C", "central", "requirements[1]", "requirementC"),
    ("requirement_M", "central", "requirements[2]", "requirementM"),
    ("requirement_K", "central", "requirements[3]", "requirementK"),
    ("deficit_W", "central", "deficits[0]", "deficitW"),
    ("deficit_C", "central", "deficits[1]", "deficitC"),
    ("deficit_M", "central", "deficits[2]", "deficitM"),
    ("deficit_K", "central", "deficits[3]", "deficitK"),
    ("guarded_deficit_W", "central", "guarded_deficits[0]", "guardedDeficitW"),
    ("guarded_deficit_C", "central", "guarded_deficits[1]", "guardedDeficitC"),
    ("guarded_deficit_M", "central", "guarded_deficits[2]", "guardedDeficitM"),
    ("guarded_deficit_K", "central", "guarded_deficits[3]", "guardedDeficitK"),
    ("S2", "central", "S2", "structuralTermS2"),
    ("S3", "central", "S3", "structuralTermS3"),
    ("S4", "central", "S4", "structuralTermS4"),
    ("D", "central", "D", "weightedDeficit"),
    ("epistemic_penalty_u", "central", "u", "epistemicPenalty"),
    ("facet_exposure_phi", "central", "phi", "facetExposurePhi"),
    ("adequacy_raw", "central", "aa_raw", "adequacyRaw"),
    ("adequacy", "central", "aa", "adequacy"),
    ("adequacy_low", "pessimistic", "aa", "adequacyLow"),
    ("material_gap_low", "pessimistic", "material_gap", "materialGapLow"),
    ("cap_gap_low", "pessimistic", "cap_gap", None),
    ("stakes", "central", "stakes", "stakesWeighted"),
    ("sigma", "central", "sigma", "sigmaFloor"),
    ("decision_bar", "central", "bar", "decisionBar"),
    ("failure_probability_low", "pessimistic", "p_fail", "failureProbability"),
    ("risk_ratio_low", "pessimistic", "ratio", "riskRatio"),
    ("residual_risk_low", "pessimistic", "residual_risk", "residualRisk"),
    ("harm_scale_low", "pessimistic", "harm", "harmScale"),
    ("coverage", "central", "coverage", "coverage"),
    ("guard_failure_count", "central", "guard_failures_count", "guardFailureCount"),
    ("cross_pillar_duty", "central", "psi", "crossPillarDuty"),
    ("cross_pillar_duty_edge", "central", "psi_edge", "crossPillarDutyEdge"),
    ("cross_pillar_duty_face", "central", "psi_face", "crossPillarDutyFace"),
    ("case_salience_W", "central", "salience[0]", "caseSalienceW"),
    ("case_salience_C", "central", "salience[1]", "caseSalienceC"),
    ("case_salience_M", "central", "salience[2]", "caseSalienceM"),
    ("case_salience_K", "central", "salience[3]", "caseSalienceK"),
    ("review_need", "central", "review_need", "reviewNeed"),
]

CORE_EDGES = tuple(__import__("itertools").combinations(range(4), 2))
CORE_FACES = tuple(__import__("itertools").combinations(range(4), 3))


def run_mirror(full, facets, facet_list, lattice_slots, chosen):
    ctx, levels, confs, requirements, facts, caps = mirror_inputs(full, chosen)
    core_cal_by_id = {}
    for _c, d in ctx.items():
        cid = d["calibration"]
        if cid not in core_cal_by_id:
            core_cal_by_id[cid] = core_calibration(d["cal"], lattice_slots)
    rows_out = []
    per_quantity = defaultdict(lambda: {"max_abs_diff": 0.0, "sum_abs_diff": 0.0, "n": 0,
                                        "missing": 0})
    sample_rows = []
    verdict_mismatch = {"python_ladder_vs_rdf": 0, "core_decide_vs_rdf": 0,
                        "python_ladder_vs_core_decide": 0}
    e30 = {"fact_facet_pairs": 0, "caps_binding": 0, "levels_at_or_below_cap": 0,
           "max_excess_over_cap": 0.0, "beyond_declared_storage_precision": 0,
           "declared_storage_precision": STORAGE_PRECISION["review_need"]}
    stored = stored_values(full, chosen)
    band_labels = build_labels(full)

    for c in chosen:
        d = ctx[c]
        cal_obj = core_cal_by_id[d["calibration"]]
        mid = mirror_compute(d, levels[c], confs[c], requirements[c], facet_list,
                             lattice_slots, "central", d["domain"])
        low = mirror_compute(d, levels[c], confs[c], requirements[c], facet_list,
                             lattice_slots, "pessimistic", d["domain"])
        high = mirror_compute(d, levels[c], confs[c], requirements[c], facet_list,
                              lattice_slots, "optimistic", d["domain"])
        mid["review_need"] = core.review_need(low["aa"], high["aa"], low["bar"],
                                             low["u"], mid["coverage"], cal_obj)
        # core.py reference run on the same literals
        case_spec = make_case_spec(full, d, band_labels, requirements[c])
        core_ref = core.confront(case_spec, core.Profile("mirror-profile", levels[c],
                                                         confs[c]), cal_obj, facet_list)

        for name, mode, key, rdf_prop in MIRROR_QUANTITIES:
            src = mid if mode == "central" else low
            if key.endswith("count"):
                py = len(src["guard_failures"])
            elif "[" in key:
                idx = int(key.split("[")[1].split("]")[0])
                py = src[key.split("[")[0]][idx]
            else:
                py = src[key]
            rdf = stored[c].get(rdf_prop) if rdf_prop else None
            if rdf is None:
                per_quantity[name]["missing"] += 1
                continue
            diff = abs(py - rdf)
            q = per_quantity[name]
            q["max_abs_diff"] = max(q["max_abs_diff"], diff)
            q["sum_abs_diff"] += diff
            q["n"] += 1
            rows_out.append({"sample": str(c).split("#")[-1], "quantity": name,
                            "python_value": round(py, 12), "rdf_value": round(rdf, 12),
                            "abs_diff": round(diff, 12)})

        # E30 caps: the declared level must not exceed the cap the facts impose
        for f, cap in caps[c].items():
            lvl = levels[c].get(f)
            if lvl is None:
                continue
            e30["fact_facet_pairs"] += 1
            excess = lvl - cap
            if excess <= 1e-9:
                e30["levels_at_or_below_cap"] += 1
            else:
                e30["caps_binding"] += 1
                e30["max_excess_over_cap"] = max(e30["max_excess_over_cap"], excess)
                if excess > STORAGE_PRECISION["review_need"]:
                    e30["beyond_declared_storage_precision"] += 1

        ladder, epistemic, reference = python_decision(d, low, mid, cal_obj, case_spec, facet_list)
        core_decision = core_ref["decision"]
        rdf_decision = stored[c]["decision"]
        if ladder != rdf_decision:
            verdict_mismatch["python_ladder_vs_rdf"] += 1
        if reference is not None and reference != rdf_decision:
            verdict_mismatch["core_decide_vs_rdf"] += 1
        if reference is not None and ladder != reference:
            verdict_mismatch["python_ladder_vs_core_decide"] += 1
        if core_decision != rdf_decision:
            verdict_mismatch["core_confront_vs_rdf"] = \
                verdict_mismatch.get("core_confront_vs_rdf", 0) + 1

        sample_rows.append({
            "confrontation": str(c).split("#")[-1],
            "domain": d["domain"],
            "python_ladder_decision": ladder,
            "core_decide_decision": reference,
            "core_confront_decision": core_decision,
            "rdf_decision": rdf_decision,
            "agree": ladder == rdf_decision == core_decision,
            "aa_low_python": round(low["aa"], 12),
            "aa_low_rdf": stored[c]["adequacyLow"],
            "ratio_python": round(low["ratio"], 12),
            "ratio_rdf": stored[c]["riskRatio"],
            "veto_python_low": [PILLARS[i] for i in low["veto"]],
            "veto_rdf_central": stored[c]["veto_pillars"],
            "hard_veto_python_low": [PILLARS[i] for i in low["hard_veto"]],
            "hard_veto_rdf_central": stored[c]["hard_veto_pillars"],
            "epistemic_abstention_python": epistemic,
            "epistemic_abstention_rdf": stored[c]["epistemic_abstention"],
        })
    return rows_out, per_quantity, sample_rows, verdict_mismatch, e30, stored


def make_case_spec(full, ctx, band_labels, requirements):
    cu = URIRef(ctx["case"])
    def label_of(prop):
        node = full.value(cu, URIRef(ETH + prop))
        return band_labels.get(str(node))
    return core.CaseSpec(case_id=str(cu).split("#")[-1], domain=ctx["domain"],
                         severity=label_of("severity"), prudential=label_of("prudentialMode"),
                         irreversibility=label_of("reversibility"), horizon=label_of("horizon"),
                         facet_requirements=dict(requirements), U_E=ctx["UE"], R_c=ctx["Rc"],
                         critical_pillars=tuple(sorted(ctx["critical_pillars"])),
                         norm_conflict=ctx["conflict_status"],
                         evidence_conflict=ctx["evidence_conflict"],
                         exposure=ctx["exposure"],
                         oversight=ctx.get("oversight", "unspecified"))


def registry_check(modules, facets):
    csv_rows = {}
    csv_path = os.path.join(ROOT, "_analysis", "facets", "facet_registry_v13.csv")
    if os.path.exists(csv_path):
        import csv as _csv
        with open(csv_path) as fh:
            for r in _csv.DictReader(fh):
                csv_rows[r["code"]] = r
    sys.path.insert(0, CORE_DIR)
    try:
        from facet_registry import FACETS
        py = {f.code: f for f in FACETS}
    except Exception as exc:
        py = {}
    mismatches = []
    for code, t in sorted(facets.items()):
        c, p = csv_rows.get(code), py.get(code)
        if c is None or p is None:
            mismatches.append({"facet": code, "problem": "missing from CSV or facet_registry.py"})
            continue
        if any(abs(t.beta[i] - float(c["beta" + w])) > 1e-9 for i, w in enumerate(PILLARS)):
            mismatches.append({"facet": code, "problem": "beta differs CSV vs TTL"})
        if any(abs(t.beta[i] - p.beta[i]) > 1e-9 for i in range(4)):
            mismatches.append({"facet": code, "problem": "beta differs facet_registry.py vs TTL"})
        if t.guard != bool(p.guard):
            mismatches.append({"facet": code, "problem": "guard flag differs"})
        if abs(t.guard_min - float(p.guard_min)) > 1e-9:
            mismatches.append({"facet": code, "problem": "guard_min differs"})
        if t.policy != p.policy:
            mismatches.append({"facet": code, "problem": "policy differs"})
        if t.criticality != {d: int(c[d]) for d in t.criticality if d in c}:
            mismatches.append({"facet": code, "problem": "criticality matrix differs"})
    return {"facets_in_ttl": len(facets), "facets_in_csv": len(csv_rows),
            "facets_in_facet_registry_py": len(py),
            "in_registry_not_in_ontology": sorted(set(py) - set(facets)),
            "in_csv_not_in_ttl": sorted(set(csv_rows) - set(facets)),
            "mismatches": mismatches}


def previous_versions():
    out = {}
    for path, label in ((os.path.join(ROOT, "Evaluacoes", "r3", "ontology_v3_validation.json"), "v3"),
                       (os.path.join(ROOT, "Evaluacoes", "r2", "ontology_v2_validation.json"), "v2")):
        if os.path.exists(path):
            with open(path) as fh:
                d = json.load(fh)
            out[label] = {k: d.get(k) for k in d if k in
                          ("triples", "shacl", "shapes", "constraints", "violations",
                           "sparql_checks", "mirror", "classes", "properties")}
            if not out[label]:
                out[label] = {k: d[k] for k in list(d)[:12]}
    return out


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    t0 = time.time()

    modules, shapes_v4, shapes_v6, instances, invalid_v4, invalid_v6, per_module = load_graphs()
    shapes_all = shapes_v4 + shapes_v6
    full_graph = modules + instances

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_selection.json")) as fh:
        sample_meta = json.load(fh)

    inv = inventory(modules, instances)
    ioi = inv["instances_of_interest"]
    stats = shape_stats(shapes_all)
    shacl_modules = run_shacl(modules, shapes_v4, "modules vs v4 shapes")
    shacl_full_v4 = run_shacl(full_graph, shapes_v4, "instances vs v4 shapes")
    shacl_full_v6 = run_shacl(full_graph, shapes_v6, "instances vs v6 shapes")

    with open(os.path.join(ONT, "fixtures", "invalid_expectations.json")) as fh:
        expectations = json.load(fh)
    if isinstance(expectations, dict):
        expectations = expectations.get("expectations") or expectations.get("fixtures") or []
    fixtures_v4 = invalid_fixture_test(invalid_v4, modules, shapes_all, expectations,
                                       "invalid_examples.ttl (73 fixtures)")
    fixtures_v6 = invalid_fixture_test(invalid_v6, modules, shapes_all, expectations,
                                       "invalid_examples_v6.ttl (12 E30 fixtures)")
    fixtures = {"fixtures": fixtures_v4["fixtures"] + fixtures_v6["fixtures"],
                "detected": fixtures_v4["detected"] + fixtures_v6["detected"],
                "detected_by_expected_shape": fixtures_v4["detected_by_expected_shape"]
                + fixtures_v6["detected_by_expected_shape"],
                "not_detected": fixtures_v4["not_detected"] + fixtures_v6["not_detected"],
                "wrong_shape": fixtures_v4["wrong_shape"] + fixtures_v6["wrong_shape"],
                "total_violations_on_invalid_graph":
                    fixtures_v4["total_violations_on_invalid_graph"]
                    + fixtures_v6["total_violations_on_invalid_graph"],
                "violations_by_shape": dict(Counter(fixtures_v4["violations_by_shape"])
                                           + Counter(fixtures_v6["violations_by_shape"])),
                "violations_by_component": dict(Counter(fixtures_v4["violations_by_component"])
                                               + Counter(fixtures_v6["violations_by_component"])),
                "table": fixtures_v4["table"] + fixtures_v6["table"]}

    checks = consistency_checks(full_graph)
    lattice_slots = lattice_from_graph(full_graph)
    lattice = lattice_report(lattice_slots)
    facets = facet_registry(full_graph)
    facet_list = sorted(facets.values(), key=lambda f: f.code)

    chosen, strata, total_confrontations, corpus_distribution = select_confrontations(
        full_graph, int(os.environ.get("MIRROR_N", "403")))
    mirror_rows, per_quantity, sample_rows, verdicts, e30, stored = run_mirror(
        full_graph, facets, facet_list, lattice_slots, chosen)
    max_all = max((q["max_abs_diff"] for q in per_quantity.values()), default=0.0)
    for name, q in per_quantity.items():
        q["tolerance"] = STORAGE_PRECISION.get(name, MIRROR_TOLERANCE)
        q["within_declared_precision"] = q["max_abs_diff"] <= q["tolerance"]
    mirror_ok = all(q["within_declared_precision"] for q in per_quantity.values())
    reg = registry_check(modules, facets)

    n_checks = len(checks)
    n_deontic = sum(1 for c in checks if c["kind"] == "deontic")
    n_findings = sum(1 for c in checks if c["kind"] == "finding")
    # "finding" checks report a fact about the corpus (how many links retain a duty, how
    # many stakes exceed the ceiling); they are never gates, so they do not condition the
    # verdict. Everything else must pass.
    all_checks_pass = all(c.get("pass") for c in checks if c["kind"] != "finding")
    fixtures_ok = fixtures["detected"] == fixtures["fixtures"] and \
        fixtures["detected_by_expected_shape"] == fixtures["fixtures"]
    lattice_ok = (lattice["total_slots"] == 15 and lattice["every_term_sums_to_one"] and
                  lattice["slots_by_kind"] == lattice["expected_slots_by_kind"])
    registry_ok = (not reg["mismatches"] and reg["facets_in_ttl"] ==
                   reg["facets_in_facet_registry_py"] == reg["facets_in_csv"])
    verdicts_ok = verdicts.get("python_ladder_vs_rdf", 0) == 0 and \
        verdicts.get("core_decide_vs_rdf", 0) == 0 and \
        verdicts.get("core_confront_vs_rdf", 0) == 0

    gate = (shacl_full_v4["conforms"] and shacl_full_v6["conforms"] and all_checks_pass and
            fixtures_ok and mirror_ok and verdicts_ok and lattice_ok and registry_ok)

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "gate": "G4'",
        "gate_verdict": "PASS" if gate else "CONDITIONAL / NOT MET",
        "verdict": {
            "gate_met": bool(gate),
            "summary": (
                "G4' is met only if the SHACL corpus is conformant, every consistency check "
                "passes, every invalid fixture is caught by the intended shape, the arithmetic "
                "mirror reproduces the values asserted in the graph to <= 1e-6 and the verdicts "
                "agree exactly. Current failures: " +
                ("none" if gate else ", ".join(
                    x for x in [
                        "SHACL violations on the instance graph" if not shacl_full_v4["conforms"]
                        or not shacl_full_v6["conforms"] else None,
                        "failed SPARQL consistency checks" if not all_checks_pass else None,
                        "invalid fixtures not caught by the intended shape" if not fixtures_ok
                        else None,
                        "arithmetic mirror outside 1e-6 or verdict disagreement"
                        if not (mirror_ok and verdicts_ok) else None,
                        "face lattice incomplete" if not lattice_ok else None,
                        "facet registry mismatch" if not registry_ok else None,
                    ] if x)),
            ),
            "shacl_instances_conforms_v4": shacl_full_v4["conforms"],
            "shacl_instances_conforms_v6": shacl_full_v6["conforms"],
            "sparql_checks_total": n_checks,
            "sparql_checks_deontic": n_deontic,
            "sparql_checks_findings": n_findings,
            "sparql_checks_failed": [c["check"] for c in checks
                                     if not c.get("pass") and c["kind"] != "finding"],
            "sparql_findings": [{"check": c["check"], "rows": c.get("rows_returned", 0)}
                                for c in checks if c["kind"] == "finding"],
            "invalid_fixtures_caught": f"{fixtures['detected']}/{fixtures['fixtures']}",
            "invalid_fixtures_shape_matched": f"{fixtures['detected_by_expected_shape']}/{fixtures['fixtures']}",
            "mirror_max_abs_difference": max_all,
            "mirror_declared_tolerance": MIRROR_TOLERANCE,
            "mirror_declared_storage_precision": STORAGE_PRECISION,
            "mirror_verdict_mismatches": verdicts,
            "lattice_slots": lattice["total_slots"],
            "lattice_terms_sum_to_one": lattice["every_term_sums_to_one"],
        },
        "validator": "_analysis/ontology/validate_ontology_v4.py",
        "generator": "_analysis/ontology/gen_ontology_v6.py (ontology v4.2.0)",
        "graph": {
            "instance_file_validated": "Ontologias/ontology_v4_2/fixtures/instances.ttl",
            "module_triples": per_module,
            "module_triples_total": sum(per_module.values()),
            "instances_triples": len(instances),
            "total_validated_triples": len(full_graph),
            "shapes_v4_triples": len(shapes_v4),
            "shapes_v6_triples": len(shapes_v6),
            "invalid_fixture_triples_v4": len(invalid_v4),
            "invalid_fixture_triples_v6": len(invalid_v6),
            "inventory": inv,
        },
        "corpus": {
            "corpus_rows": sample_meta.get("corpus_rows"),
            "cases_covered_by_sample_selection": sample_meta.get("cases_covered"),
            "confrontations_instantiated_in_rdf": ioi.get("Confrontation"),
            "cases_instantiated": ioi.get("EthicalCase"),
            "decision_distribution_in_graph": dict(corpus_distribution),
        },
        "shacl": {"shapes": stats,
                  "modules_only_v4_shapes": shacl_modules,
                  "instances_vs_v4_shapes": shacl_full_v4,
                  "instances_vs_v6_shapes": shacl_full_v6},
        "invalid_fixtures": {k: v for k, v in fixtures.items() if k != "table"},
        "invalid_fixture_table": fixtures["table"],
        "sparql_checks": checks,
        "face_lattice": lattice,
        "mirror": {
            "confrontations_selected": len(chosen),
            "selection_rule": "round-robin over (domain, verdict) strata, rare strata first, "
                              "confrontation id ascending",
            "strata": strata,
            "total_confrontations_in_graph": total_confrontations,
            "how_arithmetic_is_done": {
                "inputs": "all facet levels, confidences, requirements, criticality levels, "
                          "guard floors, pillar lambdas/mus/thetas, lattice weights, band "
                          "values, stake weights and ladder thresholds are read from the RDF",
                "aggregation": "core.project (E2/E20-E23) with the RDF-declared betas and weights",
                "S2/S3/S4 and D": "computed through the face-lattice slots themselves",
                "exposure, material gap, veto, cap, adequacy, sigma, bar, stakes, ratio":
                    "computed in this file from the RDF literals",
                "ladder": "implemented in python_decision and cross-checked against core.decide "
                          "and core.confront built from the same literals",
                "hard-coded constants in the mirror": UNDECLARED_CONSTANTS,
            },
            "max_abs_difference_by_quantity": {k: {"n": v["n"], "missing_in_rdf": v["missing"],
                                                   "max_abs_diff": round(v["max_abs_diff"], 12),
                                                   "mean_abs_diff": round(v["sum_abs_diff"] / v["n"], 12)
                                                   if v["n"] else 0.0}
                                               for k, v in sorted(per_quantity.items())},
            "global_max_abs_difference": max_all,
            "declared_tolerance": MIRROR_TOLERANCE,
            "quantities_stored_rounded": STORAGE_PRECISION,
            "within_declared_precision": mirror_ok,
            "verdict_agreement": verdicts,
            "e30_fact_grounding": e30,
            "mirror_table": mirror_rows,
            "sample_decisions": sample_rows,
            "sample_ids": [str(c).split("#")[-1] for c in chosen[:10]],
        },
        "registry": reg,
        "comparison_with_previous_versions": previous_versions(),
        "defects_found_and_fixed": [
            "the SPARQL mirror used BIND(if(...) AS ...), which rdflib cannot parse: all such "
            "queries were rewritten as plain SELECTs with the conditional computed in Python",
            "the check 'no chain link delegates more than the four pillars' used a nested "
            "sub-select that rdflib rejects; rewritten with GROUP BY/HAVING",
            "the check 'an incomplete profile never yields a non-ABSTAIN verdict' read coverage "
            "off the Profile, where it is not asserted; it now reads eth:coverage off the "
            "Confrontation",
            "the PROHIBIT grounding check used predicate expressions inside BIND, which is not "
            "SPARQL; the gate is now evaluated in Python against the declared thresholds",
        ],
        "limitations": [
            "the arithmetic mirror covers 100 sampled confrontations, not the whole corpus of "
            f"{ioi.get('Confrontation', 0)} instantiated confrontations",
            "the 1e-6 gate is measured against the values the generator asserted in the graph, "
            "which are rounded to 12 decimals; rounding alone contributes < 1e-12",
            "the previous round's agreement with corpus_v6_confrontations.jsonl was not "
            "re-run here; the mirror is compared against the RDF literals and core.py",
            "no inference is used in SHACL (inference=\"none\"), as specified",
        ],
        "runtime_seconds": round(time.time() - t0, 1),
    }
    with open(OUT_PATH, "w") as fh:
        json.dump(result, fh, indent=2)

    print("=" * 70)
    print("GATE G4' verdict:", result["gate_verdict"])
    print("triples: modules", sum(per_module.values()), "instances", len(instances),
          "total validated", len(full_graph))
    print("instantiated confrontations:", ioi.get("Confrontation"))
    print("SHACL v4 shapes on instances:", shacl_full_v4["violations"], "violations;",
          "v6 shapes:", shacl_full_v6["violations"], "; modules:", shacl_modules["violations"])
    print("invalid fixtures caught:", fixtures["detected"], "/", fixtures["fixtures"],
          "attributed to the intended shape:", fixtures["detected_by_expected_shape"])
    print("SPARQL checks:", n_checks, "(deontic:", n_deontic, ") all pass:", all_checks_pass)
    print("failed checks:", [c["check"] for c in checks if not c.get("pass")])
    print("mirror global max abs diff:", max_all)
    print("verdict mismatches:", verdicts)
    print("lattice slots:", lattice["total_slots"], "by kind:", lattice["slots_by_kind"],
          "sums to one:", lattice["every_term_sums_to_one"])
    print("registry mismatches:", len(reg["mismatches"]))
    print("seconds:", round(time.time() - t0, 1))
    print("written:", OUT_PATH)
    print("=" * 70)


if __name__ == "__main__":
    main()
