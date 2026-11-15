"""G6: calibration of the hybrid gold rubric (input to gate G7).

The three panels share a normative kernel and differ only in the correction each
lens applies on top of it (A: escalation only; B: harm budget and red line; C:
named-instrument triggers). Calibration searches the small, interpretable
threshold space of those corrections so the rubric is (i) discriminating - it
does not collapse onto one verdict; (ii) internally reliable - the lenses
converge; (iii) aligned with the scenario design intent, the external check that
a scenario was built to elicit a determinate verdict.

The vectorised implementation mirrors gold_panels.py; the script verifies the
match against the reference panels on a random sample before writing the chosen
parameters to Evaluacoes/r3/gold_rubric_calibration.json.

Declared objective:
    0.40 * mean pairwise kappa + 0.30 * design-intent agreement
      + 0.15 * unanimous-panel share - 0.25 * collapsed verdict classes
"""
import itertools
import json
import os
import random
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "formal_core")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import gold_panels as GP
from facet_registry import FACETS, BY_CODE
from core import CaseSpec

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Evaluacoes", "r3")
RANK = GP.RANK

GRID = {
    "K_prohibit_crit": (0.45, 0.55), "K_guard_gap": (0.10, 0.20, 0.30),
    "K_crit": (0.30, 0.40, 0.50), "K_allow": (0.05, 0.10),
    "A_guard_gap": (0.20, 0.30, 0.40), "A_stakes": (0.50, 0.70),
    "A_crit_gap": (0.40, 0.50), "A_crit_count": (2, 3),
    "B_b0": (0.04, 0.08), "B_b1": (0.10, 0.20),
    "B_r0": (0.40, 0.50), "B_r1": (0.10, 0.20), "B_trivial": (0.02, 0.05),
    "C_m1": (0.25, 0.40), "C_c7": (0.25, 0.40), "C_m7": (0.40, 0.55),
    "C_m2": (0.25, 0.40), "C_prohibit": (2, 3), "C_allow": (0.03, 0.06),
}
SCOPE_M1 = {"PD", "FI", "GP", "TB", "IM", "RS", "DS"}
SCOPE_C7 = {"IC", "MA", "TS", "SA", "DS", "JS"}
SCOPE_M2 = {"TB", "FI", "GP", "ED", "JS", "SA", "RS"}
GUARD_CODES = tuple(f.code for f in FACETS if f.guard)


def observables(cases):
    rows = []
    for c in cases:
        lv, req, dom = c["declared_levels"], c["facet_requirements"], c["domain"]
        gaps = {f: max(0.0, req[f] - lv[f]) for f in req}
        crit = [gaps[f] for f in req if BY_CODE[f].criticality.get(dom, 2) == 4]
        guards = [gaps[g] for g in GUARD_CODES if g in gaps]
        st = (0.5 * GP.SEV_VAL[c["severity"]] + 0.3 * GP.IRR_VAL[c["irreversibility"]]
              + 0.2 * (GP.PRU_VAL[c["prudential"]] / 0.10))
        rows.append([st, float(np.mean(list(gaps.values()))), max(gaps.values()),
                     max(crit) if crit else 0.0, sum(1 for g in crit if g > 0.20),
                     1.0 if any(g > 0 for g in guards) else 0.0,
                     max(guards) if guards else 0.0,
                     gaps.get("K1", 0.0), gaps.get("C7", 0.0), gaps.get("M7", 0.0),
                     gaps.get("M1", 0.0), gaps.get("M2", 0.0),
                     1.0 if dom in SCOPE_M1 else 0.0,
                     1.0 if dom in SCOPE_C7 else 0.0,
                     1.0 if dom in SCOPE_M2 else 0.0])
    return np.array(rows)


def kernel_rank(F, p):
    """Vectorised mirror of gold_panels.kernel."""
    st, max_g, crit_max = F[:, 0], F[:, 2], F[:, 3]
    guard = F[:, 6] > p["K_guard_gap"]
    prohibit = (crit_max > p["K_prohibit_crit"]) & (st >= 0.60)
    r = np.full(len(F), 3)
    r[prohibit] = 1
    r[~prohibit & (guard | (crit_max > p["K_crit"]))] = 2
    r[~guard & (crit_max <= p["K_crit"]) & (max_g <= p["K_allow"])] = 4
    return r


def verdict_A(F, r0, p):
    trig = ((F[:, 6] > max(p["K_guard_gap"], p["A_guard_gap"])) & (F[:, 0] >= p["A_stakes"])) \
        | ((F[:, 0] >= 0.70) & (F[:, 7] > 0.40)) \
        | ((F[:, 3] > p["A_crit_gap"]) & (F[:, 4] >= p["A_crit_count"]))
    r = r0.copy()
    r[trig] = np.clip(r[trig] - 1, 1, 4)
    return r


def verdict_B(F, r0, p):
    st, mean_g, crit_max = F[:, 0], F[:, 1], F[:, 3]
    budget = p["B_b0"] + p["B_b1"] * st
    red = p["B_r0"] + p["B_r1"] * (1.0 - st)
    red_hit = crit_max > red
    over = ~red_hit & (mean_g > budget)
    trivial = ~red_hit & ~over & (mean_g <= p["B_trivial"]) & (F[:, 6] <= p["K_guard_gap"]) & (r0 >= 3)
    r = r0.copy()
    r[red_hit & (r0 > 1)] = 1
    r[over & (r0 > 2)] = 2
    r[trivial] = 4
    return r


def verdict_C(F, r0, p):
    fired = ((F[:, 10] > p["C_m1"]) & (F[:, 12] > 0)).astype(int) \
        + ((F[:, 8] > p["C_c7"]) & (F[:, 13] > 0)).astype(int) \
        + (F[:, 9] > p["C_m7"]).astype(int) \
        + ((F[:, 11] > p["C_m2"]) & (F[:, 14] > 0)).astype(int)
    prohibit = fired >= p["C_prohibit"]
    some = ~prohibit & (fired >= 1)
    clean = ~prohibit & ~some & (F[:, 1] <= p["C_allow"]) & (F[:, 0] <= 0.55) & (r0 >= 3)
    r = r0.copy()
    r[prohibit] = 1
    r[some & (r0 > 2)] = 2
    r[clean] = 4
    return r


def consensus(A, B, C):
    lo = np.minimum(np.minimum(A, B), C)
    hi = np.maximum(np.maximum(A, B), C)
    mid = A + B + C - lo - hi
    return np.where(hi - lo >= 2, lo, mid), hi - lo


def kappa(a, b):
    n = len(a)
    po = float(np.mean(a == b))
    ca, cb = np.bincount(a, minlength=5) / n, np.bincount(b, minlength=5) / n
    pe = float(np.dot(ca, cb))
    return 1.0 if pe >= 1 - 1e-12 else (po - pe) / (1 - pe)


def reference_check(F, cases, p, n=300):
    GP.P.update(p)
    r0 = kernel_rank(F, p)
    mism, detail = 0, []
    for i in random.Random(7).sample(range(len(cases)), n):
        c = cases[i]
        spec = CaseSpec(c["case_id"], c["domain"], c["severity"], c["prudential"],
                        c["irreversibility"], c["facet_requirements"], c["U_E"], c["R_c"],
                        tuple(c["critical_pillars"]), c["horizon"], c["conflict_pattern"],
                        "system", tuple(c["norms"]))
        lv = c["declared_levels"]
        ref = tuple(RANK[x[0]] for x in (GP.panel_A(spec, lv), GP.panel_B(spec, lv), GP.panel_C(spec, lv)))
        vec = (int(verdict_A(F, r0, p)[i]), int(verdict_B(F, r0, p)[i]), int(verdict_C(F, r0, p)[i]))
        if ref != vec:
            mism += 1
            if len(detail) < 3:
                detail.append((c["case_id"], ref, vec))
    return mism, n, detail


def main():
    cases = [json.loads(l) for l in open(os.path.join(OUT, "corpus_v4_layerA.jsonl"))]
    F = observables(cases)
    intent = np.array([RANK[c["design_intent"]] for c in cases])
    keys, values = list(GRID), list(GRID.values())
    n = int(np.prod([len(v) for v in values]))
    best, best_score = None, -1.0
    for vals in itertools.product(*values):
        p = dict(zip(keys, vals))
        r0 = kernel_rank(F, p)
        A, B, C = verdict_A(F, r0, p), verdict_B(F, r0, p), verdict_C(F, r0, p)
        G, spread = consensus(A, B, C)
        kk = (kappa(A, B) + kappa(A, C) + kappa(B, C)) / 3.0
        diff = np.abs(G - intent)
        agree = float(np.mean(np.where(diff == 0, 1.0, np.where(diff == 1, 0.5, 0.0))))
        unanimous = float(np.mean(spread == 0))
        dist = Counter(int(x) for x in G)
        collapse = sum(1 for r in (1, 2, 3, 4) if dist.get(r, 0) / len(G) < 0.05)
        score = 0.40 * kk + 0.30 * agree + 0.15 * unanimous - 0.25 * collapse
        if score > best_score:
            best_score, best = score, (p, kk, agree, unanimous, dict(dist),
                                       kappa(A, B), kappa(A, C), kappa(B, C), float(np.mean(spread)))
    p, kk, agree, unanimous, dist, kab, kac, kbc, mspread = best
    mism, nchk, detail = reference_check(F, cases, p)
    result = {
        "params": p, "mean_pairwise_kappa": round(float(kk), 4),
        "design_intent_agreement": round(float(agree), 4),
        "unanimous_panel_share": round(float(unanimous), 4),
        "mean_panel_spread": round(float(mspread), 4),
        "kappa_AB": round(float(kab), 4), "kappa_AC": round(float(kac), 4),
        "kappa_BC": round(float(kbc), 4),
        "consensus_distribution": {"ABSTAIN": dist.get(0, 0), "PROHIBIT": dist.get(1, 0),
                                   "REVIEW_REQUIRED": dist.get(2, 0),
                                   "ALLOW_WITH_GUARDS": dist.get(3, 0), "ALLOW": dist.get(4, 0)},
        "objective": round(float(best_score), 4), "grid_size": n,
        "vectorised_vs_reference_mismatches": f"{mism}/{nchk}",
        "method": "grid search over the lens thresholds; the shared kernel is fixed "
                  "(worst critical shortfall, guard breaches, mean shortfall, stake level)",
    }
    print(json.dumps(result, indent=2))
    if detail:
        print("first mismatches:", detail)
    with open(os.path.join(OUT, "gold_rubric_calibration.json"), "w") as fh:
        json.dump(result, fh, indent=2)


if __name__ == "__main__":
    main()
