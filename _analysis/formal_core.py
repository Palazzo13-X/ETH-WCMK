"""
ETH-WCMK formal core — reference implementation (v2-corrected)
Implements the corrected formal layer of §6 of the paper and the six
invariants proposed in the critical analysis.

Pure stdlib + numpy. Run:  python3 formal_core.py
"""
from __future__ import annotations
import itertools
import math
import random
from dataclasses import dataclass

VILLARS = ("W", "C", "M", "K")

# ---------------------------------------------------------------- geometry
P_RAW = {                                   # Eq.(5) of paper v9 (edge 1, W at origin)
    "W": (0.0, 0.0, 0.0),
    "C": (1.0, 0.0, 0.0),
    "M": (0.5, math.sqrt(3) / 2, 0.0),
    "K": (0.5, math.sqrt(3) / 6, math.sqrt(2 / 3)),
}
CENTROID = tuple(sum(P_RAW[i][d] for i in VILLARS) / 4 for d in range(3))
R_CIRC = math.sqrt(3 / 8)
V_UNIT = {i: tuple((P_RAW[i][d] - CENTROID[d]) / R_CIRC for d in range(3)) for i in VILLARS}


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def norm(u):
    return math.sqrt(dot(u, u))


def check_geometry():
    """Proposition 1: the paper's coordinates, centred and rescaled, satisfy Eq.(1)."""
    assert abs(sum(sum(V_UNIT[i][d] for i in VILLARS) for d in range(3))) < 1e-12
    for i in VILLARS:
        assert abs(norm(V_UNIT[i]) - 1.0) < 1e-12
    for i, j in itertools.combinations(VILLARS, 2):
        assert abs(dot(V_UNIT[i], V_UNIT[j]) + 1 / 3) < 1e-12
    for i, j in itertools.combinations(VILLARS, 2):
        assert abs(norm([a - b for a, b in zip(V_UNIT[i], V_UNIT[j])]) - math.sqrt(8 / 3)) < 1e-12
    return True


def barycentric_point(a):
    return tuple(sum(a[i] * V_UNIT[v][d] for i, v in enumerate(VILLARS)) for d in range(3))


def euclidean_on_simplex(a, b):
    """Distance induced by the tetrahedron embedding: (2/sqrt(3)) * ||a-b||_2."""
    return (2 / math.sqrt(3)) * math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(4)))


def tv_distance(a, b):
    """d_Delta of Eq.(3): half L1. Max = 1 (opposite vertices)."""
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


def volume_shares(a):
    """Barycentric identity: share_i = Vol(x(a), face_opposite_i) / Vol(tetra)."""
    x = barycentric_point(a)
    total = tetra_volume(*[V_UNIT[v] for v in VILLARS])
    shares = []
    for i, v in enumerate(VILLARS):
        face = [V_UNIT[u] for u in VILLARS if u != v]
        shares.append(tetra_volume(x, *face) / total)
    return shares


def volumetric_coherence(a):
    """V(a) = 4 * (prod a_i)^(1/4) in [0,1]; 1 at the barycentre, 0 if any pillar is 0."""
    p = 1.0
    for x in a:
        p *= x
    return 4.0 * (p ** 0.25) if p > 0 else 0.0


def balance_coherence(a):
    """B(a) = 4 * min a_i — the weakest-pillar measure."""
    return 4.0 * min(a)


# ---------------------------------------------------------------- scoring
@dataclass
class Case:
    r: tuple                    # requirement vector, sums to 1
    lam: tuple                  # salience vector, sums to 1
    U_E: float                  # case uncertainty in [0,1]
    R_c: float                  # contextual severity in [0,1]
    critical: tuple = ()        # pillars flagged critical for the domain
    theta: float = 0.15         # critical-deficit threshold
    phi: float = 0.25          # extra penalty for a critical deficit
    sigma: float = 0.10        # prudential floor on residual risk

def _norm(v):
    s = sum(v)
    return tuple(x / s for x in v)

def deficits(case, a):
    return tuple(max(0.0, case.r[i] - a[i]) for i in range(4))

def weighted_deficit(case, a):
    lam = _norm(case.lam)
    D = sum(lam[i] * deficits(case, a)[i] for i in range(4))
    crit = sum(case.phi * (1.0 if d > case.theta else 0.0)
               for i, d in enumerate(deficits(case, a)) if VILLARS[i] in case.critical)
    return D + crit

def profile_tension(case, a, alpha=1.0 / 6.0):
    """Dispersion of NEGATIVE slacks only: excess capacity is never punished.
    With alpha=1/6 the term is bounded in [0,1] (proven bound: 6 * alpha)."""
    s = [min(0.0, a[i] - case.r[i]) for i in range(4)]
    T = sum(alpha * abs(s[i] - s[j]) for i in range(4) for j in range(i + 1, 4))
    return min(1.0, T)

def epistemic_penalty(case, a, U_E=None):
    """Single count of the Know shortfall, scaled by case uncertainty."""
    U = U_E if U_E is not None else case.U_E
    r_K = case.r[3]
    if r_K <= 1e-9:
        return 0.0
    return U * max(0.0, r_K - a[3]) / r_K

def adequacy(case, a, gamma=0.20, rho=0.15):
    """v2: tension acts as an AMPLIFIER of the deficit, never as an independent
    penalty. Excess capacity is therefore never punished."""
    D = weighted_deficit(case, a)
    raw = 1.0 - D * (1.0 + gamma * profile_tension(case, a)) - rho * epistemic_penalty(case, a)
    return max(0.0, min(1.0, raw))

def adequacy_v9(case, a, gamma=0.20, rho=0.15):
    """v9 as written in the paper: T over ALL slacks, u = U_E(1-k). Kept only
    to demonstrate the defects (double counting of Know, punishment of surplus)."""
    s = [a[i] - case.r[i] for i in range(4)]
    T = sum((1 / 6) * abs(s[i] - s[j]) for i in range(4) for j in range(i + 1, 4))
    D = sum(case.lam[i] * max(0.0, case.r[i] - a[i]) for i in range(4))
    u = case.U_E * (1.0 - a[3])
    return max(0.0, min(1.0, 1.0 - D - gamma * T - rho * u))

def residual_risk_v9(case, a):
    return case.R_c * (1.0 - adequacy_v9(case, a))

def residual_risk(case, a, eta=0.90):
    """Attenuation WITHOUT erasure: even at Aa = 1, a prudential floor survives."""
    Aa = adequacy(case, a)
    floor = case.sigma * case.R_c
    return max(case.R_c * (1.0 - eta * Aa), floor)

def decision(case, a, t_block=0.20, t_restrict=0.40, t_review=0.60, t_allow=0.80):
    Aa = adequacy(case, a)
    d = deficits(case, a)
    lam = _norm(case.lam)
    worst = max(range(4), key=lambda i: lam[i] * d[i])
    if any(lam[i] * d[i] > 0.25 for i in range(4)):
        return ("needs-review", VILLARS[worst], Aa, residual_risk(case, a))
    if Aa < t_block:
        return ("block", VILLARS[worst], Aa, residual_risk(case, a))
    if Aa < t_restrict:
        return ("restrict", VILLARS[worst], Aa, residual_risk(case, a))
    if Aa < t_review:
        return ("needs-review", VILLARS[worst], Aa, residual_risk(case, a))
    if Aa < t_allow:
        return ("allow-with-guards", VILLARS[worst], Aa, residual_risk(case, a))
    return ("allow", VILLARS[worst], Aa, residual_risk(case, a))


# ---------------------------------------------------------------- invariants (tests)
def simplex_sample(rng, n=4):
    xs = [rng.random() for _ in range(n)]
    s = sum(xs)
    return tuple(x / s for x in xs)

def run_invariants(trials=20000, seed=1234):
    """Six invariants of the corrected formal core, checked by random sampling
    over the admissible simplex."""
    rng = random.Random(seed)
    counts = {"bounds": 0, "risk_floor": 0, "non_compensation": 0,
              "monotonicity": 0, "volume_degeneracy": 0, "tension_bound": 0}
    fails = {k: None for k in counts}

    def viol(k, ex):
        counts[k] += 1
        if fails[k] is None:
            fails[k] = ex

    for _ in range(trials):
        a = simplex_sample(rng)
        r = simplex_sample(rng)
        lam = simplex_sample(rng)
        case = Case(r, lam, rng.random(), rng.random(), critical=("M", "K"))

        Aa, R = adequacy(case, a), residual_risk(case, a)
        if not (0.0 - 1e-12 <= Aa <= 1.0 + 1e-12):
            viol("bounds", (a, r, Aa))
        if case.R_c > 0 and R <= 0.0 + 1e-12:
            viol("risk_floor", (a, r, R, case.R_c))
        if R < case.sigma * case.R_c - 1e-12:
            viol("risk_floor", (a, r, R, case.R_c))

        # non-compensation: growing an already-satisfied pillar never reduces
        # the deficit of another pillar (component-wise independence).
        d = deficits(case, a)
        for i in range(4):
            for j in range(4):
                if i == j or a[j] <= case.r[j]:
                    continue
                a2 = list(a)
                a2[j] += 0.05                      # unnormalised: pure extra capacity
                if deficits(case, tuple(a2))[i] > d[i] + 1e-12:
                    viol("non_compensation", (a, case.r, i, j))

        # monotonicity: moving mass FROM a deficient pillar TO a surplus pillar
        # must never improve adequacy.
        for i in range(4):
            for j in range(4):
                if i == j or a[i] < 1e-3:
                    continue
                if a[i] < r[i] and a[j] >= r[j]:
                    a2 = list(a)
                    a2[i] -= 0.02; a2[j] += 0.02
                    s = sum(a2); a2 = tuple(x / s for x in a2)
                    if adequacy(case, a2) > adequacy(case, a) + 1e-9:
                        viol("monotonicity", (a, r, i, j, adequacy(case, a), adequacy(case, a2)))

        # geometric degeneracy: volumetric coherence is bounded by the weakest pillar
        m = min(a)
        bound = 4.0 * (m ** 0.25) * (((1.0 - m) / 3.0) ** 0.75)
        if volumetric_coherence(a) > bound + 1e-12:
            viol("volume_degeneracy", (a, volumetric_coherence(a), bound))

        T = profile_tension(case, a)
        if not (0.0 <= T <= 1.0):
            viol("tension_bound", (a, r, T))

    return counts, fails


def demo_scenarios():
    """Before/after comparison of the v9 and corrected v2 formal layer."""
    rows = [
        ("Clinical triage / action-oriented agent",
         (.25, .25, .30, .20), (.20, .25, .35, .20), 0.35, 0.80, (.40, .30, .15, .15), ("M", "K")),
        ("Clinical triage / epistemic reviewer",
         (.25, .25, .30, .20), (.20, .25, .35, .20), 0.35, 0.80, (.15, .20, .25, .40), ("M", "K")),
        ("Creative assistant / balanced profile",
         (.30, .25, .25, .20), (.30, .25, .25, .20), 0.10, 0.25, (.25, .25, .25, .25), ()),
        ("Critical case, agent with ZERO Know",
         (.25, .25, .30, .20), (.20, .25, .35, .20), 0.40, 0.90, (.40, .30, .30, .00), ("M", "K")),
        ("Severe Must-deficit hidden by low salience (lambda_M = 0.05)",
         (.30, .30, .40, .00), (.30, .30, .05, .35), 0.20, 0.85, (.30, .30, .10, .30), ("M",)),
        ("Perfect-fit profile (Aa = 1) in a critical domain",
         (.25, .25, .25, .25), (.25, .25, .25, .25), 0.05, 0.70, (.25, .25, .25, .25), ()),
    ]
    print("\n--- ABLATION: paper v9 formula vs corrected v2 formula ---")
    print(f"{'scenario':48}{'Aa(v9)':>8}{'Aa(v2)':>8}{'Rr(v9)':>8}{'Rr(v2)':>8}{'decision':>18}")
    for name, r, lam, U, Rc, a, crit in rows:
        c = Case(r, lam, U, Rc, critical=crit)
        print(f"{name:48}{adequacy_v9(c, a):8.3f}{adequacy(c, a):8.3f}"
              f"{residual_risk_v9(c, a):8.3f}{residual_risk(c, a):8.3f}"
              f"{decision(c, a)[0]:>18}")

    print("\nSurplus-punishment test (v9 penalises a profile that merely skews,")
    print("even when every requirement is met):")
    c = Case((.25, .25, .25, .25), (.25, .25, .25, .25), 0.0, 0.5, critical=())
    print("  balanced  (.25,.25,.25,.25): Aa(v9) =", round(adequacy_v9(c, (.25, .25, .25, .25)), 4),
          "| Aa(v2) =", round(adequacy(c, (.25, .25, .25, .25)), 4))
    print("  skewed    (.30,.30,.30,.10): Aa(v9) =", round(adequacy_v9(c, (.30, .30, .30, .10)), 4),
          "| Aa(v2) =", round(adequacy(c, (.30, .30, .30, .10)), 4))

    print("\nGeometric coherence for a=(.40,.30,.20,.10):")
    print("  V(a) =", round(volumetric_coherence((.40, .30, .20, .10)), 4),
          "| B(a) =", round(balance_coherence((.40, .30, .20, .10)), 4),
          "| volume shares =", [round(x, 4) for x in volume_shares((.40, .30, .20, .10))])


if __name__ == "__main__":
    print("Proposition 1 (Eq.1 satisfied by centred unit embedding):", check_geometry())
    a, b = (.4, .3, .2, .1), (.1, .2, .3, .4)
    print("d_Delta (Eq.3) =", tv_distance(a, b),
          "| induced Euclidean =", euclidean_on_simplex(a, b),
          "| ratio =", tv_distance(a, b) / euclidean_on_simplex(a, b))
    print("volume shares of a=(.2,.3,.25,.25):", volume_shares((.2, .3, .25, .25)))
    print("volumetric coherence: balanced =", volumetric_coherence((.25, .25, .25, .25)),
          "| degenerate (K=0) =", volumetric_coherence((.4, .3, .3, 0.0)))
    counts, fails = run_invariants()
    print("invariant violations over 20000 sampled cases:")
    for k, v in counts.items():
        print("  ", k, "->", v, ("| example: %s" % (fails[k],)) if fails[k] else "")

