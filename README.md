# ETH-WCMK — a formally verified core and a SHACL-valid ontology for auditing delegated ethical agency

![license](https://img.shields.io/badge/license-MIT-blue.svg) ![model licence](https://img.shields.io/badge/model-CC--BY--SA--4.0-brightgreen.svg) ![python](https://img.shields.io/badge/python-3.11%2B-blue.svg) ![invariants](https://img.shields.io/badge/invariant%20tests-69-passing-green.svg) ![release](https://img.shields.io/github/release/Palazzo13-X/ETH-WCMK.svg) ![DOI](https://img.shields.io/badge/DOI-pending-blue.svg)

> **Owner note.** The repository currently lives under `Palazzo13-X/ETH-WCMK`.
> Once the `ETH-WCMK` organisation exists the repository is transferred to it
> (GitHub Settings → Transfer), and GitHub redirects the old URL automatically.
> CITATION.cff and the paper already cite `github.com/ETH-WCMK/ETH-WCMK`.

**ETH-WCMK** turns an ethical judgement about a *delegated* AI agent into a
computation you can inspect, test and re-run. An ethical case (ETHCASE) meets a
profile of delegated agency (WCMK: **W**ant, **C**an, **M**ust, **K**now) and the
model returns one of five verdicts:

```
ABSTAIN · PROHIBIT · REVIEW_REQUIRED · ALLOW_WITH_GUARDS · ALLOW
```

Every published number comes from an artefact, not from prose. That is the whole
project: five layers, each independently falsifiable.

**Languages:** English below · [Portuguese summary](#resumo-em-português)

---

## Table of contents

1. [What the model is](#1-what-the-model-is)
2. [Headline results](#2-headline-results)
3. [Quick start](#3-quick-start)
4. [Repository map](#4-repository-map)
5. [Data availability](#5-data-availability)
6. [Reproducing a specific number](#6-reproducing-a-specific-number)
7. [Limitations declared, not hidden](#7-limitations-declared-not-hidden)
8. [Citation](#8-citation)
9. [Licence](#9-licence)
10. [Governance and contact](#10-governance-and-contact)

---

## 1. What the model is

| Layer | Artefact | What it guarantees |
|---|---|---|
| **Arithmetic core** | `_analysis/formal_core/core.py` (v13) | `S2 ≥ S3 ≥ S4` unconditionally; `Ψ ∈ [0,1]`; guards are caps, never offsets |
| **Geometry** | `_analysis/formal_core/geometry.py` | 15 relation slots (4 vertices, 6 edges, 4 faces, 1 cell), each summing to 1 |
| **Facet canon** | `_analysis/facets/facet_registry_v13.csv` | 33 facets, `Σβ = 1`, ≤ 3 pillars per facet, none spanning all four |
| **Ontology** | `Ontologias/ontology_v4_2/` (7 TTL modules + SHACL shapes) | the RDF graph reproduces the Python verdicts |
| **Corpus** | `Evaluacoes/r5/corpus_v7_*` | 1,520 cases × 145 profiles = **220,400 confrontations**, deterministically generated |

The core is not a prompt template: it is 42 KB of Python with 44 numbered
invariants enforced by 69 tests.

## 2. Headline results

| Result | Value | Evidence |
|---|---|---|
| Invariant tests | 69 passed, 0 failed, 45 s | `pytest _analysis/formal_core/tests -q` |
| Structural hierarchy | `S2 ≥ S3 ≥ S4` for **every** deficit vector, proved by exhaustion over `{0,0.05,…,1}⁴` | test `I34` |
| Edge weights | `α_e = ⅓ Σβ_f` is **derived**, not assumed; at `β = 1/4` it equals the calibrated 1/6, so no published number changes | Prop. 1, `I36` |
| Ontology validation | 42/42 checks; SHACL 0 violations; 76/76 invalid fixtures detected | `Evaluacoes/r5/ontology_v4_2_validation.json` |
| Arithmetic mirror | graph ↔ Python diff **1.61 × 10⁻¹²**, 0 verdict divergences; full corpus mirror diff **0.0** | `mirror_full_corpus_v13.json` |
| Lattice census | 15 slots, each summing to 1; registry RDF ↔ CSV ↔ Python: 0 mismatches | `I24`, `I36` |
| Traceability | **177/177** numeric checks pass on the DOCX manuscript; 166/166 claims in the v13 text | `paper_docx_number_trace_v15.json`, `paper_consistency_check_v13.json` |
| Agreement with the panel | κ = 0.5336 global; 0.8167 in the unanimous stratum | `kappa_by_stratum_v13.json` |
| Round manifest | 51 artefacts, 22 runs, 65.9 MB, SHA-256 each, git revision stamped | `Evaluacoes/r5/manifest_r5.json` |

## 3. Quick start

```bash
git clone https://github.com/Palazzo13-X/ETH-WCMK.git   # redirects to ETH-WCMK/ETH-WCMK after the transfer
cd ETH-WCMK
python3 -m pip install -r requirements.txt

make test          # 69 invariant tests, ~45 s
make batteries     # regenerate the round artefacts and the manifest (~31 min)
make ontology      # generate + validate the ontology
make data          # build the compressed corpora for release
```

Without `make`:

```bash
python3 _analysis/run_all_batteries.py --round r5 --list
python3 _analysis/run_all_batteries.py --round r5
python3 -m pytest _analysis/formal_core/tests -q
```

Tested on Python 3.11–3.14 (the reference run used 3.14.4, rdflib 7.6.0,
pyshacl 0.40.1, numpy 2.5.4).

## 4. Repository map

```
README.md  LICENSE  NOTICE  CITATION.cff  CHANGELOG.md
CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md
Makefile  pyproject.toml  environment.yml  requirements.txt  requirements-dev.txt
.gitignore  .gitattributes  .editorconfig  .pre-commit-config.yaml  .zenodo.json
.github/            issue and PR templates, CODEOWNERS, dependabot
ci/                 the Actions workflows (installed with scripts/push_ci.sh)
docs/               ARCHITECTURE · REPRODUCIBILITY · DATA · GATES · PUBLISHING
                    archive/ (legacy drafts and the source PDF)
data/               CORPUS_MANIFEST.sha256
scripts/            audit, manifest, asset builder, fetch, publish gate,
                    clean-branch builder, branch sync, CI installer
_analysis/
  formal_core/      core.py, geometry.py, facet_registry.py, fact_grounding.py
  formal_core/tests/  test_invariants.py, test_geometry.py, test_fact_grounding.py
  corpus/           ETHCASE and ground-truth generators (seeded)
  ontology/         TTL + SHACL generators and validators
  analysis/         batteries B0–B26
  paper/            equation rendering, figure scripts, DOCX number trace
  facets/           facet registry versions + beta differentiation evidence
  PAPER_v15.docx, RELATORIO_TECNICO_CIENTIFICO_PT.docx, GATE_REPORT_r5.md,
  SPEC_v13_equations.md, CHANGELOG_DECISIONS.md, AUDIT_v12.md
Ontologias/ontology_v4_2/   the current ontology (v2, v3 kept as history)
Evaluacoes/r2 r3 r4 r5/      frozen rounds, each with a manifest
paper/                       rendered figures (PNG/PDF/MathML)
```

Full rationale: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 5. Data availability

The frozen rounds **r2 and r3** are committed in the tree
(`Evaluacoes/r2/corpus_v3_*`, `Evaluacoes/r3/corpus_v4_*` — 46 MB of corpora;
the whole tree is 116 MB, which clones in a few seconds). They anchor the
earlier, immutable results. The larger rounds are **not** in the git tree:
GitHub rejects objects above 100 MB, and rounds r4–r5 total 1.57 GB raw /
104.5 MB compressed across 20 assets. They are deterministic (seeded generator),
so they are published as compressed release assets and verified by checksum:

```bash
python3 scripts/build_release_assets.py      # builds release_assets/*.gz
python3 scripts/fetch_data.py --release v13.0.0
python3 scripts/make_data_manifest.py --check
```

`data/CORPUS_MANIFEST.sha256` lists the SHA-256 of every artefact above 1 MB
that a paper number depends on — 27 files, 1,602,477,756 bytes. See
[docs/DATA.md](docs/DATA.md).

**Privacy.** The corpus is synthetic. Personas are parameter vectors, not
people. The adjudication packets are blind and keyed (`case_id`,
`model_verdict`, `panel_A/B/C`, `consensus`, `rules_applied`) and contain no
names. No real individual appears in any artefact.

## 6. Reproducing a specific number

Three commands cover the whole chain:

```bash
# does the core hold?
python3 -m pytest _analysis/formal_core/tests -q

# does the RDF graph agree with the Python core?
python3 _analysis/analysis/mirror_full_corpus.py

# is the number in the text the number in the artefact?
python3 _analysis/analysis/paper_artifact_consistency_v13.py
```

The manifest records the git revision that produced it, so any artefact can be
re-created by checking out that revision and re-running the round.

## 7. Limitations declared, not hidden

- **κ is below the gate.** 0.5336 global against the declared threshold of 0.60.
  The variant that reaches 0.6005 does so by making model and panel abstain
  together — agreeing on not judging is cheap (D5.24). We report it as an open
  item, not as a success.
- **The ground truth is a rubric.** B26 shows κ ranging from 0.2974 to 0.6005
  depending on how undeclared facts and the coverage gate are handled. The most
  sensitive knob is not the duty floors (±10 % → ±0.01), it is the treatment of
  what is not declared.
- **B24 (LLM anchor)** was declared infeasible on the reference machine (D5.15),
  not faked.
- **The human panel** has not yet been run independently: the blind adjudication
  packet (120 cases, 360 cells) is ready and is exactly the thing external
  reviewers should do.

## 8. Citation

```bibtex
@software{palazzo2026ethwcmk,
  title   = {ETH-WCMK: a formal core and a SHACL-validated ontology for auditing
             delegated ethical agency},
  author  = {Palazzo, Luiz M. M. and Vanzin, Tarcísio},
  year    = {2026},
  version = {13.0.0},
  url     = {https://github.com/ETH-WCMK/ETH-WCMK}
}
```

[CITATION.cff](CITATION.cff) is what GitHub shows in the "Cite this repository"
panel.

## 9. Licence

- **Code** — MIT ([LICENSE](LICENSE)).
- **Model, ontologies, corpora, text, figures** — CC BY-SA 4.0
  ([NOTICE](NOTICE), [LICENSE-CC-BY-SA-4.0.txt](LICENSE-CC-BY-SA-4.0.txt)).

ETH-WCMK is a computational model of delegated agency. It is not legal advice,
not a compliance product, and is not endorsed by any of the instruments it
cites.

## 10. Governance and contact

- Rules of the project: [CONTRIBUTING.md](CONTRIBUTING.md)
- Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Reporting a problem: [SECURITY.md](SECURITY.md)
- Version history: [CHANGELOG.md](CHANGELOG.md)

Maintainers: **Luiz M. M. Palazzo** and **Tarcísio Vanzin**, PPGEGC,
Universidade Federal de Santa Catarina, Brazil.

---

## Resumo em português

**ETH-WCMK** transforma um juízo ético sobre um agente delegado em uma
computação verificável: núcleo aritmético com 44 invariantes (69 testes, 0
falhas), canon de 33 facetas, geometria tetraédrica de 15 slots, ontologia
RDF/SHACL sem violações em todo o corpus e um corpus de 1.520 casos × 145
perfis = 220.400 confrontações. Cada número do paper está ancorado em um
artefacto com SHA-256 registrado em `manifest_r5.json`; a verificação automática
de rastreabilidade passou em 166/166 afirmações.

**Limitação declarada:** a concordância com o painel humano de ground truth é
κ = 0,5336 global (0,8167 no estrato unânime), abaixo do gate de 0,60. A
bateria B26 mostra quanto cada prior da rubrica move esse κ — a maior
sensibilidade vem do tratamento do não declarado, não dos pisos de dever.

Licença: código MIT; modelo, ontologia, corpus, texto e figuras CC BY-SA 4.0.
Para reproduzir: `python3 _analysis/run_all_batteries.py --round r5`.
