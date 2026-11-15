"""Supplementary analyses for the F5 batteries (continuous validity + robustness).

Adds to B5/B6:
  * Spearman correlation between the continuous adequacy score and the
    continuous statistics each panel uses internally (weighted shortfall for
    Panel B, number of critical gaps for Panel A). This tests whether the model
    orders cases the same way the panels do, independently of the discrete label.
  * Decision-band sensitivity: how many test cases sit within 0.05 of a
    decision boundary, and how stability changes with perturbation size.
Output: Evaluacoes/r2/B9_supplementary.json
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "corpus")))

from facet_registry import FACETS, BY_CODE
from core import default_calibration, CaseSpec, Profile, confront
from gold_panels import _gaps, RANK

R2 = os.path.abspath(os.path.join(HERE, "..", "..", "Evaluacoes", "r2"))
CAL = default_calibration()
SEED = 20261031


def load(name):
    with open(os.path.join(R2, name)) as fh:
        return [json.loads(line) for line in fh]


CASES = load("corpus_v3_cases.jsonl")
PROFILES = load("corpus_v3_profiles.jsonl")
GOLD = load("corpus_v3_gold.jsonl")
CASE_BY_ID = {c["case_id"]: c for c in CASES}
PROF_BY_ID = {p["profile_id"]: Profile(p["profile_id"], p["levels"], p["confidence"])
             for p in PROFILES}
SEV = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.00}
IRR = {"reversible": 0.0, "partially_irreversible": 0.5, "irreversible": 1.0}
PRU = {"standard": 0.0, "elevated": 0.05, "maximum": 0.10}


def spearman(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den if den else 0.0


def panel_continuous_stats(case, levels):
    g = _gaps(case, levels)
    wsum = 0.0
    short = 0.0
    n_critical_gaps = 0
    max_gap = 0.0
    for code, gap in g.items():
        w = BY_CODE[code].criticality.get(case.domain, 2)
        wsum += w
        short += w * gap
        if w == 4 and gap > 0.25:
            n_critical_gaps += 1
        max_gap = max(max_gap, gap)
    return short / max(wsum, 1.0), n_critical_gaps, max_gap


def main():
    adequacy, short_b, gaps_a, max_gap = [], [], [], []
    for gse in GOLD:
        c = CASE_BY_ID[gse["case_id"]]
        pr = PROF_BY_ID[gse["profile_id"]]
        sp = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                      c["irreversibility"], c["requirements"],
                      c["epistemic_uncertainty"], c["contextual_risk"],
                      tuple(c["critical_pillars"]))
        res = confront(sp, pr, CAL)
        s, ncr, mg = panel_continuous_stats(sp, pr.facet_scores)
        adequacy.append(res["adequacy"])
        short_b.append(s)
        gaps_a.append(ncr)
        max_gap.append(mg)
    out = {
        "n_pairs": len(adequacy),
        "spearman_adequacy_vs_panelB_shortfall": round(spearman(adequacy, short_b), 4),
        "spearman_adequacy_vs_panelA_critical_gap_count": round(spearman(adequacy, gaps_a), 4),
        "spearman_adequacy_vs_max_facet_gap": round(spearman(adequacy, max_gap), 4),
    }

    # boundary-proximity analysis: how close are cases to a decision threshold
    test_specs = [CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                           c["irreversibility"], c["requirements"],
                           c["epistemic_uncertainty"], c["contextual_risk"],
                           tuple(c["critical_pillars"])) for c in CASES[:400]]
    margins = []
    for sp in test_specs:
        for pr in PROF_BY_ID.values():
            r = confront(sp, pr, CAL)
            if r["adequacy"] is None:
                continue
            bar = CAL.decision_bar(sp)
            margins.append(min(abs(r["adequacy"] - bar),
                              abs(r["adequacy"] - (bar - CAL.prohibit_margin)),
                              abs(r["adequacy"] - (bar + CAL.guards_margin))))
    margins = np.array(margins)
    out["n_confrontations_boundary_analysis"] = int(len(margins))
    out["share_within_0.05_of_a_boundary"] = round(float(np.mean(margins < 0.05)), 4)
    out["share_within_0.10_of_a_boundary"] = round(float(np.mean(margins < 0.10)), 4)
    out["median_distance_to_nearest_boundary"] = round(float(np.median(margins)), 4)

    # perturbation-size sweep for ordinal stability
    stability = {}
    for step in (0.02, 0.05, 0.10, 0.15):
        rng = np.random.default_rng(SEED)
        flips = 0
        total = 0
        rank_changes = []
        for sp in test_specs[:200]:
            for pr in list(PROF_BY_ID.values())[:12]:
                noisy = {f.code: max(0.0, min(1.0, pr.facet_scores[f.code]
                                             + rng.normal(0, step))) for f in FACETS}
                a = confront(sp, pr, CAL)
                b = confront(sp, Profile(pr.profile_id, noisy, pr.confidence), CAL)
                total += 1
                if a["decision"] != b["decision"]:
                    flips += 1
                rank_changes.append(abs(RANK[a["decision"]] - RANK[b["decision"]]))
        stability[f"sd_{step}"] = {"decision_stability": round(1 - flips / total, 4),
                                   "mean_abs_rank_change": round(float(np.mean(rank_changes)), 4)}
    out["noise_stability_by_sd"] = stability
    with open(os.path.join(R2, "B9_supplementary.json"), "w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
