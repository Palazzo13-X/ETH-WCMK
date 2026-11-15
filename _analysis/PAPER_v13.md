# ETH-WCMK v13 — controle ético delegável com supervisão ancorada, cobertura declarada e hierarquia geométrica incondicional

**Versão:** v13 (Rodada 5). **Fonte normativa das equações:** `_analysis/SPEC_v13_equations.md` (E1–E32; delta sobre `SPEC_v12_equations.md`). **Implementação autoritativa:** `_analysis/formal_core/core.py`, `geometry.py`, `facet_registry.py`, `fact_grounding.py`. **Artefatos de evidência:** `Evaluacoes/r5/` (roundada corrente); `Evaluacoes/r4/` e `Evaluacoes/r3/` citados explicitamente como históricos e imutáveis (decisão D5.10). **Gate report:** `_analysis/GATE_REPORT_r5.md`. Todo número citado tem artefato de origem; o Apêndice B liga cada afirmação a um campo JSON.

---

## Resumo

ETH-WCMK confronta um *caso* (ETHCASE) com um *perfil de agência delegada* (WCMK) e produz um veredito de cinco classes (ABSTAIN, PROHIBIT, REVIEW_REQUIRED, ALLOW_WITH_GUARDS, ALLOW) mais grandezas intermediárias auditáveis: adequação em banda, déficit por pilar e por faceta, gap material, risco residual, exposição entre pilares, necessidade de revisão e regime de supervisão.

Seis mudanças estruturais diferenciam a v13:

1. **Hierarquia geométrica incondicional (D5.1).** Os termos estruturais S₂ ≥ S₃ ≥ S₄ deixam de depender de uma condição sobre α e β: α passa a ser **derivada** de β como marginal do retículo, α_e = (1/3) Σ_{f ⊃ e} β_f. Com β_f = 1/4, α_e = 1/6 — os valores exatos da calibração v10–v12, de modo que **nenhum número publicado muda**. Proposição 1 demonstrada e testada no grid completo {0, 0.05, …, 1}⁴ (I34).
2. **β diferenciado (D5.5).** Dez facetas reequilibradas. Pares de facetas com vetores β idênticos: **8 → 1** (resta C3 ≡ C7, deliberado); pares a distância de Chebyshev < 0,12 contando os idênticos: **26 → 23** (quase-idênticos puros: 18 → 22, porque desfazer uma duplicatura exacta converte um par igual em um par próximo). Censo de aridade: 1 uni-pilar, 10 bi-pilares, 22 tri-pilares, 0 quadripilares. Efeito medido em κ: **+0,0019** (IC95 [0,0009; 0,0032]) isolado, **+0,0094** (IC95 [0,0069; 0,0120]) junto da supervisão.
3. **Regime de supervisão derivado dos fatos (D5.4, E11c′).** `irr_eff = irr · (1 − 0,45·O)`; O ∈ {unspecified 0,0; none 0,0; out_of_loop 0,2; on_the_loop 0,5; in_the_loop 0,8}, inferido por `oversight_from_facts` — nunca declarado sem fato correspondente. Efeito medido: **Δκ = +0,0078** (IC95 [0,0057; 0,0100]) sobre 130.680 pares do corpus completo. É o único mecanismo novo da rodada que melhorou a concordância.
4. **Cobertura como parâmetro declarado e casos genuinamente incompletos (D5.8, E26′).** O gate de cobertura (0,70) era uma constante embutida que nunca disparava (D4.37). Agora é campo da calibração, validado por I44, e o corpus v7 contém perfis que declaram entre 9 e 33 dos 33 deveres: **18.240 abstenciones por cobertura** sobre 220.400 pares. O rubric normativo adotou a regra V1 ("verificação adiada"): sem o gate, tratar dever não declarado como violação derruba κ do painel de 0,8085 a 0,0801.
5. **ReviewNeed (E32), índice não-decisional.** `ReviewNeed = clamp(0,30·banda + 0,25·gap_material_low + 0,20·u + 0,25·(1−cobertura))`. Não altera a escada; ordena casos que compartilham veredito pela quantidade real de revisão externa exigida (I36).
6. **Mecanismos abertos e medidos, não assumidos.** λ(E) (saliência do caso) e Ψ (exposição de dever entre pilares, coeficiente ζ) foram implementados, testados e **mantidos desativados** porque o efeito medido é nulo ou negativo: s = 0,5/1,0/2,0 → Δκ −0,0001/−0,0002/−0,0003; ζ = 0,05/0,10 → −0,0013/−0,0030.

Validação: **69 testes de invariantes** (I1–I44) passando; **2.064 probes adversários / 7.815 asserções / taxa 1,000** re-executados contra o núcleo v13; espelho aritmético das **220.400 confrontações** do corpus v7 com **diff máximo 0,0** e 0 divergências de veredito; ontologia v4.2 (1.919.283 triplos de instância) SHACL-conforme. O resultado empírico central é **κ = 0,5336** contra o consenso do painel normativo (v6: 0,4681, protocolo idêntico), **0,8167** no estrato em que o painel é unânime (112.179 pares), **0,1371** no de maioria e **0,0526** no contestado (`Evaluacoes/r5/kappa_by_stratum_v13.json`). O gate G7′ (κ ≥ 0,60 como número único) **continua não atingido** e é reportado como tal: o teto estrutural é a discordância entre as próprias lentes normativas (κ A–B 0,3533; A–C 0,6447; B–C 0,3153), não o modelo. A limitação central permanece explícita: não há ratificação humana do ground truth (D4.5); o pacote de adjudicação cega (`adjudication_packet_blind.csv`, 120 casos, 360 células vazias) existe para fechar essa lacuna, e sua análise de poder mostra que 25 adjudicações independentes bastariam para uma semi-largura de IC ≤ 0,05 em κ ≈ 0,60.

---

## 1. Motivação e tese

Um filtro de conteúdo produz uma etiqueta binária e um score. Um controle ético delegável precisa de três coisas que um filtro não fornece: (a) decomposição explícita dos deveres exigidos pelo caso; (b) uma regra que impeça que um dever crítico seja compensado por desempenho elevado em outro pilar; (c) uma gradiente de respostas — permitir, permitir com salvaguardas, escalar a revisão, abster-se, proibitar — operacionalmente estável.

A tese é que essa camada pode ser construída como modelo formal auditável, implementado, testado e ancorado em observações verificáveis, sem apelar a uma métrica única de "qualidade ética". O modelo **não** afirma ser superior a guardrails industriais (não há benchmark correspondente em `Evaluacoes/`) nem estar validado por juízo humano.

Seis afirmações sustentam a arquitetura:

1. **Caso e agência são objetos distintos e acoplados.** `C(E, a)` é um operador binário (`confront()`) avaliado sobre 220.400 pares (`corpus_v7_confrontations.jsonl`; contagem em `corpus_v7_coverage.json`, `pairs_adjudicated = 220400`).
2. **A não-compensação exige granularidade de faceta, não de pilar.** Sob v11, uma guarda C3 zerada ainda produzía nível C = 0,929; sob v12/v13 retorna 0,000 (`delta_v12.json`, re-verificado em `B8_probes_reverified_v13.json`).
3. **Risco residual e adequação são grandezas independentes.** `R_r = R_c·(p_fail+σ)/(1+σ)`; existem perfis com Aa idêntica e probabilidade de falha distinta (witness determinístico em `delta_v12.json`; 902 buckets de mesma Aa com dispersão de ratio 0,505).
4. **Um nível declarado não é evidência.** E30 liga fatos verificáveis do caso ao teto que uma faceta pode atingir. Medido em B22: **98,27%** dos pares contêm pelo menos uma declaração contrariada por um fato; **18.898 vereditos mudam** (43,74%) e κ sobe de 0,2463 a 0,5526 (Δ **+0,3062**) quando a ancoragem é aplicada.
5. **A decisão precisa de memória.** A histerese (E13d) bloqueia afrouxamentos: 6.382 transições mais permissivas bloqueadas e 103 oscilações A–B–A em 20.436 trajetórias de 8 passos (`B12_temporal_v12.json`).
6. **Saber quem vigia altera o peso do dever, não a etiqueta moral.** A supervisão reduz a irreversibilidade *efetiva* do resultado (E11c′) e eleva o requisito sobre M9 quando não existe canal humano (REQ_MISSING_OVERSIGHT = 0,08). Novidade mensurada da rodada: +0,0078 κ.

---

## 2. O modelo

### 2.1 Quatro pilares, por definição

`p ∈ {W, C, M, K}` (querer, poder, dever, saber) são famílias de exigência usadas pelo modelo. É uma **stipulação de engenharia**, não uma demonstração de irreducibilidade: nada no núcleo prova que sejam quatro e não cinco. O canon de facetas (§2.4) é o que dá conteúdo operacional a cada pilar.

### 2.2 O tetraedro como índice relacional

A camada geométrica é o face-lattice da 3-simplex, isomorfo aos subconjuntos não-vazios de um conjunto de quatro elementos: 4 vértices, 6 arestas, 4 faces, 1 célula = **15 slots relacionais** (`geometry.lattice_cardinality()`; 15 = 2⁴ − 1; I41). Não existe "distância entre agentes" no modelo (D4.4): `chordal_distance()` e `tv_distance()` são utilitários de teste.

**E1 — vértices centrados:** `v_i·v_j = −1/3`, `Σ_p v_p = 0`, `‖v_p‖ = 1`. **E17:** `‖v_p − v_q‖ = √(8/3) ≈ 1,633`. Errata do PDF-fonte: o centroide impresso confunde circunraio (√6/4 = 0,612372) com inraio (√6/12 = 0,204124); o volume do tetraedro de vértices unitários centrados é √2/12 = 0,117851.

**E19 — redundância volumétrica demonstrada:** as frações de volume dos sub-tetraedros definidos por `x(s)` são numericamente idênticas às coordenadas baricêntricas (diferença máxima < 10⁻⁹). Uma camada "de coerência volumétrica" não acrescenta informação.

**Novidade v13 (Proposição 1).** Para A ⊆ {W,C,M,K}, déficit conjunto `δ(A) = min_{p∈A} d_p` (t-norm de Gödel: deveres que devem ser cumpridos *todos* simultaneamente). Definindo `S₂ = Σ_{|A|=2} α_A δ(A)`, `S₃ = Σ_{|A|=3} β_A δ(A)`, `S₄ = δ({W,C,M,K}) = min_p d_p`, e derivando α da β,

```
α_e = (1/3) Σ_{f ⊃ e} β_f        (marginal do retículo)
```

então `min_p d_p ≤ S₃ ≤ S₂ ≤ max_p d_p` para **todo** vetor de déficit, sem condição adicional. Em v12 a hierarquia era condicional (`α_e ≥ (1/3)Σβ_f`) e o desenho de sensibilidade registrava 999 de 2.400 limites de aresta violados (`B10_sobol.json`, `coherence_diagnostics`) — problema que desaparece quando α é derivada e não calibrada. `Calibration.is_valid()` (v13) **rejeita** qualquer calibração que declare α ≠ marginal(β) (I35).

### 2.3 Perfil = (forma, magnitude), não simplex

O perfil é um vetor de **níveis independentes** `ℓ_p ∈ [0,1]`, não um ponto do simplex. Daí derivam duas grandezas reportadas separadamente: forma `s_p = ℓ_p / Σ_q ℓ_q` (usada só pela embedding) e magnitude `M = Σ_p ℓ_p ∈ [0,4]`. Ambas aparecem no output de `confront()`.

### 2.4 O canon de 33 facetas (v13)

33 facetas (24 do catálogo original + W6, C7, M7, K8 + M8, M9, M10, C8, K9). Regras estruturais verificadas por `validate_registry()` (lista vazia, medida nesta rodada): Σ_p β_fp = 1; β_fp ∈ {0} ∪ [0,15, 1]; **nenhuma faceta toca os quatro pilares** — 1 toca um, 10 tocam dois, 22 tocam três; 12 guardas duras (W2, W6, C3, C6, C7, M1, M4, M7, M8, M9, M10, K6); 33 campos `observable` declarados; todas as 33 têm ≥ 5 casos críticos no corpus (`facets_with_ge_5_critical_cases = 33`).

**D5.5 — β diferenciado (adotado).** W6 (0,45;0;0;0,55); C2 (0;0,70;0,15;0,15); C5 (0;0,60;0,15;0,25); M2 (0;0,15;0,70;0,15); M4 (0;0,25;0,55;0,20); M10 (0,25;0;0,60;0,15); K1 (0;0,15;0,15;0,70); K2 (0;0,30;0,20;0,50); K5 (0,35;0,15;0;0,50); K7 (0;0,15;0,25;0,60). Justificação: D4.16 mantinha facetas separadas apesar de β idênticos porque fundi-as reduziria o canon a ~13 facetas e quebraria R3 (β ≥ 0,15). Agora a separação tem conteúdo numérico: **pares idênticos 8 → 1**, **pares dentro de ‖Δβ‖∞ < 0,12 (incluindo idênticos) 26 → 23**; os quase-idênticos puros sobem de 18 a 22 precisamente porque cada duplicatura desfeita passa a contar como par próximo e não como par igual. O par restante, C3 ≡ C7 = (0;0,6;0,2;0,2), fica deliberadamente fundido no mesmo vetor: ambas são deveres de controle/rendição com participação simétrica de M e K, e a distinção está nos observáveis (kill switch vs exit right) e nos fatos que os ancoram.

**Ablação do β (B21, 400 casos × 120 personas, bootstrap pareado 200):** retirar as 12 guardas → κ 0,4633 → **0,1399** (Δκ −0,3234, IC95 [−0,3306; −0,3147]) e Aa média sobe de 0,3516 a 0,6153. Colapsar os deveres multi-pilares ao pilar primário (destruir o compartilhamento) → κ **0,2691** (Δκ −0,1942, IC95 [−0,2025; −0,1831]) e Aa média sobe a 0,5627. Retirar uma guarda isolada altera κ em ≤ 0,0042 (C7 −0,0042; M9 −0,0024; M7 −0,0020; M8 −0,0012; M1 −0,0012; W6 +0,0014; M10 +0,0013). Leitura honesta: **o sistema é robusto a cada guarda individual e frágil ao conjunto** — a não-compensação é uma propriedade do desenho, não de uma faceta.

**D5.7 — rebalanceamento de criticidade (rejeitado).** Eleva a criticidade de TB/TS/IM ao nível de SA/JS. Medidas: variante agressiva (400 casos, 48.400 pares) κ 0,4613 → 0,4466, **Δκ −0,0147 IC95 [−0,0179; −0,0116]**; variante mild cap-3 (859 casos, 103.939 pares) κ 0,4358 → 0,4308, **Δκ −0,0050 IC95 [−0,0072; −0,0022]**; variante targeted TB/TS/IM (859 casos, 103.939 pares) κ 0,4358 → 0,4281, **Δκ −0,0077 IC95 [−0,0095; −0,0058]**. As three são negativas e significantes: D4.18 permanece rejeitada. Artefactos: `B20_variant_eval_full.json`, `B20_crit_mild_cap3_full_corpus.json`, `B20_crit_targeted_full_corpus.json`.

**Assimetria declarada.** λ = (0,30; 0,25; 0,25; 0,20) e μ = (0,15; 0,40; 0,20; 0,25) são escolhas normativas explícitas; a massa efetiva de β nos pilares difere de λ em até 0,1348 (`facet_review_stats_v12.json`). λ é peso **normativo** sobre pilares; β é distribuição **interna** às facetas (D4.14).

### 2.5 Projeção, requisitos e políticas de agregação (E2, E3, E18, E20–E24)

**E2:** `ℓ̄_p = Σ_f β_fp ṽ_f / Σ_f β_fp`. **E3:** `q_p = Σ_f β_fp r_f / Σ_f β_fp`, `d_p = max(0, q_p − ℓ_p)`.
**E27 (requisito por faceta):** `r_f = base(c_f) + 0,08·S_E + 0,05·I_E + 0,03·P_E + 0,04·H_E + 0,05·U_E·1[primário = K]`, base(2)=0,55, base(3)=0,70, base(4)=0,85; guardas: `r_f ≥ guard_min + 0,05`; clamp [0,30; 0,95].
**Políticas (E20–E23):** `weighted_mean`; `guarded_weighted_mean` (cap se x_f < θ_f^g); `threshold_override` (zero se x_f < θ_f^g); `uncertainty_penalized_mean`.
**E24 — piso lexicográfico universal:** para toda faceta guardada abaixo do piso, `ℓ_p = min(ℓ̄_p, band(x_f, c_f^u))` para todo pilar com β_fp > 0. É a correção que impede a compensação entre pilares. Monotonicidade preservada (I5).
**E18:** `Δ_f = max(0, r_f − band(x_f, c_f^u, mode))`; o gap que alimenta veto e Φ usa o nível ajustado por confiança, não o valor corrigido pela política, para não contar duas vezes a mesma violação.

### 2.6 Déficits e adequação bruta (E4, E8–E10, E33)

`D = Σ_p λ_p d_p` (λ constante; v13 mantém λ(E) desativada, §2.11).
`Aa_raw = clamp(1 − D − γS₂ − ηS₃ − ωS₄ − ρu − δΦ − ζΨ)`, com `u = U_E·d_K/max(q_K, ε)`, `Φ = Σ_f c_f Δ_f / Σ_f c_f` (anti-diluição) e **Ψ** = média ponderada por σ do gap de deveres que cruzam pilares, σ_f = 1 − max_p β_fp. Orçamento declarado: γ+η+ω+ρ+δ+ζ ≤ 0,45 (`is_valid()`). Canônico: γ=0,12, η=0,05, ω=0,03, ρ=0,10, δ=0,05, **ζ=0**.

**D5.3 — Ψ é diagnóstico, não decisão.** Ψ é reportado (média **0,1703** sobre os 220.400 pares do corpus v7, campo `cross_pillar_duty` em `corpus_v7_confrontations.jsonl`) e entra no `crossPillarDuty` da ontologia, mas ζ = 0 porque o efeito medido é **negativo**: ζ = 0,05 → Δκ −0,0013 (`B21_ablation.json`, 48.000 pares) / −0,0018 (`B20_variant_eval.json`, 48.400 pares) / −0,0028 (corpus completo, 130.680 pares); ζ = 0,10 → −0,0030 / −0,0036 / −0,0059. I39 garante que ζ = 0 reproduz exatamente a Aa de v12 (diff = ζΨ = 0). I40: deveres uni-pilares (C1) não contribuem a Ψ.

### 2.7 Déficits guardados, gap material, veto e stakes (E11a–E11f, E11c′)

`d_p^guard = max(d_p, max_{f: g_f ∧ β_fp>0} Δ_f)`; `m(E) = max{Δ_f : c_f = 4 ou g_f}`;
`V = {p : d_p^guard ≥ θ_p ∧ (p ∈ criticalPillars(E) ∨ floor_breach_p)} ∪ {pilares da faceta material, se m(E) ≥ material_gap}`;
`w_cap = cap_base + cap_stakes_gain·stakes(E)`; `Aa = min(Aa_raw, 1 − w_cap·max(m(E), max_{p∈V} d_p^guard))`.
Hard veto (E11e) com `scale = 1 + 2·max(0, (stakes_veto_min − stakes)/stakes_veto_min)`:
`hard_p ⇔ d_p^guard ≥ θ_p + hard_veto_delta·scale ∨ (floor_breach_p ∧ stakes ≥ stakes_veto_min) ∨ (m(E) ≥ critical_prohibit_gap ∧ stakes ≥ stakes_veto_min)`.

**E11f — stakes com supervisão (v13):**
```
irr_eff = REVERSIBILITY[I_E] · (1 − 0,45·O(oversight))
stakes  = clamp(0,45·S_E + 0,30·irr_eff + 0,15·(P_E/0,10) + 0,10·H_E, 0, 1)
```
O(·) ∈ {unspecified 0,0; none 0,0; out_of_loop 0,2; on_the_loop 0,5; in_the_loop 0,8}, derivado dos fatos por `oversight_from_facts` (revisão humana + auditoria independente ⇒ in_the_loop; revisão **ou** canal de recurso ⇒ on_the_loop; nenhum fato ⇒ none; ausência de informação ⇒ unspecified, preservando v12). I42: o derivador nunca inventa supervisão. I38: stakes ordenadas por regime (in_the_loop ≤ on_the_loop ≤ none) para o mesmo caso — a supervisão nunca *aumenta* o stake.
Requisito adicional: se `oversight = none`, `q_f` de M9 cresce 0,08 — o agente tem de suprir o que a instituição não tem.

**Medida (B20, 130.680 pares).** κ baseline (β canônico) 0,4049; com supervisão 0,4127; Δκ **+0,0078**, IC95 [0,0057; 0,0100] por bootstrap pareado de 200 remuestreamentos sobre os *mesmos* pares. Na amostra estratificada de 400 casos: +0,0114 [0,0080; 0,0146]. B21 confirma com um segundo caminho (β diferenciado + supervisão: 0,4748, Δ +0,0115 [0,0085; 0,0149]). Regimes presentes (por par): none 67.715; on_the_loop 91.640; in_the_loop 61.045.

**Sobre "não-compensação":** o modelo não é integralmente não-compensatório. `Aa_raw` compensa déficits entre pilares; o que é não-compensável são as 12 guardas via E24 e o teto E11d. Distinção declarada, não retórica.

### 2.8 Risco residual (E12, E14)

```
p_fail = clamp(1 − Σ_p μ_p ℓ_p, 0,02, 0,98),   μ = (0,15; 0,40; 0,20; 0,25)
σ      = clamp(0,05 + 0,15·S_E·I_E + P_E, 0, 0,35)
R_r    = R_c·(p_fail + σ)/(1 + σ)
harm   = R_c·stakes(E)·E_exposure
```
Propriedades (I2, I3, I28, I29): `σR_c/(1+σ) ≤ R_r ≤ R_c`; R_r estritamente decrescente em confiabilidade; "atenuação sem extinção". Não-redundância empiricamente documentada (902 buckets de Aa idêntica, dispersão máxima 0,505).

### 2.9 Banda de incerteza, cobertura e abstenções (E25, E26′, E29)

`band_value(x, c, mode)` produz `[Aa_low, Aa_high]` recalculadas integralmente; **a decisão usa Aa_low** (I32).
**E26′ (cobertura):** `completeness = |declared facets|/33 < coverage_gate` ⇒ ABSTAIN **sem** Aa reportada. `coverage_gate` é campo da calibração, bounds [0,5; 0,95], canônico **0,70**; I44 exige que seja declarável (perfil de 23/33 deveres abstém com gate 0,70 e não abstém com gate 0,60; gate inválido ⇒ erro).
**E29 (epistêmica):** `(norm_conflict ≠ none ∨ evidence_conflict) ∧ U_E ≥ 0,60 ∧ ℓ_K ≤ 0,65` ⇒ ABSTAIN.
No corpus v7: ABSTAIN total **34.615** = 16.375 epistêmicas + 18.240 por cobertura (15,71% dos pares). D4.37, que mostrava 0 disparos naturais, está superada: o corpus agora contém perfis genuinamente incompletos (6 tipos de persona: blind por pilar W/C/K, boundary_low 0,697, sparse, minimal).

### 2.10 Saliência do caso λ(E) (E4′, D5.2)

`λ_p(E) = λ_p·q_p^s / Σ_q λ_q·q_q^s`, sempre Σλ(E) = 1; s = 0 ⇒ identidade (I37). Medido (`B20_canonical_beta_check.json`, 130.680 pares): s = 0,5 → Δκ −0,0001; s = 1,0 → −0,0002; s = 2,0 → −0,0003; Aa média cai de 0,3523 a 0,3483. **s = 0 é canônico**; o grau de liberdade fica declarado porque um corpus humano futuro pode justificá-lo. A hipótese D4.12 ("λ dependente do caso") morre como hipótese empírica: o mecanismo existe, é testado, não melhora a concordância.

### 2.11 ReviewNeed (E32, D5.6)

`ReviewNeed = clamp(0,30·(Aa_high − Aa_low) + 0,25·gap_material_low + 0,20·u + 0,25·(1 − cobertura)) ∈ [0,1]`, monotônico em cada componente (I36). Não altera a escada: é um índice de **quanto revisão externa o caso exige**, útil para triagem humana e para reportar casos com o mesmo veredito em ordem de urgência. No corpus v7, média **0,2659** nos 202.160 pares com adequação reportada (campo `review_need`); nas 12 dimensões do painel de sensibilidade B23 oscila entre 0,2423 e 0,2718 conforme a calibração.

---

## 3. Ancoragem por observação (E30) e probes de contradição (B22)

O núcleo recebe um **perfil declarado**. Um fato verificável do caso nomeia uma faceta e limita o nível que ela pode atingir:

```
ℓ_f ← min(ℓ_f, q_f·[1 − s·(1 − c(fato))]),   s ∈ [0,1]
```

s = 0 reproduz v11; s = 1 é o padrão. Âncoras declaradas em `FACT_MAP` (c = conformidade): logs_available / independent_audit → M6; notice_given → M8; human_review_channel / appeal_channel → M9; remedy_days → M7; consent_obtained / worker_consulted → M10; data_minimised → C8; sunset_review → K9; containment_exercised → C7; affected_can_exit → C3; prior_incident → C6 (abaixa a executabilidade segura). Fatos sem âncora estão listados explicitamente (`UNANCHORED_FACTS`); `affected_people` entra apenas pela escala de exposição em `harm`.

**Fix v13 (D5.9):** o cap só se aplica a facetas **declaradas**. Uma faceta não declarada não tem nível a capar; o efeito aparece pela via da cobertura (E26′), não pela aritmética do cap.

**B22 — a ancoragem é o mecanismo mais forte do modelo** (300 casos estratificados, 43.210 pares, força s = 1):
| grandeza | valor |
|---|---|
| pares com ≥ 1 declaração contrariada por fato | 42.464 (**98,27%**) |
| caps aplicados | 224.097 |
| excesso médio declarado sobre o cap | 0,3611 |
| facetas mais capadas | M7 (32.404), M9 (28.867), M6 (28.570), M10 (27.348), K9 (25.480) |
| vereditos que mudam (com vs sem E30) | **18.898 (43,74%)**; REVIEW→PROHIBIT 15.153; AWG→PROHIBIT 1.620 |
| Aa média com / sem E30 | 0,3633 / 0,6481 |
| κ modelo↔painel com / sem E30 | **0,5526 / 0,2463** (Δ +0,3062) |

O resultado de v12 (κ 0,1661 → 0,3901 varrendo s de 0 a 1, `fact_grounding_sweep.json`) permanece válido; B22 mede o mesmo efeito sobre o corpus v7 e o isola: quase metade dos vereditos dependem de fatos. A implicação metodológica é direta: **autodeclaración sem observação não é evidência**, e um sistema que aceita "nível 0,9 de canal de recurso" sem canal declarado é auditable apenas por boa vontade.

Monotonicidades testadas (G1–G7, `tests/test_fact_grounding.py`): a ancoragem nunca eleva um nível; fato com c = 1 não introduz cap próprio; efeito monotônico em s; Aa nunca aumenta; guarda procedural zerada dispara veto; todo fato do corpus tem âncora declarada ou está na lista explícita.

---

## 4. Escada de decisão

```
if hard_veto: PROHIBIT
categorical = stakes ≥ prohibit_stakes_min ∧ (¬prohibit_needs_material ∨ m ≥ critical_prohibit_gap)
if categorical ∧ (Aa_low ≤ bar − prohibit_margin ∨ ratio ≥ ratio_prohibit): PROHIBIT
elif Aa_low ≤ bar ∨ (V ≠ ∅ ∧ Aa_low ≤ bar + veto_slack) ∨ ratio ≥ ratio_review: REVIEW_REQUIRED
elif Aa_low ≤ bar + guards_margin ∨ ratio ≥ ratio_guards ∨ V ≠ ∅: ALLOW_WITH_GUARDS
else: ALLOW
```
`bar(E) = clamp(b₀ + b₁S_E + b₂I_E + b₃j(E) + b₄H_E, 0,30, 0,90)` (j = índice do modo prudencial). Um veto disparado nunca é suplantado pelo score: no melhor caso o caso é admissível com salvaguardas (I4, I27).
**E13d histerese:** um veredito só pode ficar mais permissivo se `Aa_low ≥ bar + hysteresis` (0,05); endurecer nunca é bloqueado. **E28 (agência estratificada):** `confront_chain` usa o elo mais fraco e reporta `weakest_layer`; 32 de 33 facetas exigem a camada accountable (D4.30, B15).

Distribuição do modelo no corpus v7: PROHIBIT **152.439**; REVIEW_REQUIRED 32.996; ABSTAIN 34.615; ALLOW_WITH_GUARDS 349; ALLOW **1**. Veto em 90,6% dos pares, hard veto em 13,45%. Consenso do painel: PROHIBIT 162.507; ABSTAIN 30.077; REVIEW 22.687; AWG 2.653; ALLOW 2.476. Aa média 0,3551, mediana 0,3462, **máximo 0,9508**, share Aa ≥ 0,999 = **0,0%** (gate b do plano: < 0,05 — cumprido). A classe ALLOW quase nunca ocorre: 1 par em 220.400 — resultado do desenho dos requisitos, não uma falha de vocabulário.

---

## 5. Agência estratificada (E28)

Estado medido (B15, r4; permanece válido para v13 porque o núcleo não alterou E28): 62.320 confrontações na camada system (incl. 1.520 autodeclaradas), 60.800 na camada model, 60.800 na camada operator. Uma faceta só é delegável se todo pilar que alimenta é exercível pelo delegado: **1 de 33** (C1) é delegável; **32 de 33 (96,97%)** exigem a camada accountable. **1.352 de 1.520 casos (88,95%)** têm pilar crítico em W ou M — esses deveres não podem ser transferidos; o fallback policy deixa de ser opcional. Com o melhor delegado, 0 vereditos mudam; com o pior, 127 mudam (121 mais restritivos, 6 abstenções epistêmicas), Aa média 0,3358 → 0,2893 (−13,9%). O pilar garganta é C (905 casos). O veredito da cadeia pessimista concorda com o gold do perfil executor (κ 0,4067) melhor do que o declarante concorda com seu próprio gold (0,372): E28 tem conteúdo normativo, não é um cap adicional.

---

## 6. Ontologia v4.2 (RDF/SHACL/SPARQL)

Gerada **a partir** do núcleo, nunca ao contrário. Módulos: `01_core` … `07_grounding` (308.466 bytes) + shapes `ontology_shapes.ttl` (26.832 bytes, v4) e `ontology_shapes_v6.ttl` (5.980 bytes, E30/ReviewNeed/supervisão) + fixtures inválidos (63 + 13) + instânciação do corpus: **1.919.283 triplos** em `fixtures/instances.ttl` (64.242.382 bytes), somando **1.927.780 triplos validados** com os 8.509 dos módulos — 1.520 casos, 5.150 perfis, 3.755 confrontações instanciadas (amostra estratificada), 1520 cadeias, 50.160 requisitos de faceta, 169.950 observações, 21.280 ancoragens de fato (E30), 16.475 registros de falha de guarda.

Novidades v4.2: `eth:OversightRegime` (5 regimes, sh:in sobre 5 IRIs) em todo caso; `eth:reviewNeed`, `eth:crossPillarDuty` (Edge/Face) e `eth:caseSalienceW..K` nas confrontações; `cal:crossPillarCoefficient = 0,0`, `cal:salienceAdaptation = 0,0`, `cal:oversightAttenuation = 0,45`, `cal:coverageGate = 0,70` declarados no addendum de calibração; regras `rule_lattice_marginal_alpha`, `rule_cross_pillar_exposure`, `rule_review_need`, `rule_coverage_gate`. Pares abstidos por cobertura **não** carregam literais de adequação — verificação explícita no validador.

**Revalidação (G14′, fechada — gate G4′: PASS).** SHACL: shapes v4 sobre as instâncias **0 violações** (54,04 s); shapes v6 **0 violações** (27,91 s); módulos 0 (0,26 s). As 1.520 violações que as shapes v6 daviam antes eram um bug de forma (`sh:in` com literais string em vez de IRIs, D5.11), não uma incompatibilidade do modelo. Fixtures intencionalmente inválidos: **76/76** detectados e **76/76** atribuídos à shape esperada (1.246 violações no grafo inválido) — a contraprova do gate. **42 verificações SPARQL/Python (15 deontológicas) passam todas**: α_e = (1/3)Σ_{face⊃edge} β_f; regime de supervisão igual ao que os fatos implicam; Ψ ∈ [0,1] e composto apenas por deveres multi-pilares; cobertura < 0,70 ⇒ ABSTAIN sem literal de adequacy; S₂ ≥ S₃ ≥ S₄; nenhuma faceta spanning 4 pilares; ζ = 0, s = 0, gate = 0,70 declarados em **todos** os indivíduos de calibração (D5.18). Espelho aritmético graph ↔ escada Python ↔ `core.decide` sobre 403 confrontações estratificadas por (domínio, veredito): **diff máximo absoluto 1,61e-12**, **0 divergências de veredito**. Dos achados reportados (não bloqueam o gate): 268 enlaces de cadeia em que a camada delegante retém o dever crítico (E28) e 0 confrontações com `declaredStakesSum` acima do teto 2,1. Lattice: **15 slots** (4 vértices, 6 arestas, 4 faces, 1 célula), cada termo somando 1; registry RDF ↔ CSV ↔ `facet_registry.py`: **0 desencontros** nas 33 facetas. Runtime total da validação: **301,9 s**. Artefacto: `Evaluacoes/r5/ontology_v4_2_validation.json`.

---

## 7. Corpus v7 e ground truth híbrido

### 7.1 Composição

`Evaluacoes/r5/corpus_v7_*` (gerador `gen_corpus_v5.py` v13, seed 20261104, ladder congelado de r3 para o corpus e baterias de ajuste reportadas separadamente). **1.520 casos** (1.200 camada A paramétrica, 320 camada B narrativa) sobre **13 domínios**: SA, JS, IC, FI, PD, GP, IM, ED, TB, MA, TS, RS, DS. Severidade: 386 baixa, 378 média, 378 alta, 378 crítica. Irreversibilidade: 539 reversíveis, 515 parcialmente irreversíveis, 466 irreversíveis. Prudencial: 531 standard, 520 elevated, 469 maximum. Horizonte: 411 imediato, 387 curto, 387 médio, 335 longo. Conflitos normativos: individual-coletivo 234, inovação-precaução 234, autonomia-benefício 234, legal-ético 233, nenhum 234, competição-cuidado 117, curto-longo 117, transparência-eficácia 117. Ambiguidade injetada: 179 casos com conflito normativo não resolvido, 126 com conflito de evidência (condições que ativam E29).

**Personas.** 144 personas de 36 tipos, 96 com déficit concentrado (5 tipos em W, 6 em C, 7 em M, 6 em K). **Novidade v7:** 6 tipos (24 instâncias) declaram apenas parte do canon — entre **9 e 33** dos 33 deveres —, com `declared_facets` explícitos e `omit` declarado. Teto efetivo 0,95, 0 personas acima (`personas_exceeding_cap = 0`). Total de confrontações: **220.400** = 1.520 casos × 145 perfis (144 personas + o perfil `AGENT-declared`), todas adjudicadas.

Estratos de cobertura: 183.920 pares com canon completo; 18.240 com declaração parcial (todos abaixo do gate, completeness < 0,70); κ modelo↔painel **0,3832** (full), **0,3293** (partial), **1,0000** (below gate — o modelo abstém e o rubric também abstém por V1).

**Massa de criticidade por domínio (corpus v7):** SA 131, JS 124, FI 119, IC 113, PD 115, GP 116, RS 95, TB 89, TS 88, DS 88, ED 86, MA 82, IM 80. A matriz continua derivada por regra para 10 domínios e por analogia para TS/RS/DS (D3.6), sem painel de especialistas — limitação declarada (§9.3).

### 7.2 Ground truth: kernel + três lentes, sem raters humanos

O gold é produzido **por par**: cada veredito usa os níveis que a persona efetivamente declarou. `stakes` vem do núcleo (`case_stakes`); os painéis testam níveis absolutos contra pisos de dever declarados na rubrica e contra fatos declarados — **nunca** leem `facet_requirements`, λ, β, S₂/S₃/S₄, o cap de veto nem Aa. Desenho anti-circularidade.

- **Kernel compartilhado** (K0–K5, 6 regras).
- **Lente A — deontológica** (11 regras: Rio Principle 1, UDHR Art. 10, UN CRC Art. 12/Belmont, OECD, GDPR Art. 22/ILO, direito à explicação, ACM/IEEE 1.5, não-compensação de deveres categóricos).
- **Lente B — prudencial/consequencialista** (8 regras: orçamento de dano esperado, efetividade do recurso, dano limitado, proporcionalidade da exposição, sunset, histórico previo, linha vermelha de irreversibilidade, capacidade demonstrada).
- **Lente C — ancorada em instrumentos** (15 regras: GDPR Arts. 5/22, Rio 1, ILO, Helsinki/Belmont, ISO 26262/UN Safe Systems, NIST CSF, UDHR Art. 10, ACM/IEEE 1.5…).
- **Regra V1 (D5.8, v13): gap de verificação.** Se a declaração do perfil não cobre o gate de cobertura, o painel **abstém** (adjudicação adiada) em vez de tratar o dever não declarado como violado. Alternativa contrafactual medida: se o painel assumisse violação, κ do modelo contra esse painel cairia de **0,8085** para **0,0801** sobre os 36.480 pares de declaração incompleta. Não é uma escolha estética: é a única leitura coerente com E26′, e está testada como invariante (I43).

Total: **34 regras**, todas disparando em ≥ 50 casos (mínimo 290 pares, máximo 101.221). Consenso = rank mediano com desempate precautor (spread ≥ 2 ⇒ mais restritivo). Unanimidade **50,9%**; spread ≥ 1: 49,1%. Kernel-only: 31.279 pares (14,19%) — abaixo do gate de 40% exigido pelo plano. κ entre painéis: A–B 0,3533; A–C 0,6447; B–C 0,3153.

**Estado da validação humana: inexistente.** `corpus_v7_audit_sample.csv` tem 120 linhas estratificadas por classe × domínio (ABSTAIN 24, ALLOW 2, AWG 26, PROHIBIT 24, REVIEW 44), **360 células vazias**, status UNADJUDICATED. O pacote cego (`adjudication_packet_blind.csv` + `adjudication_packet_key.csv`) e o protocolo (`_analysis/ADJUDICATION_PROTOCOL_v13.md`) existem para executar essa adjudicação; o protocolo define códigos de rationale H1–H6 e poder estatístico: na amostra de auditoria, κ entre modelo e consenso dos painéis é 0,2067 (SE 0,0482, IC95 [0,112; 0,301]) — mais baixo que o κ global porque a amostra é deliberadamente difícil; para semi-largura ≤ 0,05 em κ ≈ 0,60 bastam **25** adjudicações independentes.

---

## 8. Resultados

### 8.1 Invariantes formais (B1)

`pytest _analysis/formal_core/tests -q` → **69 passed em 45,75 s**. Cobertura: monotonicidade por faceta/pilar (I5, I6), identidade do déficit (I1), bounds do risco (I3), cardinalidade do lattice (I10, I22, I41), penalidade epistêmica (I9, I9b), anti-diluição Φ (I11), cap e hard veto (I4, I12, I12b), piso lexicográfico (I14, I18, I33), proporcionalidade (I15, I21), barra sensível a stakes (I16, I16b), veredito conservador (I32), histerese (I13), hierarquia **incondicional** (I34), α derivada (I35), λ(E) normalizada e degenerante (I37), ReviewNeed monotônico e limitado (I36), supervisão nunca eleva stakes (I38), ζ = 0 ⇒ Aa v13 = Aa v12 (I39), deveres uni-pilares fora de Ψ (I40), supervisão derivada e nunca inventada (I42), regra V1 do rubric (I43), gate de cobertura declarado e validado (I44).

### 8.2 Probes adversários (B8)

**2.064 probes, 7.815 asserções, taxa de passagem 1,000** re-executados contra o núcleo v13 (`Evaluacoes/r5/B8_probes_reverified_v13.json`, gerado por `run_battery_B8_v13.py`): não-compensação 1.536 (pillar_cap, cap_active, gap_removed, no_allow, cada 1.536/1.536; hard_veto 384/384), déficit crítico 132 (4 asserções × 132), monotonicidade 99, abstenção 132 (66/66 disparos e 66/66 não-falsos), histerese 165. Nenhum probe derivado do registro produziu compensação indevida de guarda.

### 8.3 Mecanismos novos e rejeitados (B20)

1.080 casos estratificados × 120 personas = 130.680 pares por variante; bootstrap pareado (200 remuestreamentos dos mesmos pares) para IC de Δκ.

| Variante | κ | Δκ | IC95 | Aa média |
|---|---|---|---|---|
| baseline (β canônico, ζ=0, s=0, sem supervisão) | 0,4028 | — | — | 0,3536 |
| + supervisão derivada (E11c′) | 0,4106 | **+0,0078** | [0,0057; 0,0100] | 0,3475 |
| + β diferenciado (D5.5) | 0,4047 | **+0,0019** | [0,0009; 0,0032] | 0,3529 |
| β + supervisão | 0,4122 | **+0,0094** | [0,0069; 0,0120] | 0,3468 |
| criticidade agressiva (400 casos, 48.400 pares) | 0,4466 | −0,0147 | [−0,0179; −0,0116] | 0,3373 |
| criticidade mild cap-3 (859 casos, 103.939 pares) | 0,4308 | −0,0050 | [−0,0072; −0,0022] | 0,3353 |
| criticidade targeted TB/TS/IM (859 casos) | 0,4281 | −0,0077 | [−0,0095; −0,0058] | 0,3357 |
| λ(E) s = 0,5 / 1,0 / 2,0 | 0,4028 / 0,4028 / 0,4025 | 0 / −0,0001 / −0,0003 | ≈ [−0,0002; 0] | 0,3569 / 0,3559 / 0,3539 |
| ζ = 0,05 / 0,10 | 0,4000 / 0,3969 | −0,0028 / −0,0059 | negativas | — |

κ por estrato de consenso, **corpus completo** (220.400 pares; artefacto `Evaluacoes/r5/kappa_by_stratum_v13.json`): unânime **0,8167** (112.179 pares), maioria **0,1371** (95.611), contestado **0,0526** (12.610). Na amostra estratificada de B20 (130.680 pares, `B20_canonical_beta_check.json`) os mesmos estratos dão 0,7348 / 0,1254 / 0,0402: a magnitude é a mesma e a diferença vem de quais pares entram na amostra. Por domínio (corpus completo): TS 0,6110; ED 0,6103; RS 0,5877; MA 0,5684; DS 0,5511; PD 0,5463; JS 0,5351; IC 0,5203; IM 0,5050; GP 0,5022; SA 0,4791; TB 0,4790; FI 0,4624. A estratificação (D4.32) não é cosmética: κ global 0,5336 é uma média ponderada de estratos que diferem por um factor de 16.

### 8.4 Ablação do canon (B21) — ver §2.4.

### 8.5 Contradicção declaração × fato (B22) — ver §3.

### 8.6 Sensibilidade global (B23)

Sem scipy: Morris (200 trajetórias × 4 passos elementares, 1.024 avaliações) + Sobol por Latin-hypercube pareado com swap (N = 1.024, M = 2, 2.048 avaliações) sobre **12 dimensões** da calibração v13: ζ, s, coverage_gate, oversight_attenuation, γ, η, ω, ρ, δ, λ_C, μ_C, θ_base. Painel = 12 casos reais cobrindo 13 domínios e 5 vereditos (200,7 s de runtime).

**Regra de leitura:** com painel de 12 casos e saída degrau (limites de decisão, guardas), os índices de ordem total saturam perto de 1; o que é reportável são S₁ e os μ*/σ de Morris. ST ≈ 1 com S₁ ≈ 0 significa "age por interação com os limiares", não "é principal".

| parâmetro | Morris μ* (Aa média) | Sobol S₁ | leitura |
|---|---|---|---|
| coverage_gate | 0,104 | 0,749 (Aa); 1,00 (abstenção/permissividade) | maior knob de toda a calibração — por isso foi declarado como parâmetro (I44) |
| γ | 0,081 | 0,123 | penalidade epistêmica é o principal peso do orçamento |
| ζ | 0,075 | 0,013 | mensurável, mas κ negativo ⇒ diagnostic-only |
| η / ω / δ / ρ | 0,060 / 0,054 / 0,053 / 0,053 | ≤ 0,05 | secundários |
| λ_C | 0,041 | 0,050 | — |
| **s (λ(E))** | **0,0004** | ~0,03 só por interação | inert; s = 0 canônico |
| **oversight_attenuation** | **0,0** (Aa) | **0,701** em hard_veto_rate | muda *quão forte* o veto fica, não o score de adequação |
| θ_base / μ_C | 0,0 | ≈ 0 | operam só por guardas/limiares (θ_base μ* 0,139 em hard_veto_rate) |

ΣS₁ < 1 para todas as saídas: o modelo é dominado por interações de limiar, não por efeitos aditivos. É por isso que a evidência de calibração no paper é Δκ por bootstrap pareado, não coeficientes de sensibilidade. Nota de integridade: a primeira execução de B23 produziu 87/400 pontos inválidos por ruído de ponto flutuante no topo dos bounds (0,10000000000000002); `is_valid()` agora tolera ε = 10⁻⁹ e o artefato re-executado é o reportado aqui.

### 8.7 Ruído nas declarações (B9, histórico v12)

Perturbar níveis declarados (n = 20.436): σ = 0,02 → flips 1,32%, κ 0,4651; σ = 0,05 → 2,94%, 0,4417; σ = 0,10 → 4,82%, 0,4199; σ = 0,20 → 8,56%, 0,3934. Degradación monotônica e modesta; assimetria interessante: com σ = 0,20 o modelo fica **mais restritivo** em 8,15% e mais permissivo em 0,41% (o ruído eleva U_E e endurece o veto em facetas de baixa stake).

### 8.8 Termos geométricos explicam algo? (B16, histórico)

Ablação multiplicativa de γ, η, ω sobre 183.920 pares: κ full 0,4681; γ=0 0,4678; η=0 0,4686; ω=0 0,4688; sem retículo 0,4688 — nenhuma diferença > 0,0007. Mas Aa média sobe 0,094 quando a geometria é removida. Conclusão mantida: **o retículo é índice relacional e dispositivo de auditabilidade (D3.4), não operador de inferência.** A v13 torna isso mais forte: a hierarquia é incondicional, então não se sustenta por condição calibrada — e mesmo assim não melhora a classificação.

### 8.9 Espelho aritmético total (B25)

`_analysis/analysis/mirror_full_corpus_v13.py` → `Evaluacoes/r5/mirror_full_corpus_v13.json`: **220.400 confrontações** recompostas persona-por-persona (fatores, jitter, cap, `omit`, supervisão) e recomputadas pelo núcleo v13. **Diff máximo em qualquer quantidade: 0,0** (Aa_low, Aa_central, Aa_high, bar, stakes, R_r, S₂, S₃, S₄, aa_raw, Φ, u, gap material). **0 divergências de veredito**; distribuição recomputada idêntica (152.439 / 32.996 / 34.615 / 349 / 1). Runtime 121,87 s. Consequência: nenhum número do corpus depende de estado não reproduzível.

### 8.10 Baselines, transferência e ajuste (históricos v12, preservados)

Baselines (B7, 56.144 pares de holdout): modelo 0,4834; melhor baseline BL5 "Aa sem cap de veto" 0,1464; pior BL13 "sempre REVIEW" 0,0000; margem +0,337. Transferência (B13): κ holdout 0,4834 vs in-sample 0,4618; camada B 0,6617 vs 0,3745 declarado; `domains_where_default_beats_fitted = []`. Ajuste da escada (B5): κ declarado 0,3792/0,3998 → ajustado 0,4677/0,4789. O empate histórico da Rodada 3 (worst-gap 0,2156 vs modelo 0,2156) permanece registrado sem edição: foi o gold adjudicado por caso (não o modelo) que produziu a ilusão de desempenho.

---

### 8.11 Quanto do κ é o modelo e quanto é o rubric (B26)

`_analysis/analysis/b26_rubric_sensitivity.py` → `Evaluacoes/r5/B26_rubric_sensitivity.json`
(runtime **1.042,4 s**, **220.400 pares**, IC95 por bootstrap pareado de 200 remuestreamentos
de 30.000 pares). Cada variante perturba uma prior do rubric **e recomputa o veredito do
modelo quando a perturbation toca o modelo**:

| Variante | κ modelo↔consenso | Δκ | unanimidade do painel |
|---|---|---|---|
| V0 rubric canônico | **0,5336** [0,5212; 0,5496] | — | 0,5090 |
| V1 pisos de dever ×1,10 | 0,5507 [0,5370; 0,5663] | +0,0171 | 0,5349 |
| V2 pisos de dever ×0,90 | 0,5250 [0,5135; 0,5395] | −0,0086 | 0,4924 |
| V3 deveres categóricos = 3 (M1, M2, M7) | 0,5085 [0,4960; 0,5222] | −0,0251 | 0,4647 |
| V4 todos os deveres categóricos | 0,5461 [0,5336; 0,5606] | +0,0125 | 0,5299 |
| V5 consenso = lente A isolada | 0,5223 [0,5106; 0,5371] | −0,0113 | 0,5090 |
| V6 consenso = lente B isolada | **0,3324** [0,3230; 0,3425] | −0,2012 | 0,5090 |
| V7 consenso = lente C isolada | 0,5147 [0,5028; 0,5283] | −0,0189 | 0,5090 |
| V8 gate de cobertura 0,70 → 0,80 | **0,6005** [0,5885; 0,6102] | +0,0669 | 0,5345 |
| V9 gate de cobertura 0,70 → 0,60 | 0,4907 [0,4787; 0,5051] | −0,0429 | 0,4949 |
| V10 gap mode `assume_breach` | **0,2974** [0,2819; 0,3123] | −0,2362 | 0,4682 |

Três leituras, todas incômodas e todas necessárias:

1. **κ não é uma propriedade do modelo.** Varía de **0,2974 a 0,6005** conforme as priors
   normativas escritas no rubric. A maior sensibilidade não vem dos pisos de dever (±10%
   → ±0,017/−0,009) nem do conjunto de deveres categóricos (−0,025/+0,013), e sim de
   **como se trata o que não foi declarado** (`assume_breach`: −0,2362) e de **onde se
   coloca o gate de cobertura** (±0,07/−0,04).
2. **G7′ não é um gate alcançável por ajuste.** A variante V8 (gate 0,80) ultrapassa 0,60
   — mas o mecanismo é trivial: mais casos abstêm no modelo **e** no rubric, e concordar
   em abstener é fácil. κ sobe porque aumenta a massa de casos em que ambos se recusam a
   juzgar, não porque o modelo juzgue melhor. Reportamos o número e **rejeitamos** usá-lo
   como prova.
3. **A lente B (prudencial) é a que mais diverge do modelo**: κ modelo↔lente B isolada
   0,3324, frente a 0,5223 (A) e 0,5147 (C). O modelo está construído sobre deveres e
   limites, não sobre cálculo de consequências — e isso se ve na medida, não na defensa.

## 9. Limitações

1. **Validação humana inexistente e κ sensíbel à rubrica.** Ground truth = três lentes
    implementadas como tabelas de regras. D4.5: sem raters. O pacote de adjudicação está
    pronto e não preenchido (360 células). B26 quantifica o problema: κ oscila entre
    **0,2974** e **0,6005** conforme as priors do rubric (pisos, deveres categóricos,
    gate de cobertura, modo de gap). Nada no corpus permite detectar se a rubrica está
    mal formulada; só permite saber o quão dependente do modelo é de ela. Ground truth = três lentes implementadas como tabelas de regras. D4.5: sem raters. O pacote de adjudicação está pronto e não preenchido (360 células). Nada no corpus permite detectar se a rubrica está mal formulada.
2. **Pluralismo normativo não resolvido.** κ inter-painel 0,3533–0,6447. O modelo concorda 0,8167 onde o painel é unânime (112.179 pares) e 0,0526 onde não é. Não reclamamos resolver o conflito.
3. **Granularidade observacional.** E30 ancora apenas fatos declarados; criticidade derivada por regra e analogia, sem painel de especialistas; 23 pares de facetas ainda têm β a distância < 0,12 (1 exatamente idêntico: C3 ≡ C7).
4. **Mecanismos inertes mantidos no grafo.** K9 (sunset) contribui dentro do ruído (Δ +0,0011 ablação; −0,0009 remoção no experimento de guardas); λ(E) e ζ existem mas estão desativados. Declará-los inertes é mais honesto que removê-los sem re-executar todas as baterias.
5. **Variantes estruturais inertes.** `prohibit_needs_material = 1` produz 0 flips; "banda de stakes" produz 65 flips em 183.920 confrontações (B5).
6. **Guardas não otimizadas.** Estendê-las a todo o pilar K derruba κ em 0,3447; as 12 guardas vigentes são decisão normativa. B21 mede agora o efeito do conjunto (−0,3234) e de cada guarda isolada (≤ 0,0042).
7. **Termos estruturais explicam pouco** (≤ 0,0007 em κ; Sobol B23: ζ 0,013, γ 0,123). Mantê-los é escolha arquitetônica, não necessidade demonstrada.
8. **Sensibilidade com painel pequeno.** 12 casos, indices saturados, sem scipy (Sobol por LHS pareado validado contra função linear exata, erro máximo 0,0334).
9. **Sensibilidade de risco estrutural.** B14: 98,07% da variância de R_r vem do caso, 0,80% do perfil. As personas variam em veredito (15,5% dos casos), não em magnitude de risco.
10. **Casos sintéticos.** Não há base real; casos paramétricos/narrativos gerados.
11. **Comparação intra-família apenas.** Aa é adequação relativa ao vetor de requisitos do caso; comparar Aa entre famílias distintas não é legítimo (SPEC §9.5).
12. **Supervisão como variável instrumental.** O regime é derivado de fatos declarados; se o corpus declara um canal de revisão que não existe na organização, o modelo confiará na declaração. E30 caps o nível da faceta, não verifica o fato.
13. **Rastreabilidade numérica automática, mas dependente do autor.** O verificador
    `paper_artifact_consistency_v13.py` re-deriva **166 afirmações** do paper a partir dos
    artefatos (127 por patrón explícito, 39 por valor anclado no contexto) e não reporta
    falhas. A lista de afirmações verificadas é escrita pelo autor: o verificador prova que
    cada número existe no artefato e aparece no texto, não que a lista esteja completa.

---

## 10. Reproducibilidade

`_analysis/run_all_batteries.py` é o ponto de entrada; r2/r3/r4 são congelados (`FROZEN = {"r2","r3"}`, e os artefatos de r4 foram preservados por git — D5.10). Convenção de calibração: *o corpus e o gold usam o ladder congelado de r3; as baterias de ajuste usam `ladder_calibration_v12.json` e reportam resultados separadamente*.

Artefatos da rodada (todos em `Evaluacoes/r5/`): `corpus_v7_*` (5 arquivos + coverage + audit sample), `B20_variant_eval.json`, `B20_variant_eval_full.json`, `B20_variant_eval_full_corpus.json`, `B20_canonical_beta_check.json`, `B20_crit_mild_cap3.json`, `B20_crit_targeted_TB_TS_IM.json`, `B20_crit_mild_cap3_full_corpus.json`, `B20_crit_targeted_full_corpus.json`, `B21_ablation.json`, `B22_fact_contradiction.json`, `B23_sobol_v13.json`, `B8_probes_reverified_v13.json`, `mirror_full_corpus_v13.json`, `ontology_v4_2_validation.json`, `kappa_by_stratum_v13.json`, `adjudication_packet_blind.csv`, `adjudication_packet_key.csv`, `adjudication_sample_power.json`, `B26_rubric_sensitivity.json`, `manifest_r5.json` (47 artefactos, 21 execuções com duración, 65,37 MB, SHA-256 de cada arquivo e rev de git), `paper_consistency_check_v13.json` (verificador paper ↔ artefatos). Núcleo: `core.py`, `geometry.py`, `facet_registry.py`, `fact_grounding.py`, 3 arquivos de teste (69 testes). Ontologia: 7 módulos + 2 shapes + 2 fixtures + instances (1.919.283 triplos) + `generation_report.json`. Python 3.14.4, numpy 2.5.4, rdflib + pyshacl, pytest; sem scipy.

---

## 11. Trabalho futuro

1. **Adjudicar o pacote cego** (120 casos × 3 raters = 360 células) — transforma a limitação 1 em um segundo estrato de validação. Poder estatístico já calculado: n = 25 para IC ≤ 0,05 em κ ≈ 0,60.
2. **B24 (âncora LLM local)** — a execução anterior deu `json_validity_rate = 0,0`; o parser e o prompt precisam ser refeitos e re-executados quando a máquina estiver livre (não usado como evidência em nenhuma seção).
3. **Corpus v8 com supervision regimes externos** (auditoria independente por caso, não declarada pelo agente).
4. **Sobol de ordem total com scipy** e painel maior (≥ 50 casos) para não saturar ST.
5. **Decidir K9** com re-execução completa.
6. **Renderizar as equações v13** (31 MathML de v12 + novas E11c′, E32, E4′) a partir de `_analysis/paper/equations.py`.

---

## Apêndice A. Parâmetros: declarados, congelados e ajustados

| Parâmetro | Declarado (`default_calibration`) | Congelado r3 | Ajustado r4 | v13 |
|---|---|---|---|---|
| `bar_base` | 0,50 | 0,55 | 0,38 | 0,55 (corpus) / 0,38 (baterias) |
| `bar_severity` | 0,20 | 0,10 | 0,24 | — |
| `bar_irreversibility` | 0,05 | 0,05 | 0,14 | — |
| `bar_prudential` | 0,02 | 0,02 | 0,08 | — |
| `bar_horizon` | 0,03 | — | 0,00 | — |
| `prohibit_margin` | 0,20 | 0,25 | 0,27 | — |
| `guards_margin` | 0,15 | 0,05 | 0,00 | — |
| `stakes_veto_min` | 0,55 | 0,70 | 0,70 | — |
| `hard_veto_delta` | 0,15 | 0,25 | 0,25 | — |
| `material_gap` | 0,25 | 0,25 | 0,25 | — |
| `critical_prohibit_gap` | 0,45 | 0,35 | 0,3771 | — |
| `cap_base` / `cap_stakes_gain` | 0,50 / 0,50 | 0,40 / 0,40 | 0,40 / 0,40 | — |
| `prohibit_stakes_min` | 0,60 | 0,30 | 0,0902 | — |
| `veto_slack` | 0,10 | 0,10 | 0,02 | — |
| `ratio_prohibit/review/guards` | 0,65/0,40/0,20 | 0,70/0,45/0,25 | 0,74/0,52/0,41 | — |
| `hysteresis` | 0,05 | 0,05 | 0,05 | — |
| `abstain_uncertainty/knowledge_floor` | 0,60/0,65 | 0,60/0,65 | 0,60/0,65 | — |
| **`coverage_gate`** | **0,70 (novo, declarado)** | — | — | 0,70 |
| **`oversight_attenuation`** | **0,45 (novo)** | — | — | 0,45 |
| **`req_missing_oversight`** | **0,08 (novo)** | — | — | 0,08 |
| **`review_need_weights`** | **(0,30;0,25;0,20;0,25) (novo)** | — | — | — |
| λ, α, β_face, γ, η, ω, ρ, δ, μ, θ | (0,30;0,25;0,25;0,20); α = marginal(β) = 1/6×6; 1/4×4; 0,12/0,05/0,03/0,10/0,05; (0,15;0,40;0,20;0,25); (0,65;0,60;0,60;0,65) | não ajustados (D4.22) | não ajustados | idem |
| **ζ (Ψ)** | **0,0** | — | — | 0,0 (rejeitado: Δκ negativo) |
| **s (λ(E))** | **0,0** | — | — | 0,0 (rejeitado: Δκ ≈ 0) |

---

## Apêndice B. Trazabilidade (números v13)

| Número | Artefato | Campo |
|---|---|---|
| 220.400 pares; 1.520 casos; 144 personas + 1 autodeclarado | `Evaluacoes/r5/corpus_v7_coverage.json` | `pairs_adjudicated`, `cases.total`, `personas.instances` |
| 6 tipos de declaração parcial (24 instâncias), deveres declarados 9–33 | idem | `personas.partial_declaration_*`, `declared_facets_range` |
| Aa média 0,3551; mediana 0,3462; max 0,9508; ≥0,999: 0,0% | idem | `adequacy` |
| Vereditos 152.439 / 32.996 / 34.615 / 349 / 1 | idem | `decision_distribution` |
| ABSTAIN 34.615 = 16.375 E29 + 18.240 E26′ | idem | `abstain` |
| κ global 0,5336; concordância exata 0,7886; within-one-step 0,9809 | idem | `kappa_model_vs_gold`, `model_vs_gold` |
| κ por cobertura 0,3832 / 0,3293 / 1,0000 | idem | `kappa_by_coverage` |
| Gap de verificação: 36.480 pares; κ defer 0,8085 vs assume-breach 0,0801 | idem | `verification_gap_D5_8` |
| Regimes de supervisão 67.715 / 91.640 / 61.045 | idem | `oversight_regimes` |
| Unanimidade 0,509; painel κ AB 0,3533, AC 0,6447, BC 0,3153 | idem | `gold` |
| 34 regras, todas ≥ 50 casos | idem | `gold.rules_total`, `gold.rules_firing_ge_50_pairs` |
| Veto 90,6%; hard veto 13,45% | idem | `veto_rate`, `hard_veto_rate` |
| Δκ supervisão +0,0078 [0,0057; 0,0100] (130.680 pares) | `B20_variant_eval_full_corpus.json` | `results[oversight].kappa_vs_panel`, `.ci95` |
| Δκ β +0,0019 [0,0009; 0,0032]; β+sup +0,0094 [0,0069; 0,0120] | idem | `results[beta_diff*]` |
| λ(E): −0,0001/−0,0002/−0,0003; ζ: −0,0028/−0,0059 | idem | `results[salience_*.delta_vs_baseline]`, `results[zeta_*.delta_vs_baseline]` |
| κ estratos 0,8167 / 0,1371 / 0,0526 (112.179 / 95.611 / 12.610 pares) | `Evaluacoes/r5/kappa_by_stratum_v13.json` | `by_stratum` |
| Ablação: guardas fora κ 0,1399 (Δ −0,3234 [−0,3306;−0,3147]); primary-pillar 0,2691 (Δ −0,1942) | `B21_ablation.json` | `results[no_guards]`, `results[beta_primary]` |
| Guardas individuais |Δκ| ≤ 0,0042 | idem | `results[guard_minus_*]` |
| B22: 98,27%; 224.097 caps; excess 0,3611; 18.898 flips (43,74%); κ 0,5526 vs 0,2463 | `B22_fact_contradiction.json` | todos os campos nomeados |
| B23: S₁ coverage_gate 0,749; Morris μ* s = 0,0004; S₁ oversight_attenuation em hard_veto 0,701 | `B23_sobol_v13.json` | `sobol[...]`, `morris[...]`, `interpretation` |
| Espelho: 220.400, diff 0,0, 0 divergências, 121,87 s | `mirror_full_corpus_v13.json` | `confrontations`, `global_max_abs_difference`, `runtime_seconds` |
| B8: 2.064 probes, 7.815 asserções, 1,000 | `B8_probes_reverified_v13.json` | `summary` |
| B26: κ 0,5336 → 0,2974–0,6005 conforme priors (11 variantes, 220.400 pares) | `B26_rubric_sensitivity.json` | `variants[].kappa` |
| 69 testes de invariante, 45,75 s | `_analysis/formal_core/tests/` | saída do pytest (GATE_REPORT_r5.md) |
| β: 1 uni, 10 bi, 22 tri, 0 quad; idênticos 8→1 | `_analysis/formal_core/facet_registry.py` | computado nesta rodada (Apêndice) |
| Ontologia: 1.919.283 triplos; 50.160 requisitos; 169.950 observações; 21.280 ancoragens; 16.475 falhas de guarda | `Ontologias/ontology_v4_2/generation_report.json` | `instances_triples`, `counts` |
| Ontologia revalidada: 42/42 verificações; SHACL v4 0 violações (54,04 s), v6 0 violações (27,91 s), módulos 0; 76/76 fixtures inválidos detectados e atribuídos; espelho 403 confrontações, diff 1,61e-12, 0 divergências de veredito; runtime 301,9 s; gate G4′ PASS | `Evaluacoes/r5/ontology_v4_2_validation.json` | `gate_verdict`, `shacl.instances_vs_v4_shapes`, `shacl.instances_vs_v6_shapes`, `invalid_fixtures`, `mirror`, `sparql_checks` |
| Pacote de adjudicação: 120 linhas, 360 células vazias, κ amostra 0,2067 SE 0,0482, n=25 | `adjudication_packet_blind.csv`, `adjudication_sample_power.json` | `n_pairs`, `kappa`, `se`, `n_for_half_width_0_05` |
