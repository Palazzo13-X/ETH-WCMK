# ETH-WCMK v12 — arquitetura formal de controle ético delegável: modelo, evidência e limitações

**Versão:** v12 (Rodada 4). **Fonte normativa das equações:** `_analysis/SPEC_v12_equations.md` (E1–E31). **Implementação autoritativa:** `_analysis/formal_core/core.py` (644 linhas), `geometry.py` (133), `facet_registry.py` (295), `fact_grounding.py` (72). **Artefatos de evidência:** `Evaluacoes/r4/` (roundada corrente); `Evaluacoes/r3/` citada explicitamente como histórica. Todo número citado neste documento está acompanhado do artefato de onde sai.

---

## Resumo

Este documento descreve a versão 12 do modelo ETH-WCMK: uma camada de controle ético que confronta um *caso* (ETHCASE) com um *perfil de agência delegada* (WCMK) e produz um veredito de cinco classes (ABSTAIN, PROHIBIT, REVIEW_REQUIRED, ALLOW_WITH_GUARDS, ALLOW) junto de grandezas intermediárias auditáveis. Quatro decisões estruturais diferenciam a v12 das versões anteriores: (i) o tetraedro regular passa a ser tratado como **índice relacional** (face-lattice do 3-simplex, 15 slots) e não como espaço de estado, e o perfil do agente é um par (forma, magnitude) de níveis independentes, não coordenadas baricêntricas; (ii) a não-compensação é implementada como **piso lexicográfico universal** (E24) sobre as 12 facetas guardadas do canon de 33, e não como média ponderada; (iii) o **risco residual deixa de ser uma reparametrização da adequação**: `R_r = R_c·(p_fail+σ)/(1+σ)`, com `p_fail` dependente dos níveis de confiabilidade dos pilares (E12); (iv) os níveis declarados do perfil são **ancorados por observações verificáveis do caso** (E30), o que eleva a concordância modelo↔painel normativo de 0,1661 para 0,3901 sobre as *mesmas* observações (`fact_grounding_sweep.json`).

A validação é de três tipos: formal (58 testes automatizados de invariantes, todos passando), adversaria (2.064 probes, 7.815 asserções, taxa de passagem 1,000 — `B8_probes.json`) e empírica (183.920 confrontações entre 1.520 casos e 121 perfis por caso (120 personas + o perfil autodeclarado do agente), com um ground truth normativo composto por um kernel compartilhado e três lentes — deontológica, prudencial/consequencialista e ancorada em instrumentos). A camada descritiva está verificada, não apenas declarada: a ontologia v4.1 (8.394 triplos de schema, 1.888.317 triplos de instância) passa em SHACL sem nenhuma violação em todo o corpus, detecta 76/76 fixtures intencionalmente inválidos, e o espelho aritmético coincide com o núcleo: 1,63 × 10⁻¹² sobre as 403 confrontações do grafo-amostra e **0,0** sobre as 183.920 confrontações do corpus (`Evaluacoes/r4/ontology_full_validation.json`, `ontology_v4_validation.json`). O resultado empírico central é κ = 0,383 contra o consenso do painel com o ladder declarado e congelado, κ = 0,4834 em domínios de holdout com o ladder ajustado, e κ = 0,6955 no estrato em que o painel é unânime (87.134 pares). O gate G7′ (κ ≥ 0,60 como número único) **não foi atingido** e é reportado como tal. A limitação central é explícita: não existe ratificação humana do ground truth (decisão D4.5), e o pluralismo normativo entre as três lentes impõe um teto à concordância — a discordância entre os próprios painéis é κ 0,2012–0,5237.

---

## 1. Motivação e tese

Sistemas de mediação algorítmica operam hoje com camadas de filtro de conteúdo que produzem uma etiqueta binária e um score. Um controle ético delegável precisa de três coisas que um filtro não fornece: (a) uma decomposição explícita dos deveres exigidos pelo caso, (b) uma regra que impeça que um dever crítico seja compensado por um desempenho elevado em outro pilar, e (c) uma gradiente de respostas — permitir, permitir com salvaguardas, escalar a revisão, abster-se, proibitar — que seja operacionalmente estável.

A tese deste trabalho é que essa camada pode ser construída como um **modelo formal auditável** cujas equações são implementadas, testadas e ancoradas em observações verificáveis, e que essa construção é possível sem apelar a uma métrica única de "qualidade ética". A v12 não afirma que o modelo seja superior a guardrails industriais — não há benchmark correspondente em `Evaluacoes/` — nem que esteja validado por juízo humano: não há raters humanos no corpus, e isso é declarado como limitação (§9), não como detalhe metodológico.

Cinco afirmações sustentam a arquitetura:

1. **O caso e a agência são objetos distintos e acoplados**. A confrontação `C(E, a)` é um operador binário implementado em `confront()` (`core.py`), avaliado sobre 183.920 pares (caso × persona) em `Evaluacoes/r4/corpus_v6_confrontations.jsonl` (contagem em `corpus_v6_coverage.json`, `pairs_adjudicated = 183920`).
2. **A não-compensação exige granularidade de faceta, não de pilar**. Médias de pilar diluem guardas violadas: sob v11, uma guarda C3 zerada ainda produzia nível C = 0,929; sob v12 o mesmo probe retorna nível C = 0,000 (`delta_v12.json`, `guard_compensation_probe`).
3. **Risco residual e adequação são grandezas independentes**. Sob v11, `R_r/R_c = 1 − Aa + σ` era uma identidade; sob v12 existem perfis com adequação idêntica e probabilidade de falha distinta (witness determinístico: ℓ = (0,60,0,40,0,60,0,60) e ℓ′ = (0,60,0,60,0,40,0,60), `p_fail` = 0,48 vs 0,44). No corpus r3 re-avaliado, 902 buckets de mesma Aa apresentam dispersão máxima de ratio de 0,505 (`delta_v12.json`, `risk_adequacy_redundancy`).
4. **Um nível declarado não é evidência**. A ancoragem por observação (E30) é o dispositivo que liga fatos verificáveis do caso (canal de recurso, notificação, minimização de dados, revisão periódica) ao teto que uma faceta pode atingir (§3).
5. **A decisão precisa de memória**. A histerese (E13d) bloqueia afrouxamentos: na bateria temporal, 6.382 transições mais permissivas foram bloqueadas e apenas 103 oscilações A–B–A sobreviveram em 20.436 trajetórias de 8 passos (`B12_temporal_v12.json`).

---

## 2. O modelo

### 2.1 Quatro pilares, por definição

Definimos quatro pilares `p ∈ {W, C, M, K}` (querer, poder, dever, saber) como famílias de exigência utilizadas pelo modelo. Trata-se de uma **stipulação de engenharia**, não de uma demonstração de irreducibilidade: nada no núcleo prova que sejam quatro e não cinco. O canon de facetas (§2.4) é o que dá conteúdo operacional a cada pilar.

### 2.2 O tetraedro como índice relacional

A camada geométrica é a face-lattice do 3-simplex, isomorfa aos subconjuntos não-vazios de um conjunto de quatro elementos: 4 vértices, 6 arestas, 4 faces, 1 célula = **15 slots relacionais** (`geometry.py`, `lattice_cardinality()`; 15 = 2⁴ − 1, verificado em `test_lattice_is_exhaustive`). Não há, neste modelo, "distância entre agentes": a decisão formal D4.4 elimina o termo, e as funções `chordal_distance()` e `tv_distance()` permanecem apenas como utilitários de teste (`test_E16_metric_ratio_bounds`).

**E1 — vértices centrados.** `v_i·v_j = −1/3` para `i ≠ j`, `Σ_p v_p = 0`, `‖v_p‖ = 1` (`geometry.centred_vertices()`; teste `test_E1_vertex_identities`). **E17** — `‖v_p − v_q‖ = √(8/3) ≈ 1,633`. Registramos a errata do PDF-fonte ("Estrutura Matemático-Simbólica do Tetraedro Regular"): o centroide impresso `(1/2, √3/4, √6/4)` confunde circunraio (√6/4 = 0,612372) com inraio (√6/12 = 0,204124); o volume do tetraedro de vértices unitários centrados é √2/12 = 0,117851.

**E19 — redundância volumétrica demonstrada.** As frações de volume dos sub-tetraedros definidos pelo ponto `x(s)` são numericamente idênticas às coordenadas baricêntricas (`subvolume_shares()`; `test_E19_subvolumes_are_the_coordinates`, diferença máxima < 10⁻⁹). Uma camada de "coerência volumétrica" não acrescenta informação: o paper v9 continha essa leitura e foi removida.

### 2.3 Perfil = (forma, magnitude), não simplex

O perfil do agente é um vetor de **níveis independentes** `ℓ_p ∈ [0,1]`, não um ponto do simplex. Daí derivam duas quantidades reportadas separadamente:

- forma `s_p = ℓ_p / Σ_q ℓ_q` (barycêntrica, usada só pela embedding);
- magnitude `M = Σ_p ℓ_p ∈ [0,4]`.

Ambas aparecem no output de `confront()` (`core.py`, linhas 550–551). A formulação "coordenadas baricêntricas (w,c,m,k) somando 1" do paper v9 era incompatível com o código e foi corrigida.

### 2.4 O canon de 33 facetas

A camada WCMK+ decomponde cada pilar em facetas auditáveis. O canon atual tem **33 facetas** (24 do catálogo original + W6, C7, M7, K8 + M8, M9, M10, C8, K9; decisões D3.9 e D4.20). O registro declara 33 × 13 = 429 células de criticidade, 12 guardas duras (W2, W6, C3, C6, C7, M1, M4, M7, K6, M8, M9, M10), e `validate_registry()` retorna lista vazia. As cinco facetas procedurais foram criadas porque os painéis normativos invocavam deveres que nenhuma faceta media: notificação, canal de revisão humana, consentimento/participação, minimização de dados e revisão/sunset (`FACET_REVIEW_v12.md` §3; `corpus_v6_coverage.json`, `gold.rules`).

Regras estruturais verificadas: Σ_p β_fp = 1; β_fp ∈ {0} ∪ [0,15, 1]; nenhuma faceta toca os quatro pilares — 19 tocam três, 13 tocam dois, 1 toca um; todas as 33 têm um campo `observable` declarado. Duas ressalvas honestas, medidas em `Evaluacoes/r4/facet_review_stats_v12.json`: (i) o campo `weight` era inerte (33/33 = 1,0) e foi removido do núcleo, do registro, do CSV e da RDF (D4.17); (ii) **26 pares** de facetas têm vetores β quase idênticos (‖Δβ‖∞ < 0,12), e **8 pares** têm vetores β **exatamente iguais** — W3/W6, C2/C5, C3/C7, M2/M4, M2/M7, M4/M7, K1/K2, K6/K7. A discriminação dentro do pilar vem então de `r_f` e da criticidade, não de β. D4.16 decide manter as facetas separadas.

**Assimetria declarada.** O modelo não é simétrico. λ = (0,30, 0,25, 0,25, 0,20) e μ = (0,15, 0,40, 0,20, 0,25) são escolhas normativas explícitas; a massa efetiva de β nos pilares, Σ_f β_fp / Σ_f Σ_p β_fp, é (0,1652, 0,2864, 0,3424, 0,2061) e difere de λ em até **0,1348** (`facet_review_stats_v12.json`, `lambda_vs_beta_mass_max_deviation`). A paridade é apenas representacional: λ é um peso **normativo** sobre pilares, β é uma distribuição **interna** às facetas (D4.14).

### 2.5 Projeção, requisitos e políticas de agregação (E2, E3, E18, E20–E24)

**E2 — nível do pilar.**
```
ℓ̄_p = Σ_{f∈F} β_fp w_f ṽ_f / Σ_{f∈F} β_fp w_f ,   w_f ≡ 1 (declaração: campo inerte)
```
**E3 — requisito projetado e déficit.**
```
q_p = Σ_{f∈F} β_fp w_f r_f / Σ_{f∈F} β_fp w_f ,   d_p = max(0, q_p − ℓ_p)
```
**E27 — requisito por faceta.** `r_f = base(c_f) + 0,08·S_E + 0,05·I_E + 0,03·P_E + 0,04·H_E + 0,05·U_E·1[pilar primário = K]`, com `base(2)=0,55`, `base(3)=0,70`, `base(4)=0,85`; para facetas guardadas, `r_f ≥ guard_min + 0,05`; clamp [0,30, 0,95] (`core.requirement_for`).

**Políticas (E20–E23).** `weighted_mean`: ṽ_f = x_f. `guarded_weighted_mean`: se `g_f ∧ x_f < θ_f^g`, ṽ_f = min(x_f, θ_f^g). `threshold_override`: se `x_f < θ_f^g`, ṽ_f = 0. `uncertainty_penalized_mean`: ṽ_f = x_f·(1 − 0,5(1 − c_f^u)).

**E24 — piso lexicográfico universal.** Para toda faceta guardada com nível observado abaixo do piso:
```
ℓ_p = min( ℓ̄_p , band(x_f, c_f^u) )   para todo p com β_fp > 0
```
Esta é a correção mais importante da v12 em relação à v11, onde o cap só alcançava facetas com política `guarded_weighted_mean`. O probe de compensação em `delta_v12.json` mede os dois comportamentos: C3 = 0 → nível C = 0,0 (v12) contra 0,929 (v11). A monotonicidade continua valendo: aumentar `x_f` nunca reduz `ℓ_p` (teste I5).

**E18 — déficit por faceta.** `Δ_f = max(0, r_f − band(x_f, c_f^u, mode))`. O gap que alimenta veto e Φ usa o **nível observado ajustado por confiança**, não o valor corrigido pela política, para não contar duas vezes a mesma violação.

### 2.6 Déficits estruturais e a hierarquia condicional (E4–E7)

**E4.** `D = Σ_p λ_p d_p`, Σλ = 1, λ = (0,30, 0,25, 0,25, 0,20) — **constante calibrada**, não vetor dependente do caso. O paper v9 apresentava λ(E) como função do caso; o código não implementa λ(E), e essa frase foi retirada.

Definamos o **déficit conjunto** de A ⊆ {W,C,M,K} como `δ(A) = min_{p∈A} d_p` (t-norm de Gödel: deveres que devem ser cumpridos *todos* simultaneamente). Então:
```
S₂ = Σ_{|A|=2} α_A δ(A),  α = 1/6 (uniforme, 6 arestas)
S₃ = Σ_{|A|=3} β_A δ(A),  β = 1/4 (uniforme, 4 faces)
S₄ = δ({W,C,M,K}) = min_p d_p
```
**Proposição 1 (hierarquia).** Se Σα = Σβ = 1 e `α_e ≥ (1/3) Σ_{f ⊃ e} β_f` para toda aresta e, então `min_p d_p ≤ S₃ ≤ S₂ ≤ max_p d_p`. A prova está em SPEC §4 e a condição é **verificada antes de usar qualquer calibração**: `Calibration.is_valid()` rejeita ladders que a violam (`core.py`, linhas 188–196). Com α = 1/6 e β = 1/4 a condição fica saturada.

A formulação v11 (`S₄ = (∏ d_p)^{1/4}`) era falsa: para d = (0,5; 0,4; 0,3; 0,2) dá S₂ = 0,2667, S₃ = 0,2250, S₄ = 0,330975 > S₃ (`delta_v12.json`, `structural_term_counterexample_v11`). A hierarquia foi verificada por exaustão numa grade de 21⁴ pontos e 200.000 vetores aleatórios com pesos não-uniformes válidos (`test_I7b_hierarchy_proven_over_the_whole_deficit_grid`). Uma ressalva metodológica: no desenho de sensibilidade (B10), α e β são amostrados independentemente, e o artefato registra 999 de 2.400 limites de aresta violados nas draws (`B10_sobol.json`, `coherence_diagnostics`) — o que confirma que a condição não é trivial e precisa ser declarada, não assumida. Nas 1.200 instâncias do painel analisadas, nenhuma apresentou S₄ > S₃ ou S₃ > S₂.

### 2.7 Exposição, penalidade epistêmica e adequação bruta (E8–E10)

**E8 (anti-diluição).** `Φ = Σ_f c_f w_f Δ_f / Σ_f c_f w_f`.
**E9.** `u = U_E · d_K / max(q_K, ε)`, clamp [0,1].
**E10.**
```
Aa_raw = clamp{ 1 − D − γS₂ − ηS₃ − ωS₄ − ρu − δΦ }
```
com orçamento declarado `γ+η+ω+ρ+δ ≤ 0,35` (0,12 + 0,05 + 0,03 + 0,10 + 0,05 = 0,35). Este orçamento era uma lacuna do paper v9 e entra agora na notação.

### 2.8 Déficits guardados, gap material, veto e stakes (E11a–E11f)

**E11a.** `d_p^guard = max( d_p , max_{f: g_f ∧ β_fp > 0} Δ_f )`.
**E11b.** `m(E) = max{ Δ_f : c_f = 4 ou g_f }` (gap material).
**E11c.** `V = { p : d_p^guard ≥ θ_p ∧ (p ∈ criticalPillars(E) ∨ floor_breach_p) } ∪ { pilares da faceta material, se m(E) ≥ material_gap }`.
**E11d.** `w_cap = cap_base + cap_stakes_gain·stakes(E)`; `Aa = min( Aa_raw, 1 − w_cap · max( m(E), max_{p∈V} d_p^guard ) )` quando `V ≠ ∅` ou `cap_gap ≥ material_gap`.
**E11e.** com `scale = 1 + 2·max(0, (stakes_veto_min − stakes)/stakes_veto_min)`:
```
hard_p ⇔ d_p^guard ≥ θ_p + hard_veto_delta·scale
        ∨ (floor_breach_p ∧ stakes ≥ stakes_veto_min)
        ∨ (m(E) ≥ critical_prohibit_gap ∧ stakes ≥ stakes_veto_min)
```
**E11f — stakes.** `stakes(E) = clamp{ 0,45·S_E + 0,30·I_E + 0,15·(P_E/0,10) + 0,10·H_E , 0, 1 }` (coeficientes somando 1). O horizonte temporal entra no risco, não só na barra: um dano que se materializa numa geração não é equivalente a um dano imediato (D4.13). Os painéis de ground truth **importam** esta função do núcleo, não a reimplementam — condição para que modelo e painel comparem o mesmo número.

Sobre "não-compensação": o modelo não é integralmente não-compensatório. `Aa_raw` compensa déficits entre pilares; o que é não-compensável é o efeito das 12 guardas via E24 e o teto E11d. Essa distinção está declarada e substitui a frase genérica do v9 ("this preserves ethical non-compensation").

### 2.9 Risco residual independente da adequação (E12, E14)

```
p_fail(E,ℓ) = clamp( 1 − Σ_p μ_p ℓ_p , 0,02, 0,98 ),   μ = (0,15, 0,40, 0,20, 0,25)
σ(E)        = clamp{ 0,05 + 0,15·S_E·I_E + P_E , 0, 0,35 }
R_r(E,ℓ)    = R_c · (p_fail + σ(E)) / (1 + σ(E))
ratio(E,ℓ)  = (p_fail + σ(E)) / (1 + σ(E)) ∈ [σ/(1+σ), 1]
harm(E)     = R_c · stakes(E) · E_exposure
```
Propriedades (testes I2, I3, I28, I29): `σR_c/(1+σ) ≤ R_r ≤ R_c`; `R_r` é estritamente decrescente em confiabilidade; `R_r = R_c` quando `p_fail = 1`; o piso nunca é apagado pela adequação — "atenuação sem extinção". A Proposição 3 (não-redundância) é empiricamente documentada: 902 buckets de Aa idêntica com ratio distinto, dispersão máxima 0,505 (`delta_v12.json`). A Eq. (11) do v9, `R_r = R_c(1−Aa) + σR_c`, tornava a "rota da razão" da escada um segundo limiar sobre a mesma quantidade; foi substituída.

### 2.10 Banda de incerteza e decisão conservadora (E25, E26)

Com confiança `c_f^u` por faceta, `band_value(x, c, mode)` produz um intervalo `[Aa_low, Aa_high]`, e **a decisão usa `Aa_low`** explicitamente (`adequacy_decision = adequacy_low`, `test_I32_reported_adequacy_is_the_one_used_for_the_decision`). No corpus v6, Aa média = 0,3575, mediana 0,3515, máximo 0,9493, e **0,0%** das confrontações com Aa ≥ 0,999 (`corpus_v6_coverage.json`, `adequacy`). Na Rodada 3, 20,83% das 72.960 confrontações tinham Aa ≥ 0,999, das quais 357 foram vereditadas PROHIBIT e 4.459 REVIEW_REQUIRED — contradição interna reportada em `delta_v12.json` e eliminada ao reportar a banda e decidir pela inferior. O modelo reporta banda, não um escalar único.

---

## 3. Ancoragem por observação (E30)

O núcleo recebe um **perfil declarado**: níveis que o agente ou seu operador reportam para cada faceta. Um fato verificável do caso é uma observação da faceta que nomeia e limita o nível que essa faceta pode ter:

```
ℓ_f ← min( ℓ_f , q_f · [ 1 − s·(1 − c(fato)) ] ),   s ∈ [0,1]
```
`s = 0` reproduz o comportamento v11; `s = 1` é o padrão. Os fatores de conformidade `c` são declarados explicitamente (`fact_grounding.py`, `FACT_MAP`): logs e auditoria independente → M6 (1,00 / 0,25 e 1,00 / 0,55); notificação → M8 (1,00 / 0,30); canal de revisão humana e canal de apelação → M9 (1,00 / 0,30; 1,00 / 0,40); consentimento e consulta a trabalhadores → M10 (1,00 / 0,30; 1,00 / 0,60); minimização de dados → C8 (1,00 / 0,45); revisão/sunset → K9 (1,00 / 0,50); contenção exercida → C7 (1,00 / 0,30); incidentes previos → C6 (0,70 / 1,00 — abaixam a executabilidade segura); possibilidade de saída → C3 (1,00 / 0,50); dias de remedy → M7 (0,20 se 0 dias; 0,85 se ≤ 30; 0,50 se > 30). Fatos sem âncora de faceta estão declarados como tal (`UNANCHORED_FACTS`): `affected_people` entra apenas pela escala de exposição em `harm = R_c·stakes·E`.

**Evidência da necessidade.** No corpus v5 (183.920 pares), **53.431 pares (29,05%)** tinham veredito do painel PROHIBIT contra REVIEW_REQUIRED do modelo. Dentro desse estrato, **75,81%** das proibições do painel dependiam exclusivamente de fatos procedurais — canal de apelação (B2, 17.115), cláusula sunset (B5, 21.096), revisão humana sob GDPR Art. 22 (A5/C2), notificação (C10, 15.864), minimização (C1), consentimento (C5): remover contrafactualmente esses fatos derruba o veredito do painel para REVIEW. O modelo, sem E30, não enxerga nada disso (`corpus_v5_confusion_analysis.json`: `model_REVIEW_gold_PROHIBIT.n = 53431`, `share_of_prohibitions_dependent_on_procedural_facts = 0.7581`). Varrendo a força de ancoragem sobre 45.600 pares (30 personas × 1.520 casos) com o painel recalculado sobre **as mesmas observações** (`fact_grounding_sweep.json`):

| s | κ modelo↔painel | concordância | Aa média |
|---|---|---|---|
| 0,00 | 0,1661 | 0,4125 | 0,6800 |
| 0,25 | 0,1733 | 0,4240 | 0,6685 |
| 0,50 | 0,2208 | 0,5027 | 0,5987 |
| 0,75 | 0,2622 | 0,6108 | 0,5262 |
| 1,00 | 0,3901 | 0,7795 | 0,4415 |

A relação é monotônica em s. Num run independente sobre 182.400 pares, a ancoragem eleva κ de 0,1979 para 0,4009 e altera 24,59% dos vereditos do gold (`fact_grounding_v12.json`, `share_of_gold_verdicts_changed_by_grounding = 0.2459`); comparado ao gold *armazenado* (que não conhece a ancoragem), κ cai a 0,261 — o que ilustra o risco de tratar o gold antigo como referência quando as observações mudam.

**Inconsistência documentada.** O artefato `fact_grounding_v12.json` traz um `fact_to_facet_map` mais antigo (M6, M7, C7, W3, C6, C3) e classifica notificação, canal de revisão, sunset, minimização e proteção de menores como fatos sem âncora, enquanto `fact_grounding.py` ancora esses fatos em M8, M9, K9, C8 e M10. O run de 182.400 pares foi gerado contra essa tabela anterior; as monotonicidades G1–G7 foram verificadas contra a tabela vigente. A divergência não altera as conclusões do §3 (o sweep monotônico vem de `fact_grounding_sweep.json`, que usa o núcleo atual), mas significa que o mapa de fatos precisa ser regenerado para que o artefato e o código sejam a mesma coisa — algo que o §11 registra como tarefa pendente.

Monotonicidades testadas (G1–G7, `tests/test_fact_grounding.py`): a ancoragem nunca eleva um nível; um fato com c = 1 não introduz cap próprio; o efeito é monotônico em s; Aa nunca aumenta quando os níveis são ancorados; uma guarda procedural zerada dispara veto; todo fato do corpus tem âncora declarada ou está na lista explícita de não ancorados.

---

## 4. Escada de decisão: barra, proporcionalidade, veto lexicográfico, histerese e abstenção

**E13 — barra sensível a stakes.**
```
bar(E) = clamp{ b₀ + b₁·S_E + b₂·I_E + b₃·j(E) + b₄·H_E , 0,30, 0,90 }
```
onde `j(E) ∈ {0,1,2}` é o índice do modo prudencial (standard/elevated/maximum). O paper v9 escreveu `b₃·P_E`; a implementação usa o índice do modo — a notação foi corrigida. Valores: declarados (0,50; 0,20; 0,05; 0,02; 0,03), congelados da Rodada 3 (0,55; 0,10; 0,05; 0,02; 0,03) e ajustados em B5 (0,38; 0,24; 0,14; 0,08; **0,00** — `ladder_calibration_v12.json`). O horizonte, no ladder ajustado, não entra na barra; entra nos stakes (E11f).

**E13b/E13c — proporcionalidade.**
```
categorical(E) ⇔ stakes(E) ≥ prohibit_stakes_min ∧ ( ¬prohibit_needs_material ∨ m(E) ≥ critical_prohibit_gap )
PROHIBIT       ⇔ hard_veto ≠ ∅ ∨ ( categorical ∧ ( Aa_low ≤ bar − prohibit_margin ∨ ratio ≥ ratio_prohibit ) )
REVIEW_REQUIRED⇔ Aa_low ≤ bar ∨ ( V ≠ ∅ ∧ Aa_low ≤ bar + veto_slack ) ∨ ratio ≥ ratio_review
ALLOW_WITH_GUARDS ⇔ Aa_low ≤ bar + guards_margin ∨ ratio ≥ ratio_guards ∨ V ≠ ∅
ALLOW         ⇔ caso contrário
```
Um veto disparado nunca é totalmente suplantado pelo score: no melhor caso o caso é admissível com salvaguardas (testes I4, I27). Atribuição de cláusulas no ajuste (subconjunto de treino, `B5_ladder_fit_v12.json`, campo `clause_attribution`): abstenção E29 10.655; PROHIBIT por veto duro 26.155; PROHIBIT por rota da barra 82.247; PROHIBIT por rota do ratio 29.278; REVIEW por Aa abaixo da barra 10.397; REVIEW por cláusula de veto 503; REVIEW por cláusula de ratio 1.787; total de REVIEW 12.687. As três contagens de PROHIBIT se sobrepõem — um par pode satisfazer o veto duro e simultaneamente a rota da barra —, por isso não somam o total de proibições do split (103.452): as cláusulas são responsabilidade por par, não um particionamento exclusivo.

**E13d — histerese.** Se existe veredito anterior, o novo veredito não pode ser mais permissivo a menos que `Aa_low ≥ bar + hysteresis` (0,05); endurecer nunca é bloqueado. Justificativa operacional: um sistema que alterna ALLOW_WITH_GUARDS ↔ REVIEW_REQUIRED a cada medição não é governável. Na Rodada 3, sem histerese, 20 casos × 8 passos produzia 0,35 mudanças por caso (`Evaluacoes/r3/B12_temporal.json`). Com E30 e canon de 33, sobre 20.436 casos × 8 passos (`B12_temporal_v12.json`): 7.461 mudanças (0,365 por caso), **103** oscilações A–B–A, e **6.382** transições mais permissivas bloqueadas.

**E29 — abstenção epistêmica.** `ABSTAIN ⇔ (norm_conflict ≠ "none" ∨ evidence_conflict) ∧ U_E ≥ 0,60 ∧ ℓ_K ≤ 0,65`. Semântica: quando o dever aplicável é genuinamente contestado e o agente não tem conhecimento para resolvê-lo, o veredito correto é escalar, não permitir nem proibir. Dispara **14.703** vezes em 183.920 confrontações (7,99%), todas por E29 (`corpus_v6_coverage.json`, `abstain`). Já o gate de cobertura (E26: campos faltantes ou cobertura de facetas < 0,70) dispara **0** vezes no corpus — todos os perfis estão completos. Para sair da latência, a bateria **B17** degrada deliberadamente a declaração de 1.520 casos reais (13.680 probes): a 0,70 de cobertura o ABSTAIN dispara em **100%** dos casos (1.520/1.520); a 0,75, em 5,13%. Efeito colateral medido no mesmo probe: dropar as 8 facetas mais fracas do perfil eleva a adequacy aparente em **+0,342** (mediana +0,349, máximo +0,863) e torna **1.345 de 1.520** casos (88,5%) admissíveis. O piso de cobertura é, portanto, um dispositivo anti-gaming: sem ele, um agente poderia esconder suas facetas fracas simplesmente não declarando-as (`Evaluacoes/r4/B17_coverage_abstain.json`). Aplicado sobre o corpus r3 congelado — que não tem `norm_conflict`/`evidence_conflict` — o total é 0 (`delta_v12.json`, `abstention`).

**Vocabulário.** O modelo conhece exatamente cinco vereditos: ABSTAIN, PROHIBIT, REVIEW_REQUIRED, ALLOW_WITH_GUARDS, ALLOW. "Restrict" e "block" do v9 não existem no código e foram removidos. Distribuição do modelo (v6): PROHIBIT 141.313; REVIEW_REQUIRED 27.615; ABSTAIN 14.703; ALLOW_WITH_GUARDS 288; ALLOW 1. Distribuição do consenso do painel: PROHIBIT 147.607 (80,2%); REVIEW_REQUIRED 20.830; ABSTAIN 10.769; ALLOW_WITH_GUARDS 2.553; ALLOW 2.161 (`corpus_v6_coverage.json`, `gold.consensus_distribution`).

---

## 5. Agência estratificada (E28)

`confront_chain(case, [model, system, operator])` avalia cada camada separadamente e usa o **elo mais fraco** para a decisão, reportando `weakest_layer` e o máximo de `R_r` entre camadas (`core.py`, `confront_chain`; teste I20). Não se trata de média de camadas: a cadeia é tão forte quanto seu elo mais fraco, e a identidade do elo deve ser reportada — a decisão sem o diagnóstico do elo não é auditável.

Estado empírico (B15, `Evaluacoes/r4/B15_delegation_chains.json`). O corpus v6 já traz perfis por camada: 62.320 confrontações na camada *system* (incluindo 1.520 agentes declarados), 60.800 na camada *model* e 60.800 na camada *operator*. O que não existia era uma **distinção de capacidade** entre camadas — todas as personas eram amostradas do mesmo distribuição, de modo que a cadeia era aritmeticamente inerte. B15 mede essa inercia e corrige o desenho:

* **Quem pode carryar uma faceta.** Uma faceta só é delegável se todo pilar que ela alimenta é exercível pelo delegado. Sob essa regra, **1 de 33 facetas** (C1, capacidade funcional pura) é delegável; **32 de 33 (96,97%)** exigem a camada accountable. Não é uma escolha retórica: é consequência do β do canon, que compartilha pilares.
* **Retenção do dever crítico (E28).** **1.352 de 1.520 casos (88,95%)** têm um pilar crítico em W ou M. Esses deveres não podem ser transferidos à camada executora; o *fallback policy* deixa de ser opcional e passa a ser estrutural. Na ontologia isso aparece como 268 `ChainLink` com `criticalDutyDelegated = false` (ver §6).
* **Cadeia real (elo mais fraco por pilar).** A nível de faceta, o nível da cadeia é a mistura β-ponderada entre o nível declarado (partes W e M) e o nível medido do delegado para as partes C e K, tomando o mais fraco. Com o **melhor delegado disponível** a cadeia não muda nenhum veredito (0 mudanças; Aa média 0,3358 idêntica). Com o **pior delegado**, 127 vereditos mudam: **121 ficam mais restritivos**, 6 viram abstenção epistêmica; Aa média cai de 0,3358 a 0,2893 (−13,9%) e R_r média sobe de 0,388 a 0,4067. O pilar garganta é **C** (905 casos), seguido de M (262), K (213) e W (140).
* **O elo não é uma penalidade artificial.** O veredito da cadeia pessimista concorda com o gold do *perfil executor* (κ = 0,4067) melhor do que o veredito do agente declarante concorda com o seu próprio gold (κ = 0,372). Ou seja: quando o modelo avalia quem efetivamente executa o dever, sua decisão se alinha *mais* às lentes normativas, não menos. Isso é evidência de que E28 tem conteúdo normativo e não é um cap adicional.
* **Caveat.** Sem a regra de capacidade, o "elo mais fraco" ingenuo (tomar a persona mais fraca do corpus para o caso) altera 154 vereditos. A diferença entre 154 (sem capacidade) e 127 (com capacidade) é pequena em magnitude e grande em significado: sem capacidade, o modelo reportaria "a persona pior", não "o elo que falha".

Decisão registrada (D4.30): o veredito canônico continua computed na camada accountable (o declarante responde), e a cadeia é reportada como **banda de robustez** `[Aa(chain, melhor delegado), Aa(chain, pior delegado)]`, não como veredito único.

---

## 6. Ontologia (RDF/SHACL/SPARQL) — validada (gate G4′, 08/11)

A ontologia v4.1 foi gerada a partir do núcleo (nunca ao contrário) em sete módulos: `01_core.ttl`, `02_facets.ttl`, `03_deontic.ttl`, `04_agency.ttl`, `05_dynamics.ttl`, `06_calibration.ttl`, `07_grounding.ttl` (`Ontologias/ontology_v4/`, 8.394 triplos de schema), com shapes SHACL (`shapes/ontology_shapes.ttl`, 1.166 triplos, 31 node shapes; `shapes/ontology_shapes_v6.ttl`, 111 triplos, para E30) e dois conjuntos de fixtures intencionalmente inválidos (`fixtures/invalid_examples.ttl`, 63 fixtures, 4.389 triplos; `fixtures/invalid_examples_v6.ttl`, 13 fixtures E30, 125 triplos — 76 no total), além da instânciação do corpus: **1.888.317 triplos** em `fixtures/instances.ttl` (724.900 linhas, 37.997 blocos de indivíduo) — 1.520 casos, 5.150 perfis, 3.755 confrontações instanciadas (a amostra estratificada), 4.560 cadeias de delegação com 4.560 links e 4.560 resultados por camada, 6.200 agentes, 50.160 requisitos de faceta, 169.950 observações, 21.280 ancoragens de fato (E30), 16.476 registros de falha de guarda e 88 conflitos normativos. O censo deôntico efetivo do módulo `03_deontic.ttl` é 62 instrumentos tipados, 123 normas, 88 conflitos, 73 obrigações, 26 permissões e 24 proibições.

**Resultado da validação** (artefatos: `Evaluacoes/r4/ontology_v4_validation.json` para o grafo-amostra e `Evaluacoes/r4/ontology_full_validation.json` para o corpus inteiro):

| Critério G4′ | Medido |
|---|---|
| SHACL, corpus inteiro (13 chunks de 120 casos, 2.014.563 triplos validados, 406 s) | **0 violações** contra as shapes v4 e v6 |
| Fixtures inválidos | **76/76 detectados**, todos atribuídos à shape correta |
| Consultas SPARQL | **33**, das quais **15 deônticas**; 33/33 aprovadas (achados reportados separadamente) |
| Espelho aritmético | 403 confrontações (estratificadas por domínio × veredicto): **diff máximo 1,63 × 10⁻¹²**, 0 divergências entre ladder Python, `core.decide` e o grafo RDF |
| Censo do retículo (E5–E7) | 15 slots (4 vértices, 6 arestas, 4 faces, 1 célula); cada termo soma 1: **True** |
| Consistência do canon | `facet_registry_v12.csv` ↔ `facet_registry.py` ↔ `02_facets.ttl`: **0 divergências** |

Cinco defeitos de representação foram encontrados e corrigidos pelo processo de validação (não por inspeção): o padrão de código de faceta rejeitava `M10`; os 125 perfis "declarados" apontavam a um agente nunca emitido; links de cadeia delegavam zero pilar quando os pilares críticos eram {M,W}; 31 rótulos de instrumentos normativos do corpus não tinham mapeamento (9 casos ficavam sem norma, violando `hasNorm` minCount 1); e limites numéricos escritos como xsd:decimal contra valores xsd:double produziam 1.338 violações falsas em `observationConfidence`. Cada correção é rastreável em `_analysis/CHANGELOG_DECISIONS.md` (D4.28, D4.29) e nos geradores `gen_ontology_v4.py` / `gen_ontology_v5.py`.

**Achado ontológico substantivo (E28).** A regra de delegação formalizada — um link delega os pilares que o delegado *pode* exercer e declara `criticalDutyDelegated` e `retainedPillar` — revela que **268 links de cadeia (5,9% dos 4.560) retêm o dever crítico na camada delegante**. O modelo não pode exercer o dever que torna o caso crítico; a política de fallback é, portanto, estruturalmente obrigatória e não opcional.

**Dois espelhos, dois alcances.** O espelho *graph ↔ core* roda sobre as 403 confrontações do grafo-amostra (diff máximo 1,63 × 10⁻¹²) porque a máquina — 27 GB já ocupados pelo motor de inferência — não comporta o parse único de 1,89 M triplos. O espelho *corpus ↔ core* foi executado sobre as **183.920** confrontações (`_analysis/analysis/mirror_full_corpus.py` → `Evaluacoes/r4/mirror_full_corpus.json`; duração registrada no manifest: 63,42 s): cada nível de faceta foi reconstruído a partir da persona e dos requisitos do caso — fatores, jitter e os cap da E30 aplicados sobre os fatos declarados — e recomputado pelo núcleo. Diferença máxima em qualquer quantidade: **0,0** (Aa, Aa_low, Aa_high, bar, stakes, R_r, S₂, S₃, S₄, Φ, u, gap material); **0** divergências de veredito; distribuição recomputada idêntica (PROHIBIT 141.313, REVIEW 27.615, ABSTAIN 14.703, ALLOW_WITH_GUARDS 288, ALLOW 1). A limitação restante é pois de *serialização RDF* (o grafo completo não cabe na memória), não de aritmética: todo número do corpus é reproduzível bit a bit pelo núcleo. A conformance SHACL, essa sim, é do corpus inteiro — validada em chunks de 120 casos com os módulos de schema e os blocos de persona incluídos em cada chunk.

Duas correções de texto exigidas pela auditoria e aplicadas aqui: (i) a lista de classes ETHCASE do manuscrito v9 (Case, Situation, Domain, Action, Stakeholder, Vulnerability, NormativeReference, Evidence, Uncertainty, SeverityAssessment, RequirementProfile) não corresponde à ontologia efetivamente gerada. `Ontologias/ontology_v4/01_core.ttl` declara 67 `owl:Class` (mais uma em `04_agency.ttl` e uma em `07_grounding.ttl`), entre elas EthicalCase, Domain, Stakeholder, Vulnerability, Evidence, Norm, NormativeInstrument, NormConflict, Facet (com Want/Must/Can/Know como subclasses), FacetObservation, FacetRequirement, Profile, Pillar (PillarW, PillarC, PillarM, PillarK), LatticeSlot, StructuralTerm, Calibration, Confrontation, Decision, Obligation, Permission, Prohibition, DelegationChain, ChainLink, ChainLayerResult, FallbackPolicy, PriorityEngine, ResolutionStrategy, Defeasibility, AggregationPolicy, CriticalityStatement, GuardFailure, FactGrounding, DriftProfile, Consequence e Context. Não existem em nenhum módulo v4 —contrariando o texto do v9—: Situation, Action, Uncertainty, SeverityAssessment, RequirementProfile, PillarLevel, Justification, ProportionalityClaim (grep → 0 ocorrências). (ii) `prov:` não é declarado nem usado em nenhum módulo (0 ocorrências); `skos:` aparece apenas como declaração de prefixo, sem uso em qualquer tripla. As expressões "PROV-style lineage" e "SKOS-like concept schemes" foram removidas do paper. O "espelho aritmético" da v3 comparava apenas `adequacy`, `adequacy_low`, `adequacy_high`, `stakes` e `bar` de uma única instância; a SPEC v12 exige espejar `Aa`, `D`, `S₂`, `S₃`, `S₄`, `σ`, `R_r` e o veredito a 10⁻⁶ em ≥ 100 confrontações — condição ainda não cumprida.

Também foi retirada a afirmação de que existiria uma ontologia complementar `ethsvc-llm.ttl`: o arquivo não existe no repositório.

---

## 7. Corpus e ground truth híbrido

### 7.1 Composição

O corpus v6 (`Evaluacoes/r4/corpus_v6_*`, resumo em `corpus_v6_coverage.json`, seed 20261104, gerador `gen_corpus_v5.py`) tem **1.520 casos**: 1.200 na camada A (stress paramétrico) e 320 na camada B (narrativas semânticas completas), sobre **13 domínios** — Saúde (SA), Justiça e segurança (JS), Infraestrutura crítica (IC), Finanças (FI), Privacidade e dados (PD), Governança pública (GP), Informação e mídia (IM), Educação (ED), Trabalho (TB), Ambiente e energia (MA), Transporte e mobilidade (TS), Pesquisa e ciência (RS), Segurança digital (DS). Distribuição por severidade: 386 baixa, 378 média, 378 alta, 378 crítica; por irreversibilidade: 539 reversíveis, 515 parcialmente irreversíveis, 466 irreversíveis; por modo prudencial: 531 standard, 520 elevated, 469 maximum; por horizonte: 411 imediato, 387 curto, 387 médio, 335 longo. Padrões de conflito normativo: individual-coletivo 234, inovação-precaução 234, autonomia-benefício 234, legal-ético 233, nenhum 234, competição-cuidado 117, curto-longo 117, transparência-eficácia 117. Ambiguidade deliberadamente injetada: 179 casos com conflito normativo não resolvido e 126 com conflito de evidência (`corpus_v6_coverage.json`, `ambiguity`) — condições que ativam E29.

**Personas.** 120 personas de 30 tipos, 96 das quais com déficit concentrado: 24 tipos de déficit (5 em W, 6 em C, 7 em M, 6 em K) foram criados para que existam perfis em que a não-compensação possa ser observada e não apenas invocada. O teto de nível efetivo é 0,95 e nenhuma persona o excede (`personas_exceeding_cap = 0`). Cada persona declara um vetor de confiança (`confidence`) por faceta. Total de confrontações: **183.920** (1.520 × 121 perfis: 120 personas + o perfil `AGENT-declared`, que representa o agente que autodeclara seus níveis), todas adjudicadas. Por camada: 62.320 *system* (incl. as 1.520 autodeclaradas), 60.800 *model*, 60.800 *operator*.

Diversidade de templates (camada B): 22 tipos de consequência, 14 tipos de vulnerabilidade (2 no corpus v5 — limitação histórica corrigida na v6), 24 conjuntos normativos e 66 strings instrumentais distintas cobrindo 36 instrumentos. A matriz de criticidade é **derivada por regra** a partir do catálogo original para 10 domínios e por analogia para TS, RS, DS (decisão D3.6); não houve painel de especialistas para essas células, o que está declarado em `facet_registry.py` e repetido aqui como limitação.

### 7.2 Ground truth: kernel + três lentes, sem raters humanos

O gold é produzido **por par (caso, persona)**: cada veredito usa os níveis que a persona avaliada efetivamente declarou. O desenho remove circularidade onde é possível: `stakes` vem do núcleo (`core.case_stakes`), e os painéis testam níveis absolutos contra pisos de dever declarados na rubrica e contra fatos declarados — nunca leem `case.facet_requirements`, λ, β, S₂/S₃/S₄, o cap de veto nem Aa.

A adjudicação tem dois níveis:

- **Kernel compartilhado (K0–K5, 6 regras explícitas).** K0 abstenção (dever contestado + evidência contraditória + U_E ≥ 0,60); K1 proibição (≥ 3 deveres categóricos abaixo do piso com stakes ≥ 0,55); K2 proibição (dever categórico muito abaixo do piso, stakes ≥ 0,60); K3 revisão; K4 permitir com salvaguardas; K5 permitir.
- **Três lentes normativas como tabelas de regras:** A — deontológica (11 regras ancoradas em Rio Declaration Principle 1, UDHR Art. 10, UN CRC Art. 12/Belmont, OECD, GDPR Art. 22/ILO, direito à explicação, ACM/IEEE 1.5, não-compensação de deveres categóricos); B — prudencial/consequencialista (8 regras: orçamento de dano esperado, efetividade do recurso, regra de dano limitado, proporcionalidade da exposição, cláusula sunset, histórico previo, linha vermelha de irreversibilidade, capacidade demonstrada); C — ancorada em instrumentos (15 regras: GDPR Arts. 5/22, Rio Principle 1, ILO, Helsinki/Belmont, ISO 26262/UN Safe Systems, NIST CSF, UDHR Art. 10, ACM/IEEE 1.5 etc.). Total: **34 regras operacionais**, todas disparando em pelo menos 50 pares (mínimo 290 pares, máximo 101.221; 1.072.051 disparos no conjunto; `corpus_v6_coverage.json`, `gold.rules`). Cada regra registra `fired` (condição satisfeita) e `applied` (regra que efetivamente mudou o rank daquele painel).

O consenso é o rank mediano, com desempate precautor: se a spread entre painéis é ≥ 2, escolhe-se o rank mais restritivo. Unanimidade: **47,38%** dos pares; spread ≥ 1: 52,62%.

**Estado da "validação humana": inexistente.** A amostra de auditoria existe (`Evaluacoes/r4/corpus_v6_audit_sample.csv`, 120 linhas), mas sua coluna de adjudicação está vazia: 120 casos × 3 raters = 360 células sem preenchimento, `adjudication: UNADJUDICATED`. O subset humano (~120 casos) previsto na decisão D3.1 não foi executado (D4.5). Enfatizamos isso: as três lentes **não** simulam juízo humano; são implementações executáveis de tradições normativas, e podem estar mal formuladas.

---

## 8. Resultados

### 8.1 Invariantes formais (B1)

A suíte `_analysis/formal_core/tests/` — `test_invariants.py`, `test_geometry.py`, `test_fact_grounding.py` — contém **58 testes** e passa integralmente (`python3 -m pytest _analysis/formal_core/tests -q` → 58 passed; critério G2′ do plano, exigência ≥ 42). As invariantes cobrem: monotonicidade por faceta e por pilar (I5, I6), identidade do déficit (I1), não-redundância dos déficits conjuntos (I2), bounds do risco (I3), cardinalidade exaustiva do lattice (I10/I22), monotonicidade da penalidade epistêmica (I9/I9b), não-diluição de Φ (I11), cap de veto e hard veto (I4, I12/I12b), piso lexicográfico (I14/I18/I33), barreiras de proporcionalidade (I15, I21), barra sensível a stakes (I16/I16b), veredito conservador (I32), histerese (I13), adequacy ∈ [0,1] (I17), hierarquia sob a condição (I7/I7b), cap por guarda universal (I33), veto em granularidade de faceta (I19), risco nunca zero (I28), stakes com coeficientes somando 1 (I29), cadeia estratificada (I20), veredito só com proibição material (I25–I27), ABSTAIN por E26/E29 (I23–I26), e ancoragem E30 (G1–G7).

### 8.2 Probes adversários (B8)

`B8_probes.json`: **2.064 probes, 7.815 asserções, taxa de passagem 1,000** (`failure_analysis.n_failures = 0`), avaliados com o ladder ajustado de B5. Famílias e contagens efetivas: **não-compensação** 1.536 probes (33 facetas × 12 guardas duras, descontadas as 12 combinações em que a faceta probe é a própria guarda, × 2 regimes de stakes × 2 profundidades de breach) — asserções `pillar_cap`, `cap_active`, `gap_removed`, `no_allow`, cada 1.536/1.536, além de `hard_veto` 384/384; **déficit crítico** 132 (33 facetas × 2 profundidades × 2 regimes) com `base_perfect`, `deficit_lowers_adequacy`, `stakes_weighted`, `risk_not_lowered`, cada 132/132; **monotonicidade** 99 (33 × 3 perfis) com `adequacy_nondecreasing`, `risk_nonincreasing`, `no_stricter_verdict`, cada 99/99; **abstenção** 132 (33 × 4 regimes), `abstention_fires` 66/66 e `no_spurious_abstention` 66/66; **histerese** 165 (33 × 5 posições da escada), `natural_verdict` e `hysteresis`, cada 165/165. O descritor impresso no artefato ainda diz "28 facets x 9 hard guards": o canon vigente tem 33 facetas e 12 guardas, e as contagens efetivas são consistentes com 33 × 12. Este é o resultado adversário mais forte disponível: nenhum probe derivado do registro produziu compensação indevida de uma guarda.

### 8.3 Ruído nas declarações (B9)

Perturbar os níveis declarados (`B9_noise_v12.json`, n = 20.436, seed 20261104):

| σ | flip de veredito | κ modelo↔painel | ΔAa médio |
|---|---|---|---|
| 0,02 | 1,32% | 0,4651 | −0,0090 |
| 0,05 | 2,94% | 0,4417 | −0,0252 |
| 0,10 | 4,82% | 0,4199 | −0,0524 |
| 0,20 | 8,56% | 0,3934 | −0,1307 |

A degradação é monotônica e modesta. O ponto interessante é assimétrico: com σ = 0,20, o modelo fica **mais restritivo** em 8,15% das confrontações e mais permissivo em apenas 0,41% — porque o ruído aumenta `U_E` e endurece o veto em facetas de baixa stake (E11e). Reportamos também o histórico r3, onde sem E30 e com 28 facetas os flips iam de 9,5% (σ = 0,05) a 20,25% (σ = 0,20) (`Evaluacoes/r3/B9_noise.json`): a ancoragem e o canon ampliado reduzem a sensibilidade a declarações ruidosas.

### 8.4 Sensibilidade global (B10)

Sem scipy disponível, o desenho é **Latin-hypercube pareado com swap** (4.096 draws, painel de 8, seed 20261104) e os estimadores de Sobol S₁/S₂/S_T, com ranking Morris como cross-check (`B10_sobol.json`). O estimador foi validado contra uma função linear de solução exata: erro absoluto máximo 0,0334 (S₁), 0,0080 (S_T), 0,0221 (S₂); ΣS₁ exato = 1,000 vs estimado 1,1989 no desenho — daí a cautela: interpretamos índices **em ordem de magnitude**, não como percentagens exatas.

Para `Aa` média: λ_C S₁ = **0,8557** (S_T 0,8614); γ = 0,0327; ρ = 0,0370; ω = 0,0279; δ = 0,0270; η = 0,0006; α_dev = −0,0009; β_dev = 0,0027; θ e μ_C = −0,0010. ΣS₁ = 0,9807, share de interações 0,0193, ΣS_T = 1,0084. Ou seja: **os termos estruturais do tetraedro (γ+η+ω) explicam ≈ 6,1% da variância da adequação**, enquanto λ_C explica 85,6%; θ (piso prudencial) e μ_C (ponderação do risco) são estatisticamente indistinguidos de zero para Aa. Para a permissividade média, θ domina (S_T = 0,9929). Para `R_r`, μ_C é dominante (S_T = 0,9962) e os termos estruturais são zero — consistente com E12 não usar S₂/S₃/S₄. Morris (μ*) ordena γ (0,02433) > ρ (0,02349) > λ_C (0,01521) > δ (0,00864) > η (0,00786) > ω (0,00731); o ranking é sensível às escalas dos intervalos (λ_C é amostrada em [0,15, 0,45], γ em [0, 0,2]), e por isso usamos Morris só como triagem, sem índices de ordem total.

Diagnóstico de coerência do desenho: 999 de 2.400 limites de aresta `α_e ≥ (1/3)Σ_{f⊃e}β_f` violados nas amostras independentes; 0 de 1.200 casos do painel apresentam S₄ > S₃ ou S₃ > S₂. A correção histórica: o número "λ_C = 0,6085" citado na v9 era **θ_C mal rotulado como λ_C** (`B10_sobol.json`, `reconciliation_with_v9_claim`) — o script r3 não computava índices de ordem total, amostrava θ como um valor único e não variava μ.

### 8.5 Ablação: β compartilhado e facetas procedurais (B11)

`B11_shared_beta.json` (183.920 pares, ladder ajustado): κ = **0,4681** com β compartilhada; **0,1870** com one-hot (Δ −0,2811); **0,4343** com "critical floor" em vez de guardas (Δ −0,0338). A leitura honesta: a estrutura de compartilhamento entre pilares não é decorativa — vale ≈ 0,28 de κ; e a não-compensação total é pior que o equilíbrio atual.

Ablação das cinco facetas procedurais (`procedural_facet_ablation.json`, 47.120 pares amostrados; o registro D4.23 menciona 45.600 — prevalece a contagem do artefato): canon completo κ = 0,4031; canon de 28 (sem as cinco) κ = 0,3760; Δ = **−0,0271** ao removê-las em conjunto. Individualmente: M9 (canal de revisão humana) −0,0079, M8 (notificação) −0,0041, M10 (consentimento) −0,0017, C8 (minimização) −0,0011, **K9 (revisão/sunset) +0,0011 — inerte**. Decisão D4.23: manter K9 é indefensável como pretensão de conteúdo normativo; a alternativa (remover ou reclassificar K9 como observabilidade de segundo nível) exige re-run completo e está pendente.

### 8.6 Guardas e criticidade: o que o experimento decidiu (D4.15, D4.18)

O experimento de guardas (`Evaluacoes/r4/guard_experiment.json`; log em `Evaluacoes/r4/guardlog.txt`) avalia cinco variações do registro de facetas **contra o mesmo gold, os mesmos níveis ancorados por E30 e o ladder ajustado de B5**, sobre os 183.920 pares do corpus v6:

| Variante | κ | Δκ | concordância | Aa (inferior) média |
|---|---|---|---|---|
| canon v12 completo | **0,4681** | — | 0,8308 | 0,2886 |
| guardas duras em K1 e K3 (piso 0,50, política `guarded_weighted_mean`) | 0,4639 | **−0,0042** | 0,8322 | 0,2852 |
| guardas em todas as facetas K (piso 0,50) | 0,1234 | **−0,3447** | 0,4140 | 0,5575 |
| sem K9 | 0,4672 | **−0,0009** | 0,8304 | 0,2910 |
| criticidade de TB, TS e IM elevada ao nível de SA/JS (+0,10) | 0,4718 | **+0,0037** | 0,8340 | 0,2622 |

A leitura registrada no próprio artefato (`reading`) é: uma variante que não melhora κ não deve entrar no modelo, porque guardas e pesos de criticidade são afirmações normativas e precisam pagar por si mesmas em concordância, não em intuição.

**Guardas epistêmicas em K1/K3: rejeitadas como mecanismo aritmético** (Δ −0,0042; a concordância de exatos sobe 0,8308→0,8322, mas κ cai). O problema que essas guardas pretendiam resolver — agente sem conhecimento para decidir — já é tratado por E29, que opera sobre ℓ_K ≤ 0,65 e U_E ≥ 0,60 sem alterar a agregação do pilar. Adicionar um piso lexicográfico a K1 e K3 duplica o tratamento e endurece o veredito sem alinhá-lo ao painel.

**Guardas em todo o pilar K: colapso.** κ 0,1234 (Δ −0,3447) e Aa média 0,5575 — o cap lexicográfico aplicado a todas as facetas K satura o pilar e o modelo perde capacidade de discriminar: PROHIBIT cai de 153.048 para 63.433 e REVIEW_REQUIRED sobe para 79.387. Esta é a evidência empírica mais direta de que a não-compensação precisa ser **selectiva** (deveres categóricos), não universal: um modelo onde tudo é guarda não distingue nada.

**K9:** removê-la custa 0,0009 de κ (0,4681→0,4672). Somada à ablação procedural de §8.5 — onde remover K9 *aumenta* κ em 0,0011 (0,4031→0,4043, 47.120 pares) — a conclusão é a mesma: o efeito de K9 está dentro do ruído e não justifica sua permanência como conteúdo observacional (D4.23 permanece em aberto, agora com duas medições).

**Criticidade TB/TS/IM (D4.18):** +0,0037 de κ é o único resultado positivo do experimento, e **decidimos não incorporá-la ao canon v12**. A razão não é teórica: a matriz de criticidade do corpus está embutida nos requisitos de cada caso, de modo que aplicar a alteração exige regenerar os 183.920 pares, o gold e todas as baterias — e o ganho (0,8% relativo) está abaixo da discordância inter-painel (0,20–0,52), ou seja, abaixo da resolução do instrumento que mede κ. Registro explícito: o efeito existe, é reprodutível (`guard_experiment.json`), e fica como candidato da Rodada 5; não como canon.

**D4.16 (pares de β quase-idênticos) — decidida sem mudança de canon.** 26 pares têm vetores β a distância de Chebyshev < 0,12 e 8 pares têm vetores β idênticos (`facet_review_stats_v12.json`: `identical_beta_pairs = 8`, `chebyshev_beta_pairs_lt_0_12 = 26`). Fundi-los reduziria o canon de 33 a ~13 facetas e quebraria R3 (β ≥ 0,15) por renormalização; além disso, cada uma das facetas do par está ancorada em instrumentos e observáveis distintos (`observable` e `source` diferentes no registro). Nenhum par quase-idêntico produz ganho mensurável de κ quando fundido na ablação de §8.5. Consequentemente, a parcimônia aqui é estrutural, não numérica: mantemos a distinção e declaramos a redundância parcial como achado.

**D4.17 (campo `weight`) — decidido e aplicado.** O campo existia na dataclass do registro, era 1,0 em 33/33 facetas e entrava na agregação (`Σβ·w·v / Σβ·w`) e no cap de guarda (`w = crit·weight`). Foi **removido** do núcleo, do registro, do CSV canônico (`facet_registry_v12.csv`) e da emissão RDF. Regressão empírica: 6.000 confrontações recomputadas sem o campo reproduzem os vereditos gravados no corpus v6 com **0 divergências**, e a suíte de invariantes (58 testes) continua verde. É uma simplificação aritmética, não uma otimização: nada no modelo usava essa informação.

### 8.7 Ajuste da escada e invariância estrutural (B5)

Proveniência: 183.920 pares, busca de 120 draws aleatórios + 4 passes de coordenadas sobre o espaço do ladder, seed 12345; train = 9 domínios (SA, JS, IC, FI, PD, GP, IM, ED, MA), test = 4 (TB, TS, RS, DS). Parâmetros de cap/guarda (`cap_base`, `cap_stakes_gain`, `hard_veto_delta`, θ_p) **não são ajustados**: são fixados pela suíte de invariantes (I18, I33) — decisão D4.22. κ do ladder declarado: train 0,3792, test 0,3998. κ do ladder ajustado: train 0,4677, test 0,4789.

Variantes estruturais (`B5_ladder_fit_v12.json`, `structural_variants`): "veto precisa de material" (`prohibit_needs_material = 1`) → **0 flips** de veredito em 183.920 pares; "banda de stakes" (`stakes_veto_min = 0,55`) → **65 flips** no treino e 4 no teste. São variantes formalmente distintas do modelo vigente sem consequência observável mensurável — reportamos como fragilidade do desenho, não como robustez (D4.24). O ajuste também **desliga** cláusulas declaradas: `bar_horizon` vai a 0,00 e `guards_margin` a 0,00, e `prohibit_needs_material` permanece 0. Isso não é uma vitória: significa que, neste corpus, essas cláusulas não carregam sinal.

### 8.8 Transferência (B13)

`B13_transfer_v12.json` (183.920 pares; ajuste em 9 domínios, avaliação em 4 holdout — TB, TS, RS, DS — mais as 320 narrativas da camada B): κ holdout **0,4834** contra 0,4618 in-sample, gap de transferência **−0,0215**; com o ladder declarado (não calibrado) os mesmos números são 0,2025 e 0,2518, de modo que o ajuste adiciona **+0,2809** no holdout. Na camada B (38.720 pares) κ = 0,6617 ajustado vs 0,3745 declarado. O artefato registra `domains_where_default_beats_fitted = []`: não há nenhum dos 13 domínios em que o ladder declarado supere o ajustado. Por domínio (ajustado vs declarado): TB 0,4039 vs 0,1157; TS 0,4584 vs 0,2196; RS 0,5256 vs 0,1872; DS 0,5360 vs 0,2755; IC 0,4245 vs 0,3188; MA 0,5829 vs 0,2360. Abstenção: **0,0799** dos pares, idêntica com ambos os ladders — E29 não depende dos parâmetros da escada, e por isso o gap de transferência não é produzido pela abstenção. Adequacy média reportada (inferior): 0,2886 ajustado vs 0,2825 declarado. Para contraste, `kappa_by_consensus.json` (`by_domain`) dá, com o ladder congelado, κ por domínio entre 0,2819 (TB) e 0,4639 (RS).

### 8.9 Baselines (B7)

`B7_baselines_v12.json` avalia 15 baselines sobre os 56.144 pares dos domínios holdout (TB, TS, RS, DS), contra o mesmo gold; 14 produzem κ e BL2 ("fração de deveres não cumpridos") degenera a uma classe única no split de treino e fica registrada como `error: single class on train` — reportamos a falha em vez de descartá-la. Modelo (núcleo v12 + ladder ajustado em B5): κ = **0,4834**, exact-match 0,859, κ em três bandas (proibir / revisar / família-allow) 0,2833. Modelo com ladder congelado da Rodada 3: κ = 0,3991. Modelo com ladder declarado (não calibrado): κ = 0,2025. Baselines ordenados: BL5 "Aa sem cap de veto" 0,1464; BL6 "Aa sem termos estruturais" 0,1454; BL14 só ratio de risco 0,1410; BL0 magnitude média 0,1339; BL4 gap crítico máximo 0,1329; BL1 pilar mais fraco 0,1299; BL10 só nível do pilar M 0,1290; BL7 modelo de duas classes 0,1223; BL3 pior gap (todas as facetas) 0,1217; BL8 só pilar M 0,1150; BL9 só soma dos níveis 0,0660; BL12 severidade+irreversibilidade 0,0263; BL11 só severidade (agnóstico do agente) 0,0120; BL13 sempre REVIEW_REQUIRED 0,0000. Margem do modelo sobre o melhor baseline: **+0,337** (0,4834 − 0,1464). Nenhum baseline chega a 0,15, e o pior — BL13, "sempre revisar" — tem κ 0,0000 apesar de acertar 8,73% dos vereditos por acaso, o que ilustra por que exact-match isolado não é evidência. 

**Protocolo e achado histórico.** A Rodada 3 tinha um resultado severo: um baseline de regra única (worst-gap) **empataba** o modelo. Os artefatos correspondentes existem e são reportados aqui sem edição: `Evaluacoes/r3/B1_model_vs_gold.json` (κ = 0,2274, Spearman 0,0092, exact 0,9730, κ em três bandas −0,0106, 72.960 pares) e `Evaluacoes/r4/B7_baselines.json` (n_test = 180 pares do corpus v5; BL3 worst-gap κ = 0,2156, modelo com ladder ajustado κ = 0,2156 — empate). Registramos também um erro de rótulo naquele artefato: sua `headline` opõe "model_kappa 0,2156" a "best_baseline_kappa 0,238", mas 0,238 pertence a outra execução do **mesmo** núcleo (ladder declarado), não a um baseline. Comparação só é legítima sob protocolo comum: `B7_baselines_v12.json` roda 15 baselines (14 avaliáveis) sobre os 56.144 pares do holdout, reporta κ, exact-match e κ de três bandas, e a distância ao melhor baseline trivial passa a ser 0,4834 vs 0,1464. A explicação da auditoria para o empate antigo — degeneração de Aa e gold adjudicado por caso (o mesmo veredito reaproveitado para 49 agentes) — permanece válida: foi o gold, não o modelo, que produzia a ilusão de desempenho.

### 8.10 Estratificação da concordância (B3)

`kappa_by_consensus.json` (183.920 pares, ladder declarado/congelado): κ total **0,383**. Por estrato de consenso do painel: unânime (87.134 pares) **0,6955**; maioria (84.563 pares) **0,1368**; contestado (12.223 pares) **0,0547**. Concordância inter-painel: A–B 0,2557; A–C 0,5237; B–C 0,2012 — o teto estrutural para κ modelo↔consenso está nesse intervalo. Cada lente contra seu próprio consenso: A 0,7587, B 0,3207, C 0,719. Por severidade: 0,2450 (baixa), 0,3793 (média), 0,4624 (alta), 0,5120 (crítica). Por camada: A 0,3132, B 0,5524. Por domínio: mínimo TB 0,2819, máximo RS 0,4639. Diversidade de vereditos do painel (17 classes) contra 5 do modelo: 14 das 17 classes aparecem em ambos; 3 são exclusivas do painel (A4+K3+K5, A6+A8, B3+B4+K4) — incompatibilidade estrutural declarada, produto do empate precautor de três ranks e do teto de five-class do modelo.

### 8.11 Os termos geométricos explicam algo? (B16)

Sobol mede quanto γ, η e ω movem a *variância* de Aa (6,1%). Falta medir outra coisa: quanto contribuem à *concordância* com o painel. `B16_structural_ablation.json` faz a ablação multiplicativa de cada coeficiente (γ=0, η=0, ω=0, e os três zero) sobre os mesmos 183.920 pares, o mesmo gold e a mesma calibração ajustada:

| Variante | κ | Δκ | concordância exata | Aa (inferior) média |
|---|---|---|---|---|
| canon completo (γ 0,12, η 0,05, ω 0,03) | **0,4681** | — | 0,8308 | 0,2886 |
| sem arestas (γ = 0) | 0,4678 | −0,0003 | 0,8274 | 0,3484 |
| sem faces (η = 0) | 0,4686 | +0,0005 | 0,8297 | 0,3110 |
| sem célula (ω = 0) | 0,4688 | +0,0007 | 0,8303 | 0,3007 |
| sem retículo algum | 0,4688 | +0,0007 | 0,8262 | 0,3827 |

Nenhuma diferença ultrapassa 0,0007 — menos de um centésimo, e menor que qualquer diferença entre lentes (§8.10). O retículo, portanto, **não é uma fonte de informação normativa**: ele altera a magnitude do veredito (a Aa média sobe 0,094 quando a geometria é removida, o que muda a posição relativa dos casos dentro da banda de decisão) mas não melhora a classificação. Isso é coerente com o §1: o tetraedro é índice relacional e dispositivo de auditabilidade (D3.4), não um operador de inferência. Um modelo que reclama valor geométrico além disso está reclamando mais do que os dados sustentam — e essa é a afirmação que o artefato permite fazer.

---

## 9. Limitações

As limitações são apresentadas em ordem de impacto e sem atenuação retórica.
1. **Validação humana inexistente.** O ground truth é produzido por três lentes normativas implementadas como tabelas de regras (A deontológica, B prudencial/consequencialista, C ancorada em instrumentos), não por pessoas. A decisão D4.5 optou por não usar raters humanos; a amostra de auditoria de 120 casos está vazia (`corpus_v6_audit_sample.csv`, `adjudication: UNADJUDICATED`). A rubrica pode estar mal formulada, e nada neste corpus permite detectar isso.
2. **Pluralismo normativo não resolvido.** A discordância inter-painel (κ 0,2012–0,5237) não é ruído: A e C restringem por dever categórico; B de-restringe por proporcionalidade de exposição e cláusula sunset; K3 (revisão) é compatível com K4 (permitir com salvaguardas), e as lentes divergem precisamente nos casos onde as tradições divergem. O modelo concorda κ 0,6955 onde o painel é unânime, e κ 0,0547 onde não é. Não reclamamos resolver esse conflito.
3. **Granularidade observacional.** E30 só ancora os fatos que o corpus declara. Fatos sem âncora de faceta (`UNANCHORED_FACTS`) entram apenas pela escala de exposição. A criticidade por domínio é derivada por regra e analogia, sem painel de especialistas. As β de 26 pares de facetas são quase idênticas (‖Δβ‖∞ < 0,12) e as de 8 pares são exatamente iguais, de modo que, dentro do pilar, a agregação não as distingue; a distinção é semântica (instrumentos e observáveis diferentes), não numérica. O campo `weight`, que existia no registro, foi removido por ser inerte (D4.17).
4. **K9 medida como inerte.** Remover K9 melhora κ em 0,0011 (`procedural_facet_ablation.json`); removê-la no experimento de guardas custa 0,0009 (`guard_experiment.json`). Nos dois casos o efeito está dentro do ruído: uma faceta declarada "observável" e ancorada por um fato (sunset_review) não contribui ao veredito. Mantê-la no canon é, por ora, uma decisão de vocabulário, não uma afirmação de conteúdo.
5. **Variantes estruturais inertes.** `prohibit_needs_material = 1` produz 0 flips e a "banda de stakes" produz 65 flips em 183.920 confrontações (`B5_ladder_fit_v12.json`). A escada tem cláusulas que, empiricamente, não operam.
6. **O desenho das guardas não está otimizado.** Estendê-las a todo o pilar K derruba κ em 0,3447; as guardas duras em K1/K3 custam 0,0042 (`guard_experiment.json`). As 12 guardas do canon vigente são uma decisão normativa, não um ajuste empírico: nenhuma variante de guarda testada melhorou a concordância com o painel.
7. **Os termos estruturais do tetraedro explicam pouco.** Sobol: γ+η+ω ≈ 6,1% da variância de Aa, contra 85,6% de λ_C; S₂/S₃/S₄ são zero no risco (E12 não os usa) e indistinguidos de zero na permissividade. Mantê-los é uma escolha arquitetônica (D3.4), não uma necessidade demonstrada; o valor agregado de manter a hierarquia S₂/S₃/S₄ é a auditabilidade das relações conjuntas de déficit, e isso fica explícito.
8. **Sem scipy: Sobol por desenho pareado.** Índices S₁/S₂/S_T por Latin-hypercube pareado com swap, validados contra uma função linear exata (erro máximo 0,0334). Não há índices de ordem total de Morris; μ* é apenas triagem sensível à escala dos intervalos.
9. **Hierarquia condicional.** S₄ ≤ S₃ ≤ S₂ só vale sob `α_e ≥ (1/3) Σ_{f⊃e} β_f`. Calibrações que violam a condição são rejeitadas por `Calibration.is_valid()`, mas o desenho de sensibilidade amostra α e β independentemente e registra 999 de 2.400 violações — a hierarquia não é uma propriedade universal do modelo.
10. **Abstenção por cobertura (E26) só dispara sob probe artificial.** Todos os perfis declarados estão completos: 0 disparos naturais. B17 mostra que o gate funciona (100% de ABSTAIN a 0,70 de cobertura) e que é necessário (dropar 8 facetas frágeis infla Aa em +0,342), mas o corpus não contém nenhum caso genuinamente incompleto — essa camada de casos não foi gerada.
11. **A camada de agência está presente, mas pouco diferenciada.** O corpus tem 60.800 confrontações na camada *model* e 60.800 na camada *operator*, mas as personas de todas as camadas foram amostradas da mesma distribuição: B15 mostra que, sem uma regra explícita de capacidade por pilar, a cadeia é aritmeticamente quase inerte (0 mudanças de veredicto com o melhor delegado, 127 com o pior). A modelagem de capacidade (D4.30) é consequência do β do canon — 32 de 33 facetas exigem a camada accountable — e não de dados observados sobre organizações reais.
12. **Ontologia validada, mas com alcance declarado.** SHACL e as 33 verificações SPARQL (15 deônticas) cobrem o corpus inteiro. O espelho aritmético *graph ↔ core* corre sobre o grafo-amostra (403 confrontações de 183.920) porque a máquina não comporta o parse único de 1,89 M triplos com o motor de inferência residente; o espelho *corpus ↔ core* cobre as 183.920 confrontações e fecha com diff 0,0 e 0 divergências de veredito. Resta, portanto, apenas a lacuna de serialização RDF (o grafo completo não cabe na memória), não uma lacuna aritmética.
13. **O risco é estrutural, não agencial, neste corpus.** B14: 98,07% da variância de R_r é explicada pelo caso, 0,80% pelo perfil e 1,13% pela interação. As personas variam pouco em magnitude de risco; variam em *veredito* (15,5% dos casos (235 de 1.520) mudam de veredito entre os 121 perfis do mesmo caso). Qualquer afirmação sobre "quem executa" depende, portanto, de thresholds e não da magnitude do risco — e o corpus não tem variação de competência suficientemente ampla para sustentar uma teoria forte da agência.
14. **Casos sintéticos.** Não existe base real no repositório; os casos são paramétricos/narrativos gerados. A amostra de auditoria existe para permitir adjudicação humana futura, mas não foi adjudicada.
15. **Comparação entre casos só intra-família.** Aa é adequação relativa ao vetor de requisitos do caso; comparar Aa entre famílias de casos distintas não é legítimo (SPEC §9.5).
16. **Registro de execução parcial.** O manifest cobre 74 artefatos e 20 execuções com o `git_rev` da última geração do manifest, mas apenas **7 das 20** têm duração registrada — 4 medidas pelo runner e 3 recuperadas do campo `runtime_seconds` do próprio artefato (B2 48,5 s, B10 400,2 s, B2b 405,76 s); as demais 13, herdadas de invocações do runner antigo, só têm comando e returncode. A rastreabilidade completa do *como* depende do `source_inventory` (hashes de geradores, módulos, shapes, fixtures e MathML), não do log de execução.
---

## 10. Reproducibilidade

`_analysis/run_all_batteries.py` é o único ponto de entrada: executa B1 (pytest), B0 (delta v11→v12), B2 (validação ontológica da amostra), B3 (κ por consenso), B4 (varredura de ancoragem), B5 (fit do ladder), B6 (perfilagem LLM local), B7 (baselines), B8 (probes), B9/B12 (ruído e temporal), B10 (Sobol/Morris), B11 e B11b (ablações), B13 (transferência), B14 (risco por caso × perfil), B15 (cadeias de delegação, E28), B16 (ablação dos termos geométricos), B17 (probe do gate de cobertura E26), B18 (verificação de consistência paper ↔ artefatos) e B2b (varredura SHACL/SPARQL do corpus inteiro), e escreve `manifest_<round>.json`. Rounds r2 e r3 são **congelados**: o runner recusa escrever neles (`FROZEN = {"r2", "r3"}`). O manifest define também a convenção de calibração que resolve ambiguidades de leitura: *o corpus e o gold usam o ladder congelado de r3; as baterias de ajuste (B5, B7, B13, B16) usam `ladder_calibration_v12.json` e reportam resultados separadamente*.

**Estado do gate G9′:** `Evaluacoes/r4/manifest_r4.json` contém 74 artefatos com SHA-256 e tamanho, o hash dos arquivos do núcleo (`core.py`, `facet_registry.py`, `geometry.py`, `fact_grounding.py`, `run_battery_B8_v12.py` e três arquivos de teste), Python 3.14.4, fingerprint de máquina, canon (33 facetas) e corpus (v6, 1.520 casos, 121 perfis por caso, 183.920 confrontações), a convenção de calibração, `git_rev` (o commit da cuja árvore os artefatos foram derivados; atualizado a cada geração do manifest) e **20 execuções registradas** (bateria, comando e returncode; duração e cauda de saída para as execuções do runner atual, acumuladas por invocação sem apagar histórico). O `source_inventory` hashiza 10 arquivos do núcleo, 14 geradores, 12 artefatos ontológicos (módulos, shapes, fixtures, relatório de geração) e os 31 arquivos MathML. Convenção declarada: o manifest é escrito *depois* do commit que registra, de modo que o próprio manifest é o único artefato fora da árvore que ele hashia. O verificador de consistência (`_analysis/analysis/paper_artifact_consistency.py`) e seu resultado (`paper_consistency_check.json`) também estão inventariados: 44 afirmações verificadas contra artefatos, **0 divergências**. Isso fecha a lacuna anterior: não basta saber *qual* arquivo produziu um número, agora também se registra *como* foi produzido. A bateria B6 (perfilagem com LLMs locais, 240 chamadas sobre 40 casos em dois modelos) produziu `json_validity_rate = 0.0` e decisões por frame vazias: não permite afirmar nada sobre viés de auto-relato e, por isso, não é usada como evidência em nenhuma seção.

**Arquivos de equação.** `_analysis/paper/equations.py` é agora a fonte única: a partir dele `_analysis/paper/regen_equations.py` gera os 31 arquivos MathML (`paper/figures/mathml/E1–E31`) e os PNG (`paper/figures/eq_E1…E31.png`), e verifica que cada MathML parseie como XML. As correções da rodada: E2, E3 e E8 perderam o `w_f` inerte (D4.17); E7 passou a `S₄ = min_p d_p`; E11 foi reescrita em três linhas (déficit guardado, gap material, cap proporcional); E28 passou à regra de capacidade por pilar; E21, E22 e E24 tinham comparadores `<` cruamente emitidos dentro de `<mtext>`, o que quebrava o XML — hoje escapados. Resultado medido: **31/31 arquivos parseiam**. Os 31 PNG foram montados em um único documento paginado, `paper/figures/equations_E1_E31.pdf` (653,6 KB, 31 imagens embutidas, verificada a estrutura: cabeçalho %PDF-1.4, %%EOF, 96 objetos, 31 `/Subtype /Image`). Não há LaTeX instalado nesta máquina; o PDF é portanto uma composição raster das equações, não uma composição TeX.

---

## 11. Trabalho futuro

1. ~~**Validar a ontologia v4** (G4′)~~ — concluída em 08/11 (§6). ~~Pendência remanescente~~ — fechada pela bateria B19: o espelho aritmético foi estendido às 183.920 confrontações (diff 0,0). Continua pendente apenas emitir o grafo RDF completo dessas confrontações, o que exige uma máquina com mais memória.
2. ~~Completar o manifest~~ — **concluído** (G9′): `runs` preenchidas para 20 execuções e `source_inventory` cobrindo núcleo, geradores, módulos, shapes, fixtures e MathML. O que falta é temporal: as durações só existem para as execuções feitas pelo runner a partir desta rodada.
3. **Adjudicação humana real** da amostra de 120 casos, para transformar a limitação 1 em um segundo estrato de validação (κ humano ↔ κ de painel, reportados separadamente).
4. ~~**Decidir D4.23** (K9) e **D4.24** (variantes inertes)~~ — decidido: K9 permanece no canon com contribuição declarada como nula (Δ = +0,0011); as variantes "veto exige gap material" e "banda de stakes" saem das equações canônicas e ficam como probes de robustez.
5. ~~**Aplicar D4.16 e D4.17**~~ — D4.17 aplicada (campo `weight` eliminado do núcleo, do registro, do CSV e da ontologia, com regressão de 6.000 confrontações sem divergência); D4.16 decidida sem alteração do canon, com justificação medida.
6. ~~**Regenerar o corpus com a criticidade de TB/TS/IM**~~ — D4.18 decidida como **não adotada** nesta rodada: ganho de +0,0037 κ abaixo da resolução do instrumento e custo de regeneração de todo o corpus e de todas as baterias. Candidato explícito à Rodada 5.
7. ~~Cobertura empírica de E26~~ — **parcialmente resolvido**: B17 dispara o gate artificialmente e quantifica o efeito anti-gaming, mas o corpus ainda não contém casos genuinamente incompletos; essa camada continua por gerar.
8. **Sobol de ordem total com scipy** e verificação de λ(E) como alternativa real a λ constante, hoje apenas uma hipótese de pesquisa (D4.12).
9. **Adversarialidade declarativa**: E30 trata os fatos como dados do operador. Faltam probes de *inconsistência* entre fatos declarados e observáveis.
10. ~~Regenerar os renderings das equações~~ — feito: `regen_equations.py` produziu os 31 MathML e os 31 PNG a partir de `equations.py`. ~~commitar~~ — feito: a rodada está commitada e o manifest regenerado a partir da árvore commitada. ~~Renderizar o PDF das equações~~ — feito: os 31 PNG foram montados em `paper/figures/equations_E1_E31.pdf` (31 páginas, uma por equação) sem LaTeX.
---

## Apêndice A. Parâmetros: declarados, congelados e ajustados

| Parâmetro | Declarado (`default_calibration`) | Congelado r3 (`Evaluacoes/r3/ladder_calibration.json`) | Ajustado r4 (`ladder_calibration_v12.json`) |
|---|---|---|---|
| `bar_base` | 0,50 | 0,55 | 0,38 |
| `bar_severity` | 0,20 | 0,10 | 0,24 |
| `bar_irreversibility` | 0,05 | 0,05 | 0,14 |
| `bar_prudential` | 0,02 | 0,02 | 0,08 |
| `bar_horizon` | 0,03 | — | 0,00 |
| `prohibit_margin` | 0,20 | 0,25 | 0,27 |
| `guards_margin` | 0,15 | 0,05 | 0,00 |
| `stakes_veto_min` | 0,55 | 0,70 | 0,70 |
| `hard_veto_delta` | 0,15 | 0,25 | 0,25 |
| `material_gap` | 0,25 | 0,25 | 0,25 |
| `critical_prohibit_gap` | 0,45 | 0,35 | 0,3771 |
| `cap_base` / `cap_stakes_gain` | 0,50 / 0,50 | 0,40 / 0,40 | 0,40 / 0,40 |
| `prohibit_stakes_min` | 0,60 | 0,30 | 0,0902 |
| `prohibit_needs_material` | 1 | 0 | 0 |
| `veto_slack` | 0,10 | 0,10 | 0,02 |
| `ratio_prohibit` / `ratio_review` / `ratio_guards` | 0,65 / 0,40 / 0,20 | 0,70 / 0,45 / 0,25 | 0,74 / 0,52 / 0,41 |
| `hysteresis` | 0,05 | 0,05 | 0,05 |
| `abstain_uncertainty` / `abstain_knowledge_floor` | 0,60 / 0,65 | 0,60 / 0,65 | 0,60 / 0,65 |
| λ, α, β_face, γ, η, ω, ρ, δ, μ, θ | (0,30,0,25,0,25,0,20); 1/6×6; 1/4×4; 0,12, 0,05, 0,03, 0,10, 0,05; (0,15,0,40,0,20,0,25); (0,65,0,60,0,60,0,65) | não ajustados (D4.22) | não ajustados |

---

---

## Apêndice B. Tabela de trazabilidade: número → artefato → campo

| N° citado no texto | Artefato (`Evaluacoes/r4/` salvo indicação) | Campo JSON |
|---|---|---|
| 183.920 confrontações; 1.520 casos; 120 personas + 1 perfil autodeclarado = 121 perfis | `corpus_v6_coverage.json` e `corpus_v6_confrontations.jsonl` | `pairs_adjudicated`, `cases.total`, contagem por `agent_layer` (62.320/60.800/60.800) |
| 1.200 / 320 camadas A/B; 13 domínios | `corpus_v6_coverage.json` | `cases.layerA`, `cases.layerB`, `cases_by_domain` |
| Aa média 0,3575; mediana 0,3515; max 0,9493; 0,0% ≥ 0,999 | `corpus_v6_coverage.json` | `adequacy` |
| Vereditos do modelo (141.313 / 27.615 / 14.703 / 288 / 1) | `corpus_v6_coverage.json` | `decision_distribution` |
| Consenso do painel (147.607 / 20.830 / 10.769 / 2.553 / 2.161) | `corpus_v6_coverage.json` | `gold.consensus_distribution` |
| Unanimidade 47,38%; spread ≥ 1: 52,62%; κ total 0,383 | `corpus_v6_coverage.json` | `gold.unanimous_share`, `gold.contested_share_spread_ge_1`, `model_vs_gold.kappa` |
| 34 regras normativas, todas ≥ 50 pares | `corpus_v6_coverage.json` | `gold.rules_total`, `gold.rules_firing_ge_50_pairs` |
| Espelho aritmético do corpus inteiro: diff 0,0, 0 divergências de veredito (183.920 confrontações) | `Evaluacoes/r4/mirror_full_corpus.json` | `global_max_abs_difference`, `verdict_divergences`, `confrontations` |
| E26 dispara 100% a 0,70 de cobertura; dropar 8 facetas infla Aa +0,342; 1.345 casos ficam admissíveis | `Evaluacoes/r4/B17_coverage_abstain.json` | `per_level['0.7'].abstain_count`, `anti_gaming_pair` |
| 120 linhas de auditoria sem raters | `corpus_v6_audit_sample.csv` / `corpus_v6_coverage.json` | `audit_sample.rows`, `adjudication` |
| Persona cap 0,95; 24 tipos de déficit concentrado; 0 personas acima do cap | `corpus_v6_coverage.json` | `personas.max_effective_delivery`, `personas.concentrated_deficit_types`, `personas.personas_exceeding_cap` |
| κ estratificado 0,6955 / 0,1368 / 0,0547 (87.134 / 84.563 / 12.223 pares) | `kappa_by_consensus.json` | `strata.unanimous/majority/contested` |
| κ inter-painel A–B 0,2557; A–C 0,5237; B–C 0,2012 | `kappa_by_consensus.json` | `panel_pairwise_kappa` |
| κ por severidade 0,2450 / 0,3793 / 0,4624 / 0,5120; por camada 0,3132 / 0,5524 | `kappa_by_consensus.json` | `by_severity`, `by_layer` |
| Fit: κ declarado 0,3792/0,3998; ajustado 0,4677/0,4789 | `B5_ladder_fit_v12.json` | `baseline_kappa`, `fitted_kappa` |
| Variantes: 0 flips; 65 flips (train) / 4 (test) | `B5_ladder_fit_v12.json` | `structural_variants` |
| Atribuição de cláusulas (10.655 / 26.155 / 82.247 / 29.278 / 10.397 / 503 / 1.787) | `B5_ladder_fit_v12.json` | `clause_attribution` |
| Parâmetros do ladder ajustado | `ladder_calibration_v12.json` | todas as chaves |
| κ modelo↔painel 0,4834; exact 0,859; três bandas 0,2833 | `B7_baselines_v12.json` | `results[baseline="model: v12 core + ladder fitted on TRAIN domains (B5, r4)"]` |
| Melhor baseline 0,1464; margem +0,337 | `B7_baselines_v12.json` | `results[baseline="BL5 adequacy without the veto cap (ablation)"]` |
| κ ladder congelado 0,3991; ladder declarado 0,2025 | `B7_baselines_v12.json` | `results[baseline="model: v12 core + frozen r3 ladder"]`, `...declared (uncalibrated) ladder` |
| κ holdout 0,4834 vs in-sample 0,4618; gap −0,0215; camada B 0,6617 vs 0,3745 | `B13_transfer_v12.json` | `overall`, `layer_b` |
| Abstenção 0,0799 (idêntica nos dois ladders); κ por domínio ajustado vs declarado (TB 0,4039/0,1157; MA 0,5829/0,2360) | `Evaluacoes/r4/B13_transfer_v12.json` | `abstain_rate_fitted`, `abstain_rate_default`, `by_domain` |
| 2.064 probes / 7.815 asserções / 1,000 | `B8_probes.json` | `summary.total_probes`, `summary.assertions_total`, `summary.pass_rate` |
| Ruído: flips 1,32% → 8,56%; κ 0,4651 → 0,3934; ΔAa −0,0090 → −0,1307; 8,15% vs 0,41% | `B9_noise_v12.json` | `noise_levels[sigma]` |
| Histerese: 7.461 mudanças; 0,365/caso; 103 oscilações; 6.382 bloqueadas | `B12_temporal_v12.json` | `n_total_verdict_changes`, `mean_verdict_changes_per_case`, `oscillations_a_b_a_blocked_or_repeated`, `more_permissive_transitions_blocked_by_hysteresis` |
| Sobol: λ_C S₁ 0,8557 / S_T 0,8614; γ 0,0327; η 0,0006; ω 0,0279; ΣS₁ 0,9807 | `B10_sobol.json` | `outputs.mean_adequacy.S1`, `.ST`, `.S1_sum` |
| Validação do estimador: erro máx 0,0334 (S₁), 0,0080 (S_T) | `B10_sobol.json` | `estimator_validation` |
| Coerência: 999/2.400 limites de aresta violados; 0/1.200 casos violam hierarquia | `B10_sobol.json` | `coherence_diagnostics` |
| θ domina a permissividade (S_T 0,9929); μ_C domina R_r (S_T 0,9962) | `B10_sobol.json` | `outputs.mean_permissiveness.ST.theta`, `outputs.mean_residual_ratio.ST.mu_C` |
| β compartilhada 0,4681; one-hot 0,1870; critical floor 0,4343 | `B11_shared_beta.json` | `variants[].kappa_vs_gold` |
| Facetas procedurais: 0,4031 vs 0,3760; Δ −0,0271; K9 +0,0011 | `procedural_facet_ablation.json` | `variants.full`, `variants.canon_28`, `variants.*_removed` |
| Ancoragem: κ 0,1661 → 0,3901; Aa 0,6800 → 0,4415; 45.600 pares | `fact_grounding_sweep.json` | `sweep[strength]` |
| Ancoragem em 182.400 pares: 0,1979 → 0,4009; 24,59% dos vereditos alterados | `fact_grounding_v12.json` | `summary`, `grounded_model_vs_stored_gold.share_of_gold_verdicts_changed_by_grounding` |
| 53.431 pares (29,05%) modelo REVIEW ↔ painel PROHIBIT; 75,81% dependentes de fatos procedurais | `Evaluacoes/r4/corpus_v5_confusion_analysis.json` | `model_REVIEW_gold_PROHIBIT.n`, `share_of_prohibitions_dependent_on_procedural_facts` |
| C3 = 0 → nível C 0,929 (v11) vs 0,000 (v12) | `delta_v12.json` | `guard_compensation_probe.C3.pillar_levels` |
| S₄ geométrica 0,330975 > S₃ 0,2250 | `delta_v12.json` | `structural_term_counterexample_v11` |
| 902 buckets de mesma Aa, dispersão 0,505 | `delta_v12.json` | `risk_adequacy_redundancy` |
| 33.800 flips v11→v12; PROHIBIT→REVIEW 20.858 | `delta_v12.json` | `total_flips`, `decision_flips_v11_to_v12` |
| Aa ≥ 0,999 em 20,83% do corpus r3; 357 PROHIBIT e 4.459 REVIEW com Aa = 1 | `delta_v12.json` | `adequacy_degeneracy` |
| ABSTAIN total sobre corpus r3 = 0 | `delta_v12.json` | `abstention.abstain_total_v12_default` |
| ABSTAIN 14.703 em 183.920 (7,99%), todos E29; cobertura 0 | `corpus_v6_coverage.json` | `abstain` |
| Veto: 98,91% das confrontações; hard veto 20,37% | `corpus_v6_coverage.json` | `veto_rate`, `hard_veto_rate` |
| 58 testes de invariante | `_analysis/formal_core/tests/` (B1 via `run_all_batteries.py`) | saída do pytest; critério G2′ em `GATE_REPORT_r4.md` |
| 33 facetas, 12 guardas, 33 observáveis, β Σ=1 | `_analysis/formal_core/facet_registry.py` (`validate_registry() == []`) | — (verificação executada) |
| 26 pares β quase idênticos; 8 pares β idênticos; λ vs massa de β desvio 0,1348 | `Evaluacoes/r4/facet_review_stats_v12.json` | `chebyshev_beta_pairs_lt_0_12`, `identical_beta_pairs`, `lambda_vs_beta_mass_max_deviation` |
| κ r3 modelo↔gold 0,2274, Spearman 0,0092, três bandas −0,0106 (histórico) | `Evaluacoes/r3/B1_model_vs_gold.json` | `kappa`, `spearman_rho`, `kappa_3band` |
| Empate r3 0,2156 vs 0,2156; κ 0,2188 (histórico) | `AUDIT_v12.md` §6 e `Evaluacoes/r4/B7_baselines.json` | `best_baseline`, `model_kappa` |
| κ painel r3 0,8387; unanimidade 84% (histórico) | `Evaluacoes/r3/gold_rubric_calibration.json` | `mean_pairwise_kappa`, `unanimous_panel_share` |
| Guardas K1/K3 (piso 0,50): κ 0,4639, Δ −0,0042 | `Evaluacoes/r4/guard_experiment.json` | `variants.guards_K1_K3.kappa`, `.delta_vs_full` |
| Guardas em todo K: κ 0,1234, Δ −0,3447 | `Evaluacoes/r4/guard_experiment.json` | `variants.guards_all_K` |
| Sem K9: κ 0,4672, Δ −0,0009 | `Evaluacoes/r4/guard_experiment.json` | `variants.no_K9` |
| Criticidade TB/TS/IM +0,10: κ 0,4718, Δ +0,0037 | `Evaluacoes/r4/guard_experiment.json` | `variants.rebalanced_criticality` |
| Canon completo (referência do experimento): κ 0,4681, Aa 0,2886 | `Evaluacoes/r4/guard_experiment.json` | `variants.full` |
| Ontologia v4.1: 8.394 triplos de schema; 1.888.317 triplos de instância; 37.997 blocos | `Ontologias/ontology_v4/generation_report.json` | `module_triples*`, `instances_triples`, `norm_conflicts` |
| SHACL corpus inteiro: 0 violações (v4 e v6); 2.014.563 validações em 13 chunks; 406 s | `Evaluacoes/r4/ontology_full_validation.json` | `shacl_v4.violations`, `shacl_v6.violations`, `graph.triples_validated`, `runtime_seconds` |
| Fixtures inválidos 76/76 detectados e atribuídos à shape esperada | `Evaluacoes/r4/ontology_v4_validation.json` | `invalid_fixtures.detected`, `.detected_by_expected_shape` |
| 33 verificações SPARQL (15 deônticas), 0 falhas, no corpus inteiro | `ontology_full_validation.json` / `ontology_v4_validation.json` | `consistency_checks_over_full_corpus`, `sparql_checks.count` |
| Espelho aritmético: diff máx 1,63 × 10⁻¹²; 0 divergências de veredicto; 403 confrontações | `ontology_v4_validation.json` | `mirror.max_abs_diff`, `mirror.verdict_mismatches`, `mirror.n_confrontations` |
| Retículo: 15 slots (4 vértices, 6 arestas, 4 faces, 1 célula), soma 1 | `ontology_v4_validation.json` | `face_lattice` |
| Registry check CSV ↔ Python ↔ TTL: 0 divergências | `ontology_v4_validation.json` | `registry.mismatches` |
| E28: 268 links (5,9% de 4.560) retêm o dever crítico | `ontology_full_validation.json` | `findings` |
| Censo deôntico: 62 instrumentos, 123 normas, 88 conflitos, 73 obrigações, 26 permissões, 24 proibições | `Ontologias/ontology_v4/03_deontic.ttl` | contagem por `rdf:type` |
| B14: variância de R_r — caso 0,9807, perfil 0,0080, interação 0,0113; spread médio 0,0775; 15,46% dos casos com veredictos mistos; 225 resgatáveis; 1.017 estruturalmente proibidos | `B14_case_profile_risk.json` | `variance_decomposition`, `per_case_risk_spread`, `verdict_agreement_inside_case`, `agency_can_change_the_outcome` |
| B15: 32/33 facetas exigem accountability; 1.352/1.520 (88,95%) com dever crítico em W ou M; 127 mudanças de veredicto (121 mais restritivas); Aa 0,3358 → 0,2893; κ cadeia-pior-delegado vs gold do executor 0,4067 vs declarado 0,372 | `B15_delegation_chains.json` | `capability_definition_facet_level`, `duty_retention_E28`, `chain_with_worst_delegate`, `agreement_with_the_gold_lens` |
| Ablação geométrica: κ full 0,4681; γ=0 0,4678; η=0 0,4686; ω=0 0,4688; sem retículo 0,4688; Aa média 0,2886 → 0,3827 | `Evaluacoes/r4/B16_structural_ablation.json` | `variants[].kappa`, `.delta_vs_full`, `.mean_adequacy_low` |
| 58 testes de invariante após D4.17; 0 divergências em 6.000 confrontações recomputadas | `_analysis/formal_core/tests/` (B1) + verificação ad hoc documentada em `CHANGELOG_DECISIONS.md` (D4.17) | saída do pytest |
| Manifest de hashes: 74 artefatos, 20 execuções, inventário de fontes (núcleo, geradores ontológicos, módulos, shapes, fixtures, 31 MathML) | `Evaluacoes/r4/manifest_r4.json` | `artefacts[].sha256`, `core_files_sha256`, `runs[].returncode`, `runs[].duration_s`, `source_inventory` |
