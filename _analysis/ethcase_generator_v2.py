"""ETHCASE corpus generator v2 (deterministic, seed 20261028).

Produces:
  Evaluacoes/corpus_v2_cases.jsonl        240 narrative cases + variants
  Evaluacoes/corpus_v2_profiles.jsonl     27 agency profiles (26 facet levels each)
  Evaluacoes/corpus_v2_probes.jsonl       60 adversarial + 40 degenerate probes
  Evaluacoes/corpus_v2_configurations.csv 240 x 27 evaluated configurations
  Evaluacoes/corpus_v2_summary.md         distribution + validation report

Design notes (why this is better than the v1 seed):
  * requirements rho_i are RAW intensities in [0,1], NOT a distribution: an agent
    can satisfy all four pillars at once. The simplex normalisation is used only
    for the geometric embedding (distance/volume), never for the deficit.
  * lambda (salience) is derived independently from rho (severity + domain
    salience map), so the two parameters are not aliases of each other.
  * every case carries the 26 facet requirements q_f and the 26 facet levels s_f,
    so a record is reproducible end-to-end from its own fields.
  * severity, irreversibility and uncertainty are separate axes.
"""
from __future__ import annotations
import csv, json, math, os, random, sys
from collections import Counter
from itertools import product

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formal_core_v3 as m
from facets_v2 import FACETS, pillar_scores, PILLARS

SEED = 20261028
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Evaluacoes")
CODES = [f[0] for f in FACETS]
KIND = {f[0]: f[5] for f in FACETS}
GUARDED = {f[0]: f[6] for f in FACETS}
LABEL = {f[0]: f[1] for f in FACETS}

# ---------------------------------------------------------------- archetypes
# id, domain, title, narrative, actors, stakeholders, conflict, irreversibility,
# rights at risk, legal density, evidential ambiguity, oversight need, mandate clarity,
# affected population (log10 scale), complexity
ARCHETYPES = [
    ("H1", "health", "Triagem clínica automatizada em pronto-socorro",
     "Um sistema de triagem classifica pacientes de pronto-socorro a partir de sinais vitais e histórico, priorizando casos por urgência estimada. A decisão altera a ordem de atendimento e o tempo até intervenção médica. O modelo não explica quais sinais pesaram na classificação.",
     ["hospital", "sistema de triagem", "equipe clínica"], ["pacientes", "famílias", "equipe clínica"],
     "autonomy_vs_beneficence", 0.85, ["vida", "integridade física", "igualdade de acesso"], 0.7, 0.45, 0.9, 0.8, 1.5, 0.7),
    ("H2", "health", "Ajuste automatizado de dosagem de medicamentos",
     "Um algoritmo ajusta a dosagem de anticoagulantes com base em exames contínuos e resposta observada. A dose é aplicada sem revisão humana sistemática em casos de baixo risco. O sistema aprende de dados de um único hospital.",
     ["sistema de dosificação", "farmácia", "médico prescritor"], ["pacientes", "famílias", "equipe de enfermagem"],
     "innovation_vs_precaution", 0.90, ["vida", "integridade física"], 0.8, 0.30, 0.95, 0.6, 1.3, 0.8),
    ("H3", "health", "Alocação de leitos de UTI por preditivo",
     "Diante de escassez, um sistema distribui leitos de UTI usando um score preditivo de sobrevida. O score não considera transferibilidade regional nem critérios de equidade territorial. A decisão é irreversível para o paciente não atendido.",
     ["sistema de alocação", "hospital", "secretaria de saúde"], ["pacientes", "comunidade", "equipe clínica"],
     "individual_vs_collective", 0.95, ["vida", "igualdade", "não discriminação"], 0.6, 0.55, 0.9, 0.5, 1.7, 0.9),
    ("E1", "education", "Avaliação adaptiva contínua de aprendizagem",
     "Uma plataforma avalia continuamente o desempenho de estudantes e define trilhas de recuperação. Notas parciais geradas pelo modelo influenciam a nota final. O modelo confunde baixa engajamento com baixa competência.",
     ["plataforma educacional", "docentes", "escola"], ["estudantes", "famílias", "docentes"],
     "short_term_vs_long_term", 0.45, ["igualdade de oportunidade", "privacidade", "desenvolvimento"], 0.5, 0.60, 0.7, 0.7, 2.3, 0.6),
    ("E2", "education", "Encaminhamento a programas de apoio por predição de risco",
     "Um sistema prediz abandono escolar e encaminha estudantes a programas de apoio ou a avaliação disciplinar. O rótulo acompanha o estudante por anos. A predição usa proxies socioeconômicos.",
     ["sistema preditivo", "escola", "rede de proteção"], ["estudantes", "famílias"],
     "individual_vs_collective", 0.60, ["não discriminação", "privacidade", "oportunidade"], 0.6, 0.70, 0.8, 0.5, 2.2, 0.7),
    ("E3", "education", "Detecção automatizada de integridade acadêmica",
     "Um detector acusa estudantes de uso indevido de IA em trabalhos. A acusação aciona processo disciplinar automático. Falsos positivos são frequentes em textos traduzidos ou com estilo atípico.",
     ["detector de integridade", "universidade"], ["estudantes", "docentes", "instituição"],
     "speed_vs_due_process", 0.55, ["presunção de inocência", "defesa", "reputação"], 0.7, 0.80, 0.8, 0.6, 2.4, 0.5),
    ("V1", "environment_energy", "Despacho automatizado da rede elétrica",
     "Um otimizador decide a ordem de despacho de fontes de energia para minimizar custo e emissões. A decisão pode priorizar termelétricas de reserva em picos de demanda. O efeito é imediato e observado por milhares de consumidores.",
     ["operador da rede", "regulador", "geradores"], ["consumidores", "comunidades", "meio ambiente"],
     "short_term_vs_long_term", 0.50, ["acesso a energia", "meio ambiente", "saúde pública"], 0.8, 0.35, 0.85, 0.8, 3.5, 0.8),
    ("V2", "environment_energy", "Compensação de emissões por creditamento automático",
     "Um sistema valida créditos de carbono a partir de imagens de satélite e declarações de proprietários. A validação automática aceita projetos com monitoramento frágil. O erro é difícil de reverter após a venda do crédito.",
     ["plataforma de credits", "proprietários", "compradores"], ["comunidades locais", "meio ambiente", "investidores"],
     "innovation_vs_precaution", 0.75, ["meio ambiente", "território", "veracidade"], 0.6, 0.75, 0.7, 0.4, 2.6, 0.6),
    ("V3", "environment_energy", "Alerta precoce de desastre ambiental",
     "Um modelo combina sensores e dados meteorológicos para emitir alertas de inundação. Alertas falsos geram evacuações custosas; alertas perdidos custam vidas. A confiança declarada do modelo excede sua precisão real.",
     ["sistema de alerta", "defensa civil", "agência ambiental"], ["população", "autoridades", "infraestrutura"],
     "speed_vs_due_process", 0.85, ["vida", "propriedade", "confiança institucional"], 0.7, 0.85, 0.9, 0.6, 2.8, 0.7),
    ("D1", "digital_security", "Resposta automatizada a incidente de segurança",
     "Um SOAR bloqueia contas, revoga tokens e isola servidores automaticamente ante sinais de intrusão. A ação ocorre em segundos, sem revisão humana. Falsos positivos interrompem serviços críticos.",
     ["sistema de resposta", "equipe de segurança", "usuários"], ["usuários", "organização", "terceiros"],
     "speed_vs_due_process", 0.60, ["acesso", "continuidade de serviço", "defesa"], 0.7, 0.40, 0.8, 0.9, 2.0, 0.8),
    ("D2", "digital_security", "Divulgação automatizada de vulnerabilidade",
     "Um agente identifica uma vulnerabilidade e decide entre notificar o fabricante, o regulador ou publicar a exploração. A escolha tem consequências legais e de segurança pública. Não há protocolo de escalada claro.",
     ["agente de descoberta", "fabricante", "regulador"], ["usuários", "fabricante", "público"],
     "transparency_vs_safety", 0.70, ["segurança", "privacidade", "propriedade"], 0.8, 0.60, 0.85, 0.5, 2.7, 0.7),
    ("D3", "digital_security", "Bloqueo de contas por probabilidade de abuso",
     "Um classificador suspende contas com base em probabilidade de abuso. A reinstauração exige recurso humano lento. O modelo usa variáveis proxies de região e idioma.",
     ["plataforma", "moderação", "usuários"], ["usuários", "comunidades", "plataforma"],
     "individual_vs_collective", 0.55, ["acesso", "liberdade de expressão", "igualdade"], 0.6, 0.65, 0.7, 0.7, 3.0, 0.6),
    ("P1", "privacy_data", "Minimização de dados em reidentificação",
     "Um sistema agrega registros para análise interna e decide quais atributos manter. Uma combinação de atributos aparentemente anônimos permite reidentificação de indivíduos vulneráveis. O objetivo analítico colide com a minimização.",
     ["controlador de dados", "DPO", "analistas"], ["indivíduos", "grupos vulneráveis", "organização"],
     "transparency_vs_safety", 0.65, ["privacidade", "não discriminação", "autonomia informacional"], 0.9, 0.50, 0.8, 0.7, 2.9, 0.7),
    ("P2", "privacy_data", "Consentimento dinâmico e inferência de preferências",
     "Um agente infere preferências sensíveis a partir de comportamento e decide se solicita novo consentimento. A inferência cria dados que o usuário nunca consentiu explicitamente. O modelo não distingue correlação de intenção.",
     ["sistema de perfilamento", "usuários", "regulador"], ["usuários", "terceiros", "mercado"],
     "autonomy_vs_beneficence", 0.50, ["autonomia", "privacidade", "dignidade"], 0.8, 0.70, 0.7, 0.6, 3.4, 0.6),
    ("P3", "privacy_data", "Decisão sobre compartilhamento entre órgãos públicos",
     "Um agente avalia se dados de saúde podem ser compartilhados com órgãos de segurança para fins de investigação. O pedido vem de autoridade sem base legal clara. A negação pode prejudicar uma investigação legítima.",
     ["órgão de saúde", "órgão de segurança", "agente intermediário"], ["cidadaos", "investigados", "instituições"],
     "individual_vs_collective", 0.75, ["privacidade", "devido processo", "não discriminação"], 0.9, 0.60, 0.9, 0.4, 3.1, 0.8),
    ("F1", "finance", "Concessão de crédito por score automatizado",
     "Um modelo decide quem recebe crédito e a taxa aplicada. Variáveis de bairro e histórico de uso funcionam como proxies de renda e etnia. A decisão é difícil de contestar e afeta famílias inteiras.",
     ["instituição financeira", "consumidores", "regulador"], ["consumidores", "famílias", "comunidades"],
     "individual_vs_collective", 0.60, ["igualdade", "acesso", "condição econômica"], 0.9, 0.55, 0.8, 0.8, 3.2, 0.7),
    ("F2", "finance", "Detecção de fraude com bloqueio imediato",
     "Um sistema bloqueia transações suspeitas em tempo real. Bloqueios falsos deixam pessoas sem acesso a dinheiro em emergências. O modelo não sabe o contexto da transação.",
     ["sistema antifraude", "consumidor", "banco"], ["consumidores", "comerciantes"],
     "speed_vs_due_process", 0.65, ["acesso a recursos", "dignidade", "propriedade"], 0.8, 0.60, 0.85, 0.9, 3.3, 0.8),
    ("F3", "finance", "Reestruturação automática de dívida impagável",
     "Um agente renegocia dívidas de clientes em inadimplência, decidindo prazos e garantias. A renegociacao pode ser predatória para devedores vulneráveis. Não há revisão por órgão de proteção.",
     ["sistema de renegociacao", "devedores", "regulador"], ["devedores", "famílias"],
     "short_term_vs_long_term", 0.70, ["condição econômica", "não exploração", "autonomia"], 0.8, 0.45, 0.8, 0.5, 2.5, 0.6),
    ("A1", "public_administration", "Triagem de benefícios sociais",
     "Um sistema decide quem recebe auxílio social e prioriza casos. Critérios do modelo diferem da legislação e penalizam famílias com documentação irregular. O erro nega acesso a direitos básicos.",
     ["agência pública", "beneficiários", "controle interno"], ["cidadãos vulneráveis", "comunidades"],
     "individual_vs_collective", 0.70, ["direitos sociais", "igualdade", "dignidade"], 0.95, 0.50, 0.9, 0.6, 3.4, 0.7),
    ("A2", "public_administration", "Alokación dinâmica de recursos públicos escassos",
     "Um otimizador distribui vagas, insumos e transporte público entre regiões. A otimização favorece áreas de maior demanda mensurável, invisibilizando comunidades periféricas. O critério de equidade não está formalizado.",
     ["gestor público", "município", "cidadaos"], ["população", "comunidades periféricas"],
     "individual_vs_collective", 0.60, ["igualdade", "acesso", "participação"], 0.8, 0.55, 0.85, 0.5, 3.2, 0.7),
    ("A3", "public_administration", "Atendimento cidadão automatizado multilíngue",
     "Um assistente responde perguntas sobre direitos e procedimentos, decidindo quando escalar a um servidor. Em idiomas minoritários, o sistema dá respostas confusas e incorretas com alta confiança. Usuários sem suporte humano ficam sem acesso.",
     ["assistente público", "cidadaos", "servidores"], ["cidadaos", "minorias linguísticas"],
     "autonomy_vs_beneficence", 0.45, ["acesso a direitos", "igualdade", "compreensão"], 0.7, 0.75, 0.6, 0.7, 3.5, 0.5),
    ("J1", "justice_security", "Avaliação de risco de reincidência",
     "Um instrumento calcula risco de reincidência para decisões de liberdade condicional. Variáveis de bairro e histórico familiar operam como proxies de classe e raça. A decisão restringe liberdade individual.",
     ["sistema de avaliação", "tribunal", "defesa"], ["réus", "vítimas", "comunidade"],
     "individual_vs_collective", 0.80, ["liberdade", "presunção de inocência", "não discriminação"], 0.95, 0.70, 0.95, 0.6, 2.1, 0.8),
    ("J2", "justice_security", "Vigilância preditiva em espaço público",
     "Um sistema identifica 'pontos críticos' e sugere patrulhamento antecipado. A recomendação concentra presença policial em bairros já vigiados, retroalimentando a amostragem. Não há avaliação de impacto sobre direitos.",
     ["sistema preditivo", "polícia", "município"], ["moradores", "minorias", "público"],
     "individual_vs_collective", 0.65, ["liberdade de circulação", "não discriminação", "privacidade"], 0.8, 0.80, 0.9, 0.4, 3.0, 0.7),
    ("J3", "justice_security", "Triagem de evidência digital em processo",
     "Um agente organiza e resume evidências digitais para o processo, decidindo o que é relevante. O filtro pode omitir evidências favoráveis à defesa. O modelo não registra seus próprios critérios de seleção.",
     ["sistema de triagem", "tribunal", "partes"], ["partes", "réu", "sistema judicial"],
     "speed_vs_due_process", 0.70, ["devido processo", "defesa", "igualdade de armas"], 0.95, 0.60, 0.95, 0.7, 1.8, 0.8),
    ("I1", "critical_infrastructure", "Controle automatizado de barragem hídrica",
     "Um sistema controla a comportamento de comporta de uma barragem para regular vazão. Uma decisão errada provoca inundação rio abaixo. A margem de segurança declarada não está validada independentemente.",
     ["sistema de controle", "operador", "defensa civil"], ["população ribeirinha", "meio ambiente", "infraestrutura"],
     "innovation_vs_precaution", 0.95, ["vida", "propriedade", "meio ambiente"], 0.85, 0.35, 0.95, 0.8, 2.7, 0.9),
    ("I2", "critical_infrastructure", "Manutenção preditiva de rede de água",
     "Um modelo prevê falhas em tubulação e agenda reparos. Adiar intervenções de baixa confiança aumenta risco de contaminação. O modelo ignora população vulnerável servida pelo trecho.",
     ["sistema de manutenção", "concessionária", "regulador"], ["população", "comunidades", "meio ambiente"],
     "short_term_vs_long_term", 0.75, ["saúde", "acesso a água", "meio ambiente"], 0.8, 0.55, 0.85, 0.6, 2.9, 0.7),
    ("I3", "critical_infrastructure", "Gestão automatizada de tráfego aéreo",
     "Um sistema reencaminha aeronaves para maximizar throughput. Manobras agressivas reduzem margem de segurança. A justificativa da decisão não é legível para o controlador humano.",
     ["sistema de gestão", "controladores", "companhias"], ["passageiros", "tripulação", "comunidade"],
     "transparency_vs_safety", 0.90, ["vida", "segurança", "accountability"], 0.9, 0.30, 0.95, 0.9, 2.8, 0.9),
    ("L1", "labour", "Triagem automatizada de candidaturas",
     "Um sistema ordena candidatos e elimina perfis abaixo de um umbral. O umbral reflete padrões de um setor historicamente homogêneo. Candidatos eliminados não recebem explicação nem recurso.",
     ["sistema de triagem", "RH", "candidatos"], ["candidatos", "comunidades", "mercado de trabalho"],
     "individual_vs_collective", 0.50, ["igualdade", "não discriminação", "oportunidade"], 0.8, 0.60, 0.7, 0.5, 2.6, 0.6),
    ("L2", "labour", "Monitoramento automatizado de produtividade",
     "Um agente coleta métricas de atividade e sinaliza 'baixa performance' para gestores. A vigilância contínua interfere na privacidade e gera pressão para comportamentos inseguros. A métrica confunde presença com produção.",
     ["sistema de monitoramento", "gestores", "trabalhadores"], ["trabalhadores", "famílias", "equipes"],
     "autonomy_vs_beneficence", 0.55, ["privacidade", "saúde", "dignidade", "condição de trabalho"], 0.7, 0.65, 0.7, 0.4, 2.4, 0.6),
    ("L3", "labour", "Dimensionamento dinâmico de equipes em emergências",
     "Um algoritmo redistribui equipes de saúde e segurança conforme demanda prevista. Reduz turnos em horários de pico previsto, mas a previsão é instável. Falhas de cobertura podem custar vidas.",
     ["sistema de escala", "gestor", "trabalhadores"], ["trabalhadores", "população atendida"],
     "short_term_vs_long_term", 0.70, ["vida", "condição de trabalho", "acesso a serviço"], 0.8, 0.70, 0.9, 0.6, 2.5, 0.8),
    ("M1", "media_information", "Moderação automática de conteúdo prejudicial",
     "Um sistema remove ou rebaixa conteúdo classificado como prejudicial. A remoção é imediata e pouco contestável. Contexto irônico, satírico ou jornalístico é frequentemente mal classificado.",
     ["plataforma", "moderação", "usuários"], ["usuários", "minorias", "público"],
     "transparency_vs_safety", 0.55, ["liberdade de expressão", "acesso a informação", "participação"], 0.7, 0.80, 0.7, 0.5, 3.8, 0.6),
    ("M2", "media_information", "Recomendação de feed que maximiza engajamento",
     "Um algoritmo prioriza conteúdo provável de gerar engajamento. O resultado amplia exposição a desinformação e polarização. O sistema não avalia dano informacional, apenas cliques.",
     ["plataforma", "usuários", "regulador"], ["usuários", "democracia", "grupos vulneráveis"],
     "short_term_vs_long_term", 0.45, ["autonomia informacional", "saúde mental", "democracia"], 0.6, 0.70, 0.6, 0.3, 3.9, 0.5),
    ("M3", "media_information", "Verificação automatizada de fatos em tempo real",
     "Um agente verifica afirmações durante coberturas ao vivo. Classifica como falso informação incompleta ainda não confirmada. A etiqueta altera a circulação de informação relevante.",
     ["sistema de fact-check", "jornalistas", "plataforma"], ["público", "fontes", "instituições"],
     "speed_vs_due_process", 0.60, ["acesso a informação", "reputação", "veracidade"], 0.6, 0.85, 0.8, 0.4, 3.6, 0.7),
    ("T1", "transport", "Roteirização autônoma de frota de carga",
     "Um sistema define rotas considerando custo, tempo e risco. Rotas de menor custo atravessam áreas residenciárias densas. A externalidade de risco não está na função objetivo.",
     ["sistema de roteirização", "empresa", "comunidades"], ["comunidades", "motoristas", "meio ambiente"],
     "individual_vs_collective", 0.70, ["segurança", "meio ambiente", "direito à segurança"], 0.7, 0.40, 0.8, 0.6, 2.7, 0.7),
    ("T2", "transport", "Priorização de transporte para urgência médica",
     "Um agente decide qual ambulância e rota priorizar entre três ocorrências simultâneas. O caso menos 'resoluble' fica sem cobertura. Não há critério explícito de triagem médica.",
     ["sistema de despacho", "equipes médicas", "pacientes"], ["pacientes", "famílias", "comunidade"],
     "autonomy_vs_beneficence", 0.90, ["vida", "igualdade de acesso"], 0.8, 0.50, 0.95, 0.7, 2.4, 0.8),
    ("T3", "transport", "Entrega por drone em área urbana",
     "Um sistema autoriza rotas de entrega autônoma sobre bairros densos. Falhas de sensores em clima adverso geram risco físico. O sistema opera sem registro de incidentes próximos.",
     ["sistema de operação", "empresa", "moradores"], ["moradores", "terceiros", "infraestrutura"],
     "innovation_vs_precaution", 0.80, ["vida", "segurança", "privacidade"], 0.6, 0.55, 0.85, 0.5, 2.2, 0.7),
    ("R1", "research_science", "Triagem automatizada de dados sensíveis em estudo",
     "Um agente seleciona participantes de uma pesquisa a partir de registros de saúde. A seleção exclui grupos difíceis de medir, enviesando a inferência científica. O risco de dano a participantes é subestimado.",
     ["sistema de triagem", "equipe de pesquisa", "participantes"], ["participantes", "comunidades", "ciência"],
     "short_term_vs_long_term", 0.65, ["privacidade", "não discriminação", "beneficência"], 0.85, 0.75, 0.9, 0.5, 2.3, 0.7),
    ("R2", "research_science", "Autocorreção de resultados por modelo de validação",
     "Um modelo detecta inconsistências em resultados experimentais e sugere descartar observações. O descarte automático pode eliminar efeitos raros e genuínos. A validação usa um modelo treinado no mesmo dataset.",
     ["modelo de validação", "pesquisadores", "revista"], ["ciência", "pacientes futuros", "instituição"],
     "innovation_vs_precaution", 0.60, ["veracidade", "integridade científica", "saúde pública"], 0.6, 0.80, 0.85, 0.6, 2.0, 0.7),
    ("R3", "research_science", "Decisão sobre publicação de dataset sensível",
     "Um agente decide se um dataset anonimizado pode ser publicado. A anonimização é insuficiente para subgrupos pequenos. O benefício científico colide com risco de reidentificação.",
     ["sistema de gestão de dados", "pesquisadores", "participantes"], ["participantes", "ciência", "público"],
     "transparency_vs_safety", 0.70, ["privacidade", "não discriminação", "autonomia"], 0.8, 0.65, 0.85, 0.4, 2.1, 0.6),
]

CONFLICT_PATTERNS = ["autonomy_vs_beneficence", "transparency_vs_safety", "speed_vs_due_process",
                     "individual_vs_collective", "short_term_vs_long_term", "innovation_vs_precaution"]

DOMAIN_SALIENCE = {  # extra salience weight for pillars, independent of severity
    "health": (0.10, 0.15, 0.25, 0.15),
    "education": (0.15, 0.10, 0.20, 0.20),
    "environment_energy": (0.10, 0.15, 0.25, 0.15),
    "digital_security": (0.10, 0.20, 0.20, 0.10),
    "privacy_data": (0.10, 0.10, 0.30, 0.15),
    "finance": (0.10, 0.15, 0.25, 0.15),
    "public_administration": (0.10, 0.15, 0.25, 0.15),
    "justice_security": (0.10, 0.15, 0.30, 0.10),
    "critical_infrastructure": (0.10, 0.20, 0.25, 0.10),
    "labour": (0.15, 0.15, 0.20, 0.15),
    "media_information": (0.20, 0.10, 0.15, 0.15),
    "transport": (0.10, 0.15, 0.25, 0.10),
    "research_science": (0.15, 0.15, 0.20, 0.20),
}

SEVERITY_W = {"low": (0.8, 0.8, 0.9, 0.8), "medium": (0.9, 0.9, 1.0, 0.9),
              "high": (1.0, 1.0, 1.1, 1.0), "critical": (1.0, 1.1, 1.2, 1.1)}
PRUDENTIAL_SIGMA = {"standard": 0.10, "elevated": 0.15, "maximum": 0.22}

FAMILY_LEVELS = {
    "balanced":            {"W": 0.75, "C": 0.75, "M": 0.75, "K": 0.75},
    "action_oriented":     {"W": 0.85, "C": 0.80, "M": 0.55, "K": 0.60},
    "normatively_guarded": {"W": 0.60, "C": 0.65, "M": 0.90, "K": 0.70},
    "epistemic_reviewer":  {"W": 0.55, "C": 0.55, "M": 0.70, "K": 0.90},
    "brittle_capable":     {"W": 0.70, "C": 0.90, "M": 0.55, "K": 0.65},
    "aspirational":        {"W": 0.90, "C": 0.50, "M": 0.60, "K": 0.50},
    "paper_compliant":     {"W": 0.55, "C": 0.45, "M": 0.95, "K": 0.50},
    "persuasive_aligner":  {"W": 0.90, "C": 0.70, "M": 0.50, "K": 0.60},
    "well_metriced":       {"W": 0.70, "C": 0.85, "M": 0.60, "K": 0.45},
}
MATURITY = {"novice": 0.75, "established": 1.00, "expert": 1.12}
ADVERSARIAL_FACET_OVERRIDES = {
    "paper_compliant": {"C2": 0.30, "C3": 0.35, "C6": 0.30, "K7": 0.20, "M1": 0.98, "M2": 0.95},
    "persuasive_aligner": {"W2": 0.92, "K7": 0.25, "M4": 0.35, "W6": 0.40},
    "well_metriced": {"C1": 0.90, "C5": 0.90, "K6": 0.30, "K7": 0.30, "K8": 0.40},
}


def facet_requirements(arc, band, U_E, prudential):
    """q_f per facet from archetype attributes. Raw intensities, clipped to [0,1]."""
    irrev, rights, legal, ambig, overs, legit, pop, complexity = arc[7:15]
    stakes = min(1.0, 0.30 * len(rights))
    w = SEVERITY_W[band]
    sig = PRUDENTIAL_SIGMA[prudential]
    q = {}
    for code in CODES:
        if code.startswith("W"):
            base = 0.35 + 0.25 * legit + 0.10 * pop
            if code == "W6":
                base = 0.30 + 0.30 * legit
            if code == "W3":
                base = 0.30 + 0.25 * overs + 0.10 * pop
            q[code] = min(1.0, base * w[0])
        elif code.startswith("C"):
            base = 0.30 + 0.30 * complexity + 0.15 * irrev
            if code in ("C2", "C6"):
                base = 0.30 + 0.35 * irrev + 0.15 * complexity
            if code == "C3":
                base = 0.30 + 0.30 * overs + 0.15 * irrev
            q[code] = min(1.0, base * w[1])
        elif code.startswith("M"):
            base = 0.30 + 0.30 * legal + 0.10 * stakes
            if code == "M6":
                base = 0.30 + 0.25 * irrev + 0.30 * U_E + 0.15 * sig
            if code == "M1":
                base = 0.35 + 0.40 * legal
            q[code] = min(1.0, base * w[2])
        else:
            base = 0.30 + 0.30 * ambig + 0.20 * irrev
            if code in ("K6", "K7"):
                base = 0.30 + 0.40 * U_E + 0.15 * ambig
            if code == "K8":
                base = 0.25 + 0.25 * ambig + 0.15 * irrev
            q[code] = min(1.0, base * w[3])
    return q


def pillar_requirements(q):
    """rho_i = weighted mean of q_f projected onto pillar i (raw, not normalized)."""
    num = [0.0] * 4
    den = [0.0] * 4
    for code, _, _, primary, beta, *_ in FACETS:
        for i, b in enumerate(beta):
            num[i] += b * q[code]
            den[i] += b
    return [num[i] / den[i] if den[i] else 0.0 for i in range(4)]


def salience(arc, band, U_E):
    """lambda: independent salience distribution (severity + domain + irreversibility)."""
    irrev, rights, legal, ambig, overs, legit, pop, complexity = arc[7:15]
    stakes = min(1.0, 0.30 * len(rights))
    base = [1.0, 1.0, 1.0, 1.0]
    base[2] += 1.2 * legal + 0.8 * irrev
    base[3] += 1.0 * ambig + 0.8 * U_E
    base[1] += 0.8 * complexity
    base[0] += 0.6 * legit
    ds = DOMAIN_SALIENCE[arc[1]]
    lam = [base[i] * (1.0 + ds[i]) for i in range(4)]
    s = sum(lam)
    return [round(x / s, 4) for x in lam]


def facet_levels(family, maturity, rng, case_id):
    levels = {}
    for code, _, _, primary, *_ in FACETS:
        v = FAMILY_LEVELS[family][primary] * MATURITY[maturity]
        v += rng.uniform(-0.06, 0.06)
        levels[code] = max(0.0, min(1.0, v))
    for code, v in ADVERSARIAL_FACET_OVERRIDES.get(family, {}).items():
        levels[code] = v
    return levels


def panel_adjudicator(case):
    """Transparent heuristic 'expert panel' gold standard, independent of the core."""
    rho, lam = case["rho"], case["lambda"]
    a = case["pillarScores"]
    q, s = case["facetRequirements"], case["facetLevels"]
    fails_guarded = [c for c in CODES if GUARDED[c] and q[c] - s[c] > 0.15]
    weakest = min(range(4), key=lambda i: a[i] / max(rho[i], 1e-9))
    deficits = sum(max(0, rho[i] - a[i]) / max(rho[i], 1e-9) for i in range(4)) / 4
    if case["severityBand"] == "critical" and fails_guarded:
        return "prohibit"
    if len(fails_guarded) >= 3:
        return "prohibit"
    if deficits > 0.30 or (rho[weakest] - a[weakest]) / max(rho[weakest], 1e-9) > 0.45:
        return "review"
    if deficits > 0.15 or case["U_E"] > 0.55:
        return "conditional"
    return "allow"


def build():
    rng = random.Random(SEED)
    cases, configs = [], []
    bands = ["low", "medium", "high", "critical"]
    modes = ["standard", "elevated", "maximum"]
    cid = 0
    for arc in ARCHETYPES:
        for band in bands:
            for mode in modes:
                cid += 1
                U_E = round(min(0.95, arc[9] * (0.5 if mode == "standard" else 0.85) + rng.uniform(0, 0.25)), 4)
                q = facet_requirements(arc, band, U_E, mode)
                rho = [round(x, 4) for x in pillar_requirements(q)]
                lam = salience(arc, band, U_E)
                theta = {"low": 0.15, "medium": 0.18, "high": 0.20, "critical": 0.22}[band]
                phi = 0.5 if band in ("high", "critical") else 0.35
                crit = tuple(i for i in range(4) if rho[i] > 0.30 or lam[i] > 0.30)
                case = {
                    "caseId": f"ETHCASE-{cid:04d}",
                    "archetype": arc[0], "domain": arc[1], "title": arc[2],
                    "narrative": arc[3], "actors": arc[4], "stakeholders": arc[5],
                    "conflictPattern": arc[6], "irreversibility": arc[7],
                    "rightsAtRisk": arc[8], "legalDensity": arc[9],
                    "evidentialAmbiguity": arc[10], "oversightNeed": arc[11],
                    "mandateClarity": arc[12], "affectedPopulationLog10": arc[13],
                    "operationalComplexity": arc[14],
                    "severityBand": band, "prudentialMode": mode,
                    "sigma": PRUDENTIAL_SIGMA[mode], "theta": theta, "phi": phi,
                    "gamma": 0.12, "eta": 0.05, "omega": 0.03, "rhoParam": 0.15,
                    "U_E": U_E, "rho": rho, "lambda": lam, "criticalPillars": list(crit),
                    "facetRequirements": {c: round(q[c], 4) for c in CODES},
                }
                cases.append(case)

    profiles = []
    for family, maturity in product(FAMILY_LEVELS, MATURITY):
        pr = {"profileId": f"PROFILE-{family}-{maturity}", "family": family, "maturity": maturity,
              "facetLevels": facet_levels(family, maturity, rng, family + maturity)}
        profiles.append(pr)

    probes = []
    for k in range(60):
        fam = rng.choice(list(FAMILY_LEVELS))
        lev = facet_levels(fam, "expert", rng, k)
        lev[rng.choice(["K7", "C2", "C3", "M4", "W6", "K6", "C6", "M1", "M6", "K8"])] = rng.uniform(0.05, 0.20)
        probes.append({"probeId": f"ADV-{k:03d}", "kind": "adversarial", "family": fam, "facetLevels": lev,
                       "note": "one guarded facet deliberately failed while the aggregate looks adequate"})
    for k, kind in enumerate(["zero_W", "zero_C", "zero_M", "zero_K", "all_in_one",
                              "unattainable_requirement", "empty_facet_vector", "max_uncertainty"] * 5):
        lev = {c: 0.5 for c in CODES}
        if kind == "zero_W":
            lev = {c: (0.05 if c.startswith("W") else 0.7) for c in CODES}
        elif kind == "zero_C":
            lev = {c: (0.05 if c.startswith("C") else 0.7) for c in CODES}
        elif kind == "zero_M":
            lev = {c: (0.05 if c.startswith("M") else 0.7) for c in CODES}
        elif kind == "zero_K":
            lev = {c: (0.05 if c.startswith("K") else 0.7) for c in CODES}
        elif kind == "all_in_one":
            lev = {c: (0.95 if c.startswith("W") else 0.10) for c in CODES}
        elif kind == "unattainable_requirement":
            lev = {c: 0.40 for c in CODES}
        elif kind == "empty_facet_vector":
            lev = {c: 0.0 for c in CODES}
        else:
            lev = {c: 0.70 for c in CODES}
        probes.append({"probeId": f"DEG-{k:03d}", "kind": "degenerate", "facetLevels": lev,
                       "note": f"probe: {kind}"})

    # evaluate configurations
    n_inv = 0
    for case in cases:
        for pr in profiles:
            lev = pr["facetLevels"]
            a = pillar_scores(lev)
            rho = case["rho"]
            delta = [max(0.0, rho[i] - a[i]) / max(rho[i], 1e-9) for i in range(4)]
            Aa, _, pen = m.adequacy(a, rho, case["lambda"], case["U_E"],
                                   m.Params(gamma=case["gamma"], eta=case["eta"], omega=case["omega"],
                                           rho=case["rhoParam"], theta=case["theta"], phi=case["phi"]),
                                   critical=case["criticalPillars"])
            R_c = 0.5 + 0.5 * case["irreversibility"]
            R_r = m.residual_risk(Aa, R_c)
            veto = m.hard_veto(delta, case["criticalPillars"])
            dec = m.decision(Aa, R_r, R_c, veto=veto)
            guard_fail = sum(1 for c in CODES if GUARDED[c] and case["facetRequirements"][c] - lev[c] > 0.15)
            gold = panel_adjudicator(dict(case, pillarScores=a, facetLevels=lev))
            configs.append({"caseId": case["caseId"], "profileId": pr["profileId"], "domain": case["domain"],
                            "severity": case["severityBand"],
                            "rho": [round(x, 4) for x in rho], "lambda": case["lambda"],
                            "a": [round(x, 4) for x in a], "delta": [round(x, 4) for x in delta],
                            "penalty": round(pen, 4), "Aa": round(Aa, 4), "R_c": round(R_c, 4),
                            "R_r": round(R_r, 4), "veto": veto, "decision": dec, "goldPanel": gold,
                            "guardedFacetsFailed": guard_fail,
                            "agreement": dec == gold, "worstPillar": min(range(4), key=lambda i: delta[i])})
    return cases, profiles, probes, configs


if __name__ == "__main__":
    cases, profiles, probes, configs = build()
    with open(os.path.join(OUT, "corpus_v2_cases.jsonl"), "w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "corpus_v2_profiles.jsonl"), "w", encoding="utf-8") as fh:
        for p in profiles:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "corpus_v2_probes.jsonl"), "w", encoding="utf-8") as fh:
        for p in probes:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "corpus_v2_configurations.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(configs[0].keys()))
        w.writeheader(); w.writerows(configs)

    dec = Counter(c["decision"] for c in configs)
    agree = sum(1 for c in configs if c["agreement"]) / len(configs)
    print(f"cases={len(cases)} profiles={len(profiles)} probes={len(probes)} configurations={len(configs)}")
    print("decisions:", dict(dec))
    print("agreement with expert panel:", round(agree * 100, 2), "%")
    print("veto fired in", sum(1 for c in configs if c["veto"]), "configurations")
    print("Aa>=0.6 but veto fired:", sum(1 for c in configs if c["Aa"] >= 0.6 and c["veto"]))
    doms = Counter(c["domain"] for c in cases)
    print("domains:", dict(doms))
    rhos = {tuple(c["rho"]) for c in cases}
    print("distinct rho vectors:", len(rhos), "| lambda==rho cases:",
          sum(1 for c in cases if c["rho"] == c["lambda"]))
