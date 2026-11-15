"""G7: model decisions vs the hybrid gold standard (ethcase x WCMK battery, B1-B2).

Compares the model's decision ladder against the panel consensus over the same
declared facts. Two comparisons are reported, because they answer different
questions:

  1. *declared agent* - the profile the scenario was built around. This is the
     semantic test: does the arithmetic reach the verdict the normative
     description of the case supports?
  2. *all 48 personas* - the full confrontation grid. This is the discriminant
     test: does the model still sort agents the way the rubric would, when the
     agent varies while the case is fixed?

Partial credit: adjacent verdicts count 0.5, two steps apart 0.
"""
import json
import os
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r3")
ORDER = ["ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
RANK = {v: i for i, v in enumerate(ORDER)}


def load(path):
    return [json.loads(l) for l in open(path)]


def kappa(a, b):
    n = len(a)
    if n == 0:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    cats = sorted(set(a) | set(b))
    pa = {c: a.count(c) / n for c in cats}
    pb = {c: b.count(c) / n for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats)
    return 1.0 if pe >= 1 - 1e-12 else (po - pe) / (1 - pe)


def partial(a, b):
    return float(np.mean([1.0 if x == y else (0.5 if abs(RANK[x] - RANK[y]) == 1 else 0.0)
                         for x, y in zip(a, b)]))


def confusion(a, b):
    m = {}
    for x, y in zip(a, b):
        m[(x, y)] = m.get((x, y), 0) + 1
    return {f"{x} -> {y}": v for (x, y), v in sorted(m.items(), key=lambda kv: -kv[1])}


def spearman(x, y):
    def rank(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = np.mean(rx), np.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = np.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return float(num / den) if den else 0.0


def main():
    conf = load(os.path.join(OUT, "corpus_v4_confrontations.jsonl"))
    spread = {g["case_id"]: g["spread"] for g in load(os.path.join(OUT, "corpus_v4_gold.jsonl"))}
    for c in conf:
        c["clear_case"] = spread.get(c["case_id"], 0) == 0
    declared = [c for c in conf if c["persona"] == "declared"]
    others = [c for c in conf if c["persona"] != "declared"]

    dec_d = [c["decision"] for c in declared]
    gold_d = [c["gold"] for c in declared]
    dec_o = [c["decision"] for c in others]
    gold_o = [c["gold"] for c in others]

    clear = [c for c in declared if c["clear_case"]]
    contested = [c for c in declared if not c["clear_case"]]

    # adequacy vs rubric severity: does the numeric scale track the verdict rank?
    aa = [c["adequacy"] for c in declared]
    gold_rank = [RANK[g] for g in gold_d]

    result = {
        "declared_agent": {
            "n": len(declared),
            "kappa_model_vs_gold": round(kappa(dec_d, gold_d), 4),
            "partial_credit_accuracy": round(partial(dec_d, gold_d), 4),
            "exact_match_rate": round(float(np.mean(np.array(dec_d) == np.array(gold_d))), 4),
            "confusion": confusion(dec_d, gold_d),
            "spearman_adequacy_vs_gold_rank": round(spearman(aa, gold_rank), 4),
        },
        "clear_cases_only": {
            "n": len(clear),
            "kappa": round(kappa([c["decision"] for c in clear], [c["gold"] for c in clear]), 4),
            "exact_match_rate": round(float(np.mean(np.array([c["decision"] for c in clear])
                                                   == np.array([c["gold"] for c in clear]))), 4),
        },
        "contested_cases": {
            "n": len(contested),
            "kappa": round(kappa([c["decision"] for c in contested], [c["gold"] for c in contested]), 4),
            "model_stricter_share": round(float(np.mean(np.array([RANK[c["decision"]] - RANK[c["gold"]] for c in contested]) < 0)), 4),
        },
        "full_grid_48_personas": {
            "n": len(others),
            "kappa_model_vs_gold": round(kappa(dec_o, gold_o), 4),
            "partial_credit_accuracy": round(partial(dec_o, gold_o), 4),
            "mean_decision_rank_model": float(np.mean([RANK[d] for d in dec_o])),
            "mean_decision_rank_gold": float(np.mean([RANK[g] for g in gold_o])),
            "stricter_than_gold_rate": round(float(np.mean(np.array([RANK[d] - RANK[g] for d, g in zip(dec_o, gold_o)]) < 0)), 4),
            "looser_than_gold_rate": round(float(np.mean(np.array([RANK[d] - RANK[g] for d, g in zip(dec_o, gold_o)]) > 0)), 4),
        },
        "by_archetype": {},
        "by_domain": {},
        "target": {"kappa_declared_agent": 0.60, "spearman_adequacy_vs_gold": 0.80},
    }

    by_arch = defaultdict(lambda: ([], []))
    for c in declared:
        by_arch[c["design_intent"]][0].append(c["decision"])
        by_arch[c["design_intent"]][1].append(c["gold"])
    for k, (a, b) in by_arch.items():
        result["by_archetype"][k] = {"n": len(a), "kappa": round(kappa(a, b), 4),
                                     "exact": round(float(np.mean(np.array(a) == np.array(b))), 4)}
    for c in declared:
        result["by_domain"].setdefault(c["domain"], []).append((c["decision"], c["gold"]))
    result["by_domain"] = {d: {"n": len(v), "exact": round(float(np.mean([a == g for a, g in v])), 4)}
                           for d, v in result["by_domain"].items()}

    print(json.dumps(result, indent=2))
    with open(os.path.join(OUT, "B1_model_vs_gold.json"), "w") as fh:
        json.dump(result, fh, indent=2)


if __name__ == "__main__":
    main()
