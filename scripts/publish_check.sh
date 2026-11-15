#!/usr/bin/env bash
# Pre-publication gate. Run before every push.
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0

echo "== 1. Repository hygiene =="
python3 scripts/audit_repo.py || fail=1

echo
echo "== 2. Formal core invariants =="
python3 -m pytest _analysis/formal_core/tests -q || fail=1

echo
echo "== 3. Data manifest well-formed =="
python3 scripts/make_data_manifest.py --check --skip-missing || fail=1

echo
echo "== 4. Required documentation =="
for f in README.md LICENSE LICENSE-CC-BY-SA-4.0.txt NOTICE CITATION.cff \
         CHANGELOG.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md \
         .gitignore .gitattributes .editorconfig .pre-commit-config.yaml \
         Makefile pyproject.toml environment.yml requirements.txt requirements-dev.txt \
         ci/ci.yml .zenodo.json docs/ARCHITECTURE.md docs/REPRODUCIBILITY.md docs/DATA.md docs/GATES.md docs/PUBLISHING.md PLANO_ARQUITETURA_GIT.md scripts/make_public_branch.sh data/README.md docs/GATES.md .github/CODEOWNERS .github/ISSUE_TEMPLATE/question.yml .github/ISSUE_TEMPLATE/critique.yml .github/ISSUE_TEMPLATE/verification.yml .github/PULL_REQUEST_TEMPLATE.md ci/release-assets.yml; do
  if [[ -f "$f" ]]; then echo "  ok   $f"; else echo "  MISS $f"; fail=1; fi
done

echo
if [[ $fail -eq 0 ]]; then
  echo "READY TO PUBLISH."
else
  echo "NOT ready: fix the items above before pushing."
  exit 1
fi
