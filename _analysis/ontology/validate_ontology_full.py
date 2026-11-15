#!/usr/bin/env python3
"""G4' full-corpus validation of ontology v4.1 over fixtures/instances.ttl.

Why not a single parse: the instance graph is 1,893,019 triples and rdflib needs
~2.2 GB for it, while 27 GB of this machine's RAM are held by the local inference
engine and the swap is already exhausted. The file is therefore validated in units of
individuals:

  * every block in the emitted Turtle is one individual plus its inline blank nodes,
    so every SHACL node shape can be evaluated on the block it targets;
  * each chunk is completed with the seven modules (8,433 triples, always in RAM) and
    with the persona/layer agent individuals the chunk references, so that
    sh:class constraints and the cross-block SPARQL checks see a closed graph.

Blocks are grouped by case, never split across chunks, which is what makes the
cross-block checks (case -> norms, confrontation -> profile, link -> agent) safe.

Output: Evaluacoes/r4/ontology_full_validation.json
"""

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

from rdflib import Graph
from pyshacl import validate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ONT = os.path.join(ROOT, "Ontologias", "ontology_v4")
OUT = os.path.join(ROOT, "Evaluacoes", "r4", "ontology_full_validation.json")

sys.path.insert(0, HERE)
from validate_ontology_v4 import consistency_checks, parse_report  # noqa: E402

CASE_RE = re.compile(r"ETHCASE-[A-Z]-\d{4}")
BLOCKS_PER_CHUNK = 120  # cases per chunk


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


def shapes_graph(path):
    g = Graph()
    g.parse(path, format="turtle")
    return g


def run_shacl(chunk_text, shapes, label):
    data = Graph()
    data.parse(data=chunk_text, format="turtle")
    t0 = time.time()
    conformed, report, _ = validate(data, shacl_graph=shapes, inference="none", abort=False)
    viol = parse_report(report)
    return conformed, len(viol), time.time() - t0, viol


def main():
    t0 = time.time()
    inst = os.path.join(ONT, "fixtures", "instances.ttl")
    prefixes, blocks = read_blocks(inst)
    prefix_text = "\n".join(prefixes) + "\n"
    mod = module_text()

    persona_text, case_blocks = [], defaultdict(list)
    for b in blocks:
        m = CASE_RE.search(b)
        if m:
            case_blocks[m.group(0)].append(b)
        else:
            persona_text.append(b)
    persona_chunk = "\n".join(persona_text)

    cases = sorted(case_blocks)
    shapes_v4 = shapes_graph(os.path.join(ONT, "shapes", "ontology_shapes.ttl"))
    shapes_v6 = shapes_graph(os.path.join(ONT, "shapes", "ontology_shapes_v6.ttl"))

    shacl_v4 = {"conforms": True, "violations": 0, "seconds": 0.0,
                "by_shape": Counter(), "by_component": Counter(), "by_path": Counter(),
                "sample": []}
    shacl_v6 = dict(shacl_v4)
    shacl_v6 = {"conforms": True, "violations": 0, "seconds": 0.0,
                "by_shape": Counter(), "by_component": Counter(), "by_path": Counter(),
                "sample": []}
    triples_seen = 0
    chunks = 0
    check_totals = defaultdict(int)
    check_names = {}


    for i in range(0, len(cases), BLOCKS_PER_CHUNK):
        group = cases[i:i + BLOCKS_PER_CHUNK]
        body = "\n".join(b for c in group for b in case_blocks[c])
        chunk = prefix_text + mod + persona_chunk + body
        g = Graph()
        g.parse(data=chunk, format="turtle")
        triples_seen += len(g)
        chunks += 1

        for shapes, bucket in ((shapes_v4, shacl_v4), (shapes_v6, shacl_v6)):
            ok, n, s, viol = run_shacl(chunk, shapes, "chunk")
            bucket["conforms"] = bucket["conforms"] and ok
            bucket["violations"] += n
            bucket["seconds"] += s
            for v in viol:
                bucket["by_shape"][str(v["shape"])] += 1
                bucket["by_component"][str(v["component"])] += 1
                bucket["by_path"][str(v["path"])] += 1
                if len(bucket["sample"]) < 10:
                    bucket["sample"].append(v)
        for c in consistency_checks(g):
            name = c["check"]
            check_names[name] = c["kind"]
            if c.get("error"):
                check_totals[name] += 0
                check_names[name] = "error"
            else:
                check_totals[name] += c.get("rows_returned", 0)
        print(f"chunk {chunks}: {len(group)} cases, {len(g)} triples, "
              f"v4 violations {bucket['violations']}, v6 violations {shacl_v6['violations']}",
              file=sys.stderr)

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "gate": "G4' (full corpus, streamed)",
        "graph": {"blocks": len(blocks), "case_groups": len(cases),
                  "persona_blocks": len(persona_text), "chunks": chunks,
                  "triples_validated": triples_seen,
                  "triples_in_file": int(os.environ.get("EXPECTED_TRIPLES", "0"))},
        "shacl_v4": {"conforms": shacl_v4["conforms"], "violations": shacl_v4["violations"],
                     "seconds": round(shacl_v4["seconds"], 2),
                     "by_component": dict(shacl_v4["by_component"]),
                     "by_path": dict(shacl_v4["by_path"]),
                     "sample": shacl_v4["sample"]},
        "shacl_v6": {"conforms": shacl_v6["conforms"], "violations": shacl_v6["violations"],
                     "seconds": round(shacl_v6["seconds"], 2),
                     "by_component": dict(shacl_v6["by_component"]),
                     "by_path": dict(shacl_v6["by_path"]),
                     "sample": shacl_v6["sample"]},
        "consistency_checks_over_full_corpus": {
            name: {"kind": check_names[name], "violating_rows": check_totals[name]}
            for name in sorted(check_totals)},
        "failed_checks": [n for n in sorted(check_totals)
                          if check_totals[n] > 0 and check_names[n] != "finding"],
        "findings": {n: check_totals[n] for n in sorted(check_totals)
                     if check_names[n] == "finding"},
        "runtime_seconds": round(time.time() - t0, 2),
    }
    result["gate_verdict"] = "PASS" if (result["shacl_v4"]["violations"] == 0
                                        and result["shacl_v6"]["violations"] == 0
                                        and not result["failed_checks"]) else "NOT MET"
    with open(OUT, "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps({k: result[k] for k in ("gate_verdict", "shacl_v4", "shacl_v6",
                                            "failed_checks", "findings",
                                            "runtime_seconds")}, indent=2))


if __name__ == "__main__":
    main()
