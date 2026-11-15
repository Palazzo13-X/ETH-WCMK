"""
ETH-WCMK facet ontology v2 (26 facets, cross-pillar projection).

Design decisions
----------------
1. A facet belongs primarily to one pillar, but it can *project* onto other
   pillars with declared weights beta_{f,i}, sum_i beta_{f,i} = 1.
   This is what the paper's "facetas compartilhadas" need and what the current
   SHACL shape (sh:maxCount 1 on projectsToCoreVertex) forbids.
2. Facet levels s_f and facet requirements q_f live in [0,1]; they are NOT a
   distribution. The pillar score is the beta-weighted average of the facet
   levels that project onto it. The simplex constraint sum_i a_i = 1 is used
   ONLY for the tetrahedral embedding (geometry, volume, distances), never for
   the deficit computation: an agent can be strong in all four pillars at once,
   and forcing sum = 1 manufactures a fake trade-off.
3. Deficits are relative: delta_i = max(0, rho_i - a_i) / rho_i.
4. Every facet carries theta_f (tolerance) and a guard flag: guarded facets
   cannot be compensated by other pillars.

Outputs: facets_v2.json, facets_v2.csv (machine readable).
"""
from __future__ import annotations

import csv
import json

# code, label(pt), label(en), primary pillar, beta weights over (W,C,M,K),
# type of facet, guarded?, theta, rationale
FACETS = [
    # ---- WANT (Intenção) ------------------------------------------------------
    ("W1", "Orientação de fins", "Goal orientation", "W",
     (0.70, 0.20, 0.05, 0.05), "teleological", False, 0.15,
     "A goal the agent cannot state cannot be pursued; ties to capability for feasibility."),
    ("W2", "Alinhamento de valores", "Value alignment", "W",
     (0.60, 0.10, 0.20, 0.10), "teleological", True, 0.15,
     "Misaligned goals are an obligation problem as well as an intention problem."),
    ("W3", "Consideração de stakeholders", "Stakeholder regard", "W",
     (0.55, 0.15, 0.20, 0.10), "relational", False, 0.15,
     "Whose ends count; requires knowledge of who is affected."),
    ("W4", "Disciplina de prioridades", "Priority discipline", "W",
     (0.60, 0.25, 0.10, 0.05), "teleological", False, 0.15,
     "Trade-off arbitration among competing goals."),
    ("W5", "Estabilidade intencional", "Intentional stability", "W",
     (0.70, 0.20, 0.05, 0.05), "temporal", False, 0.20,
     "Goal drift over time; needs monitoring capability."),
    ("W6", "Legitimidade da intenção", "Legitimacy of intention", "W",
     (0.50, 0.10, 0.30, 0.10), "normative", True, 0.15,
     "NEW: an intention can be coherent and still illegitimate (usurped mandate). "
     "Separates 'wanting well' from 'having the right to want it'."),

    # ---- CAN (Recursos) -------------------------------------------------------
    ("C1", "Capacidade funcional", "Functional capability", "C",
     (0.15, 0.70, 0.10, 0.05), "capability", False, 0.15,
     "Can the action be performed at all."),
    ("C2", "Robustez", "Robustness", "C",
     (0.10, 0.65, 0.15, 0.10), "reliability", True, 0.20,
     "Performance under distribution shift and adversarial stress."),
    ("C3", "Controlabilidade", "Controllability", "C",
     (0.15, 0.55, 0.20, 0.10), "governance", True, 0.15,
     "Intervention, rollback, human override."),
    ("C4", "Adequação de escopo", "Scope adequacy", "C",
     (0.20, 0.60, 0.15, 0.05), "boundary", False, 0.15,
     "Fit between declared scope and actual deployment."),
    ("C5", "Suficiência de recursos", "Resource sufficiency", "C",
     (0.15, 0.70, 0.10, 0.05), "material", False, 0.15,
     "Compute, data, staffing, time."),
    ("C6", "Exequibilidade segura", "Safe executability", "C",
     (0.10, 0.55, 0.25, 0.10), "safety", True, 0.20,
     "Can it be executed without foreseeable harm."),

    # ---- MUST (Obrigação) ----------------------------------------------------
    ("M1", "Obrigação legal", "Legal obligation", "M",
     (0.05, 0.10, 0.75, 0.10), "deontic", True, 0.20,
     "Hard statutory constraints; non-negotiable."),
    ("M2", "Obrigação institucional", "Institutional policy obligation", "M",
     (0.05, 0.10, 0.70, 0.15), "deontic", False, 0.15,
     "Organizational mandates and internal policy."),
    ("M3", "Obrigação de princípio", "Ethical principle obligation", "M",
     (0.15, 0.10, 0.60, 0.15), "deontic", False, 0.15,
     "Non-codified normative expectations."),
    ("M4", "Obrigação de prestação de contas", "Accountability obligation", "M",
     (0.10, 0.20, 0.55, 0.15), "relational", True, 0.15,
     "Answerability to affected parties."),
    ("M5", "Obrigação de papel", "Role obligation", "M",
     (0.15, 0.15, 0.55, 0.15), "relational", False, 0.15,
     "Duties arising from the role the agent occupies."),
    ("M6", "Obrigação prudencial", "Prudential obligation", "M",
     (0.10, 0.20, 0.50, 0.20), "precautionary", True, 0.15,
     "Duty of care under uncertainty; bridges to Know."),

    # ---- KNOW (Conhecimento) -------------------------------------------------
    ("K1", "Conhecimento normativo", "Normative knowledge", "K",
     (0.10, 0.10, 0.30, 0.50), "epistemic", False, 0.15,
     "Knowing which norms apply and how they conflict."),
    ("K2", "Conhecimento causal", "Causal knowledge", "K",
     (0.15, 0.20, 0.15, 0.50), "epistemic", False, 0.15,
     "Model of consequences; prerequisite for prudent action."),
    ("K3", "Conhecimento contextual", "Contextual knowledge", "K",
     (0.20, 0.15, 0.15, 0.50), "epistemic", False, 0.15,
     "Local, situated, contingent information."),
    ("K4", "Conhecimento evidencial", "Evidential knowledge", "K",
     (0.10, 0.20, 0.20, 0.50), "epistemic", False, 0.15,
     "Quality, currency and coverage of the evidence base."),
    ("K5", "Conhecimento procedimental", "Procedural knowledge", "K",
     (0.10, 0.30, 0.20, 0.40), "operational", False, 0.15,
     "Knowing how to act correctly, including escalation."),
    ("K6", "Awareness de provenance", "Provenance awareness", "K",
     (0.05, 0.20, 0.20, 0.55), "epistemic", True, 0.20,
     "Source reliability and traceability of inputs."),
    ("K7", "Awareness de incerteza", "Uncertainty awareness", "K",
     (0.10, 0.15, 0.20, 0.55), "metacognitive", True, 0.20,
     "Calibration of confidence; the pillar that feeds U_E."),
    ("K8", "Capacidade de aprendizagem", "Learnability", "K",
     (0.10, 0.25, 0.20, 0.45), "metacognitive", True, 0.20,
     "NEW: the ability to improve after error. Absorbs the duplicated K6/K4 "
     "overlap and makes the model diachronic."),
]

PILLARS = ("W", "C", "M", "K")

# overlaps detected in the v1 catalogue and how v2 resolves them
OVERLAPS = [
    ("C2 Robustez", "C6 Exequibilidade segura", "distinct: robustness = performance under stress, executability = harm under normal operation"),
    ("C4 Escopo", "C5 Recursos", "distinct: scope = boundary of the mandate, resources = means available"),
    ("M1 Legal", "M3 Princípio", "distinct: enforceable vs. non-enforceable; M1 is guarded, M3 is not"),
    ("M1 Legal", "M2 Institucional", "distinct: source of authority; keeps both for jurisdiction mapping"),
    ("K1 Normativo", "M1 Legal", "cross-pillar: K1 measures knowing the norm, M1 measures complying with it"),
    ("K6 Provenance", "K4 Evidencial", "K4 = quality of evidence, K6 = traceability of its origin"),
    ("W1 Fins", "W4 Prioridades", "W1 = what is sought, W4 = how competing aims are arbitrated"),
    ("W2 Valores", "M3 Princípio", "W2 = agent's own values, M3 = external normative expectation"),
    ("K7 Incerteza", "M6 Prudencial", "K7 = knowing you do not know, M6 = acting accordingly"),
]


def pillar_scores(facet_levels):
    """a_i = sum_f beta_{f,i} s_f / sum_f beta_{f,i}."""
    num = [0.0] * 4
    den = [0.0] * 4
    for code, _, _, primary, beta, *_rest in FACETS:
        s = facet_levels[code]
        for k in range(4):
            num[k] += beta[k] * s
            den[k] += beta[k]
    return [num[k] / den[k] if den[k] else 0.0 for k in range(4)]


if __name__ == "__main__":
    assert len(FACETS) == 26
    for f in FACETS:
        assert abs(sum(f[4]) - 1.0) < 1e-9, f"beta of {f[0]} does not sum to 1"
    counts = {}
    for f in FACETS:
        counts[f[3]] = counts.get(f[3], 0) + 1
    payload = {
        "version": "2.0",
        "pillars": list(PILLARS),
        "facets": [
            {"code": c, "label_pt": pt, "label_en": en, "pillar": p,
             "beta": dict(zip(PILLARS, b)), "kind": kind, "guarded": g,
             "theta": th, "rationale": r}
            for c, pt, en, p, b, kind, g, th, r in FACETS
        ],
        "counts_by_pillar": counts,
        "overlaps_resolved": [
            {"a": a, "b": b, "resolution": res} for a, b, res in OVERLAPS
        ],
    }
    with open("facets_v2.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    with open("facets_v2.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "label_pt", "label_en", "pillar", "beta_W", "beta_C",
                    "beta_M", "beta_K", "kind", "guarded", "theta"])
        for c, pt, en, p, b, kind, g, th, _ in FACETS:
            w.writerow([c, pt, en, p, *b, kind, int(g), th])
    print("facets:", len(FACETS), "| by pillar:", counts)
    print("max beta spill-out:", max(min(b) for *_, b, _, _, _, _ in [(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) for f in FACETS]))
    print("wrote facets_v2.json and facets_v2.csv")
