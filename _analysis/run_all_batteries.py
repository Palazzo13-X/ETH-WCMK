"""Single entry point for the ETH-WCMK evaluation pipeline (gate G9').

Every number quoted in the paper must come from a file produced by this runner or by a
script it calls. The runner:

  1. runs the formal-invariant suite (B1 invariants),
  2. regenerates the corpus (optional, --corpus),
  3. runs every battery in order, writing into Evaluacoes/<round>/,
  4. writes manifest_<round>.json with SHA-256 of every produced artefact and the
     git commit / machine fingerprint, so a reviewer can verify that the paper's
     tables and the artefacts on disk are the same objects.

Frozen rounds are never overwritten: r2 and r3 are read-only by construction.

Usage:
    python3 _analysis/run_all_batteries.py --round r4 [--corpus] [--skip B7]
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE = os.path.join(ROOT, "_analysis", "formal_core")
ANALYSIS = os.path.join(ROOT, "_analysis", "analysis")
CORPUS = os.path.join(ROOT, "_analysis", "corpus")
ONTO = os.path.join(ROOT, "_analysis", "ontology")
FROZEN = {"r2", "r3"}

BATTERIES = [
    ("B1_invariants", [sys.executable, "-m", "pytest",
                       os.path.join(CORE, "tests"), "-q"], None),
    ("B0_delta", [sys.executable, os.path.join(ANALYSIS, "delta_v12_r4.py")],
     "delta_v12.json"),
    ("B2_ontology_validation", [sys.executable, os.path.join(ONTO, "validate_ontology_v4.py")],
     "ontology_v4_validation.json"),
    ("B3_consensus_kappa", [sys.executable, os.path.join(ANALYSIS, "kappa_by_consensus.py")],
     "kappa_by_consensus.json"),
    ("B4_grounding_sweep", [sys.executable, os.path.join(ANALYSIS, "fact_grounding_sweep.py")],
     "fact_grounding_sweep.json"),
    ("B5_ladder_fit", [sys.executable, os.path.join(ANALYSIS, "fit_ladder_v12.py")],
     "ladder_calibration_v12.json"),
    ("B6_llm_profile", [sys.executable, os.path.join(ANALYSIS, "llm_profile_v12.py"),
                        "--cases", "40"], "B6_llm_profile.json"),
    ("B7_baselines", [sys.executable, os.path.join(ANALYSIS, "b7_baselines_v12.py")],
     "B7_baselines_v12.json"),
    ("B8_probes", [sys.executable, os.path.join(CORE, "run_battery_B8_v12.py")],
     "B8_probes.json"),
    ("B9_noise_B12_temporal", [sys.executable, os.path.join(ANALYSIS, "robustness_v12.py")],
     "B9_noise_v12.json"),
    ("B10_sobol_morris", [sys.executable, os.path.join(ANALYSIS, "sobol_v12_b10.py")],
     "B10_sobol.json"),
    ("B11_shared_beta_ablation", [sys.executable, os.path.join(ANALYSIS, "b11_shared_beta.py")],
     "B11_shared_beta.json"),
    ("B11b_procedural_facet_ablation",
     [sys.executable, os.path.join(ANALYSIS, "procedural_facet_ablation.py")],
     "procedural_facet_ablation.json"),
    ("B13_transfer", [sys.executable, os.path.join(ANALYSIS, "b13_transfer_v12.py")],
     "B13_transfer_v12.json"),
    ("B14_case_profile_risk", [sys.executable, os.path.join(ANALYSIS, "b14_case_profile_risk.py")],
     "B14_case_profile_risk.json"),
    ("B15_delegation_chains", [sys.executable, os.path.join(ANALYSIS, "b15_delegation_chains.py")],
     "B15_delegation_chains.json"),
    ("B16_structural_ablation", [sys.executable, os.path.join(ANALYSIS, "b16_structural_ablation.py")],
     "B16_structural_ablation.json"),
    ("B17_coverage_abstain", [sys.executable, os.path.join(ANALYSIS, "b17_coverage_abstain.py")],
     "B17_coverage_abstain.json"),
    ("B18_paper_consistency", [sys.executable, os.path.join(ANALYSIS, "paper_artifact_consistency.py")],
     "paper_consistency_check.json"),
    ("B19_full_corpus_mirror", [sys.executable, os.path.join(ANALYSIS, "mirror_full_corpus.py")],
     "mirror_full_corpus.json"),
    ("B2b_full_ontology_sweep", [sys.executable, os.path.join(ONTO, "validate_ontology_full.py")],
     "ontology_full_validation.json"),
]



# --- Rodada 5 (v13): baterias novas, executadas na ordem que fecha os gates ---
BATTERIES_V13 = [
    ("B1_invariants_v13", [sys.executable, "-m", "pytest", os.path.join(CORE, "tests"), "-q"], None),
    ("corpus_v7", [sys.executable, os.path.join(CORPUS, "gen_corpus_v5.py")], "corpus_v7_coverage.json"),
    ("B8_probes_v13", [sys.executable, os.path.join(CORE, "run_battery_B8_v13.py")],
     "B8_probes_reverified_v13.json"),
    ("B20_variant_eval_full", [sys.executable, os.path.join(ANALYSIS, "b20_variant_eval.py"),
                               "--cases", "1080",
                               "--out", os.path.join(ROOT, "Evaluacoes", "r5", "B20_variant_eval_full_corpus.json")],
     "B20_variant_eval_full_corpus.json"),
    ("B20_crit_mild_cap3", [sys.executable, os.path.join(ANALYSIS, "b20_variant_eval.py"),
                            "--cases", "859",
                            "--crit", os.path.join(ROOT, "_analysis", "facets", "criticality_mild_cap3_v13.json"),
                            "--out", os.path.join(ROOT, "Evaluacoes", "r5", "B20_crit_mild_cap3_full_corpus.json")],
     "B20_crit_mild_cap3_full_corpus.json"),
    ("B20_crit_targeted", [sys.executable, os.path.join(ANALYSIS, "b20_variant_eval.py"),
                           "--cases", "859",
                           "--crit", os.path.join(ROOT, "_analysis", "facets", "criticality_targeted_TB_TS_IM_v13.json"),
                           "--out", os.path.join(ROOT, "Evaluacoes", "r5", "B20_crit_targeted_full_corpus.json")],
     "B20_crit_targeted_full_corpus.json"),
    ("B21_guard_beta_ablation", [sys.executable, os.path.join(ANALYSIS, "b20_variant_eval.py"),
                                 "--cases", "400", "--guards-ablation", "--beta-primary",
                                 "--out", os.path.join(ROOT, "Evaluacoes", "r5", "B21_ablation.json")],
     "B21_ablation.json"),
    ("B22_fact_contradiction", [sys.executable, os.path.join(ANALYSIS, "b22_fact_contradiction.py")],
     "B22_fact_contradiction.json"),
    ("B23_sobol_morris_v13", [sys.executable, os.path.join(ANALYSIS, "sobol_v13_b23.py")],
     "B23_sobol_v13.json"),
    ("B25_full_corpus_mirror", [sys.executable, os.path.join(ANALYSIS, "mirror_full_corpus_v13.py")],
     "mirror_full_corpus_v13.json"),
    ("ontology_v4_2_gen", [sys.executable, os.path.join(ONTO, "gen_ontology_v6.py")], None),
    ("G14_ontology_validation", [sys.executable, os.path.join(ONTO, "validate_ontology_v6.py")],
     "ontology_v4_2_validation.json"),
    ("B26_rubric_sensitivity", [sys.executable, os.path.join(ANALYSIS, "b26_rubric_sensitivity.py")],
     "B26_rubric_sensitivity.json"),
    ("kappa_by_stratum", [sys.executable, os.path.join(ANALYSIS, "kappa_by_stratum.py")],
     "kappa_by_stratum_v13.json"),
    ("adjudication_packet", [sys.executable, os.path.join(ANALYSIS, "adjudication_packet.py")],
     "adjudication_packet_blind.csv"),
    ("B24_llm_anchor", [sys.executable, os.path.join(ANALYSIS, "llm_anchor_v13.py"), "--cases", "24"],
     "B24_llm_anchor.json"),
    ("G18_paper_artifact_traceability",
     [sys.executable, os.path.join(ANALYSIS, "paper_artifact_consistency_v13.py")],
     "paper_consistency_check_v13.json"),
    ("manifest_r5", [sys.executable, os.path.join(ANALYSIS, "make_manifest_r5.py")], "manifest_r5.json"),
]
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_rev():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip() or "no-git"
    except Exception:
        return "no-git"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="r4")
    ap.add_argument("--corpus", action="store_true", help="regenerate the corpus first")
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--manifest-only", action="store_true",
                        help="only hash the artefacts already in the round directory")
    args = ap.parse_args()

    if args.round in FROZEN:
        sys.exit(f"round {args.round} is frozen; write to a new round directory")
    out = os.path.join(ROOT, "Evaluacoes", args.round)
    os.makedirs(out, exist_ok=True)
    if args.list:
        table = BATTERIES_V13 if args.round == "r5" else BATTERIES
        for name, cmd, artefact in table:
            print(f"{name:<32} -> {artefact}   [{' '.join(cmd)}]")
        return

    env = dict(os.environ, ETHWCMK_ROUND=args.round)
    log = []
    if args.corpus:
        log.append(run("corpus", [sys.executable, os.path.join(CORPUS, "gen_corpus_v5.py")], env))
    if not args.manifest_only:
        for name, cmd, _ in BATTERIES:
            if name in args.skip:
                continue
            log.append(run(name, cmd, env))

    # Accumulate the execution log across invocations of the same round, so a reviewer
    # sees one complete history without forcing a re-run of the expensive batteries.
    mf_path = os.path.join(out, f"manifest_{args.round}.json")
    prev_runs = []
    if os.path.exists(mf_path):
        try:
            prev_runs = json.load(open(mf_path)).get("runs", [])
        except Exception:
            prev_runs = []
    by_name = {r["name"]: r for r in prev_runs}
    for r in log:
        by_name[r["name"]] = r
    merged = sorted(by_name.values(), key=lambda r: r.get("started_at") or "")
    artefact_of = {name: (art or "") for name, _, art in BATTERIES}
    for r in merged:
        if r.get("duration_s") is None:
            art = os.path.join(out, artefact_of.get(r["name"], ""))
            try:
                d = json.load(open(art))
                for key in ("runtime_seconds", "duration_seconds", "elapsed_seconds"):
                    if isinstance(d.get(key), (int, float)):
                        r["duration_s"] = round(float(d[key]), 2)
                        r["duration_source"] = "artefato"
                        break
            except Exception:
                pass
    if prev_runs and log:
        print(f"merging {len(prev_runs)} previous run records with {len(log)} new ones")

    artefacts = {}
    for fn in sorted(os.listdir(out)):
        artefacts[fn] = {"sha256": sha256(os.path.join(out, fn)),
                        "bytes": os.path.getsize(os.path.join(out, fn))}
    manifest = {
        "round": args.round,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_rev": git_rev(),
        "python": platform.python_version(),
        "machine": platform.platform(),
        "canon": "33 facets (v12)",
        "corpus": "corpus_v6 (1,520 cases, 120 personas, 183,920 confrontations)",
        "calibration_convention": ("ground truth and corpus verdicts use the frozen r3 ladder; "
                                   "threshold-fitting batteries (B5, B7, B13) use "
                                   "ladder_calibration_v12.json and are reported separately"),
        "core_files_sha256": {
            os.path.relpath(os.path.join(CORE, f), ROOT): sha256(os.path.join(CORE, f))
            for f in ("core.py", "facet_registry.py", "geometry.py", "fact_grounding.py",
                      "run_battery_B8_v12.py", "tests/test_invariants.py",
                      "tests/test_geometry.py", "tests/test_fact_grounding.py")
            if os.path.exists(os.path.join(CORE, f))
        },
        "runs": merged,
        "n_invocations_logged": len(merged),
        "source_inventory": source_inventory(),
        "artefacts": artefacts,
    }
    manifest_path = os.path.join(out, f"manifest_{args.round}.json")
    if os.path.exists(manifest_path):
        try:
            previous = {r["name"]: r for r in json.load(open(manifest_path)).get("runs", [])}
        except Exception:
            previous = {}
        for r in log:
            previous[r["name"]] = r
        merged = list(previous.values())
        log = merged
    with open(os.path.join(out, f"manifest_{args.round}.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(json.dumps({k: v["sha256"][:16] for k, v in artefacts.items()}, indent=2))
    failed = [r for r in log if r.get("returncode") != 0]
    if failed:
        print("FAILED RUNS:", [r["name"] for r in failed])
        sys.exit(1)


def source_inventory():
    """Hash everything that *produces* a number: core, registry, generators, shapes,
    fixtures and the equation files. A reviewer can recompute any artefact from these."""
    groups = {
        "formal_core": sorted(os.listdir(CORE)),
        "ontology_generators": [f for f in sorted(os.listdir(ONTO)) if f.endswith(".py")],
        "ontology_artefacts": ["01_core.ttl", "02_facets.ttl", "03_deontic.ttl", "04_agency.ttl",
                               "05_dynamics.ttl", "06_calibration.ttl", "07_grounding.ttl",
                               "shapes/ontology_shapes.ttl", "shapes/ontology_shapes_v6.ttl",
                               "fixtures/invalid_examples.ttl", "fixtures/invalid_examples_v6.ttl",
                               "generation_report.json"],
        "equations": sorted(os.listdir(os.path.join(ROOT, "paper", "figures", "mathml"))),
        "equation_sources": ["equations.py", "build_omml.py", "render_equation.py", "regen_equations.py"],
    }
    base = {"formal_core": CORE, "ontology_generators": ONTO, "ontology_artefacts":
            os.path.join(ROOT, "Ontologias", "ontology_v4"),
            "equations": os.path.join(ROOT, "paper", "figures", "mathml"),
            "equation_sources": os.path.join(ROOT, "_analysis", "paper")}
    inv = {}
    for group, names in groups.items():
        inv[group] = {}
        for n in names:
            f = os.path.join(base[group], n)
            if os.path.isfile(f):
                inv[group][n] = {"sha256": sha256(f), "bytes": os.path.getsize(f)}
    return inv


def run(name, cmd, env):
    t0 = datetime.now(timezone.utc)
    print(f"\n=== {name} ===")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    print(p.stdout[-3000:])
    if p.returncode:
        print("STDERR:", p.stderr[-1500:])
    return {"name": name, "cmd": cmd, "returncode": p.returncode,
            "started_at": t0.isoformat(),
            "duration_s": round((datetime.now(timezone.utc) - t0).total_seconds(), 2),
            "output_tail": p.stdout[-400:]}


if __name__ == "__main__":
    main()
