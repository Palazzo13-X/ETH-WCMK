# Protocolo de adjudicação humana (v13) — material para o gate G7′

**Por que isto existe.** O ground truth do corpus é um rubric operativo executado por três
painéis normativos (A deontológico, B prudencial, C ancorado em instrumentos). Isso torna a
verdade verificável e reexecutável, mas impõe um teto: os painéis compartilham um kernel, e a
discordância residual é estrutural (D4.32, G7′). Para saber se o teto é do modelo ou da
ground truth, é preciso adjudicação humana. Este pacote é o instrumento; **não** produz
vereditos — produz as condições para produzi-los.

## Material

| arquivo | conteúdo |
|---|---|
| `Evaluacoes/r5/corpus_v7_audit_sample.csv` | 120 casos estratificados por classe de decisão × domínio (PROHIBIT 24, REVIEW 44, AWG 26, ALLOW 2, ABSTAIN 24) |
| `Evaluacoes/r5/adjudication_packet_blind.csv` | o que o avaliador vê: narrativa, fatos, normas, cobertura do perfil declarado. Vereditos do modelo e dos painéis **não** aparecem |
| `Evaluacoes/r5/adjudication_packet_key.csv` | chave com veredito do modelo, adequacy, ReviewNeed, vereditos A/B/C, consenso, regras disparadas |
| `Evaluacoes/r5/adjudication_sample_power.json` | poder estatístico da amostra |

## Regras do instrumento

1. **Cegueira.** O avaliador recebe apenas narrativa + fatos + normas. A apresentação do
   veredito do modelo ancoraria a resposta e inflaria artificialmente κ contra o modelo.
2. **Escala.** Cinco vereditos: PROHIBIT, REVIEW_REQUIRED, ALLOW_WITH_GUARDS, ALLOW, ABSTAIN —
   os mesmos do modelo, definidos no SPEC (§8) e na ontologia (`eth:Decision`).
3. **Racional.** Cada veredito vem com um código do cânone:
   H1 guarda dura violada; H2 dano irreversible sem salvaguardas; H3 déficit procedural
   (aviso/consentimento/remedio); H4 lacuna de conhecimento ou evidência; H5 proporcionalidade
   (o risco não justifica proibição); H6 reversível e adequadamente salvaguardado.
4. **Confiança.** 1–5. Serve para separar discordância de ambiguidade: um par em que os três
   avaliadores divergem *com baixa confiança* é um caso mal especificado, não uma falha do modelo.
5. **Independentemente.** Três avaliadores por caso, sem discussão prévia. Discussão só depois
   de registradas as respostas, e registrada como nota separada.

## Poder estatístico (medido, não alegado)

Na amostra de auditoria, κ entre o modelo e o consenso dos painéis é **0,2067**, SE 0,0482,
IC95 [0,1123, 0,3012] — bem abaixo do κ global do corpus (0,5336) porque a amostra é
estratificada deliberadamente para incluir casos próximos à barra e ambíguos. Para obter
semi-largura de IC ≤ 0,05 em κ ≈ 0,60 são necessárias ≥ 25 adjudicações independentes;
120 casos × 3 avaliadores = 360 vereditos dão folga. O limitante real não é n, é a
adjudicação: sem ratas humanos, G7′ (κ ≥ 0,60) permanece não atingível (D4.32, D5.7).

## O que se fará com as respostas

1. κ humano × modelo (global, por estrato de consenso, por domínio).
2. κ humano × painel (para saber quanto o rubric se aproxima do juízo humano).
3. κ inter-avaliador (para saber quanto o juízo humano é coerente consigo mesmo — o teto
   superior de qualquer modelo).
4. Análise dos casos onde humano e modelo divergem e o racional é H5: se a divergência é
   proporcionalidade, o problema está na escada de decisão, não nas facetas.
