"""DocumentRecord + the DocumentStore interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.domain.analysis import AnalysisProgress
from app.domain.issues import ChangeLog, HealthScore, Issue, PreservationResult
from app.domain.manuscript import Manuscript

# Lifecycle states. Kept as plain strings so the store stays serialization-agnostic.
STATES = (
    "uploaded",
    "analyzing",
    "analyzed",
    "formatting",
    "formatted",
    "validating",
    "validated",
    "exported",
    "error",
)


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class DocumentRecord:
    id: str
    filename: str
    size: int
    state: str = "uploaded"
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    source_path: Path | None = None
    manuscript: Manuscript | None = None
    analysis: AnalysisProgress | None = None
    artifacts: dict[str, Path] = field(default_factory=dict)
    change_log: ChangeLog | None = None
    issues: list[Issue] = field(default_factory=list)
    health: HealthScore | None = None
    preservation: PreservationResult | None = None
    profile_id: str | None = None
    page_count: int | None = None
    error: str | None = None
    error_id: str | None = None
    # Anonymous per-browser id; only meaningful on a shared (hosted) server.
    owner: str = ""


class DocumentStore(ABC):
    """Persistence boundary. One in-memory implementation today; a SQLite one later."""

    @abstractmethod
    def create(self, record: DocumentRecord) -> DocumentRecord: ...

    @abstractmethod
    def get(self, doc_id: str) -> DocumentRecord | None: ...

    @abstractmethod
    def update(self, record: DocumentRecord) -> DocumentRecord: ...

    @abstractmethod
    def delete(self, doc_id: str) -> None: ...

    @abstractmethod
    def list(self) -> list[DocumentRecord]: ...
