#!/usr/bin/env bash
# Enable GitHub Actions on the published branch.
#
# GitHub refuses any commit that touches `.github/workflows/` unless the token
# has the `workflow` scope, so the workflow definitions are staged in `ci/`
# and installed here once that scope is granted:
#
#   gh auth refresh -h github.com -s workflow
#   ./scripts/push_ci.sh
set -euo pipefail
cd "$(dirname "$0")/.."

OWNER=$(gh api /user -q '.login')
REPO=$(git remote get-url origin | sed -E 's#.*github.com/([^/]+)/([^/.]+).*#\2#')

ORIG=$(git rev-parse --abbrev-ref HEAD)
git checkout -q main
mkdir -p .github/workflows
cp ci/ci.yml .github/workflows/ci.yml
cp ci/release-assets.yml .github/workflows/release-assets.yml
git add .github/workflows

if git diff --cached --quiet; then
  echo "Actions are already installed on main"
else
  git commit -q -m "ci: install the Actions workflows staged in ci/"
  git push origin main
  echo "pushed. First run:  gh run list --repo $OWNER/$REPO --limit 5"
fi
git checkout -q "$ORIG"