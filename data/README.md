# Data pointer

This directory contains only the checksum manifest. The corpora themselves are
too large for a git tree and are published as compressed assets on the GitHub
release (and mirrored on Zenodo).

- `CORPUS_MANIFEST.sha256` — SHA-256 of every artefact > 1 MB that a paper
  number depends on (27 files, 1,602,477,756 bytes).
- `release_assets/` (local, gitignored) — the 20 gzipped assets you drag into
  the release. Rebuild with `python3 scripts/build_release_assets.py`.

Fetch and verify:

```bash
python3 scripts/fetch_data.py --release v13.0.0        # from GitHub Releases
python3 scripts/fetch_data.py --local release_assets   # from the local build
python3 scripts/make_data_manifest.py --check
```

Full description, schemas and determinism notes: [docs/DATA.md](../docs/DATA.md).
