#!/usr/bin/env python3
"""ETH-WCMK - Bateria B2 (conformance SHACL): runner minimo e deterministico.

Executa PyShACL sobre cada par (dados, shapes) listado em PAIRS e imprime um
relatorio compacto: conformidade, numero de violacoes e as primeiras N
violacoes (texto literal do relatorio PyShACL).

Uso:
    python3 shacl_runner.py                   # todos os pares
    python3 shacl_runner.py --json b2.json    # relatorio completo (JSON)
    python3 shacl_runner.py --limit 5         # detalhes por arquivo

Exit code: 0 se todas as validacoes conformes; 1 caso contrario (usavel em CI).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


from pyshacl import validate

ROOT = Path(__file__).resolve().parent.parent
ONTO = ROOT / "Ontologias"

PAIRS = [
    ("wcmk_extracted/wcmk/wcmk-facets.ttl", "wcmk_extracted/wcmk/wcmk-facets.shacl.ttl", "facetas WCMK"),
    ("wcmk_extracted/wcmk/wcmk-profile.ttl", "wcmk_extracted/wcmk/wcmk-profile.ttl", "vocabulario WCMK (auto-valid)"),
    ("wcmk_extracted/wcmk/bridge-wcmkplus.ttl", "wcmk_extracted/wcmk/bridge-wcmkplus.ttl", "bridge (auto-valid)"),
    ("wcmk_extracted/wcmk/bridge-wcmkplus-scoring-example-valid.ttl", "wcmk_extracted/wcmk/bridge-wcmkplus.ttl", "exemplo de scoring VALIDO"),
    ("wcmk_extracted/wcmk/bridge-wcmkplus-scoring-example-invalid.ttl", "wcmk_extracted/wcmk/bridge-wcmkplus.ttl", "exemplo de scoring INVALIDO"),
    ("wcmk_extracted/wcmk/wcmk-assessment.ttl", "wcmk_extracted/wcmk/wcmk-assessment.shacl.ttl", "assessment WCMK"),
    ("wcmk_extracted/wcmk/wcmk-instance.ttl", "wcmk_extracted/wcmk/wcmk-instance.shacl.ttl", "instancia de perfil"),
    ("eth_extracted/eth/ethcase-core.ttl", "eth_extracted/eth/ethcase-core.ttl", "nucleo ETHCASE (auto-valid)"),
    ("eth_extracted/eth/ethcase-analysis.ttl", "eth_extracted/eth/ethcase-analysis.ttl", "analise ETHCASE (auto-valid)"),
    ("eth_extracted/eth/ethcase-facet-requirements.ttl", "eth_extracted/eth/ethcase-facet-requirements.shacl.ttl", "requisitos por faceta"),
    ("eth_extracted/eth/ethcase-facet-requirements-example-valid.ttl", "eth_extracted/eth/ethcase-facet-requirements.shacl.ttl", "exemplo de requisitos VALIDO"),
    ("eth_extracted/eth/ethcase-facet-requirements-example-invalid.ttl", "eth_extracted/eth/ethcase-facet-requirements.shacl.ttl", "exemplo de requisitos INVALIDO"),
]


def run_pair(data_p, shapes_p, label, detail_limit):
    """Valida um par (dados, shapes). PyShACL 0.40.1 + Python 3.14 retorna
    conformidade incorreta quando recebe objetos Graph ja construidos; passar
    caminhos de arquivo evita esse problema (verificado empiricamente)."""
    rec = {"label": label, "data": data_p, "shapes": shapes_p}
    try:
        ok, conv_graph, report = validate(
            str(ONTO / data_p), shacl_graph=str(ONTO / shapes_p),
            detailed=True, advanced=True)
    except Exception as e:
        rec.update(conforms=None, error=str(e), n_violations=0,
                   n_violation_triples=0, report="", violations=[])
        return rec
    lines = [l for l in report.splitlines() if l.strip()]
    rec.update(conforms=bool(ok),
              n_violations=report.count("Constraint Violation"),
              n_violation_triples=len(conv_graph),
              violations=lines[1:detail_limit + 1], report=report)
    return rec


def main(argv):
    detail_limit = 6
    out_json = None
    if "--json" in argv:
        out_json = argv[argv.index("--json") + 1]
    if "--limit" in argv:
        detail_limit = int(argv[argv.index("--limit") + 1])

    results = [run_pair(d, s, l, detail_limit) for d, s, l in PAIRS]
    total = sum(r.get("n_violations", 0) for r in results)
    for r in results:
        status = "PASS" if r["conforms"] else ("FAIL" if r["conforms"] is not None else "ERROR")
        print(f"[{status}] {r['label']}: violations={r['n_violations']} (violation triples={r.get('n_violation_triples', 0)})")
        for v in r.get("violations", []):
            print("    " + v)
        if r["n_violations"] > detail_limit:
            print(f"    ... {r['n_violations'] - detail_limit} violacoes adicionais")
    print(f"\nTOTAL de violacoes: {total}")
    if out_json:
        Path(out_json).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"relatorio completo -> {out_json}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
