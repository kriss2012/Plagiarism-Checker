"""Professional Academic PDF Report & Certificate Generator using ReportLab.
Produces the official SES's R. C. Patel IMRD Shirpur Central Library Plagiarism Clearance Certificate
complete with institutional letterhead, student credentials, UGC compliance status, signature blocks,
and detailed itemized match audit ledgers.
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
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from app.config import (
    ACADEMIC_DISCLAIMER,
    AFFILIATION_TEXT,
    BASE_DIR,
    INSTITUTION_ADDRESS,
    INSTITUTION_NAME,
    INSTITUTION_SHORT,
    ORGANIZATION,
)
from app.utils.logger import logger


class PDFReportGenerator:
    """Generates the official IMRD Central Library Plagiarism Clearance Certificate & Audit Report."""

    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """Initializes typography and color styles for IMRD Shirpur documents."""
        # Institutional Header styles
        self.trust_style = ParagraphStyle(
            "TrustHeader",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=1,  # Center
            textColor=colors.HexColor("#002461"),  # IMRD Navy
        )
        self.inst_title_style = ParagraphStyle(
            "InstTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=1,  # Center
            textColor=colors.HexColor("#002461"),
        )
        self.inst_sub_style = ParagraphStyle(
            "InstSub",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            alignment=1,  # Center
            textColor=colors.HexColor("#475569"),
        )
        self.dept_style = ParagraphStyle(
            "DeptStyle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            alignment=1,  # Center
            textColor=colors.HexColor("#005FEA"),  # Royal Blue
        )
        self.cert_title_style = ParagraphStyle(
            "CertTitle",
            parent=self.styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            alignment=1,  # Center
            textColor=colors.HexColor("#002461"),
            spaceBefore=8,
            spaceAfter=6,
        )
        self.cert_ref_style = ParagraphStyle(
            "CertRef",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#002461"),
        )
        self.date_style = ParagraphStyle(
            "CertDate",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=2,  # Right
            textColor=colors.HexColor("#0F172A"),
        )
        self.body_style = ParagraphStyle(
            "ReportBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#0F172A"),
        )
        self.bold_body_style = ParagraphStyle(
            "ReportBoldBody",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#002461"),
        )
        self.declaration_style = ParagraphStyle(
            "ReportDeclaration",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=8,
        )
        self.heading2_style = ParagraphStyle(
            "ReportH2",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#002461"),
            spaceBefore=12,
            spaceAfter=6,
        )
        self.disclaimer_style = ParagraphStyle(
            "ReportDisclaimer",
            parent=self.styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748B"),
        )

    def generate_report(
        self,
        document_data: Dict,
        score_breakdown: Dict,
        matches: List[Dict],
        citation_data: Optional[Dict] = None,
        structure_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> Path:
        """Builds and compiles the official institutional certificate and multi-page audit report."""
        logger.info(f"Generating IMRD Clearance Certificate at: {self.output_path}")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            rightMargin=0.45 * inch,
            leftMargin=0.45 * inch,
            topMargin=0.45 * inch,
            bottomMargin=0.45 * inch,
        )

        elements = []
        meta = metadata or {}
        cit_data = citation_data or {}
        struct_data = structure_data or {}

        # =========================================================================
        # PAGE 1: OFFICIAL IMRD CENTRAL LIBRARY CLEARANCE CERTIFICATE
        # =========================================================================

        # 1. College Letterhead with Logo
        logo_path = BASE_DIR / "Logo.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "resources" / "app_icon.png"

        hdr_cells = []
        if logo_path.exists():
            try:
                img = Image(str(logo_path), width=0.85 * inch, height=0.85 * inch)
                img.hAlign = "CENTER"
                hdr_cells.append(img)
            except Exception:
                hdr_cells.append(Paragraph("<b>IMRD</b>", self.trust_style))
        else:
            hdr_cells.append(Paragraph("<b>IMRD</b>", self.trust_style))

        letterhead_text = [
            Paragraph("SES's R. C. PATEL EDUCATIONAL TRUST'S", self.trust_style),
            Paragraph("INSTITUTE OF MANAGEMENT RESEARCH AND DEVELOPMENT, SHIRPUR", self.inst_title_style),
            Paragraph(AFFILIATION_TEXT, self.inst_sub_style),
            Paragraph(INSTITUTION_ADDRESS, self.inst_sub_style),
            Spacer(1, 2),
            Paragraph("CENTRAL LIBRARY • STUDENT DISSERTATION & RESEARCH PAPER VERIFICATION CELL", self.dept_style),
        ]
        hdr_table_data = [[hdr_cells[0], letterhead_text]]
        t_header = Table(hdr_table_data, colWidths=[1.0 * inch, 6.5 * inch])
        t_header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t_header)

        # Institutional Separator Bar (Navy + Gold)
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=2.5, color=colors.HexColor("#002461"), spaceAfter=1))
        elements.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor("#D97706"), spaceAfter=8))

        # Certificate Reference Number & Date
        cert_no = meta.get("certificate_no") or document_data.get("certificate_no") or f"IMRD/LIB/PLAG/{datetime.now().year}/0001"
        curr_date = datetime.now().strftime("%d-%m-%Y")
        ref_table = Table(
            [[
                Paragraph(f"<b>Ref. No.:</b> {cert_no}", self.cert_ref_style),
                Paragraph(f"<b>Date:</b> {curr_date}", self.date_style),
            ]],
            colWidths=[4.2 * inch, 3.3 * inch]
        )
        ref_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(ref_table)

        # Formal Certificate Title
        elements.append(Paragraph("<u>PLAGIARISM VERIFICATION & CLEARANCE CERTIFICATE</u>", self.cert_title_style))
        elements.append(Spacer(1, 4))

        # Preamble Statement
        student_name = meta.get("student_name") or document_data.get("student_name") or "Student Name"
        prn_no = meta.get("prn_number") or document_data.get("prn_number") or "-"
        course_name = meta.get("course_name") or document_data.get("course_name") or "MCA"
        sem_name = meta.get("semester") or document_data.get("semester") or "Semester IV"
        guide_name = meta.get("guide_name") or document_data.get("guide_name") or "Faculty Guide"
        paper_title = meta.get("paper_title") or document_data.get("paper_title") or document_data.get("filename", "Project Report")

        # 2. Student Particulars Table
        student_info = [
            [Paragraph("<b>Name of the Student:</b>", self.bold_body_style), Paragraph(f"<b>{student_name}</b>", self.body_style)],
            [Paragraph("<b>PRN / Roll Number:</b>", self.bold_body_style), Paragraph(f"<b>{prn_no}</b>", self.body_style)],
            [Paragraph("<b>Class / Program:</b>", self.bold_body_style), Paragraph(f"{course_name} ({sem_name})", self.body_style)],
            [Paragraph("<b>Academic Year:</b>", self.bold_body_style), Paragraph(meta.get("academic_year", "2025-2026"), self.body_style)],
            [Paragraph("<b>Research Guide / Supervisor:</b>", self.bold_body_style), Paragraph(f"<b>{guide_name}</b>", self.body_style)],
            [Paragraph("<b>Title of Project / Dissertation:</b>", self.bold_body_style), Paragraph(f"<b><i>\"{paper_title}\"</i></b>", self.body_style)],
        ]
        t_student = Table(student_info, colWidths=[2.3 * inch, 5.2 * inch])
        t_student.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_student)
        elements.append(Spacer(1, 8))

        # 3. Similarity Verification & UGC Compliance Metrics
        overall_sim = float(score_breakdown.get("overall_similarity", 0.0))
        word_count = int(document_data.get("word_count", 0))

        # UGC Regulation 2018 Clearance Logic:
        # Level 0 (<= 10%): Cleared / Acceptable
        # Level 1 (10% - 40%): Minor Revisions Required
        # Level 2 (40% - 60%): Major Revisions Required
        # Level 3 (> 60%): Rejected
        if overall_sim <= 10.0:
            ugc_tier = "LEVEL 0 (SIMILARITY <= 10.0%) – ACCEPTABLE"
            clearance_badge_text = "CLEARED & APPROVED"
            status_bg = colors.HexColor("#ECFDF5")
            status_border = colors.HexColor("#10B981")
            status_fg = "#047857"
            verdict_text = (
                f"The overall textual similarity index of <b>{overall_sim:.1f}%</b> is strictly within the permissible "
                "limit of 10.0% prescribed under UGC (Promotion of Academic Integrity and Prevention of Plagiarism in "
                "Higher Educational Institutions) Regulations, 2018. "
                "<b>The student is hereby GRANTED PLAGIARISM CLEARANCE for final submission and evaluation.</b>"
            )
        elif overall_sim <= 40.0:
            ugc_tier = "LEVEL 1 (SIMILARITY 10.1% – 40.0%) – MINOR REVISIONS"
            clearance_badge_text = "REVISIONS REQUIRED"
            status_bg = colors.HexColor("#FFFBEB")
            status_border = colors.HexColor("#F59E0B")
            status_fg = "#B45309"
            verdict_text = (
                f"The overall textual similarity index of <b>{overall_sim:.1f}%</b> falls under UGC Level 1. "
                "The student must revise the uncredited passages under the supervisor's guidance and submit for re-verification."
            )
        elif overall_sim <= 60.0:
            ugc_tier = "LEVEL 2 (SIMILARITY 40.1% – 60.0%) – MAJOR REVISIONS"
            clearance_badge_text = "MAJOR REVISIONS"
            status_bg = colors.HexColor("#FEF2F2")
            status_border = colors.HexColor("#EF4444")
            status_fg = "#B91C1C"
            verdict_text = (
                f"The overall textual similarity index of <b>{overall_sim:.1f}%</b> exceeds acceptable limits (Level 2). "
                "Significant revision is mandatory as per University guidelines."
            )
        else:
            ugc_tier = "LEVEL 3 (SIMILARITY > 60.0%) – REJECTED"
            clearance_badge_text = "REJECTED / UNACCEPTABLE"
            status_bg = colors.HexColor("#450A0A")
            status_border = colors.HexColor("#991B1B")
            status_fg = "#FFFFFF"
            verdict_text = (
                f"The overall textual similarity index of <b>{overall_sim:.1f}%</b> represents severe textual duplication (Level 3). "
                "Paper rejected in accordance with institutional academic integrity policies."
            )

        sim_metrics_data = [
            [
                Paragraph("<b>Total Words Analyzed:</b>", self.bold_body_style),
                Paragraph(f"{word_count:,}", self.body_style),
                Paragraph("<b>Overall Similarity Index:</b>", self.bold_body_style),
                Paragraph(f"<font size=12 color='{status_fg}'><b>{overall_sim:.1f}%</b></font>", self.body_style),
            ],
            [
                Paragraph("<b>Bibliography Excluded:</b>", self.bold_body_style),
                Paragraph("YES (As per UGC Sec 6.1)", self.body_style),
                Paragraph("<b>Quotes & Citations Excluded:</b>", self.bold_body_style),
                Paragraph("YES (As per UGC Sec 6.1)", self.body_style),
            ],
            [
                Paragraph("<b>UGC 2018 Regulation Tier:</b>", self.bold_body_style),
                Paragraph(f"<b>{ugc_tier}</b>", self.body_style),
                Paragraph("<b>Clearance Status:</b>", self.bold_body_style),
                Paragraph(f"<font size=10 color='{status_fg}'><b>{clearance_badge_text}</b></font>", self.body_style),
            ],
        ]
        t_metrics = Table(sim_metrics_data, colWidths=[2.1 * inch, 1.65 * inch, 2.1 * inch, 1.65 * inch])
        t_metrics.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), status_bg),
            ("BOX", (0, 0), (-1, -1), 1.2, status_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(t_metrics)
        elements.append(Spacer(1, 8))

        # 4. Formal Certification Declaration
        declaration_para = Paragraph(
            f"<b>CERTIFICATION STATEMENT:</b><br/>"
            f"This is to certify that the project report / dissertation titled <i>\"{paper_title}\"</i> submitted by "
            f"<b>{student_name}</b> (PRN: {prn_no}) of <b>{course_name} ({sem_name})</b> has been examined for textual similarity and plagiarism "
            f"at the Central Library, SES's R. C. Patel IMRD, Shirpur using the ResearchGuard Plagiarism Verification System. "
            f"{verdict_text}",
            self.declaration_style
        )
        elements.append(declaration_para)
        elements.append(Spacer(1, 24))

        # 5. Formal Three-Column Signatures
        sig_data = [
            [
                Paragraph("<b>________________________</b><br/><b>Signature of Student</b><br/>Name: " + student_name + "<br/>Date: " + curr_date, self.body_style),
                Paragraph("<b>________________________</b><br/><b>Signature of Guide / Supervisor</b><br/>Name: " + guide_name + "<br/>Department of " + course_name, self.body_style),
                Paragraph("<b>________________________</b><br/><b>Librarian / Verification Officer</b><br/>Central Library & Research Cell<br/>SES's R. C. Patel IMRD, Shirpur", self.body_style),
            ]
        ]
        t_sig = Table(sig_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
        t_sig.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_sig)

        # Institutional Footer Seal Note
        elements.append(Spacer(1, 14))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=4))
        elements.append(Paragraph(
            f"<b>Official Verification Notice:</b> {ACADEMIC_DISCLAIMER} Certificate verified and archived in Central Library repository.",
            self.disclaimer_style
        ))

        # =========================================================================
        # PAGE 2+: DETAILED SIMILARITY BREAKDOWN & ITEMISED MATCH AUDIT
        # =========================================================================
        elements.append(PageBreak())

        elements.append(Paragraph("SES's R. C. Patel IMRD Shirpur • Central Library", self.dept_style))
        elements.append(Paragraph("Plagiarism & Textual Similarity Audit Breakdown", self.heading2_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#002461"), spaceAfter=10))

        # Algorithm breakdown table
        breakdown_table = [
            ["Analysis Metric", "Percentage", "Count", "Institutional Scoring Treatment"],
            ["Exact Verbatim Matches", f"{score_breakdown.get('exact_percentage', 0.0):.1f}%", str(score_breakdown.get('exact_count', 0)), "Included in similarity score (Weight 0.45)"],
            ["Fuzzy Modifications / Paraphrases", f"{score_breakdown.get('fuzzy_percentage', 0.0):.1f}%", str(score_breakdown.get('fuzzy_count', 0)), "Included in similarity score (Weight 0.30)"],
            ["Semantic Paraphrase Indicators", f"{score_breakdown.get('semantic_percentage', 0.0):.1f}%", str(score_breakdown.get('semantic_count', 0)), "Included in similarity score (Weight 0.25)"],
            ["Quoted & Cited Text Segments", f"{score_breakdown.get('quoted_percentage', 0.0):.1f}%", str(score_breakdown.get('quoted_count', 0)), "Excluded from uncredited similarity (UGC Sec 6.1)"],
            ["Ignored Matches", "-", str(score_breakdown.get('ignored_count', 0)), "Excluded upon faculty review"],
        ]
        t_breakdown = Table(breakdown_table, colWidths=[2.3 * inch, 1.1 * inch, 0.9 * inch, 3.2 * inch])
        t_breakdown.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#002461")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(t_breakdown)
        elements.append(Spacer(1, 14))

        # Citations & Academic Structure Table
        elements.append(Paragraph("Academic Paper Structure & In-Text Citations", self.heading2_style))
        cit_rows = [
            ["Integrity Parameter", "Status / Count", "Academic Notes"],
            ["In-Text Academic Citations", str(cit_data.get("citation_count", 0)), "Parsed IEEE [1], APA/Harvard (Author, Year), and DOI citations"],
            ["Bibliography Reference Entries", str(cit_data.get("reference_count", 0)), "Parsed entries in References / Bibliography section"],
            ["Quoted Text Passages", str(len(cit_data.get("quotes", []))), "Isolated quotation marks credited to external authors"],
            ["AI-Assisted Writing Indicator", meta.get("ai_likelihood", "Low"), "Stylometric sentence-length variance and burstiness evaluation"],
        ]
        t_cit = Table(cit_rows, colWidths=[2.4 * inch, 1.4 * inch, 3.7 * inch])
        t_cit.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#005FEA")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
        ]))
        elements.append(t_cit)
        elements.append(Spacer(1, 14))

        # Detailed Itemized Matches
        elements.append(Paragraph("Itemized Textual Match Details", self.heading2_style))
        elements.append(Paragraph("Detailed itemization of the most significant matching text passages identified across available comparison corpora:", self.body_style))
        elements.append(Spacer(1, 6))

        match_headers = [["#", "Sim%", "Algorithm", "Pg", "Matched Student Document Excerpt", "Matched Source Reference"]]
        match_rows = []
        for idx, m in enumerate(matches[:50]):  # Cap at top 50 matches
            snippet = m.get("sentence", "")
            if len(snippet) > 130:
                snippet = snippet[:127] + "..."

            src_snippet = m.get("source_name", "Comparison Source")
            if len(src_snippet) > 65:
                src_snippet = src_snippet[:62] + "..."

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

        t_matches = Table(match_headers + match_rows, colWidths=[0.35 * inch, 0.55 * inch, 0.85 * inch, 0.4 * inch, 3.25 * inch, 2.1 * inch])
        t_matches.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#002461")),
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
        logger.info(f"ReportLab successfully built IMRD Certificate: {self.output_path}")
        return self.output_path
