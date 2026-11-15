"""Recompute the canon statistics for the 33-facet registry (v12).

The original `facet_review_stats.json` was generated while the canon still had 28
facets and the inert `weight` field. Every number quoted in the paper about facet
redundancy, guard distribution or the lambda-vs-beta-mass deviation must come from
this artifact, not from prose.

Output: Evaluacoes/r4/facet_review_stats_v12.json
"""
import itertools
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "formal_core"))
from facet_registry import FACETS, PILLARS, validate_registry  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Evaluacoes", "r4",
                   "facet_review_stats_v12.json")


def beta_distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main():
    n = len(FACETS)
    total_beta = sum(sum(f.beta) for f in FACETS)
    mass = [sum(f.beta[i] for f in FACETS) / total_beta for i in range(4)]
    lam = (0.30, 0.25, 0.25, 0.20)

    pairs = [(f1.code, f2.code, list(f1.beta), list(f2.beta), round(beta_distance(f1.beta, f2.beta), 6))
             for f1, f2 in itertools.combinations(FACETS, 2)
             if beta_distance(f1.beta, f2.beta) < 0.12]
    exact = [p for p in pairs if p[4] == 0.0]
    near = [p for p in pairs if 0.0 < p[4] < 0.12]

    def chebyshev(a, b):
        return max(abs(x - y) for x, y in zip(a, b))

    cheb = [(f1.code, f2.code, round(chebyshev(f1.beta, f2.beta), 6))
            for f1, f2 in itertools.combinations(FACETS, 2)
            if chebyshev(f1.beta, f2.beta) < 0.12]

    domains = sorted({d for f in FACETS for d in f.criticality})
    flat_criticality = [f.code for f in FACETS
                        if len(set(f.criticality.values())) == 1]

    out = {
        "registry": "canon v12 (33 facets)",
        "n_facets": n,
        "registry_validation_errors": validate_registry(),
        "beta_rows_sum_to_one": all(abs(sum(f.beta) - 1.0) < 1e-9 for f in FACETS),
        "facets_per_pillar": {p: sum(1 for f in FACETS if f.beta[PILLARS.index(p)] > 0) for p in PILLARS},
        "pillars_touched_distribution": {
            k: sum(1 for f in FACETS if sum(1 for b in f.beta if b > 0) == k) for k in (1, 2, 3, 4)
        },
        "pillar_beta_mass_share": {p: round(mass[i], 4) for i, p in enumerate(PILLARS)},
        "pillar_declared_lambda": {p: lam[i] for i, p in enumerate(PILLARS)},
        "lambda_vs_beta_mass_max_deviation": round(max(abs(mass[i] - lam[i]) for i in range(4)), 4),
        "guard_count": sum(1 for f in FACETS if f.guard),
        "guards_per_pillar": {p: sum(1 for f in FACETS if f.guard and f.beta[PILLARS.index(p)] > 0)
                             for p in PILLARS},
        "facets_with_observable": sum(1 for f in FACETS if f.observable),
        "inert_weight_field": "removed from core, registry, CSV and RDF (D4.17)",
        "identical_beta_pairs": len(exact),
        "identical_beta_pairs_list": [[p[0], p[1], p[2]] for p in exact],
        "near_duplicate_beta_pairs_0_to_0_12": len(near),
        "near_duplicate_beta_pairs_list": near,
        "chebyshev_beta_pairs_lt_0_12": len(cheb),
        "chebyshev_beta_pairs_list": cheb,
        "facets_with_flat_criticality": len(flat_criticality),
        "mean_criticality_per_facet": round(
            sum(sum(f.criticality.values()) / len(f.criticality) for f in FACETS) / n, 4),
        "criticality_mass_per_domain": {
            d: round(sum(f.criticality.get(d, 0) for f in FACETS) / n, 4) for d in domains
        },
        "share_of_beta_mass_in_single_pillar_facets": round(
            sum(sum(f.beta) for f in FACETS if sum(1 for b in f.beta if b > 0) == 1) / total_beta, 4),
        "beta_above_floor_r3": sum(1 for f in FACETS for b in f.beta if 0 < b < 0.15),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2)[:1500])
    print("\nwritten:", OUT)


if __name__ == "__main__":
    main()
