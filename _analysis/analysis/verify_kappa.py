"""Verify the kappa numbers reported by the corpus generator.

The coverage report in corpus_v5_coverage.json states kappa(model, gold) = -0.4823.
That is suspicious: agreement is 0.473 and the marginals are skewed in the same
direction, which cannot give a negative Cohen kappa. This script recomputes it
directly from the stored rows and reports the three pairwise kappas (model vs gold,
gold vs design intent, model vs design intent) plus the confusion matrix, so we
know which number is real.
"""
import json
from collections import Counter

R4 = "/home/luiz/Documentos/Strata/Shared/Evaluacoes/r4"
CLASSES = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")
IDX = {c: i for i, c in enumerate(CLASSES)}


def kappa(pairs):
    n = len(pairs)
    m = [[0] * len(CLASSES) for _ in range(len(CLASSES))]
    for a, b in pairs:
        if a in IDX and b in IDX:
            m[IDX[a]][IDX[b]] += 1
    tot = sum(sum(r) for r in m)
    if tot == 0:
        return float("nan")
    obs = sum(m[i][i] for i in range(len(CLASSES))) / tot
    row = [sum(m[i]) / tot for i in range(len(CLASSES))]
    col = [sum(m[i][j] for i in range(len(CLASSES))) / tot for j in range(len(CLASSES))]
    exp = sum(r * c for r, c in zip(row, col))
    return (obs - exp) / (1 - exp) if 1 - exp > 1e-12 else 0.0


def main():
    mg, gm, md = [], [], []
    cm = Counter()
    dist_model, dist_gold, dist_intent = Counter(), Counter(), Counter()
    n = 0
    with open(R4 + "/corpus_v5_confrontations.jsonl") as fh:
        for line in fh:
            r = json.loads(line)
            dec, gold, intent = r["decision"], r.get("gold_consensus"), r.get("design_intent")
            if gold is None:
                continue
            n += 1
            mg.append((dec, gold))
            gm.append((gold, intent))
            md.append((dec, intent))
            dist_model[dec] += 1
            dist_gold[gold] += 1
            dist_intent[intent] += 1
            cm[(dec, gold)] += 1
    print(f"rows={n}")
    print("kappa(model, gold)      =", round(kappa(mg), 4), " agreement =",
          round(sum(1 for a, b in mg if a == b) / n, 4))
    print("kappa(gold, intent)     =", round(kappa(gm), 4))
    print("kappa(model, intent)    =", round(kappa(md), 4))
    print("marginals model:", dict(dist_model))
    print("marginals gold :", dict(dist_gold))
    print("marginals intent:", dict(dist_intent))
    print("top confusion:")
    for (a, b), v in sorted(cm.items(), key=lambda x: -x[1])[:12]:
        print(f"  {a:18} vs {b:18} {v}")


if __name__ == "__main__":
    main()
