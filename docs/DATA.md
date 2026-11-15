# Data availability

Every number in the paper is derived from an artefact. This file describes the
artefacts, where they live and how to verify them.

## Where the data lives

| Tier | Contents | Location | Size |
|---|---|---|---|
| A | code, docs, configs, manifests, facet registry, aggregated JSON < 5 MB, figures, ontology TTL, **frozen r2/r3 corpora** | repository | 116.6 MB (measured, `git ls-tree -r -l main`) |
| B | corpora and instance graphs from rounds r4–r5, gzipped (1 MB – 2 GB) | GitHub Releases | 104.4 MB (measured) |
| C | per-version snapshot with a citable DOI | Zenodo | mirror of B |

Rounds r2 and r3 (`corpus_v3_*`, `corpus_v4_*`, 46.4 MB raw) are deliberately
kept in the git tree: they are the historical anchor of the ladder and are small
enough that cloning them costs nothing. Everything from r4 onwards is a release
asset.

GitHub rejects objects larger than 100 MB (recommended 1 MB). Release assets may
be up to 2 GiB each with no total or bandwidth limit. Git LFS would also work but
is unnecessary here: the corpora are deterministic, so publishing them as assets
keeps every clone fast without losing anything.

## Assets attached to release v13.0.0

Built by `scripts/build_release_assets.py` (gzip level 9). Raw → compressed:

```
corpus_v7_confrontations.jsonl.gz   497.8 MB → 40.90 MB
corpus_v6_confrontations.jsonl.gz   391.2 MB → 33.48 MB
corpus_v5_confrontations.jsonl.gz   129.5 MB →  7.76 MB
corpus_v7_gold.jsonl.gz             129.0 MB →  3.95 MB
corpus_v6_gold.jsonl.gz             104.5 MB →  3.12 MB
corpus_v5_gold.jsonl.gz             102.7 MB →  3.23 MB
ontology v4.2 instances.ttl.gz       64.2 MB →  3.48 MB
ontology v4   instances.ttl.gz       62.8 MB →  3.36 MB
corpus_v4_confrontations.jsonl.gz     27.5 MB →  0.84 MB
B20_variant_eval_full.json.gz         26.3 MB →  0.14 MB
corpus_v3_confrontations.jsonl.gz     11.0 MB →  0.69 MB
corpus_v7_layerA.jsonl.gz              3.4 MB →  0.44 MB
corpus_v6_layerA.jsonl.gz              3.4 MB →  0.43 MB
corpus_v4_layerA.jsonl.gz              3.1 MB →  0.88 MB
corpus_v5_layerA.jsonl.gz              3.1 MB →  0.37 MB
corpus_v2_configurations.csv.gz        3.2 MB →  0.30 MB
corpus_v7_layerB.jsonl.gz              2.0 MB →  0.30 MB
corpus_v6_layerB.jsonl.gz              2.0 MB →  0.30 MB
corpus_v5_layerB.jsonl.gz              1.9 MB →  0.27 MB
corpus_v4_layerB.jsonl.gz              1.3 MB →  0.31 MB
-----------------------------------------
TOTAL (20 assets)                  1,569.8 MB → 104.5 MB
```

`release_assets/ASSET_MANIFEST.json` records, for each asset, its source path,
raw size, compressed size and SHA-256.

## Verifying what you downloaded

```bash
python3 scripts/make_data_manifest.py --check
python3 scripts/fetch_data.py --release v13.0.0 --local release_assets
```

`data/CORPUS_MANIFEST.sha256` lists the SHA-256 of every artefact above 1 MB used
by the paper: 27 files, 1,602,477,756 bytes. If the files on disk match, your
corpus is bit-identical to the one the numbers came from.

## Schemas

`*_confrontations.jsonl` — one JSON object per confrontation:

```json
{"case_id": "...", "persona_id": "...", "pillars": {"W":0.4,"C":0.7,"M":0.5,"K":0.3},
 "deficits": {...}, "S2":..., "S3":..., "S4":..., "stakes":...,
 "adequacy": {"raw":..., "low":..., "high":...}, "bar":0.70,
 "risk":..., "verdict":"REVIEW_REQUIRED", "trace":{...}}
```

`*_gold.jsonl` — one object per (case, persona): panel consensus, per-panel votes
and the rules applied.

`*_layerA.jsonl` — stress cases (deliberately hard, boundary conditions).
`*_layerB.jsonl` — semantic cases drawn from real-world domains.

## Determinism

`SEED = 20261104`, recorded inside the artefact as
`"generator": "gen_corpus_v5.py", "seed": 20261104`. Re-running the generator
from the same revision reproduces the corpus.

## Privacy and licence

The corpus is synthetic: cases come from templates and personas are parameter
vectors. The adjudication packets are blind and keyed, with columns `case_id`,
`model_verdict`, `panel_A`, `panel_B`, `panel_C`, `consensus`, `rules_applied` —
no names, no identifying data. No real individual appears in any artefact.

Data are CC BY-SA 4.0 (see `NOTICE`).
