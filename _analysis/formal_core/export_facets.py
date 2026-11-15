"""F2 export: facet registry CSV, beta-sharing matrix, criticality matrix."""
import csv, json, os
from facet_registry import FACETS, DOMAINS, DOMAIN_LABELS, PILLAR_DEFAULT, CATALOG_CRITICAL, validate_registry

OUT = os.path.dirname(os.path.abspath(__file__))  # _analysis/formal_core
FACETS_DIR = os.path.join(OUT, "..", "facets")

def main():
    problems = validate_registry()
    rows = []
    for f in FACETS:
        rows.append({
            "code": f.code, "label": f.label,
            "primary_pillar": f.code[0],
            "beta_W": f.beta[0], "beta_C": f.beta[1], "beta_M": f.beta[2], "beta_K": f.beta[3],
            "pillars_shared": "".join(p for p, b in zip("WCMK", f.beta) if b > 0),
            "n_pillars": sum(1 for b in f.beta if b > 0),
            "aggregation_policy": f.policy,
            "hard_guard": f.guard, "guard_min": f.guard_min,
            "source": f.source,
            "criticality": f.criticality,
            "critical_domains": ";".join(d for d in DOMAINS if f.criticality[d] == 4),
        })
    with open(os.path.join(FACETS_DIR, "facet_registry_v10.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

    with open(os.path.join(FACETS_DIR, "criticality_matrix_v10.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["facet"] + [f"{d}({DOMAIN_LABELS[d]})" for d in DOMAINS])
        for f in FACETS:
            w.writerow([f.code] + [f.criticality[d] for d in DOMAINS])

    sharing = {}
    for f in FACETS:
        key = tuple(round(b, 2) for b in f.beta)
        sharing.setdefault(key, []).append(f.code)
    summary = {
        "n_facets": len(FACETS),
        "n_single_pillar": sum(1 for f in FACETS if sum(1 for b in f.beta if b > 0) == 1),
        "n_shared_2": sum(1 for f in FACETS if sum(1 for b in f.beta if b > 0) == 2),
        "n_shared_3plus": sum(1 for f in FACETS if sum(1 for b in f.beta if b > 0) >= 3),
        "pillars": {p: sum(1 for f in FACETS if f.beta["WCMK".index(p)] > 0) for p in "WCMK"},
        "beta_mass_per_pillar": {p: round(sum(f.beta["WCMK".index(p)] for f in FACETS), 3) for p in "WCMK"},
        "guards": [f.code for f in FACETS if f.guard],
        "new_facets": [f.code for f in FACETS if f.source == "new"],
        "criticality_distribution": {k: sum(1 for f in FACETS for v in f.criticality.values() if v == k) for k in (2, 3, 4)},
        "mean_criticality": round(sum(v for f in FACETS for v in f.criticality.values()) / (len(FACETS) * len(DOMAINS)), 2),
        "domains_with_no_critical_facet": [d for d in DOMAINS if not any(f.criticality[d] == 4 for f in FACETS)],
        "facets_critical_in_no_domain": [f.code for f in FACETS if 4 not in f.criticality.values()],
        "facets_critical_in_all_13_domains": [f.code for f in FACETS if all(v == 4 for v in f.criticality.values())],
        "problems": problems,
    }
    with open(os.path.join(FACETS_DIR, "facet_registry_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
