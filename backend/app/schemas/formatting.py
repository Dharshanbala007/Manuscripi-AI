from __future__ import annotations

from pydantic import BaseModel

from app.domain.issues import ChangeLog
from app.schemas.validation import HealthScoreOut, IssueOut, PreservationOut


class FormatIn(BaseModel):
    profile_id: str


class ChangeLogOut(BaseModel):
    formatting_changes: list[str]
    content_changes: list[str]
    warnings_remaining: int

    @classmethod
    def from_domain(cls, log: ChangeLog) -> ChangeLogOut:
        return cls(
            formatting_changes=list(log.formatting_changes),
            content_changes=list(log.content_changes),
            warnings_remaining=log.warnings_remaining,
        )


class FormatOut(BaseModel):
    state: str
    profile_id: str
    change_log: ChangeLogOut
    health: HealthScoreOut
    issues: list[IssueOut]
    preservation: PreservationOut


class ValidateOut(BaseModel):
    state: str
    issues: list[IssueOut]
    health: HealthScoreOut
    preservation: PreservationOut
