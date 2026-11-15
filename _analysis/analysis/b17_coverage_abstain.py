"""B17 — coverage-abstention (E26) fired on purpose.

AUDIT_v12 declared that the coverage-abstention branch never fires in the corpus,
because every declared profile is complete. That is a data gap, not a code gap: the
branch exists and I22 tests it, but no corpus case exercises it. This battery
degrades declared coverage systematically on real case x persona pairs and measures
where the branch actually triggers, and what it costs in verdict terms.

Method. For each case we take one real persona from the corpus, take its declared
facet levels, and drop facet declarations in a deterministic order (lowest level
first, then by code) to reach target coverages 1.00 ... 0.60. At each level we run
`confront` with the frozen ladder and record the verdict.

Output: Evaluacoes/r4/B17_coverage_abstain.json
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import CaseSpec, Profile, confront, load_fitted_calibration  # noqa: E402
from facet_registry import FACETS  # noqa: E402

OUT = os.path.join(ROOT, "Evaluacoes", "r4", "B17_coverage_abstain.json")
LEVELS = [1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60]
CONFRONTATIONS = os.path.join(ROOT, "Evaluacoes", "r4", "corpus_v6_confrontations.jsonl")


def as_dict(values):
    if isinstance(values, dict):
        return {k: float(v) for k, v in values.items()}
    return {f.code: float(v) for f, v in zip(FACETS, values)}


def case_from_row(row):
    return CaseSpec(
        case_id=row["case_id"], domain=row["domain"], severity=row["severity"],
        prudential=row["prudential"], irreversibility=row["irreversibility"],
        facet_requirements=as_dict(row["facet_requirements"]),
        U_E=float(row["U_E"]),
        R_c=float(row["R_c"]), critical_pillars=tuple(row["critical_pillars"]),
        horizon=row["horizon"], conflict_pattern=row["conflict_pattern"],
        agent_layer=row.get("agent_layer", "system"), norms=tuple(row.get("norms", ())),
        norm_conflict=row.get("norm_conflict", "none"),
        evidence_conflict=bool(row.get("evidence_conflict", False)),
        exposure=float(row.get("exposure", 0.5)),
    )


def drop_to(levels, target):
    """Remove facet declarations until completeness <= target, deterministic order."""
    codes = sorted(levels, key=lambda c: (levels[c], c))
    keep = max(1, int(round(len(codes) * target)))
    dropped = set(codes[: len(codes) - keep])
    return {c: v for c, v in levels.items() if c not in dropped}, len(dropped)


def main():
    started = time.time()
    cal = load_fitted_calibration()
    cases = {}
    for path in (os.path.join(ROOT, "Evaluacoes", "r4", "corpus_v6_layerA.jsonl"),
                 os.path.join(ROOT, "Evaluacoes", "r4", "corpus_v6_layerB.jsonl")):
        for line in open(path):
            r = json.loads(line)
            cases[r["case_id"]] = case_from_row(r)

    seen = set()
    per_level = {}
    fires = 0
    probes = 0
    examples = []
    first_fire = {}
    n_cases = 0
    full_aa = []
    trimmed_aa = []
    for line in open(CONFRONTATIONS):
        row = json.loads(line)
        if row["case_id"] in seen:
            continue
        seen.add(row["case_id"])
        n_cases += 1
        case = cases[row["case_id"]]
        base = as_dict(row["facet_levels"])
        for level in LEVELS:
            scores, dropped = drop_to(base, level)
            res = confront(case, Profile("probe", scores), cal)
            probes += 1
            d = per_level.setdefault(level, {"verdicts": {}, "abstain": 0, "adequacies": []})
            d["verdicts"][res["decision"]] = d["verdicts"].get(res["decision"], 0) + 1
            if res["decision"] == "ABSTAIN":
                d["abstain"] += 1
                fires += 1
                if level not in first_fire and "coverage" in res.get("reason", ""):
                    first_fire[level] = {"case_id": case.case_id, "reason": res["reason"],
                                        "completeness": res.get("completeness")}
                if len(examples) < 6:
                    examples.append({"case_id": case.case_id, "domain": row["domain"],
                                    "persona": row["persona"], "target_coverage": level,
                                    "facets_dropped": dropped, "reason": res.get("reason", "epistemic abstention"),
                                    "completeness": res.get("completeness"),
                                    "verdict_before_abstention": None})
            elif res.get("adequacy") is not None:
                d["adequacies"].append(res["adequacy"])
            if level == 1.00:
                full_aa.append((case.case_id, res["decision"], res.get("adequacy")))
            elif level == 0.75:
                trimmed_aa.append((case.case_id, res["decision"], res.get("adequacy")))

    by_id_full = {c: (dec, aa) for c, dec, aa in full_aa}
    pairs = []
    for cid, dec, aa in trimmed_aa:
        fdec, faa = by_id_full.get(cid, (None, None))
        if faa is not None and aa is not None:
            pairs.append(aa - faa)
    pairs.sort()
    anti_gaming = {
        "comparison": "same case, same persona: full declaration vs 8 weakest facets dropped",
        "n_pairs": len(pairs),
        "mean_adequacy_change": round(sum(pairs) / len(pairs), 4) if pairs else None,
        "median_adequacy_change": round(pairs[len(pairs) // 2], 4) if pairs else None,
        "max_adequacy_change": round(max(pairs), 4) if pairs else None,
        "cases_that_become_admissible": sum(1 for x in pairs if x > 0.10),
        "note": "coverage floor is an anti-gaming device: omitting the weakest facets raises apparent adequacy",
    }


    out = {
        "battery": "B17_coverage_abstain",
        "purpose": "exercise the E26 coverage-abstention branch that never fires on the corpus",
        "cases": n_cases,
        "probes": probes,
        "levels": LEVELS,
        "coverage_floor_in_code": 0.70,
        "per_level": {
            str(k): {
                "verdicts": v["verdicts"],
                "abstain_count": v["abstain"],
                "abstain_share": round(v["abstain"] / n_cases, 4),
                "mean_adequacy_when_not_abstaining": round(sum(v["adequacies"]) / len(v["adequacies"]), 4)
                if v["adequacies"] else None,
            }
            for k, v in per_level.items()
        },
        "total_abstain_fires": fires,
        "anti_gaming_pair": anti_gaming,
        "first_fire_by_level": first_fire,
        "examples": examples,
        "runtime_seconds": round(time.time() - started, 2),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out["per_level"], indent=2))
    print("fires:", fires, "of", probes, "probes; runtime", out["runtime_seconds"], "s")


if __name__ == "__main__":
    main()
