#!/usr/bin/env bash
# Move the repository to the ETH-WCMK organisation and update every URL.
#
# Prerequisite: the organisation must already exist. GitHub has no API for
# creating one with a regular account, so create it once in the browser:
#   https://github.com/orgs/new
#
# Usage:
#   ./scripts/transfer_repo.sh --org ETH-WCMK
#
# After the transfer GitHub keeps redirecting the old URL, so the release
# assets and existing links keep working.
set -euo pipefail
cd "$(dirname "$0")/.."

ORG="ETH-WCMK"
for a in "$@"; do
  case "$a" in
    --org=*) ORG="${a#--org=}" ;;
    *) echo "usage: transfer_repo.sh --org <organisation>"; exit 1 ;;
  esac
done

OWNER=$(gh api /user -q '.login')
REPO="ETH-WCMK"

if ! gh api "/orgs/$ORG" -q '.login' 2>/dev/null; then
  echo "organisation '$ORG' does not exist yet."
  echo "Create it at https://github.com/orgs/new, then run this script again."
  exit 1
fi

echo "== transferring $OWNER/$REPO -> $ORG/$REPO =="
gh api -X PUT "/repos/$OWNER/$REPO/transfer" -f new_owner="$ORG" -q '.message // "transfer requested"'

# Update the local remote and the citation URLs.
git remote set-url origin "https://github.com/$ORG/$REPO.git"

sed -i "s|github.com/Palazzo13-X/ETH-WCMK|github.com/$ORG/$REPO|g" README.md CITATION.cff docs/*.md
sed -i 's|# will become .* after the transfer||' CITATION.cff

git add README.md CITATION.cff docs
git commit -q -m "chore: repository transferred to the $ORG organisation; URLs updated"
git push origin main

echo "done. New URL: https://github.com/$ORG/$REPO"
echo "the release tag must be re-pointed: ./scripts/sync_main.sh --owner=$ORG --repo=$REPO --tag=v13.0.0"