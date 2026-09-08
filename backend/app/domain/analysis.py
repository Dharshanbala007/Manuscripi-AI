"""Analysis progress model — the staged view the frontend polls."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class StageStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"


@dataclass
class Stage:
    key: str
    label: str
    status: StageStatus = StageStatus.PENDING
    detail: str = ""


# Ordered pipeline stages. Keys are stable API contract; labels are display text.
STAGE_DEFS: list[tuple[str, str]] = [
    ("read", "Reading document"),
    ("extract", "Extracting content"),
    ("metadata", "Detecting metadata"),
    ("classify", "Classifying sections"),
    ("figures", "Detecting figures & tables"),
    ("references", "Detecting references"),
    ("structure", "Preparing document structure"),
]


@dataclass
class AnalysisProgress:
    stages: list[Stage] = field(
        default_factory=lambda: [Stage(key, label) for key, label in STAGE_DEFS]
    )

    def stage(self, key: str) -> Stage:
        for s in self.stages:
            if s.key == key:
                return s
        raise KeyError(key)
