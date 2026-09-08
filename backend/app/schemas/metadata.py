from __future__ import annotations

from pydantic import BaseModel

from app.domain.manuscript import Metadata
from app.schemas.common import (
    AffiliationOut,
    AuthorsFieldOut,
    FieldOut,
    KeywordsFieldOut,
)


class MetadataOut(BaseModel):
    title: FieldOut
    authors: AuthorsFieldOut
    affiliations: list[AffiliationOut]
    abstract: FieldOut
    keywords: KeywordsFieldOut

    @classmethod
    def from_domain(cls, md: Metadata) -> MetadataOut:
        return cls(
            title=FieldOut.from_field(md.title),
            authors=AuthorsFieldOut.from_field(md.authors),
            affiliations=[AffiliationOut.from_affiliation(a) for a in md.affiliations],
            abstract=FieldOut.from_field(md.abstract),
            keywords=KeywordsFieldOut.from_field(md.keywords),
        )


class AuthorIn(BaseModel):
    name: str
    email: str | None = None
    affiliation_ids: list[str] = []


class AffiliationIn(BaseModel):
    id: str | None = None
    text: str


class MetadataIn(BaseModel):
    title: str | None = None
    authors: list[AuthorIn] | None = None
    affiliations: list[AffiliationIn] | None = None
    abstract: str | None = None
    keywords: list[str] | None = None
