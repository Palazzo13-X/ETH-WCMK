"""Batteries B4-B8 (phase F5).

B4  parameter sensitivity: first-order Sobol indices (Monte-Carlo conditional
    variance estimator) plus Morris elementary effects. Pure numpy.
B5  gold agreement: formal-core decisions against two independent documented
    adjudication panels and their consensus; Cohen's kappa, ordinal agreement,
    Spearman rho, confusion matrix, per-severity breakdown.
B6  profile-inference robustness: decision stability under three noise models.
B7  baseline comparison: severity filter, v9 compensatory mean as published,
    veto-only, and the full v10 core, scored against the panels.
B8  adversarial probes: every probe carries explicit assertions the core must
    satisfy.

Outputs: Evaluacoes/r2/B4_results.json, B5_results.json, B6_results.json,
         B7_results.json, B8_results.json
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "corpus")))

from facet_registry import FACETS, BY_CODE
from core import (default_calibration, CaseSpec, Profile, confront, project)
from gold_panels import cohens_kappa, RANK

R2 = os.path.abspath(os.path.join(HERE, "..", "..", "Evaluacoes", "r2"))
SEED = 20261031
rng = np.random.default_rng(SEED)


def load(name):
    with open(os.path.join(R2, name)) as fh:
        return [json.loads(line) for line in fh]


CASES = load("corpus_v3_cases.jsonl")
PROFILES = load("corpus_v3_profiles.jsonl")
GOLD = load("corpus_v3_gold.jsonl")
PROBES = load("corpus_v3_probes.jsonl")
SPLIT = json.load(open(os.path.join(R2, "corpus_v3_split.json")))
CASE_BY_ID = {c["case_id"]: c for c in CASES}
PROFILE_BY_ID = {p["profile_id"]: Profile(p["profile_id"], p["levels"], p["confidence"])
                 for p in PROFILES}
PROFILES12 = [PROFILE_BY_ID[p["profile_id"]] for p in PROFILES[:12]]
CAL = default_calibration()


def spec_of(c):
    return CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                    c["irreversibility"], c["requirements"], c["epistemic_uncertainty"],
                    c["contextual_risk"], tuple(c["critical_pillars"]))


TEST_SPECS = [spec_of(CASE_BY_ID[i]) for i in SPLIT["test"]]

# ------------------------------------------------------------------ B4 sensitivity
PARAMS = ("lam_W", "lam_C", "lam_M", "gamma", "eta", "omega", "rho", "theta")
RANGES = {"lam_W": (0.20, 0.40), "lam_C": (0.20, 0.40), "lam_M": (0.20, 0.40),
          "gamma": (0.05, 0.20), "eta": (0.02, 0.10), "omega": (0.00, 0.08),
          "rho": (0.05, 0.25), "theta": (0.45, 0.80)}


def make_cal(draw):
    lw, lc, lm = draw[0], draw[1], draw[2]
    lk = 1.0 - lw - lc - lm
    if lk < 0.05 or lk > 0.45:
        return None
    g, e, o, r = draw[3], draw[4], draw[5], draw[6]
    if g + e + o + r > 0.35:
        return None
    th = draw[7]
    return Calibration_(lw, lc, lm, lk, g, e, o, r, th)


def Calibration_(lw, lc, lm, lk, g, e, o, r, th):
    from core import Calibration
    return Calibration(lam=(lw, lc, lm, lk), alpha=(1 / 6,) * 6, beta_face=(1 / 4,) * 4,
                       gamma=g, eta=e, omega=o, rho=r,
                       theta=(th + 0.05, th, th, th + 0.05), hard_veto_delta=0.15)


def adequacy_mean(cal, specs, profiles):
    tot, n = 0.0, 0
    for s in specs:
        for p in profiles:
            r = confront(s, p, cal)
            if r["adequacy"] is not None:
                tot += r["adequacy"]
                n += 1
    return tot / max(1, n)


def sobol_and_morris(n=2048, probe_cases=60, n_profiles=4):
    specs = TEST_SPECS[:probe_cases]
    profiles = PROFILES12[:n_profiles]
    draws, y = [], []
    rejected = 0
    while len(y) < n:
        d = np.array([RANGES[p][0] + rng.random() * (RANGES[p][1] - RANGES[p][0])
                      for p in PARAMS])
        if make_cal(d) is None:
            rejected += 1
            continue
        draws.append(d)
        y.append(adequacy_mean(make_cal(d), specs, profiles))
    Y = np.array(y)
    D = np.array(draws)
    var = float(np.var(Y))
    mean = float(np.mean(Y))
    S1 = {}
    for k, p in enumerate(PARAMS):
        nb = 16
        bins = np.floor((D[:, k] - RANGES[p][0]) / (RANGES[p][1] - RANGES[p][0]) * nb)
        bins = bins.astype(int)
        cond_var = 0.0
        for b in range(nb):
            idx = np.where(bins == b)[0]
            if len(idx) >= 4:
                cond_var += len(idx) * (np.mean(Y[idx]) - mean) ** 2
        cond_var /= len(Y)
        S1[p] = round(max(0.0, cond_var) / var, 4) if var > 1e-9 else 0.0
    effects = {p: [] for p in PARAMS}
    for _ in range(60):
        while True:
            base = np.array([RANGES[p][0] + rng.random() * (RANGES[p][1] - RANGES[p][0])
                             for p in PARAMS])
            if make_cal(base) is not None:
                break
        prev = adequacy_mean(make_cal(base), specs[:20], PROFILES12[:1])
        for k in range(len(PARAMS)):
            step = (RANGES[PARAMS[k]][1] - RANGES[PARAMS[k]][0]) / 6.0
            alt = base.copy()
            alt[k] = min(RANGES[PARAMS[k]][1], base[k] + step)
            cal_alt = make_cal(alt)
            if cal_alt is None:
                continue
            cur = adequacy_mean(cal_alt, specs[:20], PROFILES12[:1])
            effects[PARAMS[k]].append(abs(cur - prev) / step)
    morris = {p: round(float(np.mean(v)), 4) for p, v in effects.items() if v}
    return {"n_valid_draws": n, "rejected_invalid_draws": rejected,
            "response_mean": round(mean, 4), "response_std": round(float(np.std(Y)), 4),
            "sobol_first_order": S1,
            "sobol_sum_first_order": round(float(sum(S1.values())), 4),
            "morris_mean_abs_elementary_effect": morris,
            "ranking_sobol": sorted(S1, key=lambda k: -S1[k]),
            "ranking_morris": sorted(morris, key=lambda k: -morris[k])}


# ------------------------------------------------------------------ B5 gold
def ordinal_stats(model, panel):
    diffs = [abs(RANK[a] - RANK[b]) for a, b in zip(model, panel)]
    rm = [RANK[a] for a in model]
    rp = [RANK[b] for b in panel]
    n = len(model)
    mx = sum(rm) / n
    my = sum(rp) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rm, rp))
    den = (sum((a - mx) ** 2 for a in rm) * sum((b - my) ** 2 for b in rp)) ** 0.5
    return {"mean_abs_rank_difference": round(sum(diffs) / n, 4),
            "within_one_rank": round(sum(1 for d in diffs if d <= 1) / n, 4),
            "model_stricter_than_panel": round(sum(1 for a, b in zip(model, panel)
                                                  if RANK[a] < RANK[b]) / n, 4),
            "model_more_permissive": round(sum(1 for a, b in zip(model, panel)
                                              if RANK[a] > RANK[b]) / n, 4),
            "spearman_rho": round(num / den if den else 0.0, 4)}


def collapse(dec):
    if dec in ("ALLOW", "ALLOW_WITH_GUARDS"):
        return "PERMISSIVE"
    if dec == "REVIEW_REQUIRED":
        return "DELIBERATIVE"
    return "RESTRICTIVE"


def block(m, p):
    cats = sorted(set(m) | set(p))
    conf = {a: {b: sum(1 for x, y in zip(m, p) if x == a and y == b) for b in cats}
            for a in cats}
    return {"exact_agreement": round(sum(1 for x, y in zip(m, p) if x == y) / len(m), 4),
            "cohens_kappa": round(cohens_kappa(m, p), 4),
            "ordinal": ordinal_stats(m, p),
            "collapsed_kappa_three_band": round(
                cohens_kappa([collapse(x) for x in m], [collapse(y) for y in p]), 4),
            "confusion_matrix_model_rows": conf}


def gold_agreement():
    model, A, B, cons = [], [], [], []
    for g in GOLD:
        sp = spec_of(CASE_BY_ID[g["case_id"]])
        pr = PROFILE_BY_ID[g["profile_id"]]
        model.append(confront(sp, pr, CAL)["decision"])
        A.append(g["panelA"])
        B.append(g["panelB"])
        cons.append(g["gold_decision"])
    by_sev = {}
    for sev in ("low", "medium", "high", "critical"):
        m = [x for x, g in zip(model, GOLD) if g["severity"] == sev]
        c = [g["gold_decision"] for g in GOLD if g["severity"] == sev]
        a = [g["panelA"] for g in GOLD if g["severity"] == sev]
        b = [g["panelB"] for g in GOLD if g["severity"] == sev]
        by_sev[sev] = {"n": len(m),
                       "agreement_consensus": round(sum(1 for x, y in zip(m, c) if x == y)
                                                   / len(m), 4),
                       "kappa_consensus": round(cohens_kappa(m, c), 4),
                       "kappa_panelA": round(cohens_kappa(m, a), 4),
                       "kappa_panelB": round(cohens_kappa(m, b), 4)}
    return {"n_pairs": len(model),
            "model_vs_panelA": block(model, A),
            "model_vs_panelB": block(model, B),
            "model_vs_consensus": block(model, cons),
            "panelA_vs_panelB": block(A, B),
            "by_severity": by_sev,
            "decision_distribution": {c: model.count(c) / len(model) for c in set(model)},
            "panelA_distribution": {c: A.count(c) / len(A) for c in set(A)},
            "panelB_distribution": {c: B.count(c) / len(B) for c in set(B)},
            "consensus_distribution": {c: cons.count(c) / len(cons) for c in set(cons)}}


# ------------------------------------------------------------------ B6 robustness
def noise(name, value, code, r):
    if name == "self_report_optimism":
        return max(0.0, min(1.0, value + 0.10))
    if name == "calibration_drift":
        return max(0.0, min(1.0, value + r.normal(0, 0.10)))
    if name == "adversarial_inflation":
        bump = 0.15 if BY_CODE[code].primary_pillar() == "K" else 0.05
        return max(0.0, min(1.0, value + bump))
    return value


def robustness():
    out = {}
    for name in ("self_report_optimism", "calibration_drift", "adversarial_inflation"):
        flips = 0
        total = 0
        shifts = []
        for seed in range(5):
            r = np.random.default_rng(SEED + seed)
            for p in PROFILES12:
                noisy = {f.code: noise(name, p.facet_scores[f.code], f.code, r) for f in FACETS}
                npf = Profile(p.profile_id, noisy, p.confidence)
                for cs in TEST_SPECS[:20]:
                    base = confront(cs, p, CAL)
                    alt = confront(cs, npf, CAL)
                    total += 1
                    if base["decision"] != alt["decision"]:
                        flips += 1
                    shifts.append(abs(base["adequacy"] - alt["adequacy"]))
        out[name] = {"n_confrontations": total,
                     "decision_stability": round(1 - flips / total, 4),
                     "mean_abs_adequacy_shift": round(float(np.mean(shifts)), 4),
                     "p95_abs_adequacy_shift": round(float(np.percentile(shifts, 95)), 4)}
    return out


# ------------------------------------------------------------------ B7 baselines
def v9_adequacy(case, profile):
    """Adequacy exactly as published in v9 (Eq. 8-11): unnormalised pillar sums,
    compensatory tension, no veto, no risk floor."""
    sums = [0.0] * 4
    den = [0.0] * 4
    for f in FACETS:
        v = profile.facet_scores.get(f.code)
        if v is None:
            continue
        for i, b in enumerate(f.beta):
            if b > 0:
                sums[i] += b * f.weight * v
                den[i] += b * f.weight
    a = [sums[i] / den[i] if den[i] else 0.0 for i in range(4)]
    q, _ = project(case.facet_requirements, FACETS)
    d = [max(0.0, q[i] - a[i]) for i in range(4)]
    D = sum(0.30 * d[i] for i in range(4))
    T = 0.0
    for i in range(4):
        for j in range(i + 1, 4):
            T += abs((a[i] - q[i]) - (a[j] - q[j])) / 6.0
    u = case.U_E * (1 - a[3])
    return max(0.0, min(1.0, 1.0 - D - 0.12 * T - 0.15 * u))


def severity_filter(case):
    if case.severity == "critical" or (case.severity == "high"
                                       and case.irreversibility == "irreversible"):
        return "PROHIBIT"
    if case.severity == "high":
        return "REVIEW_REQUIRED"
    if case.severity == "medium":
        return "ALLOW_WITH_GUARDS"
    return "ALLOW"


def veto_only(case, profile, cal):
    from core import PILLARS
    ell, _ = project(profile.facet_scores, FACETS, cap_guards=True)
    q, _ = project(case.facet_requirements, FACETS)
    d = [max(0.0, q[i] - ell[i]) for i in range(4)]
    crit = [i for i in range(4) if PILLARS[i] in case.critical_pillars]
    if any(d[i] >= cal.theta[i] + cal.hard_veto_delta or d[i] >= 0.75 for i in crit):
        return "PROHIBIT"
    if any(d[i] >= cal.theta[i] for i in crit):
        return "REVIEW_REQUIRED"
    return "ALLOW"


def baselines():
    out = {}
    for name in ("severity_filter", "v9_compensatory_mean", "veto_only", "v10_core"):
        model, cons = [], []
        for g in GOLD:
            sp = spec_of(CASE_BY_ID[g["case_id"]])
            pr = PROFILE_BY_ID[g["profile_id"]]
            if name == "severity_filter":
                dec = severity_filter(sp)
            elif name == "veto_only":
                dec = veto_only(sp, pr, CAL)
            elif name == "v9_compensatory_mean":
                aa = v9_adequacy(sp, pr)
                dec = ("PROHIBIT" if aa <= 0.45 else "REVIEW_REQUIRED" if aa <= 0.60
                       else "ALLOW_WITH_GUARDS" if aa <= 0.78 else "ALLOW")
            else:
                dec = confront(sp, pr, CAL)["decision"]
            model.append(dec)
            cons.append(g["gold_decision"])
        out[name] = {"agreement_consensus": round(sum(1 for x, y in zip(model, cons)
                     if x == y) / len(model), 4),
                     "kappa_consensus": round(cohens_kappa(model, cons), 4),
                     "ordinal": ordinal_stats(model, cons),
                     "decision_distribution": {c: model.count(c) / len(model)
                                              for c in set(model)}}
    return out


# ------------------------------------------------------------------ B8 probes
def evaluate_probes():
    results = {"total": len(PROBES), "passed": 0, "failed": 0, "by_kind": {}, "failures": []}
    ladder_values = {}
    for prb in PROBES:
        c = prb["case"]
        sp = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                      c["irreversibility"], c["requirements"], c["epistemic_uncertainty"],
                      c["contextual_risk"], tuple(c["critical_pillars"]))
        prof = Profile("probe-agent", prb["profile_levels"], 0.8)
        r = confront(sp, prof, CAL)
        ok_all = True
        for a in prb["asserts"]:
            kind = a["kind"]
            if kind == "ladder_monotone":
                ladder_values[c["case_id"]] = r["adequacy"]
                continue
            if kind == "decision":
                ok = r["decision"] == a["value"]
            elif kind == "decision_not":
                ok = r["decision"] not in a["value"]
            elif kind == "adequacy":
                ok = abs(r["adequacy"] - a["value"]) <= a.get("tol", 1e-4)
            elif kind == "adequacy_range":
                ok = a["lo"] <= r["adequacy"] <= a["hi"]
            elif kind == "adequacy_less_than":
                ok = r["adequacy"] < a["value"]
            elif kind == "adequacy_raw_at_least":
                ok = r["adequacy_raw"] >= a["value"]
            elif kind == "deficit":
                idxp = ({"W": 0, "C": 1, "M": 2, "K": 3})[a["pillar"]]
                val = r["deficits"][idxp]
                if a["op"] == "ge":
                    ok = val >= a["value"] - 1e-6
                elif a["op"] == "le":
                    ok = val <= a["value"] + 1e-6
                else:
                    ok = abs(val - a["value"]) <= a.get("tol", 1e-3)
            elif kind == "veto":
                ok = set(a["contains"]) <= set(r["veto"])
            elif kind == "veto_empty":
                ok = not r["veto"]
            elif kind == "hard_veto_nonempty":
                ok = bool(r["hard_veto"])
            elif kind == "guard_failures_include":
                ok = set(a["value"]) <= {g["facet"] for g in r["guard_failures"]}
            elif kind == "facet_exposure_at_least":
                ok = r.get("facet_exposure", 0.0) >= a["value"]
            elif kind == "risk_floor_positive":
                ok = r["sigma"] > 0 and r["R_r"] >= r["sigma"] * r["R_c"] - 1e-9
            else:
                ok = False
            if not ok:
                ok_all = False
                results["failures"].append({"probe": prb["probe_id"], "kind": prb["kind"],
                                           "assertion": a, "decision": r["decision"],
                                           "adequacy": r["adequacy"],
                                           "deficits": [round(x, 4) for x in r["deficits"]]})
        results["by_kind"].setdefault(prb["kind"], {"n": 0, "pass": 0})
        results["by_kind"][prb["kind"]]["n"] += 1
        results["by_kind"][prb["kind"]]["pass"] += 1 if ok_all else 0
        results["passed"] += 1 if ok_all else 0
        results["failed"] += 0 if ok_all else 1

    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    fam = {}
    for cid, aa in ladder_values.items():
        fam.setdefault(cid.split("-")[2], []).append((order[cid.split("-")[-1]], aa))
    results["severity_ladder_families"] = len(fam)
    results["severity_ladder_monotone"] = all(
        all(b[1] <= a[1] + 1e-9 for a, b in zip(v, v[1:])) for v in fam.values())
    edges = []
    for prb in PROBES:
        if prb["kind"] != "threshold_edge":
            continue
        c = prb["case"]
        sp = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                      c["irreversibility"], c["requirements"], c["epistemic_uncertainty"],
                      c["contextual_risk"], tuple(c["critical_pillars"]))
        r = confront(sp, Profile("probe-agent", prb["profile_levels"], 0.8), CAL)
        edges.append({"probe": prb["probe_id"], "deficit_M": round(r["deficits"][2], 5),
                      "veto": bool(r["veto"]), "decision": r["decision"]})
    results["threshold_edges_below_veto"] = sum(1 for e in edges if not e["veto"])
    results["threshold_edges_above_veto"] = sum(1 for e in edges if e["veto"])
    results["threshold_edges_sample"] = edges[:6]
    return results


def main():
    out = {"seed": SEED,
           "calibration": "v10 default: theta (0.65,0.60,0.60,0.65), stakes-aware bar"}
    out["B4"] = sobol_and_morris()
    out["B5"] = gold_agreement()
    out["B6"] = robustness()
    out["B7"] = baselines()
    out["B8"] = evaluate_probes()
    for name, payload in out.items():
        with open(os.path.join(R2, f"{name}_results.json"), "w") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    return out


if __name__ == "__main__":
    res = main()
    print(json.dumps(res["B4"], indent=1))
    for key in ("model_vs_panelA", "model_vs_panelB", "model_vs_consensus",
                "panelA_vs_panelB"):
        b = res["B5"][key]
        print(key, b["exact_agreement"], b["cohens_kappa"], b["collapsed_kappa_three_band"],
            b["ordinal"])
    print(json.dumps(res["B7"], indent=1))
    print(json.dumps(res["B8"]["by_kind"], indent=1))
    print(json.dumps(res["B6"], indent=1))
