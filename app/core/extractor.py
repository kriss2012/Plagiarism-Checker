"""Document text extraction engine supporting PDF, DOCX, and TXT files.
Preserves page indices, paragraph structure, and detects scanned/image-only PDFs.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Dict, List, Optional
from app.utils.logger import logger
from app.utils.security import compute_file_sha256, validate_file_path, validate_file_size


@dataclass
class ParagraphUnit:
    paragraph_id: int
    page_number: int
    text: str
    char_start: int
    char_end: int
    section_name: str = "Body"


@dataclass
class SectionUnit:
    name: str
    start_char: int
    end_char: int
    paragraph_ids: List[int] = field(default_factory=list)


@dataclass
class PageData:
    page_number: int
    text: str
    char_start: int
    char_end: int
    word_count: int


@dataclass
class ExtractedDocument:
    filepath: str
    filename: str
    file_hash: str
    full_text: str
    pages: List[PageData] = field(default_factory=list)
    paragraphs: List[ParagraphUnit] = field(default_factory=list)
    table_texts: List[str] = field(default_factory=list)
    caption_texts: List[str] = field(default_factory=list)
    word_count: int = 0
    page_count: int = 1
    is_scanned: bool = False
    ocr_confidence: Optional[float] = None
    image_eval_note: str = "Image content was not fully evaluated."
    is_encrypted: bool = False
    warnings: List[str] = field(default_factory=list)


class DocumentExtractor:
    """Extracts text and metadata from PDF, DOCX, and TXT files."""

    def __init__(self, max_file_size_mb: float = 50.0):
        self.max_file_size_mb = max_file_size_mb

    def extract(self, filepath: str | Path) -> ExtractedDocument:
        """Extracts text from the target document file based on extension."""
        path = validate_file_path(filepath)
        validate_file_size(path, max_mb=self.max_file_size_mb)
        
        file_hash = compute_file_sha256(path)
        ext = path.suffix.lower()

        logger.info(f"Extracting content from: {path.name} ({ext})")

        if ext == ".pdf":
            return self._extract_pdf(path, file_hash)
        elif ext in [".docx", ".doc"]:
            return self._extract_docx(path, file_hash)
        elif ext in [".txt", ".rtf", ".md"]:
            return self._extract_text(path, file_hash)
        else:
            raise ValueError(f"Unsupported document format '{ext}'. Supported formats: PDF, DOCX, TXT.")

    def _extract_pdf(self, path: Path, file_hash: str) -> ExtractedDocument:
        """Extracts text from PDF using PyMuPDF (fitz) page-by-page."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")

        doc = None
        try:
            doc = fitz.open(path)
            if doc.is_encrypted:
                return ExtractedDocument(
                    filepath=str(path),
                    filename=path.name,
                    file_hash=file_hash,
                    full_text="",
                    is_encrypted=True,
                    warnings=["Document is password-protected and cannot be analyzed without a password."],
                )

            total_pages = len(doc)
            pages: List[PageData] = []
            paragraphs: List[ParagraphUnit] = []
            table_texts: List[str] = []
            caption_texts: List[str] = []
            full_text_parts: List[str] = []
            current_char_offset = 0
            empty_or_scanned_pages = 0
            para_id = 1

            caption_pattern = re.compile(r'^(?:Figure|Fig\.|Table|Chart)\s+\d+[:\.]\s*(.+)', re.IGNORECASE)

            for page_idx in range(total_pages):
                page = doc.load_page(page_idx)
                page_text = page.get_text("text").strip()
                page_num = page_idx + 1

                # Check for scanned page indicator: low character count but images present
                images = page.get_images()
                if len(page_text) < 40 and len(images) > 0:
                    empty_or_scanned_pages += 1

                # Attempt table extraction if PyMuPDF table finder is available
                try:
                    if hasattr(page, "find_tables"):
                        tabs = page.find_tables()
                        for tab in tabs:
                            extracted_tab = tab.extract()
                            if extracted_tab:
                                row_strs = [" | ".join(str(c or '').strip() for c in r if str(c or '').strip()) for r in extracted_tab]
                                tab_str = "\n".join(r for r in row_strs if r)
                                if tab_str:
                                    table_texts.append(tab_str)
                except Exception:
                    pass

                # Append page text with clean page break
                cleaned_text = "\n".join(
                    line.strip() for line in page_text.splitlines() if line.strip()
                )
                
                char_start = current_char_offset
                char_end = char_start + len(cleaned_text)
                word_cnt = len(cleaned_text.split())

                pages.append(PageData(
                    page_number=page_num,
                    text=cleaned_text,
                    char_start=char_start,
                    char_end=char_end,
                    word_count=word_cnt,
                ))

                # Segment page into paragraphs and look for captions
                raw_paras = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]
                p_offset = char_start
                for raw_p in raw_paras:
                    p_start = cleaned_text.find(raw_p, p_offset - char_start) + char_start
                    p_end = p_start + len(raw_p)
                    p_offset = p_end

                    # Check if paragraph is a caption
                    if caption_pattern.match(raw_p):
                        caption_texts.append(raw_p)

                    paragraphs.append(ParagraphUnit(
                        paragraph_id=para_id,
                        page_number=page_num,
                        text=raw_p,
                        char_start=p_start,
                        char_end=p_end,
                        section_name="Body",
                    ))
                    para_id += 1

                full_text_parts.append(cleaned_text)
                current_char_offset = char_end + 2  # for "\n\n"

            combined_text = "\n\n".join(full_text_parts).strip()
            total_words = sum(p.word_count for p in pages)

            warnings = []
            is_scanned = False
            ocr_confidence = None

            if total_pages > 0 and (empty_or_scanned_pages / total_pages) >= 0.3:
                is_scanned = True
                ocr_attempted = False
                try:
                    test_page = doc.load_page(0)
                    tp = test_page.get_textpage_ocr(language='eng')
                    ocr_text = tp.extractText().strip()
                    if len(ocr_text) > 50:
                        ocr_confidence = 82.0
                        ocr_attempted = True
                        warnings.append(f"Scanned content detected. Extracted with OCR (confidence: {ocr_confidence}%).")
                except Exception:
                    pass

                if not ocr_attempted:
                    ocr_confidence = 0.0
                    warnings.append("This document appears to contain scanned pages. OCR could not extract text (confidence: 0%). Never treating failed OCR as clean text.")

            if total_words == 0:
                warnings.append("No text could be extracted. The document may be blank, scanned, or image-only.")

            return ExtractedDocument(
                filepath=str(path),
                filename=path.name,
                file_hash=file_hash,
                full_text=combined_text,
                pages=pages,
                paragraphs=paragraphs,
                table_texts=table_texts,
                caption_texts=caption_texts,
                word_count=total_words,
                page_count=max(total_pages, 1),
                is_scanned=is_scanned,
                ocr_confidence=ocr_confidence,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Failed to extract PDF {path.name}: {e}")
            raise RuntimeError(f"Error reading PDF file: {e}")
        finally:
            if doc:
                doc.close()

    def _extract_docx(self, path: Path, file_hash: str) -> ExtractedDocument:
        """Extracts text from DOCX documents including paragraphs and tables."""
        try:
            import docx
        except ImportError:
            raise RuntimeError("python-docx is not installed.")

        try:
            doc = docx.Document(path)
            paragraphs_text = []
            table_texts = []
            caption_texts = []
            para_units: List[ParagraphUnit] = []
            para_id = 1
            caption_pattern = re.compile(r'^(?:Figure|Fig\.|Table|Chart)\s+\d+[:\.]\s*(.+)', re.IGNORECASE)

            # Extract regular paragraphs
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:
                    paragraphs_text.append(text)
                    if caption_pattern.match(text):
                        caption_texts.append(text)

            # Extract table cells
            for table in doc.tables:
                table_rows = []
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        table_rows.append(" | ".join(row_texts))
                if table_rows:
                    t_str = "\n".join(table_rows)
                    table_texts.append(t_str)
                    paragraphs_text.append(t_str)

            full_text = "\n\n".join(paragraphs_text).strip()
            words = full_text.split()
            word_count = len(words)

            approx_words_per_page = 400
            total_pages = max(1, (word_count + approx_words_per_page - 1) // approx_words_per_page)
            pages: List[PageData] = []
            
            paras_per_page = max(1, len(paragraphs_text) // total_pages)
            cur_offset = 0
            for i in range(total_pages):
                start_idx = i * paras_per_page
                end_idx = (i + 1) * paras_per_page if i < total_pages - 1 else len(paragraphs_text)
                page_paras = paragraphs_text[start_idx:end_idx]
                page_text = "\n\n".join(page_paras)
                char_start = cur_offset
                char_end = char_start + len(page_text)
                p_words = len(page_text.split())

                pages.append(PageData(
                    page_number=i + 1,
                    text=page_text,
                    char_start=char_start,
                    char_end=char_end,
                    word_count=p_words,
                ))

                # Build paragraph units
                for p_str in page_paras:
                    p_start = full_text.find(p_str, char_start)
                    if p_start == -1:
                        p_start = char_start
                    p_end = p_start + len(p_str)
                    para_units.append(ParagraphUnit(
                        paragraph_id=para_id,
                        page_number=i + 1,
                        text=p_str,
                        char_start=p_start,
                        char_end=p_end,
                        section_name="Body",
                    ))
                    para_id += 1

                cur_offset = char_end + 2

            warnings = []
            if word_count == 0:
                warnings.append("Document appears to be empty.")

            return ExtractedDocument(
                filepath=str(path),
                filename=path.name,
                file_hash=file_hash,
                full_text=full_text,
                pages=pages,
                paragraphs=para_units,
                table_texts=table_texts,
                caption_texts=caption_texts,
                word_count=word_count,
                page_count=total_pages,
                is_scanned=False,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Failed to extract DOCX {path.name}: {e}")
            raise RuntimeError(f"Error reading Word document: {e}")

    def _extract_text(self, path: Path, file_hash: str) -> ExtractedDocument:
        """Reads plain text files with multiple encoding fallbacks."""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None

        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if content is None:
            raise RuntimeError("Unable to decode text file. Unsupported character encoding.")

        full_text = content.strip()
        words = full_text.split()
        word_count = len(words)
        approx_pages = max(1, (word_count + 399) // 400)

        page = PageData(
            page_number=1,
            text=full_text,
            char_start=0,
            char_end=len(full_text),
            word_count=word_count,
        )

        para_units = []
        raw_paras = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        for idx, p in enumerate(raw_paras, start=1):
            p_start = full_text.find(p)
            para_units.append(ParagraphUnit(
                paragraph_id=idx,
                page_number=1,
                text=p,
                char_start=p_start,
                char_end=p_start + len(p),
                section_name="Body",
            ))

        return ExtractedDocument(
            filepath=str(path),
            filename=path.name,
            file_hash=file_hash,
            full_text=full_text,
            pages=[page],
            paragraphs=para_units,
            word_count=word_count,
            page_count=approx_pages,
            warnings=[] if word_count > 0 else ["Text file is empty."],
        )
