import os
import io
from docx import Document as DocxDocument
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def _register_pdf_fonts():
    """
    Helvetica has no Bengali glyphs, so Bangla text rendered as blank boxes.
    Register a Unicode font covering Latin + Bengali (Nirmala UI on Windows, or PDF_FONT_PATH),
    and enable HarfBuzz shaping when uharfbuzz is installed so conjuncts and vowel signs join correctly.
    Returns (regular_name, bold_name, shaping_flag).
    """
    regular_path = os.getenv("PDF_FONT_PATH", "C:/Windows/Fonts/Nirmala.ttc")
    bold_path = os.getenv("PDF_FONT_BOLD_PATH", regular_path)
    try:
        is_ttc = regular_path.lower().endswith(".ttc")
        pdfmetrics.registerFont(TTFont("LegalUnicode", regular_path, subfontIndex=0))
        pdfmetrics.registerFont(TTFont("LegalUnicode-Bold", bold_path, subfontIndex=1 if is_ttc and bold_path == regular_path else 0))
    except Exception:
        return "Helvetica", "Helvetica-Bold", 0
    try:
        import uharfbuzz  # noqa: F401
        shaping = 1
    except ImportError:
        shaping = 0
    return "LegalUnicode", "LegalUnicode-Bold", shaping

PDF_FONT, PDF_FONT_BOLD, PDF_SHAPING = _register_pdf_fonts()

class ExportService:
    @staticmethod
    def generate_docx(document_title: str, full_text: str, output_path: str) -> str:
        """
        Generates a professionally styled Microsoft Word (.docx) legal document.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = DocxDocument()

        # Set 1-inch margins
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        lines = full_text.split('\n')
        is_title = True

        for line in lines:
            line_str = line.strip()
            if not line_str:
                doc.add_paragraph()
                continue

            if is_title and ("COMMERCIAL LEASE" in line_str.upper() or "AGREEMENT" in line_str.upper()):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(line_str)
                run.bold = True
                run.font.size = Pt(16)
                run.font.name = "Times New Roman"
                is_title = False
            elif line_str.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "SCHEDULE", "BETWEEN", "WHEREAS", "NOW THIS")):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(line_str)
                run.bold = True
                run.font.size = Pt(12)
                run.font.name = "Times New Roman"
            else:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                run = p.add_run(line_str)
                run.font.size = Pt(11)
                run.font.name = "Times New Roman"

        doc.save(output_path)
        return output_path

    @staticmethod
    def generate_pdf(document_title: str, full_text: str, output_path: str) -> str:
        """
        Generates a clean, print-ready PDF legal document.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name="LegalTitle",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            fontSize=15,
            leading=18,
            fontName=PDF_FONT_BOLD,
            shaping=PDF_SHAPING,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            name="LegalHeading",
            parent=styles["Heading2"],
            alignment=TA_LEFT,
            fontSize=11,
            leading=14,
            fontName=PDF_FONT_BOLD,
            shaping=PDF_SHAPING,
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            name="LegalBody",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
            fontSize=9.5,
            leading=13,
            fontName=PDF_FONT,
            shaping=PDF_SHAPING,
            spaceAfter=6
        )

        story = []
        lines = full_text.split('\n')
        is_first = True

        for line in lines:
            line_str = line.strip()
            if not line_str:
                story.append(Spacer(1, 6))
                continue

            # Escape basic XML entities for ReportLab
            clean_str = line_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if is_first and ("COMMERCIAL LEASE" in line_str.upper() or "AGREEMENT" in line_str.upper()):
                story.append(Paragraph(clean_str, title_style))
                is_first = False
            elif line_str.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "SCHEDULE", "BETWEEN", "WHEREAS", "NOW THIS")):
                story.append(Paragraph(clean_str, heading_style))
            else:
                story.append(Paragraph(clean_str, body_style))

        doc.build(story)
        return output_path

export_service = ExportService()
