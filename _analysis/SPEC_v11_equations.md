# SPEC v11 — especificação canônica das equações ETH-WCMK

> **AVISO (rodada 4, v12):** este documento é **histórico**. A fonte canônica atual é
> `_analysis/SPEC_v12_equations.md`. Dois itens aqui estão formalmente superados:
> (i) **S₄ = média geométrica dos déficits** — substituída por `S₄ = min_p d_p`
> (t-norm de Gödel, decisão D1, teste I7b); (ii) **canon de 28 facetas** — ampliado
> para 33 (M8, M9, M10, C8, K9; decisão D4.20). Não citar este arquivo como fonte de
> um número do paper.

**Propósito:** única fonte de verdade entre paper, núcleo Python e ontologia. Cada equação tem: notação, domínio de variáveis, implementação no código e teste que a valida. A notação de v9/v10 tinha colisões (por exemplo `s_f` para score de faceta e `s_p` para share de pilar); aqui ficam resolvidas.

## 0. Notação (normalizada)

| Símbolo | Significado | Domínio | Implementação |
|---|---|---|---|
| `p ∈ {W,C,M,K}` | pilar | — | `PILLARS` |
| `f ∈ F` | faceta (28 em v11) | — | `FACETS` |
| `x_f` | nível observado da faceta no agente | [0,1] | `profile.facet_scores[f]` |
| `r_f` | requisito da faceta para o caso | [0,1] | `case.facet_requirements[f]` |
| `c_f` | criticidade da faceta no domínio | {2,3,4} | `facet.criticality[domain]` |
| `β_fp` | participação da faceta no pilar p | [0,1], Σ_p β_fp = 1 | `facet.beta` |
| `w_f` | peso interno de agregação | ≥ 0 | `facet.weight` |
| `g_f`, `θ_f^g` | guarda dura e mínimo | booleano, [0,1] | `facet.guard`, `guard_min` |
| `c_f^u` | confiança do observador na faceta | [0,1] | `profile.confidence[f]` |
| `ℓ_p` | **nível** do pilar | [0,1] | `project()` |
| `q_p` | **requisito** projetado do pilar | [0,1] | `project()` |
| `d_p` | déficit do pilar | [0,1] | `max(0, q_p − ℓ_p)` |
| `s_p = ℓ_p / Σ_q ℓ_q` | **forma** do perfil (barycentric) | simplex | `confront()["shape"]` |
| `M = Σ_p ℓ_p` | **magnitude** do perfil | [0,4] | `confront()["magnitude"]` |
| `S_E, I_E, P_E` | severidade, irreversibilidade, modo prudencial | [0,1] | `SEVERITY_VALUE`, etc. |
| `U_E`, `R_c` | incerteza epistêmica, risco contextual | [0,1], (0,1] | `case.U_E`, `case.R_c` |

## 1. Camada geométrica (relacional)

**E1 — vértices.** `v_i·v_j = −1/3 (i≠j)`, `Σ_p v_p = 0`, `‖v_p‖ = 1`.
Implementação: `geometry.centred_vertices()`. Teste: `test_I?` em `test_invariants.py` (identidades verificadas numericamente). Corrige o PDF-fonte (centroide impresso como (1/2, √3/4, √6/4) confunde circunraio e inraio; o centroide é 0 no embedding centrado).

**E17 — aresta.** `‖v_p − v_q‖ = √(8/3) ≈ 1.633`.
**E16 — razão de métricas.** Para a métrica euclidiana induzida no simplex centrado: `2/√3 ≤ ‖x(a)−x(b)‖ / (½‖a−b‖₁) ≤ √(8/3)`. **Decisão formal:** o modelo não usa distância de estado; usa o face-lattice como índice relacional. Qualquer afirmação de "distância entre agentes" é eliminada do paper.

**E19 (nova) — sub-volumes.** As coordenadas barycêntricas são exatamente as frações de volume dos sub-tetraedros (`geometry.subvolume_shares`). Isso legitima "coerência volumétrica" apenas como reformulação da forma `s_p`, sem informação adicional.

## 2. Projeção faceta → pilar

**E2 — nível do pilar.**
```
ℓ_p = Σ_f β_fp w_f ṽ_f / Σ_f β_fp w_f
```
onde `ṽ_f` é o valor da faceta **depois da política de agregação** (E20–E23) e das guardas (E24). Em v10 o código só aplicava guardas; em v11 a política é implementada.

**E3 — requisito projetado e déficit.**
```
q_p = Σ_f β_fp w_f r_f / Σ_f β_fp w_f ,   d_p = max(0, q_p − ℓ_p)
```

**E18 — déficit por faceta.** `Δ_f = max(0, r_f − x_f)` (usado em Φ e nos painéis de ground truth).

## 3. Políticas de agregação (implementadas em v11)

**E20 `weighted_mean`** — `ṽ_f = x_f`.

**E21 `guarded_weighted_mean`** — se `g_f` e `x_f < θ_f^g`, o valor contribution é limitado a `x_f` (cap): `ṽ_f = min(x_f, θ_f^g)` quando `x_f < θ_f^g`; caso contrário `x_f`. Semântica: o excesso não compensa a falta.

**E22 `threshold_override`** — se `x_f < θ_f^g`, `ṽ_f = 0` (override não-compensatório); caso contrário `ṽ_f = x_f`.

**E23 `uncertainty_penalized_mean`** — `ṽ_f = x_f · (1 − κ(1 − c_f^u))`, κ = 0.5 default. Quando `c_f^u = 1` (observação confiável) não há penalidade.

**E24 — cap por guarda em todos os pilares compartilhados.** Se `g_f` e `x_f < θ_f^g`, `ℓ_p = min(ℓ_p, x_f)` para todo pilar com `β_fp > 0`. Teste: I14.

## 4. Déficits e termos estruturais

**E4 — déficit ponderado.** `D = Σ_p λ_p d_p`, Σλ = 1, λ = (0.30, 0.25, 0.25, 0.20).

**E5/E6/E7 — S₂, S₃, S₄** (arestas, faces, célula do 3-simplex):
```
S₂ = Σ_{edges} α_pq min(d_p,d_q)      (α = 1/6)
S₃ = Σ_{faces} β_pqr min(d_p,d_q,d_r) (β = 1/4)
S₄ = (∏_p d_p)^{1/4}
```
**Hierarquia provada/algebraicamente verificada:** `S₄ ≤ S₃ ≤ S₂ ≤ max_p d_p` **se** `α_pq ≥ (1/3) Σ_{faces ⊃ edge} β`. Implementada como validação em `Calibration.is_valid()` (E15) e testada em I7.

**E8 — exposição de facetas (anti-diluição).**
```
Φ = Σ_f c_f w_f Δ_f / Σ_f c_f w_f
```

**E9 — penalidade epistêmica.** `u = U_E · d_K / max(q_K, ε)`. Evita divisão por zero e não penaliza excesso de Know (P1.5 de v9 corrigido).

## 5. Adequação, veto e risco

**E10 — adequação bruta.**
```
Aa_raw = clip{ 1 − D − γS₂ − ηS₃ − ωS₄ − ρu − δΦ }
```
Budget declarado: γ+η+ω+ρ+δ ≤ 0.35 (γ=0.12, η=0.05, ω=0.03, ρ=0.10, δ=0.05).

**E11a — déficit guardado (facet-level).** A média de pilar permite que facetas saudáveis compensem uma guarda violada — o que elimina o propósito da guarda. Por isso o veto opera sobre
```
d^guard_p = max( d_p , max_{f : g_f ∧ β_fp > 0} ( r_f − v_f^eff ) )
```
Testes: I14, I18.

**E11b — gap material.** `m(E) = max{ Δ_f : crit(f, dom) = 4 ou g_f }`, com `m(E) ≥ gap_material` considerado shortfall real (não ruído de medição). O pilar correspondente entra no veto mesmo sem `d^guard_p ≥ θ_p`. Testes: I25, I27.

**E11c — conjunto de veto.**
```
V = { p : d^guard_p ≥ θ_p ∧ ( p ∈ criticalPillars(E) ∨ floor_breach_p ) }
    ∪ { p : ∃ f crítica/guardada com Δ_f ≥ gap_material }
```

**E11d — teto proporcional ao risco.**
```
w_cap = cap_base + cap_gain · stakes(E)          (0.5 + 0.5·stakes, ≤ 1)
Aa    = min( Aa_raw , 1 − w_cap · max( m(E), max_{p∈V} d^guard_p ) )
```
se `V ≠ ∅` ou `max(...) ≥ gap_material`. Nenhum gap crítico pode ser "escondido" pela média; porém, a parcela contabilizada cresce com o risco em jogo.

**E11e — hard veto proporcional.**
```
stakes(E) = clip{ 0.5·S_E + 0.3·I_E + 0.2·P_E/0.10 , 0 , 1 }
λ(E)      = 1 + 2·max(0, (stakes_min − stakes(E)) / stakes_min)      ∈ [1, 3]
hard_p    ⇔ d^guard_p ≥ θ_p + Δθ·λ(E)  ou  ( floor_breach_p ∧ stakes(E) ≥ stakes_min )
          ou  ( m(E) ≥ critical_prohibit_gap ∧ stakes(E) ≥ stakes_min )
```
Um hard veto ⇒ PROHIBIT antes de qualquer score. Testes: I19, I23, I24, I26.

**E12 — risco residual.** `R_r = R_c(1 − Aa) + σ(E) R_c`, com `R_r ≥ σ(E)R_c` sempre.
**E14 — piso prudencial.** `σ(E) = clip{σ₀ + σ₁S_E + σ₂I_E + σ₃P_E}` = `0.05 + 0.15·S_E·I_E + P_E`, limitada a [0, 0.35].

**E13 — bar de decisão (stakes-aware).**
```
bar(E) = clip{ b₀ + b₁S_E + b₂I_E + b₃P_E + b₄H_E , 0.30 , 0.90 }
```
(`b₀` base, `b₁` severidade, `b₂` irreversibilidade, `b₃` modo prudencial, `b₄` horizonte).

**E13b/E13c — proportionalidade do ladder.** As duas rotas de proibição (bar e razão de risco) são categóricas e carregam as mesmas gates:
```
categorical(E) ⇔ stakes(E) ≥ stakes_prohibit  ∧  ( m(E) ≥ critical_prohibit_gap )
PROHIBIT ⇔ hard_veto  ou  ( categorical(E) ∧ ( Aa ≤ bar − margin_prohibit  ou  ratio ≥ ratio_prohibit ) )
REVIEW_REQUIRED ⇔ Aa ≤ bar  ou  (V ≠ ∅ ∧ Aa ≤ bar + slack_veto)  ou  ratio ≥ ratio_review
ALLOW_WITH_GUARDS ⇔ Aa ≤ bar + margin_guards  ou  ratio ≥ ratio_guards  ou  V ≠ ∅
ALLOW ⇔ caso contrário
```
`ABSTAIN` precede tudo se cobertura de facetas < 0.70 ou caso incompleto (I10, I22). Justificativa conceitual: **não-compensação se aplica a deveres, não a médias**. Um déficit difuso (muitos deveres levemente abaixo do requisito) é um problema de competência → revisão/guardas; apenas um déficit concentrado num dever crítico do domínio, com risco real, autoriza a proibição categórica.

## 6. Incerteza (v11, E25–E26)

**E25 — déficit intervalar.** Com confiança por faceta, `d_p` tem banda:
```
d_p⁻ = max(0, q_p − ℓ_p⁺) ,  d_p⁺ = max(0, q_p − ℓ_p⁻)
```
onde `ℓ_p⁺/ℓ_p⁻` vêm dos valores otimistas/pessimistas (`x_f ± (1−c_f^u)·x_f(1−x_f)`). Reportado como `Aa_low … Aa_high`; a **decisão usa Aa_low** (precaução) e a banda fica no output.

**E26 — sensibilidade.** `∂Aa/∂c_f` não-negativo: mais confiança observacional nunca piora Aa (testado numericamente, I21).

## 7. Invariantes (número → teste)

| Invariante | Enunciado | Teste |
|---|---|---|
| R1–R6 | integridade do registro de 28 facetas (β soma 1, ≤3 pilares, peso de guarda, criticalidade total, cobertura por domínio) | `test_registry_integrity` |
| I1 | `Aa ∈ [0,1]`, `R_r ∈ [σ R_c, (1+σ)R_c]` | `test_I1_bounds` |
| I2 | `Aa = 1 ⟺ d_p = 0 ∀p` | `test_I2_perfect_adequacy_iff_no_deficit` |
| I3 | piso/teto de risco | `test_I3_risk_floor_and_ceiling` |
| I4 | veto domina o score (`Aa ≤ Aa_raw`, `Aa ≤ 1 − w_cap·gap`) e a decisão | `test_I4_veto_dominates_score_and_decision` |
| I5 | monotonicidade em níveis de faceta | `test_I5_monotonicity_in_facet_scores` |
| I6 | monotonicidade em severidade | `test_I6_severity_monotonicity` |
| I7 | hierarquia estrutural `S₄ ≤ S₃ ≤ S₂ ≤ max d_p` | `test_I7_structural_hierarchy` |
| — | calibração incoerente é rejeitada | `test_calibration_is_valid`, `test_bad_calibration_is_rejected` |
| I8 | faceta compartilhada não é duplamente contada | `test_I8_shared_facet_is_not_double_counted` |
| I9/I9b | níveis uniformes projetam no mesmo nível; guarda abaixo do piso é reportada | `test_I9*`, `test_I9b*` |
| I10 | abstención com dados incompletos | `test_I10_abstention_on_incomplete_data` |
| I11 | invariância à ordem das facetas | `test_I11_facet_order_irrelevance` |
| I12/I12b | continuidade (ΔAa ≤ 0.05 em facetas sem guarda); salto limitado na travessia de guarda | `test_I12*` |
| I13 | determinismo | `test_I13_determinism` |
| I14 | cap/override de guarda bloqueia compensação | `test_I14_guard_cap_blocks_compensation` |
| I15 | Φ impede diluição | `test_I15_facet_exposure_prevents_dilution` |
| I16/I16b | banda de incerteza ordenada e crescente com a confiança; a decisão usa `Aa_low` | `test_I16*` |
| I17/I17b | semântica das políticas (threshold_override, uncertainty_penalized_mean) | `test_I17*` |
| I18 | gap de guarda gera veto em granularidade de faceta | `test_I18_guard_gap_creates_a_facet_level_veto` |
| I19 | hard veto ⇒ PROHIBIT independentemente do score | `test_I19_*` (dentro de I23/I24) |
| I19 | horizonte eleva o bar monotonicamente | `test_I19_horizon_raises_the_bar_monotonically` |
| I20 | `confront_chain` é elo mais fraco | `test_I20_chain_is_weakest_link` |
| I21 | requisito `r_f` monotônico e limitado | `test_I21_requirement_is_monotone_and_bounded` |
| I22 | ABSTAIN abaixo de cobertura com 28 facetas | `test_I22_abstain_below_coverage_with_28_facets` |
| I23 | hard veto proporcional ao risco (E11e) | `test_I23_hard_veto_is_stakes_proportional` |
| I24 | dureza do veto monotônica em stakes | `test_I24_veto_hardness_monotone_in_stakes` |
| I25 | travessia do bar só prohibe com stakes reais (E13b) | `test_I25_bar_crossing_is_prohibitive_only_with_stakes` |
| I26 | stakes baixos nunca escalam um veto para proibição | `test_I26_veto_never_escalates_low_stakes_to_prohibition` |
| I27 | rota do bar exige déficit concentrado em dever crítico (E13c) | `test_I27_bar_route_needs_a_concentrated_duty_failure` |

## 8. Parâmetros e calibração

Todos os parâmetros quantitativos estão declarados em `Calibration` e espelhados em `ontology_v3/05_calibration.ttl` como indivíduos `cal:v11`. **Regra de coerência:** valores do RDF são gerados a partir do Python (nunca ao contrário) e um teste SPARQL/Python compara os dois a 1e-6 (gate G4').
