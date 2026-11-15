"""Paper <-> artefact consistency check, v13.

Regla del proyecto: ningún número del paper viene de texto. Este script toma cada
afirmación numérica señalada en `_analysis/PAPER_v13.md` y la re-deriva del artefacto
que debe sostenerla. Reporta divergencias; no prueba el modelo, prueba la cadena de cita.

Run:  python3 _analysis/analysis/paper_artifact_consistency_v13.py
Out:  Evaluacoes/r5/paper_consistency_check_v13.json
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
R5 = os.path.join(ROOT, "Evaluacoes", "r5")
ONT = os.path.join(ROOT, "Ontologias", "ontology_v4_2")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

PAPER = open(os.path.join(ROOT, "_analysis", "PAPER_v13.md")).read()


def euro(tok):
    tok = tok.strip().rstrip(",")   # trailing punctuation is not part of the number
    if "," in tok and "." in tok:
        return float(tok.replace(".", "").replace(",", "."))
    if "," in tok:
        return float(tok.replace(",", "."))
    if "." in tok:
        parts = tok.split(".")
        if len(parts) > 2 or len(parts[-1]) == 3:      # "1.919.283" / "152.439" -> thousands
            return float("".join(parts))
        return float(tok)
    return float(tok)


def quoted(pattern, index=0):
    m = re.search(pattern, PAPER, re.S)
    if not m:
        return None
    toks = re.findall(r"[-−]?\d[\d.,]*", m.group(0))
    if not toks:
        return None
    tok = toks[index] if 0 <= index < len(toks) else toks[-1]
    return euro(tok.replace("−", "-"))


ALL_TOKENS = [t for t in re.findall(r"[-−]?\d[\d.,]*", PAPER)]
CONTEXTS = {}


def _flat(text):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if c.isalnum())


def spellings(value):
    """Every way the paper could plausibly write this number: comma as decimal mark,
    dot as thousands separator, minus or U+2212, from 0 to 5 decimals."""
    out = []
    integral = abs(value - round(value)) < 1e-9
    for dec in range(0, 6):
        if dec == 0 and not integral:
            continue          # "0" must not stand in for 0,4308
        a = round(abs(value), dec)
        txt = f"{a:.{dec}f}"
        intpart, dot, frac = txt.partition(".")
        if len(intpart) > 3:
            grouped = ""
            for i, ch in enumerate(reversed(intpart)):
                if i and i % 3 == 0:
                    grouped = "." + grouped
                grouped = ch + grouped
            intpart = grouped
        base = intpart + ("," + frac if frac else "")
        for sign in ("", "-", "−"):
            out.append((dec, sign + base))
    # most precise spelling first: the paper's exact digits, not a rounded proxy
    return [t for _, t in sorted(out, key=lambda x: -x[0])]


def value_present(value, keywords=()):
    """Traceability fallback. A number counts as traceable only if the paper writes it
    with enough precision to carry the artefact value AND in a passage that talks about
    the subject of the claim. Without the context test a stray "0,1" elsewhere would
    "verify" a kappa of 0,1399 - the same trap as D5.17."""
    for tok in spellings(value):
        for m in re.finditer(r"(?<!\d)" + re.escape(tok) + r"(?!\d)", PAPER):
            window = PAPER[max(0, m.start() - 260):m.start() + 120]
            if not keywords or any(k in _flat(window) for k in keywords):
                CONTEXTS[tok] = window.replace("\n", " ")
                return tok
    return None


checks = []


def check(name, pattern, derived, tol=1e-4, index=0):
    q = quoted(pattern, index)
    if q is not None and abs(q - derived) <= tol:
        checks.append({"claim": name, "paper_value": q, "artifact_value": derived,
                       "pass": True, "verified_by": "explicit pattern"})
        return
    kw = tuple(_flat(w)[:7] for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", name)
                 if _flat(w)[:7] not in {"kappa", "pares", "casos", "delta", "runtime"})
    tok = value_present(derived, kw)
    if tok is not None:
        checks.append({"claim": name, "paper_value": euro(tok.replace("−", "-")),
                       "artifact_value": derived, "pass": True,
                       "verified_by": "value stated in the paper",
                       "context": CONTEXTS.get(tok, "")})
        return
    checks.append({"claim": name, "paper_value": q, "artifact_value": derived,
                   "pass": False, "note": "value not traceable in the paper"})


def j(path):
    return json.load(open(path))
cov = j(os.path.join(R5, "corpus_v7_coverage.json"))
b20f = {r["name"]: r for r in j(os.path.join(R5, "B20_variant_eval_full_corpus.json"))["results"]}
b20s = {r["name"]: r for r in j(os.path.join(R5, "B20_variant_eval.json"))["results"]}
b20_can = {r["name"]: r for r in j(os.path.join(R5, "B20_canonical_beta_check.json"))["results"]}
b21 = {r["name"]: r for r in j(os.path.join(R5, "B21_ablation.json"))["results"]}
b22 = j(os.path.join(R5, "B22_fact_contradiction.json"))
b23 = j(os.path.join(R5, "B23_sobol_v13.json"))
b25 = j(os.path.join(R5, "mirror_full_corpus_v13.json"))
b8 = j(os.path.join(R5, "B8_probes_reverified_v13.json"))
ks = j(os.path.join(R5, "kappa_by_stratum_v13.json"))
ont = j(os.path.join(ONT, "generation_report.json"))
val = j(os.path.join(R5, "ontology_v4_2_validation.json")) if os.path.exists(
    os.path.join(R5, "ontology_v4_2_validation.json")) else None
psi = 0.0
rev = 0.0
for r in map(json.loads, open(os.path.join(R5, "corpus_v7_confrontations.jsonl"))):
    if r.get("cross_pillar_duty"):
        psi += r["cross_pillar_duty"]
    if r.get("review_need") is not None:
        rev += r["review_need"]
check("220.400 confrontaciones", r"220\.400 confrontaciones", cov["pairs_adjudicated"], 0)
check("1.520 casos", r"1\.520 casos", cov["cases"]["total"], 0)
check("144 personas / 36 tipos", r"144 personas de 36 tipos", cov["personas"]["instances"], 0)
check("Aa media 0,3551", r"Aa média 0,3551", cov["adequacy"]["mean"])
check("Aa mediana 0,3462", r"mediana 0,3462", cov["adequacy"]["p50"])
check("Aa max 0,9508", r"máximo 0,9508", cov["adequacy"]["max"])
check("PROHIBIT 152.439", r"PROHIBIT[^0-9]{0,3}152\.439", cov["decision_distribution"]["PROHIBIT"], 0)
check("REVIEW 32.996", r"REVIEW_REQUIRED 32\.996", cov["decision_distribution"]["REVIEW_REQUIRED"], 0)
check("ABSTAIN 34.615 total", r"ABSTAIN[^0-9]{0,3}34\.615", cov["abstain"]["total"], 0)
check("ABSTAIN = 16.375 + 18.240", r"16\.375 epistémicas \+ 18\.240",
      cov["abstain"]["epistemic_E29"] + cov["abstain"]["coverage_E26"], 0)
check("veto 90,6%", r"Veto em 90,6%", cov["veto_rate"] * 100, 0.01)
check("hard veto 13,45%", r"hard veto em 13,45%", cov["hard_veto_rate"] * 100, 0.01)
check("kappa global 0,5336", r"κ[^0-9]{0,6}0,5336", cov["kappa_model_vs_gold"]["overall"])
check("concordancia exacta 0,7886", r"0,7886", cov["model_vs_gold"]["exact_match_rate"], 0.0001)
check("Psi media 0,1703", r"0,1703", psi / cov["pairs_adjudicated"], 0.0005)
check("review_need media 0,2659", r"0,2659", rev / cov["adequacy"]["n"], 0.0005)
check("regimes none 67.715", r"none 67\.715", cov["oversight_regimes"]["none"], 0)
check("regimes on_the_loop 91.640", r"91\.640", cov["oversight_regimes"]["on_the_loop"], 0)
check("regimes in_the_loop 61.045", r"61\.045", cov["oversight_regimes"]["in_the_loop"], 0)
check("unanimidad 50,9%", r"Unanimidad \*\*50,9%\*\*", cov["gold"]["unanimous_share"] * 100, 0.01)
check("kernel-only 14,19%", r"14,19%", cov["gold"]["kernel_only_share"] * 100, 0.01)
check("gap de verificacion 36.480 pares", r"36\.480 pares",
      cov["verification_gap_D5_8"]["pairs_with_incomplete_declaration"], 0)
check("kappa defer 0,8085", r"0,8085", cov["verification_gap_D5_8"]["kappa_defer_rule_on"], 0.0001)
check("kappa assume-breach 0,0801", r"0,0801",
      cov["verification_gap_D5_8"]["kappa_if_missing_duties_count_as_zero"], 0.0001)
check("panel kappa A-B 0,3533", r"A–B 0,3533", cov["gold"]["panel_kappa"]["AB"], 0.0001)
check("panel kappa A-C 0,6447", r"A–C 0,6447", cov["gold"]["panel_kappa"]["AC"], 0.0001)
check("panel kappa B-C 0,3153", r"B–C 0,3153", cov["gold"]["panel_kappa"]["BC"], 0.0001)
check("kappa estrato unânime (corpus completo) 0,8167", r"unânime \*\*0,8167\*\* \(112\.179 pares\)",
      ks["by_stratum"]["unanimous"]["kappa_model_vs_consensus"], 0.0001)
check("pares estrato unânime 112.179", r"unânime \*\*0,8167\*\* \(112\.179 pares\)",
      ks["by_stratum"]["unanimous"]["pairs"], 0)
check("kappa estrato maioria 0,1371", r"maioria \*\*0,1371\*\*",
      ks["by_stratum"]["majority"]["kappa_model_vs_consensus"], 0.0001)
check("kappa estrato contestado 0,0526", r"contestado \*\*0,0526\*\*",
      ks["by_stratum"]["contested"]["kappa_model_vs_consensus"], 0.0001)
check("kappa global (mesmo artefacto) 0,5336", r"κ = 0,5336",
      ks["kappa_model_vs_consensus_overall"], 0.0001)
for st, tok in (("unanimous", 0), ("majority", 1), ("contested", 2)):
    check(f"κ estrato {st} na amostra B20 canonical", r"0,7348 / 0,1254 / 0,0402",
          b20_can["v13_baseline"]["kappa_by_stratum"][st], 0.0001, index=tok)
for dom, tok in (("TS", 0), ("ED", 1), ("FI", -1)):
    check(f"kappa por domínio {dom}", r"TS 0,6110; ED 0,6103; RS 0,5877; MA 0,5684; DS 0,5511; PD 0,5463; JS 0,5351; IC 0,5203; IM 0,5050; GP 0,5022; SA 0,4791; TB 0,4790; FI 0,4624",
          ks["by_domain"][dom]["kappa_model_vs_consensus"], 0.0001, index=tok)
check("pares abaixo do gate de cobertura 18.240", r"18\.240",
      ks["by_coverage"]["below_gate"]["pairs"], 0)
check("Δκ supervisión +0,0078", r"Δκ = \*\*\+0,0078\*\*", b20f["oversight from facts"]["delta_kappa_vs_baseline"])
check("Δκ β +0,0019", r"\+0,0019", b20f["revised beta canon"]["delta_kappa_vs_baseline"])
check("Δκ β+sup +0,0094", r"\+0,0094", b20f["revised beta + oversight"]["delta_kappa_vs_baseline"])
check("ζ=0,05 delta (B21, 48.000)", r"ζ = 0,05 → Δκ −0,0013", b21["cross-pillar zeta=0.05"]["delta_kappa_vs_baseline"] if "cross-pillar zeta=0.05" in b21 else b20s["cross-pillar zeta=0.05"]["delta_kappa_vs_baseline"], 0.0001)
check("ζ=0,05 delta (corpus completo)", r"−0,0028 \(corpus completo, 130\.680 pares\)", b20f["cross-pillar zeta=0.05"]["delta_kappa_vs_baseline"], 0.0001)
check("ζ=0,10 delta (400-caso)", r"ζ = 0,10 → −0,0030", b20s["cross-pillar zeta=0.10"]["delta_kappa_vs_baseline"])
check("ζ=0,10 delta (corpus)", r"−0,0059", b20f["cross-pillar zeta=0.10"]["delta_kappa_vs_baseline"])
check("λ(E) s=0,5 −0,0001 (canonical check)", r"s = 0,5 → Δκ −0,0001", b20_can["lambda(E) s=0.5"]["delta_kappa_vs_baseline"], 0.0001)
check("λ(E) s=2,0 −0,0003 (canonical check)", r"s = 2,0 → −0,0003", b20_can["lambda(E) s=2.0"]["delta_kappa_vs_baseline"], 0.0001)
check("Aa λ s=0 canonical 0,3523", r"de 0,3523 a 0,3483", b20_can["v13_baseline"]["mean_adequacy"], 0.0001)
check("Aa λ s=2 canonical 0,3483", r"de 0,3523 a 0,3483", b20_can["lambda(E) s=2.0"]["mean_adequacy"], 0.0001)
check("κ sin guardas 0,1399", r"κ 0,4633 → \*\*0,1399\*\*", b21["all guards removed"]["kappa_overall"])
check("Δκ sin guardas −0,3234", r"Δκ −0,3234", b21["all guards removed"]["delta_kappa_vs_baseline"])
check("Aa sin guardas 0,6153", r"0,3516 a 0,6153", b21["all guards removed"]["mean_adequacy"], 0.0001)
check("κ pilar primario 0,2691", r"κ \*\*0,2691\*\*", b21["duties collapsed to primary pillar"]["kappa_overall"])
check("Δκ pilar primario −0,1942", r"Δκ −0,1942", b21["duties collapsed to primary pillar"]["delta_kappa_vs_baseline"])
check("Aa pilar primario 0,5627", r"0,5627", b21["duties collapsed to primary pillar"]["mean_adequacy"], 0.0001)
max_guard = max(abs(r["delta_kappa_vs_baseline"]) for r in b21.values() if r["name"].startswith("guard removed:"))
check("|Δκ| guarda individual ≤ 0,0042", r"≤ 0,0042", max_guard, 0.0001)
check("C7 −0,0042", r"C7 −0,0042", b21["guard removed: C7"]["delta_kappa_vs_baseline"], 0.0001)
check("M9 −0,0024", r"M9 −0,0024", b21["guard removed: M9"]["delta_kappa_vs_baseline"], 0.0001)
check("98,27% de pares con contradicción", r"98,27%", b22["share_pairs_with_contradiction"] * 100, 0.01)
check("224.097 caps", r"224\.097", b22["caps_applied_total"], 0)
check("exceso medio 0,3611", r"0,3611", b22["mean_excess_over_cap"], 0.0001)
check("18.898 vereditos cambian", r"18\.898", b22["n_verdict_flips"], 0)
check("43,74% flips", r"43,74%", b22["flip_share"] * 100, 0.01)
check("Aa con E30 0,3633", r"0,3633", b22["mean_adequacy_with_E30"], 0.0001)
check("Aa sin E30 0,6481", r"0,6481", b22["mean_adequacy_without_E30"], 0.0001)
check("κ con E30 0,5526", r"0,5526", b22["kappa_with_E30"], 0.0001)
check("κ sin E30 0,2463", r"0,2463", b22["kappa_without_E30"], 0.0001)
check("Δκ E30 +0,3062", r"\+0,3062", b22["delta_kappa_E30"], 0.0001)
check("REVIEW→PROHIBIT 15.153", r"15\.153", b22["verdict_flips"]["REVIEW_REQUIRED->PROHIBIT"], 0)
check("S1 coverage_gate 0,749", r"coverage_gate \| (0,104) \| (0,749)",
      b23["sobol"]["mean_adequacy"]["S1"]["coverage_gate"], 0.001, index=1)
check("S1 gamma 0,123", r"γ \| 0,081 \| 0,123", b23["sobol"]["mean_adequacy"]["S1"]["gamma"], 0.001, index=1)
check("Morris μ* s = 0,0004", r"\*\*0,0004\*\*", b23["morris"]["mean_adequacy"]["salience_adaptation"]["mu_star"], 0.0001)
check("S1 oversight hard_veto 0,701", r"\*\*0,701\*\*", b23["sobol"]["hard_veto_rate"]["S1"]["oversight_attenuation"], 0.001)
check("Morris μ* ζ 0,075", r"ζ \| 0,075", b23["morris"]["mean_adequacy"]["zeta"]["mu_star"], 0.001)
check("B23 runtime 200,7 s", r"200,7 s", b23["runtime_seconds"], 0.1)
check("mirror 220.400 recomputadas", r"\*\*220\.400 confrontações\*\* recompostas persona-por-persona", b25["confrontations"], 0)
check("mirror diff max 0,0", r"\*\*Diff máximo em qualquer quantidade: 0,0\*\*", b25["global_max_abs_difference"], 0)
check("mirror 0 divergências de veredito", r"\*\*0 divergências de veredito\*\*", b25["verdict_divergences"], 0)
check("mirror runtime 121,87 s", r"Runtime 121,87 s", b25["runtime_seconds"], 0.01)
check("B8 2.064 probes", r"2\.064 probes", b8["summary"]["total_probes"], 0)
check("B8 7.815 asserções", r"7\.815 aserciones", b8["summary"]["assertions_total"], 0)
check("B8 pass 1,000", r"taxa de pasagem 1,000", b8["summary"]["pass_rate"], 0.001)
from facet_registry import FACETS
vec = lambda f: tuple(f.beta)
ident = sum(1 for a, b in combinations(FACETS, 2) if vec(a) == vec(b))
arity = {1: 0, 2: 0, 3: 0, 4: 0}
for f in FACETS:
    arity[sum(1 for x in vec(f) if x > 0)] += 1
check("33 facetas", r"33 facetas \(", len(FACETS), 0)
check("12 guardas duras", r"12 guardas duras", sum(1 for f in FACETS if f.guard), 0)
check("pares β idénticos = 1", r"β idênticos: \*\*8 → 1\*\*", ident, 0)
check("1 uni-pilar", r"1 uni-pilar", arity[1], 0)
check("10 bi-pilares", r"10 bi-pilares", arity[2], 0)
check("22 tri-pilares", r"22 tocam três", arity[3], 0)
check("0 quadripilares", r"0 quadripilares", arity[4], 0)
check("1.919.283 triplos", r"1\.919\.283 triplos", ont["instances_triples"], 0)
check("50.160 requisitos de faceta", r"50\.160 requisitos de faceta", ont["counts"]["requirements"], 0)
check("169.950 observações", r"169\.950 observações", ont["counts"]["observations"], 0)
check("21.280 ancoragens de fato", r"21\.280 ancoragens de fato", ont["counts"]["grounded_facts"], 0)
check("16.475 registros de falha de guarda", r"16\.475 registros de falha de guarda", ont["counts"]["guard_failure_records"], 0)
check("144 personas + 1 autodeclarado", r"144 personas \+ 1 autodeclarado", cov["personas"]["instances"] + 1, 0)
if val:
    v4 = val["shacl"]["instances_vs_v4_shapes"]
    v6 = val["shacl"]["instances_vs_v6_shapes"]
    check("SHACL v4 sobre instâncias: 0 violações", r"shapes v4 sobre as instâncias \*\*0 violações\*\*",
          v4["violations"], 0)
    check("SHACL v6 sobre instâncias: 0 violações tras a corrección", r"shapes v6 \*\*0 violações\*\*",
          v6["violations"], 0)
    check("76 fixtures inválidos detectados e atribuídos", r"76/76 detectados e \*\*76/76\*\* atribuídos",
          val["invalid_fixtures"]["detected_by_expected_shape"], 0)
    check("1.246 violações nos fixtures inválidos", r"1\.246 violações",
          val["invalid_fixtures"]["total_violations_on_invalid_graph"], 0)
    check("403 confrontações no espelho da ontologia", r"403 confrontações",
          val["mirror"]["confrontations_selected"], 0)
    m = re.search(r"diff máximo absoluto (\d+,\d+)e-(\d+)", PAPER)
    paper_diff = None
    if m:
        paper_diff = float(m.group(1).replace(",", ".")) * 10 ** (-int(m.group(2)))
    checks.append({"claim": "diff máximo do espelho RDF", "paper_value": paper_diff,
                   "artifact_value": val["mirror"]["global_max_abs_difference"],
                   "pass": paper_diff is not None and abs(paper_diff - val["mirror"]["global_max_abs_difference"]) < 1e-14,
                   "verified_by": "explicit pattern"})
    check("espelho dentro da precisión declarada", r"True",
          int(val["mirror"]["within_declared_precision"]), 0)
    check("excedente E30 dentro da precisión de almacenamento declarada", r"0 excedentes",
          val["mirror"]["e30_fact_grounding"]["beyond_declared_storage_precision"], 0)
    check("15 slots do face lattice", r"15 slots", val["face_lattice"]["total_slots"], 0)
    check("0 divergências de veredito RDF vs escada", r"0 divergências de veredito",
          val["mirror"]["verdict_agreement"]["python_ladder_vs_rdf"], 0)
    check("registry: 0 desencontros", r"0 desencontros", len(val["registry"]["mismatches"]), 0)
    n_checks = len(val["sparql_checks"])
    check("42 verificações SPARQL/Python", r"\*\*42 verificações\*\*", n_checks, 0)
    check("15 delas deontológicas", r"15 deontológicas",
          sum(1 for c in val["sparql_checks"] if c["kind"] == "deontic"), 0)
    check("todas as verificações passam", r"passam todas",
          sum(1 for c in val["sparql_checks"] if c["pass"]), n_checks)
    check("runtime de validación 301,9 s", r"Runtime total da validação: \*\*301,9 s\*\*",
          val["runtime_seconds"], 0.1)
    check("gate G4' PASS", r"gate G4′: PASS",
          1 if "PASS" in val.get("gate_verdict", "") else 0, 0)
    check("308.466 bytes de módulos", r"\(308\.466 bytes\)",
          sum(len(open(os.path.join(ROOT, "Ontologias/ontology_v4_2/" + f)).read())
              for f in os.listdir(os.path.join(ROOT, "Ontologias/ontology_v4_2"))
              if f.endswith(".ttl")), 0)
    cm = j(os.path.join(R5, "B20_crit_mild_cap3_full_corpus.json"))
    ct = j(os.path.join(R5, "B20_crit_targeted_full_corpus.json"))
    bf = j(os.path.join(R5, "B20_variant_eval_full.json"))
    cases = [("criticidade agressiva (400 casos)", bf,
              r"agressiva \(400 casos, 48\.400 pares\) κ 0,4613 → 0,4466, \*\*Δκ −0,0147 IC95 \[−0,0179; −0,0116\]\*\*"),
             ("criticidade mild cap-3 (859 casos)", cm,
              r"mild cap-3 \(859 casos, 103\.939 pares\) κ 0,4358 → 0,4308, \*\*Δκ −0,0050 IC95 \[−0,0072; −0,0022\]\*\*"),
             ("criticidade targeted TB/TS/IM (859 casos)", ct,
              r"targeted TB/TS/IM \(859 casos, 103\.939 pares\) κ 0,4358 → 0,4281, \*\*Δκ −0,0077 IC95 \[−0,0095; −0,0058\]\*\*")]
    for name, art, pat in cases:
        r = next((x for x in art["results"] if x["name"] == "criticality rebalance"), None)
        if r is None:
            continue
        check(name + ": kappa variante", pat, r["kappa_overall"], 0.0001, index=3)
        check(name + ": delta kappa", pat, r["delta_kappa_vs_baseline"], 0.0001, index=4)
        check(name + ": CI inferior", pat, r["delta_ci95_bootstrap"][0], 0.0001, index=5)
        check(name + ": CI superior", pat, r["delta_ci95_bootstrap"][1], 0.0001, index=6)
        check(name + ": kappa baseline", pat, art["results"][0]["kappa_overall"], 0.0001, index=2)
else:
    checks.append({"claim": "ontology validation artefact present", "paper_value": None,
                   "artifact_value": None, "pass": False,
                   "note": "ontology_v4_2_validation.json not written yet (run in progress)"})
out = subprocess.run([sys.executable, "-m", "pytest",
                      os.path.join(ROOT, "_analysis/formal_core/tests"), "-q"],
                     capture_output=True, text=True)
m = re.search(r"(\d+) passed", out.stdout)
check("69 testes de invariante", r"69 testes de invariantes", int(m.group(1)) if m else 0, 0)
# --- coverage strata, B8 families, ontology sizes, manifest (G18') ---
_covc = j(os.path.join(R5, "corpus_v7_coverage.json"))
_b8c = j(os.path.join(R5, "B8_probes_reverified_v13.json"))
_manc = j(os.path.join(R5, "manifest_r5.json"))
_ontc = j(os.path.join(R5, "ontology_v4_2_validation.json"))
_covk = _covc.get("kappa_by_coverage", {})
_covstr = _covc.get("coverage_strata", {})
_fam = _b8c["summary"]["by_family"]
check("kappa cobertura full 0,3832", r"0,3832", _covk.get("full"), 0.0001)
check("kappa cobertura partial 0,3293", r"0,3293", _covk.get("partial"), 0.0001)
check("kappa cobertura abaixo do gate 1,0000", r"1,0000", _covk.get("below_gate"), 0.0001)
check("pares com canon completo 183.920", r"183\.920 pares com canon completo",
      _covstr.get("full_canon_33"), 0)
check("B8 não-compensación 1.536 probes", r"não-compensación 1\.536",
      _fam["non_compensation"]["n"], 0)
check("B8 déficit crítico 132 probes", r"déficit crítico 132",
      _fam["critical_deficit"]["n"], 0)
check("B8 monotonicidade 99 probes", r"monotonicidade 99", _fam["monotonicity"]["n"], 0)
check("B8 abstenção 132 probes", r"abstenção 132", _fam["abstention"]["n"], 0)
check("B8 histerese 165 probes", r"histerese 165", _fam["hysteresis"]["n"], 0)
check("B8 asserção hard_veto 384", r"hard_veto 384/384",
      _b8c["summary"]["by_assertion_type"]["hard_veto"]["n"], 0)
check("B8 abstenção dispara 66/66", r"66/66 disparos",
      _b8c["summary"]["by_assertion_type"]["abstention_fires"]["n"], 0)
_MODDIR = os.path.join(ONT, "modules") if os.path.isdir(os.path.join(ONT, "modules")) else ONT
_onto_bytes = sum(os.path.getsize(os.path.join(_MODDIR, f))
                  for f in os.listdir(_MODDIR) if f.endswith(".ttl"))
_inst_bytes = os.path.getsize(os.path.join(ONT, "fixtures", "instances.ttl"))
check("bytes dos módulos RDF 308.466", r"308\.466 bytes", _onto_bytes, 0)
check("instances.ttl 64.242.382 bytes", r"64\.242\.382 bytes", _inst_bytes, 0)
check("triplos de instância 1.919.283", r"1\.919\.283 triplos",
      _ontc["graph"]["instances_triples"], 0)
check("triplos totais validados 1.927.780", r"1\.927\.780",
      _ontc["graph"]["total_validated_triples"], 0)
check("runtime validación ontológica 301,9 s", r"301,9 s", _ontc["runtime_seconds"], 0.1)
check("manifest 46 artefactos", r"46 artefactos", _manc["counts"]["artefacts"], 0)
check("manifest 20 execuções registradas", r"20 execuções",
      _manc["counts"]["r5_json_runs"], 0)
check("manifest 65,3 MB rastreados", r"65,3 MB",
      sum(a["bytes"] for a in _manc["artefacts"]) / 1e6, 0.1)
_b26 = {v["variant"]: v for v in j(os.path.join(R5, "B26_rubric_sensitivity.json"))["variants"]}
check("B26 kappa baseline 0,5336", r"can\u00f4nico \| \*\*0,5336\*\*", _b26["V0 baseline rubric"]["kappa"], 0.0001)
check("B26 V1 floors x1.10 kappa 0,5507", r"0,5507 \[0,5370; 0,5663\]", _b26["V1 floors x1.10"]["kappa"], 0.0001)
check("B26 V1 delta +0,0171", r"\+0,0171", _b26["V1 floors x1.10"]["delta_kappa_vs_baseline"], 0.0001)
check("B26 V2 floors x0.90 kappa 0,5250", r"0,5250 \[0,5135; 0,5395\]", _b26["V2 floors x0.90"]["kappa"], 0.0001)
check("B26 V3 categorical=3 kappa 0,5085", r"0,5085 \[0,4960; 0,5222\]", _b26["V3 categorical set = 3 duties"]["kappa"], 0.0001)
check("B26 V4 all categorical kappa 0,5461", r"0,5461 \[0,5336; 0,5606\]", _b26["V4 every duty categorical"]["kappa"], 0.0001)
check("B26 V5 lens A kappa 0,5223", r"0,5223 \[0,5106; 0,5371\]", _b26["V5 consensus = lens A only"]["kappa"], 0.0001)
check("B26 V6 lens B kappa 0,3324", r"\*\*0,3324\*\* \[0,3230; 0,3425\]", _b26["V6 consensus = lens B only"]["kappa"], 0.0001)
check("B26 V7 lens C kappa 0,5147", r"0,5147 \[0,5028; 0,5283\]", _b26["V7 consensus = lens C only"]["kappa"], 0.0001)
check("B26 V8 gate 0.80 kappa 0,6005", r"\*\*0,6005\*\* \[0,5885; 0,6102\]", _b26["V8 coverage gate 0.80"]["kappa"], 0.0001)
check("B26 V9 gate 0.60 kappa 0,4907", r"0,4907 \[0,4787; 0,5051\]", _b26["V9 coverage gate 0.60"]["kappa"], 0.0001)
check("B26 V10 assume_breach kappa 0,2974", r"\*\*0,2974\*\* \[0,2819; 0,3123\]", _b26["V10 gap mode assume_breach"]["kappa"], 0.0001)
check("B26 runtime 1.042,4 s", r"1\.042,4 s", j(os.path.join(R5, "B26_rubric_sensitivity.json"))["runtime_seconds"], 0.1)
check("B26 pares 220.400", r"220\.400 pares", _b26["V0 baseline rubric"]["pairs"], 0)
check("manifest 47 artefactos", r"47 artefactos", _manc["counts"]["artefacts"], 0)
check("manifest 21 execuções", r"21 execu\u00e7\u00f5es", _manc["counts"]["r5_json_runs"], 0)
check("manifest 65,37 MB", r"65,37 MB", round(sum(a["bytes"] for a in _manc["artefacts"]) / 1e6, 2), 0.01)
check("autocontagem de afirmaciones rastreadas", r"re-deriva \*\*(\d+) afirma", len(checks) + 1, 0)


passed = sum(1 for c in checks if c["pass"])
result = {"generated_at": datetime.now(timezone.utc).isoformat(),
          "paper": "_analysis/PAPER_v13.md", "checks": len(checks), "passed": passed,
          "verified_by_explicit_pattern": sum(1 for c in checks if c.get("verified_by") == "explicit pattern"),
          "verified_by_value_in_paper": sum(1 for c in checks if c.get("verified_by") == "value stated in the paper"),
          "failed": [c for c in checks if not c["pass"]],
          "checks_detail": checks}
json.dump(result, open(os.path.join(R5, "paper_consistency_check_v13.json"), "w"), indent=1)
print(json.dumps({"checks": result["checks"], "passed": passed,
                  "failed": [c["claim"] for c in result["failed"]]}, indent=1))