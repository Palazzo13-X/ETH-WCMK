"""F3: generate ETH-WCMK ontology v2 (consolidated modules + SHACL shapes).

Single source of truth: _analysis/formal_core/facet_registry.py.

Fixes over v1 (from the read-only audit in the plan, Anexo A):
  - facets are owl:NamedIndividual, not owl:Class;
  - one namespace family (https://ethwcmk.org/ontology/*) instead of three;
  - malformed rdf: prefix (http://www.w3.org/1999-02-22-rdf-syntax-ns#) removed;
  - the bridge layer is now covered by SHACL shapes plus negative fixtures;
  - normalisation (sum beta = 1) and the arithmetic of Eq. (8)-(11) are machine-checkable;
  - the decision vocabulary is a closed, ordered set;
  - the face lattice (15 relational slots) is made explicit.
"""
import os, sys
from itertools import combinations
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, RDFS, OWL, SKOS, XSD

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "formal_core"))
from facet_registry import FACETS, DOMAINS, DOMAIN_LABELS

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "..", "Ontologias", "ontology_v2"))
os.makedirs(os.path.join(OUT, "shapes"), exist_ok=True)
os.makedirs(os.path.join(OUT, "fixtures"), exist_ok=True)

BASE = "https://ethwcmk.org/ontology/"
ETH = Namespace(BASE + "eth/")
FAC = Namespace(BASE + "facet/")
DOM = Namespace(BASE + "domain/")
PIL = Namespace(BASE + "pillar/")
SLT = Namespace(BASE + "slot/")
CAL = Namespace(BASE + "calibration/")
DEC = Namespace(BASE + "decision/")
POL = Namespace(BASE + "policy/")
SH = Namespace("http://www.w3.org/ns/shacl#")

PREFIXES = {"eth": ETH, "facet": FAC, "domain": DOM, "pillar": PIL, "slot": SLT,
            "cal": CAL, "decision": DEC, "policy": POL, "sh": SH,
            "owl": OWL, "rdf": RDF, "rdfs": RDFS, "skos": SKOS, "xsd": XSD}

PILLAR_NAMES = ("Want", "Can", "Must", "Know")
ZERO = Literal(0, datatype=XSD.decimal)
ONE = Literal(1, datatype=XSD.decimal)


def graph():
    G = Graph()
    for k, v in PREFIXES.items():
        G.bind(k, v)
    return G


def add_class(G, name):
    G.add((ETH[name], RDF.type, OWL.Class))
    G.add((ETH[name], RDFS.label, Literal(name, lang="en")))


def obj_prop(G, name, domain=None, rng=None, functional=False):
    G.add((ETH[name], RDF.type, OWL.ObjectProperty))
    if domain:
        G.add((ETH[name], RDFS.domain, domain))
    if rng:
        G.add((ETH[name], RDFS.range, rng))
    if functional:
        G.add((ETH[name], RDF.type, OWL.FunctionalProperty))
    G.add((ETH[name], RDFS.label, Literal(name, lang="en")))


def data_prop(G, name, domain, typ, functional=False):
    G.add((ETH[name], RDF.type, OWL.DatatypeProperty))
    G.add((ETH[name], RDFS.domain, domain))
    G.add((ETH[name], RDFS.range, typ))
    if functional:
        G.add((ETH[name], RDF.type, OWL.FunctionalProperty))
    G.add((ETH[name], RDFS.label, Literal(name, lang="en")))


def core():
    G = graph()
    onto = URIRef(BASE)
    G.add((onto, RDF.type, OWL.Ontology))
    G.add((onto, RDFS.label, Literal("ETH-WCMK ontology v2", lang="en")))
    G.add((onto, RDFS.comment, Literal(
        "Consolidated namespace replacing eth2.local/ontology, ethwcmk.org/ontology and "
        "eth2.ai/ontology. Facets are individuals; the tetrahedron is a relational index "
        "(face lattice of the 3-simplex), not a metric state space.", lang="en")))

    classes = ("EthicalCase", "Domain", "SeverityBand", "PrudentialMode", "ReversibilityGrade",
               "Pillar", "RelationalSlot", "Facet", "FacetRequirement", "FacetDomainCriticality",
               "AgencyProfile", "FacetLevel", "Confrontation", "Calibration", "Decision",
               "AggregationPolicy")
    for c in classes:
        add_class(G, c)
    for a, b in combinations(classes, 2):
        if {a, b} in ({"EthicalCase", "AgencyProfile"}, {"Facet", "Pillar"},
                      {"Confrontation", "Calibration"}, {"Facet", "Decision"},
                      {"FacetLevel", "FacetRequirement"}, {"RelationalSlot", "Facet"}):
            G.add((ETH[a], OWL.disjointWith, ETH[b]))

    obj_prop(G, "hasDomain", ETH["EthicalCase"], ETH["Domain"], functional=True)
    obj_prop(G, "hasSeverity", ETH["EthicalCase"], ETH["SeverityBand"], functional=True)
    obj_prop(G, "hasPrudentialMode", ETH["EthicalCase"], ETH["PrudentialMode"], functional=True)
    obj_prop(G, "hasReversibility", ETH["EthicalCase"], ETH["ReversibilityGrade"], functional=True)
    obj_prop(G, "criticalPillar", ETH["EthicalCase"], ETH["Pillar"])
    obj_prop(G, "requiresFacet", ETH["FacetRequirement"], ETH["Facet"])
    obj_prop(G, "requirementForCase", ETH["FacetRequirement"], ETH["EthicalCase"])
    obj_prop(G, "assessedBy", ETH["Confrontation"], ETH["AgencyProfile"], functional=True)
    obj_prop(G, "concernsCase", ETH["Confrontation"], ETH["EthicalCase"], functional=True)
    obj_prop(G, "usesCalibration", ETH["Confrontation"], ETH["Calibration"], functional=True)
    obj_prop(G, "decisionOf", ETH["Confrontation"], ETH["Decision"], functional=True)
    obj_prop(G, "vetoPillar", ETH["Confrontation"], ETH["Pillar"])
    obj_prop(G, "slotInvolves", ETH["RelationalSlot"], ETH["Pillar"])
    obj_prop(G, "levelOfFacet", ETH["FacetLevel"], ETH["Facet"], functional=True)
    obj_prop(G, "hasFacetLevel", ETH["AgencyProfile"], ETH["FacetLevel"])
    obj_prop(G, "contributedBy", ETH["Pillar"], ETH["Facet"])
    obj_prop(G, "criticalityOfFacet", ETH["FacetDomainCriticality"], ETH["Facet"], functional=True)
    obj_prop(G, "criticalityInDomain", ETH["FacetDomainCriticality"], ETH["Domain"], functional=True)
    obj_prop(G, "aggregationPolicy", ETH["Facet"], ETH["AggregationPolicy"], functional=True)
    obj_prop(G, "alignedWithPillar", ETH["RelationalSlot"], ETH["Pillar"], functional=True)

    data_prop(G, "domainCode", ETH["Domain"], XSD.string, functional=True)
    data_prop(G, "facetCode", ETH["Facet"], XSD.string, functional=True)
    data_prop(G, "betaWant", ETH["Facet"], XSD.decimal, functional=True)
    data_prop(G, "betaCan", ETH["Facet"], XSD.decimal, functional=True)
    data_prop(G, "betaMust", ETH["Facet"], XSD.decimal, functional=True)
    data_prop(G, "betaKnow", ETH["Facet"], XSD.decimal, functional=True)
    data_prop(G, "facetWeight", ETH["Facet"], XSD.decimal, functional=True)
    data_prop(G, "hasGuard", ETH["Facet"], XSD.boolean, functional=True)
    data_prop(G, "guardMin", ETH["Facet"], XSD.decimal, functional=True)
    data_prop(G, "source", ETH["Facet"], XSD.string, functional=True)
    data_prop(G, "criticalityLevel", ETH["FacetDomainCriticality"], XSD.integer, functional=True)
    data_prop(G, "requirementValue", ETH["FacetRequirement"], XSD.decimal, functional=True)
    data_prop(G, "observedLevel", ETH["FacetLevel"], XSD.decimal, functional=True)
    data_prop(G, "confidence", ETH["FacetLevel"], XSD.decimal, functional=True)
    data_prop(G, "pillarDeficit", ETH["Confrontation"], XSD.decimal)
    for name in ("Want", "Can", "Must", "Know"):
        data_prop(G, f"level{name}", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "facetDeficit", ETH["Confrontation"], XSD.decimal)
    data_prop(G, "adequacy", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "adequacyRaw", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "residualRisk", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "contextualRisk", ETH["EthicalCase"], XSD.decimal, functional=True)
    data_prop(G, "epistemicUncertainty", ETH["EthicalCase"], XSD.decimal, functional=True)
    data_prop(G, "riskFloor", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "structuralTermPair", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "structuralTermTriple", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "structuralTermInterior", ETH["Confrontation"], XSD.decimal, functional=True)
    data_prop(G, "shapeWant", ETH["AgencyProfile"], XSD.decimal, functional=True)
    data_prop(G, "shapeCan", ETH["AgencyProfile"], XSD.decimal, functional=True)
    data_prop(G, "shapeMust", ETH["AgencyProfile"], XSD.decimal, functional=True)
    data_prop(G, "shapeKnow", ETH["AgencyProfile"], XSD.decimal, functional=True)
    data_prop(G, "magnitude", ETH["AgencyProfile"], XSD.decimal, functional=True)
    data_prop(G, "completeness", ETH["AgencyProfile"], XSD.decimal, functional=True)
    data_prop(G, "slotArity", ETH["RelationalSlot"], XSD.integer, functional=True)
    data_prop(G, "gamma", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "eta", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "omega", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "rho", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "delta", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "hardVetoDelta", ETH["Calibration"], XSD.decimal, functional=True)
    for nm in ("barBase", "barSeverity", "barIrreversibility", "barPrudential",
               "prohibitMargin", "guardsMargin"):
        data_prop(G, nm, ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "penaltyBudget", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "severityValue", ETH["SeverityBand"], XSD.decimal, functional=True)
    data_prop(G, "prudentialValue", ETH["PrudentialMode"], XSD.decimal, functional=True)
    data_prop(G, "irreversibilityValue", ETH["ReversibilityGrade"], XSD.decimal, functional=True)
    data_prop(G, "permissivenessRank", ETH["Decision"], XSD.integer, functional=True)
    for i, name in enumerate(PILLAR_NAMES):
        data_prop(G, f"lambda{name}", ETH["Calibration"], XSD.decimal, functional=True)
        data_prop(G, f"vetoThreshold{name}", ETH["Calibration"], XSD.decimal, functional=True)
    data_prop(G, "edgeWeight", ETH["Calibration"], XSD.decimal)
    data_prop(G, "faceWeight", ETH["Calibration"], XSD.decimal)
    data_prop(G, "pillarIndex", ETH["Pillar"], XSD.integer, functional=True)
    return G


def facets():
    G = graph()
    for f in FACETS:
        fi = FAC[f.code]
        G.add((fi, RDF.type, ETH["Facet"]))
        G.add((fi, RDF.type, OWL.NamedIndividual))
        G.add((fi, ETH["facetCode"], Literal(f.code)))
        G.add((fi, SKOS.prefLabel, Literal(f.label, lang="en")))
        G.add((fi, RDFS.label, Literal(f.label, lang="en")))
        G.add((fi, ETH["betaWant"], Literal(f.beta[0], datatype=XSD.decimal)))
        G.add((fi, ETH["betaCan"], Literal(f.beta[1], datatype=XSD.decimal)))
        G.add((fi, ETH["betaMust"], Literal(f.beta[2], datatype=XSD.decimal)))
        G.add((fi, ETH["betaKnow"], Literal(f.beta[3], datatype=XSD.decimal)))
        G.add((fi, ETH["facetWeight"], Literal(f.weight, datatype=XSD.decimal)))
        G.add((fi, ETH["hasGuard"], Literal(f.guard, datatype=XSD.boolean)))
        if f.guard:
            G.add((fi, ETH["guardMin"], Literal(f.guard_min, datatype=XSD.decimal)))
        G.add((fi, ETH["aggregationPolicy"], POL[f.policy]))
        G.add((fi, ETH["source"], Literal(f.source)))
        for i, b in enumerate(f.beta):
            if b > 0:
                G.add((PIL[PILLAR_NAMES[i]], ETH["contributedBy"], fi))
        for d in DOMAINS:
            bn = BNode()
            G.add((bn, RDF.type, ETH["FacetDomainCriticality"]))
            G.add((bn, ETH["criticalityOfFacet"], fi))
            G.add((bn, ETH["criticalityInDomain"], DOM[d]))
            G.add((bn, ETH["criticalityLevel"], Literal(f.criticality[d], datatype=XSD.integer)))
    for pol in ("weighted_mean", "guarded_weighted_mean", "threshold_override", "uncertainty_penalized_mean"):
        G.add((POL[pol], RDF.type, ETH["AggregationPolicy"]))
        G.add((POL[pol], RDFS.label, Literal(pol, lang="en")))
    return G


def domains_and_context():
    G = graph()
    for d in DOMAINS:
        di = DOM[d]
        G.add((di, RDF.type, ETH["Domain"]))
        G.add((di, RDF.type, OWL.NamedIndividual))
        G.add((di, RDFS.label, Literal(DOMAIN_LABELS[d], lang="en")))
        G.add((di, ETH["domainCode"], Literal(d)))
    for band, val in (("low", 0.25), ("medium", 0.50), ("high", 0.75), ("critical", 1.00)):
        bi = URIRef(BASE + f"severity/{band}")
        G.add((bi, RDF.type, ETH["SeverityBand"]))
        G.add((bi, RDF.type, OWL.NamedIndividual))
        G.add((bi, RDFS.label, Literal(band, lang="en")))
        G.add((bi, ETH["severityValue"], Literal(val, datatype=XSD.decimal)))
    for mode, val in (("standard", 0.0), ("elevated", 0.05), ("maximum", 0.10)):
        mi = URIRef(BASE + f"prudential/{mode}")
        G.add((mi, RDF.type, ETH["PrudentialMode"]))
        G.add((mi, RDF.type, OWL.NamedIndividual))
        G.add((mi, RDFS.label, Literal(mode, lang="en")))
        G.add((mi, ETH["prudentialValue"], Literal(val, datatype=XSD.decimal)))
    for rev, val in (("reversible", 0.0), ("partially_irreversible", 0.5), ("irreversible", 1.0)):
        ri = URIRef(BASE + f"reversibility/{rev}")
        G.add((ri, RDF.type, ETH["ReversibilityGrade"]))
        G.add((ri, RDF.type, OWL.NamedIndividual))
        G.add((ri, RDFS.label, Literal(rev, lang="en")))
        G.add((ri, ETH["irreversibilityValue"], Literal(val, datatype=XSD.decimal)))
    return G


def pillars_lattice():
    G = graph()
    for i, name in enumerate(PILLAR_NAMES):
        p = PIL[name]
        G.add((p, RDF.type, ETH["Pillar"]))
        G.add((p, RDF.type, OWL.NamedIndividual))
        G.add((p, RDFS.label, Literal(name, lang="en")))
        G.add((p, ETH["pillarIndex"], Literal(i, datatype=XSD.integer)))
    for i in range(4):
        for j in range(i + 1, 4):
            G.add((PIL[PILLAR_NAMES[i]], OWL.disjointWith, PIL[PILLAR_NAMES[j]]))
    for k in (1, 2, 3, 4):
        for s in combinations(range(4), k):
            sid = SLT["_".join(PILLAR_NAMES[i][0] for i in s)]
            G.add((sid, RDF.type, ETH["RelationalSlot"]))
            G.add((sid, RDF.type, OWL.NamedIndividual))
            G.add((sid, ETH["slotArity"], Literal(k, datatype=XSD.integer)))
            for i in s:
                G.add((sid, ETH["slotInvolves"], PIL[PILLAR_NAMES[i]]))
            G.add((sid, RDFS.label, Literal(" + ".join(PILLAR_NAMES[i] for i in s), lang="en")))
            if k == 1:
                G.add((sid, ETH["alignedWithPillar"], PIL[PILLAR_NAMES[s[0]]]))
    G.add((URIRef(BASE + "lattice/axiom"), RDFS.comment, Literal(
        "Face lattice of the 3-simplex = non-empty subsets of a 4-set: 4 vertices + 6 edges "
        "+ 4 faces + 1 cell = 15 relational slots.", lang="en")))
    return G


def calibration():
    G = graph()
    c = CAL["v10"]
    G.add((c, RDF.type, ETH["Calibration"]))
    G.add((c, RDF.type, OWL.NamedIndividual))
    for i, v in enumerate((0.30, 0.25, 0.25, 0.20)):
        G.add((c, ETH[f"lambda{PILLAR_NAMES[i]}"], Literal(v, datatype=XSD.decimal)))
    for _ in range(6):
        G.add((c, ETH["edgeWeight"], Literal(1 / 6, datatype=XSD.decimal)))
    for _ in range(4):
        G.add((c, ETH["faceWeight"], Literal(0.25, datatype=XSD.decimal)))
    G.add((c, ETH["gamma"], Literal(0.12, datatype=XSD.decimal)))
    G.add((c, ETH["eta"], Literal(0.05, datatype=XSD.decimal)))
    G.add((c, ETH["omega"], Literal(0.03, datatype=XSD.decimal)))
    G.add((c, ETH["rho"], Literal(0.10, datatype=XSD.decimal)))
    G.add((c, ETH["delta"], Literal(0.05, datatype=XSD.decimal)))
    G.add((c, ETH["penaltyBudget"], Literal(0.35, datatype=XSD.decimal)))
    # veto thresholds: B3 sweep (Evaluacoes/r2/B3_calibration_sweep.json)
    for i, t in enumerate((0.65, 0.60, 0.60, 0.65)):
        G.add((c, ETH[f"vetoThreshold{PILLAR_NAMES[i]}"], Literal(t, datatype=XSD.decimal)))
    G.add((c, ETH["hardVetoDelta"], Literal(0.15, datatype=XSD.decimal)))
    # stakes-aware decision bar (B5 calibrated)
    G.add((c, ETH["barBase"], Literal(0.50, datatype=XSD.decimal)))
    G.add((c, ETH["barSeverity"], Literal(0.20, datatype=XSD.decimal)))
    G.add((c, ETH["barIrreversibility"], Literal(0.05, datatype=XSD.decimal)))
    G.add((c, ETH["barPrudential"], Literal(0.02, datatype=XSD.decimal)))
    G.add((c, ETH["prohibitMargin"], Literal(0.20, datatype=XSD.decimal)))
    G.add((c, ETH["guardsMargin"], Literal(0.15, datatype=XSD.decimal)))
    G.add((c, RDFS.comment, Literal(
        "gamma+eta+omega+rho+delta = 0.35, equal to the declared penalty budget; "
        "lambda sums to 1; edge weights sum to 1; face weights sum to 1.", lang="en")))
    return G


def decisions():
    G = graph()
    for name, rank in (("ABSTAIN", 0), ("PROHIBIT", 1), ("REVIEW_REQUIRED", 2),
                       ("ALLOW_WITH_GUARDS", 3), ("ALLOW", 4)):
        di = DEC[name]
        G.add((di, RDF.type, ETH["Decision"]))
        G.add((di, RDF.type, OWL.NamedIndividual))
        G.add((di, RDFS.label, Literal(name, lang="en")))
        G.add((di, ETH["permissivenessRank"], Literal(rank, datatype=XSD.integer)))
    names = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")
    for a in names:
        for b in names:
            if a != b:
                G.add((DEC[a], OWL.differentFrom, DEC[b]))
    return G


def rdf_list(G, items):
    """Build a proper RDF collection (needed for sh:in closed vocabularies)."""
    head = BNode()
    G.add((head, RDF.type, RDF.List))
    cur = head
    for it in items:
        G.add((cur, RDF.first, it))
        nxt = BNode()
        G.add((cur, RDF.rest, nxt))
        cur = nxt
    G.add((cur, RDF.rest, RDF.nil))
    return head


def add_shape(G, name, cls, props):
    target = URIRef(BASE + "shapes/" + name)
    G.add((target, RDF.type, SH["NodeShape"]))
    G.add((target, SH.targetClass, cls))
    for path, spec in props.items():
        ps = BNode()   # each property shape must be a distinct node
        G.add((target, SH.property, ps))
        G.add((ps, SH.path, path))
        for k, v in spec.items():
            if isinstance(v, list):
                v = rdf_list(G, v)
            elif not isinstance(v, (URIRef, Literal, BNode)):
                v = Literal(str(v))
            G.add((ps, k, v))   # keys are already fully-qualified SHACL predicates
    return target


def shapes():
    G = graph()
    d = SH
    add_shape(G, "FacetShape", ETH["Facet"], {
        ETH["facetCode"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                           d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                           d["datatype"]: XSD.string, d["pattern"]: "^[WCMK][0-9]$"},
        ETH["betaWant"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["betaCan"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["betaMust"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["betaKnow"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["facetWeight"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["hasGuard"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                          d["maxCardinality"]: Literal(1, datatype=XSD.integer), d["datatype"]: XSD.boolean},
        ETH["source"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                        d["maxCardinality"]: Literal(1, datatype=XSD.integer)},
        ETH["aggregationPolicy"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                                   d["maxCardinality"]: Literal(1, datatype=XSD.integer)},
    })
    add_shape(G, "GuardShape", ETH["Facet"], {
        ETH["guardMin"]: {d["minInclusive"]: Literal(0.30, datatype=XSD.decimal),
                         d["maxInclusive"]: Literal(0.90, datatype=XSD.decimal)},
    })
    add_shape(G, "DomainShape", ETH["Domain"], {
        ETH["domainCode"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                            d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                            d["datatype"]: XSD.string, d["pattern"]: "^[A-Z]{2}$"},
    })
    add_shape(G, "CriticalityShape", ETH["FacetDomainCriticality"], {
        ETH["criticalityLevel"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                                  d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                                  d["datatype"]: XSD.integer,
                                  d["minInclusive"]: Literal(1, datatype=XSD.integer),
                                  d["maxInclusive"]: Literal(5, datatype=XSD.integer)},
        ETH["criticalityOfFacet"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                                    d["maxCardinality"]: Literal(1, datatype=XSD.integer)},
        ETH["criticalityInDomain"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                                     d["maxCardinality"]: Literal(1, datatype=XSD.integer)},
    })
    add_shape(G, "PillarShape", ETH["Pillar"], {
        ETH["pillarIndex"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                             d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                             d["datatype"]: XSD.integer,
                             d["minInclusive"]: Literal(0, datatype=XSD.integer),
                             d["maxInclusive"]: Literal(3, datatype=XSD.integer)},
    })
    add_shape(G, "SlotShape", ETH["RelationalSlot"], {
        ETH["slotArity"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                           d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                           d["datatype"]: XSD.integer,
                           d["minInclusive"]: Literal(1, datatype=XSD.integer),
                           d["maxInclusive"]: Literal(4, datatype=XSD.integer)},
        ETH["slotInvolves"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                              d["maxCardinality"]: Literal(4, datatype=XSD.integer)},
    })
    add_shape(G, "CalibrationShape", ETH["Calibration"], {
        ETH["gamma"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(0.30, datatype=XSD.decimal)},
        ETH["eta"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(0.30, datatype=XSD.decimal)},
        ETH["omega"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(0.30, datatype=XSD.decimal)},
        ETH["rho"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(0.50, datatype=XSD.decimal)},
        ETH["delta"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(0.30, datatype=XSD.decimal)},
        ETH["hardVetoDelta"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(0.30, datatype=XSD.decimal)},
    })
    add_shape(G, "DecisionShape", ETH["Decision"], {
        ETH["permissivenessRank"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                                    d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                                    d["datatype"]: XSD.integer,
                                    d["minInclusive"]: Literal(0, datatype=XSD.integer),
                                    d["maxInclusive"]: Literal(4, datatype=XSD.integer)},
    })
    c1 = {d["minCardinality"]: Literal(1, datatype=XSD.integer),
          d["maxCardinality"]: Literal(1, datatype=XSD.integer)}
    add_shape(G, "EthicalCaseShape", ETH["EthicalCase"], {
        ETH["hasDomain"]: c1,
        ETH["hasSeverity"]: dict(c1, **{d["in"]: [URIRef(BASE + f"severity/{b}")
                                                  for b in ("low", "medium", "high", "critical")]}),
        ETH["hasPrudentialMode"]: dict(c1, **{d["in"]: [URIRef(BASE + f"prudential/{m}")
                                                        for m in ("standard", "elevated", "maximum")]}),
        ETH["hasReversibility"]: dict(c1, **{d["in"]: [URIRef(BASE + f"reversibility/{r}")
                                                       for r in ("reversible", "partially_irreversible",
                                                               "irreversible")]}),
        ETH["contextualRisk"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["epistemicUncertainty"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["criticalPillar"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                                d["maxCardinality"]: Literal(4, datatype=XSD.integer)},
    })
    add_shape(G, "FacetRequirementShape", ETH["FacetRequirement"], {
        ETH["requiresFacet"]: c1, ETH["requirementForCase"]: c1,
        ETH["requirementValue"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
    })
    add_shape(G, "AgencyProfileShape", ETH["AgencyProfile"], {
        ETH["shapeWant"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["shapeCan"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["shapeMust"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["shapeKnow"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["completeness"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["magnitude"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: Literal(4, datatype=XSD.decimal)},
    })
    add_shape(G, "FacetLevelShape", ETH["FacetLevel"], {
        ETH["levelOfFacet"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                             d["maxCardinality"]: Literal(1, datatype=XSD.integer)},
        ETH["observedLevel"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer),
                               d["maxCardinality"]: Literal(1, datatype=XSD.integer),
                               d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["confidence"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
    })
    add_shape(G, "ConfrontationShape", ETH["Confrontation"], {
        ETH["concernsCase"]: c1, ETH["assessedBy"]: c1, ETH["usesCalibration"]: c1,
        ETH["decisionOf"]: dict(c1, **{d["in"]: [DEC[x] for x in
                                                 ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED",
                                                  "ALLOW_WITH_GUARDS", "ALLOW")]}),
        ETH["adequacy"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["adequacyRaw"]: dict(c1, **{d["minInclusive"]: ZERO, d["maxInclusive"]: ONE}),
        ETH["residualRisk"]: {d["minCardinality"]: Literal(1, datatype=XSD.integer), d["minInclusive"]: ZERO},
        ETH["riskFloor"]: {d["minInclusive"]: ZERO},
        ETH["pillarDeficit"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["levelWant"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["levelCan"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["levelMust"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["levelKnow"]: {d["minInclusive"]: ZERO, d["maxInclusive"]: ONE},
        ETH["structuralTermPair"]: {d["minInclusive"]: ZERO},
        ETH["structuralTermTriple"]: {d["minInclusive"]: ZERO},
        ETH["structuralTermInterior"]: {d["minInclusive"]: ZERO},
    })
    return G


MODULES = {
    "01_core.ttl": core,
    "02_facets.ttl": facets,
    "03_domains_context.ttl": domains_and_context,
    "04_pillars_lattice.ttl": pillars_lattice,
    "05_calibration.ttl": calibration,
    "06_decisions.ttl": decisions,
    "shapes/facet_and_context_shapes.ttl": shapes,
}

if __name__ == "__main__":
    total = 0
    for path, fn in MODULES.items():
        G = fn()
        full = os.path.join(OUT, path)
        G.serialize(full, format="turtle")
        total += len(G)
        print(f"{path}: {len(G)} triples")
    print("total triples:", total)
