# ETH-WCMK — Plano de execução v2 (Retomada)
**Versão:** 2.0 · **Data:** 31/10/2026 · **Autor:** assistente de análise (reviewer técnico)
**Base documental verificada:** `ETH-WCMK v9.docx` (550 linhas, 11 equações rasterizadas), `WCMK_plus_catalogo_facetado_v1_clean.docx`, `Arquitetura_v1_ETH_WCMK_LLM.docx`, `Estrutura Matemático-Simbólica do Tetraedro Regular.pdf`, 18 arquivos TTL/SHACL (2 famílias de namespace), `_analysis/` (10 scripts, 2 relatórios), `Evaluacoes/` (B1, B3, B4, corpus v2).

---

## 0. Natureza do plano

Este plano **não reescreve** o trabalho anterior: ele o **audita e reordena**. A rodada anterior (27–28/10) produziu um diagnóstico matemático correto em sua maior parte (`formal_core.py`, `formal_core_v3.py`, `tetra_geometry.py`, bateria B1) e um corpus que, executado sobre a matemática antiga, **valida empiricamente os defeitos do modelo em vez de validar o modelo**. O problema central da retomada é therefore de **consistência entre quatro camadas** que hoje não conversam: (i) equações do paper, (ii) código de referência, (iii) ontologia/SHACL, (iv) corpus e baterias.

Cada fase abaixo tem **gate de saída explícito**. Nenhum gate pode ser considerado passado sem artefato verificável (arquivo, teste, número).

---

## 1. Inventário e estado real (verificado)

| Artefato | Estado | Confiabilidade |
|---|---|---|
| Paper v9 | Completo, 11 equações, 10 tabelas, 6 figuras | Bom conceitualmente; matematicamente impreciso |
| Catálogo de facetas (24) | Rico semanticamente; sem pesos numéricos, sem observáveis operacionais | Utilizable como canon conceitual |
| Ontologias (18 TTL/SHACL) | duas famílias desconectadas: `eth2.local/...` (core, assessment, profile, instance) e `ethwcmk.org/...` (facets, bridge, requirements) | Estruturas boas, **sem camada quantitativa declarada** |
| `formal_core.py` / `formal_core_v3.py` | v3 implementa déficits hierárquicos, piso de risco, veto | v3 nunca foi transplantado ao paper nem à ontologia |
| Corpus v2 | 468 casos, 27 perfis, 100 probes, 12.636 confrontações | **Degenerado**: Aa = 1,0 em 32,9%; déficits nulos em 4.146 casos; veto nunca dispara; Σρ ∈ [1,92, 3,04] (fora do simplex); Σa ∈ [1,82, 3,33] |
| B1 (12 invariantes, 20.000 amostras) | Rodou. v2 falha piso de risco 15,6% e monotonicidade 7 casos; v3 passa 12/12 | Válida, mas só sobre vetores do simplex que o corpus nunca produz |
| B2 (SHACL) | 184 pares, "0 violações" | **Inválida**: assinatura do pyshacl usada como posição e contador errado; `inference="rdfs"` mascara violações de classe |
| B3 / B4 | B3: 16.000 checks monotônicos, 100%. B4: Morris, não Sobol | B4 reporta ω = 0,0 e floor = 0,0 — consequência da degeneração, não do modelo |
| B5, B6, B7 | Não existem | Lacuna crítica: não há ground truth |
| Paper v10, ontologia v2, suite pytest | Não existem | — |

**Ambiente de execução disponível:** `python3` + `rdflib 7.6.0`, `pyshacl 0.40.1`, `numpy 2.5.4`, `pytest 9.2`. Indisponíveis: `scipy`, `hypothesis`, `SALib`, `owlready2`, `pandas`. Implicação: índices de Sobol e property-based testing devem ser implementados em numpy puro ou com fixtures enumerativos; a "consistência OWL" será aproximada por shapes SHACL + consultas SPARQL, e essa limitação deve ser declarada no paper.

---

## 2. Diagnóstico crítico (Tarefa 1) — pontos por prioridade

### P0 — defeitos que invalidam resultados

**P0.1 Confusão entre *nível* e *participação* (falha matriz do modelo).**
O modelo trata `a = (w,c,m,k)` com `w+c+m+k=1` como se cada coordenada fosse o *nível* do pilar. No simplex, uma coordenada é uma **fração de um total**, não uma magnitude. Consequências formais:
- O nível máximo "igual" possível é 0,25. Um agente perfeitamente ético não pode existir no modelo.
- Se `Σa = Σr = 1`, a condição "não-compensatória" `a_i ≥ r_i ∀i` só é satisfeita quando `a = r`. Ou seja, **satisfazer todos os requisitos exige identidade** — qualquer déficit em um pilar é, por construção, excesso em outro. O geometric zero-sum **contradiz** o princípio deontológico de não-compensação que o paper afirma defender.
- A distância geométrica induzida e a distância declarada não são a mesma métrica: `d_Δ = ½‖a−b‖₁` (variação total) e a corda no embedding satisfaz `‖x(a)−x(b)‖ / (½‖a−b‖₁) ∈ [1,1547; 1,633]` (verificado numericamente). Não há perda de informação, mas o paper usa as duas como se fossem equivalentes.

**P0.2 O "volume interno" é trivial ou nulo.**
Para `a` baricêntrico, os quatro sub-tetraedros formados por `x(a)` e cada face têm volume exatamente `a_i · V_total` (verificado: `a=(0.4,0.3,0.2,0.1)` → 0,0471; 0,0354; 0,0236; 0,0118, soma 0,11785 = √2/12). Logo a "coerência volumétrica" **não acrescenta informação** além do próprio vetor. E o termo quaternário `ω·δ_Wδ_Cδ_Mδ_K` é **identicamente zero** sempre que `Σa = Σr` (impossível haver quatro déficits positivos simultâneos). O B4 mediu exatamente isso: efeito do parâmetro ω = 0,0.

**P0.3 Risco residual viola seu próprio princípio.**
`R_r = R_c(1 − Aa)` (Eq. 11) zera quando `Aa = 1`, contra a tese explícita do paper de "atenuação sem apagamento". Além disso, todas as thresholds do bridge são razões `R_r/R_c`, de modo que **R_c cancela** na decisão: reproduzindo as 12.636 decisões do corpus a partir apenas de `Aa`, obtemos 3 divergências por arredondamento. Irreversibilidade e severidade, os dois atributos éticos mais relevantes do caso, não entram na adjudicação.

**P0.4 Penalidade epistemic incompatível com o simplex.**
`u = U_E(1 − k)` (Eq. 9) com `k` coordenada do simplex: para um perfil equilibrado `k = 0,25`, `u ≈ 0,75 U_E` **independentemente de o agente saber ou não** — a penalidade é quase constante e persiste mesmo com déficit de Know nulo. Com os parâmetros do paper (`ρ=0,15`, `U_E=0,35`), `Aa` não pode chegar a 1 em nenhum caso com incerteza > 0.

**P0.5 Veto declarado, invisível na pontuação.**
Nas 20.000 amostras de B1, 10.016 casos têm pilar crítico com déficit ≥ 0,5; **94,44% deles** continuam com `Aa ≥ 0,60` porque média ponderada compensa o déficit. Uma regra deontológica que não altera a decisão não é uma regra deontológica — é um peso extra.

**P0.6 Tensão penaliza excelência.**
`T = Σ α_ij |(a_i − r̂_i) − (a_j − r̂_j)|` (Eq. 4) pune desvios *simétricos*: um agente que supera muito um requisito é penalizado como se falasse. Exemplo do paper: `(a_W,a_C)=(0,20,0,35)` gera penalidade de 0,0606 apenas porque Want está **acima** do exigido.

**P0.7 Inconsistências de notação e de convenção.**
Eq. (2) define `r̂` e `λ̂`; Eq. (8) usa `r_i` e `λ_i` sem o chapéu; Eq. (4) define `T(E,a)` e Eq. (10) consome `T_int(a)`. Eq. (1) exige vértices **centrados e unitários** (`v_i·v_j = −1/3`, aresta `√(8/3)=1,633`); Eq. (5) dá vértices com aresta 1 e um vértice na origem (`v_i·v_j = +1/2`). As duas afirmações não coexistem. O PDF comete ainda: centro errado (`√6/4` em vez de `√6/12` — transposição de circunraio e inraio; o centro real do tetraedro de Eq. (5) é `(0,5; 0,2887; 0,2041)`), operadores sem tipo (`R_ij = F_i ∘ F_j` com `∘ ∈ {·,×,+,−}`), matriz de relações 4×4 quando as relações existem só sobre 6 arestas, e `F_i = α_i u_i` sem `‖u_i‖ = 1`.

### P1 — lacunas de design

1. **Metacognição rasa.** O pilar Know foi definido como "o que sabe, o que não sabe e o que pode aprender", mas K1–K7 não cobrem *aprendibilidade*, *calibração* (auto-avaliação confrontada com desfechos) nem *segunda ordem* (saber que não se sabe X implica não agir?).
2. **Facetas só nos vértices.** Se arestas (6), faces (4) e interior (1) são as relações entre pilares, faltam operadores definidos sobre eles. Hoje a "face" aparece apenas como um termo `η` e o "volume" como um produto nulo.
3. **Want sem legitimidade.** Não se distingue `Want` do agente (objetivo delegado) de `Want` do stakeholder (desejo legitimado). Sem isso, o modelo captura o interesse do operador.
4. **Must sem hierarquia de normas.** M1 (lei), M2 (política institucional), M3 (princípios), M4 (prudência), M5 (papel), M6 (accountability) têm estatutos diferentes e podem entrar em conflito; não existeprecedência nem estado `CONFLICT`.
5. **Atributos do caso sem operador.** Irreversibilidade, urgência, horizonte temporal, vulnerabilidade e população afetada existem como dados, mas nenhum entra em `Aa` ou `R_r` de forma não-trivial.
6. **Vocabulário de decisão triplicado.** Paper (ALLOW/CONDITIONAL/REVIEW/PROHIBIT), bridge (`ALLOW`, `ALLOW_WITH_WARNING`, `ALLOW_WITH_GUARDS`, `RESTRICT`, `BLOCK`, `REVIEW_REQUIRED`), corpus (`allow/conditional/review/prohibit`). Não há SKOS canônico.
7. **Fragilidade do ground truth.** "Acordo" de 23,6% é heurística contra heurística. Sem painel externo, o modelo não é avaliado, é auto-referente.

### P2 — problemas de apresentação e rigor

- Figuras rasterizadas para 11 equações (inacessível, não indexável, impropi para peer review).
- Afirmaciones sobre o PDF ("Princípio de Mínima Ação", "Consistência Hierárquica") não derivadas nem testadas.
- Limitações não declaradas: o modelo mede **níveis declarados/estimados**, não competência moral real; o corpus é sintético; sem calibração empírica externa.

---

## 3. Núcleo formal corrigido (proposta para v10) — Tarefa 2

### 3.1 Representação: níveis independentes + forma
- **Nível de agência:** `ℓ = (ℓ_W, ℓ_C, ℓ_M, ℓ_K) ∈ [0,1]⁴` — magnitudes independentes.
- **Forma (ênfase):** `s_i = ℓ_i / Σℓ`, ponto no simplex regular Δ³. O tetraedro continua válido, e é exatamente isso que ele representa: **a forma do perfil**, não seu nível.
- **Magnitude:** `m = Σℓ_i ∈ [0,4]`, `M̄ = m/4` (média) ou `M_g = (∏ℓ_i)^{1/4}` (média geométrica, sensível ao elo mais fraco).
- **Requisito do caso:** `q ∈ [0,1]⁴` (não normalizado) + saliência `λ ∈ Δ³` (pesos, Σλ=1). Saliência e requisito são objetos distintos; a redundância `λ ≈ r` do corpus v2 desaparece.

### 3.2 Geometria como índice relacional (lattice de faces)
A afirmação "vértices = pilares, arestas = relações, faces = tríades, volume = quaternário" é combinatoriamente exata: o lattice de faces do 3-simplex é isomórfico aos **subconjuntos não vazios** de {W,C,M,K}: 4 vértices (unários), 6 arestas (binários), 4 faces (ternários), 1 célula (quaternário) = 15 slots relacionais. Isso dá conteúdo matemático ao tetraedro **sem** exigir métrica de estado.
Defina uma função de set `g(S)` sobre esses 15 slots e exija:
- **Monotonia hierárquica:** para déficits, `S₄ ≤ S₃ ≤ S₂ ≤ max_i d_i` (provable: média geométrica ≤ mínimo ≤ máximo).
- **Coerência de projeção:** o nível do vértice agregado das suas facetas deve coincidir (dentro de tolerância) com o nível declarado.
- **Inversão de Möbius:** o termo quaternário é o resíduo não explicável pelos termos binários e ternários — definição não trivial do "interior".

Termos operacionais:
```
d_i        = max(0, q_i − ℓ_i)                    (déficit de nível, não-compensatório)
D          = Σ_i λ_i d_i                          (déficit ponderado)
S₂         = Σ_{i<j} α_ij · min(d_i, d_j),  Σα = 1   (fragilidad estructural, 6 arestas)
S₃         = Σ_{faces} β_f · min(d_i,d_j,d_k), Σβ = 1 (4 faces)
S₄         = (∏_i d_i)^{1/4}                       (colapso interior; não-zero só se todos falham)
Veto       = ∧_{i ∈ guarded} (d_i < θ_i)          (gate booleano, anterior à pontuação)
u          = U_E · d_K / max(q_K, ε)               (penalidade epistêmica relativa)
Aa         = clip(1 − D − γS₂ − ηS₃ − ωS₄ − ρu, 0, 1)
R_r        = R_c(1 − Aa) + σ(E)·R_c               (piso prudencial do caso)
Decisão    = vetos primeiro; depois umbral de Aa; depois umbral de R_r
```
Observável-chave: `Aa` **nunca** é publicado isolado; sempre acompanhado de `(d_W,d_C,d_M,d_K)`, pilar crítico `argmax λ_i d_i`, facetas vetadas e explicação.

### 3.3 Invariantes que v10 deve provar (14)
1. `Aa ∈ [0,1]`; 2. `Aa = 1` ⟺ todos os déficits zero e sem veto; 3. piso de risco `R_r ≥ σ R_c`; 4. `R_r ≤ R_c(1+σ)`; 5. **domínio do veto**: veto ⇒ decisão ∈ {review, prohibit} independentemente de `Aa`; 6. monotonicidade em cada `ℓ_i`; 7. monotonicidade em severidade; 8. `S₄ ≤ S₃ ≤ S₂`; 9. **não double-counting** de facetas compartilhadas (invariance a duplicação de contribuição); 10. coerência projeção faceta→vértice; 11. **abstention** obrigatória quando o caso tem dados faltantes acima de um limiar; 12. invariancia a renomeação/ordenamento de facetas; 13. continuidade (Lipschitz): |Δℓ| ≤ ε ⇒ |ΔAa| ≤ Lε; 14. reprodutibilidade determinística com seed.

---

## 4. Canon de facetas e compartilhamento — Tarefa 3

**Contagem canônica proposta: 26** (24 do catálogo + W6 Legitimidade + K8 Aprendibilidade). Cada faceta ganha: (i) código; (ii) observável(s) mensuráveis; (iii) política de agregação (uma das 5 já nomeadas na ontologia: `weighted_mean`, `guarded_weighted_mean`, `threshold_override`, `soft_min`, `uncertainty_penalized_mean`); (iv) vetor de projeção `β_f ∈ [0,1]⁴` com `Σ_i β_{f,i} = 1`; (v) slot de relação (vértice/aresta/face/célula); (vi) criticidade numérica por domínio (1–5, derivada do catálogo, não adjetiva).

**Compartilhamentos explícitos (propostas a validar):**
| Faceta | Projeção β | Justificativa |
|---|---|---|
| W1 Orientação finalística | W 0.8 / C 0.2 | viabilidade do fim |
| W2 Alinhamento axiológico | W 0.7 / M 0.3 | valores ↔ normas |
| W3 Consideração de stakeholders | W 0.6 / M 0.4 | duties toward affected parties |
| W5 Estabilidade intencional | W 0.7 / C 0.3 | robustness of behaviour |
| **W6 Legitimidade do Want** (nova) | W 0.6 / M 0.4 | proveniência do objetivo |
| C2 Robustez | C 0.8 / M 0.2 | falha segura = dever |
| **C3 Controlabilidade** | C 0.6 / M 0.4 | pode ser auditado/interrompido |
| C6 Executabilidade segura | C 0.5 / M 0.5 | guardrail duro (guarded) |
| M4 Prudência | M 0.7 / K 0.3 | prudência exige conhecer a incerteza |
| M6 Accountability | M 0.6 / W 0.4 | prestação de contas ao stakeholder |
| **K3 Conhecimento normativo** | K 0.6 / M 0.4 | saber a norma ≠ cumprir a norma |
| K4 Conhecimento procedimental | K 0.8 / C 0.2 | know-how operativo |
| K5 Conhecimento causal | K 0.7 / W 0.3 | previsão das consequências do fim |
| **K6 Consciência de incerteza** | K 0.6 / M 0.4 | limiar de agir sob incerteza |
| K7 Proveniência | K 0.5 / M 0.5 | evidência rastreável = dever |
| **K8 Aprendibilidade** (nova) | K 0.6 / C 0.4 | capacidade de adquirir conhecimento/recursos |

**Redundâncias a fundir ou demarcar** (conflitos já identificados em `facets_v2.py`): C2↔C6 (robustez vs executabilidade segura), C4↔C5 (escopo vs suficiência de recursos), M1↔M3 (legal vs principial), K1↔K7 (evidência vs proveniência), K3↔M1/M2, K6↔K4.

**Regra de parada:** nenhuma faceta entra no canon sem (a) observável, (b) política de agregação, (c) criticidade por domínio, (d) exemplo de instância TTL. Isso evita explosión combinatória e é testável.

---

## 5. Ontologia v2 e validações formais — Tarefa 4

**Módulos (base única `https://ethwcmk.org/ontology/`):**
1. `ethcase-core.ttl` — EthicalCase, Stakeholder, Action, Consequence, Vulnerability, EvidenceItem, Domain + atributos normativos (irreversibilidade como enum controlado + decimal, urgência, horizonte, direitos em risco, população afetada).
2. `ethcase-requirements.ttl` — requisito por faceta, regras de derivação com versão, agregação, bandas de severidade, modo prudencial.
3. `wcmk-core.ttl` — os quatro pilares como `skos:Concept`, **níveis** `wantLevel/canLevel/mustLevel/knowLevel` com `sh:minInclusive 0 sh:maxInclusive 1`.
4. `wcmk-facets.ttl` — 26 facetas como **indivíduos** (não `owl:Class`), `projectsToFacetPillars` (multi-pilar), `projectionWeight β`, `guarded`, `hasObservable`, `hasAggregationPolicy`.
5. `wcmk-calibration.ttl` — perfis de domínio, Ω_d, α, β, γ, η, ω, ρ, θ, φ, σ.
6. `bridge.ttl` — confrontação, déficit por faceta, termos estruturais S₂/S₃/S₄, `adequacy`, `residualRisk`, `decision`, `explanation`.
7. `decision-vocabulary.ttl` — um único SKOS: ALLOW / ALLOW_WITH_GUARDS / RESTRICT / REVIEW_REQUIRED / PROHIBIT / ABSTAIN.
8. `provenance.ttl` (prov) — toda requirement derivada e toda avaliação tracejam regra + versão + data.

**Validações formais (gate G4):**
- V1 integridade de IRIs: nenhum prefixo usado sem declaração; nenhuma classe referenciada sem definição (resolver o dual `eth2.local` vs `ethwcmk.org`).
- V2 consistência de tipo: facetas são indivíduos de `Facet`; avaliações são instâncias.
- V3 cobertura: 26/26 facetas com observável + política + criticidade.
- V4 integridade β: `Σ_i β = 1` por faceta (SPARQL/SHACL rule), ≥ 1 pilar por faceta.
- V5 normalização de saliência: `Σ λ = 1` (tolerância 1e-6).
- V6 domínio do veto expresso (a shape declara pilares `guarded` e limiares θ).
- V7 completude de proveniência: requisito derivado sem regra = violação.
- V8 regressão negativa: conjunto de casos *invalid* com **contagem esperada** de violações (não "0").
- V9 alinhamento vocabulário de decisão (1 esquema).
- V10 consistência numérica entre ontologia e `formal_core` (mesmos nomes e faixas de α,β,γ,η,ω,ρ,θ,φ,σ,U_E,R_c).

Limitação declarada: SHACL não aritmética não expressa invariantes de monotonia; esses serão provados por **property-based tests** (pytest + enumeración/parametrização) e por consultas SPARQL dedicadas, não por shapes.

---

## 6. Corpus ETHCASE v3 — Tarefa 5

**Especificação:**
- **Arquétipos:** 60 (40 existentes refinados + 20 novos cobrindo health, education, environment/energy, digital security, privacy, finance, public admin, justice, critical infra, labour, media, transport, research, plus cross-domain e "long-horizon autonomy" e "multi-stakeholder conflict").
- **Domínios:** 13 (catálogo) com criticidade numérica por faceta (matriz 26 × 13 preenchida, derivada do catálogo, não arbitrária).
- **Bandas de severidade:** 4; **modos prudenciales:** 3; **reversibilidade:** 3; **horizonte temporal:** 3.
- **Amostragem estratificada:** cobertura de célula do design fatorial (não cartesian full): alvo **1.200 casos**, com quota mínima por domínio e por classe de conflito.
- **Gold seed:** **120 casos** adjudicados por 3 avaliadores (humanos, se disponível; caso contrário, painel LLM heterogéneo com protocolo documentado e limitação explícita), adjudicação dupla, κ inter-avaliador ≥ 0,60 alvo.
- **Splits:** 70% desenvolvimento / 15% calibração / 15% cego (blind) — o cego nunca entra na calibração de pesos.
- **Probes degenerados/adversariais:** ≥ 150 (dados faltantes, requisitos contraditórios, nível todo-zero, requirement > 1, veto vs adequacy em conflito, saliência degenerada, perfil fora de [0,1]).
- **Perfis de agência:** ≥ 40 (famílias × maturidade), agora como **vetores de nível** `ℓ` + vetor de nível por faceta.

**Saída:** `corpus_v3_cases.jsonl`, `corpus_v3_facet_requirements.jsonl`, `corpus_v3_profiles.jsonl`, `corpus_v3_gold.jsonl`, `corpus_v3_probes.jsonl`, `coverage_matrix.csv`.

**Critério de qualidade (gate G5):** nenhuma degeneração observada — `Aa=1` deve ocorrer em < 3% dos confrontos; o veto deve disparar em 5–20% dos casos de severidade crítica; severidade deve mover a decisão monotonicamente em ≥ 95% das pares comparáveis; ≥ 120 perfis distintos.

---

## 7. Baterias de teste — Tarefa 6

| Bateria | Objeto | Métrica | Gate |
|---|---|---|---|
| **B1 Invariantes** | núcleo formal v3, 50.000 amostras estratificadas + fixtures | 14 invariantes; violações = 0 | G2 |
| **B2 Conformância ontológica** | 8 módulos + shapes, suite positiva e negativa | resultados esperados reproduzíveis; contagem de violações por fixture | G4 |
| **B3 Severidade & perturbación** | escalón Low→Critical, perturbações ±0,05 e ±0,10 nos níveis | monotonia 100%; decisões não-involutivas | G6 |
| **B4 Sensibilidad global** | Sobol' de primeiro e total (implementação numpy, N=4096, 8 parámetros) | ranking μ/σ; identificar parámetros inertes | G6 |
| **B5 Gold & concordancia** | 120 casos gold, κ painel vs modelo | κ ≥ 0,60 painel; Spearman ≥ 0,70 modelo–gold | G7 |
| **B6 Robustez de perfis** | inferência de níveis por LLM, 5 seeds × 3 prompts | CV por faceta ≤ 0,10; decisão-flip ≤ 5% | G7 |
| **B7 Baselines** | (a) filtro de regras; (b) média compensatória simples; (c) só veto; (d) modelo completo | concordancia com gold, AUROC de "should-prohibit", estabilidade ante ruído ±0,1, nº de razões citadas | G7 |
| **B8 Probes degenerados** | 150 probes adversarios | taxa de abstention correta = 100% | G6 |

Saída: `Evaluacoes/r2_B1_invariants.json` … `Evaluacoes/r2_report.md` (relatório consolidado) + figure set (Sobol, ladders, calibration curves).

---

## 8. Paper v10 — Tarefa 7

Estructura proposta (mantendo todo o conteúdo válido de v9):
1. Introdução e gap. 2. Positioning vs guardrails, value-sensitive design, deontological logging, auditability. 3. ETHCASE (caso + requisitos). 4. WCMK como núcleo modal (want/can/must/know). 5. WCMK+ (26 facetas, compartilhamento, criticidade por domínio). 6. **Núcleo formal corrigido** (Eq. 1–12, com níveis independentes, déficits hierárquicos, veto, piso de risco) e **14 invariantes**. 7. **Geometria como índice relacional** (lattice de faces, 15 slots, S₂/S₃/S₄) — aqui entra, corrigida, a camada do PDF, sem apelar a "princípio de mínima ação" não demonstrado. 8. Ontologia dual e pipeline. 9. Avaliação empírica (corpus v3 + baterias). 10. Limitações e ameaças à validade. 11. Implicações de governança. 12. Conclusão + apêndice de reproduciibilidade (repositório, seeds, versões, equações em LaTeX nativo).

Conversão obrigatória: todas as equações em LaTeX/MathML nativo (não raster).

---

## 9. Gates e cronograma

| Fase | Entregável | Gate de saída | Esforço estimado |
|---|---|---|---|
| **F0** Congelamento e manifest | inventário com SHA-256, decisões aprovadas, layout de diretórios | G0: manifest + 6 decisões respondidas | 1 sessão |
| **F1** Núcleo formal v3 canônico | `formal_core/` (single source), spec de equações | **G1/G2**: 14 invariantes verdes, counterexamples documentados | 2 sessões |
| **F2** Canon de facetas + β | registry (CSV/TTL-ready), matriz β, criticidade 26×13 | G3: cobertura 26/26, β soma 1, conflitos adjudicados | 1–2 sessões |
| **F3** Ontologia v2 + SHACL | 8 módulos, shapes, suite regressiva | G4: V1–V10, contagem esperada de violações | 2–3 sessões |
| **F4** Corpus v3 + gold | cases, profiles, probes, gold seed, splits | G5: não-degeneração, κ painel ≥ 0,60 | 3–4 sessões |
| **F5** Baterias B1–B8 | JSON/CSV + relatório consolidado + figuras | G6/G7: métricas acima | 3 sessões |
| **F6** Paper v10 | draft completo + traceability matrix | G8: cada número do paper vem de um artefato | 2 sessões |
| **F7** Empacotamento | README, requirements, dashboard spec, decision log | G9: reproduzível por terceiro | 1 sessão |

Total: ~14–16 sessões de trabalho, com checkpoints humanos após cada gate.

---

## 10. Quick wins (executáveis imediatamente, destrava todo o resto)

1. Corrigir a chamada do runner SHACL (`shacl_graph=` keyword) e o contador (`subjects(RDF.type, SH.ValidationResult)`).
2. Substituir `u = U_E(1−k)` por `u = U_E·d_K/max(q_K,ε)`.
3. Adicionar piso de risco: `R_r = R_c(1−Aa) + σ R_c`.
4. Penalizar só déficits em `T` (usar `min(d_i,d_j)`).
5. Alinhar vocabulário de decisão em um único SKOS e ligar a matriz de decisão (Table 7).
6. Declarar na ontologia todos os parâmetros quantitativos com faixas.
7. Trocar `sh:maxCount 1` em `projectsToCoreVertex` por `hasProjectionWeight` com `Σβ=1`.
8. Renormalizar ou abandonar o simplex no corpus (hoje Σρ ≈ 2–3).

---

## 11. Riscos

| Risco | Mitigação |
|---|---|
| Tetraedro percebido como metáfora decorativa | Reenquadrar como lattice de faces; provar invariantes; remover claims não testáveis |
| Corpus sintético ≠ evidência | Declarar limites; adicionar gold seed e painel; separar "validação de coerência formal" de "validação empírica" |
| Inflación de facetas | Regra de parada (observável + política + criticidade) |
| Dependência de bibliotecas ausentes | Implementações numpy próprias para Sobol; property tests por fixtures |
| Overfitting aos pesos | Split cego + relatório de sensibilidade + versão congelada de pesos |
| Auto-referência do ground truth | Painel externo/humano e baselines explícitos |

---

## 12. Decisões que precisam de você

1. **Níveis independentes ou simplex estrito?** (recomendado: níveis independentes; tetraedro como forma/perfil de ênfase e índice relacional)
2. **26 facetas** (24 + W6 Legitimidade + K8 Aprendibilidade)?
3. **Compartilhamento β normalizado** (`Σβ=1`) ou contribuições não normalizadas?
4. **Ground truth:** há avaliadores humanos para os 120 casos gold? Se não, aceito painel LLM heterogéneo documentado como substituto, com limitação declarada?
5. **Quanto do PDF do tetraedro** manter: só o lattice de faces e invariantes (recomendado) ou também energia/mínima ação como apêndice exploratório?
6. **Alvo editorial** (venue, limite de páginas, idioma) — define o nível de formalismo e o tamanho do corpus.
7. **Reutilizar ou regenerar o corpus v2?** Recomendo regenerar: os números atuais são consequência dos defeitos formais.

---

## Anexo A — Auditoria ontológica verificada (Tarefa 4, evidência dura)

**A1. Sintaxe e namespaces.** Os 24 arquivos TTL parseam sem erro com rdflib 7.6.0 (soma de triples: core 52, analysis 37, efr 292, wcmk-facets 541, bridge-wcmkplus 161, derived 87, bridge-arch-v2 37, bridge-v0.9 27, ethsvc-llm 47, assessment 25, profile 21, instance 14; shapes: core 14, analysis 10, efr 149, wcmk-facets 311, assessment 18, profile 10, instance 10, ethsvc 22).
Três famílias incompatíveis de namespace: `https://eth2.local/ontology/*` (legacy), `https://ethwcmk.org/ontology/{wcmk-facets, bridge, bridge-wcmkplus-derived, ethcase-facet-requirements}` (draft rico) e `https://eth2.ai/ontology/{bridge, ethsvc-llm}#` (huésped en `eth_wcmk_bridge_v0_9.ttl`). `BridgeEvaluation` existe bajo tres IRIs distintos (`eth2.local`, `eth2.ai`, `ethwcmk.org/bridge#BridgeConfrontation` + `...derived#DerivedBridgeConfrontation`): cuatro clases de "evaluación de bridge" sin alineación. `EthicalCase` aparece en dos IRIs.
Prefijo `rdf:` mal escrito (`http://www.w3.org/1999-02-22-rdf-syntax-ns#`, con guiones) en 6 archivos; nombres locales vacíos (`brg:`, `prov:` en `owl:imports`). Consecuencia real: `FacetDefinitionShape` usa `sh:path rdf:type` + `sh:hasValue owl:Class` apuntando al IRI roto → **la约束 de tipo nunca dispara**.

**A2. Las formas SHACL vivas son solo dos.** `ethcase-facet-requirements.shacl.ttl` y `wcmk-facets.shacl.ttl`. Los seis shapes legacy apuntan a clases `arch:` (definidas en ninguna parte) → inertes; pyshacl devuelve `Conforms: True` contra datos reales. **No existe SHACL para la capa bridge** (`bridge-wcmkplus`, `-derived`): en el ejemplo inválido pasan sin violación `derivedResidualRisk "1.20"`, `requirementCoverageScore "1.20"`, `comparedFacetCount "-2"`, `localWeight "1.20"`, `localCriticality "urgent"`, `recommendedAction "OPEN"`.
Lo que sí se enforce: `requirementCoverage [0,1]`; `derivedRequirementCount ≥ 1` con SPARQL de igualdad de conteo; `minimumRequiredLevel/baseRequiredLevel/derivedWeight/severityFloor/domainBaseWeight [0,1]`; `prudentialDelta [0,0.5]`; déficit = max(0, required − observed) con tolerancia 1e-6; `criticalityLevel sh:in ("critical","high","medium","low")`; ≥24 assessments con ≥5 Want/≥6 Can/≥6 Must/≥7 Know; dos avisos de score < 0,20. **Ningún archivo contiene una restricción de suma** (`grep sum|Σ|normaliz` → 0 coincidencias): ni pesos a 1, ni simplex, ni normalización de scores. No hay `owl:inverseOf`, `owl:FunctionalProperty` ni `owl:maxCardinality` en ningún archivo.

**A3. Facetas como clases.** Las 24 facetas son `owl:Class`, no individuos, sin código (`skos:notation`), observables, pesos ni umbrales. Como son clases, todas las `sh:class wcmkf:Facet` fallan: **59 violaciones** en el ejemplo "válido" del bridge, 14 en el ejemplo "válido" de efr. El axioma `AllDisjointClasses` sobre Want/Can/Must/Know es vacuo, y `projectsToCoreVertex sh:maxCount 1` impide expresamente el reparto multi-pilar que la Tarea 3 pide.

**A4. La aritmética del ejemplo insignia no es derivable** (verificado con rdflib sobre `bridge-wcmkplus-scoring-example-valid.ttl`):
- Σ niveles observados 18,31; Σ requisitos 18,46; Σ pesos 19,20.
- Déficits por faceta: 10 de 24 facetas con déficit, Σ = **1,000** (media 0,0417, máximo 0,17).
- Déficits a nivel de pilar (media por pilar): Want 0, Can 0, Must 0,015, Know 0,073 → Σ = **0,088**.
- Déficits tras normalizar a participaciones: Σ = **0,028**.
- Valor declarado: `aggregateDeficit = 0,21`, `Aa = 0,77` (⇒ 1 − Aa = 0,23), `Aa* = 0,74`, `residualRisk = 0,19`.
Solo dos cifras son coherentes: `Aa* = Aa − coveragePenalty` (0,77 − 0,03 = 0,74) y `R_r = R_c(1 − Aa)` (0,82 × 0,23 = 0,1886 ≈ 0,19, que coincide con la Eq. 11). `aggregateDeficit = 0,21` **no se obtiene de ninguna combinación** de los datos declarados.
Inconsistencias internas: 3 comparaciones marcadas `isBlockingFacet` vs `blockingFacetCount 0`; 7 etiquetas "critical" vs `criticalDeficitCount 3`; `requirementCoverage 1,00` aunque solo 8 de 24 facetas son comparadas (`comparisonCoverageScore 0,33`); el perfil del agente **no declara `usesDomainProfile`**, violando su propia shape; `prudentialDelta = 0,04` uniforme bajo `PRUDENTIAL_MAXIMUM`; los déficits de las 8 comparaciones suman 0,88 (no 0,21).
Protecciones reales: solo avisos para `LegalObligation`, `PrudentialObligation`, `UncertaintyAwareness` y `SafeExecutability` — `Controllability`, declarada crítica en tres dominios, no tiene guard.

**A5. Contradicciones conceptuales detectadas.** (i) `SeverityBand`/`PrudentialMode` no tienen umbral numérico: la severidad se introduce por `severityFloor` y `prudentialDelta`, de modo que severidad y nivel requerido son el mismo escalar. (ii) Se afirma no-compensación para `ThresholdOverride` con `allowsCompensation false`, pero el vector de requisitos es absoluto (Σ 18,46) y ninguna regla lo aplica. (iii) `hasWeight` y `derivedWeight` conviven sin regla de autoridad. (iv) Los dominios de perfil están duplicados entre efr y wcmk-facets; `PrivacyData` y `InformationMedia` no tienen ninguna faceta crítica; `EducationDomainProfile` está declarada pero no es referida por ninguna regla. (v) `requirementCoverage` tiene dos significados incompatibles (proporción de facetas cubiertas vs. adequación del vector).

**A6. Correcciones mínimas para v1.0 de la ontología** (alimentan el gate G4): un único namespace de caso; facetas como individuos con esquema de código; `owl:inverseOf` y `owl:FunctionalProperty` donde haya relación uno-a-uno; SHACL para la capa bridge con decimales acotados [0,1] y `decisionRegion` ligada al vocabulario SKOS; reglas SPARQL que *deriven* `aggregateDeficit`, `blockingFacetCount`, `criticalDeficitCount` y `Aa*` (en lugar de declararlos como literales); y decisión explícita: normalizar los requisitos o declararlos como niveles absolutos por faceta (recomendado: absolutos, con saliencia λ normalizada).
