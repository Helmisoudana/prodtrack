import io
import re
import json
import tempfile
from datetime import datetime
from fpdf import FPDF

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


REPORT_SYSTEM_PROMPT = """You are a factory report generator for Pristini.
Your output is directly converted to a PDF document. Output ONLY the report content.

CRITICAL RULES:
- Do NOT include any preamble, introduction, or commentary like "Here is the report" or "Let me generate...".
- Do NOT explain what you are doing. Just output the report directly.
- Start immediately with the report title on the very first line.
- STRICTLY NO emojis, no unicode symbols. Use only plain ASCII text.
- Do NOT use emoji characters as section markers or decorators. Use plain text headings only.
- Do NOT use **bold** inside table cells. Tables should contain plain text only.

REPORT FORMAT:
- First line: report title (plain text, no # prefix).
- Use ## for section headings and ### for subsection headings.
- Use **bold** for key metrics and labels in paragraphs and lists.
- Use markdown tables with pipes: | Col1 | Col2 | with header row and separator (|---|---|).
- Use bullet lists (- item) for findings and recommendations.
- Use numbered lists (1. 2. 3.) for rankings or steps.
- End with a "Recommendations" or "Summary" section.
- Be thorough and data-driven with specific numbers.

CHARTS (MANDATORY):
You MUST include 2-3 chart blocks per report to visualize the key data.
Every report MUST have at least one chart. Use this exact format:

```chart
{"type": "bar", "title": "Chart Title", "labels": ["Label1", "Label2", "Label3"], "values": [10, 20, 30], "ylabel": "Unit"}
```

Chart types: bar, horizontal_bar, pie, line.

Examples of when to use each chart type:
- bar: comparing metrics across employees, machines, or shifts
- horizontal_bar: ranking employees or items by score
- pie: showing distribution (status breakdown, task completion vs interrupted)
- line: trends over time (monthly performance, daily output)

Place each chart block right after the data section it visualizes.
For a "top performers" report, you MUST include a bar chart comparing their scores.
For a "factory overview" report, you MUST include a pie chart for status distribution.
"""


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------
CHART_COLORS = ["#00b4d8", "#ff6b35", "#4ade80", "#f59e0b", "#8b5cf6",
                "#ef4444", "#06b6d4", "#ec4899", "#14b8a6", "#a855f7"]


def _generate_chart(chart_data: dict) -> str | None:
    """Generate a chart image and return the temp file path."""
    chart_type = chart_data.get("type", "bar")
    title = chart_data.get("title", "")
    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    ylabel = chart_data.get("ylabel", "")

    if not labels or not values:
        return None

    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    colors = CHART_COLORS[:len(labels)]

    if chart_type == "pie":
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct="%1.1f%%",
            colors=colors, startangle=90,
            textprops={"fontsize": 8},
        )
        for t in autotexts:
            t.set_fontsize(8)
            t.set_fontweight("bold")

    elif chart_type == "horizontal_bar":
        bars = ax.barh(labels, values, color=colors, height=0.6, edgecolor="white", linewidth=0.5)
        ax.set_xlabel(ylabel, fontsize=9, color="#555")
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                    f"{val}", va="center", fontsize=8, fontweight="bold", color="#333")
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    elif chart_type == "line":
        ax.plot(labels, values, color=CHART_COLORS[0], linewidth=2.5, marker="o",
                markersize=6, markerfacecolor="white", markeredgewidth=2, markeredgecolor=CHART_COLORS[0])
        ax.fill_between(range(len(values)), values, alpha=0.1, color=CHART_COLORS[0])
        ax.set_ylabel(ylabel, fontsize=9, color="#555")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.xticks(fontsize=8, rotation=30, ha="right")

    else:  # bar
        bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white", linewidth=0.5)
        ax.set_ylabel(ylabel, fontsize=9, color="#555")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                    f"{val}", ha="center", fontsize=8, fontweight="bold", color="#333")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.xticks(fontsize=8, rotation=30, ha="right")

    if title:
        ax.set_title(title, fontsize=11, fontweight="bold", color="#1a1a1a", pad=12)

    ax.tick_params(axis="both", labelsize=8, colors="#666")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g"))
    plt.tight_layout()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=180, bbox_inches="tight", facecolor="#fafafa")
    plt.close(fig)
    return tmp.name


# ---------------------------------------------------------------------------
# Text sanitization
# ---------------------------------------------------------------------------
def _sanitize(text: str) -> str:
    replacements = {
        "\u2022": "-", "\u2013": "-", "\u2014": "--",
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u2192": "->", "\u2190": "<-",
        "\u2713": "[OK]", "\u2714": "[OK]", "\u2715": "[X]", "\u2716": "[X]",
        "\u00b7": "-",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    # Strip emojis and other non-latin1 chars completely (not replace with ?)
    cleaned = []
    for ch in text:
        try:
            ch.encode("latin-1")
            cleaned.append(ch)
        except UnicodeEncodeError:
            pass  # drop the character
    return "".join(cleaned)


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------
class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "PRISTINI Smart Factory", align="L")
        self.cell(0, 8, datetime.now().strftime("%B %d, %Y"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 180, 216)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


# ---------------------------------------------------------------------------
# Table parsing
# ---------------------------------------------------------------------------
def _parse_table(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and not all(re.match(r'^[-:]+$', c) for c in cells):
            rows.append(cells)
    return rows


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------
def markdown_to_pdf(md_content: str) -> bytes:
    chart_blocks: list[tuple[int, dict]] = []
    clean_lines = []
    in_chart = False
    chart_json = ""

    for line in md_content.split("\n"):
        if line.strip() == "```chart":
            in_chart = True
            chart_json = ""
            continue
        if in_chart:
            if line.strip() == "```":
                in_chart = False
                try:
                    data = json.loads(chart_json)
                    clean_lines.append(f"__CHART_{len(chart_blocks)}__")
                    chart_blocks.append((len(chart_blocks), data))
                except json.JSONDecodeError:
                    pass
                continue
            chart_json += line
            continue
        clean_lines.append(line)

    md_content = _sanitize("\n".join(clean_lines))
    lines = md_content.split("\n")

    chart_images = {}
    for idx, data in chart_blocks:
        img = _generate_chart(data)
        if img:
            chart_images[idx] = img

    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    i = 0
    title_set = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            pdf.ln(3)
            i += 1
            continue

        # Chart placeholder
        chart_match = re.match(r'^__CHART_(\d+)__$', stripped)
        if chart_match:
            chart_idx = int(chart_match.group(1))
            if chart_idx in chart_images:
                pdf.ln(3)
                pdf.image(chart_images[chart_idx], x=15, w=180)
                pdf.ln(5)
            i += 1
            continue

        # Table detection
        if "|" in stripped and i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i + 1].strip()):
            table_lines = []
            while i < len(lines) and "|" in lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            rows = _parse_table(table_lines)
            if rows:
                _render_table(pdf, rows)
            continue

        # Title
        if not title_set and not stripped.startswith("#"):
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 22)
            pdf.set_text_color(0, 140, 170)
            pdf.cell(0, 14, stripped, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(0, 180, 216)
            pdf.set_line_width(0.8)
            pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
            pdf.ln(8)
            title_set = True
            i += 1
            continue

        # H1
        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = stripped[2:].strip()
            if not title_set:
                pdf.set_font("Helvetica", "B", 20)
                pdf.set_text_color(15, 15, 15)
                pdf.cell(0, 14, text, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                title_set = True
            else:
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(20, 20, 20)
                pdf.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(0, 180, 216)
                pdf.set_line_width(0.3)
                pdf.line(10, pdf.get_y(), 120, pdf.get_y())
                pdf.ln(3)
            i += 1
            continue

        # H2
        if stripped.startswith("## "):
            text = stripped[3:].strip()
            if not title_set:
                pdf.set_font("Helvetica", "B", 20)
                pdf.set_text_color(15, 15, 15)
                pdf.cell(0, 14, text, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                title_set = True
            else:
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(0, 140, 170)
                pdf.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(0, 180, 216)
                pdf.set_line_width(0.2)
                pdf.line(10, pdf.get_y() + 1, 80, pdf.get_y() + 1)
                pdf.ln(4)
            i += 1
            continue

        # H3
        if stripped.startswith("### "):
            text = stripped[4:].strip()
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, _strip_bold(text), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            i += 1
            continue

        # H4
        if stripped.startswith("#### "):
            text = stripped[5:].strip()
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 7, _strip_bold(text), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            i += 1
            continue

        # Standalone bold line (used as sub-heading, e.g. **PHASE 2: ...**)
        if stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
            text = stripped[2:-2]
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}$', stripped):
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.2)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            i += 1
            continue

        # Numbered list
        num_match = re.match(r'^(\d+)[.)]\s+(.*)$', stripped)
        if num_match:
            num = num_match.group(1)
            text = num_match.group(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(0, 140, 170)
            pdf.cell(8, 6, f"{num}.", align="R")
            pdf.set_x(pdf.get_x() + 2)
            _render_rich_text(pdf, text, x_offset=20)
            i += 1
            continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            indent = len(line) - len(line.lstrip())
            x_start = 14 + (indent * 2)
            pdf.set_x(x_start)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 140, 170)
            pdf.cell(5, 6, "-")
            _render_rich_text(pdf, text, x_offset=x_start + 6)
            i += 1
            continue

        # Regular paragraph
        _render_rich_text(pdf, stripped, x_offset=10)
        i += 1

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Rich text renderer (bold support)
# ---------------------------------------------------------------------------
def _render_rich_text(pdf: FPDF, text: str, x_offset: float = 10):
    parts = re.split(r'(\*\*.*?\*\*)', text)
    pdf.set_x(x_offset)

    if any(p.startswith("**") for p in parts):
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 30, 30)
                pdf.write(6, part[2:-2])
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.write(6, part)
        pdf.ln(7)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        effective_width = 190 - x_offset + 10
        pdf.multi_cell(effective_width, 6, text)
        pdf.ln(1)


# ---------------------------------------------------------------------------
# Table renderer
# ---------------------------------------------------------------------------
def _strip_bold(text: str) -> str:
    return text.replace("**", "")


def _render_table(pdf: FPDF, rows: list[list[str]]):
    if not rows:
        return

    pdf.ln(2)
    n_cols = max(len(r) for r in rows)

    # Auto-calculate column widths based on content
    max_chars = [0] * n_cols
    for row in rows:
        for j in range(min(len(row), n_cols)):
            max_chars[j] = max(max_chars[j], len(_strip_bold(row[j])))

    total_chars = max(sum(max_chars), 1)
    usable = 190
    col_widths = [max(usable * (mc / total_chars), 18) for mc in max_chars]
    # Normalize to fit page
    scale = usable / sum(col_widths)
    col_widths = [w * scale for w in col_widths]

    for row_idx, row in enumerate(rows):
        while len(row) < n_cols:
            row.append("")

        if row_idx == 0:
            pdf.set_fill_color(0, 150, 180)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 9)
            for j, cell in enumerate(row):
                max_len = int(col_widths[j] / 2)
                pdf.cell(col_widths[j], 8, _strip_bold(cell)[:max_len], border=1, fill=True, align="C")
            pdf.ln()
        else:
            if row_idx % 2 == 0:
                pdf.set_fill_color(240, 248, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(50, 50, 50)
            pdf.set_font("Helvetica", "", 9)
            for j, cell in enumerate(row):
                max_len = int(col_widths[j] / 2)
                pdf.cell(col_widths[j], 7, _strip_bold(cell)[:max_len], border=1, fill=True)
            pdf.ln()

    pdf.ln(3)
