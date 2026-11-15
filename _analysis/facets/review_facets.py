"""Structural review of the facet canon (Tarefa 3 / F4).

Answers three questions that the paper must answer with numbers, not adjectives:
  1. Is every pillar actually covered by facets, and is the coverage balanced?
  2. How much cross-pillar sharing is there really (facets that touch >1 pillar)?
  3. Which declared parameters are inert (they exist in the schema but never change
     anything)?

Writes Evaluacoes/r4/facet_review_stats.json.
"""
import csv
import json
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REG = os.path.join(ROOT, "_analysis", "facets", "facet_registry_v11.csv")
OUT = os.path.join(ROOT, "Evaluacoes", "r4", "facet_review_stats.json")
DOMS = ["SA", "JS", "IC", "FI", "PD", "GP", "IM", "ED", "TB", "MA", "TS", "RS", "DS"]


def main():
    rows = list(csv.DictReader(open(REG)))
    for r in rows:
        r["b"] = [float(r["betaW"]), float(r["betaC"]), float(r["betaM"]), float(r["betaK"])]
        r["nz"] = sum(1 for x in r["b"] if x > 0)
        r["guard"] = r["guard"] == "True"
        r["crit"] = [int(x) for x in r["criticality"].split("|")]

    per = defaultdict(lambda: dict(facets=0, beta_sum=0.0, guarded=0))
    for r in rows:
        for i, p in enumerate("WCMK"):
            if r["b"][i] > 0:
                per[p]["facets"] += 1
                per[p]["beta_sum"] += r["b"][i]
                if r["guard"]:
                    per[p]["guarded"] += 1

    nz_hist = {k: sum(1 for r in rows if r["nz"] == k) for k in (1, 2, 3, 4)}
    beta_sum_ok = all(abs(sum(r["b"]) - 1.0) < 1e-9 for r in rows)
    inert_weights = all(float(r["weight"]) == 1.0 for r in rows)
    flat_crit = [r["code"] for r in rows if len(set(r["crit"])) == 1]
    dom_mass = {d: sum(r["crit"][i] for r in rows) for i, d in enumerate(DOMS)}

    # redundancy screen: pairs of facets whose beta vectors are nearly identical
    pairs = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i]["b"], rows[j]["b"]
            if max(abs(x - y) for x, y in zip(a, b)) < 0.12 and rows[i]["nz"] > 1:
                pairs.append((rows[i]["code"], rows[j]["code"], a, b))

    # the pillar weights lambda declared in the calibration are independent of the
    # facet beta mass; if they disagree, "importance of a pillar" has two definitions.
    LAMBDA = {"W": 0.30, "C": 0.25, "M": 0.25, "K": 0.20}
    mass = {p: per[p]["beta_sum"] / len(rows) for p in "WCMK"}

    result = {
        "n_facets": len(rows),
        "beta_rows_sum_to_one": beta_sum_ok,
        "pillars": {p: {k: round(v, 4) for k, v in d.items()} for p, d in per.items()},
        "pillar_beta_mass_share": {p: round(mass[p], 4) for p in "WCMK"},
        "pillar_declared_lambda": LAMBDA,
        "lambda_vs_beta_mass_max_deviation": round(max(abs(LAMBDA[p] - mass[p]) for p in "WCMK"), 4),
        "facets_by_number_of_pillars_touched": nz_hist,
        "guards": sorted(r["code"] for r in rows if r["guard"]),
        "guards_per_pillar": {p: sum(1 for r in rows if r["guard"] and r["b"][i] > 0)
                             for i, p in enumerate("WCMK")},
        "inert_weight_field": inert_weights,
        "facets_with_flat_criticality_all_domains": flat_crit,
        "mean_criticality_per_facet": {r["code"]: round(sum(r["crit"]) / 13, 3) for r in rows},
        "criticality_mass_per_domain": dom_mass,
        "near_duplicate_beta_vectors": pairs,
        "share_of_beta_mass_in_single_pillar_facets": round(
            sum(max(r["b"]) for r in rows if r["nz"] == 1) / len(rows), 4),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2)[:2500])


if __name__ == "__main__":
    main()
