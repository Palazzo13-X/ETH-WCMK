# Repository architecture

Design principles, target tree and the migration from the current layout.

## Principles

1. **One canonical core, many artefacts.** `_analysis/formal_core/` is the only
   place where the arithmetic is defined. Everything else either consumes it or
   records what it produced.
2. **Rounds are immutable evidence.** `Evaluacoes/rN/` is append-only. The
   manifest is the link between a paper claim and a byte-identical artefact.
3. **Code inside, data outside.** GitHub rejects objects over 100 MB and
   recommends 1 MB. The corpora are 1.6 GB, so they ship as compressed release
   assets while the repository stays ≈ 117 MB and clones in seconds.
4. **One entry point per task.** `make test`, `make batteries`, `make data`. A
   reviewer should never have to guess how to run something.

## Tree as published

```
README.md  LICENSE  NOTICE  CITATION.cff  CHANGELOG.md
CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md
.gitignore  .gitattributes  .editorconfig  .pre-commit-config.yaml
Makefile  pyproject.toml  environment.yml  requirements.txt  requirements-dev.txt
.zenodo.json
.github/  workflows/ci.yml, workflows/release-assets.yml,
          ISSUE_TEMPLATE/{verification.yml, critique.yml, question.yml},
          PULL_REQUEST_TEMPLATE.md, CODEOWNERS
docs/     ARCHITECTURE, REPRODUCIBILITY, DATA, GATES, PUBLISHING
          archive/ (v9 draft, the tetrahedron source PDF, the retomada notes)
          (plus PLANO_ARQUITETURA_GIT.md at the repository root)
data/     CORPUS_MANIFEST.sha256
scripts/  audit_repo.py, make_data_manifest.py, build_release_assets.py,
          fetch_data.py, publish_check.sh, untrack_big_files.sh,
          make_public_branch.sh, publish_to_github.sh
_analysis/
  formal_core/       core.py, geometry.py, facet_registry.py, fact_grounding.py
  formal_core/tests/ test_invariants.py, test_geometry.py, test_fact_grounding.py
  corpus/            ETHCASE and ground-truth generators (seeded)
  ontology/          TTL + SHACL generators and validators
  analysis/          batteries B0–B26
  facets/            facet registry CSV/JSON
  paper/             equations, figures, DOCX number trace
  GATE_REPORT_r5.md, SPEC_v13_equations.md, AUDIT_v12.md,
  ADJUDICATION_PROTOCOL_v13.md, CHANGELOG_DECISIONS.md,
  PAPER_v13.md, PAPER_v14.docx, PAPER_v15.docx,
  RELATORIO_TECNICO_CIENTIFICO_PT.docx
Ontologias/ontology_v4_2/  01_core.ttl … 07_grounding.ttl, shapes/, fixtures/
Ontologias/ontology_v4/    previous version, kept as evidence
Ontologias/ontology_v2/    validated semantic layer (2,815 triples)
Evaluacoes/r2 r3 r4 r5/    frozen rounds + manifests
paper/                     figures/ (MathML + PDF), figures_v14/ (PNG)
release_assets/            built locally, gitignored, uploaded to Releases
```

## Module responsibilities

| Module | Owns | Invariants tested |
|---|---|---|
| `formal_core/core.py` | deficits, pillar levels, S₂/S₃/S₄, stakes, adequacy band, verdict | I1–I33, I34–I44 |
| `formal_core/geometry.py` | 15 relation slots, derived α_e, Ψ | I24, I36 |
| `formal_core/facet_registry.py` | the 33-facet canon, β, guards | I25, I38 |
| `formal_core/fact_grounding.py` | observed fact → duty implication, λ(E) | I41–I43 |
| `corpus/` | ETHCASE and panel generation | determinism, coverage gate |
| `ontology/` | TTL modules + SHACL shapes | mirror equality with `core.decide` |
| `analysis/` | batteries B0–B26 | Δκ with paired-bootstrap IC95 |
| `paper/` | equation/figure rendering, DOCX trace | 166/166 claims traceable |

## Data tiers

| Tier | Content | Where | Size |
|---|---|---|---|
| A | code, docs, configs, manifests, registry, aggregated JSON < 5 MB, figures, TTL modules, frozen r2/r3 corpora | repository | 116.6 MB |
| B | corpora + instance graphs, gzipped | GitHub Releases | 104 MB per round set |
| C | version snapshot with DOI | Zenodo | mirror of B |

## Phase 2 (after the first public tag)

Move `_analysis/formal_core/` → `src/ethwcmk/` and the tests → `tests/`, so the
core becomes an importable package (`pip install -e .`). That requires touching
the `sys.path.insert` lines in `_analysis/analysis/*.py`. Do it only after
v13.0.0 is tagged, so the published tag matches the paths cited in the paper.
