"""Multilingual detection and Devanagari punctuation tests."""

from pathlib import Path
from app.core.extractor import DocumentExtractor
from app.core.language import detect_language
from app.core.preprocessor import TextPreprocessor


def test_language_detection_hindi():
    hindi_path = Path("resources/sample_papers/hindi_paper.txt")
    text = hindi_path.read_text(encoding="utf-8")
    lang, conf = detect_language(text)
    assert lang == "Hindi"
    assert conf > 0.6


def test_language_detection_marathi():
    marathi_path = Path("resources/sample_papers/marathi_paper.txt")
    text = marathi_path.read_text(encoding="utf-8")
    lang, conf = detect_language(text)
    assert lang == "Marathi"
    assert conf > 0.6


def test_devanagari_sentence_splitting():
    text = "कृत्रिम बुद्धिमत्ता आधुनिक जगात वेगाने विकसित होत आहे। या तंत्रज्ञानाचा वापर सर्वत्र केला जात आहे॥"
    preprocessor = TextPreprocessor()
    sentences = preprocessor.split_sentences(text)
    assert len(sentences) >= 2
    assert "कृत्रिम बुद्धिमत्ता" in sentences[0].original_text
