"""
reports_pdf.py - PDF reports (reportlab, English text) and section builders shared by the
website's report downloads.

A report is a title plus a list of (heading, markdown-ish text) sections. The PDF carries
the JalMitra name, the date, the location, the data years, the sources, tables, findings,
warnings, limitations and next steps that the caller passes in. Nothing is added here.
Hindi PDFs are not produced: reportlab does not shape Devanagari, so Hindi reports are
offered as Markdown.
"""

import datetime as _dt
import io
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BRAND = colors.HexColor("#0B6E4F")


def _inline(text):
    """Escape for reportlab and turn **bold** / _italic_ into tags; drop characters the base font cannot draw."""
    t = escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w])_(.+?)_(?![\w])", r"<i>\1</i>", t)
    t = t.replace("–", "-").replace("—", "-").replace("≤", "&lt;=").replace("≥", "&gt;=").replace("µ", "u")
    t = t.replace("→", "-&gt;").replace("⚠️", "Note:").replace("📍", "")
    return "".join(ch for ch in t if ord(ch) < 0x2500)


def build_pdf(title, sections, place_text="", tables=(), lang_note=""):
    """sections: [(heading, text)], tables: [(caption, [dict rows])]. Returns PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=title, author="JalMitra")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=BRAND, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=BRAND, fontSize=12.5, spaceBefore=8, spaceAfter=3)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("s", parent=body, fontSize=8, textColor=colors.grey)
    story = [Paragraph("JalMitra", ParagraphStyle("brand", parent=small, textColor=BRAND, fontSize=10)),
             Paragraph(_inline(title), h1),
             Paragraph(_inline(f"Created {_dt.date.today().isoformat()}" + (f" · {place_text}" if place_text else "")), small)]
    if lang_note:
        story.append(Paragraph(_inline(lang_note), small))
    story.append(Spacer(1, 4 * mm))
    for head, text in sections:
        if head:
            story.append(Paragraph(_inline(head), h2))
        for para in re.split(r"\n\s*\n", text or ""):
            lines = [x.strip() for x in para.split("\n") if x.strip()]
            if lines:
                story.append(Paragraph("<br/>".join(_inline(x.rstrip()) for x in lines), body))
                story.append(Spacer(1, 1.5 * mm))
    for caption, rows in tables:
        if not rows:
            continue
        cols = list(rows[0].keys())
        data = [[Paragraph(f"<b>{_inline(str(c))}</b>", small) for c in cols]] + \
               [[Paragraph(_inline("" if r.get(c) is None else str(r.get(c))), small) for c in cols] for r in rows[:200]]
        story.append(Paragraph(_inline(caption), h2))
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F3EE")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("JalMitra answers only from published sources and the user's own confirmed data. Missing "
                           "information is shown as missing. General suggestions are educational, not formal government "
                           "recommendations.", small))
    doc.build(story)
    return buf.getvalue()


def markdown(title, sections, place_text=""):
    out = [f"# {title}", f"_JalMitra · {_dt.date.today().isoformat()}" + (f" · {place_text}" if place_text else "") + "_"]
    for head, text in sections:
        out.append((f"## {head}\n\n" if head else "") + (text or ""))
    return "\n\n".join(out) + "\n"
