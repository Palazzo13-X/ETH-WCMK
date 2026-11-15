"""Shared DOCX builder helpers for ETH-WCMK v14 deliverables.

Mirrors the layout of `Shared/ETH-WCMK v9.docx` (Letter page, 1 in margins,
Times New Roman 11 pt body, Heading 1 numbered sections, CaptionCenter captions
for tables/figures/equations, SmallText for the reference list), but renders the
mathematics as native Word OMML instead of PNG images.
"""
import sys
sys.path.insert(0, "/home/luiz/Documentos/Strata/Shared/_analysis/paper")

from docx import Document
from docx.shared import Pt, Inches, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

from build_omml import to_omml

M_NS = "http://schemas.openxmlformats.org/office/document/2006/math"

EXTRA_SYMBOLS = {
    "zeta": "ζ", "Psi": "Ψ", "psi": "ψ", "varphi": "φ", "Theta": "Θ",
    "kappa": "κ", "nu": "ν", "xi": "ξ", "alpha": "α", "beta": "β",
    "times": "×", "bullet": "·", "neq": "≠", "equiv": "≡", "supseteq": "⊇",
    "langle": "⟨", "rangle": "⟩", "cdot": "·", "cdots": "…",
    "abs": "", "mathrm": "", "text": "", "mathcal": "",
}


def _patched():
    import build_omml
    build_omml.SYMBOLS.update(EXTRA_SYMBOLS)
    return build_omml


_patched()


def new_document():
    """Letter page, 1 in side margins, 0.85 in top/bottom, TNR 11 pt body."""
    doc = Document()
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)
    # make the font apply to every script of the document
    from docx.oxml import OxmlElement
    rpr = normal.element.get_or_add_rPr()
    rfonts = OxmlElement("w:rFonts")
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn("w:" + attr), "Times New Roman")
    rpr.append(rfonts)

    h1 = doc.styles["Heading 1"]
    h1.font.name = "Times New Roman"
    h1.font.size = Pt(14)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0x36, 0x5F, 0x91)
    h1.paragraph_format.space_before = Pt(10)
    h1.paragraph_format.space_after = Pt(4)

    h2 = doc.styles["Heading 2"]
    h2.font.name = "Times New Roman"
    h2.font.size = Pt(12)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0x4F, 0x81, 0xBD)
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(4)

    h3 = doc.styles["Heading 3"]
    h3.font.name = "Times New Roman"
    h3.font.size = Pt(11)
    h3.font.bold = True
    h3.font.italic = True
    h3.font.color.rgb = RGBColor(0x4F, 0x81, 0xBD)

    from docx.enum.style import WD_STYLE_TYPE
    for name, italic in (("CaptionCenter", False), ("SmallText", False), ("SourceNote", True)):
        try:
            st = doc.styles[name]
        except KeyError:
            st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.font.name = "Times New Roman"
        st.font.size = Pt(10)
        st.font.italic = italic
        if name == "CaptionCenter":
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            st.paragraph_format.space_after = Pt(8)
        else:
            st.paragraph_format.space_after = Pt(4)
    return doc


def title_block(doc, title, authors, affiliation, meta=None):
    p = doc.add_paragraph(title)
    p.style = doc.styles["Normal"]
    run = p.runs[0]
    run.font.size = Pt(16)
    run.font.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    if authors:
        q = doc.add_paragraph(authors)
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if affiliation:
        q = doc.add_paragraph(affiliation)
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.runs[0].font.size = Pt(10)
        q.runs[0].font.italic = True
    if meta:
        q = doc.add_paragraph(meta)
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.runs[0].font.size = Pt(9)
        q.runs[0].font.italic = True
    return doc


def para(doc, text, style=None, align=None, size=None, bold=False, italic=False):
    p = doc.add_paragraph()
    if style is not None:
        p.style = doc.styles[style]
    run = p.add_run(text)
    if size:
        run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def bullets(doc, items, indent=0.25):
    for it in items:
        p = doc.add_paragraph(it, style="List Bullet")
        p.paragraph_format.left_indent = Inches(indent)
        p.paragraph_format.space_after = Pt(3)


def caption(doc, text):
    p = doc.add_paragraph(text)
    p.style = doc.styles["CaptionCenter"]
    return p


def equation(doc, latex, label=None, note=None, prefix="Equation"):
    """Append a display equation rendered as native Word math (OMML)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    xml = to_omml(latex)
    p._p.append(parse_xml(xml))
    if label:
        caption(doc, f"{prefix} ({label}). {note}")
    return p


def table(doc, header, rows, widths=None, caption_text=None, font=9.5, header_font=9.5):
    if caption_text:
        caption(doc, caption_text)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        cell = t.rows[0].cells[i]
        cell.text = str(h)
        for pr in cell.paragraphs:
            for r in pr.runs:
                r.font.size = Pt(header_font)
                r.font.bold = True
        _shade(cell)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = "" if v is None else str(v)
            for pr in cells[i].paragraphs:
                for r in pr.runs:
                    r.font.size = Pt(font)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    return t


def _shade(cell):
    from docx.oxml.ns import qn
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="E8E8E8"/>')
    tcPr.append(shd)


def figure(doc, path, caption_text, width=6.0):
    try:
        doc.add_picture(path, width=Inches(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    except Exception as exc:  # missing asset: keep the document readable
        para(doc, f"[figure unavailable: {path} — {exc}]", italic=True)
    caption(doc, caption_text)


def set_document_properties(doc, title, authors, subject, keywords, language="en-US"):
    """Fill the core properties so the file opens with a real title and author."""
    cp = doc.core_properties
    cp.title = title
    cp.author = authors
    cp.subject = subject
    cp.keywords = keywords
    cp.category = "ETH-WCMK"
    cp.language = language
    return doc


def add_running_footer(doc, running_text):
    """Footer with the running head on the left and the page number on the right."""
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.text = ""
        p.style = doc.styles["Normal"]
        run = p.add_run(running_text)
        run.font.size = Pt(9)
        run.font.name = "Times New Roman"
        run.font.italic = True
        run2 = p.add_run("\t")
        run2.font.size = Pt(9)
        begin = parse_xml('<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
        instr = parse_xml('<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w"))
        sep = parse_xml('<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
        end = parse_xml('<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
        r1 = p.add_run(); r1._r.append(begin)
        r2 = p.add_run(); r2._r.append(instr)
        r3 = p.add_run(); r3._r.append(sep)
        num = p.add_run("1"); num.font.size = Pt(9); num.font.name = "Times New Roman"
        r4 = p.add_run(); r4._r.append(end)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return doc
