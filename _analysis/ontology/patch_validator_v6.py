"""One-shot patch: validate_ontology_v4.py -> validate_ontology_v6.py (v4.2 additions)."""
p = "validate_ontology_v6.py"
s = open(p).read()

anchor = "def clamp(x, lo=0.0, hi=1.0):"
add = '''OVERSIGHT_VALUE = {"unspecified": 0.0, "none": 0.0, "out_of_loop": 0.20,
                   "on_the_loop": 0.50, "in_the_loop": 0.80}
OVERSIGHT_ATTENUATION = 0.45


def oversight_value(regime):
    return OVERSIGHT_VALUE.get(str(regime).split("Oversight_")[-1], 0.0)

'''
assert anchor in s
s = s.replace(anchor, add + anchor, 1)

old_q = '''          ?case eth:domain ?dom ; eth:severity ?sb ; eth:reversibility ?rb ;
                eth:prudentialMode ?pb ; eth:horizon ?hb ;
                eth:epistemicUncertainty ?UE ; eth:consequenceMass ?Rc ;
                eth:exposureScale ?exposure ; eth:normConflictStatus ?conflict ;
                eth:evidenceConflict ?evidence .'''
new_q = '''          ?case eth:domain ?dom ; eth:severity ?sb ; eth:reversibility ?rb ;
                eth:prudentialMode ?pb ; eth:horizon ?hb ;
                eth:epistemicUncertainty ?UE ; eth:consequenceMass ?Rc ;
                eth:exposureScale ?exposure ; eth:normConflictStatus ?conflict ;
                eth:evidenceConflict ?evidence .
          OPTIONAL { ?case eth:oversightRegime ?regime }'''
assert old_q in s
s = s.replace(old_q, new_q, 1)
s = s.replace('''SELECT ?c ?case ?profile ?calId ?dom ?sev ?rev ?pr ?hor ?UE ?Rc ?exposure
               ?conflict ?evidence ?critPillar ?pnm''',
              '''SELECT ?c ?case ?profile ?calId ?dom ?sev ?rev ?pr ?hor ?UE ?Rc ?exposure
               ?conflict ?evidence ?critPillar ?pnm ?regime''', 1)
s = s.replace('''                 "evidence_conflict": as_bool(row["evidence"])})''',
              '''                 "evidence_conflict": as_bool(row["evidence"]),
                 "oversight": (str(row["regime"]).split("Oversight_")[-1]
                               if row["regime"] is not None else "unspecified")})''', 1)

old = '''    sev, rev, pr, hor = ctx["severity"], ctx["irreversibility"], ctx["prudential"], ctx["horizon"]
    stakes = clamp(cal["stakeWeightSeverity"] * sev + cal["stakeWeightIrreversibility"] * rev
                   + cal["stakeWeightPrudential"] * (pr / 0.10)
                   + cal["stakeWeightHorizon"] * hor, 0.0, 1.0)'''
new = '''    sev, rev, pr, hor = ctx["severity"], ctx["irreversibility"], ctx["prudential"], ctx["horizon"]
    irr_eff = rev * (1.0 - OVERSIGHT_ATTENUATION
                     * oversight_value(ctx.get("oversight", "unspecified")))
    stakes = clamp(cal["stakeWeightSeverity"] * sev + cal["stakeWeightIrreversibility"] * irr_eff
                   + cal["stakeWeightPrudential"] * (pr / 0.10)
                   + cal["stakeWeightHorizon"] * hor, 0.0, 1.0)'''
assert old in s
s = s.replace(old, new, 1)

old2 = '''    phi = cs / cw if cw > EPS else 0.0
    aa_raw = clamp(1.0 - D - cal["gamma"] * S2 - cal["eta"] * S3 - cal["omega"] * S4
                   - cal["rho"] * u - cal["delta"] * phi)'''
new2 = '''    phi = cs / cw if cw > EPS else 0.0
    n2 = n3 = d2 = d3 = 0.0
    for f in facet_list:
        r_f = requirements.get(f.code)
        l_f = levels.get(f.code)
        if r_f is None or l_f is None:
            continue
        sup = f.n_pillars()
        if sup < 2:
            continue
        sigma = 1.0 - max(f.beta)
        if sigma <= EPS:
            continue
        band = core.band_value(l_f, confs.get(f.code, 1.0), mode)
        gap = max(0.0, r_f - band)
        if sup == 2:
            n2 += sigma * gap; d2 += sigma
        else:
            n3 += sigma * gap; d3 += sigma
    psi = (n2 + n3) / (d2 + d3) if (d2 + d3) > EPS else 0.0
    psi_edge = n2 / d2 if d2 > EPS else 0.0
    psi_face = n3 / d3 if d3 > EPS else 0.0
    lam0 = [cal["lam" + PILLARS[i]] for i in range(4)]
    s_adapt = cal.get("salienceAdaptation", 0.0)
    if s_adapt > 0.0:
        raw = [lam0[i] * max(q[i], 0.0) ** s_adapt for i in range(4)]
        tot = sum(raw)
        salience = [x / tot for x in raw] if tot > EPS else lam0
    else:
        salience = lam0
    aa_raw = clamp(1.0 - sum(salience[i] * d[i] for i in range(4))
                   - cal["gamma"] * S2 - cal["eta"] * S3 - cal["omega"] * S4
                   - cal["rho"] * u - cal["delta"] * phi
                   - cal.get("crossPillarCoefficient", 0.0) * psi)'''
assert old2 in s
s = s.replace(old2, new2, 1)

s = s.replace('''            "coverage": sum(1 for f in facet_list if f.code in levels) / len(facet_list)}''',
              '''            "coverage": sum(1 for f in facet_list if f.code in levels) / len(facet_list),
            "psi": psi, "psi_edge": psi_edge, "psi_face": psi_face,
            "salience": salience, "oversight": ctx.get("oversight", "unspecified")}''', 1)

s = s.replace('''    ("guard_failure_count", "central", "guard_failures_count", "guardFailureCount"),
]''',
              '''    ("guard_failure_count", "central", "guard_failures_count", "guardFailureCount"),
    ("cross_pillar_duty", "central", "psi", "crossPillarDuty"),
    ("cross_pillar_duty_edge", "central", "psi_edge", "crossPillarDutyEdge"),
    ("cross_pillar_duty_face", "central", "psi_face", "crossPillarDutyFace"),
    ("case_salience_W", "central", "salience[0]", "caseSalienceW"),
    ("case_salience_C", "central", "salience[1]", "caseSalienceC"),
    ("case_salience_M", "central", "salience[2]", "caseSalienceM"),
    ("case_salience_K", "central", "salience[3]", "caseSalienceK"),
    ("review_need", "central", "review_need", "reviewNeed"),
]''', 1)

s = s.replace('''        low = mirror_compute(d, levels[c], confs[c], requirements[c], facet_list,
                             lattice_slots, "pessimistic", d["domain"])''',
              '''        low = mirror_compute(d, levels[c], confs[c], requirements[c], facet_list,
                             lattice_slots, "pessimistic", d["domain"])
        high = mirror_compute(d, levels[c], confs[c], requirements[c], facet_list,
                              lattice_slots, "optimistic", d["domain"])
        mid["review_need"] = core.review_need(low["aa"], high["aa"], low["bar"],
                                             low["u"], mid["coverage"], cal_obj)''', 1)

s = s.replace('''             "guardFailureCount"]''',
              '''             "guardFailureCount", "crossPillarDuty", "crossPillarDutyEdge",
             "crossPillarDutyFace", "caseSalienceW", "caseSalienceC", "caseSalienceM",
             "caseSalienceK", "reviewNeed"]''', 1)

s = s.replace('''                         evidence_conflict=ctx["evidence_conflict"],
                         exposure=ctx["exposure"])''',
              '''                         evidence_conflict=ctx["evidence_conflict"],
                         exposure=ctx["exposure"],
                         oversight=ctx.get("oversight", "unspecified"))''', 1)

checks = '''    # -------- v4.2 gates: oversight (D5.4), coverage gate (D5.8), ReviewNeed (D5.6), Prop 1 ----
    slots_all = lattice_from_graph(full)
    edges = [x for x in slots_all if x["kind"] == "edge"]
    faces = [x for x in slots_all if x["kind"] == "face"]
    derived = []
    for e in edges:
        inc = set(e["incidence"])
        expected = sum(f["weight"] for f in faces if inc <= set(f["incidence"])) / 3.0
        derived.append({"slot": e["name"], "declared": round(e["weight"], 12),
                       "derived_alpha": round(expected, 12),
                       "diff": round(abs(e["weight"] - expected), 12)})
    bad_alpha = [x for x in derived if x["diff"] > 1e-6]
    add_python("Proposition 1 (D5.1): every declared edge weight equals (1/3) * sum of the "
               "face weights of the faces containing that edge", "structural", not bad_alpha,
               {"rows": len(bad_alpha), "edges_examined": len(edges), "max_diff":
                max((x["diff"] for x in derived), default=0.0), "examples": derived[:6]})

    regime_of = {}
    for case in full.subjects(RDF.type, URIRef(ETH + "EthicalCase")):
        r = full.value(case, URIRef(ETH + "oversightRegime"))
        regime_of[str(case)] = str(r).split("Oversight_")[-1] if r is not None else None
    review, audit, appeal = set(), set(), set()
    for case in full.subjects(RDF.type, URIRef(ETH + "EthicalCase")):
        for gf in full.objects(case, URIRef(ETH + "groundedByFact")):
            name = str(full.value(gf, URIRef(ETH + "factName")))
            if name == "human_review_channel":
                review.add(str(case))
            elif name == "independent_audit":
                audit.add(str(case))
            elif name == "appeal_channel":
                appeal.add(str(case))

    def expected_regime(c):
        if c in review and c in audit:
            return "in_the_loop"
        if c in review or c in appeal:
            return "on_the_loop"
        return "none"

    missing_regime = [c for c, v in regime_of.items() if v is None]
    add_python("every case declares exactly one oversight regime (E11c')", "structural",
               not missing_regime, {"rows": len(missing_regime),
                                   "cases_examined": len(regime_of)})
    wrong = {c: (v, expected_regime(c)) for c, v in regime_of.items()
             if v is not None and v != expected_regime(c)}
    add_python("the declared oversight regime is exactly the one the declared facts imply "
               "(no invented supervision)", "deontic", not wrong,
               {"rows": len(wrong), "cases_examined": len(regime_of),
                "examples": {k: list(v) for k, v in list(wrong.items())[:5]},
                "regime_mix": dict(Counter(v for v in regime_of.values() if v))})

    add("no confrontation has coverage or reviewNeed outside [0,1]", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation .
           OPTIONAL { ?c eth:coverage ?cv } OPTIONAL { ?c eth:reviewNeed ?rn }
           FILTER((bound(?cv) && (?cv < 0 || ?cv > 1)) ||
                  (bound(?rn) && (?rn < 0 || ?rn > 1))) }""")
    add("every confrontation with declared coverage below the gate abstains (E26')", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:coverage ?cv ; eth:decision ?d
           FILTER(?cv < 0.70 - 1e-9 && ?d != eth:Decision_ABSTAIN) }""")
    add("no coverage-abstaining confrontation carries an adequacy literal (D5.8)", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:coverage ?cv ;
           eth:decision eth:Decision_ABSTAIN ; eth:adequacy ?a
           FILTER(?cv < 0.70 - 1e-9) }""")
    add("no confrontation violates S2 >= S3 >= S4 (Proposition 1, measured on the graph)",
        "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:structuralTermS2 ?s2 ;
           eth:structuralTermS3 ?s3 ; eth:structuralTermS4 ?s4
           FILTER(?s2 < ?s3 - 1e-9 || ?s3 < ?s4 - 1e-9) }""")
    add("no canonical duty spans all four pillars: the cell has no facet-level witness",
        "structural",
        """SELECT ?f WHERE { ?f a eth:Facet . ?f eth:betaW ?w . ?f eth:betaC ?c .
           ?f eth:betaM ?m . ?f eth:betaK ?k FILTER(w > 0 && c > 0 && m > 0 && k > 0) }""")
    add("every recorded cross-pillar duty exposure lies in [0,1]", "structural",
        """SELECT ?c WHERE { ?c a eth:Confrontation ; eth:crossPillarDuty ?p
           FILTER(?p < 0 || ?p > 1) }""")
'''

anchor2 = "    # ---------------- findings (reported, not gates) ----------------"
assert anchor2 in s
s = s.replace(anchor2, checks + "\n" + anchor2, 1)

open(p, "w").write(s)
import ast
ast.parse(s)
print("validator patched ok")
