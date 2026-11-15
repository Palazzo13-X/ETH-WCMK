"""B15 — the agency layer: what E28 actually says, and whether it bites.

AUDIT_v12 item 51: the corpus had no agent-layer / chain cases, so E28 (delegation,
weakest link, retention of the critical duty) had no empirical content.

Chain model (all arithmetic comes from core.py, rule 1 of the project):

  A layer can exercise only the pillars it is capable of carrying:
      system   -> W, C, M, K
      model    -> C, K
      operator -> C, K
  The chain is evaluated per pillar: the part of a duty that feeds W or M belongs to the
  accountable (declaring) layer, the part that feeds C or K is discharged by the
  executing layer, at its weakest link. The chain profile is therefore the beta-weighted
  mixture of the declared facet level and the delegate's measured level for the same
  facet, and the chain verdict is the verdict core.py returns for that profile. We run
  it twice: with the best delegate available in the delegable layers (optimistic
  delegation) and with the worst delegate (pessimistic delegation). The distance between
  the two is how much of the decision is really decided by *who executes* the duty.

Reported:
  * verdict distribution declared vs chain (best/worst delegate);
  * how many verdicts become stricter, and how many the model could never detect if the
    chain were evaluated only at the declaring layer;
  * the number of facets that no delegated layer can carry (the structural ceiling of
    delegation);
  * duty retention: cases whose critical pillars include W or M, i.e. the duty cannot be
    transferred to the executing layer at all;
  * declaration optimism: the gap between the adequacy the declared agent claims and the
    adequacy the chain actually has with its best delegate.

Output: Evaluacoes/r4/B15_delegation_chains.json
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
from core import CaseSpec, Profile, confront, load_fitted_calibration  # noqa: E402
from facet_registry import FACETS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")

CARRIED = {"system": {"W", "C", "M", "K"}, "model": {"C", "K"}, "operator": {"C", "K"}}
ORDER = ("PROHIBIT", "REVIEW_REQUIRED", "ALLOW_WITH_GUARDS", "ALLOW", "ABSTAIN")
RANK = {d: i for i, d in enumerate(ORDER)}   # lower rank = stricter


def carriers(facet):
    used = {p for p, b in zip("WCMK", facet.beta) if b > 0}
    return [L for L, cap in CARRIED.items() if used <= cap]


def spec_of(case):
    return CaseSpec(case["case_id"], case["domain"], case["severity"], case["prudential"],
                    case["irreversibility"], case["facet_requirements"], case["U_E"], case["R_c"],
                    tuple(case["critical_pillars"]), case["horizon"], case["conflict_pattern"],
                    "system", tuple(case["norms"]), norm_conflict=case["norm_conflict"] or "none",
                    evidence_conflict=case["evidence_conflict"], exposure=case["exposure"])


def main():
    cal = load_fitted_calibration()
    codes = [f.code for f in FACETS]
    cases = {}
    for name in ("corpus_v6_layerA.jsonl", "corpus_v6_layerB.jsonl"):
        for line in open(os.path.join(R4, name)):
            c = json.loads(line)
            cases[c["case_id"]] = c

    declared, delegates = {}, {}
    for line in open(os.path.join(R4, "corpus_v6_confrontations.jsonl")):
        r = json.loads(line)
        cid, L = r["case_id"], r["agent_layer"]
        if r["persona"] == "AGENT-declared":
            declared[cid] = r
        else:
            delegates.setdefault(cid, {}).setdefault(L, []).append(r)

    # how many facets can a delegated layer carry at all
    carry_counts = {L: sum(1 for f in FACETS if L in carriers(f)) for L in CARRIED}
    single_layer = [f.code for f in FACETS if carriers(f) == ["system"]]

    stats = {k: {"aa": [], "risk": []} for k in CARRIED}
    best_changes = worst_changes = 0
    best_kinds, worst_kinds = {}, {}
    aa_best, aa_worst, gap_delegate = [], [], []
    risk_best, risk_worst = [], []
    bottleneck = {}
    retention = []
    verdicts_best, verdicts_worst = {}, {}
    flips_naive = 0
    pillar_carry = {p: [L for L, cap in CARRIED.items() if p in cap] for p in "WCMK"}

    def classify(a, b):
        """ABSTAIN is an epistemic state, not a permissive rung of the ladder, so it is
        counted separately from the strictness direction."""
        if "ABSTAIN" in (a, b):
            return "epistemic (abstention appears or disappears)"
        if RANK[b] < RANK[a]:
            return "stricter"
        return "looser"

    def chain_profile(cid, decl_lv, delegates_case, mode):
        """Pillar-scoped weakest link. The part of a facet that feeds W or M is the
        responsibility of the accountable (declaring) layer; the part that feeds C or K
        is discharged by the executing layer, so the chain level of facet f is the
        beta-weighted mixture

            level_f = [ sum_{p in {W,M}} beta_fp * level_f(system)
                      + sum_{p in {C,K}} beta_fp * min(level_f(system), level_f(delegate)) ]
                      / sum_p beta_fp

        where level_f(delegate) is the level of the same facet measured on the best (or
        worst) delegate available in the model or operator layer. The chain can only be
        weaker than the declaration, never stronger: a delegate cannot repair a deficit
        the accountable layer did not have."""
        best_lv, worst_lv = dict(decl_lv), dict(decl_lv)
        for L, rows in delegates_case.items():
            if not rows:
                continue
            pick = (max(rows, key=lambda r: r["adequacy_low"]) if mode == "best"
                    else min(rows, key=lambda r: r["adequacy_low"]))
            lv = dict(zip(codes, pick["facet_levels"]))
            for f in FACETS:
                best_lv[f.code] = max(best_lv[f.code], lv[f.code])
                worst_lv[f.code] = min(worst_lv[f.code], lv[f.code])
        out = {}
        for f in FACETS:
            w = sum(f.beta)
            if w == 0:
                out[f.code] = decl_lv[f.code]
                continue
            acc = sum(f.beta[i] * decl_lv[f.code] for i in range(4) if "WCMK"[i] in ("W", "M"))
            exe = sum(f.beta[i] * min(decl_lv[f.code],
                                      best_lv[f.code] if mode == "best" else worst_lv[f.code])
                      for i in range(4) if "WCMK"[i] in ("C", "K"))
            out[f.code] = (acc + exe) / w
        return out

    best_dec, worst_dec, gold = [], [], []
    gold_best_delegate, gold_worst_delegate = [], []

    def kappa(a, b):
        n = len(a)
        po = sum(1 for x, y in zip(a, b) if x == y) / n
        cats = set(a) | set(b)
        pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
        return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)

    for cid, dec in declared.items():
        case = cases[cid]
        spec = spec_of(case)
        crit = set(case["critical_pillars"])
        if crit & {"W", "M"}:
            retention.append(cid)

        decl_lv = dict(zip(codes, dec["facet_levels"]))
        decl_cf = dict(zip(codes, dec["facet_confidence"]))
        for L, rows in delegates[cid].items():
            for r in rows:
                stats[L]["aa"].append(r["adequacy_low"])
                stats[L]["risk"].append(r["R_r"])

        best_lv = chain_profile(cid, decl_lv, delegates[cid], "best")
        worst_lv = chain_profile(cid, decl_lv, delegates[cid], "worst")

        rb = confront(spec, Profile("chain-best-" + cid, best_lv, decl_cf, "chain"), cal, FACETS)
        rw = confront(spec, Profile("chain-worst-" + cid, worst_lv, decl_cf, "chain"), cal, FACETS)
        aa_best.append(rb.get("adequacy_low") or 0.0)
        aa_worst.append(rw.get("adequacy_low") or 0.0)
        best_dec.append(rb["decision"])
        worst_dec.append(rw["decision"])
        gold.append(dec["gold_consensus"])
        allrows = [r for rows in delegates[cid].values() for r in rows]
        gold_best_delegate.append(max(allrows, key=lambda r: r["adequacy_low"])["gold_consensus"])
        gold_worst_delegate.append(min(allrows, key=lambda r: r["adequacy_low"])["gold_consensus"])
        gap_delegate.append((rb.get("adequacy_low") or 0.0) - (rw.get("adequacy_low") or 0.0))
        risk_best.append(rb.get("R_r") or 0.0)
        risk_worst.append(rw.get("R_r") or 0.0)
        if rb["decision"] != dec["decision"]:
            best_changes += 1
            kind = classify(dec["decision"], rb["decision"])
            best_kinds[kind] = best_kinds.get(kind, 0) + 1
        if rw["decision"] != dec["decision"]:
            worst_changes += 1
            kind = classify(dec["decision"], rw["decision"])
            worst_kinds[kind] = worst_kinds.get(kind, 0) + 1
        gd = rw.get("guarded_deficits")
        if gd:
            p = "WCMK"[max(range(4), key=lambda i: gd[i])]
            bottleneck[p] = bottleneck.get(p, 0) + 1
        verdicts_best[rb["decision"]] = verdicts_best.get(rb["decision"], 0) + 1
        verdicts_worst[rw["decision"]] = verdicts_worst.get(rw["decision"], 0) + 1

        # naive chain: ignore capability, take the weakest persona in the corpus for this case
        rows_all = [r for rows in delegates[cid].values() for r in rows] + [dec]
        weakest = min(rows_all, key=lambda r: r["adequacy_low"])
        if weakest["decision"] != dec["decision"]:
            flips_naive += 1

    out = {
        "battery": "B15",
        "question": "E28: who can carry a duty, and what happens when it is delegated",
        "cases": len(declared),
        "capability_definition_facet_level": {
            "facets_carryable_by_model_or_operator": carry_counts["model"],
            "facets_only_the_accountable_layer_can_carry": len(single_layer),
            "share_of_canon_requiring_accountability": round(len(single_layer) / len(FACETS), 4),
            "note": "a facet is delegable only if every pillar it feeds is exercisable by "
                    "the delegate; with 33 facets, only C1 (pure capability) is",
        },
        "capability_definition_pillar_level": {"W": pillar_carry["W"], "C": pillar_carry["C"],
                                              "M": pillar_carry["M"], "K": pillar_carry["K"]},
        "declared_baseline": {
            "mean_adequacy_low": round(statistics.mean(d["adequacy_low"] for d in declared.values()
                                                      if d["adequacy_low"] is not None), 4),
            "mean_R_r": round(statistics.mean(d["R_r"] for d in declared.values()), 4),
            "verdict_distribution": {d: sum(1 for x in declared.values() if x["decision"] == d)
                                     for d in ORDER},
        },
        "layer_means": {L: {"adequacy_low": round(statistics.mean(v["aa"]), 4),
                            "R_r": round(statistics.mean(v["risk"]), 4), "n": len(v["aa"])}
                        for L, v in stats.items()},
        "chain_with_best_delegate": {
            "verdict_changes_vs_declared": best_changes,
            "transition_kinds": best_kinds,
            "mean_adequacy": round(statistics.mean(aa_best), 4),
            "mean_R_r": round(statistics.mean(risk_best), 4),
            "verdict_distribution": verdicts_best,
        },
        "chain_with_worst_delegate": {
            "verdict_changes_vs_declared": worst_changes,
            "transition_kinds": worst_kinds,
            "mean_adequacy": round(statistics.mean(aa_worst), 4),
            "mean_R_r": round(statistics.mean(risk_worst), 4),
            "verdict_distribution": verdicts_worst,
            "bottleneck_pillar_counts": bottleneck,
        },
        "agreement_with_the_gold_lens": {
            "declared_verdict_vs_its_own_gold": round(kappa([d["decision"] for d in declared.values()],
                                                           [d["gold_consensus"] for d in declared.values()]), 4),
            "chain_best_delegate_vs_gold_of_that_delegate": round(kappa(best_dec, gold_best_delegate), 4),
            "chain_worst_delegate_vs_gold_of_that_delegate": round(kappa(worst_dec, gold_worst_delegate), 4),
            "chain_worst_delegate_vs_gold_of_the_declaring_agent": round(kappa(worst_dec, gold), 4),
        },
        "spread_decided_by_the_executor": {
            "mean_gap_best_minus_worst_delegate": round(statistics.mean(gap_delegate), 4),
            "max_gap": round(max(gap_delegate), 4),
        },
        "naive_weakest_link_ignoring_capability": {
            "verdict_changes_vs_declared": flips_naive,
        },
        "duty_retention_E28": {
            "cases_whose_critical_pillars_include_W_or_M": len(retention),
            "share": round(len(retention) / len(declared), 4),
            "consequence": "the critical duty cannot be transferred to the executing layer; "
                           "the fallback policy is not optional but structurally required",
        },
    }
    with open(os.path.join(R4, "B15_delegation_chains.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
