# RETOMADA — Relatório de verificação de gates (Rodada 4) e agenda da Rodada 5

**Data:** 09/11/2026, 08:36 (America/Sao_Paulo) · **Árvore verificada:** git HEAD `4af83b1`,
manifest `git_rev` = `882058a` (a árvore cujos artefatos foram hashados).
**Método:** cada gate abaixo foi re-medido nesta sessão a partir do artefato que o sustenta
(comando ou arquivo citado), não a partir do README.

## 1. Gates vencidos — re-verificados agora

| Gate | Re-verificação nesta sessão | Resultado |
|---|---|---|
| G0′ empacotamento | README, requirements, LICENSE, CHANGELOG, SPEC v12, runner, git (5 commits na rodada) | ✅ |
| G1′ núcleo formal | `core.py` (33,470 B), `geometry.py`, `facet_registry.py`, `fact_grounding.py` presentes; docstring de mapeamento E2–E31 | ✅ |
| G2′ invariantes | `pytest _analysis/formal_core/tests -q` rodado agora → **58 passed, 29,94 s** (I1–I33 + 10 geometria + 7 ancoragem) | ✅ |
| G3′ canon de facetas | `facet_review_stats_v12.json`: **33 facetas**, 12/25/28/19 tocando W/C/M/K, 12 guardas, 0 violações de R3 (β ≥ 0,15) | ✅ |
| G4′ ontologia v4.1 | `ontology_full_validation.json`: `gate_verdict: PASS`, SHACL 0 violações nos 13 chunks, 76/76 fixtures detectados, 33 SPARQL, espelho-amostra 1,63 × 10⁻¹² | ✅ |
| G5′ corpus v6 | `corpus_v6_coverage.json`: 1.520 casos (1.200 A + 320 B), 120 personas, **183.920** confrontações adjudicadas; Aa média 0,3575, p50 0,3515, max 0,9493, `share_ge_0.999 = 0,0`; ABSTAIN 14.703; 8/8 gates internos do corpus `True` | ✅ |
| G6′ robustez | B8 2.064 probes/7.815 asserções taxa 1,000; B10 ΣS₁ = 0,98 (λ_C 0,856; termos estruturais 0,061); B9 flip 1,32 %→8,56 %; B12 103 oscilações, 6.382 transições bloqueadas | ✅ |
| G7′ κ ≥ 0,60 (número único) | `corpus_v6_coverage.json` → κ modelo↔painel **0,383** (ladder congelado); estratos (`kappa_by_consensus.json`): unânime 0,6955 (87.134 pares), maioria 0,1368, contestado 0,0547; holdout ajustado 0,4834 | ❌ **aberto** — teto estrutural: a discordância entre as próprias lentes (A–B 0,2557, A–C 0,5237, B–C 0,2012) impede um κ agregado ≥ 0,60 |
| G8′ paper v12 | `paper_consistency_check.json`: **44 afirmações verificadas, 0 divergências**; 31 MathML/PNG regenerados; PDF `paper/figures/equations_E1_E31.pdf` | ✅ |
| G9′ manifest | `manifest_r4.json`: 20 execuções, **74 artefatos** SHA-256, `source_inventory` (71 arquivos-fonte), canon 33, corpus v6, `calibration_convention` declarada | ✅ |

## 2. O que a auditoria (AUDIT_v12) ainda deixou pendente — e que é retomável

A auditoria classificou 44 afirmações do paper. As "não sustentadas" apontam lacunas de
implementação concretas, que definem a agenda da Rodada 5:

1. **`ReviewNeed`** é reivindicado no Abstract, mas não existe nenhuma grandeza com esse nome
   no núcleo (só o veredito `REVIEW_REQUIRED`). → **E32** a implementar e reportar.
2. **λ(E)** (vetor de saliência dependente do caso, Table 12 do paper) não existe: λ é
   global. → **E4′** a implementar e medir (D4.12 continua hipótese).
3. **`oversight_mode`** (in/on/out-of-the-loop) é citado no §3 e não está em `CaseSpec`.
4. **Hierarquia condicional** (limitação 9): `S₄ ≤ S₃ ≤ S₂` só vale sob α_e ≥ (1/3)Σβ. →
   reparametrização por **perfil de aridade monotônico** (κ₂ ≥ κ₃ ≥ κ₄), que torna a
   hierarquia incondicional.
5. **Termos geométricos inertes** (limitação 7, D4.31): γ+η+ω = 6,1 % da variância de Aa e
   Δκ ≈ 0 na ablação. → redefinir os termos estruturais ancorados na **spread de facetas**
   (duties que atravessam pilares) e medir o ganho; resultado nulo será declarado.
6. **E26 nunca dispara naturalmente** (limitação 10, B17 artificial) → corpus v7 com camada
   de perfis genuinamente incompletos.
7. **D4.18 bloqueada** (rebalanceamento de criticidade TB/TS/IM, +0,0037 κ) exigia
   regeneração do corpus — a regeneração de v7 é justamente o que falta.
8. **β quase idênticas em 26 pares / idênticas em 8** (limitação 3) → revisão do canon
   com pesos diferenciados por pilar (Tarefa 3 do pedido original).
9. **Adversarialidade declarativa** (§11 item 9): probes de inconsistência fato-declarado ×
   nível-de-faceta.
10. **Ausência de âncora externa** (limitação 1): B6 (LLM local) produziu
    `json_validity_rate = 0.0` — instrumento quebrado, não resultado. Corrigir o harness para
    obter uma segunda âncora não humana e preparar a adjudicação humana dos 120 casos.

## 3. Agenda da Rodada 5 (v13) e estimativas

| # | Entrega | Gate | Artefato esperado | Est. |
|---|---|---|---|---|
| 1 | Núcleo v13: hierarquia incondicional (κ₂≥κ₃≥κ₄), λ(E), ReviewNeed (E32), oversight_mode | G10′ | `core.py` + invariantes I34–I41 | 1 h |
| 2 | Revisão do canon de 33 facetas: β diferenciadas para os 26 pares redundantes, guardas K1/K3, ablação medida | G11′ | `facet_registry.py` + B21 (ablação de β) | 1,5 h |
| 3 | Camada geométrica informativa (terms de aridade ancorados em spread de facetas) + ablação | G12′ | `geometry.py` + B20 | 1 h |
| 4 | Corpus v7: camada C (perfis incompletos), rebalanceamento TB/TS/IM (D4.18), `oversight_mode`, fatos adversariais | G13′ | `corpus_v7_*` + coverage | 2 h |
| 5 | Ontologia v4.2: shapes para ReviewNeed/oversight/incomplete + revalidação SHACL/SPARQL + espelho | G14′ | `ontology_v4_2_validation.json` | 1,5 h |
| 6 | Baterias: B20 (geométrica), B21 (β), B22 (probes de inconsistência declarativa), B23 (Morris ordem total), B24 (âncora LLM corrigida) | G15′ | JSON por bateria + durations | 2 h |
| 7 | κ e ground truth: relatório por estrato + instrumento de adjudicação humana | G16′ | `adjudication_packet_120.csv` | 0,5 h |
| 8 | Paper v13 + GATE_REPORT_r5 + manifest r5 | G17′ | `_analysis/PAPER_v13.md`, `manifest_r5.json` | 2 h |

**Total estimado:** ~10,5 h de execução; G7′ (κ único ≥ 0,60) não depende só de nós: sem
adjudicação humana ou sem reconciliar as lentes normativas, o teto é ~0,70 (estrato unânime).
Reportar κ por estrato é a posição metodológica vigente (D4.32).

## 4. Decisões de continuidade (sem retrabalho)

- r2, r3 e r4 permanecem **congelados**; a Rodada 5 produz delta em `Evaluacoes/r5/`.
- Toda afirmação do paper v13 passa pelo verificador `paper_artifact_consistency.py` (B18),
  que já existe e já roda: 44/44 checks sem divergência na v12.
- Nenhuma mudança de canon entra sem regressão aritmética (espelho corpus↔núcleo) e sem
  re-roda da suite de invariantes.
