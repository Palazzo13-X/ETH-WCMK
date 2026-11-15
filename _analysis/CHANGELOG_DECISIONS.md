# ETH-WCMK — Decision log (registro de decisões de modelagem)

Formato: decisão · alternativa escolhida · justificação · artefato que a implementa · gate.

## Rodada 1 (27–28/10) — diagnósticos que viraram decisões

| ID | Decisão | Implementação | Gate |
|---|---|---|---|
| D0.1 | Pilares são **níveis independentes**, não shares de um simplex; o tetraedro indexa relações (face-lattice), não métrica de estado | `formal_core/core.py` (nível ℓ_p, forma s_p, magnitude M) | G2 |
| D0.2 | Não-compensação via **déficit** `d_p = max(0, q_p − ℓ_p)` + veto lexicográfico | `confront()` em `core.py` | G2 |
| D0.3 | Risco residual **nunca zera**: `R_r = R_c(1−Aa) + σ(E)R_c` | Eq.12, `prudential_floor()` | G2 |
| D0.4 | Tensão estrutural sobre déficits (S₂, S₃, S₄) com hierarquia S₄ ≤ S₃ ≤ S₂ ≤ max d | `structural_terms()`, bound em `Calibration.is_valid()` | G2 |
| D0.5 | Facetas podem ser compartilhadas com pesos β (Σβ=1) e não devem ser duplamente contadas | `project()`, teste I8 | G3 |
| D0.6 | Corpus degenerado (Aa=1 em 32,9%) regenerado | `Evaluacoes/r2/corpus_v3_*` | G5 |
| D0.7 | SHACL v1 era inerte (`shapes_graph=`); reescrito com `shacl_graph=` | `ontology_v2/shapes/` | G4 |

## Rodada 3 (02/11) — decisões aprovadas pelo autor

| ID | Questão | Escolha do autor | Consequência de engenharia |
|---|---|---|---|
| D3.1 | Ground truth | **Híbrido**: rubric rules anchored in external normative instruments + heterogeneous adjudication panel + human-anchored subset (~120 cases) | `_analysis/ground_truth/anchor_gold.py`; κ reported separately for each layer |
| D3.2 | Corpus | **Dual**: camada A (stress paramétrico, 1.200 casos v3 reetiquetados) + camada B (300–400 casos semânticos completos) | `_analysis/corpus/gen_corpus_v4.py` |
| D3.3 | Facetas | Aceitar **26–28** e compartilhamento até **3 pilares** (Σβ=1 por faceta) | `facet_registry.py` v11: 28 facetas, até 3 pilares |
| D3.4 | Tetraedro | **Manter** S₂, S₃, S₄ como penalidades estruturais | mantidas em Eq.10; ablation quantifica o contributo (gate: ΔAa ≥ 0.01) |
| D3.5 | Profilagem | **Rodar** B6 com LLMs locais reais | `_analysis/batteries/b6_llm_profile.py` (ollama) |
| D3.6 | Domínios | **13** (10 do catálogo + TS, RS, DS), justificados no paper | `facet_registry.DOMAINS` |

## Decisions taken during execução (auto-documentadas)

| ID | Decisão | Motivo |
|---|---|---|
| D3.7 | Políticas de agregação (`weighted_mean`, `guarded_weighted_mean`, `threshold_override`, `uncertainty_penalized_mean`) passam a ser **implementadas** no núcleo | P0.3: ontologia e código divergiam |
| D3.8 | `Profile.confidence` entra na aritmética como penalidade de incerteza por faceta | P1.5 |
| D3.9 | Adicionadas duas facetas: **M7 Proportionality & redress** e **C7 Containment & reversibility capacity** | Lacunas: proporcionalidade e capacidade de reversão não representadas |

| D3.10 | **Veto em granularidade de faceta** (`d^guard_p`, E11a) | A média de pilar dilui uma guarda violada: com 28 facetas o hard veto disparava em 1,5% dos confrontos. Artefato: `core._adequacy`, testes I14, I18 |
| D3.11 | **Gap material crítico** (E11b–E11c): máx. gap entre facetas críticas do domínio ou guardadas | O não-compensação do modelo não podia operar a nível de pilar; implementado como `material_gap`, `critical_prohibit_gap` |
| D3.12 | **Veto proporcional ao risco** (E11d–E11e): `w_cap = 0.5 + 0.5·stakes`, `λ(E) = 1 + 2·max(0,(stakes_min−stakes)/stakes_min)` | Um gap crítico nunca é average-away, mas um breach de baixa stake não prohibitiona automaticamente. Testes I23–I26. (Versão inicial com `absolute_hard_deficit = 0.75` foi removida por tornar a modulação inerte.) |
| D3.13 | **Proibição exige concentração** (E13c, `prohibit_needs_material`) | Déficit difuso = problema de competência → REVIEW/guards; proibição categórica só com dever crítico do domínio. Teste I27 |
| D3.14 | **Ground truth = um kernel normativo + três lentes corretivas** | Painéis independentes "puros" divergiam (κ 0.04–0.29). Kernel compartilhado + correções (escalation, prudential budget, instrument rules) → κ pairwise médio **0.839** (calibrado em grade de 1,77 M combos, `Evaluacoes/r3/gold_rubric_calibration.json`) |
| D3.15 | **Calibração do ladder separada da calibração estrutural** | Grade B5′ sobre 82.944 (v1) e ~3 M (v2) combinações, otimizando κ + concordância de intenção − colapso de classes; θ e λ não foram ajustados nesta etapa (limitação declarada) |
| D3.16 | **Parâmetros fitted congelados** em `Evaluacoes/r3/ladder_calibration.json` e carregados pelo corpus e pela bateria B1 via `load_fitted_calibration()` | Reproducibilidade: todo número do paper traça a um artefato |

## Rodada 4 (04/11) — decisões aprovadas pelo autor

| ID | Questão | Escolha do autor | Consequência de engenharia |
|---|---|---|---|
| D4.1 | Termo celular S₄ | **Corrigir** (recomendação): S₄ = min_p d_p (t-norm de Gödel), não a média geométrica | `core.structural_terms`, `geometry.hierarchical_bound`; prova por exaustão I7b (grid 21⁴ + 200 k vetores aleatórios). A hierarquia S₄ ≤ S₃ ≤ S₂ ≤ max d passa a ser teorema, não postulado |
| D4.2 | Risco residual | **Independente de Aa**: R_r = R_c·(p_fail+σ)/(1+σ), p_fail = 1 − Σ μ_p ℓ_p, μ=(0.15,0.40,0.20,0.25) | Eq. 12 reescrita; piso σR_c/(1+σ) nunca apagado; testes I2, I3, I28 (bucket de adequacy × dispersão de ratio), I29 (witness Aa igual, risco distinto) |
| D4.3 | Guardas não-compensatórias | **Sim**: toda faceta guardada limita o nível do pilar ao nível observado dessa faceta | `project()` cap universal; testes I18, I33 (9 guardas × pilares β>0) |
| D4.4 | Tetraedro | **Índice relacional** (mantido como penalidade estrutural, mas com contribuição medida por ablação ancorada) | gate G4/G6: ΔAa(S₂,S₃,S₄) reportado contra ground truth, não contra o próprio modelo |
| D4.5 | Ground truth humano | **Não** — painel LLM heterogêneo declarado como limitação | κ humano não é gate; limitação redigida na Seção de Validade; âncora = adjudicação por rubrica + painel, com auditoria amostral |
| D4.6 | Profilagem LLM | **Rodar** B6 com os GGUFs locais | `_analysis/batteries/b6_llm_profile.py` contra `../models/qwen36-UD-Q4_K_XL` e `../mtp/mtp-q2_0.gguf` |
| D4.7 | Nº de facetas | **28** mantidas, com revisão de duplicatas na Tarefa 3 | `facet_registry_v11.csv` é a fonte única; TTL e Python derivam dela |
| D4.8 | Camada B do corpus | Definida por cobertura de templates, não por volume nominal | 320 narrativas existentes re-equilibradas; gate: ≥ 12 domínios × 6 padrões de conflito × 4 severidades |
| D4.9 | Instanciação da ontologia | **Instanciar o corpus** (casos + confrontações representativas), não as 74.480 | ≥ 100.000 triplos; espelho aritmético em 100 casos aleatórios |
| D4.10 | Publicação | Confirmado (venue/formato da v12) | paper/ v12 com artefatos r4 |
| D4.11 | Abstenção epistêmica | Nova regra E29: dever contestado + U_E ≥ 0.60 + ℓ_K ≤ 0.65 ⇒ ABSTAIN | `core.confront`, teste I31; corrige o fato de ABSTAIN nunca disparar (0/74.480) |
| D4.12 | Histerese de decisão | E13d: veredito não afrouxa se Aa < bar + 0.05; endurecer sempre é permitido | `core.decide(previous=...)`, teste I30; corrige flip-flop de B12 |
| D4.13 | Horizon entra nos stakes | S(E) = 0.45·sev + 0.30·irr + 0.15·prud + 0.10·horizon (Σ = 1) | P0.9: o horizonte aparecia só na barra, não no risco; gold panels passam a importar `case_stakes` (fonte única) |

## Rodada 4 — resultados medidos (e correções de números anteriores)

| Achado | Nº verificado | Artefato | Consequência |
|---|---|---|---|
| Delta v11 → v12 sobre o corpus r3 (72.960 confrontações re-avaliadas) | 33.800 vereditos mudam (46,3%); maior classe PROHIBIT→REVIEW_REQUIRED (20.858) | `Evaluacoes/r4/delta_v12.json` | Todos os números da rodada 3 no paper estão invalidados; precisam de re-ancoragem |
| Contraexemplo S₄ | d=(0.5,0.4,0.3,0.2): S₂=0.2667, S₃=0.2250, S₄(geom)=0.3310 > S₃ | `delta_v12.json`, teste I7b | Hierarquia era falsa; corrigida e provada |
| Invariantes | 51 testes passando (41 invariantes + 10 geometria) | `_analysis/formal_core/tests/` | Gate G1′/G2′ vencido |
| Guardas universais | 9 guardas;probe C3=0 → nível C = 0 (antes 0.929) | `delta_v12.json`, I33 | Não-compensação efetiva |
| Sensibilidade (B10, v12) | S₁: λ_C 0.462 ± 0.017; ρ 0.330 ± 0.021; ω 0.086; δ 0.084; η 0.043; γ 0.043; α_dev 0.018; β_dev 0.027. θ e μ_C estatisticamente indistinguidos de zero | `Evaluacoes/r4/B10_sobol.json` | O valor 0.6085 citado como "λ_C" na r3 era na verdade **θ_C** mal rotulado; os índices total (ST) nunca foram calculados na r3. Correção obrigatória no paper |
| Probes adversariais (B8) | 1.420 probes, 5.223 asserções, 100% passing (5 famílias: não-compensação 972, déficit crítico 112, monotonicidade 84, abstención 112, histerese 140) | `Evaluacoes/r4/B8_probes.json` | Gate G3′ vencido |
| Baselines (B7) | κ do modelo vs gold (test holdout r3): 0.2156 | `Evaluacoes/r4/B7_baselines.json` | B7 nunca rodou antes (NameError) |
| Fit do ladder (B5′) | κ baseline 0.222 (train) / 0.271 (test) → 0.279 / 0.269 com parâmetros fitted | `Evaluacoes/r4/B5_ladder_fit_v12.json`, `ladder_calibration_v12.json` | O ajuste de limiares rende +0.05 κ; a discordância estrutural (REVIEW vs PROHIBIT) não se resolve por limiares |
| Corpus v5 | 1.520 casos (1.200 A + 320 B), 120 personas (cap de entrega 0.95, 24 tipos com déficit concentrado), 183.920 confrontações; Aa ≥ 0.999: 0% (era 20,6%); ABSTAIN dispara 9.342 vezes (era 0) | `Evaluacoes/r4/corpus_v5_*` | Saturação de personas eliminada (P1) |
| Discordância modelo–gold | κ = 0.2035, agreement 0.4997; confusão dominante: modelo REVIEW / gold PROHIBIT (53.431 pares = 29%) | `Evaluacoes/r4/corpus_v5_confrontations.jsonl` (re-computado por `verify_kappa.py`) | O `-0.4823` reportado pelo coverage v5 é um erro de contagem do relatório; o valor real é +0.2035 |
| Facetas (Tarefa 3) | 28 facetas; 18 tocam 3 pilares, nenhuma toca 4; 22 pares com β quase idênticos; campo `weight` inerte (28/28 = 1.0); λ ≠ massa de β (desvio 0.12); crítica média por domínio: SA 111 vs IM 66 | `Evaluacoes/r4/facet_review_stats.json`, `_analysis/FACET_REVIEW_v12.md` | Decisões D4.14–D4.19 propostas, ainda não aplicadas |

## Rodada 4 — decisões de engenharia aplicadas (D4.20–D4.22)

| ID | Questão | Decisão | Justificação mensurável |
|---|---|---|---|
| D4.20 | Âncora de facetas para deveres procedurais | **Ampliar o canon de 28 para 33 facetas**: M8 Transparency & notice β=(0,0.2,0.5,0.3) guarda 0.50; M9 Human review channel β=(0,0.3,0.7,0) guarda 0.50; M10 Consent & participation β=(0.4,0,0.6,0) guarda 0.50; C8 Data minimisation β=(0,0.5,0.5,0); K9 Periodic review & sunset β=(0,0,0.4,0.6) | `corpus_v5_confusion_analysis.json`: 75,81% da discordância modelo↔painel (REVIEW vs PROHIBIT) vinha de fatos procedurais que nenhuma faceta observava. Regras do painel sem âncora: B5 sunset 21.096, C10 notice 15.864, A5/C2 revisão humana 16.732/12.518, C1 minimização 14.526, C5 consentimento 7.282. `facet_registry_v12.csv` (33 linhas, R1–R6 verificadas; 51→58 testes) |
| D4.21 | Níveis declarados vs observáveis | **E30 (fact grounding)**: ℓ_f ← min(ℓ_f, q_f·c(fato)), com fatores de conformidade declarados; strength s ∈ [0,1] para análise de sensibilidade | κ modelo↔painel sobre as *mesmas* observações: s=0 → 0.198; s=0.5 → 0.221; s=0.75 → 0.262; s=1.0 → 0.390 (`Evaluacoes/r4/fact_grounding_sweep.json`). Testes G1–G7 em `tests/test_fact_grounding.py` |
| D4.22 | Independência dos fatos do desenho do caso | **Fatos procedurais correlacionados ao arquétipo** (maturidade processual P: A1 0.30 … A6 0.85) | Corpus anterior: A6 "aligned & resourced" sem salvaguardas procedurais → PROHIBIT do painel; a região ALLOW/AWG estava vazia e limitava o κ achievable. Corpus v6: todos os gates PASS, κ 0.383 |

**Efeito combinado (corpus v6, 183.920 confrontações, painel recalibrado sobre as mesmas observações):**
κ modelo↔consenso = **0.383**, agreement 0.777 (v5, sem grounding: κ 0.2035, agreement 0.4997).
Distribuição do consenso: PROHIBIT 147.607 (80,2%), REVIEW 20.830, AWG 2.553, ALLOW 2.161, ABSTAIN 10.769.
Distribuição do modelo: PROHIBIT 141.313, REVIEW 27.615, ABSTAIN 14.703, AWG 288, ALLOW 1.
κ interno do painel (A–B 0.256, A–C 0.524, B–C 0.201) — o κ do modelo (0.383) está dentro da
discordância normativa entre as próprias lentes; essa é a limitação central declarada na Seção de Validade.

## Rodada 4 — decisões de engenharia aplicadas (D4.23–D4.27)

**D4.23 — K9 é inerte; M8/M9 carregam conteúdo.** Ablação das cinco facetas
procedurais (45.600 pares, mesmo gold, mesma calibração):
`Evaluacoes/r4/procedural_facet_ablation.json`. κ full (33) = 0,4031; sem as 5 (28)
= 0,3760 (Δ = −0,027). Individual: M9 −0,0079, M8 −0,0041, M10 −0,0017, C8 −0,0011,
K9 **+0,0011**. Conclusão: o efeito conjunto é real, mas modesto; K9 não melhora a
concordância e é candidata a ser removida ou rebaixada a observabilidade de segundo
nível. Foi mantida no canon (sem guarda) porque a exigência de revisão temporal é
observável no corpus (`sunset_review`) — mas o paper deve declarar que seu efeito
medido é nulo.

**D4.24 — As variantes estruturais da escada são empiricamente inertas.** Com os
parâmetros ajustados, "veto precisa de gap material" produz **0** mudanças de
veredicto em 183.920 pares, e "banda de stakes para o veto" produz 65 (train) e 4
(test). Fonte: `Evaluacoes/r4/B5_ladder_fit_v12.json` → `structural_variants`.
Decisão: retirar essas cláusulas do paper como mecanismos, ou declará-las e admitir
que não alteram o comportamento observável (Occam).

**D4.25 — Compartilhar β entre pilares é essencial, não decorativo.** Ablação
`Evaluacoes/r4/B11_shared_beta.json` (corpus v6, ladder ajustado, 183.920 pares):
full κ = 0,4681; one-hot β (cada faceta contribui só ao pilar dominante) κ = 0,1870
(Δ = −0,2811); guardas totais (floor 0,35·requisito, não-compensação universal)
κ = 0,4343 (Δ = −0,0338). Ou seja: a estrutura tetraédrica explica ~0,28 de κ; e a
não-compensação absoluta é pior que o equilíbrio atual entre compensação e guardas.
Isto contradiz o resultado de r3 (B11 afirmava que remover β compartilhada *melhorava*
κ em +0,188): aquele número vinha de um gold por caso e de um recálculo sem
grounding; com canon e gold corretos, a direção se inverte.

**D4.26 — Convenção de calibração: congelada vs ajustada.** `load_fitted_calibration()`
usa o ladder congelado de r3, salvo passagem explícita de caminho ou
`ETH_WCMK_CALIB=fitted`. Razão metodológica: o gold do corpus é computado com o ladder
declarado/congelado, de modo que as etiquetas normativas do painel não dependem de
limiares ajustados sobre os mesmos dados. As baterias de ajuste (B5, B7, B13) usam
`ladder_calibration_v12.json` e são reportadas separadamente.

**D4.27 — O ajuste de limiares transfere (G7′ superado no sentido forte).**
`Evaluacoes/r4/B13_transfer_v12.json`: κ holdout (TB, TS, RS, DS) ajustado = **0,4834**
contra 0,4618 dentro da amostra de ajuste — gap de transferência **−0,0215** (o modelo
generaliza melhor fora dos domínios de ajuste). Nas 320 narrativas da camada B,
κ = 0,6617 contra 0,3745 com o ladder declarado. Nenhum domínio melhora com o ladder
declarado. `B7_baselines_v12.json`: nos domínios holdout, o modelo alcança κ = 0,4834
e o melhor baseline trivial (Aa sem cap de veto) κ = 0,1464 → margem **+0,337**.
Corrige-se assim o achado severo de r3 ("um baseline de um número empata o modelo"):
esse empate era produto da degeneração de Aa e do gold por caso; com facetas
procedurais, grounding E30 e gold por (caso, persona), a distância é mais de três
vezes o baseline.

## Rodada 4 — decisões de design avaliadas (D4.28)

Experimento de guardas e criticidade (`Evaluacoes/r4/guard_experiment.json`,
183.920 pares, mesmo gold, mesmo ladder ajustado, níveis armazenados com ancoragem E30):

| Variante | κ | Δκ | Concordância | Aa média |
|---|---|---|---|---|
| full (canon v12) | 0,4681 | 0 | 0,8308 | 0,2886 |
| guardas em K1 e K3 (floor 0,50) | 0,4639 | −0,0042 | 0,8322 | 0,2852 |
| guardas em **todas** as facetas K | 0,1234 | −0,3447 | 0,4140 | 0,5575 |
| sem K9 | 0,4672 | −0,0009 | 0,8304 | 0,2910 |
| criticidade TB/TS/IM +0,10 (D4.18) | 0,4718 | **+0,0037** | 0,8340 | 0,2622 |

Decisões:
* **D4.15 rejeitada como mecanismo aritmético.**
  A guarda em K1/K3 não paga: κ cai 0,004. A abstenção epistémica (E29) já cobre o
  caso que a guarda pretendia resolver; duplicá-la introduz um cap que empobrece a
  discriminação. Mantém-se apenas como recomendação de observabilidade (o caso deve
  declarar se normas e evidências estão identificadas), não como restrição dura.
* **Estender as guardas a todo o pilar K é destrutivo**: κ desaba a 0,12. É a
  evidência mais forte de que a não-compensação deve ser selectiva (deveres
  categóricos), nunca universal.
* **D4.18 (registrada como candidata)**: elevar a criticidade de Trabalho (TB),
  Transporte (TS) e Media (IM) ao nível de Saúde/Justiça melhora κ (+0,0037) e a
  concordância (+0,0032). Exige regenerar o corpus e re-validar R1–R6 e I1–I33 antes de
  entrar como canon. **Decisão final nesta rodada (ver D4.18 mais abaixo): não
  incorporada ao canon v12** — o ganho está abaixo da resolução do instrumento.
* **K9**: removê-la custa 0,0009 de κ. Efeito neutro; mantém-se por coerência
  ontológica e declara-se expressamente sua contribuição nula medida (D4.23).

---

## Rodada 4 (08/11) — decisões de ontologia e canon aplicadas

* **D4.28 (nova, aplicada) — semântica de delegação E28.** Um `ChainLink` delega
  os pilares que o delegado *pode* exercer (`W,C,M,K` na camada system; `C,K` na
  camada model/component) e declara `criticalDutyDelegated` e `retainedPillar`.
  Justificação: a regra anterior (`delegated = critical_pillars ∩ allowed`) emitia
  links vazios quando os pilares críticos eram {M,W}, o que é uma representação
  incoerente de "delegação". O achado medido é real e reportável: **268 de 4.560
  links (5,9%)** retêm o dever crítico na camada delegante. Gate formal: todo link
  declara ao menos um pilar e nenhum link delega um pilar proibido ao delegado
  (0 violações no corpus inteiro).
* **D4.29 (nova, aplicada) — expansão do cânone deôntico.** 31 rótulos de
  instrumentos citados pelo corpus não had mapping into the 39-instrument canon;
  23 instrumentos novos tipados + aliases para rótulos compostos. Critério:
  todo caso do corpus deve ter pelo menos uma norma tipada (`hasNorm` minCount 1).
  Conflitos de norma gerados: 82 → **88**.
* **D4.17 (decidida e aplicada) — remoção do campo `weight`.** Inerte em 33/33
  facetas (=1,0). Removido de `FacetDef`, da agregação (`level_i = Σβ_i v_i / Σβ_i`),
  do cap de guarda (`w = crit`), do CSV do registro e de qualquer forma SHACL.
  Regressão: 6.000 confrontações recomputadas sem o campo reproduzem os veredictos
  gravados em `corpus_v6_confrontations.jsonl` com **0 divergências**; `pytest`
  continua verde (I8 reformulada: duplicar uma faceta compartilhada não altera os
  níveis porque numerator e denominator escalam igual). Occam, não optimisation.
* **D4.16 (decidida, sem mudança de canon).** 22 pares de facetas com vetores β a
  distância < 0,12 são conservados: a separação é semântica (facetas distintas
  ancoradas em instrumentos e observáveis distintos). Justificação empírica: a
  ablação de facet individual já está medida (guard_experiment) e nenhuma das
  duplas quase-idênticas produz ganho de κ ao ser fundida; fundir reduziria o
  canon de 33 para 11–13 facetas e quebraria R3 (β ≥ 0,15) por renormalização.
  Registrado como achado de parcimónia, não como defeito.
* **D4.24 (decidida, declarada).** As variantes estruturais "veto exige gap
  material" (0 flips) e "banda de stakes" (65/183.920 flips) são declaradas
  **inertes** no paper e removidas das equações canônicas; ficam como probe de
  robustez (B8), não como mecanismo.
* **D4.18 (mantida como pendente bloqueada).** O efeito é positivo (+0,0037 κ),
  mas exigir regeneração completa do corpus v6 esbarra em `load_fitted_calibration`
  que rejeita o ladder ajustado (`material_gap` ≥ `critical_prohibit_gap`). Sem
  regeneração não há re-validação de R1–R6/I1–I33, logo D4.18 **não entra** como
  canon nesta rodada. Decisão honesta: declarar o resultado como experimento
  (guard_experiment) e não como canon.
* **G4′: PASS.** Corpus inteiro (37.985 indivíduos, 2.015.070 triplos validados em
  13 chunks) sem nenhuma violação SHACL; 76/76 fixtures inválidos detectados e
  atribuídos à forma correta; 33/33 verificações SPARQL aprovadas; espelho
  aritmético 1,63 × 10⁻¹² com 0 divergências de veredicto; censo do retículo
  15/15; registry check 0 divergências. Artefatos:
  `Evaluacoes/r4/ontology_v4_validation.json`,
  `Evaluacoes/r4/ontology_full_validation.json`.

* **D4.30 (nova, aplicada) — o veredito da cadeia não substitui o veredito do caso.**
  B15 mostra que, sob a regra de capacidade por pilar, a cadeia com o *melhor* delegado
  disponível não altera nenhum veredito (0 mudanças) e, com o *pior* delegado, altera 127
  (121 mais restritivos). O veredito da cadeia pessimista concorda com o gold do perfil
  executor (κ 0,4067) melhor do que o veredito do declarante concorda com o seu próprio
  gold (κ 0,372). Decisão: o veredito canônico continua sendo o da camada accountable
  (quem responde pelo dever), e a cadeia é reportada como **banda de robustez**
  `[Aa(chain, melhor delegado), Aa(chain, pior delegado)]`, não como decisão única.
  Justificação: trocar o veredito pela cadeia duplicaria a punição (o déficit do delegado
  já está embutido nos requisitos do caso) e quebraria I22 (a cadeia não pode piorar o
  veredito de forma não auditável).

* **D4.31 (nova, aplicada) — os termos estruturais do retículo não melhoram a
  concordância (B16).** Ablação multiplicativa de γ (arestas, S₂), η (faces, S₃) e ω
  (célula, S₄) sobre os 183.920 pares, mesmo gold e mesma calibração ajustada:
  κ full 0,4681; sem S₂ 0,4678 (Δ −0,0003); sem S₃ 0,4686 (Δ +0,0005); sem S₄ 0,4688
  (Δ +0,0007); sem estrutura nenhuma 0,4688 (Δ +0,0007). A Aa média sobe de 0,2886 para
  0,3827 quando a geometria é removida: a geometria aperta o veredito em média 0,094 de
  adequação, mas não acrescenta informação normativa mensurável. Decisão: manter
  S₂/S₃/S₄ como dispositivos de auditabilidade (D3.4), declarar explicitamente que a
  contribuição empiricamente medida à concordância é ~0, e não reclamar valor normativo
  para eles. Artefato: `Evaluacoes/r4/B16_structural_ablation.json`.

* **D4.32 (nova, aplicada) — κ não é um número único e isso passa a ser parte do
  resultado.** `kappa_by_consensus.json` estratifica por consenso do painel: unânime
  (87.134 pares) κ 0,6955; maioria (84.563) 0,1368; contestado (12.223) 0,0547. O teto
  estrutural é a discordância entre as próprias lentes (A–B 0,2557, A–C 0,5237,
  B–C 0,2012). Decisão: reportar κ por estrato e declarar o teto, em vez de promover
  um agregado que mistura um estrato resolvível com um estrato onde as tradições
  normativas divergem de fato. G7′ (κ ≥ 0,60 único) permanece marcada como não
  atingida.

* **D4.33 (nova, aplicada) — espelho aritmético padronizado em 403 confrontações.**
  O tamanho da amostra do espelho era uma variável de ambiente (`MIRROR_N`, default 100).
  Passa a 403 por default (toda confrontação instanciada na amostra estratificada), de
  modo que o número citado no paper é reproduzível sem flags especiais. Medido: diff
  máximo absoluto 1,6309 × 10⁻¹² e 0 divergências de veredicto nas três comparações
  (ladder Python ↔ RDF, `core.decide` ↔ RDF, ladder Python ↔ `core.decide`). Artefato:
  `Evaluacoes/r4/ontology_v4_validation.json` (`mirror`, `verdict_agreement`).

* **D4.34 (nova, aplicada) — E31 formalizada.** A histerese da escada (E13d) estava
  implementada e testada (I13, B8: 165 probes, B12: 6.382 transições bloqueadas, 103
  oscilações A–B–A) mas não aparecia como equação numerada. Entra como **E31** no SPEC
  e em `paper/equations.py`; os 31 arquivos MathML e PNG são regenerados a partir de
  `equations.py` por `_analysis/paper/regen_equations.py`, com verificação de parse XML
  (31/31 ok). Também se corrigiu E26 (conjunto de veto e proporcionalidade do veto duro)
  e E28 (regra de capacidade por pilar), que não coincidian com o código.

* **D4.35 (nova, aplicada) — censo deôntico declarado.** O módulo `03_deontic.ttl`
  contém 62 instrumentos tipados, 123 normas, 88 conflitos, 73 obrigações, 26 permissões
  e 24 proibições. A limitação do SPEC que falava de "35 strings" foi substituída por
  esse censo verificável.

* **D4.36 (nova, aplicada) — artefato de estatística do canon regenerado.**
  `facet_review_stats.json` (28 facetas, campo `weight` presente) foi substituído por
  `Evaluacoes/r4/facet_review_stats_v12.json`, gerado por
  `_analysis/analysis/facet_review_stats_v12.py` a partir de `formal_core/facet_registry.py`.
  Números vigentes: 33 facetas, 12/25/28/19 tocando W/C/M/K, 19 facetas tri-pilares,
  13 bi-pilares, 1 uni-pilar, 0 quadripilares; massa de β por pilar (0,1652, 0,2864,
  0,3424, 0,2061) vs λ (0,30, 0,25, 0,25, 0,20) → desvio máximo 0,1348; 12 guardas
  (3W/8C/12M/8K); criticidade média por faceta 3,0909; 0 facetas com criticidade plana;
  0 violações de R3 (nenhuma β não-zero abaixo de 0,15). O paper cita apenas estes
  números.

* **D4.37 (nova, aplicada) — E26 testado artificialmente (B17).** O gate de abstenção
  por cobertura nunca dispara no corpus porque todos os perfis estão completos. Em vez
  de retirar a claim, gerou-se um probe sistemático
  (`_analysis/analysis/b17_coverage_abstain.py`, 13.680 probes sobre 1.520 casos reais):
  a 0,70 de cobertura o ABSTAIN dispara em 100% dos casos; a 0,75, em 5,13%. A mesma
  bateria mostra que dropar as 8 facetas mais fracas do perfil eleva Aa média em +0,342
  (mediana 0,349, máximo 0,863) e torna 1.345 casos admissíveis. Conclusão registrada:
  o piso de cobertura 0,70 não é decorativo — é a única defesa contra autodeclaração
  seletiva. Permanece a lacuna: o corpus não tem casos genuinamente incompletos
  (Rodada 5).

* **D4.38 (nova, aplicada) — verificador de consistência paper ↔ artefato.**
  `_analysis/analysis/paper_artifact_consistency.py` lê 44 afirmações numéricas do
  paper, re-derive cada uma do artefato que deveria sustentá-la e reporta divergências
  (`Evaluacoes/r4/paper_consistency_check.json`). Resultado da rodada: **44 checks,
  0 divergências**. É a materialização da regra "nenhum número do paper vem de texto":
  se um artefato muda, o verificador acusa antes da publicação. Rodado como B18 pelo
  runner.

### D4.39 — Espelho aritmético do corpus inteiro (B19) — **aplicado** (08/11)
**Problema.** G4' exigía um espelho aritmético núcleo ↔ camada descritiva. O validador ontológico só
pode espejar as 403 confrontações presentes no grafo-amostra: o `instances.ttl` completo tem
1.888.317 triplos e a máquina (27 GB residentes no motor de inferência) não comporta o parse único.
**Decisão.** Separar duas questões que estavam misturadas: (i) *a serialização RDF reproduz a
aritmética?* — respondida pelo espelho graph ↔ core sobre o grafo-amostra, diff 1,63 × 10⁻¹²; (ii)
*todos os números do corpus são reproduzíveis pelo núcleo?* — respondida por `mirror_full_corpus.py`
sobre as **183.920** confrontações, reconstruindo cada perfil a partir de persona (fator, jitter,
teto de 0,95) + requisitos do caso + cap da E30 sobre os fatos declarados, e recomputando com
`confront()`.
**Medida.** Diferença máxima **0,0** em Aa, Aa_low, Aa_high, bar, stakes, R_r, S₂, S₃, S₄, Φ, u e gap
material; **0** divergências de veredito e **0** divergências de conjunto de veto; distribuição
recomputada idêntica à registrada (PROHIBIT 141.313 / REVIEW 27.615 / ABSTAIN 14.703 /
ALLOW_WITH_GUARDS 288 / ALLOW 1). Runtime registrado no manifest: 63,42 s.
**Artefato.** `Evaluacoes/r4/mirror_full_corpus.json`. Nota metodológica: usar os `facet_levels`
armazenados no JSONL como entrada do espelho **não** é fiel — estão arredondados a 4 decimais e
produzem divergências de até 1,7 × 10⁻² que atravessam floors de guarda. O espelho correto
reconstrói os níveis não arredondados antes de chamar o núcleo. Essa armadilha está documentada
no cabeçalho do script.

## Rodada 5 (v13) — decisões D5.x

* **D5.1 (aplicada) — hierarquia estrutural incondicional (Proposição 1).** Em v12, S₂ ≥ S₃ ≥ S₄
  só valia sob uma condição sobre α. Em v13 α não é mais um parâmetro livre: é a **marginal do
  retículo derivada de β**, α_e = (1/3) Σ_{f ⊃ e} β_f (`geometry.lattice_marginal_alpha`,
  `Calibration.__post_init__`). A hierarquia passa a ser teorema, não suposição. Validado
  numericamente sobre todo o grid {0,0.05,…,1}⁴ de déficits × quatro β (21⁴ combinações, I34):
  S₂ ≥ S₃ ≥ S₄ sempre, e `is_valid()` rejeita calibration incoherente (I35).
* **D5.2 (mecanismo aberto, ativação rejeitada) — λ(E).** O peso de saliência por caso
  λ_p(E) = λ_p q_p^s / Σ λ_p q_p^s. Com s = 0 (canônico) λ(E) ≡ λ, identidade exata (I37).
  Medido em B20 (1.080 casos × 120 personas, 130.680 pares): s=0.5 Δκ = 0.0000
  CI95 [−0.0001, 0.0001]; s=1.0 Δκ = −0.0001 CI95 [−0.0004, 0.0]; s=2.0 Δκ = −0.0003 CI95
  [−0.0007, −0.0001]. Não aumenta a concordância e reduz Aa média (0.358 → 0.354). Conclusão:
  o mecanismo permanece disponível como grau de liberdade declarativo, **s = 0 é o canônico**;
  qualquer ativação precisa de evidência futura.
* **D5.3 (diagnóstico mantido, termo ativo rejeitado) — exposição inter-pilar Ψ.**
  Ψ = média ponderada por σ_f = 1 − max_p β_fp dos déficits de deveres que atravessam pilares.
  Com ζ = 0 (canônico) a adequade de v13 é **exatamente** a de v12 (I39: diferença = ζΨ,
  e ζ=0 ⇒ diff 0.0). Medido: ζ=0.05 Δκ = −0.0028 CI95 [−0.0036, −0.0021]; ζ=0.10
  Δκ = −0.0059 CI95 [−0.007, −0.0049]. Ψ continua registrado no grafo e no JSONL como
  diagnóstico de governança (média 0,1839), mas não entra na decisão.
* **D5.4 (aplicada) — regime de supervisão derivado dos fatos declarados (E11c′).**
  `oversight_from_facts`: review + auditoria independente ⇒ `in_the_loop`; review ou canal de
  recurso ⇒ `on_the_loop`; nenhum ⇒ `none`; ausência de informação ⇒ `unspecified`
  (comportamento v12). Efeito medido em B20 full: Δκ = **+0.0078 CI95 [0.0057, 0.0100]**
  (n = 130.680; na amostra de 400 casos, +0.0114 CI95 [0.0080, 0.0146). Racionalidade
  material: um mecanismo de revisão humano verificado reduz a irreversibilidade efetiva do
  resultado (atenuação 0.45 em REVERSIBILITY) e é um requisito mínimo faltante em M9 quando
  não existe (REQ_MISSING_OVERSIGHT = 0.08). Ordem de stakes invariante: s_in ≤ s_on ≤ s_none (I38).
* **D5.5 (aplicada) — differentiation de β por âncora semântica.** Dez vetores alterados
  (W6, C2, C5, M2, M4, M10, K1, K2, K5, K7) respeitando R3 (Σβ = 1, ≤3 pilares não-zero,
  cada β > 0 ⇒ β ≥ 0.15). Efeito colateral medido: pares de facetas com vetores **idênticos**
  caíram de 22 para 1 (C3/C7 = (0,0.6,0.2,0.2), mantido deliberadamente: ambas são deveres
  de controle e rendição com participação M/K simétrica); census de aridade 1/13/19 → 1/10/22.
  Ganho mensurado: Δκ = +0.0019 CI95 [0.0009, 0.0032] isolado; +0.0094 CI95 [0.0069, 0.0120]
  combinado com D5.4. Adotado porque o ganho é pequeno, statisticamente resolvable, e corrige
  uma fraqueza estrutural documentada (D4.16: fundir facetas quase-duplicadas reduziria o
  cânon a 11–13 e violaria R3).
* **D5.6 (aplicada, não decisória) — ReviewNeed (E32).** Índice [0,1] = 0.30·banda +
  0.25·gap material low + 0.20·penalidade epistêmica + 0.25·(1 − cobertura), monotônico em
  cada componente (I36). Não altera a ladder (peso zero na decisão), mas materializa a
  obrigação de reavaliar: registrado em cada confrontação e na ontologia v4.2.
* **D5.7 (rejeitada) — rebalance de criticidade por domínio.** As três candidatas medidas em
  B20 pioram a concordância: agressiva Δκ = −0.0147 CI95 [−0.0179, −0.0116]; variante suave
  (cap 3) −0.0147; variante dirigida TB/TS/IM −0.0147/−0.0073. Massa por domínio atual
  (SA 131, JS 124, IC 114, FI 119, PD 114, GP 116, RS 95, TB 89, TS 88, DS 88, ED 86, MA 82, IM 80)
  é mantida como canônica.
* **D5.8 (aplicada) — gap de verificação no rubric (V1_verification_gap).** A bateria B17
  mostrou que o gate E26 nunca disparava porque todos os perfis eram completos (D4.37). Em v13
  o corpus inclui perfis genuinamente incompletos (6 tipos: blind por pilar W/C/K, boundary_low,
  sparse, minimal). Sem regra de rubric, os painéis tratavam dever não declarado como violação
  (κ = 0,0 na estrato abaixo do gate). Decisão: **defer** — um registro que omite >30% dos
  deveres que deveria avaliar não pode ser adjudicado; o veredito do kernel é ABSTAIN
  (V1_verification_gap), e o painel não vota. A alternativa "assume_breach" (comportamento v6)
  fica executable como sensibilidade e é reportada lado a lado.
* **D5.9 (aplicada) — E26′ correção do capping E30.** `grounded_levels` só aplica o teto a uma
  faceta **reportada**: `if code in out and out[code] > cap`. Ausência de reporte não é um nível
  zero Grounded; é cobertura faltante (D5.8). Sem isso, perfis parciais recebiam zeros artificiais
  (KeyError/C8 na geração v7).

* **D5.10 (aplicada) — congelação real de r4.** A re-verificação dos gates G0′–G9′ com o
  núcleo v13 reescreveu artefatos em `Evaluacoes/r4` (timestamps e ordenação de chaves).
  Como a regra do projeto exige que r2/r3/r4 sejam imutáveis, os arquivos originais foram
  restaurados via git e as re-execuções de v13 foram gravadas em `Evaluacoes/r5`
  (`mirror_full_corpus_v13.json`, `B8_probes_reverified.json`,
  `ontology_v4_validation_reverified.json`). As re-execuções reproduziram os mesmos
  vereditos (diff numérico 0,0; distribuição de decisões idêntica), o que constitui a
  evidência de que D5.1–D5.3 são inertes por default.

* **D5.11 (aplicada) — bug de representação nas shapes v6.** A validação SHACL do grafo
  completo reportava **1.520 violações** (exactamente uma por caso) em `sh:OversightCaseShape`.
  Causa: `sh:in ("eth:Oversight_unspecified" ...)` — literais string em lugar de IRIs. As
  instâncias usam `eth:Oversight_none` (IRI), logo nenhuma conformava. Corrigido em
  `gen_ontology_v6.py` (`sh:in (eth:Oversight_unspecified eth:Oversight_none ...)`) e re-emitido.
  Lesson registada: uma shape que nunca conforma é um erro de forma, não um achado normativo.

* **D5.12 (aplicada) — espelho aritmético do corpus v7 (B25).** `mirror_full_corpus_v13.py`
  recomputou as **220.400 confrontações** reconstruyendo níveis persona a persona (fatores,
  jitter, cap E30, `omit`, supervisão). Diff máximo **0,0** em todas as grandezas e **0**
  divergências de veredito (121,9 s). Condição G4′/G11′ fecha para v13. Nota de integridade:
  a primeira execução divergia (diff 0,58, 20.326 vereditos) porque omitia `oversight` e
  não respeitaba `omit` ao reconstruir os níveis — o divergente não era do modelo, era do
  espelho.

* **D5.13 (aplicada) — tolerância de bounds em `Calibration.is_valid()`.** A primeira
  execução de B23 invalidava 87/400 pontos do grid Morris porque `lo + (hi−lo)·3/3`
  produzía 0.10000000000000002. `is_valid()` aceita agora ε = 10⁻⁹ nos bounds de ζ, s,
  coverage_gate e oversight_attenuation. Sem essa correção, o artefato de sensibilidade
  estaria reportando índices de desenhos inválidos.

* **D5.14 (aplicada) — probes adversários re-executados contra o núcleo v13.**
  `run_battery_B8_v13.py` → `Evaluacoes/r5/B8_probes_reverified_v13.json`:
  **2.064 probes, 7.815 asserções, taxa 1,000**. Os probes não usam supervisão nem cobertura,
  e por isso o resultado é idêntico ao de r4 — o que era precisamente o que havia que
  demonstrar: Prop-1, λ(E) (s = 0), ReviewNeed e o gate declarado não alteram nenhuma
  asserção de não-compensação.

* **D5.15 (declarada, não executada) — âncora LLM local (B24).** O motor de inferência
  residente ocupa ~27 GB e o sistema entra em swap; uma chamada de teste ("ping") a
  `gemma4:12b-it-q4_K_M` não respondeu em 60 s. A bateria foi reescrita com warm-up explícito,
  parser tolerante (JSON estrito → pares `W1 0.4 0.7` por linha), duas tentativas e contagem
  de latência (`llm_anchor_v13.py`), e aborta declarando "local model unavailable" em vez de
  registar `json_validity_rate = 0.0` como se fosse resultado. Decisão: **não se usa nenhuma
  afirmação sobre auto-relato de LLM no paper v13**; a bateria fica pendente por limitação de
  máquina, não por falha de desenho.

* **D5.16 (aplicada) — κ reportado por estrato de consenso, corpus completo.**
  `_analysis/analysis/kappa_by_stratum.py` → `Evaluacoes/r5/kappa_by_stratum_v13.json`:
  **0,8167** no estrato unânime (112.179 pares), **0,1371** no de maioria (95.611),
  **0,0526** no contestado (12.610), κ global 0,5336. Lección metodológica: un κ único es
  una media ponderada de estratos que difieren por un factor de 16; el paper debe dar los
  tres números y el artefacto que los sostiene, no uno solo.

* **D5.17 (aplicada) — tres falsos fracasos del validador de ontología, no del modelo.**
  (a) La comprobación "el régimen de supervisión es el que implican los hechos" devolvía
  1.099 contradicciones porque miraba la *presencia* del nombre del hecho y no su
  `eth:factValue`: un hecho declarado y `false` no implica vigilancia. Corregido; 0
  contradicciones. (b) Las comparaciones numéricas en FILTER contra literales
  `"0.70"^^xsd:double` son sensibles al tipo en rdflib (xsd:decimal ≠ xsd:double a efectos
  de `!=`); las constantes canónicas ζ = 0, s = 0, gate = 0,70 se verifican ahora en Python
  con ε = 10⁻⁹. (c) Los checks con `kind: "finding"` (E28 retention: 268 enlaces) se
  marcaban como `pass = (rows == 0)`, convirtiendo un hallazgo declarado en un fallo de
  gate; ahora un finding se reporta con su conteo y no bloquea el gate. Un detector que
  confunde un hallazgo con una violación fabrica gates falsos.

* **D5.18 (aplicada) — coeficientes v13 declarados en todo individuo de calibración.**
  `gen_ontology_v6.py` emite el addendum (ζ, s, attenuación de supervisión, requisito
  faltante, pesos de ReviewNeed, coverage gate) para `cal:default_v12` **y**
  `cal:ladder_fit_v12`. Razón: un grafo donde algunos individuos declaran parámetros y
  otros no permite reproducir la aritmética solo "por suerte".

* **D5.19 (aplicada) — verificador paper ↔ artefactos.**
  `paper_artifact_consistency_v13.py` re-deriva cada afirmación numérica del paper desde el
  artefacto correspondiente y escribe `Evaluacoes/r5/paper_consistency_check_v13.json`. Es la
  versión automatizada de la regla del proyecto (ningún número viene de la prosa). Los
  primeros 32 "fallos" eran en su mayoría del verificador (patrones escritos en español cuando el paper está en portugués, signos
  negativos perdidos, artefacto equivocado para el número), no del paper: quedó corregido.

* **D5.20 (aplicada) — precisión de almacenamiento declarada, no asumida.** El espejo
  aritmético de la ontología fallaba el gate (`max diff ≤ 1e-6`) con 4,97e-05: el grafo
  guardaba `eth:reviewNeed` leído desde la fila del corpus, que `core.confront()` redondea
  a 4 decimales, mientras la escalera Python lo recalculaba en precisión completa. No era
  una divergencia del modelo, era una precisión no declarada. Corrección doble: (i)
  `gen_ontology_v6.py` emite ahora `reviewNeed` con la aritmética completa de la escalera
  — como cualquier otro literal; (ii) el validador declara explícitamente
  `MIRROR_TOLERANCE = 1e-6` y `STORAGE_PRECISION = {review_need: 1e-4, completeness: 1e-4}`,
  y registra cuántos excedentes de techo E30 (352 de 4.030, máximo 5e-05) quedan dentro de
  esa precisión. Resultado: **diff global 1,61e-12, gate G4′ PASS**. Lección: una
  tolerancia que no se declara se convierte en un supuesto oculto que más tarde aparece
  como "hallazgo".

* **D5.21 (aplicada) — el verificador paper ↔ artefactos sólo acepta un número si el
  texto lo sostiene en su contexto.** `paper_artifact_consistency_v13.py` ahora busca el
  valor del artefacto escrito en el paper con la precisión que el paper usa, y exige que
  aparezca en un pasaje que hable del asunto de la afirmación. Sin esa ancla contextual,
  un "0,0" suelto en la Proposición 1 "verificaba" un Δκ de −0,0013: el mismo error de
  D5.17 invertido (un detector que acepta coincidencias numéricas fabrica gates falsos).
  Veredicto final: **129 afirmaciones verificadas, 0 fallidas** (93 por patrón explícito,
  35 por valor anclado en contexto) → `Evaluacoes/r5/paper_consistency_check_v13.json`.

* **D5.22 (aplicada) — B24: constatación de inviabilidad, no suposición.** Se midió el
  estado de la máquina en vez de asumir la limitación: `strata-host` (PID 1425370) tiene
  25.930.740 KB de RSS sobre 30.951 MB totales; `ollama ps` muestra `ornith-1.5:9b` cargado
  (6,2 GB, 98% GPU) y aun así una generación de 60 tokens tarda **141,9 s** y el prompt
  completo de 33 facetas (2.370 caracteres, `num_predict` 1.400) supera 300 s sin devolver
  texto. `gemma4:12b-it-q4_K_M` no responde en 180 s. Decisión: B24 queda declarada no
  ejecutable en esta ronda, con el número de latencia en el gate report. Un gate que no se
  puede ejecutar se declara; no se rellena con un cero.

* **D5.23 (aplicada) — G18′, gate de rastreabilidad.** `paper_artifact_consistency_v13.py`
  verifica 149 afirmaciones numéricas del paper contra su artefacto (111 por patrón explícito,
  38 por valor anclado en el contexto del pasaje), 0 fallidas. El verificador incluye los
  tamaños de artefacto (308.466 bytes de módulos RDF, 64.242.382 bytes de instances.ttl,
  1.927.780 triplos validados) y el propio manifest (46 artefactos, 20 ejecuciones, 65,3 MB).

* **D5.22 (aplicada) — B24 declarada no ejecutable, con medición.** Se midió la máquina
  antes de concluir: `strata-host` (PID 1425370) tiene 25.930.740 KB de RSS sobre 30.951 MB
  totales; `ollama ps` muestra `ornith-1.5:9b` cargado (6,2 GB, 98% GPU) y aun así una
  generación de 60 tokens tarda **141,9 s** y el prompt completo de 33 facetas (2.370
  caracteres, `num_predict` 1.400) supera 300 s sin devolver texto; `gemma4:12b-it-q4_K_M`
  no responde en 180 s. El harness (`llm_anchor_v13.py`) usa ahora el endpoint de
  completación y un warm-up con timeout configurable, y aborta declarando la limitación.
  Lección: un gate que no se puede ejecutar se declara con su medición; no se rellena con
  un cero.

* **D5.24 (aplicada) — B26: el kappa depende del rubric, y eso se reporta.** Once variantes
  perturbadas sobre los 220.400 pares: κ 0,5336 → 0,5507 (pisos ×1,10), 0,5250 (×0,90), 0,5085
  (deberes categóricos = 3), 0,5461 (todos categóricos), 0,5223/0,3324/0,5147 (lente A/B/C sola),
  0,6005 (gate 0,80), 0,4907 (gate 0,60), 0,2974 (`assume_breach`). G7′ sigue sin considerarse
  alcanzado: la única variante que cruza 0,60 lo hace aumentando la abstención compartida, no
  la calidad del juicio. La sensibilidad dominante está en el tratamiento de lo no declarado
  (−0,2362) y en el gate de cobertura (±0,07/−0,04), no en los pisos de deber (±0,01).

* **D5.25 (aplicada) — lente B es la que más diverge del modelo** (κ modelo↔B = 0,3324 frente a
  0,5223 con A y 0,5147 con C). No se presenta como defecto ni como virtud: el núcleo está
  construido sobre deberes y límites, y la lente prudencial castiga esa asimetría. Queda
  medido, no defendido.

* **D5.26 (aplicada) — Cierre documental de la rodada 5: notación, citas y
  disponibilidad abierta.** Los dos entregables (`_analysis/PAPER_v14.docx`,
  inglés, y `_analysis/RELATORIO_TECNICO_CIENTIFICO_PT.docx`, portugués) se
  regeneraron desde `_analysis/paper/build_paper_v14.py` y
  `build_report_pt.py`, con el helper común `docx_build_v14.py` (carta,
  márgenes 1 in, Times New Roman 11 pt, ecuaciones OMML nativas, pie de página
  con número de página y propiedades del documento). Tres defectos cerrados:
  (1) la lista de referencias se había colapsado en un único párrafo — las 44
  entradas sin comas se concatenaban en una sola cadena; (2) ningún símbolo ni
  término metodológico se definía en su primera aparición, por lo que se insertó
  una tabla de notación (48 entradas) como Tabla 1 y se desplazó la numeración
  de las demás tablas; (3) el informe PT listaba 44 fuentes y solo una minoría
  aparecía en el cuerpo: ahora las 44 están citadas donde se hace la afirmación.
  Ambos documentos incluyen además una sección de disponibilidad abierta
  (código MIT, ontologías y corpus CC BY-SA 4.0, RDF en
  `Ontologias/ontology_v4_2/`, artefactos en `Evaluacoes/r5/`, rodadas r2 y r3
  solo lectura). Verificación final: 166/166 cifras rastreadas por
  `paper_artifact_consistency_v13.py`; 44 ecuaciones OMML; 7 figuras; 12 tablas
  en el paper y 19 en el informe; 28 y 31 páginas respectivamente; 44
  referencias autor-año citadas en el cuerpo de ambos textos.
