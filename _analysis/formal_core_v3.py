"""
ETH-WCMK formal core - version 3 (hierarchical-deficit formulation)

What this file does
-------------------
1. Verifies the geometry claims of the paper (Proposition 1: the centred unit
   embedding satisfies Eq.(1); relation between the Eq.(3) metric and the
   metric actually induced by the tetrahedron).
2. Replaces the current confrontation formula
        Aa = 1 - D * (1 + gamma*T) - rho*u
   with a formulation whose penalty terms are all *monotone in the deficits*
   and organised by the simplex's own cell structure
   (vertex -> edge -> face -> volume). This gives the "internal volume" of the
   paper a precise meaning and turns the hierarchical-consistency axiom of
   section 6.2 of the mathematical appendix into a checkable theorem.
3. Runs invariant/property tests over the simplex and reports violations.

Run:  python3 formal_core_v3.py
"""
from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass

PILLARS = ("W", "C", "M", "K")          # canonical order: Want Can Must Know
EDGES = list(itertools.combinations(range(4), 2))
FACES = list(itertools.combinations(range(4), 3))
CELLS = [(i,) for i in range(4)] + EDGES + FACES + [tuple(range(4))]

# ---------------------------------------------------------------- geometry
# Eq.(5) of paper v9: regular tetrahedron of edge 1 with W at the origin.
P_RAW = {
    "W": (0.0, 0.0, 0.0),
    "C": (1.0, 0.0, 0.0),
    "M": (0.5, math.sqrt(3) / 2, 0.0),
    "K": (0.5, math.sqrt(3) / 6, math.sqrt(2 / 3)),
}
CENTROID = tuple(sum(P_RAW[p][d] for p in PILLARS) / 4 for d in range(3))
R_CIRC = math.sqrt(3 / 8)               # circumradius of edge-1 tetrahedron = sqrt(6)/4

# Proposition 1: v_i = (P_i - g) / R  =>  |v_i| = 1, v_i . v_j = -1/3, sum = 0.
V_UNIT = {p: tuple((P_RAW[p][d] - CENTROID[d]) / R_CIRC for d in range(3)) for p in PILLARS}
V = [V_UNIT[p] for p in PILLARS]


def dot(u, w):
    return sum(a * b for a, b in zip(u, w))


def norm(u):
    return math.sqrt(dot(u, u))


def proposition_1():
    for v in V:
        assert abs(norm(v) - 1.0) < 1e-12
    for i, j in itertools.combinations(range(4), 2):
        assert abs(dot(V[i], V[j]) + 1 / 3) < 1e-12
    centroid = tuple(sum(V[i][d] for i in range(4)) / 4 for d in range(3))
    assert all(abs(c) < 1e-12 for c in centroid)
    edge = norm([V[0][d] - V[1][d] for d in range(3)])
    assert abs(edge - math.sqrt(8 / 3)) < 1e-12
    return edge


def simplex_point(a):
    """Barycentric embedding of a profile a (sum a_i = 1) in R^3."""
    return tuple(sum(a[i] * V[i][d] for i in range(4)) for d in range(3))


def d_induced(a, b):
    """Distance induced by the tetrahedron embedding: (2/sqrt(3)) * ||a-b||_2."""
    z = [a[i] - b[i] for i in range(4)]
    return (2 / math.sqrt(3)) * math.sqrt(sum(x * x for x in z))


def d_total_variation(a, b):
    """Eq.(3) of the paper: half the L1 distance (total variation)."""
    return 0.5 * sum(abs(a[i] - b[i]) for i in range(4))


# ---------------------------------------------------------------- volumes
def tetra_volume(p, q, r, s):
    u = [q[i] - p[i] for i in range(3)]
    v = [r[i] - p[i] for i in range(3)]
    w = [s[i] - p[i] for i in range(3)]
    det = (u[0] * (v[1] * w[2] - v[2] * w[1])
           - u[1] * (v[0] * w[2] - v[2] * w[0])
           + u[2] * (v[0] * w[1] - v[1] * w[0]))
    return abs(det) / 6.0


def barycentric_volume_shares(a):
    """
    share_i = Vol(x(a), face opposite vertex i) / Vol(tetrahedron).
    By the barycentric identity this equals a_i exactly: the profile point
    partitions the tetrahedron into four sub-tetrahedra whose volumes are
    proportional to the four pillar levels. This is the *only* defensible
    reading of "internal volume" in the paper.
    """
    x = simplex_point(a)
    total = tetra_volume(*V)
    shares = []
    for i in range(4):
        face = [V[j] for j in range(4) if j != i]
        shares.append(tetra_volume(x, *face) / total)
    return shares


def volumetric_coherence(a):
    """C_vol(a) = 4 * (prod a_i)^(1/4): 1 at the barycentre, 0 iff a pillar is 0."""
    p = 1.0
    for x in a:
        p *= max(0.0, x)
    return 4.0 * (p ** 0.25) if p > 0 else 0.0


def balance_coherence(a):
    """C_min(a) = 4 * min a_i: weakest-pillar coherence."""
    return 4.0 * min(max(0.0, x) for x in a)


# ---------------------------------------------------------------- deficits
@dataclass
class Params:
    gamma: float = 0.12     # edge (pairwise joint-deficiency) weight
    eta: float = 0.05       # face (triple joint-deficiency) weight
    omega: float = 0.03     # volume (quadruple joint-deficiency) weight
    rho: float = 0.15       # epistemic penalty weight
    alpha: float = 1.0 / 6  # uniform edge salience
    beta: float = 1.0 / 4   # uniform face salience
    theta: float = 0.15     # tolerance: deficits below this are not escalated
    phi: float = 0.5        # extra weight on critical pillars
    veto: float = 0.5       # hard veto: critical pillar at/above this relative deficit
    floor: float = 0.05     # irreducible-risk coefficient


def relative_deficits(a, r):
    """delta_i = max(0, r_i - a_i) / r_i  in [0,1]; 0 when the pillar is met."""
    return [max(0.0, r[i] - a[i]) / r[i] if r[i] > 0 else 0.0 for i in range(4)]


def unary(deficit, lam):
    return sum(lam[i] * deficit[i] for i in range(4))


def pairwise(deficit, p):
    return sum(p.alpha * min(deficit[i], deficit[j]) for i, j in EDGES)


def triple(deficit, p):
    return sum(p.beta * min(deficit[i], deficit[j], deficit[k]) for i, j, k in FACES)


def quadruple(deficit):
    d = 1.0
    for x in deficit:
        d *= x
    return d


def adequacy(a, r, lam, U_E, p=Params(), critical=()):
    """Hierarchical-deficit adequacy. Provably monotone: every term is
    non-decreasing in every deficit."""
    delta = relative_deficits(a, r)
    penalty = (unary(delta, lam)
               + p.gamma * pairwise(delta, p)
               + p.eta * triple(delta, p)
               + p.omega * quadruple(delta))
    if critical:
        penalty += sum(p.phi * max(0.0, delta[i] - p.theta) for i in critical)
    epistemic = p.rho * U_E * delta[3]
    total = penalty + epistemic
    return max(0.0, min(1.0, 1.0 - total)), delta, total


def hard_veto(delta, critical, p=Params()):
    """Lexicographic guard that the compensatory Aa can never cancel:
    a critical pillar failing beyond the veto level blocks the action."""
    return bool(critical) and max(delta[i] for i in critical) >= p.veto


def cell_deficit(cell, a, r):
    """Absolute unmet requirement of a simplex cell (sum over its vertices)."""
    return sum(max(0.0, r[i] - a[i]) for i in cell)


def cell_coherence(cell, delta):
    """Weakest-link coherence of a cell: 1 - max relative deficit inside it."""
    return 1.0 - max(delta[i] for i in cell)


def residual_risk(Aa, R_c, p=Params()):
    """R_r = R_c * (1 - Aa) + floor * R_c  -> never collapses to 0."""
    return R_c * (1.0 - Aa) + p.floor * R_c


def decision(Aa, R_r, R_c, p=Params(), veto=False):
    """Bands used by the bridge ontology. The veto is lexicographic: it cannot
    be bought back by a high compensatory adequacy."""
    if veto:
        return "prohibit"
    if R_r >= 0.5 * R_c or Aa < 0.45:
        return "prohibit"
    if R_r >= 0.30 * R_c or Aa < 0.60:
        return "review"
    if R_r >= 0.15 * R_c or Aa < 0.75:
        return "conditional"
    return "allow"


# ---------------------------------------------------------------- legacy variant (for comparison)
def adequacy_v2(a, r, lam, U_E, gamma=0.15, rho=0.20, theta=0.15, phi=0.5, critical=()):
    """The form currently implemented in formal_core.py (deficit amplifier by tension)."""
    d = [max(0.0, r[i] - a[i]) for i in range(4)]
    D = sum(lam[i] * d[i] for i in range(4))
    s = [min(0.0, a[i] - r[i]) for i in range(4)]
    T = sum((1 / 6) * abs(s[i] - s[j]) for i, j in EDGES)
    u = U_E * max(0.0, (r[3] - a[3]) / r[3]) if r[3] > 0 else 0.0
    raw = 1 - D * (1 + gamma * T) - rho * u
    if critical:
        raw -= phi * sum(max(0.0, d[i] - theta) for i in critical)
    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------- invariant tests
def random_simplex(rng, n=4):
    xs = [rng.random() for _ in range(n)]
    s = sum(xs)
    return [x / s for x in xs]


def invariant_tests(n=20000, seed=7, variant="v3"):
    rng = random.Random(seed)
    fails = {}
    stats = {"cases": 0, "veto_present": 0, "veto_present_but_adequacy_high": 0}
    for _ in range(n):
        r = random_simplex(rng)
        a = random_simplex(rng)
        lam = random_simplex(rng)
        U_E = rng.random()
        R_c = rng.random()
        critical = tuple(i for i in range(4) if r[i] > 0.30)
        delta = relative_deficits(a, r)
        if variant == "v3":
            Aa, delta, pen = adequacy(a, r, lam, U_E, critical=critical)
            Rr = residual_risk(Aa, R_c)
        else:
            Aa = adequacy_v2(a, r, lam, U_E, critical=critical)
            Rr = R_c * (1 - Aa)

        def record(name, cond, sample):
            if not cond:
                fails.setdefault(name, [0, sample])
                fails[name][0] += 1

        record("bounds", 0.0 <= Aa <= 1.0, (a, r, lam, Aa))
        record("perfect_adequacy", (all(d <= 1e-12 for d in delta) and Aa >= 1.0 - 1e-9)
                                 or not all(d <= 1e-12 for d in delta), (a, r, Aa, delta))
        record("risk_band", 0.0 <= Rr <= (1.0 + 0.05) * R_c + 1e-12, (Aa, R_c, Rr))
        record("risk_floor", Rr >= 0.05 * R_c - 1e-12, (Aa, R_c, Rr))
        record("veto_guard",
              (not hard_veto(delta, critical))
              or decision(Aa, Rr, R_c, veto=hard_veto(delta, critical)) == "prohibit",
              (Aa, delta, critical))
        # no-free-lunch: capacity moved from a deficient pillar to a surplus one
        # must never increase adequacy
        ok = True
        for i in range(4):
            for j in range(4):
                if i == j:
                    continue
                if a[i] < r[i] and a[j] > r[j]:
                    eps = min(r[i] - a[i], a[j] - r[j], 0.05)
                    if eps <= 1e-9:
                        continue
                    a2 = list(a)
                    a2[i] -= eps
                    a2[j] += eps
                    if variant == "v3":
                        Aa2 = adequacy(a2, r, lam, U_E, critical=critical)[0]
                    else:
                        Aa2 = adequacy_v2(a2, r, lam, U_E, critical=critical)
                    if Aa2 > Aa + 1e-12:
                        ok = False
                        break
            if not ok:
                break
        record("monotonicity", ok, (a, r, lam, U_E, Aa))
        # volume degeneracy: coherence is 0 iff at least one pillar is 0
        record("volume_degeneracy",
              (volumetric_coherence(a) < 1e-9) == (min(a) < 1e-9), a)
        # Hierarchical-consistency axiom (paper 6.2), stated so it is falsifiable:
        #   (a) deficit accumulation: the unmet requirement of a cell is the SUM of
        #       the vertex deficits inside it, hence monotone under inclusion.
        #   (b) weakest link: a composite cell is never more coherent than any of
        #       its sub-cells.
        nested = [(s, t) for s in CELLS for t in CELLS
                  if set(s) < set(t) and len(t) == len(s) + 1]
        record("hier_deficit_monotone",
              all(cell_deficit(t, a, r) >= cell_deficit(s, a, r) - 1e-12 for s, t in nested), a)
        record("hier_weakest_link",
              all(cell_coherence(t, delta) <= cell_coherence(s, delta) + 1e-12
                  for s, t in nested), a)
        record("veto_guard",
              decision(Aa, Rr, R_c, veto=hard_veto(delta, critical)) == "prohibit"
              if hard_veto(delta, critical) else True,
              (a, r, lam, Aa, delta, critical))
        # Diagnostic (not a failure): how often a compensatory Aa would *hide*
        # a lexicographic veto. This is the empirical argument for the veto.
        if hard_veto(delta, critical) and Aa >= 0.60:
            stats["veto_present_but_adequacy_high"] += 1
        if hard_veto(delta, critical):
            stats["veto_present"] += 1
        # AM-GM balance index of every cell is in [0,1] and =1 iff cell is balanced
        def balance(idx):
            m = sum(a[i] for i in idx)
            if m <= 0:
                return 0.0
            return len(idx) * (math.prod(a[i] for i in idx) ** (1.0 / len(idx))) / m
        record("balance_bounds", 0.0 <= balance(range(4)) <= 1.0 + 1e-9
                             and all(0.0 <= balance(c) <= 1.0 + 1e-9 for c in EDGES + FACES), a)
        record("amgm_volume_balance", volumetric_coherence(a) <= balance(range(4)) + 1e-9, (a,))
        record("shares_equal_profile",
              all(abs(s - a[i]) < 1e-9 for i, s in enumerate(barycentric_volume_shares(a))), a)
        stats["cases"] += 1
    return fails, stats


def show_metric_relation():
    rng = random.Random(1)
    lo = hi = None
    for _ in range(50000):
        a, b = random_simplex(rng), random_simplex(rng)
        tv, ed = d_total_variation(a, b), d_induced(a, b)
        if tv > 1e-9:
            ratio = ed / tv
            lo = ratio if lo is None else min(lo, ratio)
            hi = ratio if hi is None else max(hi, ratio)
    return lo, hi, 2 / math.sqrt(3), 4 / math.sqrt(3)


if __name__ == "__main__":
    print("Proposition 1 holds:", proposition_1(), "(edge of unit embedding = sqrt(8/3))")
    lo, hi, l0, h0 = show_metric_relation()
    print(f"d_induced / d_total_variation  observed [{lo:.4f}, {hi:.4f}]  theory [{l0:.4f}, {h0:.4f}]")
    a = (0.40, 0.30, 0.20, 0.10)
    print("volume shares of a=(.4,.3,.2,.1):", [round(x, 4) for x in barycentric_volume_shares(a)])
    print("C_vol(barycentre) =", volumetric_coherence((.25, .25, .25, .25)),
          "| C_vol(degenerate) =", volumetric_coherence((.4, .3, .3, 0.0)))

    results = {"geometry": {"proposition_1_edge": proposition_1(),
                            "metric_ratio_observed": [lo, hi],
                            "metric_ratio_theory": [l0, h0]}}
    for variant in ("v2", "v3"):
        fails, stats = invariant_tests(variant=variant)
        results[variant] = {"violations": {k: v[0] for k, v in fails.items()},
                            "examples": {k: v[1] for k, v in fails.items()},
                            "stats": stats}
        print(f"\ninvariants, {variant} (20000 random cases):")
        if not fails:
            print("  no violations")
        for k, (n, sample) in fails.items():
            print(f"  {k}: {n} violations  e.g. {sample}")
        print("  stats:", stats)

    # worked example: same case, two profiles
    r = (0.20, 0.25, 0.35, 0.20)
    lam = (0.15, 0.20, 0.45, 0.20)
    profiles = {
        "Balanced": (0.25, 0.25, 0.25, 0.25),
        "Capable but unaccountable": (0.20, 0.45, 0.15, 0.20),
        "Normatively strong, weak on means": (0.20, 0.15, 0.45, 0.20),
        "Intent-only (aspiring)": (0.50, 0.15, 0.20, 0.15),
    }
    print("\nconfrontation of one case against four profiles (R_c=0.6, U_E=0.35):")
    for name, a in profiles.items():
        Aa, delta, pen = adequacy(a, r, lam, 0.35, critical=(2, 3))
        print(f"  {name:28s} Aa={Aa:.4f} R_r={residual_risk(Aa,0.6):.4f} "
            f"delta={[round(x,3) for x in delta]} decision={decision(Aa, residual_risk(Aa,0.6), 0.6)}")
