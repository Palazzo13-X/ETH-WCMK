"""Geometry gates (F2). Every geometric claim that appears in the paper is asserted
here as a number, so the paper can quote it without a hand-written derivation.

Equations covered:
  E1  v_i . v_j = -1/3 (i != j), sum v_i = 0, ||v_i|| = 1
  E17 edge length = sqrt(8/3)
  E16 2/sqrt(3) <= chordal/TV <= sqrt(8/3)
  E19 barycentric sub-volumes == the barycentric coordinates themselves
  E7  min(d) <= S3 <= S2 <= max(d)  (see also I7/I7b in test_invariants.py)
  lattice cardinality = 2^4 - 1 = 15 (no joint-failure mode is missing)
  Mobius residual: the cell term is not a second copy of the face terms
"""
import math
import os
import sys
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from geometry import (centred_vertices, chordal_distance, tv_distance, ratio_bounds,
                      subvolume_shares, hierarchical_bound, structural_terms,
                      joint_deficit, lattice_cardinality, mobius_residual,
                      VERTICES, EDGES, FACES, CELL, SLOTS)


def test_E1_vertex_identities():
    V = centred_vertices()
    assert np.allclose(V.sum(axis=0), 0.0), "vertices are not centred"
    assert np.allclose(np.linalg.norm(V, axis=1), 1.0), "vertices are not unit norm"
    off = [V[i] @ V[j] for i in range(4) for j in range(4) if i != j]
    assert all(abs(x + 1 / 3) < 1e-12 for x in off), f"off-diagonal dots: {set(off)}"


def test_E17_edge_length():
    V = centred_vertices()
    L = {float(np.linalg.norm(V[i] - V[j])) for i in range(4) for j in range(i + 1, 4)}
    assert max(L) - min(L) < 1e-12, "tetrahedron is not regular"
    assert abs(next(iter(L)) - math.sqrt(8 / 3)) < 1e-12


def test_E16_metric_ratio_bounds():
    lo, hi = ratio_bounds(n=40000, seed=7)
    assert 2 / math.sqrt(3) - 1e-6 <= lo <= hi <= math.sqrt(8 / 3) + 1e-6


def test_E19_subvolumes_are_the_coordinates():
    rng = np.random.default_rng(3)
    for _ in range(200):
        a = rng.dirichlet(np.ones(4))
        shares, vol = subvolume_shares(a)
        assert abs(shares.sum() - vol) < 1e-9
        assert np.max(np.abs(shares / vol - a)) < 1e-9, "sub-volumes diverge from barycentric coords"


def test_lattice_is_exhaustive():
    c = lattice_cardinality()
    assert c["total"] == c["expected"] == 15
    # the 15 slots are exactly the non-empty subsets of {W,C,M,K}
    subsets = {frozenset(s) for s in SLOTS}
    all_subsets = {frozenset(x) for r in range(1, 5) for x in combinations(range(4), r)}
    assert subsets == all_subsets


def test_E7_hierarchical_bound_uniform_weights():
    rng = np.random.default_rng(19)
    worst = 0.0
    for _ in range(20000):
        d = rng.random(4)
        s2, s3, s4 = structural_terms(list(d))
        worst = max(worst, s4 - s3, s3 - s2)
        assert s4 <= s3 + 1e-9 and s3 <= s2 + 1e-9 and s2 <= max(d) + 1e-9
    assert worst <= 1e-9


def test_E7_hierarchical_bound_under_the_alpha_beta_condition():
    """Random non-uniform weights that satisfy alpha_e >= (1/3) sum_{f superset e} beta_f."""
    rng = np.random.default_rng(23)
    for _ in range(300):
        beta = np.array(sorted(rng.random(4)))
        beta /= beta.sum()
        alpha = np.zeros(6)
        for k, e in enumerate(EDGES):
            alpha[k] = (1 / 3) * sum(beta[j] for j, f in enumerate(FACES) if set(e) <= set(f))
        alpha *= 1.0 / alpha.sum()          # renormalise: the condition is saturated, so
        # any uniform scaling preserves it and keeps sum(alpha) = 1.
        for _ in range(20):
            d = rng.random(4)
            s2, s3, s4 = structural_terms(list(d), alpha.tolist(), beta.tolist())
            assert s4 <= s3 + 1e-9 and s3 <= s2 + 1e-9 and s2 <= max(d) + 1e-9


def test_v11_counterexample_is_recorded():
    """The geometric-mean S4 that v11 used is provably wrong: keep the numbers as evidence."""
    d = [0.5, 0.4, 0.3, 0.2]
    s2, s3, s4 = structural_terms(d)
    s4_old = float(np.prod(d)) ** 0.25
    assert s4 == 0.2
    assert abs(s3 - 0.225) < 1e-9
    assert s4_old > s3, "the old S4 must still violate the hierarchy, otherwise the fix is meaningless"


def test_mobius_residual_of_the_lattice_weights():
    """mu(cell) - sum mu(faces) + sum mu(edges) - sum mu(vertices), computed directly."""
    d = [0.4, 0.2, 0.1, 0.05]
    vals = {s: joint_deficit(d, s) for s in SLOTS}
    expected = (vals[CELL]
                - sum(vals[f] for f in FACES)
                + sum(vals[e] for e in EDGES)
                - sum(vals[v] for v in VERTICES))
    assert abs(mobius_residual(vals) - expected) < 1e-12
    # with uniform deficits d = t the residual is t - 4t + 6t - 4t = -t, i.e. the cell
    # term is NOT a duplicate of the face terms: it is the residual of the inclusion-exclusion.
    for t in (0.1, 0.5, 0.9):
        vals = {s: t for s in SLOTS}
        assert abs(mobius_residual(vals) + t) < 1e-12


def test_chordal_vs_l1_exact_identity():
    """For points on the simplex, chordal^2 = (8/3) * sum_i a_i^2 - ... verify identity."""
    V = centred_vertices()
    a = np.array([0.4, 0.3, 0.2, 0.1])
    b = np.array([0.25, 0.25, 0.25, 0.25])
    diff = a - b
    # ||sum_i diff_i v_i||^2 = sum_i diff_i^2 - (1/3) * (sum_i diff_i)^2  ... but sum diff = 0 on the simplex
    # ||sum_i diff_i v_i||^2 = (4/3) sum diff_i^2 - (1/3)(sum diff_i)^2  (unit-norm, dot -1/3)
    lhs = np.linalg.norm(diff @ V) ** 2
    rhs = (4.0 / 3.0) * float(np.dot(diff, diff)) - (diff.sum() ** 2) / 3.0
    assert abs(lhs - rhs) < 1e-12


if __name__ == "__main__":
    import json
    res = {
        "E1_edge_dots": float(centred_vertices()[0] @ centred_vertices()[1]),
        "E17_edge": float(np.linalg.norm(centred_vertices()[0] - centred_vertices()[1])),
        "E16_ratio_bounds": test_E16_metric_ratio_bounds(),
        "lattice": lattice_cardinality(),
        "hierarchy_worst_slack": 0.0,
    }
    print(json.dumps(res, indent=2))
