# Revisão do canon de facetas (Tarefa 3, rodada 4)

**Fonte de verdade:** `_analysis/facets/facet_registry_v11.csv` (28 linhas), gerado a partir de
`_analysis/formal_core/facet_registry.py` (autoritativo). Estatísticas estruturais:
`Evaluacoes/r4/facet_review_stats.json` (gerado por `_analysis/facets/review_facets.py`).

## 1. De onde vieram as 28

O catálogo original (v1) tinha 24 facetas: W1–W5, C1–C6, M1–M6, K1–K7. O canon v11/v12
mantém as 24 e acrescenta quatro:

| Nova | Código | Por que foi necessária | Falha que corrige |
|---|---|---|---|
| Want legitimacy | W6 | nenhuma faceta media **quem autorizou** o objetivo do agente | um agente pode ter intenção bem alinhada e agir sem mandato |
| Containment/reversibility | C7 | C3 mede controle *durante*; nada mediaa capacidade de **reverter** | agentes "controláveis" que produzem danos irreversíveis sem plano de reversão |
| Proportionality & redress | M7 | duties de proporcionalidade e reparação não estavam representadas | proibição/permitir sem canal de recurso |
| Learnability | K8 | nenhum pilar media adaptação (o modelo era estático) | perfis que não melhoram com feedback são tratados como equivalentes aos que melhoram |

Fix aplicado nesta rodada: **K8** tinha β = (0.10, 0.40, 0.0, 0.50), violando a regra do
próprio registro (R3: todo β não-zero ≥ 0.15). Corrigido para (0.15, 0.35, 0.0, 0.50)
no CSV e no Python — as duas fontes agora concordam.

## 2. O que a estrutura realmente faz (números)

| P | Facetas que tocam P | Massa de β | Guardas |
|---|---|---|---|
| W | 11 | 18,0% | 2 (W2, W6) |
| C | 22 | 30,2% | 6 (C3, C6, C7 + compartilhadas) |
| M | 23 | 30,7% | 9 compartilhadas; 3 guardas em facetas M (M1, M4, M7) |
| K | 17 | 21,1% | 1 guardada em faceta K (K6) |

- **Nenhuma faceta toca os quatro pilares.** 18 tocam três, 9 tocam duas, 1 (C1) toca uma.
  Ou seja: o "compartilhamento entre pilares" existe, mas nunca na forma de uma duty
  simultaneamente W+C+M+K. Isso não é um erro, mas limita o que S₄ pode significar:
  o déficit quaternário é sempre derivado de déficits menores.
- **λ (importância declarada dos pilares) ≠ massa de β.** λ = (0.30, 0.25, 0.25, 0.20)
  e a massa real é (0.18, 0.30, 0.31, 0.21): desvio máximo 0.12 (60% do valor de W).
  Não é inconsistência aritmética — q_p é uma média *dentro* do pilar, e λ pondera D —
  mas significa que "importância do pilar" tem duas definições no modelo. Decisão
  necessária (D4.14 abaixo): ou λ é declarado como escolha normativa explícita e β
  como distribuição interna, ou λ := massa de β. Recomendo o primeiro, e dizer isso
  no paper: o peso do pilar não vem das facetas, vem de λ.
- **O campo `weight` é decorativo**: 28/28 facetas têm peso 1.0. Ele aparece na fórmula
  de ℓ_p e q_p, mas nunca altera nada. Dois caminhos honestos: (a) derivar
  `w_f = mean_criticality_f / 4` (0.5–1.0) e revalidar tudo; (b) remover o campo.
  Recomendo (a) só se a bateria de sensibilidade mostrar efeito mensurável; caso
  contrário (b), por Occam.
- **22 pares de facetas têm vetores β quase idênticos** (distância < 0.12), eixo
  dominante: K1/K2/K6/K7, C2/C4/C5, M2/M4/M7, W2/W3/W6. Consequência prática: dentro
  do pilar, a agregação não distingue essas facetas; toda a discriminção vem de
  `r_f` (requisito do caso) e `criticality`. É um resultado legítimo e deve ser
  declarado — mas sugere que ou (i) essas facetas são redundantes, ou (ii) suas β
  deveriam ser distintas. Recomendo (ii): por exemplo K2 (conhecimento contextual)
  deveria tocar C mais (contexto determina viabilidade), K5 (causal) deveria tocar W
  (orienta objetivos) mais do que 0.2.
- **Cobertura de guardas é assimétrica**: C e M concentram 8 das 9 guardas. K tem uma
  única guarda (K6, auto-awareness de incertez). Como a abstención epistêmica (E29)
  depende de ℓ_K ≤ 0.65, um agente que ignora as normas aplicáveis (K3 = 0) pode
  ainda obter ℓ_K alto por compensação das demais facetas. Recomendo guardas em
  **K3 (normative knowledge)** e **K1 (evidential knowledge)**: sem normas e sem
  evidências, nenhum veredito deve ser ALLOW.
- **Massa de criticidade por domínio**: SA 111, JS 107, IC 99, FI 100, PD 95, GP 96,
  ED 72, TB 69, MA 70, TS 71, RS 78, DS 74, IM 66. Domínios de transporte (TB/TS) e
  indígena (IM) têm ~60% menos exigência que saúde/j legal. Isso pode ser intencional
  (crítica de domínio) ou um artefato de preenchimento. Tem que ser justificado ou
  rebalanceado: um caso TB critical hoje tem bar e exigência menores que um SA critical.

## 3. Lacuna entre as facetas e os painéis normativos

Os painéis de ground truth v5 usam 30 regras operacionais (`gold_panels_v5.py`,
registradas em `Evaluacoes/r4/corpus_v5_coverage.json`). Cruzando as condições das
regras com o registro de facetas, há normas que **nenhuma faceta mede**:

| Regra do painel | Facto observado | Faceta que o captura |
|---|---|---|
| A5/C2 — "decision rights-affecting sem canal de revisão humana" | existência de human-review | M6 (accountability) parcialmente |
| A6/C10 — "parte afetada não foi notificada" | notificação/explicabilidade | **nenhuma** |
| A7/C9 — "nenhum canal de recurso" | redress | M7 |
| A3/C5 — "sem consentimento" | consent | **nenhuma** |
| B5 — "cláusula de revisão/sunset" | governança temporal | **nenhuma** (K8 é a mais próxima) |
| C1 — "minimização de dados não evidenciada" | data minimisation | C4 (scope) parcialmente |
| C4 — "trabalhadores afetados sem consulta" | participação | W3 (stakeholder regard) parcialmente |

Consequência metodológica: o painel gold pode proibir um caso que o modelo não tem
como medir. Isso não invalida o gold — é exatamente a discordância que se espera de
um modelo formal — mas deve aparecer como limitação: *a granularidade observacional
do modelo é mais coarse que a dos instrumentos normativos que ele invoca*.
Ação concreta: declarar explicitamente no paper quais duties normativas estão fora
do scope observacional, ou adicionar uma faceta **T1 Explainability/transparency**
(β = W 0.2, C 0.2, M 0.3, K 0.3, guarda com floor 0.5) e uma **G1 Temporality of
oversight** (β = W 0.1, C 0.2, M 0.4, K 0.3). Decisão do autor (D4.14).

## 4. Decisões propostas para v12 (a confirmar pelo autor)

| # | Decisão | Evidência | Impacto |
|---|---|---|---|
| D4.14 | λ é escolha normativa explícita; β é distribuição interna. Documentar, não unificar. | facet_review_stats.json | elimina ambiguidade de "importância do pilar" |
| D4.15 | Guardas em K1 e K3 (floor 0.5) | E29 depende de ℓ_K; hoje K tem 1 guarda | abstención epistêmica deixa de ser contornável |
| D4.16 | Diferenciar β de pares quase idênticos (K1/K2/K6/K7; C2/C4/C5; M2/M4/M7; W2/W3/W6) | 22 pares com ‖β‖∞ < 0.12 | aumenta a resolução do modelo |
| D4.17 | Remover ou derivar `weight` | 28/28 = 1.0 | simplifica; evita parâmetro decorativo |
| D4.18 | Rebalancear criticidade nos domínios TB/TS/IM, ou justificar a diferença | massa 66–71 vs 111 | evita que "critical" signifique coisas distintas por domínio |
| D4.19 (opcional) | Adicionar T1 (explainability) e G1 (oversight temporality) | 7 regras do gold sem faceta correspondente | alinha scope observacional com normas invocadas |

Nenhuma dessas mudanças foi aplicada ao registro ainda; todas exigem re-validação
(invariantes R1–R6 + I1–I33) e re-execução das baterias. Aplicar uma sem re-rodar
tudo quebraria a regra "todo número do paper vem de um artefato".

## 5. O que foi aplicado (D4.20) e com que evidência

O canon passou de 28 para **33 facetas**. As cinco novas são âncoras observacionais dos
deveres procedurais que os painéis normativos já aplicavam sem faceta correspondente:

| Código | Faceta | β (W,C,M,K) | Guarda | Fato que a ancora |
|---|---|---|---|---|
| M8 | Transparency and notice | (0, 0.2, 0.5, 0.3) | 0.50 | notice_given |
| M9 | Human review channel | (0, 0.3, 0.7, 0) | 0.50 | human_review_channel, appeal_channel |
| M10 | Consent and participation | (0.4, 0, 0.6, 0) | 0.50 | consent_obtained, worker_consulted |
| C8 | Data minimisation and purpose limitation | (0, 0.5, 0.5, 0) | - | data_minimised |
| K9 | Periodic review and sunset | (0, 0, 0.4, 0.6) | - | sunset_review |

Códigos prefixados pelo pilar dominante para manter a convención do registro
(regra `code[0] in {W,C,M,K}`, verificada por `test_registry_integrity`).

**Ablação (45.600 pares, mesma calibração, mesmo gold):** artefato
`Evaluacoes/r4/procedural_facet_ablation.json`.

| Variante | kappa | Concordância | Aa media | delta kappa |
|---|---|---|---|---|
| full (33) | 0.4031 | 0.7614 | 0.3476 | 0 |
| 5 procedurais removidas (28) | 0.3760 | 0.7140 | 0.4625 | -0.0271 |
| só M9 removida | 0.3952 | 0.7495 | 0.3578 | -0.0079 |
| só M8 removida | 0.3990 | 0.7529 | 0.3580 | -0.0041 |
| só M10 removida | 0.4014 | 0.7507 | 0.4305 | -0.0017 |
| só C8 removida | 0.4020 | 0.7607 | 0.3496 | -0.0011 |
| só K9 removida | 0.4043 | 0.7614 | 0.3503 | **+0.0011** |

Leitura honesta: o efeito *conjunto* é real (+0.027 kappa) mas modesto; individualmente,
M9 e M8 carregam conteúdo, M10 e C8 quase nada, e **K9 é inerte** (ligeiramente melhor
sem ela). K9 é candidata a ser removida ou reclassificada como observabilidade de
segundo nível - decisão D4.23 em aberto.

**Estado das decisões propostas:** D4.14 (lambda normativo vs beta interna) aplicada
como declaração no SPEC; D4.15 (guardas em K1, K3) **pendente**; D4.16 (beta distintas
para pares quase idênticos) **pendente**; D4.17 (campo `weight` inerte: 33/33 = 1.0)
**pendente**; D4.18 (rebalancear criticidade TB/TS/IM) **pendente**; D4.19 aplicada
via D4.20.
