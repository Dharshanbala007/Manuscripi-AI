"""Figure checks: flag missing captions and oversize images. Never invent captions."""

from __future__ import annotations

from docx.shared import Inches

from app.domain.elements import ElementType
from app.domain.issues import Issue, IssueCategory, Severity
from app.profiles.base import PublisherProfile


def check_figures(doc, manuscript, profile: PublisherProfile) -> list[Issue]:
    issues: list[Issue] = []
    body = manuscript.body

    for i, block in enumerate(body):
        if block.kind != ElementType.FIGURE:
            continue
        prev_caption = i > 0 and body[i - 1].kind == ElementType.CAPTION
        next_caption = i + 1 < len(body) and body[i + 1].kind == ElementType.CAPTION
        if not (prev_caption or next_caption):
            issues.append(
                Issue(
                    id=f"fig-{block.id}-nocap",
                    severity=Severity.WARNING,
                    category=IssueCategory.LAYOUT,
                    message="A figure has no caption.",
                    location=block.id,
                    suggested_action="Add a caption near the figure, e.g. 'Fig. 1. …'.",
                )
            )

    max_emu = Inches(profile.figures.max_width_in)
    oversize = sum(1 for shape in doc.inline_shapes if shape.width and shape.width > max_emu)
    if oversize:
        issues.append(
            Issue(
                id="fig-oversize",
                severity=Severity.WARNING,
                category=IssueCategory.LAYOUT,
                message=f"{oversize} figure(s) are wider than the single-column width.",
                suggested_action="Resize the image or use a full-width figure block.",
            )
        )

    return issues
