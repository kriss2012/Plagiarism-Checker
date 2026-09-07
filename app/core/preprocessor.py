"""Text preprocessing and segmentation engine.
Normalizes Unicode, standardizes punctuation/quotes, performs multilingual sentence tokenization,
and maintains dual representation (original text vs normalized analysis text).
"""

from dataclasses import dataclass, field
import hashlib
import re
import unicodedata
from typing import List, Tuple
from app.core.extractor import PageData


@dataclass
class SentenceUnit:
    index: int
    page_number: int
    original_text: str
    normalized_text: str
    start_char: int
    end_char: int
    tokens: List[str] = field(default_factory=list)
    hash: str = ""
    is_quoted: bool = False
    is_cited: bool = False
    is_reference_section: bool = False


@dataclass
class PreprocessedDocument:
    original_full_text: str
    normalized_full_text: str
    sentences: List[SentenceUnit] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    language: str = "English"
    word_count: int = 0


# Common academic abbreviations that should not trigger sentence splits
COMMON_ABBREVIATIONS = {
    "al.", "e.g.", "i.e.", "dr.", "prof.", "fig.", "figs.", "eq.", "eqs.",
    "vol.", "no.", "pp.", "p.", "vs.", "ca.", "etc.", "cf.", "ref.", "refs."
}


class TextPreprocessor:
    """Preprocesses raw extracted text and splits into analytical units."""

    def __init__(self, min_word_count_to_flag: int = 4):
        self.min_words = min_word_count_to_flag

    def normalize_text(self, text: str) -> str:
        """Normalizes Unicode, whitespace, and uniform punctuation."""
        if not text:
            return ""

        # Normalize unicode to NFKC
        text = unicodedata.normalize("NFKC", text)

        # Standardize quotation marks
        text = re.sub(r'[“”„«»‟]', '"', text)
        text = re.sub(r'[‘’‚‛‹›′`]', "'", text)

        # Standardize dashes and hyphens
        text = re.sub(r'[—–−―]', '-', text)

        # Remove control characters (except standard newlines and tabs)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # Normalize spaces
        text = re.sub(r'[ \t\r\f\v]+', ' ', text)

        return text.strip()

    def clean_for_analysis(self, text: str) -> str:
        """Lowercases and cleans text for similarity comparison."""
        norm = self.normalize_text(text).lower()
        # Remove punctuation for fuzzy/bag-of-words token comparison
        cleaned = re.sub(r'[^\w\s\u0900-\u097F]', ' ', norm)
        return re.sub(r'\s+', ' ', cleaned).strip()

    def tokenize_words(self, text: str) -> List[str]:
        """Extracts words supporting both Latin and Devanagari scripts."""
        cleaned = self.clean_for_analysis(text)
        return [w for w in cleaned.split() if w]

    def split_sentences(self, text: str, page_number: int = 1, base_offset: int = 0) -> List[SentenceUnit]:
        """Segments text into sentences with exact character offsets, supporting Devanagari and Latin."""
        if not text:
            return []

        # Regex recognizing English (. ? !) and Devanagari danda (। \u0964, ॥ \u0965)
        # Uses lookbehind to capture boundaries while checking for abbreviation safety
        pattern = re.compile(
            r'([^\n.?!।॥]+[.?!।॥]+[\s\n]*|[^\n.?!।॥]+$)'
        )

        raw_chunks = list(pattern.finditer(text))
        sentences: List[SentenceUnit] = []
        sentence_idx = 0

        buffer_text = ""
        buffer_start = 0

        for match in raw_chunks:
            chunk = match.group(0)
            chunk_clean = chunk.strip()
            if not chunk_clean:
                continue

            if not buffer_text:
                buffer_start = match.start()
                buffer_text = chunk
            else:
                buffer_text += chunk

            # Check if buffer ends with an abbreviation
            last_word = buffer_text.strip().split()[-1].lower() if buffer_text.strip().split() else ""
            if last_word in COMMON_ABBREVIATIONS and not buffer_text.endswith(("\n", "\r")):
                # Likely part of same sentence
                continue

            # Complete sentence unit
            orig_sentence = buffer_text.strip()
            norm_analysis = self.clean_for_analysis(orig_sentence)
            tokens = norm_analysis.split()

            if len(tokens) >= self.min_words or len(orig_sentence) >= 15:
                s_hash = hashlib.sha256(norm_analysis.encode("utf-8")).hexdigest()
                sentences.append(SentenceUnit(
                    index=sentence_idx,
                    page_number=page_number,
                    original_text=orig_sentence,
                    normalized_text=norm_analysis,
                    start_char=base_offset + buffer_start,
                    end_char=base_offset + buffer_start + len(buffer_text),
                    tokens=tokens,
                    hash=s_hash,
                ))
                sentence_idx += 1

            buffer_text = ""

        # Flush any remaining buffer
        if buffer_text.strip():
            orig_sentence = buffer_text.strip()
            norm_analysis = self.clean_for_analysis(orig_sentence)
            tokens = norm_analysis.split()
            if tokens:
                s_hash = hashlib.sha256(norm_analysis.encode("utf-8")).hexdigest()
                sentences.append(SentenceUnit(
                    index=sentence_idx,
                    page_number=page_number,
                    original_text=orig_sentence,
                    normalized_text=norm_analysis,
                    start_char=base_offset + buffer_start,
                    end_char=base_offset + buffer_start + len(buffer_text),
                    tokens=tokens,
                    hash=s_hash,
                ))

        return sentences

    def preprocess_pages(self, pages: List[PageData], language: str = "English") -> PreprocessedDocument:
        """Preprocesses a list of pages into a structured PreprocessedDocument."""
        all_sentences: List[SentenceUnit] = []
        all_paragraphs: List[str] = []
        full_original_text = ""
        total_words = 0

        for page in pages:
            # Segment page text into sentences
            page_sentences = self.split_sentences(
                page.text,
                page_number=page.page_number,
                base_offset=page.char_start,
            )
            all_sentences.extend(page_sentences)

            # Extract paragraphs
            paras = [p.strip() for p in page.text.split("\n\n") if p.strip()]
            all_paragraphs.extend(paras)

            full_original_text += page.text + "\n\n"
            total_words += page.word_count

        normalized_full = self.clean_for_analysis(full_original_text)

        return PreprocessedDocument(
            original_full_text=full_original_text.strip(),
            normalized_full_text=normalized_full,
            sentences=all_sentences,
            paragraphs=all_paragraphs,
            language=language,
            word_count=total_words,
        )
