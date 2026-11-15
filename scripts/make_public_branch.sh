#!/usr/bin/env bash
# Build a clean, publishable branch from the current tree.
#
# Why: the development history still contains blobs of 100-500 MB (the corpora
# committed before the data policy). GitHub rejects pushes containing any object
# larger than 100 MB, so pushing `master` fails. An orphan branch carries only
# the curated tree; the development history stays local or in a private mirror.
#
#   ./scripts/make_public_branch.sh            # creates branch `main`
#   ./scripts/make_public_branch.sh release    # creates branch `release`
set -euo pipefail
cd "$(dirname "$0")/.."
BRANCH="${1:-main}"

if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  echo "branch '$BRANCH' already exists. Remove it with: git branch -D $BRANCH"
  exit 1
fi

ORIG=$(git rev-parse --abbrev-ref HEAD)

git checkout --orphan "$BRANCH"
git add -A
git commit -q -m "ETH-WCMK v13.0.0: formal core, ontologies, evaluation manifests, documentation (corpora published as release assets)"

COUNT=$(git ls-tree -r HEAD | wc -l)
MAX=$(git ls-tree -r -l HEAD | awk -F'\t' '{split($1,a," "); if (a[4] > 100000000) print a[4], $2}')
if [[ -n "$MAX" ]]; then
  echo "WARNING: objects over 100 MB are still reachable from $BRANCH:"
  echo "$MAX"
  echo "Run ./scripts/untrack_big_files.sh and repeat."
  exit 1
fi

git checkout "$ORIG"
echo "branch '$BRANCH' ready: $COUNT files, no object over 100 MB"
echo "push with:  git push -u origin $BRANCH"
