"""Add the interpretation layer and the open-science declarations to the v14 deliverables.

The two DOCX files are already complete in content and citations. What the project
brief still requires, and what the reference document (Shared/DS_Beyond_Datasets_v2.docx)
makes explicit, is that every relevant result is followed by its interpretation in the
text, and that an open-science paper carries a declarations block: data and code
availability, author contributions, funding, competing interests, ethics, AI use.

This script edits the two build scripts in place; rerunning them writes the DOCX.

Run:  python3 _analysis/paper/patch_interpretations.py
"""
PAPER = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/build_paper_v14.py"
REPORT = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/build_report_pt.py"

PAPER_INTERP = [
    ('section(doc, "7.1 Invariants and geometry", [',
     "The value of the suite is not the number of tests but what they rule out. I35 makes an incoherent "
     "calibration impossible to load, I38 makes the ordering of the stakes a property of the model rather than a "
     "hope about the parameters, and I44 turns the coverage gate into a variable the auditor can see and change. "
     "A reviewer can re-derive the geometry from the code instead of trusting the paper: the fifteen slots of the "
     "lattice, their weights and their incidences are computed, not declared."),
    ('section(doc, "7.2 Adversarial probes", [',
     "A pass rate of 1.000 does not show that the model is correct. It shows that no input built to break it "
     "succeeded in breaking the promises the arithmetic makes about itself. The consequence is narrow and usable: "
     "the compensation hole found in v12, where a strong level in one duty covered a failing duty in another, now "
     "leaves a recorded guard failure and a material gap, so an audit can cite an event instead of interpreting a "
     "score."),
    ('section(doc, "7.3 Which mechanisms actually change agreement", [',
     "Two mechanisms change the verdict for a reason an audit can name; two do not. Inferring the oversight regime "
     "from declared facts raises agreement because a reviewed case is treated differently from an unreviewed one. "
     "Differentiating beta raises agreement because duties that were indistinguishable become distinguishable. "
     "Salience and cross-pillar exposure move the outputs without moving the judgement, so they are kept as "
     "diagnostics: a governance team can inspect them, but the verdict does not depend on them. The rule the round "
     "establishes is that a mechanism is adopted only when its effect is measured, signed and significant."),
    ('section(doc, "7.4 Ablation of the canon", [',
     "The normative weight of the model sits exactly where the design placed it. Removing the twelve hard guards "
     "takes the agreement with the panels from 0.4633 to 0.1399, a fall of 69.8%, which means the guard floors are not a stylistic choice but the "
     "mechanism that produces the behaviour the panels reward. The small individual deltas carry the opposite "
     "instruction: no guard can be defended one by one, so the canon has to be defended as a whole. For a deploying "
     "organisation, that means the floors cannot be negotiated per duty without destroying the property the model "
     "is being used for."),
    ('section(doc, "7.5 Fact grounding", [',
     "Declaring a level is not the same as delivering it. Almost every profile states a level that the case's own "
     "facts contradict, and correcting that changes nearly half of the verdicts. The rise of kappa from 0.2463 to "
     "0.5526 is not a tuning effect: it is the difference between judging what an agent claims and judging what an "
     "agent can show. An audit trail built on declared levels alone would systematically overstate agency."),
    ('section(doc, "7.6 Sensitivity of the parameters", [',
     "Two parameters govern the model, and both belong in the audit record rather than in a code default: the "
     "coverage gate decides when the model is allowed to speak at all, and the structural penalty decides how much "
     "a deficit weighs. Everything else is comparatively flat, including coefficients earlier rounds spent effort "
     "calibrating. For a deploying organisation this is a governance finding, not a numerical curiosity: the "
     "settings with the largest influence define the scope of the judgement, so they must be declared, versioned "
     "and reviewed."),
    ('section(doc, "7.7 The arithmetic mirror", [',
     "The mirror closes the distance between the paper and the implementation: a reviewer who reads only the graph "
     "obtains the same verdict as the code, quantity by quantity. It also carries a caution that generalises beyond "
     "this project, because the divergence disappeared only after the mirror reconstructed the unrounded levels. A "
     "mirror fed with rounded values looks correct and is not, so the declared storage precision is part of the "
     "verification rather than a detail of it."),
    ('section(doc, "7.8 Noise, hysteresis and structural ablation", [',
     "The asymmetry is the finding. When observations degrade, the model becomes more restrictive twenty times as "
     "often than more permissive: noise pushes the verdict toward caution rather than toward permission. The "
     "hysteresis blocks 6,382 loosening transitions, so a profile does not oscillate across a decision boundary. "
     "The near-zero effect of removing the structural terms is a negative result and is reported as such: the "
     "tetrahedron organises the record, it does not generate the judgement."),
    ('section(doc, "7.9 Risk, agency and transfer", [',
     "Two practical conclusions follow from the same battery. Risk belongs to the case: 98.07% of its variance "
     "comes from the duties and the context, not from the agent. Admissibility belongs to the delegation: 15.46% of "
     "cases change verdict depending on which profile faces them, and 225 cases can be rescued by a better agency. "
     "Improving the agent is therefore not the same as reducing risk, and a deployment that promises the first by "
     "investing in the second is making a claim the model can measure and reject."),
    ('section(doc, "7.10 Agreement is an instrument property", [',
     "Kappa 0.5336 is not a measure of the model's quality. It is the overlap between the model and one particular "
     "normative instrument. The claim that can be defended is a qualified one: the model agrees with the "
     "instruments where the instruments agree with each other, and outside that region the disagreement is "
     "documented rather than resolved. Where both the model and the rubric abstain, the agreement of 1.000 measures "
     "shared silence, not shared judgement."),
]

REPORT_INTERP = [
    ('sec(doc, "7.1 Invariantes e geometria", [',
     "O valor da suite não está no número de testes, mas no que ela impede. I35 torna impossível carregar uma "
     "calibração incoherente; I38 transforma a ordenação dos stakes em propriedade do modelo, e não em expectativa "
     "sobre os parâmetros; I44 converte o gate de cobertura em uma variável visível e ajustável pelo auditor. Um "
     "revisador pode rederivar a geometria a partir do código sem depender do texto: os quinze slots do lattice, "
     "seus pesos e suas incidências são calculados, não declarados."),
    ('sec(doc, "7.2 Probes adversários", [',
     "Uma taxa de passagem de 1,000 não prova que o modelo esteja certo; prova que nenhuma entrada construída para "
     "quebrá-lo conseguiu quebrar as promessas que a aritmética faz sobre si mesma. A consequência prática é "
     "estreita, mas utilizável: a lacuna de compensação encontrada em v12, um nível alto em um dever cobrindo um "
     "dever falho em outro, passa a registrar falha de guarda e gap material, de modo que a auditoria cita um "
     "evento e não interpreta uma pontuação."),
    ('sec(doc, "7.3 Que mecanismos mudam realmente a concordância", [',
     "Dois mecanismos mudam o veredicto por uma razão que a auditoria pode nomear; dois não. Inferir o regime de "
     "supervisão a partir dos fatos declarados eleva a concordância porque um caso revisado é tratado de forma "
     "diferente de um caso não revisado. Diferenciar as β eleva a concordância porque deveres indistinguidos passam "
     "a ser distinguidos. Saliência e dever transversal movem as saídas sem mover o julgamento, por isso permanecem "
     "como diagnósticos: a equipe de governança pode inspecioná-los, mas o veredicto não depende deles. A regra que "
     "a rodada estabelece é que um mecanismo é adotado apenas quando seu efeito é medido, tem sinal e é "
     "significativo."),
    ('sec(doc, "7.4 Ablação do canon", [',
     "O peso normativo do modelo está exatamente onde o projeto o colocou. Remover as doze guardas duras leva κ "
     "de 0,4633 a 0,1399, uma queda de 69,8%: as guardas não são um detalhe de estilo, são o mecanismo que produz o "
     "comportamento que as rubricas valorizam. Os deltas individuais dizem o contrário, nenhuma guarda se defende "
     "isoladamente, e o canon deve ser defendado como conjunto. Para uma organização que implanta o modelo, isso "
     "significa que os pisos não podem ser negociados dever a dever sem destruir a propriedade para a qual o modelo "
     "existe."),
    ('sec(doc, "7.5 Ancoragem factual (E30)", [',
     "Declarar um nível não é entregá-lo. Quase todo perfil afirma um nível que os fatos do próprio caso "
     "contradizem, e corrigir isso muda quase metade dos veredictos. O aumento de κ de 0,2463 para 0,5526 não é "
     "efeito de ajuste, é a diferença entre julgar o que o agente afirma e julgar o que o agente pode demonstrar. "
     "Uma trilha de auditoria construída apenas sobre níveis declarados superestimaria sistematicamente a agência."),
    ('sec(doc, "7.6 Sensibilidade dos parâmetros", [',
     "Dois parâmetros governam o modelo, e ambos devem constar no registro de auditoria em lugar de residir em um "
     "valor-padrão do código: o gate de cobertura decide quando o modelo pode falar, e a penalidade estrutural "
     "decide quanto pesa um déficit. Todo o resto é comparativamente plano, inclusive coeficientes a que rodadas "
     "anteriores dedicaram esforço. Para quem implanta, é uma constatação de governança, não uma curiosidade "
     "numérica, porque as configurações de maior influência definem o alcance do julgamento e precisam ser "
     "declaradas, versionadas e revisadas."),
    ('sec(doc, "7.7 O espelho aritmético", [',
     "O espelho fecha a distância entre o texto e a implementação: quem lê apenas o grafo obtém o mesmo veredicto "
     "que o código, grandeza por grandeza. Também traz um alerta que vale fora deste projeto, porque a divergência "
     "desapareceu somente quando o espelho reconstruiu os níveis sem arredondar. Um espelho alimentado com valores "
     "arredondados parece correto e não é: a precisão de armazenamento declarada faz parte da verificação, não do "
     "detalhe."),
    ('sec(doc, "7.8 Ruído, histerese e ablação estrutural", [',
     "A assimetria é o achado. Quando as observações se degradam, o modelo torna-se mais restritivo vinte vezes mais "
     "frequentemente do que mais permissivo: o ruído empurra o veredicto para a cautela, não para a permissão. A "
     "histerese bloqueia 6.382 flexibilizações, de modo que um perfil não oscila na fronteira de decisão. O efeito "
     "quase nulo de remover os termos estruturais é um resultado negativo e é reportado como tal, porque o tetraedro "
     "organiza o registro, mas não gera o julgamento."),
    ('sec(doc, "7.9 Risco, agência e transferência", [',
     "Duas conclusões práticas decorrem da mesma bateria. O risco pertence ao caso, 98,07% da sua variância vem dos "
     "deveres e do contexto, não do agente. A admissibilidade pertence à delegação, 15,46% dos casos mudam de "
     "veredicto conforme o perfil que os enfrenta, e 225 casos podem ser recuperados por uma agência melhor. "
     "Melhorar o agente não é o mesmo que reduzir o risco, e uma implantação que promete o segundo investindo no "
     "primeiro faz uma afirmação que o modelo pode medir e rejeitar."),
    ('sec(doc, "7.10 A concordância é uma propriedade do instrumento", [',
     "κ = 0,5336 não é uma medida da qualidade do modelo, e sim a sobreposição entre o modelo e um instrumento "
     "normativo particular. A afirmação defensável é qualificada: o modelo concorda com os instrumentos onde os "
     "instrumentos concordam entre si; fora dessa região, a divergência está documentada, não resolvida. Onde modelo "
     "e rubrica se abstêm juntos, a concordância de 1,000 mede silêncio compartilhado, não julgamento "
     "compartilhado."),
]

PAPER_DECLARATIONS = [
    "Data and code availability. Every figure quoted in this paper is produced by code that is part of the "
    "repository and by artefacts stored with it. The formal core, the corpus and rubric generators, the ontology "
    "generator and its validator, the batteries and the invariant tests are under the MIT licence; the model text, "
    "the ontologies and the facet registry are under CC BY-SA 4.0. Each round is registered in a manifest, "
    "manifest_r5.json for this one, which lists 47 artefacts with their SHA-256 hash, their size, the runtime of "
    "each execution and the git revision of the tree. Rounds r2 and r3 are frozen and are never edited in place: a "
    "new revision writes a new round directory, which is what makes the numbers re-derivable rather than merely "
    "reported. The corpus itself is generated from declared parameters, so the 220,400 (case, profile) pairs can be "
    "rebuilt by the generator and do not have to be distributed as a dataset. The blind adjudication packet, 120 "
    "cases and 360 cells, is included in the repository for the human panel.",
    "Author contributions. L. M. M. Palazzo: conceptualisation, formal modelling, implementation of the core, "
    "ontology engineering, execution of the batteries and writing. T. Vanzin: review of the formal layer, "
    "validation of the semantic layer and editorial revision. Both authors read and approved the final text.",
    "Competing interests. The authors declare no competing interests.",
    "Funding. This work was developed with internal resources of the Postgraduate Program in Engineering and "
    "Knowledge Management (PPGEGC) at the Federal University of Santa Catarina. No external funding body is "
    "involved, and no funder influenced the choice of mechanisms, the rejection of any parameter value or the "
    "reporting of the negative results.",
    "Ethics. The cases are synthetic and contain no personal or sensitive data. The normative instruments cited, "
    "the UDHR, the CRC, the GDPR, the AI Act, the Belmont and Helsinki declarations, the ILO declaration, ISO and "
    "NIST documents, are used as sources of duties and are quoted as instruments. Nothing in this paper is legal "
    "advice, and no body named here endorses the model.",
    "Use of artificial intelligence. Language-model tools assisted with drafting, section organisation and "
    "editorial revision. Every quoted number comes from an artefact listed in Appendix A and is re-derived by the "
    "consistency checker, so the arithmetic is not model-generated. The authors are responsible for the content and "
    "for the claims verified against the artefacts.",
    "Open-science status. Code, data definitions, evaluation artefacts, the ontology and the equations are "
    "distributed with the paper under the licences stated above. The paper is written so that each claim can be "
    "checked from the repository without contacting the authors.",
]

REPORT_DECLARATIONS = [
    "Disponibilidade de dados e de código. Todo número citado neste relatório é produzido por código incluído no "
    "repositório e por artefatos guardados junto dele. O núcleo formal, os geradores do corpus e da rubrica, o "
    "gerador e o validador da ontologia, as baterias e os testes de invariante estão sob licença MIT; o texto do "
    "modelo, as ontologias e o registro de facetas estão sob CC BY-SA 4.0. Cada rodada fica registrada em um "
    "manifest, manifest_r5.json no caso desta rodada, com 47 artefatos, seus SHA-256, tamanho, duração de execução "
    "e revisão de git. As rodadas r2 e r3 estão congeladas e nunca são editadas no lugar, porque uma nova revisão "
    "escreve uma nova rodada, e é isso que torna os números rederiváveis em lugar de apenas reportados. O corpus é "
    "gerado a partir de parâmetros declarados, de modo que os 220.400 pares (caso, perfil) podem ser reconstruídos "
    "pelo gerador e não precisam ser distribuídos como base de dados. O pacote de adjudicação cega, 120 casos e 360 "
    "células, está incluído no repositório para o painel humano.",
    "Contribuições dos autores. L. M. M. Palazzo: conceptualização, modelagem formal, implementação do núcleo, "
    "engenharia da ontologia, execução das baterias e escrita. T. Vanzin: revisão da camada formal, validação da "
    "camada semântica e revisão editorial. Ambos leram e aprovaram o texto final.",
    "Conflitos de interesse. Os autores declaram não ter conflitos de interesse.",
    "Financiamento. O trabalho foi desenvolvido com recursos internos do Programa de Pós-Graduação em Engenharia e "
    "Gestão do Conhecimento (PPGEGC) da Universidade Federal de Santa Catarina. Não houve entidade financiadora "
    "externa, e nenhuma entidade influenciou a escolha de mecanismos, a rejeição de valores de parâmetros ou a "
    "publicação dos resultados negativos.",
    "Aspectos éticos. Os casos são sintéticos e não contêm dados pessoais ou sensíveis. Os instrumentos normativos "
    "citados, UDHR, CRC, GDPR, AI Act, Belmont, Helsinki, ILO, ISO e NIST, são usados como fontes de deveres e "
    "citados como instrumentos. Nada neste relatório constitui aconselhamento jurídico, e nenhum órgão mencionado "
    "endossa o modelo.",
    "Uso de inteligência artificial. Ferramentas de modelagem de linguagem apoiaram a redação, a organização das "
    "seções e a revisão editorial. Cada número citado vem de um artefato listado no Apêndice A e é rederivado pelo "
    "verificador de consistência, de modo que a aritmética não foi gerada por modelo. A responsabilidade pelas "
    "afirmações verificadas contra os artefatos é dos autores.",
    "Condição de ciência aberta. Código, definições de dados, artefatos de avaliação, ontologia e equações são "
    "distribuídos junto ao texto sob as licenças indicadas. O relatório foi escrito para que cada afirmação possa "
    "ser conferida a partir do repositório, sem contato com os autores.",
]

CORRECTIONS = [
    (PAPER, 'calibration space) were run on a panel', 'calibration space, were run on a panel'),
    (PAPER, 'By domain, the highest agreement is TS and IC, the lowest TB and FI.',
            'By domain, agreement runs from 0.6110 in transport and 0.6103 in education down to 0.4624 in finance, '
            'with health at 0.4791 and telecommunications at 0.4790 in between. The spread across domains is 0.15, '
            'smaller than the spread produced by changing the rubric itself, which is why the instrument, not the '
            'domain, is the dominant source of disagreement.'),
    (REPORT, 'com mais frequência do que mais permissivo', 'mais frequentemente do que mais permissivo'),
    (REPORT, 'calibração de 12 dimensões) foram executados', 'calibração de 12 dimensões, foram executados'),
]


def insert_paragraphs(path, items, lead):
    lines = open(path, encoding="utf-8").read().split("\n")
    inserted = 0
    for heading, text in items:
        found = [i for i, line in enumerate(lines) if line.strip() == heading]
        if not found:
            print(f"  missing heading: {heading}")
            continue
        i = found[0]
        j = i + 1
        while lines[j].strip() != "])":
            j += 1
        if any(lead in line for line in lines[i:j]):   # idempotent: do not insert twice
            print(f"  already present: {heading}")
            continue
        lines.insert(j, '        ("p", "%s %s"),' % (lead, text))
        inserted += 1
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{path.split('/')[-1]}: {inserted} interpretations inserted")


def insert_block(path, anchor, block_lines):
    t = open(path, encoding="utf-8").read()
    if t.count(anchor) != 1:
        print(f"  anchor not unique ({t.count(anchor)}) in {path.split('/')[-1]}")
        return
    if any(line.strip() == block_lines[0] for line in t.split("\n")):
        print(f"  block already present in {path.split('/')[-1]}")
        return
    open(path, "w", encoding="utf-8").write(
        t.replace(anchor, "\n".join(block_lines) + "\n" + anchor))
    print(f"{path.split('/')[-1]}: declarations block added")


def main():
    insert_paragraphs(PAPER, PAPER_INTERP, "Interpretation.")
    insert_paragraphs(REPORT, REPORT_INTERP, "Interpretação.")

    for path, old, new in CORRECTIONS:
        t = open(path, encoding="utf-8").read()
        if t.count(old) != 1:
            print(f"  correction skipped ({t.count(old)}): {old[:40]}")
            continue
        open(path, "w", encoding="utf-8").write(t.replace(old, new))
        print(f"  corrected in {path.split('/')[-1]}: {old[:40]}")

    decl = ['    section(doc, "Declarations", [']
    for d in PAPER_DECLARATIONS:
        decl.append('        ("p", "%s"),' % d.replace('"', "'"))
    decl.append('    ])')
    insert_block(PAPER, '    section(doc, "References", [("b", REFS)])', decl)

    decl = ['    sec(doc, "Declarações", [']
    for d in REPORT_DECLARATIONS:
        decl.append('        ("p", "%s"),' % d.replace('"', "'"))
    decl.append('    ])')
    insert_block(REPORT, '    sec(doc, "Referências", [("b", REFS)])', decl)

    for path, meta_anchor, extra in (
        (PAPER, '"Round 5. Formal core v13; ontology v4.2; corpus v7.',
         "Prepared for open-access submission, November 2026. Code, evaluation artefacts and the ontology are "
         "distributed with the paper under the licences declared below."),
        (REPORT, '"artefato listado no Apêndice A.',
         "Relatório técnico-científico, novembro de 2026. Código, artefatos de avaliação e ontologia distribuídos "
         "junto ao texto."),
    ):
        t = open(path, encoding="utf-8").read()
        if "submission, November 2026" in t or "novembro de 2026" in t:
            print(f"  date line already in {path.split('/')[-1]}")
            continue
        if t.count(meta_anchor) != 1:
            print(f"  meta line not found in {path.split('/')[-1]}")
            continue
        open(path, "w", encoding="utf-8").write(
            t.replace(meta_anchor, meta_anchor + '"\n        "' + extra + '"'))
        print(f"  date and submission line added to {path.split('/')[-1]}")


if __name__ == "__main__":
    main()
