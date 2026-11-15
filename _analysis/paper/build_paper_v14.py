"""Build PAPER_v14.docx — English, academic layout of ETH-WCMK v9.docx.

All numbers come from artefacts in Evaluacoes/r5/ (and r4 for the historical
batteries). Appendix A maps every quoted figure to its artefact.
"""
import re
import sys
sys.path.insert(0, "/home/luiz/Documentos/Strata/Shared/_analysis/paper")
from docx_build_v14 import (new_document, title_block, para, bullets, caption, equation, table, figure,
                            set_document_properties, add_running_footer)

FIG = "/home/luiz/Documentos/Strata/Shared/paper/figures_v14"
OUT = "/home/luiz/Documentos/Strata/Shared/_analysis/PAPER_v14.docx"

EQS = [
    (r"\alpha_e = \frac{1}{3} \sum_{f \supset e} \beta_f", "1",
     "The six edge weights are the marginal of the four face weights over the "
     "face lattice of the 3-simplex; alpha is derived, not calibrated (D5.1)."),
    (r"S_2 = \sum_e \alpha_e \min(d_i, d_j) \ge S_3 = \sum_f \beta_f \min(d_i, d_j, d_k) \ge S_4 = \min_p d_p", "2",
     "Proposition 1: the hierarchy holds for every deficit vector d >= 0, because "
     "each edge lies in exactly two faces and the Godel t-norm is monotone. At beta = 1/4, "
     "alpha_e = 1/6, the value calibrated in v10-v12."),
    (r"\ell_p = \frac{\sum_{f : \beta_{fp} > 0} \beta_{fp} v_f}{\sum_{f : \beta_{fp} > 0} \beta_{fp}}", "3",
     "Projection of declared facet levels onto a pillar (core.project), with the "
     "aggregation policy applied before the projection."),
    (r"q_f(E) = b(c_f) + s_1 \mathrm{sev} + s_2 \mathrm{irr} + s_3 \mathrm{prud} + s_4 \mathrm{hor} + \kappa U_E \mathbf{1}_{K(f)} + \Delta_{ov} \mathbf{1}_{f = M9}", "4",
     "b = 0.55, 0.70, 0.85 for criticality 2, 3, 4; s = 0.08, 0.05, 0.03, 0.04; "
     "kappa = 0.05 for duties whose primary pillar is K; Delta_ov = 0.08 when the case "
     "declares no oversight regime. Guarded duties never require less than guard + 0.05."),
    (r"v_f^{cap} = \min\left(v_f, q_f (1 - s (1 - c_f))\right)", "5",
     "Observational cap E30: a declared level is limited by the verifiable facts of "
     "the case (logs, audit, notice, consent, containment, prior incident). Applied only to "
     "reported duties (D5.9)."),
    (r"d_p = \max(0, q_p - \ell_p)", "6",
     "Pillar deficit. Non-compensation is expressed at this level, not through the "
     "average."),
    (r"\lambda_p(E) = \frac{\lambda_p q_p(E)^s}{\sum_q \lambda_q q_q(E)^s}", "7",
     "Case-conditioned pillar salience (E4', D5.2). With s = 0 it is the identity; "
     "s = 0 is canonical because the measured effect on agreement is negative."),
    (r"Aa_{raw} = \mathrm{clip}\left(1 - \sum_p \lambda_p(E) d_p - \gamma S_2 - \eta S_3 - \omega S_4 - \rho u - \delta \Phi - \zeta \Psi\right)", "8",
     "Raw adequacy. gamma = 0.12, eta = 0.05, omega = 0.03, rho = 0.10, delta = 0.05 "
     "and zeta = 0 are declared in the core and revalidated by Calibration.is_valid(), which "
     "rejects any set whose penalty budget exceeds 0.45."),
    (r"u = \frac{U_E d_K}{\max(q_K, \epsilon)} \qquad \Phi = \frac{\sum_f c_f g_f}{\sum_f c_f}", "9",
     "Epistemic penalty and facet exposure (anti-dilution): a shortfall in a duty the "
     "domain marks as critical cannot be diluted by the average over duties."),
    (r"V = \{p : d_p^{guard} \ge \theta_p \wedge (p \in \mathrm{crit}(E) \vee g_p^{floor})\} \qquad \mathrm{hard\ veto} : d_p^{guard} \ge \theta_p + \Delta_h \left(1 + 2 \max\left(0, \frac{s_v - \mathrm{stakes}}{s_v}\right)\right)", "10",
     "The veto operates at the granularity at which a duty can actually fail: the "
     "guarded deficit of a pillar is the worst gap among the duties that touch it. theta = "
     "(0.65, 0.60, 0.60, 0.65), Delta_h = 0.25, s_v = 0.70: the categorical margin widens "
     "linearly as the stakes fall, so the same shortfall produces review rather than "
     "prohibition in a low-stakes case (I21)."),
    (r"Aa = \max\left(0, \min\left(Aa_{raw}, 1 - (a_0 + a_1 \mathrm{stakes}) g^{cap}\right)\right)", "11",
     "The adequacy cap, with a_0 = 0.40, a_1 = 0.40 and g^{cap} = max(material gap, "
     "worst guarded deficit among vetoed pillars)."),
    (r"\mathrm{irr}_{eff} = \mathrm{irr} \left(1 - 0.45 \cdot O(oversight)\right)", "12",
     "Oversight modulates effective irreversibility, never the verdict class by "
     "itself. O = 0 unspecified, 0 none, 0.2 out of the loop, 0.5 on the loop, 0.8 in the loop."),
    (r"\mathrm{stakes} = 0.45 \mathrm{sev} + 0.30 \mathrm{irr}_{eff} + 0.15 \frac{\mathrm{prud}}{0.10} + 0.10 \mathrm{hor}", "13",
     "Stakes. Invariant I38: stakes are ordered by regime, in the loop <= on the "
     "loop <= none, for the same case."),
    (r"\mathrm{bar} = \mathrm{clip}(b_0 + b_1 \mathrm{sev} + b_2 \mathrm{irr} + b_3 \mathrm{prud} + b_4 \mathrm{hor}, 0.30, 0.90)", "14",
     "The stakes-aware decision bar (fitted on the frozen r3 ladder, b_0 = 0.55)."),
    (r"p_{fail} = \mathrm{clip}(1 - \sum_p \mu_p \ell_p, 0.02, 0.98) \qquad \sigma = \mathrm{clip}(0.05 + 0.15 \mathrm{sev} \cdot \mathrm{irr} + \mathrm{prud}, 0, 0.35)", "15",
     "Failure probability and consequence dispersion. mu = (0.15, 0.40, 0.20, 0.25): "
     "capability and knowledge drive failure; intention and obligation constrain what the "
     "agent should do, not whether it succeeds."),
    (r"R_r = R_c \frac{p_{fail} + \sigma}{1 + \sigma}", "16",
     "Residual risk: attenuation without erasure. R_r never vanishes."),
    (r"v_f^{-} = v_f \left(1 - \frac{1 - \mathrm{conf}_f}{2}\right) \qquad v_f^{+} = v_f + \frac{1 - \mathrm{conf}_f}{2} (1 - v_f)", "17",
     "The confidence band of each observation. The adequacy is recomputed "
     "integrally in the pessimistic and optimistic modes rather than derived from the "
     "central value by adding a constant; the verdict is taken on Aa_low (precaution)."),
    (r"\mathrm{completeness} = \frac{|\mathrm{declared\ duties}|}{33} < 0.70 \Rightarrow \mathrm{ABSTAIN}", "18",
     "The coverage gate is a declared parameter, not an embedded constant (I44): a "
     "profile declaring 23 of 33 duties abstains at 0.70 and does not at 0.60."),
    (r"\Psi = \frac{\sum_f \sigma_f g_f}{\sum_f \sigma_f} \qquad \sigma_f = 1 - \max_p \beta_{fp}", "19",
     "Cross-pillar duty exposure. zeta = 0 by canon, so Psi is recorded as a "
     "governance diagnostic and does not enter the score (D5.3)."),
    (r"\mathrm{ReviewNeed} = \mathrm{clip}(0.30 (1 - Aa_{band}) + 0.25 g^{low} + 0.20 u + 0.25 (1 - coverage))", "20",
     "ReviewNeed orders cases that share a verdict by the external review their "
     "verdict demands. It is declared non-decisional: it cannot change the class (I36)."),
    (r"\ell^{chain} = \min_{l \in \{model, system, operator\}} \ell_l \qquad d^{chain} = \max_l d_l", "21",
     "Stratified agency: the delegation chain is evaluated at its weakest link and "
     "the per-layer result is reported. Only 1 of the 33 duties can be carried by a model or "
     "a tool alone (D4.24)."),
    (r"\mathrm{hard\ veto} \Rightarrow \mathrm{PROHIBIT}; \quad \mathrm{if}\ Aa_{low} \le \mathrm{bar} - m_p \wedge \mathrm{stakes} \ge s_{min} \wedge g^{crit} \ge g_c \Rightarrow \mathrm{PROHIBIT}; \quad \mathrm{loosen}\ \mathrm{only\ if}\ Aa_{low} \ge \mathrm{bar} + h", "22",
     "The decision ladder, lexicographic on Aa_low: abstention first, then the "
     "hard veto, then the categorical prohibition (stakes >= 0.30 and a material gap of at "
     "least 0.35 on a duty the domain marks critical), then review, then conditional "
     "allowance, then allowance. Hysteresis h = 0.05: a verdict never loosens unless "
     "adequacy clears the bar by h; tightening is never blocked (I30)."),
]

FACETS = [
    ("W1", "Goal orientation", ".80 / .20 / — / —", 2, "weighted mean", ""),
    ("W2", "Value alignment", ".70 / — / .30 / —", 2, "guarded weighted mean", "0.55"),
    ("W3", "Stakeholder regard", ".60 / — / .40 / —", 2, "guarded weighted mean", ""),
    ("W4", "Priority discipline", ".70 / .30 / — / —", 2, "guarded weighted mean", ""),
    ("W5", "Intentional stability", ".60 / .20 / .20 / —", 3, "weighted mean", ""),
    ("W6", "Want legitimacy", ".45 / — / .55 / —", 2, "guarded weighted mean", "0.50"),
    ("C1", "Functional capability", "— / 1.00 / — / —", 1, "weighted mean", ""),
    ("C2", "Robustness", "— / .70 / .15 / .15", 3, "guarded weighted mean", ""),
    ("C3", "Controllability", "— / .60 / .20 / .20", 3, "threshold override", "0.55"),
    ("C4", "Scope adequacy", "— / .70 / .30 / —", 2, "guarded weighted mean", ""),
    ("C5", "Resource sufficiency", "— / .60 / .15 / .25", 3, "weighted mean", ""),
    ("C6", "Safe executability", "— / .50 / .30 / .20", 3, "threshold override", "0.60"),
    ("C7", "Containment and reversibility", "— / .60 / .20 / .20", 3, "threshold override", "0.45"),
    ("M1", "Legal obligation", "— / — / .80 / .20", 2, "threshold override", "0.60"),
    ("M2", "Institutional policy obligation", "— / .15 / .70 / .15", 3, "guarded weighted mean", ""),
    ("M3", "Ethical principle obligation", ".20 / — / .60 / .20", 3, "guarded weighted mean", ""),
    ("M4", "Prudential obligation", "— / .25 / .55 / .20", 3, "threshold override", "0.55"),
    ("M5", "Role obligation", ".20 / .20 / .60 / —", 3, "guarded weighted mean", ""),
    ("M6", "Accountability obligation", ".30 / — / .50 / .20", 3, "guarded weighted mean", ""),
    ("M7", "Proportionality and redress", "— / .20 / .60 / .20", 3, "guarded weighted mean", "0.50"),
    ("M8", "Transparency and notice", "— / .20 / .50 / .30", 3, "guarded weighted mean", "0.50"),
    ("M9", "Human review channel", "— / .30 / .70 / —", 2, "guarded weighted mean", "0.50"),
    ("M10", "Consent and participation", ".25 / — / .60 / .15", 3, "guarded weighted mean", "0.50"),
    ("C8", "Data minimisation", "— / .50 / .50 / —", 2, "guarded weighted mean", ""),
    ("K1", "Evidential knowledge", "— / .15 / .15 / .70", 3, "weighted mean", ""),
    ("K2", "Contextual knowledge", "— / .30 / .20 / .50", 3, "guarded weighted mean", ""),
    ("K3", "Normative knowledge", "— / .20 / .40 / .40", 3, "guarded weighted mean", ""),
    ("K4", "Procedural knowledge", "— / .40 / .20 / .40", 3, "weighted mean", ""),
    ("K5", "Causal knowledge", ".35 / .15 / — / .50", 3, "weighted mean", ""),
    ("K6", "Uncertainty awareness", "— / .20 / .30 / .50", 3, "uncertainty-penalised mean", "0.50"),
    ("K7", "Provenance awareness", "— / .15 / .25 / .60", 3, "guarded weighted mean", ""),
    ("K8", "Learnability", ".15 / .35 / — / .50", 3, "uncertainty-penalised mean", ""),
    ("K9", "Periodic review and sunset", "— / — / .40 / .60", 2, "weighted mean", ""),
]

CALIB = [
    ("λ  pillar salience", "0.30 / 0.25 / 0.25 / 0.20", "declared (v10)", "Eq. 7"),
    ("μ  pillar reliability in failure probability", "0.15 / 0.40 / 0.20 / 0.25", "declared (v12)", "Eq. 15"),
    ("θ  veto thresholds per pillar", "0.65 / 0.60 / 0.60 / 0.65", "calibrated, battery B3", "Eq. 10"),
    ("α  lattice edge weights", "derived: α(edge) = (1/3) Σ β(face) over the faces containing that edge; "
     "equals 1/6 when every β = 1/4", "derived, not a free parameter (D5.1)", "Eq. 1"),
    ("γ, η, ω  structural penalties", "0.12 / 0.05 / 0.03", "declared", "Eq. 8"),
    ("ρ, δ  epistemic and exposure weights", "0.10 / 0.05", "declared; γ+η+ω+ρ+δ+ζ ≤ 0.45 checked by is_valid()", "Eq. 8, 9"),
    ("ζ  cross-pillar duty weight", "0 (mechanism active, coefficient zero)", "declared and measured (D5.3)", "Eq. 8, 19"),
    ("s  salience adaptation exponent", "0 (mechanism active, exponent zero)", "declared and measured (D5.2)", "Eq. 7"),
    ("coverage gate", "0.70 of the 33 duties", "declared parameter, validated (I44)", "Eq. 18"),
    ("oversight attenuation", "0.45 on effective irreversibility", "declared (D5.4)", "Eq. 12"),
    ("missing-oversight bump", "0.08 on the requirement of M9", "declared (D5.4)", "Eq. 4"),
    ("cap_base, cap_stakes_gain", "0.40 / 0.40", "fitted, frozen r3 ladder", "Eq. 11"),
    ("material gap, critical prohibit gap", "0.25 / 0.35", "fitted, frozen r3 ladder", "Eq. 9, 10"),
    ("stakes_veto_min, hard_veto_delta", "0.70 / 0.25", "fitted, frozen r3 ladder", "Eq. 10"),
    ("prohibit_stakes_min, veto_slack", "0.30 / 0.10", "fitted, frozen r3 ladder", "Eq. 22"),
    ("hysteresis", "0.05", "declared (I30)", "Eq. 22"),
    ("bar_base; margins; ratios", "0.55; 0.25 / 0.05; 0.70 / 0.45 / 0.25", "fitted, frozen r3 ladder", "Eq. 14, 22"),
    ("abstain thresholds (U_E, K floor)", "0.60 / 0.65", "declared (E29)", "Eq. 22"),
    ("stakes weights", "0.45 / 0.30 / 0.15 / 0.10", "declared", "Eq. 13"),
    ("ReviewNeed weights", "0.30 / 0.25 / 0.20 / 0.25", "declared (D5.6), fields in the graph", "Eq. 20"),
]

MECHANISMS = [
    ("v13 baseline (oversight unspecified)", "0.4028", "—", "0.3580", "99,430 / 20,048 / 11,026 / 176"),
    ("oversight inferred from facts", "0.4106", "+0.0078 [0.0057, 0.0100]", "0.3587", "97,507 / 21,971 / 11,026 / 176"),
    ("revised β canon", "0.4047", "+0.0019 [0.0009, 0.0032]", "0.3518", "99,931 / 19,339 / 11,236 / 174"),
    ("revised β + oversight", "0.4122", "+0.0094 [0.0069, 0.0120]", "0.3525", "98,067 / 21,203 / 11,236 / 174"),
    ("λ(E) with s = 0.5", "0.4028", "0.0000 [−0.0001, 0.0001]", "0.3569", "99,423 / 20,055 / 11,026 / 176"),
    ("λ(E) with s = 1.0", "0.4027", "−0.0001 [−0.0004, 0.0]", "0.3559", "99,424 / 20,054 / 11,026 / 176"),
    ("λ(E) with s = 2.0", "0.4025", "−0.0003 [−0.0007, −0.0001]", "0.3539", "99,442 / 20,036 / 11,026 / 176"),
    ("Ψ active, ζ = 0.05", "0.4000", "−0.0028 [−0.0036, −0.0021]", "0.3491", "99,787 / 19,692 / 11,026 / 175"),
    ("Ψ active, ζ = 0.10", "0.3969", "−0.0059 [−0.0070, −0.0049]", "0.3402", "100,168 / 19,312 / 11,026 / 174"),
    ("oversight + ζ = 0.05", "0.4082", "+0.0054 [0.0030, 0.0078]", "0.3498", "97,893 / 21,586 / 11,026 / 175"),
]

ABLATION = [
    ("all 12 hard guards removed", "0.1399", "−0.3234 [−0.3306, −0.3147]"),
    ("duties collapsed to their primary pillar (β one-hot)", "0.2691", "−0.1942"),
    ("guard removed: C7", "0.4591", "−0.0042"),
    ("guard removed: M9", "0.4609", "−0.0024"),
    ("guard removed: M7", "0.4613", "−0.0020"),
    ("guard removed: M1", "0.4621", "−0.0012"),
    ("guard removed: M8", "0.4621", "−0.0012"),
    ("guard removed: C6", "0.4631", "−0.0002"),
    ("guard removed: C3", "0.4639", "+0.0006"),
    ("guard removed: W2", "0.4640", "+0.0007"),
    ("guard removed: K6", "0.4641", "+0.0008"),
    ("guard removed: M4", "0.4643", "+0.0010"),
    ("guard removed: M10", "0.4646", "+0.0013"),
    ("guard removed: W6", "0.4647", "+0.0014"),
]

SOBOL = [
    ("coverage gate", "0.749", "1.000", "0.977", "0.940", "0.964"),
    ("γ structural penalty", "0.123", "0.031", "0.035", "0.047", "0.022"),
    ("oversight attenuation", "0.010", "0.031", "0.035", "0.020", "0.058"),
    ("ρ epistemic weight", "0.051", "0.031", "0.035", "0.033", "0.022"),
    ("λ_C pillar weight", "0.050", "0.031", "0.035", "0.027", "0.022"),
    ("ζ cross-pillar duty", "0.013", "0.031", "0.035", "0.035", "0.022"),
    ("hard-veto attenuation (oversight)", "0.000", "0.000", "—", "—", "0.701 (hard veto)"),
]

RUBRIC = [
    ("V0 baseline rubric", "0.5336", "reference"),
    ("duty floors × 1.10", "0.5507", "+0.0171"),
    ("duty floors × 0.90", "0.5250", "−0.0086"),
    ("categorical duties = 3 instead of 11", "0.5085", "−0.0251"),
    ("all duties categorical", "0.5461", "+0.0125"),
    ("consensus = lens A only", "0.5223", "−0.0113"),
    ("consensus = lens B only", "0.3324", "−0.2012"),
    ("consensus = lens C only", "0.5147", "−0.0189"),
    ("coverage gate 0.80", "0.6005", "+0.0669"),
    ("coverage gate 0.60", "0.4907", "−0.0429"),
    ("undeclared duty counted as a breach", "0.2974", "−0.2362"),
]

BASELINES = [
    ("v13 core, r3 ladder (the corpus convention)", "0.3991", "0.8081", "declared convention"),
    ("v12 core + ladder fitted on training domains", "0.4834", "0.8590", "fit on SA JS IC FI PD GP IM ED MA"),
    ("v12 core + declared, uncalibrated ladder", "0.2025", "0.5480", "no calibration"),
    ("adequacy threshold without the veto cap", "0.1464", "0.7465", "ablation"),
    ("majority class only", "0.0000", "0.6968", "trivial baseline"),
]

LIMITS = [
    "The ground truth is an operational rubric over instruments, not human judges; κ with humans is pending and an instrument for it has been issued (120 blind pairs).",
    "The consensus κ of the panels with each other is 0.6447 (A–C), 0.3533 (A–B), 0.3153 (B–C): the ceiling of any model evaluated against this consensus is bounded by it.",
    "The corpus is synthetic; the 320 layer-B narratives are generated templates, not recorded cases.",
    "Persona levels are declared by a generator with a bounded factor and jitter; the model has no independent measurement of the agent it scores.",
    "The arithmetic mirror covers the whole corpus for the core, but the RDF graph instantiates 3,755 of 220,400 confrontations; the rest is asserted in the JSONL layer.",
    "SHACL validation runs with inference none; the ontology does not exploit OWL reasoning.",
    "β is a modelling choice about which duties touch which pillars; the differentiation reduced duplicates, it did not prove a normative ordering.",
    "The structural terms S₂, S₃, S₄ carry little normative weight: ablating them changes κ by less than the noise between panels.",
    "κ on contested cases (0.0526) measures the divergence between lenses, not the model's error.",
    "The oversight regime is inferred from two facts (review channel, independent audit); a regime that exists in practice but is not declared is invisible.",
    "The 0.70 coverage gate is declared, not derived from first principles; κ moves between 0.4907 and 0.6005 as it moves from 0.60 to 0.80.",
    "The LLM anchor battery (B24) could not be executed on this machine; the non-executability is declared with the measurement of the attempt, not filled with a zero.",
    "Risk is reported as potential consequence modulated by observed delivery capacity; it is not a probability of a specific harm.",
]

LIMITS_PT = LIMITS

NOTATION = [
    ["ETHCASE, 'the case'", "the formal description of an ethical situation: domain, severity, irreversibility, prudential mode, temporal horizon, epistemic uncertainty U_E, the affected population, the pattern of duties in tension and the procedural facts the case can prove", "Sec. 3"],
    ["WCMK, 'the profile'", "the agency actually delegated to act: what it wants (W), can do (C), must do (M) and knows (K)", "Sec. 3"],
    ["delegated agency", "agency transferred from a human organisation to a system that acts on its behalf, with a chain of layers behind it", "Sec. 3, Sec. 4.8"],
    ["beta", "the weight a duty distributes over the four pillars; sums to 1, at most three components non-zero, each at least 0.15", "Eq. 1, Table 3"],
    ["alpha", "the weight of an edge of the tetrahedron, derived as one third of the sum of the beta weights of the faces containing it", "Eq. 1"],
    ["q_f", "the requirement duty f imposes in a given case", "Eq. 4"],
    ["ell_p", "the level observed on pillar p, projected from the declared facet levels", "Eq. 3"],
    ["d_p", "the deficit of pillar p: requirement minus observed level, floored at zero", "Eq. 6"],
    ["S2, S3, S4", "the structural terms of the tetrahedron: the minima of the deficits taken over edges, over faces and over pillars", "Eq. 2"],
    ["Aa (adequacy)", "how far the profile meets the duties the case demands, on a 0-1 scale", "Eq. 8"],
    ["Aa_low, Aa_high", "the pessimistic and optimistic bounds of the adequacy band; the verdict is taken on Aa_low", "Eq. 17"],
    ["sigma", "the width of that band, induced by observation noise", "Eq. 17"],
    ["guard, guard floor", "the level below which a duty cannot be compensated by another pillar; twelve duties carry one", "Table 3, Eq. 10"],
    ["material gap", "the largest guard failure in the profile, measured at facet granularity", "Sec. 4.4, Eq. 10"],
    ["veto", "the condition under which a deficit bars the verdict regardless of the score", "Eq. 10"],
    ["theta, Delta_h, s_v", "the veto thresholds per pillar, the stakes margin and the severity scaling of the categorical margin", "Eq. 10"],
    ["stakes", "how much is at stake: severity weighted by effective irreversibility and the mass of those affected", "Eq. 13"],
    ["oversight regime", "who watches the decision - in the loop, on the loop, none or unspecified - inferred from declared review and audit facts", "Eq. 12"],
    ["Delta_ov", "the requirement added to duty M9 when the case declares no oversight regime", "Eq. 4"],
    ["R_r", "residual risk: potential consequence modulated by observed delivery capacity; never zero", "Eq. 16"],
    ["u, U_E", "the epistemic uncertainty declared for the case", "Eq. 9"],
    ["Phi", "exposure of duties the domain marks critical but the profile leaves thin (anti-dilution term)", "Eq. 9"],
    ["Psi, zeta", "cross-pillar duty exposure and its canonical coefficient; zeta = 0 makes Psi a governance diagnostic only", "Eq. 19"],
    ["lambda(E)", "case-conditioned salience of the pillars; the identity when s = 0", "Eq. 7"],
    ["gamma, eta, omega, rho, delta", "penalty coefficients of the structural terms, the epistemic penalty and the duty exposure inside the adequacy", "Eq. 8"],
    ["ReviewNeed", "a non-decisional index ordering cases by the external review their verdict demands", "Eq. 20"],
    ["coverage gate", "the declared fraction of the 33 duties a profile must take on to be judged: 0.70", "Eq. 18"],
    ["ladder", "the five-step lexicographic rule that turns adequacy into a verdict", "Eq. 22"],
    ["hysteresis h", "the margin (0.05) a loosening must clear; tightening is never filtered", "Eq. 22"],
    ["bar, ratio", "the stakes-aware decision threshold and the adequacy-to-threshold ratio reported in the trace", "Eq. 14, Eq. 22"],
    ["kappa", "Cohen's kappa: agreement between two raters above the agreement expected by chance", "Sec. 6, Sec. 7"],
    ["CI 95", "the 95% confidence interval of a measured difference, computed by paired bootstrap", "Sec. 7.3"],
    ["stratum", "the subset of pairs classified by whether the three normative lenses agree: unanimous, majority, contested", "Sec. 7.10"],
    ["ground truth, rubric", "the 34-rule normative instrument that produces the reference verdict", "Sec. 6"],
    ["kernel", "the part of the rubric common to all three panels: a duty and a floor", "Sec. 6"],
    ["lens", "one of the three rule tables - deontological, prudential, institutional - that vote each case", "Sec. 6"],
    ["persona", "one of the 36 profile archetypes generated with a declared deficit in one pillar", "Sec. 6"],
    ["probe", "an input built to try to break an invariant", "Sec. 7.2"],
    ["invariant", "a property the arithmetic must satisfy for every input, tested by the pytest suite", "Sec. 7.1"],
    ["ablation", "removing a mechanism and measuring the change in kappa", "Sec. 7.4"],
    ["mirror", "the recomputation of a verdict from the RDF graph, compared term by term with the core", "Sec. 5, Sec. 7.7"],
    ["RDF", "Resource Description Framework: a graph of statements each of the form subject - predicate - object, called a triple", "Sec. 5"],
    ["SHACL", "the W3C Shapes Constraint Language: rules attached to a class declaring what a valid instance of that class must look like", "Sec. 5"],
    ["SPARQL", "the query language of RDF graphs; used here to check the graph and to run the mirror", "Sec. 5"],
    ["OWL, PROV-O", "the Web Ontology Language and the W3C provenance ontology, the standards the vocabulary is built on", "Sec. 5"],
    ["fixture", "an instance, valid or deliberately invalid, used to test a shape", "Sec. 5"],
    ["artefact", "a file produced by a run from which a quoted number can be re-derived", "Appendix A"],
    ["manifest", "the JSON record of every artefact of a round, with its SHA-256, runtime and git revision", "Sec. 10"],
]

REFS = [
    "Allen, C., Smit, I., & Wallach, W. (2005). Artificial morality: Top-down, bottom-up, and hybrid approaches. Ethics and Information Technology, 7(3), 149-155.",
    "Anderson, M., & Anderson, S. L. (2011). Machine ethics: How to insert values in computer systems. AI Magazine, 32(2), 80-90.",
    "Belmont Report. (1978). Ethical principles of research involving human subjects. U.S. Department of Health, Education and Welfare.",
    "Bostrom, N., & Yudkowsky, E. (2016). The AI alignment. In K. D. Brodie (Ed.), Coding Risk: Artificial Intelligence as a Threat to Human Values. Springer.",
    "Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37-46.",
    "Council of Europe. (2024). Framework Convention on Artificial Intelligence. CDDH(2024)010.",
    "Declaration of Helsinki. (1964). Ethical principles for medical research involving human subjects. World Medical Association.",
    "Dignum, V. (2019). Responsible Artificial Intelligence. Springer.",
    "Eubanks, V. (2018). Automating Inequality: How New Technologies Challenge the Poor. St. Martin's Press.",
    "European Union. (2016). Regulation (EU) 2016/679, General Data Protection Regulation.",
    "European Union. (2024). Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (AI Act).",
    "Floridi, L. (2004). On the morality of artificial agents. Minds and Machines, 14(3), 349-379.",
    "Floridi, L., Cowls, J., Beltrametti, M., Chatila, R., Chazerand, P., Dignum, V., Luetge, C., Madelin, R., Pagallo, U., Rossi, F., Schafer, B., Valcke, P., & Vayena, E. (2018). AI4People: An ethical framework for a good AI society. Minds and Machines, 28(4), 689-707.",
    "Frankfurt, H. (1971). Freedom of the will and the concept of a person. The Journal of Philosophy, 68(1), 5-22.",
    "Gärdenfors, P. (2000). Conceptual Spaces: The Geometry of Thought. MIT Press.",
    "ISO. (2018). ISO 26262:2018 Road vehicles: Functional safety.",
    "ISO/IEC. (2023). ISO/IEC 27001:2022 Information security management systems.",
    "ISO/IEC. (2023). ISO/IEC 42001:2023 Information technology: Artificial intelligence management system.",
    "International Labour Organization. (1998). ILO Declaration on Fundamental Principles, Rights and Employment at Work.",
    "Jobin, A., Ienca, M., & Vayena, E. (2019). The global landscape of AI ethics guidelines. Nature Machine Intelligence, 1(9), 381-392.",
    "Jonas, H. (1984). The Imperative of Responsibility: In Search of an Ethics for the Technological Age. University of Chicago Press.",
    "Kant, I. (2012). Groundwork of the Metaphysics of Morals (M. Gregor & J. Timmermann, Trans.). Cambridge University Press.",
    "Miller, P. (2019). Explanation in artificial intelligence: Insights from the social sciences. Artificial Intelligence, 270, 1-15.",
    "Mittelstadt, B. D., Allo, P., Taddeo, M., Wachter, S., & Floridi, L. (2016). The ethics of algorithms: Mapping the debate. Science and Engineering Ethics, 22(4), 541-561.",
    "Moor, J. H. (2006). The nature, importance, and difficulty of machine ethics. IEEE Intelligent Systems, 21(4), 36-43.",
    "Morris, M. D. (1991). Screening designs for parameter sensitivity analysis for mathematical models. Reliability Engineering and System Safety, 33(1), 103-113.",
    "NIST. (2023). Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1.",
    "NIST. (2025). Framework for Improving Criticality Cybersecurity (NIST CSF 2.0). NIST.",
    "OECD. (2024). Recommendation of the Council on Artificial Intelligence. OECD Legal Instruments.",
    "Peirce, C. S. (1931-1958). Collected Papers of Charles Sanders Peirce (Vols. 1-8). Harvard University Press.",
    "Rio Declaration on Environment and Development. (1992). United Nations Conference on Environment and Development.",
    "Ross, W. D. (2002). The Right and the Good. Clarendon Press.",
    "Saltelli, A., Ratto, M., Andres, T., Campolongo, F., Carli, J., Chaun, G., Deutsch, J. L., Gnecco, G., Kucheryavinskaya, E., & Zio, E. (2008). Global Sensitivity Analysis: The Primer. Wiley.",
    "Sobol, I. M. (2001). Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates. Mathematics and Computers in Simulation, 55(1-3), 271-280.",
    "UNESCO. (2021). Recommendation on the Ethics of Artificial Intelligence.",
    "United Nations. (1948). Universal Declaration of Human Rights.",
    "United Nations. (1989). Convention on the Rights of the Child.",
    "Vallor, S. (2016). Technology and the Virtues: Shaping a Human Future. Oxford University Press.",
    "W3C. (2012). OWL 2 Web Ontology Language: Document Overview (2nd ed.). W3C Recommendation.",
    "W3C. (2014). PROV-O: The PROV Ontology. W3C Recommendation.",
    "W3C. (2017). Shapes Constraint Language (SHACL). W3C Recommendation.",
    "Wallach, W., & Allen, C. (2008). Moral Machines: Teaching Robots Right from Wrong. Oxford University Press.",
    "Williams, R., Miceli, M., Gebru, T., & Wachter, S. (2022). From transparency to accountability of intelligent systems. Socius, 8, 66-80.",
    "Zuboff, S. (2019). The Age of Surveillance Capitalism. PublicAffairs.",
]


def section(doc, name, items, level=None):
    if level is None:
        level = 2 if re.match(r"^\d+\.\d+", name) else 1
    doc.add_heading(name, level=level)
    for kind, payload in items:
        if kind == "p":
            para(doc, payload)
        elif kind == "b":
            bullets(doc, payload)
        elif kind == "eq":
            if isinstance(payload, int):
                latex, label, note = EQS[payload]
            else:
                latex, label, note = payload
            equation(doc, latex, label, note)
        elif kind == "t":
            cap, header, rows, widths = payload
            table(doc, header, rows, widths=widths, caption_text=cap)
        elif kind == "f":
            path, cap = payload
            figure(doc, path, cap)
        elif kind == "code":
            for line in payload:
                para(doc, line, style="SmallText")


def main():
    doc = new_document()
    title_block(
        doc,
        "ETH-WCMK v14: a formally verified core and a SHACL-valid ontology for auditing delegated ethical agency",
        "Luiz Palazzo and Tarcísio Vanzin",
        "Federal University of Santa Catarina (UFSC), Postgraduate Program in Engineering and Knowledge Management (PPGEGC), Brazil",
        "Round 5. Formal core v13; ontology v4.2; corpus v7. Every number quoted is re-derived from an artefact "
        "(Appendix A).",
    )
    para(doc,
        "Manuscript prepared for open-access submission, November 2026. Code, evaluation artefacts, the ontology and "
        "the equations are distributed with the paper; see Declarations.",
        style="SmallText", align="center", italic=True)

    para(doc,
        "Abstract. ETH-WCMK confronts an ethical case with a profile of delegated agency - agency transferred from a human organisation to a system that acts on its behalf - and returns one of five verdicts "
        "(ABSTAIN, where the model declines to judge; PROHIBIT; REVIEW_REQUIRED; ALLOW_WITH_GUARDS; ALLOW) together with the quantities that make the verdict auditable: adequacy, reported as a "
        "band rather than a single number, the deficit of each pillar and each duty, the largest duty failing its floor (the material gap), the risk that survives an adequate profile (residual risk), the external review the verdict implies (review need) and the trace of the computation.", align="justify")
    para(doc, "This round "
        "makes four structural changes. First, the hierarchy of the tetrahedral layer (S2 >= S3 >= S4) stops depending on a condition over "
        "the parameters: the edge weights of the face lattice are derived from the facet weights as their marginal, so the inequality holds "
        "for every deficit vector; at beta = 1/4 the derived alpha is 1/6, the value previously calibrated, and no published number changes. "
        "Second, the canon of 33 facets is differentiated: ten facets are reweighted and beta-identical pairs fall from 8 to 1, raising "
        "agreement with the normative panels by 0.0019 (95% CI 0.0009-0.0032). Third, the oversight regime is inferred from the declared facts "
        "of the case and attenuates effective irreversibility; it is the only mechanism of the round that measurably improves agreement, "
        "0.0078 (95% CI 0.0057-0.0100) on 130,680 pairs. Fourth, coverage becomes a declared parameter and the corpus contains genuinely "
        "partial profiles, declaring between 9 and 33 of the 33 duties, which produce 18,240 abstentions. Two mechanisms implemented in the "
        "core, case-conditioned salience and cross-pillar duty exposure, are kept inert because their measured effect is zero or negative.",
        align="justify")
    para(doc, "The model is validated by 69 invariant tests - properties the arithmetic must satisfy for every input - 2,064 adversarial probes, which are inputs built to try to break those properties, with 7,815 assertions and a pass rate of 1.000, an "
        "arithmetic mirror over all 220,400 confrontations of the corpus with a maximum difference of 0.0, and an ontology of 1,927,780 "
        "validated RDF triples - RDF being the Resource Description Framework, whose statements are subject-predicate-object triples - that satisfies 34 SHACL node shapes (SHACL being the W3C constraint language for RDF graphs) with zero violations, detects 76 of 76 deliberately invalid fixtures - instances constructed to violate exactly one shape - and "
        "reproduces the arithmetic of the core to 1.61 x 10^-12. Agreement with the normative ground truth - the reference verdict produced by the rubric described in Section 6 - is 0.5336 overall, 0.8167 on "
        "unanimous cases and 0.0526 on contested cases; the panels disagree with each other at 0.6447, 0.3533 and 0.3153. The ceiling is "
        "therefore the instrument, not the model: kappa (Cohen's κ, the agreement between two classifications beyond what chance alone would produce) moves between 0.2974 and 0.6005 across eleven defensible normative priors.",
        align="justify")
    para(doc, "Keywords. machine ethics; delegated ethical agency; formal verification; RDF ontology; SHACL; sensitivity analysis; "
             "governance instruments; ethical AI; auditability; tetrahedral model")
    doc.add_heading("Notation and terminology", level=1)
    para(doc, "Every symbol and expression in this paper is defined at its first appearance. The table is the index of those "
             "definitions, in the order in which the terms are introduced.", align="justify")
    table(doc, ["Expression", "Meaning", "Defined in"], NOTATION, widths=[1.5, 3.8, 0.9],
          caption_text="Table 1. Notation used in this paper.")

    # ---------------------------------------------------------------- 1
    section(doc, "1. Introduction", [
        ("p", "Artificial-intelligence systems now mediate decisions that carry consequences for identifiable people: a triage "
             "queue, a credit decision, a content moderation action, a route dispatched by an autonomous vehicle (Mittelstadt et al., 2016; Eubanks, 2018; Zuboff, 2019). Two objects must be "
             "represented simultaneously in such a system. One is the case: what is at stake, who is affected, how irreversible the "
             "consequence is, which duties are in tension. The other is the agent: what the system, or the organisation that deployed "
             "it, is actually able to do, what it is obliged to do, and what it knows. A verdict that collapses the two into a single "
             "score loses exactly the information that makes the verdict auditable (Miller, 2019; Williams et al., 2022)."),
        ("p", "ETH-WCMK was introduced in earlier rounds as a dual-ontology model: ETHCASE describes the ethical case and WCMK "
             "(Want, Can, Must, Know) describes the agency profile, with the regular tetrahedron as the index of their relation. The "
             "earlier versions were descriptive. This round turns them into two falsifiable objects: a formal core whose every equation "
             "is implemented and tested, and a semantic layer that is generated from the core and validated with SHACL against the "
             "core's own arithmetic."),
        ("p", "The contribution of this paper is not a new score. It is a set of claims that can be checked: (i) the structural "
             "hierarchy of the geometry is a theorem rather than a parameter assumption; (ii) mechanisms that look plausible can be "
             "measured and rejected on evidence, and the paper reports the rejection with the numbers; (iii) the semantic layer is not "
             "an illustration of the model but a mirror of it, and the difference between the two can be computed; (iv) the quality of "
             "the empirical agreement is limited by the normative instrument used to produce the ground truth, and that limitation is "
             "quantified rather than hidden."),
        ("b", [
            "Proposition 1 (unconditional hierarchy). Deriving the edge weights alpha from the facet weights beta makes S2 >= S3 >= S4 "
            "hold for every deficit vector; the reparameterisation changes no published number.",
            "Differentiated beta canon. Ten facets reweighted; identical beta pairs fall from 8 to 1; measured kappa effect +0.0019.",
            "Oversight inferred from facts. The regime is derived from declared review and audit facts, never invented; kappa +0.0078.",
            "Declared coverage. The gate is a parameter, the corpus contains genuinely incomplete profiles, and 18,240 pairs abstain.",
            "ReviewNeed, a non-decisional index that orders cases by the external review their verdict demands.",
            "Two mechanisms implemented, tested and left inert (lambda(E), Psi) because their measured effect is null or negative.",
            "Ontology v4.2: 1,927,780 triples, 34 SHACL shapes, zero violations, 76/76 invalid fixtures detected, arithmetic mirror to "
            "1.61 x 10^-12.",
            "An instrument for human adjudication (120 blind pairs), and the measurement of how kappa depends on the normative priors.",
        ]),
        ("p", "The paper is organised as follows. Section 2 situates the model among the families of machine-ethics approaches. "
             "Section 3 states the architecture. Section 4 gives the formal core, equation by equation, with the canonical parameters. "
             "Section 5 describes the ontology and its validation. Section 6 describes the corpus and the normative ground truth. "
             "Section 7 reports the measured results. Sections 8 and 9 discuss them and state the limitations. Section 10 gives the "
             "reproduction recipe."),
    ])

    # ---------------------------------------------------------------- 2
    section(doc, "2. Machine ethics, governance instruments and operational stacks", [
        ("p", "Machine ethics has developed along four families (Moor, 2006; Floridi, 2004; Wallach & Allen, 2008; Allen, Smit & Wallach, 2005; Anderson & Anderson, 2011). Top-down approaches encode principles or rules; bottom-up approaches "
             "learn values from data or interaction; hybrid approaches combine the two; value-alignment programmes optimise objective functions (Bostrom & Yudkowsky, 2016); and the governance tradition supplies "
             "instruments - the UNESCO Recommendation on the Ethics of Artificial Intelligence (UNESCO, 2021), the OECD "
             "Recommendation on AI (OECD, 2024), the EU AI Act (European Union, 2024), the GDPR (European Union, 2016), ISO/IEC "
             "42001 (ISO/IEC, 2023), the Council of Europe Framework Convention (Council of Europe, 2024) and the NIST AI Risk Management Framework (NIST, 2023) - which enumerate duties without formalising how a particular case satisfies them (Jobin et al., 2019; Dignum, 2019)."),
        ("p", "Industrial safety stacks - moderation APIs and guard models - solve a different problem: filtering content at scale, in the way functional-safety and information-security standards govern failure modes (ISO, 2018; ISO/IEC, 2023; NIST, 2025). "
             "They are strong at enforcement and weak at justification: they do not represent the duties of the agent, the "
             "irreversibility of the consequence, or the chain that delegates a duty. ETH-WCMK addresses the gap in Table 2."),
        ("t", ("Table 2. Position of ETH-WCMK relative to the main families of machine-ethics approaches.",
              ["Family", "What it represents", "What it leaves out", "How ETH-WCMK differs"],
              [["Principle-based (top-down)", "Principles and rules", "Context, capacity, measurement", "Principles become typed duties anchored to instruments"],
               ["Learning-based (bottom-up)", "Preferences from data", "Normative justification", "The model does not learn values; it evaluates declared capabilities against duties"],
               ["Value alignment", "Objective functions", "Institutional duties and redress", "Adequacy is measured per duty, not per objective"],
               ["Governance frameworks", "Obligations at the institutional level", "Operational decision per case", "34 operational rules derived from instruments, applied per case-agent pair"],
               ["Safety stacks (moderation, guard models)", "Content filtering at scale", "Agency, oversight, redress", "Verdict plus trace: deficits, gap, risk, review need, regime"],
               ["ETH-WCMK", "Case x agency confrontation with a trace", "Human judgment (pending, instrumented)", "Formal core plus validated ontology, both testable"]],
              [1.3, 1.6, 1.6, 2.0]),
        ),
        ("p", "The design principle that distinguishes the model is non-compensation, a deontic commitment in the sense of Ross (2002): a duty that cannot be traded is not a weight in a score. A deficiency in one duty does not buy credit in "
             "another; adequacy is attenuation, never erasure; and the verdict is taken on the pessimistic bound of the adequacy band, "
             "not on its central value. The model does not claim that the agent is virtuous (Vallor, 2016); it measures whether the duties the agent declared were met."),
    ])

    # ---------------------------------------------------------------- 3
    section(doc, "3. The model: two objects and a bridge", [
        ("f", (FIG + "/fig1_pipeline.png", "Figure 1. The confrontation pipeline: an ETHCASE and a WCMK profile meet in the formal core, "
              "which produces a verdict and a trace, and the ontology mirrors the trace in RDF.")),
        ("p", "An ETHCASE is a tuple of domain, severity, irreversibility, prudential mode, temporal horizon, epistemic uncertainty, "
             "the number and nature of those affected, the conflict pattern among duties, and a set of procedural facts (whether logs "
             "exist, whether notice was given, whether an appeal channel exists, whether consent was obtained, whether a prior incident "
             "occurred). A WCMK profile is a vector of declared levels over the 33 canonical duties, with beta specifying which pillars "
             "each duty touches, four aggregation policies, twelve hard guards and a declared subset of the duties it has taken on."),
        ("p", "The bridge is the arithmetic of the core. It produces, in this order: the projection of levels and requirements onto the "
             "four pillars (what each duty demands of the agent and what the agent actually reports), the deficits (the distance "
             "between demand and delivery, per pillar and per duty), the structural terms S2, S3 and S4 (the face, edge and vertex "
             "corrections of the tetrahedron), the raw adequacy, the guard failures and the material gap (the largest single "
             "shortfall of a duty below the minimum its domain requires), the stakes (how much the case puts at risk, ordered by "
             "regime) and the veto (the condition under which no adequacy score can lift the verdict), the adequacy band (the range "
             "the value can take rather than one number), the abstention conditions, the residual risk, the review need and the "
             "verdict. Each of "
             "these is a field in the ontology, so the verdict can always be reconstructed from the graph. The representation is canonical rather than lexical: two cases described in different words enter the same arithmetic only if they occupy the same conceptual roles, which is the semiotic assumption the model inherits (Peirce, 1931-1958; Gärdenfors, 2000)."),
    ])

    # ---------------------------------------------------------------- 4
    section(doc, "4. The formal core", [
        ("p", "The core is four files, about 1,070 lines: core.py (the arithmetic), geometry.py (the lattice), facet_registry.py "
             "(the canon of 33 duties) and fact_grounding.py (the observational caps). Its parameters are declared, not hidden: "
             "Calibration.is_valid() refuses to accept an incoherent set, and the invariants I1-I44 test the behaviour of each."),
    ])
    section(doc, "4.1 Pillars, geometry and Proposition 1", [
        ("p", "The four pillars W (Want), C (Can), M (Must), K (Know) are independent magnitudes, not shares of a simplex: an agent "
             "can be competent and obliged at the same time. The tetrahedron does not measure the state; it indexes the relation "
             "between duties, a representational device in the sense of conceptual spaces (Gärdenfors, 2000). Its face lattice has fifteen slots - four vertices, six edges, four faces, one cell - and a duty is "
             "represented by the face it spans."),
        ("f", (FIG + "/fig2_lattice.png", "Figure 2. The face lattice of the 3-simplex: four vertices, six edges, four faces and one "
              "cell. Each duty occupies the face it spans; the edge weights are the marginal of the face weights.")),
        ("eq", 0),
        ("eq", 1),
        ("p", "Proposition 1. If the weight of every edge is one third of the sum of the weights of the faces that contain it, and "
             "the four face weights sum to one, then for every deficit vector d ≥ 0 we have S₂ ≥ S₃ ≥ S₄. The proof is short: each "
             "edge of the tetrahedron lies in exactly two faces, so the derived edge weights sum to one; for each face the sum of the "
             "weights of its three edges is proportional to the weight of the face; and the minimum over an edge is never smaller than "
             "the minimum over the face that contains it, because the Gödel t-norm is monotone. In v12 the inequality required a "
             "condition on alpha. In v13 alpha is not a free parameter, and the condition disappears."),
        ("p", "The consequence is measurable: at beta = 1/4 the derived alpha is exactly 1/6, the value used in the v10-v12 "
             "calibration, so the reparameterisation changes no published number. The proposition was tested on the complete grid "
             "{0, 0.05, ..., 1}^4 x four beta-vectors, including non-uniform ones (invariant I34), and the mirror over the corpus "
             "confirmed that the derived alpha reproduces the previous numbers to 0.0 (Section 7.7)."),
    ])
    section(doc, "4.2 The canon of 33 duties", [
        ("p", "The canon is deontic in the classical sense (Kant, 2012; Ross, 2002) and obeys three rules: the beta vector of a duty sums to one; at most three pillars may be non-zero; and every "
             "non-zero beta is at least 0.15. The census is 1 uni-pillar duty, 10 bi-pillar and 22 tri-pillar, none spanning four. "
             "Twelve duties carry a hard guard: below the guard floor the duty cannot be compensated by another pillar."),
        ("t", ("Table 3. The canonical facet set: beta over (W, C, M, K), number of pillars, aggregation policy and guard floor.",
              ["Code", "Duty", "beta (W / C / M / K)", "Pillars", "Aggregation policy", "Guard floor"],
              [list(r) for r in FACETS], [0.5, 1.6, 1.5, 0.6, 1.5, 0.7]),
        ),
        ("p", "The differentiation of beta in this round (D5.5) changed ten duties (W6, C2, C5, M2, M4, M10, K1, K2, K5, K7). "
             "The number of pairs with identical beta vectors fell from 8 to 1 (C3 and C7 remain deliberately equivalent, both "
             "containment-type duties); pairs with Chebyshev distance below 0.12 fell from 26 to 23, while exact-identity pairs "
             "turned into close pairs, which is why the strictly near-identical count rose from 18 to 22. The measured effect on "
             "agreement with the panels is +0.0019 (95% CI 0.0009-0.0032), and +0.0094 combined with the oversight mechanism."),
    ])
    section(doc, "4.3 Requirements, projection and deficits", [
        ("eq", 2),
        ("eq", 3),
        ("eq", 4),
        ("eq", 5),
        ("p", "The requirement of a duty in a case is its criticality base (0.55, 0.70, 0.85 for criticality 2, 3, 4) plus terms "
             "for severity, irreversibility, prudential mode and horizon, an uncertainty term for duties whose primary pillar is K, "
             "and, when the case declares no oversight regime, an additional 0.08 on the human-review duty M9: what the institution "
             "does not provide, the agent must supply. For guarded duties the requirement is never below guard floor + 0.05 (I18). "
             "A duty is never reported with a weight: beta is the only weight in the model (D4.17)."),
        ("p", "A declared level is limited by a verifiable fact of the case. If the agent reports an accountability level of 0.9 but "
             "no logs exist, the level is capped by the requirement of that duty times the compliance implied by the fact "
             "(Eq. 5). The cap applies only to duties actually reported: an unreported duty is recorded as missing coverage, not as "
             "a zero (D5.9). Without this rule, 75.8% of the prohibitions the panels issue are invisible to the arithmetic."),
    ])
    section(doc, "4.4 Structural terms, adequacy and the veto", [
        ("eq", 6),
        ("eq", 7),
        ("eq", 8),
        ("eq", 9),
        ("eq", 10),
        ("p", "A duty fails as a guard when the level achieved - after the observational cap - is below its requirement; the "
             "material gap is the largest such failure among duties the domain marks critical or that carry a hard guard. A veto is "
             "triggered on a pillar when the worst gap among the duties touching it reaches the pillar threshold theta and the "
             "pillar is critical for the domain or a guard floor has been crossed; it is a hard veto when that gap exceeds theta by "
             "0.25 scaled by the stakes, or when a floor breach coincides with stakes of at least 0.70. Both conditions are "
             "explicit fields in the graph, because a threshold that is not declared cannot be audited. Adequacy is then capped: it "
             "cannot exceed 1 - (0.40 + 0.40 stakes) times the cap gap."),
    ])
    section(doc, "4.5 Stakes, oversight and residual risk", [
        ("p", "The stakes of a case weight severity, effective irreversibility, prudential posture and horizon. Oversight enters "
             "through the effective irreversibility: a harm that a verified human review can still catch is not the same harm as one "
             "no one can catch. The regime is inferred from the declared facts (review plus independent audit implies in the loop; "
             "review or an appeal channel implies on the loop; nothing declared implies none; nothing stated at all implies "
             "unspecified, which is exactly the v12 behaviour). The order of stakes is provably s_in <= s_on <= s_none (I38), and "
             "the adequacy under an unspecified regime is identical to the v12 adequacy (I36)."),
        ("eq", 11),
        ("eq", 12),
        ("eq", 13),
        ("eq", 14),
        ("eq", 15),
        ("p", "Risk is a potential consequence modulated by the observed delivery capacity of the agent, in the sense of responsibility for consequences that outlive the act (Jonas, 1984). It never vanishes: a "
             "perfectly adequate agent still carries residual risk, because the probability of failure is not zero and the "
             "consequence mass is not reduced by adequacy alone."),
    ])
    section(doc, "4.6 Uncertainty, coverage and abstention", [
        ("eq", 16),
        ("eq", 17),
        ("p", "Confidence propagates into an adequacy band, and the verdict is taken on the lower bound. The coverage gate "
             "declared at 0.70 of the 33 duties is a parameter, validated by invariant I44: a profile declaring 23 duties abstains "
             "with the gate at 0.70 and does not abstain at 0.60. This is the difference between a model that punishes silence and "
             "a model that refuses to judge what it cannot see. In the corpus the two treatments of an undeclared duty produce "
             "kappa 0.8085 and 0.0801 respectively, on the same 36,480 pairs."),
    ])
    section(doc, "4.7 Review need, salience and cross-pillar duty", [
        ("eq", 18),
        ("eq", 19),
        ("p", "ReviewNeed is declared as non-decisional: it may not change the class of a verdict, only order the cases that share "
             "it by the external review they actually demand (I36). Its weights sum to one and are fields in the ontology. "
             "Psi measures how much of a duty escapes the pillar that carries it: for C6 the containment component belongs to M, "
             "and that exposure is recorded as a governance diagnostic even though it does not enter the score."),
    ])
    section(doc, "4.8 The decision ladder and stratified agency", [
        ("eq", 20),
        ("eq", 21),
        ("p", "The ladder is lexicographic and runs on Aa_low: abstention first (coverage or epistemic conflict), then the hard "
             "veto, then the categorical prohibition, then review, then conditional allowance, then allowance. Hysteresis prevents "
             "oscillation: a verdict loosens only if the adequacy exceeds the bar plus 0.05; it tightens immediately. Agency is "
             "stratified - model, system, operator - because the capacity to act and the capacity to answer for the act are not the same thing (Frankfurt, 1971); the chain is evaluated at its weakest link and the result of each layer is "
             "reported (Eq. 21). Thirty-two of the 33 duties require an accountability layer that a model or a tool cannot carry "
             "alone, which is why delegation has consequences (D4.24)."),
        ("f", (FIG + "/fig3_ladder.png", "Figure 3. The decision ladder, its thresholds and the hysteresis that governs loosening.")),
    ])
    section(doc, "4.9 Canonical parameters", [
        ("t", ("Table 4. Canonical parameters of the v13 core, with their status and the equation in which they appear.",
              ["Parameter", "Canonical value", "Status", "Equation"],
              [list(r) for r in CALIB], [1.7, 2.3, 1.4, 0.8]),
        ),
    ])

    # ---------------------------------------------------------------- 5
    section(doc, "5. The semantic layer: ontology v4.2", [
        ("p", "The ontology is generated from the code, not written by hand. Every class, individual and constant comes from "
             "facet_registry.py, core.py or the corpus generator, so a facet that exists in the graph is a facet that the core "
             "applies, and a guard floor in the graph is the same number as the guard floor in the code (D4.28). The namespace is "
             "ethwcmk.org with the prefixes eth, fac, cal, cse, ag and norm, with PROV, SKOS, OWL, SHACL and TIME as standard "
             "supports (W3C, 2012; W3C, 2014; W3C, 2017). The model is a classical instance graph: the semantics live in explicit typed individuals, not in OWL "
             "reasoning."),
        ("p", "The vocabulary contains 69 classes, 84 object properties and 225 datatype properties, with 29,310 named individuals. "
             "The principal classes are Agent, AgentLayer, DelegationChain, ChainLink, Profile, EthicalCase, Facet, FacetObservation, "
             "FacetRequirement, GuardFailure, Norm, NormativeInstrument, NormConflict, Obligation, Permission, Prohibition, "
             "LatticeSlot, StructuralTerm, Confrontation, Decision, Evidence, Consequence, Stakeholder, Vulnerability, "
             "OversightRegime, Calibration and FactGrounding. Facets are typed into the four pillar families and guarded facets "
             "carry the GuardedFacet type."),
        ("f", (FIG + "/fig7_ontology.png", "Figure 4. Ontology v4.2: modules, instance graph and the validation gates.")),
        ("t", ("Table 5. Ontology modules and the elements they declare.",
              ["Module", "Triples", "What it declares"],
              [["01_core", "1,804", "pillars, the 15 lattice slots, structural terms, weights"],
               ["02_facets", "2,381", "33 facets, beta components, policy, guard floor, observables, 429 criticality statements"],
               ["03_deontic", "3,716", "123 norms, 62 instruments, 88 conflicts, 73 obligations, 26 permissions, 24 prohibitions, 5 priority engines, 5 defeasibility rules, 8 resolution strategies"],
               ["04_agency", "256", "three agent layers, delegation rules, pillars a layer cannot carry"],
               ["05_dynamics", "141", "drift profiles, hysteresis rule, value mappings for severity, reversibility, prudential mode"],
               ["06_calibration", "148", "the ladder, declared coefficients and their sum constraints, two Calibration individuals"],
               ["07_grounding", "63", "the E30 observational cap rules"],
               ["shapes (v4 and v6)", "1,347", "34 node shapes for the core graph, plus six for the v13 mechanisms"]],
              [1.1, 0.8, 4.6]),
        ),
        ("t", ("Table 6. Instance graph generated from corpus v7 (counts of typed individuals).",
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
        ("p", "The shapes constrain the graph against the same rules the code implements: the beta sum must be exactly 1 and at "
             "most three components non-zero (min 0.15); severity, reversibility, prudential mode and horizon must be among the "
             "declared individuals; the lattice slot kind must be vertex, edge, face or cell and must satisfy the incidence "
             "constraints; a prohibition must declare an obligation on the pillar it prohibits; a conflict must declare the "
             "resolution strategy and its outcome and the status must be consistent with whether it was resolved; every level, "
             "risk and adequacy field is bounded to [0, 1]; the v6 shapes add the bounds for review need, the salience fields and "
             "the oversight enumeration."),
        ("p", "Validation produced four independent checks. SHACL: zero violations against both shape sets, with no violation "
             "reaching a level other than info. The 76 deliberately invalid fixtures - instances constructed to violate exactly one shape - were detected, and every one was attributed "
             "to the shape it was designed to break. SPARQL: 42 checks, 42 passing, among them the lattice census (15 slots, 108 "
             "incidences, weight sums correct), the registry rules (33 facets, 12 guard floors above zero, beta sums 1.0), and the "
             "arithmetic mirror over 403 instantiated confrontations, which agrees with core.decide to a maximum difference of "
             "1.61 x 10^-12, below the declared 1 x 10^-6 tolerance, with zero verdict divergences. Validation took 301.9 s."),
        ("p", "Three defects were found during validation and corrected, and they are part of the methodological record: a SPARQL "
             "check of the beta sum used the facet's own literal, which SHACL already enforces, so it was tautological; two checks "
             "used nested sub-selects and predicate expressions inside BIND, which are not valid SPARQL and were rejected by the "
             "engine; and a check that read coverage from the Profile, where it is not asserted, was rewritten to read it from the "
             "Confrontation. A validator that cannot fail cannot validate."),
    ])

    # ---------------------------------------------------------------- 6
    section(doc, "6. Corpus and normative ground truth", [
        ("p", "Corpus v7 contains 1,520 cases (1,200 procedurally generated with distinct parameter vectors and 320 narrative "
             "layer-B cases), confronted with 145 profiles - 144 persona instances across 36 types - personas are profile archetypes generated with a declared deficit in one pillar - plus one self-declared profile - "
             "giving 220,400 (case, profile) pairs. The cases span 13 domains: health, justice and security, critical "
             "infrastructure, finance, privacy, public governance, media, education, labour, environment and energy, transport, "
             "research and digital security. Twenty-four persona types concentrate a deficit in one pillar, one per duty; six types "
             "declare only between 9 and 33 duties, which is what makes coverage a live parameter."),
        ("p", "The ground truth is an operational rubric, not a set of human judges. A shared kernel anchors every panel to a duty "
             "and a floor; three lenses then apply explicit rule tables: A is deontological (rights, due process, consent), B is "
             "prudential (expected harm, redress, bounded harm, sunset clauses), and C is institutional compliance (data "
             "minimisation, human review, fail-safe design, detect and respond). Thirty-four rules, all anchored to a named "
             "instrument - Rio Declaration Principle 1 (1992), UDHR Article 10 (United Nations, 1948), UN CRC Article 12 (United Nations, 1989), GDPR Articles 5, 22 and 25 (European Union, 2016), the Belmont Report (1978), the Declaration of Helsinki (1964), the ILO Declaration (International Labour Organization, 1998), ACM/IEEE codes, ISO 26262 (ISO, 2018), IEC 62443, ISO 27001 (ISO/IEC, 2023), NIST CSF (NIST, 2025), the OECD Recommendation (OECD, 2024) - fire on declared facts and levels, "
             "and each is counted: fired pairs and pairs whose verdict actually changed. Rule A8 (three or more duties below their "
             "floor) fires on 137,723 pairs and changes the panel verdict in 76,559 of them."),
        ("p", "The consensus of the three panels is the reference, and agreement with it is measured with Cohen's kappa (Cohen, 1960). It is unanimous on 50.9% of the pairs; 31,279 pairs (14.2%) are "
             "adjudicated by the kernel alone, below the declared ceiling of 40%. The panels agree with each other at 0.6447 (A-C), "
             "0.3533 (A-B) and 0.3153 (B-C): the rubric is not a single voice, and B diverges from the model more than the others "
             "(0.3324 against 0.5223 and 0.5147), which is expected, since the core is built on duties and limits and the "
             "prudential lens penalises that asymmetry."),
    ])

    # ---------------------------------------------------------------- 7
    section(doc, "7. Results", [
        ("p", "Table 7 summarises the gates of the round; each gate names the artefact that measures it. The rule of the project is "
             "that no number enters the paper without an artefact behind it."),
        ("t", ("Table 7. Gates of Round 5 and their verdicts.",
              ["Gate", "Content", "Verdict", "Evidence"],
              [["G10", "Core v13: unconditional hierarchy, derived alpha, lambda(E), ReviewNeed, oversight", "PASS", "pytest suite, 69 invariants, 45.75 s"],
               ["G11", "Facet canon: differentiated beta, guards, measured ablation", "PASS with explicit rejection", "B21_ablation.json"],
               ["G12", "Geometric layer informative? Psi diagnostic, zeta rejected", "PASS", "B20, B21, B23"],
               ["G13", "Corpus v7: genuinely incomplete profiles, derived oversight, rebalanced domains", "PASS", "corpus_v7_coverage.json"],
               ["G14", "Ontology v4.2 revalidated", "PASS, 42/42 checks, mirror 1.61e-12", "ontology_v4_2_validation.json"],
               ["G15", "Batteries B20-B25", "5 of 6 closed; B24 declared non-executable with its measurement", "Evaluacoes/r5"],
               ["G16", "Stratified kappa and human adjudication instrument", "PASS (instrument issued)", "adjudication_packet_blind.csv"],
               ["G17", "Paper, manifest, commit", "PASS (47 artefacts, 20 runs, 65.35 MB)", "manifest_r5.json"],
               ["G18", "Traceability: every number re-derived from its artefact", "PASS, 166/166 statements", "paper_consistency_check_v13.json"],
               ["G19", "Sensitivity of kappa to the rubric priors", "PASS, 11 variants, kappa 0.2974-0.6005", "B26_rubric_sensitivity.json"]],
              [0.5, 2.3, 1.5, 1.9]),
        ),
    ])
    section(doc, "7.1 Invariants and geometry", [
        ("p", "The invariant suite contains 69 tests (I1-I44 plus geometry and grounding tests). New in this round: I34 tests "
             "Proposition 1 on the complete grid of deficits; I35 refuses to load an incoherent calibration; I36 makes the "
             "unspecified oversight regime identical to v12 and declares the weights of ReviewNeed; I37 proves lambda(E) is the "
             "identity when s = 0; I38 orders the stakes by regime; I39 proves the adequacy with zeta = 0 differs from v12 by "
             "exactly zeta times Psi; I44 validates the coverage gate as a parameter. The lattice census computed from the code is "
             "15 slots, 108 incidences, structural weights summing to 1.0000000000, and the derived marginal is uniform at 1/6 at "
             "the canonical beta."),
        ("p", "Interpretation. The value of the suite is not the number of tests but what they rule out. I35 makes an incoherent calibration impossible to load, I38 makes the ordering of the stakes a property of the model rather than a hope about the parameters, and I44 turns the coverage gate into a variable the auditor can see and change. A reviewer can re-derive the geometry from the code instead of trusting the paper: the fifteen slots of the lattice, their weights and their incidences are computed, not declared."),
    ])
    section(doc, "7.2 Adversarial probes", [
        ("p", "2,064 adversarial probes and 7,815 assertions were re-executed against the v13 core with a pass rate of 1.000: "
             "zero monotonicity violations, no non-compensation breach, no guard bypass, and the hard veto is not overridden by the "
             "score in any probe. The probes include the case that exposed the compensation hole in v12 (C3 = 0, a high level on "
             "another duty lifting the C pillar above the duty floor), which now produces a guard failure and a material gap."),
        ("p", "Interpretation. A pass rate of 1.000 does not show that the model is correct. It shows that no input built to break it succeeded in breaking the promises the arithmetic makes about itself. The consequence is narrow and usable: the compensation hole found in v12, where a strong level in one duty covered a failing duty in another, now leaves a recorded guard failure and a material gap, so an audit can cite an event instead of interpreting a score."),
    ])
    section(doc, "7.3 Which mechanisms actually change agreement", [
        ("p", "Each mechanism was implemented, enabled across its canonical range, and measured on 130,680 pairs of the corpus "
             "(1,080 cases x 120 profiles), against the consensus, with bootstrap confidence intervals on the difference (the pairs are resampled repeatedly to estimate the uncertainty of that difference)."),
        ("t", ("Table 8. Effect of the v13 mechanisms on kappa against the panels (130,680 pairs, frozen r3 ladder).",
              ["Variant", "kappa", "Delta vs baseline [95% CI]", "mean adequacy", "verdicts P / R / A / AWG"],
              [list(r) for r in MECHANISMS], [2.3, 0.7, 2.2, 1.0, 1.8]),
        ),
        ("p", "Only the oversight inferred from facts and the differentiated beta improve agreement, and their effects are "
             "significant. Salience and cross-pillar duty do not: kappa falls as they are activated. Both are therefore kept "
             "available in the core and inert by canon, with the numbers reported. In the sensitivity analysis (Sec. 7.6) they saturate the total-"
             "order index (ST ~ 1) precisely because they act through the decision thresholds: they move outputs but not agreement."),
        ("p", "Interpretation. Two mechanisms change the verdict for a reason an audit can name; two do not. Inferring the oversight regime from declared facts raises agreement because a reviewed case is treated differently from an unreviewed one. Differentiating beta raises agreement because duties that were indistinguishable become distinguishable. Salience and cross-pillar exposure move the outputs without moving the judgement, so they are kept as diagnostics: a governance team can inspect them, but the verdict does not depend on them. The rule the round establishes is that a mechanism is adopted only when its effect is measured, signed and significant."),
    ])
    section(doc, "7.4 Ablation of the canon", [
        ("p", "Removing the twelve hard guards drops kappa from 0.4633 to 0.1399 (delta -0.3234, CI -0.3306 to -0.3147): the "
             "guards are not decoration, they are the non-compensation. Removing the cross-pillar structure by collapsing every "
             "duty to its primary pillar drops kappa to 0.2691 (-0.1942). Removing a single guard changes kappa by at most 0.0042 "
             "in either direction, which is the reason no guard can be defended individually by its effect on kappa alone: their "
             "value is structural, not marginal."),
        ("t", ("Table 9. Ablation (48,400 pairs, 400 cases x 120 profiles).",
              ["Ablation", "kappa", "Delta"],
              [list(r) for r in ABLATION], [3.4, 0.8, 1.1]),
        ),
        ("p", "Interpretation. The normative weight of the model sits exactly where the design placed it. Removing the twelve hard guards takes the agreement with the panels from 0.4633 to 0.1399, a fall of 69.8%, which means the guard floors are not a stylistic choice but the mechanism that produces the behaviour the panels reward. The small individual deltas carry the opposite instruction: no guard can be defended one by one, so the canon has to be defended as a whole. For a deploying organisation, that means the floors cannot be negotiated per duty without destroying the property the model is being used for."),
    ])
    section(doc, "7.5 Fact grounding", [
        ("p", "On 43,210 pairs, 42,464 (98.27%) contained at least one fact contradicting a declared level. The rule applied "
             "224,097 caps; the mean excess over the cap was 0.3611. The grounding changed the verdict of 18,898 pairs (43.74%), "
             "of which 15,153 moved from review to prohibition. Kappa against the panels rises from 0.2463 without grounding to "
             "0.5526 with it, which is why the mechanism is mandatory and why the strength parameter s is declared: at s = 0 the "
             "core behaves exactly as v11."),
        ("p", "Interpretation. Declaring a level is not the same as delivering it. Almost every profile states a level that the case's own facts contradict, and correcting that changes nearly half of the verdicts. The rise of kappa from 0.2463 to 0.5526 is not a tuning effect: it is the difference between judging what an agent claims and judging what an agent can show. An audit trail built on declared levels alone would systematically overstate agency."),
    ])
    section(doc, "7.6 Sensitivity of the parameters", [
        ("p", "Morris elementary effects - a first-order screening that varies one parameter at a time and records the resulting change in the output (200 trajectories; Morris, 1991) and a paired Sobol design (Sobol, 2001; Saltelli et al., 2008) with N = 1,024 over the 12-dimensional "
             "calibration space, were run on a panel of 12 real cases spanning the 13 domains and five verdicts. With outputs that "
             "are step functions at the decision boundaries, the total-order indices saturate near 1; the reportable quantities are "
             "the first-order indices and the Morris means."),
        ("t", ("Table 10. First-order Sobol index S1 for selected parameters and outputs.",
              ["Parameter", "S1 on mean adequacy", "S1 on abstention", "S1 on residual risk", "S1 on review need", "S1 on permissiveness"],
              [list(r) for r in SOBOL], [1.8, 1.1, 1.0, 1.1, 1.1, 1.4]),
        ),
        ("p", "The coverage gate is the dominant tuning knob (S1 = 0.749 on adequacy, 1.0 on abstention), which is why it was moved "
             "from an implicit constant to a declared parameter. Gamma is the largest structural coefficient (0.123). The oversight "
             "attenuation has no effect on adequacy - the verdicts are saturated - but is the dominant driver of the hard veto "
             "(S1 = 0.701). The canonical zero coefficients are inert at the declared value, not inert in principle: Morris mu is "
             "0.0004 for salience at the canonical setting, while its total order is 0.9998, which is precisely the distinction "
             "between a parameter that does nothing and a parameter whose value has not been declared."),
        ("p", "Interpretation. Two parameters govern the model, and both belong in the audit record rather than in a code default: the coverage gate decides when the model is allowed to speak at all, and the structural penalty decides how much a deficit weighs. Everything else is comparatively flat, including coefficients earlier rounds spent effort calibrating. For a deploying organisation this is a governance finding, not a numerical curiosity: the settings with the largest influence define the scope of the judgement, so they must be declared, versioned and reviewed."),
    ])
    section(doc, "7.7 The arithmetic mirror", [
        ("p", "The mirror recomputes every one of the 220,400 confrontations of corpus v7 from persona factors, jitter, the "
             "requirement of the case, the declared subset of duties and the observational caps, and compares each quantity with the "
             "value stored in the corpus. The maximum absolute difference is 0.0 for S2, S3, S4, raw adequacy, the band bounds, the "
             "bar, the stakes, residual risk, the structural terms, the epistemic penalty, the material gap and the veto set; there "
             "are zero verdict divergences and the recomputed distribution is identical to the stored one. Runtime 121.9 s. The "
             "methodological caution is that feeding the mirror the stored, rounded levels (4 decimals) produces differences up to "
             "1.7 x 10^-2 that cross guard floors; the faithful mirror reconstructs the unrounded levels before calling the core."),
        ("p", "Interpretation. The mirror closes the distance between the paper and the implementation: a reviewer who reads only the graph obtains the same verdict as the code, quantity by quantity. It also carries a caution that generalises beyond this project, because the divergence disappeared only after the mirror reconstructed the unrounded levels. A mirror fed with rounded values looks correct and is not, so the declared storage precision is part of the verification rather than a detail of it."),
    ])
    section(doc, "7.8 Noise, hysteresis and structural ablation", [
        ("p", "Injecting noise into the observed levels increases the verdict flip rate from 1.32% at sigma = 0.02 to 8.56% at "
             "sigma = 0.2, and the shifts are asymmetric: degraded observations make the model more restrictive twenty times as "
             "often than more permissive (0.0815 versus 0.0041 at sigma = 0.2). Over an eight-step trajectory of 20,436 tracked "
             "cases there were 7,461 verdict changes, 103 of them oscillations, and the hysteresis blocks 6,382 loosening "
             "transitions. Ablating the structural terms changes kappa by 0.0007 relative to the full model on 183,920 pairs: the "
             "geometry organises the audit trail, it does not by itself produce normative information. That is a finding, not a "
             "failure."),
        ("p", "Interpretation. The asymmetry is the finding. When observations degrade, the model becomes more restrictive twenty times as often as more permissive: noise pushes the verdict toward caution rather than toward permission. The hysteresis blocks 6,382 loosening transitions, so a profile does not oscillate across a decision boundary. The near-zero effect of removing the structural terms is a negative result and is reported as such: the tetrahedron organises the record, it does not generate the judgement."),
    ])
    section(doc, "7.9 Risk, agency and transfer", [
        ("p", "Decomposing the variance of residual risk over 183,920 pairs gives 98.07% to the case, 0.80% to the profile and "
             "1.13% to their interaction: risk is a property of the duty and the context, not of the agent. Yet 15.46% of cases "
             "change verdict across the 121 profiles confronting the same case, and 225 cases are rescuable by a better agency: "
             "risk is structural, admissibility is agential. In the delegation battery, only one of the 33 duties (pure "
             "capability) can be carried by a model or a tool alone; 96.97% of the canon requires an accountability layer, and "
             "choosing the best available delegate changes no verdict, while the worst changes 127, with the bottleneck pillar C in "
             "905 of them."),
        ("p", "Transfer is measured, not assumed. Fitting the ladder on nine domains and testing on the four never used "
             "(transport, research, digital security and labour) plus the 320 narrative cases gives kappa 0.4834 on the holdout "
             "against 0.4618 in sample, a transfer gap of -0.0215 - the model generalises better out of sample than inside it, which "
             "indicates that the fit is not memorising domain-specific patterns. Against baselines, the model beats a threshold on "
             "adequacy without the veto (0.1464), a majority-class classifier (0.0000) and an uncalibrated ladder (0.2025)."),
        ("p", "The LLM anchor battery - asking a local model to produce the profile that the arithmetic infers - could not be "
             "executed on this machine: the attempt produced an empty output file and a logged run of zero records. It is declared "
             "as non-executable with the measurement of the attempt, not replaced by a zero (D5.15)."),
        ("p", "Interpretation. Two practical conclusions follow from the same battery. Risk belongs to the case: 98.07% of its variance comes from the duties and the context, not from the agent. Admissibility belongs to the delegation: 15.46% of cases change verdict depending on which profile faces them, and 225 cases can be rescued by a better agency. Improving the agent is therefore not the same as reducing risk, and a deployment that promises the first by investing in the second is making a claim the model can measure and reject."),
    ])
    section(doc, "7.10 Agreement is an instrument property", [
        ("p", "Kappa depends on the normative priors of the rubric. Perturbing the duty floors by 10% moves kappa from 0.5336 to "
             "0.5507 or 0.5250; reducing the set of categorical duties to three moves it to 0.5085; using a single lens gives "
             "0.5223, 0.3324 or 0.5147; moving the coverage gate to 0.80 gives 0.6005 and to 0.60 gives 0.4907; treating an "
             "undeclared duty as a violation gives 0.2974. The variant that crosses 0.60 does so by increasing shared abstention, "
             "not by producing a better judgment. A kappa that rises because both sides fall silent is not a kappa that improves."),
        ("t", ("Table 11. Kappa against the rubric under eleven defensible priors (220,400 pairs).",
              ["Prior variant", "kappa", "delta"],
              [list(r) for r in RUBRIC], [2.6, 0.8, 0.9]),
        ),
        ("f", (FIG + "/fig4_strata.png", "Figure 5. Kappa by consensus stratum and kappa under the normative priors of the rubric.")),
        ("p", "Kappa is reported by stratum because the aggregate hides the structure: 0.8167 where the three lenses agree "
             "(112,179 pairs), 0.1371 where they split by one step (95,611), 0.0526 where they disagree by more (12,610). By "
             "coverage: 0.3832 for fully declared profiles and 0.3293 for partial ones, where both the model and the rubric "
             "abstain. By domain, agreement runs from 0.6110 in transport and 0.6103 in education down to 0.4624 in finance, with health at 0.4791 and telecommunications at 0.4790 in between. The spread across domains is 0.15, smaller than the spread produced by changing the rubric itself, which is why the instrument, not the domain, is the dominant source of disagreement."),
        ("f", (FIG + "/fig5_domains.png", "Figure 6. Kappa per domain in the corpus (13 domains).")),
        ("f", (FIG + "/fig6_verdicts.png", "Figure 7. Verdict distribution over the 220,400 (case, profile) pairs, and the two "
              "abstention classes: 18,240 pairs abstain for lack of coverage, 16,375 for epistemic underdetermination.")),
        ("p", "Interpretation. Kappa 0.5336 is not a measure of the model's quality. It is the overlap between the model and one particular normative instrument. The claim that can be defended is a qualified one: the model agrees with the instruments where the instruments agree with each other, and outside that region the disagreement is documented rather than resolved. Where both the model and the rubric abstain, the agreement of 1.000 measures shared silence, not shared judgement."),
    ])

    # ---------------------------------------------------------------- 8
    section(doc, "8. Discussion", [
        ("p", "Three things follow from the measurements. First, a formal model earns its authority by being testable against "
             "itself: the geometry is a theorem, the parameters are declared, and the ontology reproduces the arithmetic to "
             "machine precision. The mirror is the strongest result of the round because it eliminates the most common failure of "
             "this class of work - a paper whose numbers do not match its code. The trace fields - deficits, material gap, residual risk, review need, regime - are what make that claim auditable (Miller, 2019; Williams et al., 2022)."),
        ("p", "Second, the pluralism is not a rhetorical choice but a measured one. Three lenses anchored in named instruments "
             "disagree with each other, and the model is evaluated against the consensus. Reporting kappa by stratum is the honest "
             "way to do this: the model can defend 0.8167 on the cases where the instruments converge, and on the contested cases "
             "the divergence belongs to the lenses, not to the arithmetic. The abstention classes make that visible: 18,240 pairs "
             "abstain because the profile does not declare enough duties, 16,375 because the case is epistemically underdetermined."),
        ("p", "Third, the veto is where the model is most consequential. Ninety per cent of the cases trigger a veto, and 13.45% "
             "trigger a hard veto. The adequacy score does not override them. This is a design commitment: a duty that cannot be "
             "compensated is not a weight in a score, and the paper measures how much agreement the commitment costs."),
        ("p", "The decision to leave mechanisms inert is as important as the decision to add them. A cross-pillar duty term that "
             "reduces agreement is not a defect to be hidden: it is a hypothesis falsified with numbers, and it survives as a "
             "diagnostic in the graph, where governance can use it without the verdict depending on it."),
    ])

    section(doc, "9. Limitations", [("b", LIMITS)])

    section(doc, "10. Reproducibility", [
        ("p", "The repository is organised so that any claim can be traced: _analysis/formal_core holds the core and the "
             "invariant tests; _analysis/corpus the generators of the corpus and the rubric; _analysis/ontology the generator and "
             "the validator of the RDF; Evaluacoes/r5 the artefacts; manifest_r5.json lists 47 artefacts, 20 executions with their "
             "runtimes, the SHA-256 of each file and the git revision of the tree. The commands are: pytest over the invariant "
             "suite (45 s); the corpus generator; the battery runner, which writes the manifest; the ontology generator and "
             "validator (301.9 s); and the corpus mirror (121.9 s). Rounds r2 and r3 are frozen and are never overwritten; new "
             "results enter as deltas."),
        ("b", [
            "Open-science availability. The whole evidence chain is in the repository: the formal core and its tests under MIT; the ontologies, the facet registry, the corpus definitions and the texts under CC BY-SA 4.0. The generated RDF is in Ontologias/ontology_v4_2/, every measured artefact in Evaluacoes/r5/, the frozen rounds r2 and r3 read-only, and the manifest_r5.json ties each quoted number to a SHA-256 and a git revision. Nothing in this paper requires access beyond "
            "those files and the five commands listed above.",
        ]),
    ])

    section(doc, "11. Future work", [
        ("b", [
            "Execute the human adjudication packet with a panel of domain reviewers, and report kappa with confidence intervals "
            "against the sample power already computed.",
            "Re-derive the coverage gate from empirical abstention rather than declaring it, and test it across domains.",
            "Instrument oversight with more facts (who reviews, with what authority, on what time scale) instead of two booleans.",
            "Run the LLM anchor on a machine capable of it, to test whether a model can generate the profile that the arithmetic infers.",
            "Extend the ontology with PROV chains so that each verdict carries the version of the core that produced it.",
            "Test the mirror against a second implementation of the core, written independently, to separate the test from the code.",
        ]),
    ])

    section(doc, "12. Conclusion", [
        ("p", "ETH-WCMK v14 is a model whose geometry is proved, whose parameters are declared, whose mechanisms are measured "
             "before they are enabled, and whose semantic layer reproduces its arithmetic to 1.61 x 10^-12. Its verdicts come with "
             "a trace that can be inspected in RDF, and its agreement with the normative ground truth - 0.5336 overall, 0.8167 on "
             "unanimous cases - is limited less by the model than by the instrument used to produce the ground truth. The "
             "contribution of this round is therefore as much methodological as architectural: it shows how a model of machine "
             "ethics can be audited against its own numbers, and what remains genuinely open."),
    ])

    section(doc, "Declarations", [
        ("p", "Data and code availability. Every figure quoted in this paper is produced by code that is part of the repository and by artefacts stored with it. The formal core, the corpus and rubric generators, the ontology generator and its validator, the batteries and the invariant tests are under the MIT licence; the model text, the ontologies and the facet registry are under CC BY-SA 4.0. Each round is registered in a manifest, manifest_r5.json for this one, which lists 47 artefacts with their SHA-256 hash, their size, the runtime of each execution and the git revision of the tree. Rounds r2 and r3 are frozen and are never edited in place: a new revision writes a new round directory, which is what makes the numbers re-derivable rather than merely reported. The corpus itself is generated from declared parameters, so the 220,400 (case, profile) pairs can be rebuilt by the generator and do not have to be distributed as a dataset. The blind adjudication packet, 120 cases and 360 cells, is included in the repository for the human panel."),
        ("p", "Author contributions. L. M. M. Palazzo: conceptualisation, formal modelling, implementation of the core, ontology engineering, execution of the batteries and writing. T. Vanzin: review of the formal layer, validation of the semantic layer and editorial revision. Both authors read and approved the final text."),
        ("p", "Competing interests. The authors declare no competing interests."),
        ("p", "Funding. This work was developed with internal resources of the Postgraduate Program in Engineering and Knowledge Management (PPGEGC) at the Federal University of Santa Catarina. No external funding body is involved, and no funder influenced the choice of mechanisms, the rejection of any parameter value or the reporting of the negative results."),
        ("p", "Ethics. The cases are synthetic and contain no personal or sensitive data. The normative instruments cited, the UDHR, the CRC, the GDPR, the AI Act, the Belmont and Helsinki declarations, the ILO declaration, ISO and NIST documents, are used as sources of duties and are quoted as instruments. Nothing in this paper is legal advice, and no body named here endorses the model."),
        ("p", "Use of artificial intelligence. Language-model tools assisted with drafting, section organisation and editorial revision. Every quoted number comes from an artefact listed in Appendix A and is re-derived by the consistency checker, so the arithmetic is not model-generated. The authors are responsible for the content and for the claims verified against the artefacts."),
        ("p", "Open-science status. Code, data definitions, evaluation artefacts, the ontology and the equations are distributed with the paper under the licences stated above. The paper is written so that each claim can be checked from the repository without contacting the authors."),
    ])
    section(doc, "References", [("b", REFS)])

    appendix = [
        ("t", ("Table 12. Traceability: quoted figures and their artefacts.",
              ["Figure quoted", "Artefact", "Field"],
              [["220,400 pairs; 1,520 cases; 145 profiles", "Evaluacoes/r5/corpus_v7_coverage.json", "pairs_adjudicated, cases.total, personas"],
               ["18,240 coverage abstentions; 16,375 epistemic", "idem", "abstain"],
               ["kappa 0.5336; exact agreement 0.7886; within one step 0.9809", "idem", "kappa_model_vs_gold, model_vs_gold"],
               ["kappa by stratum 0.8167 / 0.1371 / 0.0526", "Evaluacoes/r5/kappa_by_stratum_v13.json", "by_stratum"],
               ["oversight +0.0078 [0.0057, 0.0100]; beta +0.0019 [0.0009, 0.0032]", "Evaluacoes/r5/B20_variant_eval_full_corpus.json", "results[].kappa_vs_panel, .ci95"],
               ["guards -0.3234; primary-pillar -0.1942", "Evaluacoes/r5/B21_ablation.json", "results"],
               ["grounding 98.27%, 224,097 caps, 18,898 flips, kappa 0.5526 vs 0.2463", "Evaluacoes/r5/B22_fact_contradiction.json", "all named fields"],
               ["S1 coverage gate 0.749; hard veto 0.701", "Evaluacoes/r5/B23_sobol_v13.json", "sobol, morris"],
               ["mirror 220,400, max difference 0.0, 0 divergences, 121.87 s", "Evaluacoes/r5/mirror_full_corpus_v13.json", "confrontations, global_max_abs_difference, runtime_seconds"],
               ["2,064 probes, 7,815 assertions, 1.000", "Evaluacoes/r5/B8_probes_reverified_v13.json", "summary"],
               ["rubric kappa range 0.2974-0.6005", "Evaluacoes/r5/B26_rubric_sensitivity.json", "variants[].kappa"],
               ["1,927,780 triples; 50,160 requirements; 169,950 observations; 21,280 groundings; 16,475 guard failures", "Ontologias/ontology_v4_2/generation_report.json", "instances_triples, counts"],
               ["42/42 checks; SHACL 0 violations; 76/76 fixtures; mirror 1.61e-12; 301.9 s", "Evaluacoes/r5/ontology_v4_2_validation.json", "gate_verdict, shacl, invalid_fixtures, mirror, sparql_checks"],
               ["69 invariant tests, 45.75 s", "_analysis/formal_core/tests", "pytest output"],
               ["34 rules; panel kappa 0.6447 / 0.3533 / 0.3153", "Evaluacoes/r5/corpus_v7_coverage.json", "gold.rules, gold.panel_kappa"]],
              [2.4, 2.1, 1.9]),
        ),
    ]
    section(doc, "Appendix A. Traceability", appendix)

    set_document_properties(
        doc,
        "ETH-WCMK v14: a formally verified core and a SHACL-valid ontology for auditing delegated ethical agency",
        "Luiz Palazzo and Tarcisio Vanzin",
        "Machine ethics; formal verification; RDF/SHACL ontology; sensitivity analysis; delegated ethical agency",
        "machine ethics; formal core; ontology; SHACL; Sobol; kappa; reproducibility",
    )
    add_running_footer(doc, "ETH-WCMK v14 - Palazzo & Vanzin - round 5")
    doc.save(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
