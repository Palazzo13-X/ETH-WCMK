#!/usr/bin/env python3
"""Where the model and the normative panels disagree, and why.

Reads the corpus v5 artefacts in Evaluacoes/r4 and decomposes the two dominant
divergences:

  (i)  model REVIEW_REQUIRED  vs  panel consensus PROHIBIT
  (ii) model PROHIBIT        vs  panel consensus REVIEW_REQUIRED

For every divergent pair the script records the route the decision ladder took
(stakes gate / bar / categorical margin / risk ratio / veto) and the route the
panels took (kernel rule K1/K2 vs escalation by rules A/B/C), and separates
panel prohibitions that rest on *procedural facts the facet vector does not
measure* (consent, notice, appeal channel, remedy period, audit, human review,
sunset, worker voice, exit) from those that rest on a duty level below a floor.

Writes Evaluacoes/r4/corpus_v5_confusion_analysis.json.
"""

import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gold_panels_v5 import ALL_RULES, RANK, LABELS, _half_round      # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r4")

# --- calibration actually used by the run (read from corpus_v5_coverage.json) ---
CAL = json.load(open(os.path.join(OUT, "corpus_v5_coverage.json")))["calibration"]
PROHIBIT_STAKES_MIN = CAL["prohibit_stakes_min"]
PROHIBIT_MARGIN = 0.25          # cal.prohibit_margin, r3 fitted ladder
RATIO_PROHIBIT = 0.70
RATIO_REVIEW = 0.45
VETO_SLACK = 0.10

# Rules whose condition is a *declared procedural fact* rather than a duty level or
# the model's own risk arithmetic. These are the facts no facet in the ontology
# directly measures.
FACT_UP = {"A2", "A3", "A4", "A5", "A6", "A7", "B2", "B6",
           "C1", "C2", "C4", "C5", "C7", "C8", "C9", "C10"}      # escalate on a procedural gap
FACT_DOWN = {"B5"}                                               # de-escalate on a sunset clause
FACT_ONLY = FACT_UP | FACT_DOWN
# Counterfactual panel: drop only the positive procedural rules. If the prohibition
# disappears, it rested on facts the facet vector does not measure.
CF_IDS = set(r[0] for r in ALL_RULES) - FACT_UP
PANEL_OF = {rid: rid[0] for rid, *_ in ALL_RULES}
WEIGHT = {r[0]: r[4] for r in ALL_RULES}
KERNEL_RANK = {"K0": 0, "K1": 1, "K2": 1, "K3": 2, "K4": 3, "K5": 4}


def panel_rank(kernel_rank, fired, breached, allowed_ids):
    """Reproduce a panel verdict from the kernel rank and the rules that fired,
    restricted to `allowed_ids` (used for the counterfactual 'no procedural facts')."""
    net = sum(WEIGHT[r] for r in fired if r in allowed_ids)
    if net > 1.0 and not breached:
        net = 1.0
    elif net < -1.0 and not breached:
        net = -1.0
    return max(1, min(4, kernel_rank - _half_round(net)))


def consensus(ranks):
    lo, mid, hi = sorted(ranks)
    return lo if (hi - lo) >= 2 else mid


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def main():
    gold = list(read_jsonl(os.path.join(OUT, "corpus_v5_gold.jsonl")))
    conf = list(read_jsonl(os.path.join(OUT, "corpus_v5_confrontations.jsonl")))
    gold_by_key = {(g["case_id"], g["persona"]): g for g in gold}
    cases = {c["case_id"]: c for c in list(read_jsonl(os.path.join(OUT, "corpus_v5_layerA.jsonl")))
                        + list(read_jsonl(os.path.join(OUT, "corpus_v5_layerB.jsonl")))}

    ALL_IDS = set(WEIGHT)
    LEVEL_IDS = ALL_IDS - FACT_ONLY

    buckets = Counter()
    stats = defaultdict(list)
    rule_divergent = Counter()
    fact_rule_divergent = Counter()
    divergent_by_persona = Counter()
    divergent_by_domain = Counter()
    divergent_by_layer = Counter()
    model_route = Counter()
    gold_route = Counter()
    examples = []
    n_pairs = 0
    agreement_rank = []

    for c in conf:
        g = gold_by_key[(c["case_id"], c["persona"])]
        n_pairs += 1
        m, gp = c["decision"], g["consensus"]
        agreement_rank.append(RANK[m] - RANK[gp])
        if m == gp:
            continue
        bucket = f"{m} -> {gp}"
        buckets[bucket] += 1

        krank = RANK[g["kernel"]]
        breached = g["duties_below_floor"]
        fired = g["rules_fired"]
        if krank == 0:                       # K0: the case is epistemically undecidable;
            cf_consensus = "ABSTAIN"         # the lenses do not vote at all
        else:
            # full reconstruction (sanity check against the stored panel verdicts)
            pa = panel_rank(krank, fired, breached, {r for r in ALL_IDS if PANEL_OF[r] == "A"})
            pb = panel_rank(krank, fired, breached, {r for r in ALL_IDS if PANEL_OF[r] == "B"})
            pc = panel_rank(krank, fired, breached, {r for r in ALL_IDS if PANEL_OF[r] == "C"})
            assert LABELS[pa] == g["panelA"] and LABELS[pb] == g["panelB"] and LABELS[pc] == g["panelC"], \
                f"panel reconstruction failed for {c['case_id']}/{c['persona']}"

            # counterfactual: drop the positive procedural-fact rules
            cfA = panel_rank(krank, fired, breached, {r for r in CF_IDS if PANEL_OF[r] == "A"})
            cfB = panel_rank(krank, fired, breached, {r for r in CF_IDS if PANEL_OF[r] == "B"})
            cfC = panel_rank(krank, fired, breached, {r for r in CF_IDS if PANEL_OF[r] == "C"})
            cf_consensus = LABELS[consensus([cfA, cfB, cfC])]

        if gp == "PROHIBIT" and m == "REVIEW_REQUIRED":
            stats["rev_vs_pro"].append({
                "stakes": c["stakes"], "material_gap": c["material_gap"],
                "aa_low": c["adequacy_low"], "bar": c["bar"], "ratio": c["risk_ratio"],
                "veto": bool(c["veto"]), "hard_veto": bool(c["hard_veto"]),
                "kernel_rule": g["kernel_rule"], "fact_driven": cf_consensus != "PROHIBIT",
                "no_duty_below_floor": not breached,
                "fact_rules": [r for r in fired if r in FACT_ONLY],
                "level_rules": [r for r in fired if r not in FACT_ONLY],
            })
            if g["kernel_rule"] in ("K1", "K2"):
                gold_route["kernel K1/K2 (categorical duty below floor)"] += 1
            elif cf_consensus != "PROHIBIT":
                gold_route["escalation needs procedural facts (counterfactual drops to review)"] += 1
            else:
                gold_route["escalation by duty-floor rules alone"] += 1
            if c["stakes"] < PROHIBIT_STAKES_MIN:
                pass  # handled by the route classification below
            # model-side route (the ladder as implemented in core.py, decide())
            categorical = c["stakes"] >= PROHIBIT_STAKES_MIN
            bar_route = c["adequacy_low"] <= c["bar"] - PROHIBIT_MARGIN
            ratio_route = c["risk_ratio"] >= RATIO_PROHIBIT
            if not categorical:
                model_route["proportionality gate: stakes < prohibit_stakes_min"] += 1
            elif bar_route or ratio_route:
                model_route["categorical gate passed but ladder did not fire (should not happen)"] += 1
            else:
                model_route["categorical gate passed; adequacy above bar-margin and ratio < 0.70"] += 1
            if c["hard_veto"]:
                model_route["hard veto present (ladder would prohibit)"] += 1
            if c["veto"] and not c["hard_veto"]:
                model_route["guard veto triggered but stakes < stakes_veto_min"] += 1
            for r in fired:
                rule_divergent[r] += 1
            for r in fired:
                if r in FACT_ONLY:
                    fact_rule_divergent[r] += 1
            divergent_by_persona[c["persona_type"]] += 1
            divergent_by_domain[c["domain"]] += 1
            divergent_by_layer[c["layer"]] += 1
            if len(examples) < 12:
                examples.append({"case_id": c["case_id"], "persona": c["persona"],
                                 "domain": c["domain"], "persona_type": c["persona_type"],
                                 "stakes": c["stakes"],
                                 "aa_low": c["adequacy_low"], "bar": c["bar"],
                                 "ratio": c["risk_ratio"], "material_gap": c["material_gap"],
                                 "kernel_rule": g["kernel_rule"],
                                 "panels": [g["panelA"], g["panelB"], g["panelC"]],
                                 "fact_rules": [r for r in fired if r in FACT_ONLY],
                                 "counterfactual_consensus": cf_consensus})

        elif m == "PROHIBIT" and gp == "REVIEW_REQUIRED":
            stats["pro_vs_rev"].append({
                "stakes": c["stakes"], "material_gap": c["material_gap"],
                "aa_low": c["adequacy_low"], "bar": c["bar"], "ratio": c["risk_ratio"],
                "veto": bool(c["veto"]), "hard_veto": bool(c["hard_veto"]),
                "kernel_rule": g["kernel_rule"],
                "allowance_rules": [r for r in fired if r in {"A10", "B3", "B4", "B5", "B8", "C11", "C12"}],
            })

    def mean(xs):
        return round(float(np.mean(xs)), 4) if xs else None

    def share(cond):
        return round(sum(1 for x in cond if x) / len(cond), 4) if cond else None

    rev = stats["rev_vs_pro"]
    pro = stats["pro_vs_rev"]

    out = {
        "pairs": n_pairs,
        "exact_agreement_rate": round(sum(1 for d in agreement_rank if d == 0) / n_pairs, 4),
        "mean_rank_gap_model_minus_gold": round(float(np.mean(agreement_rank)), 4),
        "top_divergences": [{"pair": k, "n": v, "share_of_pairs": round(v / n_pairs, 4)}
                            for k, v in buckets.most_common(12)],
        "model_REVIEW_gold_PROHIBIT": {
            "n": len(rev),
            "stakes": {"mean": mean([x["stakes"] for x in rev]),
                       "p25": round(float(np.percentile([x["stakes"] for x in rev], 25)), 4),
                       "p75": round(float(np.percentile([x["stakes"] for x in rev], 75)), 4)},
            "material_gap": {"mean": mean([x["material_gap"] for x in rev]),
                             "share_ge_critical_gap_0.35": share([x["material_gap"] >= 0.35 for x in rev])},
            "adequacy_low_vs_bar": {"mean_aa_low": mean([x["aa_low"] for x in rev]),
                                    "mean_bar": mean([x["bar"] for x in rev]),
                                    "share_aa_low_above_bar": share([x["aa_low"] > x["bar"] for x in rev]),
                                    "share_aa_low_below_bar_but_above_margin":
                                        share([x["aa_low"] <= x["bar"] and x["aa_low"] > x["bar"] - PROHIBIT_MARGIN
                                             for x in rev])},
            "risk_ratio": {"mean": mean([x["ratio"] for x in rev]),
                           "share_ge_0.70": share([x["ratio"] >= 0.70 for x in rev]),
                           "share_ge_0.45": share([x["ratio"] >= 0.45 for x in rev])},
            "veto": {"share_any_veto": share([x["veto"] for x in rev]),
                     "share_hard_veto": share([x["hard_veto"] for x in rev])},
            "gold_route": dict(gold_route),
            "model_route": dict(model_route),
            "prohibitions_that_depend_on_procedural_facts_only":
                sum(1 for x in rev if x["fact_driven"]),
            "share_of_prohibitions_dependent_on_procedural_facts":
                round(sum(1 for x in rev if x["fact_driven"]) / len(rev), 4),
            "prohibitions_with_no_duty_below_any_floor":
                sum(1 for x in rev if x["no_duty_below_floor"]),
            "fact_rules_firing_in_this_bucket": dict(fact_rule_divergent.most_common()),
            "all_rules_firing_in_this_bucket": dict(rule_divergent.most_common()),
            "divergent_pairs_by_persona_type": dict(divergent_by_persona.most_common()),
            "divergent_pairs_by_domain": dict(divergent_by_domain.most_common()),
            "divergent_pairs_by_layer": dict(divergent_by_layer),
            "examples": examples,
        },
        "model_PROHIBIT_gold_REVIEW": {
            "n": len(pro),
            "stakes": {"mean": mean([x["stakes"] for x in pro])},
            "material_gap": {"mean": mean([x["material_gap"] for x in pro]),
                             "share_ge_0.35": share([x["material_gap"] >= 0.35 for x in pro])},
            "adequacy_low": {"mean": mean([x["aa_low"] for x in pro]),
                             "share_below_bar": share([x["aa_low"] <= x["bar"] for x in pro])},
            "risk_ratio": {"mean": mean([x["ratio"] for x in pro]),
                           "share_ge_0.70": share([x["ratio"] >= 0.70 for x in pro])},
            "hard_veto_share": share([x["hard_veto"] for x in pro]),
            "gold_kernel_rule": dict(Counter(x["kernel_rule"] for x in pro)),
            "panels_deescalated_by_allowance_rules":
                sum(1 for x in pro if x["allowance_rules"]),
            "allowance_rule_counts": dict(Counter(r for x in pro for r in x["allowance_rules"]).most_common()),
        },
        "note_on_interpretation": (
            "The panels' prohibition route is deliberately not the ladder's: the kernel uses "
            "declared duty floors and observable procedural infrastructure (appeal channel, notice, "
            "consent, audit, remedy period). The ladder uses adequacy against a stakes-scaled bar "
            "and a risk ratio. Where they disagree the model is usually more permissive, because "
            "no facet in the ontology measures the procedural fact the instruments name."
        ),
    }
    with open(os.path.join(OUT, "corpus_v5_confusion_analysis.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != "model_REVIEW_gold_PROHIBIT"}, indent=2)[:3000])
    print("\nmodel REVIEW -> gold PROHIBIT:")
    print(json.dumps(out["model_REVIEW_gold_PROHIBIT"], indent=2)[:2500])
    print(f"\nwrote {os.path.join(OUT, 'corpus_v5_confusion_analysis.json')}")


if __name__ == "__main__":
    main()
