"""Document statistics computed from classified blocks. Shared by the pipeline
and the before/after comparison."""

from __future__ import annotations

from app.domain.elements import Block, ElementType
from app.domain.manuscript import DocumentStats
from app.utils.text import count_words

_HEADING_KINDS = (ElementType.HEADING, ElementType.SUBHEADING)


def compute_stats(blocks: list[Block]) -> DocumentStats:
    return DocumentStats(
        words=sum(count_words(b.text) for b in blocks),
        paragraphs=sum(1 for b in blocks if b.kind == ElementType.PARAGRAPH),
        headings=sum(1 for b in blocks if b.kind in _HEADING_KINDS),
        tables=sum(1 for b in blocks if b.kind == ElementType.TABLE),
        figures=sum(1 for b in blocks if b.kind == ElementType.FIGURE),
        references=sum(1 for b in blocks if b.kind == ElementType.REFERENCE_ITEM),
        sections=sum(1 for b in blocks if b.kind == ElementType.HEADING),
    )
