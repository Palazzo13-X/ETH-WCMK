"""ETH-WCMK v11 canonical facet registry.

Changes vs v10 (decisions D3.3 / D3.9 in CHANGELOG_DECISIONS.md):
  * 28 facets (26 + M7 Proportionality & redress + C7 Containment & reversibility);
  * a facet may now touch up to THREE pillars (v10 allowed at most two), with
    sum(beta) == 1 and every non-zero beta >= 0.15;
  * every facet declares an OBSERVABLE (the proxy that makes the facet measurable)
    and an aggregation POLICY that is actually implemented in core.project().

Registry integrity rules (checked by validate_registry()):
  R1  sum(beta) == 1 exactly;
  R2  1 <= number of non-zero beta <= 3;
  R3  each non-zero beta >= 0.15;
  R4  a declared guard implies guard_min > 0;
  R5  every pillar is touched by at least one facet;
  R6  every facet has an observable and a criticality value for all 13 domains.

Criticality rule (documented, reproducible):
  4  -> domain listed in the catalogue's "critical domains" column for that facet,
        or in the transfer table DOMAIN_ADDITIONS (documented limitation: no expert
        panel was used for those cells; they are derived from the nearest analogue).
  3  -> domain belongs to the primary pillar's structural-salience set.
  2  -> otherwise.
"""
from dataclasses import dataclass, field

PILLARS = ("W", "C", "M", "K")

DOMAINS = (
    "SA", "JS", "IC", "FI", "PD", "GP", "IM", "ED", "TB", "MA",          # catalogue's 10 reference domains
    "TS", "RS", "DS",                                                    # extended: transport, research, digital security
)

DOMAIN_LABELS = {
    "SA": "Health", "JS": "Justice and security", "IC": "Critical infrastructure",
    "FI": "Finance", "PD": "Privacy and data", "GP": "Public governance",
    "IM": "Information and media", "ED": "Education", "TB": "Labour",
    "MA": "Environment and energy", "TS": "Transport and mobility",
    "RS": "Research and science", "DS": "Digital security",
}

PILLAR_DEFAULT = {                      # domains where the pillar is structurally salient
    "W": {"SA", "JS", "IC", "FI", "GP", "ED"},
    "C": {"SA", "JS", "IC", "FI", "DS", "TS"},
    "M": {"SA", "JS", "PD", "GP", "FI", "RS"},
    "K": {"SA", "JS", "IC", "PD", "MA", "RS"},
}

# Domains declared critical for the facet in the facet catalogue (verbatim source).
CATALOG_CRITICAL = {
    "W1": {"SA", "JS", "IC", "FI", "GP"},
    "W2": {"SA", "JS", "IC", "PD", "GP"},
    "W3": {"SA", "JS", "PD", "GP", "IM"},
    "W4": {"SA", "JS", "IC", "PD", "FI"},
    "W5": {"SA", "JS", "IC", "FI", "PD"},
    "C1": {"SA", "JS", "IC", "FI"},
    "C2": {"SA", "JS", "IC", "FI", "IM"},
    "C3": {"SA", "JS", "IC", "FI", "PD", "GP"},
    "C4": {"SA", "JS", "IC", "FI", "PD"},
    "C5": {"IC", "SA", "FI", "GP"},
    "C6": {"SA", "JS", "IC", "FI", "PD"},
    "M1": {"SA", "JS", "IC", "FI", "PD", "GP"},
    "M2": {"FI", "PD", "GP", "IC", "SA"},
    "M3": {"SA", "JS", "PD", "GP", "IM"},
    "M4": {"SA", "JS", "IC", "FI", "PD"},
    "M5": {"GP", "JS", "SA", "FI", "IC"},
    "M6": {"FI", "PD", "GP", "SA", "JS"},
    "K1": {"SA", "FI", "JS", "PD", "GP"},
    "K2": {"SA", "JS", "PD", "GP", "IC"},
    "K3": {"SA", "JS", "FI", "PD", "GP"},
    "K4": {"SA", "JS", "FI", "GP", "IC"},
    "K5": {"IC", "GP", "JS", "SA", "MA"},
    "K6": {"SA", "JS", "IC", "FI", "PD"},
    "K7": {"PD", "FI", "GP", "SA", "JS"},
}

# Transfer assignments for facets/domains the catalogue leaves silent.
# FACET_ADDITIONS: new facets, assigned by analogy with their nearest catalogued twin.
FACET_ADDITIONS = {
    "W6": {"SA": 4, "GP": 4, "ED": 4, "JS": 3, "FI": 3, "RS": 3},
    "C7": {"IC": 4, "DS": 4, "TS": 4, "SA": 4, "MA": 3, "JS": 3, "FI": 3},
    "M7": {"SA": 4, "JS": 4, "GP": 4, "PD": 4, "TB": 3, "FI": 3, "ED": 3},
    "K8": {"RS": 4, "ED": 4, "SA": 3, "IC": 3, "DS": 3, "GP": 3},
    "M8": {"SA": 4, "GP": 4, "IM": 4, "PD": 4, "FI": 4, "ED": 4, "TB": 4, "TS": 4, "JS": 3},
    "M9": {"SA": 4, "JS": 4, "GP": 4, "FI": 4, "TB": 4, "PD": 4, "TS": 4, "IC": 4},
    "M10": {"SA": 4, "RS": 4, "ED": 4, "PD": 4, "GP": 4, "TB": 4, "JS": 4},
    "C8": {"PD": 4, "FI": 4, "SA": 4, "GP": 4, "DS": 4, "RS": 4, "IM": 4, "TB": 4},
    "K9": {"GP": 4, "IC": 4, "TS": 4, "MA": 4, "FI": 4, "SA": 4, "DS": 4, "TB": 4},
}
# DOMAIN_ADDITIONS: domains absent from the v1 catalogue (TS, RS, DS) or left blank (TB, MA, ED, IM).
DOMAIN_ADDITIONS = {
    "TB": {"W2": 4, "M1": 4, "M3": 4, "C3": 4, "K2": 4, "M5": 3, "W3": 3},
    "TS": {"C1": 4, "C3": 4, "M1": 4, "K1": 4, "K4": 3, "C4": 3},
    "DS": {"C1": 4, "C3": 4, "M1": 4, "K2": 4, "K7": 4, "C5": 3},
    "MA": {"C1": 4, "C3": 4, "M4": 4, "K1": 3},
    "RS": {"K1": 4, "K2": 4, "K3": 4, "K7": 4, "M3": 4, "W1": 3},
    "ED": {"W1": 4, "W4": 4, "M3": 4, "K3": 4},
    "IM": {"W2": 4, "W3": 4, "K7": 4, "M3": 4},
}

POLICIES = ("weighted_mean", "guarded_weighted_mean", "threshold_override", "uncertainty_penalized_mean")


@dataclass(frozen=True)
class FacetDef:
    code: str
    label: str
    beta: tuple                      # normalized, sums to 1, at most 3 non-zero entries
    policy: str
    guard: bool = False
    guard_min: float = 0.0
    source: str = "catalog"          # catalog | new
    observable: str = ""             # proxy that makes the facet measurable
    criticality: dict = field(default_factory=dict)

    def primary_pillar(self) -> str:
        return PILLARS[max(range(4), key=lambda i: self.beta[i])]

    def n_pillars(self) -> int:
        return sum(1 for b in self.beta if b > 0)

    def pillar_weights(self) -> dict:
        return {p: b for p, b in zip(PILLARS, self.beta) if b > 0}


_REGISTRY = [
    # ---- Want -------------------------------------------------------------
    FacetDef("W1", "Goal orientation", (0.8, 0.2, 0.0, 0.0), "weighted_mean",
             observable="divergence between stated objective and deployed objective"),
    FacetDef("W2", "Value alignment", (0.7, 0.0, 0.3, 0.0), "guarded_weighted_mean", guard=True, guard_min=0.55,
             observable="declared values vs. observed outcome distribution (fairness metrics)"),
    FacetDef("W3", "Stakeholder regard", (0.6, 0.0, 0.4, 0.0), "guarded_weighted_mean",
             observable="stakeholder map coverage and complaint channels"),
    FacetDef("W4", "Priority discipline", (0.7, 0.3, 0.0, 0.0), "guarded_weighted_mean",
             observable="ranked objective hierarchy and trade-off logs"),
    FacetDef("W5", "Intentional stability", (0.6, 0.2, 0.2, 0.0), "weighted_mean",
             observable="objective drift across runs and time windows"),
    FacetDef("W6", "Want legitimacy", (0.45, 0.00, 0.55, 0.00), "guarded_weighted_mean", guard=True, guard_min=0.50,
             source="new",
             observable="mandate provenance: who authorised the goal and with what scope"),
    # ---- Can --------------------------------------------------------------
    FacetDef("C1", "Functional capability", (0.0, 1.0, 0.0, 0.0), "weighted_mean",
             observable="task success rate against benchmark"),
    FacetDef("C2", "Robustness", (0.00, 0.70, 0.15, 0.15), "guarded_weighted_mean",
             observable="performance degradation under distribution shift or adversarial input"),
    FacetDef("C3", "Controllability", (0.0, 0.6, 0.2, 0.2), "threshold_override", guard=True, guard_min=0.55,
             observable="existence and latency of stop / hand-off mechanisms"),
    FacetDef("C4", "Scope adequacy", (0.0, 0.7, 0.3, 0.0), "guarded_weighted_mean",
             observable="fit between declared scope and observed use"),
    FacetDef("C5", "Resource sufficiency", (0.00, 0.60, 0.15, 0.25), "weighted_mean",
             observable="compute / data / staffing budget vs. task demand"),
    FacetDef("C6", "Safe executability", (0.0, 0.5, 0.3, 0.2), "threshold_override", guard=True, guard_min=0.60,
             observable="incident rate under production conditions"),
    FacetDef("C7", "Containment and reversibility capacity", (0.0, 0.6, 0.2, 0.2), "threshold_override",
             guard=True, guard_min=0.45, source="new",
             observable="rollback, quarantine and mitigation procedures actually exercised"),
    # ---- Must -------------------------------------------------------------
    FacetDef("M1", "Legal obligation", (0.0, 0.0, 0.8, 0.2), "threshold_override", guard=True, guard_min=0.60,
             observable="mapped applicable statutes and compliance evidence"),
    FacetDef("M2", "Institutional policy obligation", (0.00, 0.15, 0.70, 0.15), "guarded_weighted_mean",
             observable="policy coverage of the deployment context"),
    FacetDef("M3", "Ethical principle obligation", (0.2, 0.0, 0.6, 0.2), "guarded_weighted_mean",
             observable="principles enumerated and mapped to design decisions"),
    FacetDef("M4", "Prudential obligation", (0.00, 0.25, 0.55, 0.20), "threshold_override", guard=True, guard_min=0.55,
             observable="precaution measures proportionate to irreversibility"),
    FacetDef("M5", "Role obligation", (0.2, 0.2, 0.6, 0.0), "guarded_weighted_mean",
             observable="role/duty specification of the acting agent"),
    FacetDef("M6", "Accountability obligation", (0.3, 0.0, 0.5, 0.2), "guarded_weighted_mean",
             observable="traceability, audit trail and responsible-party assignment"),
    FacetDef("M7", "Proportionality and redress", (0.0, 0.2, 0.6, 0.2), "guarded_weighted_mean", guard=True,
             guard_min=0.50, source="new",
             observable="benefit/harm proportionality assessment and remedy availability"),
    # ---- Know -------------------------------------------------------------
    FacetDef("K1", "Evidential knowledge", (0.00, 0.15, 0.15, 0.70), "weighted_mean",
             observable="quality, freshness and representativeness of the evidence base"),
    FacetDef("K2", "Contextual knowledge", (0.00, 0.30, 0.20, 0.50), "guarded_weighted_mean",
             observable="local and domain factors captured in the model of the situation"),
    FacetDef("K3", "Normative knowledge", (0.0, 0.2, 0.4, 0.4), "guarded_weighted_mean",
             observable="norms correctly retrieved and correctly applied"),
    FacetDef("K4", "Procedural knowledge", (0.0, 0.4, 0.2, 0.4), "weighted_mean",
             observable="documented procedures followed in operation"),
    FacetDef("K5", "Causal knowledge", (0.35, 0.15, 0.00, 0.50), "weighted_mean",
             observable="validated causal/counterfactual understanding of outcomes"),
    FacetDef("K6", "Uncertainty awareness", (0.0, 0.2, 0.3, 0.5), "uncertainty_penalized_mean", guard=True,
             guard_min=0.50,
             observable="calibration of reported confidence against realized error"),
    FacetDef("K7", "Provenance awareness", (0.00, 0.15, 0.25, 0.60), "guarded_weighted_mean",
             observable="source lineage of data, claims and decisions"),
    FacetDef("K8", "Learnability", (0.15, 0.35, 0.0, 0.5), "uncertainty_penalized_mean", source="new",
             observable="feedback loop that measurably improves performance or safety"),
    # ---- v12 additions (D4.20): procedural duties the normative panel applies but the
    # model could not observe. Evidence: Evaluacoes/r4/corpus_v5_confusion_analysis.json
    # - the rules that fire on these facts (B5 sunset 21,096; C10 notice 15,864;
    # A5/C2 human review 16,732/12,518; C1 minimisation 14,526; C5 consent 7,282) are the
    # main source of model-panel divergence and no facet anchored them.
    FacetDef("M8", "Transparency and notice", (0.0, 0.2, 0.5, 0.3), "guarded_weighted_mean",
             guard=True, guard_min=0.50, source="new",
             observable="affected parties are informed that a decision was made about them and can see its logic"),
    FacetDef("M9", "Human review channel", (0.0, 0.3, 0.7, 0.0), "guarded_weighted_mean",
             guard=True, guard_min=0.50, source="new",
             observable="an accessible, exercised human review or appeal route exists before harm crystallises"),
    FacetDef("M10", "Consent and participation", (0.25, 0.00, 0.60, 0.15), "guarded_weighted_mean",
             guard=True, guard_min=0.50, source="new",
             observable="informed consent or documented participation of the affected parties"),
    FacetDef("C8", "Data minimisation and purpose limitation", (0.0, 0.5, 0.5, 0.0), "guarded_weighted_mean",
             source="new",
             observable="fields collected are limited to those necessary for the declared purpose"),
    FacetDef("K9", "Periodic review and sunset", (0.0, 0.0, 0.4, 0.6), "weighted_mean",
             source="new",
             observable="a scheduled review, expiry or sunset clause in the deployment contract"),
]

FACETS = list(_REGISTRY)
BY_CODE = {f.code: f for f in FACETS}
CODES = tuple(f.code for f in FACETS)


def _complete_criticality(f: FacetDef) -> dict:
    crit = dict(f.criticality)
    add_facet = FACET_ADDITIONS.get(f.code, {})
    for d in DOMAINS:
        if d in crit:
            continue
        if d in CATALOG_CRITICAL.get(f.code, ()) or d in add_facet:
            crit[d] = 4 if (d in CATALOG_CRITICAL.get(f.code, ())) else add_facet[d]
        elif d in DOMAIN_ADDITIONS and f.code in DOMAIN_ADDITIONS[d]:
            crit[d] = DOMAIN_ADDITIONS[d][f.code]
        elif d in PILLAR_DEFAULT[f.primary_pillar()]:
            crit[d] = 3
        else:
            crit[d] = 2
    return crit


for _f in FACETS:
    _f.criticality.update(_complete_criticality(_f))


def validate_registry():
    """Return integrity failures (empty list means the registry is coherent)."""
    errs = []
    for f in FACETS:
        if abs(sum(f.beta) - 1.0) > 1e-9:
            errs.append(f"{f.code}: beta does not sum to 1 ({sum(f.beta)})")
        if any(b < 0 for b in f.beta):
            errs.append(f"{f.code}: negative beta")
        nz = f.n_pillars()
        if nz < 1 or nz > 3:
            errs.append(f"{f.code}: touches {nz} pillars (must be 1..3)")
        if any(0 < b < 0.15 for b in f.beta):
            errs.append(f"{f.code}: beta entry below 0.15 -> token sharing, not real sharing")
        if f.guard and f.guard_min <= 0:
            errs.append(f"{f.code}: guard declared without threshold")
        if f.policy not in POLICIES:
            errs.append(f"{f.code}: unknown aggregation policy {f.policy}")
        if not f.observable:
            errs.append(f"{f.code}: no observable declared")
        if len(f.criticality) != len(DOMAINS):
            errs.append(f"{f.code}: criticality matrix incomplete ({len(f.criticality)}/{len(DOMAINS)})")
    for i, p in enumerate(PILLARS):
        if not any(f.beta[i] > 0 for f in FACETS):
            errs.append(f"pillar {p} has no contributing facet")
    codes = {f.code for f in FACETS}
    if len(codes) != len(FACETS):
        errs.append("duplicate facet codes")
    return errs


def coverage_report():
    crit_counts = {f.code: sum(1 for v in f.criticality.values() if v == 4) for f in FACETS}
    return {"facets": len(FACETS), "domains": len(DOMAINS), "cells": len(FACETS) * len(DOMAINS),
            "critical_cells": sum(crit_counts.values()),
            "facets_with_ge_3_critical_domains": sum(1 for v in crit_counts.values() if v >= 3),
            "pillars_per_facet": {f.code: f.n_pillars() for f in FACETS}}


def to_csv(path):
    import csv
    with open(path, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["code", "label", "betaW", "betaC", "betaM", "betaK", "pillars", "policy",
                     "guard", "guard_min", "source", "observable", "criticality"] + list(DOMAINS))
        for f in FACETS:
            wr.writerow([f.code, f.label] + list(f.beta) + [f.n_pillars(), f.policy, f.guard, f.guard_min,
                            f.source, f.observable,
                            "|".join(str(f.criticality[d]) for d in DOMAINS)] + [f.criticality[d] for d in DOMAINS])


if __name__ == "__main__":
    print("facets:", len(FACETS), "| problems:", validate_registry() or "none")
    print(coverage_report())
    for f in FACETS:
        print(f"{f.code} {f.label:<44} beta={f.beta} pillars={f.n_pillars()} policy={f.policy:<26} "
              f"guard={f.guard}:{f.guard_min}")
