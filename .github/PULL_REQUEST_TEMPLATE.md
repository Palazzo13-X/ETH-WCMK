## What changed

- [ ] Which layer: core / facet registry / ontology / battery / paper / data
- [ ] Summary of the change

## Artefact evidence (required)

Attach the file this change produces. If a published number moved, give:

| Number | Before | After | Artefact | Manifest entry |
|---|---|---|---|---|
| | | | | |

## Checks run

```bash
python3 -m pytest _analysis/formal_core/tests -q      # 69 tests
python3 scripts/audit_repo.py                          # repo hygiene
python3 _analysis/analysis/paper_artifact_consistency_v13.py
```

- [ ] Invariants pass
- [ ] Ontology still SHACL-valid
- [ ] Arithmetic mirror unchanged (or the change is justified)
- [ ] Manifest regenerated
- [ ] No file above 100 MB is being committed

## Decision log

- [ ] `CHANGELOG.md` entry added
- [ ] Modelling decision recorded in `_analysis/CHANGELOG_DECISIONS.md` (ID + justification)
