# Security policy

ETH-WCMK is a research model and a set of generators/validators. It runs no
service, stores no personal data and decides nothing about real individuals: the
corpus is synthetic and the personas are parameterised profiles.

## What we treat as a security issue

- A reproducible way to make the formal core return a verdict that violates a
  stated invariant (I1–I44).
- A SHACL shape that fails to detect an invalid instance (the invalid fixtures
  exist precisely to test this).
- A generator that would ingest real personal data if pointed at a real dataset.
- Any script that executes untrusted input without validation.

## What is not a security issue

- Disagreement with the normative rubric or the ground-truth panels.
- κ below the declared gate: a published limitation, not a vulnerability.

## How to report

Open a private report to the maintainers (README → Contact). For an ordinary
bug, open a public issue with the git revision, the Python version, the exact
command, the artefact produced and its SHA-256 from the manifest.

We acknowledge within 5 working days and ship a fix in the next round.
