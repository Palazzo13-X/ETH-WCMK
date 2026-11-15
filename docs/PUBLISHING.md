# Runbook: publishing ETH-WCMK on GitHub

Work through the phases in order. All commands run from
`/home/luiz/Documentos/Strata/Shared`.

## Status (2026-11-15)

| Item | State |
|---|---|
| Clean branch `main` (668 files, ~122 MB tracked, 0 blobs > 100 MB) | **pushed** |
| Repository | **live**: `https://github.com/Palazzo13-X/ETH-WCMK` (public) |
| Description, 13 topics, issues on, wiki off | **done** |
| `main` protected | **done** (status checks added once CI exists) |
| Release `v13.0.0` with 20 corpus assets (104.5 MB) | **done** |
| `ETH-WCMK` organisation | **not created** — GitHub exposes no org-creation endpoint for regular users; create it in the browser at <https://github.com/orgs/new>, then transfer the repository (Settings → Transfer). GitHub keeps redirecting the old URL. |
| CI workflow files | **pending** — pushing files under `.github/workflows/` requires the `workflow` scope, which this token does not have: `gh auth refresh -h github.com -s workflow` |
| Zenodo DOI | pending the release |

To move the published repository into the organisation later:

```bash
gh api -X PUT /repos/Palazzo13-X/ETH-WCMK/transfer -f new_owner=ETH-WCMK
```

Repo transfer keeps stars, issues, releases and assets, and `github.com/Palazzo13-X/ETH-WCMK`
redirects to the new location.

## Phase 0 — backup first

```bash
git bundle create ../ETH-WCMK-backup.bundle --all      # whole history, one file
git bundle verify ../ETH-WCMK-backup.bundle
```

## Phase 1 — decide the repository identity

Verified on this machine with the GitHub CLI (`gh auth status`, 2026-11-15):
the authenticated account is **`Palazzo13-X`**, which has three public
repositories (`Palazzo13-X.github.io`, `WCMK`, `QPDS`). No organisation named
**ETH-WCMK** exists yet, and `Palazzo13-X/WCMK` is a 3 KB placeholder created on
2026-03-09 (one README plus a `code/policy` folder).

The paper already cites `github.com/ETH-WCMK/ETH-WCMK`, so pick one:

| Option | URL | Trade-off |
|---|---|---|
| **Create the `ETH-WCMK` organisation** (recommended) | `github.com/ETH-WCMK/ETH-WCMK` | matches the paper; free with a personal account |
| Rename `Palazzo13-X/WCMK` → `ETH-WCMK` | `github.com/Palazzo13-X/ETH-WCMK` | GitHub redirects the old name, but the URL no longer matches the paper |
| New repository under the personal account | `github.com/Palazzo13-X/ETH-WCMK` | requires updating the URL in the paper, `CITATION.cff` and the README |

Option 1 from the command line:

```bash
gh api -X POST /orgs -f login=ETH-WCMK
gh repo create ETH-WCMK/ETH-WCMK --public \
  --description "Formal core + SHACL ontology for auditing delegated ethical agency: 69 invariants, a 220,400-confrontation corpus, FAIR data."
```

Do **not** tick "Add a README" and do **not** choose a `.gitignore` template:
the tree already ships both.

## Phase 2 — make the tree publishable

```bash
python3 scripts/audit_repo.py                        # sizes, tiers, missing docs
./scripts/untrack_big_files.sh --dry-run             # preview
./scripts/untrack_big_files.sh                       # git rm --cached the >100 MB artefacts
git add .
git commit -m "data+docs: publication layer; corpora moved to release assets"
python3 scripts/audit_repo.py                        # must report 0 blockers
```

If the audit still shows blobs **in history** (`.git` is 223 MB because the
corpora were committed before), choose one:

**A — clean orphan branch (recommended, non-destructive)**

```bash
./scripts/make_public_branch.sh          # creates branch `main` from the current tree
git checkout main
git ls-tree -r -l HEAD | awk -F'\t' '{split($1,a," "); if (a[4] > 100000000) print $2}'  # must print nothing
```

Only this branch's objects get pushed; the heavy blobs stay in `master` locally.
The branch is already built in this repository (`main`, 666 files, 83 MB).

**B — rewrite the history (keeps the 17 commits, drops the blobs)**

```bash
pip install --user git-filter-repo       # PEP 668: add --break-system-packages if needed
git filter-repo --path-glob 'Evaluacoes/*/corpus_*_confrontations.jsonl' \
                --path-glob 'Evaluacoes/*/corpus_*_gold.jsonl' \
                --path-glob 'Ontologias/**/instances.ttl' \
                --path '.cache_validation' --invert-paths
```

Never run B without Phase 0.

## Phase 3 — identity and push

```bash
git config user.name  "Luiz M. M. Palazzo"
git config user.email "your-github-email@example.com"
git remote add origin https://github.com/<OWNER>/ETH-WCMK.git
git push -u origin main
```

Expected: ~45 MB pushed, no 100 MB rejection.

## Phase 4 — repository settings (the "About" panel)

- **Description**: as in Phase 1.
- **Website**: `https://github.com/ETH-WCMK/ETH-WCMK/releases` until a docs site
  exists.
- **Topics**: `ai-ethics`, `deontic-logic`, `rdf`, `shacl`, `ontologies`,
  `reproducibility`, `fair-data`, `governance`, `audit`, `formal-verification`.
- **Settings → Branches**: protect `main` (require a PR and a passing CI check).

## Phase 5 — the release with the data

```bash
python3 scripts/build_release_assets.py        # 20 assets, 104.5 MB total
```

1. **Releases → Draft new release** → tag `v13.0.0`, target `main`.
2. Title: "ETH-WCMK v13 (round 5, corpus v7, ontology v4.2)".
3. Body: the three headline numbers (69 invariants; 220,400 confrontations;
   κ = 0.5336) plus links to `docs/REPRODUCIBILITY.md` and `docs/DATA.md`.
4. Attach every file in `release_assets/` (largest is 40.9 MB — GitHub allows
   2 GiB per asset).
5. Publish, then add the release URL to the README.

## Phase 6 — persistent identifier (recommended for a paper)

1. zenodo.org → New → **Deposit** → link the GitHub repository.
2. Zenodo reads `.zenodo.json`; each release tag gets its own DOI.
3. Put the DOI in `CITATION.cff` and in the README.

## Phase 7 — badges and CI

Once the first Actions run is green, add at the top of the README:

```markdown
[![CI](https://github.com/<OWNER>/ETH-WCMK/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/ETH-WCMK/actions/workflows/ci.yml)
![tests](https://img.shields.io/badge/invariant%20tests-69-green)
![release](https://img.shields.io/github/release/ETH-WCMK/ETH-WCMK.svg)
![zenodo](https://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXX-blue)
```

## Phase 8 — final gate before announcing

```bash
./scripts/publish_check.sh
```

It runs the audit, the 69 tests, the manifest check and the documentation
inventory. Ship only when it prints `READY TO PUBLISH`.
