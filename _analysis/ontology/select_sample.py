#!/usr/bin/env python3
"""Stratified sample of confrontations for the ontology instance graph (decision D9).

The corpus has 183,920 confrontations; instantiating all of them would make a
1.7 GB graph that nothing can validate. The sample instantiates:

  * every case (1,520) and its E30 grounding facts,
  * every persona (120) at least once,
  * the declared profile of every case,
  * one persona confrontation per case chosen by a deterministic rotation, so the
    120 personas and all persona archetypes are spread evenly over the corpus,
  * plus every missing stratum (domain, persona archetype, case archetype, layer,
    conflict pattern, decision class).

Deterministic: no random seed involved. Writes sample_selection.json.
"""
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_selection.json")
STRATA = ("persona", "ptype", "domain", "kind", "layer", "pattern", "decision")


def conf_id(case_id, persona):
    return "CONF_" + case_id + "_" + persona.replace("-", "_")


def main():
    pattern = {}
    for name in ("corpus_v6_layerA.jsonl", "corpus_v6_layerB.jsonl"):
        with open(os.path.join(R4, name)) as fh:
            for line in fh:
                r = json.loads(line)
                pattern[r["case_id"]] = r.get("conflict_pattern") or "none"

    personas = [json.loads(line)["profile_id"]
                for line in open(os.path.join(R4, "corpus_v6_personas.jsonl"))]

    rows = {}
    case_rows = defaultdict(list)
    for line in open(os.path.join(R4, "corpus_v6_confrontations.jsonl")):
        r = json.loads(line)
        rid = conf_id(r["case_id"], r["persona"])
        rec = {"id": rid, "case": r["case_id"], "persona": r["persona"],
               "domain": r["domain"], "ptype": r["persona_type"], "kind": r["kind"],
               "layer": r["layer"], "decision": r["decision"],
               "pattern": pattern.get(r["case_id"], "none")}
        rows[rid] = rec
        case_rows[r["case_id"]].append(rec)

    chosen = set()
    # one persona confrontation per case, rotating through the 120 personas
    for i, case in enumerate(sorted(case_rows)):
        chosen.add(conf_id(case, personas[(i * 7 + 3) % len(personas)]))
        chosen.add(conf_id(case, "AGENT-declared"))

    by = defaultdict(lambda: defaultdict(list))
    for rec in rows.values():
        for key in STRATA:
            by[key][rec[key]].append(rec)
    covered = {key: set() for key in STRATA}
    for rec in (rows[c] for c in chosen):
        for key in STRATA:
            covered[key].add(rec[key])

    # coverage pass: add the rarest uncovered stratum members first
    for key in sorted(by, key=lambda k: len(by[k])):
        for value in sorted(by[key], key=lambda v: (len(by[key][v]), v)):
            if value in covered[key]:
                continue
            cands = [r for r in by[key][value] if r["id"] not in chosen]
            if not cands:
                continue
            pick = max(cands, key=lambda r: (sum(1 for k in STRATA
                                                if r[k] not in covered[k]), r["id"]))
            chosen.add(pick["id"])
            for k in STRATA:
                covered[k].add(pick[k])

    dist = defaultdict(int)
    for rid in chosen:
        dist[rows[rid]["decision"]] += 1
    out = {"chosen": sorted(chosen),
           "n_chosen": len(chosen),
           "corpus_rows": len(rows),
           "cases_covered": len({rows[r]["case"] for r in chosen}),
           "coverage": {"domains": len(covered["domain"]),
                        "persona_archetypes": len(covered["ptype"]),
                        "individual_personas": len(covered["persona"]),
                        "case_archetypes": len(covered["kind"]),
                        "layers": len(covered["layer"]),
                        "conflict_patterns": len(covered["pattern"]),
                        "decision_classes": len(covered["decision"])},
           "decision_distribution": dict(dist)}
    with open(OUT, "w") as fh:
        json.dump(out, fh)
    print(json.dumps({"chosen": out["n_chosen"], "cases_covered": out["cases_covered"],
                      "coverage": out["coverage"],
                      "decision_distribution": out["decision_distribution"]}, indent=2))


if __name__ == "__main__":
    main()
