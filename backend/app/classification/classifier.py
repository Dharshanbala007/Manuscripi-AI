"""classify_blocks: ParsedBlocks + reviewed Metadata -> ordered domain Blocks.

A conservative rule cascade. Low-confidence results are flagged for review,
never silently forced into a destructive shape.
"""

from __future__ import annotations

import re

from app.classification.structure import canonicalize_heading
from app.domain.elements import Block, ElementType, FormattingState, SourceRef
from app.domain.manuscript import Metadata
from app.parsing.blocks import ParsedBlock

_CAPTION_RE = re.compile(
    r"^\s*(figure|fig\.?|table|tbl\.?)\s*([0-9]+|[ivxlcdm]+|[a-z])\b", re.IGNORECASE
)
_REF_ITEM_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+\S")
_NUM_HEADING_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+\S")


def classify_blocks(
    parsed: list[ParsedBlock],
    metadata: Metadata,
    confidence_threshold: float = 0.6,
) -> list[Block]:
    meta_refs = _metadata_refs(metadata)
    abstract_norm = _norm(metadata.abstract.value)

    blocks: list[Block] = []
    current_section: str | None = None
    in_references = False
    abstract_active = False

    for pb in parsed:
        idx = pb.source_ref.index
        text = pb.text or ""
        block = Block(
            id=f"b{idx}",
            kind=ElementType.PARAGRAPH,
            text=text,
            source_ref=pb.source_ref
            if isinstance(pb.source_ref, SourceRef)
            else SourceRef(index=idx),
            formatting=_formatting(pb),
        )

        kind, level, number, confidence = _classify_one(
            pb,
            text,
            idx,
            meta_refs,
            abstract_norm,
            abstract_active,
            current_section,
            in_references,
        )

        block.kind = kind
        block.level = level
        block.number = number
        block.confidence = round(confidence, 3)
        block.section = current_section
        block.needs_review = confidence < confidence_threshold

        if kind == ElementType.HEADING or kind == ElementType.SUBHEADING:
            current_section = canonicalize_heading(text)
            block.section = current_section
            in_references = current_section == "references"
            abstract_active = False
        elif kind == ElementType.ABSTRACT:
            abstract_active = True
        elif abstract_active and kind != ElementType.ABSTRACT:
            abstract_active = False

        blocks.append(block)

    return blocks


def _classify_one(
    pb: ParsedBlock,
    text: str,
    idx: int,
    meta_refs: dict[str, int],
    abstract_norm: str,
    abstract_active: bool,
    current_section: str | None,
    in_references: bool,
) -> tuple[ElementType, int | None, int | None, float]:
    stripped = text.strip()

    if pb.kind_hint == "table":
        return ElementType.TABLE, None, None, 1.0
    if pb.kind_hint == "image":
        return ElementType.FIGURE, None, None, 0.9
    if pb.has_equation and not stripped:
        return ElementType.EQUATION, None, None, 0.9

    if meta_refs.get("title") == idx:
        return ElementType.TITLE, None, None, 0.95
    if meta_refs.get("authors") == idx:
        return ElementType.AUTHOR, None, None, 0.9
    if meta_refs.get("keywords") == idx:
        return ElementType.KEYWORDS, None, None, 0.9
    if meta_refs.get("abstract") == idx:
        return ElementType.ABSTRACT, None, None, 0.9
    if abstract_active and abstract_norm and _norm(stripped) and _norm(stripped) in abstract_norm:
        return ElementType.ABSTRACT, None, None, 0.85

    caption = _CAPTION_RE.match(stripped)
    if caption:
        return ElementType.CAPTION, None, _as_int(caption.group(2)), 0.85

    if pb.outline_level is not None:
        level = max(pb.outline_level + 1, 1)
        kind = ElementType.SUBHEADING if level >= 3 else ElementType.HEADING
        return kind, level, None, 0.95

    num_heading = _NUM_HEADING_RE.match(stripped)
    if (
        num_heading
        and len(stripped.split()) <= 12
        and (pb.all_bold or not stripped.rstrip().endswith("."))
    ):
        level = len(num_heading.group(1).split("."))
        kind = ElementType.SUBHEADING if level >= 3 else ElementType.HEADING
        return kind, level, None, 0.75

    if (
        stripped
        and len(stripped.split()) <= 8
        and not stripped.rstrip().endswith((".", ",", ";"))
        and (stripped.isupper() or pb.all_bold)
        and pb.kind_hint == "paragraph"
        and not pb.numbering
    ):
        return ElementType.HEADING, 1, None, 0.5

    if in_references:
        ref = _REF_ITEM_RE.match(stripped)
        if ref:
            return ElementType.REFERENCE_ITEM, None, _as_int(ref.group(1) or ref.group(2)), 0.9

    if pb.numbering == "bullet":
        return ElementType.BULLET_LIST_ITEM, None, None, 0.85
    if pb.numbering in ("number", "list"):
        return ElementType.NUMBERED_LIST_ITEM, None, None, 0.85

    if current_section == "acknowledgement":
        return ElementType.ACKNOWLEDGEMENT, None, None, 0.8
    if current_section == "appendix":
        return ElementType.APPENDIX, None, None, 0.8

    return ElementType.PARAGRAPH, None, None, 0.9


def _metadata_refs(metadata: Metadata) -> dict[str, int]:
    refs: dict[str, int] = {}
    for key, field in (
        ("title", metadata.title),
        ("authors", metadata.authors),
        ("abstract", metadata.abstract),
        ("keywords", metadata.keywords),
    ):
        ref = field.source_ref
        has_value = bool(field.value) if not isinstance(field.value, list) else bool(field.value)
        if ref is not None and has_value:
            refs[key] = ref.index
    return refs


def _formatting(pb: ParsedBlock) -> FormattingState:
    first = pb.runs[0] if pb.runs else None
    return FormattingState(
        font=first.font if first else None,
        size_pt=pb.max_size_pt,
        bold=pb.all_bold,
        italic=bool(pb.runs) and all(r.italic for r in pb.runs if r.text.strip()),
        alignment=pb.alignment,
        style_name=pb.style_name,
    )


def _norm(s: str) -> str:
    return " ".join((s or "").split()).lower()


def _as_int(token: str | None) -> int | None:
    return int(token) if token and token.isdigit() else None
