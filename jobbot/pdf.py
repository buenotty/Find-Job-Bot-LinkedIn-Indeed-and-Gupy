from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from fpdf import FPDF

from jobbot.resume import ResumeDoc
from jobbot.store import atomic_write

_MAP = {
    "–": "-", "—": "-", "−": "-", "•": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    " ": " ", "…": "...",
}


def _fold(ch: str) -> str:
    """Keep Latin-1 characters; fold others to a Latin-1 base when one exists, else '?'."""
    if ord(ch) < 256:
        return ch
    base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
    return base if base and all(ord(c) < 256 for c in base) else "?"


def _mapped(text: str) -> str:
    for old, new in _MAP.items():
        text = text.replace(old, new)
    return text


def sanitize(text: str) -> str:
    """Map typographic characters to plain ones; fold others to Latin-1; the rest becomes '?'."""
    return "".join(_fold(ch) for ch in _mapped(text))


def lossy_chars(text: str) -> list[str]:
    """Characters that sanitize() turns into '?', in order of appearance, without repeats."""
    return list(dict.fromkeys(ch for ch in _mapped(text) if ch != "?" and _fold(ch) == "?"))


ACCENT = (31, 78, 121)
INK = (28, 28, 28)
MUTED = (100, 100, 100)
RULE = (178, 190, 205)
_MONTHS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
_BODY, _LINE = 9.5, 4.7


def _period(text: str) -> str:
    """'2024-10 - Atual' -> 'out/2024 - atual'; anything else is left alone."""
    text = re.sub(r"(\d{4})-(\d{2})", lambda m: f"{_MONTHS[int(m.group(2)) - 1]}/{m.group(1)}" if 1 <= int(m.group(2)) <= 12 else m.group(0), text)
    return text.replace(" Atual", " atual")


def render_pdf(doc: ResumeDoc) -> bytes:
    """Single-column, text-only PDF in core Helvetica: one accent colour, a hairline under each section title,
    dates on the right. No images, tables, text boxes or links, so screening parsers read it in order."""
    pdf = FPDF(format="A4")
    pdf.set_compression(False)  # plain streams are the easiest for screening parsers to read
    pdf.set_margins(17, 15, 17)
    pdf.set_auto_page_break(True, 14)
    pdf.set_title(sanitize(doc.name))
    pdf.add_page()

    def font(style: str = "", size: float = _BODY, color=INK) -> None:
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)

    def section(title: str) -> None:
        pdf.ln(3.2)
        font("B", 10.5, ACCENT)
        pdf.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y() + 0.4
        pdf.set_draw_color(*RULE)
        pdf.set_line_width(0.25)
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(2)

    def head(left_bold: str, left_plain: str, right: str) -> None:
        y = pdf.get_y()
        font("B", 10)
        pdf.write(5, left_bold)
        if left_plain:
            font("", 10)
            pdf.write(5, "  |  " + left_plain)
        if right:
            font("", 8.5, MUTED)
            w = pdf.get_string_width(right) + 1
            pdf.set_xy(pdf.w - pdf.r_margin - w, y)
            pdf.cell(w, 5, right, align="R")
        pdf.ln(5.6)

    def bullet(text: str) -> None:
        font()
        pdf.set_x(pdf.l_margin + 1.5)
        pdf.set_text_color(*ACCENT)
        pdf.cell(3.5, _LINE, "-")
        pdf.set_text_color(*INK)
        pdf.multi_cell(pdf.epw - 5, _LINE, sanitize(text), align="L", new_x="LMARGIN", new_y="NEXT")

    def paragraph(text: str, **kw) -> None:
        font()
        pdf.multi_cell(0, _LINE, sanitize(text), align="L", new_x="LMARGIN", new_y="NEXT", **kw)

    font("B", 22)
    pdf.cell(0, 9.5, sanitize(doc.name), new_x="LMARGIN", new_y="NEXT")
    if doc.headline:
        font("", 11.5, ACCENT)
        pdf.cell(0, 6, sanitize(doc.headline), new_x="LMARGIN", new_y="NEXT")
    font("", 8.5, MUTED)
    pdf.multi_cell(0, 4.4, sanitize(doc.contact), new_x="LMARGIN", new_y="NEXT")

    if doc.summary:
        section("Resumo")
        paragraph(doc.summary)
    if doc.experiences:
        section("Experiência")
        for e in doc.experiences:
            head(sanitize(e["title"]), sanitize(e["company"]), sanitize(_period(e["period"])))
            for b in e["bullets"]:
                bullet(b)
            pdf.ln(1.2)
    if doc.projects:
        section("Projetos e voluntariado")
        for x in doc.projects:
            head(sanitize(x["name"]), "", sanitize(x["label"]))
            for b in x["bullets"]:
                bullet(b)
            pdf.ln(1.2)
    if doc.skill_groups or doc.skills:
        section("Competências")
        if doc.skill_groups:
            for label, names in doc.skill_groups:
                paragraph(f"**{label}:** {', '.join(names)}", markdown=True)
        else:
            paragraph(", ".join(doc.skills))
    if doc.education:
        section("Formação")
        for line in doc.education:
            paragraph(line)
    if doc.certifications:
        section("Certificações")
        paragraph("; ".join(doc.certifications))
    if doc.languages:
        section("Idiomas")
        paragraph("; ".join(doc.languages))
    return bytes(pdf.output())


def write_pdf(doc: ResumeDoc, path: Path) -> None:
    atomic_write(path, render_pdf(doc))


def extract_text(path: Path) -> str:
    from pypdf import PdfReader  # dev dependency, imported lazily

    return "\n".join(page.extract_text() for page in PdfReader(str(path)).pages)
