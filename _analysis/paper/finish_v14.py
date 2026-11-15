"""Finish the v14 deliverables after the interruption.

What was left open, and what this script does:

1. Terminology. Every symbol and methodological expression (alpha, Aa_low,
   material gap, stratum, fixture, mirror, SE, IC95, RSS, bootstrap, persona)
   appeared before any definition. A Notation table is inserted as Table 1 and
   every other table shifts by one; the remaining opaque terms are glossed in
   the sentence where they first appear.
2. Citations. The Portuguese report listed 44 sources and cited almost none of
   them. The citation layer is added to the sentences that invoke them.
3. Open science. Both documents now state what is available, under which
   licence and where each artefact lives.

Run:  python3 _analysis/paper/finish_v14.py
"""

PAPER = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/build_paper_v14.py"
REPORT = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/build_report_pt.py"

NOTATION_EN = '''NOTATION = [
    ["ETHCASE, 'the case'", "the formal description of an ethical situation: domain, severity, irreversibility, prudential mode, temporal horizon, epistemic uncertainty U_E, the affected population, the pattern of duties in tension and the procedural facts the case can prove", "Sec. 3"],
    ["WCMK, 'the profile'", "the agency actually delegated to act: what it wants (W), can do (C), must do (M) and knows (K)", "Sec. 3"],
    ["delegated agency", "agency transferred from a human organisation to a system that acts on its behalf, with a chain of layers behind it", "Sec. 3, Sec. 4.8"],
    ["beta", "the weight a duty distributes over the four pillars; sums to 1, at most three components non-zero, each at least 0.15", "Eq. 1, Table 3"],
    ["alpha", "the weight of an edge of the tetrahedron, derived as one third of the sum of the beta weights of the faces containing it", "Eq. 1"],
    ["q_f", "the requirement duty f imposes in a given case", "Eq. 4"],
    ["ell_p", "the level observed on pillar p, projected from the declared facet levels", "Eq. 3"],
    ["d_p", "the deficit of pillar p: requirement minus observed level, floored at zero", "Eq. 6"],
    ["S2, S3, S4", "the structural terms of the tetrahedron: the minima of the deficits taken over edges, over faces and over pillars", "Eq. 2"],
    ["Aa (adequacy)", "how far the profile meets the duties the case demands, on a 0-1 scale", "Eq. 8"],
    ["Aa_low, Aa_high", "the pessimistic and optimistic bounds of the adequacy band; the verdict is taken on Aa_low", "Eq. 17"],
    ["sigma", "the width of that band, induced by observation noise", "Eq. 17"],
    ["guard, guard floor", "the level below which a duty cannot be compensated by another pillar; twelve duties carry one", "Table 3, Eq. 10"],
    ["material gap", "the largest guard failure in the profile, measured at facet granularity", "Sec. 4.4, Eq. 10"],
    ["veto", "the condition under which a deficit bars the verdict regardless of the score", "Eq. 10"],
    ["theta, Delta_h, s_v", "the veto thresholds per pillar, the stakes margin and the severity scaling of the categorical margin", "Eq. 10"],
    ["stakes", "how much is at stake: severity weighted by effective irreversibility and the mass of those affected", "Eq. 13"],
    ["oversight regime", "who watches the decision - in the loop, on the loop, none or unspecified - inferred from declared review and audit facts", "Eq. 12"],
    ["Delta_ov", "the requirement added to duty M9 when the case declares no oversight regime", "Eq. 4"],
    ["R_r", "residual risk: potential consequence modulated by observed delivery capacity; never zero", "Eq. 16"],
    ["u, U_E", "the epistemic uncertainty declared for the case", "Eq. 9"],
    ["Phi", "exposure of duties the domain marks critical but the profile leaves thin (anti-dilution term)", "Eq. 9"],
    ["Psi, zeta", "cross-pillar duty exposure and its canonical coefficient; zeta = 0 makes Psi a governance diagnostic only", "Eq. 19"],
    ["lambda(E)", "case-conditioned salience of the pillars; the identity when s = 0", "Eq. 7"],
    ["gamma, eta, omega, rho, delta", "penalty coefficients of the structural terms, the epistemic penalty and the duty exposure inside the adequacy", "Eq. 8"],
    ["ReviewNeed", "a non-decisional index ordering cases by the external review their verdict demands", "Eq. 20"],
    ["coverage gate", "the declared fraction of the 33 duties a profile must take on to be judged: 0.70", "Eq. 18"],
    ["ladder", "the five-step lexicographic rule that turns adequacy into a verdict", "Eq. 22"],
    ["hysteresis h", "the margin (0.05) a loosening must clear; tightening is never filtered", "Eq. 22"],
    ["bar, ratio", "the stakes-aware decision threshold and the adequacy-to-threshold ratio reported in the trace", "Eq. 14, Eq. 22"],
    ["kappa", "Cohen's kappa: agreement between two raters above the agreement expected by chance", "Sec. 6, Sec. 7"],
    ["CI 95", "the 95% confidence interval of a measured difference, computed by paired bootstrap", "Sec. 7.3"],
    ["stratum", "the subset of pairs classified by whether the three normative lenses agree: unanimous, majority, contested", "Sec. 7.10"],
    ["ground truth, rubric", "the 34-rule normative instrument that produces the reference verdict", "Sec. 6"],
    ["kernel", "the part of the rubric common to all three panels: a duty and a floor", "Sec. 6"],
    ["lens", "one of the three rule tables - deontological, prudential, institutional - that vote each case", "Sec. 6"],
    ["persona", "one of the 36 profile archetypes generated with a declared deficit in one pillar", "Sec. 6"],
    ["probe", "an input built to try to break an invariant", "Sec. 7.2"],
    ["invariant", "a property the arithmetic must satisfy for every input, tested by the pytest suite", "Sec. 7.1"],
    ["ablation", "removing a mechanism and measuring the change in kappa", "Sec. 7.4"],
    ["mirror", "the recomputation of a verdict from the RDF graph, compared term by term with the core", "Sec. 5.5, Sec. 7.7"],
    ["RDF", "Resource Description Framework: a graph of statements each of the form subject - predicate - object, called a triple", "Sec. 5"],
    ["SHACL", "the W3C Shapes Constraint Language: rules attached to a class declaring what a valid instance of that class must look like", "Sec. 5.4"],
    ["SPARQL", "the query language of RDF graphs; used here to check the graph and to run the mirror", "Sec. 5.6"],
    ["OWL, PROV-O", "the Web Ontology Language and the W3C provenance ontology, the standards the vocabulary is built on", "Sec. 5.1"],
    ["fixture", "an instance, valid or deliberately invalid, used to test a shape", "Sec. 5.6"],
    ["artefact", "a file produced by a run from which a quoted number can be re-derived", "Appendix A"],
    ["manifest", "the JSON record of every artefact of a round, with its SHA-256, runtime and git revision", "Sec. 10"],
]

'''

NOTATION_PT = '''NOTATION_PT = [
    ["ETHCASE", "descrição formal do caso ético: domínio, severidade, irreversibilidade, modo prudencial, horizonte, incerteza U_E, população afetada, padrão de deveres em tensão e fatos verificáveis", "Sec. 3"],
    ["WCMK", "perfil da agência delegada: Want (querer), Can (poder), Must (dever), Know (saber)", "Sec. 3"],
    ["agência delegada", "agência transferida de uma organização humana a um sistema que age em seu nome, organizada em camadas", "Sec. 3, 4.7"],
    ["beta", "peso que um dever distribui entre os quatro pilares; soma 1, no máximo três componentes não zero, cada uma ≥ 0,15", "Eq. 1, Tabela 5"],
    ["alpha", "peso de uma aresta do tetraedro, derivado como um terço da soma dos beta das faces que a contêm", "Eq. 1"],
    ["q_f", "requisito que o dever f impõe naquele caso", "Eq. 4"],
    ["ell_p", "nível observado no pilar p, projetado a partir dos níveis declarados", "Eq. 3"],
    ["d_p", "déficit do pilar p: requisito menos nível observado, limitado a zero", "Eq. 6"],
    ["S₂, S₃, S₄", "termos estruturais do tetraedro: mínimos do déficit sobre arestas, faces e pilares", "Eq. 2"],
    ["Aa (adequacy)", "quanto o perfil atende aos deveres exigidos pelo caso, em escala 0-1", "Eq. 8"],
    ["Aa_low, Aa_high", "limites pessimista e otimista da banda de adequacy; o veredicto usa Aa_low", "Eq. 17"],
    ["σ", "largura dessa banda, induzida pelo ruído de observação", "Eq. 17"],
    ["guarda, piso de guarda", "nível abaixo do qual um dever não pode ser compensado por outro pilar; doze deveres a têm", "Tabela 5, Eq. 10"],
    ["gap material", "a maior falha de guarda do perfil, medida por faceta", "Sec. 4.3, Eq. 11"],
    ["veto", "condição que barra o veredicto independentemente da pontuação", "Eq. 10"],
    ["θ, Δ_h, s_v", "limiares de veto por pilar, margem de stakes e escalonamento por severidade", "Eq. 10"],
    ["stakes", "quanto está em jogo: severidade ponderada pela irreversibilidade efetiva e pela massa de afetados", "Eq. 13"],
    ["regime de supervisão", "quem observa a decisão: in the loop, on the loop, none ou unspecified, inferido dos fatos declarados", "Eq. 12"],
    ["Δ_ov", "acréscimo de requisito em M9 quando o caso não declara regime de supervisão", "Eq. 4"],
    ["R_r", "risco residual: consequência potencial modulada pela capacidade observada de entrega; nunca zero", "Eq. 16"],
    ["u, U_E", "incerteza epistêmica declarada para o caso", "Eq. 9"],
    ["Φ", "exposição de deveres críticos para o domínio e mal atendidos pelo perfil (termo anti-diluição)", "Eq. 9"],
    ["Ψ, ζ", "exposição transversal dos deveres e seu coeficiente canônico; ζ = 0 torna Ψ diagnóstico de governança", "Eq. 19"],
    ["λ(E)", "saliência condicional dos pilares; identidade quando s = 0", "Eq. 7"],
    ["γ, η, ω, ρ, δ", "coeficientes de penalidade dos termos estruturais, da penalidade epistêmica e da exposição de deveres", "Eq. 8"],
    ["ReviewNeed", "índice não decisório que ordena casos pela revisão externa que seu veredicto exige", "Eq. 20"],
    ["gate de cobertura", "fração declarada dos 33 deveres que um perfil precisa assumir para ser julgado: 0,70", "Eq. 18"],
    ["escada", "regra lexicográfica de cinco passos que converte adequacy em veredicto", "Eq. 22"],
    ["histerese", "margem (0,05) que uma flexibilização precisa superar; o endurecimento nunca é filtrado", "Eq. 22"],
    ["bar, ratio", "limiar de decisão ajustado aos stakes e a razão adequacy/bar registrada no rastro", "Eq. 14, Eq. 22"],
    ["κ (kappa)", "coeficiente de concordância de Cohen: acordo acima do esperado por acaso", "Sec. 6, Sec. 7"],
    ["IC95, SE", "intervalo de confiança de 95% e erro padrão de uma diferença medida, por bootstrap pareado", "Sec. 7.3, 7.10"],
    ["estrato", "subconjunto de pares classificado pelo grau de acordo entre as três lentes: unânime, maioria, contestado", "Sec. 7.10"],
    ["ground truth, rubrica", "instrumento normativo de 34 regras que produz o veredicto de referência", "Sec. 6"],
    ["kernel", "parte da rubrica comum às três lentes: um dever e um piso", "Sec. 6"],
    ["lente", "uma das três tabelas de regras — deontológica, prudencial, institucional — que votam cada caso", "Sec. 6"],
    ["persona", "arquétipo de perfil gerado com um déficit declarado em um pilar; 36 tipos", "Sec. 6"],
    ["probe", "entrada construída para tentar quebrar uma invariante", "Sec. 7.2"],
    ["invariante", "propriedade que a aritmética deve satisfazer para qualquer entrada, testada pela suite pytest", "Sec. 7.1"],
    ["ablação", "remover um mecanismo e medir a variação de κ", "Sec. 7.4"],
    ["espelho aritmético", "recalcular o veredicto a partir do grafo RDF e compará-lo termo a termo com o núcleo", "Sec. 5.7, 7.7"],
    ["RDF", "Resource Description Framework: grafo de afirmações no formato sujeito-predicado-objeto, cada uma chamada triplo", "Sec. 5"],
    ["shape SHACL", "restrição W3C aplicada a uma classe, declarando como deve ser uma instância válida dessa classe", "Sec. 5.4"],
    ["SPARQL", "linguagem de consulta de grafos RDF; usada aqui para verificar o grafo e executar o espelho", "Sec. 5.6"],
    ["OWL, PROV-O", "a linguagem de ontologias W3C e o ontologia de proveniência, padrões sobre os quais o vocabulário é construído", "Sec. 5.1"],
    ["fixture", "indivíduo válido ou deliberadamente inválido usado para testar uma shape", "Sec. 5.6"],
    ["artefato", "arquivo produzido por uma execução do qual se pode rederivar uma cifra citada", "Apêndice A"],
    ["manifest", "registro JSON de todos os artefatos da rodada, com SHA-256, duração e revisão de git", "Sec. 10"],
    ["RSS", "resident set size: a memória ocupada por um processo", "Sec. 7.9"],
    ["token", "unidade de texto que o modelo de linguagem gera; cerca de 0,4 token/s na máquina usada", "Sec. 7.9"],
]

'''

PAPER_EDITS = [
    ("a profile of delegated agency and returns one of five verdicts ",
     "a profile of delegated agency - agency transferred from a human organisation to a system that acts on its behalf - and returns one of five verdicts "),

    ("(ABSTAIN, PROHIBIT, REVIEW_REQUIRED, ALLOW_WITH_GUARDS, ALLOW) together with auditable intermediate quantities: adequacy in a ",
     "(ABSTAIN, where the model declines to judge; PROHIBIT; REVIEW_REQUIRED; ALLOW_WITH_GUARDS; ALLOW) together with the quantities that make the verdict auditable: adequacy, reported as a "),

    ("confidence band, per-pillar and per-facet deficits, a material gap, residual risk, review need and a decision trace. This round ",
     "band rather than a single number, the deficit of each pillar and each duty, the largest duty failing its floor (the material gap), the risk that survives an adequate profile (residual risk), the external review the verdict implies (review need) and the trace of the computation. This round "),

    ("The model is validated by 69 invariant tests, 2,064 adversarial probes with 7,815 assertions and a pass rate of 1.000, an ",
     "The model is validated by 69 invariant tests - properties the arithmetic must satisfy for every input - 2,064 adversarial probes, which are inputs built to try to break those properties, with 7,815 assertions and a pass rate of 1.000, an "),

    ("validated RDF triples that satisfies 34 SHACL node shapes with zero violations, detects 76 of 76 deliberately invalid fixtures and ",
     "validated RDF triples - RDF being the Resource Description Framework, whose statements are subject-predicate-object triples - that satisfies 34 SHACL node shapes (SHACL being the W3C constraint language for RDF graphs) with zero violations, detects 76 of 76 deliberately invalid fixtures - instances constructed to violate exactly one shape - and "),

    ("Agreement with the normative ground truth is 0.5336 overall, 0.8167 on ",
     "Agreement with the normative ground truth - the reference verdict produced by the rubric described in Section 6 - is 0.5336 overall, 0.8167 on "),

    ("    para(doc, \"Keywords. machine ethics; delegated ethical agency; formal verification; RDF ontology; SHACL; sensitivity analysis; \"\n"
     "             \"governance instruments; ethical AI; auditability; tetrahedral model\")",
     "    para(doc, \"Keywords. machine ethics; delegated ethical agency; formal verification; RDF ontology; SHACL; sensitivity analysis; \"\n"
     "             \"governance instruments; ethical AI; auditability; tetrahedral model\")\n"
     "    doc.add_heading(\"Notation and terminology\", level=1)\n"
     "    para(doc, \"Every symbol and expression in this paper is defined at its first appearance. The table is the index of those \"\n"
     "             \"definitions, in the order in which the terms are introduced.\", align=\"justify\")\n"
     "    table(doc, [\"Expression\", \"Meaning\", \"Defined in\"], NOTATION, widths=[1.5, 3.8, 0.9],\n"
     "          caption_text=\"Table 1. Notation used in this paper.\")"),

    ("The 76 deliberately invalid fixtures were detected, and every one was attributed ",
     "The 76 deliberately invalid fixtures - instances constructed to violate exactly one shape - were detected, and every one was attributed "),

    ("144 persona instances across 36 types plus one self-declared profile - ",
     "144 persona instances across 36 types - personas are profile archetypes generated with a declared deficit in one pillar - plus one self-declared profile - "),

    ("(1,080 cases x 120 profiles), against the consensus, with bootstrap confidence intervals on the difference.",
     "(1,080 cases x 120 profiles), against the consensus, with bootstrap confidence intervals on the difference (the pairs are resampled repeatedly to estimate the uncertainty of that difference)."),

    ("results enter as deltas.\"),\n    ])",
     "results enter as deltas.\"),\n        (\"b\", [\n"
     "            \"Open-science availability. The whole evidence chain is in the repository: the formal core and its tests under "
     "MIT; the ontologies, the facet registry, the corpus definitions and the texts under CC BY-SA 4.0. The generated RDF is in "
     "Ontologias/ontology_v4_2/, every measured artefact in Evaluacoes/r5/, the frozen rounds r2 and r3 read-only, and the "
     "manifest_r5.json ties each quoted number to a SHA-256 and a git revision. Nothing in this paper requires access beyond \"\n"
     "            \"those files and the five commands listed above.\",\n"
     "        ]),\n    ])"),
]

REPORT_EDITS = [
    ("limiares e uma escada de decisão de cinco veredictos. A terceira ",
     "limiares e uma escada de decisão de cinco veredictos (abstenção: o modelo recusa-se a julgar; proibição; revisão exigida; permitido com guardas; permitido). A terceira "),

    ("interpreta os resultados das baterias de testes: invariantes, probes adversários, ablações, sensibilidade de ",
     "interpreta os resultados das baterias de testes: invariantes (propriedades que a aritmética deve satisfazer para qualquer entrada), probes adversários (entradas construídas para tentar quebrar essas propriedades), ablações (remover um mecanismo e medir o efeito) e sensibilidade de "),

    ("parâmetros, espelho aritmético entre grafo e código, e a sensibilidade da concordância à própria rubrica normativa.",
     "parâmetros, o espelho aritmético (recalcular o veredicto a partir do grafo RDF e compará-lo termo a termo com o núcleo) e a sensibilidade da concordância à própria rubrica normativa (o conjunto de regras que gera o gabarito contra o qual o modelo é medido)."),

    ("que satisfaz 34 node shapes SHACL (W3C, 2017) sem violações, ",
     "que satisfaz 34 shapes SHACL (regras W3C de restrição aplicadas a nós do grafo; W3C, 2017) sem violações, "),

    ("detecta 76 de 76 fixtures deliberadamente inválidos",
     "detecta 76 de 76 fixtures (indivíduos construídos para violar exatamente uma shape) deliberadamente inválidos"),

    ("e uma concordância com o ground truth normativo de κ = 0,5336 (Cohen, 1960) global,",
     "e uma concordância com o ground truth normativo — o gabarito de referência produzido pela rubrica — de κ = 0,5336 (κ, o coeficiente de concordância de Cohen, 1960: acordo acima do esperado por acaso) global,"),

    ("    sec(doc, \"1. Objetivo e alcance\", [",
     "    doc.add_heading(\"Notação e terminologia\", level=1)\n"
     "    para(doc, \"Cada símbolo e cada expressão do relatório é definido no ponto em que aparece pela primeira vez. A tabela abaixo \"\n"
     "             \"é o índice dessas definições.\", align=\"justify\")\n"
     "    table(doc, [\"Expressão\", \"Significado\", \"Onde é definida\"], NOTATION_PT, widths=[1.5, 3.8, 0.9],\n"
     "          caption_text=\"Tabela 1. Notação usada no relatório.\")\n"
     "    sec(doc, \"1. Objetivo e alcance\", ["),

    ("        (\"p\", \"O documento é complementar ao PAPER v14: o paper argumenta uma tese, e este relatório detalha os elementos do \"",
     "        (\"p\", \"O modelo pertence à vertente deontológica da ética de máquinas. Enquanto as abordagens bottom-up aprendem valores \"\n"
     "             \"dos dados ou da interação e as de alinhamento optimizam uma função objetivo (Moor, 2006; Floridi, 2004; Wallach & Allen, \"\n"
     "             \"2008; Allen, Smit & Wallach, 2005; Anderson & Anderson, 2011; Bostrom & Yudkowsky, 2016; Dignum, 2019), o ETH-WCMK \"\n"
     "             \"declara deveres e verifica se foram cumpridos. A camada normativa que operacionaliza vem dos instrumentos de \"\n"
     "             \"governança que enumeram deveres sem formalizar como um caso concreto os satisfaz (Jobin et al., 2019): a \"\n"
     "             \"Recomendação da UNESCO (UNESCO, 2021), a Recomendação da OECD (OECD, 2024), a Convenção-Quadro do Council of Europe \"\n"
     "             \"(Council of Europe, 2024), o AI Act europeu (European Union, 2024), ISO/IEC 42001 (ISO/IEC, 2023) e o AI Risk \"\n"
     "             \"Management Framework (NIST, 2023).\"),\n"
     "        (\"p\", \"O documento é complementar ao PAPER v14: o paper argumenta uma tese, e este relatório detalha os elementos do \""),

    ("        (\"p\", \"O sistema está organizado para que qualquer afirmação possa ser rastreada. O núcleo formal vive em \"",
     "        (\"p\", \"A rastreabilidade não é decorativa: um veredicto só é auditável quando as quantidades intermediárias ficam \"\n"
     "             \"registradas, e não apenas o resultado final (Miller, 2019; Williams et al., 2022). A representação é canônica, não \"\n"
     "             \"lexical: dois casos descritos com palavras diferentes entram na mesma aritmética apenas se ocupam os mesmos papéis \"\n"
     "             \"conceptuais (Peirce, 1931-1958; Gärdenfors, 2000).\"),\n"
     "        (\"p\", \"O sistema está organizado para que qualquer afirmação possa ser rastreada. O núcleo formal vive em \""),

    ("             \"os verificadores do caso sustentam.\"),",
     "             \"os verificadores do caso sustentam. O perfil não descreve um agente virtuoso (Vallor, 2016): declara o que foi \"\n"
     "             \"assumido e o que os fatos sustentam.\"),"),

    ("             \"O risco residual nunca é zero: a capacidade observada de entrega atenua o risco potencial, mas não o apaga.\"),",
     "             \"O risco residual nunca é zero: a responsabilidade por consequências que sobrevivem ao ato não se extingue com o \"\n"
     "             \"ato (Jonas, 1984), e a capacidade observada de entrega atenua o risco potencial sem apagá-lo.\"),"),

    ("    \"Agência estratificada: a cadeia de delegação é avaliada pelo elo mais fraco e cada camada reporta seu resultado. Apenas \"",
     "    \"Agência estratificada: agir e responder pelo ato não são a mesma coisa (Frankfurt, 1971), por isso a cadeia de delegação é \"\n"
     "     \"avaliada pelo elo mais fraco e cada camada reporta seu resultado. Apenas \""),

    ("        (\"p\", \"As shapes convertem as invariantes do núcleo em restrições verificáveis sobre o grafo. A ConfrontationShape, por \"",
     "        (\"p\", \"As shapes convertem as invariantes do núcleo em restrições verificáveis sobre o grafo (W3C, 2017). A ConfrontationShape, por \""),

    ("        (\"p\", \"O corpus v7 contém 220.400 confrontações (1.520 casos × 145 perfis, com 36 tipos de persona e um perfil \"",
     "        (\"p\", \"O corpus v7 contém 220.400 confrontações (1.520 casos × 145 perfis: 36 tipos de persona — arquétipos de perfil \"\n"
     "             \"gerados com um déficit declarado em um pilar — e um perfil \""),

    ("             \"casos × 120 perfis) contra o consenso, com intervalos de confiança por bootstrap pareado sobre a diferença.\"),",
     "             \"casos × 120 perfis) contra o consenso, com intervalos de confiança por bootstrap pareado sobre a diferença \"\n"
     "             \"(remostragem repetida dos pares para estimar a incerteza daquela diferença).\"),"),

    ("             \"pesos do lattice, valores de banda, pesos do stakes e limiares da escada; recalcula D, S₂, S₃, S₄, exposição, gap \"",
     "             \"pesos do lattice, valores de banda, pesos do stakes e limiares da escada; recalcula o déficit por dever (D), S₂, S₃, \"\n"
     "             \"S₄, a exposição transversal, o gap \""),

    ("             \"material, veto, teto, adequacy, σ, bar, stakes e ratio, e executa a escada em Python. A comparação com core.decide \"",
     "             \"material, o conjunto de veto, o teto de adequacy, a adequacy, σ (a largura da banda), bar (o limiar ajustado aos \"\n"
     "             \"stakes) e o ratio (a razão entre adequacy e bar), e executa a escada em Python. A comparação com core.decide \""),

    ("\"Organization, 1998), ACM/IEEE, ISO 26262 (ISO, 2018), IEC 62443, ISO 27001 (ISO/IEC, 2023), NIST CSF (NIST, 2025), OECD (OECD, 2024) — cada uma com um dever, uma condição e \"\n"
     "             \"uma direção, cada uma com um instrumento, uma condição e \"\n",
     "\"Organization, 1998), ACM/IEEE, ISO 26262 (ISO, 2018), IEC 62443, ISO 27001 (ISO/IEC, 2023), NIST CSF (NIST, 2025), NIST AI RMF \"\n"
     "             \"(NIST, 2023), OECD (OECD, 2024), a Convenção-Quadro do Council of Europe (Council of Europe, 2024), o AI Act europeu \"\n"
     "             \"(European Union, 2024) e a Recomendação da UNESCO (UNESCO, 2021) — cada regra com um instrumento, um dever, uma \"\n"
     "             \"condição e \""),

    ("             \"executada nesta máquina: o processo residente de inferência ocupa 25.930.740 KB de RSS de um total de 30.951 MB; \"",
     "             \"executada nesta máquina: o processo residente de inferência ocupa 25.930.740 KB de RSS (resident set size, a memória \"\n"
     "             \"ocupada pelo processo) de um total de 30.951 MB; \""),

    ("             \"uma resposta de 60 tokens levou 141,9 s (≈ 0,4 token/s efetivo) e a chamada com o prompt completo de 33 facetas \"",
     "             \"uma resposta de 60 tokens (unidade de texto que o modelo gera) levou 141,9 s, cerca de 0,4 token/s efetivo, e a \"\n"
     "             \"chamada com o prompt completo de 33 facetas \""),

    ("             \"(2.370 caracteres, num_predict 1.400) ultrapassou 300 s sem devolver texto; gemma4:12b-it-q4_K_M não responde em \"",
     "             \"(2.370 caracteres, num_predict 1.400: o limite de tokens que o motor se compromete a gerar) ultrapassou 300 s sem \"\n"
     "             \"devolver texto; gemma4:12b-it-q4_K_M, um modelo de 12 bilhões de parâmetros quantizado, não responde em \""),

    ("        (\"p\", \"κ depende das priors normativas da rubrica. Perturbar os pisos de dever em 10% move κ de 0,5336 para 0,5507 ou \"",
     "        (\"p\", \"κ, o coeficiente de concordância de Cohen (1960), depende das priors normativas da rubrica — os pressupostos de \"\n"
     "             \"valor embutidos nas regras: pisos de dever, deveres categóricos e lente escolhida. Perturbar os pisos de dever em 10% \"\n"
     "             \"move κ de 0,5336 para 0,5507 ou \""),

    ("             \"modelo-vs-consenso é 0,2067 (SE 0,0482, IC95 [0,112; 0,301]), mais baixo que o global porque a amostra é \"",
     "             \"modelo-vs-consenso é 0,2067 (SE, o erro padrão da estimativa, 0,0482; IC95, o intervalo de confiança de 95%, \"\n"
     "             \"[0,112; 0,301]), mais baixo que o global porque a amostra é \""),

    ("             \"e r3 estão congeladas: não são sobrescritas, e os resultados novos entram como delta sobre elas.\"),",
     "             \"e r3 estão congeladas: não são sobrescritas, e os resultados novos entram como delta sobre elas. Toda essa evidência \"\n"
     "             \"está disponível no repositório: o núcleo e os testes sob licença MIT; ontologias, registro de facetas, definições do \"\n"
     "             \"corpus e textos sob CC BY-SA 4.0; o RDF gerado em Ontologias/ontology_v4_2/, cada artefato medido em Evaluacoes/r5/, \"\n"
     "             \"e as rodadas r2 e r3 somente para leitura. Nenhuma afirmação do relatório exige acesso além desses arquivos e dos \"\n"
     "             \"cinco comandos listados na seção 10.\"),"),
]


def renumber(text, token):
    import re
    return re.sub(rf"{token}(\d+)", lambda m: f"{token}{int(m.group(1)) + 1}", text)


def apply(path, edits, notation_block):
    text = open(path, encoding="utf-8").read()
    if "Notation used in this paper" in text or "Notação usada no relatório" in text:
        print(f"{path}: already finished, nothing to do")
        return
    # shift every existing table number first, so the notation table can take Table 1
    token = "Tabela " if path.endswith("build_report_pt.py") else "Table "
    text = renumber(text, token)
    ok = 0
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            print(f"  SKIP ({n} matches): {old[:60]!r}")
            continue
        text = text.replace(old, new, 1)
        ok += 1
    anchor = "REFS = [" if path.endswith("build_paper_v14.py") else "FIG = \""
    pos = text.index(anchor)
    text = text[:pos] + notation_block + text[pos:]
    open(path, "w", encoding="utf-8").write(text)
    print(f"{path}: {ok} edits applied; notation inserted; tables renumbered")


if __name__ == "__main__":
    apply(PAPER, PAPER_EDITS, NOTATION_EN)
    apply(REPORT, REPORT_EDITS, NOTATION_PT)
