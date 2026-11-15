# GATE REPORT — Rodada 5 (v13)

**Data:** 2026-11-09, 13:30 America/Sao_Paulo. **Núcleo:** `_analysis/formal_core/core.py` (v13).
**Regla do projeto:** nenhum número entra no paper sem artefato que o sustente. Cada gate abaixo
indica o artefato que o mede.

| Gate | Conteúdo | Veredito | Evidência (artefato) |
|---|---|---|---|
| G10′ | Núcleo v13: hierarquia estrutural incondicional, α derivada, λ(E), ReviewNeed, regime de supervisão | **PASS** | `formal_core/core.py`, `geometry.py`; suite **69 invariantes** (I34–I44) `pytest _analysis/formal_core/tests -q`, 45 s |
| G11′ | Cânone de 33 facetas: β diferenciadas, guardas, ablação medida | **PASS** (com rejeição explícita) | `_analysis/facets/beta_differentiation_v13.json`, `Evaluacoes/r5/B21_ablation.json` |
| G12′ | Camada geométrica informativa: os termos de aridade e Ψ realmente informam? | **PASS** (Ψ = diagnóstico; ζ rejeitado) | `B20_variant_eval_full_corpus.json`, `B21_ablation.json`, `B23_sobol_v13.json` |
| G13′ | Corpus v7: perfis genuinamente incompletos, supervisão derivada, domínios rebalanceados | **PASS** | `Evaluacoes/r5/corpus_v7_*` + `corpus_v7_coverage.json`, `gen_v7_log.txt` |
| G14′ | Ontologia v4.2 revalidada (SHACL + SPARQL + espelho aritmético) | **PASS** (42/42 verificações; diff do espelho 1,61e-12) | `Ontologias/ontology_v4_2/`, `Evaluacoes/r5/ontology_v4_2_validation.json` |
| G15′ | Baterias B20–B25 | **5 de 6 fechadas** (B20, B21, B22, B23, B25 + B8 reexecutada); B24 (âncora LLM) declarada não executável nesta máquina (D5.15) | JSON por bateria em `Evaluacoes/r5/` |
| G16′ | κ por estrato + instrumento de adjudicação humana | **PASS** (instrumento emitido; vereditos humanos = trabalho externo) | `adjudication_packet_blind.csv`, `adjudication_packet_key.csv`, `adjudication_sample_power.json`, `_analysis/ADJUDICATION_PROTOCOL_v13.md` |
| G17′ | Paper v13 + manifest + commit | **PASS** (manifest: 47 artefactos / 21 runs / 65,37 MB; commits 97ddab3, e38544a) | `Evaluacoes/r5/manifest_r5.json`, `_analysis/PAPER_v13.md`, git e38544a |
| G18′ | Rastreabilidad: ningún número del paper sin artefacto | **PASS** (166/166 afirmaciones; 127 por patrón explícito, 39 por valor anclado en el contexto) | `Evaluacoes/r5/paper_consistency_check_v13.json` |
| G19′ | Sensibilidad de κ a las priors del rubric (B26) | **PASS** (11 variantes, 220.400 pares; κ 0,2974–0,6005). G7′ **no** se da por alcanzado: la variante que supera 0,60 lo hace por abstención compartida, no por mejor juicio | `Evaluacoes/r5/B26_rubric_sensitivity.json` |
| G20′ | Documentação final: Paper v14 (EN) e Relatório técnico-científico (PT), com notação, citação completa e disponibilidade aberta | **PASS** (44/44 referências citadas; 166/166 cifras rastreadas; 28 e 31 páginas) | `_analysis/PAPER_v14.docx`, `_analysis/RELATORIO_TECNICO_CIENTIFICO_PT.docx`, `_analysis/paper/{build_paper_v14,build_report_pt,docx_build_v14,finish_v14}.py` |


Gates das rodadas anteriores (G0′–G9′) não foram refeitos: foram apenas **re-verificados**
contra o núcleo v13, com os artefatos originais de r2/r3/r4 preservados (D5.10). A re-verificação
produziu `Evaluacoes/r5/mirror_full_corpus_v13.json`, `B8_probes_reverified.json` e
`ontology_v4_validation_reverified.json`, todos com os mesmos vereditos.

---

## O que foi medido (números que sustentam o paper)

### G10′ — hierarquia incondicional e α derivada
Proposição 1: se α_e = (1/3)Σ_{f∃e} β_f e Σβ = 1, então S₂ ≥ S₃ ≥ S₄ para **todo** vetor de
déficit. Testada no grid completo {0, 0.05, …, 1}⁴ × 4 conjuntos de β (I34). Com β_f = 1/4,
α_e = 1/6 — exatamente a calibração v10–v12: a reparameterização não altera nenhum número
publicado. Espelho aritmético total (B25) confirma: **220.400 confrontações do corpus v7
reproducidas pelo núcleo v13, diff máximo 0,0**
para S₂, S₃, S₄, Aa raw/low/high, bar, stakes, risco, φ, u e material_gap (102–122 s).

### G11′ — β diferenciadas e guardas
Dez facetas alteradas (W6, C2, C5, M2, M4, M10, K1, K2, K5, K7). Pares de facetas com vetor β
idêntico: **8 → 1** (resta C3 ≡ C7, deliberado); pares quase-idênticos (‖Δβ‖∞ < 0,12): 18 → 22; total dentro de 0,12: 26 → 23. Censo de aridade: 1 uni-pilar, 10 bi-pilares,
22 tri-pilares, 0 quadripilares.
Efeito sobre κ (1.080 casos × 120 personas, bootstrap pareado 200 remuestreamentos):
- β isoladas: κ 0,4028 → 0,4047, **Δκ +0,0019 IC95 [0,0009; 0,0032]**;
- β + supervisão: 0,4122, **Δκ +0,0094 IC95 [0,0069; 0,0120]**.

Ablação (400 casos, 48.400 pares):
- retirar as 12 guardas: κ 0,4633 → 0,1399, **Δκ −0,3234 IC95 [−0,3306; −0,3147]**; Aa média
  sobe de 0,3516 a 0,6153;
- colapsar deveres multi-pilares ao pilar primário: κ 0,2691, **Δκ −0,1942 IC95 [−0,2025; −0,1831]**;
- retirar uma guarda isolada: |Δκ| ≤ 0,0042 (C7 −0,0042; M9 −0,0024; M8 −0,0012; W6 +0,0014).

Rebalanceamento de criticidade: **rejeitado** — agressiva Δκ −0,0147 IC95 [−0,0179; −0,0116]
(400 casos, 48.400 pares); mild cap-3 Δκ −0,0050 IC95 [−0,0072; −0,0022] e targeted TB/TS/IM
Δκ −0,0077 IC95 [−0,0095; −0,0058], ambas sobre 859 casos / 103.939 pares
(`B20_crit_mild_cap3_full_corpus.json`, `B20_crit_targeted_full_corpus.json`).

### G12′ — a camada geométrica
- ζ (termo de exposição entre pilares): ζ = 0,05 → −0,0013; ζ = 0,10 → −0,0030 (400 casos);
  no corpus completo −0,0028 e −0,0059. **ζ = 0 permanece canônico**: Ψ é registrado como
  diagnóstico (média 0,1839 na mostra de B20, 130.680 pares; **0,1703** nos 220.400 pares
  do corpus completo, campo `cross_pillar_duty`) e não entra na decisão.
- λ(E) (saliência adaptativa): s = 0,5/1,0/2,0 → −0,0001/−0,0002/−0,0002. Mecanismo
  implementado e testado (I37), valor canônico **s = 0** (identidade).

### G13′ — corpus v7
1.520 casos (1.200 camada A, 320 camada B), 144 personas (36 tipos; 24 com déficit concentrado;
6 tipos de declaração parcial, 24 instâncias), 220.400 pares.
Aa média 0,3551, mediana 0,3462, máximo 0,9508, **nenhum par com Aa ≥ 0,999**.
Decisões: PROHIBIT 152.439, REVIEW 32.996, ABSTAIN 34.615 (16.375 epistêmicas + 18.240 por
cobertura), ALLOW_WITH_GUARDS 349, ALLOW 1.
Ground truth (rubric): PROHIBIT 162.507, ABSTAIN 30.077, REVIEW 22.687, AWG 2.653, ALLOW 2.476;
kernel-only 14,19%; concordância modelo×painel 0,7886.
**κ global 0,5336** (v6: 0,4681). Por estrato: unânime 0,7348 (63.681 pares), maioria 0,1254
(44.603), contestado 0,0402 (22.396).
Gap de verificação (D5.8): 36.480 pares com declaração incompleta; κ 0,8085 quando o rubric
adia (canônico) vs 0,0801 quando assume violação.
Oversight (pares): none 67.715, on_the_loop 91.640, in_the_loop 61.045.
34 regras do rubric, todas disparando em ≥ 50 casos.

### G15′ — ancoragem factual (B22)
300 casos estratificados, 43.210 pares: **98,27%** dos pares contêm ao menos uma declaração
contrariada por um fato verificável; 224.097 caps aplicados; excesso médio declarado sobre o
cap 0,361. **18.898 vereditos mudam** (43,7% dos pares). κ com ancoragem E30 0,5526 vs sem
ancoragem 0,2463 → **Δκ +0,3062**. É o mecanismo que transforma "autodeclaración" em evidência.

### G15′ — probes adversários e sensibilidade
**B8 re-executado contra o núcleo v13** (`run_battery_B8_v13.py` → `B8_probes_reverified_v13.json`):
2.064 probes, 7.815 asserções, **taxa 1,000**; famílias: não-compensação 1.536 (pillar_cap,
cap_active, gap_removed, no_allow, cada 1.536/1.536; hard_veto 384/384), déficit crítico 132,
monotonicidade 99, abstenção 132 (66 disparos + 66 não-falsos), histerese 165. Idêntico ao
r4 — e é exatamente isso que tinha que acontecer: Prop-1, λ(E) com s = 0, ReviewNeed e o gate
declarado não alteram nenhuma asserção de não-compensação (D5.14).

**B23 (Morris + Sobol pareado, 12 dimensões, painel de 12 casos, 200,7 s).** Primeira
execução produzía 87/400 pontos inválidos por ruído de float no topo dos bounds — corrigido
(D5.13) e re-executada. S₁ para Aa média: coverage_gate **0,749**, γ 0,123, ρ 0,051, λ_C 0,050,
ζ 0,013; para permissividade e abstenção, coverage_gate S₁ = 1,00; para hard_veto_rate,
oversight_attenuation S₁ = 0,701 e θ_base 0,262. Morris μ* (Aa): gate 0,104; γ 0,081; ζ 0,075;
**s 0,0004** (inert). ΣS₁ < 1 em todas as saídas: o modelo é dominado por interações de limiar,
não por efeitos aditivos — por isso a evidencia de calibração no paper é Δκ por bootstrap
pareado, não coeficientes de sensibilidade.

### G15′ — o que não foi executado (medido, não presumido)
**B24 (âncora LLM local).** Medido nesta máquina: o processo `strata-host` (PID 1425370)
ocupa 25.930.740 KB de RSS de um total de 30.951 MB; `ollama ps` mostra `ornith-1.5:9b`
carregado (6,2 GB, 98% GPU) e, ainda assim, **uma completion de 60 tokens levou 141,9 s**
(≈0,4 token/s efetivo) e uma chamada com o prompt completo de 33 facetas (2.370 caracteres,
`num_predict` 1.400) ultrapassou 300 s sem devolver texto. `gemma4:12b-it-q4_K_M` não
responde em 180 s. Conclusão: a bateria não é executável enquanto o motor de inferência
residente ocupa a memória; abortar e declará-lo é preferível a registar
`json_validity_rate = 0,0` como se fosse resultado. A bateria foi reescrita
(`llm_anchor_v13.py`: warm-up com timeout configurável, endpoint de completación, parser
tolerante, retries, contagem de latência) e nenhuma afirmação sobre auto-relato de LLM
entra no paper v13 (D5.15, D5.22).

### G14′ — ontologia v4.2, fechada
`Ontologias/ontology_v4_2/` (7 módulos + 2 shapes + 2 fixtures + instances) e
`Evaluacoes/r5/ontology_v4_2_validation.json` (runtime **301,9 s**).

- Grafo validado: **8.509** triplos de módulo + **1.919.283** triplos de instância =
  **1.927.780**; 1.520 casos, 5.150 perfis, 3.755 confrontações instanciadas, 6.224 agentes,
  50.160 requisitos de faceta, 169.950 observações, 21.280 ancoragens de fato, 16.475
  registros de falha de guarda, 88 conflitos normativos.
- **SHACL**: shapes v4 sobre as instâncias **0 violações** (54,0 s); shapes v6 (E30,
  ReviewNeed, supervisão) **0 violações** (27,9 s); módulos 0 (0,26 s). As 1.520 violações
  que as shapes v6 daviam antes eram um bug de forma (`sh:in` com literais string em vez de
  IRIs, D5.11), não uma incompatibilidade do modelo.
- **Fixtures inválidos**: 76/76 detectados e **76/76** atribuídos à shape esperada
  (1.246 violações totais no grafo inválido). Um validador que não detecta os casos
  deliberadamente inválidos não vale nada: é a contraprova do gate.
- **42 verificações** (15 deontológicas, 26 estruturais/dinâmicas + achados reportados):
  **todas passam**. Entre elas: α_e = (1/3)Σβ_f por aresta; regime de supervisão igual ao
  que os fatos implicam; Ψ ∈ [0,1] e composto só por deveres multi-pilares; cobertura < 0,70
  ⇒ ABSTAIN sem literal de adequacy; S₂ ≥ S₃ ≥ S₄; nenhuma faceta spanning 4 pilares;
  ζ = 0, s = 0, gate = 0,70 declarados em **todos** os indivíduos de calibración (D5.18).
  Dos achados declarados (no bloquean el gate): 268 enlaces de cadena donde la capa
  delegante retiene el deber crítico (E28) y 0 confrontaciones cuyo declaredStakesSum
  supera el techo 2,1.
- **Espelho aritmético** graph ↔ escada Python ↔ `core.decide`, 403 confrontações
  estratificadas por (domínio, veredito): **diff máximo absoluto 1,61e-12** e
  **0 divergências de veredito** nas três comparaciones. Los 352 pares donde el nivel
  declarado excede el techo E30 lo hacen por ≤ 5×10⁻⁵, exactamente la mitad del paso de
  almacenamiento (4 decimales): no es una violación, es la precisión declarada.
- Lattice: **15 slots** (4 vértices, 6 aristas, 4 caras, 1 célula), cada término sumando 1;
  registry RDF ↔ CSV ↔ facet_registry.py: **0 desencontros** (33 facetas nas três).
- **Veredicto do gate G4′: PASS** (`"Current failures: none"`).

### G16′ — teto humano e κ por estrato (corpus completo, 220.400 pares)
`Evaluacoes/r5/kappa_by_stratum_v13.json`: unânime **0,8167** (112.179 pares, concordancia
exacta 0,915); maioria **0,1371** (95.611, 0,6656); contestado **0,0526** (12.610, 0,5977);
global **0,5336**. Por cobertura: abaixo do gate 1,000 (18.240 — ambos abstêm); canon completo
0,3832 (183.920); perfil parcial 0,3293 (18.240). Por domínio: TS 0,6110; ED 0,6103; RS 0,5877;
MA 0,5684; DS 0,5511; PD 0,5463; JS 0,5351; IC 0,5203; IM 0,5050; GP 0,5022; SA 0,4791;
TB 0,4790; FI 0,4624.

Lectura: o κ global é una media ponderada de estratos que difieren por un factor de 16; el
número que se puede defender sin disputa normativa es el del estrato unánime.

Pacote de adjudicación cega: 120 casos, 360 células baleias. Na amostra de auditoria,
κ modelo-vs-consenso **0,2067** (SE 0,0482, IC95 [0,112; 0,301]): mais baixo que o κ global
porque a amostra é deliberadamente difícil. Para uma semi-largura de IC ≤ 0,05 em κ ≈ 0,60
bastan 25 adjudicações independentes; o pacote prevê 360. O limitante não é n, é a adjudicação
humana.

### G19′ — κ no es del modelo: sensibilidad de la ground truth a sus propias priors (B26)

`b26_rubric_sensitivity.py` → `B26_rubric_sensitivity.json` (1.042,4 s, 220.400 pares, IC95 por
bootstrap pareado). Baseline **0,5336**; pisos de deber ×1,10 → 0,5507 (+0,0171); ×0,90 → 0,5250
(−0,0086); deberes categóricos reducidos a 3 → 0,5085 (−0,0251); todos categóricos → 0,5461
(+0,0125); lente A sola → 0,5223; **lente B sola → 0,3324** (−0,2012); lente C sola → 0,5147;
gate de cobertura 0,80 → **0,6005**; 0,60 → 0,4907; `assume_breach` → **0,2974** (−0,2362).

Conclusión declarada: la sensibilidad más grande no viene de los pisos (±10 % → ±0,01) sino de
**cómo se trata lo no declarado** y de **dónde se pone el gate de cobertura**. La variante V8
alcanza 0,6005 — y se rechaza como prueba de G7′: subir el gate hace abstener a modelo y rubric
a la vez, y concordar en no juzgar es barato. Lección (D5.24): un κ que sube porque ambos se
callan no es un κ que mejora.

### G17′ — rastreabilidad, manifest y commit
`_analysis/analysis/paper_artifact_consistency_v13.py` → `Evaluacoes/r5/paper_consistency_check_v13.json`:
**166 afirmaciones numéricas del paper re-derivadas del artefacto: 127 por patrón explícito y 39 por
valor anclado en el contexto del pasaje; 0 fallidas.** El verificador no se conforma con que un
número aparezca en el texto: exige (a) la precisión con la que el paper lo escribe y (b) que el
pasaje hable del asunto de la afirmación. Sin esa ancla, un "0,0" suelto en la Proposición 1
habría "verificado" un Δκ de −0,0013 (D5.21).

Manifest: `Evaluacoes/r5/manifest_r5.json` — **47 artefactos** (código, documentos, ontología),
**20 ejecuciones** con su duración reportada, **65.349.421 bytes** totales, SHA-256 de cada uno y
rev de git. Commit de cierre de la ronda: **97ddab3**.
