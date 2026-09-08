"""Manuscript-level model: metadata, body, outline, statistics."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.elements import Block, SectionNode, SourceRef


@dataclass
class Field[T]:
    """A detected metadata value plus how confident detection was and whether the
    user has since corrected it. User corrections are never auto-overwritten."""

    value: T
    confidence: float = 0.0
    source_ref: SourceRef | None = None
    edited_by_user: bool = False

    def set_by_user(self, value: T) -> None:
        self.value = value
        self.confidence = 1.0
        self.edited_by_user = True


@dataclass
class Affiliation:
    id: str
    text: str
    confidence: float = 0.0


@dataclass
class Author:
    name: str
    email: str | None = None
    affiliation_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Metadata:
    title: Field[str]
    authors: Field[list[Author]]
    affiliations: list[Affiliation]
    abstract: Field[str]
    keywords: Field[list[str]]

    @staticmethod
    def empty() -> Metadata:
        return Metadata(
            title=Field(value=""),
            authors=Field(value=[]),
            affiliations=[],
            abstract=Field(value=""),
            keywords=Field(value=[]),
        )


@dataclass
class DocumentStats:
    words: int = 0
    paragraphs: int = 0
    headings: int = 0
    tables: int = 0
    figures: int = 0
    references: int = 0
    sections: int = 0


@dataclass
class Manuscript:
    id: str
    source_filename: str
    metadata: Metadata
    body: list[Block] = field(default_factory=list)
    outline: list[SectionNode] = field(default_factory=list)
    stats: DocumentStats = field(default_factory=DocumentStats)
    parse_warnings: list[str] = field(default_factory=list)
