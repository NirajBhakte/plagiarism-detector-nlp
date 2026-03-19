# src/report_generator.py

import os
from datetime import datetime

from reportlab.lib             import colors
from reportlab.lib.pagesizes   import A4
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units       import cm
from reportlab.platypus        import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, HRFlowable,
    KeepTogether,
)
from reportlab.graphics.shapes    import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart

# ─────────────────────────────────────────────────────────── #
#  CONFIG
# ─────────────────────────────────────────────────────────── #

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

LABEL_COLORS = {
    "Copied"      : colors.HexColor("#C53030"),
    "Paraphrased" : colors.HexColor("#B7791F"),
    "Original"    : colors.HexColor("#276749"),
}
LABEL_BG = {
    "Copied"      : colors.HexColor("#FFF5F5"),
    "Paraphrased" : colors.HexColor("#FFFFF0"),
    "Original"    : colors.HexColor("#F0FFF4"),
}

BRAND_BLUE  = colors.HexColor("#2B6CB0")
BRAND_DARK  = colors.HexColor("#1A202C")
LIGHT_GREY  = colors.HexColor("#F7FAFC")
MID_GREY    = colors.HexColor("#CBD5E0")
HEADER_BG   = colors.HexColor("#2D3748")

PAGE_W = A4[0] - 4 * cm   # usable width (2cm margins each side)


# ─────────────────────────────────────────────────────────── #
#  STYLES
# ─────────────────────────────────────────────────────────── #

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "T", parent=base["Title"],
            fontSize=22, textColor=BRAND_DARK,
            spaceAfter=4, spaceBefore=0,
        ),
        "subtitle": ParagraphStyle(
            "Sub", parent=base["Normal"],
            fontSize=10, textColor=colors.HexColor("#718096"),
            spaceAfter=2,
        ),
        "heading": ParagraphStyle(
            "H", parent=base["Heading2"],
            fontSize=12, textColor=BRAND_BLUE,
            spaceBefore=10, spaceAfter=4,
        ),
        "cell": ParagraphStyle(
            "C", parent=base["Normal"],
            fontSize=7.5, leading=10, wordWrap="CJK",
        ),
        "cell_c": ParagraphStyle(
            "CC", parent=base["Normal"],
            fontSize=7.5, leading=10, alignment=1,
        ),
        "small": ParagraphStyle(
            "S", parent=base["Normal"],
            fontSize=7, leading=9,
            textColor=colors.HexColor("#4A5568"),
        ),
        "score_big": ParagraphStyle(
            "SB", parent=base["Normal"],
            fontSize=38, alignment=1, leading=46,
            textColor=colors.white,
        ),
        "score_sub": ParagraphStyle(
            "SS", parent=base["Normal"],
            fontSize=10, alignment=1,
            textColor=colors.HexColor("#E2E8F0"),
        ),
    }


# ─────────────────────────────────────────────────────────── #
#  COVER PAGE
# ─────────────────────────────────────────────────────────── #

def _cover_page(story, summary, S):
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("Plagiarism Detection Report", S["title"]))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=BRAND_BLUE, spaceAfter=6))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        S["subtitle"],
    ))
    story.append(Spacer(1, 0.6 * cm))

    pct   = summary.get("plagiarism_percent", 0)
    total = summary.get("total_sentences", 0)
    plag  = summary.get("plagiarized_sentences", 0)

    score_color = (colors.HexColor("#C53030") if pct >= 40
                   else colors.HexColor("#B7791F") if pct >= 20
                   else colors.HexColor("#276749"))

    # Big score block + stats side by side
    score_cell = Table(
        [[Paragraph(f"{pct}%", S["score_big"])],
         [Paragraph("Overall Plagiarism", S["score_sub"])]],
        colWidths=[5 * cm],
        rowHeights=[2.8 * cm, 0.8 * cm],
    )
    score_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), score_color),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    stats_data = [
        [Paragraph("Total Chunks",  S["subtitle"]),
         Paragraph(str(total),       S["heading"])],
        [Paragraph("Plagiarised",   S["subtitle"]),
         Paragraph(str(plag),        S["heading"])],
        [Paragraph("Original",      S["subtitle"]),
         Paragraph(str(total - plag), S["heading"])],
    ]
    stats_tbl = Table(stats_data, colWidths=[3.5 * cm, 2 * cm])
    stats_tbl.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
    ]))

    cover_row = Table(
        [[score_cell, stats_tbl]],
        colWidths=[5.5 * cm, PAGE_W - 5.5 * cm],
    )
    cover_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (1, 0), (1, 0), 24),
    ]))
    story.append(cover_row)
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────── #
#  SOURCE BREAKDOWN
# ─────────────────────────────────────────────────────────── #

def _source_breakdown(story, summary, S):
    source_breakdown = summary.get("source_breakdown", {})

    story.append(Paragraph("Per-Source Similarity Breakdown", S["heading"]))
    story.append(HRFlowable(width="100%", thickness=0.8,
                             color=MID_GREY, spaceAfter=6))

    if not source_breakdown:
        story.append(Paragraph("No plagiarism detected from any source.", S["cell"]))
        story.append(Spacer(1, 0.3 * cm))
        return

    sorted_src = sorted(source_breakdown.items(), key=lambda x: x[1], reverse=True)

    # Table
    header = [
        Paragraph("<b>Source File</b>",  S["cell_c"]),
        Paragraph("<b>Similarity %</b>", S["cell_c"]),
        Paragraph("<b>Risk</b>",         S["cell_c"]),
    ]
    rows = [header]
    for src, pct in sorted_src:
        risk       = "HIGH" if pct >= 40 else "MEDIUM" if pct >= 20 else "LOW"
        risk_color = (LABEL_COLORS["Copied"] if risk == "HIGH"
                      else LABEL_COLORS["Paraphrased"] if risk == "MEDIUM"
                      else LABEL_COLORS["Original"])
        rows.append([
            Paragraph(src,     S["cell"]),
            Paragraph(f"{pct}%", S["cell_c"]),
            Paragraph(f'<font color="{risk_color.hexval()}"><b>{risk}</b></font>',
                      S["cell_c"]),
        ])

    cw = [PAGE_W * 0.60, PAGE_W * 0.22, PAGE_W * 0.18]
    tbl = Table(rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",           (0, 0), (-1, -1), 0.4, MID_GREY),
        ("FONTSIZE",       (0, 0), (-1, -1), 8),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("ALIGN",          (1, 0), (2, -1),  "CENTER"),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))

    # Bar chart — only if more than one source
    if len(sorted_src) >= 1:
        chart_h = max(2 * cm, len(sorted_src) * 1 * cm)
        drawing = Drawing(PAGE_W, chart_h + 1 * cm)

        bc = HorizontalBarChart()
        bc.x      = 3.5 * cm
        bc.y      = 0.3 * cm
        bc.height = chart_h
        bc.width  = PAGE_W - 4 * cm

        pct_vals = [p for _, p in sorted_src]
        bc.data   = [pct_vals]

        bc.valueAxis.valueMin  = 0
        bc.valueAxis.valueMax  = max(100, max(pct_vals) + 5)
        bc.valueAxis.valueStep = 20
        bc.categoryAxis.categoryNames = [s for s, _ in sorted_src]
        bc.categoryAxis.labels.fontSize = 7
        bc.bars[0].fillColor = BRAND_BLUE

        drawing.add(bc)
        story.append(drawing)
        story.append(Spacer(1, 0.3 * cm))


# ─────────────────────────────────────────────────────────── #
#  SENTENCE-LEVEL DETAIL TABLE
# ─────────────────────────────────────────────────────────── #

def _detail_table(story, results, S):
    story.append(PageBreak())
    story.append(Paragraph("Sentence-Level Analysis", S["heading"]))
    story.append(HRFlowable(width="100%", thickness=0.8,
                             color=MID_GREY, spaceAfter=6))

    if not results:
        story.append(Paragraph("No results to display.", S["cell"]))
        return

    # Column widths — adjusted so nothing gets squished
    cw = [
        0.6  * cm,   # #
        PAGE_W * 0.30,  # Student chunk
        PAGE_W * 0.30,  # Best match
        PAGE_W * 0.16,  # Source file
        PAGE_W * 0.09,  # Score
        PAGE_W * 0.11,  # Label
    ]

    header = [
        Paragraph("<b>#</b>",                  S["cell_c"]),
        Paragraph("<b>Student Chunk</b>",       S["cell"]),
        Paragraph("<b>Best Match</b>",          S["cell"]),
        Paragraph("<b>Source File</b>",         S["cell"]),
        Paragraph("<b>Score</b>",               S["cell_c"]),
        Paragraph("<b>Label</b>",               S["cell_c"]),
    ]

    all_rows = [header]

    for idx, item in enumerate(results, start=1):
        label      = item.get("Category", "Original")
        lc         = LABEL_COLORS.get(label, colors.black)
        score      = item.get("Similarity Score", 0)
        src_file   = item.get("Source File", "—")

        # Truncate long text sensibly
        student_txt = item.get("Student Sentence", "")[:220]
        matched_txt = item.get("Matched Source",   "")[:220]

        all_rows.append([
            Paragraph(str(idx),    S["small"]),
            Paragraph(student_txt, S["cell"]),
            Paragraph(matched_txt, S["cell"]),
            Paragraph(src_file,    S["small"]),
            Paragraph(str(score),  S["small"]),
            Paragraph(
                f'<font color="{lc.hexval()}"><b>{label}</b></font>',
                S["cell_c"],
            ),
        ])

    tbl = Table(all_rows, colWidths=cw, repeatRows=1)

    # Build row-by-row background for label column
    row_styles = [
        ("BACKGROUND",    (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID_GREY),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (0, -1),  "CENTER"),
        ("ALIGN",         (4, 0), (5, -1),  "CENTER"),
    ]

    for i, item in enumerate(results, start=1):
        label = item.get("Category", "Original")
        bg    = LABEL_BG.get(label, colors.white)
        row_styles.append(("BACKGROUND", (5, i), (5, i), bg))
        # Alternating row tint on data columns
        if i % 2 == 0:
            row_styles.append(("BACKGROUND", (0, i), (4, i), LIGHT_GREY))

    tbl.setStyle(TableStyle(row_styles))
    story.append(tbl)


# ─────────────────────────────────────────────────────────── #
#  PUBLIC FUNCTIONS
# ─────────────────────────────────────────────────────────── #

def generate_pdf_report(results: list, summary: dict,
                         output_path: str = None) -> str:
    """Save PDF to disk. Called by detector.py after every run."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    if output_path is None:
        ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(REPORTS_DIR, f"plagiarism_report_{ts}.pdf")

    _build_pdf(results, summary, output_path)
    print(f"PDF report saved at:\n  {output_path}")
    return output_path


def generate_pdf_report_bytes(results: list, summary: dict) -> bytes:
    """Return PDF as bytes (used by API streaming endpoint)."""
    import io
    buf = io.BytesIO()
    _build_pdf(results, summary, buf)
    buf.seek(0)
    return buf.read()


def _build_pdf(results, summary, dest):
    """Core builder — dest can be a file path string or a BytesIO buffer."""
    doc = SimpleDocTemplate(
        dest,
        pagesize     = A4,
        leftMargin   = 2 * cm,
        rightMargin  = 2 * cm,
        topMargin    = 1.8 * cm,
        bottomMargin = 1.8 * cm,
        title        = "Plagiarism Detection Report",
    )

    S     = _build_styles()
    story = []

    _cover_page(story, summary, S)
    _source_breakdown(story, summary, S)
    _detail_table(story, results, S)

    doc.build(story)