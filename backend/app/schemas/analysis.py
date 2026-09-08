from __future__ import annotations

from pydantic import BaseModel

from app.domain.elements import SectionNode
from app.domain.manuscript import DocumentStats
from app.schemas.metadata import MetadataOut
from app.schemas.validation import IssueOut
from app.storage.base import DocumentRecord


class StageOut(BaseModel):
    key: str
    label: str
    status: str
    detail: str


class StatsOut(BaseModel):
    words: int
    paragraphs: int
    headings: int
    tables: int
    figures: int
    references: int
    sections: int

    @classmethod
    def from_domain(cls, stats: DocumentStats) -> StatsOut:
        return cls(
            words=stats.words,
            paragraphs=stats.paragraphs,
            headings=stats.headings,
            tables=stats.tables,
            figures=stats.figures,
            references=stats.references,
            sections=stats.sections,
        )


class AnalysisOut(BaseModel):
    state: str
    stages: list[StageOut]
    stats: StatsOut | None = None
    metadata: MetadataOut | None = None
    parse_warnings: list[str] = []
    issues_preview: list[IssueOut] = []
    error: str | None = None

    @classmethod
    def from_record(cls, record: DocumentRecord) -> AnalysisOut:
        prog = record.analysis
        stages = (
            [
                StageOut(key=s.key, label=s.label, status=str(s.status), detail=s.detail)
                for s in prog.stages
            ]
            if prog
            else []
        )
        ms = record.manuscript
        return cls(
            state=record.state,
            stages=stages,
            stats=StatsOut.from_domain(ms.stats) if ms else None,
            metadata=MetadataOut.from_domain(ms.metadata) if ms else None,
            parse_warnings=list(ms.parse_warnings) if ms else [],
            issues_preview=[IssueOut.from_domain(i) for i in record.issues],
            error=record.error,
        )


class ElementOut(BaseModel):
    id: str
    kind: str
    confidence: float
    text_preview: str
    needs_review: bool
    level: int | None = None
    number: int | None = None
    section: str | None = None


class ElementPage(BaseModel):
    items: list[ElementOut]
    total: int
    offset: int
    limit: int


class OutlineNodeOut(BaseModel):
    id: str
    label: str
    level: int
    block_id: str | None
    canonical: str | None
    children: list[OutlineNodeOut] = []

    @classmethod
    def from_node(cls, node: SectionNode) -> OutlineNodeOut:
        return cls(
            id=node.id,
            label=node.label,
            level=node.level,
            block_id=node.block_id,
            canonical=node.canonical,
            children=[cls.from_node(c) for c in node.children],
        )


OutlineNodeOut.model_rebuild()


class OutlineOut(BaseModel):
    nodes: list[OutlineNodeOut]
