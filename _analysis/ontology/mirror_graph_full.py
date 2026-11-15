#!/usr/bin/env python3
"""B20 - graph <-> core arithmetic mirror over ALL confrontation nodes in the RDF graph.

The slice validator (validate_ontology_v4.py) mirrors only the 403 confrontation nodes
present in fixtures/instances_subset.ttl, because the full instance graph
(1,888,317 triples) cannot be parsed on this machine. Here the same mirror is run over
every confrontation node that the generator actually serialized (3,755 of them), by
streaming fixtures/instances.ttl in case-sized chunks: modules + the chunk's blocks are
parsed, and the mirror machinery from validate_ontology_v4 is applied to that closed
subgraph.

Run:  python3 _analysis/ontology/mirror_graph_full.py
Writes: Evaluacoes/r4/graph_mirror_full.json
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

from rdflib import Graph

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ONT = os.path.join(ROOT, "Ontologias", "ontology_v4")
OUT = os.path.join(ROOT, "Evaluacoes", "r4", "graph_mirror_full.json")

sys.path.insert(0, HERE)
from validate_ontology_v4 import (load_graphs, facet_registry,
                                  select_confrontations, run_mirror, lattice_from_graph)


def read_blocks(path):
    prefixes, blocks, buf = [], [], []
    started = False
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not started:
                if line.startswith("prefix"):
                    prefixes.append(line)
                    continue
                if not line.strip() or line.startswith("#"):
                    continue
                started = True
            buf.append(line)
            if line.rstrip().endswith("."):
                blocks.append("\n".join(buf))
                buf = []
    return prefixes, blocks


def module_text():
    parts = []
    for name in sorted(os.listdir(ONT)):
        if name.endswith(".ttl") and not name.startswith("fixtures"):
            with open(os.path.join(ONT, name)) as fh:
                parts.append(fh.read())
    return "\n".join(parts)

CASE_RE = "ETHCASE-[A-Z]-\\d{4}"
CASES_PER_CHUNK = 120


def main():
    t0 = time.time()
    modules, shapes_v4, shapes_v6, _inst, _i4, _i6, _pm = load_graphs()
    base = module_text()
    prefixes, blocks = read_blocks(os.path.join(ONT, "fixtures", "instances.ttl"))
    prefix_text = "\n".join(prefixes)

    # group blocks by case; blocks without a case (agents, personas, calibration, lattice)
    # are carried in every chunk so the subgraph is closed.
    by_case = defaultdict(list)
    shared = []
    for b in blocks:
        cases = set()
        for tok in b.split():
            if "ETHCASE-" in tok:
                cases.add(tok.split("ETHCASE-")[1][:9])
        if len(cases) == 1:
            by_case[list(cases)[0]].append(b)
        else:
            shared.append(b)

    facet_defs = facet_registry(modules)
    facet_list = sorted(facet_defs.values(), key=lambda f: f.code)

    totals = {"nodes": 0, "verdict_divergences": 0, "max_abs_diff": 0.0}
    per_quantity = defaultdict(float)
    decisions = Counter()
    lattice_slots_seen = set()
    chunks = 0
    samples = []
    order = sorted(by_case)
    for i in range(0, len(order), CASES_PER_CHUNK):
        chunk_cases = order[i:i + CASES_PER_CHUNK]
        text = prefix_text + "\n" + base + "\n" + "\n".join(shared)
        for c in chunk_cases:
            text += "\n" + "\n".join(by_case[c]) + "\n"
        g = Graph()
        g.parse(data=text, format="turtle")
        chunks += 1
        slots = lattice_from_graph(g)
        for s in slots:
            lattice_slots_seen.add((s["kind"], tuple(s["incidence"])))
        chosen, strata, total, dist = select_confrontations(g, len(g))
        if not chosen:
            continue
        rows, pq, srows, verdicts, e30, stored = run_mirror(g, facet_defs, facet_list, slots, chosen)
        totals["nodes"] += len(chosen)
        for q, v in pq.items():
            per_quantity[q] = max(per_quantity[q], v["max_abs_diff"])
        totals["max_abs_diff"] = max(totals["max_abs_diff"], max([v["max_abs_diff"] for v in pq.values()] or [0.0]))
        totals["verdict_divergences"] += verdicts["python_ladder_vs_rdf"] + verdicts["core_decide_vs_rdf"]
        decisions.update(dist)
        for r in srows[:2]:
            if len(samples) < 6:
                samples.append(r)

    out = {
        "battery": "B20_graph_mirror_full",
        "question": "Does every arithmetic value serialized in the RDF graph match the core?",
        "scope": "all confrontation nodes emitted by the generator, streamed in chunks of 120 cases",
        "chunks": chunks,
        "confrontation_nodes_mirrored": totals["nodes"],
        "max_abs_difference_by_quantity": dict(sorted(per_quantity.items())),
        "global_max_abs_difference": totals["max_abs_diff"],
        "verdict_divergences": totals["verdict_divergences"],
        "decision_distribution": dict(decisions),
        "lattice_slots_seen": sorted(map(str, map(list, lattice_slots_seen)))[:20],
        "lattice_slot_count": len(lattice_slots_seen),
        "sample_rows": samples,
        "runtime_seconds": round(time.time() - t0, 2),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: out[k] for k in ("confrontation_nodes_mirrored", "global_max_abs_difference",
                                         "verdict_divergences", "chunks", "runtime_seconds")}, indent=2))


if __name__ == "__main__":
    main()
