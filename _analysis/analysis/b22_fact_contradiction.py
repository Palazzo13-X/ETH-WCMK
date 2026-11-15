"""B22 (Rodada 5, gate G13') - can a declared level survive a contradictory fact?

E30 says: a verifiable fact caps the level a facet may claim,  ell_f = min(ell_f, q_f * c(fact)).
D4.21 introduced the rule; D5.9 (E26') fixed its interaction with incomplete profiles.
This battery measures the *bite* of the rule instead of asserting it:

  1. how many (case, persona) pairs contain a declaration that contradicts a declared fact;
  2. by how much the declaration is over the cap, facet by facet;
  3. what the model decides with the cap (strength 1) and without it (strength 0, the v11
     behaviour), and how many verdicts flip;
  4. how agreement with the normative panels changes: kappa with E30 vs kappa without it.

Run:  python3 _analysis/analysis/b22_fact_contradiction.py --cases 300 --seed 7
Writes Evaluacoes/r5/B22_fact_contradiction.json
"""
import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "corpus"))

from core import CaseSpec, Profile, confront, requirement_for, load_fitted_calibration  # noqa: E402
from facet_registry import FACETS                                                        # noqa: E402
from fact_grounding import FACT_MAP, grounded_levels, fact_compliance                    # noqa: E402
from gold_panels_v5 import adjudicate, cohens_kappa                                      # noqa: E402
from gen_corpus_v5 import delivery, case_spec                                                          # noqa: E402

R5 = os.path.join(ROOT, "Evaluacoes", "r" + os.environ.get("ETH_WCMK_ROUND", "5"))
DELIVERED_CAP = 0.95


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def stratified(rows, n, rng):
    by = defaultdict(list)
    for r in rows:
        by[(r["domain"], r["layer"])].append(r)
    out, per = [], max(1, n // len(by))
    for k in sorted(by):
        pool = by[k]
        take = min(len(pool), per + (1 if rng.random() < 0.5 else 0))
        idx = rng.choice(len(pool), size=take, replace=False)
        out.extend(pool[int(i)] for i in idx)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(R5, "B22_fact_contradiction.json"))
    args = ap.parse_args()
    rng = __import__("numpy").random.default_rng(args.seed)
    cal = load_fitted_calibration()

    cases = list(read_jsonl(os.path.join(R5, "corpus_v7_layerA.jsonl"))) + \
            list(read_jsonl(os.path.join(R5, "corpus_v7_layerB.jsonl")))
    cases = stratified(cases, args.cases, rng)
    personas = {p["profile_id"]: p for p in read_jsonl(os.path.join(R5, "corpus_v7_personas.jsonl"))}
    wanted = {c["case_id"] for c in cases}
    rows_by_case = defaultdict(list)
    conf_map = {}
    for row in read_jsonl(os.path.join(R5, "corpus_v7_confrontations.jsonl")):
        if row["case_id"] in wanted:
            rows_by_case[row["case_id"]].append(row)
            cf = row.get("facet_confidence")
            conf_map[(row["case_id"], row["persona"])] = (
                dict(zip((f.code for f in FACETS), cf)) if isinstance(cf, list) else (cf or {}))

    pairs = 0
    contradictions = 0
    excess_by_fact = defaultdict(list)
    excess_by_facet = defaultdict(list)
    flips = Counter()
    flip_examples = []
    aa_with, aa_without = [], []
    model_with, model_without, gold_labels = [], [], []

    t0 = time.time()
    for raw in cases:
        reqs = raw["facet_requirements"]
        case = case_spec(raw)
        for row in rows_by_case[raw["case_id"]]:
            persona = personas.get(row["persona"])
            if row["persona"] == "AGENT-declared":
                declared = dict(raw["declared_levels"])
            else:
                declared = {f.code: delivery(f, persona, reqs)
                            for f in FACETS if f.code not in persona.get("omit", ())}
            grounded, applied = grounded_levels(raw["facts"], reqs, declared, 1.0)
            ungrounded, _ = grounded_levels(raw["facts"], reqs, declared, 0.0)
            conf = conf_map[(raw["case_id"], row["persona"])]
            pairs += 1
            if applied:
                contradictions += 1
            for fact, code, cap in applied:
                excess_by_fact[fact].append(round(declared[code] - cap, 4))
                excess_by_facet[code].append(round(declared[code] - cap, 4))
            r_with = confront(case, Profile(row["persona"], grounded, conf,
                                           row.get("agent_layer", "system")), cal, FACETS)
            r_without = confront(case, Profile(row["persona"], ungrounded, conf,
                                              row.get("agent_layer", "system")), cal, FACETS)
            flips[(r_without["decision"], r_with["decision"])] += 1
            if r_without["decision"] != r_with["decision"] and len(flip_examples) < 8:
                flip_examples.append  # noqa
            if r_without["decision"] != r_with["decision"] and len(flip_examples) < 8:
                flip_examples.append({"case": raw["case_id"], "persona": row["persona"],
                                      "facts": {f: raw["facts"][f] for f, _, _ in applied},
                                      "without_E30": r_without["decision"],
                                      "with_E30": r_with["decision"],
                                      "aa_without": r_without.get("adequacy"),
                                      "aa_with": r_with.get("adequacy")})
            if r_with.get("adequacy") is not None:
                aa_with.append(r_with["adequacy"])
            if r_without.get("adequacy") is not None:
                aa_without.append(r_without["adequacy"])
            gold = adjudicate(case, grounded, raw["facts"])["consensus"]
            model_with.append(r_with["decision"])
            model_without.append(r_without["decision"])
            gold_labels.append(gold)

    out = {
        "battery": "B22",
        "question": "does a declared level survive a fact that contradicts it?",
        "n_pairs": pairs,
        "n_pairs_with_contradiction": contradictions,
        "share_pairs_with_contradiction": round(contradictions / pairs, 4),
        "caps_applied_total": sum(len(v) for v in excess_by_fact.values()),
        "mean_excess_over_cap": round(sum(sum(v) for v in excess_by_fact.values())
                                      / max(1, sum(len(v) for v in excess_by_fact.values())), 4),
        "by_fact": {f: {"count": len(v), "mean_excess": round(sum(v) / len(v), 4),
                        "max_excess": max(v)} for f, v in sorted(excess_by_fact.items())},
        "by_facet": {c: {"count": len(v), "mean_excess": round(sum(v) / len(v), 4)}
                     for c, v in sorted(excess_by_facet.items())},
        "verdict_flips": {f"{a}->{b}": n for (a, b), n in sorted(flips.items(),
                                                                key=lambda x: -x[1])},
        "n_verdict_flips": sum(v for (a, b), v in flips.items() if a != b),
        "flip_share": round(sum(v for (a, b), v in flips.items() if a != b) / pairs, 4),
        "mean_adequacy_with_E30": round(sum(aa_with) / len(aa_with), 4),
        "mean_adequacy_without_E30": round(sum(aa_without) / len(aa_without), 4),
        "kappa_with_E30": round(cohens_kappa(model_with, gold_labels), 4),
        "kappa_without_E30": round(cohens_kappa(model_without, gold_labels), 4),
        "delta_kappa_E30": round(cohens_kappa(model_with, gold_labels)
                                 - cohens_kappa(model_without, gold_labels), 4),
        "flip_examples": flip_examples,
        "runtime_seconds": round(time.time() - t0, 2),
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k not in ("by_fact", "by_facet",
                                                                "flip_examples")}, indent=2))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
