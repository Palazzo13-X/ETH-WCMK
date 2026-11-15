# Reproducibility

The chain is:

```
seed → corpus (.jsonl) → core.decide → manifest (SHA-256) → number in the paper
```

## Environment

| Item | Reference run | Minimum |
|---|---|---|
| Python | 3.14.4 | 3.11 |
| rdflib | 7.6.0 | 7.6 |
| pyshacl | 0.40.1 | 0.40 |
| numpy | 2.5.4 | 2.0 |
| pytest | 9.2.0 | 9.0 |

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`environment.yml` gives the conda variant if you prefer a pinned environment.

## Run everything

```bash
python3 _analysis/run_all_batteries.py --round r5
```

Measured on the reference machine: **22 runs, 1,874 s (≈ 31 min)**, producing
51 artefacts hashed in `Evaluacoes/r5/manifest_r5.json`.

| Flag | Effect |
|---|---|
| `--round r5` | target round directory |
| `--corpus` | regenerate the corpus first (seeded) |
| `--skip B7` | omit one battery |
| `--list` | print the battery list without running |

## The three checks that matter

```bash
# (a) the core: 44 invariants, 69 tests
python3 -m pytest _analysis/formal_core/tests -q

# (b) does the RDF graph agree with the Python core?
python3 _analysis/analysis/mirror_full_corpus.py

# (c) is the number in the text the number in the artefact?
python3 _analysis/analysis/paper_artifact_consistency_v13.py
```

Expected: 69 passed; mirror diff ≤ 1.7 × 10⁻¹² with 0 verdict divergences; 166
claims re-derived with 0 failures.

## What the manifest guarantees

`manifest_r5.json` stores, for every artefact: SHA-256, byte size, the git
revision that produced it, the Python version, per-run duration and a
`source_inventory` of the files that fed the round. A number that is not in the
manifest is not in the paper.

## Known reproducibility limits

1. **The human panel.** Ground-truth consensus was produced by the maintainers.
   Independent replication requires the blind adjudication packet (120 cases,
   360 cells) plus `ADJUDICATION_PROTOCOL_v13.md`. κ depends on that consensus;
   B26 quantifies the range: 0.2974–0.6005 across 11 rubric variants.
2. **B6/B24 need a local LLM.** Without one they are reported as skipped, not as
   failures (D5.15).
3. **Timings are machine-dependent.** The manifest records per-run duration so a
   deviation can be attributed rather than guessed.
