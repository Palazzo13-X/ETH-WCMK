"""κ por estrato de consenso normativo, corpus v7 (canon β v13).

Reads `corpus_v7_confrontations.jsonl` and reports Cohen's κ between the model's
verdict and the panel consensus inside three strata: unanimous (three panels agree),
majority (two agree), contested (all three differ). Written so the paper can quote
stratified κ from an artefact rather than from prose (D4.32).

Run:  python3 _analysis/analysis/kappa_by_stratum.py
Out:  Evaluacoes/r5/kappa_by_stratum_v13.json
"""
import json
import os
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
R5 = os.path.join(ROOT, "Evaluacoes", "r5")

ORDER = ["PROHIBIT", "ABSTAIN", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW"]
RANK = {v: i for i, v in enumerate(ORDER)}  # most restrictive first


def cohen(pairs):
    """pairs: list of (a, b) categorical labels."""
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    idx = {c: i for i, c in enumerate(cats)}
    n = len(pairs)
    M = [[0] * len(cats) for _ in range(len(cats))]
    ra = [0] * len(cats)
    rb = [0] * len(cats)
    for a, b in pairs:
        M[idx[a]][idx[b]] += 1
        ra[idx[a]] += 1
        rb[idx[b]] += 1
    po = sum(M[i][i] for i in range(len(cats))) / n
    pe = sum(ra[i] * rb[i] for i in range(len(cats))) / (n * n)
    if pe >= 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1.0 - pe)


def stratum(panels):
    if isinstance(panels, dict):
        vals = [panels.get(k) for k in ("A", "B", "C")]
    else:
        vals = list(panels)
    vals = [v for v in vals if v]
    if len(vals) != 3:
        return "incomplete_panel"
    if len(set(vals)) == 1:
        return "unanimous"
    if Counter(vals).most_common(1)[0][1] == 2:
        return "majority"
    return "contested"


def main():
    by_stratum = {}
    by_domain = {}
    by_coverage = {}
    overall = []
    spread_hist = Counter()
    for line in open(os.path.join(R5, "corpus_v7_confrontations.jsonl")):
        r = json.loads(line)
        panels = r.get("gold_panels") or {}
        s = stratum(panels)
        model = r.get("decision")
        gold = r.get("gold_consensus")
        if model is None or gold is None:
            continue
        overall.append((model, gold))
        by_stratum.setdefault(s, []).append((model, gold))
        by_domain.setdefault(r.get("domain", "?"), []).append((model, gold))
        cov = r.get("completeness")
        key = "full_canon_33" if cov == 1.0 else ("below_gate" if (cov or 0) < 0.70 else "partial")
        by_coverage.setdefault(key, []).append((model, gold))
        pv = panels if isinstance(panels, list) else list(panels.values())
        ranks = [RANK[v] for v in pv if v in RANK]
        if ranks:
            spread_hist[max(ranks) - min(ranks)] += 1

    out = {
        "battery": "B16_kappa_by_stratum",
        "question": "How much of the model-panel disagreement is the disagreement between the normative lenses themselves?",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Evaluacoes/r5/corpus_v7_confrontations.jsonl (corpus v7, canonical beta of v13)",
        "pairs": len(overall),
        "kappa_model_vs_consensus_overall": round(cohen(overall), 4),
        "by_domain": {d: {"pairs": len(p),
                        "kappa_model_vs_consensus": round(cohen(p), 4)}
                      for d, p in sorted(by_domain.items(), key=lambda kv: -cohen(kv[1]))},
        "by_coverage": {d: {"pairs": len(p),
                            "kappa_model_vs_consensus": round(cohen(p), 4)}
                        for d, p in sorted(by_coverage.items(), key=lambda kv: -cohen(kv[1]))},
        "by_stratum": {s: {"pairs": len(p),
                           "kappa_model_vs_consensus": round(cohen(p), 4),
                           "exact_agreement": round(sum(a == b for a, b in p) / len(p), 4)}
                        for s, p in sorted(by_stratum.items(), key=lambda kv: -len(kv[1]))},
        "panel_spread_histogram_ranks": dict(spread_hist),
        "reading": ("κ no estrato unânime é o número que o modelo pode defender sem disputa normativa; "
                    "no estrato contestado, la divergencia es la de las lentes, no la del modelo."),
    }
    json.dump(out, open(os.path.join(R5, "kappa_by_stratum_v13.json"), "w"), indent=1)
    print(json.dumps(out, indent=1)[:1200])


if __name__ == "__main__":
    main()
