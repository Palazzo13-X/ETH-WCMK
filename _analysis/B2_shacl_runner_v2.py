#!/usr/bin/env python3
"""ETH-WCMK - Bateria B2 v2: bateria SHACL completa e auditavel.

Diferencas em relacao a shacl_runner.py:
  * testa TODOS os pares (dados x shapes) possiveis, nao apenas pares nomeados;
  * conta triplos e shapes por arquivo com rdflib antes de validar;
  * separa violacoes por severidade (Violation / Warning / Info);
  * captura erros de parse/parse de shapes (ex.: PropertyShape sem sh:path);
  * escreve _analysis/B2_shacl_results.json (maquina-level) e um resumo textual.

Uso:
    python3 B2_shacl_runner_v2.py            # originals
    python3 B2_shacl_runner_v2.py --v2      # originals + ontology_v2
    python3 B2_shacl_runner_v2.py --json out.json
Exit code 0 sempre (relatorio, nao gate).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import RDF
from pyshacl import validate

ROOT = Path(__file__).resolve().parent.parent
ONTO = ROOT / "Ontologias"
SH = "http://www.w3.org/ns/shacl#"  # SHACL Core namespace


def triples_and_shapes(path: Path):
    g = Graph()
    g.parse(str(path), format="turtle")
    n_triples = len(g)
    n_node = sum(1 for s, p, o in g.triples((None, RDF.type, None)) if str(o) == SH + "NodeShape")
    n_prop = sum(1 for s, p, o in g.triples((None, RDF.type, None)) if str(o) == SH + "PropertyShape")
    n_sparql = sum(1 for s, p, o in g.triples((None, RDF.type, None)) if str(o) == SH + "SPARQLConstraint")
    n_rule = sum(1 for s, p, o in g.triples((None, RDF.type, None)) if str(o) == SH + "Rule")
    paths_without_path = []
    for s, p, o in g.triples((None, RDF.type, None)):
        if str(o) == SH + "PropertyShape":
            if not list(g.triples((s, SH + "path", None))):
                paths_without_path.append(str(s))
    return {
        "triples": n_triples,
        "nodeShapes": n_node,
        "propertyShapes": n_prop,
        "sparqlConstraints": n_sparql,
        "rules": n_rule,
        "propertyShapesWithoutPath": paths_without_path,
    }


def validate_pair(data_path: Path, shapes_path: Path):
    try:
        ok, report_graph, _ = validate(
            str(data_path),
            str(shapes_path),
            format="turtle",
            inference="rdfs",
        )
    except Exception as exc:  # PyShACL hard error (e.g. sh:path missing)
        return {"error": f"{type(exc).__name__}: {exc}", "conformant": None,
                "violations": [], "warnings": [], "infos": [], "total": 0}
    sev = {"Violation": [], "Warning": [], "Info": []}
    for b in report_graph.subjects(SH + "ValidationResult", None):
        def get(p):
            v = report_graph.value(b, SH + p)
            return str(v) if v is not None else ""
        s = get("severity")
        key = "Violation" if "Violation" in s else ("Warning" if "Warning" in s else "Info")
        sev[key].append({
            "path": get("sourcePath"),
            "shape": get("sourceShape"),
            "target": get("focusNodePath") or get("focusNode"),
            "message": get("resultMessage"),
            "severity": s,
        })
    return {
        "error": None,
        "conformant": bool(ok),
        "violations": sev["Violation"],
        "warnings": sev["Warning"],
        "infos": sev["Info"],
        "total": sum(len(v) for v in sev.values()),
    }


def main():
    argv = sys.argv[1:]
    include_v2 = "--v2" in argv
    out_json = None
    if "--json" in argv:
        out_json = Path(argv[argv.index("--json") + 1])

    dirs = [ONTO / "wcmk_extracted" / "wcmk", ONTO / "eth_extracted" / "eth"]
    if include_v2:
        dirs.append(ONTO / "ontology_v2")

    files = []
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.ttl")):
            files.append(f)

    results = []
    for f in files:
        meta = triples_and_shapes(f)
        results.append({"file": str(f.relative_to(ROOT)), "parse": meta})

    # shapes files = those declaring at least one shape
    shape_files = [f for f in files if any(r["parse"]["nodeShapes"] or r["parse"]["propertyShapes"]
                                           for r in results if r["file"] == str(f.relative_to(ROOT)))]
    data_files = files

    pairs = []
    for d in data_files:
        for s in shape_files:
            if d == s:
                continue  # self-validation is a degenerate case, skipped
            pairs.append((d, s))

    runs = []
    for d, s in pairs:
        r = validate_pair(d, s)
        entry = {
            "data": str(d.relative_to(ROOT)),
            "shapes": str(s.relative_to(ROOT)),
            **r,
        }
        runs.append(entry)

    report = {"generator": "B2_shacl_runner_v2.py", "pairsRun": len(pairs),
              "files": results, "runs": runs}
    if out_json:
        out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"arquivos analisados: {len(files)} | pares validados: {len(pairs)}")
    print("\n=== METADADOS ===")
    for r in results:
        p = r["parse"]
        extra = ""
        if p["propertyShapesWithoutPath"]:
            extra = "  [!] PropertyShape sem sh:path: " + ", ".join(p["propertyShapesWithoutPath"])
        print(f"{r['file']:70s} triples={p['triples']:5d} nodeShapes={p['nodeShapes']:3d} "
              f"propShapes={p['propertyShapes']:3d} sparql={p['sparqlConstraints']:3d} rules={p['rules']:2d}{extra}")

    print("\n=== CONFORMANCE ===")
    for r in runs:
        if r["error"]:
            print(f"ERRO  {r['data']} x {r['shapes']}: {r['error']}")
        else:
            print(f"{'OK   ' if r['conformant'] else 'FAIL '} {r['data']} x {r['shapes']} "
                  f"total={r['total']} violations={len(r['violations'])} warnings={len(r['warnings'])} infos={len(r['infos'])}")
    if out_json:
        print(f"\nrelatorio completo: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
