from __future__ import annotations

from pydantic import BaseModel

from app.domain.issues import HealthScore, Issue, PreservationResult


class IssueOut(BaseModel):
    id: str
    severity: str
    category: str
    message: str
    location: str | None = None
    suggested_action: str | None = None

    @classmethod
    def from_domain(cls, issue: Issue) -> IssueOut:
        return cls(
            id=issue.id,
            severity=str(issue.severity),
            category=str(issue.category),
            message=issue.message,
            location=issue.location,
            suggested_action=issue.suggested_action,
        )


class HealthContributorOut(BaseModel):
    category: str
    delta: int
    reason: str


class HealthScoreOut(BaseModel):
    total: int
    categories: dict[str, int]
    contributors: list[HealthContributorOut]

    @classmethod
    def from_domain(cls, score: HealthScore) -> HealthScoreOut:
        return cls(
            total=score.total,
            categories=dict(score.categories),
            contributors=[
                HealthContributorOut(category=c.category, delta=c.delta, reason=c.reason)
                for c in score.contributors
            ],
        )


class PreservationOut(BaseModel):
    passed: bool
    paragraph_delta: int
    text_match: bool
    details: list[str]

    @classmethod
    def from_domain(cls, result: PreservationResult) -> PreservationOut:
        return cls(
            passed=result.passed,
            paragraph_delta=result.paragraph_delta,
            text_match=result.text_match,
            details=list(result.details),
        )
