from __future__ import annotations

from pydantic import BaseModel

from app.domain.manuscript import Affiliation, Author, Field


def _source_index(field: Field) -> int | None:
    return field.source_ref.index if field.source_ref is not None else None


class FieldOut(BaseModel):
    value: str
    confidence: float
    edited_by_user: bool
    source_index: int | None = None

    @classmethod
    def from_field(cls, field: Field) -> FieldOut:
        return cls(
            value=field.value or "",
            confidence=field.confidence,
            edited_by_user=field.edited_by_user,
            source_index=_source_index(field),
        )


class AuthorOut(BaseModel):
    name: str
    email: str | None = None
    affiliation_ids: list[str] = []

    @classmethod
    def from_author(cls, author: Author) -> AuthorOut:
        return cls(
            name=author.name, email=author.email, affiliation_ids=list(author.affiliation_ids)
        )


class AuthorsFieldOut(BaseModel):
    value: list[AuthorOut]
    confidence: float
    edited_by_user: bool

    @classmethod
    def from_field(cls, field: Field) -> AuthorsFieldOut:
        return cls(
            value=[AuthorOut.from_author(a) for a in field.value],
            confidence=field.confidence,
            edited_by_user=field.edited_by_user,
        )


class KeywordsFieldOut(BaseModel):
    value: list[str]
    confidence: float
    edited_by_user: bool

    @classmethod
    def from_field(cls, field: Field) -> KeywordsFieldOut:
        return cls(
            value=list(field.value),
            confidence=field.confidence,
            edited_by_user=field.edited_by_user,
        )


class AffiliationOut(BaseModel):
    id: str
    text: str

    @classmethod
    def from_affiliation(cls, aff: Affiliation) -> AffiliationOut:
        return cls(id=aff.id, text=aff.text)
