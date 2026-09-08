"""Element-level model: classified blocks and the derived section outline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ElementType(StrEnum):
    TITLE = "title"
    AUTHOR = "author"
    AFFILIATION = "affiliation"
    ABSTRACT = "abstract"
    KEYWORDS = "keywords"
    HEADING = "heading"
    SUBHEADING = "subheading"
    PARAGRAPH = "paragraph"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    BULLET_LIST_ITEM = "bullet_list_item"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    EQUATION = "equation"
    REFERENCE_ITEM = "reference_item"
    ACKNOWLEDGEMENT = "acknowledgement"
    APPENDIX = "appendix"
    OTHER = "other"


@dataclass
class SourceRef:
    """Locates a block's origin element in the source package, for round-tripping."""

    part: str = "document"
    index: int = -1

    def __str__(self) -> str:
        return f"{self.part}[{self.index}]"


@dataclass
class FormattingState:
    font: str | None = None
    size_pt: float | None = None
    bold: bool = False
    italic: bool = False
    alignment: str | None = None
    style_name: str | None = None


@dataclass
class Block:
    id: str
    kind: ElementType
    text: str = ""
    confidence: float = 1.0
    source_ref: SourceRef = field(default_factory=SourceRef)
    level: int | None = None
    list_kind: str | None = None
    number: int | None = None
    section: str | None = None
    formatting: FormattingState = field(default_factory=FormattingState)
    needs_review: bool = False
    validation_notes: list[str] = field(default_factory=list)


@dataclass
class SectionNode:
    id: str
    label: str
    level: int
    block_id: str | None = None
    canonical: str | None = None
    children: list[SectionNode] = field(default_factory=list)
