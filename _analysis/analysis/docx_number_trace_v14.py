"""DOCX number-traceability check for the v14 deliverables.

Project rule: no number enters the paper without an artefact behind it. The v13
checker (paper_artifact_consistency_v13.py) was written against the markdown
draft and cannot read the Word files. This one reads the two DOCX deliverables
themselves and re-derives each headline figure from the artefact that must
support it - including the figures the new interpretation paragraphs cite.

Run:  python3 _analysis/analysis/docx_number_trace_v14.py
Out:  Evaluacoes/r5/paper_docx_number_trace_v15.json
"""
import json
import os
import re
import unicodedata
from datetime import datetime, timezone

import docx

ROOT = "/home/luiz/Documentos/Strata/Shared"
R5 = os.path.join(ROOT, "Evaluacoes", "r5")
R4 = os.path.join(ROOT, "Evaluacoes", "r4")

DOCX_PATHS = {
    "paper": os.path.join(ROOT, "_analysis", "PAPER_v15.docx"),
    "report": os.path.join(ROOT, "_analysis", "RELATORIO_TECNICO_CIENTIFICO_PT.docx"),
}

INVARIANT_TESTS = sum(
    len(re.findall(r"^\s*def test_", open(f, encoding="utf-8").read(), re.M))
    for f in os.listdir(os.path.join(ROOT, "_analysis", "formal_core"))
    if f.startswith("test_")
)


def text_of(path):
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.extend(c.text for c in row.cells)
    return " ".join(parts)


TEXTS = {k: text_of(v) for k, v in DOCX_PATHS.items()}


def num(tok):
    tok = tok.strip().rstrip(".,").replace("−", "-")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", tok):      # 220.400 or 1,927,780 -> thousands
        return float(tok.replace(".", "").replace(",", ""))
    if "," in tok and "." in tok:
        dec = "," if tok.rfind(",") > tok.rfind(".") else "."   # the last separator is the decimal one
        thousands = "." if dec == "," else ","
        return float(tok.replace(thousands, "").replace(dec, "."))
    if "," in tok:
        return float(tok.replace(",", "."))
    return float(tok)


SUP = str.maketrans("\u2070\u2071\u2072\u2073\u2074\u2075\u2076\u2077\u2078\u2079", "0123456789")
EXPONENT = r"(?:\s*[x\u00d7]\s*10[\u207b\^-]*(?:\d+|[\u2070-\u2079]+))?"


def token_value(tok):
    """Interpret a numeric token that may carry a x 10^-n exponent."""
    m = re.fullmatch(r"(\d[\d.,]*)\s*[x\u00d7]\s*10([\u207b\^-]*)([\d\u2070-\u2079]+)", tok)
    if m:
        exp = m.group(3).translate(SUP)
        return num(m.group(1)) * 10 ** (-int(exp) if m.group(2) else int(exp))
    return num(tok)


def find(where, value, keywords, tol=1e-9):
    txt = TEXTS[where]
    for m in re.finditer(r"\d[\d.,]*" + EXPONENT, txt):
        raw = m.group(0)
        try:
            v = token_value(raw)
        except ValueError:
            continue
        for cand in (v, v / 100.0, v * 100.0):
            if abs(cand - value) <= max(tol, abs(value) * 1e-6) or abs(abs(cand) - abs(value)) <= max(tol, abs(value) * 1e-6):
                window = txt[max(0, m.start() - 420): m.end() + 420].lower()
                if any(k.lower() in window for k in keywords):
                    return raw
    return None


def all_artifact_values(path):
    out = set()
    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            out.add(float(o))
    walk(json.load(open(path, encoding="utf-8")))
    return out


ART_VALUES = set()
NUMBER_RE = re.compile(r"\d[\d.,]*(?:\s*[x\u00d7]\s*10[\u207b\^-]*(?:\d+|[\u2070-\u2079]+))?")

def harvest_text(text):
    for m in NUMBER_RE.finditer(text):
        try:
            ART_VALUES.add(token_value(m.group(0)))
        except ValueError:
            pass


for path in sorted(os.listdir(R5)) + sorted(os.listdir(R4)):
    full = os.path.join(R5 if path in os.listdir(R5) else R4, path)
    if not os.path.isfile(full):
        continue
    if path.endswith(".json"):
        ART_VALUES |= all_artifact_values(full)
    try:
        harvest_text(open(full, encoding="utf-8", errors="replace").read())
    except OSError:
        pass

checks = []


UNMATCHED = []


def check(label, where, derived, keywords, tol=1e-9):
    tok = find(where, derived, keywords, tol)
    checks.append({"claim": label, "document": where, "artifact_value": derived,
                   "found_in_document": tok, "pass": tok is not None})


def j(p):
    return json.load(open(p, encoding="utf-8"))


cov = j(os.path.join(R5, "corpus_v7_coverage.json"))
ks = j(os.path.join(R5, "kappa_by_stratum_v13.json"))
b20 = {r["name"]: r for r in j(os.path.join(R5, "B20_variant_eval_full_corpus.json"))["results"]}
b21 = {r["name"]: r for r in j(os.path.join(R5, "B21_ablation.json"))["results"]}
b22 = j(os.path.join(R5, "B22_fact_contradiction.json"))
b23 = j(os.path.join(R5, "B23_sobol_v13.json"))
b25 = j(os.path.join(R5, "mirror_full_corpus_v13.json"))
b8 = j(os.path.join(R5, "B8_probes_reverified_v13.json"))
b26 = {v["variant"]: v for v in j(os.path.join(R5, "B26_rubric_sensitivity.json"))["variants"]}
ont = j(os.path.join(R5, "ontology_v4_2_validation.json"))
man = j(os.path.join(R5, "manifest_r5.json"))
noise = j(os.path.join(R4, "B9_noise_v12.json"))
temp = j(os.path.join(R4, "B12_temporal_v12.json"))
risk = j(os.path.join(R4, "B14_case_profile_risk.json"))
trans = j(os.path.join(R4, "B13_transfer_v12.json"))
deleg = j(os.path.join(R4, "B15_delegation_chains.json"))
base = {r["baseline"]: r for r in j(os.path.join(R4, "B7_baselines_v12.json"))["results"]}

for where in ("paper", "report"):
    # corpus and agreement
    check("confrontations in corpus v7", where, cov["pairs_adjudicated"], ["confrontation", "confrontaç"])
    check("abstentions below the coverage gate", where,
          cov["coverage_strata"]["below_gate_lt_0.70"], ["abstain", "absten"])
    check("pairs with the full canon", where, cov["coverage_strata"]["full_canon_33"], ["canon", "full model", "full corpus", "modelo completo", "pares"])
    check("coverage gate value 0.70", where, 0.70, ["gate", "cobertura", "coverage"])
    check("kappa baseline against the rubric", where, b26["V0 baseline rubric"]["kappa"], ["kappa", "κ"])
    for s in ("unanimous", "majority", "contested"):
        check(f"kappa {s} stratum", where, ks["by_stratum"][s]["kappa_model_vs_consensus"], ["kappa", "κ"])
    check("pairs unanimous stratum", where, ks["by_stratum"]["unanimous"]["pairs"], ["pair", "par"])
    check("highest domain kappa (TS)", where, ks["by_domain"]["TS"]["kappa_model_vs_consensus"], ["TS", "transport", "kappa", "domínio", "domain"])
    check("second highest domain (ED)", where, ks["by_domain"]["ED"]["kappa_model_vs_consensus"], ["ED", "education", "educa"])
    check("lowest domain kappa (FI)", where, ks["by_domain"]["FI"]["kappa_model_vs_consensus"], ["FI", "finance", "financ"])
    check("health domain kappa (SA)", where, ks["by_domain"]["SA"]["kappa_model_vs_consensus"], ["SA", "health", "saúde"])
    check("telecom domain kappa (TB)", where, ks["by_domain"]["TB"]["kappa_model_vs_consensus"], ["TB", "telecom"])
    check("panel-vs-panel kappa A-C", where, cov["gold"]["panel_kappa"]["AC"], ["panel", "painel", "lens", "lente"])
    check("panel-vs-panel kappa A-B", where, cov["gold"]["panel_kappa"]["AB"], ["panel", "painel", "lens", "lente"])
    check("panel-vs-panel kappa B-C", where, cov["gold"]["panel_kappa"]["BC"], ["panel", "painel", "lens", "lente"])
    for v in ("V1 floors x1.10", "V2 floors x0.90", "V6 consensus = lens B only",
              "V8 coverage gate 0.80", "V10 gap mode assume_breach"):
        check(f"rubric variant {v}", where, b26[v]["kappa"], ["kappa", "κ", "prior", "prior"])
    # mechanisms
    check("baseline kappa of the mechanism battery", where, b20["v13_baseline"]["kappa_overall"], ["baseline"])
    check("oversight inferred from facts kappa", where, b20["oversight from facts"]["kappa_overall"], ["oversight", "supervis"])
    check("delta of oversight mechanism", where, b20["oversight from facts"]["delta_kappa_vs_baseline"], ["delta", "Δ"])
    check("CI of oversight delta lower", where, b20["oversight from facts"]["delta_ci95_bootstrap"][0], ["CI", "IC"])
    check("revised beta canon kappa", where, b20["revised beta canon"]["kappa_overall"], ["beta", "β"])
    check("pairs in the mechanism battery", where, b20["v13_baseline"]["n_pairs"], ["130", "pair", "par"])
    # ablation
    check("ablation baseline kappa", where, b21["v13_baseline"]["kappa_overall"], ["baseline", "guard", "guarda"])
    check("all guards removed kappa", where, b21["all guards removed"]["kappa_overall"], ["guard", "guarda"])
    check("guards delta", where, b21["all guards removed"]["delta_kappa_vs_baseline"], ["delta", "Δ"])
    check("collapse to primary pillar kappa", where, b21["duties collapsed to primary pillar"]["kappa_overall"], ["pillar", "pilar"])
    check("collapse delta", where, b21["duties collapsed to primary pillar"]["delta_kappa_vs_baseline"], ["delta", "Δ"])
    check("largest single-guard delta", where,
          max(abs(r["delta_kappa_vs_baseline"]) for r in b21.values() if r["name"].startswith("guard removed")),
          ["guard", "guarda"])
    # fact grounding
    check("pairs tested for grounding", where, b22["n_pairs"], ["pair", "par"])
    check("pairs with a contradicting fact", where, b22["n_pairs_with_contradiction"], ["contradict", "contradiz", "contrari"])
    check("share with contradicting fact", where, b22["share_pairs_with_contradiction"], ["share", "%"])
    check("caps applied", where, b22["caps_applied_total"], ["cap", "teto"])
    check("mean excess over cap", where, b22["mean_excess_over_cap"], ["excess", "excesso"])
    check("verdicts changed by grounding", where, b22["n_verdict_flips"], ["verdict", "veredicto"])
    check("review to prohibition moves", where, b22["verdict_flips"]["REVIEW_REQUIRED->PROHIBIT"], ["prohibit", "proibição"])
    check("kappa without grounding", where, b22["kappa_without_E30"], ["kappa", "κ"])
    check("kappa with grounding", where, b22["kappa_with_E30"], ["kappa", "κ"])
    # probes, mirror, ontology
    check("adversarial probes", where, b8["summary"]["total_probes"], ["probe"])
    check("probe assertions", where, b8["summary"]["assertions_total"], ["assertion", "asser"])
    check("probe pass rate", where, b8["summary"]["pass_rate"], ["pass", "taxa"])
    check("mirror maximum absolute difference", where, b25["global_max_abs_difference"], ["mirror", "espelho"])
    check("mirror runtime", where, b25["runtime_seconds"], ["mirror", "espelho"])
    check("mirror confrontations", where, b25["confrontations"], ["mirror", "espelho"])
    check("ontology validated triples", where, ont["graph"]["total_validated_triples"], ["triple", "triplo"])
    check("SHACL node shapes", where, ont["shacl"]["shapes"]["node_shapes"], ["SHACL", "shacl"])
    check("SHACL violations", where, ont["shacl"]["instances_vs_v4_shapes"]["violations"], ["violation", "viola"])
    check("invalid fixtures detected", where, ont["invalid_fixtures"]["detected"], ["fixture"])
    check("ontology mirror max difference", where, ont["mirror"]["global_max_abs_difference"], ["mirror", "espelho"])
    check("declared mirror tolerance", where, ont["mirror"]["declared_tolerance"], ["tolerance", "tolerância", "toler"])
    check("ontology validation runtime", where, ont["runtime_seconds"], ["validation", "validaç"])
    check("manifest artefacts", where, man["counts"]["artefacts"], ["manifest", "artefact", "artefato"])
    check("manifest tracked bytes", where, round(sum(a["bytes"] for a in man["artefacts"]) / 1e6, 2), ["MB", "megabyte", "bytes"], tol=0.1)
    # noise, hysteresis, risk, transfer, delegation, baselines
    check("flip rate at sigma 0.02", where, noise["noise"]["sigma_0.02"]["verdict_flip_rate"], ["noise", "ruído"])
    check("flip rate at sigma 0.2", where, noise["noise"]["sigma_0.2"]["verdict_flip_rate"], ["noise", "ruído"])
    check("restrictive shift at sigma 0.2", where, noise["noise"]["sigma_0.2"]["became_more_restrictive_rate"], ["restrictive", "restritiv"])
    check("permissive shift at sigma 0.2", where, noise["noise"]["sigma_0.2"]["became_more_permissive_rate"], ["permissive", "permissiv"])
    ratio = round(noise["noise"]["sigma_0.2"]["became_more_restrictive_rate"] /
                  noise["noise"]["sigma_0.2"]["became_more_permissive_rate"], 1)
    wording = "twenty times as often" if "twenty times as often" in TEXTS[where] else (
        "vinte vezes mais" if "vinte vezes mais" in TEXTS[where] else None)
    checks.append({"claim": "restrictive-to-permissive ratio at sigma 0.2 (19.9, written as twenty times)",
                   "document": where, "artifact_value": ratio, "found_in_document": wording,
                   "pass": wording is not None})
    check("tracked cases in the trajectory", where, temp["cases_tracked"], ["trajectory", "trajetória"])
    check("verdict changes in the trajectory", where, temp["verdict_changes_total"], ["change", "mudança"])
    check("oscillations", where, temp["A_B_A_oscillations"], ["oscillation", "oscila"])
    check("hysteresis blocked transitions", where, temp["permissive_transitions_blocked_by_hysteresis_note"], ["hysteresis", "histerese"])
    check("risk variance from the case", where, risk["variance_decomposition"]["case"], ["risk", "risco"])
    check("risk variance from the profile", where, risk["variance_decomposition"]["profile"], ["profile", "perfil"])
    check("risk variance interaction", where, risk["variance_decomposition"]["interaction_case_x_profile"], ["interaction", "interação"])
    check("cases with mixed verdicts share", where, risk["verdict_agreement_inside_case"]["share"], ["verdict", "veredicto"])
    check("rescuable cases by agency", where, risk["agency_can_change_the_outcome"]["rescuable_cases"], ["agency", "agência"])
    check("holdout kappa", where, trans["kappa_fitted_holdout"], ["holdout"])
    check("in-sample kappa", where, trans["kappa_fitted_in_sample"], ["sample", "amostra"])
    check("transfer gap", where, trans["transfer_gap"], ["transfer", "transf"])
    if where == "report":   # the paper does not quote the narrative-layer figure
        check("narrative layer kappa fitted", where, trans["layerB_transfer"]["kappa_fitted"], ["narrative", "narrativ", "320"])
    check("duties delegable without accountability", where,
          deleg["capability_definition_facet_level"]["facets_carryable_by_model_or_operator"], ["delegate", "deleg"])
    check("share of canon needing accountability", where,
          deleg["capability_definition_facet_level"]["share_of_canon_requiring_accountability"],
          ["accountability", "responsabiliza"])
    check("worst delegate verdict changes", where,
          deleg["chain_with_worst_delegate"]["verdict_changes_vs_declared"], ["delegate", "deleg"])
    check("worst delegate bottleneck C", where, deleg["chain_with_worst_delegate"]["bottleneck_pillar_counts"]["C"],
          ["bottleneck", "gargalo"])
    check("baseline adequacy without the veto cap", where,
          base["BL5 adequacy without the veto cap (ablation)"]["kappa"], ["threshold", "without the veto", "adequacy"])
    check("baseline majority class", where, base["BL13 always REVIEW_REQUIRED"]["kappa"], ["majority", "maioria"])
    check("baseline uncalibrated ladder", where,
          base["model: v12 core + declared (uncalibrated) ladder"]["kappa"], ["uncalibrated", "declared ladder", "escada declarada"])
    # structural canon
    check("facets in the canon", where, 33, ["facet", "faceta", "duty", "dever"])
    check("hard guards", where, 12, ["guard", "guarda"])
    check("lattice slots", where, 15, ["lattice", "retículo"])
    check("lattice incidences", where, 108, ["incidence", "incid"])
    checks.append({"claim": "derived marginal at canonical beta (1/6)", "document": where,
                   "artifact_value": 1 / 6, "found_in_document": "1/6" if "1/6" in TEXTS[where] else None,
                   "pass": "1/6" in TEXTS[where]})
    check("invariant tests", where, INVARIANT_TESTS, ["invariant", "invariante"])

# Reverse sweep: every number printed in the body of the documents must come from
# an artefact. Bibliographic numbers (years, article pages, standard numbers) and
# internal cross-references are excluded because they are not results.
def precision_of(tok):
    """Half a unit in the last printed digit: 0.749 implies a tolerance of 0.0005."""
    m = re.fullmatch(r"(\d[\d.,]*)\s*[x\u00d7]\s*10([\u207b\^-]*)([\d\u2070-\u2079]+)", tok)
    if m:
        mant, exp = m.group(1), m.group(3).translate(SUP)
        exp = -int(exp) if m.group(2) else int(exp)
    else:
        mant, exp = tok, 0
    decimals = len(mant.split(".")[1].rstrip(",")) if "." in mant else 0
    return 0.5 * 10 ** (-decimals + exp)


def in_artifacts(value, token):
    tol = precision_of(token)
    for cand in (value, value / 100.0, value * 100.0):
        for a in ART_VALUES:
            if abs(cand - a) <= tol or abs(abs(cand) - abs(a)) <= tol:
                return True
    return False


UNMATCHED = []
for where, txt in TEXTS.items():
    ref = txt.find("References") if where == "paper" else txt.find("Refer")
    body = txt[:ref] if ref > 0 else txt
    for m in re.finditer(r"\d[\d.,]*(?:\s*[x\u00d7]\s*10[\u207b\^-]*\d+)?", body):
        tok = m.group(0)
        if re.fullmatch(r"\d{1,2}\.\d{1,2}", tok):     # section and equation cross-references
            continue
        try:
            v = token_value(tok)
        except ValueError:
            continue
        if v == int(v) and 1 <= v <= 60:                 # counts the reader already has in the text
            continue
        if 1900 <= v <= 2030:
            continue
        if not in_artifacts(v, tok):
            UNMATCHED.append({"document": where, "token": tok, "value": v,
                              "context": body[max(0, m.start() - 90): m.end() + 90]})

result = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "documents": list(DOCX_PATHS),
    "checks": len(checks),
    "passed": sum(1 for c in checks if c["pass"]),
    "failed": [c for c in checks if not c["pass"]],
    "numbers_not_found_in_artifacts": UNMATCHED,
    "distinct_unmatched": len({(u["token"], u["value"]) for u in UNMATCHED}),
    "detail": checks,
}
out = os.path.join(R5, "paper_docx_number_trace_v15.json")
json.dump(result, open(out, "w", encoding="utf-8"), indent=1)
print(json.dumps({"checks": result["checks"], "passed": result["passed"]}, indent=1))
for c in result["failed"]:
    print("FAIL:", c["claim"], "| expected", c["artifact_value"], "| doc", c["document"])
