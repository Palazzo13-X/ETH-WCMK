"""B25 - arithmetic mirror over the FULL corpus v7 (closes the G4'/G11' mirror limitation).

The ontology validator (B2) mirrors the arithmetic against the RDF graph on a 403
confrontation sample, because the 1,888,317-triple instance graph cannot be parsed on
this machine. Here the mirror is run over all 183,920 confrontations of corpus v7.

Method. The corpus stores, for every (case, persona) pair, the declared facet levels
rounded to four decimals. Feeding those rounded numbers back into core.py is *not* a
faithful reproduction: rounding at the fourth decimal moves a level across a guard floor
or a cap boundary. The faithful reconstruction goes one step earlier, from the objects
the generator actually used:

    level_f = min(1.0, requirement_f * min(0.95, factor_f * (1 + jitter)))      (persona)
    level_f = declared level, then E30 caps from the case's declared facts       (declared agent)

Those unrounded levels, plus the stored confidences, are pushed through core.confront and
the recomputed quantities are compared with the values the corpus records. Agreement to
1e-12 means the semantic layer and the arithmetic core are the same theory.

Run:  python3 _analysis/analysis/mirror_full_corpus.py
Writes: Evaluacoes/r4/mirror_full_corpus_v13.json
"""
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_analysis", "formal_core"))

from core import CaseSpec, Profile, confront, load_fitted_calibration
from facet_registry import FACETS
from fact_grounding import grounded_levels

R4 = os.path.join(ROOT, "Evaluacoes", "r5")
CODES = [f.code for f in FACETS]
DELIVERED_CAP = 0.95
GROUND_STRENGTH = 1.0


def case_from_row(r):
    return CaseSpec(r["case_id"], r["domain"], r["severity"], r["prudential"], r["irreversibility"],
                    r["facet_requirements"], r["U_E"], r["R_c"], tuple(r["critical_pillars"]),
                    r["horizon"], r["conflict_pattern"], r.get("agent_layer", "system"),
                    tuple(r["norms"]), norm_conflict=r["norm_conflict"],
                    evidence_conflict=r["evidence_conflict"], exposure=r["exposure"],
                    oversight=r.get("oversight", "unspecified"))


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    cal = load_fitted_calibration()            # frozen r3 ladder: the corpus was built with it
    cases = {}
    for fn in ("corpus_v7_layerA.jsonl", "corpus_v7_layerB.jsonl"):
        for r in read_jsonl(os.path.join(R4, fn)):
            cases[r["case_id"]] = (r, case_from_row(r))
    personas = {p["profile_id"]: p for p in read_jsonl(os.path.join(R4, "corpus_v7_personas.jsonl"))}

    n = 0
    max_diff = dict.fromkeys(("adequacy_low", "adequacy_central", "adequacy_high", "bar", "stakes",
                             "residual_risk", "S2", "S3", "S4", "aa_raw", "phi", "u", "material_gap"), 0.0)
    decisions = Counter()
    divergences = []
    guard_flips = 0
    t0 = time.time()
    for row in read_jsonl(os.path.join(R4, "corpus_v7_confrontations.jsonl")):
        raw_case, spec = cases[row["case_id"]]
        req = raw_case["facet_requirements"]
        if row["persona"] == "AGENT-declared":
            levels = dict(raw_case["declared_levels"])
        else:
            p = personas[row["persona"]]
            levels = {f.code: float(min(1.0, req[f.code] *
                                       min(DELIVERED_CAP, p["factors"].get(f.code, p["default_factor"])
                                                     * (1.0 + p["jitter"]))))
                      for f in FACETS if f.code not in p.get("omit", ())}
        levels, _caps = grounded_levels(raw_case["facts"], req, levels, GROUND_STRENGTH)
        cf = row.get("facet_confidence")
        conf = dict(zip(CODES, cf)) if isinstance(cf, list) else (cf or {})
        conf = {k: v for k, v in conf.items() if v is not None}
        res = confront(spec, Profile(row["persona"] + "-" + row["case_id"], levels, conf,
                                    row["agent_layer"]), cal)
        if res.get("adequacy") is None or row.get("adequacy") is None:
            if res["decision"] != row["decision"]:
                divergences.append({"case_id": row["case_id"], "persona": row["persona"],
                                    "recomputed": res["decision"], "stored": row["decision"]})
            decisions[res["decision"]] += 1
            n += 1
            continue
        checks = {
            "adequacy_low": (res["adequacy_low"], row["adequacy_low"]),
            "adequacy_central": (res["adequacy"], row["adequacy"]),
            "adequacy_high": (res["adequacy_high"], row["adequacy_high"]),
            "bar": (res["bar"], row["bar"]),
            "stakes": (res["stakes"], row["stakes"]),
            "residual_risk": (res["R_r"], row["R_r"]),
            "S2": (res["S2"], row["S2"]),
            "S3": (res["S3"], row["S3"]),
            "S4": (res["S4"], row["S4"]),
            "aa_raw": (res["adequacy_raw"], row["aa_raw"]),
            "phi": (res["facet_exposure"], row["phi"]),
            "u": (res["epistemic_penalty"], row["u"]),
            "material_gap": (res["material_gap"], row["material_gap"]),
        }
        for k, (a, b) in checks.items():
            d = abs(float(a) - float(b))
            if d > max_diff.get(k, 0.0):
                max_diff[k] = d
        n += 1
        if res["decision"] != row["decision"]:
            divergences.append({"case_id": row["case_id"], "persona": row["persona"],
                                "recomputed": res["decision"], "stored": row["decision"]})
        if tuple(res["veto"]) != tuple(row["veto"]) or tuple(res["hard_veto"]) != tuple(row["hard_veto"]):
            guard_flips += 1
            if len(divergences) < 20:
                divergences.append({"case_id": row["case_id"], "persona": row["persona"],
                                    "kind": "veto_set",
                                    "recomputed": list(res["veto"]), "stored": list(row["veto"])})
        decisions[res["decision"]] += 1

    rounded_max = max(max_diff.values())
    out = {
        "battery": "B25_full_corpus_mirror_v13",
        "question": "Is every number recorded in corpus v7 reproducible from the v13 core given the same inputs?",
        "calibration": "frozen r3 ladder (core.load_fitted_calibration default)",
        "confrontations": n,
        "cases": len(cases),
        "max_abs_difference_by_quantity": {k: v for k, v in sorted(max_diff.items())},
        "global_max_abs_difference": rounded_max,
        "verdict_divergences": len([d for d in divergences if d.get("kind") != "veto_set"]),
        "veto_set_divergences": guard_flips,
        "decision_distribution_recomputed": dict(decisions),
        "divergence_samples": divergences[:20],
        "runtime_seconds": round(time.time() - t0, 2),
    }
    with open(os.path.join(R4, "mirror_full_corpus_v13.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: out[k] for k in ("confrontations", "global_max_abs_difference",
                                         "verdict_divergences", "veto_set_divergences",
                                         "runtime_seconds")}, indent=2))


if __name__ == "__main__":
    main()
