# ETH-WCMK Ontology v2 (release candidate)

Generated, validated artefacts for the semantic layer of the ETH-WCMK model.
Everything in this folder is **machine-generated** from the Python formal core
(`_analysis/formal_core/`), so the RDF and the arithmetic cannot drift apart.

## Modules

| File | Content | Triples |
|---|---|---|
| `01_core.ttl` | Classes, object/data properties, disjointness axioms, provenance hooks | 450 |
| `02_facets.ttl` | 26 facets as `owl:NamedIndividual`, β quartets (Σβ = 1), guard minima, aggregation policy, per-domain criticality | 1 749 |
| `03_domains_context.ttl` | 13 reference domains, 4 severity bands, 3 prudential modes, 3 reversibility levels | 92 |
| `04_pillars_lattice.ttl` | 4 pillars (pairwise disjoint) + 15 face-lattice slots (4 vertices, 6 edges, 4 faces, 1 cell) | 119 |
| `05_calibration.ttl` | `cal:v10`: λ = (.30,.25,.25,.20), 6 edge weights 1/6, 4 face weights 1/4, γ .12, η .05, ω .03, ρ .10, δ .05, budget .35, θ = (.65,.60,.60,.65), hard-veto delta .15, stakes-aware decision bar | 26 |
| `06_decisions.ttl` | 5 decision individuals with permissiveness rank 0–4 | 40 |
| `shapes/facet_and_context_shapes.ttl` | SHACL shapes for facets, guards, domains, criticality, pillars, slots, calibration, decisions, cases, requirements, profiles, confrontations | 339 |
| `fixtures/instance_valid.ttl` | One fully populated confrontation (case IC-0001 × agent-114) computed by the core | 275 |
| `fixtures/instance_invalid.ttl` | Deliberate legacy mistakes (facet as class, β sum 1.3, guardMin 1.2, severity `very_high`, adequacy 1.30, decision `OPEN`, arity-5 slot) | 31 |

Total: **2 815 triples**.

## Validation (battery V, results in `Evaluacoes/r2/ontology_v2_validation.json`)

* SHACL: valid fixture **conformant, 0 violations**; invalid fixture **10 violations**, each attributable to a specific shape.
* SPARQL coherence checks V1–V17 all pass:
  1. every facet's β quartet sums to 1;
  2. each pillar has at least one contributing facet;
  3. facets are individuals, not classes;
  4. facet codes are unique;
  5. the face lattice is complete (15 slots, arities 1–4);
  6. every guard minimum lies in [0.3, 0.9];
  7. the decision vocabulary is closed and totally ordered;
  8. λ, edge weights and face weights each sum to 1;
  9. every recorded confrontation satisfies `R_r = R_c(1 − Aa) + σ R_c` arithmetically;
  10. veto pillars are always declared critical pillars of the case;
  11. every domain has at least one criticality-4 facet;
  12. no requirement references an undefined facet;
  13. requirement coverage spans all 26 facets;
  14. profile pillar values are in [0, 1];
  15. γ + η + ω + ρ + δ ≤ declared penalty budget (0.35);
  16. veto thresholds in [0, 1] and hard-veto delta > 0;
  17. decision-bar coefficients declared and non-negative.
* Legacy comparison: `ethcase-facet-requirements` data fails its own shapes (21 violations); `bridge-wcmkplus.ttl` makes pyshacl raise *"A shape defined as a PropertyShape must include one sh:path property"*; the v1 "invalid" bridge example passes with 0 violations against `wcmk-assessment.shacl.ttl` and `wcmk-profile.shacl.ttl` — evidence that the v1 shapes were inert.

## How to reproduce

```bash
cd _analysis/ontology
python3 gen_ontology_v2.py        # writes the six modules + shapes
python3 gen_fixtures_v2.py        # writes fixtures, computing values from core.py
python3 validate_ontology_v2.py   # SHACL + V1-V17, writes Evaluacoes/r2/ontology_v2_validation.json
```

Requires `rdflib` 7.6 and `pyshacl` 0.40. Note that in pyshacl 0.40 the keyword
is `shacl_graph=`; passing `shapes_graph=` silently falls into `**kwargs` and the
validation runs with no shapes at all (the cause of the v1 "177 conformant / 0
violations" result).

## Known limitations

* OWL consistency is approximated by SHACL + SPARQL: DL-reasoning over the
  tetrahedron arithmetic is not expressible in OWL 2 DL, so normalisation and
  veto semantics are enforced by shapes and queries rather than by a reasoner.
* The geometry layer states the vertex coordinates and the 15 slots as data;
  the distance identities are verified in Python (`geometry.py`), not proven in
  RDF.
