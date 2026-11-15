r"""Render the paper's equations to 300-dpi PNG with a small layout engine
over the parse tree produced by build_omml.py.

Reference: 1 pt = 4.167 px at 300 dpi, so the base size (11 pt, the body
size of the docx) is 46 px. All drawing uses the text *baseline* as the
vertical datum (PIL anchor "ls").
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont
from build_omml import tokenize, parse_seq

DPI = 300
BASE = 46
PAD = 16

SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
ITAL = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
SAN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for p in (SERIF, ITAL, SAN):
    if not os.path.exists(p):
        raise SystemExit(f"missing font: {p}")

GREEK = set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩϕΦ")
OPS = set("−+=≤≥≠≈→·×±∩∪∈⊂⊃⊆≡∓√")
PUNCT = set("|‖()[]{},:⟨⟩")

_cache = {}

def _load(path, size):
    size = int(round(size))
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]

def roman(size):
    return _load(SERIF, size)

def italic(size):
    return _load(ITAL, size)

def sans(size):
    return _load(SAN, size)

def has(font, ch):
    return font.getmask(ch).getbbox() is not None and \
        font.getmask(ch).getbbox() != font.getmask("\ue000").getbbox()

def pick(text, size):
    """Choose the font for a leaf token."""
    if len(text) == 1 and text.isalpha() and text not in GREEK:
        return italic(size)
    if text.isalnum() and len(text) > 1:
        return roman(size)
    f = roman(size)
    if all(has(f, c) for c in text):
        return f
    return sans(size)

def leaf(node, s):
    kind, text = node[0], node[1]
    if kind == "sep":
        return sans(s).getlength(",") + 0.14 * s, 0.70 * s, 0.24 * s
    if text in (" ", "  "):
        return (0.62 * s if len(text) == 1 else 1.24 * s), 0.0, 0.0
    f = pick(text, s)
    w = f.getlength(text)
    if text in OPS:
        w += 0.32 * s
    elif text in PUNCT:
        w += 0.06 * s
    if text.isdigit():
        return w, 0.66 * s, 0.22 * s
    return w, 0.72 * s, 0.24 * s

def m_seq(nodes, s):
    w = asc = desc = 0.0
    for n in nodes:
        nw, na, nd = metrics(n, s)
        w += nw
        asc = max(asc, na)
        desc = max(desc, nd)
    return w, asc, desc

def delim_width(op, cl, h, s):
    ds = max(s, h * 0.92)
    return sans(ds).getlength(op) + sans(ds).getlength(cl) + 0.12 * s

def metrics(node, s):
    kind = node[0]
    if kind in ("run", "sym", "sep"):
        return leaf(node, s)
    if kind == "frac":
        wn, an, dn = m_seq(node[1], s)
        wd, ad, dd = m_seq(node[2], s)
        axis, gap = 0.28 * s, 0.10 * s
        return max(wn, wd) + 0.24 * s, axis + gap + an + dn, -axis + gap + ad + dd
    if kind == "rad":
        wc, ac, dc = m_seq(node[1], s)
        gw = sans(1.15 * s).getlength("√")
        return gw + wc + 0.06 * s, max(ac, 0.80 * s) + 0.08 * s, dc
    if kind == "nary":
        os_ = 1.35 * s
        w_op = sans(os_).getlength(node[1])
        a_op, d_op = 0.72 * os_, 0.28 * os_
        gap = 0.12 * s
        ss = 0.60 * s
        lim_w = 0.0
        asc, desc = a_op, d_op
        if node[2]:
            ws, a2, d2 = m_seq(node[2], ss)
            lim_w = max(lim_w, ws)
            desc = max(desc, d_op + gap + a2 + d2)
        if node[3]:
            ws, a2, d2 = m_seq(node[3], ss)
            lim_w = max(lim_w, ws)
            asc = max(asc, a_op + gap + a2 + d2)
        wa, aa, da = m_seq(node[4], s)
        body = max(w_op, lim_w)
        return body + 0.22 * s + wa, max(asc, aa), max(desc, da)
    if kind == "fnary":
        wn = roman(s).getlength(node[1])
        ss = 0.60 * s
        asc, desc = 0.72 * s, 0.24 * s
        lim_w = 0.0
        if node[2]:
            ws, a2, d2 = m_seq(node[2], ss)
            lim_w = max(lim_w, ws)
            desc = max(desc, 0.24 * s + 0.10 * s + a2 + d2)
        if node[3]:
            ws, a2, d2 = m_seq(node[3], ss)
            lim_w = max(lim_w, ws)
            asc = max(asc, 0.72 * s + 0.10 * s + a2 + d2)
        wn = max(wn, lim_w)
        wc, ac, dc = m_seq(node[6], s)
        dw = 0.10 * s if node[4] is None else delim_width(node[4], node[5], ac + dc, s)
        return wn + dw + wc, max(asc, ac), max(desc, dc)
    if kind == "funcd":
        wn = roman(s).getlength(node[1])
        wc, ac, dc = m_seq(node[4], s)
        return wn + delim_width(node[2], node[3], ac + dc, s) + wc, ac, dc
    if kind == "delim":
        wc, ac, dc = m_seq(node[3], s)
        return delim_width(node[1], node[2], ac + dc, s) + wc + 0.08 * s, ac, dc
    if kind == "sub":
        wb, ab, db = m_seq(node[1], s)
        ws, a2, d2 = m_seq(node[2], 0.66 * s)
        drop = 0.20 * s
        return wb + ws + 0.05 * s, max(ab, a2 + drop), max(db, d2 + drop)
    if kind == "sup":
        wb, ab, db = m_seq(node[1], s)
        ws, a2, d2 = m_seq(node[2], 0.66 * s)
        rise = 0.40 * s
        return wb + ws + 0.04 * s, max(ab, a2 + rise), max(db, d2 + rise - 0.20 * s)
    if kind == "subsup":
        wb, ab, db = m_seq(node[1], s)
        w1, a1, d1 = m_seq(node[2], 0.60 * s)
        w2, a2, d2 = m_seq(node[3], 0.60 * s)
        return wb + max(w1, w2) + 0.10 * s, max(ab, a2 + 0.42 * s), max(db, d1 + 0.22 * s)
    if kind == "acc":
        wa, aa, da = m_seq(node[1], s)
        return wa, aa + 0.12 * s, da
    return 0.0, 0.0, 0.0

def draw_seq(gc, nodes, x, baseline, s):
    for node in nodes:
        x += draw(gc, node, x, baseline, s)
    return x

def draw_delim(gc, op, cl, x, baseline, content, s):
    asc, desc = m_seq(content, s)[1:]
    h = asc + desc
    ds = max(s, h * 0.92)
    f = sans(ds)
    a, d = f.getmetrics()
    top = baseline - asc
    y_base = top + a * h / (a + d)
    gc.text((x, y_base), op, font=f, fill=(0, 0, 0), anchor="ls")
    w1 = f.getlength(op)
    draw_seq(gc, content, x + w1 + 0.04 * s, baseline, s)
    gc.text((x + w1 + 0.04 * s + m_seq(content, s)[0], y_base), cl,
            font=f, fill=(0, 0, 0), anchor="ls")
    return w1 + f.getlength(cl) + 0.12 * s

def draw(gc, node, x, baseline, s):
    kind = node[0]
    if kind in ("run", "sym", "sep"):
        text = node[1]
        if text in (" ", "  "):
            return leaf(node, s)[0]
        gc.text((x, baseline), text, font=pick(text, s), fill=(0, 0, 0), anchor="ls")
        return leaf(node, s)[0]
    if kind == "frac":
        wn, an, dn = m_seq(node[1], s)
        wd, ad, dd = m_seq(node[2], s)
        axis, gap = 0.28 * s, 0.10 * s
        body = max(wn, wd)
        bar_y = int(baseline - axis)
        gc.line((x + 0.08 * s, bar_y, x + 0.08 * s + body + 0.08 * s, bar_y),
                fill=(0, 0, 0), width=2)
        draw_seq(gc, node[1], x + 0.08 * s + (body - wn) / 2, bar_y - gap - dn, s)
        draw_seq(gc, node[2], x + 0.08 * s + (body - wd) / 2, bar_y + gap + ad, s)
        return body + 0.24 * s
    if kind == "rad":
        wc, ac, dc = m_seq(node[1], s)
        f = sans(1.15 * s)
        gc.text((x, baseline), "√", font=f, fill=(0, 0, 0), anchor="ls")
        gx = x + f.getlength("√")
        top = baseline - max(ac, 0.80 * s) - 0.08 * s
        gc.line((gx, int(top), gx + wc + 0.04 * s, int(top)), fill=(0, 0, 0), width=2)
        draw_seq(gc, node[1], gx + 0.02 * s, baseline, s)
        return f.getlength("√") + wc + 0.06 * s
    if kind == "nary":
        os_ = 1.35 * s
        f = sans(os_)
        w_op = f.getlength(node[1])
        a_op, d_op = 0.72 * os_, 0.28 * os_
        ss = 0.60 * s
        gap = 0.12 * s
        lim_w = 0.0
        if node[2]:
            lim_w = max(lim_w, m_seq(node[2], ss)[0])
        if node[3]:
            lim_w = max(lim_w, m_seq(node[3], ss)[0])
        body = max(w_op, lim_w)
        cx = x + body / 2
        gc.text((x + (body - w_op) / 2, baseline), node[1], font=f, fill=(0, 0, 0), anchor="ls")
        if node[3]:
            ws, a2, d2 = m_seq(node[3], ss)
            draw_seq(gc, node[3], cx - ws / 2, baseline - a_op - gap - d2, ss)
        if node[2]:
            ws, a2, d2 = m_seq(node[2], ss)
            draw_seq(gc, node[2], cx - ws / 2, baseline + d_op + gap + a2, ss)
        wa, _, _ = m_seq(node[4], s)
        draw_seq(gc, node[4], x + body + 0.22 * s, baseline, s)
        return body + 0.22 * s + wa
    if kind == "fnary":
        ss = 0.60 * s
        wn = roman(s).getlength(node[1])
        lim_w = 0.0
        if node[2]:
            lim_w = max(lim_w, m_seq(node[2], ss)[0])
        if node[3]:
            lim_w = max(lim_w, m_seq(node[3], ss)[0])
        wn = max(wn, lim_w)
        cx = x + wn / 2
        gc.text((cx - wn / 2, baseline), node[1], font=roman(s), fill=(0, 0, 0), anchor="ls")
        if node[3]:
            ws, a2, d2 = m_seq(node[3], ss)
            draw_seq(gc, node[3], cx - ws / 2, baseline - 0.72 * s - 0.10 * s - d2, ss)
        if node[2]:
            ws, a2, d2 = m_seq(node[2], ss)
            draw_seq(gc, node[2], cx - ws / 2, baseline + 0.24 * s + 0.10 * s + a2, ss)
        if node[4] is None:
            draw_seq(gc, node[6], x + wn + 0.10 * s, baseline, s)
            return wn + 0.10 * s + m_seq(node[6], s)[0]
        return wn + draw_delim(gc, node[4], node[5], x + wn, baseline, node[6], s)
    if kind == "funcd":
        wn = roman(s).getlength(node[1])
        gc.text((x, baseline), node[1], font=roman(s), fill=(0, 0, 0), anchor="ls")
        return wn + draw_delim(gc, node[2], node[3], x + wn, baseline, node[4], s)
    if kind == "delim":
        return draw_delim(gc, node[1], node[2], x, baseline, node[3], s)
    if kind == "sub":
        wb, _, _ = m_seq(node[1], s)
        draw_seq(gc, node[1], x, baseline, s)
        ws, a2, d2 = m_seq(node[2], 0.66 * s)
        draw_seq(gc, node[2], x + wb + 0.05 * s, baseline + 0.20 * s, 0.66 * s)
        return wb + ws + 0.05 * s
    if kind == "sup":
        wb, _, _ = m_seq(node[1], s)
        draw_seq(gc, node[1], x, baseline, s)
        ws, a2, d2 = m_seq(node[2], 0.66 * s)
        draw_seq(gc, node[2], x + wb + 0.04 * s, baseline - 0.40 * s, 0.66 * s)
        return wb + ws + 0.04 * s
    if kind == "subsup":
        wb, _, _ = m_seq(node[1], s)
        draw_seq(gc, node[1], x, baseline, s)
        w1, _, _ = m_seq(node[2], 0.60 * s)
        w2, _, _ = m_seq(node[3], 0.60 * s)
        draw_seq(gc, node[2], x + wb + 0.05 * s, baseline + 0.22 * s, 0.60 * s)
        draw_seq(gc, node[3], x + wb + 0.05 * s, baseline - 0.42 * s, 0.60 * s)
        return wb + max(w1, w2) + 0.10 * s
    if kind == "acc":
        wa, aa, _ = m_seq(node[1], s)
        y = int(baseline - aa - 0.06 * s)
        gc.line((x, y, x + wa, y), fill=(0, 0, 0), width=2)
        draw_seq(gc, node[1], x, baseline, s)
        return wa
    return 0.0

def render(latex, base=BASE, pad=PAD):
    nodes, _ = parse_seq(tokenize(latex), 0)
    w, asc, desc = m_seq(nodes, base)
    img = Image.new("RGB", (int(math.ceil(w)) + 2 * pad,
                            int(math.ceil(asc + desc)) + 2 * pad), (255, 255, 255))
    gc = ImageDraw.Draw(img)
    draw_seq(gc, nodes, pad, pad + asc, base)
    return img

def render_block(spec):
    if isinstance(spec, str):
        return render(spec)
    parts = [render(p) for p in spec]
    W = max(p.width for p in parts) + 2 * PAD
    H = sum(p.height for p in parts) + 2 * PAD + 12 * (len(parts) - 1)
    out = Image.new("RGB", (W, H), (255, 255, 255))
    y = PAD
    for p in parts:
        out.paste(p, (PAD, y))
        y += p.height + 12
    return out


if __name__ == "__main__":
    from equations import EQUATIONS
    out = "/home/luiz/Documentos/Strata/Shared/paper/figures"
    for lab, spec in EQUATIONS:
        im = render_block(spec)
        im.save(f"{out}/eq_{lab}.png")
        print(f"{lab}: {im.width}x{im.height} px -> {im.width/300:.2f} in")
