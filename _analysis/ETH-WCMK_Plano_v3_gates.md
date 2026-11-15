# ETH-WCMK — Plano de execução v3 (Rodada 3)

**Versão:** 3.0 · **Data:** 02/11/2026 · **Escopo:** retomada a partir do estado verificado em `Evaluacoes/r2/`, `Ontologias/ontology_v2/` e `_analysis/formal_core/`.
**Status:** *proposta para avaliação humana — nada foi executado nesta rodada além da auditoria dos gates.*

---

## 0. Princípio de continuidade

A rodada anterior não produziu paper, mas produziu **matemática canônica, canon de facetas, ontologia validada e corpus de stress**. Este plano não recomeça: **reusa 100% dos artefatos verdes** e corrige exatamente onde o sistema falhou. Regra de não-regressão: nenhum artefato `r2` será apagado; as novas versões entram como `v11`/`v3` e o paper v10 é montado a partir dos ativos já renderizados (E1–E18, fig1–fig7).

**Reaproveitamento imediato (sem retrabalho):**

| Ativo | Onde | Reuso |
|---|---|---|
| Núcleo formal v10 | `_analysis/formal_core/core.py`, `geometry.py`, `facet_registry.py` | Base aritmética do paper e das baterias |
| 15 invariantes testables | `_analysis/formal_core/tests/test_invariants.py` (18 testes, 100% passando) | Kernel de validação permanente |
| Canon de 26 facetas + β + criticidade | `_analysis/facets/facet_registry_v10.csv`, `criticality_matrix_v10.csv` | Base do F3 (revisão de facetas) |
| Ontologia v2 (2.815 triplos) | `Ontologias/ontology_v2/` | Base do F4 (v3) |
| Corpus de stress 1.200×40 (14.400 confrontações) | `Evaluacoes/r2/corpus_v3_*` | Camada "stress paramétrico" do corpus v4 |
| Resultados B1, B3, B4, B8 | `Evaluacoes/r2/B*.json` | Seção de sensibilidade do paper |
| Figuras e equações | `paper/figures/` (7 figuras) + `paper/figures/mathml/{E1..E18}.{mathml,pdf}` | Seções de método do paper v10 |

---

## 1. Auditoria dos gates vencidos (evidência verificada nesta rodada)

| Gate (Plano v2) | Critério | Evidência verificada | Status |
|---|---|---|---|
| **G0** Manifesto e decisões de projeto | 6 decisões registradas | `manifest_r2.json` → representação (níveis independentes + forma tetraédrica), 26 facetas, β normalizada, gold *rule-based*, geometria *face-lattice only*, venue (periódico open access, EN, ~10.000 palavras, docx), corpus regenerado | ✅ |
| **G1** Núcleo formal v10 completo | equações implementadas + parâmetros declarados | `core.py` docstring mapeia Eq.1–11; `Calibration` declara λ, α, β, γ, η, ω, ρ, δ, θ, veto, bar | ✅ |
| **G2** Invariantes ≥14, automatizados e passando | ≥14 invariantes, 0 falha | I1–I15 + integridade do canon + validade de calibração = **18 testes, todos passing** (5,6 s). B1 v10: bounds ok, piso/teto de risco ok, monotonicidade 0 falhas, `Aa=1` 0%. Contraste com v9 publicada: 21,5% falhas de monotonicidade, 5,2% violações de piso | ✅ |
| **G3** Canon de facetas fixado com β e criticidade | 26 facetas, Σβ=1, matriz 26×13 | `facet_registry_v10.csv`: 26 facetas (18 compartilhadas de 2 pilares, 8 exclusivas), 7 hard guards, matriz 26×13 = 338 células; V1, V4, V13 passam | ✅ (com ressalva F3 abaixo) |
| **G4** Ontologia v2 validada | SHACL + SPARQL coerentes | 2.815 triplos; fixture válido 0 violações; fixture inválido 10 violações atribuíveis; V1–V17 passam; legacy v1 prova ser *inerte* (177 conformantes, shapes ignoradas por `shapes_graph=`) | ✅ (limitações: sem razão DL; policies inertes) |
| **G5** Corpus não-degenerado | Aa=1 <3%; veto em faixa; monotonicidade ≥95%; ≥120 perfis | Aa=1 em **0,03%** ✅; monotonicidade de severidade **100%** ✅; veto 25,45% ✅; 210 probes ✅; **perfis = 40** ❌; narrativas: **38 distintas** ❌; classes ETHCASE (stakeholders, consequências, normas, evidências) **sem instância** ❌ | ⚠️ parcialmente |
| **G6** Sensibilidade e robustez estrutural | Sobol + sweep + probes | B3 sweep ✅; B4 Sobol ✅ (θ = 0,799); B8 **210/210 probes** ✅ | ✅ (com caveat metodológico) |
| **G7** Gold com concordância κ ≥ 0,60 | κ modelo-consenso ≥ 0,60 | κ = **0,310** (consenso), 0,289 (A), 0,141 (B); κ intra-painel A↔B = **0,042**; B6 estabilidade de decisão ante otimismo de auto-relato = **0,475** | ❌ **falhou** |
| **G8** Paper v10 com trazabilidade | cada número vem de artefato | **Documento não existe.** Só ativos prontos (18 equações MathML/PDF, 7 figuras) | ❌ |
| **G9** Empaquetamento reproduzível | README, requirements, decision log, licença | Só `Ontologias/ontology_v2/README.md`; falta README-raiz, `requirements.txt`, decision log, e o `SPEC_v10_equations.md` citado por `core.py` mas ausente | ❌ |

**Leitura honesta:** G1–G4 e G6 estão verdes e são reutilizáveis. **G5 é verde só na aritmética**, não na semântica. **G7 é o gargalo real**: sem ground truth confiável, toda a validação empírica do modelo é frágil. G8/G9 ainda não começaram.

---

## 2. Pontos críticos identificados (novos, não cobertos pelos planos v1/v2)

### P0 — bloqueantes para a nova rodada

**P0.1 Ground truth circular e inconsistente.** Os painéis gold (A deontológico, B prudencial) consomem **os mesmos níveis de faceta e os mesmos requisitos** que o modelo consome, sem λ, β ou geometria; a concordância κ = 0,042 entre eles indica que as duas heurísticas divergem quase por completo, e o tie-break "menos permissivo" produz um consenso 65% PROHIBIT. Consequência: κ = 0,31 do modelo não significa validação, significa **semelhança parcial de heurísticas**.

**P0.2 Corpus sem densidade semântica.** 1.200 casos vêm de 38 fragmentos de narrativa (média 33 caracteres) e de requisitos derivados de uma fórmula (criticidade + severidade + modo prudencial + reversibilidade). Não existem stakeholders, consequências, normas aplicáveis, evidências, vulnerabilidades, horizonte temporal. As classes `Stakeholder`, `Consequence`, `EvidenceItem`, `Vulnerability`, `Norm` da ontologia **não têm um único indivíduo instanciado** — o "modelo semântico" nunca foi testado semanticamente.

**P0.3 Policies de agregação declaradas, mas inertes.** O canon e a ontologia declaram 4 políticas por faceta (`weighted_mean` 7, `guarded_weighted_mean` 13, `threshold_override` 4, `uncertainty_penalized_mean` 2). A função `project()` **implementa apenas o teto de guarda**; as demais políticas não afetam a aritmética. Isso quebra a afirmação central de "única fonte de truth entre RDF e Python".

**P0.4 Geometria com efeito marginal demonstrado.** Sobol: θ = 0,799; λ_C 0,062; λ_W 0,050; λ_M 0,044; γ 0,024; ω 0,013; η 0,011; ρ 0,007. Os termos estruturais (aresta/face/célula) explicam ~5% da variância; hard veto dispara em **1,47%** das confrontações. O tetraedro hoje é **indexação relacional legítima**, mas o paper precisa dizer isso explicitamente e medir o ganho incremental (Δ Aa com vs. sem S2/S3/S4).

### P1 — fragilidades conceituais/operacionais

**P1.5** `Profile.confidence` existe no schema e na ontologia, **não entra na aritmética** (nada propaga incerteza de observação para déficits nem para a decisão).
**P1.6** Calibração declarada (`05_calibration.ttl`) não é operacional: valores ficam hardcoded em `default_calibration()`; não há protocolo de calibração documentado nem re-calibração por domínio.
**P1.7** Ausência de **horizonte temporal** (imediatismo vs. consequência de longo prazo) e de **estado de conflito normativo** (`CONFLICT`, justificação, proporcionalidade) — ambos prometidos nos planos v1/v2.
**P1.8** **Perfil mono-nível**: não distingue camada de modelo-base, sistema de produto e operador/deployer (decisão de agência descentralizada), nem tem política de *fallback* (agência insuficiente → abstención/humano).
**P1.9** Distribuição de decisão skewed: PROHIBIT 41,8% das confrontações (65% no consenso). O "bar" stakes-aware não foi ancorado externamente.
**P1.10** Drift de vocabulário: **13 domínios** na ontologia/corpus vs. **10** no paper v9. Precisa reconciliação explícita.
**P1.11** Perfis sintéticos (8 arquétipos × gaussianismo) — nenhuma profilagem real por LLM foi executada; o teste B6 é perturbação numérica simulada.
**P1.12** Invariância I16 (razão chordal/TV ∈ [2/√3, √(8/3)]) mostra que a "distância" do texto original não era a métrica induzida; a decisão "face-lattice only" resolve, mas o paper ainda não reflete essa reframing.

### P2 — refinamentos desejáveis

**P2.13** B4 com 2.048 draws: ΣS₁ = 1,011 (erro de Monte Carlo) e ranking Morris contradiz Sobol → subir para ≥8.192 draws e reportar índices de ordem-total e termos de interação.
**P2.14** Reproducibilidade: falta `requirements.txt`, LICENSE, decision log, hashes de corpus, e um runner único (`make all`).
**P2.15** Faltam métricas de *interpretabilidade* do output (por que Aa caiu, qual faceta, qual aresta) — necessárias para o público de ética computacional.

---

## 3. Plano por fases, com gates e entregáveis

> Cada fase termina com um **gate** que só passa com artefato verificável (arquivo + número). Nenhuma fase seguinte começa sem gate assinado.

### F0. Congelamento e trazabilidade *(prerequisício de tudo)*
**Entregáveis:** `README.md` raiz (estado do projeto, como reproduzir), `requirements.txt`, `CHANGELOG_DECISIONS.md`, `SPEC_v10_equations.md` (Eq.1–18 com variáveis, domínios e artefato de origem), mapa v9→v10 (o que foi mantido, corrigido, removido).
**Gate G0′:** qualquer equação do paper rastreável a uma função do núcleo; `python3 -m pytest` reproduzível em ambiente limpo. ✅ estimado: 2–4 h.

### F1. Avaliação crítica do modelo (Tarefa 1)
**Entregáveis:** `AUDIT_v11.md` (lista P0/P1/P2 com evidência, como §2 acima, expandida), **carta de decisão de modelagem** (D1–D7 abaixo), e um diagrama "claim → formalização → teste" para todas as 11 asserções centrais.
**Gate G1′:** cada asserção do modelo tem (i) formalização, (ii) teste correspondente, (iii) evidência numérica; asserções sem teste são marcadas como *descriptive only* e removidas do abstract. ✅ 1–2 dias.

### F2. Revisão matemática (Tarefa 2)
**Entregáveis:**
1. **Teorema de embedding** (prova de que vértices centrados unitários existem e são únicos até rotação) + nota sobre o erro impresso no PDF (centroide ≠ (1/2, √3/4, √6/4)).
2. **Separação formal nível × forma × magnitude:** `ℓ_i` (nível), `s_i = ℓ_i/Σℓ` (forma), `M = Σℓ` (magnitude) — com prova de que déficits e decisão operam sobre **níveis**, não sobre shares.
3. **Termos estruturais justificados:** definição de S₂/S₃/S₄ como agregados de déficits sobre o face-lattice; prova de S₄ ≤ S₃ ≤ S₂ ≤ max d_i (já implementada em `Calibration.is_valid`).
4. **Análise de ganho incremental:** ΔAa e Δκ quando S₂,S₃,S₄ são removidos; se o ganho for < 0,01, os termos viram camada interpretativa, não penalidade.
5. **Piso de risco e veto:** prova de `R_r ≥ σ(E)R_c` e da não-compensação lexicográfica.
6. **Propagação de incerteza** (novidade): deficit esperado `d_i` com intervalo, decisão com *confidence band*.
**Gate G2′:** (a) 22 invariantes passando (15 atuais + 7 novos: idempotência, monotonicidade em β, robustez a reordenação de facetas, bounds de S₂/S₃/S₄, continuidade de bar, σ-dependência, abstención); (b) relatório de sensibilidade com ≥8.192 draws e índices de ordem-total; (c) decisão documentada sobre manter/remover cada termo. ✅ 3–5 dias.

### F3. Revisão das 24→26 facetas (Tarefa 3)
**Entregáveis:**
1. **Canon v11** com: justificação de cada uma das 26 (por que não 24), merge/split de facetas redundantes (ex.: `W1` Goal orientation vs `W4` Priority discipline), e candidatos novos só se aprovados.
2. **Política de compartilhamento explícita:** permitir até **3 pilares** por faceta (hoje máx. 2), com Σβ = 1 por faceta e regra de não-duplo-contagem (I8 já cobre 2 pilares; estender o teste).
3. **Implementação real das políticas de agregação** (`weighted_mean`, `guarded_weighted_mean`, `threshold_override`, `uncertainty_penalized_mean`, `soft_min`) no núcleo — fim da divergência RDF↔Python.
4. **Observáveis por faceta:** cada faceta recebe 1–2 observáveis mensuráveis (proxy) e uma fonte de evidência; sem observável, a faceta não entra.
5. **Matriz β por domínio** (opcional, experimental) — β uniforme hoje é uma hipótese não testada.
**Gate G3′:** 26–28 facetas; cada uma com: política implementada e testada, guard (quando houver), criticidade por domínio, observável, e cobertura ≥95% dos casos do corpus; teste de regressão mostrando que o Δ de κ (vs. gold ancorado) não piora. ✅ 4–6 dias.

### F4. Ontologia v3 + validação formal (Tarefa 4)
**Entregáveis:** namespaces unificados e versionados; camada deontológica (`Norm`, `NormConflict`, `Justification`, `Proportionality`); camada de agência multi-nível (`ModelLayer`, `SystemLayer`, `OperatorLayer`, `DelegationChain`, `FallbackPolicy`); tempo/horizonte (`TemporalHorizon`); calibração como indivíduos operacionais vinculados às constantes do núcleo; SHACL para confrontação e decisão (hoje faltam shapes de `Confrontation` completas); fixtures de casos reais do corpus; **testes de coerência**: (a) 0 violações SHACL em instâncias válidas, (b) ≥12 violações detectadas em fixtures inválidos, (c) 17+ consultas SPARQL de consistência, (d) demonstração de que `R_r`, `Aa`, `D` derivados por SPARQL coincidem com `core.py` a 1e-6.
**Gate G4′:** ontology_v3 validada + relatório `ontology_v3_validation.json` + mapa de herança (o que mudou vs v2 e por quê). ✅ 4–7 dias. *(Limitação a declarar: sem razão DL para aritmética do simplex; aproximação por SHACL+SPARQL.)*

### F5. Corpus ETHCASE v4 (Tarefa 5) — duas camadas
**Camada A (stress paramétrico):** reaproveitar os 1.200 casos v3, re-etiquetados com o canon v11.
**Camada B (casos semânticos ricos):** **300–400 casos** totalmente especificados, com: narrativa (≥200 palavras), stakeholders nomeados com vulnerabilidades, consequências esperadas e não intencionadas, normas aplicáveis (lei/regulamento/princípio), evidências disponíveis e ausentes, irreversibilidade, horizonte, conflito pattern, e **ambiguidade deliberada** (10% dos casos com requisitos contraditórios). Domínios: saúde, educação, meio ambiente/energia, segurança digital, justiça/segurança, infraestrutura crítica, finanças, trabalho, transporte, mídia, pesquisa.
**Gate G5′:** (a) 100% das 26 facetas com ≥5 casos críticos; (b) **0 casos** sem stakeholders, normas e consequências preenchidos; (c) cobertura de conflitos ≥6 padrões por domínio; (d) split train/calibration/test congelado e publicado; (e) casos ancorados em instrumentos externos reais (ex.: GDPR, HIPAA, Belmont, princípio de precaution, ACM/IEEE codes). ✅ 6–10 dias.

### F6. Ground truth v2 (condição para G7)
**Entregáveis e decisão metodológica (aprovação humana necessária):**
- **R1.** *Rúbrica ancorada:* regras derivadas de instrumentos normativos externos, não de heurísticas internas.
- **R2.** *Painel heterogêneo:* 3 juízes independentes (deontológico, consequencialista, prudencial) com entrada **narrativa completa** (Camada B), não vetores numéricos; adjudicação humana em ~120 casos-âncora.
- **R3.** *Tie-break explícito* documentado e testável (precaução vs. proporcionalidade).
- **R4.** *Calibração da bar de decisão* contra o painel âncora (grid sobre b₀..b₃, θ, margins).
**Gate G6′:** κ inter-raters humano/painel ≥ 0,60; κ modelo-âncora ≥ 0,60; estabilidade de decisão ante perturbação de auto-relato ≥ 0,90. Enquanto não passar, **toda afirmação de validação no paper deve ser reescrita como "alignment com painel de regras"**. ✅ 8–12 dias.

### F7. Baterias e testes ethcase × WCMK (Tarefa 6)
**Entregáveis:** suíte executável `run_all_batteries.py` com B1 (invariantes), B2 (SHACL), B3 (calibração), B4 (Sobol/Morris de ordem-total), B5 (concordância vs âncora), B6 (perfis reais por LLM local — há modelos GGUF disponíveis: `qwen36-UD-Q4_K_XL`, `Q2_0`), B7 (baselines), B8 (210 probes), B9 (correlação/ruído), **B10 nova**: robustez adversarial (prompt injection / auto-relato inflado), B11: *ablation* (sem tetraedro, sem veto, sem β compartilhada, sem piso de risco), B12: estabilidade temporal (mismo caso, agentes em momentos diferentes).
**Gate G7′:** todos os resultados com IC95; tabela comparativa v9 vs v11; **nenhuma afirmação no paper sem número correspondente**. ✅ 5–8 dias.

### F8. Paper v10 (Tarefa 7)
**Entregáveis:** documento ~10.000 palavras (EN, open access) com: modelo, formalização (Eq.1–18 já renderizadas), ontologia, corpus, resultados, **limitações declaradas** (sem razão DL, geometria como indexação relacional, ground truth de painéis), figuras fig1–fig7 atualizadas, appendices com canon completo e estatísticas do corpus.
**Gate G8′:** (a) trazabilidade equação→código→figura; (b) zero afirmação empírica sem artefato; (c) revisão interna contra a carta de decisões F1; (d) versão PDF + DOCX + fonte Markdown/LaTeX. ✅ 5–8 dias.

### F9. Empaquetamento e release
**Entregáveis:** repo/artefato final com `README`, `requirements.txt`, `LICENSE`, `Makefile`/runner, corpus com hashes, resultados em JSON, CHANGELOG de decisões.
**Gate G9′:** clone limpo → `pytest` + `run_all_batteries.py` reproduzem todos os números citados. ✅ 1–2 dias.

---

## 4. Ordem de execução proposta

`F0 → F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9`
Estimativa total: **34–54 dias úteis de trabalho assistido**, ou versão mínima viável (MVP) em **F0, F1, F2, F3, F5-B, F6-R1** (~14 dias), com F7/F8 depois.

**Risco principal:** F6 (ground truth) é o que sustenta qualquer afirmação de validação. Se não houver adjudicação humana ou ancoragem externa, o paper deve ser posicionado como **framework normativo formal + benchmark sintético**, não como instrumento validado.

---

## 5. Decisões que precisam de avaliação humana antes de executar

| # | Questão | Recomendação do plano |
|---|---|---|
| D1 | Ground truth: humano, LLM-heterogêneo ancorado, ou regras externas? | **Híbrido**: regras ancoradas em instrumentos normativos + ~120 casos âncora adjudicados por humanos; painel LLM como extensão |
| D2 | Corpus: regenerar do zero ou dual (stress paramétrico + semântico)? | **Dual** (A+B) — preserva G5 já verde e resolve P0.2 |
| D3 | Facetas: 24, 26 ou até 28? Permitir compartilhamento em 3 pilares? | **26–28**, máximo 3 pilares, Σβ=1 por faceta, observável obrigatório |
| D4 | Tetraedro: mantém como penalidade estrutural ou só como indexação relacional/interpretativa? | **Relacional + termos S₂/S₃/S₄ só se Δ mensurável ≥ 0,01** (F2.4) |
| D5 | Implementar as 4 políticas de agregação de fato, ou simplificar a ontologia a 1 política + guards? | Implementar; é a falha P0.3 |
| D6 | Rodar profilagem real com os modelos locais (ollama/GGUF) na bateria B6? | **Sim**, se houver tempo; caso contrário, declarar explicitamente B6 como perturbação sintética |
| D7 | Paper único (10k) ou paper + paper-benchmark (corpus como artefato separado)? | **Principal + supplementary artifact**; corpus v4 publicável como dataset |
| D8 | Reconciliação de domínios: 10 (paper) ou 13 (ontologia/corpus)? | **13** no v10, justificando a expansão |
| D9 | Venue/idioma confirmados (EN, open access, docx)? | Confirmar alvo e formato de submissão |
| D10 | Prazo e prioridade: MVP (F0–F3 + F5-B + F6-R1) ou rodada completa? | MVP primeiro, depois F7–F9 |

---

## 6. O que **não** fazer

- Reescrever o núcleo aritmético (v10 já corrige os 4 P0 identificados em v9: incompatibilidade Eq.1/Eq.5, métrica ½‖·‖₁, "volume" indefinido, risco que zera quando Aa=1).
- Refazer as baterias B1, B3, B4, B8 (só recalcular com canon v11 e draws maiores).
- Re-derivar a geometria (geometry.py já verifica os constantes e corrige o erro do PDF).
- Revalidar do zero a ontologia v2 (v3 é delta sobre v2).
