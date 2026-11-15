# SPEC v12 — especificação canônica das equações ETH-WCMK (Rodada 4)

**Propósito:** única fonte de verdade entre paper, núcleo Python e ontologia. Esta versão
substitui `SPEC_v11_equations.md` (mantida como histórico). Cada equação tem notação,
domínio, implementação e teste. As correções em relação à v11 estão marcadas **[v12]**
e cada uma tem artefato de evidência em `Evaluacoes/r4/`.

---

## 0. Notação (normalizada)

| Símbolo | Significado | Domínio | Implementação |
|---|---|---|---|
| `p ∈ {W,C,M,K}` | pilar | — | `PILLARS` |
| `f ∈ F` | faceta (33 no canon v12) | — | `FACETS` |
| `x_f` | nível observado da faceta no agente | [0,1] | `profile.facet_scores[f]` |
| `r_f` | requisito da faceta para o caso | [0,1] | `case.facet_requirements[f]` |
| `c_f` | criticidade da faceta no domínio | {2,3,4} | `facet.criticality[domain]` |
| `β_fp` | participação da faceta no pilar p | [0,1], Σ_p β_fp = 1, β_fp ∈ {0} ∪ [0.15,1] | `facet.beta` |
| `g_f`, `θ_f^g` | guarda dura e mínimo | booleano, [0,1] | `facet.guard`, `guard_min` |
| `c_f^u` | confiança do observador na faceta | [0,1] | `profile.confidence[f]` |
| `ℓ_p` | **nível efetivo** do pilar (com piso lexicográfico, E24) | [0,1] | `project()` |
| `q_p` | **requisito** projetado do pilar | [0,1] | `project()` |
| `d_p` | déficit do pilar | [0,1] | `max(0, q_p − ℓ_p)` |
| `s_p = ℓ_p / Σ_q ℓ_q` | **forma** do perfil (barycentric) | simplex | `confront()["shape"]` |
| `M = Σ_p ℓ_p` | **magnitude** do perfil | [0,4] | `confront()["magnitude"]` |
| `S_E, I_E, P_E, H_E` | severidade, irreversibilidade, modo prudencial, horizonte | [0,1] | `SEVERITY_VALUE`, `REVERSIBILITY`, `PRUDENTIAL_VALUE`, `HORIZON_VALUE` |
| `U_E`, `R_c`, `E` | incerteza epistêmica, risco contextual, escala de exposição | [0,1], (0,1], [0,1] | `case.U_E`, `case.R_c`, `case.exposure` |

---

## 1. Camada geométrica (índice relacional, não métrica de estado)

**E1 — vértices.** `v_i·v_j = −1/3 (i≠j)`, `Σ_p v_p = 0`, `‖v_p‖ = 1`.
Implementação: `geometry.centred_vertices()`. Corrige o PDF-fonte (centroide impresso
como (1/2, √3/4, √6/4) confunde circunraio com inraio).

**E17 — aresta.** `‖v_p − v_q‖ = √(8/3) ≈ 1.633`.
**E16 — razão de métricas.** `2/√3 ≤ ‖x(a)−x(b)‖ / (½‖a−b‖₁) ≤ √(8/3)`.
**Decisão formal (D4.4):** o modelo **não** usa distância entre agentes. O face-lattice
do 3-simplex (isomorfo às subconjuntos não vazios de um set de 4) é usado como índice
relacional dos modos de falha conjunta. O termo "distância de estado" é eliminado do paper.

**E19 — sub-volumes.** As coordenadas barycêntricas são exatamente as frações de volume
dos sub-tetraedros (`geometry.subvolume_shares`): "coerência volumétrica" não adiciona
informação além de `s_p`. Declarado como redundância identificada, não como camada.

---

## 2. Projeção faceta → pilar

**E2 — nível do pilar.**
```
ℓ̄_p = Σ_f β_fp ṽ_f / Σ_f β_fp
```
`ṽ_f` = valor da faceta após a política de agregação (E20–E23).

**E24 [v12] — piso lexicográfico universal.** Para toda faceta guardada (`g_f`) com
`ṽ_f < θ_f^g`:
```
ℓ_p = min( ℓ̄_p , ṽ_f )      para todo p com β_fp > 0
```
Em v11 o cap só era aplicado às facetas com política `guarded_weighted_mean`, de modo
que uma faceta com `threshold_override` (C3 = 0) podia ser compensada pela média do
mesmo pilar: nível C = 0.929 com uma guarda zerada. **[v12]** o piso vale para todas
as 9 guardas. Testes: I18, I33 (9 guardas × pilares com β > 0).
Semântica: um pilar não pode ser creditado acima do nível que o agente efetivamente
demonstrou na duty mais dura que aquele pilar contém. A monotonicidade continua
valendo: aumentar `x_f` nunca reduz `ℓ_p` (I5).

**E3 — requisito projetado e déficit.**
```
q_p = Σ_f β_fp r_f / Σ_f β_fp ,   d_p = max(0, q_p − ℓ_p)
```

**E18 — déficit por faceta.** `Δ_f = max(0, r_f − band(x_f, c_f^u, mode))`.
Notar que o gap que alimenta o veto e Φ usa o **nível observado ajustado por
confiança**, não o valor corrigido pela política (E11e de v11, mantido).

---

## 3. Políticas de agregação

**E20 `weighted_mean`** — `ṽ_f = x_f`.
**E21 `guarded_weighted_mean`** — se `g_f ∧ x_f < θ_f^g`, `ṽ_f = min(x_f, θ_f^g)`.
**E22 `threshold_override`** — se `x_f < θ_f^g`, `ṽ_f = 0`; caso contrário `x_f`.
**E23 `uncertainty_penalized_mean`** — `ṽ_f = x_f · (1 − κ(1 − c_f^u))`, κ = 0.5.
E24 (acima) é orthogonal a estas políticas: a política define o valor contribution;
E24 define o teto do pilar.

---

## 4. Déficits e termos estruturais

**E4 — déficit ponderado.** `D = Σ_p λ_p d_p`, Σλ = 1, λ = (0.30, 0.25, 0.25, 0.20).

**E5/E6/E7 [v12] — S₂, S₃, S₄.** Definamos o *déficit conjunto* de um subconjunto
A ⊆ {W,C,M,K} como
```
δ(A) = min_{p ∈ A} d_p
```
(t-norm de Gödel: o déficit simultaneamente presente em todos os pilares de A — a
semântica de deveres que devem ser cumpridos **todos**). Então
```
S₂ = Σ_{|A|=2} α_A δ(A)      α = 1/6 (uniforme)
S₃ = Σ_{|A|=3} β_A δ(A)      β = 1/4 (uniforme)
S₄ = δ({W,C,M,K}) = min_p d_p
```

**Proposição 1 (hierarquia).** Se Σα = Σβ = 1 e `α_e ≥ (1/3) Σ_{f ⊃ e} β_f` para toda
aresta e, então
```
min_p d_p  ≤  S₃  ≤  S₂  ≤  max_p d_p .
```
*Prova.* (i) Cada face contém o mínimo global, logo S₃ ≥ min d. (ii) Para cada face f,
`δ(f) = min_{e ⊂ f} δ(e) ≤ (1/3) Σ_{e ⊂ f} δ(e)`; somando com β e trocando a ordem,
`S₃ ≤ Σ_e δ(e) (1/3) Σ_{f ⊃ e} β_f ≤ Σ_e α_e δ(e) = S₂`. (iii) `S₂ ≤ max d` porque
Σα = 1 e cada δ(e) ≤ max d. ∎
Verificação por exaustão: grid de 21⁴ pontos + 200.000 vetores aleatórios com pesos
não-uniformes válidos (teste I7b).

**Contraexemplo da v11 (registrado):** com S₄ = (∏_p d_p)^{1/4} e d = (0.5,0.4,0.3,0.2),
S₂ = 0.2667, S₃ = 0.2250, S₄ = 0.3310 → S₄ > S₃. Sobre uma grade de 10⁴ pontos,
9.991/10.000 violavam S₄ ≤ S₃. Artefato: `Evaluacoes/r4/delta_v12.json`.

**E8 — exposição de facetas (anti-diluição).**
```
Φ = Σ_f c_f Δ_f / Σ_f c_f
```
(Em v11 e v12.0 aparecia `w_f`, o peso interno de agregação, dentro da soma: `Σ c_f w_f Δ_f / Σ c_f w_f`. Como `w_f = 1,0` em 33/33 facetas, o termo era inerte e foi eliminado por D4.17; a aritmética é idêntica, verificada por regressão sobre 6.000 confrontações.)
**E9 — penalidade epistêmica.** `u = U_E · d_K / max(q_K, ε)`.

---

## 5. Adequação, veto e risco

**E10 — adequação bruta.**
```
Aa_raw = clip{ 1 − D − γS₂ − ηS₃ − ωS₄ − ρu − δΦ }
```
Budget declarado: γ+η+ω+ρ+δ ≤ 0.35 (γ=0.12, η=0.05, ω=0.03, ρ=0.10, δ=0.05).

**E11a — déficit guardado.**
```
d^guard_p = max( d_p , max_{f : g_f ∧ β_fp > 0} (r_f − band(x_f)) )
```
**E11b — gap material.** `m(E) = max{ Δ_f : c_f = 4 ou g_f }`.
**E11c — conjunto de veto.**
```
V = { p : d^guard_p ≥ θ_p ∧ (p ∈ criticalPillars(E) ∨ floor_breach_p) }
    ∪ { p : ∃ f crítica/guardada com Δ_f ≥ gap_material }
```
**E11d — teto proporcional ao risco.**
```
w_cap = cap_base + cap_gain·stakes(E)
Aa = min( Aa_raw , 1 − w_cap·max( m(E), max_{p∈V} d^guard_p ) )     se V ≠ ∅ ou gap ≥ gap_material
```
**E11e — hard veto proporcional.**
```
s(E) = 1 + 2·max(0, (stakes_min − stakes(E)) / stakes_min)      (escala de proporcionalidade)
hard_p ⇔ p ∈ V  ∧  [ d^guard_p ≥ θ_p + Δθ·s(E)
                    ∨ (floor_breach_p ∧ stakes(E) ≥ stakes_min) ]
       ∨ [ m(E) ≥ critical_prohibit_gap ∧ stakes(E) ≥ stakes_min ∧ β_fp > 0 ]
```
Correção de notação (auditoria, item 28): a escala proporcional era chamada `λ(E)`, o
que colidia com os pesos de pilar `λ_p`. Os `λ_p` são **constantes calibradas** e não
dependem do caso; `λ(E)` como função do caso não existe no núcleo e foi retirada do
paper. A escala passa a denominarse `s(E)` (em código: `scale`, `core.py:440`).

**E11f [v12] — stakes com horizonte.**
```
stakes(E) = clip{ 0.45·S_E + 0.30·I_E + 0.15·(P_E/0.10) + 0.10·H_E , 0, 1 }    (Σ coef. = 1)
```
Motivo: o horizonte aparecia só na barra de decisão, nunca no risco — um dano que se
materializa numa geração era tratado como equivalente a um dano imediato. Os painéis
de ground truth importam esta função (fonte única); não re-implementam a fórmula.

**E12 [v12] — risco residual independente da adequação.**
```
p_fail(E,ℓ) = clip( 1 − Σ_p μ_p ℓ_p , 0.02, 0.98 )      μ = (0.15, 0.40, 0.20, 0.25)
R_r(E,ℓ)    = R_c · (p_fail + σ(E)) / (1 + σ(E))
ratio(E,ℓ)  = (p_fail + σ(E)) / (1 + σ(E)) ∈ [σ/(1+σ), 1]
harm(E)     = R_c · stakes(E) · E
```
**Proposição 2 (propriedades).** `σR_c/(1+σ) ≤ R_r ≤ R_c`; `R_r` é strictly decrescente
em confiabilidade; `R_r = R_c` quando `p_fail = 1`; o piso nunca é apagado pela
adequação ("atenuação sem extinção").
**Proposição 3 (não-redundância).** Em v11, `ratio = 1 − Aa + σ` exatamente, i.e. a
"rota da razão" do ladder era um segundo limiar sobre a mesma quantidade. **[v12]**
existem perfis com adequação idêntica e risco distinto: ℓ = (0.60,0.40,0.60,0.60) e
ℓ' = (0.60,0.60,0.40,0.60) têm D, S₂, S₃, S₄ idênticos (déficit único, mesmo λ_C = λ_M)
e `p_fail` = 0.48 vs 0.44. Testes: I28 (902 buckets de mesma Aa com ratio distinto,
spread máximo 0.505 no corpus r3) e I29 (witness determinístico). Artefato:
`Evaluacoes/r4/delta_v12.json`.

**E14 — piso prudencial.** `σ(E) = clip{0.05 + 0.15·S_E·I_E + P_E, 0, 0.35}`.

**E13 — bar de decisão (stakes-aware).**
```
bar(E) = clip{ b₀ + b₁S_E + b₂I_E + b₃P_E + b₄H_E , 0.30, 0.90 }
```

**E13b/E13c — proportionalidade do ladder.**
```
categorical(E) ⇔ stakes(E) ≥ stakes_prohibit ∧ m(E) ≥ critical_prohibit_gap
PROHIBIT ⇔ hard_veto ∨ ( categorical(E) ∧ (Aa ≤ bar − margin_prohibit ∨ ratio ≥ ratio_prohibit) )
REVIEW_REQUIRED ⇔ Aa ≤ bar ∨ (V ≠ ∅ ∧ Aa ≤ bar + slack_veto) ∨ ratio ≥ ratio_review
ALLOW_WITH_GUARDS ⇔ Aa ≤ bar + margin_guards ∨ ratio ≥ ratio_guards ∨ V ≠ ∅
ALLOW ⇔ caso contrário
```

**E13d [v12] — histerese.** Se `previous` é dado, o veredito **não** pode tornar-se mais
permissivo a menos que `Aa_low ≥ bar + hysteresis` (hysteresis = 0.05). Endurecer
nunca é bloqueado. Justificativa: um sistema de governança que alterna
`ALLOW_WITH_GUARDS` ↔ `REVIEW_REQUIRED` a cada medição não é operacional. Teste I30;
evidência do problema na bateria B12 (r3).

**E29 [v12] — abstención epistêmica.**
```
ABSTAIN ⇔ (norm_conflict(E) ≠ "none" ∨ evidence_conflict(E)) ∧ U_E ≥ 0.60 ∧ ℓ_K ≤ 0.65
```
Semântica: quando o dever aplicável é genuinamente contestado e o agente não tem
conhecimento para resolvê-lo, o veredito correto é escalar a humanos, não permitir ou
proibir. Em v11, ABSTAIN disparava 0 vezes em 74.480 confrontações (dependia só de
cobertura). Teste I31.

**E25 — déficit intervalar.** Com confiança por faceta, bandas `ℓ_p⁺/ℓ_p⁻` e
`Aa_low … Aa_high`. **[v12]** a decisão usa `Aa_low` e o output reporta
`adequacy_decision = Aa_low` explicitamente. Em v11 reportava-se `Adequacy` central e
decidia-se pela inferior: 1.239 casos "Aa = 1.000 → PROHIBIT" e 1.941 "Aa = 1.000 →
REVIEW_REQUIRED" no corpus r3. Teste I32.

---

## 6. Agência em camadas

**E28.** `confront_chain(case, [model, system, operator])` = elo mais fraco; cada
camada mantém sua adequacy; a decisão usa o mínimo. O elo mais fraco deve ser
reportado (`worst_layer`) — não apenas o mínimo.

---

## 6.5 Ancoragem por observação (E30) — introduzida na v12

O núcleo recebe um **perfil declarado**. Um fato verificável do caso é uma
observação da faceta que nomeia, e limita o nível que essa faceta pode ter:

**E30.**  ℓ_f ← min(ℓ_f, q_f · c(fato)),  c ∈ [0,1] declarado por fato
(`_analysis/formal_core/fact_grounding.py`), com knob de força s ∈ [0,1]:
ℓ_f ← min(ℓ_f, q_f·[1 − s(1 − c)]).  s = 0 reproduz a v11; s = 1 é o padrão.
**E31 [v12] — histerese da decisão (formalização de E13d).**
```
veredito_new = veredito_previous   se   perm(veredito_new) > perm(veredito_previous)
                                      e  Aa_low < bar(E) + h
```
onde `perm` é a ordem ABSTAIN < PROHIBIT < REVIEW_REQUIRED < ALLOW_WITH_GUARDS <
ALLOW, e `h = 0,05`. Endurecer nunca é bloqueado; afrouxar exige superar a barra por
histerese. Implementação: `decide(..., previous_decision=...)` em
`_analysis/formal_core/core.py` (E13d); invariante I13; medido em B12 (`B12_temporal_v12.json`:
103 oscilações A–B–A evitadas e 6.382 transições mais permissivas bloqueadas).

Fatos mapeados: logs/audit → M6; notice → M8; revisão humana e apelação → M9;
consentimento e consulta a trabalhadores → M10; minimização de dados → C8;
revisão/sunset → K9; contenção exercida → C7; incidentes previos → C6;
possibilidade de saída → C3; dias de remedy → M7.
Fatos sem âncora de faceta estão declarados explicitamente (`UNANCHORED_FACTS`):
`affected_people` entra apenas pela exposição (E12′).

Motivo (evidência): 75,8% da discordância modelo↔painel na corpus v5 era REVIEW
do modelo contra PROHIBIT do painel, e o painel motivava essa escalada por fatos
que nenhuma faceta observava. Com E30 e as cinco facetas procedurais (M8, M9, M10,
C8, K9 — D4.20), κ modelo↔painel sobre as *mesmas* observações sobe de 0.198 para
0.390 (sweep completo em `Evaluacoes/r4/fact_grounding_sweep.json`).

**Monotonicidades testadas (G1–G7, `tests/test_fact_grounding.py`):** grounding nunca
eleva um nível; um fato com c = 1 não introduz cap próprio; o efeito é monotônico em s;
Aa nunca aumenta quando os níveis são ancorados por observação; uma guarda procedural
zerada dispara veto; todo fato do corpus tem âncora declarada.

## 7. Invariantes (número → teste)

| Invariante | Enunciado | Teste |
|---|---|---|
| R1–R6 | integridade do registro (β soma 1, ≤3 pilares, β ≥ 0.15, criticidade, cobertura) — **canon de 33 facetas** (v12) | `test_registry_integrity` |
| I1 | `Aa ∈ [0,1]`, `R_r ≥ 0`, níveis e déficits em [0,1] | `test_I1_bounds` |
| I2 | `Aa = 1 ⟺ d_p = 0 ∀p`; risco no piso irreduzível | `test_I2_perfect_adequacy_iff_no_deficit` |
| I3 [v12] | `σR_c/(1+σ) ≤ R_r ≤ R_c`; `p_fail ∈ [0.02,0.98]` | `test_I3_risk_floor_and_ceiling` |
| I4 | veto domina o score e a decisão | `test_I4_veto_dominates_score_and_decision` |
| I5 | monotonicidade em níveis de faceta | `test_I5_monotonicity_in_facet_scores` |
| I6 | monotonicidade em severidade | `test_I6_severity_monotonicity` |
| I7 [v12] | **hierarquia S₄ ≤ S₃ ≤ S₂ ≤ max d** | `test_I7_structural_hierarchy` |
| I7b [v12] | hierarquia provada por exaustão (grid 21⁴ + 200k vetores, pesos não-uniformes válidos) | `test_I7b_hierarchy_proven_over_the_whole_deficit_grid` |
| I8 | faceta compartilhada não é duplamente contada | `test_I8_shared_facet_is_not_double_counted` |
| I9/I9b | projeção uniforme; guarda abaixo do piso reportada | `test_I9*` |
| I10/I22 | abstención por cobertura | `test_I10*`, `test_I22*` |
| I11 | invariância à ordem das facetas | `test_I11_facet_order_irrelevance` |
| I12/I12b | continuidade; salto limitado na travessia de guarda | `test_I12*` |
| I13 | determinismo | `test_I13_determinism` |
| I14/I18/I33 [v12] | cap universal: guarda zerada limita o pilar; gap de guarda gera veto em granularidade de faceta | `test_I14*`, `test_I18*`, `test_I33_guard_cap_applies_to_every_guarded_facet` |
| I15 | Φ impede diluição | `test_I15_facet_exposure_prevents_dilution` |
| I16/I16b | banda ordenada e crescente com a incerteza | `test_I16*` |
| I17/I17b | semântica das políticas | `test_I17*` |
| I19 | horizonte eleva o bar monotonicamente | `test_I19_horizon_raises_the_bar_monotonically` |
| I20 | `confront_chain` é elo mais fraco | `test_I20_chain_is_weakest_link` |
| I21 | requisito `r_f` monotônico e limitado | `test_I21_requirement_is_monotone_and_bounded` |
| I23–I26 | proporcionalidade do veto e do bar a stakes | `test_I23*`–`test_I26*` |
| I27 | rota do bar exige déficit concentrado (gate material) | `test_I27_bar_route_needs_a_concentrated_duty_failure` |
| I28 [v12] | o ratio de risco **não** é função da adequacy | `test_I28_residual_risk_is_not_determined_by_adequacy` |
| I29 [v12] | witness determinístico: Aa idêntica, risco distinto | `test_I29_equal_adequacy_can_have_different_risk` |
| I30 [v12] | histerese bloqueia afrouxamento; endurecimento nunca é bloqueado | `test_I30_decision_hysteresis_blocks_loosening` |
| I31 [v12] | dever contestado + U_E alto + ℓ_K baixo ⇒ ABSTAIN | `test_I31_contested_duty_with_low_knowledge_abstains` |
| I32 [v12] | o valor reportado para a decisão é o usado (`adequacy_decision = adequacy_low`) | `test_I32_reported_adequacy_is_the_one_used_for_the_decision` |
| G1–G7 [v12] | propriedades de E30 (ancoragem por observação): monotonicidade em s, não-elevação de níveis, Aa não-aumenta, guarda procedural zerada → veto, cobertura de fatos | `tests/test_fact_grounding.py` |

**Validação da calibração:** Σλ = Σα = Σβ = Σμ = 1; γ+η+ω+ρ+δ ≤ 0.35; α_e ≥ (1/3)Σ_{f⊃e}β_f;
domínios/ severidades/ modos prudenciais no enumerado. `load_fitted_calibration()`
revalida antes de usar (D3.16 + D4.1).

---

## 8. Parâmetros e calibração

Todos os parâmetros quantitativos estão declarados em `Calibration` e espelhados na
ontologia como indivíduo `cal:v12`, incluindo os novos: `μ` (pesos de confiabilidade),
`hysteresis`, `abstain_uncertainty`, `abstain_knowledge_floor` e os quatro coeficientes
de stakes.

**Regra de coerência:** valores do RDF são gerados a partir do Python (nunca ao
contrário) e o espelho aritmético compara `Aa`, `D`, `S₂`, `S₃`, `S₄`, `σ`, `R_r` e a
**decisão** a 1e-6 em ≥ 100 confrontações instanciadas (gate G4′).

Dois alcances, medidos separadamente (rodada 4): (i) **grafo ↔ núcleo**, sobre os nós
de confrontação efetivamente serializados no grafo-amostra — 403 de 3.755, diff máximo
1,63 × 10⁻¹²; (ii) **corpus ↔ núcleo**, sobre as 183.920 confrontações, reconstruindo
cada perfil a partir de persona + requisitos + fatos (E30) e recomputando pelo núcleo —
diff máximo **0,0** e zero divergências de veredito (`Evaluacoes/r4/mirror_full_corpus.json`,
bateria B19). A restrição restante é de serialização, não de aritmética.

---

## 9. O que a v12 *não* afirma (limitações declaradas)

1. O tetraedro é um índice relacional; nenhuma afirmação métrica de "distância entre
   agentes" é feita.
2. O ground truth é um painel LLM heterogêneo ancorado em rubricas normativas — não
   consenso humano. κ humano não é gate; é limitação declarada (D4.5).
3. Os instrumentos normativos citados têm força apenas se as regras correspondentes
   dispararem. Censo efetivo do módulo `03_deontic.ttl`: 62 instrumentos tipados, 123
   normas, 88 conflitos, 73 obrigações, 26 permissões, 24 proibições. O número de regras
   operacionais do gold (34) é reportado em `corpus_v6_coverage.json`.
4. A hierarquia S₄ ≤ S₃ ≤ S₂ vale sob a condição sobre (α, β); calibrações que violam
   a condição são rejeitadas por `Calibration.is_valid()`.
5. `Aa` não é uma medida de "qualidade ética absoluta": é uma adequação relativa ao
   vetor de requisitos do caso. A comparação entre casos só é legítima dentro da
   mesma família de casos.
