# Auditoria read-only do corpus ETH-WCMK — `_analysis/` (nenhum artefato foi modificado)

Data da auditoria: 2026-10-28 (America/Sao_Paulo). Escopo: `ethcase_seed_v1.jsonl`, `Evaluacoes_tmp_b2.json`, `ethcase_generator.py`, `formal_core.py`, `shacl_runner.py`, `facets_catalog_v1.txt`, `architecture_v1.txt`.

---

## 1. Inventário do corpus

**Arquivo:** `ethcase_seed_v1.jsonl` — 93.759 bytes, **190 registros**, **190 caseId únicos (0 duplicados)**. Gerador: `ethcase_generator.py` (119 linhas, `random.Random(42)` → determinístico).

**Composição:** 160 casos "principais" + 30 sondas degeneradas (`"type":"degenerate"`).

| Dimensão | Distribuição |
|---|---|
| Domínio (10) | 19 casos cada: health, justice_security, critical_infrastructure, finance, privacy_data, public_governance, information_media, education, labour, environment_energy |
| severityBand | low 40, medium 40, high 40, critical 70 (40 principais + 30 sondas, todas "critical") |
| prudentialMode (principais) | elevated 80, standard 48, maximum 32 |
| agencyFamily (principais) | balanced 40, action_oriented 40, normatively_guarded 40, epistemic_reviewer 40 → **só 4 perfis WCMK distintos em todo o corpus** |
| conflictPattern | autonomy_vs_beneficence 27, transparency_vs_safety 27, speed_vs_due_process 27, individual_vs_collective 27, short_term_vs_long_term 26, innovation_vs_precaution 26 |

**Schema exato**
- Caso principal: **17 chaves** — `caseId, domain, severityBand, prudentialMode, agencyFamily, conflictPattern, r[4], lambda[4], U_E, R_c, criticalPillars[], agency[4], deficits[4], Aa, Rr, decision, worstPillar`.
- Sonda degenerada: **10 chaves** — `caseId, domain, severityBand, type, agency, deficits, Aa, Rr, decision, worstPillar`. Faltam 7 (`r, lambda, U_E, R_c, criticalPillars, prudentialMode, agencyFamily, conflictPattern`) → **210 campos ausentes** no total.

**Codificação de r(E) e λ(E)**
- `r`: array de 4 floats (ordem W,C,M,K), 4 decimais = prior do domínio × multiplicadores do conflito.
- `lambda`: array de 4 floats — **idêntico a `r` nos 160/160 casos** (λ = r renormalizado) → λ não carrega informação independente.
- Σλ = Σr ≠ 1 (tolerância 1e-6) em **67/160** casos (desvio máx. +0,001). Nenhum valor fora de [0,1]; λ mínimo 0,1433. Σagency = 1,0 em 190/190.

**Requisitos por faceta (q_f): não existem.** Zero campos de faceta no JSONL. `facets_catalog_v1.txt` (460 linhas) lista **24 códigos** (W1–W5, C1–C6, M1–M6, K1–K7) e propriedades tipo `hasLegalRequirement`, `hasAuditRequirement`, `hasProvenanceRequirement`. `wcmk-facets.ttl` (v0.1-draft) define `Facet`, `FacetRequirement`, `FacetDeficit`, `FacetAssessment`, `CalibrationArtifact` e **5 `AggregationPolicy`** (WeightedMeanCompensatory, GuardedWeightedMean, ThresholdOverride, SoftMinPenalty, UncertaintyPenalizedMean). `ethcase-facet-requirements.ttl` (v0.3-draft) define `CaseRequirementProfile`, `DerivedFacetRequirement`, `RequirementDerivationRule`, `RequirementAggregationProfile` — **sem nenhum valor q_f instanciado**.

**Parâmetros** (θ=0.15, φ=0.25, σ=0.10/0.15/0.22, η=0.90, γ=0.20, ρ=0.15) estão hardcoded no código e **não são serializados** no JSONL.

**Escor agregado (casos principais):** Aa = min 0,5928 / max 0,9875 / média 0,896 / sd 0,121; Rr = min 0,0157 / max 0,3757 / média 0,1058 / sd 0,078; U_E ∈ [0,0909; 0,708]; R_c ∈ [0,135; 0,9025]. Σdeficits média = 0,1623; max deficit médio = 0,1148. Deficit > 0 por pilar: **M 145/160 (90,6%), C 92 (57,5%), W 82 (51,3%), K 40 (25,0%)**. Casos com todos os deficits = 0: **0**. `worstPillar`: M 105, W 30, C 25, **K 0**. `criticalPillars`: 2 pilares em 112 casos, 1 em 48.
**Decisões (principais):** allow 129 (80,6%), allow-with-guards 30 (18,75%), needs-review 1 (0,6%), restrict 0, block 0. **Sondas:** allow-with-guards 12, allow 8, restrict 7, needs-review 3.

---

## 2. Problemas de qualidade detectados

1. **λ redundante:** 160/160 casos com λ ≡ r. A Eq.(2) do paper (re-weighting de requisito e salience por domínio) nunca foi implementada; não existe sensibilidade a λ.
2. **Σλ/Σr ≠ 1 em 67/160 (41,9%)** — artefato de arredondamento a 4 decimais; as invariantes de simplex não são verificadas nem restauradas.
3. **r só depende de (domínio, conflito):** apenas **60 vetores r distintos** entre 160 casos (40 grupos de 3, 20 grupos de 2). `severityBand` e `agencyFamily` não alteram r.
4. **severity quase não altera Aa** (média: low 0,9090; medium 0,8953; high 0,8740; critical 0,9058) → **não monotônico**. R_c escala com severity (0,2265 → 0,7172) e U_E (0,1602 → 0,4867), mas Aa não acompanha porque r, λ e agency são constantes dentro do grupo. O conflito é atribuído por `n % 6`, confundindo severity × conflict.
5. **Limiares de decisão não são exercitados:** max(λ_i·d_i) no corpus = **0,129** (min 0,0072) → a regra de override "λ_i d_i > 0.25 → needs-review" dispara **0** vezes nos 160 casos (640 verificações). Nenhum caso principal chega a restrict/block; 80,6% são "allow".
6. **Piso prudencial vinculante:** em **67/160 casos (41,9%)** Rr = σ·R_c exatamente → nesses casos Aa não tem efeito algum sobre o risco residual. Rr < 0,05 em 41 casos.
7. **Dimensão epistêmica subtestada:** deficit em K só em 40/160 casos; K nunca é `worstPillar`; a penalidade epistêmica nunca é dominante.
8. **Sondas degeneradas estruturalmente pobres:** só 3 perfis ((0.4,0.3,0.3,0.0), (0.35,0.35,0.3,0), (1.0,0,0,0)), todas severity "critical", r implícito (0.25,0.25,0.25,0.25); producem **apenas 4 valores distintos de Aa** {0.2353 (7×), 0.4916 (3×), 0.6197 (12×), 0.8759 (8×)}. `zero_know` e `zero_must` dão Aa idêntico (0,6197) → colapso de discriminção.
9. **Cobertura de domínios vs. paper:** presentes health, education, finance, labour, public administration (public_governance), media (information_media), environment (environment_energy). **Ausentes: transport e research**; "digital security" apenas implícito em privacy_data. Extras sem correspondência nominal: justice_security, critical_infrastructure. Domínios sensíveis (health+finance+privacy_data+critical_infrastructure) = 76/190 (40%), mas **nenhum caso** carrega atributos de sensibilidade/irreversibilidade (`eth:hasDataSensitivity`, `eth:hasIrreversibility` existem na ontologia, 0 instâncias).
10. **Auto-reproducibilidade:** recomputando com `formal_core.py`, a concordância é 160/160 para `deficits`, `Aa`, `decision` e `worstPillar`. `Rr` diverge em **67/160** quando σ não é informado (default 0,10); só coincide com σ inferido de `prudentialMode` (0,15/0,22). Os registros não são reproduzíveis por si sós.

---

## 3. Inventário da avaliação

`Evaluacoes_tmp_b2.json` — 30.103 bytes, lista de **12 registros** com chaves: `label, data, shapes, conforms, error, n_violations, n_violation_triples, report, violations`.

| Resultado | Contagem |
|---|---|
| conforms = True | 7 |
| conforms = False | 4 |
| conforms = None (erro) | 1 — "facetas WCMK": *"A shape defined as a PropertyShape must include one `sh:path` property"* |
| Total de violações | **40** |
| Total de triples de violação | **488** |

Detalhe: `requisitos por faceta` 11 violações/106 triples; `exemplo de requisitos VALIDO` 13/154 (**falso positivo** — o exemplo válido é rejeitado); `exemplo de requisitos INVALIDO` 16/212. **Falso negativo crítico:** `bridge-wcmkplus-scoring-example-invalid.ttl` → `conforms=True`, ou seja, as shapes **não rejeitam** o exemplo deliberadamente inválido. Acerto real da bateria B2: **7/12 = 58,3%**.

**Configurações caso × perfil WCMK executadas: 0.** O JSON não contém Aa, Rr, decision, T, D ou penalty por configuração. O diretório `/Shared/Evaluacoes` está **vazio (0 arquivos)**. Grid implícito: 160 casos × 4 perfis = **640 configurações**; o corpus materializa 160 (25%), mais 30 sondas (1 perfil cada).

**Sensibilidades realmente feitas:** apenas (i) `run_invariants()` — 20.000 amostras Dirichlet aleatórias, seed=1234, critical=("M","K"); (ii) `demo_scenarios()` — 6 cenários manuais comparando v9 vs v2. **Não existe** sweep de λ, adição de facetas, comparação compensatório vs não-compensatório, variação de γ/ρ/η/σ, nem benchmarks.

**Invariantes (20.000 casos):** bounds 0, risk_floor 0, non_compensation 0, tension_bound 0, volume_degeneracy 0, **monotonicity 23 violações** (0,115% dos casos; 23 de ~240.000 pares testados).

---

## 4. Auditoria de `formal_core.py` (303 linhas, 24 funções, "v2-corrected")

**Geometria:** `VILLARS = ("W","C","M","K")`; `P_RAW` = Eq.(5) (tetraedro regular de aresta 1, W na origem); `check_geometry()` verifica ΣV=0, ‖V‖=1, V_i·V_j=−1/3, aresta √(8/3) → **True**; `R_CIRC = √(3/8) = 0,6124`.
- `barycentric_point(a)` = Eq.(7) ✓
- `euclidean_on_simplex(a,b) = (2/√3)‖a−b‖₂`
- `tv_distance(a,b) = ½Σ|a_i−b_i|` = Eq.(3) ✓ (exemplo a=(.4,.3,.2,.1), b=(.1,.2,.3,.4): d_Δ = 0,4; Euclidiano = 0,5164; razão 0,7746)
- `tetra_volume(p,q,r,s)`; `volume_shares(a)` (identidade barycêntrica: a=(.2,.3,.25,.25) → [0.2,0.3,0.25,0.25]) ✓
- `volumetric_coherence(a) = 4·(∏a_i)^{1/4}` → 1,0 balanceado, 0,0 se algum pilar = 0 ✓; `balance_coherence(a) = 4·min(a)` ✓

**Fórmulas centrais**
1. `deficits`: d_i = max(0, r_i − a_i) — Eq.(8a) ✓ (déficit absoluto, não relativo a r_i).
2. `weighted_deficit`: D = Σ λ̂_i d_i + Σ_{i∈critical, d_i>θ} φ, θ=0.15, φ=0.25. **Desvio:** o segundo termo não existe no paper; é um degrau discontinuo (φ por pilar crítico acima de θ), somatório de até 2φ = 0,50, independente de λ; contribui para nenhum caso atingir Aa = 1.
3. `profile_tension`: s_i = min(0, a_i − r_i); T = Σ_{i<j} (1/6)|s_i − s_j|, clipado a [0,1]. **Desvio vs Eq.(4):** só folgas negativas → T = 0 sempre que o perfil cobre todos os requisitos, exatamente onde o risco de compensação é maior.
4. `epistemic_penalty`: U_E·max(0, r_K−a_K)/r_K (guarda r_K ≤ 1e-9). **Desvio vs Eq.(9)** (paper: u = U_E(1−k), absoluto). `adequacy_v9` preserva a fórmula do paper explicitamente "para demonstrar os defeitos".
5. `adequacy`: Aa = clip(1 − D·(1 + γT) − ρ·penalty), γ=0.20, ρ=0.15. Eq.(10) do paper é aditiva (1 − D − γT − ρu); aqui T é multiplicador do déficit.
6. `residual_risk`: Rr = max(R_c(1 − η·Aa), σ·R_c), η=0.90. Piso vinculante em 67/160 casos (41,9%) → Aa irrelevante para Rr nesses casos. `residual_risk_v9 = R_c(1−Aa)` permite erasure total (Rr = 0 quando Aa = 1), defeito reconhecido pelo plano.
7. `decision`: override `λ_i d_i > 0.25 → needs-review` (ordem lexicográfica, antes dos tiers); depois tiers: Aa<0.20 block, <0.40 restrict, <0.60 needs-review, <0.80 allow-with-guards, senão allow. Inconsistência: o override pode rebaixar um caso com Aa ≥ 0.80; o métrico do override (max λ_i d_i) é o mesmo do `worstPillar`. Nunca dispara no corpus (max 0,129 < 0,25).
8. `run_invariants`: 6 invariantes, 20.000 amostras, seed=1234. **Bug de teste:** o teste de non_compensation usa `a2 = a` com `a_j += 0.05` **sem renormalizar** (Σ = 1.05), i.e. verifica uma invariante fora do simplex admissível → "0 violações" é spurio. O teste de monotonicidade renormaliza e **falha 23/20.000**.
9. **Agregação:** compensatória (soma ponderada Σλ_i d_i); a "não-compensação" vem só do clamp `max(0,·)` por pilar e do piso de risco. **Nenhuma** das 5 `AggregationPolicy` da ontologia está implementada; não há modo min/lexicográfico.
10. Não há pytest, assertions sobre o corpus nem harness: `__main__` apenas imprime `demo_scenarios()` e `run_invariants()`.

---

## 5. Lacunas para "baterias ethcase × wcmk"

1. **Grid real nunca executado:** 640 configurações (160×4) ou 760 (+30 sondas). Falta um output por configuração com D, T, penalty, Aa, Rr, tier, worstPillar.
2. **Baselines ausentes:** perfil == r (Aa ideal), uniforme (0.25,0.25,0.25,0.25), pilar único (1,0,0,0), Dirichlet(α) aleatório, perfil adversarial (W alto / M=K=0). Hoje só 4 perfis no corpus e 3 nas sondas.
3. **Sweep de perturbação (B3):** ±0,05 e ±0,10 em cada um dos 4 pilares de a → 640 × 2 magnitudes × 4 pilares × 2 sinais = **5.120 runs**; o critério "ΔAa na direção correta em ≥95%" não pode ser calculado hoje.
4. **Sweep de λ:** impossível com λ ≡ r. É preciso gerar λ independente (ex. Dirichlet: 10 draws × 640 = **6.400 runs**).
5. **Ablação de termos:** só 6 cenários manuais. Falta ablação sistemática (com/sem T, com/sem φ crítico, com/sem penalidade epistêmica, Σλd vs min vs soft-min) sobre os 160/640 casos.
6. **Ablação de agregação:** implementar e comparar as 5 `AggregationPolicy` definidas em `wcmk-facets.ttl` (**0% implementadas**).
7. **Calibração (B4):** grid γ∈{0,0.1,0.2,0.3} × ρ∈{0,0.1,0.15,0.2} × η∈{0.8,0.9,1.0} × σ∈{0.10,0.15,0.22} = **192 combinações × 640 = 122.880 runs** + índices de Sobol. Hoje γ+ρ = 0.35, acima do teto planejado (≤0.30).
8. **Facetas:** 24 códigos, **0 instâncias q_f**. Antes de qualquer bateria facetada, resolver os 40 violações SHACL (11+13+16), o falso positivo do exemplo válido e o falso negativo do exemplo inválido.
9. **Invariantes como testes (B1):** pytest + Hypothesis/fuzzing com shrink de contraexemplos; a monotonicidade já falha (23/20.000) e o teste de non-compensation está mal formulado.
10. **Axioma §6.2 (vértice→aresta→face→volume, R_ij(1)=F_i, Φ|_{f_ij}=T_ijk):** 0 implementações; hoje Aa, T e facet scores são três cálculos independentes.
11. **Reproducibilidade:** serializar σ, θ, φ, η, γ, ρ, versão do core, seed e hash do gerador em cada registro; hoje Rr não é recomputável a partir do JSONL (67/160 divergem).
12. **Formato de saída e estatística:** não há CSV/Parquet, intervalos de confiança, κ inter-avaliador, plots nem sumário; `Evaluacoes/` está vazio e o único artefato de avaliação é um relatório SHACL (B2) sem Aa/Rr/decision.
13. **Cobertura de domínios:** adicionar transport e research e tornar "digital security" explícito; marcar sensibilidade/irreversibilidade por caso (0 instâncias hoje).
14. **Estresse de limiares:** gerar casos com λ_i d_i > 0.25 (impossível no corpus atual, max 0,129) e Aa < 0.40 nos casos principais (0/160 hoje) para exercitar restrict/block.
15. **Consistência numérica:** normalizar r e λ exatamente a 1 antes de serializar (67/160 Σ≠1) e eliminar sondas duplicadas (4 valores de Aa para 30 sondas).

---

## Conclusão numérica

Corpus de **190 casos** sem caseId duplicado, mas com apenas **60 vetores r distintos**, **λ 100% redundante**, **4 perfis WCMK**, **0 configurações caso×perfil avaliadas**, **1 bateria existente** (B2: 12 pares SHACL, 40 violações, 58,3% de acerto, 1 falso negativo e 1 falso positivo), **6 invariantes fuzzadas com 23 violações de monotonicidade**, e **5 políticas de agregação** definidas na ontologia e **nenhuma implementada** no núcleo formal.
