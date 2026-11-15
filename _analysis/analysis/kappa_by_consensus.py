"""Where does the model disagree with the normative panel, and is that disagreement
noise or a property of the corpus?

Splits the 183,920 (case x persona) pairs by how settled the panel consensus is:
  - UNANIMOUS: panels A, B and C gave the same verdict.
  - MAJORITY:  two of three agreed.
  - CONTESTED: all three differ.
Computes kappa, agreement and the confusion matrix in each stratum, plus kappa by
domain, conflict pattern and severity. No model recomputation: it uses the verdicts
already stored in corpus_v5_confrontations.jsonl.

Writes Evaluacoes/r4/kappa_by_consensus.json.
"""
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
CLASSES = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")
IDX = {c: i for i, c in enumerate(CLASSES)}
BAND3 = {"ALLOW": "PERMISSIVE", "ALLOW_WITH_GUARDS": "CONDITIONAL",
         "REVIEW_REQUIRED": "CONDITIONAL", "PROHIBIT": "PROHIBITIVE",
         "ABSTAIN": "CONDITIONAL"}
B3 = ("PERMISSIVE", "CONDITIONAL", "PROHIBITIVE")
B3I = {c: i for i, c in enumerate(B3)}


def kappa(pairs, classes):
    idx = {c: i for i, c in enumerate(classes)}
    n = len(pairs)
    if n < 2:
        return None
    m = [[0] * len(classes) for _ in classes]
    for a, b in pairs:
        if a in idx and b in idx:
            m[idx[a]][idx[b]] += 1
    po = sum(m[i][i] for i in range(len(classes))) / n
    row = [sum(r) / n for r in m]
    col = [sum(m[i][j] for i in range(len(classes))) for j in range(len(classes))]
    col = [c / n for c in col]
    pe = sum(r * c for r, c in zip(row, col))
    if 1 - pe <= 1e-12:
        return 0.0
    return (po - pe) / (1 - pe)


def dist(pairs, side, classes):
    return dict(Counter(p[1 if side == "gold" else 0] for p in pairs))


def confusion(pairs):
    return {f"{a}->{b}": c for (a, b), c in
            Counter((a, b) for a, b in pairs).most_common(12)}


def main():
    rows = 0
    strata = defaultdict(list)
    by_domain = defaultdict(list)
    by_pattern = defaultdict(list)
    by_severity = defaultdict(list)
    by_horizon = defaultdict(list)
    by_layer = defaultdict(list)
    panel_pairs = {"A": [], "B": [], "C": []}
    panel_vs_consensus = {"A": [], "B": [], "C": []}
    unanimity = Counter()
    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        dec, gold = r["decision"], r["gold_consensus"]
        panels = r.get("gold_panels") or []
        if dec is None or gold is None:
            continue
        rows += 1
        vals = [p for p in panels if p]
        if len(set(vals)) == 1:
            stratum = "unanimous"
        elif len(set(vals)) == 2:
            stratum = "majority"
        else:
            stratum = "contested"
        unanimity[stratum] += 1
        strata[stratum].append((dec, gold))
        by_domain[r["domain"]].append((dec, gold))
        by_pattern[r.get("conflict_pattern", "none")].append((dec, gold))
        by_severity[r["severity"]].append((dec, gold))
        by_horizon[r.get("horizon", "immediate")].append((dec, gold))
        by_layer[r.get("layer", "A")].append((dec, gold))
        for i, label in enumerate(("A", "B", "C")):
            if i < len(panels) and panels[i]:
                panel_pairs[label].append(panels[i])
                panel_vs_consensus[label].append((panels[i], gold))

    out = {"pairs": rows, "panel_unanimity": dict(unanimity), "strata": {}}
    for name, pairs in strata.items():
        out["strata"][name] = {
            "n": len(pairs),
            "share": round(len(pairs) / rows, 4),
            "kappa_5class": round(kappa(pairs, CLASSES), 4),
            "kappa_3band": round(kappa([(BAND3[a], BAND3[b]) for a, b in pairs], B3), 4),
            "agreement": round(sum(1 for a, b in pairs if a == b) / len(pairs), 4),
            "gold_marginal": dist(pairs, "gold", CLASSES),
            "model_marginal": dist(pairs, "model", CLASSES),
            "top_confusions": confusion(pairs),
        }
    out["by_domain"] = {d: {"n": len(p), "kappa": round(kappa(p, CLASSES) or 0, 4),
                            "agreement": round(sum(1 for a, b in p if a == b) / len(p), 4)}
                        for d, p in sorted(by_domain.items())}
    out["by_conflict_pattern"] = {d: {"n": len(p), "kappa": round(kappa(p, CLASSES) or 0, 4)}
                                  for d, p in sorted(by_pattern.items())}
    out["by_severity"] = {d: {"n": len(p), "kappa": round(kappa(p, CLASSES) or 0, 4)}
                          for d, p in sorted(by_severity.items(), key=lambda x: -len(x[1]))}
    out["by_horizon"] = {d: {"n": len(p), "kappa": round(kappa(p, CLASSES) or 0, 4)}
                         for d, p in sorted(by_horizon.items())}
    out["by_layer"] = {d: {"n": len(p), "kappa": round(kappa(p, CLASSES) or 0, 4)}
                       for d, p in by_layer.items()}
    out["panel_vs_own_consensus"] = {k: round(kappa(v, CLASSES), 4) for k, v in panel_vs_consensus.items()}
    out["panel_pairwise_agreement"] = {
        f"{a}-{b}": round(sum(1 for x, y in zip(panel_pairs[a], panel_pairs[b]) if x == y) / len(panel_pairs[a]), 4)
        for a, b in (("A", "B"), ("A", "C"), ("B", "C"))}
    out["panel_pairwise_kappa"] = {}
    ks = list(panel_pairs)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            pairs = list(zip(panel_pairs[ks[i]], panel_pairs[ks[j]]))
            out["panel_pairwise_kappa"][f"{ks[i]}-{ks[j]}"] = round(kappa(pairs, CLASSES), 4)
    with open(os.path.join(R4, "kappa_by_consensus.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: out[k] for k in ("pairs", "panel_unanimity", "strata",
                                         "panel_pairwise_kappa")}, indent=2)[:2500])


if __name__ == "__main__":
    main()