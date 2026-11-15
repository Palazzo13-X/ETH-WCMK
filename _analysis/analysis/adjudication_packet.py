"""G7' support material (Rodada 5) - the human adjudication packet.

The corpus's ground truth is a rubric operated by three normative panels, not people.
That is a legitimate design, but it caps how far Cohen's kappa can go: the panels share
a kernel, and the residual disagreement is structural (D4.32, G7'). To break that ceiling
a human adjudication of a stratified sample is required. This script produces the
instrument; it does not produce the verdicts.

Two files are emitted:
  * adjudication_packet_blind.csv - what the rater sees. The model verdict and the panel
    consensus are deliberately absent: presenting them first would anchor the rater and
    inflate kappa against the model.
  * adjudication_packet_key.csv   - the same rows with the model verdict, each panel's
    verdict, coverage and ReviewNeed, for computing kappa after the raters answer.

Raters answer with one of the five verdicts plus a rationale code from the canon:
  H1 hard-guard breach, H2 irreversible harm with insufficient safeguards,
  H3 procedural deficit (notice/consent/remedy), H4 knowledge or evidence gap,
  H5 proportionality (the stakes do not justify prohibition), H6 reversible and
  adequately safeguarded.

Run:  python3 _analysis/analysis/adjudication_packet.py
"""
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "corpus"))

from facet_registry import FACETS                                     # noqa: E402
from core import confront, Profile, load_fitted_calibration            # noqa: E402
from gold_panels_v5 import adjudicate, profile_coverage               # noqa: E402
from gen_corpus_v5 import case_spec                                          # noqa: E402

R5 = os.path.join(ROOT, "Evaluacoes", "r" + os.environ.get("ETH_WCMK_ROUND", "5"))

VERDICTS = ["PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW", "ABSTAIN"]
RATIONALES = ["H1", "H2", "H3", "H4", "H5", "H6"]

BLIND_COLS = ["case_id", "domain", "severity", "irreversibility", "horizon",
              "prudential", "conflict_pattern", "norm_conflict", "evidence_conflict",
              "norms", "facts", "coverage_of_declared_profile", "narrative",
              "rater_1_verdict", "rater_1_rationale", "rater_1_confidence",
              "rater_2_verdict", "rater_2_rationale", "rater_2_confidence",
              "rater_3_verdict", "rater_3_rationale", "rater_3_confidence"]


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    cal = load_fitted_calibration()
    audit_ids = []
    with open(os.path.join(R5, "corpus_v7_audit_sample.csv")) as fh:
        for row in csv.DictReader(fh):
            audit_ids.append(row["case_id"])

    cases = {}
    for name in ("corpus_v7_layerA.jsonl", "corpus_v7_layerB.jsonl"):
        for c in read_jsonl(os.path.join(R5, name)):
            cases[c["case_id"]] = c

    blind, key = [], []
    for cid in audit_ids:
        c = cases[cid]
        levels = c["declared_levels"]
        conf = c["declared_confidence"]
        cov = round(profile_coverage(levels), 4)
        spec = case_spec(c)
        r = confront(spec, Profile("AGENT-declared", levels, conf, "system"), cal)
        g = adjudicate(spec, levels, c["facts"])
        blind.append({
            "case_id": cid, "domain": c["domain"], "severity": c["severity"],
            "irreversibility": c["irreversibility"], "horizon": c["horizon"],
            "prudential": c["prudential"], "conflict_pattern": c["conflict_pattern"],
            "norm_conflict": c["norm_conflict"], "evidence_conflict": c["evidence_conflict"],
            "norms": "; ".join(c["norms"]),
            "facts": json.dumps(c["facts"], sort_keys=True),
            "coverage_of_declared_profile": cov,
            "narrative": c.get("narrative") or " | ".join(
                str(c.get(k, "")) for k in ("scenario", "objective", "consequence",
                                           "resource", "review_body", "ambiguity")),
            "rater_1_verdict": "", "rater_1_rationale": "", "rater_1_confidence": "",
            "rater_2_verdict": "", "rater_2_rationale": "", "rater_2_confidence": "",
            "rater_3_verdict": "", "rater_3_rationale": "", "rater_3_confidence": "",
        })
        key.append({
            "case_id": cid, "model_verdict": r["decision"],
            "model_adequacy": r.get("adequacy"), "model_review_need": r.get("review_need"),
            "coverage": cov,
            "panel_A": g["panelA"], "panel_B": g["panelB"], "panel_C": g["panelC"],
            "consensus": g["consensus"], "unanimous": g["unanimous"],
            "kernel_only": g["kernel_only"], "rules_applied": "; ".join(g["rules_applied"]),
        })

    with open(os.path.join(R5, "adjudication_packet_blind.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=BLIND_COLS)
        w.writeheader()
        w.writerows(blind)
    with open(os.path.join(R5, "adjudication_packet_key.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(key[0].keys()))
        w.writeheader()
        w.writerows(key)

    print(json.dumps({"rows": len(blind),
                      "verdict_composition_of_model": {},
                      "model_verdicts": {k: sum(1 for x in key if x["model_verdict"] == k)
                                        for k in VERDICTS},
                      "panel_consensus": {k: sum(1 for x in key if x["consensus"] == k)
                                         for k in VERDICTS},
                      "coverage_min": min(x["coverage"] for x in key),
                      "coverage_max": max(x["coverage"] for x in key)}, indent=2))


if __name__ == "__main__":
    main()
