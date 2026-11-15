"""Generate the figures for paper v10 (pure PIL, no matplotlib)."""
import json, math
from PIL import Image, ImageDraw, ImageFont

FIG = "/home/luiz/Documentos/Strata/Shared/paper/figures"
R2 = "/home/luiz/Documentos/Strata/Shared/Evaluacoes/r2"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(size, bold=False, mono=False):
    path = MONO if mono else (BOLD if bold else SANS)
    return ImageFont.truetype(path, size)


def canvas(w, h, title=None):
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    if title:
        d.text((14, 10), title, fill="black", font=font(17, bold=True))
    return img, d


def axes(d, x0, y0, x1, y1):
    d.line([(x0, y0), (x1, y0)], fill="#333", width=2)
    d.line([(x0, y0), (x0, y1)], fill="#333", width=2)


def bar_chart(data, title, xlabel, ylabel, fname, w=900, h=560, colour="#2f6f9f"):
    img, d = canvas(w, h, title)
    x0, y0, x1, y1 = 90, h - 90, w - 30, 60
    axes(d, x0, y0, x1, y1)
    keys = list(data)
    vmax = max(max(data.values()), 1e-9)
    bw = (x1 - x0) / len(keys)
    for k, key in enumerate(keys):
        val = data[key]
        bx = x0 + k * bw + 0.12 * bw
        bx2 = x0 + (k + 1) * bw - 0.12 * bw
        by = y0 - (y0 - y1) * (val / vmax)
        d.rectangle([bx, by, bx2, y0], fill=colour)
        d.text((bx, y0 + 8), str(key), fill="#222", font=font(12))
        d.text(((bx + bx2) / 2 - 12, by - 20), f"{val:.3f}", fill="#222", font=font(12))
    d.text((x0, y0 + 32), xlabel, fill="#555", font=font(12))
    d.text((x0 - 80, (y0 + y1) / 2), ylabel, fill="#555", font=font(12))
    img.save(fname)


def grouped(data, series_names, title, xlabel, ylabel, fname, w=980, h=560,
            colours=("#2f6f9f", "#d1495b", "#2a9d8f", "#e9a319")):
    img, d = canvas(w, h, title)
    x0, y0, x1, y1 = 90, h - 90, w - 30, 60
    axes(d, x0, y0, x1, y1)
    keys = list(data[0])
    vmax = max(max(d2.values()) for d2 in data)
    for i, key in enumerate(keys):
        slot = (x1 - x0) / len(keys)
        n = len(data)
        for j, row in enumerate(data):
            sub = slot / n
            bx = x0 + i * slot + j * sub + 0.05 * sub
            bx2 = x0 + i * slot + (j + 1) * sub - 0.05 * sub
            by = y0 - (y0 - y1) * (row[key] / vmax)
            d.rectangle([bx, by, bx2, y0], fill=colours[j % len(colours)])
        d.text((x0 + i * slot + slot / 2 - 18, y0 + 8), key, fill="#222", font=font(12))
    legend_y = h - 50
    for j, name in enumerate(series_names):
        lx = x0 + j * 190
        d.rectangle([lx, legend_y, lx + 16, legend_y + 12], fill=colours[j % len(colours)])
        d.text((lx + 22, legend_y - 2), name, fill="#222", font=font(12))
    d.text((x0, y0 + 32), xlabel, fill="#555", font=font(12))
    d.text((x0 - 80, (y0 + y1) / 2), ylabel, fill="#555", font=font(12))
    img.save(fname)


def line_chart(points, title, xlabel, ylabel, fname, w=900, h=520,
               series=(("sd", "noise sd (facet-level random noise)", "#2f6f9f"),
                       ("rank", "mean absolute rank change", "#d1495b"))):
    img, d = canvas(w, h, title)
    x0, y0, x1, y1 = 90, h - 90, w - 30, 60
    axes(d, x0, y0, x1, y1)
    xs = [p[0] for p in points]
    for idx, (key, label, colour) in enumerate(series):
        vals = [p[idx] for p in points]
        vmax = max(vals) if max(vals) > 0 else 1.0
        pts = []
        for i, xv in enumerate(xs):
            px = x0 + (x1 - x0) * ((xv - min(xs)) / (max(xs) - min(xs)))
            py = y0 - (y0 - y1) * (vals[i] / vmax)
            pts.append((px, py))
        d.line(pts, fill=colour, width=3)
        for (px, py), xv, v in zip(pts, xs, vals):
            d.circle if False else d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=colour)
            d.text((px - 14, py - 20), f"{v:.3f}", fill="#222", font=font(11))
        for xv in xs:
            px = x0 + (x1 - x0) * ((xv - min(xs)) / (max(xs) - min(xs)))
            d.text((px - 12, y0 + 8), str(xv), fill="#222", font=font(12))
    legend_y = h - 50
    for j, (_, label, colour) in enumerate(series):
        d.line([(x0 + j * 300, legend_y + 6), (x0 + j * 300 + 26, legend_y + 6)],
              fill=colour, width=3)
        d.text((x0 + j * 300 + 32, legend_y - 2), label, fill="#222", font=font(12))
    d.text((x0, y0 + 32), xlabel, fill="#555", font=font(12))
    d.text((x0 - 80, (y0 + y1) / 2), ylabel, fill="#555", font=font(12))
    img.save(fname)


def fig1_lattice():
    w, h = 1000, 700
    img, d = canvas(w, h, "Figure 1. Face lattice of the 3-simplex: 4 vertices, 6 edges, "
                       "4 faces, 1 cell = 15 relational slots")
    W = (150, 420); C = (860, 420); M = (505, 640); K = (505, 210)
    pts = {"W": W, "C": C, "M": M, "K": K}
    edges = [("W", "C"), ("W", "M"), ("W", "K"), ("C", "M"), ("C", "K"), ("M", "K")]
    for a, b in edges:
        d.line([pts[a], pts[b]], fill="#555", width=2)
    faces = [("W", "C", "K"), ("W", "C", "M"), ("W", "M", "K"), ("C", "M", "K")]
    for f in faces:
        cx = sum(pts[p][0] for p in f) / 3
        cy = sum(pts[p][1] for p in f) / 3
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill="#e8f4ff")
        d.text((cx - 8, cy - 8), "F", fill="#1a5276", font=font(13, bold=True))
    cell = ((W[0] + C[0] + M[0] + K[0]) / 4, (W[1] + C[1] + M[1] + K[1]) / 4)
    d.ellipse([cell[0] - 14, cell[1] - 14, cell[0] + 14, cell[1] + 14], fill="#f6d7a8")
    d.text((cell[0] - 8, cell[1] - 8), "T", fill="#7a4a12", font=font(13, bold=True))
    for p, (x, y) in pts.items():
        d.ellipse([x - 13, y - 13, x + 13, y + 13], fill="#2f6f9f")
        d.text((x - 8, y - 9), p, fill="white", font=font(14, bold=True))
    for i, (a, b) in enumerate(edges, start=1):
        mx, my = (pts[a][0] + pts[b][0]) / 2, (pts[a][1] + pts[b][1]) / 2
        d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill="#8ab4d6")
        d.text((mx - 12, my - 16), f"e{i}", fill="#2c5b86", font=font(11))
    d.text((30, 60), "Vertices (1-pillar states): W, C, M, K", fill="#333", font=font(13))
    d.text((30, 82), "Edges (2-pillar blends): 6", fill="#333", font=font(13))
    d.text((30, 104), "Faces (3-pillar blends): 4", fill="#333", font=font(13))
    d.text((30, 126), "Cell (all four, the only fully integrated state): 1", fill="#333", font=font(13))
    d.text((30, 160), "Every non-empty subset of the four pillars corresponds to exactly one "
                      "slot;\nthe count is 2^4 - 1 = 15. The 'shape' of an assessment is which "
                      "slot it occupies,\nnot merely its four numbers.", fill="#333", font=font(12))
    img.save(f"{FIG}/fig1_face_lattice.png")


def fig2_pipeline():
    w, h = 1100, 520
    img, d = canvas(w, h, "Figure 2. Computation pipeline from facet evidence to decision")
    boxes = [
        (60, 60, 220, 140, "Facet scores s_f\n+ requirements r_f", "#dfe8f3"),
        (300, 60, 470, 140, "Pillar levels ℓ_p\n(β-weighted, guards capped)", "#dfe8f3"),
        (550, 60, 720, 140, "Deficits d_p =\nmax(0, q_p − ℓ_p)", "#dfe8f3"),
        (800, 60, 970, 140, "Structural terms\nD, S2, S3, S4, Φ", "#dfe8f3"),
        (60, 250, 230, 330, "Veto set V\n(lexicographic)", "#fde3e3"),
        (300, 250, 470, 330, "Adequacy Aa\n∈ [0,1]", "#e9f5e9"),
        (550, 250, 720, 330, "Residual risk\nR_r = R_c(1−Aa)+σR_c", "#e9f5e9"),
        (800, 250, 970, 330, "Decision\n(ABSTAIN → ALLOW)", "#eef7ee"),
    ]
    for x0, y0, x1, y1, label, fill in boxes:
        d.rectangle([x0, y0, x1, y1], fill=fill, outline="#444")
        d.text((x0 + 12, y0 + 12), label, fill="#222", font=font(13))
    arrows = [((220, 100), (300, 100)), ((470, 100), (550, 100)),
              ((720, 100), (800, 100)), ((885, 140), (885, 250)),
              ((230, 290), (300, 290)), ((470, 290), (550, 290)),
              ((720, 290), (800, 290))]
    for (a, b) in arrows:
        d.line([a, b], fill="#444", width=2)
        d.text((a[0] + 10, a[1] - 12), "", fill="#444", font=font(10))
    d.text((60, 360), "Stakes enter twice: σ floors the residual risk, and the decision bar "
                      "moves with severity,\nirreversibility and prudential mode. The veto cap is "
                      "applied last, so no surplus can buy\nback a pillar that the case declares "
                      "critical.", fill="#333", font=font(12))
    img.save(f"{FIG}/fig2_pipeline.png")


def fig3_veto_sweep():
    sweep = json.load(open(f"{R2}/B3_calibration_sweep.json"))
    variants = [v for v in sweep["variants"] if v["mode"] == "absolute"]
    data = []
    for sev in ("low", "medium", "high", "critical"):
        data.append({f"θ={v['variant'].split('_')[-1]}": v["veto_share_by_severity"][sev]
                     for v in variants})
    grouped(data, ["low", "medium", "high", "critical"],
            "Figure 3. Veto trigger rate by severity for candidate thresholds θ",
            "veto threshold (absolute deficit)", "share of confrontations triggering the veto",
            f"{FIG}/fig3_veto_sweep.png")
    with open(f"{FIG}/fig3_data.json", "w") as fh:
        json.dump(data, fh, indent=1)


def fig4_sobol():
    b4 = json.load(open(f"{R2}/B4_results.json"))
    first = b4["sobol_first_order"]
    morris = {k: 0.0 for k in first}
    for entry in b4["ranking_morris"]:
        if isinstance(entry, dict):
            morris[entry.get("param", entry.get("name"))] = entry.get("mean_abs_EE", 0.0)
    bar_chart({k: v for k, v in sorted(first.items(), key=lambda kv: -kv[1])},
              "Figure 4. First-order Sobol' index of adequacy on calibration parameters",
              "parameter", "first-order sensitivity index",
              f"{FIG}/fig4_sobol.png")
    if any(morris.values()):
        bar_chart({k: v for k, v in sorted(morris.items(), key=lambda kv: -kv[1])},
                  "Figure 4b. Morris elementary-effect mean (exploratory ranking)",
                  "parameter", "mean |elementary effect|",
                  f"{FIG}/fig4b_morris.png", colour="#d1495b")


def fig5_decisions():
    gate = json.load(open(f"{R2}/corpus_v3_gate.json"))
    dist = gate["decision_distribution"]
    bar_chart({k: v for k, v in sorted(dist.items(), key=lambda kv: -kv[1])},
              "Figure 5. Decision distribution over the 14,400 corpus confrontations",
              "decision", "share", f"{FIG}/fig5_decisions.png", colour="#2a9d8f")


def fig6_stability():
    b9 = json.load(open(f"{R2}/B9_supplementary.json"))
    pts = [(float(k.split("_")[1]), v["decision_stability"], v["mean_abs_rank_change"])
           for k, v in b9["noise_stability_by_sd"].items()]
    line_chart(pts, "Figure 6. Decision stability against random facet noise",
               "sd of facet noise", "stability / rank change",
               f"{FIG}/fig6_stability.png")
    bar_chart({"self-report optimism (+0.10)": 0.475,
               "calibration drift (sd 0.10)": 0.838,
               "adversarial inflation (+0.15)": 0.583,
               "random noise sd 0.10": 0.888,
               "random noise sd 0.02": 0.977},
              "Figure 6b. Decision stability under four perturbation regimes",
              "perturbation regime", "share of decisions unchanged",
              f"{FIG}/fig6b_perturbations.png", colour="#d1495b", w=1000, h=520)


def fig7_criticality():
    mat = json.load(open("/home/luiz/Documentos/Strata/Shared/_analysis/facets/facet_registry_summary.json"))
    dist = mat.get("criticality_distribution", {})
    bar_chart({f"level {k}": v / sum(dist.values()) for k, v in sorted(dist.items())},
              "Figure 7. Domain-facet criticality distribution (1,354 domain-facet pairs)",
              "criticality level", "share of pairs", f"{FIG}/fig7_criticality.png",
              colour="#e9a319")


if __name__ == "__main__":
    fig1_lattice()
    fig2_pipeline()
    fig3_veto_sweep()
    fig4_sobol()
    fig5_decisions()
    fig6_stability()
    fig7_criticality()
    print("figures written to", FIG)
