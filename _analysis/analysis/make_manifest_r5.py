"""manifest_r5.json — inventário de hashes e durações da Rodada 5 (v13).

Regra do projeto: cada número do paper tem de poder ser rastreado a um artefato, e cada
artefato tem de poder ser identificado por hash. Este script não re-executa baterias:
registra o que existe, com a duração reportada pelo próprio artefato quando houver.

Run:  python3 _analysis/analysis/make_manifest_r5.py
Out:  Evaluacoes/r5/manifest_r5.json
"""
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R5 = os.path.join(ROOT, "Evaluacoes", "r5")

CORE = ["_analysis/formal_core/core.py", "_analysis/formal_core/geometry.py",
        "_analysis/formal_core/facet_registry.py", "_analysis/formal_core/fact_grounding.py",
        "_analysis/formal_core/run_battery_B8_v13.py",
        "_analysis/formal_core/tests/test_invariants.py",
        "_analysis/formal_core/tests/test_geometry.py",
        "_analysis/formal_core/tests/test_fact_grounding.py"]

GENERATORS = ["_analysis/corpus/gen_corpus_v5.py", "_analysis/corpus/gold_panels_v5.py",
              "_analysis/ontology/gen_ontology_v6.py", "_analysis/ontology/validate_ontology_v6.py",
              "_analysis/analysis/b20_variant_eval.py", "_analysis/analysis/b22_fact_contradiction.py",
              "_analysis/analysis/sobol_v13_b23.py", "_analysis/analysis/mirror_full_corpus_v13.py",
              "_analysis/analysis/adjudication_packet.py", "_analysis/analysis/llm_anchor_v13.py",
              "_analysis/analysis/kappa_by_stratum.py",
              "_analysis/analysis/paper_artifact_consistency_v13.py",
              "_analysis/analysis/make_manifest_r5.py",
              "_analysis/analysis/b26_rubric_sensitivity.py"]

DOCS = ["_analysis/PAPER_v13.md", "_analysis/SPEC_v13_equations.md",
        "_analysis/GATE_REPORT_r5.md", "_analysis/CHANGELOG_DECISIONS.md",
        "_analysis/ADJUDICATION_PROTOCOL_v13.md", "_analysis/RETOMADA_r5_REPORT.md"]

FACETS = ["_analysis/facets/beta_differentiation_v13.json",
          "_analysis/facets/criticality_rebalance_v13.json",
          "_analysis/facets/criticality_mild_cap3_v13.json",
          "_analysis/facets/criticality_targeted_TB_TS_IM_v13.json",
          "_analysis/facets/facet_registry_v13.csv"]

DURATION_KEYS = ["runtime_seconds", "seconds", "duration_s", "runtime_s"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def duration_of(path):
    try:
        with open(path) as fh:
            d = json.load(fh)
    except Exception:
        return None
    for k in DURATION_KEYS:
        if isinstance(d.get(k), (int, float)):
            return round(float(d[k]), 2)
    return None


def git_rev():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        return out.stdout.strip() or None
    except Exception:
        return None


def main():
    artefacts = []
    for rel in CORE + GENERATORS + DOCS + FACETS:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            artefacts.append({"path": rel, "sha256": sha256(p), "bytes": os.path.getsize(p),
                             "kind": "code" if rel in CORE + GENERATORS else "document"})
    ont = os.path.join(ROOT, "Ontologias", "ontology_v4_2")
    if os.path.isdir(ont):
        for dirpath, _, files in os.walk(ont):
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                artefacts.append({"path": os.path.relpath(p, ROOT), "sha256": sha256(p),
                                  "bytes": os.path.getsize(p), "kind": "ontology"})
    runs = []
    for rel in sorted(os.listdir(R5)):
        p = os.path.join(R5, rel)
        if rel.endswith(".json") and not rel.startswith("manifest"):
            runs.append({"name": rel, "duration_s": duration_of(p), "sha256": sha256(p),
                        "bytes": os.path.getsize(p)})
    manifest = {
        "round": "r5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_rev": git_rev(),
        "python": sys.version.split()[0],
        "machine": platform.platform(),
        "canon": "33 facets, differentiated beta (v13 canon)",
        "corpus": "corpus_v7 (1,520 cases, 144 personas + 1 declared profile, 220,400 confrontations)",
        "core_version": "v13 (Prop-1 derived alpha, oversight regime E11c', ReviewNeed E32, declared coverage gate)",
        "calibration_convention": ("corpus and gold use the frozen r3 ladder; sensitivity and mechanism "
                                   "batteries use core.load_fitted_calibration() defaults and are reported separately"),
        "immutability_note": ("r2/r3/r4 artefacts are not rewritten (D5.10). v13 re-verifications are "
                             "stored in r5: mirror_full_corpus_v13.json, B8_probes_reverified_v13.json, "
                             "ontology_v4_validation_reverified.json"),
        "artefacts": artefacts,
        "runs": runs,
        "counts": {"artefacts": len(artefacts), "r5_json_runs": len(runs),
                   "core_files": len(CORE), "ontology_files": sum(1 for a in artefacts if a["kind"] == "ontology")},
    }
    out = os.path.join(R5, "manifest_r5.json")
    json.dump(manifest, open(out, "w"), indent=1)
    print(json.dumps({"artefacts": len(artefacts), "runs": len(runs),
                      "total_bytes": sum(a["bytes"] for a in artefacts)}, indent=1))
    print("written:", out)


if __name__ == "__main__":
    main()
