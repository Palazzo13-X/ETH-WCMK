"""Apply the author-year citation layer to the two v14 deliverables.

The DOCX files were already generated before the interruption. The defect left
behind is that 27 of the 43 entries of the reference list never appear in the
body of the paper. Academic style - the one used in Shared/ETH-WCMK v9.docx -
requires every listed source to be cited where the claim is made.

This script inserts the citations in the sentences that actually invoke them,
adds Morris (1991), sorts the reference list alphabetically and adds a running
footer with page numbers. It edits the build scripts in place; rerunning the
scripts rebuilds the DOCX.

Run:  python3 _analysis/paper/patch_citations.py
"""
import re

PAPER = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/build_paper_v14.py"
REPORT = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/build_report_pt.py"
HELPER = "/home/luiz/Documentos/Strata/Shared/_analysis/paper/docx_build_v14.py"

L = '             "'
NL = "\n"

PAPER_EDITS = [
    ("a route dispatched by an autonomous vehicle. Two objects must be ",
     "a route dispatched by an autonomous vehicle (Mittelstadt et al., 2016; Eubanks, 2018; Zuboff, 2019). Two objects must be "),

    ("score loses exactly the information that makes the verdict auditable.",
     "score loses exactly the information that makes the verdict auditable (Miller, 2019; Williams et al., 2022)."),

    ("Machine ethics has developed along four families. Top-down approaches encode principles or rules; bottom-up approaches ",
     "Machine ethics has developed along four families (Moor, 2006; Floridi, 2004; Wallach & Allen, 2008; Allen, Smit & Wallach, 2005; Anderson & Anderson, 2011). Top-down approaches encode principles or rules; bottom-up approaches "),

    ("learn values from data or interaction; hybrid approaches combine the two; and the governance tradition supplies ",
     "learn values from data or interaction; hybrid approaches combine the two; value-alignment programmes optimise objective functions (Bostrom & Yudkowsky, 2016); and the governance tradition supplies "),

    (L + "42001 (ISO/IEC, 2023) - that specify duties without formalising how a particular case satisfies them. " + NL +
     L + "(Moor, 2006; Floridi, 2004; Wallach & Allen, 2008; Allen, Smit, & Wallach, 2005).",
     L + "42001 (ISO/IEC, 2023), the Council of Europe Framework Convention (Council of Europe, 2024) and the NIST AI Risk Management Framework (NIST, 2023) - which enumerate duties without formalising how a particular case satisfies them (Jobin et al., 2019; Dignum, 2019)."),

    ("Industrial safety stacks - moderation APIs and guard models - solve a different problem: filtering content at scale. ",
     "Industrial safety stacks - moderation APIs and guard models - solve a different problem: filtering content at scale, in the way functional-safety and information-security standards govern failure modes (ISO, 2018; ISO/IEC, 2023; NIST, 2025). "),

    ("The design principle that distinguishes the model is non-compensation. A deficiency in one duty does not buy credit in ",
     "The design principle that distinguishes the model is non-compensation, a deontic commitment in the sense of Ross (2002): a duty that cannot be traded is not a weight in a score. A deficiency in one duty does not buy credit in "),

    ('not on its central value.")',
     'not on its central value. The model does not claim that the agent is virtuous (Vallor, 2016); it measures whether the duties the agent declared were met.")'),

    (L + "between duties. Its face lattice has fifteen slots",
     L + "between duties, a representational device in the sense of conceptual spaces (G\u00e4rdenfors, 2000). Its face lattice has fifteen slots"),

    ("The canon obeys three rules:",
     "The canon is deontic in the classical sense (Kant, 2012; Ross, 2002) and obeys three rules:"),

    ("Risk is a potential consequence modulated by the observed delivery capacity of the agent. It never vanishes: a ",
     "Risk is a potential consequence modulated by the observed delivery capacity of the agent, in the sense of responsibility for consequences that outlive the act (Jonas, 1984). It never vanishes: a "),

    (L + "supports. The model is a classical instance graph:",
     L + "supports (W3C, 2012; W3C, 2014; W3C, 2017). The model is a classical instance graph:"),

    (L + "instrument - Rio Declaration Principle 1, UDHR Article 10, UN CRC Article 12, GDPR Articles 5, 22 and 25, Belmont, " + NL +
     L + "Helsinki, ILO, ACM/IEEE codes, ISO 26262, IEC 62443, ISO 27001, NIST CSF, OECD - fire on declared facts and levels, ",
     L + "instrument - Rio Declaration Principle 1 (1992), UDHR Article 10 (United Nations, 1948), UN CRC Article 12 (United Nations, 1989), GDPR Articles 5, 22 and 25 (European Union, 2016), the Belmont Report (1978), the Declaration of Helsinki (1964), the ILO Declaration (International Labour Organization, 1998), ACM/IEEE codes, ISO 26262 (ISO, 2018), IEC 62443, ISO 27001 (ISO/IEC, 2023), NIST CSF (NIST, 2025), the OECD Recommendation (OECD, 2024) - fire on declared facts and levels, "),

    ("The consensus of the three panels is the reference. It is unanimous on 50.9% of the pairs",
     "The consensus of the three panels is the reference, and agreement with it is measured with Cohen's kappa (Cohen, 1960). It is unanimous on 50.9% of the pairs"),

    ('the verdict can always be reconstructed from the graph.")',
     'the verdict can always be reconstructed from the graph. The representation is canonical rather than lexical: two cases described in different words enter the same arithmetic only if they occupy the same conceptual roles, which is the semiotic assumption the model inherits (Peirce, 1931-1958; G\u00e4rdenfors, 2000).")'),

    (L + "this class of work - a paper whose numbers do not match its code.\"),",
     L + "this class of work - a paper whose numbers do not match its code. The trace fields - deficits, material gap, residual risk, review need, regime - are what make that claim auditable (Miller, 2019; Williams et al., 2022).\"),"),

    (L + "stratified: model, system and operator; the chain is evaluated at its weakest link and the result of each layer is ",
     L + "stratified - model, system, operator - because the capacity to act and the capacity to answer for the act are not the same thing (Frankfurt, 1971); the chain is evaluated at its weakest link and the result of each layer is "),

    ("Morris elementary effects (200 trajectories) and a paired Sobol design (N = 1,024 over the 12-dimensional ",
     "Morris elementary effects (200 trajectories; Morris, 1991) and a paired Sobol design (Sobol, 2001; Saltelli et al., 2008) with N = 1,024 over the 12-dimensional "),

    ('"Moor, J. H. (2006)',
     '"Morris, M. D. (1991). Screening designs for parameter sensitivity analysis for mathematical models. Reliability Engineering and System Safety, 33(1), 103-113.",\n    "Moor, J. H. (2006)'),
]

REPORT_EDITS = [
    ("34 node shapes SHACL sem violacoes", "34 node shapes SHACL (W3C, 2017) sem violacoes"),
]


def apply(path, edits):
    text = open(path, encoding="utf-8").read()
    ok = 0
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            print(f"  SKIP ({n} matches): {old[:60]}")
            continue
        text = text.replace(old, new)
        ok += 1
    open(path, "w", encoding="utf-8").write(text)
    print(f"{path}: {ok} edits applied")


def sort_refs(text):
    start = text.index("REFS = [")
    end = text.index("\n]", start)
    block = text[start:end]
    refs = re.findall(r'"([^"]+)"', block)
    ordered = sorted(refs)
    new_block = "REFS = [\n" + "\n".join(f'    "{r}"' for r in ordered)
    return text[:start] + new_block + text[end:]


if __name__ == "__main__":
    apply(PAPER, PAPER_EDITS)
    t = open(PAPER, encoding="utf-8").read()
    t = sort_refs(t)
    open(PAPER, "w", encoding="utf-8").write(t)
    print("reference list sorted")
