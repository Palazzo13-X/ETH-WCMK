"""B3: calibration sweep (absolute vs relative veto thresholds) and gold agreement.

The corpus fixes the requirement scale (critical facets are required at ~0.85-0.95
of the pillar), so an absolute veto threshold tuned by eye is arbitrary. This battery
compares two veto semantics against the externally documented gold adjudication rules:

  A. absolute:  veto pillar i if d_i >= theta_i
  B. relative:  veto pillar i if d_i / q_i >= phi  (the agent delivers less than
                (1-phi) of what the case demands on that pillar)

Reported for each candidate: share of confrontations where the cap binds, veto share
by severity band (must be monotone), decision distribution, and Cohen's kappa against
the gold rule decisions on the 120 gold cases.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from facet_registry import FACETS
from core import (Calibration, CaseSpec, Profile, confront, PILLARS, EDGES, FACES,
                  prudential_floor, structural_terms, clamp, IDX)

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Evaluacoes", "r2"))
R2 = os.path.join(OUT)

def cal(**kw):
    base = dict(lam=(0.30, 0.25, 0.25, 0.20), alpha=(1/6,)*6, beta_face=(1/4,)*4,
                gamma=0.12, eta=0.05, omega=0.03, rho=0.15)
    base.update(kw)
    return Calibration(**base)


def confront_variant(case, profile, c, veto_mode="absolute", theta=None, phi=None,
                     hard_extra=0.15):
    """Same core arithmetic, with the veto rule swapped between modes."""
    ell, guard_failures = __import__("core").project(profile.facet_scores, FACETS, cap_guards=True)
    q, _ = __import__("core").project(case.facet_requirements, FACETS)
    d = tuple(max(0.0, q[i] - ell[i]) for i in range(4))
    s2, s3, s4 = structural_terms(d, c)
    D = sum(c.lam[i] * d[i] for i in range(4))
    qk = q[IDX["K"]]
    u = case.U_E * d[IDX["K"]] / qk if qk > 1e-9 else case.U_E * d[IDX["K"]]
    u = clamp(u)
    aa_raw = clamp(1.0 - D - c.gamma * s2 - c.eta * s3 - c.omega * s4 - c.rho * u)
    if veto_mode == "absolute":
        rel = [d[i] >= theta[i] for i in range(4)]
        hard = [d[i] >= theta[i] + hard_extra or d[i] >= 0.75 for i in range(4)]
    elif veto_mode == "relative":
        rel = [q[i] > 1e-9 and d[i] / q[i] >= phi[i] for i in range(4)]
        hard = [q[i] > 1e-9 and d[i] / q[i] >= phi[i] + hard_extra for i in range(4)]
    else:  # none
        rel = [False]*4; hard = [False]*4
    if any(rel):
        aa = min(aa_raw, 1.0 - max(d[i] for i in range(4) if rel[i]))
    else:
        aa = aa_raw
    aa = max(0.0, aa)
    sigma = prudential_floor(case)
    r_r = case.R_c * (1.0 - aa) + sigma * case.R_c
    ratio = r_r / case.R_c
    if any(hard):
        decision = "PROHIBIT"
    elif aa <= 0.45 or ratio >= 0.65:
        decision = "PROHIBIT"
    elif any(rel) or aa <= 0.60 or ratio >= 0.40:
        decision = "REVIEW_REQUIRED"
    elif aa <= 0.78 or ratio >= 0.20:
        decision = "ALLOW_WITH_GUARDS"
    else:
        decision = "ALLOW"
    return {"adequacy": aa, "adequacy_raw": aa_raw, "decision": decision,
            "veto": any(rel), "hard_veto": any(hard), "ratio": ratio,
            "deficits": d, "relative": d}


def kappa(labels_a, labels_b):
    cats = sorted(set(labels_a) | set(labels_b))
    n = len(labels_a)
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pa = {c: labels_a.count(c) / n for c in cats}
    pb = {c: labels_b.count(c) / n for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats)
    return 1.0 if pe >= 1.0 else (po - pe) / (1.0 - pe)


def main():
    cases = [json.loads(l) for l in open(os.path.join(R2, "corpus_v3_cases.jsonl"))]
    profiles = [json.loads(l) for l in open(os.path.join(R2, "corpus_v3_profiles.jsonl"))][:12]
    specs = [CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                      c["irreversibility"], c["requirements"], c["epistemic_uncertainty"],
                      c["contextual_risk"], tuple(c["critical_pillars"])) for c in cases]
    gold = {c["case_id"]: c["gold_decision"] for c in cases[:120]}
    profs = [Profile(p["profile_id"], p["levels"], p["confidence"]) for p in profiles]

    variants = []
    for b in (0.45, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        variants.append(("absolute", {"theta": (b+0.05, b, b, b+0.05)}, f"abs_theta_{b:.2f}"))
    for phi in (0.40, 0.50, 0.55, 0.60, 0.65):
        variants.append(("relative", {"phi": (phi, phi-0.05, phi-0.05, phi)}, f"rel_phi_{phi:.2f}"))
    variants.append(("none", {}, "no_veto_compensatory_only"))

    results = []
    for mode, kw, name in variants:
        c = cal(**{k: v for k, v in kw.items() if k != "phi"})
        rows = []
        for spec in specs:
            for pr in profs:
                r = confront_variant(spec, pr, c, veto_mode=mode,
                                     theta=kw.get("theta"), phi=kw.get("phi"))
                r["severity"] = spec.severity
                rows.append(r)
        sev = {s: [r for r in rows if r["severity"] == s]
               for s in ("low", "medium", "high", "critical")}
        by_sev = {s: round(sum(1 for r in sev[s] if r["veto"]) / max(1, len(sev[s])), 4)
                  for s in sev}
        dec = [r["decision"] for r in rows]
        dist = {k: round(dec.count(k) / len(dec), 4) for k in set(dec)}
        # gold agreement: use the 120 gold cases confronted with the first profile only,
        # plus every profile: report mean kappa across profiles
        ks = []
        for pr in profs:
            a = [confront_variant(spec, pr, c, veto_mode=mode, theta=kw.get("theta"),
                                  phi=kw.get("phi"))["decision"]
                 for spec in specs[:120]]
            b_ = [gold[spec.case_id] for spec in specs[:120]]
            ks.append(kappa(a, b_))
        mean_a = float(np.mean([r["adequacy"] for r in rows]))
        cap_bind = sum(1 for r in rows if r["adequacy"] < r["adequacy_raw"] - 1e-9)
        results.append({
            "variant": name, "mode": mode,
            "veto_share_overall": round(sum(1 for r in rows if r["veto"]) / len(rows), 4),
            "cap_binds_share": round(cap_bind / len(rows), 4),
            "hard_veto_share": round(sum(1 for r in rows if r["hard_veto"]) / len(rows), 4),
            "veto_share_by_severity": by_sev,
            "veto_monotone_in_severity": all(by_sev[a] <= by_sev[b]
                                            for a, b in zip(("low", "medium", "high"),
                                                           ("medium", "high", "critical"))),
            "mean_adequacy": round(mean_a, 4),
            "decision_distribution": dist,
            "gold_kappa_mean": round(float(np.mean(ks)), 4),
            "gold_kappa_min": round(float(np.min(ks)), 4),
            "gold_kappa_max": round(float(np.max(ks)), 4),
        })
    with open(os.path.join(R2, "B3_calibration_sweep.json"), "w") as fh:
        json.dump({"variants": results,
                   "gold_rule_decisions": dict(
                       {k: sum(1 for v in gold.values() if v == k) for k in set(gold.values())})},
                  fh, indent=2)
    for r in results:
        print(f"{r['variant']:>18} veto {r['veto_share_overall']:.3f} hard {r['hard_veto_share']:.3f} "
              f"meanAa {r['mean_adequacy']:.3f} kappa {r['gold_kappa_mean']:.3f} "
              f"monotone {r['veto_monotone_in_severity']} decisions {r['decision_distribution']}")


if __name__ == "__main__":
    main()
