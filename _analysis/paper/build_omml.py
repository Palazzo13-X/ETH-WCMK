r"""Minimal LaTeX-subset -> OMML (Office Math Markup Language) converter.

Supports the subset used by the ETH-WCMK equation set: \frac, \sqrt,
\sum/\prod with limits, \max/\min/clip as functions, \left|..\right| and
\lvert..\rvert, sub/superscripts, \hat, \bar, \mathbf/\text (rendered as
plain), greek letters and comparison/set symbols (mapped to Unicode).
"""

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "eta": "η", "theta": "θ", "lambda": "λ", "mu": "μ",
    "zeta": "ζ", "kappa": "κ", "Psi": "Ψ", "psi": "ψ", "nu": "ν", "chi": "χ",
    "xi": "ξ", "varphi": "φ", "star": "∗", "equiv": "≡", "wedge": "∧",
    "Rightarrow": "⇒", "leftarrow": "←", "longrightarrow": "⟶", "vee": "∨",
    "lfloor": "⌊", "rfloor": "⌋", "cdot": "·",
    "omega": "ω", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "Phi": "Φ",
    "Delta": "Δ", "Sigma": "∑", "Pi": "∏", "cdot": "·", "times": "×",
    "le": "≤", "ge": "≥", "ne": "≠", "approx": "≈", "in": "∈", "pm": "±",
    "infty": "∞", "to": "→", "cap": "∩", "cup": "∪", "prime": "'",
    "ell": "ℓ", "lbrace": "{", "rbrace": "}", "quad": " ", "qquad": "  ",
    "mid": "∣", "setminus": "∖", "geq": "≥", "leq": "≤", "neq": "≠", "setminus": "∖",
    "mathbb": "", "supset": "⊃", "subset": "⊂", "inseteq": "⊆",
    "forall": "∀", "exists": "∃", "land": "∧", "lor": "∨", "partial": "∂",
    "langle": "⟨", "rangle": "⟩", "Vert": "‖", "lVert": "‖", "rVert": "‖",
    "lvert": "|", "rvert": "|", "quad": " ",
}
FUNCS = {"max", "min", "clip", "argmax", "argmin", "rank", "sign"}


def tokenize(s):
    toks, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch != "\\":
            toks.append((ch, None))
            i += 1
            continue
        j = i + 1
        while j < n and s[j].isalpha():
            j += 1
        name = s[i + 1:j]
        if name:
            toks.append((name, None))
            i = j
        else:
            c = s[i + 1] if i + 1 < n else ""
            toks.append((SYMBOLS.get(c, c), None))
            i += 2
    return toks


def parse_seq(toks, pos, stop=None):
    nodes = []
    while pos < len(toks):
        name = toks[pos][0]
        if stop is not None and name == stop:
            pos += 1
            break
        if name == "{":
            g, pos = parse_group(toks, pos)
            nodes.extend(g)
            continue
        pos += 1
        if name in ("}", " ", ";", "!"):
            continue
        if name == ",":
            nodes.append(("sep", ","))
            continue
        if name == "frac":
            num, pos = parse_group(toks, pos)
            den, pos = parse_group(toks, pos)
            nodes.append(("frac", num, den))
        elif name == "sqrt":
            arg, pos = parse_group(toks, pos)
            nodes.append(("rad", arg))
        elif name in ("sum", "prod"):
            sub = sup = None
            while pos < len(toks) and toks[pos][0] in ("_", "^"):
                op = toks[pos][0]
                pos += 1
                g, pos = parse_group(toks, pos)
                if op == "_":
                    sub = g
                else:
                    sup = g
            while pos < len(toks) and toks[pos][0] == " ":
                pos += 1
            arg, pos = parse_group(toks, pos)
            nodes.append(("nary", "∑" if name == "sum" else "∏", sub, sup, arg))
        elif name in FUNCS:
            while pos < len(toks) and toks[pos][0] == " ":
                pos += 1
            lim_sub = lim_sup = None
            while pos < len(toks) and toks[pos][0] in ("_", "^"):
                op2 = toks[pos][0]
                pos += 1
                g, pos = parse_group(toks, pos)
                if op2 == "_":
                    lim_sub = g
                else:
                    lim_sup = g
            if lim_sub or lim_sup:
                while pos < len(toks) and toks[pos][0] == " ":
                    pos += 1
                if pos < len(toks) and toks[pos][0] == "lbrace":
                    pos += 1
                    a, pos = parse_seq(toks, pos, stop="rbrace")
                    op, cl = "{", "}"
                else:
                    a, pos = parse_group(toks, pos)
                    op, cl = None, None
                nodes.append(("fnary", name, lim_sub, lim_sup, op, cl, a))
                continue
            if pos < len(toks) and toks[pos][0] == "left":
                pos += 1
                op = toks[pos][0] if pos < len(toks) else "("
                pos += 1
                arg, pos = parse_seq(toks, pos, stop="right")
                cl = toks[pos][0] if pos < len(toks) else op
                pos += 1
            elif pos < len(toks) and toks[pos][0] == "{":
                arg, pos = parse_group(toks, pos)
                op, cl = "(", ")"
            elif pos < len(toks) and toks[pos][0] in ("lbrace", "(", "["):
                opener = toks[pos][0]
                pos += 1
                if opener == "lbrace":
                    arg, pos = parse_seq(toks, pos, stop="rbrace")
                    op, cl = "{", "}"
                elif opener == "(":
                    arg, pos = parse_seq(toks, pos, stop=")")
                    op, cl = "(", ")"
                else:
                    arg, pos = parse_seq(toks, pos, stop="]")
                    op, cl = "[", "]"
            else:
                arg, pos = parse_group(toks, pos)
                op, cl = "(", ")"
            nodes.append(("funcd", name, op, cl, arg))
        elif name in ("hat", "bar", "vec", "widehat", "overline"):
            arg, pos = parse_group(toks, pos)
            chr_ = {"hat": "̂", "widehat": "̂", "bar": "̄",
                    "overline": "̄", "vec": "⃗"}[name]
            nodes.append(("acc", arg, chr_))
        elif name in ("mathbf", "mathrm", "mathcal", "text", "mathbb"):
            arg, pos = parse_group(toks, pos)
            nodes.extend(arg)
        elif name == "left":
            op = toks[pos][0] if pos < len(toks) else "("
            pos += 1
            arg, pos = parse_seq(toks, pos, stop="right")
            closer = toks[pos][0] if pos < len(toks) else op
            pos += 1
            nodes.append(("delim", op, closer, arg))
        elif name in ("lvert", "lVert", "langle"):
            opener = {"lvert": "|", "lVert": "‖", "langle": "⟨"}[name]
            arg, pos = parse_seq(toks, pos, stop="rvert")
            closer = {"|": "|", "‖": "‖", "⟨": "⟩"}[opener]
            nodes.append(("delim", opener, closer, arg))
        elif name in SYMBOLS:
            nodes.append(("sym", SYMBOLS[name]))
        elif name == "_":
            base = nodes.pop() if nodes else None
            b, pos = parse_group(toks, pos)
            nodes.append(("sub", [base] if base else [], b))
        elif name == "^":
            base = nodes.pop() if nodes else None
            b, pos = parse_group(toks, pos)
            if isinstance(base, tuple) and base[0] == "sub":
                nodes.append(("subsup", base[1], base[2], b))
            else:
                nodes.append(("sup", [base] if base else [], b))
        elif name == "-":
            nodes.append(("sym", "−"))
        elif name == "+":
            nodes.append(("sym", "+"))
        elif name == "=":
            nodes.append(("sym", "="))
        elif name == "*":
            nodes.append(("sym", "·"))
        elif name.isdigit() or name == ".":
            j = pos
            while j < len(toks) and (toks[j][0].isdigit() or toks[j][0] == "."):
                j += 1
            nodes.append(("run", "".join(t[0] for t in toks[pos - 1:j])))
            pos = j
        elif name.isalpha():
            nodes.append(("run", name))
        else:
            nodes.append(("sym", name))
    return nodes, pos


def parse_group(toks, pos):
    if pos >= len(toks):
        return [], pos
    if toks[pos][0] == "{":
        return parse_seq(toks, pos + 1, stop="}")
    if toks[pos][0] in (" ", ";", "!"):
        return [], pos + 1
    name = toks[pos][0]
    if name in SYMBOLS:
        return [("sym", SYMBOLS[name])], pos + 1
    if name.isalnum() or name == ".":
        return [("run", name)], pos + 1
    return [("sym", name)], pos + 1


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ser(nodes):
    out = []
    for node in nodes:
        kind = node[0]
        if kind == "run":
            out.append(f'<m:r><m:t>{_esc(node[1])}</m:t></m:r>')
        elif kind == "sym":
            out.append(f'<m:r><m:t>{_esc(node[1])}</m:t></m:r>')
        elif kind == "sep":
            out.append('<m:r><m:t>,</m:t></m:r>')
        elif kind == "frac":
            out.append(f'<m:f><m:num>{ser(node[1])}</m:num>'
                       f'<m:den>{ser(node[2])}</m:den></m:f>')
        elif kind == "rad":
            out.append('<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/>'
                       f'<m:e>{ser(node[1])}</m:e></m:rad>')
        elif kind == "nary":
            sub = f'<m:sub>{ser(node[2])}</m:sub>' if node[2] else '<m:sub/>'
            sup = f'<m:sup>{ser(node[3])}</m:sup>' if node[3] else '<m:sup><m:r><m:t xml:space="preserve"> </m:t></m:r></m:sup>'
            out.append('<m:nary><m:naryPr><m:chr m:val="' + _esc(node[1]) +
                       '"/><m:limLoc m:val="subSup"/></m:naryPr>'
                       f'{sub}{sup}<m:e>{ser(node[4])}</m:e></m:nary>')
        elif kind == "funcd":
            out.append(f'<m:r><m:t>{_esc(node[1])}</m:t></m:r>'
                       f'<m:d><m:dPr><m:openChr m:val="{_esc(node[2])}"/>'
                       f'<m:closeChr m:val="{_esc(node[3])}"/></m:dPr>'
                       f'<m:e>{ser(node[4])}</m:e></m:d>')
        elif kind == "fnary":
            name, sub, sup, op, cl, arg = node[1], node[2], node[3], node[4], node[5], node[6]
            base = f'<m:r><m:t>{_esc(name)}</m:t></m:r>'
            if sub and sup:
                base = f'<m:sSubSup><m:e>{base}</m:e><m:sub>{ser(sub)}</m:sub><m:sup>{ser(sup)}</m:sup></m:sSubSup>'
            elif sub:
                base = f'<m:sSub><m:e>{base}</m:e><m:sub>{ser(sub)}</m:sub></m:sSub>'
            elif sup:
                base = f'<m:sSup><m:e>{base}</m:e><m:sup>{ser(sup)}</m:sup></m:sSup>'
            if op and arg:
                out.append(f'{base}<m:d><m:dPr><m:openChr m:val="{_esc(op)}"/>'
                           f'<m:closeChr m:val="{_esc(cl)}"/></m:dPr>'
                           f'<m:e>{ser(arg)}</m:e></m:d>')
            else:
                out.append(base)
        elif kind == "delim":
            out.append(f'<m:d><m:dPr><m:openChr m:val="{_esc(node[1])}"/>'
                       f'<m:closeChr m:val="{_esc(node[2])}"/></m:dPr>'
                       f'<m:e>{ser(node[3])}</m:e></m:d>')
        elif kind == "sub":
            out.append(f'<m:sSub><m:e>{ser(node[1])}</m:e>'
                       f'<m:sub>{ser(node[2])}</m:sub></m:sSub>')
        elif kind == "sup":
            out.append(f'<m:sSup><m:e>{ser(node[1])}</m:e>'
                       f'<m:sup>{ser(node[2])}</m:sup></m:sSup>')
        elif kind == "subsup":
            out.append(f'<m:sSubSup><m:e>{ser(node[1])}</m:e>'
                       f'<m:sub>{ser(node[2])}</m:sub>'
                       f'<m:sup>{ser(node[3])}</m:sup></m:sSubSup>')
        elif kind == "acc":
            out.append(f'<m:acc><m:accPr><m:chr m:val="{_esc(node[2])}"/></m:accPr>'
                       f'<m:e>{ser(node[1])}</m:e></m:acc>')
        else:
            out.append(f'<m:r><m:t>{_esc(node)}</m:t></m:r>')
    return "".join(out)


def to_omml(latex):
    nodes, _ = parse_seq(tokenize(latex), 0)
    return (f'<m:oMathPara xmlns:m="{M_NS}">'
            f'<m:oMath>{ser(nodes)}</m:oMath></m:oMathPara>')


if __name__ == "__main__":
    samples = [
        r"T(E,a) = \sum_{i<j} \alpha_{ij}(E) \left| (a_i - \hat{r}_i) - (a_j - \hat{r}_j) \right|",
        r"a_i = \frac{\ell_i}{\sum_k \ell_k}",
        r"d_i = \max\{0, q_i - \ell_i\}",
        r"Aa = 1 - D - \gamma S_2 - \eta S_3 - \omega S_4 - \rho u - \delta \Phi",
        r"S_2 = \sum_{(i,j) \in E} \alpha_{ij} \min(d_i, d_j)",
        r"R_r = R_c (1 - Aa) + \sigma R_c",
        r"\Phi = \frac{\sum_f c_f w_f \max(0, r_f - \ell_f)}{\sum_f c_f w_f}",
        r"v_i \cdot v_j = -\frac{1}{3}",
        r"S_4 = (\prod_i d_i)^{1/4}",
        r"\bar{A} = \frac{1}{n}\sum_{i} A_i",
    ]
    for s in samples:
        o = to_omml(s)
        flat = o.replace("<m:r><m:t>", "|").replace("</m:t></m:r>", "")
        print(s)
        print("   ", flat[:300])


def _is_number(text):
    return all(ch.isdigit() or ch == "." for ch in text)


def mm(nodes):
    """Serialize a parse tree to presentation MathML."""
    parts = []
    for node in nodes:
        kind = node[0]
        if kind in ("run", "sym"):
            text = node[1]
            if _is_number(text):
                parts.append(f"<mn>{text}</mn>")
            elif text in ("−", "+", "=", "≤", "≥", "≠", "≈", "→", "·", "×", "±", "∩", "∪"):
                parts.append(f"<mo>{text}</mo>")
            elif text in ("(", ")", "[", "]", "{", "}", "|", "‖", ":", "<", ">"):
                parts.append(f"<mo>{text.replace('<', '&lt;').replace('>', '&gt;')}</mo>")
            else:
                parts.append(f"<mi>{text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')}</mi>")
        elif kind == "sep":
            parts.append("<mo>,</mo>")
        elif kind == "frac":
            parts.append(f"<mfrac><mrow>{mm(node[1])}</mrow><mrow>{mm(node[2])}</mrow></mfrac>")
        elif kind == "rad":
            parts.append(f"<msqrt><mrow>{mm(node[1])}</mrow></msqrt>")
        elif kind == "nary":
            chr_ = node[1]
            sub, sup = node[2], node[3]
            if sub and sup:
                head = f"<munderover><mo>{chr_}</mo><mrow>{mm(sub)}</mrow><mrow>{mm(sup)}</mrow></munderover>"
            elif sub:
                head = f"<munder><mo>{chr_}</mo><mrow>{mm(sub)}</mrow></munder>"
            elif sup:
                head = f"<mover><mo>{chr_}</mo><mrow>{mm(sup)}</mrow></mover>"
            else:
                head = f"<mo>{chr_}</mo>"
            parts.append(head + f"<mrow>{mm(node[4])}</mrow>")
        elif kind == "funcd":
            parts.append(f"<mo>{node[1]}</mo><mrow><mo>{node[2]}</mo>{mm(node[4])}<mo>{node[3]}</mo></mrow>")
        elif kind == "fnary":
            name, sub, sup, op, cl, arg = node[1], node[2], node[3], node[4], node[5], node[6]
            base = f'<m:r><m:t>{_esc(name)}</m:t></m:r>'
            if sub and sup:
                base = f'<m:sSubSup><m:e>{base}</m:e><m:sub>{ser(sub)}</m:sub><m:sup>{ser(sup)}</m:sup></m:sSubSup>'
            elif sub:
                base = f'<m:sSub><m:e>{base}</m:e><m:sub>{ser(sub)}</m:sub></m:sSub>'
            elif sup:
                base = f'<m:sSup><m:e>{base}</m:e><m:sup>{ser(sup)}</m:sup></m:sSup>'
            if op and arg:
                out.append(f'{base}<m:d><m:dPr><m:openChr m:val="{_esc(op)}"/>'
                           f'<m:closeChr m:val="{_esc(cl)}"/></m:dPr>'
                           f'<m:e>{ser(arg)}</m:e></m:d>')
            else:
                out.append(base)
        elif kind == "delim":
            parts.append(f"<mrow><mo>{node[1]}</mo>{mm(node[3])}<mo>{node[2]}</mo></mrow>")
        elif kind == "sub":
            parts.append(f"<msub><mrow>{mm(node[1])}</mrow><mrow>{mm(node[2])}</mrow></msub>")
        elif kind == "sup":
            parts.append(f"<msup><mrow>{mm(node[1])}</mrow><mrow>{mm(node[2])}</mrow></msup>")
        elif kind == "subsup":
            parts.append(f"<msubsup><mrow>{mm(node[1])}</mrow><mrow>{mm(node[2])}</mrow>"
                         f"<mrow>{mm(node[3])}</mrow></msubsup>")
        elif kind == "acc":
            parts.append(f"<mover accent='true'><mrow>{mm(node[1])}</mrow><mo>{node[2]}</mo></mover>")
        else:
            text = node[1] if isinstance(node, tuple) else node
            parts.append(f"<mtext>{text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')}</mtext>")
    return "".join(parts)


def to_mathml(latex):
    nodes, _ = parse_seq(tokenize(latex), 0)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">'
            + mm(nodes) + "</math>\n")
