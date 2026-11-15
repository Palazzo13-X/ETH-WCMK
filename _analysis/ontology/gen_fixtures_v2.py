"""Generate the ontology v2 instance fixtures, computed by the formal core.

Every numeric value in the "valid" fixture is produced by core.confront(), so the
ontology instances and the executable model cannot drift apart.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "formal_core")))
from facet_registry import FACETS
from core import CaseSpec, Profile, Calibration, confront, prudential_floor, structural_terms

from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD

BASE = "https://ethwcmk.org/ontology/"
ETH = Namespace(BASE + "eth/"); FAC = Namespace(BASE + "facet/"); DOM = Namespace(BASE + "domain/")
PIL = Namespace(BASE + "pillar/"); CAL = Namespace(BASE + "calibration/"); DEC = Namespace(BASE + "decision/")
POL = Namespace(BASE + "policy/")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Ontologias", "ontology_v2", "fixtures"))

CALIB = Calibration(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1/6,)*6, beta_face=(1/4,)*4,
                    gamma=0.12, eta=0.05, omega=0.03, rho=0.15)

REQ = {  # rule-based requirement template for an IC (critical infrastructure) case, severity high
    "W1": 0.80, "W2": 0.85, "W3": 0.70, "W4": 0.75, "W5": 0.65, "W6": 0.80,
    "C1": 0.85, "C2": 0.80, "C3": 0.80, "C4": 0.70, "C5": 0.60, "C6": 0.75,
    "M1": 0.90, "M2": 0.80, "M3": 0.85, "M4": 0.85, "M5": 0.75, "M6": 0.80,
    "K1": 0.85, "K2": 0.80, "K3": 0.75, "K4": 0.75, "K5": 0.70, "K6": 0.80, "K7": 0.70, "K8": 0.65,
}
LEVEL = {
    "W1": 0.75, "W2": 0.60, "W3": 0.70, "W4": 0.65, "W5": 0.55, "W6": 0.40,
    "C1": 0.80, "C2": 0.72, "C3": 0.55, "C4": 0.68, "C5": 0.60, "C6": 0.70,
    "M1": 0.50, "M2": 0.75, "M3": 0.70, "M4": 0.60, "M5": 0.65, "M6": 0.70,
    "K1": 0.80, "K2": 0.70, "K3": 0.65, "K4": 0.60, "K5": 0.55, "K6": 0.55, "K7": 0.60, "K8": 0.35,
}

def graph():
    G = Graph()
    for k, v in (("eth", ETH), ("facet", FAC), ("domain", DOM), ("pillar", PIL),
                 ("cal", CAL), ("decision", DEC), ("policy", POL), ("owl", OWL),
                 ("rdf", RDF), ("rdfs", RDFS), ("xsd", XSD)):
        G.bind(k, v)
    return G

def valid_fixture():
    G = graph()
    case = URIRef(BASE + "case/IC-0001")
    G.add((case, RDF.type, ETH["EthicalCase"]))
    G.add((case, RDFS.label, Literal("Grid-load balancing agent operating under market pressure")))
    G.add((case, ETH["hasDomain"], DOM["IC"]))
    G.add((case, ETH["hasSeverity"], URIRef(BASE + "severity/high")))
    G.add((case, ETH["hasPrudentialMode"], URIRef(BASE + "prudential/elevated")))
    G.add((case, ETH["hasReversibility"], URIRef(BASE + "reversibility/partially_irreversible")))
    G.add((case, ETH["contextualRisk"], Literal(0.82, datatype=XSD.decimal)))
    G.add((case, ETH["epistemicUncertainty"], Literal(0.30, datatype=XSD.decimal)))
    for p in ("Must", "Know"):
        G.add((case, ETH["criticalPillar"], PIL[p]))
    for code, val in REQ.items():
        rn = BNode()
        G.add((rn, RDF.type, ETH["FacetRequirement"]))
        G.add((rn, ETH["requirementForCase"], case))
        G.add((rn, ETH["requiresFacet"], FAC[code]))
        G.add((rn, ETH["requirementValue"], Literal(val, datatype=XSD.decimal)))

    prof = URIRef(BASE + "profile/agent-114")
    cfr = URIRef(BASE + "confrontation/IC-0001-agent-114")
    G.add((prof, RDF.type, ETH["AgencyProfile"]))
    G.add((prof, RDFS.label, Literal("Delegated grid-balancing agent (LLM-mediated)")))
    res = confront(CaseSpec("IC-0001", "IC", "high", "elevated", "partially_irreversible",
                            REQ, 0.30, 0.82, ("M", "K")), Profile("agent-114", LEVEL), CALIB)
    for code, val in LEVEL.items():
        ln = BNode()
        G.add((ln, RDF.type, ETH["FacetLevel"]))
        G.add((ln, ETH["levelOfFacet"], FAC[code]))
        G.add((ln, ETH["observedLevel"], Literal(val, datatype=XSD.decimal)))
        G.add((ln, ETH["confidence"], Literal(0.85, datatype=XSD.decimal)))
        G.add((prof, ETH["hasFacetLevel"], ln))
    for i, ell in enumerate(res["levels"]):
        G.add((cfr, ETH[f"level{('Want','Can','Must','Know')[i]}"], Literal(ell, datatype=XSD.decimal)))
        share = ell / sum(res["levels"])
        G.add((prof, ETH[f"shape{('Want','Can','Must','Know')[i]}"], Literal(round(share, 4), datatype=XSD.decimal)))
    G.add((prof, ETH["magnitude"], Literal(res["magnitude"], datatype=XSD.decimal)))
    G.add((prof, ETH["completeness"], Literal(res["completeness"], datatype=XSD.decimal)))

    G.add((cfr, RDF.type, ETH["Confrontation"]))
    G.add((cfr, ETH["concernsCase"], case))
    G.add((cfr, ETH["assessedBy"], prof))
    G.add((cfr, ETH["usesCalibration"], CAL["v10"]))
    for i, d in enumerate(res["deficits"]):
        G.add((cfr, ETH["pillarDeficit"], Literal(d, datatype=XSD.decimal)))
    for code, d in res["top_facet_deficits"]:
        G.add((cfr, ETH["facetDeficit"], Literal(d, datatype=XSD.decimal)))
    G.add((cfr, ETH["structuralTermPair"], Literal(res["S2"], datatype=XSD.decimal)))
    G.add((cfr, ETH["structuralTermTriple"], Literal(res["S3"], datatype=XSD.decimal)))
    G.add((cfr, ETH["structuralTermInterior"], Literal(res["S4"], datatype=XSD.decimal)))
    G.add((cfr, ETH["adequacyRaw"], Literal(res["adequacy_raw"], datatype=XSD.decimal)))
    G.add((cfr, ETH["adequacy"], Literal(res["adequacy"], datatype=XSD.decimal)))
    G.add((cfr, ETH["riskFloor"], Literal(round(res["sigma"] * res["R_c"], 4), datatype=XSD.decimal)))
    G.add((cfr, ETH["residualRisk"], Literal(res["R_r"], datatype=XSD.decimal)))
    for p in res["veto"]:
        G.add((cfr, ETH["vetoPillar"], PIL[p]))
    G.add((cfr, ETH["decisionOf"], DEC[res["decision"]]))
    return G, res

def invalid_fixture():
    """Reproduces the v1 bridge example's broken values: facets as classes, sums > 1,
    residual risk above contextual risk, decision outside the vocabulary, arity 5."""
    G = graph()
    case = URIRef(BASE + "case/BROKEN-0001")
    G.add((case, RDF.type, ETH["EthicalCase"]))
    G.add((case, ETH["hasDomain"], DOM["IC"]))
    G.add((case, ETH["hasSeverity"], URIRef(BASE + "severity/very_high")))      # undefined band
    G.add((case, ETH["contextualRisk"], Literal(1.20, datatype=XSD.decimal)))   # out of range
    G.add((case, ETH["epistemicUncertainty"], Literal(-0.1, datatype=XSD.decimal)))

    # legacy mistake 1: a facet declared as a class instead of an individual
    bad_facet = URIRef(BASE + "facet/W9")
    G.add((bad_facet, RDF.type, OWL.Class))
    G.add((bad_facet, ETH["facetCode"], Literal("W11")))

    # legacy mistake 2: betas that do not normalise and an impossible guard threshold
    bad_facet2 = URIRef(BASE + "facet/M7")
    G.add((bad_facet2, RDF.type, ETH["Facet"]))
    G.add((bad_facet2, RDF.type, OWL.NamedIndividual))
    G.add((bad_facet2, ETH["facetCode"], Literal("M7"))
    )
    G.add((bad_facet2, ETH["betaWant"], Literal(0.9, datatype=XSD.decimal)))
    G.add((bad_facet2, ETH["betaCan"], Literal(0.4, datatype=XSD.decimal)))       # sum = 1.3
    G.add((bad_facet2, ETH["betaMust"], Literal(0.0, datatype=XSD.decimal)))
    G.add((bad_facet2, ETH["betaKnow"], Literal(0.0, datatype=XSD.decimal)))
    G.add((bad_facet2, ETH["hasGuard"], Literal(True, datatype=XSD.boolean)))
    G.add((bad_facet2, ETH["guardMin"], Literal(1.20, datatype=XSD.decimal)))      # impossible guard
    G.add((bad_facet2, ETH["facetWeight"], Literal(1.2, datatype=XSD.decimal)))
    G.add((bad_facet2, ETH["aggregationPolicy"], POL["weighted_mean"]))
    G.add((bad_facet2, ETH["source"], Literal("legacy_import")))

    # legacy mistake 3: a decision outside the closed vocabulary
    G.add((URIRef(BASE + "decision/OPEN"), RDF.type, ETH["Decision"]))
    G.add((URIRef(BASE + "decision/OPEN"), ETH["permissivenessRank"], Literal(9, datatype=XSD.integer)))

    cfr = URIRef(BASE + "confrontation/BROKEN-0001")
    G.add((cfr, RDF.type, ETH["Confrontation"]))
    G.add((cfr, ETH["concernsCase"], case))
    G.add((cfr, ETH["adequacy"], Literal(1.30, datatype=XSD.decimal)))
    G.add((cfr, ETH["residualRisk"], Literal(1.20, datatype=XSD.decimal)))
    G.add((cfr, ETH["riskFloor"], Literal(0.0, datatype=XSD.decimal)))
    G.add((cfr, ETH["structuralTermPair"], Literal(-0.2, datatype=XSD.decimal)))
    G.add((cfr, ETH["decisionOf"], URIRef(BASE + "decision/OPEN")))             # undefined decision
    G.add((cfr, ETH["pillarDeficit"], Literal(1.000, datatype=XSD.decimal)))
    bad_slot = URIRef(BASE + "slot/BAD_ARITY")
    G.add((bad_slot, RDF.type, ETH["RelationalSlot"]))
    G.add((bad_slot, ETH["slotArity"], Literal(5, datatype=XSD.integer)))
    return G

if __name__ == "__main__":
    G, res = valid_fixture()
    G.serialize(os.path.join(OUT, "instance_valid.ttl"), format="turtle")
    print("instance_valid.ttl:", len(G), "triples")
    print("computed:", {k: res[k] for k in ("levels", "deficits", "S2", "S3", "S4",
                                            "adequacy_raw", "adequacy", "sigma", "R_r", "decision", "veto")})
    H = invalid_fixture()
    H.serialize(os.path.join(OUT, "instance_invalid.ttl"), format="turtle")
    print("instance_invalid.ttl:", len(H), "triples")
