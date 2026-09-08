from __future__ import annotations

from pydantic import BaseModel

from app.analysis.comparison import Comparison, Side
from app.schemas.analysis import StatsOut


class MetaSummaryOut(BaseModel):
    title: str
    authors: list[str]
    abstract_present: bool
    keywords: list[str]


class SideOut(BaseModel):
    stats: StatsOut
    metadata: MetaSummaryOut
    sections: list[str]

    @classmethod
    def from_side(cls, side: Side) -> SideOut:
        return cls(
            stats=StatsOut.from_domain(side.stats),
            metadata=MetaSummaryOut(**vars(side.metadata)),
            sections=list(side.sections),
        )


class CompareSummaryOut(BaseModel):
    formatting_changes: int
    content_changes: int
    warnings_remaining: int
    preservation_passed: bool


class ComparisonOut(BaseModel):
    original: SideOut
    formatted: SideOut
    deltas: dict[str, int]
    summary: CompareSummaryOut

    @classmethod
    def from_domain(cls, comparison: Comparison) -> ComparisonOut:
        return cls(
            original=SideOut.from_side(comparison.original),
            formatted=SideOut.from_side(comparison.formatted),
            deltas=dict(comparison.deltas),
            summary=CompareSummaryOut(**vars(comparison.summary)),
        )
