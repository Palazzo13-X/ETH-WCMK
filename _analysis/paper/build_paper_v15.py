"""Build PAPER_v15.docx — English manuscript, revised style.

Changes with respect to v14:
  * prose tightened: repeated constructions removed, project-internal decision
    tags (D5.x, D4.x) dropped from the running text, interpretation merged into
    the flow of each section instead of a labelled paragraph;
  * "Notation and terminology" moved to the end of the document, after the
    references; table numbering follows the new order;
  * references rendered as hanging-indent entries, no bullets;
  * availability statement points to the GitHub repository and to the arXiv
    deposit; the venue is left open.

Every number quoted still comes from an artefact in Evaluacoes/r5/ (and r4 for
the historical batteries); Appendix A maps each figure to its artefact.
"""
import re
import sys

sys.path.insert(0, "/home/luiz/Documentos/Strata/Shared/_analysis/paper")
from docx.shared import Cm
from docx_build_v14 import (new_document, title_block, para, bullets, caption,
                            equation, table, figure, set_document_properties,
                            add_running_footer)
from build_paper_v14 import (EQS, FACETS, CALIB, MECHANISMS, ABLATION, SOBOL,
                            RUBRIC, BASELINES, REFS, NOTATION, LIMITS)

FIG = "/home/luiz/Documentos/Strata/Shared/paper/figures_v14"
OUT = "/home/luiz/Documentos/Strata/Shared/_analysis/PAPER_v15.docx"

REPO = "github.com/ETH-WCMK/ETH-WCMK"          # to be confirmed by the authors
INTERNAL_TAG = re.compile(r"\s*\((?:D\d+\.\d+|I\d+|D\d+)\)")


def note(text):
    """Equation captions without the project's internal decision tags."""
    return INTERNAL_TAG.sub("", text).strip()


POLISH = [
    # repeated constructions
    ("The ceiling, therefore, belongs to the normative instrument rather than to the model.",
     "The ceiling is therefore set by the normative instrument, not by the model."),
    ("is a theorem rather than a parameter assumption", "is a theorem, not a parameter assumption"),
    ("a limitation that is quantified rather than concealed", "a limitation that is quantified, not concealed"),
    ("The representation is conceptual rather than lexical", "The representation is conceptual, not lexical"),
    ("Its parameters are explicit rather than implicit:", "Its parameters are explicit:"),
    ("produces review rather than prohibition", "produces review instead of prohibition"),
    ("recomputed integrally in the pessimistic and optimistic modes rather than derived from the "
     "central value by adding a constant", "recomputed integrally in the pessimistic and optimistic "
     "modes, not from the central value plus a constant"),
    ("is a parameter rather than a hidden constant", "is a declared parameter, not a hidden constant"),
    ("The ontology is generated from the code rather than written by hand",
     "The ontology is generated from the code, not written by hand"),
    ("the invalid fixtures are part of the test rather than an afterthought",
     "the invalid fixtures belong to the test itself"),
    ("so a reviewer can re-derive the geometry rather than take it from the paper",
     "so a reviewer can re-derive the geometry instead of trusting the paper"),
    ("both belong in the audit record rather than in a code default",
     "both belong in the audit record, not in a code default"),
    ("this is a governance finding rather than a numerical detail",
     "this is a governance finding, not a numerical detail"),
    ("noise pushes the verdict toward caution rather than permission",
     "noise pushes the verdict toward caution, not permission"),
    ("Transfer is measured rather than assumed", "Transfer is measured, not assumed"),
    ("which is why the instrument rather than the domain is the dominant source of disagreement",
     "so the instrument, not the domain, is the dominant source of disagreement"),
    ("the disagreement is documented rather than resolved", "the disagreement is documented, not resolved"),
    ("Pluralism is measured rather than declared", "Pluralism is measured, not declared"),
    ("the divergence belongs to the lenses rather than to the arithmetic",
     "the divergence belongs to the lenses, not to the arithmetic"),
    ("the numbers remain re-derivable rather than merely reported",
     "the numbers can be re-derived instead of merely reported"),
    ("pairs, which is why the count of strictly near-identical pairs rose",
     "pairs, so the count of strictly near-identical pairs rose"),
    ("alone, which is why delegation has consequences", "alone; delegation therefore has consequences"),
    ("which is why the mechanism is mandatory and why its strength s is declared",
     "the mechanism is therefore mandatory, and its strength s is explicit"),
    ("which is why it moved from an implicit constant to a declared parameter",
     "so it moved from an implicit constant to a declared parameter"),

    # long sentences split
    ("Proposition 1. If the weight of every edge is one third of the sum of the weights of the faces "
     "that contain it, and the four face weights sum to one, then S₂ ≥ S₃ ≥ S₄ for every deficit vector "
     "d ≥ 0. Each edge of the tetrahedron lies in exactly two faces, so the derived edge weights sum to "
     "one; the three edges of a face sum to a quantity proportional to the weight of that face; and the "
     "minimum over an edge is never smaller than the minimum over the face containing it, because the "
     "Gödel t-norm is monotone.",
     "Proposition 1. Suppose the weight of every edge equals one third of the sum of the weights of the "
     "faces containing it, and the four face weights sum to one. Then S₂ ≥ S₃ ≥ S₄ for every deficit "
     "vector d ≥ 0. Each edge of the tetrahedron lies in exactly two faces, so the derived edge weights "
     "sum to one. The three edges of a face add up to a quantity proportional to the weight of that face, "
     "and the minimum over an edge is never smaller than the minimum over the face containing it, because "
     "the Gödel t-norm is monotone."),
    ("The requirement a duty imposes in a case is its criticality base — 0.55, 0.70 or 0.85 for criticality "
     "2, 3 or 4 — plus terms for severity, irreversibility, prudential mode and horizon, an uncertainty term "
     "for duties whose primary pillar is K, and 0.08 on the human-review duty M9 when the case reports no "
     "oversight regime: what the institution does not provide, the agent has to supply.",
     "The requirement a duty imposes in a case is its criticality base, 0.55, 0.70 or 0.85 for criticality "
     "2, 3 or 4, plus terms for severity, irreversibility, prudential mode and horizon. Duties whose "
     "primary pillar is K carry an uncertainty term. When the case reports no oversight regime, the "
     "human-review duty M9 carries an extra 0.08: what the institution does not provide, the agent has to "
     "supply."),
    ("The shapes constrain the graph with the same rules the code implements: β must sum to exactly 1 with "
     "at most three non-zero components, each at least 0.15; severity, reversibility, prudential mode and "
     "horizon must be among the declared individuals; a lattice slot must be a vertex, edge, face or cell "
     "and satisfy the incidence rules; a prohibition must declare the obligation it bars; a conflict must "
     "declare its resolution strategy and outcome, consistently with whether it was resolved; every level, "
     "risk and adequacy field is bounded to [0, 1]; and the v6 shapes add the bounds for review need, "
     "salience and the oversight enumeration.",
     "The shapes constrain the graph with the rules the code implements. β must sum to exactly 1, with at "
     "most three non-zero components, each at least 0.15. Severity, reversibility, prudential mode and "
     "horizon must be among the individuals declared in the graph. A lattice slot must be a vertex, edge, "
     "face or cell and satisfy the incidence rules. A prohibition must state the obligation it bars, and a "
     "conflict must state its resolution strategy and outcome consistently with whether it was resolved. "
     "Every level, risk and adequacy field lies in [0, 1]. The v6 shapes add the bounds for review need, "
     "salience and the oversight enumeration."),
    ("Three defects appeared during validation and were corrected. A SPARQL check of the β sum used the "
     "facet's own literal, which SHACL already enforces, so the check was tautological; two checks used "
     "nested sub-selects and predicate expressions inside BIND, which are not valid SPARQL and were "
     "rejected by the engine; and a check that read coverage from the Profile, where it is not asserted, "
     "was rewritten to read it from the Confrontation.",
     "Three defects appeared during validation and were corrected. One SPARQL check of the β sum used the "
     "facet's own literal, which SHACL already enforces, so the check proved nothing. Two checks used "
     "nested sub-selects and predicate expressions inside BIND, which are not valid SPARQL and were "
     "rejected by the engine. A third read coverage from the Profile, where it is not asserted, and was "
     "rewritten to read it from the Confrontation."),
    ("Thirty-four rules, each anchored to a named instrument — the Rio Declaration (1992), UDHR Article 10 "
     "(United Nations, 1948), UN CRC Article 12 (United Nations, 1989), GDPR Articles 5, 22 and 25 "
     "(European Union, 2016), the Belmont Report (1978), the Declaration of Helsinki (1964), the ILO "
     "Declaration (International Labour Organization, 1998), ACM/IEEE codes, ISO 26262 (ISO, 2018), IEC "
     "62443, ISO 27001 (ISO/IEC, 2023), the NIST Framework (NIST, 2025) and the OECD Recommendation (OECD, "
     "2024) — fire on the facts and levels reported, and each firing is counted separately from the verdict "
     "it actually changes.",
     "Thirty-four rules are anchored to named instruments: the Rio Declaration (1992), UDHR Article 10 "
     "(United Nations, 1948), UN CRC Article 12 (United Nations, 1989), GDPR Articles 5, 22 and 25 "
     "(European Union, 2016), the Belmont Report (1978), the Declaration of Helsinki (1964), the ILO "
     "Declaration (International Labour Organization, 1998), the ACM and IEEE codes, ISO 26262 (ISO, 2018), "
     "IEC 62443, ISO 27001 (ISO/IEC, 2023), the NIST Framework (NIST, 2025) and the OECD Recommendation "
     "(OECD, 2024). They fire on the facts and levels the case reports, and each firing is counted "
     "separately from the verdict it changes."),
    ("Morris elementary effects, a first-order screening that varies one parameter at a time and records the "
     "resulting change in the output (200 trajectories; Morris, 1991), and a paired Sobol design (Sobol, "
     "2001; Saltelli et al., 2008) with N = 1,024 over the 12-dimensional calibration space were run on a "
     "panel of 12 cases covering the 13 domains and the five verdicts.",
     "Two designs were used. Morris elementary effects vary one parameter at a time and record the change "
     "in the output, with 200 trajectories (Morris, 1991). The paired Sobol design (Sobol, 2001; Saltelli "
     "et al., 2008) used N = 1,024 over the 12-dimensional calibration space. Both ran on a panel of 12 "
     "cases covering the 13 domains and the five verdicts."),
    ("The maximum absolute difference is 0.0 for S₂, S₃, S₄, raw adequacy, the band bounds, the bar, the "
     "stakes, residual risk, the structural terms, the epistemic penalty, the material gap and the veto set; "
     "there are no verdict divergences, and the recomputed distribution is identical to the stored one.",
     "The maximum absolute difference is 0.0 for S₂, S₃, S₄, raw adequacy, the band bounds, the bar, the "
     "stakes, residual risk, the structural terms, the epistemic penalty, the material gap and the veto set. "
     "There are no verdict divergences, and the recomputed distribution is identical to the stored one."),
    ("Injecting noise into the observed levels raises the verdict flip rate from 1.32% at σ = 0.02 to 8.56% "
     "at σ = 0.2, and the shifts are asymmetric: degraded observations make the model more restrictive about "
     "twenty times as often as they make it more permissive (0.0815 against 0.0041 at σ = 0.2).",
     "Injecting noise into the observed levels raises the verdict flip rate from 1.32% at σ = 0.02 to 8.56% "
     "at σ = 0.2. The shifts are asymmetric: a degraded observation makes the model more restrictive about "
     "twenty times as often as it makes it more permissive, 0.0815 against 0.0041 at σ = 0.2."),
    ("Transfer is measured, not assumed. Fitting the ladder on nine domains and testing on the four never "
     "used — transport, research, digital security and labour — plus the 320 narrative cases gives κ of "
     "0.4834 on the holdout against 0.4618 in sample, a gap of −0.0215: the model generalises slightly "
     "better outside the training domains, which indicates that the fit is not memorising domain-specific "
     "patterns. Against simple comparators the model beats a threshold on adequacy without the veto (0.1464), "
     "a majority-class classifier (0.0000) and an uncalibrated ladder (0.2025).",
     "Transfer is measured, not assumed. The ladder was fitted on nine domains and tested on the four never "
     "used: transport, research, digital security and labour, together with the 320 narrative cases. κ "
     "reached 0.4834 on the holdout against 0.4618 in sample, a gap of −0.0215. The model generalises "
     "slightly better outside the training domains, so the fit does not memorise domain-specific patterns. "
     "Against simple comparators it beats a threshold on adequacy without the veto (0.1464), a "
     "majority-class classifier (0.0000) and an uncalibrated ladder (0.2025)."),
    ("New in this round, I34 tests Proposition 1 over the complete grid of deficits; I35 refuses to load an "
     "incoherent calibration; I36 makes the unspecified oversight regime identical to v12 and declares the "
     "weights of ReviewNeed; I37 proves that λ(E) is the identity when s = 0; I38 orders the stakes by "
     "regime; I39 proves that adequacy with ζ = 0 differs from v12 by exactly ζ times Ψ; and I44 validates "
     "the coverage gate as a parameter. The lattice census computed from the code is 15 slots, 108 "
     "incidences and structural weights summing to 1.0000000000, with the derived marginal uniform at 1/6 "
     "for the canonical β.",
     "New in this round: I34 tests Proposition 1 over the complete grid of deficits; I35 refuses to load an "
     "incoherent calibration; I36 makes the unspecified oversight regime identical to v12 and states the "
     "weights of ReviewNeed; I37 proves that λ(E) is the identity when s = 0; I38 orders the stakes by "
     "regime; I39 proves that adequacy with ζ = 0 differs from v12 by exactly ζ times Ψ; I44 validates the "
     "coverage gate as a parameter. The lattice census computed from the code is 15 slots, 108 incidences "
     "and structural weights summing to 1.0000000000, with the derived marginal uniform at 1/6 for the "
     "canonical β."),
    ("The regime is inferred from what the case reports — review plus independent audit gives a regime in "
     "the loop; review or an appeal channel gives one on the loop; nothing reported gives none; nothing "
     "stated at all gives the unspecified case, which reproduces the v12 behaviour exactly.",
     "The regime is inferred from what the case reports. Review plus independent audit places it in the "
     "loop; review or an appeal channel places it on the loop; nothing reported gives none; nothing stated "
     "at all gives the unspecified case, which reproduces the v12 behaviour exactly."),
    ("The mirror recomputes all 220,400 confrontations of corpus v7 from the persona factors, jitter, the "
     "requirements of the case, the subset of duties declared and the observational caps, and compares each "
     "quantity with the value stored in the corpus.",
     "The mirror recomputes all 220,400 confrontations of corpus v7 from the persona factors, the jitter, "
     "the requirements of the case, the duties the profile reports and the observational caps, and compares "
     "each quantity with the value stored in the corpus."),

    # duplication removed: the interpretation no longer restates the numbers
    # paragraphs that restated numbers already given above
    ("Only oversight inferred from facts and the differentiated β improve agreement, and both effects are "
     "significant. Salience and cross-pillar exposure do not: κ falls as they are activated. Both remain "
     "available in the core and inert by default, with the numbers published. In the sensitivity analysis of "
     "Sec. 7.6 they saturate the total-order index because they act through the decision thresholds: they "
     "move outputs without moving agreement.",
     "Only oversight inferred from facts and the differentiated β improve agreement, and both effects are "
     "significant. Salience and cross-pillar exposure do not: κ falls when they are activated, so both "
     "remain in the core, inert by default, with the numbers published."),
    ("Two mechanisms change the verdict for a reason an audit can name and two do not. Oversight inferred "
     "from reported facts raises agreement because a reviewed case is treated differently from an "
     "unreviewed one. Differentiating β raises agreement because duties that were indistinguishable become "
     "distinguishable. Salience and cross-pillar exposure move outputs without moving the judgment, so they "
     "stay as diagnostics: a governance team may inspect them, but the verdict does not depend on them. The "
     "rule this round establishes is that a mechanism is adopted only when its effect is measured, signed "
     "and significant.",
     "The gains have a mechanism an auditor can name. A reviewed case is treated differently from an "
     "unreviewed one, and duties that were indistinguishable become distinguishable. Salience and exposure "
     "move outputs without moving the judgment, so they remain diagnostics: a governance team may inspect "
     "them, but the verdict does not depend on them. A mechanism is adopted here only when its effect is "
     "measured, signed and significant."),
    ("The normative weight of the model sits where the design placed it. Taking the twelve guards away costs "
     "69.8% of the agreement with the panels, so the guard floors are not a stylistic choice but the "
     "mechanism that produces the behaviour the panels reward. The small individual deltas carry the "
     "opposite instruction: no guard can be defended one at a time, so the canon must be defended as a "
     "whole. For an organisation using the model, that means the floors cannot be negotiated duty by duty "
     "without destroying the property for which the model is used.",
     "The normative weight of the model sits where the design placed it. The guard floors are not a "
     "stylistic choice: they produce the behaviour the panels reward. The small individual deltas carry the "
     "opposite instruction. No guard can be defended one at a time, so the canon must be defended as a "
     "whole. For an organisation using the model, the floors cannot be negotiated duty by duty without "
     "destroying the property the model is used for."),
    ("Reporting a level is not the same as delivering it. Nearly every profile states a level that the facts "
     "of the case contradict, and correcting it changes almost half of the verdicts. κ against the panels "
     "rises from 0.2463 without grounding to 0.5526 with it, which is why the mechanism is mandatory and "
     "why its strength s is explicit: at s = 0 the core behaves as v11.",
     "Reporting a level is not the same as delivering it. Nearly every profile states a level that the facts "
     "of the case contradict, and correcting it changes almost half of the verdicts. The difference in κ is "
     "not a tuning effect: it is the difference between judging what an agent claims and judging what an "
     "agent can show. The mechanism is therefore mandatory, and its strength s is explicit: at s = 0 the "
     "core behaves as v11."),
    ("Two parameters govern the model, and both belong in the audit record, not in a code default: the "
     "coverage gate decides when the model is allowed to speak at all, and the structural penalty decides "
     "how much a deficit weighs. Everything else is comparatively flat, including coefficients that earlier "
     "rounds spent effort calibrating. For an organisation deploying the model this is a governance finding, "
     "not a numerical detail: the settings with the largest influence define the reach of the judgment, so "
     "they must be declared, versioned and reviewed.",
     "The reading is a governance one. The coverage gate decides when the model is allowed to speak at all, "
     "and the structural penalty decides how much a deficit weighs; the rest is comparatively flat, "
     "including coefficients earlier rounds spent effort calibrating. Those two settings define the reach of "
     "the judgment, so they belong in the audit record rather than in a code default, and they must be "
     "declared, versioned and reviewed."),
    ("The mirror closes the distance between the paper and the implementation: a reviewer who reads only the "
     "graph reaches the same verdict as the code, quantity by quantity. It also carries a warning that "
     "generalises. Feeding the mirror the stored, rounded levels produced differences of up to 1.7 × 10⁻² "
     "that crossed guard floors; the divergence disappeared only when the mirror rebuilt the unrounded "
     "levels before calling the core. Storage precision is part of verification, not a detail of it.",
     "The mirror closes the distance between the paper and the implementation: a reviewer who reads only the "
     "graph reaches the same verdict as the code, quantity by quantity. It also carries a warning that "
     "generalises. Feeding it the stored, rounded levels produced differences of up to 1.7 × 10⁻² that "
     "crossed guard floors, and the divergence disappeared only when the unrounded levels were rebuilt "
     "before calling the core. Storage precision belongs to verification, not to the detail of the code."),
    ("The asymmetry is the finding. When observations degrade, the model becomes more restrictive far more "
     "often than it becomes more permissive: noise pushes the verdict toward caution, not permission. The "
     "hysteresis blocks 6,382 loosening transitions, so a profile does not oscillate across a decision "
     "boundary. The near-zero effect of the structural terms is a negative result, reported as such: the "
     "tetrahedron organises the record, it does not produce the judgment.",
     "The asymmetry is the finding. Degraded observations push the verdict toward caution, not permission. "
     "Hysteresis stops a profile from oscillating across a decision boundary. The near-zero effect of the "
     "structural terms is a negative result, reported as such: the tetrahedron organises the record, it does "
     "not produce the judgment."),
    ("Two conclusions come from the same battery. Risk belongs to the case: 98.07% of its variance comes from "
     "the duties and the context. Admissibility belongs to the delegation: 15.46% of cases change verdict "
     "depending on which profile faces them, and 225 can be rescued by a better agency. Improving the agent "
     "is therefore not the same as reducing risk, and a deployment that promises the first by investing in "
     "the second makes a claim the model can measure and reject.",
     "Two practical consequences follow. Risk is structural, so improving the agent does not reduce it by "
     "itself. Admissibility depends on the delegation, and 225 cases can be rescued by choosing a better "
     "agency. A deployment that promises lower risk by investing in the agent makes a claim this instrument "
     "can measure and reject."),
    ("κ = 0.5336 is not a measure of the quality of the model. It is the overlap between the model and one "
     "normative instrument. The claim that can be defended is qualified: the model agrees with the "
     "instruments where the instruments agree with each other, and outside that region the disagreement is "
     "documented, not resolved. Where both the model and the rubric abstain, the agreement of 1.000 records "
     "shared silence, not shared judgment.",
     "The κ reported here is not a measure of the quality of the model. It is the overlap between the model "
     "and one normative instrument. The claim that can be defended is qualified: the model agrees with the "
     "instruments where the instruments agree with each other, and outside that region the disagreement is "
     "documented, not resolved. Where both the model and the rubric abstain, the agreement of 1.000 records "
     "shared silence, not shared judgment."),
    ("The abstention classes make that visible: 18,240 pairs abstain because the profile does not declare "
     "enough duties and 16,375 because the case is epistemically underdetermined.",
     "The abstention classes make that visible."),
    ("ETH-WCMK v14 is a model whose geometry is proved, whose parameters are declared, whose mechanisms are "
     "measured before they are enabled and whose semantic layer reproduces its arithmetic to 1.61 × 10⁻¹². "
     "Its verdicts arrive with a trace readable in RDF, and its agreement with the normative reference — "
     "0.5336 overall, 0.8167 on unanimous cases — is limited more by the instrument that produces that "
     "reference than by the model. The contribution of this round is methodological as much as "
     "architectural: it shows how a model of machine ethics can be audited against its own numbers and what "
     "remains genuinely open.",
     "ETH-WCMK v14 is a model whose geometry is proved, whose parameters are explicit, whose mechanisms are "
     "measured before they are enabled and whose semantic layer reproduces its arithmetic to machine "
     "precision. Its verdicts arrive with a trace readable in RDF. The agreement it reaches with the "
     "normative reference is limited more by the instrument producing that reference than by the model "
     "itself. The contribution of this round is methodological as much as architectural: it shows how a "
     "model of machine ethics can be audited against its own numbers and what remains genuinely open."),
    ("It is a set of claims that can be checked from the repository: the structural hierarchy of the "
     "geometry is a theorem, not a parameter assumption; mechanisms that look plausible can be measured and "
     "rejected, and the rejection is published with its numbers; the ontology is not an illustration of the "
     "model but a mirror of it, and the difference between the two can be computed; and the quality of the "
     "empirical agreement is limited by the instrument that produces the reference verdict, a limitation "
     "that is quantified, not concealed.",
     "It is a set of claims that can be checked from the repository. The structural hierarchy of the "
     "geometry is a theorem, not a parameter assumption. Mechanisms that look plausible can be measured and "
     "rejected, and the rejection is published with its numbers. The ontology is not an illustration of the "
     "model but a mirror of it, and the difference between the two can be computed. The quality of the "
     "empirical agreement is limited by the instrument that produces the reference verdict, a limitation "
     "that is quantified, not concealed."),
    ("The governance tradition supplies instruments — the UNESCO Recommendation on the Ethics of "
     "Artificial Intelligence (UNESCO, 2021), the OECD Recommendation on AI (OECD, 2024), the EU AI Act "
     "(European Union, 2024), the GDPR (European Union, 2016), ISO/IEC 42001 (ISO/IEC, 2023), the Council of "
     "Europe Framework Convention (Council of Europe, 2024) and the NIST AI Risk Management Framework (NIST, "
     "2023) — which list duties without formalising how a particular case satisfies them (Jobin et al., "
     "2019; Dignum, 2019).",
     "The governance tradition supplies instruments: the UNESCO Recommendation on the Ethics of Artificial "
     "Intelligence (UNESCO, 2021), the OECD Recommendation on AI (OECD, 2024), the EU AI Act (European "
     "Union, 2024), the GDPR (European Union, 2016), ISO/IEC 42001 (ISO/IEC, 2023), the Council of Europe "
     "Framework Convention (Council of Europe, 2024) and the NIST AI Risk Management Framework (NIST, 2023). "
     "They list duties without formalising how a particular case satisfies them (Jobin et al., 2019; "
     "Dignum, 2019)."),
    ("SPARQL runs 42 checks, all passing, including the lattice census (15 slots, 108 incidences, correct "
     "weight sums), the registry rules (33 facets, 12 guard floors above zero, β sums of 1.0) and an "
     "arithmetic mirror over 403 instantiated confrontations, which agrees with core.decide to a maximum "
     "difference of 1.61 × 10⁻¹², below the declared tolerance of 1 × 10⁻⁶, with no verdict divergences.",
     "SPARQL runs 42 checks, all passing: the lattice census (15 slots, 108 incidences, correct weight "
     "sums), the registry rules (33 facets, 12 guard floors above zero, β sums of 1.0) and an arithmetic "
     "mirror over 403 instantiated confrontations. The mirror agrees with core.decide to a maximum "
     "difference of 1.61 × 10⁻¹², below the declared tolerance of 1 × 10⁻⁶, with no verdict divergences."),
    ("κ depends on the priors of the rubric. Moving the duty floors by 10% changes κ from 0.5336 to 0.5507 "
     "or 0.5250; reducing the set of categorical duties to three gives 0.5085; using a single lens gives "
     "0.5223, 0.3324 or 0.5147; moving the coverage gate to 0.80 gives 0.6005 and to 0.60 gives 0.4907; "
     "treating an undeclared duty as a violation gives 0.2974. The variant that exceeds 0.60 does so by "
     "increasing shared abstention, not by producing a better judgment.",
     "κ depends on the priors of the rubric. Moving the duty floors by 10% changes it from 0.5336 to 0.5507 "
     "or 0.5250. Reducing the set of categorical duties to three gives 0.5085; a single lens gives 0.5223, "
     "0.3324 or 0.5147; a coverage gate of 0.80 gives 0.6005, and one of 0.60 gives 0.4907. Treating an "
     "undeclared duty as a violation gives 0.2974. The variant above 0.60 gains by increasing shared "
     "abstention, not by producing a better judgment."),
    ("The panels are unanimous on 50.9% of the pairs; 31,279 pairs (14.2%) are settled by the kernel alone, "
     "below the declared ceiling of 40%. Between themselves the panels agree at 0.6447 (A–C), 0.3533 (A–B) "
     "and 0.3153 (B–C). The rubric is not a single voice, and lens B diverges from the model more than the "
     "others (0.3324 against 0.5223 and 0.5147), which is expected: the core is built on duties and limits, "
     "and the prudential lens penalises that asymmetry.",
     "The panels are unanimous on 50.9% of the pairs, and the kernel settles 31,279 of them (14.2%) alone, "
     "below the stated ceiling of 40%. Between themselves they agree at 0.6447 (A–C), 0.3533 (A–B) and "
     "0.3153 (B–C). The rubric is not a single voice. Lens B diverges from the model more than the others "
     "(0.3324 against 0.5223 and 0.5147), which is expected: the core is built on duties and limits, and "
     "the prudential lens penalises that asymmetry."),
    ("Corpus v7 contains 1,520 cases — 1,200 generated with distinct parameter vectors and 320 narrative "
     "cases — confronted with 145 profiles: 144 persona instances across 36 archetypes and one "
     "self-declared profile. The result is 220,400 case–profile pairs.",
     "Corpus v7 contains 1,520 cases, 1,200 generated with distinct parameter vectors and 320 narrative "
     "cases, and 145 profiles: 144 persona instances across 36 archetypes and one self-declared profile. "
     "The confrontation produces 220,400 pairs."),
    ("Twenty-four persona types concentrate a deficit in one pillar, one per duty; six declare only between "
     "9 and 33 of the 33 duties, which is what makes coverage a live parameter.",
     "Twenty-four persona types concentrate a deficit in a single pillar, one per duty. Six profiles report "
     "between 9 and 33 of the 33 duties, which makes coverage a live parameter."),
    ("The round also records the opposite decision: a cross-pillar term that reduces agreement is not a "
     "defect to hide but a hypothesis falsified with numbers, and it survives as a diagnostic in the graph "
     "where governance can use it without the verdict depending on it.",
     "The round also records the opposite decision. A cross-pillar term that reduces agreement is not a "
     "defect to hide: it is a hypothesis falsified with numbers. It survives as a diagnostic in the graph, "
     "where governance can use it without the verdict depending on it."),
    ("The practical consequence is narrow and usable: the hole found in v12, where a strong level in one "
     "duty covered a failing duty in another, now leaves an event that an audit can cite instead of a score "
     "to interpret.",
     "The practical consequence is narrow and usable. The hole found in v12, where a strong level in one "
     "duty covered a failing duty in another, now produces an event an audit can cite instead of a score to "
     "interpret."),
    ("Every class, individual and constant comes from the registry, the core or the corpus generator, so a "
     "facet in the graph is a facet the core applies, and a guard floor in the graph is the same number as "
     "the guard floor in the code.",
     "Every class, individual and constant comes from the registry, the core or the corpus generator. A "
     "facet in the graph is a facet the core applies, and a guard floor in the graph is the same number as "
     "the guard floor in the code."),

    ("recomputed integrally in the pessimistic and optimistic modes rather than derived from the "
     "central value by adding a constant",
     "recomputed integrally in the pessimistic and optimistic modes, not from the central value plus "
     "a constant"),
    ("the same shortfall produces review rather than prohibition in a low-stakes case",
     "the same shortfall produces review instead of prohibition in a low-stakes case"),
    ("so they belong in the audit record rather than in a code default",
     "so they belong in the audit record, not in a code default"),
    ("Hysteresis h = 0.05", "Hysteresis, the margin h = 0.05 that prevents oscillation"),
    ("with bootstrap confidence intervals on the difference",
     "with confidence intervals estimated by resampling (bootstrap)"),
    ("the guard failures and the material gap, the stakes and the veto",
     "the guard failures and the material gap — the worst failure a duty cannot compensate — the stakes and "
     "the veto"),
    ("Salience, the weight a duty carries in a particular case, and cross-pillar exposure, the reach of "
     "a duty across pillars, are implemented and tested",
     "Salience, the weight a duty carries in a particular case, and cross-pillar exposure, the reach of "
     "a duty across pillars, are implemented and tested"),

    ("New in this round: I34 tests Proposition 1 over the complete grid of deficits; I35 refuses to load "
     "an incoherent calibration; I36 makes the unspecified oversight regime identical to v12 and states "
     "the weights of ReviewNeed; I37 proves that λ(E) is the identity when s = 0; I38 orders the stakes "
     "by regime; I39 proves that adequacy with ζ = 0 differs from v12 by exactly ζ times Ψ; I44 validates "
     "the coverage gate as a parameter.",
     "Seven tests were added. I34 checks Proposition 1 over the complete grid of deficits. I35 refuses to "
     "load an incoherent calibration. I36 makes the unspecified oversight regime identical to v12 and "
     "states the weights of ReviewNeed. I37 proves that λ(E) is the identity when s = 0. I38 orders the "
     "stakes by regime, and I39 proves that adequacy with ζ = 0 differs from v12 by exactly ζ times Ψ. "
     "I44 validates the coverage gate as a parameter."),
    ("Coverage becomes a declared parameter, and the corpus now contains", "Coverage becomes an explicit parameter, and the corpus contains"),
    ("Coverage as a declared parameter: 18,240", "Coverage as an explicit parameter: 18,240"),
    ("rho = 0.10, delta = 0.05 and zeta = 0 are declared in the core",
     "rho = 0.10, delta = 0.05 and zeta = 0 are fixed in the core"),
    ("It is declared non-decisional: it cannot", "It is explicitly non-decisional: it cannot"),
    ("Its weights sum to one and are declared in the ontology", "Its weights sum to one and are stated in the ontology"),
    ("The 0.70 coverage gate is declared, not derived from first principles",
     "The 0.70 coverage gate is a design choice, not a derivation from first principles"),
    ("It is declared non-executable together with", "It is reported non-executable together with"),
    ("the non-executability is declared with the measurement", "the non-executability is stated with the measurement"),
    ("Persona levels are declared by a generator", "Persona levels are set by a generator"),
    ("so they must be declared, versioned and reviewed", "so they must be stated, versioned and reviewed"),

    ("The consensus κ of the panels with each other is 0.6447 (A–C), 0.3533 (A–B), 0.3153 (B–C): the ceiling "
     "of any model evaluated against this consensus is bounded by it.",
     "The panels' agreement with one another bounds the ceiling of any model evaluated against their "
     "consensus."),
    ("Coverage as a declared parameter: 18,240", "Coverage as an explicit parameter: 18,240"),
    ("A differentiated β canon: ten facets reweighted, identical pairs reduced from 8 to 1, κ increased "
     "by 0.0019.", "A differentiated β canon: ten facets reweighted, identical pairs reduced from 8 to 1, "
     "and agreement raised by 0.0019."),
    ("Oversight inferred from reported facts: κ increased by 0.0078.",
     "Oversight inferred from reported facts: agreement raised by 0.0078."),

    ("The abstention classes make that visible.",
     "The two abstention classes, coverage and epistemic underdetermination, make that visible."),

]

def polish(text):
    for old, new in POLISH:
        text = text.replace(old, new)
    return text

SYMBOLS = [
    (r"\balpha_e\b", "α_e"), (r"\bDelta_ov\b", "Δ_ov"), (r"\bDelta_h\b", "Δ_h"), (r"\bGodel\b", "Gödel"),
    (r"\balpha\b", "α"), (r"\bbeta\b", "β"), (r"\bgamma\b", "γ"), (r"\bdelta\b", "δ"), (r"\bEta\b", "η"),
    (r"\bEta\b", "η"), (r"\btheta\b", "θ"), (r"\bkappa\b", "κ"), (r"\bmu\b", "μ"),
    (r"\bomega\b", "ω"), (r"\brho\b", "ρ"), (r"\bzeta\b", "ζ"), (r"\bPsi\b", "Ψ"),
    (r"\bPhi\b", "Φ"), (r"\bsigma\b", "σ"), (r">=", "≥"), (r"<=", "≤"),
    (r"S2, S3, S4", "S₂, S₃, S₄"), (r"v10-v12", "v10–v12"),
]

def caption(text):
    text = polish(text)
    for pat, new in SYMBOLS:
        text = re.sub(pat, new, text)
    return text

def section(doc, name, items):
    doc.add_heading(name, level=2 if re.match(r"^\d+\.\d+", name) else 1)
    for kind, payload in items:
        if kind == "p":
            para(doc, polish(payload), align="justify")
        elif kind == "b":
            bullets(doc, [caption(x) if isinstance(x, str) else x for x in payload])
        elif kind == "eq":
            latex, label, cap = EQS[payload]
            equation(doc, latex, label, caption(note(cap)))
        elif kind == "t":
            cap, header, rows, widths = payload
            table(doc, header, [[caption(c) if isinstance(c, str) else c for c in row] for row in rows],
                  widths=widths, caption_text=polish(cap))
        elif kind == "f":
            path, cap = payload
            figure(doc, path, caption(cap))


def reference_list(doc, refs):
    """Standard author-date entries, hanging indent, no bullets."""
    for r in refs:
        p = para(doc, r, style="SmallText", align="justify")
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Cm(0.15)


def main():
    doc = new_document()
    title_block(
        doc,
        "ETH-WCMK v14: a formally verified core and a SHACL-valid ontology for auditing "
        "delegated ethical agency",
        "Luiz Palazzo and Tarcísio Vanzin",
        "Federal University of Santa Catarina (UFSC), Postgraduate Program in Engineering "
        "and Knowledge Management (PPGEGC), Brazil",
        "Preprint. Formal core v13, ontology v4.2, corpus v7.",
    )
    para(doc,
         "Manuscript to be deposited on arXiv (cs.CY; cs.AI). The journal venue is not yet "
         "decided. The code, the corpus, the ontology and every evaluation artefact are "
         "published in the project repository at " + REPO + ".",
         style="SmallText", align="center", italic=True)

    para(doc,
         "Abstract. ETH-WCMK confronts an ethical case with a profile of delegated agency — "
         "the agency a human organisation transfers to a system that acts on its behalf — and "
         "returns one of five verdicts: ABSTAIN, PROHIBIT, REVIEW_REQUIRED, ALLOW_WITH_GUARDS "
         "or ALLOW. Each verdict is accompanied by the quantities that make it reviewable: an "
         "adequacy band, the deficit of each pillar and each duty, the largest duty failing its "
         "floor, the risk that survives an adequate profile, the external review the verdict "
         "requires and the trace of the computation.", align="justify")
    para(doc, polish(
         "Four changes distinguish this round. The hierarchy S₂ ≥ S₃ ≥ S₄ of the tetrahedral "
         "layer no longer depends on a condition over the parameters: the edge weights of the "
         "face lattice are derived from the facet weights, the inequality holds for every "
         "deficit vector, and at β = 1/4 the derived α is 1/6, the value already calibrated, so "
         "no published number changes. Ten of the 33 facets are reweighted, β-identical pairs "
         "fall from 8 to 1, and agreement with the normative panels rises by 0.0019 (95% CI "
         "0.0009–0.0032). The oversight regime is inferred from the facts the case reports, and "
         "it is the only mechanism that measurably improves agreement: 0.0078 (95% CI "
         "0.0057–0.0100) on 130,680 pairs. Coverage becomes a declared parameter, and the "
         "corpus now contains genuinely partial profiles, which produce 18,240 abstentions. "
         "Salience, the weight a duty carries in a particular case, and cross-pillar exposure, "
         "the reach of a duty across pillars, are implemented and tested; both remain inert "
         "because their measured effect is zero or negative."), align="justify")
    para(doc, polish(
         "The core is verified by 69 invariant tests, 2,064 adversarial probes and 7,815 "
         "assertions with a pass rate of 1.000, and by an arithmetic mirror over all 220,400 "
         "confrontations of the corpus, whose maximum difference is 0.0. The semantic layer "
         "holds 1,927,780 validated RDF triples, satisfies 34 SHACL node shapes without "
         "violations, detects 76 of 76 deliberately invalid fixtures and reproduces the "
         "arithmetic of the core to 1.61 × 10⁻¹². Agreement with the normative reference is "
         "0.5336 overall, 0.8167 on the cases where the three normative lenses agree and 0.0526 "
         "on the contested ones. The panels disagree with one another at 0.6447, 0.3533 and "
         "0.3153, and κ, the coefficient of agreement that corrects for agreement by chance "
         "(Cohen, 1960), moves between 0.2974 and 0.6005 under eleven defensible priors. The "
         "ceiling is therefore set by the normative instrument, not by the model."),
         align="justify")

    para(doc, "Keywords. machine ethics; delegated ethical agency; formal verification; RDF "
             "ontology; SHACL; sensitivity analysis; governance instruments; ethical AI; "
             "auditability; tetrahedral model")

    # ---------------------------------------------------------------- 1
    section(doc, "1. Introduction", [
        ("p", "Automated systems now mediate decisions with consequences for identifiable "
             "people: a triage queue, a credit decision, a moderation action, a route dispatched "
             "by an autonomous vehicle (Mittelstadt et al., 2016; Eubanks, 2018; Zuboff, 2019). "
             "Auditing such a decision requires two objects at once. One is the case: what is at "
             "risk, who is affected, how irreversible the consequence is, which duties are in "
             "tension. The other is the agent: what it can do, what it is obliged to do and what "
             "it knows. A verdict that merges the two into a single score discards the "
             "information that makes the verdict reviewable (Miller, 2019; Williams et al., 2022)."),
        ("p", "ETH-WCMK was presented in earlier rounds as a dual ontology. ETHCASE describes "
             "the ethical case; WCMK (Want, Can, Must, Know) describes the agency profile; a "
             "regular tetrahedron indexes the relation between them. The earlier versions "
             "described a representation. This round makes the representation testable: the "
             "arithmetic is implemented, its properties are checked by a test suite, and the "
             "semantic layer is generated from the code and validated against the code's own "
             "numbers."),
        ("p", "The contribution is not a new score. It is a set of claims that can be checked "
             "from the repository: the structural hierarchy of the geometry is a theorem rather "
             "than a parameter assumption; mechanisms that look plausible can be measured and "
             "rejected, and the rejection is published with its numbers; the ontology is not an "
             "illustration of the model but a mirror of it, and the difference between the two "
             "can be computed; and the quality of the empirical agreement is limited by the "
             "instrument that produces the reference verdict, a limitation that is quantified "
             "rather than concealed."),
        ("b", [
            "Proposition 1: deriving α from β makes S₂ ≥ S₃ ≥ S₄ hold for every deficit vector, "
            "without changing any published number.",
            "A differentiated β canon: ten facets reweighted, identical pairs reduced from 8 to 1, "
            "κ increased by 0.0019.",
            "Oversight inferred from reported facts: κ increased by 0.0078.",
            "Coverage as a declared parameter: 18,240 pairs abstain because the profile does not "
            "cover enough duties.",
            "ReviewNeed, an index that orders cases by the review their verdict requires without "
            "changing the verdict.",
            "Two mechanisms implemented, tested and rejected: λ(E) and Ψ, with κ ≤ 0 when they "
            "are activated.",
            "Ontology v4.2: 1,927,780 triples, 34 shapes, no violations, mirror agreement of "
            "1.61 × 10⁻¹².",
            "An instrument for human adjudication (120 blind pairs) and a measurement of how κ "
            "depends on the priors of the normative rubric.",
        ]),
    ])

    # ---------------------------------------------------------------- 2
    section(doc, "2. Machine ethics, governance instruments and operational stacks", [
        ("p", "Machine ethics has developed in four families (Moor, 2006; Floridi, 2004; "
             "Wallach & Allen, 2008; Allen, Smit & Wallach, 2005; Anderson & Anderson, 2011). "
             "Top-down approaches encode principles; bottom-up approaches learn values from data "
             "or interaction; hybrid approaches combine the two; alignment programmes optimise "
             "objective functions (Bostrom & Yudkowsky, 2016). The governance tradition supplies "
             "instruments — the UNESCO Recommendation on the Ethics of Artificial Intelligence "
             "(UNESCO, 2021), the OECD Recommendation on AI (OECD, 2024), the EU AI Act (European "
             "Union, 2024), the GDPR (European Union, 2016), ISO/IEC 42001 (ISO/IEC, 2023), the "
             "Council of Europe Framework Convention (Council of Europe, 2024) and the NIST AI "
             "Risk Management Framework (NIST, 2023) — which list duties without formalising how "
             "a particular case satisfies them (Jobin et al., 2019; Dignum, 2019)."),
        ("p", "Operational stacks, such as moderation APIs and guard models, solve a different "
             "problem: filtering content at scale, in the manner of functional-safety and "
             "information-security standards (ISO, 2018; ISO/IEC, 2023; NIST, 2025). They enforce "
             "well and justify poorly. They do not represent the duties of the agent, the "
             "irreversibility of a consequence or the chain that delegates a duty. ETH-WCMK "
             "occupies that gap."),
        ("t", ("Table 1. Position of ETH-WCMK relative to the main families of machine-ethics "
               "approaches.",
              ["Family", "What it represents", "What it leaves out", "How ETH-WCMK differs"],
              [["Principle-based (top-down)", "Principles and rules", "Context, capacity, measurement",
                "Principles become typed duties anchored to named instruments"],
               ["Learning-based (bottom-up)", "Preferences from data", "Normative justification",
                "The model does not learn values; it measures declared capability against duties"],
               ["Value alignment", "Objective functions", "Institutional duties and redress",
                "Adequacy is measured per duty, not per objective"],
               ["Governance frameworks", "Obligations at the institutional level", "The decision per case",
                "34 operational rules derived from instruments, applied to each case–agent pair"],
               ["Safety stacks", "Content filtering at scale", "Agency, oversight, redress",
                "Verdict plus trace: deficits, gap, risk, review need, regime"],
               ["ETH-WCMK", "Case and agency confronted, with a trace", "Human judgment (pending, instrumented)",
                "Formal core and validated ontology, both testable"]],
              [1.3, 1.6, 1.6, 2.0]),
        ),
        ("p", "The principle that separates the model from the rest is non-compensation, in the "
             "deontic sense of Ross (2002): a duty that cannot be traded is not a weight in a "
             "score. A shortfall in one duty earns no credit in another; adequacy attenuates "
             "consequences without erasing them; and the verdict is taken on the lower bound of "
             "the adequacy band, not on its centre. The model does not claim that the agent is "
             "virtuous (Vallor, 2016). It measures whether the duties the agent declared were "
             "met."),
    ])

    # ---------------------------------------------------------------- 3
    section(doc, "3. The model: two objects and a bridge", [
        ("f", (FIG + "/fig1_pipeline.png",
               "Figure 1. The confrontation pipeline: an ETHCASE and a WCMK profile meet in the "
               "formal core, which produces a verdict and a trace, and the ontology mirrors that "
               "trace in RDF.")),
        ("p", "An ETHCASE records the domain, severity, irreversibility, prudential mode, "
             "temporal horizon, epistemic uncertainty, the number and nature of those affected, "
             "the pattern of duties in conflict and the procedural facts the case can support: "
             "whether logs exist, whether notice was given, whether an appeal channel exists, "
             "whether consent was obtained, whether an incident occurred earlier. A WCMK profile "
             "records the level achieved on each of the 33 canonical duties, the β vector that "
             "assigns each duty to pillars, four aggregation policies, twelve hard guards and the "
             "subset of duties the agent has actually taken on."),
        ("p", "The arithmetic of the core produces, in order: the projection of levels and "
             "requirements onto the four pillars, the deficits, the structural terms of the "
             "tetrahedron, the raw adequacy, the guard failures and the material gap, the stakes "
             "and the veto, the adequacy band, the abstention conditions, residual risk, review "
             "need and the verdict. Each of these is a field in the ontology, so a verdict can "
             "always be rebuilt from the graph. The representation is conceptual rather than "
             "lexical: two cases written in different words enter the same arithmetic only if they "
             "occupy the same roles, the assumption the model inherits from the semiotic account "
             "of representation (Peirce, 1931–1958; Gärdenfors, 2000)."),
    ])

    # ---------------------------------------------------------------- 4
    section(doc, "4. The formal core", [
        ("p", "The core is four files, about 1,070 lines: core.py (the arithmetic), geometry.py "
             "(the lattice), facet_registry.py (the 33 duties) and fact_grounding.py "
             "(the observational caps). Its parameters are explicit rather than implicit: "
             "Calibration.is_valid() rejects an incoherent set, and the invariant suite tests the "
             "behaviour of each one."),
    ])
    section(doc, "4.1 Pillars, geometry and Proposition 1", [
        ("p", "W (Want), C (Can), M (Must) and K (Know) are independent magnitudes, not shares "
             "of a simplex: an agent can be competent and obliged at the same time. The "
             "tetrahedron does not measure a state; it indexes the relation between duties, as a "
             "representational device in the sense of conceptual spaces (Gärdenfors, 2000). Its "
             "face lattice has fifteen slots — four vertices, six edges, four faces and one cell "
             "— and a duty is represented by the face it spans."),
        ("f", (FIG + "/fig2_lattice.png",
               "Figure 2. The face lattice of the 3-simplex: four vertices, six edges, four faces "
               "and one cell. Each duty occupies the face it spans, and the edge weights are the "
               "marginal of the face weights.")),
        ("eq", 0),
        ("eq", 1),
        ("p", "Proposition 1. If the weight of every edge is one third of the sum of the weights "
             "of the faces that contain it, and the four face weights sum to one, then S₂ ≥ S₃ ≥ "
             "S₄ for every deficit vector d ≥ 0. Each edge of the tetrahedron lies in exactly two "
             "faces, so the derived edge weights sum to one; the three edges of a face sum to a "
             "quantity proportional to the weight of that face; and the minimum over an edge is "
             "never smaller than the minimum over the face containing it, because the Gödel "
             "t-norm is monotone. In v12 the inequality required a condition on α; in v13 α is "
             "derived, so the condition disappears."),
        ("p", "The consequence is measurable. At β = 1/4 the derived α is exactly 1/6, the value "
             "used in the v10–v12 calibration, so the reparameterisation changes nothing already "
             "published. The proposition was tested over the complete grid {0, 0.05, …, 1}⁴ with "
             "four β vectors, including non-uniform ones, and the mirror over the corpus "
             "confirms that the derived α reproduces the earlier numbers to 0.0 (Sec. 7.7).",
        ),
    ])
    section(doc, "4.2 The canon of 33 duties", [
        ("p", "The canon is deontic in the classical sense (Kant, 2012; Ross, 2002) and obeys "
             "three rules: the β vector of a duty sums to one, at most three pillars may be "
             "non-zero, and every non-zero component is at least 0.15. The census is one "
             "single-pillar duty, ten two-pillar and twenty-two three-pillar duties; none spans "
             "all four. Twelve duties carry a hard guard: below the guard floor the duty cannot be "
             "compensated by another pillar."),
        ("t", ("Table 2. The canonical facet set: β over (W, C, M, K), number of pillars, "
               "aggregation policy and guard floor.",
              ["Code", "Duty", "β (W / C / M / K)", "Pillars", "Aggregation policy", "Guard floor"],
              [list(r) for r in FACETS], [0.5, 1.6, 1.5, 0.6, 1.5, 0.7]),
        ),
        ("p", "Reweighting β in this round changed ten duties: W6, C2, C5, M2, M4, M10, K1, K2, "
             "K5 and K7. Pairs with identical β vectors fell from 8 to 1; C3 and C7 remain "
             "deliberately equivalent, since both are containment duties. Pairs with Chebyshev "
             "distance below 0.12 fell from 26 to 23, while former duplicates became close pairs, "
             "which is why the count of strictly near-identical pairs rose from 18 to 22. The "
             "measured effect on agreement with the panels is +0.0019 (95% CI 0.0009–0.0032), and "
             "+0.0094 when combined with the oversight mechanism."),
    ])
    section(doc, "4.3 Requirements, projection and deficits", [
        ("eq", 2), ("eq", 3), ("eq", 4), ("eq", 5),
        ("p", "The requirement a duty imposes in a case is its criticality base — 0.55, 0.70 or "
             "0.85 for criticality 2, 3 or 4 — plus terms for severity, irreversibility, prudential "
             "mode and horizon, an uncertainty term for duties whose primary pillar is K, and 0.08 "
             "on the human-review duty M9 when the case reports no oversight regime: what the "
             "institution does not provide, the agent has to supply. For guarded duties the "
             "requirement never falls below the guard floor plus 0.05. No duty carries a separate "
             "weight: β is the only weight in the model."),
        ("p", "A reported level is limited by a verifiable fact. If an agent claims an "
             "accountability level of 0.9 and no logs exist, the level is capped by the requirement "
             "of that duty scaled by the compliance the fact implies. The cap applies only to "
             "duties actually reported; an unreported duty is recorded as missing coverage, not as "
             "a zero. Without this distinction, 75.8% of the prohibitions the panels issue would be "
             "invisible to the arithmetic."),
    ])
    section(doc, "4.4 Structural terms, adequacy and the veto", [
        ("eq", 6), ("eq", 7), ("eq", 8), ("eq", 9), ("eq", 10),
        ("p", "A duty fails as a guard when the level achieved, after the observational cap, is "
             "below its requirement. The material gap is the largest such failure among duties the "
             "domain marks critical or that carry a hard guard. A veto is triggered on a pillar "
             "when the worst gap among the duties touching it reaches the pillar threshold θ and "
             "the pillar is critical for the domain or a guard floor has been crossed. It is a hard "
             "veto when that gap exceeds θ by 0.25 adjusted for the stakes, or when a floor breach "
             "coincides with stakes of at least 0.70. Both conditions are recorded fields in the "
             "graph, because a threshold that is not stated cannot be audited. Adequacy is then "
             "capped: it cannot exceed 1 − (0.40 + 0.40 stakes) times the governing gap.",
        ),
    ])
    section(doc, "4.5 Stakes, oversight and residual risk", [
        ("p", "Stakes weight severity, effective irreversibility, prudential posture and horizon. "
             "Oversight enters through irreversibility: harm that a verified human review can still "
             "catch is not the same harm as harm no one can catch. The regime is inferred from what "
             "the case reports — review plus independent audit gives a regime in the loop; review "
             "or an appeal channel gives one on the loop; nothing reported gives none; nothing "
             "stated at all gives the unspecified case, which reproduces the v12 behaviour exactly. "
             "The ordering of stakes by regime is proved by the suite, and adequacy under the "
             "unspecified regime equals the v12 adequacy."),
        ("eq", 11), ("eq", 12), ("eq", 13), ("eq", 14), ("eq", 15),
        ("p", "Risk is a potential consequence modulated by the delivery capacity observed in the "
             "agent, in the sense of responsibility for consequences that outlive the act (Jonas, "
             "1984). It never vanishes: a fully adequate agent still carries residual risk, because "
             "the probability of failure is not zero and adequacy does not reduce the mass of the "
             "consequence."),
    ])
    section(doc, "4.6 Uncertainty, coverage and abstention", [
        ("eq", 16), ("eq", 17),
        ("p", "Confidence propagates into an adequacy band, and the verdict is taken on its lower "
             "bound. The coverage gate, set at 0.70 of the 33 duties, is a parameter rather than a "
             "hidden constant: a profile declaring 23 duties abstains with the gate at 0.70 and "
             "does not abstain at 0.60. That is the difference between a model that punishes "
             "silence and a model that refuses to judge what it cannot see. In the corpus, the two "
             "ways of treating an undeclared duty give κ of 0.8085 and 0.0801 on the same 36,480 "
             "pairs."),
    ])
    section(doc, "4.7 Review need, salience and cross-pillar duty", [
        ("eq", 18), ("eq", 19),
        ("p", "ReviewNeed is declared non-decisional: it may not change the class of a verdict, "
             "only order the cases that share one by the external review they actually require. Its "
             "weights sum to one and are declared in the ontology. Ψ measures how much of a duty "
             "escapes the pillar that carries it — the containment component of C6 belongs to M, "
             "for instance — and that exposure is recorded as a governance diagnostic without "
             "entering the score."),
    ])
    section(doc, "4.8 The decision ladder and stratified agency", [
        ("eq", 20), ("eq", 21),
        ("p", "The ladder is lexicographic and runs on Aa_low: abstention first, then the hard "
             "veto, then categorical prohibition, then review, then conditional allowance, then "
             "allowance. Hysteresis prevents oscillation: a verdict loosens only if adequacy clears "
             "the bar by 0.05, and tightens immediately. Agency is stratified into model, system "
             "and operator, because the capacity to act and the capacity to answer for the act are "
             "not the same thing (Frankfurt, 1971); the chain is evaluated at its weakest link and "
             "the result of each layer is reported. Only one of the 33 duties can be carried by a "
             "model or a tool alone, which is why delegation has consequences."),
        ("f", (FIG + "/fig3_ladder.png",
               "Figure 3. The decision ladder, its thresholds and the hysteresis that governs "
               "loosening.")),
    ])
    section(doc, "4.9 Canonical parameters", [
        ("t", ("Table 3. Canonical parameters of the v13 core, their status and the equation in "
               "which they appear.",
              ["Parameter", "Canonical value", "Status", "Equation"],
              [list(r) for r in CALIB], [1.7, 2.3, 1.4, 0.8]),
        ),
    ])

    # ---------------------------------------------------------------- 5
    section(doc, "5. The semantic layer: ontology v4.2", [
        ("p", "The ontology is generated from the code rather than written by hand. Every class, "
             "individual and constant comes from the registry, the core or the corpus generator, so "
             "a facet in the graph is a facet the core applies, and a guard floor in the graph is "
             "the same number as the guard floor in the code. The namespace is ethwcmk.org, with "
             "the prefixes eth, fac, cal, cse, ag and norm, supported by PROV, SKOS, OWL, SHACL and "
             "TIME (W3C, 2012; W3C, 2014; W3C, 2017). The semantics live in typed individuals, not "
             "in OWL reasoning."),
        ("p", "The vocabulary contains 69 classes, 84 object properties, 225 datatype properties "
             "and 29,310 named individuals. Its principal classes are Agent, AgentLayer, "
             "DelegationChain, ChainLink, Profile, EthicalCase, Facet, FacetObservation, "
             "FacetRequirement, GuardFailure, Norm, NormativeInstrument, NormConflict, Obligation, "
             "Permission, Prohibition, LatticeSlot, StructuralTerm, Confrontation, Decision, "
             "Evidence, Consequence, Stakeholder, Vulnerability, OversightRegime, Calibration and "
             "FactGrounding. Facets are typed into the four pillar families, and guarded facets "
             "carry the GuardedFacet type."),
        ("f", (FIG + "/fig7_ontology.png",
               "Figure 4. Ontology v4.2: modules, instance graph and the validation gates.")),
        ("t", ("Table 4. Ontology modules and the elements they declare.",
              ["Module", "Triples", "What it declares"],
              [["01_core", "1,804", "pillars, the 15 lattice slots, structural terms, weights"],
               ["02_facets", "2,381", "33 facets, β components, policy, guard floor, observables, 429 criticality statements"],
               ["03_deontic", "3,716", "123 norms, 62 instruments, 88 conflicts, 73 obligations, 26 permissions, 24 prohibitions, 5 priority engines, 5 defeasibility rules, 8 resolution strategies"],
               ["04_agency", "256", "three agent layers, delegation rules, pillars a layer cannot carry"],
               ["05_dynamics", "141", "drift profiles, the hysteresis rule, value mappings for severity, reversibility and prudential mode"],
               ["06_calibration", "148", "the ladder, declared coefficients and their sum constraints, two Calibration individuals"],
               ["07_grounding", "63", "the observational cap rules"],
               ["shapes (v4 and v6)", "1,347", "34 node shapes for the core graph, plus six for the v13 mechanisms"]],
              [1.1, 0.8, 4.6]),
        ),
        ("t", ("Table 5. Instance graph generated from corpus v7 (count of typed individuals).",
              ["Class", "Individuals", "Class", "Individuals"],
              [["Agent", "6,224", "FacetRequirement", "50,160"],
               ["Profile", "5,150", "FacetObservation", "169,950"],
               ["DelegationChain / ChainLink", "4,560 / 4,560", "FactGrounding", "21,280"],
               ["Confrontation", "3,755", "GuardFailure", "16,475"],
               ["EthicalCase", "1,520", "Consequence / Evidence / Stakeholder", "320 / 320 / 960"],
               ["Norm / Instrument / Conflict", "123 / 62 / 88", "Decision / OversightRegime", "5 / 5"],
               ["Facet", "33", "CriticalityStatement", "429"]],
              [1.9, 1.0, 1.9, 1.0]),
        ),
        ("p", "The shapes constrain the graph with the same rules the code implements: β must sum "
             "to exactly 1 with at most three non-zero components, each at least 0.15; severity, "
             "reversibility, prudential mode and horizon must be among the declared individuals; "
             "a lattice slot must be a vertex, edge, face or cell and satisfy the incidence rules; "
             "a prohibition must declare the obligation it bars; a conflict must declare its "
             "resolution strategy and outcome, consistently with whether it was resolved; every "
             "level, risk and adequacy field is bounded to [0, 1]; and the v6 shapes add the bounds "
             "for review need, salience and the oversight enumeration."),
        ("p", "Validation consists of four independent checks. SHACL reports zero violations "
             "against both shape sets. The 76 deliberately invalid fixtures, each constructed to "
             "break exactly one shape, were all detected and attributed to the shape they were "
             "designed to break. SPARQL runs 42 checks, all passing, including the lattice census "
             "(15 slots, 108 incidences, correct weight sums), the registry rules (33 facets, 12 "
             "guard floors above zero, β sums of 1.0) and an arithmetic mirror over 403 "
             "instantiated confrontations, which agrees with core.decide to a maximum difference "
             "of 1.61 × 10⁻¹², below the declared tolerance of 1 × 10⁻⁶, with no verdict "
             "divergences. The whole validation took 301.9 s."),
        ("p", "Three defects appeared during validation and were corrected. A SPARQL check of the "
             "β sum used the facet's own literal, which SHACL already enforces, so the check was "
             "tautological; two checks used nested sub-selects and predicate expressions inside "
             "BIND, which are not valid SPARQL and were rejected by the engine; and a check that "
             "read coverage from the Profile, where it is not asserted, was rewritten to read it "
             "from the Confrontation. A validator that cannot fail validates nothing, so the "
             "invalid fixtures are part of the test rather than an afterthought."),
    ])

    # ---------------------------------------------------------------- 6
    section(doc, "6. Corpus and normative ground truth", [
        ("p", "Corpus v7 contains 1,520 cases — 1,200 generated with distinct parameter vectors "
             "and 320 narrative cases — confronted with 145 profiles: 144 persona instances across "
             "36 archetypes and one self-declared profile. The result is 220,400 case–profile "
             "pairs. The cases span 13 domains: health, justice and security, critical "
             "infrastructure, finance, privacy, public governance, media, education, labour, "
             "environment and energy, transport, research and digital security. Twenty-four persona "
             "types concentrate a deficit in one pillar, one per duty; six declare only between 9 "
             "and 33 of the 33 duties, which is what makes coverage a live parameter."),
        ("p", "The reference verdict comes from an operational rubric, not from human judges. A "
             "shared kernel anchors every panel to a duty and a floor, and three lenses apply "
             "explicit rule tables: A is deontological (rights, due process, consent), B prudential "
             "(expected harm, redress, bounded harm, sunset clauses) and C institutional (data "
             "minimisation, human review, fail-safe design, detect and respond). Thirty-four rules, "
             "each anchored to a named instrument — the Rio Declaration (1992), UDHR Article 10 "
             "(United Nations, 1948), UN CRC Article 12 (United Nations, 1989), GDPR Articles 5, 22 "
             "and 25 (European Union, 2016), the Belmont Report (1978), the Declaration of Helsinki "
             "(1964), the ILO Declaration (International Labour Organization, 1998), ACM/IEEE "
             "codes, ISO 26262 (ISO, 2018), IEC 62443, ISO 27001 (ISO/IEC, 2023), the NIST "
             "Framework (NIST, 2025) and the OECD Recommendation (OECD, 2024) — fire on the facts "
             "and levels reported, and each firing is counted separately from the verdict it "
             "actually changes. Rule A8, three or more duties below their floor, fires on 137,723 "
             "pairs and changes the panel verdict in 76,559 of them."),
        ("p", "The consensus of the three panels is the reference, and agreement with it is "
             "measured with Cohen's κ (Cohen, 1960). The panels are unanimous on 50.9% of the "
             "pairs; 31,279 pairs (14.2%) are settled by the kernel alone, below the declared "
             "ceiling of 40%. Between themselves the panels agree at 0.6447 (A–C), 0.3533 (A–B) "
             "and 0.3153 (B–C). The rubric is not a single voice, and lens B diverges from the "
             "model more than the others (0.3324 against 0.5223 and 0.5147), which is expected: the "
             "core is built on duties and limits, and the prudential lens penalises that "
             "asymmetry."),
    ])

    # ---------------------------------------------------------------- 7
    section(doc, "7. Results", [
        ("p", "Table 6 lists the gates of the round, each with the artefact that measures it.",
        ),
        ("t", ("Table 6. Gates of Round 5 and their verdicts.",
              ["Gate", "Content", "Verdict", "Evidence"],
              [["G10", "Core v13: unconditional hierarchy, derived α, λ(E), ReviewNeed, oversight",
                "PASS", "pytest suite, 69 invariants, 45.75 s"],
               ["G11", "Facet canon: differentiated β, guards, measured ablation",
                "PASS with explicit rejection", "B21_ablation.json"],
               ["G12", "Is the geometric layer informative? Ψ diagnostic, ζ rejected", "PASS", "B20, B21, B23"],
               ["G13", "Corpus v7: genuinely incomplete profiles, derived oversight, rebalanced domains",
                "PASS", "corpus_v7_coverage.json"],
               ["G14", "Ontology v4.2 revalidated", "PASS, 42/42 checks, mirror 1.61 × 10⁻¹²",
                "ontology_v4_2_validation.json"],
               ["G15", "Batteries B20–B25", "5 of 6 closed; B24 declared non-executable with its measurement",
                "Evaluacoes/r5"],
               ["G16", "Stratified κ and the human adjudication instrument", "PASS (instrument issued)",
                "adjudication_packet_blind.csv"],
               ["G17", "Paper, manifest, commit", "PASS (51 artefacts, 22 runs, 65.86 MB)", "manifest_r5.json"],
               ["G18", "Traceability: every number in the manuscript re-derived from an artefact",
                "PASS, 177 checks", "paper_docx_number_trace_v14.json"],
               ["G19", "Sensitivity of κ to the priors of the rubric", "PASS, 11 variants, κ 0.2974–0.6005",
                "B26_rubric_sensitivity.json"]],
              [0.5, 2.3, 1.5, 1.9]),
        ),
    ])
    section(doc, "7.1 Invariants and geometry", [
        ("p", "The suite contains 69 tests: I1–I44 plus geometry and grounding tests. New in this "
             "round, I34 tests Proposition 1 over the complete grid of deficits; I35 refuses to load "
             "an incoherent calibration; I36 makes the unspecified oversight regime identical to "
             "v12 and declares the weights of ReviewNeed; I37 proves that λ(E) is the identity when "
             "s = 0; I38 orders the stakes by regime; I39 proves that adequacy with ζ = 0 differs "
             "from v12 by exactly ζ times Ψ; and I44 validates the coverage gate as a parameter. The "
             "lattice census computed from the code is 15 slots, 108 incidences and structural "
             "weights summing to 1.0000000000, with the derived marginal uniform at 1/6 for the "
             "canonical β."),
        ("p", "The value of the suite lies in what it rules out, not in the number of tests. I35 "
             "makes an incoherent calibration impossible to load; I38 turns the ordering of the "
             "stakes into a property of the model instead of a hope about the parameters; I44 makes "
             "the coverage gate visible and adjustable by the auditor. The fifteen slots of the "
             "lattice, their weights and their incidences are computed from the code, so a "
             "reviewer can re-derive the geometry rather than take it from the paper."),
    ])
    section(doc, "7.2 Adversarial probes", [
        ("p", "2,064 adversarial probes and 7,815 assertions were re-executed against the v13 core "
             "with a pass rate of 1.000: no monotonicity violation, no breach of non-compensation, "
             "no guard bypass, and no probe in which the score overrode a hard veto. The set "
             "includes the case that exposed the compensation hole in v12 — C3 = 0 while a high "
             "level in another duty lifted the C pillar above the duty floor — which now produces a "
             "recorded guard failure and a material gap."),
        ("p", "A pass rate of 1.000 does not show that the model is right. It shows that no input "
             "designed to break it succeeded in breaking the promises the arithmetic makes about "
             "itself. The practical consequence is narrow and usable: the hole found in v12, where "
             "a strong level in one duty covered a failing duty in another, now leaves an event "
             "that an audit can cite instead of a score to interpret."),
    ])
    section(doc, "7.3 Which mechanisms actually change agreement", [
        ("p", "Each mechanism was implemented, enabled across its canonical range and measured on "
             "130,680 pairs of the corpus (1,080 cases × 120 profiles) against the consensus, with "
             "bootstrap confidence intervals on the difference."),
        ("t", ("Table 7. Effect of the v13 mechanisms on κ against the panels (130,680 pairs, "
               "frozen r3 ladder).",
              ["Variant", "κ", "Δ against the baseline [95% CI]", "Mean adequacy", "Verdicts P / R / A / AWG"],
              [list(r) for r in MECHANISMS], [2.3, 0.7, 2.2, 1.0, 1.8]),
        ),
        ("p", "Only oversight inferred from facts and the differentiated β improve agreement, and "
             "both effects are significant. Salience and cross-pillar exposure do not: κ falls as "
             "they are activated. Both remain available in the core and inert by default, with the "
             "numbers published. In the sensitivity analysis of Sec. 7.6 they saturate the "
             "total-order index because they act through the decision thresholds: they move outputs "
             "without moving agreement."),
        ("p", "The gains have a mechanism an auditor can name. A reviewed case is treated "
             "differently from an unreviewed one, and duties that were indistinguishable become "
             "distinguishable. Salience and exposure move outputs without moving the judgment, so "
             "they remain diagnostics: a governance team may inspect them, but the verdict does not "
             "depend on them. A mechanism is adopted here only when its effect is measured, signed "
             "and significant."),
    ])
    section(doc, "7.4 Ablation of the canon", [
        ("p", "Removing the twelve hard guards drops κ from 0.4633 to 0.1399 (Δ −0.3234, CI "
             "−0.3306 to −0.3147): the guards are not decoration, they are non-compensation. "
             "Collapsing every duty to its primary pillar, which removes the cross-pillar "
             "structure, drops κ to 0.2691 (Δ −0.1942). Removing a single guard changes κ by at "
             "most 0.0042 in either direction."),
        ("t", ("Table 8. Ablation (48,400 pairs, 400 cases × 120 profiles).",
              ["Ablation", "κ", "Δ"],
              [list(r) for r in ABLATION], [3.4, 0.8, 1.1]),
        ),
        ("p", "The normative weight of the model sits where the design placed it. Taking the twelve "
             "guards away costs 69.8% of the agreement with the panels, so the guard floors are not "
             "a stylistic choice but the mechanism that produces the behaviour the panels reward. "
             "The small individual deltas carry the opposite instruction: no guard can be defended "
             "one at a time, so the canon must be defended as a whole. For an organisation using the "
             "model, that means the floors cannot be negotiated duty by duty without destroying the "
             "property for which the model is used."),
    ])
    section(doc, "7.5 Fact grounding", [
        ("p", "Of 43,210 pairs examined, 42,464 (98.27%) contained at least one fact contradicting "
             "a reported level. The rule applied 224,097 caps, with a mean excess over the cap of "
             "0.3611. Grounding changed the verdict of 18,898 pairs (43.74%), of which 15,153 moved "
             "from review to prohibition. κ against the panels rises from 0.2463 without grounding "
             "to 0.5526 with it. The mechanism is therefore mandatory, and its strength s is "
             "explicit: at s = 0 the core behaves as v11."),
        ("p", "Reporting a level is not the same as delivering it. Nearly every profile states a "
             "level that the facts of the case contradict, and correcting it changes almost half of "
             "the verdicts. The difference is not a tuning effect: it is the distance between "
             "judging what an agent claims and judging what an agent can show. A record built on "
             "reported levels alone overstates agency."),
    ])
    section(doc, "7.6 Sensitivity of the parameters", [
        ("p", "Morris elementary effects, a first-order screening that varies one parameter at a "
             "time and records the resulting change in the output (200 trajectories; Morris, 1991), "
             "and a paired Sobol design (Sobol, 2001; Saltelli et al., 2008) with N = 1,024 over the "
             "12-dimensional calibration space were run on a panel of 12 cases covering the 13 "
             "domains and the five verdicts. Because the outputs are step functions at the decision "
             "boundaries, the total-order indices saturate near 1, and the quantities worth "
             "reporting are the first-order indices and the Morris means."),
        ("t", ("Table 9. First-order Sobol index S₁ for selected parameters and outputs.",
              ["Parameter", "S₁ on mean adequacy", "S₁ on abstention", "S₁ on residual risk",
               "S₁ on review need", "S₁ on permissiveness"],
              [list(r) for r in SOBOL], [1.8, 1.1, 1.0, 1.1, 1.1, 1.4]),
        ),
        ("p", "The coverage gate is the dominant control (S₁ = 0.749 on adequacy, 1.0 on "
             "abstention), which is why it moved from an implicit constant to a declared parameter. "
             "γ is the largest structural coefficient (0.123). Oversight attenuation has no effect "
             "on adequacy, since the verdicts are saturated, but it dominates the hard veto "
             "(S₁ = 0.701). The coefficients set to zero are inert at the value declared, not inert "
             "in principle: Morris μ is 0.0004 for salience under the canonical setting while its "
             "total order is 0.9998."),
        ("p", "Two parameters govern the model, and both belong in the audit record rather than in "
             "a code default: the coverage gate decides when the model is allowed to speak at all, "
             "and the structural penalty decides how much a deficit weighs. Everything else is "
             "comparatively flat, including coefficients that earlier rounds spent effort "
             "calibrating. For an organisation deploying the model this is a governance finding "
             "rather than a numerical detail: the settings with the largest influence define the "
             "reach of the judgment, so they must be declared, versioned and reviewed."),
    ])
    section(doc, "7.7 The arithmetic mirror", [
        ("p", "The mirror recomputes all 220,400 confrontations of corpus v7 from the persona "
             "factors, jitter, the requirements of the case, the subset of duties declared and the "
             "observational caps, and compares each quantity with the value stored in the corpus. "
             "The maximum absolute difference is 0.0 for S₂, S₃, S₄, raw adequacy, the band bounds, "
             "the bar, the stakes, residual risk, the structural terms, the epistemic penalty, the "
             "material gap and the veto set; there are no verdict divergences, and the recomputed "
             "distribution is identical to the stored one. Runtime: 121.9 s."),
        ("p", "The mirror closes the distance between the paper and the implementation: a reviewer "
             "who reads only the graph reaches the same verdict as the code, quantity by quantity. "
             "It also carries a warning that generalises. Feeding the mirror the stored, rounded "
             "levels produced differences of up to 1.7 × 10⁻² that crossed guard floors; the "
             "divergence disappeared only when the mirror rebuilt the unrounded levels before "
             "calling the core. Storage precision is part of verification, not a detail of it.",
        ),
    ])
    section(doc, "7.8 Noise, hysteresis and structural ablation", [
        ("p", "Injecting noise into the observed levels raises the verdict flip rate from 1.32% at "
             "σ = 0.02 to 8.56% at σ = 0.2, and the shifts are asymmetric: degraded observations "
             "make the model more restrictive about twenty times as often as they make it more "
             "permissive (0.0815 against 0.0041 at σ = 0.2). Over an eight-step trajectory of "
             "20,436 tracked cases there were 7,461 verdict changes, 103 of them oscillations, and "
             "the hysteresis blocked 6,382 loosening transitions. Removing the structural terms "
             "changes κ by 0.0007 relative to the full model on 183,920 pairs."),
        ("p", "The asymmetry is the finding. When observations degrade, the model becomes more "
             "restrictive far more often than it becomes more permissive: noise pushes the verdict "
             "toward caution rather than permission. The hysteresis blocks 6,382 loosening "
             "transitions, so a profile does not oscillate across a decision boundary. The "
             "near-zero effect of the structural terms is a negative result, reported as such: the "
             "tetrahedron organises the record, it does not produce the judgment."),
    ])
    section(doc, "7.9 Risk, agency and transfer", [
        ("p", "The variance of residual risk over 183,920 pairs decomposes as 98.07% to the case, "
             "0.80% to the profile and 1.13% to their interaction: risk belongs to the duties and "
             "the context, not to the agent. Still, 15.46% of cases change verdict across the 121 "
             "profiles confronting the same case, and 225 cases can be rescued by a better agency. "
             "Risk is structural; admissibility is agential."),
        ("p", "In the delegation battery only one of the 33 duties, pure capability, can be carried "
             "by a model or a tool alone; 96.97% of the canon requires an accountability layer. "
             "Choosing the best available delegate changes no verdict, while the worst changes 127, "
             "with pillar C as the bottleneck in 905 of them."),
        ("p", "Transfer is measured rather than assumed. Fitting the ladder on nine domains and "
             "testing on the four never used — transport, research, digital security and labour — "
             "plus the 320 narrative cases gives κ of 0.4834 on the holdout against 0.4618 in "
             "sample, a gap of −0.0215: the model generalises slightly better outside the training "
             "domains, which indicates that the fit is not memorising domain-specific patterns. "
             "Against simple comparators the model beats a threshold on adequacy without the veto "
             "(0.1464), a majority-class classifier (0.0000) and an uncalibrated ladder (0.2025).",
        ),
        ("p", "The anchor battery, which would ask a local language model to produce the profile "
             "that the arithmetic infers, could not be executed on this machine: the attempt left an "
             "empty output file and a logged run of zero records. It is declared non-executable "
             "together with the measurement of the attempt, not replaced by a zero."),
        ("p", "Two practical consequences follow. Risk belongs to the case, so improving the agent "
             "does not reduce it by itself. Admissibility belongs to the delegation, and the small "
             "number of cases a better agency could rescue marks where the leverage lies. A "
             "deployment that promises lower risk by investing in the agent makes a claim this "
             "instrument can measure and reject."),
    ])
    section(doc, "7.10 Agreement is a property of the instrument", [
        ("p", "κ depends on the priors of the rubric. Moving the duty floors by 10% changes κ from "
             "0.5336 to 0.5507 or 0.5250; reducing the set of categorical duties to three gives "
             "0.5085; using a single lens gives 0.5223, 0.3324 or 0.5147; moving the coverage gate to "
             "0.80 gives 0.6005 and to 0.60 gives 0.4907; treating an undeclared duty as a violation "
             "gives 0.2974. The variant that exceeds 0.60 does so by increasing shared abstention, "
             "not by producing a better judgment. κ that rises because both sides fall silent is not "
             "an improvement."),
        ("t", ("Table 10. κ against the rubric under eleven defensible priors (220,400 pairs).",
              ["Prior variant", "κ", "Δ"],
              [list(r) for r in RUBRIC], [2.6, 0.8, 0.9]),
        ),
        ("f", (FIG + "/fig4_strata.png",
               "Figure 5. κ by consensus stratum and κ under the priors of the normative rubric.")),
        ("p", "κ is reported by stratum because the aggregate hides the structure: 0.8167 where the "
             "three lenses agree (112,179 pairs), 0.1371 where they differ by one step (95,611) and "
             "0.0526 where they differ by more (12,610). By coverage: 0.3832 for fully declared "
             "profiles and 0.3293 for partial ones, where the model and the rubric both abstain. By "
             "domain, agreement runs from 0.6110 in transport and 0.6103 in education down to 0.4624 "
             "in finance, with health at 0.4791 and telecommunications at 0.4790. The spread across "
             "domains is 0.15, smaller than the spread produced by changing the rubric itself, which "
             "is why the instrument rather than the domain is the dominant source of disagreement.",
        ),
        ("f", (FIG + "/fig5_domains.png", "Figure 6. κ per domain in the corpus (13 domains).")),
        ("f", (FIG + "/fig6_verdicts.png",
               "Figure 7. Verdict distribution over the 220,400 case–profile pairs, with the two "
               "abstention classes: 18,240 pairs abstain for lack of coverage and 16,375 for "
               "epistemic underdetermination.")),
        ("p", "κ = 0.5336 is not a measure of the quality of the model. It is the overlap between "
             "the model and one normative instrument. The claim that can be defended is qualified: "
             "the model agrees with the instruments where the instruments agree with each other, and "
             "outside that region the disagreement is documented rather than resolved. Where both "
             "the model and the rubric abstain, the agreement of 1.000 records shared silence, not "
             "shared judgment."),
    ])

    # ---------------------------------------------------------------- 8
    section(doc, "8. Discussion", [
        ("p", "A formal model earns authority by being testable against itself. The geometry is a "
             "theorem, the parameters are explicit and the ontology reproduces the arithmetic to "
             "machine precision. The mirror is the strongest result of the round because it removes "
             "the most common failure of this class of work: a paper whose numbers do not match its "
             "code. The trace fields — deficits, material gap, residual risk, review need, regime — "
             "are what make the claim reviewable (Miller, 2019; Williams et al., 2022)."),
        ("p", "Pluralism is measured rather than declared. Three lenses anchored in named "
             "instruments disagree with one another, and the model is evaluated against their "
             "consensus. Reporting κ by stratum is the honest way to do this: the model can defend "
             "0.8167 where the instruments converge, and on the contested cases the divergence "
             "belongs to the lenses rather than to the arithmetic. The abstention classes make that "
             "visible: 18,240 pairs abstain because the profile does not declare enough duties and "
             "16,375 because the case is epistemically underdetermined."),
        ("p", "The veto is where the model has the most consequence. Ninety per cent of cases "
             "trigger a veto and 13.45% a hard one, and the adequacy score does not override them. "
             "The round also records the opposite decision: a cross-pillar term that reduces "
             "agreement is not a defect to hide but a hypothesis falsified with numbers, and it "
             "survives as a diagnostic in the graph where governance can use it without the verdict "
             "depending on it."),
    ])

    section(doc, "9. Limitations", [("b", LIMITS)])

    section(doc, "10. Reproducibility", [
        ("p", "Each claim can be traced. _analysis/formal_core holds the core and its invariant "
             "tests; _analysis/corpus the generators of the corpus and the rubric; _analysis/ontology "
             "the generator and validator of the RDF; Evaluacoes/r5 the artefacts. manifest_r5.json "
             "lists 51 artefacts, 22 executions with their runtimes, the SHA-256 of each file and "
             "the git revision of the tree. Reproducing the paper requires five commands: the "
             "invariant suite through pytest (45 s), the corpus generator, the battery runner, which "
             "writes the manifest, the ontology generator and validator (301.9 s), and the corpus "
             "mirror (121.9 s). Rounds r2 and r3 are frozen and never overwritten; new results enter "
             "as deltas."),
        ("p", "A checker, _analysis/analysis/docx_number_trace_v14.py, reads the manuscript and "
             "re-derives 177 headline figures from the artefacts of rounds r5 and r4. It also "
             "sweeps every number printed in the body of the text and confirms that it appears in an "
             "artefact."),
    ])

    section(doc, "11. Future work", [
        ("b", [
            "Run the adjudication packet with a panel of domain reviewers and report κ with "
            "confidence intervals, using the sample power already computed.",
            "Derive the coverage gate from observed abstention instead of declaring it, and test it "
            "across domains.",
            "Instrument oversight with more facts — who reviews, with what authority, on what time "
            "scale — instead of two booleans.",
            "Run the language-model anchor on a machine capable of it, to test whether a model can "
            "produce the profile the arithmetic infers.",
            "Extend the ontology with PROV chains so that every verdict carries the version of the "
            "core that produced it.",
            "Test the mirror against a second, independently written implementation of the core, to "
            "separate the test from the code.",
        ]),
    ])

    section(doc, "12. Conclusion", [
        ("p", "ETH-WCMK v14 is a model whose geometry is proved, whose parameters are declared, "
             "whose mechanisms are measured before they are enabled and whose semantic layer "
             "reproduces its arithmetic to 1.61 × 10⁻¹². Its verdicts arrive with a trace readable "
             "in RDF, and its agreement with the normative reference — 0.5336 overall, 0.8167 on "
             "unanimous cases — is limited more by the instrument that produces that reference than "
             "by the model. The contribution of this round is methodological as much as "
             "architectural: it shows how a model of machine ethics can be audited against its own "
             "numbers and what remains genuinely open."),
    ])

    section(doc, "Declarations", [
        ("p", "Data and code availability. Every figure quoted here is produced by code in the "
             "repository and by artefacts stored with it. The formal core, the generators of the "
             "corpus and the rubric, the ontology generator and its validator, the batteries and the "
             "invariant tests are under the MIT licence; the model texts, the ontologies and the "
             "facet registry are under CC BY-SA 4.0. Each round is registered in a manifest — "
             "manifest_r5.json for this one — listing 51 artefacts with their SHA-256 hash, size, "
             "runtime and the git revision of the tree (revisions 97ddab3, e38544a and a99a708). "
             "Rounds r2 and r3 are frozen, so a new revision writes a new round directory and the "
             "numbers remain re-derivable rather than merely reported. The corpus is generated from "
             "declared parameters, so the 220,400 case–profile pairs can be rebuilt and do not have "
             "to be distributed as a dataset. The blind adjudication packet, 120 cases and 360 "
             "cells, is included for the human panel."),
        ("p", "Author contributions. L. M. M. Palazzo: conceptualisation, formal modelling, "
             "implementation of the core, ontology engineering, execution of the batteries and "
             "writing. T. Vanzin: review of the formal layer, validation of the semantic layer and "
             "editorial revision. Both authors read and approved the final text."),
        ("p", "Competing interests. The authors declare no competing interests."),
        ("p", "Funding. The work was developed with internal resources of the Postgraduate Program "
             "in Engineering and Knowledge Management (PPGEGC) at the Federal University of Santa "
             "Catarina. No external funder participated, and no funder influenced the choice of "
             "mechanisms, the rejection of any parameter value or the reporting of negative results.",
        ),
        ("p", "Ethics. The cases are synthetic and contain no personal or sensitive data. The "
             "instruments cited — the UDHR, the CRC, the GDPR, the AI Act, the Belmont and Helsinki "
             "declarations, the ILO declaration, ISO and NIST documents — are used as sources of "
             "duties. Nothing here is legal advice, and no body named here endorses the model.",
        ),
        ("p", "Use of artificial intelligence. Language-model tools assisted with drafting, "
             "organisation of sections and editorial revision. Every number quoted comes from an "
             "artefact listed in Appendix A and is re-derived by the consistency checker; the "
             "arithmetic is not model-generated. The authors are responsible for the content and "
             "for the claims verified against the artefacts."),
        ("p", "Open-science status. Code, data definitions, evaluation artefacts, the ontology and "
             "the equations are distributed with the manuscript under the licences stated above. The "
             "deposit will be announced in this repository and on arXiv once the identifiers exist.",
        ),
    ])

    section(doc, "References", [])
    reference_list(doc, REFS)

    section(doc, "Appendix A. Traceability", [
        ("t", ("Table 11. Figures quoted in the manuscript and the artefacts that support them.",
              ["Figure quoted", "Artefact", "Field"],
              [["220,400 pairs; 1,520 cases; 145 profiles", "Evaluacoes/r5/corpus_v7_coverage.json",
                "pairs_adjudicated, cases.total, personas"],
               ["18,240 coverage abstentions; 16,375 epistemic", "idem", "abstain"],
               ["κ 0.5336; exact agreement 0.7886; within one step 0.9809", "idem",
                "kappa_model_vs_gold, model_vs_gold"],
               ["κ by stratum 0.8167 / 0.1371 / 0.0526", "Evaluacoes/r5/kappa_by_stratum_v13.json", "by_stratum"],
               ["Oversight +0.0078 [0.0057, 0.0100]; β +0.0019 [0.0009, 0.0032]",
                "Evaluacoes/r5/B20_variant_eval_full_corpus.json", "results[].kappa_vs_panel, .ci95"],
               ["Guards −0.3234; primary pillar −0.1942", "Evaluacoes/r5/B21_ablation.json", "results"],
               ["Grounding 98.27%, 224,097 caps, 18,898 flips, κ 0.5526 vs 0.2463",
                "Evaluacoes/r5/B22_fact_contradiction.json", "all named fields"],
               ["S₁ coverage gate 0.749; hard veto 0.701", "Evaluacoes/r5/B23_sobol_v13.json", "sobol, morris"],
               ["Mirror 220,400, maximum difference 0.0, 0 divergences, 121.87 s",
                "Evaluacoes/r5/mirror_full_corpus_v13.json",
                "confrontations, global_max_abs_difference, runtime_seconds"],
               ["2,064 probes, 7,815 assertions, 1.000", "Evaluacoes/r5/B8_probes_reverified_v13.json", "summary"],
               ["Rubric κ range 0.2974–0.6005", "Evaluacoes/r5/B26_rubric_sensitivity.json", "variants[].kappa"],
               ["1,927,780 triples; 50,160 requirements; 169,950 observations; 21,280 groundings; 16,475 guard failures",
                "Ontologias/ontology_v4_2/generation_report.json", "instances_triples, counts"],
               ["42/42 checks; SHACL 0 violations; 76/76 fixtures; mirror 1.61 × 10⁻¹²; 301.9 s",
                "Evaluacoes/r5/ontology_v4_2_validation.json",
                "gate_verdict, shacl, invalid_fixtures, mirror, sparql_checks"],
               ["69 invariant tests, 45.75 s", "_analysis/formal_core/tests", "pytest output"],
               ["34 rules; panel κ 0.6447 / 0.3533 / 0.3153", "Evaluacoes/r5/corpus_v7_coverage.json",
                "gold.rules, gold.panel_kappa"]],
              [2.4, 2.1, 1.9]),
        ),
    ])

    section(doc, "Notation and Terminology", [
        ("p", "Symbols and expressions are listed in the order in which they appear in the text.",
        ),
        ("t", ("Table 12. Notation and terminology used in this manuscript.",
              ["Expression", "Meaning", "Defined in"], NOTATION, [1.5, 3.8, 0.9]),
        ),
    ])

    set_document_properties(
        doc,
        "ETH-WCMK v14: a formally verified core and a SHACL-valid ontology for auditing delegated ethical agency",
        "Luiz Palazzo and Tarcisio Vanzin",
        "Machine ethics; formal verification; RDF/SHACL ontology; sensitivity analysis; delegated ethical agency",
        "machine ethics; formal core; ontology; SHACL; Sobol; kappa; reproducibility",
    )
    add_running_footer(doc, "ETH-WCMK v14 — Palazzo & Vanzin — preprint")
    doc.save(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
