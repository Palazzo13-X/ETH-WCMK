#!/usr/bin/env python3
"""Independent verification of the ETH-WCMK corpus v5 artefacts.

Reads ONLY the artefacts written by gen_corpus_v5.py into Evaluacoes/r4, recomputes
every coverage number straight from the .jsonl rows (no reliance on the numbers the
generator printed into corpus_v5_coverage.json), writes
Evaluacoes/r4/corpus_v5_coverage_verified.json and prints the divergences.

Run:  python3 verify_corpus_v5.py
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gold_panels_v5 import cohens_kappa, RANK, ALL_RULES          # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r4")

DECISIONS = ("ABSTAIN", "PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW")


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_artefacts():
    layerA = list(read_jsonl(os.path.join(OUT, "corpus_v5_layerA.jsonl")))
    layerB = list(read_jsonl(os.path.join(OUT, "corpus_v5_layerB.jsonl")))
    personas = list(read_jsonl(os.path.join(OUT, "corpus_v5_personas.jsonl")))
    gold = list(read_jsonl(os.path.join(OUT, "corpus_v5_gold.jsonl")))
    conf = list(read_jsonl(os.path.join(OUT, "corpus_v5_confrontations.jsonl")))
    return layerA, layerB, personas, gold, conf


def main():
    layerA, layerB, personas, gold, conf = load_artefacts()
    cases = layerA + layerB

    # ---- alignment check: gold and confrontations must describe the same pairs ----
    gold_by_key = {(g["case_id"], g["persona"]): g for g in gold}
    conf_by_key = {(c["case_id"], c["persona"]): c for c in conf}
    assert len(gold_by_key) == len(gold), "duplicate (case, persona) keys in gold.jsonl"
    assert len(conf_by_key) == len(conf), "duplicate (case, persona) keys in confrontations.jsonl"
    missing_in_gold = [k for k in conf_by_key if k not in gold_by_key]
    missing_in_conf = [k for k in gold_by_key if k not in conf_by_key]
    stored_mismatch = sum(1 for k, c in conf_by_key.items()
                          if k in gold_by_key and c.get("gold_consensus") != gold_by_key[k]["consensus"])

    pairs = len(conf)
    model_seq, gold_seq = [], []
    model_dist, gold_dist = Counter(), Counter()
    aa = []
    abstain = epistemic = veto = hard = 0
    agree = within1 = 0
    spread_ge1 = unanimous = kernel_only = 0
    confusion = Counter()
    rule_fired_pairs = Counter()
    rule_changed_pairs = Counter()
    rule_fired_cases = defaultdict(set)
    by_type = defaultdict(lambda: ([], [], []))
    rank_gap = []

    for c in conf:
        g = gold_by_key.get((c["case_id"], c["persona"]))
        if g is None:
            continue
        model_seq.append(c["decision"])
        gold_seq.append(g["consensus"])
        model_dist[c["decision"]] += 1
        gold_dist[g["consensus"]] += 1
        aa.append(c["adequacy"])
        abstain += (c["decision"] == "ABSTAIN")
        epistemic += bool(c.get("epistemic_abstention"))
        veto += bool(c.get("veto"))
        hard += bool(c.get("hard_veto"))
        confusion[(c["decision"], g["consensus"])] += 1
        gap = abs(RANK[c["decision"]] - RANK[g["consensus"]])
        rank_gap.append(gap)
        agree += (gap == 0)
        within1 += (gap <= 1)
        unanimous += g["unanimous"]
        spread_ge1 += (g["spread"] >= 1)
        kernel_only += g["kernel_only"]
        by_type[c["persona_type"]][0].append(c["decision"])
        by_type[c["persona_type"]][1].append(g["consensus"])
        by_type[c["persona_type"]][2].append(c["adequacy"])
        for rid in g["rules_fired"]:
            rule_fired_pairs[rid] += 1
            rule_fired_cases[rid].add(c["case_id"])
        for rid in g["rules_applied"]:
            rule_changed_pairs[rid] += 1

    declared = [(c["decision"], gold_by_key[(c["case_id"], c["persona"])]["consensus"])
                for c in conf if c["persona_type"] == "declared"]
    kappa_overall = cohens_kappa(model_seq, gold_seq)
    kappa_declared = cohens_kappa([m for m, _ in declared], [g for _, g in declared])
    kappa_by_type = {t: round(cohens_kappa(m, g), 4) for t, (m, g, _) in by_type.items()}
    panel_kappa = {
        "AB": cohens_kappa([g["panelA"] for g in gold], [g["panelB"] for g in gold]),
        "AC": cohens_kappa([g["panelA"] for g in gold], [g["panelC"] for g in gold]),
        "BC": cohens_kappa([g["panelB"] for g in gold], [g["panelC"] for g in gold]),
    }

    distinct_vectors = {(c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                         c["horizon"], c["conflict_pattern"], tuple(c["critical_pillars"]),
                         c["U_E"], c["R_c"], c["exposure"]) for c in layerA}
    concentrated_types = {p["persona_type"] for p in personas if p["kind"].startswith("concentrated")}
    deficit_pillars = {next(iter(p["factors"]))[0] for p in personas
                       if p["kind"].startswith("concentrated") and p["factors"]}
    rules_on_cases = {rid: len(rule_fired_cases[rid]) for rid, *_ in ALL_RULES}

    verified = {
        "verified_from": ["corpus_v5_layerA.jsonl", "corpus_v5_layerB.jsonl",
                          "corpus_v5_personas.jsonl", "corpus_v5_gold.jsonl",
                          "corpus_v5_confrontations.jsonl"],
        "seed_note": "all numbers recomputed from the artefacts, not from the generator's in-memory counters",
        "cases": {"layerA": len(layerA), "layerB": len(layerB), "total": len(cases)},
        "personas": {"instances": len(personas),
                     "concentrated_deficit_instances": sum(1 for p in personas
                                                           if p["kind"].startswith("concentrated")),
                     "concentrated_deficit_types": len(concentrated_types),
                     "pillars_with_concentrated_deficit_type": sorted(deficit_pillars)},
        "pairs_adjudicated": pairs,
        "pair_alignment": {"keys_in_gold": len(gold_by_key), "keys_in_confrontations": len(conf_by_key),
                           "pairs_missing_in_gold": len(missing_in_gold),
                           "pairs_missing_in_confrontations": len(missing_in_conf),
                           "stored_gold_consensus_mismatches": stored_mismatch},
        "cases_by_layer": dict(Counter(c["layer"] for c in cases)),
        "cases_by_domain": dict(Counter(c["domain"] for c in cases)),
        "cases_by_layer_domain": dict(Counter(f"{c['layer']}/{c['domain']}" for c in cases)),
        "cases_by_severity": dict(Counter(c["severity"] for c in cases)),
        "cases_by_layer_severity": dict(Counter(f"{c['layer']}/{c['severity']}" for c in cases)),
        "cases_by_horizon": dict(Counter(c["horizon"] for c in cases)),
        "cases_by_irreversibility": dict(Counter(c["irreversibility"] for c in cases)),
        "cases_by_prudential": dict(Counter(c["prudential"] for c in cases)),
        "cases_by_conflict_pattern": dict(Counter(c["conflict_pattern"] for c in cases)),
        "distinct_layerA_parameter_vectors": len(distinct_vectors),
        "layerA_duplicate_vectors": len(layerA) - len(distinct_vectors),
        "ambiguity": {"norm_conflict_unresolved": sum(1 for c in cases if c["norm_conflict"] != "none"),
                      "evidence_conflict": sum(1 for c in cases if c["evidence_conflict"])},
        "template_diversity": {"consequence_types": len({c["consequence"] for c in layerB}),
                               "vulnerability_types": len({c["vulnerability"] for c in layerB}),
                               "norm_sets": len({x for c in layerB for x in c["norm_sets"]}),
                               "distinct_instrument_strings": len({x for c in cases for x in c["norms"]})},
        "adequacy": {"n": len(aa), "mean": round(float(np.mean(aa)), 4),
                     "min": round(min(aa), 4), "max": round(max(aa), 4),
                     "p50": round(float(np.median(aa)), 4),
                     "share_ge_0.999": round(sum(1 for x in aa if x >= 0.999) / len(aa), 6),
                     "share_ge_0.99": round(sum(1 for x in aa if x >= 0.99) / len(aa), 6)},
        "decision_distribution": dict(model_dist),
        "abstain": {"total": abstain, "epistemic_E29": epistemic,
                    "coverage_gate": abstain - epistemic,
                    "share": round(abstain / pairs, 6)},
        "veto_rate": round(veto / pairs, 4), "hard_veto_rate": round(hard / pairs, 4),
        "gold": {"consensus_distribution": dict(gold_dist),
                 "unanimous_share": round(unanimous / pairs, 4),
                 "contested_share_spread_ge_1": round(spread_ge1 / pairs, 4),
                 "kernel_only_count": kernel_only,
                 "kernel_only_share": round(kernel_only / pairs, 6),
                 "kernel_only_gate_max_0.40": (kernel_only / pairs) <= 0.40,
                 "panel_kappa": {k: round(v, 4) for k, v in panel_kappa.items()},
                 "rules": [{"id": rid, "fired_pairs": rule_fired_pairs[rid],
                            "fired_distinct_cases": rules_on_cases[rid],
                            "changed_panel_verdict_pairs": rule_changed_pairs[rid]}
                           for rid, *_ in ALL_RULES],
                 "rules_firing_on_ge_50_cases": sum(1 for rid in rules_on_cases
                                                    if rules_on_cases[rid] >= 50),
                 "rules_total": len(ALL_RULES)},
        "model_vs_gold": {"kappa_overall": round(kappa_overall, 4),
                          "kappa_declared_agent": round(kappa_declared, 4),
                          "exact_match_rate": round(agree / pairs, 4),
                          "within_one_step_rate": round(within1 / pairs, 4),
                          "mean_rank_gap": round(float(np.mean(rank_gap)), 4),
                          "model_stricter_than_gold_rate": round(sum(n for (m, g), n in confusion.items()
                                                    if RANK[m] < RANK[g]) / pairs, 4),
                          "model_looser_than_gold_rate": round(sum(n for (m, g), n in confusion.items()
                                                   if RANK[m] > RANK[g]) / pairs, 4),
                          "spearman_Aa_vs_gold_rank": round(float(np.corrcoef(
                              np.argsort(aa), np.argsort([RANK[g] for g in gold_seq]))[0, 1]), 4),
                          "confusion": {f"{m} -> {g}": n for (m, g), n in
                                        sorted(confusion.items(), key=lambda x: -x[1])}},
        "kappa_by_persona_type": kappa_by_type,
        "decision_distribution_by_persona_type": {t: dict(Counter(m)) for t, (m, _, _) in by_type.items()},
        "audit_sample": {"rows": 0},
        "gates": {
            "a_no_duplicate_layerA_parameter_vectors": len(distinct_vectors) == len(layerA),
            "b_share_adequacy_ge_0.999_below_0.05": (sum(1 for x in aa if x >= 0.999) / len(aa)) < 0.05,
            "c_concentrated_deficit_persona_type_per_pillar": (
                len(deficit_pillars) == 4 and len(concentrated_types) >= 15),
            "d_at_least_15_rules_firing_on_50_plus_cases": sum(1 for rid in rules_on_cases
                                                               if rules_on_cases[rid] >= 50) >= 15,
            "e_abstain_fires_on_some_cases": abstain > 0,
            "f_all_artefacts_written_to_r4": all(os.path.exists(os.path.join(OUT, f)) for f in (
                "corpus_v5_layerA.jsonl", "corpus_v5_layerB.jsonl", "corpus_v5_personas.jsonl",
                "corpus_v5_gold.jsonl", "corpus_v5_confrontations.jsonl",
                "corpus_v5_coverage.json", "corpus_v5_audit_sample.csv")),
            "gold_kernel_only_share_below_0.40": (kernel_only / pairs) <= 0.40,
            "severity_low_used_in_layerA": any(c["severity"] == "low" for c in layerA),
            "all_13_domains_covered": len({c["domain"] for c in cases}) == 13,
        },
    }

    # ---- audit sample verification ----
    with open(os.path.join(OUT, "corpus_v5_audit_sample.csv"), newline="") as fh:
        rows = list(csv.DictReader(fh))
    verified["audit_sample"] = {
        "rows": len(rows),
        "decision_composition": dict(Counter(r["model_decision_declared_agent"] for r in rows)),
        "domain_composition": dict(Counter(r["domain"] for r in rows)),
        "empty_rater_cells": sum(1 for r in rows for k in ("rater_1_verdict", "rater_2_verdict",
                                                           "rater_3_verdict") if not r[k]),
        "status_marked_unadjudicated": all("UNADJUDICATED" in r["adjudication_status"] for r in rows),
    }

    # ---- divergence report against corpus_v5_coverage.json ----
    with open(os.path.join(OUT, "corpus_v5_coverage.json")) as fh:
        original = json.load(fh)
    divergences = []
    comparable = [
        ("pairs_adjudicated", verified["pairs_adjudicated"], original.get("pairs_adjudicated")),
        ("cases.total", verified["cases"]["total"], original.get("cases", {}).get("total")),
        ("personas.instances", verified["personas"]["instances"], original.get("personas", {}).get("instances")),
        ("distinct_layerA_parameter_vectors", verified["distinct_layerA_parameter_vectors"],
         original.get("distinct_layerA_parameter_vectors")),
        ("decision_distribution", verified["decision_distribution"], original.get("decision_distribution")),
        ("gold.consensus_distribution", verified["gold"]["consensus_distribution"],
         original.get("gold", {}).get("consensus_distribution")),
        ("adequacy.share_ge_0.999", verified["adequacy"]["share_ge_0.999"],
         original.get("adequacy", {}).get("share_ge_0.999")),
        ("abstain.total", verified["abstain"]["total"], original.get("abstain", {}).get("total")),
        ("veto_rate", verified["veto_rate"], original.get("veto_rate")),
        ("hard_veto_rate", verified["hard_veto_rate"], original.get("hard_veto_rate")),
        ("kappa_overall", verified["model_vs_gold"]["kappa_overall"],
         original.get("kappa_model_vs_gold", {}).get("overall")),
        ("gold.kernel_only_share", verified["gold"]["kernel_only_share"],
         original.get("gold", {}).get("kernel_only_share")),
        ("exact_match_rate", verified["model_vs_gold"]["exact_match_rate"],
         original.get("model_vs_gold", {}).get("exact_match_rate")),
    ]
    for name, v, o in comparable:
        if isinstance(v, dict) and isinstance(o, dict):
            same = all(v.get(k) == o.get(k) for k in set(v) | set(o))
            if not same:
                divergences.append({"metric": name, "verified": v, "coverage_json": o})
        elif v != o:
            divergences.append({"metric": name, "verified": v, "coverage_json": o})

    verified["divergences_vs_coverage_json"] = divergences
    verified["gates_recomputed_from_verified_numbers"] = verified["gates"]

    with open(os.path.join(OUT, "corpus_v5_coverage_verified.json"), "w") as fh:
        json.dump(verified, fh, indent=2)

    print("=" * 78)
    print("ETH-WCMK corpus v5 - independent verification (recomputed from the .jsonl files)")
    print("=" * 78)
    print(f"pairs confronted: {pairs}   pairs in gold: {len(gold_by_key)}   "
          f"alignment mismatches: {stored_mismatch}")
    print(f"cases: A={len(layerA)} B={len(layerB)} total={len(cases)}; "
          f"distinct layerA vectors={len(distinct_vectors)} (dup={len(layerA)-len(distinct_vectors)})")
    print(f"model decisions: {dict(model_dist)}")
    print(f"gold consensus:  {dict(gold_dist)}")
    print(f"Aa: mean={np.mean(aa):.4f} median={np.median(aa):.4f} min={min(aa):.4f} "
          f"max={max(aa):.4f} share>=0.999={sum(1 for x in aa if x >= 0.999)/len(aa):.6f}")
    print(f"ABSTAIN: {abstain} ({abstain/pairs:.4f}) all epistemic={epistemic}")
    print(f"kappa(model,gold) overall={kappa_overall:.4f} declared-agent={kappa_declared:.4f} "
          f"agreement={agree/pairs:.4f} within-1-step={within1/pairs:.4f}")
    print(f"kernel-only share={kernel_only/pairs:.4f}  panel kappa AB/AC/BC = "
          f"{panel_kappa['AB']:.3f}/{panel_kappa['AC']:.3f}/{panel_kappa['BC']:.3f}")
    print(f"rules firing on >=50 distinct cases: {sum(1 for r in rules_on_cases if rules_on_cases[r] >= 50)}"
          f" of {len(ALL_RULES)}")
    print("\nGates (recomputed from the artefacts):")
    for k, v in verified["gates"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("\nDivergences vs corpus_v5_coverage.json:")
    if not divergences:
        print("  none - coverage.json matches the artefacts")
    for d in divergences:
        print(f"  {d['metric']}: verified={d['verified']} | coverage.json={d['coverage_json']}")
    print(f"\nwrote {os.path.join(OUT, 'corpus_v5_coverage_verified.json')}")
    return verified


if __name__ == "__main__":
    main()
