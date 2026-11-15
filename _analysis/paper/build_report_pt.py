"""Relatório técnico-científico (português) do modelo ETH-WCMK:
modelo, ontologia e interpretação dos resultados dos testes.

Todos os números vêm dos artefatos de Evaluacoes/r5/ (e, para as baterias
históricas, de r4). O Apêndice A liga cada cifra citada ao seu artefato.
"""
import re
import sys
sys.path.insert(0, "/home/luiz/Documentos/Strata/Shared/_analysis/paper")
from docx_build_v14 import (new_document, title_block, para, bullets, caption, equation, table, figure,
                            set_document_properties, add_running_footer)
from build_paper_v14 import EQS, CALIB, MECHANISMS, ABLATION, SOBOL, RUBRIC, BASELINES, REFS

NOTATION_PT = [
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

FIG = "/home/luiz/Documentos/Strata/Shared/paper/figures_v14"
OUT = "/home/luiz/Documentos/Strata/Shared/_analysis/RELATORIO_TECNICO_CIENTIFICO_PT.docx"

# ------------------------------------------------------------------ tabelas --

FACETS_PT = [
    ("W1", "Orientação a objetivos", ".80 / .20 / — / —", 2, "média ponderada", "—"),
    ("W2", "Alinhamento de valores", ".70 / — / .30 / —", 2, "média ponderada com guarda", "0,55"),
    ("W3", "Consideração das partes interessadas", ".60 / — / .40 / —", 2, "média ponderada com guarda", "—"),
    ("W4", "Disciplina de prioridades", ".70 / .30 / — / —", 2, "média ponderada com guarda", "—"),
    ("W5", "Estabilidade intencional", ".60 / .20 / .20 / —", 3, "média ponderada", "—"),
    ("W6", "Legitimidade do querer", ".45 / — / .55 / —", 2, "média ponderada com guarda", "0,50"),
    ("C1", "Capacidade funcional", "— / 1.00 / — / —", 1, "média ponderada", "—"),
    ("C2", "Robustez", "— / .70 / .15 / .15", 3, "média ponderada com guarda", "—"),
    ("C3", "Controlabilidade", "— / .60 / .20 / .20", 3, "override por limiar", "0,55"),
    ("C4", "Adequação de escopo", "— / .70 / .30 / —", 2, "média ponderada com guarda", "—"),
    ("C5", "Suficiência de recursos", "— / .60 / .15 / .25", 3, "média ponderada", "—"),
    ("C6", "Exequibilidade segura", "— / .50 / .30 / .20", 3, "override por limiar", "0,60"),
    ("C7", "Contenção e reversibilidade", "— / .60 / .20 / .20", 3, "override por limiar", "0,45"),
    ("C8", "Minimização de dados", "— / .50 / .50 / —", 2, "média ponderada com guarda", "—"),
    ("M1", "Obrigação legal", "— / — / .80 / .20", 2, "override por limiar", "0,60"),
    ("M2", "Obrigação de política institucional", "— / .15 / .70 / .15", 3, "média ponderada com guarda", "—"),
    ("M3", "Obrigação de princípio ético", ".20 / — / .60 / .20", 3, "média ponderada com guarda", "—"),
    ("M4", "Obrigação prudencial", "— / .25 / .55 / .20", 3, "override por limiar", "0,55"),
    ("M5", "Obrigação de papel", ".20 / .20 / .60 / —", 3, "média ponderada com guarda", "—"),
    ("M6", "Obrigação de responsabilização", ".30 / — / .50 / .20", 3, "média ponderada com guarda", "—"),
    ("M7", "Proporcionalidade e reparação", "— / .20 / .60 / .20", 3, "média ponderada com guarda", "0,50"),
    ("M8", "Transparência e notificação", "— / .20 / .50 / .30", 3, "média ponderada com guarda", "0,50"),
    ("M9", "Canal de revisão humana", "— / .30 / .70 / —", 2, "média ponderada com guarda", "0,50"),
    ("M10", "Consentimento e participação", ".25 / — / .60 / .15", 3, "média ponderada com guarda", "0,50"),
    ("K1", "Conhecimento evidêncial", "— / .15 / .15 / .70", 3, "média ponderada", "—"),
    ("K2", "Conhecimento contextual", "— / .30 / .20 / .50", 3, "média ponderada com guarda", "—"),
    ("K3", "Conhecimento normativo", "— / .20 / .40 / .40", 3, "média ponderada com guarda", "—"),
    ("K4", "Conhecimento procedural", "— / .40 / .20 / .40", 3, "média ponderada", "—"),
    ("K5", "Conhecimento causal", ".35 / .15 / — / .50", 3, "média ponderada", "—"),
    ("K6", "Consciência da incerteza", "— / .20 / .30 / .50", 3, "média penalizada pela incerteza", "0,50"),
    ("K7", "Consciência da proveniência", "— / .15 / .25 / .60", 3, "média ponderada com guarda", "—"),
    ("K8", "Aprendizabilidade", ".15 / .35 / — / .50", 3, "média penalizada pela incerteza", "—"),
    ("K9", "Revisão periódica e sunset", "— / — / .40 / .60", 2, "média ponderada", "—"),
]

CALIB_PT = [
    ("λ  saliência dos pilares", "0.30 / 0.25 / 0.25 / 0.20", "declarado (v10)", "Eq. 7"),
    ("μ  confiabilidade dos pilares na probabilidade de falha", "0.15 / 0.40 / 0.20 / 0.25", "declarado (v12)", "Eq. 15"),
    ("θ  limiares de veto por pilar", "0.65 / 0.60 / 0.60 / 0.65", "calibrado, bateria B3", "Eq. 10"),
    ("α  pesos das arestas do lattice", "derivado: α(aresta) = (1/3) Σ β(face) sobre as faces que a contêm; vale 1/6 "
     "quando todo β = 1/4", "derivado, não parâmetro livre (D5.1)", "Eq. 1"),
    ("γ, η, ω  penalidades estruturais", "0.12 / 0.05 / 0.03", "declarado", "Eq. 8"),
    ("ρ, δ  pesos epistêmicos e de exposição", "0.10 / 0.05", "declarado; γ+η+ω+ρ+δ+ζ ≤ 0.45 verificado por is_valid()", "Eq. 8, 9"),
    ("ζ  peso do dever transversal", "0 (mecanismo ativo, coeficiente zero)", "declarado e medido (D5.3)", "Eq. 8, 19"),
    ("s  expoente de saliência adaptativa", "0 (mecanismo ativo, expoente zero)", "declarado e medido (D5.2)", "Eq. 7"),
    "gate de cobertura | 0,70 das 33 obrigações | parâmetro declarado, validado (I44) | Eq. 18".split(" | "),
    "atenuação da supervisão | 0,45 sobre a irreversibilidade efetiva | declarado (D5.4) | Eq. 12".split(" | "),
    "incremento por ausência de supervisão | 0,08 sobre o requisito de M9 | declarado (D5.4) | Eq. 4".split(" | "),
    "cap_base, cap_stakes_gain | 0.40 / 0.40 | ajustado, escada r3 congelada | Eq. 11".split(" | "),
    "gap material, gap crítico de proibição | 0.25 / 0.35 | ajustado, escada r3 congelada | Eq. 9, 10".split(" | "),
    "stakes_veto_min, hard_veto_delta | 0.70 / 0.25 | ajustado, escada r3 congelada | Eq. 10".split(" | "),
    "prohibit_stakes_min, veto_slack | 0.30 / 0.10 | ajustado, escada r3 congelada | Eq. 22".split(" | "),
    "histerese | 0,05 | declarado (I30) | Eq. 22".split(" | "),
    "bar_base; márgenes; ratios | 0.55; 0.25 / 0.05; 0.70 / 0.45 / 0.25 | ajustado, escada r3 congelada | Eq. 14, 22".split(" | "),
    "limiares de abstenção (U_E, piso de K) | 0.60 / 0.65 | declarado (E29) | Eq. 22".split(" | "),
    "pesos do stakes | 0.45 / 0.30 / 0.15 / 0.10 | declarado | Eq. 13".split(" | "),
    "pesos do ReviewNeed | 0.30 / 0.25 / 0.20 / 0.25 | declarado (D5.6), campos presentes no grafo | Eq. 20".split(" | "),
]

MODULES_PT = [
    ("01_core.ttl", "Classes, pilares, 15 slots do lattice, termos estruturais, aritmética da adequacy", "1.804"),
    ("02_facets.ttl", "33 facetas, vetores β, guardas, políticas de agregação, criticidade por domínio", "2.381"),
    ("03_deontic.ttl", "Normas, instrumentos, conflitos normativos, obrigações, permissões, proibições", "3.716"),
    ("04_agency.ttl", "Camadas de agência, regras de delegação, pilares não delegáveis", "256"),
    ("05_dynamics.ttl", "Perfis de deriva, histerese, regras temporais", "141"),
    ("06_calibration.ttl", "Parâmetros da escada, coeficientes declarados, limiares", "148"),
    ("07_grounding.ttl", "Regras de ancoragem factual (E30)", "63"),
    ("shapes/ontology_shapes.ttl", "Formas SHACL v4: 27 node shapes, 152 nós de restrição", "1.166"),
    ("shapes/ontology_shapes_v6.ttl", "Formas SHACL v6: 7 node shapes (E30, ReviewNeed, supervisão)", "185"),
    ("fixtures/instances.ttl", "Grafo de instâncias gerado a partir do corpus v7", "1.919.283"),
]

CLASSES_PT = [
    ("Raiz e contexto", "Entity, Context, Pillar, PillarW, PillarC, PillarM, PillarK, Domain, TemporalHorizon, "
     "HorizonImmediate/Short/Medium/Long, SeverityBand, SeverityLow/Medium/High/Critical, Reversibility, Reversible, "
     "PartiallyIrreversible, Irreversible, PrudentialMode, PrudentialStandard/Elevated/Maximum, LatticeSlot, StructuralTerm",
     "24"),
    ("Objeto do caso", "EthicalCase, Consequence, Evidence, Stakeholder, Norm, NormativeInstrument, NormConflict, "
     "ConflictPattern, Obligation, Permission, Prohibition", "11"),
    ("Objeto da agência", "Agent, Profile, AgentLayer, DelegationChain, ChainLink, ChainLayerResult, Facet, FacetRequirement, "
     "FacetObservation, GuardedFacet, GuardFailure, FactGrounding, OversightRegime, DriftProfile, FallbackPolicy, PriorityEngine",
     "16"),
    ("Aritmética e decisão", "Calibration, Decision, Defeasibility, Confrontation, ConfrontationChain, CriticalityStatement, "
     "AggregationPolicy, WantFacet, CanFacet, MustFacet, KnowFacet, Vulnerability", "12"),
    ("Enumerações e subclasses de faceta", "PillarWFacet, PillarCFacet, PillarMFacet, PillarKFacet (usadas como tipo, mas "
     "não declaradas como owl:Class), e as subclasses declaradas em 02_facets.ttl", "4 + 12"),
]

INSTANCES_PT = [
    ("Agent", "6.224", "144 personas (36 tipos) + 6.080 agentes de caso"),
    ("Profile", "5.150", "1.520 perfis declarados (um por caso) e 3.630 perfis de persona"),
    ("DelegationChain / ChainLink", "4.560 / 4.560", "uma cadeia por caso, três elos por cadeia"),
    ("Confrontation", "3.755", "confrontações instanciadas; as 220.400 do corpus vivem na camada JSONL)"),
    ("EthicalCase / ConfrontationChain", "1.520 / 1.520", "1.200 casos da camada A + 320 da camada B"),
    ("Stakeholder", "960", "partes interessadas declaradas nos casos"),
    ("Consequence / Evidence", "320 / 320", "consequências e evidências da camada B"),
    ("Norm / NormativeInstrument / NormConflict / Obligation", "123 / 62 / 88 / 73", "camada deontológica"),
    ("Facet", "33", "canon; 12 delas com guarda explícita"),
    ("FacetRequirement", "50.160", "requisito por faceta e confrontação instanciada"),
    ("FacetObservation", "169.950", "nível declarado e confiança por faceta"),
    ("FactGrounding", "21.280", "ancoragens factuais (E30)"),
    ("GuardFailure", "16.475", "falhas de guarda registradas"),
    ("LatticeSlot", "15", "4 vértices + 6 arestas + 4 faces + 1 célula"),
]

VALID_PT = [
    ("Gate G4′", "PASS — “Current failures: none”", "ontology_v4_2_validation.json", "301,9 s"),
    ("SHACL: módulos e instâncias vs shapes v4", "0 violações", "54,04 s sobre as instâncias; 0,26 s sobre os módulos", "—"),
    ("SHACL: instâncias vs shapes v6", "0 violações", "27,91 s", "—"),
    ("Fixtures deliberadamente inválidos", "76 detectados / 76; 76 atribuídos à forma esperada", "1.246 violações no grafo inválido", "—"),
    ("Verificações SPARQL", "42/42 passam (25 estruturais, 15 deontológicas, 2 achados reportados)", "268 elos de cadeia em que a camada delegante retém o dever crítico (E28); 0 confrontações com declaredStakesSum acima do teto 2,1", "—"),
    ("Espelho aritmético graph ↔ escada Python ↔ core.decide", "diferença absoluta máxima 1,614×10⁻¹²; 0 divergências de veredicto", "403 confrontações estratificadas por (domínio, veredicto), 43 quantidades", "—"),
    ("Censo do lattice", "15 slots; cada termo soma 1,0000000000", "108 incidências; β = ¼ → α = 1/6", "—"),
    ("Registro de facetas", "33 na RDF = 33 no CSV = 33 em facet_registry.py; 0 desencontros", "—", "—"),
]

DEFECTS_PT = [
    "As classes PillarWFacet, PillarCFacet, PillarMFacet e PillarKFacet são usadas como tipo de alguns indivíduos, mas não "
    "estão declaradas como owl:Class: são “classes fantasma”, que só funcionam porque rdflib não exige a declaração.",
    "WantFacet, CanFacet, MustFacet, KnowFacet e Vulnerability estão declaradas, mas não têm nenhum indivíduo: 0 instâncias.",
    "Em 07_grounding.ttl duas propriedades usam eth:string em vez de xsd:string como tipo de literal.",
    "declaredLevelOf e declaredConfidenceOf são declaradas como datatype properties com range eth:Facet, mas nunca são usadas "
    "no grafo — o nível declarado viaja em FacetObservation.",
    "prohibitNeedsMaterial aparece como booleano false em cal:default_v12 e como inteiro 0 em cal:ladder_fit_v12: mesma "
    "semântica, dois tipos. A shape SHACL não capta essa inconsistência porque aceita ambos.",
    "ζ só existe como eth:crossPillarCoefficient = 0.0. Não há uma propriedade dedicada ao coeficiente do dever transversal, "
    "o que dificulta distinguir o zero canônico de um zero ausente.",
    "A cobertura é 1,0 em todas as 3.755 confrontações instanciadas: o gate de cobertura está declarado, mas é vazio dentro "
    "do grafo — a abstenção por cobertura vive na camada JSONL, não na RDF.",
    "cap_gap_low não é asertado como literal RDF: faltou em 403 confrontações do espelho.",
    "A validação registra corpus_rows = 183.920, enquanto o corpus v7 tem 220.400 pares: o espelho da ontologia trabalha sobre "
    "a mostra instanciada, não sobre o corpus inteiro.",
    "owl:version e owl:versionIRI dentro de 01_core.ttl dizem 4.0.0, enquanto o relatório de geração declara 4.2.0: o "
    "declarante de versão não foi atualizado pelo gerador.",
    "A validação usa inference=\"none\": o OWL não raciocina. Toda a consistência vem das SHACL shapes e das consultas SPARQL.",
]

GATES_PT = [
    ("G10′", "Núcleo v13: hierarquia incondicional, α derivada, λ(E), ReviewNeed, regime de supervisão", "PASS", "suite de 69 invariantes, 45,75 s"),
    ("G11′", "Canon de 33 facetas: β diferenciadas, guardas, ablação medida", "PASS, com rejeição explícita", "B21_ablation.json"),
    ("G12′", "A camada geométrica informa? Ψ como diagnóstico, ζ rejeitado", "PASS", "B20, B21, B23"),
    ("G13′", "Corpus v7: perfis genuinamente incompletos, supervisão derivada, domínios rebalanceados", "PASS", "corpus_v7_coverage.json"),
    ("G14′", "Ontologia v4.2 revalidada", "PASS: 42/42 verificações, espelho 1,61×10⁻¹²", "ontology_v4_2_validation.json"),
    ("G15′", "Baterias B20–B25", "5 de 6 fechadas; B24 declarada não executável, com a medição da tentativa", "Evaluacoes/r5"),
    ("G16′", "κ por estrato e instrumento de adjudicação humana", "PASS (instrumento emitido)", "adjudication_packet_blind.csv"),
    ("G17′", "Paper, manifest, commit", "PASS (51 artefatos, 22 execuções, 65,86 MB)", "manifest_r5.json"),
    ("G18′", "Rastreabilidade: nenhum número sem artefato", "PASS, 166/166 afirmações", "paper_consistency_check_v13.json"),
    ("G19′", "Sensibilidade de κ às priors da rubrica", "PASS, 11 variantes, κ 0,2974–0,6005", "B26_rubric_sensitivity.json"),
]

INTERP = [
    "O modelo é auditável, não apenas declarativo: cada veredicto chega com uma cadeia de quantidades (déficit por pilar, "
    "déficit por dever, gap material, stakes, risco residual, necessidade de revisão) que também estão declaradas em RDF. Um "
    "auditor pode reconstruir a decisão a partir do grafo sem tocar o código.",
    "A geometria deixou de ser hipótese e passou a teorema: α derivada de β torna S₂ ≥ S₃ ≥ S₄ incondicional, e o ponto "
    "β = ¼ reproduz exatamente a calibração antiga (α = 1/6), de modo que nenhuma publicação anterior precisa ser corrigida.",
    "Os mecanismos plausíveis foram medidos antes de ser ativados. Dois melhoram a concordância de forma significativa "
    "(supervisão inferida dos fatos: Δκ = +0,0078, IC95 [0,0057; 0,0100]; β diferenciadas: +0,0019, IC95 [0,0009; 0,0032]). "
    "Dois pioram (saliência adaptativa e coeficiente ζ do dever transversal) e permanecem inertes por cânone, com os números "
    "publicados. A ablação mostra que as guardas duras e a estrutura multi-pilar são determinantes: sem elas, κ cai de 0,4633 "
    "para 0,1399 e para 0,2691.",
    "A ancoragem factual é o mecanismo de maior impacto: 98,27% dos pares têm pelo menos uma declaração contrariada por um "
    "fato verificável; a regra aplica 224.097 tetos, muda o veredicto de 18.898 pares (43,74%) e eleva κ de 0,2463 a 0,5526.",
    "O risco é propriedade do dever e do contexto, não do agente: a decomposição da variância do risco residual dá 98,07% ao "
    "caso, 0,80% ao perfil e 1,13% à interação. A admissibilidade, porém, é agencial: 15,46% dos casos mudam de veredicto entre "
    "os 121 perfis que enfrentam o mesmo caso, e 225 casos podem ser resgatados por uma agência melhor.",
    "O teto do resultado é instrumental. κ global 0,5336; 0,8167 nos casos em que as três lentes normativas convergem; 0,0526 "
    "nos contestados. Como os painéis divergem entre si (κ A–C 0,6447; A–B 0,3533; B–C 0,3153), nenhum modelo pode exceder essa "
    "concordância sem que a divergência seja do instrumento, não do modelo.",
    "O método é tão contributivo quanto a arquitetura: cada rejeição aparece com seus números, cada limite é declarado e cada "
    "gate tem um artefato. A não executabilidade de uma bateria é registrada como medida, não como zero.",
]

LIMITS_PT = [
    "O ground truth é uma rubrica operacional sobre instrumentos, não juízos humanos; κ contra juízes humanos ainda não foi "
    "medido. O instrumento para fazê-lo foi emitido (120 pares cegos, 360 células) e a potência amostral já está calculada.",
    "O corpus é sintético: os 320 casos narrativos da camada B são templates gerados, não casos registrados.",
    "Os níveis dos perfis são declarados por um gerador com fator limitado e jitter; o modelo não mede o agente que avalia.",
    "O espelho aritmético da ontologia cobre 403 confrontações instanciadas (de 3.755 no grafo), e o grafo só instancia 3.755 "
    "das 220.400 confrontações do corpus; o resto vive na camada JSONL.",
    "A validação SHACL roda com inference=\"none\": não há raciocínio OWL, apenas restrições declaradas.",
    "β é uma escolha de modelagem sobre quais deveres tocam quais pilares; a diferenciación reduziu duplicidades, não provou "
    "uma ordenação normativa.",
    "Os termos estruturais S₂, S₃, S₄ têm pouco peso normativo: ablá-los muda κ menos do que o ruído entre painéis.",
    "κ nos casos contestados (0,0526) mede a divergência entre lentes, não o erro do modelo.",
    "O regime de supervisão é inferido de dois fatos (canal de revisão, auditoria independente); um regime que existe na "
    "prática, mas não é declarado, é invisível.",
    "O gate de cobertura 0,70 é declarado, não derivado de primeiros princípios: κ oscila entre 0,4907 e 0,6005 quando o gate "
    "passa de 0,60 a 0,80.",
    "A bateria de âncora LLM (B24) não pôde ser executada nesta máquina; a não executabilidade está declarada com a medição "
    "da tentativa, não substituída por um zero.",
    "O risco é reportado como consequência potencial modulada pela capacidade observada de entrega; não é a probabilidade de "
    "um dano específico.",
]

NEXT_PT = [
    "Executar o pacote de adjudicação humana com revisores de domínio e reportar κ com intervalos de confiança frente à "
    "potência amostral já calculada.",
    "Derivar o gate de cobertura da abstenção empírica, em vez de declará-lo, e testá-lo por domínio.",
    "Instrumentar a supervisão com mais fatos (quem revisa, com que autoridade, em que prazo) em lugar de dois booleanos.",
    "Executar a âncora LLM em uma máquina capaz, para testar se um modelo consegue gerar o perfil que a aritmética infere.",
    "Estender a ontologia com cadeias PROV, para que cada veredicto carregue a versão do núcleo que o produziu.",
    "Confrontar o espelho com uma segunda implementação do núcleo, escrita de forma independente, para separar o teste do código.",
]

TRACE = [
    ("220.400 pares; 1.520 casos; 145 perfis", "Evaluacoes/r5/corpus_v7_coverage.json", "pairs_adjudicated, cases.total, personas"),
    ("18.240 abstenções por cobertura; 16.375 epistémicas", "idem", "abstain"),
    ("κ 0,5336; concordância exata 0,7886; a um passo 0,9809", "idem", "kappa_model_vs_gold, model_vs_gold"),
    ("κ por estrato 0,8167 / 0,1371 / 0,0526", "Evaluacoes/r5/kappa_by_stratum_v13.json", "by_stratum"),
    ("supervisão +0,0078 [0,0057; 0,0100]; β +0,0019 [0,0009; 0,0032]", "Evaluacoes/r5/B20_variant_eval_full_corpus.json", "results[].kappa_vs_panel, .ci95"),
    ("guardas −0,3234; pilar primário −0,1942", "Evaluacoes/r5/B21_ablation.json", "results"),
    ("ancoragem 98,27%, 224.097 tetos, 18.898 mudanças, κ 0,5526 vs 0,2463", "Evaluacoes/r5/B22_fact_contradiction.json", "todos os campos"),
    ("S₁ gate 0,749; veto duro 0,701", "Evaluacoes/r5/B23_sobol_v13.json", "sobol, morris"),
    ("espelho 220.400, diferença máxima 0,0, 0 divergências, 121,87 s", "Evaluacoes/r5/mirror_full_corpus_v13.json", "confrontations, global_max_abs_difference, runtime_seconds"),
    ("2.064 probes, 7.815 asserções, 1,000", "Evaluacoes/r5/B8_probes_reverified_v13.json", "summary"),
    ("κ da rubrica 0,2974–0,6005", "Evaluacoes/r5/B26_rubric_sensitivity.json", "variants[].kappa"),
    ("1.927.780 triplos; 50.160 requisitos; 169.950 observações; 21.280 ancoragens; 16.475 falhas de guarda", "Ontologias/ontology_v4_2/generation_report.json", "instances_triples, counts"),
    ("42/42 verificações; SHACL 0 violações; 76/76 fixtures; espelho 1,61×10⁻¹²; 301,9 s", "Evaluacoes/r5/ontology_v4_2_validation.json", "gate_verdict, shacl, invalid_fixtures, mirror, sparql_checks"),
    ("69 testes de invariantes, 45,75 s", "_analysis/formal_core/tests", "saída do pytest"),
    ("34 regras da rubrica; κ entre painéis 0,6447 / 0,3533 / 0,3153", "Evaluacoes/r5/corpus_v7_coverage.json", "gold.rules, gold.panel_kappa"),
]



NOTES_PT = [
    "Reparametrização de D5.1: os seis pesos de aresta são a marginal dos quatro pesos de face sobre o face lattice da "
    "3-simplex. α não é um parâmetro livre; com β = ¼ resulta α = 1/6, exatamente o valor calibrado em v10–v12.",
    "Proposição 1: a hierarquia vale para todo vetor de déficit d ≥ 0, porque cada aresta do tetraedro está exatamente em "
    "duas faces e a t-norm de Gödel é monótona. Em v12 a desigualdade exigia uma condição sobre α; em v13 desaparece.",
    "Projeção dos níveis declarados sobre um pilar (core.project), aplicando antes da projeção a política de agregação de "
    "cada faceta.",
    "Requisito do dever: b = 0,55 / 0,70 / 0,85 para criticidade 2 / 3 / 4; pesos s = 0,08 / 0,05 / 0,03 / 0,04 por "
    "severidade, irreversibilidade, prudência e horizonte; κ = 0,05 quando o pilar primário do dever é crítico no domínio.",
    "Ancoragem factual (E30): o nível declarado é limitado pelos fatos verificáveis do caso — logs, notificação, canal de "
    "apelação, auditoria, consentimento, saída observada — com s = 0,30 canônico.",
    "Déficit por pilar. A não compensação se expressa aqui, não na média: um W alto não pode tapar um M baixo.",
    "Saliência condicional dos pilares (E4′, D5.2). Com s = 0 é a identidade; s = 0 é canônico porque o efeito medido sobre "
    "κ é nulo ou negativo.",
    "Adequacy bruta. γ = 0,12, η = 0,05, ω = 0,03, ρ = 0,10, δ = 0,05 e ζ = 0 estão declarados no grafo e no código, e "
    "is_valid() verifica que γ + η + ω + ρ + δ + ζ ≤ 0,45.",
    "Penalidade epistêmica e exposição de facetas (anti-diluição): o déficit num dever crítico para o domínio não pode ser "
    "diluído por facetas não críticas.",
    "Conjunto de veto. O veto opera na granularidade em que um dever pode efetivamente falhar: o déficit com guarda de um "
    "pilar é o pior gap entre suas facetas. θ = 0,65 / 0,60 / 0,60 / 0,65.",
    "Teto de adequacy, com a₀ = 0,40, a₁ = 0,40 e gap de teto igual a máx(gap material, pior déficit com guarda entre os "
    "pilares em veto).",
    "A supervisão modula a irreversibilidade efetiva, nunca a classe do veredicto por si só. O regime é inferido dos fatos "
    "declarados: O = 0 não especificado, 0 nenhum, 0,2 out-of-the-loop, 0,45 on-the-loop, 0,70 in-the-loop.",
    "Stakes. Invariante I38: para um mesmo caso, os stakes são ordenados por regime — in the loop ≤ on the loop ≤ none.",
    "Bar de decisão consciente dos stakes, ajustado sobre a escada r3 congelada (b₀ = 0,55).",
    "Probabilidade de falha e dispersão da consequência. μ = (0,15, 0,40, 0,20, 0,25): capacidade e conhecimento determinam "
    "a falha; W e M determinam o peso do stakes.",
    "Risco residual: attenua sem apagar. R_r nunca é zero; a capacidade observada de entrega modula o risco potencial.",
    "Banda de confiança de cada observação. A adequacy é recalculada integralmente nos modos pessimista e otimista, não "
    "por um valor pontual, e não pelo valor declarado.",
    "O gate de cobertura é um parâmetro declarado, não uma constante embutida (I44): um perfil que declara 23 dos 33 deveres "
    "se abstém mesmo quando o resto da aritmética é excelente. Abaixo do gate, modelo e rubrica abstêm juntos, e κ vale 1,000.",
    "Exposição transversal dos deveres. ζ = 0 por cânone: Ψ é registrado como diagnóstico de governança e não entra na "
    "pontuação.",
    "ReviewNeed ordena os casos que compartilham o mesmo veredicto segundo a revisão externa que esse veredicto exige. É "
    "declarado não decisório (D5.6) e está presente como campo auditável no grafo.",
    "Agência estratificada: agir e responder pelo ato não são a mesma coisa (Frankfurt, 1971), por isso a cadeia de delegação é "
     "avaliada pelo elo mais fraco e cada camada reporta seu resultado. Apenas "
    "1 dos 33 deveres é delegável.",
    "Escada de decisão, lexicográfica sobre Aa_low: primeiro a abstenção, depois o veto duro, depois a proibição categórica "
    "(stakes ≥ 0,30 e gap material ≥ 0,35), depois a revisão exigida, depois permitido com guardas e, por fim, permitido. A "
    "histerese de 0,05 só bloqueia a flexibilização.",
]


def sec(doc, name, items, level=None):
    if level is None:
        level = 2 if re.match(r"^\d+\.\d+", name) else 1
    doc.add_heading(name, level=level)
    for kind, payload in items:
        if kind == "p":
            para(doc, payload, align="justify")
        elif kind == "b":
            bullets(doc, payload)
        elif kind == "eq":
            latex, label, _ = EQS[payload]
            equation(doc, latex, label, NOTES_PT[payload], prefix="Equação")
        elif kind == "t":
            cap, header, rows, widths = payload
            table(doc, header, rows, widths, cap)
        elif kind == "f":
            path, cap = payload
            figure(doc, path, cap)


def main():
    doc = new_document()
    title_block(
        doc,
        "Relatório técnico-científico do modelo ETH-WCMK",
        "Luiz Palazzo e Tarcísio Vanzin",
        "Universidade Federal de Santa Catarina (UFSC), Programa de Pós-Graduação em Engenharia e Gestão do Conhecimento "
        "(PPGEGC), Brasil",
        "Núcleo formal v13 · ontologia v4.2 · corpus v7 · rodada 5 de validação. Cada número citado corresponde a um "
        "artefato listado no Apêndice A.",
    )
    para(doc,
        "Relatório técnico-científico, novembro de 2026. Código, artefatos de avaliação, ontologia e equações "
        "distribuídos junto ao texto: código sob licença MIT, textos e ontologias sob CC BY-SA 4.0.",
        style="SmallText", align="center", italic=True)

    doc.add_heading("Resumo executivo", level=1)
    para(doc, "Este relatório descreve o sistema ETH-WCMK em três partes. A primeira apresenta o modelo e sua ontologia "
             "conceptual: dois objetos — o caso ético (ETHCASE) e o perfil de agência delegada (WCMK) — ligados por uma "
             "geometria de relações entre deveres. A segunda descreve a camada formal executável: 33 deveres canônicos, seus "
             "requisitos, déficits, termos estruturais, limiares e uma escada de decisão de cinco veredictos (abstenção: o modelo recusa-se a julgar; proibição; revisão exigida; permitido com guardas; permitido). A terceira "
             "interpreta os resultados das baterias de testes: invariantes (propriedades que a aritmética deve satisfazer para qualquer entrada), probes adversários (entradas construídas para tentar quebrar essas propriedades), ablações (remover um mecanismo e medir o efeito) e sensibilidade de "
             "parâmetros, o espelho aritmético (recalcular o veredicto a partir do grafo RDF e compará-lo termo a termo com o núcleo) e a sensibilidade da concordância à própria rubrica normativa (o conjunto de regras que gera o gabarito contra o qual o modelo é medido).",
             align="justify")
    para(doc, "Os resultados medidos são: uma hierarquia estrutural demonstrada (S₂ ≥ S₃ ≥ S₄ para todo vetor de déficit, sem "
             "condições sobre os parâmetros); 69 testes de invariante e 2.064 probes adversários com 7.815 asserções e taxa de "
             "passagem 1,000; uma ontologia de 1.927.780 triplos validados que satisfaz 34 shapes SHACL (regras W3C de restrição aplicadas a nós do grafo; W3C, 2017) sem violações, "
             "detecta 76 de 76 fixtures (indivíduos construídos para violar exatamente uma shape) deliberadamente inválidos e reproduz a aritmética do núcleo com diferença máxima de "
             "1,61×10⁻¹²; e uma concordância com o ground truth normativo — o gabarito de referência produzido pela rubrica — de κ = 0,5336 (κ, o coeficiente de concordância de Cohen, 1960: acordo acima do esperado por acaso) global, 0,8167 nos casos em que as três "
             "lentes normativas convergem e 0,0526 nos casos contestados. A divergência entre painéis (0,6447, 0,3533, 0,3153) "
             "existe antes que o modelo fale: o teto do resultado é do instrumento, não do modelo.", align="justify")

    doc.add_heading("Notação e terminologia", level=1)
    para(doc, "Cada símbolo e cada expressão do relatório é definido no ponto em que aparece pela primeira vez. A tabela abaixo "
             "é o índice dessas definições.", align="justify")
    table(doc, ["Expressão", "Significado", "Onde é definida"], NOTATION_PT, widths=[1.5, 3.8, 0.9],
          caption_text="Tabela 1. Notação usada no relatório.")
    sec(doc, "1. Objetivo e alcance", [
        ("b", [
            "Descrever o modelo: que objetos representa, quais elementos tem cada um e como se conectam.",
            "Descrever a ontologia v4.2: classes, propriedades, shapes SHACL, grafo de instâncias e sua validação.",
            "Interpretar os resultados das baterias — que mecanismo funciona, qual não, qual foi rejeitado e com que evidência.",
            "Declarar explicitamente as limitações e os defeitos detectados, incluída a não executabilidade de uma bateria.",
        ]),
        ("p", "Sistemas de IA mediate hoje decisões com consequências para pessoas identificáveis — uma fila de triagem, uma "
             "decisão de crédito, uma moderação de conteúdo, uma rota despachada por um veículo autônomo (Mittelstadt et al., "
             "2016; Eubanks, 2018; Zuboff, 2019). O modelo pertence à vertente deontológica da ética de máquinas. Enquanto as abordagens bottom-up aprendem valores "
             "dos dados ou da interação e as de alinhamento optimizam uma função objetivo (Moor, 2006; Floridi, 2004; Wallach & Allen, "
             "2008; Allen, Smit & Wallach, 2005; Anderson & Anderson, 2011; Bostrom & Yudkowsky, 2016; Dignum, 2019), o ETH-WCMK "
             "declara deveres e verifica se foram cumpridos. A camada normativa que operacionaliza vem dos instrumentos de "
             "governança que enumeram deveres sem formalizar como um caso concreto os satisfaz (Jobin et al., 2019): a "
             "Recomendação da UNESCO (UNESCO, 2021), a Recomendação da OECD (OECD, 2024), a Convenção-Quadro do Council of Europe "
             "(Council of Europe, 2024), o AI Act europeu (European Union, 2024), ISO/IEC 42001 (ISO/IEC, 2023) e o AI Risk "
             "Management Framework (NIST, 2023)."),
        ("p", "O documento é complementar ao PAPER v14: o paper argumenta uma tese, e este relatório detalha os elementos do "
             "sistema e a leitura das medições. Ambos compartilham os mesmos artefatos e a mesma regra: nenhum número aparece "
             "sem um artefato que o derive."),
    ])

    sec(doc, "2. Método: a cadeia de evidência", [
        ("p", "A rastreabilidade não é decorativa: um veredicto só é auditável quando as quantidades intermediárias ficam "
             "registradas, e não apenas o resultado final (Miller, 2019; Williams et al., 2022). A representação é canônica, não "
             "lexical: dois casos descritos com palavras diferentes entram na mesma aritmética apenas se ocupam os mesmos papéis "
             "conceptuais (Peirce, 1931-1958; Gärdenfors, 2000)."),
        ("p", "O sistema está organizado para que qualquer afirmação possa ser rastreada. O núcleo formal vive em "
             "_analysis/formal_core (core.py, geometry.py, facet_registry.py, fact_grounding.py) e em sua suite de invariantes; "
             "os geradores do corpus e da rubrica normativa em _analysis/corpus; o gerador e o validador da ontologia em "
             "_analysis/ontology; e os artefatos de cada corrida em Evaluacoes/r5/. O manifest da rodada (manifest_r5.json) "
             "registra 51 artefatos, 22 execuções com sua duração, o SHA-256 de cada arquivo e a revisão de git. As rodadas r2 "
             "e r3 estão congeladas: não são sobrescritas, e os resultados novos entram como delta sobre elas. Toda essa evidência "
             "está disponível no repositório: o núcleo e os testes sob licença MIT; ontologias, registro de facetas, definições do "
             "corpus e textos sob CC BY-SA 4.0; o RDF gerado em Ontologias/ontology_v4_2/, cada artefato medido em Evaluacoes/r5/, "
             "e as rodadas r2 e r3 somente para leitura. Nenhuma afirmação do relatório exige acesso além desses arquivos e dos "
             "cinco comandos listados na seção 10."),
        ("t", ("Tabela 2. Componentes do sistema e onde reside cada evidência.",
              ["Componente", "Elementos", "Artefato de referência"],
              [["Núcleo formal", "4 arquivos, ~1.070 linhas, 22 equações, invariantes I1–I44", "_analysis/formal_core/; suite pytest (69 testes, 45,75 s)"],
               ["Camada geométrica", "15 slots do face lattice, 108 incidências, α derivada", "geometry.py; censo do lattice na validação RDF"],
               ["Canon de deveres", "33 facetas, β por pilar, 12 guardas duras, 4 políticas de agregação", "facet_registry.py; Ontologias/ontology_v4_2/02_facets.ttl"],
               ["Ontologia", "69 classes, 309 propriedades, 34 node shapes, 1.927.780 triplos", "Ontologias/ontology_v4_2/; ontology_v4_2_validation.json (301,9 s)"],
               ["Corpus", "220.400 confrontações; 1.520 casos; 145 perfis", "Evaluacoes/r5/corpus_v7_*.jsonl; corpus_v7_coverage.json"],
               ["Ground truth", "34 regras derivadas de instrumentos; 3 lentes normativas", "gold_panels_v5.py; corpus_v7_gold.jsonl"],
               ["Baterias", "B3, B7, B8, B12, B14, B15, B20–B26", "Evaluacoes/r5/B*.json; run_all_batteries.py --round r5"]],
              [1.4, 2.6, 2.4]),
        ),
    ])

    sec(doc, "3. O modelo: dois objetos e uma ponte", [
        ("f", (FIG + "/fig1_pipeline.png", "Figura 1. Pipeline da confrontação: um ETHCASE e um perfil WCMK se encontram no "
              "núcleo formal, que produz as quantidades intermediárias e o veredicto; a ontologia espelha essa aritmética.")),
    ])
    sec(doc, "3.1 O caso ético (ETHCASE)", [
        ("p", "Um caso é um objeto com domínio, severidade, irreversibilidade, modo prudencial, horizonte temporal, incerteza "
             "epistêmica U_E e um conjunto de fatos verificáveis. Os fatos não são decoração: são a base da ancoragem factual "
             "(E30) e da inferência do regime de supervisão. Cada elemento do caso tem contraparte na ontologia."),
        ("t", ("Tabela 3. Elementos do ETHCASE e sua função na aritmética.",
              ["Elemento", "O que declara", "Onde se usa"],
              [["Domínio (13)", "SA, JS, IC, FI, PD, GP, IM, ED, MA, TS, RS, TB, DS", "criticidade da faceta por domínio; requisito do dever"],
               ["Severidade (4 bandas)", "low / medium / high / critical", "stakes, bar de decisão, σ do risco"],
               ["Irreversibilidade (3 níveis)", "reversible / partially / irreversible", "stakes; atenuada pela supervisão (Eq. 12)"],
               ["Modo prudencial (4)", "standard / elevated / maximum / floor", "piso de prudência no bar e no risco"],
               ["Horizonte (4)", "immediate / short / medium / long", "stakes e requisito de K9 (revisão periódica)"],
               ["U_E (0–1)", "incerteza epistêmica do caso", "abstenção epistêmica (E29) e requisito dos deveres K"],
               ["Fatos de processo", "logs, notificação, canal de apelação, auditoria independente, consentimento, saída", "ancoragem E30; inferência do regime de supervisão"],
               ["Partes, consequências, evidências", "quem, qual dano, qual prova", "grafo ETHCASE; ReviewNeed e risco residual"]],
              [1.5, 2.6, 2.3]),
        ),
    ])
    sec(doc, "3.2 O perfil de agência (WCMK)", [
        ("p", "Um perfil declara níveis por dever (33), uma confiança por nível, o subconjunto de deveres que efetivamente assumiu "
             "— daí a cobertura —, o regime de supervisão e uma política de agregação por faceta. A diferença entre o que se "
             "declara e o que os fatos permitem afirmar resolve-se pelo teto observacional: um nível não pode superar aquilo que "
             "os verificadores do caso sustentam. O perfil não descreve um agente virtuoso (Vallor, 2016): declara o que foi "
             "assumido e o que os fatos sustentam."),
        ("t", ("Tabela 4. Elementos do perfil WCMK.",
              ["Elemento", "O que é", "Observação"],
              [["Nível de faceta v_f ∈ [0,1]", "capacidade ou obrigação declarada para um dever", "limitado pelo teto E30 (Eq. 5)"],
               ["Confiança c_f ∈ [0,1]", "grau de evidência desse nível", "define a banda v_f⁻ / v_f⁺ (Eq. 17)"],
               ["Cobertura", "deveres declarados / 33", "gate declarado 0,70; abaixo disso, ABSTAIN (Eq. 18)"],
               ["Guardas duras (12 facetas)", "piso de nível abaixo do qual o déficit é crítico", "C3 0,55; C6 0,60; C7 0,45; K6 0,50; M1 0,60; M4 0,55; M7 0,50; M8 0,50; M9 0,50; M10 0,50; W2 0,55; W6 0,50"],
               ["Política de agregação", "média ponderada; média com guarda; override por limiar; média penalizada pela incerteza", "decide como os deveres se projetam sobre os pilares"],
               ["Regime de supervisão", "in the loop / on the loop / none", "inferido dos fatos, nunca inventado (Eq. 12)"]],
              [1.9, 2.4, 2.3]),
        ),
    ])
    sec(doc, "3.3 Os quatro pilares e a geometria das relações", [
        ("p", "W (Want), C (Can), M (Must) e K (Know) são magnitudes independentes, não frações de um mesmo simplex: um agente "
             "pode ser competente e obrigado ao mesmo tempo. O tetraedro não mede o estado do agente; indexa a relação entre "
             "deveres, dispositivo representativo no sentido dos espaços conceptuais (Gärdenfors, 2000). Seu face lattice tem quinze slots — quatro vértices, seis arestas, quatro faces e uma célula — e cada dever "
             "ocupa a face que abrange. Um dever unipilar ocupa um vértice; bipilar, uma aresta; tripilar, uma face. O censo atual "
             "é: 1 faceta unipilar, 10 bipilares, 22 tripilares e 0 quadripilares. Nenhum dever pode tocar os quatro pilares, o "
             "que impede que um déficit se dilua por compensação."),
        ("f", (FIG + "/fig2_lattice.png", "Figura 2. Face lattice da 3-simplex com os termos estruturais S₂, S₃ e S₄.")),
        ("eq", 0),
        ("eq", 1),
        ("p", "Proposição 1. Se o peso de cada aresta é um terço da soma dos pesos das faces que a contêm, e os quatro pesos de "
             "face somam um, então, para todo vetor de déficit d ≥ 0, S₂ ≥ S₃ ≥ S₄. A prova é breve: cada aresta do tetraedro "
             "está em exatamente duas faces, de modo que os pesos derivados somam um; para cada face, a soma dos pesos de suas "
             "três arestas é proporcional ao peso da face; e o mínimo sobre uma aresta nunca é menor que o mínimo sobre a face que "
             "a contém, porque a t-norm de Gödel é monótona. Em v12 a desigualdade exigia uma condição sobre α; em v13 α não é "
             "um parâmetro livre e a condição desaparece. A reparametrização não altera nenhum número publicado: com β = ¼, "
             "α = 1/6, exatamente o valor calibrado em v10–v12."),
    ])

    sec(doc, "4. O núcleo formal: elementos e equações", [
        ("p", "O núcleo é aritmética determinista. A partir do caso e do perfil calcula, nesta ordem: projeção de níveis e "
             "requisitos sobre os quatro pilares (o que cada dever exige do agente e o que o agente efetivamente declara), déficits "
             "(a distância entre exigência e entrega, por pilar e por dever), termos estruturais (S₂, S₃, S₄: as correções de face, "
             "aresta e vértice do tetraedro), adequacy bruta, falhas de guarda e gap material (a maior lacuna de um dever abaixo do "
             "mínimo exigido pelo domínio), stakes (o peso das consequências do caso, ordenado por regime) e veto (a condição em que "
             "nenhum score de adequacy sustenta o veredicto), banda de adequacy (a faixa provável do valor, não um número único), "
             "condições de abstenção, risco residual, necessidade de revisão e veredicto. "
             "Todas essas quantidades são campos declarados na ontologia, de modo que o veredicto pode ser reconstruído a partir "
             "do grafo."),
    ])
    sec(doc, "4.1 O canon de 33 deveres", [
        ("p", "O canon está declarado, não sugerido: o canon é deontológico no sentido clássico (Kant, 2012; Ross, 2002): cada dever tem código, etiqueta, vetor β sobre os pilares, criticidade por "
             "domínio, política de agregação e, quando corresponde, guarda dura com piso. A tabela abaixo é a versão canônica "
             "verificada contra facet_registry.py e contra o registro RDF: os 33 indivíduos da RDF coincidem com os 33 do CSV e "
             "com os 33 do código."),
        ("t", ("Tabela 5. Canon de facetas: β sobre (W, C, M, K), número de pilares, política de agregação e piso de guarda.",
              ["Código", "Dever", "β (W / C / M / K)", "Pilares", "Política", "Guarda"],
              [list(r) for r in FACETS_PT], [0.5, 2.2, 1.3, 0.5, 1.5, 0.6]),
        ),
    ])
    sec(doc, "4.2 Requisito, projeção e déficits", [
        ("eq", 2), ("eq", 3), ("eq", 4), ("eq", 5),
        ("p", "O requisito de um dever depende do caso: o mesmo dever exige mais num contexto de severidade crítica do que num "
             "contexto banal. A projeção dos níveis declarados sobre os pilares aplica a política de agregação antes de projetar, "
             "e o déficit é calculado por pilar, não por média: a não compensação se expressa nesse nível, de modo que um W alto "
             "não pode tapar um M baixo."),
    ])
    sec(doc, "4.3 Saliência condicional, adequacy e veto", [
        ("eq", 6), ("eq", 7), ("eq", 8), ("eq", 9), ("eq", 10),
        ("p", "A adequacy bruta penaliza o déficit agregado, os termos estruturais do lattice (γ, η, ω), a penalidade epistêmica u "
             "e a exposição de deveres Φ. O veto opera na granularidade em que um dever pode efetivamente falhar: o déficit com "
             "guarda. O teto de adequacy converte um gap material concentrado em redução da pontuação, e a adequacy é recalculada "
             "integralmente dentro da banda de confiança (Eq. 17), não pelo valor pontual."),
    ])
    sec(doc, "4.4 Supervisão, stakes e risco residual", [
        ("eq", 11), ("eq", 12), ("eq", 13), ("eq", 14), ("eq", 15),
        ("p", "O regime de supervisão não é assumido: é inferido dos fatos declarados (canal de revisão, auditoria "
             "independente) e atenua a irreversibilidade efetiva sem mudar, por si só, a classe do veredicto. Invariante I38: os "
             "stakes são ordenados por regime — in the loop ≤ on the loop ≤ none — porque mais supervisão reduz o stakes efetivo. "
             "O risco residual nunca é zero: a responsabilidade por consequências que sobrevivem ao ato não se extingue com o "
             "ato (Jonas, 1984), e a capacidade observada de entrega atenua o risco potencial sem apagá-lo."),
    ])
    sec(doc, "4.5 Incerteza, cobertura e abstenção", [
        ("eq", 16), ("eq", 17),
        ("p", "Duas condições distintas levam a abster-se: falta de cobertura (menos de 70% dos 33 deveres declarados, E26′) e "
             "conflito epistêmico (U_E ≥ 0,60 com um piso de conhecimento K abaixo de 0,65, E29). A primeira declara ignorância "
             "sobre o agente; a segunda, sobre o caso. O gate de cobertura é um parâmetro declarado no grafo e no código, não uma "
             "constante embutida (I44)."),
    ])
    sec(doc, "4.6 Dever transversal e necessidade de revisão", [
        ("eq", 18), ("eq", 19),
        ("p", "ReviewNeed ordena os casos que compartilham veredicto segundo a revisão externa que esse veredicto exige, e é "
             "guardado como campo auditable. A saliência condicional λ(E) e a exposição transversal Ψ estão implementadas, mas seu "
             "coeficiente canônico é zero: ambas foram medidas e seu efeito sobre a concordância é nulo ou negativo, portanto "
             "permanecem inertes como diagnóstico de governança (D5.2, D5.3)."),
    ])
    sec(doc, "4.7 A escada de decisão e a agência estratificada", [
        ("eq", 20), ("eq", 21),
        ("f", (FIG + "/fig3_ladder.png", "Figura 3. Escada de decisão, seus limiares e a histerese que governa as mudanças de "
              "veredicto em direção a uma leitura mais permissiva.")),
        ("p", "A escada é lexicográfica sobre o limite pessimista Aa_low: primeiro a abstenção, depois o veto duro, em seguida a "
             "proibição categórica (stakes ≥ 0,30 e gap material ≥ 0,35), depois a revisão exigida, depois a permissão com "
             "guardas e, por fim, a permissão. Um veto disparado nunca é revertido pela pontuação. A histerese (0,05) só bloqueia "
             "o flexibilização: um veredicto pode tornar-se mais permissivo se Aa_low supera o bar mais o margen; um endurecimento "
             "não é filtrado."),
    ])
    sec(doc, "4.8 Parâmetros canônicos", [
        ("t", ("Tabela 6. Parâmetros do núcleo v13, seu estado e a equação em que aparecem.",
              ["Parâmetro", "Valor canônico", "Estado", "Equação"],
              [list(r) for r in CALIB_PT], [2.2, 1.9, 1.8, 0.7]),
        ),
    ])

    sec(doc, "5. A camada semântica: ontologia v4.2", [
        ("f", (FIG + "/fig7_ontology.png", "Figura 4. Ontologia v4.2: módulos, grafo de instâncias e gates de validação.")),
    ])
    sec(doc, "5.1 Estrutura e namespaces", [
        ("p", "A ontologia é gerada a partir do núcleo executável: cada número declarado em RDF é o número que o código Python "
             "usa. Os namespaces são eth: (classes e aritmética), fac: (facetas), cal: (calibração), norm: (deontologia), cse: "
             "(casos), ag: (agentes), além de rdf, rdfs, owl, xsd, sh e skos. Há sete módulos de definição, dois arquivos de "
             "shapes SHACL e dois conjuntos de fixtures (válidos e inválidos), todos dentro da recomendação OWL 2, do PROV-O e do SHACL do W3C (W3C, 2012; 2014; 2017)."),
        ("t", ("Tabela 7. Módulos da ontologia e triplos declarados.",
              ["Módulo", "Conteúdo", "Triplos"],
              [list(r) for r in MODULES_PT], [2.2, 3.4, 1.0]),
        ),
        ("p", "Total validado: 8.509 triplos de módulo mais 1.919.283 triplos de instância = 1.927.780 triplos."),
    ])
    sec(doc, "5.2 Classes", [
        ("p", "O grafo declara 69 owl:Class. A hierarquia tem uma raiz eth:Entity e quatro blocos: contexto e enumerações, camada "
             "deontológica, camada de agência e camada de decisão."),
        ("t", ("Tabela 8. Distribuição das 69 classes declaradas.",
              ["Bloco", "Classes", "Número"],
              [list(r) for r in CLASSES_PT], [1.8, 4.2, 0.5]),
        ),
    ])
    sec(doc, "5.3 Propriedades", [
        ("p", "São declaradas 309 propriedades únicas: 84 objetivas (relações entre indivíduos) e 225 de datatype (números, "
             "strings, booleanos). 192 são FunctionalProperty e 2 TransitiveProperty (delegatesTo e chainPrefixOf). Cada "
             "propriedade tem domain e range declarados; as exceções detectadas estão na seção de defeitos."),
        ("t", ("Tabela 9. Elementos do vocabulário.",
              ["Elemento", "Quantidade", "Comentário"],
              [["owl:Class", "69", "hierarquia com subClassOf e disjointWith"],
               ["Propriedades objetivas", "84", "relações caso→dever, perfil→observação, cadeia→camada"],
               ["Propriedades datatype", "225", "níveis, confianças, limiares, veredictos, cobertura"],
               ["FunctionalProperty", "192", "um valor por indivíduo e propriedade"],
               ["TransitiveProperty", "2", "delegatesTo, chainPrefixOf"],
               ["Node shapes SHACL", "34 (27 v4 + 7 v6)", "203 nós de restrição, 189 caminhos distintos"],
               ["Indivíduos nomeados", "29.310", "29.496 asserções de tipo"],
               ["Slots do lattice", "15, 108 incidências", "pesos de vértice 0,30/0,25/0,25/0,20; arestas 1/6; faces 1/4; célula 1,0"]],
              [2.2, 1.4, 3.1]),
        ),
    ])
    sec(doc, "5.4 Restrições SHACL", [
        ("p", "As shapes convertem as invariantes do núcleo em restrições verificáveis sobre o grafo (W3C, 2017). A ConfrontationShape, por "
             "exemplo, declara 37 restrições: veredicto dentro dos cinco enumerados, adequacy em [0,1], banda dentro da banda de "
             "observação, stakes e seu teto (2,1), gap material, cobertura ∈ [0,70, 1,0] quando o veredicto não é ABSTAIN e "
             "presença obrigatória dos campos aritméticos. A shape de faceta exige que nenhum β ultrapasse 0,80 num único pilar, "
             "que a soma de β por faceta seja 1 e que nenhuma faceta toque os quatro pilares."),
        ("p", "A contraprova do gate são os fixtures inválidos: 76 indivíduos deliberadamente incorretos (nível fora de [0,1], β "
             "que não soma 1, veredicto sem banda, cobertura abaixo do gate com veredicto não abstido, cadeia sem camada "
             "responsável, entre outros). O validador detectou 76/76 e cada violação foi atribuída à forma esperada: 1.246 "
             "violações no total, distribuídas entre MinCount (366), Datatype (746) e Class (75). Um validador que não detecta "
             "os casos inválidos não vale nada: por isso essa prova faz parte do gate."),
    ])
    sec(doc, "5.5 Grafo de instâncias", [
        ("t", ("Tabela 10. Instâncias geradas a partir do corpus v7.",
              ["Tipo", "Indivíduos", "Origem"],
              [list(r) for r in INSTANCES_PT], [2.4, 1.1, 3.1]),
        ),
        ("p", "A distribuição de veredictos asertada no grafo coincide com a do corpus instanciado: PROHIBIT 2.671, ABSTAIN 593, "
             "REVIEW_REQUIRED 488, ALLOW_WITH_GUARDS 2 e ALLOW 1 sobre as 3.755 confrontações."),
    ])
    sec(doc, "5.6 Validação", [
        ("t", ("Tabela 11. Resultados da validação da ontologia (gate G4′).",
              ["Prova", "Resultado", "Detalhe", "Duração"],
              [list(r) for r in VALID_PT], [2.6, 2.0, 2.3, 0.9]),
        ),
        ("p", "O espelho aritmético lê do grafo todos os níveis, confianças, requisitos, criticidades, pisos de guarda, λ, μ, θ, "
             "pesos do lattice, valores de banda, pesos do stakes e limiares da escada; recalcula o déficit por dever (D), S₂, S₃, "
             "S₄, a exposição transversal, o gap "
             "material, o conjunto de veto, o teto de adequacy, a adequacy, σ (a largura da banda), bar (o limiar ajustado aos "
             "stakes) e o ratio (a razão entre adequacy e bar), e executa a escada em Python. A comparação com core.decide "
             "e com os literais do grafo dá uma diferença máxima de 1,614×10⁻¹², dentro da tolerância declarada de 1×10⁻⁶ "
             "(D5.20), e zero divergências de veredicto nas três "
             "comparações. Os 352 pares em que o nível declarado excede o teto E30 o fazem por ≤ 5×10⁻⁵, exatamente metade do "
             "passo de armazenamento (4 decimais): não é violação, é a precisão declarada."),
    ])
    sec(doc, "5.7 Defeitos e imperfeições detectadas", [
        ("p", "A validação passou, mas o grafo não é perfeito. Estes defeitos são declarados aqui porque condicionam a "
             "interpretação dos resultados e porque o projeto não admite silenciá-los:"),
        ("b", DEFECTS_PT),
    ])

    sec(doc, "6. Corpus e ground truth normativo", [
        ("p", "O corpus v7 contém 220.400 confrontações (1.520 casos × 145 perfis: 36 tipos de persona — arquétipos de perfil "
             "gerados com um déficit declarado em um pilar — e um perfil "
             "autodeclarado). Os casos têm duas camadas: 1.200 estruturados (camada A) e 320 narrativos (camada B). Os perfis são "
             "genuinamente incompletos: declaram entre 9 e 33 dos 33 deveres, o que produz 34.615 abstenções (18.240 por "
             "cobertura e 16.375 por conflito epistêmico). Nenhum par atinge Aa ≥ 0,999: a adequacy máxima observada é 0,9508 "
             "(média 0,3551, mediana 0,3462). A taxa de veto é 0,906 e o veto duro responde por 0,1345 das prohibitivas."),
        ("t", ("Tabela 12. Distribuição de veredictos e concordância com o ground truth (220.400 pares).",
              ["Veredicto", "Modelo", "Consenso normativo"],
              [["PROHIBIT", "152.439", "162.507"],
               ["REVIEW_REQUIRED", "32.996", "22.687"],
               ["ABSTAIN", "34.615", "30.077"],
               ["ALLOW_WITH_GUARDS", "349", "2.653"],
               ["ALLOW", "1", "2.476"],
               ["Consenso entre painéis", "A–C 0,6447; A–B 0,3533; B–C 0,3153", "consenso kernel-only 14,19%"]],
              [2.4, 1.7, 2.0]),
        ),
        ("p", "O ground truth não é uma opinião: são 34 regras derivadas de instrumentos nomeados — Rio (1992), UDHR (United Nations, 1948), CRC (United "
             "Nations, 1989), GDPR (European Union, 2016), Belmont (1978), a Declaration of Helsinki (1964), ILO (International Labour "
             "Organization, 1998), ACM/IEEE, ISO 26262 (ISO, 2018), IEC 62443, ISO 27001 (ISO/IEC, 2023), NIST CSF (NIST, 2025), NIST AI RMF "
             "(NIST, 2023), OECD (OECD, 2024), a Convenção-Quadro do Council of Europe (Council of Europe, 2024), o AI Act europeu "
             "(European Union, 2024) e a Recomendação da UNESCO (UNESCO, 2021) — cada regra com um instrumento, um dever, uma "
             "condição e "             "uma direção; todas disparam em pelo menos 50 casos. As três lentes (prudencial, de direitos e de deveres) votam "
             "cada caso. O consenso kernel-only — os casos em que as três lentes coincidem — cobre 14,19% do corpus e é o estrato "
             "onde o resultado pode ser defendido sem controvérsia normativa. A concordância exata modelo×painel é 0,7886, e "
             "a um passo de distancia 0,9809."),
        ("f", (FIG + "/fig4_strata.png", "Figura 5. κ por estrato de consenso e κ sob as priors normativas da rubrica.")),
        ("f", (FIG + "/fig6_verdicts.png", "Figura 6. Distribuição de veredictos: modelo frente às três lentes normativas, e as "
              "duas classes de abstenção.")),
    ])

    sec(doc, "7. Resultados dos testes, interpretados", [
        ("t", ("Tabela 13. Gates da rodada 5 e seus veredictos.",
              ["Gate", "Conteúdo", "Veredicto", "Evidência"],
              [list(r) for r in GATES_PT], [0.5, 2.4, 1.5, 1.9]),
        ),
    ])
    sec(doc, "7.1 Invariantes e geometria", [
        ("p", "A suite tem 69 testes de invariante (I1–I44, mais geometria e ancoragem). Os novos da rodada: I34 testa a "
             "Proposição 1 sobre a grade completa de déficits; I35 recusa uma calibração incoherente; I36 faz o regime de "
             "supervisão não especificado idêntico ao de v12 e declara os pesos do ReviewNeed; I37 demonstra que λ(E) é a "
             "identidade quando s = 0; I38 ordena os stakes por regime; I39 prova que a adequacy com ζ = 0 difere da de v12 "
             "exatamente por ζ·Ψ; e I44 valida o gate de cobertura como parâmetro. O censo do lattice calculado a partir do "
             "código dá 15 slots, 108 incidências, pesos estruturais somando 1,0000000000 e marginal uniforme 1/6 no β canônico."),
        ("p", "Interpretação. O valor da suite não está no número de testes, mas no que ela impede. I35 torna impossível carregar uma calibração incoherente; I38 transforma a ordenação dos stakes em propriedade do modelo, e não em expectativa sobre os parâmetros; I44 converte o gate de cobertura em uma variável visível e ajustável pelo auditor. Um revisador pode rederivar a geometria a partir do código sem depender do texto: os quinze slots do lattice, seus pesos e suas incidências são calculados, não declarados."),
    ])
    sec(doc, "7.2 Probes adversários", [
        ("p", "2.064 probes adversários e 7.815 asserções foram reexecutados contra o núcleo v13 com taxa de passagem 1,000: "
             "zero violações de monotonicidade, nenhuma brecha de não compensação, nenhuma evasão de guarda e o veto duro não é "
             "revertido pela pontuação em nenhum probe. Entre eles está o caso que revelou a lacuna de compensação de v12 "
             "(C3 = 0 com um nível alto em outro dever elevando o pilar C acima do piso do dever), que agora produz falha de "
             "guarda e gap material. Que o resultado seja idêntico ao da rodada anterior é o esperado: a Proposição 1, λ(E) com "
             "s = 0, ReviewNeed e o gate declarado não alteram nenhuma asserção de não compensação (D5.14)."),
        ("p", "Interpretação. Uma taxa de passagem de 1,000 não prova que o modelo esteja certo; prova que nenhuma entrada construída para quebrá-lo conseguiu quebrar as promessas que a aritmética faz sobre si mesma. A consequência prática é estreita, mas utilizável: a lacuna de compensação encontrada em v12, um nível alto em um dever cobrindo um dever falho em outro, passa a registrar falha de guarda e gap material, de modo que a auditoria cita um evento e não interpreta uma pontuação."),
    ])
    sec(doc, "7.3 Que mecanismos mudam realmente a concordância", [
        ("p", "Cada mecanismo foi implementado, ativado em sua faixa canônica e medido sobre 130.680 pares do corpus (1.080 "
             "casos × 120 perfis) contra o consenso, com intervalos de confiança por bootstrap pareado sobre a diferença "
             "(remostragem repetida dos pares para estimar a incerteza daquela diferença)."),
        ("t", ("Tabela 14. Efeito dos mecanismos v13 sobre κ (130.680 pares, escada r3 congelada).",
              ["Variante", "κ", "Δ frente à base [IC 95%]", "Adequacy média", "Veredictos P / R / A / AWG"],
              [list(r) for r in MECHANISMS], [2.4, 0.7, 2.2, 1.0, 1.8]),
        ),
        ("p", "Somente a supervisão inferida dos fatos e as β diferenciadas melhoram a concordância, e seus efeitos são "
             "significativos. A saliência adaptativa e o dever transversal não: κ cai quando são ativados. Ambos continuam "
             "disponíveis no núcleo e inertes por cânone, com os números publicados. Na análise de sensibilidade (Sec. 7.6) saturam o índice de ordem total "
             "justamente porque atuam sobre os limiares de decisão: movem as saídas, não o acordo."),
        ("p", "Interpretação. Dois mecanismos mudam o veredicto por uma razão que a auditoria pode nomear; dois não. Inferir o regime de supervisão a partir dos fatos declarados eleva a concordância porque um caso revisado é tratado de forma diferente de um caso não revisado. Diferenciar as β eleva a concordância porque deveres indistinguidos passam a ser distinguidos. Saliência e dever transversal movem as saídas sem mover o julgamento, por isso permanecem como diagnósticos: a equipe de governança pode inspecioná-los, mas o veredicto não depende deles. A regra que a rodada estabelece é que um mecanismo é adotado apenas quando seu efeito é medido, tem sinal e é significativo."),
    ])
    sec(doc, "7.4 Ablação do canon", [
        ("p", "Remover as doze guardas duras faz κ cair de 0,4633 para 0,1399 (Δ −0,3234; IC −0,3306 a −0,3147): as guardas não "
             "são decoração, são a não compensação. Reduzir cada dever ao seu pilar primário leva κ a 0,2691 (Δ −0,1942). "
             "Remover uma guarda individual muda κ em menos de 0,0042 em qualquer direção, o que explica por que nenhuma guarda "
             "pode ser defendida por seu efeito marginal sobre κ: seu valor é estrutural."),
        ("t", ("Tabela 15. Ablação (48.400 pares, 400 casos × 120 perfis).",
              ["Ablação", "κ", "Δ"],
              [list(r) for r in ABLATION], [3.4, 0.8, 1.1]),
        ),
        ("p", "Interpretação. O peso normativo do modelo está exatamente onde o projeto o colocou. Remover as doze guardas duras leva κ de 0,4633 a 0,1399, uma queda de 69,8%: as guardas não são um detalhe de estilo, são o mecanismo que produz o comportamento que as rubricas valorizam. Os deltas individuais dizem o contrário, nenhuma guarda se defende isoladamente, e o canon deve ser defendado como conjunto. Para uma organização que implanta o modelo, isso significa que os pisos não podem ser negociados dever a dever sem destruir a propriedade para a qual o modelo existe."),
    ])
    sec(doc, "7.5 Ancoragem factual (E30)", [
        ("p", "Em 43.210 pares, 42.464 (98,27%) continham pelo menos uma declaração contrariada por um fato verificável. A regra "
             "aplicou 224.097 tetos; o excesso médio declarado sobre o teto foi 0,3611. A ancoragem mudou o veredicto de 18.898 "
             "pares (43,74%), dos quais 15.153 passaram de revisão a proibição. κ contra os painéis aumenta de 0,2463 sem ancoragem "
             "a 0,5526 com ela: é o mecanismo que converte autodeclarada em evidência, e a razão pela qual o parâmetro de "
             "força s é declarado (com s = 0 o núcleo se comporta exatamente como v11)."),
        ("p", "Interpretação. Declarar um nível não é entregá-lo. Quase todo perfil afirma um nível que os fatos do próprio caso contradizem, e corrigir isso muda quase metade dos veredictos. O aumento de κ de 0,2463 para 0,5526 não é efeito de ajuste, é a diferença entre julgar o que o agente afirma e julgar o que o agente pode demonstrar. Uma trilha de auditoria construída apenas sobre níveis declarados superestimaria sistematicamente a agência."),
    ])
    sec(doc, "7.6 Sensibilidade dos parâmetros", [
        ("p", "Efeitos elementares de Morris — uma triagem de primeira ordem que varia um parâmetro por vez e registra a mudança resultante na saída (200 trajetórias; Morris, 1991) e um desenho de Sobol pareado (Sobol, 2001; Saltelli et al., 2008) com N = 1.024 sobre o espaço de "
             "calibração de 12 dimensões, foram executados sobre um painel de 12 casos reais que cobrem os 13 domínios e os "
             "cinco veredictos. Com saídas que são funções degrau nas fronteiras de decisão, os índices de ordem total saturam "
             "perto de 1; as grandezas reportáveis são os índices de primeira ordem e as médias de Morris."),
        ("t", ("Tabela 16. Índice de primeira ordem S₁ de Sobol para parâmetros selecionados.",
              ["Parâmetro", "S₁ sobre adequacy média", "S₁ sobre abstenção", "S₁ sobre risco residual", "S₁ sobre ReviewNeed", "S₁ sobre permissividade"],
              [list(r) for r in SOBOL], [1.8, 1.1, 1.0, 1.1, 1.1, 1.4]),
        ),
        ("p", "O gate de cobertura é a alavanca dominante (S₁ = 0,749 sobre adequacy; 1,000 sobre abstenção), o que explica que "
             "tenha deixado de ser constante implícita para virar parâmetro declarado. γ é o coeficiente estrutural maior (0,123). "
             "A atenuação por supervisão não afeta a adequacy — os veredictos estão saturados —, mas é o motor dominante do veto "
             "duro (S₁ = 0,701), e θ_base contribui com 0,262. O expoente de saliência tem μ* de Morris 0,0004: inerte na "
             "configuração canônica. Os coeficientes zero são inertes no valor declarado, não inertes em princípio: para a "
             "saliência, a ordem total é 0,9998. Essa é a diferença entre um parâmetro que não faz nada e um parâmetro cujo "
             "valor não foi declarado."),
        ("p", "Interpretação. Dois parâmetros governam o modelo, e ambos devem constar no registro de auditoria em lugar de residir em um valor-padrão do código: o gate de cobertura decide quando o modelo pode falar, e a penalidade estrutural decide quanto pesa um déficit. Todo o resto é comparativamente plano, inclusive coeficientes a que rodadas anteriores dedicaram esforço. Para quem implanta, é uma constatação de governança, não uma curiosidade numérica, porque as configurações de maior influência definem o alcance do julgamento e precisam ser declaradas, versionadas e revisadas."),
    ])
    sec(doc, "7.7 O espelho aritmético", [
        ("p", "O espelho recalcula as 220.400 confrontações do corpus v7 a partir dos fatores de persona, do jitter, do "
             "requisito do caso, do subconjunto declarado de deveres e dos tetos observacionais, e compara cada grandeza com a "
             "armazenada no corpus. A diferença absoluta máxima é 0,0 para S₂, S₃, S₄, adequacy bruta, limites da banda, bar, "
             "stakes, risco residual, termos estruturais, penalidade epistêmica, gap material e conjunto de veto; há zero "
             "divergências de veredicto e a distribuição recalculada é idêntica à armazenada. Tempo: 121,9 s. A cautela "
             "metodológica é que alimentar o espelho com os níveis armazenados e arredondados (4 decimais) produz diferenças de "
             "até 1,7×10⁻² que ultrapassam pisos de guarda; o espelho fiel reconstrói os níveis sem arredondar antes de chamar o núcleo."),
        ("p", "Interpretação. O espelho fecha a distância entre o texto e a implementação: quem lê apenas o grafo obtém o mesmo veredicto que o código, grandeza por grandeza. Também traz um alerta que vale fora deste projeto, porque a divergência desapareceu somente quando o espelho reconstruiu os níveis sem arredondar. Um espelho alimentado com valores arredondados parece correto e não é: a precisão de armazenamento declarada faz parte da verificação, não do detalhe."),
    ])
    sec(doc, "7.8 Ruído, histerese e ablação estrutural", [
        ("p", "Injetar ruído nos níveis observados eleva a taxa de mudança de veredicto de 1,32% (σ = 0,02) para 8,56% "
             "(σ = 0,2), com deslocamentos assimétricos: uma observação degradada torna o modelo mais restritivo vinte vezes mais "
             "mais frequentemente do que mais permissivo (0,0815 contra 0,0041 em σ = 0,2). Em uma trajetória de oito passos sobre 20.436 "
             "casos acompanhados houve 7.461 mudanças de veredicto, 103 delas oscilações, e a histerese bloqueou 6.382 "
             "transições de flexibilização. Ablar os termos estruturais muda κ em 0,0007 em relação ao modelo completo sobre "
             "183.920 pares: a geometria organiza o rastro de auditoria, mas não produz, por si, informação normativa. Isso é "
             "um achado, não um fracasso."),
        ("p", "Interpretação. A assimetria é o achado. Quando as observações se degradam, o modelo torna-se mais restritivo vinte vezes mais frequentemente do que mais permissivo: o ruído empurra o veredicto para a cautela, não para a permissão. A histerese bloqueia 6.382 flexibilizações, de modo que um perfil não oscila na fronteira de decisão. O efeito quase nulo de remover os termos estruturais é um resultado negativo e é reportado como tal, porque o tetraedro organiza o registro, mas não gera o julgamento."),
    ])
    sec(doc, "7.9 Risco, agência e transferência", [
        ("p", "A decomposição da variância do risco residual sobre 183.920 pares dá 98,07% ao caso, 0,80% ao perfil e 1,13% à "
             "interação: o risco é propriedade do dever e do contexto, não do agente. Ainda assim, 15,46% dos casos mudam de "
             "veredicto entre os 121 perfis que enfrentam o mesmo caso, e 225 casos são recuperáveis por uma agência melhor: o "
             "risco é estrutural, a admissibilidade é agencial. Na bateria de delegação, apenas um dos 33 deveres (capacidade "
             "pura) pode ser assumido por um modelo ou ferramenta sem mais; 96,97% do canon exige uma camada de "
             "responsabilização, e escolher o melhor delegado disponível não muda nenhum veredicto, enquanto o pior muda 127, "
             "com o pilar C como gargalo em 905 deles."),
        ("p", "A transferência é medida, não presumida. Ajustar a escada em nove domínios e testá-la nos quatro nunca usados "
             "(transporte, pesquisa, segurança digital e trabalho) mais os 320 casos narrativos dá κ = 0,4834 no holdout contra "
             "0,4618 na amostra; gap de transferência −0,0215. Nos 320 casos narrativos, κ = 0,6617 com a escada ajustada contra 0,3745 "
             "com a declarada. O modelo generaliza melhor fora da amostra do que dentro dela, o que indica que o ajuste não memoriza "
             "padrões de domínio."),
        ("t", ("Tabela 17. Modelos de referência frente ao núcleo (κ / concordância exata).",
              ["Referência", "κ", "Exata", "Condição"],
              [list(r) for r in BASELINES], [3.1, 0.7, 0.8, 2.0]),
        ),
        ("p", "A bateria de âncora LLM — pedir a um modelo local que gere o perfil que a aritmética infere — não pôde ser "
             "executada nesta máquina: o processo residente de inferência ocupa 25.930.740 KB de RSS (resident set size, a memória "
             "ocupada pelo processo) de um total de 30.951 MB; "
             "uma resposta de 60 tokens (unidade de texto que o modelo gera) levou 141,9 s, cerca de 0,4 token/s efetivo, e a "
             "chamada com o prompt completo de 33 facetas "
             "(2.370 caracteres, num_predict 1.400: o limite de tokens que o motor se compromete a gerar) ultrapassou 300 s sem "
             "devolver texto; gemma4:12b-it-q4_K_M, um modelo de 12 bilhões de parâmetros quantizado, não responde em "
             "180 s. Declara-se não executável com a medição da tentativa, não substituída por um zero (D5.15)."),
        ("p", "Interpretação. Duas conclusões práticas decorrem da mesma bateria. O risco pertence ao caso, 98,07% da sua variância vem dos deveres e do contexto, não do agente. A admissibilidade pertence à delegação, 15,46% dos casos mudam de veredicto conforme o perfil que os enfrenta, e 225 casos podem ser recuperados por uma agência melhor. Melhorar o agente não é o mesmo que reduzir o risco, e uma implantação que promete o segundo investindo no primeiro faz uma afirmação que o modelo pode medir e rejeitar."),
    ])
    sec(doc, "7.10 A concordância é uma propriedade do instrumento", [
        ("p", "κ, o coeficiente de concordância de Cohen (1960), depende das priors normativas da rubrica — os pressupostos de "
             "valor embutidos nas regras: pisos de dever, deveres categóricos e lente escolhida. Perturbar os pisos de dever em 10% "
             "move κ de 0,5336 para 0,5507 ou "
             "0,5250; reduzir o conjunto de deveres categóricos a três leva a 0,5085; usar uma única lente dá 0,5223, 0,3324 ou "
             "0,5147; mover o gate de cobertura para 0,80 dá 0,6005 e para 0,60 dá 0,4907; tratar um dever não declarado como "
             "violation dá 0,2974. A variante que ultrapassa 0,60 o faz aumentando a abstenção compartilhada, não produzindo um "
             "melhor julgamento. Um κ que aumenta porque ambos se abstêm não é um κ que melhora (D5.24)."),
        ("t", ("Tabela 18. κ contra a rubrica sob onze priors normativas defensáveis (220.400 pares).",
              ["Variante de prior", "κ", "Δ"],
              [list(r) for r in RUBRIC], [2.6, 0.8, 0.9]),
        ),
        ("p", "κ é reportado por estrato porque o agregado oculta a estrutura: 0,8167 quando as três lentes coincidem (112.179 "
             "pares, concordância exata 0,915), 0,1371 quando há maioria (95.611, exata 0,6656) e 0,0526 nos casos contestados "
             "(12.610, exata 0,5977). Por cobertura: 1,000 abaixo do gate (18.240 pares, modelo e rubrica abstêm juntos), 0,3832 "
             "com o canon completo e 0,3293 com perfis parciais. Por domínio, o ranking vai de TS 0,6110 e ED 0,6103 até "
             "FI 0,4624, passando por RS 0,5877, MA 0,5684, DS 0,5511, PD 0,5463, JS 0,5351, IC 0,5203, IM 0,5050, GP 0,5022, "
             "SA 0,4791 e TB 0,4790. O pacote de adjudicação cego tem 120 casos e 360 células; na amostra de auditoria, κ "
             "modelo-vs-consenso é 0,2067 (SE, o erro padrão da estimativa, 0,0482; IC95, o intervalo de confiança de 95%, "
             "[0,112; 0,301]), mais baixo que o global porque a amostra é "
             "deliberadamente difícil: o limitante não é o tamanho da amostra, é a adjudicação humana."),
        ("f", (FIG + "/fig5_domains.png", "Figura 7. κ por domínio no corpus (13 domínios).")),
        ("p", "Interpretação. κ = 0,5336 não é uma medida da qualidade do modelo, e sim a sobreposição entre o modelo e um instrumento normativo particular. A afirmação defensável é qualificada: o modelo concorda com os instrumentos onde os instrumentos concordam entre si; fora dessa região, a divergência está documentada, não resolvida. Onde modelo e rubrica se abstêm juntos, a concordância de 1,000 mede silêncio compartilhado, não julgamento compartilhado."),
    ])

    sec(doc, "8. Interpretação consolidada", [("b", INTERP)])
    sec(doc, "9. Limitações", [("b", LIMITS_PT)])

    sec(doc, "10. Reproducibilidade", [
        ("p", "Os comandos de reprodução são: pytest sobre a suite de invariantes (45 s); o gerador do corpus; o executor de "
             "baterias, que escreve o manifest; o gerador e o validador da ontologia (301,9 s); e o espelho do corpus (121,9 s). "
             "O código está sob licença MIT e os textos sob CC BY-SA 4.0. Cada artefato da rodada está registrado em "
             "manifest_r5.json com seu SHA-256 e a revisão de git (commits 97ddab3 e e38544a)."),
        ("b", [
            "python3 -m pytest _analysis/formal_core/tests -q",
            "python3 _analysis/corpus/gen_corpus_v7.py",
            "python3 _analysis/run_all_batteries.py --round r5",
            "python3 _analysis/ontology/gen_ontology_v6.py && python3 _analysis/ontology/validate_ontology_v4.py",
            "python3 _analysis/ontology/mirror_graph_full.py",
        ]),
    ])
    sec(doc, "11. Trabalhos futuros", [("b", NEXT_PT)])
    sec(doc, "Declarações", [
        ("p", "Disponibilidade de dados e de código. Todo número citado neste relatório é produzido por código incluído no repositório e por artefatos guardados junto dele. O núcleo formal, os geradores do corpus e da rubrica, o gerador e o validador da ontologia, as baterias e os testes de invariante estão sob licença MIT; o texto do modelo, as ontologias e o registro de facetas estão sob CC BY-SA 4.0. Cada rodada fica registrada em um manifest, manifest_r5.json no caso desta rodada, com 51 artefatos, seus SHA-256, tamanho, duração de execução e revisão de git. As rodadas r2 e r3 estão congeladas e nunca são editadas no lugar, porque uma nova revisão escreve uma nova rodada, e é isso que torna os números rederiváveis em lugar de apenas reportados. O corpus é gerado a partir de parâmetros declarados, de modo que os 220.400 pares (caso, perfil) podem ser reconstruídos pelo gerador e não precisam ser distribuídos como base de dados. O pacote de adjudicação cega, 120 casos e 360 células, está incluído no repositório para o painel humano."),
        ("p", "Contribuições dos autores. L. M. M. Palazzo: conceptualização, modelagem formal, implementação do núcleo, engenharia da ontologia, execução das baterias e escrita. T. Vanzin: revisão da camada formal, validação da camada semântica e revisão editorial. Ambos leram e aprovaram o texto final."),
        ("p", "Conflitos de interesse. Os autores declaram não ter conflitos de interesse."),
        ("p", "Financiamento. O trabalho foi desenvolvido com recursos internos do Programa de Pós-Graduação em Engenharia e Gestão do Conhecimento (PPGEGC) da Universidade Federal de Santa Catarina. Não houve entidade financiadora externa, e nenhuma entidade influenciou a escolha de mecanismos, a rejeição de valores de parâmetros ou a publicação dos resultados negativos."),
        ("p", "Aspectos éticos. Os casos são sintéticos e não contêm dados pessoais ou sensíveis. Os instrumentos normativos citados, UDHR, CRC, GDPR, AI Act, Belmont, Helsinki, ILO, ISO e NIST, são usados como fontes de deveres e citados como instrumentos. Nada neste relatório constitui aconselhamento jurídico, e nenhum órgão mencionado endossa o modelo."),
        ("p", "Uso de inteligência artificial. Ferramentas de modelagem de linguagem apoiaram a redação, a organização das seções e a revisão editorial. Cada número citado vem de um artefato listado no Apêndice A e é rederivado pelo verificador de consistência, de modo que a aritmética não foi gerada por modelo. A responsabilidade pelas afirmações verificadas contra os artefatos é dos autores."),
        ("p", "Condição de ciência aberta. Código, definições de dados, artefatos de avaliação, ontologia e equações são distribuídos junto ao texto sob as licenças indicadas. O relatório foi escrito para que cada afirmação possa ser conferida a partir do repositório, sem contato com os autores."),
    ])
    sec(doc, "Referências", [("b", REFS)])

    appendix = [
        ("t", ("Tabela A.1. Rastreabilidade: cada cifra citada e seu artefato.",
              ["Cifra citada", "Artefato", "Campo"],
              [list(r) for r in TRACE], [2.4, 2.1, 1.9]),
        ),
    ]
    sec(doc, "Apêndice A. Rastreabilidade", appendix)

    set_document_properties(
        doc,
        "Relatório técnico-científico do modelo ETH-WCMK: modelo, ontologia e resultados interpretados",
        "Luiz Palazzo e Tarcísio Vanzin",
        "Modelo ETH-WCMK: núcleo formal, ontologia RDF/SHACL e interpretação dos testes da rodada 5",
        "ética de máquinas; ontologia; SHACL; análise de sensibilidade; rastreabilidade",
        "pt-BR",
    )
    add_running_footer(doc, "ETH-WCMK - Relatório técnico-científico - Palazzo & Vanzin")
    doc.save(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
