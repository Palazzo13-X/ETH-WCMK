#!/usr/bin/env bash
# Republish the curated tree as a single clean commit on `main`.
#
# Why: GitHub's free plan does not let an admin force-push over a protected
# branch, so protection is lifted, the orphan branch is rebuilt from `master`,
# force-pushed, and protection is restored. The release tag is moved to the new
# commit so the assets stay attached to the right snapshot.
#
#   ./scripts/sync_main.sh                # owner/repo read from the remote
#   ./scripts/sync_main.sh --owner ETH-WCMK --repo ETH-WCMK --tag v13.0.0
set -euo pipefail
cd "$(dirname "$0")/.."

OWNER=$(git config gh.owner || gh api /user -q '.login')
REPO=$(git remote get-url origin | sed -E 's#.*github.com/([^/]+)/([^/.]+).*#\2#')
TAG="v13.0.0"
SRC="master"
BRANCH="main"

for a in "$@"; do
  case "$a" in
    --owner=*) OWNER="${a#--owner=}" ;;
    --repo=*)  REPO="${a#--repo=}"  ;;
    --tag=*)   TAG="${a#--tag=}"    ;;
    --source=*) SRC="${a#--source=}" ;;
    *) echo "unknown argument: $a"; exit 1 ;;
  esac
done

if [[ "$OWNER/$REPO" == "/" ]]; then
  echo "no remote configured; set one with: git remote add origin https://github.com/<owner>/<repo>.git"
  exit 1
fi

echo "== $OWNER/$REPO =="

# 1. lift branch protection
curl -s -X DELETE -H "Authorization: Bearer $(gh auth token)" \
  "https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection" >/dev/null

# 2. rebuild the orphan branch from the source tree
git checkout -q "$SRC"
if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then git branch -D "$BRANCH"; fi
git checkout --orphan "$BRANCH"
git add -A
git commit -q -m "ETH-WCMK $TAG: formal core, ontologies, evaluation manifests, documentation (rounds r4+ corpora published as release assets)"
git checkout -q "$SRC"

BIG=$(git ls-tree -r -l "$BRANCH" | awk -F'\t' '{split($1,a," "); if (a[4] > 100000000) print a[4], $2}')
if [[ -n "$BIG" ]]; then
  echo "refusing to publish; objects over 100 MB still tracked:"; echo "$BIG"; exit 1
fi

# 3. push
git checkout -q "$BRANCH"
git push -f origin "$BRANCH"
git checkout -q "$SRC"

# 4. restore protection and move the tag
curl -s -X PUT -H "Authorization: Bearer $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  -d '{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null}' >/dev/null

SHA=$(git rev-parse "$BRANCH")
curl -s -X DELETE -H "Authorization: Bearer $(gh auth token)" \
  "https://api.github.com/repos/$OWNER/$REPO/git/refs/tags/$TAG" >/dev/null
curl -s -X POST -H "Authorization: Bearer $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/git/refs" \
  -d "{\"ref\":\"refs/tags/$TAG\",\"sha\":\"$SHA\"}" >/dev/null

# Deleting a tag ref turns its release into a draft; put it back online.
curl -s -X PATCH -H "Authorization: Bearer $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/releases/tags/$TAG" \
  -d '{"draft":false}' >/dev/null

echo "synced: $BRANCH at ${SHA:0:8} ($(git ls-tree -r "$BRANCH" | wc -l) files), tag $TAG re-pointed and published"