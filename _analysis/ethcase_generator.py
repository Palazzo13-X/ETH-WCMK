#!/usr/bin/env python3
"""ETHCASE synthetic-case generator (seed corpus v1) for ETH-WCMK.

Deterministic: same seed -> same file. Emits JSONL with the schema sketched in
_analysis/ETH-WCMK_Analise_Critica_e_Plano_v1.md, section 6.2.

Design axes (per case):
  domain (10) x severity band (4) x prudential mode (3) x agency family (4)
  x normative-conflict pattern (6)  -> 10*4*3*4*6 = 720 combinations;
  we emit a stratified subset: one case per (domain, severity, agency) with the
  conflict pattern cycled, plus degenerate/adversarial cases.

The point of the generator is NOT realism (that comes from the expert corpus)
but stress-testing the formal core: it produces the r(E), lambda(E), U_E, R_c
triples that battery B1/B3/B4 consume.
"""
import json, random
from formal_core import Case, adequacy, residual_risk, deficits, decision

DOMAINS = {
    # name: (base weight R_c, domain requirement prior over (W,C,M,K), prudential default)
    "health":                 (0.85, (0.22, 0.24, 0.32, 0.22), "elevated"),
    "justice_security":       (0.90, (0.20, 0.22, 0.38, 0.20), "maximum"),
    "critical_infrastructure":(0.95, (0.18, 0.34, 0.30, 0.18), "maximum"),
    "finance":                (0.75, (0.22, 0.28, 0.32, 0.18), "elevated"),
    "privacy_data":           (0.80, (0.20, 0.25, 0.35, 0.20), "elevated"),
    "public_governance":      (0.82, (0.26, 0.20, 0.34, 0.20), "elevated"),
    "information_media":      (0.45, (0.30, 0.22, 0.28, 0.20), "standard"),
    "education":              (0.60, (0.30, 0.24, 0.26, 0.20), "standard"),
    "labour":                 (0.65, (0.26, 0.26, 0.30, 0.18), "standard"),
    "environment_energy":     (0.78, (0.24, 0.30, 0.30, 0.16), "elevated"),
}
SEVERITY = {"low": 0.30, "medium": 0.55, "high": 0.78, "critical": 0.95}
CRITICAL_PILLARS = {
    "health": ("M", "K"), "justice_security": ("M", "K"),
    "critical_infrastructure": ("C", "M"), "finance": ("M", "K"),
    "privacy_data": ("M", "K"), "public_governance": ("M", "K"),
    "information_media": ("M",), "education": ("K",), "labour": ("M",),
    "environment_energy": ("C", "M"),
}
AGENCY = {
    "balanced":            (0.25, 0.25, 0.25, 0.25),
    "action_oriented":    (0.40, 0.30, 0.15, 0.15),
    "normatively_guarded":(0.20, 0.25, 0.30, 0.25),
    "epistemic_reviewer": (0.15, 0.20, 0.25, 0.40),
}
CONFLICTS = {
    "autonomy_vs_beneficence":   {"W": 1.20, "M": 1.15},
    "transparency_vs_safety":    {"K": 1.25, "C": 1.10},
    "speed_vs_due_process":      {"C": 1.20, "M": 1.20, "W": 0.90},
    "individual_vs_collective":  {"W": 0.90, "M": 1.25},
    "short_term_vs_long_term":   {"W": 1.10, "C": 1.15, "K": 0.95},
    "innovation_vs_precaution":  {"C": 1.25, "M": 1.15, "K": 1.10},
}

def make_case(domain, severity, agency, conflict, rng):
    R_c, prior, prud = DOMAINS[domain]
    mult = SEVERITY[severity]
    r = list(prior)
    for pillar, f in CONFLICTS[conflict].items():
        idx = ["W", "C", "M", "K"].index(pillar)
        r[idx] *= f
    s = sum(r); r = [x / s for x in r]
    lam = [x / sum(r) for x in r]
    U_E = min(0.95, mult * (0.30 + rng.random() * 0.45))
    c = Case(tuple(r), tuple(lam), U_E, R_c * mult, critical=CRITICAL_PILLARS[domain],
             theta=0.15, phi=0.25, sigma={"standard": 0.10, "elevated": 0.15, "maximum": 0.22}[prud])
    return c

def main(seed=42, out="ethcase_seed_v1.jsonl"):
    rng = random.Random(seed)
    rows = []
    n = 0
    for domain in DOMAINS:
        for sev in SEVERITY:
            for ag in AGENCY:
                conflict = list(CONFLICTS)[n % len(CONFLICTS)]
                n += 1
                c = make_case(domain, sev, ag, conflict, rng)
                a = AGENCY[ag]
                rows.append({
                    "caseId": f"ethcase-{seed}-{domain}-{sev}-{ag}-{conflict}",
                    "domain": domain, "severityBand": sev, "prudentialMode": DOMAINS[domain][2],
                    "agencyFamily": ag, "conflictPattern": conflict,
                    "r": [round(x, 4) for x in c.r],
                    "lambda": [round(x, 4) for x in c.lam],
                    "U_E": round(c.U_E, 4), "R_c": round(c.R_c, 4),
                    "criticalPillars": list(c.critical),
                    "agency": list(a),
                    "deficits": [round(x, 4) for x in deficits(c, a)],
                    "Aa": round(adequacy(c, a), 4),
                    "Rr": round(residual_risk(c, a), 4),
                    "decision": decision(c, a)[0],
                    "worstPillar": decision(c, a)[1],
                })
    # degenerate / adversarial probes
    for d in DOMAINS:
        for ag, a in [("zero_know", (0.40, 0.30, 0.30, 0.00)),
                      ("zero_must", (0.35, 0.35, 0.30, 0.00)),
                      ("single_pillar", (1.00, 0.00, 0.00, 0.00))]:
            c = Case(*([0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25], 0.4, DOMAINS[d][0],
                       CRITICAL_PILLARS[d], 0.15, 0.25, 0.15))
            rows.append({
                "caseId": f"ethcase-probe-{d}-{ag}", "domain": d, "severityBand": "critical",
                "type": "degenerate", "agency": list(a),
                "deficits": [round(x, 4) for x in deficits(c, a)],
                "Aa": round(adequacy(c, a), 4), "Rr": round(residual_risk(c, a), 4),
                "decision": decision(c, a)[0], "worstPillar": decision(c, a)[1],
            })
    with open(out, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"wrote {len(rows)} cases to {out}")
    from collections import Counter
    print("decisions:", Counter(r["decision"] for r in rows))
    print("mean Aa:", round(sum(r["Aa"] for r in rows) / len(rows), 4))

if __name__ == "__main__":
    main()
