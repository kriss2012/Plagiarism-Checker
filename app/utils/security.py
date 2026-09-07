"""Security and validation utilities for ResearchGuard.
Guards against path traversal, oversized files, unsafe hashes, and malicious content.
"""

import hashlib
import html
import os
import re
from pathlib import Path
from typing import Optional


def compute_file_sha256(filepath: str | Path) -> str:
    """Computes SHA-256 hash of a file efficiently in chunks."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_text_sha256(text: str) -> str:
    """Computes SHA-256 hash of a string in UTF-8."""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitizes a filename to prevent directory traversal and invalid Windows characters."""
    base_name = os.path.basename(filename)
    # Remove control characters, slashes, and characters disallowed on Windows (<>:"/\|?*)
    clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base_name)
    clean_name = clean_name.strip(" .")
    if not clean_name:
        clean_name = "unnamed_document"
    return clean_name


def validate_file_path(filepath: str | Path, allowed_dir: Optional[str | Path] = None) -> Path:
    """Validates that a file path exists and optionally verifies it does not escape allowed directory."""
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    if allowed_dir:
        allowed = Path(allowed_dir).resolve()
        try:
            path.relative_to(allowed)
        except ValueError:
            raise PermissionError(f"Access denied: path traversal detected for {path}")

    return path


def validate_file_size(filepath: str | Path, max_mb: float = 50.0) -> bool:
    """Checks whether the file size is within permitted limits."""
    size_bytes = os.path.getsize(filepath)
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValueError(f"File exceeds maximum allowed size ({size_bytes / (1024 * 1024):.1f}MB > {max_mb}MB)")
    return True


def sanitize_for_display(text: str) -> str:
    """Escapes HTML entities for safe UI or HTML report display."""
    if not text:
        return ""
    return html.escape(text, quote=True)
