"""Tests for scoring engine calculations, risk tiers, and exclusions."""

from app.core.scoring import ScoringEngine


def test_scoring_with_exclusions():
    engine = ScoringEngine()

    # 100-word document with matches
    matches = [
        {"sentence": "Exact copied sentence one with seven words.", "algorithm": "Exact Match", "is_quoted": False, "is_ignored": False},
        {"sentence": "Fuzzy modified sentence with seven words here.", "algorithm": "Fuzzy Match", "is_quoted": False, "is_ignored": False},
        {"sentence": "Quoted sentence inside quotations with seven words.", "algorithm": "Exact Match", "is_quoted": True, "is_ignored": False},
    ]

    # Calculate with quote exclusion
    res_ex = engine.calculate_score(total_document_words=100, matches=matches, exclude_quotes=True)
    assert res_ex.quoted_count == 1
    assert res_ex.exact_count == 1
    assert res_ex.fuzzy_count == 1
    # Quoted text should be excluded from similarity
    assert res_ex.overall_similarity < 20.0
    assert res_ex.risk_level in ["Very Low", "Low"]

    # Calculate including quotes
    res_in = engine.calculate_score(total_document_words=100, matches=matches, exclude_quotes=False)
    assert res_in.overall_similarity > res_ex.overall_similarity


def test_risk_levels():
    engine = ScoringEngine()
    assert engine.determine_risk_level(5.0) == "Very Low"
    assert engine.determine_risk_level(18.0) == "Low"
    assert engine.determine_risk_level(32.0) == "Moderate"
    assert engine.determine_risk_level(50.0) == "High"
    assert engine.determine_risk_level(75.0) == "Very High"
