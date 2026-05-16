"""Request/upload size and processing limits."""

from __future__ import annotations

import os


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


MAX_UPLOAD_BYTES: int = _int_env("LOU_MAX_UPLOAD_BYTES", 50 * 1024 * 1024)
MAX_PDF_PAGES: int = _int_env("LOU_MAX_PDF_PAGES", 300)
MAX_DOCX_PARAGRAPHS: int = _int_env("LOU_MAX_DOCX_PARAGRAPHS", 10_000)
MAX_AUDIO_BYTES: int = _int_env("LOU_MAX_AUDIO_BYTES", 30 * 1024 * 1024)
REQUEST_TIMEOUT_SECONDS: float = float(_int_env("LOU_REQUEST_TIMEOUT_SECONDS", 30))
RATE_LIMIT_PER_MINUTE: int = _int_env("LOU_RATE_LIMIT_PER_MINUTE", 60)
DOCX_MAX_RATIO: int = _int_env("LOU_DOCX_MAX_COMPRESSION_RATIO", 100)


PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"


def detect_kind(content: bytes) -> str:
    """Return 'pdf', 'docx', or 'unknown' from the first bytes of a payload."""
    if content.startswith(PDF_MAGIC):
        return "pdf"
    if content.startswith(DOCX_MAGIC):
        return "docx"
    return "unknown"
