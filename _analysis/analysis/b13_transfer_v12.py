"""B13 (v12): transfer. Does the ladder fitted on the training domains generalise to
the held-out domains, and does it beat the declared (uncalibrated) ladder there?

Re-runs the full arithmetic for every stored (case, persona) pair under two
calibrations:
  (a) declared default ladder  - the parameters stated in the paper before any fitting;
  (b) fitted ladder            - Evaluacoes/r4/ladder_calibration_v12.json (B5 fit).

Run: python3 _analysis/analysis/b13_transfer_v12.py
Output: Evaluacoes/r4/B13_transfer_v12.json
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "formal_core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus"))
from facet_registry import FACETS                                                # noqa: E402
from core import CaseSpec, Profile, confront, default_calibration, load_fitted_calibration  # noqa: E402
from gold_panels_v5 import cohens_kappa                                           # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R4 = os.path.join(ROOT, "Evaluacoes", "r4")
CORPUS_VER = os.environ.get("ETH_WCMK_CORPUS", "6")
TRAIN = {"SA", "JS", "IC", "FI", "PD", "GP", "IM", "ED", "MA"}
TEST = {"TB", "TS", "RS", "DS"}


def main():
    cases = {}
    for fn in (f"corpus_v{CORPUS_VER}_layerA.jsonl", f"corpus_v{CORPUS_VER}_layerB.jsonl"):
        for line in open(os.path.join(R4, fn)):
            c = json.loads(line)
            cases[c["case_id"]] = c

    cal_fit = load_fitted_calibration(os.path.join(R4, "ladder_calibration_v12.json"))
    cal_def = default_calibration()

    dec_fit, dec_def, gold, dom, layer = [], [], [], [], []
    aa_fit, aa_def = [], []
    abstain_fit = abstain_def = 0
    for line in open(os.path.join(R4, f"corpus_v{CORPUS_VER}_confrontations.jsonl")):
        r = json.loads(line)
        c = cases.get(r["case_id"])
        if c is None or r.get("gold_consensus") is None:
            continue
        levels = {f.code: v for f, v in zip(FACETS, r["facet_levels"])}
        conf = {f.code: v for f, v in zip(FACETS, r["facet_confidence"])}
        req = {f.code: v for f, v in zip(FACETS, r["facet_requirements"])}
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"], c["irreversibility"],
                        req, c["U_E"], c["R_c"], tuple(c.get("critical_pillars", ("M", "K"))),
                        c.get("horizon", "immediate"), c.get("conflict_pattern", "none"),
                        r.get("agent_layer", "system"), tuple(c.get("norms", ())),
                        norm_conflict=c.get("norm_conflict", "none"),
                        evidence_conflict=c.get("evidence_conflict", False),
                        exposure=c.get("exposure", 0.5))
        prof = Profile(r["persona"], levels, conf, "system")
        a = confront(spec, prof, cal_fit)
        b = confront(spec, prof, cal_def)
        dec_fit.append(a["decision"]); dec_def.append(b["decision"])
        aa_fit.append(a["adequacy_low"]); aa_def.append(b["adequacy_low"])
        abstain_fit += a["decision"] == "ABSTAIN"; abstain_def += b["decision"] == "ABSTAIN"
        gold.append(r["gold_consensus"]); dom.append(r["domain"]); layer.append(c["layer"])

    def sub(mask):
        return [d for d, m in zip(dec_fit, mask) if m], [g for g, m in zip(gold, mask) if m], \
               [d for d, m in zip(dec_def, mask) if m]

    test_mask = [d in TEST for d in dom]
    train_mask = [d in TRAIN for d in dom]
    b_mask = [l == "B" for l in layer]

    df, dg, dd = sub(test_mask)
    tf, tg, td = sub(train_mask)
    bf, bg, bd = sub(b_mask)

    out = {
        "corpus": f"corpus_v{CORPUS_VER}", "pairs": len(gold),
        "holdout": "domains TB, TS, RS, DS (never used in the fit) and all 320 layer-B narratives",
        "held_out_domain_pairs": sum(test_mask), "train_domain_pairs": sum(train_mask),
        "layerB_pairs": sum(b_mask),
        "kappa_fitted_holdout": round(cohens_kappa(df, dg), 4),
        "kappa_fitted_in_sample": round(cohens_kappa(tf, tg), 4),
        "kappa_default_holdout": round(cohens_kappa(dd, dg), 4),
        "kappa_default_in_sample": round(cohens_kappa(td, tg), 4),
        "transfer_gap": round(cohens_kappa(tf, tg) - cohens_kappa(df, dg), 4),
        "fitted_vs_default_on_holdout": round(cohens_kappa(df, dg) - cohens_kappa(dd, dg), 4),
        "layerB_transfer": {"kappa_fitted": round(cohens_kappa(bf, bg), 4),
                            "kappa_default": round(cohens_kappa(bd, bg), 4)},
        "by_domain": {},
        "abstain_rate_fitted": round(abstain_fit / len(gold), 4),
        "abstain_rate_default": round(abstain_def / len(gold), 4),
        "mean_adequacy_fitted": round(sum(aa_fit) / len(aa_fit), 4),
        "mean_adequacy_default": round(sum(aa_def) / len(aa_def), 4),
        "verdict_distribution_fitted": dict(Counter(dec_fit)),
        "verdict_distribution_default": dict(Counter(dec_def)),
    }
    for d in sorted(set(dom)):
        m = [x == d for x in dom]
        f, g, dd_ = sub(m)
        out["by_domain"][d] = {"n": len(g), "split": "train" if d in TRAIN else "holdout",
                              "kappa_fitted": round(cohens_kappa(f, g), 4),
                              "kappa_default": round(cohens_kappa(dd_, g), 4)}
    out["domains_where_default_beats_fitted"] = [d for d, v in out["by_domain"].items()
                                                 if v["kappa_default"] > v["kappa_fitted"]]
    with open(os.path.join(R4, "B13_transfer_v12.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: out[k] for k in ("pairs", "kappa_fitted_holdout", "kappa_fitted_in_sample",
                                         "kappa_default_holdout", "transfer_gap",
                                         "fitted_vs_default_on_holdout", "layerB_transfer",
                                         "domains_where_default_beats_fitted")}, indent=2))


if __name__ == "__main__":
    main()
