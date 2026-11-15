# ETH-WCMK — Relatório de gates (Rodada 4, alvo v12)

**Data:** 07/11/2026 · **Base:** `_analysis/formal_core/` (v12), `Evaluacoes/r4/`,
`Ontologias/ontology_v4/`. Todos os números abaixo vêm de artefatos gerados em
`Evaluacoes/r4/` (nome do artefato entre parênteses).

## 1. Estado dos gates

| Gate | Critério do plano v4 | Medido agora | Status |
|---|---|---|---|
| **G0′** Empaquetamento | README, requirements, LICENSE, decision log, spec, git, runner | README ✓, requirements ✓, LICENSE ✓, `CHANGELOG_DECISIONS.md` ✓, `SPEC_v12_equations.md` ✓, git com histórico da rodada (`4b00f4d` → HEAD) ✓, `_analysis/run_all_batteries.py` ✓ | ✅ |
| **G1′** Núcleo formal | E1–E31 implementadas, parâmetros validados | `core.py` (~640 linhas) cobre E2–E13d, E20–E26, E28, E29, E30; `Calibration.is_valid()` rejeita ladders incoerentes (corrigida nesta rodada: ajuste B5 produzia `critical_prohibit_gap < material_gap`) | ✅ |
| **G2′** Invariantes automatizadas | ≥42 invariantes, 0 falha | `pytest _analysis/formal_core/tests -q` → **58 passed** (I1–I33, geometria 10, ancoragem por observação G1–G7), 32,4 s | ✅ |
| **G3′** Canon de facetas | 26–33 facetas, Σβ=1, ≤3 pilares, guardas, criticidade, observável | **33 facetas** (24 originais + W6, C7, M7, K8 + M8, M9, M10, C8, K9); 200 células de criticidade; 12 guardas duras; 33/33 com observável; `validate_registry()` = [] | ✅, com ressalva medida (D4.23: K9 não melhora κ) |
| **G4′** Ontologia v4.1 validada | SHACL + ≥10 SPARQL (≥5 deônticas) + espelho aritmético 1e-6 + ≥25 fixtures inválidos detectados | Ontologia v4.1: 7 módulos (8.394 triplos de schema) + `fixtures/instances.ttl` (1.888.317 triplos, 37.997 blocos) + 63 + 13 fixtures inválidos. **Corpus inteiro** (`ontology_full_validation.json`, 13 chunks de 120 casos, 405,8 s): SHACL v4 **0 violações**, v6 **0 violações**, 2.014.563 triplos validados; **76/76** fixtures detectados e atribuídos à shape esperada; **33 verificações SPARQL** aprovadas (15 deônticas, 0 linhas violadoras no corpus completo). Espelho aritmético: grafo-amostra (403 confrontações) diff máx **1,63 × 10⁻¹²**, **0** divergências de veredicto; corpus inteiro (183.920 confrontações, bateria B19) diff **0,0**, **0** divergências; censo do retículo 15 slots, cada termo somando 1; registry check CSV ↔ `facet_registry.py` ↔ TTL: 0 divergências | ✅ (08/11) |
| **G5′** Corpus não degenerado | cobertura, densidade, decisões não degeneradas | corpus v6: 1.520 casos (1.200 A + 320 B), 120 personas, 183.920 confrontações; Aa média 0,3575, mediana 0,3515, max 0,9493; **0,0%** com Aa ≥ 0,999; ABSTAIN 14.703 (todos E29); 34 regras normativas, todas disparando em ≥50 casos | ✅ (`corpus_v6_coverage.json`) |
| **G6′** Sensibilidade e robustez | probes 100%, Sobol/Morris, ruído, temporal | B8: **2.064 probes, 7.815 asserções, taxa de passagem 1,000** (`B8_probes.json`). B10 Sobol/Morris com 33 facetas, 4.096 draws, erro de validação do estimador ≤0,033 (`B10_sobol.json`): ΣS₁ da adequade = 0,98, dominado por **λ_C = 0,856**; os termos estruturais γ+η+ω somam **0,061** de variância; θ (piso prudencial) domina a permissividade e μ_C o risco residual. B9 ruído (`B9_noise_v12.json`): flip de veredicto 1,32% (σ=0,02) → 8,56% (σ=0,20); κ painel 0,4651 → 0,3934; Aa **diminui** com ruído (−0,009 → −0,131), e o modelo fica *mais* restritivo em 8,15% dos casos contra 0,41% mais permissivo. B12 temporal (`B12_temporal_v12.json`): 20.436 trajetórias × 8 passos, 0,365 mudanças de veredicto por caso, **103 oscilações A–B–A** e 6.382 transições mais permissivas bloqueadas pela histerese (E13d) | ✅ (B8/B9/B12 medidos; Morris como ranking, sem índices de ordem total por falta de scipy) |
| **G7′** Ground truth com κ ≥ 0,60 | κ painel **e** κ modelo↔âncora | Modelo↔painel: **0,383** (ladder declarado/congelado, corpus inteiro), **0,4834** (ladder ajustado, domínios holdout TB/TS/RS/DS), **0,6617** nas 320 narrativas camada B, **0,6955** no estrato em que o painel é unânime (87.134 pares) | ❌ não atingida como um número único; ✅ no estrato unânime |
| **G8′** Paper v12 | documento com trazabilidade número→artefato | `_analysis/PAPER_v12.md` reescrito: §5 (agência estratificada, B15), §6 (ontologia validada, G4′), §8.11 (ablação dos termos geométricos, B16), §9 (16 limitações), §10 (reproducibilidade, manifest G9′), §11 (trabalho futuro com itens concluídos marcados) e **Apêndice B: tabela de trazabilidade** com 60+ linhas ligando cada número a artefato e campo. 31 equações MathML regeneradas e parseáveis; PNGs de E1–E31 recomputados a partir de `equations.py`. Verificação cruzada automatizada de **44 afirmações** do paper contra os artefatos (`_analysis/analysis/paper_artifact_consistency.py` → `paper_consistency_check.json`): **0 divergências**. Falta apenas a adjudicação humana do gold (D4.5), que não é uma limitação do paper | ✅ (08/11) |
| **G9′** Release reproduzível | manifest + hashes + histórico de execução | `manifest_r4.json`: **20 execuções** registradas, **74 artefatos** com SHA-256 e tamanho, `source_inventory` com 71 arquivos-fonte hashados (10 do núcleo, 14 geradores ontológicos, 12 artefatos ontológicos, 31 MathML, 4 fontes de equação), `git_rev` da última geração, Python 3.14.4, canon e corpus declarados | ✅ (08/11) |

## 2. O que mudou desde o plano aprovado (evidência nova)

1. **Ancoragem por observação (E30)** — cada fato verificável do caso é uma
   observação da faceta que nomeia e limita o nível declarado:
   `ℓ_f ← min(ℓ_f, q_f·[1 − s(1−c)])`. Varredura de força de ancoragem (s = 0 → 1):
   κ painel↔modelo **0,198 → 0,390** monotônico em s; Aa média 0,6685 → 0,4415;
   24,6% dos veredictos do gold mudam (`fact_grounding_sweep.json`,
   `fact_grounding_v12.json`).
2. **Canon ampliado (D4.20)** — 5 facetas procedurais fecham a lacuna entre as normas
   que o painel invoca e o que o modelo pode medir. Ablação (D4.23): +0,027 κ em
   conjunto; M9 −0,0079, M8 −0,0041, M10 −0,0017, C8 −0,0011, **K9 +0,0011 (inerte)**.
3. **Compartilhar β é essencial (D4.25)** — κ 0,4681 (β compartilhada) contra 0,1870
   (one-hot) e 0,4343 (guardas universais). A camada estrutural do tetraedro vale
   ~0,28 de κ; a não-compensação total é pior que o equilíbrio atual.
4. **Transferência (D4.27)** — κ ajustado no holdout 0,4834 > 0,4618 dentro da amostra
   de ajuste; gap de transferência negativo (−0,0215). Nenhum domínio melhora com o
   ladder declarado.
5. **Baselines (D4.27)** — melhor baseline trivial (Aa sem cap de veto) κ = 0,1464;
   modelo κ = 0,4834 → margem +0,337. O empate reportado em r3 era um artefato da
   degeneração de Aa e do gold por caso, não do modelo.
6. **Invariância estrutural** — variantes "veto precisa de material" (0 flips) e
   "banda de stakes" (65 flips em 183.920) não produzem efeito observável (D4.24).

## 3. Limitação central, declarada

A concordância inter-painel é **κ 0,20–0,52** (A–B 0,2557, A–C 0,5237, B–C 0,2012).
O teto de κ modelo↔consenso é, portanto, ~0,70: onde o painel é unânime (87.134 pares)
o modelo concorda com κ 0,6955; onde está contestado (12.223 pares) κ 0,0547. Não
humanos ratificando (D5 = não). A discordância residual se concentra em casos
genuinamente não ajustáveis normativamente; isso será reportado como limitação, não
oculto.

## 4. Pendências imediatas (ordem de execução)

1. ~~Validar ontologia v4 contra SHACL/SPARQL + espelho aritmético (G4′)~~ — **concluída
   em 08/11** (ver §5).
2. ~~Terminar B10 (Sobol/Morris, 33 facetas), B9/B12 (ruído/temporal) (G6′)~~ — concluída.
3. ~~Gerar `manifest_r4.json`~~ — **feito**: 74 artefatos hashados, 20 execuções registradas, `source_inventory` com 71 arquivos-fonte, `git_rev` regenerado a cada build do manifest, sempre pointing à árvore hashada.
4. ~~Reescrever o paper v12~~ — **concluída** (G8′): todas as 31 equações MathML/PNG
   regeneradas a partir de `_analysis/paper/equations.py`, e a checklist de
   `AUDIT_v12.md` tem disposição item a item na §7 daquele arquivo.
5. ~~Decidir D4.23 (K9)~~ — decidido: manter K9 declarando efeito nulo (+0,0011) por
   coerência procedimental, sem revendicar valor explicativo. ~~D4.17~~ — decidido e
   aplicado: o campo `weight` foi **removido** do núcleo, do registro, do CSV e da
   ontologia (inerte: 33/33 = 1,0); 6.000 confrontações recomputadas sem ele reproduzem
   os veredictos do corpus sem nenhuma divergência.
6. ~~Decidir D4.16 e D4.18~~ — decididas. D4.16: 26 pares com ‖Δβ‖∞ < 0,12 e 8 pares com
   β idênticos são **mantidos** (a distinção é semântica; fundir cortaria o canon de 33 a
   ~13 e quebraria R3). D4.18: ganho de +0,0037 κ medido, **não incorporado** — exige
   regenerar o corpus e `load_fitted_calibration` rejeita o ladder resultante
   (`material_gap ≥ critical_prohibit_gap`). Registrada como pendente bloqueada.
7. **G7′ (κ ≥ 0,60 como número único)** permanece ❌. É uma limitação do ground truth
   (pluralismo normativo + ausência de ratificação humana), não um bug: κ 0,6955 no
   estrato unânime, 0,1368 no majoritário, 0,0547 no contestado (D4.32). A adjudicação
   humana dos 120 casos da amostra (D4.5) continua dependente de decisão do autor.
8. ~~Estender o espelho aritmético às 183.920 confrontações~~ — **concluído** (B19, `mirror_full_corpus.json`): reconstrução dos níveis a partir de persona + requisitos + fatos (E30) e recomputação pelo núcleo; diff máximo 0,0 em todas as 13 quantidades espejadas e 0 divergências de veredito. A lacuna que sobra é só de serialização RDF.
9. ~~Render PDF das equações~~ — **concluído**: os 31 PNG de `equations.py` foram montados em
   `paper/figures/equations_E1_E31.pdf` (31 páginas, 653,6 KB). Não há LaTeX nesta máquina,
   de modo que o PDF é raster assembled a partir dos PNG verificados, não uma composição TeX.
10. **Rodada 5 (proposta):** camada de casos genuinamente incompletos (E26 natural),
    regeneração do corpus para D4.18 (se adoptada) e adjudicação humana do gold (D4.5).

## 5. G4′ fechada — o que foi corrigido (08/11)

Cinco defeitos de representação encontrados e fechados no gerador (v4.1):

1. **Padrão de código de faceta** `^[WCMK][0-9]$` rejeitava `M10`; agora `^[WCMK][0-9]{1,2}$`.
2. **Ligação de perfil a agente inexistente**: os 125 perfis `PROF_*_AGENT_declared`
   apontavam a `ag:persona_AGENT_declared`, que nunca foi emitido. O perfil declarado
   agora é um só, derivado da linha do corpus que o instancia, e aponta a
   `ag:agent_<caso>` (tipado `eth:Agent`). Nivel médio: diferença ≤ 5 × 10⁻⁵ antes da
   correção, 0 depois.
3. **Links de cadeia sem pilar delegado**: quando os pilares críticos do caso eram
   apenas {M, W}, o link para a camada do modelo não delegava nada e violava
   `ChainLinkShape`. Regra formalizada: um link delega os pilares que o delegado *pode*
   exercer (`W,C,M,K` para a camada system; `C,K` para model/component) e declara
   `eth:criticalDutyDelegated` e `eth:retainedPillar`. **Achado E28**: 268 links
   (5,9% dos 4.560) retêm o dever crítico na camada delegante — o modelo não pode
   exercer o dever que torna o caso crítico.
4. **Instrumentos normativos órfãos**: 31 rótulos de instrumentos usados pelo corpus
   não tinham mapeamento para o cânone deontológico (9 casos B ficavam sem nenhuma
   norma, violando `hasNorm` minCount 1). Foram adicionados 23 instrumentos tipados
   (Sendai, Sphere, ISO 27001, MDR Annex IX, Vision Zero, 3Rs, CIHEC, COPE, CBD, OSCE,
   Venice, SDG 4, UNECE, age-appropriate design code, ICRC, anti-redline, welfare
   animal, anti-discriminação nacional, natural justice, post-market, AML/FATF,
   proporcionalidade AML, proporcionalidade underwriting) + aliases para rótulos
   compostos. Os 1.520 casos têm ao menos uma norma.
5. **Limites numéricos mal tipados** (`sh:minInclusive 0.30` é xsd:decimal; 0,3 como
   double é 0,2999999999999999888) — 1.338 falsas violações em `observationConfidence`.
   Todos os limites agora são `"x"^^xsd:double`.

Verificação aritmética contra o grafo: espelho Python ↔ RDF ↔ `core.decide` sobre as
403 confrontações do grafo (estratificadas por domínio × veredicto): **diff máximo
1,63 × 10⁻¹²**, **0** divergências de veredicto. O grafo inteiro (37.985 indivíduos)
foi validado em 13 chunks de 120 casos porque a máquina não comporta o parse único
(27 GB residentes no motor de inferência): 2.014.563 triplos validados (8.394 de schema + instâncias por chunk), 0 violações v4 e v6, 405,8 s.

Limitação declarada: o espelho aritmético roda sobre as confrontações presentes no
grafo-amostra (403 de 183.920), não sobre as 183.920; a conformance SHACL, sim, é do
corpus inteiro.
