"""Validation findings, health score, and change/preservation reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(StrEnum):
    DOCUMENT = "document"
    STRUCTURE = "structure"
    FORMATTING = "formatting"
    CONTENT = "content"
    REFERENCES = "references"
    LAYOUT = "layout"


@dataclass
class Issue:
    id: str
    severity: Severity
    category: IssueCategory
    message: str
    location: str | None = None
    suggested_action: str | None = None


@dataclass
class HealthContributor:
    category: str
    delta: int
    reason: str


@dataclass
class HealthScore:
    total: int = 100
    categories: dict[str, int] = field(default_factory=dict)
    contributors: list[HealthContributor] = field(default_factory=list)


@dataclass
class ChangeLog:
    formatting_changes: list[str] = field(default_factory=list)
    content_changes: list[str] = field(default_factory=list)
    warnings_remaining: int = 0


@dataclass
class PreservationResult:
    passed: bool
    paragraph_delta: int = 0
    text_match: bool = True
    details: list[str] = field(default_factory=list)


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))
