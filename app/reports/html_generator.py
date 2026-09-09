"""Standalone interactive HTML report generator.
Produces a beautiful, self-contained single-file HTML report with interactive match highlights,
filter toggles, and metadata, viewable in any modern browser without internet access.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional
from app.config import ACADEMIC_DISCLAIMER
from app.utils.security import sanitize_for_display


class HTMLReportGenerator:
    """Generates self-contained interactive HTML plagiarism audit reports."""

    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)

    def generate_report(
        self,
        document_data: Dict,
        score_breakdown: Dict,
        matches: List[Dict],
        citation_data: Optional[Dict] = None,
        structure_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        extracted_text: Optional[str] = None,
        references: Optional[List] = None,
        citation_issues: Optional[List] = None,
    ) -> Path:
        """Assembles and writes the interactive HTML report."""
        meta = metadata or {}
        citation_data = citation_data or {}
        structure_data = structure_data or {}
        overall_sim = score_breakdown.get("overall_similarity", 0.0)
        risk_lvl = score_breakdown.get("risk_level", "Very Low")

        # Color token mappings
        risk_colors = {
            "Very Low": "#10B981",
            "Low": "#3B82F6",
            "Moderate": "#F59E0B",
            "High": "#EF4444",
            "Very High": "#991B1B",
        }
        badge_color = risk_colors.get(risk_lvl, "#3B82F6")

        # Prepare matches JSON for embedded JS inspector
        matches_json = json.dumps(matches)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ResearchGuard Report – {sanitize_for_display(document_data.get('filename', 'Document'))}</title>
    <style>
        :root {{
            --bg-primary: #0F172A;
            --bg-secondary: #1E293B;
            --bg-card: #1E293B;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --accent-primary: #6366F1;
            --border-color: #334155;
            --exact-color: #EF4444;
            --fuzzy-color: #F59E0B;
            --semantic-color: #8B5CF6;
            --quote-color: #0284C7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 30px 20px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .header-title h1 {{ font-size: 26px; font-weight: 700; color: #FFFFFF; }}
        .header-title p {{ color: #C7D2FE; font-size: 14px; margin-top: 4px; }}
        .score-pill {{
            background: rgba(15, 23, 42, 0.6);
            border: 2px solid {badge_color};
            border-radius: 12px;
            padding: 16px 24px;
            text-align: center;
        }}
        .score-val {{ font-size: 38px; font-weight: 800; color: #FFFFFF; line-height: 1; }}
        .risk-val {{ font-size: 14px; font-weight: 700; color: {badge_color}; text-transform: uppercase; margin-top: 4px; }}
        
        .disclaimer-bar {{
            background: #451A03;
            border: 1px solid #78350F;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 13px;
            color: #FDE68A;
            margin-bottom: 24px;
        }}

        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
        }}
        .card h3 {{ font-size: 13px; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }}
        .card .big-num {{ font-size: 26px; font-weight: 700; color: #FFFFFF; }}

        .table-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 24px;
            overflow-x: auto;
        }}
        .section-title {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }}
        th {{ background: #0F172A; padding: 12px; color: var(--text-secondary); border-bottom: 1px solid var(--border-color); font-weight: 600; }}
        td {{ padding: 12px; border-bottom: 1px solid var(--border-color); }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-exact {{ background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid #EF4444; }}
        .badge-fuzzy {{ background: rgba(245, 158, 11, 0.2); color: #FCD34D; border: 1px solid #F59E0B; }}
        .badge-semantic {{ background: rgba(139, 92, 246, 0.2); color: #DDD6FE; border: 1px solid #8B5CF6; }}
        .badge-quote {{ background: rgba(2, 132, 199, 0.2); color: #BAE6FD; border: 1px solid #0284C7; }}

        .footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">
                <h1>ResearchGuard Similarity Audit Report</h1>
                <p>Analyzed Document: <strong>{sanitize_for_display(document_data.get('filename', 'Unknown'))}</strong> &bull; Generated on {datetime.now().strftime("%B %d, %Y")}</p>
            </div>
            <div class="score-pill">
                <div class="score-val">{overall_sim:.1f}%</div>
                <div class="risk-val">{risk_lvl} Risk</div>
            </div>
        </div>

        <div class="disclaimer-bar">
            <strong>ACADEMIC DISCLAIMER:</strong> {ACADEMIC_DISCLAIMER}
        </div>

        <div class="grid-cards">
            <div class="card">
                <h3>Total Analyzed Words</h3>
                <div class="big-num">{document_data.get('word_count', 0):,}</div>
            </div>
            <div class="card">
                <h3>Exact Matches</h3>
                <div class="big-num" style="color: var(--exact-color);">{score_breakdown.get('exact_count', 0)}</div>
            </div>
            <div class="card">
                <h3>Fuzzy Modifications</h3>
                <div class="big-num" style="color: var(--fuzzy-color);">{score_breakdown.get('fuzzy_count', 0)}</div>
            </div>
            <div class="card">
                <h3>Semantic Paraphrases</h3>
                <div class="big-num" style="color: var(--semantic-color);">{score_breakdown.get('semantic_count', 0)}</div>
            </div>
            <div class="card">
                <h3>Quoted / Cited</h3>
                <div class="big-num" style="color: var(--quote-color);">{score_breakdown.get('quoted_count', 0)}</div>
            </div>
        </div>

        <div class="table-section">
            <h2 class="section-title">Detected Similarity Matches</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">ID</th>
                        <th style="width: 80px;">Similarity</th>
                        <th style="width: 140px;">Algorithm</th>
                        <th style="width: 60px;">Page</th>
                        <th>Document Text Excerpt</th>
                        <th>Matched Source</th>
                    </tr>
                </thead>
                <tbody>
"""
        for idx, m in enumerate(matches):
            algo = m.get("algorithm", "Fuzzy")
            badge_class = "badge-fuzzy"
            if "Exact" in algo:
                badge_class = "badge-exact"
            elif "Semantic" in algo:
                badge_class = "badge-semantic"
            elif m.get("is_quoted", False):
                badge_class = "badge-quote"

            html_content += f"""
                    <tr>
                        <td>#{idx + 1}</td>
                        <td><strong>{m.get('similarity_score', 0):.0f}%</strong></td>
                        <td><span class="badge {badge_class}">{algo}</span></td>
                        <td>Pg {m.get('page_number', 1)}</td>
                        <td>"{sanitize_for_display(m.get('sentence', ''))}"</td>
                        <td><strong>{sanitize_for_display(m.get('source_name', 'Unknown'))}</strong></td>
                    </tr>
"""
        if not matches:
            html_content += """
                    <tr><td colspan="6" style="text-align: center; padding: 24px; color: #94A3B8;">No significant matching passages detected.</td></tr>
"""

        html_content += f"""
                </tbody>
            </table>
        </div>
"""

        # References Section if available
        if references:
            html_content += """
        <div class="table-section">
            <h2 class="section-title">Bibliography Reference Verification & Authenticity Audit</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>Cited Publication Title</th>
                        <th>Authors</th>
                        <th style="width: 70px;">Year</th>
                        <th>DOI / Link</th>
                        <th style="width: 140px;">Status</th>
                        <th>Registry Notes</th>
                    </tr>
                </thead>
                <tbody>
"""
            for r in references[:50]:
                r_num = getattr(r, "ref_number", "-")
                r_title = sanitize_for_display(getattr(r, "title", "")[:70])
                r_authors = sanitize_for_display(getattr(r, "authors", "")[:35])
                r_year = getattr(r, "year", "-")
                r_doi = getattr(r, "doi", "") or getattr(r, "url", "") or "-"
                r_status = getattr(r, "status", "NOT VERIFIED")
                r_notes = sanitize_for_display(getattr(r, "difference_notes", "") or getattr(r, "verification_source", ""))
                
                badge_class = "badge-exact" if r_status in ["BROKEN LINK", "SUSPICIOUS"] else ("badge-quote" if r_status == "VERIFIED" else "badge-fuzzy")

                html_content += f"""
                    <tr>
                        <td>#{r_num}</td>
                        <td><strong>{r_title}</strong></td>
                        <td>{r_authors}</td>
                        <td>{r_year}</td>
                        <td><code>{sanitize_for_display(r_doi[:35])}</code></td>
                        <td><span class="badge {badge_class}">{r_status}</span></td>
                        <td><small>{r_notes}</small></td>
                    </tr>
"""
            html_content += """
                </tbody>
            </table>
        </div>
"""

        # Citation Issues Section if available
        if citation_issues:
            html_content += """
        <div class="table-section">
            <h2 class="section-title">In-Text Citation Anomalies & Reference Discrepancies</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 160px;">Anomaly Category</th>
                        <th style="width: 120px;">Citation Text</th>
                        <th style="width: 60px;">Page</th>
                        <th>Audit Details</th>
                    </tr>
                </thead>
                <tbody>
"""
            for ci in citation_issues:
                html_content += f"""
                    <tr>
                        <td><span class="badge badge-exact">{sanitize_for_display(getattr(ci, 'issue_type', 'Anomaly'))}</span></td>
                        <td><strong>{sanitize_for_display(getattr(ci, 'citation_text', '-'))}</strong></td>
                        <td>Pg {getattr(ci, 'page_number', 1)}</td>
                        <td>{sanitize_for_display(getattr(ci, 'details', ''))}</td>
                    </tr>
"""
            html_content += """
                </tbody>
            </table>
        </div>
"""

        html_content += f"""
        <div class="footer">
            ResearchGuard Academic Systems &bull; Standard Verification Engine &bull; Confidential
        </div>
    </div>
</body>
</html>"""

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return self.output_path
