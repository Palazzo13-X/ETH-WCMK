# Common targets. Run `make help` for the full list.
PY ?= python3
ROUND ?= r5

.PHONY: help install test lint batteries corpus ontology audit data verify paper clean

help:
	@grep -E '^[a-z]+:.*#' Makefile | sed 's/:.*# /  → /'

install:  # install the pinned dependencies
	$(PY) -m pip install -r requirements.txt -r requirements-dev.txt

test:     # the 69 invariant tests (~45 s)
	$(PY) -m pytest _analysis/formal_core/tests -q

lint:     # style and static checks
	$(PY) -m ruff check _analysis scripts || true

batteries: # run the whole evaluation round and write the manifest
	$(PY) _analysis/run_all_batteries.py --round $(ROUND)

corpus:   # regenerate the corpus deterministically (seed 20261104)
	$(PY) _analysis/run_all_batteries.py --round $(ROUND) --corpus

ontology: # generate and validate the ontology
	$(PY) _analysis/ontology/gen_ontology_v5.py
	$(PY) _analysis/ontology/validate_ontology_v4.py

audit:    # repository hygiene report (sizes, tiers, missing docs)
	$(PY) scripts/audit_repo.py

data:     # build the compressed release assets for GitHub Releases
	$(PY) scripts/build_release_assets.py

verify:   # check every artefact against the published manifest
	$(PY) scripts/make_data_manifest.py --check

paper:    # re-derive every number in the paper from the artefacts
	$(PY) _analysis/analysis/paper_artifact_consistency_v13.py

clean:    # remove caches and regenerable intermediates
	rm -rf .cache_validation .pytest_cache _analysis/crops _analysis/pages release_assets
