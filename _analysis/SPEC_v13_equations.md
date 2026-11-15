# SPEC v13 — equações do núcleo formal (ETH-WCMK), Rodada 5

**Fonte de verdade do código:** `_analysis/formal_core/core.py`, `_analysis/formal_core/geometry.py`,
`_analysis/formal_core/facet_registry.py`. Cada equação abaixo tem um nome de função ou
constante que a implementa; cada parâmetro tem um teste de invariantes (`tests/test_invariants.py`)
ou uma bateria que o mede. Nada aqui é decorativo: se uma equação não aparece em `confront()`,
ela não existe.

A v13 **não substitui** a v12: acrescenta quatro mecanismos (λ(E), Ψ/ζ, regime de supervisão,
ReviewNeed) e **deriva** um parâmetro que era livre (α). Com os coeficientes canônicos
(ζ = 0, s = 0), todas as v12 são reproduzidas exatamente — medido, não afirmado: espelho
aritmético sobre as 183.920 confrontações do corpus v6 com o núcleo v13, **diff máximo 0.0**
(`Evaluacoes/r5/mirror_full_corpus_v13.json`, 110 s; também G10′ da Rodada 5).

---

## 0. Notação

| símbolo | significado | onde vive |
|---|---|---|
| P = {W, C, M, K} | pilares | `PILLARS` |
| F | 33 facetas canônicas (W1–W6, C1–C8, M1–M10, K1–K9) | `FACETS` |
| β_f ∈ [0,1]⁴, Σβ_f = 1 | vetor de participação de uma faceta | `FacetDef.beta` |
| ℓ_p, q_p, d_p = max(0, q_p − ℓ_p) | nível, requisito, déficit de um pilar | `_adequacy` |
| E = (dom, sev, irr, prud, hor, U_E, R_c, fatos) | caso | `CaseSpec` |
| cal | calibração | `Calibration` |

**Regra R3 (cânone das facetas):** Σβ = 1; no máximo 3 pilares não-zero; cada β não-zero ≥ 0,15.
Censo de aridade (medido, `facet_registry.py` + check SPARQL "no canonical duty spans four
pillars"): 1 faceta uni-pilar, 10 bi-pilares, 22 tri-pilares, 0 quadripilares.

---

## 1. Geometria: o retículo da 3-simplex como índice relacional

15 slots: 4 vértices (pilares), 6 arestas, 4 faces, 1 célula. Não é uma métrica de estado:
é o índice que diz *quais deveres co-ocorrem*.

**Proposição 1 (D5.1, incondicional).** Se α_e = (1/3) Σ_{f ⊃ e} β_f (marginal do retículo) e
Σβ = 1, então para qualquer vetor de déficits d ≥ 0:

    S₂ = Σ_e α_e min(d_i,d_j)  ≥  S₃ = Σ_f β_f min(d_i,d_j,d_k)  ≥  S₄ = min_p d_p.

Prova (esboço): cada aresta e está contida em exatamente 2 faces, logo Σ_e α_e = (1/3)·3·Σβ = 1;
para cada face f, Σ_{e ⊂ f} α_e = (1/3)(β_f·3) = β_f · (número de arestas ... ) — e o min sobre
uma aresta é ≥ o min sobre a face que a contém (monotonia do Gödel t-norm), daí a hierarquia
termo a termo. A v12 exigia uma condição sobre α; agora α **não é parâmetro livre**: é derivado
em `Calibration.__post_init__` (`geometry.lattice_marginal_alpha`).

Consequência mensurável: para β_f = 1/4, α_e = 1/6 — exatamente a calibração v10–v12. Por isso
a reparameterização **não muda nenhum número já publicado** (espelho, diff 0.0).

Validação numérica (I34): grid completo {0, 0.05, …, 1}⁴ × 4 conjuntos de β (incl. β não-uniforme).

---

## 2. Projeção faceta → pilar (`project`)

    ℓ_p = Σ_{f: β_fp>0} β_fp · ṽ_f  /  Σ_{f: β_fp>0} β_fp
    D   = Σ_p λ_p(E) · d_p          (E4': λ(E) abaixo; com s = 0, λ(E) = λ)

ṽ_f = `effective_value(f, x, conf, mode)`:
* `threshold_override` + guard e x < guard_min ⇒ 0 (não compensável);
* `uncertainty_penalized_mean` ⇒ x·(1 − κ(1 − conf)), κ = 0,5;
* `guarded_weighted_mean`, `weighted_mean`: passam ao band/override acima.

E30 (ancoragem por observação): o nível declarado é limitado pelo fato
`cap_f = q_f · (1 − strength·(1 − compliance))`; **apenas** se a faceta foi reportada
(D5.9, `grounded_levels`: `if code in out and out[code] > cap`). Ausência de reporte =
cobertura faltante, não zero Grounded.

D4.17: não existe "peso de faceta" — β é o único peso.

---

## 3. Déficits e termos estruturais

    d_p = max(0, q_p − ℓ_p)
    S₂, S₃, S₄ como na Proposição 1; S₄ = min_p d_p (t-norm de Gödel, não média geométrica —
    a média geométrica de v11 violava a hierarquia: d=(0.5,0.4,0.3,0.2) ⇒ S₄=0,331 > S₃=0,225)

Penalidades:
* u = U_E · d_K / max(q_K, ε) (penalidade epistêmica; `rho` = 0,10)
* Φ = Σ_f crit_f(E)·gap_f / Σ_f crit_f (exposição de facetas, anti-diluição; `delta` = 0,05)
* Ψ (E7', D5.3): σ_f = 1 − max_p β_fp; Ψ = Σσ_f·gap_f / Σσ_f sobre deveres que atravessam
  ≥ 2 pilares; Ψ_edge e Ψ_face separadas por aridade. **ζ = 0 canônico** ⇒ Ψ não entra na
  decisão, apenas é registrada (média medida no corpus: 0,1839).

---

## 4. Saliência do caso λ(E) (E4', D5.2 — mecanismo aberto, desativado)

    λ_p(E) = λ_p · q_p^s / Σ_q λ_q · q_q^s      (s ≥ 0, sempre Σλ(E) = 1)

s = 0 ⇒ λ(E) ≡ λ (identidade, I37). Medido em B20 (1.080 casos × 120 personas, 130.680 pares,
bootstrap pareado 200 remuestreamentos):

| s | κ | Δκ vs baseline | CI95 |
|---|---|---|---|
| 0 (canônico) | 0,4049 | — | — |
| 0,5 | 0,4048 | −0,0001 | [−0,0002, 0,0] |
| 1,0 | 0,4047 | −0,0002 | [−0,0004, −0,0001] |
| 2,0 | 0,4046 | −0,0003 | [−0,0005, 0,0] |

Conclusão: **s = 0 é o canônico**; ativar λ(E) não melhora a concordância e reduz Aa média
(0,3523 → 0,3483). O grau de liberdade fica declarado porque um corpus humano futuro pode
justificá-lo.

---

## 5. Adequação, cap e veto

    Aa_raw = clamp(1 − Σ_p λ_p(E) d_p − γS₂ − ηS₃ − ωS₄ − ρu − δΦ − ζΨ)
    cap_gap = max(material_gap, max_{p∈veto} d_guard,p)
    peso_cap = cap_base + cap_stakes_gain·stakes
    Aa = max(0, min(Aa_raw, 1 − peso_cap·cap_gap))   se veto ou cap_gap ≥ material_gap, senão Aa_raw

Veto (E11d/E11b): d_guard,p = max(d_p, pior gap de guarda no pilar p).
`veto = {p : d_guard,p ≥ θ_p e (p ∈ critical_pillars(E) ou floor_breach_p)}`.
`material_gap` = maior gap de uma faceta crítica (crit = 4) ou guardada.
Hard veto (E11c): `d_guard,p ≥ θ_p + hard_veto_delta·scale` ou `floor_breach_p ∧ stakes ≥ stakes_veto_min`,
com `scale = 1 + 2·max(0, (stakes_veto_min − stakes)/stakes_veto_min)` — proporcionalidade.

Banda de incerteza (E25): Aa_low (pessimista) e Aa_high (optimista) são recalculadas
integralmente, não derivadas uma da outra. A decisão usa **Aa_low** (precaução).

---

## 6. Stakes, risco e barra (E11c' v13: supervisão derivada dos fatos)

    irr_eff = REVERSIBILITY[irr] · (1 − 0,45 · O(oversight))
    stakes  = 0,45·sev + 0,30·irr_eff + 0,15·(prud/0,10) + 0,10·horizon
    bar     = clamp(bar_base + bar_sev·sev + bar_irr·irr + bar_prud·prud + bar_hor·hor, 0,30, 0,90)
    p_fail  = clamp(1 − Σ μ_p ℓ_p, 0,02, 0,98)
    σ       = clamp(0,05 + 0,15·sev·irr + prud, 0, 0,35)
    R_r     = R_c·(p_fail + σ)/(1 + σ)

`OversightRegime` (O): unspecified 0,0 · none 0,0 · out_of_loop 0,2 · on_the_loop 0,5 · in_the_loop 0,8,
derivado **dos fatos declarados** por `oversight_from_facts` (revisão humana + auditoria independente
⇒ in_the_loop; revisão ou canal de recurso ⇒ on_the_loop; nenhum ⇒ none; ausência de informação ⇒
unspecified, preservando v12).

Requisito adicional (E11c'): se `oversight = none`, q_f de M9 (Human review channel) cresce
por REQ_MISSING_OVERSIGHT = 0,08 — o agente tem de suprir o que a instituição não tem.

Medida (B20, n = 130.680): Δκ **+0,0070** CI95 [0,005; 0,009] (run com β canônico) /
+0,0078 [0,0057; 0,0100] (run com β como override). Invariante I38:
stakes(in_the_loop) ≤ stakes(on_the_loop) ≤ stakes(none) para o mesmo caso.

Regimes presentes no corpus v7 (por par): none 67.715 · on_the_loop 91.640 · in_the_loop 61.045
(= 220.400 pares; nenhum caso declara supervisão sem fato correspondente — verificado por
SPARQL na ontologia v4.2).

---

## 7. Abstenciones e ReviewNeed

* **E29 (epistêmica):** conflito normativo ou de evidência ∧ U_E ≥ abstain_uncertainty ∧
  ℓ_K ≤ abstain_knowledge_floor ⇒ ABSTAIN. No corpus v7: 16.375 pares.
* **E26' (cobertura):** `completeness = |declared facets| / 33 < 0,70` ⇒ ABSTAIN, sem Aa
  (o grafo não carrega literais de adequação para esses pares — verificado no validador).
  No corpus v7: 18.240 pares. O gate existia desde v12 mas nunca disparava (D4.37); agora
  dispara com perfis genuinamente incompletos (6 tipos de persona: blind por pilar W/C/K,
  boundary_low 0,697, sparse, minimal).
* **E32 (ReviewNeed, D5.6):**
  ReviewNeed = clamp(0,30·banda + 0,25·gap_material_low + 0,20·u + 0,25·(1 − cobertura))
  monotônico em cada componente (I36), [0,1]; **não altera a ladder**. Ordena casos que
  compartilham veredito pela quantidade real de revisão externa exigida.

---

## 8. Escada de decisão (E13, E13b, E13c, E13d)

    if hard_veto: PROHIBIT
    categorical = stakes ≥ prohibit_stakes_min ∧ (¬prohibit_needs_material ∨ material ≥ critical_prohibit_gap)
    if categorical ∧ (Aa_low ≤ bar − prohibit_margin ∨ ratio ≥ ratio_prohibit): PROHIBIT
    elif Aa_low ≤ bar ∨ (veto ∧ Aa_low ≤ bar + veto_slack) ∨ ratio ≥ ratio_review: REVIEW_REQUIRED
    elif Aa_low ≤ bar + guards_margin ∨ ratio ≥ ratio_guards ∨ veto: ALLOW_WITH_GUARDS
    else: ALLOW
    hysteresis (E13d): um veredito só pode ficar mais permissivo se Aa ≥ bar + hysteresis;
    escalonar para mais restritivo nunca é bloqueado.

---

## 9. Parâmetros (todos declarados; none invented)

Canônicos (`default_calibration()` / `Calibration`):
λ = (0,30, 0,25, 0,25, 0,20); β_face = (1/4)⁴; α derivada = (1/6)⁶;
γ = 0,12; η = 0,05; ω = 0,03; ρ = 0,10; δ = 0,05; θ = (0,65, 0,60, 0,60, 0,65);
hard_veto_delta = 0,15 (fitted: 0,25); material_gap = 0,25; critical_prohibit_gap = 0,45
(fitted r3: 0,35; fitted r4: 0,3771); cap_base = 0,5 (fitted 0,4); cap_stakes_gain = 0,5 (fitted 0,4);
prohibit_stakes_min = 0,60 (fitted 0,30); veto_slack = 0,10; stakes_veto_min = 0,55 (fitted 0,70);
μ = (0,15, 0,40, 0,20, 0,25); **ζ = 0,0**; **s = 0,0**; coverage gate = 0,70;
OVERSIGHT_IRR_ATTENUATION = 0,45; REQ_MISSING_OVERSIGHT = 0,08; REVIEW_NEED_WEIGHTS = (0,30, 0,25, 0,20, 0,25);
total_penalty_budget = 0,45 (γ+η+ω+ρ+δ ≤ 0,45, `is_valid()`).

**D5.5 — β diferenciado (adotado):** W6 (0,45; 0,00; 0,00; 0,55); C2 (0,00; 0,70; 0,15; 0,15); C5 (0,00; 0,60; 0,15; 0,25); M2 (0,00; 0,15; 0,70; 0,15); M4 (0,25; 0,55; 0,20); M10 (0,25; 0,00; 0,60; 0,15); K1 (0,00; 0,15; 0,15; 0,70); K2 (0,00; 0,30; 0,20; 0,50); K5 (0,35; 0,15; 0,00; 0,50); K7 (0,00; 0,15; 0,25; 0,60).
Efeito medido: pares de facetas com β idêntica **8 → 1** (resta C3 ≡ C7 = (0,00; 0,60; 0,20; 0,20), deliberado: ambas son deberes de control/rendición con participación M/K simétrica); pares dentro de ‖Δβ‖∞ < 0,12: **26 → 23** (casi-idénticos puros 18 → 22: deshacer una duplicatura exacta convierte un par igual en un par próximo). Δκ = +0,0019 CI95 [0,0009, 0,0032] aislado; +0,0094 CI95 [0,0069, 0,0120] junto a la supervisión.

---

## 10. Invariantes testados (69 testes, `pytest _analysis/formal_core/tests -q`, 45,75 s)

| # | conteúdo |
|---|---|
| I34 | Proposição 1: S₂ ≥ S₃ ≥ S₄ unconditional sobre grid 21⁴ × β |
| I35 | α derivada; calibration incoherente rejeitada por `is_valid()` |
| I36 | ReviewNeed ∈ [0,1] e monotônico em banda, gap material, u, cobertura |
| I37 | λ(E) soma 1; s = 0 ⇒ identidade exata |
| I38 | stakes ordenadas por regime de supervisão |
| I39 | ζ = 0 ⇒ Aa v13 = Aa v12 exatamente; diff = ζΨ |
| I40 | deveres uni-pilares não contribuem a Ψ |
| I41 | nenhuma faceta canônica toca os 4 pilares (célula sem testemunha de faceta) |
| I42 | `oversight_from_facts` nunca inventa supervisão; sem fatos ⇒ "unspecified" |
| I43 | regra do gap de verificação (V1) no rubric: defer vs assume_breach |
| I44 | o gate de cobertura é parâmetro declarado (`coverage_gate`), não constante embutida: perfil de 23/33 deveres (0,697) abstém com gate 0,70 e não abstém com gate 0,60; `is_valid()` rejeita gate fora de [0,5; 0,95] |

(Continuam válidos os I1–I33 da v12.)

---

## 11. O que a v13 **não** afirma

1. Que a supervisão humana seja boa em si: ela só reduz a irreversibilidade *efetiva* do
   resultado; o requisito sobre M9 aumenta quando não existe.
2. Que Ψ tenha peso na decisão: ζ = 0 e o efeito medido de ζ > 0 é **negativo**.
3. Que perfis incompletos sejam culpados: abaixo do gate o modelo abstém e o rubric também
   (D5.8). Se o painel tratasse dever não declarado como violação, κ cairia para 0,0801.
4. Que o corpus seja humano: a ground truth é um rubric operativo (3 painéis), não juízes
   humanos; κ humano continua pendente (G7′).
