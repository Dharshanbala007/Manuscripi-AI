"""Compare the original manuscript against the formatted output for content loss."""

from __future__ import annotations

from pathlib import Path

from app.classification.classifier import classify_blocks
from app.domain.issues import PreservationResult
from app.domain.manuscript import Manuscript
from app.extraction.metadata import extract_metadata
from app.formatting.frontmatter import frontmatter_end
from app.parsing.docx_reader import parse_docx
from app.utils.text import normalize_ws, text_hash


def _body_text(blocks) -> str:
    start = frontmatter_end(blocks)
    return normalize_ws(" ".join(b.text for b in blocks[start:]))


def check_preservation(original: Manuscript, formatted_path: Path | str) -> PreservationResult:
    parsed = parse_docx(formatted_path)
    fmt_md = extract_metadata(parsed.blocks, 0.6)
    fmt_blocks = classify_blocks(parsed.blocks, fmt_md, 0.6)

    before = _body_text(original.body)
    after = _body_text(fmt_blocks)
    text_match = text_hash(before) == text_hash(after)

    orig_paras = sum(1 for b in original.body if (b.text or "").strip())
    fmt_paras = sum(1 for b in fmt_blocks if (b.text or "").strip())
    delta = fmt_paras - orig_paras

    details: list[str] = []
    if not text_match:
        details.append("Body text differs between the original and the formatted document.")
        bw, aw = len(before.split()), len(after.split())
        if bw != aw:
            details.append(f"Body word count changed from {bw} to {aw}.")

    return PreservationResult(
        passed=text_match,
        paragraph_delta=delta,
        text_match=text_match,
        details=details,
    )
