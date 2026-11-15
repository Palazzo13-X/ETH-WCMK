"""Paper <-> artifact consistency check.

Rule of the project: "nenhum número do paper vem de texto". This script reads the
numbers quoted in `_analysis/PAPER_v12.md` and re-derives each one from the artifact
that is supposed to back it, then reports any divergence. It is not a test of the
model; it is a test of the citation chain.

Output: Evaluacoes/r4/paper_consistency_check.json
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
ONTO = os.path.join(ROOT, "Ontologias", "ontology_v4")

PAPER = open(os.path.join(ROOT, "_analysis", "PAPER_v12.md")).read()


def j(path):
    return json.load(open(path))


def count_triples(path):
    from rdflib import Graph
    g = Graph()
    g.parse(path, format="turtle")
    return len(g)


checks = []


def check(name, quoted, derived, tolerance=0.0):
    ok = abs(float(quoted) - float(derived)) <= tolerance
    checks.append({"claim": name, "paper_value": quoted, "artifact_value": derived,
                   "match": ok, "delta": round(float(derived) - float(quoted), 6)})


full = j(os.path.join(R4, "ontology_full_validation.json"))
slice_v = j(os.path.join(R4, "ontology_v4_validation.json"))
gen = j(os.path.join(ONTO, "generation_report.json"))
cov = j(os.path.join(R4, "corpus_v6_coverage.json"))
b14 = j(os.path.join(R4, "B14_case_profile_risk.json"))
b15 = j(os.path.join(R4, "B15_delegation_chains.json"))
b16 = j(os.path.join(R4, "B16_structural_ablation.json"))
b8 = j(os.path.join(R4, "B8_probes.json"))
b13 = j(os.path.join(R4, "B13_transfer_v12.json"))
b17 = j(os.path.join(R4, "B17_coverage_abstain.json"))
kc = j(os.path.join(R4, "kappa_by_consensus.json"))
guard = j(os.path.join(R4, "guard_experiment.json"))
delta = j(os.path.join(R4, "delta_v12.json"))
man = j(os.path.join(R4, "manifest_r4.json"))
stats = j(os.path.join(R4, "facet_review_stats_v12.json"))

check("schema triples in ontology modules", 8394,
      slice_v["graph"]["module_triples_total"])
check("instance triples", 1888317, gen["instances_triples"])
check("triples validated over the full corpus", 2014563, full["graph"]["triples_validated"])
check("SHACL violations on the full corpus", 0, full["shacl_v4"]["violations"] + full["shacl_v6"]["violations"])
check("invalid fixtures detected", 76, full.get("invalid_fixtures", slice_v["invalid_fixtures"])["detected"]
      if "invalid_fixtures" in full else slice_v["invalid_fixtures"]["detected"])
check("mirror max abs difference", 1.63e-12,
      slice_v["mirror"]["global_max_abs_difference"], tolerance=1e-13)
check("lattice slots", 15, slice_v["face_lattice"]["total_slots"])
check("registry divergences", 0, len(slice_v["registry"]["mismatches"]))
check("cases", 1520, cov["cases"]["total"])
check("confrontations", 183920, cov["pairs_adjudicated"])
check("ABSTAIN (E29) in corpus", 14703, gen["decision_distribution"]["ABSTAIN"])
check("norm conflicts", 88, gen["norm_conflicts"])
check("chain links retaining critical duty", 268,
      full["findings"]["chain links where the case's critical duty is retained at the delegating layer (E28 retention, reported not penalised)"])
check("B14 case variance share", 0.9807, b14["variance_decomposition"]["case"])
check("B14 profile variance share", 0.0080, b14["variance_decomposition"]["profile"])
check("B14 interaction share", 0.0113, b14["variance_decomposition"]["interaction_case_x_profile"])
check("B14 mixed verdict cases", 235, b14["verdict_agreement_inside_case"]["cases_with_mixed_verdicts"])
check("B15 facets requiring accountable layer", 32,
      b15["capability_definition_facet_level"]["facets_only_the_accountable_layer_can_carry"])
check("B15 chain-worst verdict changes", 127,
      b15["chain_with_worst_delegate"]["verdict_changes_vs_declared"])
check("B16 full kappa", 0.4681, b16["variants"]["full"]["kappa"])
check("B16 no structure kappa", 0.4688, b16["variants"]["no_structure"]["kappa"])
check("B16 mean Aa full", 0.2886, b16["variants"]["full"]["mean_adequacy_low"])
check("B16 mean Aa no structure", 0.3827, b16["variants"]["no_structure"]["mean_adequacy_low"])
check("B8 probes", 2064, b8["summary"]["total_probes"])
check("B8 assertions", 7815, b8["summary"]["assertions_total"])
check("unanimous stratum kappa", 0.6955, kc["strata"]["unanimous"]["kappa_5class"])
check("unanimous stratum size", 87134, kc["strata"]["unanimous"]["n"])
check("holdout kappa fitted", 0.4834, b13["kappa_fitted_holdout"])
check("guards all K kappa", 0.1234, guard["variants"]["guards_all_K"]["kappa"])
check("delta flips", 33800, delta["total_flips"])
check("identical beta pairs", 8, stats["identical_beta_pairs"])
check("chebyshev beta pairs", 26, stats["chebyshev_beta_pairs_lt_0_12"])
check("lambda vs beta mass deviation", 0.1348, stats["lambda_vs_beta_mass_max_deviation"])
check("B17 probes", 13680, b17["probes"])
check("B17 abstain fires at 0.70", 1520, b17["per_level"]["0.7"]["abstain_count"])
check("B17 anti-gaming mean Aa change", 0.3419, b17["anti_gaming_pair"]["mean_adequacy_change"])
check("manifest artefacts", 74, len(man["artefacts"]))
check("manifest runs", 20, len(man["runs"]))
mirror = json.load(open(os.path.join(ROOT, "Evaluacoes", "r4", "mirror_full_corpus.json")))
check("full-corpus mirror covers 183,920 confrontations", 183920, mirror["confrontations"])
check("full-corpus mirror max difference is 0", 0.0, mirror["global_max_abs_difference"])
check("full-corpus mirror verdict divergences", 0, mirror["verdict_divergences"])
check("paper states the full-corpus mirror result", 1, 1 if "183.920 confrontações do corpus" in PAPER else 0)
mirror_run = next((r for r in man["runs"] if r["name"] == "B19_full_corpus_mirror"), None)
check("mirror runtime quoted in the paper equals the manifest record", 63.42, float(mirror_run["duration_s"]))
valid = subprocess.run(["git", "cat-file", "-e", man["git_rev"]], capture_output=True, cwd=ROOT).returncode
check("manifest git_rev resolves to a real commit", 0, valid)

# Cross-check the literal strings appear in the paper text.
strings = ["8.394", "1.888.317", "2.014.563", "76/76", "1,63", "15 slots", "14.703", "88 conflitos",
           "98,07%", "1,13%", "235", "127", "0,4681", "0,4688", "0,3827", "2.064", "7.815",
           "0,6955", "87.134", "0,4834", "0,1234", "33.800", "26 pares", "8 pares", "0,1348",
           "13.680", "1.345", "74 artefatos", "20 execuções", "235 de 1.520"]
present = {s: (s in PAPER) for s in strings}

out = {
    "checks": checks,
    "divergences": [c for c in checks if not c["match"]],
    "n_checks": len(checks),
    "n_divergences": sum(1 for c in checks if not c["match"]),
    "literal_strings_in_paper": {k: v for k, v in present.items() if not v},
    "pass": not any(not c["match"] for c in checks),
}
with open(os.path.join(R4, "paper_consistency_check.json"), "w") as fh:
    json.dump(out, fh, indent=2)

print(f"{out['n_checks']} checks, {out['n_divergences']} divergences")
for c in out["divergences"]:
    print("  DIVERGENCE:", c)
if out["literal_strings_in_paper"]:
    print("  literal strings missing from paper:", out["literal_strings_in_paper"])
