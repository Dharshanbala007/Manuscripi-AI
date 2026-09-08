"""Before/after comparison: the in-memory Manuscript vs the re-parsed formatted DOCX.

Structural + metadata comparison only — no attempt at a pixel-perfect Word diff.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.analysis.stats import compute_stats
from app.classification.classifier import classify_blocks
from app.domain.elements import ElementType
from app.domain.manuscript import DocumentStats, Manuscript, Metadata
from app.extraction.metadata import extract_metadata
from app.parsing.docx_reader import parse_docx
from app.storage.base import DocumentRecord

_HEADING_KINDS = (ElementType.HEADING, ElementType.SUBHEADING)
_DELTA_FIELDS = ("paragraphs", "headings", "tables", "figures", "references")


@dataclass
class MetaSummary:
    title: str
    authors: list[str]
    abstract_present: bool
    keywords: list[str]


@dataclass
class Side:
    stats: DocumentStats
    metadata: MetaSummary
    sections: list[str]


@dataclass
class CompareSummary:
    formatting_changes: int
    content_changes: int
    warnings_remaining: int
    preservation_passed: bool


@dataclass
class Comparison:
    original: Side
    formatted: Side
    deltas: dict[str, int]
    summary: CompareSummary


def build_comparison(record: DocumentRecord) -> Comparison:
    original = _side_from_manuscript(record.manuscript)
    formatted = _side_from_docx(record.artifacts["formatted"])
    deltas = {
        field: getattr(formatted.stats, field) - getattr(original.stats, field)
        for field in _DELTA_FIELDS
    }
    change_log = record.change_log
    summary = CompareSummary(
        formatting_changes=len(change_log.formatting_changes) if change_log else 0,
        content_changes=len(change_log.content_changes) if change_log else 0,
        warnings_remaining=change_log.warnings_remaining if change_log else 0,
        preservation_passed=bool(record.preservation and record.preservation.passed),
    )
    return Comparison(original=original, formatted=formatted, deltas=deltas, summary=summary)


def _side_from_manuscript(ms: Manuscript) -> Side:
    return Side(
        stats=ms.stats,
        metadata=_meta_summary(ms.metadata),
        sections=_sections(ms.body),
    )


def _side_from_docx(path: Path | str) -> Side:
    parsed = parse_docx(path)
    md = extract_metadata(parsed.blocks, 0.6)
    blocks = classify_blocks(parsed.blocks, md, 0.6)
    return Side(stats=compute_stats(blocks), metadata=_meta_summary(md), sections=_sections(blocks))


def _meta_summary(md: Metadata) -> MetaSummary:
    return MetaSummary(
        title=md.title.value,
        authors=[a.name for a in md.authors.value],
        abstract_present=bool(md.abstract.value),
        keywords=list(md.keywords.value),
    )


def _sections(blocks) -> list[str]:
    return [b.text.strip() for b in blocks if b.kind in _HEADING_KINDS and b.text.strip()]
