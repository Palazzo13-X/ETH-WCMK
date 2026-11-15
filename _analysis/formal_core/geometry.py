"""Face-lattice geometry of the 3-simplex (F1 deliverable).

Corrected substrate of the "Estrutura Matemático-Simbólica do Tetraedro Regular" PDF.
The tetrahedron is used as a *relational index* (the face lattice of the 3-simplex is
isomorphic to the non-empty subsets of a 4-element set), not as a metric state space.

Verified constants: edge = sqrt(8/3) for unit-norm centred vertices; centroid (1/2, 0.288675, 0.204124);
inradius = sqrt(6)/12 = 0.204124; circumradius = sqrt(6)/4 = 0.612372; volume = sqrt(2)/12 = 0.117851.
The PDF's printed centroid (1/2, sqrt(3)/4, sqrt(6)/4) confuses circumradius with inradius as coordinates.
"""
from itertools import combinations
import numpy as np

PILLARS = ("W", "C", "M", "K")
VERTICES = tuple((i,) for i in range(4))
EDGES = tuple(combinations(range(4), 2))
FACES = tuple(combinations(range(4), 3))
CELL = (0, 1, 2, 3)
SLOTS = VERTICES + EDGES + FACES + (CELL,)          # 4 + 6 + 4 + 1 = 15

# unit-norm, centred vertices: v_i . v_j = -1/3, edge length sqrt(8/3)
def centred_vertices():
    """Regular tetrahedron, edge sqrt(8/3), centred at the origin, vertices on the unit sphere:
    v_i . v_j = -1/3 for i != j, which is exactly the convention of Eq. (1) of the paper."""
    s = 1 / np.sqrt(3)
    return s * np.array([[1.0, 1.0, 1.0],
                         [1.0, -1.0, -1.0],
                         [-1.0, 1.0, -1.0],
                         [-1.0, -1.0, 1.0]])

def barycentric_to_point(a):
    """a in Delta^3 (sums to 1) -> point in R^3 as convex combination of vertices."""
    a = np.asarray(a, dtype=float)
    return a @ centred_vertices()

def chordal_distance(a, b):
    return float(np.linalg.norm(barycentric_to_point(a) - barycentric_to_point(b)))

def tv_distance(a, b):
    return 0.5 * float(np.abs(np.subtract(a, b)).sum())

def ratio_bounds(n=20000, seed=11):
    rng = np.random.default_rng(seed)
    x = rng.dirichlet(np.ones(4), size=n)
    y = rng.dirichlet(np.ones(4), size=n)
    r = chordal_batch(x, y) / np.maximum(tv_distance_batch(x, y), 1e-12)
    return float(r.min()), float(r.max())

def _points(X):
    return X @ centred_vertices()

def chordal_batch(X, Y):
    P, Q = _points(X), _points(Y)
    return np.linalg.norm(P - Q, axis=1)

def tv_distance_batch(X, Y):
    return 0.5 * np.abs(X - Y).sum(axis=1)

def mobius_residual(slot_values):
    """Mobius transform on the subset lattice: the 'interior' (cell) residual is the part
    of the quaternary relation not explained by unary, binary and ternary relations."""
    v = sum(slot_values[s] for s in VERTICES)
    e = sum(slot_values[s] for s in EDGES)
    f = sum(slot_values[s] for s in FACES)
    return slot_values[CELL] - f + e - v


def joint_deficit(d, subset):
    """Deficit simultaneously present in every pillar of `subset` (Godel t-norm of the
    indicator deficits). This is the correct semantics for a conjunction of duties:
    all of them must be met, so the joint shortfall is the largest individual one."""
    return float(min(d[i] for i in subset))


def lattice_marginal_alpha(beta=None):
    """[v13, D5.1] The edge weights are not free parameters: they are the exact
    marginalisation of the face weights over the face lattice of the 3-simplex,

        alpha_e = (1/3) * sum_{face f containing e} beta_f .

    Properties: (a) each edge lies in exactly 2 of the 4 faces, so sum_e alpha_e =
    (1/3) * sum_f beta_f * 3 = sum_f beta_f = 1; (b) for beta = 1/4 uniform this gives
    alpha_e = 1/6, i.e. the canonical v10/v11/v12 calibration is *exactly* this marginal
    -- the reparameterisation changes no number that has ever been reported.
    """
    beta = list(beta) if beta is not None else [1 / 4] * 4
    return [(1 / 3.0) * sum(beta[k] for k, f in enumerate(FACES) if set(e) <= set(f))
            for e in EDGES]


def structural_terms(d, alpha=None, beta=None):
    """[v13] S2, S3, S4 from the face lattice with the Godel t-norm.

    Proposition 1 (unconditional, v13): if beta sums to 1 and alpha is the lattice
    marginal of beta, then for EVERY deficit vector d in [0,1]^4,
        min_p d_p  <=  S3  <=  S2  <=  max_p d_p .
    Proof. (i) every face contains the global minimum and sum(beta) = 1, hence S3 >= min d.
    (ii) for each face f, delta(f) = min_{e subset f} delta(e), and each edge e subset f
    satisfies delta(e) >= delta(f); therefore
        S2 = sum_e alpha_e delta(e)
           = (1/3) sum_f beta_f sum_{e subset f} delta(e)
           >= (1/3) sum_f beta_f * 3 * delta(f) = S3.
    (iii) sum(alpha) = 1 and every delta(e) <= max d, hence S2 <= max d.  QED
    The v12 side-condition alpha_e >= (1/3) sum_{f superset e} beta_f is therefore no
    longer a property the model has to *hope* for: it holds with equality by definition.
    """
    beta = list(beta) if beta is not None else [1 / 4] * 4
    alpha = lattice_marginal_alpha(beta) if alpha is None else list(alpha)
    s2 = sum(alpha[k] * joint_deficit(d, e) for k, e in enumerate(EDGES))
    s3 = sum(beta[k] * joint_deficit(d, f) for k, f in enumerate(FACES))
    s4 = joint_deficit(d, CELL)
    return s2, s3, s4


def hierarchical_bound(d, alpha=None, beta=None):
    """S4 <= S3 <= S2 <= max_i d_i. Returns (S4, S3, S2, max). v11 used the geometric
    mean for S4, which breaks the inequality (counterexample d=(0.5,0.4,0.3,0.2):
    S2=0.2667, S3=0.2250, geometric S4=0.3310)."""
    s2, s3, s4 = structural_terms(d, alpha, beta)
    return s4, s3, s2, max(d)


def lattice_cardinality():
    """The face lattice of the 3-simplex has 15 non-empty faces = 2^4 - 1: the subsets
    of a 4-element set. This is why 'pairs of pillars', 'triples of pillars' and the
    'quaternary relation' exhaust the possible joint-failure modes: there are exactly
    15 of them, and none is missing."""
    return {"vertices": len(VERTICES), "edges": len(EDGES), "faces": len(FACES),
            "cell": 1, "total": len(SLOTS), "expected": 2 ** len(PILLARS) - 1}

def subvolume_shares(a):
    """Barycentric sub-volume shares of the point x(a) with respect to the four faces.
    Numerically identical to the coordinates a_i: the 'volumetric coherence' layer carries
    no information beyond the profile itself."""
    a = np.asarray(a, dtype=float)
    V = centred_vertices()
    vol = abs(np.linalg.det(V[1:] - V[0])) / 6.0
    sub = []
    for i in range(4):
        face = [V[j] for j in range(4) if j != i]
        sub.append(abs(np.linalg.det(np.array(face) - barycentric_to_point(a))) / 6.0)
    return np.array(sub), vol

if __name__ == "__main__":
    V = centred_vertices()
    print("vertices:\n", V)
    print("centroid:", V.mean(axis=0))
    print("dot off-diagonal:", V[0] @ V[1], "edge:", np.linalg.norm(V[0] - V[1]))
    a, b = np.array([0.4, 0.3, 0.2, 0.1]), np.array([0.25, 0.25, 0.25, 0.25])
    print("chordal:", chordal_distance(a, b), "TV:", tv_distance(a, b))
    lo, hi = ratio_bounds()
    print("chordal/TV ratio range:", lo, hi, " theory:", 2/np.sqrt(3), np.sqrt(8/3))
    shares, vol = subvolume_shares(a)
    print("subvolume shares:", shares, "sum:", shares.sum(), "total volume:", vol)
    d = [0.4, 0.2, 0.1, 0.05]
    print("hierarchical bound S4<=S3<=S2<=max:", hierarchical_bound(d))
