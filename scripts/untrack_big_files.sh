#!/usr/bin/env bash
# Untrack the multi-hundred-MB corpora from git so the repository can be pushed
# to GitHub (GitHub rejects files larger than 100 MB, and the recommended
# single-object size is 1 MB). The files stay on disk: they are published as
# compressed release assets and verified by data/CORPUS_MANIFEST.sha256.
#
#   ./scripts/untrack_big_files.sh --dry-run     # show what would be removed
#   ./scripts/untrack_big_files.sh               # actually git rm --cached
set -euo pipefail
cd "$(dirname "$0")/.."

DRY=0
if [[ "${1:-}" == "--dry-run" ]]; then DRY=1; fi

# git ls-tree -l prints: mode blob <sha> <size>\t<path>  → size is field 4 of the first column
mapfile -t files < <(git ls-tree -r -l HEAD | awk -F'\t' '{split($1,a," "); if (a[4] > 100000000) print $2}')

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No tracked file exceeds 100 MB. Nothing to do."
  exit 0
fi

echo "Files above the GitHub 100 MB limit:"
for f in "${files[@]}"; do
  size=$(stat -c %s "$f" 2>/dev/null || echo 0)
  echo "  $(numfmt --to=iec "$size")  $f"
done

if [[ $DRY -eq 1 ]]; then
  echo "dry-run: nothing was removed."
  exit 0
fi

for f in "${files[@]}"; do
  git rm --cached "$f"
done

echo "Untracked. Commit with:"
echo "  git commit -m 'data: corpora moved to release assets (no longer in git)'"
echo "Then verify: python3 scripts/audit_repo.py"
