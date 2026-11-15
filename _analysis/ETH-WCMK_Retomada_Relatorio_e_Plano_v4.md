# ETH-WCMK — Retomada (Rodada 4 / alvo v12)
**Documento:** relatório de auditoria dos gates vencidos + plano de execução com gates e entregas.
**Data:** 03/11/2026 · **Base verificada:** `_analysis/formal_core/` (v11), `Ontologias/ontology_v3/`, `Evaluacoes/r2/`, `Evaluacoes/r3/`, `paper/figures/`.
**Status:** proposta para aprovação humana. Nenhuma alteração de código/corpus foi feita nesta rodada — apenas verificação read-only e reproducible.

---

## 1. Gates vencidos (evidência verificada agora)

| Gate (Plano v3) | Critério | Evidência verificada nesta sessão | Status |
|---|---|---|---|
| **G0′ Empaquetamento e trazabilidade** | README, requirements, decision log, spec de equações | `README.md` ✓, `requirements.txt` ✓, `CHANGELOG_DECISIONS.md` ✓, `SPEC_v11_equations.md` ✓ | ✅ (falta LICENSE, runner único, hashes, git) |
| **G1′ Núcleo formal completo** | E1–E26 implementadas, parâmetros declarados e validados | `core.py` (542 linhas) cobre E2, E3–E4, E5–E7, E8–E10, E11a–e, E12–E13c, E20–E23, E25–E26, E28 (agência em camada); `Calibration.is_valid()` rejeita calibração incoerente | ✅ |
| **G2′ Invariantes automatizadas** | ≥14 invariantes, 0 falha | `python3 -m pytest tests -q` → **34 testes passando** (I1–I27 + integridade do canon + validação de calibração), 15,5 s, Python 3.14.4 | ✅ (mas ver P0.1 abaixo: uma "prova" declarada é falsa) |
| **G3′ Canon de facetas** | 26–28 facetas, Σβ=1 por faceta, ≤3 pilares, guardas, criticidade, observável | `facet_registry_v11.csv`: **28 facetas** (24 do catálogo original + W6, C7, M7, K8); 14 `guarded_weighted_mean`, 7 `weighted_mean`, 5 `threshold_override`, 2 `uncertainty_penalized_mean`; **9 guardas duras**; 18 facetas em 3 pilares, 9 em 2, 1 em 1; 28/28 com observável | ✅ |
| **G4′ Ontologia v3 validada** | SHACL + SPARQL coerentes, espelho aritmético | 843 triplos; 0 violações SHACL; **20/20 consultas SPARQL** (V1–V20) passando; espelho aritmético Python↔RDF com diferença máxima 0,0 | ✅ (escopo muito pequeno: 1 caso instanciado) |
| **G5′ Corpus não-degenerado** | cobertura, densidade semântica, decisões | Camada A 1.200 casos + Camada B 320 casos narrativos (233–270 palavras, média 252); 48 personas; 74.480 confrontações; **28/28 facetas com ≥5 casos críticos**; 13 domínios × 8 padrões de conflito; narrativas com stakeholders, normas, consequências e evidências | ✅ (com ressalvas: Aa=1 em 10,4% das confrontações; PROHIBIT 60,2%) |
| **G6′ Sensibilidade e robustez** | Sobol/Morris, probes, ruído | B6 Sobol v11 (8.192 draws, ΣS₁ = 0,755; θ_C = 0,609 domina); B8 8/8 probes; B9 ruído: flip de decisão 9,5% com σ=0,02, 20,25% com σ=0,20; B11 ablation completa | ✅ (caveats metodológicos: sem índices de ordem total, ΣS₁ < 1) |
| **G7′ Ground truth com κ ≥ 0,60** | concordância do painel **e** do modelo com a âncora | Painel: κ_AB 0,81 · κ_AC 0,77 · κ_BC 0,93 (média 0,83) ✓. **Modelo × gold: κ = 0,227** (agente declarado), 0,415 (hold-out, B5), **0,0092 na grade de 48 personas** | ❌ **gate não atingido** |
| **G8′ Paper v10/v12** | documento com trazabilidade | **Não existe.** Existem só ativos: 18 equações (MathML/PDF/PNG) em `paper/figures/mathml/`, 7 figuras (`fig1_face_lattice` … `fig7_criticality`), e o draft antigo `ETH-WCMK v9.docx` | ❌ |
| **G9′ Release reproduzível** | clone limpo → todos os números | Sem `run_all_batteries.py`, sem LICENSE, sem hashes de corpus, sem git | ❌ |

**Baterias existentes:** B1 (invariantes, r2/r3), B2 (embutida na validação da ontologia), B3 (sweep de calibração, r2), B4 (Sobol/Morris legado, r2), B5 (fit do ladder, r3), B6 (sensibilidade v11, r3), B8 (probes, r3), B9 (ruído, r3), B11 (ablation, r3), B12 (estabilidade temporal, r3). **Não executadas:** B7 (baselines —脚本 existe, sem resultado), B10 (robustez adversarial), profilagem real por LLM local (D3.5, B6 real), B13 (transferência entre domínios).

---

## 2. Falhas críticas novas, verificadas nesta rodada (P0)

**P0.1 — A hierarquia estrutural declarada é falsa.** A SPEC e o docstring de `geometry.py` afirmam `S₄ ≤ S₃ ≤ S₂ ≤ max d`. Contra-exemplo: `d = (0.5, 0.4, 0.3, 0.2)` → `S₂ = 0.2667`, `S₃ = 0.2250`, `S₄ = 0.3310`. Varredura de 10⁴ vetores de déficit (grade 0,1–1,0): **9.991 de 10.000 violam `S₄ ≤ S₃`**. O teste I7 verifica apenas `S₂ ≤ max d`, `S₃ ≤ S₂` e `S₄ ≤ max d` — portanto a "prova" nunca foi testada. Conceito: a média geométrica dos déficits não é um "déficit conjunto" (não é um t-norm monotônico em |S|).

**P0.2 — O risco residual é uma reparametrização do score, não uma medida independente.** Por construção, `R_r/R_c = 1 − Aa + σ(E)` exatamente. Logo a "rota do ratio" na escada de decisão (ratio_prohibit 0,70 / ratio_review 0,45 / ratio_guards 0,25) é apenas um limiar sobre `Aa` com constantes diferentes da rota do bar — as duas rotas podem conflitar e não acrescentam informação. Um modelo de risco ético precisa de risco que dependa de **exposição, magnitude de dano e probabilidade de falha**, não só da adequade.

**P0.3 — A calibração fitted nunca é carregada.** `load_fitted_calibration()` está quebrada (`NameError: name 'os' is not defined` — `os`, `json` e `dataclasses.fields` não são importados) **e nenhuma bateria ou gerador de corpus a chama**. Todas as baterias usam `default_calibration()` ou um `Calibration(...)` hardcoded. Conclusão: `Evaluacoes/r3/ladder_calibration.json` (objective 0,5387, grid 5.971.968) e `gold_rubric_calibration.json` são **artefatos órfãos**. A decisão D3.16 do changelog ("parâmetros fitted congelados e carregados pelo corpus e pela bateria B1") não está operationalizada.

**P0.4 — O tetraedro é decorativo na aritmética.** `S₂`, `S₃`, `S₄` são funções simétricas apenas do vetor de déficits `d`, com pesos uniformes (1/6, 1/4) e média geométrica; nenhum constante métrica do simplex (aresta √(8/3), inraio, volume) entra em qualquer cálculo. Ablation B11: remover toda a camada estrutural muda `Aa` em média **0,0125** e altera a decisão em **5,7%** dos casos (κ 0,889 vs. modelo completo). É defensável manter o tetraedro como **índice relacional** (face-lattice, 15 slots) — mas o paper deve dizer isso e medir o ganho incremental contra um gold ancorado, não apenas contra si mesmo.

**P0.5 — Ground truth circular e escalarmente inconsistente.** Painel κ = 0,83 internamente, mas o modelo concorda apenas κ ≈ 0,23–0,45 com ele, e κ ≈ 0,009 na grade de personas. Distribuição de decisão diverge fortemente: modelo **PROHIBIT 60,2%** × consenso do painel **PROHIBIT ~20%** (REVIEW 70%). Enquanto isso não fechar, nenhuma afirmação de "validação" pode aparecer no paper.

**P0.6 — O gold é por caso, não por confrontação (erro de categoria na B1).** Em `corpus_v4_confrontations.jsonl` (74.480 linhas) a campo `gold` é **idêntico para todas as personas de um mesmo caso**: 1.520 casos → 1 veredicto cada, replicado nas 49 linhas de persona. Por isso a "grade de 48 personas" tem κ = 0,0092: compara agentes diferentes (níveis de faceta variados) contra um veredicto derivado do perfil *declarado*. Correlação de `Aa` com o rank do gold na grade = **0,014**; correlação de `Aa` com a decisão do modelo = **0,683**. Ou seja, o modelo responde ao agente; a rubric não. O "teste discriminante" anunciado no docstring de `model_vs_gold.py` não existe até que o painel adjudique cada par (caso × persona).

**P0.7 — Compensação dentro do pilar.** `ℓ_p` é média ponderada dos valores de faceta; guardas só "capam" o nível quando a política é `guarded_weighted_mean`. Exemplo medido: `C3 = 0` (controllability, guarda 0,55, política `threshold_override`) → nível C = **0,929**; `M1 = 0` (guarda 0,60) → nível M = **0,907**. Ou seja, deveres críticos continuam diluídos por facetas saudáveis; o veto corrige a decisão, mas o score continua compensatório.

**P0.8 — Estabilidade temporal.** B12: 20 casos × 8 passos, **0,35 flips de decisão por caso** (máximo 2), com oscillação explícita (ETHCASE-0001: PROHIBIT→...→ALLOW→REVIEW...). Não existe hysteresis nem memória de estado.

**P0.9 — Lacunas conceituais.** (i) `stakes` não inclui horizonte temporal nem padrão de conflito; (ii) `r_f` é derivado de criticidade/severidade, **não** das normas listadas — os 15 instrumentos normativos (`03_deontic.ttl`) não operam na aritmética; (iii) o modelo avalia **capacidade de agência**, não permisibilidade de um ato específico; (iv) perfis são auto-relatados, sem protocolo de verificação independente (exceto o campo `confidence`).

**P0.10 — A "independência" dos painéis gold é retórica e há feedback loop fechado.** 54,5% (830/1.520) dos veredictos saem do kernel comum sem que nenhuma lente A/B/C dispare; spread = 0 em 83,5% dos casos. Pior: o `design_intent` de cada caso é definido por regras ARCH derivadas dos próprios requisitos do modelo (`gen_corpus_v4.py:126-135`), e tanto `calibrate_gold.py` (objetivo 0,40κ + 0,30·intent + 0,15·unanimidade − 0,25·colapso) quanto `calibrate_ladder.py:219-225` (0,50κ + 0,30·intent + …) otimizam concordância contra rótulos produzidos pela aritmética que se quer validar. Painel e escada se calibram um contra o outro.
**P0.11 — Os instrumentos normativos são decorativos.** `INSTRUMENTS` tem 35 strings (`gen_corpus_v4.py:53-67`); `case.norms` **nunca é lido** por nenhum painel. Apenas 4 regras operacionais existem (`gold_panels.py:152-161`: GDPR Art.5/25 → gap M1 > 0,25; Rio P1 → C7 > 0,40; ACM/IEEE 1.5 → M7 > 0,55; GDPR Art.22/ILO → M2 > 0,25). Belmont, Helsinki, UDHR, UN CRC, ISO 26262, FAIR, Paris, NIST CSF, HIPAA, WHO, DSA, due-process, FIS, OECD são texto decorativo.
**P0.12 — Âncora humana não existe.** `corpus_v4_human_anchor.csv` é um worksheet: 60 linhas (não 120), 180 células de rater **vazias**, sem κ inter-rater. Bug em `gen_corpus_v4.py:549` (`hard` e `easy` particionam todo o universo → o terceiro termo do `pool` é sempre vazio). 48/60 linhas são da camada A e trazem só a rationale de design (~49 caracteres) como "narrativa adjudicable". O `_analysis/ground_truth/anchor_gold.py` citado pelo README **não existe**.
**P0.13 — Degeneração de `Aa`: 20,6% das confrontações (15.362) têm adequacy central ≥ 0,999; exatamente 1,0000 em 5.331 (7,16%).** Causa: personas construídas como `level_f = req_f × factor_f` (`gen_corpus_v4.py:367-371, 401-412`); 11 das 48 células persona×tier têm factor ≥ 1 em todos os pilares (exemplary + solid = 98,8% dos casos saturados). Não é requisito baixo (req ∈ [0,59, 0,95], média 0,807) nem cobertura (28/28). A confiança observacional é quase inerte no modo central (`band_value` devolve `x`; só 2/28 facetas usam `uncertainty_penalized_mean`) → tiers "high/low confidence" saturam igualmente.
**P0.14 — Contradição interna de reporte:** entre os 15.362 com `adequacy` central ≥ 0,999, **1.239 são PROHIBIT e 1.941 REVIEW_REQUIRED**, porque a decisão usa `adequacy_low` (precaução) enquanto o campo reportado é o central. Um caso "Aa = 1,0 → PROHIBIT" é ininteligível e destrói a interpretabilidade do modelo. Banda Aa_low média 0,867, mínimo 0,287.
**P0.15 — Camada A é repetitiva e incompleta como desenho experimental:** apenas 936 combinações únicas (domínio × arquétipo × severidade × irreversibilidade) para 1.200 casos → 264 duplicatas; severidade "low" nunca aparece; o limiar do gate ("≥5 casos críticos por faceta") é trivial dado o mapa de criticidade; a contagem de cobertura considera só a camada A. ABSTAIN = **0** em 74.480 confrontações: a abstenção depende apenas de coverage, e os 32 casos deliberadamente ambíguos nunca a disparanm — o probe é inerte.
**P0.16 — Camada B é semanticamente rasa.** 320/320 narrativas têm stakeholders, consequência, norma, evidência e horizonte preenchidos, mas apenas 7 templates de consequência, 6 de vulnerabilidade e 13 listas de normas; **nenhuma parte do modelo nem do painel lê a narrativa** — a "densidade semântica" é cosmética.
**P0.17 — Bug de inventário de baterias.** `analysis/b7_baselines.py:174` usa `gold_test` nunca definido (NameError antes de escrever o JSON) → B7 não rodou. `robustness_battery.py:110-111` reporta "central" e "pessimistic" com o mesmo valor; as linhas 209-216 recalculam "pessimistic" como se fosse central. O artefato `B5_ladder_calibration.json` (grid_size 5.971.968) **não corresponde** ao script em disco (GRID1 = 995.328, faltam chaves de diagnostics) — resultado gerado por versão anterior do código. O README manda executar `_analysis/ground_truth/anchor_gold.py`, `run_battery_B4.py` e `run_battery_B8.py`, que não existem. Sobol/Morris está rotulado B6 enquanto o plano o chama B4.
**P0.18 — Inconsistência de calibração entre artefatos:** corpus e grade usam defaults v10 (`gen_corpus_v4.py:50-51`: bar_base 0,50, bar_severity 0,20, prohibit_stakes_min 0,60, needs_material True), enquanto B5/B7 usam `ladder_calibration.json` fitted (bar_base 0,55, bar_severity 0,10, prohibit_stakes_min 0,30, needs_material 0). O "unfitted reference v10" registrado em B5 dá prohibit_share 0,6738.

---

## 2.1 Correções imediatas (quick wins, antes de qualquer fase nova)

| # | Correção | Artefato | Esforço |
|---|---|---|---|
| Q1 | Fixar imports de `core.py` e ligar `load_fitted_calibration()` a todos os consumidores; calibração única declarada | `formal_core/core.py` | 1 h |
| Q2 | Reportar `Aa` na **mesma banda usada para decidir** (central e pessimista lado a lado) | `confront()` + appendices | 2 h |
| Q3 | Adjudicar gold por par (caso × persona) e reportar κ multinível/clusterado; headline κ só para o agente declarado | `gold_panels.py`, `model_vs_gold.py` | 4 h |
| Q4 | Eliminar saturação de personas (factor ≥ 1) e adicionar personas com déficits concentrados | `gen_corpus_v4.py` | 3 h |
| Q5 | Operacionalizar abstenção (ambiguidade de requisitos contraditórios → ABSTAIN) | `core.confront()` | 2 h |
| Q6 | Escrever as regras dos instrumentos normativos (≥15) como predicados executáveis, ou remover a lista e declarar decoratividade | `gold_panels.py` + `03_deontic.ttl` | 6 h |
| Q7 | `run_all_batteries.py` + hashes SHA-256 + LICENSE + git | raiz | 3 h |
| Q8 | Corrigir B7 (NameError) e B8 (central/pessimistic duplicado); regenerar artefatos | scripts | 2 h |
| Q9 | Corrigir o prefixo `rdfs:` nos 6 módulos da ontologia (1 linha em `gen_ontology_v3.py:44`) | `Ontologias/ontology_v3/*.ttl` | 1 h |
| Q10 | Sincronizar K8 (CSV ↔ registro Python ↔ TTL) e regenerar `facet_registry_summary.json` e `criticality_matrix_v10.csv` | `_analysis/facets/` | 2 h |
| Q11 | Normalizar os pesos do face-lattice em RDF (soma = 1) e instanciar S₂, S₃, S₄ por confrontação | `gen_ontology_v3.py` | 4 h |
| Q12 | Estender o espelho aritmético: comparar structuralTerm, déficits e decisão, ler todos os 44 parâmetros do TTL, e derivar `Aa`, `D` e `R_r` por SPARQL (SPEC §8 exige) | `validate_ontology_v3.py` | 6 h |

**P0.19 — A camada ontológica v3 é uma fachada, não uma ontologia.** 843 triplos, 97 indivíduos, **0 axiomas DL** (0 `subClassOf`, 0 `disjointWith`, 0 `FunctionalProperty`, 0 `inverseOf`/`transitive`/`symmetric`, 0 `sh:Rule`, inferência desligada). É um regresso formal frente a v2 (13 → 3 shapes, 59 → 17 constraints, 73 → 0 FunctionalProperty, 12 → 0 disjointWith, 84 → 0 domain/range). Bug verificado: `@prefix rdfs: <http://www.w3.org/2000/01/rdf-syntax-ns#>` em **todos** os 6 módulos (`gen_ontology_v3.py:44`) — os 22 triplos de domain/range resolvem para termos inexistentes, logo toda a tipagem é inerte. Cinco tipos usados sem declaração de classe (Pillar, Decision, AggregationPolicy, SeverityBand, Reversibility); 7 classes sem nenhum indivíduo (Norm, Justification, ProportionalityClaim, DelegationChain, Profile, PillarLevel, FacetObservation); 28 referências `policy_*` apontam para indivíduos `Policy_*` que não coincidem → nenhuma política de agregação é identificável em RDF; `Layer_model` duplicado.
**P0.20 — A aritmética não está na ontologia.** S₃ e S₄ não existem em RDF; só um `structuralTerm = 0,2137` (= S₂). Déficits, stakes, piso prudencial, coeficientes de requisito (E27), limiar ABSTAIN, banda de incerteza e a escada de decisão não são representados. Os 15 slots do face-lattice têm `structuralWeight` somando **2,030002** (vértices 0, arestas 0,166667, faces 0,25, célula 0,03 = ω) — não é uma distribuição normalizada e não corresponde a `structural_terms()`. O "arithmetic mirror" compara 112 β + 5 escalares de **uma única instância**; `structuralTerm` é lido mas nunca confrontado; α e β_face são hardcoded no validador; só 24 dos 44 parâmetros são efetivamente espelhados. V14 (RDF) testa γ+η+ω+ρ = 0,30 ≤ 0,35 enquanto `core.py` exige γ+η+ω+ρ+δ ≤ 0,35 — o check RDF é **mais fraco** que o invariante do código.
**P0.21 — Semântica deôntica nominal.** 0 indivíduos `Norm`; 7 `NormConflict` com apenas um string `conflictPattern`; 0 predicados de obrigação/proibição/permissibilidade/prioridade/resolução; 0 regras. Não se pode escrever — quanto menos detectar — uma contradição obrigação ∧ proibição sobre a mesma ação. Os 20 checks SPARQL que passam são todos estruturais, nenhum deôntico.
**P0.22 — Instância de corpus inexistente em RDF.** 1 de 74.480 confrontações existe como indivíduo. Classes Stakeholder, Consequence, Evidence, Vulnerability, Domain não existem em v3 (existiam declaradas em v1, com 0 instâncias). O único RDF de corpus (r2, 22.200 triplos) tem 0 Confrontation, 0 Decision, 0 Stakeholder/Norm/Consequence/Evidence.
**P0.23 — Divergências de dados verificadas:** K8 tem β (0,15; 0,35; 0; 0,5) no registro Python/TTL e (0,1; 0,4; 0; 0,5) na CSV canônica — a CSV viola a própria regra "β ≥ 0,15"; `criticality_matrix_v10.csv` (26 linhas) e `facet_registry_summary.json` (26 facetas, 7 guardas) estão desatualizados frente a v11 (28 facetas, 9 guardas); `prohibitNeedsMaterial` é emitido como `xsd:integer 0` no TTL e tratado como `True` no validador; arestas 0,166667 vs 0,166666667 → ΔS₂ = 4,27e-10 sem teste que compare o termo estrutural.

---

## 2.2 Implicação direta para a Tarefa 4

A ontologia atual **não sustenta** a afirmação de "capa semântica formal" do modelo. O que existe é: (i) um dicionário controlado de 28 facetas com β, guardas e criticidade; (ii) uma lista de 15 instrumentos normativos como rótulos; (iii) um espelho aritmético de um caso exemplar. Para F4, o trabalho não é "ampliar" v3: é reconstruir sobre v2 (formalmente mais rica) e adicionar o que falta.

---

## 3. Pontos de refinamento (P1/P2)

1. Sobol sem ordem total e ΣS₁ = 0,755: vários índices = 0,000 (λ, γ, η, ω, ρ, δ) — provavelmente artefato de amostragem ou de variância condicional mal especificada. Precisamos de `S_T` e índices de interação.
2. Redundância conceitual de facetas: 6 facetas de obrigação (M1–M6), 4 de conhecimento (K1, K2, K5, K7), 3 de contenção/executabilidade (C3, C6, C7), 3 de intenção (W1, W4, W6). Sem análise formal de solapamento, o canon se torna inflacionário.
3. Lacunas de cobertura externa: fairness/não-discriminação, privacidade, explicabilidade/transparência, supervisão humana robusta, sustentabilidade ambiental, dignidade/direitos.
4. β uniforme entre domínios é hipótese não testada (a matriz de criticidade já é por domínio; λ não é).
5. Interpretabilidade: `confront()` já devolve `worst_pillar`, `worst_facet`, `top_facet_deficits` — falta uma explicação estruturada (por que PROHIBIT, qual aresta, qual guarda) e um formato de "justification object" para auditoria.
6. Corpus: camada A (1.200) tem requisitos gerados por fórmula; precisa ser reetiquetada com `requirement_for()` (que existe no núcleo, mas o gerador usa valores hardcoded na camada A).
7. Reproducibilidade: seeds declaradas, mas sem hashes, sem runner, sem git.

---

## 4. Plano de execução (Rodada 4), com gates e entregas

> Regra: nenhum gate passa sem artefato verificável + comando de verificação. Fase N+1 não começa sem gate N assinado.

### F0. Congelamento e higiene (pré-requisito) — 2–4 h
**Entregas:** `git init` + commit inicial; `MANIFEST.json` com SHA-256 de corpus/registros/validações; `run_all_batteries.py`; correção dos imports de `core.py`; `AUDIT_v12.md` (este relatório expandido, com evidência linha a linha).
**Gate G0′:** `pytest tests -q` verde (34 testes) e `run_all_batteries.py` regenera todos os artefatos r4 idempotentemente.

### F1. Avaliação crítica do modelo (Tarefa 1) — 1–2 dias
**Entregas:** tabela **afirmação → formalização → teste → evidência** para as 11 asserções centrais (4 pilares, tetraedro, não-compensação, risco não-zero, veto lexicográfico, ground truth, ontologia, corpus, sensibilidade, escalonamento, aplicabilidade); lista de asserções *descritivas* a remover do abstract; declaração de escopo ("modelo de avaliação de capacidade de agência ética, não de permisibilidade ato-a-ato").
**Gate G1′:** 100% das asserções classificadas; cada uma com artefato ou标记 como descritiva.

### F2. Revisão matemática (Tarefa 2) — 3–5 dias
**Entregas:**
1. **Reformulação dos déficits conjuntos:** substituir `S₄ = (∏d)^{1/4}` por uma definição monotônica em |S| (min por subconjunto, ou Möbius-residual sobre o face-lattice com clip), com prova de `S₄ ≤ S₃ ≤ S₂ ≤ S₁ ≤ max d`; varredura exaustiva (10⁶ pontos) provando ausência de contra-exemplos.
2. **Risco independente:** `R_r = H(E) · p(fail | ℓ, C, K, E) · (1 + irreversibility weight)`, com `H(E)` = dano esperado (stakes × nº de afetados × severidade) e `p(fail)` derivada de déficits de capacidade e robustez. Prova de não-redundância: existem dois perfis com mesma `Aa` e `R_r` diferente (teste explícito).
3. **Escada de decisão com hysteresis:** transição só se a folga for ≥ ε, e memória do estado anterior; invariantes de monotonicidade temporal (anti-flip).
4. **Guardas não-compensatórias de verdade:** cap/override aplicados a todas as facetas guardadas, não só a `guarded_weighted_mean`; novo invariante "guarda violada ⇒ nível do pilar ≤ guarda".
5. **Incerteza:** banda `[Aa_low, Aa_high]` já implementada; propagar ao risco e à decisão; teste de monotonicidade em confiança.
6. **Sobol de ordem total** com ≥ 16.384 draws + índices de interação, e **ablation contra gold ancorado** (não só contra o modelo completo).
**Gate G2′:** ≥ 42 invariantes passando (I1–I27 + novas); 0 contra-exemplos na varredura; ΣS₁ ≥ 0,90 com ordem total reportada; Δ da decisão (com/sem camada estrutural) medido contra o gold, com decisão documentada de manter ou remover cada termo.

### F3. Revisão das 24 facetas (Tarefa 3) — 4–6 dias
**Entregas:**
1. **Mapa 24 → 28** (mantidas/renomeadas/divididas/mescladas/adicionadas) com justificativa por faceta.
2. **Matriz de redundância** (similaridade semântica pairwise das 28 definidas por definição + observável) e decisão de merge/split; alvo final **24–28** com defesa explícita do número.
3. **Matriz de cobertura externa** contra 6 referenciais: Beauchamp–Childress (4 princípios), EU AI Act (requisitos de alto risco), ACM/IEEE codes, Floridi (5), OECD (10), Belmont/GDPR/HIPAA. Métrica de cobertura ≥ 95%.
4. **Compartilhamento entre pilares:** até 3 pilares por faceta, Σβ = 1, regra anti-dupla-contagem provada (extensão de I8 a triplas).
5. **Observáveis:** cada faceta com 1–2 observáveis concretos, fonte de evidência e protocolo de medição; sem observável, fora do canon.
6. **β por domínio** (13 domínios) experimental, com validação estatística.
**Gate G3′:** cobertura ≥ 95% dos referenciais; cada faceta com observável e política implementada e testada; invariância à divisão de facetas (I8) para triplas; κ contra gold ancorado não piora.

### F4. Ontologia v4 + validação formal (Tarefa 4) — 4–7 dias
**Decisão de projeto:** v3 é um regresso formal frente a v2 (0 axiomas DL, 3 shapes, tipagem inerte por bug de prefixo). F4 deve **restaurar e estender v2**, não incrementar v3.
**Entregas:** namespaces unificados e versionados; hierarquia real de classes (`subClassOf`, `disjointWith`, cardinalidades, domain/range válidos); shapes SHACL **em arquivo** (não embutidas no validador) para `EthicalCase`, `AgencyProfile`, `Confrontation`, `Decision`, `Norm`, `ConflictResolution`; camada deôntica operationalizada (`Norm`, `Obligation`, `Prohibition`, `Permission`, `Defeasibility`, `ResolutionStrategy`, com `NormConflict` ligado tipadamente ao caso — não por igualdade de string); agência em camadas com `DelegationChain` e `FallbackPolicy` efetivamente usados; dinâmica temporal com trajetórias e hysteresis; **instanciar o corpus** (1.520 casos, personas, confrontações selecionadas) → ≥ 100.000 triplos; Stakeholder, Norm, Consequence, Evidence, Vulnerability como indivíduos; ≥ 30 consultas SPARQL de consistência, ≥ 5 delas deônticas; espelho aritmético em ≥ 100 casos aleatórios comparando `Aa`, `D`, `S₂`, `S₃`, `S₄`, déficits e decisão (error ≤ 1e-6); ≥ 25 fixtures inválidos, todos detectados e atribuíveis; mapa de herança v2 → v4.
**Gate G4′:** 0 violações em instâncias válidas; ≥ 25 violações nos inválidos; SPARQL reproduz `Aa`, `D`, `S₂`, `S₃`, `R_r` e a decisão de `core.py` a 1e-6 em 100 casos; pesos do face-lattice normalizados (soma = 1); β, guardas e criticidade idênticos entre CSV, registro Python e TTL para as 28 facetas; limitação de "sem razão DL" declarada e justificada.

### F5. Corpus ETHCASE v5 (Tarefa 5) — 6–10 dias
**Entregas:** Camada A (1.200, stress paramétrico, reetiquetada com `requirement_for()`); Camada B **400–600 casos ricos** (13 domínios ≥ 30 cada) com narrativa ≥ 250 palavras, stakeholders nomeados com vulnerabilidade, consequências esperadas e não-intencionadas, normas aplicáveis reais, evidências presentes e ausentes, irreversibilidade, horizonte, padrão de conflito, camada de agência, 10% deliberadamente ambíguos, 15% com auto-relato inflado (adversarial); split train/calibration/test congelado; variantes temporais (mesmo caso, t = 0..7).
**Gate G5′:** 0 casos sem stakeholders/normas/consequências/evidências; ≥ 8 padrões de conflito por domínio; ≥ 28/28 facetas com ≥ 5 casos críticos **contados sobre A+B**; duplicatas ≤ 5%; severidade "low" representada; degeneração `Aa = 1` < 3%; ABSTAIN efetivamente disparado nos casos ambíguos; narrativas com ≥ 20 templates de consequência/vulnerabilidade distintos; hashes publicados.

### F6. Ground truth v3 (condição para qualquer validação) — 8–12 dias
**Entregas:** rubrica ancorada nos instrumentos normativos (regras derivadas de GDPR Art. 22, Belmont, precaution, due process, ACM/IEEE, etc.); três lentes (deontológica, consequencialista, prudencial) com **entrada narrativa completa**, não vetores; sub-amostra âncora de 120–150 casos adjudicados (humanamente, se disponível; senão, protocolo LLM heterogêneo documentado e declarado como limitação); tie-break explícito (precaução vs. proporcionalidade) testável; calibração da bar contra a âncora; **corrigir o erro de categoria** da grade de personas (gold por persona, não por caso); **romper o feedback loop**: os rótulos de âncora não podem ser gerados por regras derivadas do próprio modelo (design intent), devem vir de texto normativo e de adjudicação independente; eliminar as personas saturadas e adjudicar gold para cada par (caso × persona).
**Gate G6′:** κ inter-painel ≥ 0,75; κ modelo–âncora ≥ 0,60; κ na grade (por persona, clusterado por caso) ≥ 0,60; estabilidade ante auto-relato otimista ≥ 0,90; share de veredictos oriundos só do kernel comum ≤ 40%. Enquanto não passar, o paper se posiciona como *framework formal + benchmark*, não instrumento validado.

### F7. Baterias ethcase × WCMK (Tarefa 6) — 5–8 dias
**Entregas:** suíte única: B1 invariantes · B2 SHACL · B3 sweep de calibração · B4 Sobol/Morris de ordem total · B5 fit do ladder (train/test congelado) · B6 profilagem real com os modelos GGUF locais (`qwen36-UD-Q4_K_XL`, `Q2_0`) — self-report vs. perfil verificado · B7 baselines (score linear, média simples, weighted-risk, veto-only) · B8 probes canônicos (210) · B9 ruído · **B10 robustez adversarial** (auto-relato inflado, prompt injection, evidence laundering) · B11 ablation (sem tetraedro, sem veto, sem β compartilhada, sem piso de risco, com S₄ corrigido) · B12 estabilidade temporal com hysteresis · **B13 transferência entre domínios**.
**Gate G7′:** todos os números com IC95; tabela comparativa v9 vs v12; nenhuma afirmação sem artefato; resultados em `Evaluacoes/r4/` (imutável).

### F8. Paper v12 (Tarefa 7) — 5–8 dias
**Entregas:** ~10.000 palavras EN: modelo, formalização (E1–E30 corrigidas e renderizadas), ontologia, corpus, resultados (B1–B13), **limitações declaradas** (geometria como indexação relacional, ausência de razão DL, ground truth de painéis ancorados em regras), figuras atualizadas, appendix com canon completo e estatísticas do corpus. Versões: Markdown fonte → DOCX → PDF.
**Gate G8′:** equação → função → figura → número rastreados; zero afirmação empírica sem artefato; revisão contra a carta de decisões de F1.

### F9. Release — 1–2 dias
**Entregas:** README raiz atualizado, requirements com versões pinadas, LICENSE, `Makefile`, hashes, dataset ETHCASE v5 publicável, CHANGELOG de decisões.
**Gate G9′:** clone limpo → `pytest` + `run_all_batteries.py` reproduzem todos os números citados no paper.

---

## 5. Ordem e estimativa

`F0 → F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9` · **34–54 dias úteis assistidos**.
**MVP crítico (≈ 14 dias):** F0 + F1 + F2 + F3 + F5 + F6-R1. Sem F6 não há afirmação de validação possível.

## 6. Decisões que precisam de sua aprovação antes de executar

| # | Questão | Recomendação |
|---|---|---|
| D1 | Corrigir `S₄` (min-based/Möbius) ou remover o termo célula? | Corrigir e provar; documentar o erro do texto original |
| D2 | Risco residual: manter como função de `Aa` ou tornar independente (dano × exposição × probabilidade)? | Tornar independente; exige adicionar campo `harm magnitude` e `exposure` ao caso |
| D3 | Guardas: cap/override para **todas** as facetas guardadas (fim da compensação)? | Sim — é a falha P0.7 |
| D4 | Tetraedro: penalidade estrutural ou índice relacional interpretativo? | Índice relacional + termos estruturais só se Δ mensurável contra gold ≥ 0,01 |
| D5 | Ground truth: humano disponível para ~120 casos? Se não, painel LLM heterogêneo declarado como limitação? | Preciso de sua decisão; sem isso o paper é "framework + benchmark" |
| D6 | Rodar B6 com os GGUF locais (qwen36-UD-Q4_K_XL / Q2_0)? | Sim, se houver tempo; caso contrário declarar B6 como simulação |
| D7 | Facetas alvo: 24, 26 ou 28? | Decidir após a matriz de redundância (F3), com defesa formal |
| D8 | Corpus v5: tamanho da Camada B (400? 600?) e domínio de partida | Sugerir 480 (13 × ~37) |
| D9 | Ontologia: instanciar todo o corpus (≥100k triplos) ou uma amostra estratificada (1.520 casos, confrontações selecionadas)? | Amostra estratificada + 100 confrontações espelho de alto valor |
| D10 | Idioma/venue e formato final do paper | Confirmar (EN, open access, DOCX + PDF) |
