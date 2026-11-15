"""Fact grounding of declared facet levels (P2 fix, gate G6').

The gold panels prohibit on *procedural facts* of the case (no audit trail, no appeal
channel, no notice, no consent). The model's persona profiles declare facet levels that
the case facts contradict, so 75.8% of the model-vs-panel prohibition gap is invisible to
the model (Evaluacoes/r4/corpus_v5_confusion_analysis.json).

Rule: a verifiable fact of the case is an *observation* of the corresponding facet. The
declared level of that facet is capped by the fact:

    ell_f = min(ell_f, q_f * compliance(fact))

with compliance = 1.0 when the duty-relevant fact is present and a fixed shortfall
otherwise. The mapping is declared here and is the only place facts touch the model.

Facets with no fact anchor at all (consent, notice/explainability, human-review channel,
sunset clause, data minimisation) are reported as ontology gaps.

Writes Evaluacoes/r4/fact_grounding_v12.json.
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))

from facet_registry import FACETS                                   # noqa: E402
from core import CaseSpec, Profile, confront, load_fitted_calibration  # noqa: E402
from gold_panels_v5 import adjudicate, cohens_kappa                    # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")

# fact -> (facet, compliance if satisfied, compliance if not)
FACT_MAP = {
    "logs_available":      ("M6", 1.00, 0.25),   # audit trail is the observable of M6
    "independent_audit":   ("M6", 1.00, 0.55),
    "appeal_channel":      ("M7", 1.00, 0.20),   # contestability is part of redress
    "remedy_days":         ("M7", 1.00, 0.20),   # handled specially below
    "containment_exercised": ("C7", 1.00, 0.30),
    "worker_consulted":    ("W3", 1.00, 0.55),
    "prior_incident":      ("C6", 0.70, 1.00),   # an incident in scope lowers safe-executability
    "affected_can_exit":   ("C3", 1.00, 0.50),   # exit is a form of controllability
}
REMEDY_TIERS = ((0, 0.20), (31, 0.50), (999, 0.85))   # days -> compliance factor

UNANCHORED_FACTS = {
    "consent_obtained": ("M1/W3", "consent of affected parties has no facet"),
    "notice_given": ("--", "notice / explainability to the affected party has no facet"),
    "human_review_channel": ("--", "human-in-the-loop review channel has no facet"),
    "sunset_review": ("--", "periodic review / sunset clause has no facet"),
    "data_minimised": ("--", "data minimisation / purpose limitation has no facet"),
    "affected_include_minors": ("--", "protection of minors as a distinct duty has no facet"),
    "affected_people": ("exposure E12'", "scale of those affected enters only through exposure"),
}


def compliance(fact, value):
    if fact == "remedy_days":
        if value == 0:
            return 0.20
        if value > 30:
            return 0.50
        return 0.85
    _facet, satisfied, unsatisfied = FACT_MAP[fact]
    return satisfied if value else unsatisfied


def grounded_levels(case, persona_levels):
    out = dict(persona_levels)
    applied = []
    facts = case.get("facts", {})
    req = case["facet_requirements"]
    for fact, (facet, _s, _u) in FACT_MAP.items():
        if fact not in facts:
            continue
        cap = req[facet] * compliance(fact, facts[fact])
        if out[facet] > cap:
            out[facet] = cap
            applied.append((fact, facet, round(cap, 4)))
    return out, applied


def main():
    cal = load_fitted_calibration()
    cases = []
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        with open(os.path.join(R4, fn)) as fh:
            cases.extend(json.loads(l) for l in fh)
    personas = []
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_personas.jsonl")) as fh:
        personas = [json.loads(l) for l in fh]
    stored_gold = {}
    with open(os.path.join(R4, f"corpus_v{CORPUS_VER}_gold.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            stored_gold[(r["case_id"], r["persona"])] = r["consensus"]

    seq_model, seq_gold, seq_model_old, seq_gold_old, seq_gold_stored = [], [], [], [], []
    dec_new, dec_old = Counter(), Counter()
    aa_new, aa_old = [], []
    applied_counts = Counter()
    cases_with_grounding = 0
    n = 0
    for c in cases:
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                        c["irreversibility"], c["facet_requirements"], c["U_E"], c["R_c"],
                        tuple(c["critical_pillars"]), c["horizon"], c["conflict_pattern"],
                        "system", tuple(c.get("norms", ())),
                        norm_conflict=c.get("norm_conflict", "none"),
                        evidence_conflict=c.get("evidence_conflict", False),
                        exposure=c.get("exposure", 0.5))
        req = c["facet_requirements"]
        touched = False
        for p in personas:
            base = {f.code: min(1.0, req[f.code] *
                                min(0.95, p["factors"].get(f.code, p["default_factor"])
                                    * (1.0 + p["jitter"])))
                    for f in FACETS}
            conf = {f.code: p.get("confidence_mu", 0.85) for f in FACETS}
            levels, applied = grounded_levels(c, base)
            if applied:
                touched = True
                for fact, facet, cap in applied:
                    applied_counts[f"{fact}->{facet}"] += 1
            r_old = confront(spec, Profile(p["profile_id"], base, conf, p["layer"]), cal)
            r_new = confront(spec, Profile(p["profile_id"], levels, conf, p["layer"]), cal)
            g = adjudicate(spec, levels, c.get("facts", {}))["consensus"]
            g_old = adjudicate(spec, base, c.get("facts", {}))["consensus"]
            dec_new_v = r_new["decision"]
            dec_old_v = r_old["decision"]
            seq_model.append(dec_new_v)
            seq_model_old.append(dec_old_v)
            seq_gold.append(g)
            seq_gold_old.append(g_old)
            seq_gold_stored.append(stored_gold.get((c["case_id"], p["profile_id"]), g))
            dec_new[dec_new_v] += 1
            dec_old[dec_old_v] += 1
            aa_new.append(r_new["adequacy"])
            aa_old.append(r_old["adequacy"])
            n += 1
        if touched:
            cases_with_grounding += 1

    out = {
        "pairs": n,
        "cases_with_fact_grounding": cases_with_grounding,
        "fact_to_facet_map": {k: v[0] for k, v in FACT_MAP.items()},
        "unanchored_facts": UNANCHORED_FACTS,
        "grounding_events": dict(applied_counts),
        "without_grounding": {
            "kappa": round(cohens_kappa(seq_model_old, seq_gold_old), 4),
            "agreement": round(sum(1 for a, b in zip(seq_model_old, seq_gold_old) if a == b) / n, 4),
            "decisions": dict(dec_old),
            "mean_adequacy": round(sum(aa_old) / len(aa_old), 4),
        },
        "with_grounding": {
            "kappa": round(cohens_kappa(seq_model, seq_gold), 4),
            "agreement": round(sum(1 for a, b in zip(seq_model, seq_gold) if a == b) / n, 4),
            "decisions": dict(dec_new),
            "mean_adequacy": round(sum(aa_new) / len(aa_new), 4),
        },
        "grounded_model_vs_stored_gold": {
            "kappa": round(cohens_kappa(seq_model, seq_gold_stored), 4),
            "agreement": round(sum(1 for a, b in zip(seq_model, seq_gold_stored) if a == b) / n, 4),
            "share_of_gold_verdicts_changed_by_grounding":
                round(sum(1 for a, b in zip(seq_gold, seq_gold_stored) if a != b) / n, 4),
        },
        "confusion_after": Counter((a, b) for a, b in zip(seq_model, seq_gold)).most_common(10),
        "confusion_before": Counter((a, b) for a, b in zip(seq_model_old, seq_gold_old)).most_common(10),
    }
    with open(os.path.join(R4, "fact_grounding_v12.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: out[k] for k in ("pairs", "cases_with_fact_grounding",
                                         "without_grounding", "with_grounding")}, indent=2))


if __name__ == "__main__":
    main()