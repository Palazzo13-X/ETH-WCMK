# Gate status — every claim mapped to its artefact

The project rule is: **no number enters the paper without an artefact that
measures it.** This table is the audit trail. The full narrative for each gate is
in `_analysis/GATE_REPORT_r5.md`; the raw measurements are in `Evaluacoes/r5/`.

## Round 5 gates (core v13)

| Gate | What it tests | Verdict | Artefact that measures it |
|---|---|---|---|
| G10' | Core v13: unconditional structural hierarchy S2 >= S3 >= S4, derived alpha_e, lambda(E), ReviewNeed, supervision regime | **PASS** | 69 invariant tests (`pytest _analysis/formal_core/tests -q`, 45 s) |
| G11' | 33-facet canon: differentiated beta, guards, measured ablation | **PASS** with an explicit rejection | `_analysis/facets/beta_differentiation_v13.json`, `Evaluacoes/r5/B21_ablation.json` |
| G12' | Is the geometry layer informative? | **PASS** (Psi kept as diagnostic; zeta rejected) | `B20_variant_eval_full_corpus.json`, `B23_sobol_v13.json` |
| G13' | Corpus v7: genuinely incomplete profiles, derived supervision, rebalanced domains | **PASS** | `Evaluacoes/r5/corpus_v7_*`, `corpus_v7_coverage.json` |
| G14' | Ontology v4.2 re-validated (SHACL + SPARQL + arithmetic mirror) | **PASS** (42/42 checks, mirror diff 1.61e-12) | `Ontologias/ontology_v4_2/`, `Evaluacoes/r5/ontology_v4_2_validation.json` |
| G15' | Batteries B20-B26 | **6 of 7 closed**; B24 (LLM anchor) declared infeasible on this machine (D5.15) | per-battery JSON in `Evaluacoes/r5/` |
| G16' | kappa by stratum + human adjudication instrument | **PASS** (instrument issued; human verdicts are external work) | `adjudication_packet_blind.csv`, `ADJUDICATION_PROTOCOL_v13.md` |
| G17' | Paper + manifest + commit | **PASS** (51 artefacts, 22 runs, 65.9 MB) | `Evaluacoes/r5/manifest_r5.json` |
| G18' | Traceability: every paper number has an artefact | **PASS** (166/166 claims in PAPER_v13.md; 177/177 numeric checks on the DOCX) | `paper_consistency_check_v13.json`, `paper_docx_number_trace_v15.json` |
| G19' | Sensitivity of kappa to rubric priors | **PASS** (11 variants, 220,400 pairs, kappa 0.2974-0.6005). G7' is **not** claimed: the variant above 0.60 wins by shared abstention, not better judgement | `Evaluacoes/r5/B26_rubric_sensitivity.json` |
| G20' | Final documentation: EN paper and PT technical report | **PASS** (44/44 references cited; 28 and 31 pages) | `_analysis/PAPER_v14.docx`, `_analysis/RELATORIO_TECNICO_CIENTIFICO_PT.docx` |

Gates G0'-G9' from rounds 2-4 were not redone: they were **re-verified** against
core v13 with the original r2/r3/r4 artefacts preserved, producing
`mirror_full_corpus_v13.json`, `B8_probes_reverified.json` and
`ontology_v4_validation_reverified.json`, all with the same verdicts.

## Declared open items

| Item | Status |
|---|---|
| kappa global 0.5336 below the 0.60 gate | declared, not hidden; kappa = 0.8167 in the unanimous stratum |
| Human panel | instrument issued; independent human adjudication not yet run |
| B24 LLM anchor | not executable on this machine (D5.15) |
| Criticality rebalancing | rejected on measurement: delta kappa = -0.0147 / -0.0050 / -0.0077 |
