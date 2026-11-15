# Contributing to ETH-WCMK

Thanks for your interest. ETH-WCMK has one rule that overrides everything else:

> **No number in a paper, report or README without an artefact that produced it.**

## Ground rules

1. **Artefact-first.** Every claim ("κ = 0.5336", "1,520 cases") must be traceable
   to a file in `Evaluacoes/<round>/` whose SHA-256 appears in
   `manifest_<round>.json`. Change the core → rerun the batteries → regenerate
   the manifest.
2. **Frozen rounds are immutable.** `Evaluacoes/r2`, `r3` and `r4` are historical
   records. A new revision opens a new round directory; it never edits a frozen
   one.
3. **Decisions are logged.** Modelling decisions go to
   `_analysis/CHANGELOG_DECISIONS.md` (ID, alternatives, justification, artefact,
   gate). Equation changes go to `_analysis/SPEC_vN_equations.md`.
4. **Invariants must pass.** `python3 -m pytest _analysis/formal_core/tests -q`
   (69 tests, ≈ 45 s). A core change that breaks an invariant is rejected unless
   the invariant itself is what is being changed, and that is justified in the
   decision log.
5. **Keep the repository light.** Plain git holds files under 5 MB. Corpora are
   published as compressed release assets (see `docs/DATA.md`). Files between 5
   and 100 MB may use Git LFS.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
make test
```

## Pull requests

- Branch from `main`: `fix/…`, `feat/…`, `battery/…`, `docs/…`.
- Conventional commits: `core:`, `ontology:`, `battery:`, `paper:`, `data:`, `docs:`.
- Attach the artefact your change produces. A PR that moves a published number
  without a manifest entry will be closed.
- Run `make lint && make test` before submitting.

## What a reviewer checks

| Question | Command / artefact |
|---|---|
| Are the invariants preserved? | `pytest _analysis/formal_core/tests -q` |
| Is the ontology still SHACL-valid? | `python3 _analysis/ontology/validate_ontology_v4.py` |
| Is the arithmetic mirror unchanged? | `python3 _analysis/analysis/mirror_full_corpus.py` |
| Are affected paper numbers re-derived? | `python3 _analysis/analysis/paper_artifact_consistency_v13.py` |
| Is the manifest regenerated? | `python3 _analysis/run_all_batteries.py --round r5` |

## Repository layout

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Large datasets are
deliberately kept out of the tree.
