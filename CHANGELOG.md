# Changelog

All notable changes to this project are documented here, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The model version is the major.minor of the arithmetic core: core v13 → `13.0.0`.
Each round is stamped in `Evaluacoes/<round>/manifest_<round>.json`, which
records the SHA-256 of every artefact and the git revision the numbers were
computed from.

## [13.0.0] — 2026-11-13 (round 5 · corpus v7 · ontology v4.2)

### Added
- Invariant suite extended to **69 tests (I1–I44)**: `I34`–`I44` cover the
  unconditional hierarchy `S2 ≥ S3 ≥ S4`, derived edge weights α_e, the
  oversight regime λ(E), `ReviewNeed`, and the declared-coverage gate.
- **Ontology v4.2** revalidated: 42/42 SPARQL + SHACL checks pass; arithmetic
  mirror diff 1.61 × 10⁻¹² on the sampled graph with 0 verdict divergences;
  lattice census 15/15; RDF↔CSV↔Python registry: 0 mismatches.
- Batteries **B20–B26**: variant evaluation, β ablation, fact-contradiction
  probe, Sobol/Morris sensitivity on v13, full-corpus mirror (220,400 pairs),
  LLM anchor (declared infeasible on the reference machine, D5.15), and
  rubric-prior sensitivity of κ.
- Human adjudication instrument: `adjudication_packet_blind.csv`,
  `adjudication_packet_key.csv`, sample-power analysis, and
  `_analysis/ADJUDICATION_PROTOCOL_v13.md`.
- Paper v14 (EN) + technical report (PT): notation table, full citation layer,
  traceability 166/166 numeric claims → artefacts.
- `CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `Makefile`, `pyproject.toml`, `environment.yml`, CI workflow and issue/PR
  templates (publication layer).

### Changed
- Edge weights are now **derived**: `α_e = (1/3) Σ_{f∃e} β_f`, so the hierarchy no
  longer depends on a parameter condition. With `β_f = 1/4`, `α_e = 1/6` —
  exactly the value already calibrated, so no published number changes.
- Ten of the 33 facets reweighted; β-identical facet pairs 8 → 1.
- Criticality rebalancing **rejected** on measured Δκ (aggressive −0.0147,
  mild −0.0050, targeted −0.0077).

### Known open items
- κ (model ↔ panel): 0.5336 global, 0.8167 unanimous stratum, 0.1371 majority
  stratum, 0.0526 contested. Gate G7 (κ ≥ 0.60) is **not** declared met: the
  variant reaching 0.6005 achieves it by shared abstention, not by better
  judgment (D5.24).
- B24 (LLM anchor) is infeasible on the reference machine, declared as such.

## [12.0.0] — 2026-11-06 (round 4 · corpus v6 · ontology v4.1)

### Fixed
- Structural layer: `S4 = (∏d)^{1/4}` violated `S4 ≤ S3` in 9,991/10,000 grid
  points → replaced with `S4 = min_p d_p` (Gödel t-norm), proven by exhaustion.
- Redundant risk: `R_r/R_c = 1 − Aa + σ` → `R_r = R_c·(p_fail+σ)/(1+σ)`,
  `p_fail = 1 − Σμ_p ℓ_p` (I2, I3, I28, I29).
- Guards became universal caps: a pillar can no longer exceed the observed level
  of a violated duty (I18, I33).
- Decision uses `adequacy_decision = Aa_low` instead of the central value (I32).
- Epistemic abstention made operational (I31): 14,703 ABSTAIN, all E29.
- Verdict hysteresis added (I30).
- `load_fitted_calibration()` wired into the runner.
- Stakes include the horizon term: 0.45/0.30/0.15/0.10 (D4.13).

### Added
- Round runner `run_all_batteries.py` with a SHA-256 manifest (G9).
- Full-corpus arithmetic mirror: 183,920 confrontations, diff 0.0 (B19).
- Paper–artefact consistency checker: 44/44 claims verified (B18).
- Delta study: 33,800 of 72,960 verdicts change (46.3%), largest class
  `PROHIBIT → REVIEW_REQUIRED`.

## [11.0.0] — 2026-11-02 (round 3 · corpus v4)

- Facet registry v11 (28 facets, up to 3 pillars, `Σβ = 1`), dual corpus
  (stress layer A + semantic layer B), hybrid ground-truth kernel.
