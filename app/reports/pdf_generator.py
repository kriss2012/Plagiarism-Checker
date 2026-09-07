"""Professional Academic PDF Report Generator using ReportLab.
Produces comprehensive academic analysis reports complete with formal cover sheet,
executive summaries, score breakdowns, match details, citation analyses, and disclaimers.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from app.config import ACADEMIC_DISCLAIMER
from app.utils.logger import logger


class PDFReportGenerator:
    """Generates formal academic plagiarism and similarity audit reports."""

    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """Initializes typography and color styles for academic documents."""
        self.title_style = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1E1B4B"),  # Deep indigo
            spaceAfter=10,
        )
        self.subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#475569"),
            spaceAfter=20,
        )
        self.heading2_style = ParagraphStyle(
            "ReportH2",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#312E81"),
            spaceBefore=14,
            spaceAfter=8,
        )
        self.body_style = ParagraphStyle(
            "ReportBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B"),
        )
        self.code_style = ParagraphStyle(
            "ReportCode",
            parent=self.styles["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0F172A"),
        )
        self.disclaimer_style = ParagraphStyle(
            "ReportDisclaimer",
            parent=self.styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
        )

    def generate_report(
        self,
        document_data: Dict,
        score_breakdown: Dict,
        matches: List[Dict],
        citation_data: Dict,
        structure_data: Dict,
        metadata: Optional[Dict] = None,
    ) -> Path:
        """Builds and compiles the full multi-page PDF document."""
        logger.info(f"Generating PDF report at: {self.output_path}")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        elements = []
        meta = metadata or {}

        # ==================== PAGE 1: COVER SHEET ====================
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph("ResearchGuard Academic Systems", self.subtitle_style))
        elements.append(Paragraph("Plagiarism & Textual Similarity Audit Report", self.title_style))
        elements.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor("#4F46E5"), spaceAfter=20))

        # Institutional Metadata Table
        inst_info = [
            [Paragraph("<b>Institution:</b>", self.body_style), Paragraph(meta.get("institution", "Academic Department"), self.body_style)],
            [Paragraph("<b>Department:</b>", self.body_style), Paragraph(meta.get("department", "Computer Science & Engineering"), self.body_style)],
            [Paragraph("<b>Researcher / Student:</b>", self.body_style), Paragraph(meta.get("researcher", "Student Name"), self.body_style)],
            [Paragraph("<b>Supervisor / Guide:</b>", self.body_style), Paragraph(meta.get("supervisor", "Faculty Advisor"), self.body_style)],
            [Paragraph("<b>Paper Title:</b>", self.body_style), Paragraph(meta.get("title", document_data.get("filename", "Research Paper")), self.body_style)],
            [Paragraph("<b>Filename:</b>", self.body_style), Paragraph(document_data.get("filename", "document.pdf"), self.body_style)],
            [Paragraph("<b>Analysis Date:</b>", self.body_style), Paragraph(datetime.now().strftime("%B %d, %Y - %H:%M:%S"), self.body_style)],
            [Paragraph("<b>File Hash (SHA-256):</b>", self.body_style), Paragraph(document_data.get("hash", "N/A")[:32] + "...", self.code_style)],
        ]
        t_meta = Table(inst_info, colWidths=[1.8 * inch, 5.2 * inch])
        t_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 20))

        # Overall Score & Risk Highlight Box
        overall_sim = score_breakdown.get("overall_similarity", 0.0)
        risk_lvl = score_breakdown.get("risk_level", "Very Low")
        
        # Color coding for risk badge
        risk_colors = {
            "Very Low": colors.HexColor("#10B981"),
            "Low": colors.HexColor("#3B82F6"),
            "Moderate": colors.HexColor("#F59E0B"),
            "High": colors.HexColor("#EF4444"),
            "Very High": colors.HexColor("#991B1B"),
        }
        badge_color = risk_colors.get(risk_lvl, colors.HexColor("#3B82F6"))

        summary_card = [
            [
                Paragraph(f"<font size=32><b>{overall_sim:.1f}%</b></font><br/><font size=10 color='#64748B'>OVERALL SIMILARITY</font>", self.body_style),
                Paragraph(f"<font size=20 color='{badge_color.hexval()}'><b>{risk_lvl.upper()} RISK</b></font><br/><font size=9 color='#64748B'>Calculated Academic Risk Heuristic</font>", self.body_style),
                Paragraph(
                    f"<b>Words Analyzed:</b> {document_data.get('word_count', 0):,}<br/>"
                    f"<b>Pages:</b> {document_data.get('page_count', 1)}<br/>"
                    f"<b>Matched Sources:</b> {len(set(m.get('source_name', 'Unknown') for m in matches))}",
                    self.body_style
                )
            ]
        ]
        t_sum = Table(summary_card, colWidths=[2.2 * inch, 2.4 * inch, 2.4 * inch])
        t_sum.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#C7D2FE")),
            ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(t_sum)
        elements.append(Spacer(1, 20))

        # Academic Disclaimer Banner on Cover
        disclaimer_box = [
            [Paragraph(f"<b>ACADEMIC REVIEW NOTICE:</b> {ACADEMIC_DISCLAIMER}", self.disclaimer_style)]
        ]
        t_disc = Table(disclaimer_box, colWidths=[7.0 * inch])
        t_disc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FDE68A")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(t_disc)

        # ==================== PAGE 2: EXECUTIVE SUMMARY & METRICS ====================
        elements.append(PageBreak())
        elements.append(Paragraph("1. Executive Summary & Algorithm Breakdown", self.heading2_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=10))

        breakdown_table = [
            ["Analysis Metric", "Percentage", "Count", "Scoring Treatment"],
            ["Exact Text Matches", f"{score_breakdown.get('exact_percentage', 0.0):.1f}%", str(score_breakdown.get('exact_count', 0)), "Included (Primary Weight 0.45)"],
            ["Fuzzy Modifications", f"{score_breakdown.get('fuzzy_percentage', 0.0):.1f}%", str(score_breakdown.get('fuzzy_count', 0)), "Included (Secondary Weight 0.30)"],
            ["Semantic Paraphrase Indicators", f"{score_breakdown.get('semantic_percentage', 0.0):.1f}%", str(score_breakdown.get('semantic_count', 0)), "Included (Context Weight 0.25)"],
            ["Quoted & Cited Content", f"{score_breakdown.get('quoted_percentage', 0.0):.1f}%", str(score_breakdown.get('quoted_count', 0)), "Excluded from uncredited similarity"],
            ["Ignored Matches", "-", str(score_breakdown.get('ignored_count', 0)), "Excluded by user"],
        ]
        t_breakdown = Table(breakdown_table, colWidths=[2.2 * inch, 1.2 * inch, 1.0 * inch, 2.6 * inch])
        t_breakdown.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#312E81")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(t_breakdown)
        elements.append(Spacer(1, 15))

        # Academic Paper Structure Table
        elements.append(Paragraph("2. Paper Structure & Section Analysis", self.heading2_style))
        structure_rows = [["Section", "Detection Status", "Notes"]]
        for sec_name, sec_obj in structure_data.items():
            det = sec_obj.get("detected", False) if isinstance(sec_obj, dict) else getattr(sec_obj, "detected", False)
            status_str = "Detected ✓" if det else "Not Detected ⚠"
            notes = "Standard section parsed" if det else "Section heading not identified"
            structure_rows.append([sec_name, status_str, notes])

        t_struct = Table(structure_rows, colWidths=[2.2 * inch, 1.8 * inch, 3.0 * inch])
        t_struct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(t_struct)
        elements.append(Spacer(1, 15))

        # Citation & Quotation Overview
        elements.append(Paragraph("3. Citation & Quotation Overview", self.heading2_style))
        cit_rows = [
            ["Metric", "Count", "Academic Context"],
            ["Total In-Text Citations", str(citation_data.get("citation_count", 0)), "Recognized IEEE, APA, Harvard, and DOI entries"],
            ["Estimated Bibliography References", str(citation_data.get("reference_count", 0)), "Entries parsed in References section"],
            ["Quoted Passages", str(len(citation_data.get("quotes", []))), "Double/single quotes with quotation mark isolation"],
            ["Potentially Uncited Paragraphs", str(citation_data.get("uncited_claims", 0)), "Substantial narrative paragraphs without detected citations"],
        ]
        t_cit = Table(cit_rows, colWidths=[2.4 * inch, 1.2 * inch, 3.4 * inch])
        t_cit.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284C7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BAE6FD")),
        ]))
        elements.append(t_cit)

        # ==================== PAGE 3+: DETAILED MATCHES TABLE ====================
        elements.append(PageBreak())
        elements.append(Paragraph("4. Detected Match Details", self.heading2_style))
        elements.append(Paragraph("The following table details individual text segments exhibiting significant similarity to comparison sources.", self.body_style))
        elements.append(Spacer(1, 8))

        match_headers = [["ID", "Sim%", "Algorithm", "Pg", "Matched Document Excerpt", "Source Information"]]
        match_rows = []
        for idx, m in enumerate(matches[:40]):  # Cap at top 40 for report size
            snippet = m.get("sentence", "")
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            
            src_snippet = m.get("source_name", "Unknown Source")
            if len(src_snippet) > 60:
                src_snippet = src_snippet[:57] + "..."

            match_rows.append([
                str(idx + 1),
                f"{m.get('similarity_score', 0):.0f}%",
                m.get("algorithm", "Fuzzy")[:10],
                str(m.get("page_number", 1)),
                Paragraph(snippet, self.body_style),
                Paragraph(f"<b>{src_snippet}</b>", self.body_style),
            ])

        if not match_rows:
            match_rows.append(["-", "0%", "None", "-", "No significant similarity matches found.", "N/A"])

        t_matches = Table(match_headers + match_rows, colWidths=[0.35 * inch, 0.55 * inch, 0.9 * inch, 0.4 * inch, 2.8 * inch, 2.0 * inch])
        t_matches.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t_matches)

        # Build PDF document
        doc.build(elements)
        logger.info(f"ReportLab successfully generated PDF report: {self.output_path}")
        return self.output_path
