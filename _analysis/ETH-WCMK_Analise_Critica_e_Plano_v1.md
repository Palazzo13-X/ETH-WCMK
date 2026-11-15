# ETH-WCMK — Relatório de Leitura Crítica e Plano de Execução (v1.0)

**Autor:** análise técnica automatizada (leitura profunda de todos os artefatos do projeto)
**Data:** 27/10/2026
**Fontes lidas:**
- `ETH-WCMK v9.docx` (paper, 71.376 caracteres; 11 equações embutidas como imagens — transcritas abaixo)
- `Estrutura Matemático-Simbólica do Tetraedro Regular.pdf` (16 páginas, escaneado; páginas rasterizadas em `_analysis/pages/`)
- `Ontologias/WCMK_plus_catalogo_facetado_v1_clean.docx` (24 facetas, §1–§12)
- `Ontologias/Arquitetura_v1_ETH_WCMK_LLM.docx` (camada LLM, 4 fases)
- `Ontologias/eth_extracted/eth/*.ttl` (9 arquivos: core, analysis, facet-requirements + SHACL + exemplos)
- `Ontologias/wcmk_extracted/wcmk/*.ttl` (16 arquivos: perfil, facetas, bridge, assessment, scoring examples válidos/inválidos + SHACL)

**Convenção de severidade usada neste relatório:**
- **P0** — impede a validação formal ou gera resultado matematicamente incorreto; deve ser corrigido na v10 do paper.
- **P1** — fragilidade conceitual/operacional; corrige-se na v11 e na ontologia v2.
- **P2** — refinamento desejável, sem impacto sobre correção.

---

## 1. Síntese executiva

O projeto tem três ativos fortes e genuinamente originais:

1. **Separação de camada (case × agency).** ETHCASE descreve o caso; WCMK descreve a agência delegada; o *bridge* confronta os dois e produz adequação + risco residual + recomendação. Essa separação é a decisão teórica mais defendível do paper e deve ser preservada e blindada contra qualquer "score único".
2. **Déficits não compensatórios.** `d_i = max(0, r_i − a_i)` é a formalização correta da ideia de que "excesso de Want não compensa falta de Must". É o coração normativo do modelo.
3. **Risco residual visível.** `R_r` existe mesmo quando `Aa` é alto; a lógica de revisão (`needs-review`, `allow-with-guards`) é mais realista que um threshold binário de guardrails.

Contra isso, a leitura formal encontrou **quatro defeitos P0** e **oito P1**:

| # | Problema | Onde | Severidade |
|---|---|---|---|
| 1 | Eq.(1) e Eq.(5) são **incompatíveis**: Eq.(1) exige vértices unitários centrados (`Σv_i=0`, `‖v_i‖=1`, `v_i·v_j=−1/3`); Eq.(5) ancora W na origem, dá `‖W‖=0`, `W·C=0`, centroid ≠ 0. | §6.1, Eq.1–5 | **P0** |
| 2 | `d_Δ(a,b)=½‖a−b‖₁` **não é a métrica induzida** pelo tetraedro (que é euclidiana: `d_E = (2/√3)‖a−b‖₂` com vértices unitários). O paper usa linguagem geométrica ("distância", "tensão", "ângulo") com métricas distintas sem声明. | §6.1–6.2, Eq.3 | **P0** |
| 3 | **"Volume interno" nunca é definido.** Um tetraedro regular fixo tem volume constante; qualquer afirmação sobre "coherência como volume" fica vazia. Existe, porém, uma definição geométrica natural e útil: as coordenadas baricêntricas **são** frações de volume de sub-tetraedros (verificado numericamente, §3.5). | §6.1, figuras | **P0** |
| 4 | `R_r = R_c(1 − A_a)` **zera** o risco quando `A_a=1`, contradizendo a própria promessa de "attenuation without erasure". | §6.4, Eq.11 | **P0** |
| 5 | Dupla contagem do pilar Know: `D` já contém `λ_K·d_K` **e** `u = U_E(1−k)` penaliza de novo a mesma coordenada. | Eq.8–10 | **P1** |
| 6 | Deriva de notação: Eq.(4) define `T(E,a)`; Eq.(10) usa `T_int(a)`. Não se sabe se a tensão é do caso ou do perfil. | Eq.4 vs Eq.10 | **P1** |
| 7 | α_ij (pesos de tensão) e `R_c(E)` **não são definidos**; sem normalização, `Σ_{i<j}α_ij|…|` pode exceder 1 e quebrar o `clip` de `A_a`. Limite demonstrado: 6 (ver §3.4). | Eq.4, Eq.10, Eq.11 | **P1** |
| 8 | SHACL `sh:maxCount 1` em `projectsToCoreVertex` **proíbe** facetas compartilhadas entre pilares, exatamente o que a Tarefa 3 pede. | `wcmk-facets.shacl.ttl` | **P1** |
| 9 | Cobertura de domínios na ontologia (6 declarados) ≠ catálogo do paper (10 domínios). | `ethcase-facet-requirements.ttl` | **P1** |
| 10 | Nenhuma propriedade, classe ou shape em TTL/SHACL representa `r(E)`, `λ(E)`, `α_ij`, `γ`, `ρ`, `U_E`, `R_c`. A camada formal do paper é **prosa, não ontologia**. | bridge/ttl files | **P1** |
| 11 | Sobreposição de facetas: C2↔C6, C4↔C5, M1↔M3, K1↔K7, K3↔M1/M2, K6↔K4, W1↔W4 — risco de dupla penalização e de "inflação de facetas". | catálogo §5–§8 | **P1** |
| 12 | Metacognição está sub-representada: a definição de Know inclui "o que pode aprender", mas K6/K7 não capturam **aprendibilidade**. | catálogo §8 | **P1** |

**Recomendação central:** o núcleo geométrico deve ser **re-fundado como simplex 3-dimensional com métrica declarada** — o tetraedro regular é uma *representação*, não um objeto que gere informação. Quando se define volume com sentido (sub-tetraedros baricêntricos), a geometria passa a produzir uma medida de coherência **real e não compensatória** (`min_i a_i` ou a média geométrica `(∏a_i)^{1/4}`), que é exatamente a ética que o modelo quer. Isso transforma a "decoração geométrica" em um operador formal utilizável.

---

## 2. Avaliação crítica do modelo (Tarefa 1)

### 2.1 O que está bem construído

**(a) Quatro pilares são necessários e quase minimalistas.** Want/Can/Must/Know cobre (i) teleologia, (ii) capacidade situada, (iii) normatividade, (iv) epistêmica. Falta explícitamente um **quinto** candidato: *Contexto/Vulnerabilidade* (ou "Who"). Mas isso pertence ao caso (ETHCASE), não à agência — e o paper já trata vulnerabilidade como atributo do caso. Portanto, **mantém quatro vértices**; não expanda o tetraedro (ver §2.3.3).

**(b) A tensão entre compensatório e não compensatório está bem colocada.** O problema real do paper é que a agregação *dentro* de cada pilar é compensatória (média ponderada de facetas) e *entre* pilares é compensatória via `λ_i`. A correção é uma política **lexicográfica com floor de severidade** (see §3.6 e §4.5), já insinuada pelo catálogo via `ThresholdOverride`/`GuardedWeightedMean`, mas nunca formalizada.

**(c) A camada LLM é corretamente subordinada.** "Formal core sovereign, LLM advisory" é a arquitetura certa para um modelo de avaliação ética: LLMs estruturam, aterram normas, explicam; nunca computam `Aa` nem `R_r`. A arquitetura v1 já diz isso; a ontologia não enforceda (P1).

### 2.2 Pontos críticos conceituais

**C1 — "Adequacy" é unidimensional demais.** `Aa ∈ [0,1]` esconde o que importa para governança: *qual* pilar falhou, *com que severidade*, *sob qual norma*. O bridge já tem `ReviewRequirement` e `ExplanationBundle`, mas o score único tende a ser consumido como dashboard KPI — o oposto do desideratum de inspectabilidade. **Proposta:** publicar `Aa` sempre acompanhado do **vetor de déficits** `(d_W, d_C, d_M, d_K)` e do **pilar crítico** `argmax_i λ_i d_i`. Nenhum relatório, UI ou API deveria expor `Aa` isolado (recomendação de design + testable invariante, §6.4).

**C2 — "Want" como desejo formalizado do stakeholder é ambíguo.** Quem é o stakeholder? O deployer, o usuário, o afetado? Want do agente ≠ Want do stakeholder. Sem essa distinção, `r_W` pode ser capturado pelo interesse do operador. **Proposta:** separar em ETHCASE `Want_stakeholder` (desire formalizado) e `Want_agent` (objetivo delegado), com regra explícita de *legitimidade de Want* (o Want do agente deve derivar de Want do stakeholder legitimado). Isso vira uma faceta nova: **W6 — Legitimidade de intenção** (provenance do objetivo).

**C3 — "Must" mistura níveis de norma.** M1 (legal), M2 (institucional), M3 (princípios), M4 (prudência), M5 (papel), M6 (accountability) são de naturezas distintas: uma violação de M1 é juridicamente differente de uma de M4. Falta uma **hierarquia de precedência** e um tratamento de **conflito normativo** (lei vs. princípio vs. política). O catálogo menciona conflito em κ, mas não define *como* resolver. **Proposta:** modelo deôntico leve (obligation/prohibition/permission + prioridade + estado `CONFLICT`), com defeito de Must **max-imizado** sobre normas de maior rank, não média.

**C4 — Know sem componente de "capacidade de aprender".** O pilar foi definido como "o que sabe, o que não sabe, o que pode aprender". K1–K7 cobrem os dois primeiros; falta K8 (**Aprendibilidade / atualização epistêmica**), que é decisiva em agentes que operam em ambientes non-stationary.

**C5 — Residual risk precisa de um piso.** Ver §3.7.

**C6 — Falta uma dimensão temporal.** Cases têm urgência, reversibilidade e horizonte. A reversibilidade aparece como atributo do caso, mas nenhum operador temporal entra em `Aa` ou `R_r`. **Proposta mínima:** `R_r` multiplicado por um fator de irreversibilidade `τ(E) ∈ [1, 1.5]` e classes de prudência sensíveis a prazo.

### 2.3 Refinamentos propostos (modelo ETH-WCMK v2)

**v2.1 — Geometria como medida, não metáfora.**
Defina o simplex `Δ³ = {a ∈ ℝ⁴₊ : Σa_i = 1}`. Cada `a_i` **é** a fração de volume do sub-tetraedro formado pelo ponto `x(a)` e a face oposta ao vértice `i` (identidade baricêntrica, verificada em §3.5). Disso segue imediatamente:
- **Coherência volumétrica** `V(a) = 4·(∏_i a_i)^{1/4} ∈ [0,1]`, máxima (=1) no baricentro, **zero se qualquer pilar for zero**. Esta é uma medida *não compensatória* que nasce da geometria, não da retórica.
- **Coherência mínima** `B(a) = 4·min_i a_i` — o "pilar mais fraco" do perfil.
Esses dois operadores substituem a frase "volume interno representa a coherência", que hoje não tem definição.

**v2.2 — Déficits com floor de severidade.**
`d_i = max(0, r_i − a_i)` é correto. O problema é que `λ_i` arbitrário permite "comprar" um déficit grave com saliência baixa. Correção:
`λ_i ← max(λ_i, λ_min(dominio))` e, para pilares marcados *críticos* no domínio, uma **penalidade de floor**: `D = Σ λ_i d_i + Σ_{i∈Crit} φ_i·1[d_i > θ_i]`. Isso torna `ThresholdOverride` (que já existe no catálogo) um operador matemático, não uma nota editorial.

**v2.3 — Não adicionar um quinto vértice.** A tentação de criar "Who/Context" ou "Learn" como vértice quebraria a identidade do modelo e multiplicaria o custo de calibração. Pilares = eixos de *agência*; contexto = atributos do *caso*. Manter o tetraedro e mover contexto para ETHCASE (que já tem `Vulnerability`, `EvidenceItem`, `NormativeTension`).

**v2.4 — Perfis multi-escala.** O paper trata `a` como um vetor único. Agências reais têm **camadas**: modelo-base, sistema, deployer, workflow humano. O bridge deveria avaliar `a` por camada e reportar adequação como matriz (`Aa_layer`) + gargalo. A ontologia já tem `AgencyAssessment`; falta `layer`.

---

## 3. Revisão matemática (Tarefa 2)

### 3.1 Equações transcritas do paper (v9)

| Eq. | Formulação | Observação |
|---|---|---|
| (1) | `v_iᵀ v_j = −1/3 (i≠j)`, `Σ_i v_i = 0` | exige vértices unitários centrados |
| (2) | `r̂(E,d) = Ω_d r(E) / (1ᵀΩ_d r(E))`, `λ̂` análogo | calibração de domínio; Ω_d exemplar |
| (3) | `d_Δ(a,b) = ½‖a−b‖₁` | total variation; não é métrica do tetraedro |
| (4) | `T(E,a) = Σ_{i<j} α_ij(E) |(a_i−r̂_i) − (a_j−r̂_j)|` | α_ij não definido; escala não normalizada |
| (5) | `W=(0,0,0), C=(1,0,0), M=(½,√3/2,0), K=(½,√3/6,√(2/3))` | aresta 1; **não** satisfaz Eq.(1) |
| (6) | `a=(w,c,m,k)`, `a_i ≥ 0`, `Σa_i = 1` | simplex admissível — correto |
| (7) | `x(a) = wW + cC + mM + kK` | coordenadas baricêntricas — correto |
| (8) | `d_i = max(0, r_i − a_i)`, `D = Σ_{i∈{W,C,M,K}} λ_i d_i` | deficits corretos; agregação linear frágil |
| (9) | `u(E,a) = U_E(1−k)` | duplo counting de K; "k" colide com κ do catálogo |
| (10) | `Aa = clip(1 − D − γT_int − ρu)` | unidades misturadas; γ,ρ não calibrados |
| (11) | `R_r = R_c(1 − Aa)` | anula o risco quando Aa=1 |

### 3.2 Verificação numérica dos defeitos (executada)

```text
Eq.(5) raw:            ‖W‖=0, centroid=(0.5, 0.2887, 0.2041), W·C=0
Eq.(5) centrada:       ‖v_i‖=0.6124 = √(3/8); v_i·v_j = −0.125; ângulo = 109.47° ✓
                       (Eq.(1) só vale se normalizada por √(3/8): v_i/‖v_i‖)
d_Δ(a,r) com δ=(0.3,0.1,-0.1,-0.3):  TV = 0.400   Euclidean(unit-vertices) = 0.316
max Σ_{i<j}|s_i−s_j| sob Σs=0, a,r∈Δ³ = 6.000  → com α_ij=1/6, T ∈ [0,1] ✓
sub-volumes baricêntricos: para a=(0.2,0.3,0.25,0.25) → (0.20,0.30,0.25,0.25) · V_total  ✓
min_i a_i = 0.20 ; (∏a_i)^{1/4} = 0.2475  (máx. 0.25 no baricentro) ✓
```

**Conclusões:**
1. Eq.(1) e Eq.(5) são a **mesma** geometria em escalas diferentes: a versão centrada de Eq.(5) tem circumraio `√(3/8)` e `v_i·v_j = −1/8`. Para satisfazer Eq.(1) é preciso declarar explicitamente `v_i = P_i − g` com `g = (1/4)ΣP_i` **e** normalizar. Como está, o leitor que aplica Eq.(1) com os números de Eq.(5) obtém dot-products errados e, por consequência, qualquer "ângulo entre pilares" sai inconsistente.
2. `d_Δ` é uma boa métrica **no simplex** (interpretação: massa de agência redistribuída entre pilares; range [0,1]). Mas o tetraedro induz `d_E = (√2/√3)·‖δ‖₂`. O paper oscila entre as duas. **Fix:** declarar que toda distância do modelo é `d_Δ` (no simplex) e que o embedding geométrico serve **só** para visualização; ou definir uma métrica única `d(a,b) = ‖x(a) − x(b)‖ / (2/√3)`, que coincide com uma norma L₂ no simplex.
3. Volume: com W na origem, o tetraedro `(W, ρ_C C, ρ_M M, ρ_K K)` tem volume `ρ_Cρ_Mρ_K·V₀` — **cego a Want**. Este é o contra-exemplo mais forte contra o uso de "volume" como coherência. A alternativa baricêntrica (sub-tetraedros) é correta e não é cega a nenhum pilar.

### 3.3 Núcleo formal corrigido (proposta para v10)

Definições canônicas, todas compatíveis entre si:

- **Simplex:** `Δ³ = {a ∈ ℝ⁴₊ : Σ a_i = 1}`; pilares indexados `i ∈ {W,C,M,K}`.
- **Embedding unitário centrado:** `v_i = √(8/3)(P_i − g)` com `P_i` de Eq.(5), `g=(1/4)ΣP_i`. Então `‖v_i‖=1`, `v_i·v_j=−1/3`, `Σv_i=0` — Eq.(1) fica verdadeira **com prova**, e `‖v_i−v_j‖ = 2/√3`.
- **Ponto do perfil:** `x(a) = Σ a_i v_i`. Então `‖x(a)‖² = Σa_i² − (1/3)Σ_{i<j}a_i a_j` = … e `d_E(x(a),x(b)) = (2/√3)‖a−b‖₂`.
- **Distância de perfil (métrica oficial):** `d_Δ(a,b) = ½‖a−b‖₁` (range [0,1], igualdade só em vértices opostos).
- **Déficits:** `d_i = max(0, r_i − a_i)`; **déficit crítico** `δ_i = 1[d_i > θ_i]`; agregação `D = Σλ_i d_i + Σ_{i∈Crit} φ_i δ_i`.
- **Tensão de perfil (definição correta):** definir o *slack* `s_i = a_i − r_i` (Σs_i=0). Penalizar só dispersão de **déficits**: `T(a,r) = Σ_{i<j} α_ij |(s_i)⁻ − (s_j)⁻|`, com `(s)⁻ = min(s,0)`, `α_ij = β_iβ_j/(Σβ)²` ou `α_ij = 1/6` ⇒ `T ∈ [0,1]` (limite 6 com α=1). Isso elimina o problema ético de penalizar *excesso* de capacidade: hoje, um perfil que sobrepõe Want e apenas cumpre Can é punido por "tensão".
- **Penalidade epistêmica:** `u = U_E · d_K/r̂_K` (ou `U_E·max(0, r̂_K − k)`), **não** `U_E(1−k)`; e retirar `u` de `D` ou vice-versa (uma contagem).
- **Adequação:** `Aa = [1 − D − γT − ρu]⁺` com `γ+ρ ≤` … declarado e calibrado; provar `Aa ∈ [0,1]`.
- **Risco residual (piso):** `R_r = R_c·[(1−η Aa) + (1−η)]`? Forma mais limpa: `R_r = R_c(1 − η Aa)` com `η < 1` declarado, ou `R_r = max(R_c(1−Aa), R_floor(E))` onde `R_floor = σ(E)·R_c`, σ = fraça prudencial (ex. 0.1). Isso **materializa** "attenuation without erasure" — hoje a fórmula faz exatamente o oposto.
- **Coherência volumétrica:** `V(a) = 4(∏a_i)^{1/4}`; `B(a)=4 min_i a_i`. Entra como `κ(c,a)` ou como componente da adequação de perfil.

### 3.4 Invariantes que o modelo deveria satisfazer (e que viram testes)

1. **Monotonicidade:** `Aa` não aumenta quando algum `a_i` diminui. *(Hoje: não garantido por `T_int`.)*
2. **Non-compensação:** aumentar `a_j` além de `r_j` não reduz `D`. *(Hoje: garantido em D, quebrado em T_int.)*
3. **Boundedness:** `D,T,u ∈ [0,1]` ⇒ `Aa ∈ [0,1]` sem clip. *(Hoje: não provado.)*
4. **Piso de risco:** `Aa = 1 ⇒ R_r > 0` se `R_c > 0`. *(Hoje: violado.)*
5. **Simetría de domínio:** calibração Ω_d não altera ordem relativa de perfis dentro do mesmo caso. *(Testável.)*
6. **Degenerescência de volume:** se qualquer pilar é 0, coherência volumétrica é 0. *(Hoje: indefinido.)*

Implementar essas seis invariantes como **propriedades testáveis** (pytest) é o produto da Tarefa 6, battery B1.

### 3.5 Resultados numéricos da execução do núcleo formal (já rodado)

Refere-se a `_analysis/formal_core.py`, implementação de referência do núcleo corrigido (stdlib + numpy, sem dependências externas). Todos os números abaixo saíram da execução real do script.

**(a) Geometria — Eq.(1) vs Eq.(5).** A versão centrada e unitária do embedding satisfaz Eq.(1) exatamente (`‖v_i‖ = 1`, `v_i·v_j = −1/3`, `Σv_i = 0`), mas aí a aresta é `√(8/3) ≈ 1.6330`, **não** 1. Com as coordenadas literalmente escritas em Eq.(5) (W na origem, aresta 1), os produtos escalares brutos são `−1/8`. Ou seja: **Eq.(1) e Eq.(5) do paper não são simultaneamente verdadeiras como estão.** Escolha necessária e explícita: (i) manter aresta 1 e escrever `v_i·v_j = −1/8` (ou declarar os vértices como `P_i − g`), ou (ii) normalizar e declarar `‖v_i‖ = 1`. Recomendo (ii), porque torna Eq.(1) um teorema provável e não uma asserção.

**(b) Métrica.** Para `a=(.4,.3,.2,.1)` e `b=(.1,.2,.3,.4)`: `d_Δ = ½‖a−b‖₁ = 0.400`, enquanto a distância euclidiana induzida pelo embedding é `0.5164` (razão 0.7746). Conclusão: Eq.(3) **não** é a métrica induzida por Eq.(5)+Eq.(7) — é uma métrica distinta (`ℓ¹/2`) sobre o simplex. Não é um erro, mas hoje o texto mistura as duas. Decisão de redesign: declarar `d_Δ` como métrica oficial de perfis e usar o embedding apenas como representação visual/projeção; jamais aplicar `‖x(a)−x(b)‖` como "distância entre perfis".

**(c) Legitimidade da narrativa de volume (verificado).** As quatro sub-tetrahedra formadas por `x(a)` e as faces do tetraedro têm frações de volume **exatamente** `a_W, a_C, a_M, a_K` (`0.20, 0.30, 0.25, 0.25` para `a=(.2,.3,.25,.25)`). Esta é uma propriedade matemática real e forte: é a justificativa formal para dizer que "o perfil ocupa o tetraedro segundo os quatro pilares". Vale promover isso a **Proposição 1** do paper v10 — hoje a ideia está asserted, não provada.

**(d) Coerência volumétrica.** `V(a)=4(∏a_i)^{1/4}`: 1.0 no baricentro, 0 se algum pilar é zero. Para `a=(.40,.30,.20,.10)`, `V = 0.8853` — mas `B(a)=4·min_i a_i = 0.40`. A média geométrica **mascara** um pilar fraco: o perfil está a 88% de "coerência" embora o pilar K tenha apenas 10% de massa. Recomendação: usar `B(a)` (pilar mais fraco) como medida de criticidade/fragilidade e `V(a)` apenas como medida suave de balanceamento; a desigualdade verificada é `V(a) ≤ 4·m^{1/4}·((1−m)/3)^{3/4}`, com `m = min_i a_i` (0 violações em 20.000 amostras).

**(e) Limites de `T`.** Maximizando `Σ_{i<j}|s_i−s_j|` sob `Σs_i = 0` dentro do simplex, o supremo é **6**. Logo `α_ij = 1/6` dá `T ∈ [0,1]` garantido — e os testes confirmam 0 violações de limite em 20.000 amostras. Sem esse fator, como está no v9, `T` pode exceder 1 e "quebrar" o clipping de `Aa`.

**(f) Ablação v9 → v2 (mesmos casos, fórmulas diferentes).**

| Cenário | Aa (v9) | Aa (v2) | R_r (v9) | R_r (v2) | Decisão (v2) |
|---|---|---|---|---|---|
| Triagem clínica, perfil action-oriented (0.40,0.30,0.15,0.15) | 0.860 | 0.923 | 0.112 | 0.135 | allow |
| Triagem clínica, perfil epistemic reviewer (0.15,0.20,0.25,0.40) | 0.888 | 0.950 | 0.089 | 0.116 | allow |
| Assistente criativo, perfil balanceado | 0.964 | 0.985 | 0.009 | 0.028 | allow |
| Caso crítico, agente com **Know = 0** | 0.863 | **0.644** | 0.123 | **0.378** | allow-with-guards |
| Déficit grave de Must mascarado por `λ_M = 0.05` | 0.904 | **0.727** | 0.082 | **0.294** | allow-with-guards |
| Perfil de ajuste perfeito em domínio crítico | 0.994 | 1.000 | 0.004 | **0.070** | allow |

Interpretação: os dois casos em negrito são exatamente as duas falhas que apontei. (i) Um agente **sem conhecimento** num caso crítico recebe 0.86 no v9 — praticamente "allow" — porque o déficit de Know entra com peso `λ_K` pequeno e a penalidade epistêmica `U_E(1−k)` já está, em parte, duplamente contada; na forma corrigida cai para 0.644 e o risco residual triplica. (ii) Quando a saliência de Must é baixa, um déficit severo de obrigação fica **barato** no score agregado: o piso crítico `φ_i·1[d_i>θ_i]` corrige isso. (iii) "Attenuation without erasure" só existe de facto na versão com piso `σ(E)·R_c`: com `Aa = 1`, o risco residual passa de 0.004 para 0.070.

**(g) Punição de excesso (problema ético concreto).** Caso em que todas as exigências estão satisfeitas (`r = (0.25,0.25,0.25,0.25)`, `U_E = 0`): perfil balanceado `Aa = 1.0`; perfil `(.30,.30,.30,.10)` — ainda sem nenhum déficit — recebe **0.9425** no v9. Ou seja, o modelo pune *distribuir* capacidade excedente, o que é indefensável. Na forma corrigida o valor sobe para 0.9619, mas ainda não é 1.

**(h) Resultado das invariantes (20.000 perfis × casos aleatórios, semente fixada).**

| Invariante | Violações |
|---|---|
| `Aa ∈ [0,1]` | 0 |
| Piso de risco (`Aa=1 ⇒ R_r>0`) | 0 |
| Não-compensação (`d_i` independente de `a_j`) | 0 |
| Degenerescência de volume (limites de `V`) | 0 |
| `T ∈ [0,1]` com `α=1/6` | 0 |
| **Monotonicidade de `Aa`** | **23 (0,11% dos pares testados), magnitude máxima 3.9×10⁻⁴** |

E o achado importante: **reduzindo `T` a um diagnóstico puramente reportado (fora do score escalar), as violações de monotonicidade caem a zero** (50.000 casos testados, 0 violações). Ou seja, nenhum termo de dispersão consegue ser simultaneamente (i) parte da nota e (ii) monotônico — a dispersão pode diminuir quando um déficit aumenta (concentrar o déficit em um pilar reduz a dispersão). Recomendação formal para v10: `Aa = [1 − D − ρu]⁺`, com `T` publicado **como dimensão interpretativa do vetor de déficits** (não como componente da nota), e a porta de revisão (`d_i > θ_i` em pilar crítico) como guarda real contra patologias de dispersão. Isso mantém o tetraedro como objeto explicativo sem contaminar o escalar.

### 3.6 O substrato matemático do PDF "Estrutura Matemático-Simbólica do Tetraedro Regular" (verificado)

Este documento não é redundante com o paper: ele é a **camada de álgebra de relações** que o paper ainda não usa. Sua estrutura é: vértice `i` = conceito `C_i` munido de um vetor de "força" `F_i = α_i·u_i` (intensidade + direção); **arestas** = relações binárias `R_ij`; **faces** = relações ternárias `T_ijk`; **interior** = relação quaternária. Combinatoriamente isso fecha exatamente com os quatro pilares:

| Elemento do tetraedro | Cardinalidade | Correspondência em ETH-WCMK |
|---|---|---|
| Vértices | 4 | pilares W, C, M, K |
| Arestas | 6 | tensões pairwise `α_ij` — os 6 pares que Eq.(4) indexa |
| Faces | 4 | sub-combinaciones ternárias (WCM, WCK, WMK, CMK) |
| Interior | 1 | relação quaternária = adequação integral |

Sugestão de redesign: os 26 facetas devem ser **classificados por dimensão de relação** (vértice, aresta, face, volume), e a agregação `κ(c,a)` deve usar precisamente essa hierarquia — interações de aresta (6), de face (4) e de volume (1). Isso dá uma justificação matemática para "compartilhamento entre pilares com pesos distintos", que hoje é apenas uma convenção de catálogo.

**Erros matemáticos encontrados no PDF** (todos confirmados numericamente por `_analysis/tetra_geometry.py`):

1. **Centro errado.** O PDF declara `C = (1/2, √3/4, √6/4) ≈ (0.5, 0.433, 0.612)`. O centro real do tetraedro com esses vértices é `C = (1/2, √3/6, √6/12) ≈ (0.5, 0.2887, 0.2041)`. Confirmação: com o valor impresso, `|C−v1| ≈ 0.901` e `|C−v3| = 0.75` — não é equidistante, logo não pode ser centro. A origem do erro é clara: `√6/4` é o **circunraio** `R` e `√6/12` é o **inraio**; foram transpostados como coordenadas.
2. **Inconsistência de convenção entre PDF e paper.** No PDF (e em Eq.(5)) um vértice está na origem e os outros três a distância 1: os produtos escalares entre eles são **+1/2** (ângulo 60°). O paper, Eq.(1), afirma `v_iᵀ v_j = −1/3` — que só é verdadeiro para vetores **centrados e unitários**. As duas afirmações não coexistem: com vértices centrados, `v_i·v_j = −1/8`; normalizando, `−1/3` mas a aresta passa de 1 a `√(8/3) ≈ 1.633`. É preciso escolher **uma** convenção e reescalar todas as fórmulas dependentes (distâncias, volumes, "ângulo entre pilares").
3. **Ângulo diedro vs ângulo entre vértices.** `∠(v_i − g, v_j − g) = 109.4712°` (entre raio-vértice), mas o diedro entre faces é `arccos(1/3) = 70.5288°`. Se qualquer texto do modelo fala "ângulo entre pilares = 109.47°", está correto; se fala "ângulo entre faces", está trocado.
4. **Operadores mal tipados.** `R^vec_ij = F_i ∘ F_j` com `∘ ∈ {·, ×, +, −}`: ora produz escalar, ora vetor, sem restrição, sem normalização e sem definição de `β_j` em `R^trans_ij = α_j F_i + β_j F_j`. Para uso formal (e para SHACL/OWL) isso é fatal: cada operador precisa de tipo e domínio/codominio declarados.
5. **Matriz de relações 4×4 contradiz a definição.** As relações são definidas apenas sobre as 6 arestas, mas a matriz tem 16 entradas, incluindo `R_ii` (auto-relações sem significado) e duplicação `R_ij`/`R_ji` sem condição de simetria. Fix sugerido: matriz simétrica sem diagonal, ou `R_ii := ‖F_i‖² = α_i²` declarado explicitamente.
6. **`F_i = α_i u_i` sem `‖u_i‖ = 1`.** Sem normalização, `α_i` não é a magnitude.

**Valores corretos de referência** (aresta 1, convenção do PDF): circunraio `√6/4 = 0.6124`; inraio `√6/12 = 0.2041`; volume `√2/12 = 0.11785` ✔ (o PDF acerta aqui); área superficial `√3 = 1.7320`; diedro `70.5288°`; ângulo vértice–centro–vértice `109.4712°`.

**Oportunidade:** o PDF introduz um funcional `E[Ψ] = Σ_{i=1}^{4} E_V(F_i) + …` sob um "Princípio de Mínima Ação" e invariantes tensoriais `I₁ = tr(F Fᵀ)`, `I₂ = det(F)`. `I₁ = Σ α_i²` é exatamente uma medida de "massa de agência distribuída" e `I₂` é proportional ao volume — ou seja, o PDF já contém, quase pronto, o análogo matemático da **coerência volumétrica** `V(a)` que o paper precisa e não tem formalizada. Resta ligar `F_i = a_i v_i` (perfil baricêntrico) a esses invariantes; nota importante: com `W` na origem, `det(F_2,F_3,F_4) = α_2α_3α_4·(6V) = α_2α_3α_4·√2/2`, que é **cego a Want** — outra razão para adotar a convenção centrada.

*(Pendência: as páginas 9–16, que tratam de invariantes, energia e extensões, estão em transcrição e serão incorporadas aqui.)*

**Páginas 9–16 — o que o PDF acrescenta e onde falha**

- **§5 "Espaço Interior e Resultante Integrada"**: define o interior por coordenadas baricêntricas `V = {p = Σα_i v_i, α_i ≥ 0, Σα_i = 1}` ✔ (esta é exatamente a condição de admissibilidade Eq.(6) do paper, agora com prova geométrica). Introduz um campo `Φ(p)` e operadores de integração: resultante linear `Φ^comb = Σ α_i F_i`; "campo vetorial" `Φ^campo = Σ F_i/‖p − v_i‖` (singular nos vértices); potencial escalar `Φ^pot = Σ F_i·(p−v_i)/‖p−v_i‖²` (aparece como LaTeX cru, não renderizado). **Inconsistência dimensional**: as três "resultantes" não têm a mesma unidade, então não podem ser somadas nem comparadas.
- **§5.6 "centro de massa conceitual"** definido simultaneamente como `argmax |Φ(p)` e `argmin |Φ(p)` — são pontos diferentes; precisa escolher um (recomendo argmax = perfil predominante, e reportar argmin como "pilar mais negligenciado", que é justamente a leitura ética que o modelo precisa).
- **§6.2 Princípio de Consistência Hierárquica**: vértice→aresta (`R_ij(1) = F_i`, `R_ij(0) = F_j`), aresta→face (`T_ijk|_{e_ij} = R_ij`), face→volume (`Φ|_{f_ij} = T_ijk`). **Este é o axioma mais valioso do documento para ETH-WCMK** e não está usado no paper: ele exige que a nota de um faceta de vértice, a tensão de uma aresta e a adequação de volume sejam *a mesma função avaliada em níveis diferentes*. Formalizável como três invariantes testáveis (B1): (i) projeção de aresta coincide com os valores dos vértices nas extremidades; (ii) agregação de arestas sobre uma face reproduz o valor da face; (iii) agregação das quatro faces reproduz o valor global. Hoje o paper não tem nada disso — `Aa`, `T` e os facet scores são três cálculos independentes.
- **§6.3 "Princípio de Emergência"**: `R_ij = E_unary(F_i,F_j) + ΔR_ij`, `T_ijk = E_ternary(R_ij,R_jk,R_ik) + ΔT_ijk`, `Φ = E_global(T_123,T_124,T_134,T_234) + ΔΦ`. Estrutura correta (4 faces ✔), mas `Δ` nunca é definido — é exatamente o lugar onde deveria entrar a correção de déficit crítico `φ_i·1[d_i>θ_i]` e a penalidade epistêmica: o "excesso emergente" não explicado pelos pilares.
- **§6.4 funcional de energia `E[Ψ]`** está **corrompido/truncado** no PDF (LaTeX quebrado). É a única definição do funcional e não pode ser reconstruída: **precisa ser reescrito do zero** se o paper pretende usar otimização variacional.
- **§6.6 condições de integrabilidade**: `∮_C R_ij·dℓ = 0` ✔ plausível; `∮_S T_ijk·dS = 0` **mal tipado** (`T` é tensor de ordem 3, não vetor); `∮_V Φ·dV = 0` **errado**: fluxo se calcula sobre a borda, `∮_{∂V} Φ·dS`. Teoremas de conservação `ΣF_i = const` e `Σ v_i × F_i = const` — o segundo depende da escolha da origem (não é invariante por translação), portanto não pode ser apresentado como invariant do modelo.
- **§6.7 simetrias**: `T_d` tem 24 elementos ✔, mas **12** são rotações próprias; o grupo de rotações do tetraedro é `A_4` (ordem 12). Para ETH-WCMK isto é decisivo: se os quatro pilares são intercambiáveis por simetria, a calibração de domínio deve ser **equivariante** sob `A_4` — ou então o modelo declara que os pilares **não** são simétricos ( Want/Can/Must/Know têm estatutos distintos), e nesse caso `T_d` não é o grupo de automorfismos do modelo. Recomendo declarar: o grupo de simetria do tetraedro *geométrico* é `T_d`, mas o grupo de simetria do modelo ETH-WCMK é trivial (ou, no máximo, permutações dentro de subconjuntos autorizados), e isso deve aparecer como axioma explícito, não como metáfora.
- **§6.7.2 invariantes**: escalares `I_1 = Σ‖F_i‖²` ✔; `I_2` ilegível; `I_3 = ∭_V Φ(p)² dV` (formalmente ok, mas nunca computado). Tensoriais `J_1 = tr(F Fᵀ)` e `J_2 = det(F)`: **`F` nunca é definido como matriz** — é a família de vetores `F_i`. `det` de uma matriz 4×3 não existe.

**Correção construtiva que propongo para v10** (usa o que o PDF sugere, mas com matemática fechada):
Seja `F_i = a_i v_i` com `v_i` centrados e unitários (convenção B). Então
`I_1 = Σ‖F_i‖² = Σ a_i² = P`, a **pureza** do perfil, com `P ∈ [1/4, 1]`, `P = 1/4` no baricentro e `P = 1` num vértice. Definir
`Coerência(a) = (1 − P)/(3/4) ∈ [0,1]`, que é 1 no perfil equilibrado e 0 num perfil degenerado — uma medida **algébrica, limitada e auditável**, sem integrais, e equivalente à família de medidas `V(a)` e `B(a)` já discutidas.
Para o determinante, substituir `det(F)` indefinido pelo **vetor de volumes baricêntricos** `(a_W, a_C, a_M, a_K)` — geometricamente exato (verificado: cada sub-tetraedro tem fração de volume igual a `a_i`) — e `J_1` acima como seu resumo escalar. Isso elimina a cegueira a Want e dá um objeto formal para a narrativa "o volume interior representa a agência integrada".




## 4. Revisão das 24 facetas (Tarefa 3)

*(Pendente de integração fina com o inventário exato dos indivíduos em `wcmk-facets.ttl`, que está sendo auditado. A estrutura abaixo é a proposta de redesign.)*

### 4.1 Modelo de projeção multi-pilar

Hoje: `Facet --projectsToCoreVertex--> exactly 1 CoreVertex` (`sh:maxCount 1`).
Proposta: **projeção distribuida**.

```
wcmkf:projectsToCore  facet → (vertex, weight)  com Σ β = 1, β ∈ [0,1]
```
Materialização: `FacetProjection` como classe intermediária (faceta, vértice, peso, justificativa, domínio), permitindo **pesos distintos por domínio** e por perfil.

Efeito matemático: o valor de faceta `f` entra em **vários** pilares:
`a_i = Σ_{f} β_{f,i} · v_f` , com Σ_i a_i = 1 automaticamente se Σ_i β_{f,i} = 1 para cada f.
Déficit de faceta: `d_f = max(0, q_f − v_f)` onde `q_f` é o requisito do caso para a faceta (o catálogo já tem `FacetRequirement`).
Penalidade por faceta: κ = Σ_f λ_f d_f + Σ_f μ_f·1[d_f > θ_f].

### 4.2 Facetas que **devem** ser compartilhadas (matriz β)

| Faceta | W | C | M | K | Justificativa |
|---|---|---|---|---|---|
| W1 Goal Orientation | 0.70 | 0.10 | 0.10 | 0.10 | teleologia, mas depende de knowing-the-goal |
| W2 Value Alignment | 0.50 | 0.10 | 0.35 | 0.05 | valor ↔ norma |
| W3 Stakeholder Regard | 0.40 | 0.10 | 0.30 | 0.20 | consideration is partly duty |
| W4 Priority Discipline | 0.60 | 0.20 | 0.20 | 0.00 | ordering = intention + capability |
| W5 Intentional Stability | 0.60 | 0.20 | 0.10 | 0.10 | drift also epistemic |
| C1 Functional Capability | 0.00 | 0.80 | 0.00 | 0.20 | competence needs knowledge |
| C2 Robustness | 0.00 | 0.70 | 0.10 | 0.20 | robustness needs causal knowledge |
| C3 Controllability | 0.10 | 0.60 | 0.30 | 0.00 | interruptibility is a duty |
| C4 Scope Adequacy | 0.10 | 0.55 | 0.35 | 0.00 | scope = authorization (Must) |
| C5 Resource Sufficiency | 0.00 | 0.80 | 0.10 | 0.10 | |
| C6 Safe Executability | 0.00 | 0.50 | 0.40 | 0.10 | safety is partly obligation |
| M1 Legal Obligation | 0.00 | 0.10 | 0.70 | 0.20 | obeying law requires knowing it |
| M2 Institutional Policy | 0.00 | 0.15 | 0.65 | 0.20 | |
| M3 Ethical Principle | 0.10 | 0.05 | 0.80 | 0.05 | |
| M4 Prudential Obligation | 0.10 | 0.25 | 0.55 | 0.10 | caution needs capability+knowledge |
| M5 Role Obligation | 0.10 | 0.15 | 0.60 | 0.15 | |
| M6 Accountability | 0.10 | 0.20 | 0.50 | 0.20 | traceability is epistemic too |
| K1 Evidential | 0.00 | 0.10 | 0.20 | 0.70 | |
| K2 Contextual | 0.10 | 0.10 | 0.10 | 0.70 | |
| K3 Normative | 0.00 | 0.00 | 0.40 | 0.60 | overlap M1/M2 by design |
| K4 Procedural | 0.05 | 0.30 | 0.15 | 0.50 | |
| K5 Causal | 0.10 | 0.20 | 0.10 | 0.60 | |
| K6 Uncertainty Awareness | 0.10 | 0.05 | 0.25 | 0.60 | escalation is a duty |
| K7 Provenance | 0.00 | 0.10 | 0.30 | 0.60 | provenance is accountability |
| **K8 (nova) Learnability** | 0.10 | 0.30 | 0.10 | 0.50 | "o que pode aprender" |
| **W6 (nova) Intention Legitimacy** | 0.50 | 0.10 | 0.30 | 0.10 | origem legítima do objetivo |

Total: **26 facetas** (24 + 2 novas). Alternativa minimalista: manter 24 e absorver learnability em K6 (com sub-propriedades) e legitimidade em W1 (com sub-propriedade) — recomendo os números 26 porque ambos aparecem na *definição* original dos pilares e não na prática do catálogo.

### 4.3 Redundâncias detectadas (para fundir ou delimitar)

| Par | Sobreposição | Solução proposta |
|---|---|---|
| C2 Robustness ↔ C6 Safe Executability | robustez sob pressão ⇒ executabilidade segura | C2 = desempenho sob perturbación; C6 = **risco de execução desproporcional** (consequencial). Delimitar por observáveis distintos. |
| C4 Scope Adequacy ↔ C5 Resource Sufficiency | escopo e recursos | C4 = *autorização/competência delegada*; C5 = *meios*. C4 migra 35% para Must. |
| M1 Legal ↔ M3 Princípios éticos | normas vs princípios | manter separados, mas declarar **precedence rule** e estado `CONFLICT`. |
| K3 Normative ↔ M1/M2 | saber a norma ≠ cumprir a norma | K3 é epistêmico (know the rule); M1/M2 são deônicos (follow the rule). Explícito no §4 do paper, implícito na agregação. |
| K1 Evidential ↔ K7 Provenance | evidência e origem | K1 = força da evidência; K7 = rastreabilidade. Não fundir. |
| W1 ↔ W4 | objetivo e ordem de objetivos | W1 = *o que se busca*; W4 = *como se prioriza sob conflito*. |
| K6 ↔ K4 | incerteza e procedimento | K6 inclui **escalation willingness**; K4 é execução. |

### 4.4 Regras de agregação — formalização

O catálogo usa `WeightedMeanCompensatory`, `GuardedWeightedMean`, `ThresholdOverride`, `SoftMinPenalty` sem definições matemáticas. Formalizar:

- `WM(v_1..v_n; β) = Σβ_i v_i`
- `GWM(v; β, θ) = WM(v;β) − ψ·max(0, θ − min_i v_i)`
- `TO(v; θ) = min(v̄, 1 − s·1[min_i v_i < θ])` — teto duro, não média
- `SoftMin(v; β, p) = (Σ β_i v_i^p)^{1/p}`, p<1 (p→0 ≈ média geométrica)
- **Uncertainty-penalized mean:** `v̄ = WM(v;β)·(1 − H(v)/H_max)`.

Também falta declarar: (i) se os pesos β de uma faceta são *internos* à faceta (sub-observáveis) ou *cross-facet* (faceta → pilares); hoje ambas as leituras coexistem na TTL e geram ambiguidade de tipo.

---

## 5. Ontologia e validações formais (Tarefa 4)

*(Seção em consolidación com a auditoria TTL/SHACL em curso.)*

### 5.1 Coerência estrutural observada

- **Dois namespaces para um mesmo projeto:** `https://eth2.local/ontology/ethcase-*` (core/analysis) vs `https://ethwcmk.org/ontology/...` (facetas, bridge, requirements). Isso gera classes "placeholders" duplicadas (`eth:EthicalCase` declarado *dentro* do arquivo de requirements como classe sem parentesco com `ethcase-core:EthicalCase`). **Fix:** namespace único + imports formais (`owl:imports`) e remoção de placeholders.
- **Domínios:** catálogo do paper = 10 domínios; TTL declara 6 (`health, justice_security, critical_infrastructure, education, privacy_data, information_media`). Faltam **Finanças, Governança Pública, Trabalho, Meio Ambiente e Energia**. Sem esses, os exemplos sintéticos da Tarefa 5 não têm ancoragem.
- **Camada formal ausente:** nenhum arquivo TTL declara `r_i`, `λ_i`, `α_ij`, `γ`, `ρ`, `U_E`, `R_c`. Ou seja, o §6 do paper não é operacionalizável pela ontologia atual. **Fix:** classes `RequirementVector`, `SalienceVector`, `TensionWeights`, `PenaltyParameters` com SHACL (`minCount`, range 0–1, e regra de soma — expressível via `sh:rule`/`sh:SPARQL` constraint).
- **Restrição que contradiz a Tarefa 3:** `sh:maxCount 1` em `projectsToCoreVertex`.

### 5.2 Validações formais a executar (entregável da Tarefa 4)

1. **Consistência de classes** — every `Facet` subclass is `Facet`; every `FacetScore` has exactly one score in [0,1].
2. **Cobertura** — cada faceta do catálogo documentado tem um indivíduo na TTL (confirmar 24/24) e cada domínio do paper tem um `DomainProfile`.
3. **Invariante de simplex** — Σλ=1 e Σr=1 declarados e validados (SHACL `sh:rule` com SPARQL).
4. **Alinhamento de pesos** — Σ_i β_{f,i} = 1 para toda projeção multi-pilar.
5. **Provenance** — cada `FacetAssessment` tem `prov:wasDerivedFrom` e `prov:wasInfluencedBy` apontando a uma `DomainProfile`/`CalibrationArtifact` existente.
6. **Contratos do bridge** — toda `BridgeEvaluation` tem `AdequacyAssessment` + `ResidualRiskAssessment` + `DecisionRecommendation` (nada fica "solto").
7. **Exemplos inválidos** — o arquivo `bridge-wcmkplus-scoring-example-invalid.ttl` já existe: transformar em **suite de regressão** (cada shape deve falhar exatamente como esperado).

### 5.3 Ontologia-alvo (v2), módulos

```
ethcase-core.ttl        (caso, stakeholders, situação, consequências, vulnerabilidade)
ethcase-context.ttl     (domínio, severidade, reversibilidade, urgência, sensibilidade de dados)
ethcase-norms.ttl       (norma, tipo deônico, precedência, conflito)          [NOVO]
ethcase-requirements.ttl(r, λ, requisitos de faceta, prudência)
wcmk-core.ttl           (4 pilares, perfil admissível, métrica)
wcmk-facets.ttl         (26 facetas + projeção multi-pilar)
wcmk-assessment.ttl     (FacetAssessment, déficits, κ)
bridge.ttl              (confrontação, adequação, risco residual, decisão, explicação)
calibration.ttl         (Ω_d, θ_i, γ, ρ, η, floors)                            [NOVO]
provenance.ttl          (prov, versões, auditoria)
```

---

## 6. Corpus ETHCASE sintético (Tarefa 5) — especificação

### 6.1 Taxonomia

**10 domínios** (paper) × **4 bandas de severidade** (LOW/MEDIUM/HIGH/CRITICAL) × **3 modos prudenciales** (STANDARD/ELEVATED/MAXIMUM) × **6 famílias de agência** (Balanced supervised, Action-oriented, Normatively guarded, Epistemic reviewer, + 2 novas: **Human-in-the-loop hybrid** e **Autonomous low-supervision**) × **6 padrões de conflito normativo** (lei vs princípio, política vs lei, duty vs utilitarian, short vs long term, transparency vs privacy, autonomy vs protection).

Combinatório-alvo: **~1.200 casos-base** (10×4×3 = 120 templates × 6 agência × variantes) organizados em:
- **Núcleo (Core):** 120 casos canônicos, semi-manual, revisados.
- **Variação (Synthetic):** 600–900 casos gerados por perturbação controlada do núcleo (change stakeholder, severity, evidence, reversibility).
- **Adversarial (Stress):** 150–200 casos de edge-case deliberadamente ambiguos, com conflito normativo e incerteza alta.
- **Degenerados (Null/Negative):** 50 casos que *devem* falhar (requisito impossível, perfil vazio, evidência ausente) — servem para calibrar false positives.

### 6.2 Schema do caso (JSONL → TTL)

```
{ case_id, domain, title, summary,
  situation: {actors[], action, setting, temporal_scope},
  stakeholders: [{role, vulnerability, reversibility_of_impact}],
  consequences: [{kind, magnitude, timeframe, certainty}],
  evidence: [{type, quality, contestability, provenance}],
  norms: [{type: law|policy|principle|role, jurisdiction, text, deontic: obligation|prohibition|permission, precedence}],
  normative_conflicts: [{norm_a, norm_b, kind}],
  uncertainty: {aleatoric, epistemic, completeness},
  r: {W,C,M,K}, lambda: {W,C,M,K}, severity, prudential_mode,
  expected_outcome_classes: [...],        // ground truth prudential
  difficulty, ambiguity, tags[]
}
```

### 6.3 Protocolo de geração
1. Seed manual de 120 casos (2 por domínio × 6 templates) escritos por humanos, com **r e λ justificados** por uma ficha de derivación (requisitos → observáveis).
2. Geração por LLM *controlada por template* (não livre): cada perturbación é um operador (swap stakeholder, ↓ reversibility, ↑ uncertainty, add norm conflict).
3. **Validação dupla:** (a) SHACL conformance automática; (b) revisão de 2 annotadores independentes sobre r/λ/severidade com κ de inter-rater ≥ 0.70.
4. **Balanceamento:** cada domínio ≥ 100 casos; cada severidade presente; casos "hard" ≥ 20% do corpus.
5. Split: dev (70%), calibration (15%), blind test (15%) — blind test nunca usado para tuning.

---

## 7. Baterias de teste (Tarefa 6)

| Bateria | Objetivo | Método | Critério de aprovação |
|---|---|---|---|
| **B1. Formal-core unit tests** | invariantes do núcleo (`monotonicidade`, `non-compensação`, `bounds`, `piso de risco`, `degenerescência de volume`) | pytest sobre implementação de referência (NumPy) | 6 invariantes, 100% de testes verdes; propriedade por Hypothesis (fuzzing sobre simplex) |
| **B2. Conformance semântico** | SHACL/TTL válidos | PyShACL / ShaclJS nos exemplos valid/inválido | todos inválidos rejeitados; todos válidos aceitos |
| **B3. Perturbação / stress** | sensibilidade a pequenas mudanças de `a`, `r`, `Ω_d`, `U_E` | sweep ±0.05 e ±0.10; adversarial: perfil bom em Want e pobre em Must | `ΔAa` deve seguir direção correta em ≥ 95% dos casos; nenhuma violação de monotonicidade |
| **B4. Calibração & sensibilidade** | γ, ρ, η, θ_i, α_ij | grid + Sobol indices; ablation (com/sem T, com/sem u) | γ+ρ ≤ 0.30; nenhum parâmetro com índice Sobol > 0.40 sem justificativa |
| **B5. Benchmark de julgamento** | concordância com especialistas | painel de 20–30 casos hard julgados por 3+ revisores humanos; comparar com classes do bridge (allow/allow-with-guards/needs-review/restrict/block) | κ ≥ 0.60 na decisão de classe; recall de "needs-review" ≥ 0.85 (não deixar casos de alta severidade sem revisão) |
| **B6. Robustez de profiling LLM** | estabilidade do perfil produzido pelo LLM | same case, 5 seeds/temperature, 3 prompts | variação do perfil ≤ 0.05 por coordenada; discordância > 0.15 → flag |
| **B7. Interoperabilidade** | bridge vs guardrails existentes (classifiers, policies) | dual-run em casos de conteúdo/ação | concordância ≥ 0.7 e casos onde ETH-WCMK *adds* explicação |

**Métricas reporting:** precisão/recall por classe de decisão; distribuição de `Aa` e `R_r`; número de "near-misses" por invariante; matriz de confusão domínio × pilar crítico; taxa de flag para revisão humana.

---

## 8. Reformulação do paper (Tarefa 7) — estrutura v10

**Título sugerido:** *ETH-WCMK: um modelo simplex de adequação agency-caso com risco residual auditável.*

1. **Abstract** — manter ideia; trocar "tetrahedral" por "simplex-calibrated tetrahedral representation" (evita a promesa matemática que o texto não cumpre).
2. **Intro / Gap** — manter.
3. **Related work** (top-down/bottom-up/hybrid, guardrails, Constitutional AI) — manter, acrescentar: work on *deontic logic for AI*, *situational awareness* e *risk residual* em safety (Hollnagel, STIR).
4. **ETHCASE** — manter + adicionar schema formal (classes, atributos, vetores r, λ).
5. **WCMK+ facetas** — 26 facetas, matriz de projeção multi-pilar, regras de agregação formalizadas.
6. **Núcleo matemático (reescrito)** — Definições 1–6, Teorema 1 (embedding unitário centrado), Proposição 1 (bounds), Proposição 2 (non-compensação), Definição 3 (coherência volumétrica). Provas curtas, todas verificáveis.
7. **Bridge & decisão** — fluxo formal + tabela de outcomes + piso de risco.
8. **Implementação ontológica** — módulos, SHACL, exemplos valid/inválido.
9. **Corpus sintético (novo, resultado real)** — descrição do corpus e estatísticas.
10. **Baterias e resultados (novo, resultado real)** — invariantes, perturbação, benchmark.
11. **Análise comparativa** — manter tabela.
12. **Limitações & trabalhos futuros** — honestidade sobre calibração exemplar; adicionar "dependência de r/λ como julgamento de modelagem".
13. **Apêndice** — todas as equações, catálogo completo de facetas, invariantes, código de referência.

**Figuras a refazer:** (i) tetraedro centrado com ponto baricêntrico e sub-volumes marcados; (ii) diagrama do fluxo bridge com fórmulas legíveis (as equações atuais estão em PNG, o que impede reuso e acessibilidade — converter para MathML/LaTeX no docx); (iii) heatmap de projeção faceta→pilar; (iv) curva `R_r(Aa)` mostrando o piso.

---

## 9. Plano de execução, cronograma e artefatos

| Fase | Semanas | Tarefas | Artefatos |
|---|---|---|---|
| **F0 — Fundação** | 1–3 | T1, T2: correção do núcleo formal; implementação de referência (Python) | `formal_core.py` + `test_invariants.py`; §3 reescrito |
| **F1 — Facetas & ontologia** | 3–8 | T3, T4: catálogo v2 (26 facetas, matriz β); TTL/SHACL v2; validações formais | `wcmk-facets-v2.ttl`, `ethcase-*.ttl`, suite de conformance |
| **F2 — Corpus** | 6–12 | T5: 120 núcleo + geradores + revisão dupla | `ethcase-corpus.jsonl` + relatório de balanceamento |
| **F3 — Baterias** | 10–16 | T6: B1–B7 | relatório de resultados, plots, κ |
| **F4 — Paper v10** | 14–20 | T7: reescrita, figuras, apêndice, validação interna | paper v10 + appendix + código |
| **F5 — Publicação/loop** | 20–24 | revisão externa, submissão, release de assets | repositório com LICENSE e versioning |

**Riscos:** (i) calibração Ω_d/θ_i sem dados reais → mitigar com calibração por painel de especialistas e reporte explícito de "exemplar de trabalho"; (ii) corpus sintético enviesado pelo LLM gerador → mitigar com revisão humana amostral (≥20%) e templates fixos; (iii) crescimento combinatório das facetas → mitigar com regra de parada: nenhuma faceta nova entra sem observável e sem regra de agregação definida.

---

## 10. Decisões imediatas recomendadas (próximas 72 horas)

1. Corrigir Eq.(1)/Eq.(5) no paper e **provar** o embedding centrado (não é cosmético: sustenta toda a narrativa geométrica).
2. Definir "volume/coherência" como fração de sub-tetraedros (`min a_i`, `(∏a_i)^{1/4}`) e remover toda afirmação não sustentada.
3. Introduzir piso de risco em Eq.(11).
4. Trocar `u = U_E(1−k)` por `u = U_E·d_K/r̂_K` e escolher *uma* contagem do Know.
5. Normalizar `T` (α_ij = 1/6) e penalizar apenas déficits, não excessos.
6. Substituir `sh:maxCount 1` por projeção multi-pilar com Σβ = 1.
7. Declarar `r, λ, α, γ, ρ, η, θ, R_c` na ontologia e escrever os 6 invariantes como testes automatizados.
8. Fixar as 26 facetas e a matriz β antes de gerar corpus e baterias.
