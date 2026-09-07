"""CSV and JSON data export utilities for plagiarism analysis results."""

import csv
import json
from pathlib import Path
from typing import Dict, List


def export_matches_to_csv(matches: List[Dict], output_path: str | Path) -> Path:
    """Exports detected matches to a standard CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "match_id",
        "similarity_score",
        "algorithm",
        "page_number",
        "is_quoted",
        "is_cited",
        "is_ignored",
        "source_name",
        "sentence",
        "matched_text",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, m in enumerate(matches):
            writer.writerow({
                "match_id": idx + 1,
                "similarity_score": m.get("similarity_score", 0.0),
                "algorithm": m.get("algorithm", "Fuzzy"),
                "page_number": m.get("page_number", 1),
                "is_quoted": m.get("is_quoted", False),
                "is_cited": m.get("is_cited", False),
                "is_ignored": m.get("is_ignored", False),
                "source_name": m.get("source_name", "Unknown Source"),
                "sentence": m.get("sentence", ""),
                "matched_text": m.get("matched_text", ""),
            })

    return path


def export_analysis_to_json(data: Dict, output_path: str | Path) -> Path:
    """Exports complete analysis hierarchy to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path
