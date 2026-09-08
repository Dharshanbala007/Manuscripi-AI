"""Apply user corrections to detected metadata and element classification.

Targeted overrides only: a reclassified element is not re-run through the full
cascade. Section tags and the outline are re-synced; review issues recomputed.
"""

from __future__ import annotations

from app.analysis.pipeline import review_issues
from app.classification.structure import build_outline, canonicalize_heading
from app.domain.elements import Block, ElementType
from app.domain.manuscript import Affiliation, Author, Metadata
from app.schemas.metadata import MetadataIn

_HEADING_KINDS = (ElementType.HEADING, ElementType.SUBHEADING)


def apply_metadata(record, data: MetadataIn) -> Metadata:
    md = record.manuscript.metadata
    if data.title is not None:
        md.title.set_by_user(data.title.strip())
    if data.abstract is not None:
        md.abstract.set_by_user(data.abstract.strip())
    if data.keywords is not None:
        md.keywords.set_by_user([k.strip() for k in data.keywords if k.strip()])
    if data.authors is not None:
        md.authors.set_by_user(
            [
                Author(name=a.name.strip(), email=a.email, affiliation_ids=list(a.affiliation_ids))
                for a in data.authors
                if a.name.strip()
            ]
        )
    if data.affiliations is not None:
        md.affiliations = [
            Affiliation(id=a.id or f"aff{i + 1}", text=a.text.strip(), confidence=1.0)
            for i, a in enumerate(data.affiliations)
            if a.text.strip()
        ]
    _resync(record)
    return md


def apply_element(record, block_id: str, kind: str | None, level: int | None) -> Block | None:
    block = next((b for b in record.manuscript.body if b.id == block_id), None)
    if block is None:
        return None
    if kind is not None:
        block.kind = ElementType(kind)  # ValueError on bad value -> 422 at the route
    if level is not None:
        block.level = level
    block.needs_review = False
    block.confidence = 1.0
    if block.kind in _HEADING_KINDS and block.level is None:
        block.level = 1
    _resync(record)
    return block


def _resync(record) -> None:
    ms = record.manuscript
    _retag_sections(ms.body)
    ms.outline = build_outline(ms.body)
    record.issues = review_issues(ms)


def _retag_sections(blocks: list[Block]) -> None:
    current: str | None = None
    for b in blocks:
        if b.kind in _HEADING_KINDS:
            current = canonicalize_heading(b.text)
        b.section = current
