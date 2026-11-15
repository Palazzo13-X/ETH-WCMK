"""B0' - measure the effect of the v12 core corrections against the frozen r3 corpus.

This is the "before/after" artefact required by gate G1': every claim in the paper about
what changed must trace to a generated file, not to a prose diff.

Run:  python3 _analysis/analysis/delta_v12_r4.py
Writes: Evaluacoes/r4/delta_v12.json

Inputs read (read-only, immutable): Evaluacoes/r3/corpus_v4_layerA.jsonl,
corpus_v4_layerB.jsonl, corpus_v4_profiles.jsonl, corpus_v4_confrontations.jsonl.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from statistics import mean, pstdev

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import (CaseSpec, Profile, confront, case_stakes, structural_terms,
                  default_calibration, load_fitted_calibration, requirement_for)
from facet_registry import FACETS

R3 = os.path.join(ROOT, "Evaluacoes", "r3")
OUT = os.path.join(ROOT, "Evaluacoes", "r4")


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def case_from_row(row):
    return CaseSpec(row["case_id"], row["domain"], row["severity"], row["prudential"],
                    row["irreversibility"], row["facet_requirements"], row["U_E"], row["R_c"],
                    tuple(row.get("critical_pillars", ())), row.get("horizon", "immediate"),
                    row.get("conflict_pattern", "none"))


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = [case_from_row(r) for r in read_jsonl(os.path.join(R3, "corpus_v4_layerA.jsonl"))]
    cases += [case_from_row(r) for r in read_jsonl(os.path.join(R3, "corpus_v4_layerB.jsonl"))]
    profiles = []
    meta = []
    for p in read_jsonl(os.path.join(R3, "corpus_v4_personas.jsonl")):
        profiles.append(p)
        meta.append(p)

    def persona_profile(persona, case_req):
        """Reproduce the r3 persona instantiation: level_f = req_f * factor_f * (1+jitter)."""
        scores, conf = {}, {}
        for f in FACETS:
            # the frozen r3 corpus predates the five procedural facets: they are
            # not requirements there, so they must not enter the aggregation at all.
            if f.code not in case_req:
                continue
            fac = persona["factors"][f.primary_pillar()]
            if persona["persona_type"] == "guard_fragile" and f.guard:
                fac = 0.25 / max(case_req[f.code], 1e-6)
            if persona["persona_type"] == "recoverable_failure" and f.code in ("C7", "M7"):
                fac = 1.15
            scores[f.code] = max(0.0, min(1.0, case_req[f.code] * fac * (1 + persona["jitter"])))
            conf[f.code] = persona["confidence_mu"]
        return Profile(persona["profile_id"], scores, conf, persona["layer"])

    stored = {}
    for row in read_jsonl(os.path.join(R3, "corpus_v4_confrontations.jsonl")):
        stored[(row["case_id"], row["agent"])] = row

    cal_default = default_calibration()
    cal_fitted = load_fitted_calibration()

    dec_default, dec_fitted = Counter(), Counter()
    aa_default, aa_fitted = [], []
    ratio_default, ratio_fitted = [], []
    by_aa = defaultdict(set)
    flips = Counter()
    satur = {"aa_ge_0999": 0, "aa_eq_1": 0, "saturated_and_prohibit": 0,
             "saturated_and_review": 0, "total": 0}
    n = 0
    for case in cases:
        for persona in meta:
            prof = persona_profile(persona, case.facet_requirements)
            n += 1
            r = confront(case, prof, cal_default)
            if r["decision"] != "ABSTAIN":
                aa_default.append(r["adequacy"])
                ratio_default.append(r["risk_ratio"])
                by_aa[round(r["adequacy"], 3)].add(round(r["risk_ratio"], 3))
                if r["adequacy"] >= 0.999:
                    satur["aa_ge_0999"] += 1
                    if abs(r["adequacy"] - 1.0) < 1e-9:
                        satur["aa_eq_1"] += 1
                    if r["decision"] == "PROHIBIT":
                        satur["saturated_and_prohibit"] += 1
                    elif r["decision"] == "REVIEW_REQUIRED":
                        satur["saturated_and_review"] += 1
            dec_default[r["decision"]] += 1
            rf = confront(case, prof, cal_fitted)
            dec_fitted[rf["decision"]] += 1
            aa_fitted.append(rf["adequacy"])
            ratio_fitted.append(rf.get("risk_ratio", 0.0))
            old = stored.get((case.case_id, prof.profile_id), {}).get("decision")
            if old and old != rf["decision"]:
                flips[(old, rf["decision"])] += 1

    def pearson(xs, ys):
        mx, my = mean(xs), mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        return num / den if den else 0.0

    d = (0.5, 0.4, 0.3, 0.2)
    s2, s3, s4 = structural_terms(d, cal_default)
    s3_old = sum(0.25 * min(d[i], d[j], d[kk]) for (i, j, kk) in
                 ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)))
    s4_old = (0.5 * 0.4 * 0.3 * 0.2) ** 0.25

    spread = max((max(v) - min(v)) for v in by_aa.values() if len(v) > 1)
    buckets_multi = sum(1 for v in by_aa.values() if len(v) > 1)

    result = {
        "generated_from": "Evaluacoes/r3 (frozen) + core.py v12",
        "confrontations": n,
        "calibration_used": {"default": str(cal_default),
                             "fitted_ladder": str(cal_fitted)},
        "decision_distribution_v12_default": dict(dec_default),
        "decision_distribution_v12_fitted_ladder": dict(dec_fitted),
        "decision_flips_v11_to_v12": {f"{a}->{b}": c for (a, b), c in flips.most_common()},
        "total_flips": sum(flips.values()),
        "adequacy_degeneracy": {
            "share_aa_ge_0.999": satur["aa_ge_0999"] / max(n, 1),
            "share_aa_exactly_1": satur["aa_eq_1"] / max(n, 1),
            "internal_contradictions_prohibit": satur["saturated_and_prohibit"],
            "internal_contradictions_review": satur["saturated_and_review"],
        },
        "structural_term_counterexample_v11": {
            "deficits": list(d),
            "S2": s2, "S3": s3_old, "S4_geometric_mean": round(s4_old, 6),
            "S4_godel_min": s4,
            "hierarchy_violated_in_v11": s4_old > s3_old,
        },
        "risk_adequacy_redundancy": {
            "pearson_Aa_vs_ratio_new": round(pearson(aa_default, ratio_default), 4),
            "buckets_with_same_Aa_and_different_ratio": buckets_multi,
            "max_ratio_spread_within_same_Aa_bucket": round(spread, 4),
        },
        "abstention": {
            "abstain_total_v12_default": dec_default.get("ABSTAIN", 0),
            "abstain_total_v11_stored": sum(1 for v in stored.values() if v.get("decision") == "ABSTAIN"),
        },
    }

    # guard-compensation probe: a hard guard set to zero must not leave the pillar high
    probe = {}
    for code in (f.code for f in FACETS if f.guard):
        req = {f.code: 0.85 for f in FACETS}
        lev = {f.code: 0.95 for f in FACETS}
        lev[code] = 0.0
        r = confront(CaseSpec(f"PROBE-{code}", "SA", "high", "maximum", "irreversible",
                              req, 0.35, 0.70, ("M", "C", "W", "K")),
                     Profile("p", lev), cal_default)
        probe[code] = {"pillar_levels": r["levels"], "adequacy": r["adequacy"],
                       "decision": r["decision"], "worst_pillar_deficit": max(r["deficits"])}
    result["guard_compensation_probe"] = probe

    with open(os.path.join(OUT, "delta_v12.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2)[:2500])


if __name__ == "__main__":
    main()
