"""Regenerate paper/figures/mathml/E*.mathml and paper/figures/eq_E*.png from
the canonical table in equations.py (which mirrors _analysis/formal_core/core.py).
Run:  python3 _analysis/paper/regen_equations.py
"""
import os
from build_omml import parse_seq, tokenize, mm
from render_equation import render_block
from equations import EQUATIONS

FIG = "/home/luiz/Documentos/Strata/Shared/paper/figures"
MATHML = os.path.join(FIG, "mathml")
os.makedirs(MATHML, exist_ok=True)

def mathml(spec):
    if isinstance(spec, str):
        nodes, _ = parse_seq(tokenize(spec), 0)
        body = mm(nodes)
    else:
        rows = "".join(f"<mtr><mtd>{mm(parse_seq(tokenize(l), 0)[0])}</mtd></mtr>" for l in spec)
        body = f'<mtable rowspacing="0.5ex">{rows}</mtable>'
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">'
            + body + "</math>\n")

def xml_ok(path):
    from xml.etree import ElementTree as ET
    try:
        ET.parse(path); return True
    except Exception as e:
        return f"XML error: {e}"

report = []
for lab, spec in EQUATIONS:
    f = os.path.join(MATHML, f"{lab}.mathml")
    open(f, "w").write(mathml(spec))
    ok = xml_ok(f)
    im = render_block(spec)
    im.save(os.path.join(FIG, f"eq_{lab}.png"))
    report.append((lab, len(mathml(spec)), f"{im.width}x{im.height}", ok))
print(f"{len(report)} equations regenerated; XML parse failures: "
      f"{[r[0] for r in report if r[3] is not True]}")
for r in report: print(r)
