"""Manuscript health score: derived only from real validation issues. Deterministic."""

from __future__ import annotations

from app.domain.issues import (
    HealthContributor,
    HealthScore,
    Issue,
    IssueCategory,
    Severity,
    clamp_score,
)

CATEGORY_WEIGHTS: dict[str, float] = {
    "Structure": 0.20,
    "Formatting": 0.20,
    "References": 0.15,
    "Figures & Tables": 0.15,
    "Metadata": 0.15,
    "Layout": 0.15,
}

_PENALTY = {Severity.ERROR: 25, Severity.WARNING: 10, Severity.INFO: 4}
_MAX_CATEGORY_DEDUCTION = 60


def _health_category(issue: Issue) -> str:
    if issue.id.startswith("meta-"):
        return "Metadata"
    if issue.category == IssueCategory.FORMATTING:
        return "Formatting"
    if issue.category == IssueCategory.REFERENCES:
        return "References"
    if issue.category == IssueCategory.LAYOUT:
        return "Figures & Tables" if issue.id.startswith(("fig-", "tbl-")) else "Layout"
    return "Structure"


def score(issues: list[Issue], manuscript=None) -> HealthScore:
    deductions = dict.fromkeys(CATEGORY_WEIGHTS, 0)
    contributors: list[HealthContributor] = []

    for issue in issues:
        category = _health_category(issue)
        penalty = _PENALTY.get(issue.severity, _PENALTY[Severity.INFO])
        before = deductions[category]
        deductions[category] = min(_MAX_CATEGORY_DEDUCTION, before + penalty)
        applied = deductions[category] - before
        if applied:
            contributors.append(
                HealthContributor(category=category, delta=-applied, reason=issue.message)
            )

    categories = {c: clamp_score(100 - deductions[c]) for c in CATEGORY_WEIGHTS}
    total = clamp_score(sum(categories[c] * w for c, w in CATEGORY_WEIGHTS.items()))
    return HealthScore(total=total, categories=categories, contributors=contributors)
