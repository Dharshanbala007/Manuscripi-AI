"""Citation <-> reference-list consistency. Reports only; never fabricates entries."""

from __future__ import annotations

import re

from app.domain.elements import ElementType
from app.domain.issues import Issue, IssueCategory, Severity
from app.domain.manuscript import Manuscript

_CITE_RE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
_RANGE_RE = re.compile(r"(\d+)\s*[–-]\s*(\d+)$")


def _expand(group: str) -> list[int]:
    out: list[int] = []
    for part in re.split(r"\s*,\s*", group):
        rng = _RANGE_RE.match(part)
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            out.extend(range(a, b + 1) if a <= b else [a])
        elif part.isdigit():
            out.append(int(part))
    return out


def check_references(manuscript: Manuscript) -> list[Issue]:
    issues: list[Issue] = []

    cited: set[int] = set()
    for b in manuscript.body:
        if b.kind == ElementType.REFERENCE_ITEM:
            continue
        for m in _CITE_RE.finditer(b.text or ""):
            cited.update(_expand(m.group(1)))

    listed: list[int] = []
    seen: set[int] = set()
    for b in manuscript.body:
        if b.kind != ElementType.REFERENCE_ITEM:
            continue
        if b.number is None:
            issues.append(
                Issue(
                    id=f"ref-{b.id}-nonum",
                    severity=Severity.WARNING,
                    category=IssueCategory.REFERENCES,
                    message="A reference item has no detectable number.",
                    location=b.id,
                    suggested_action="Check the reference list numbering.",
                )
            )
            continue
        if b.number in seen:
            issues.append(
                Issue(
                    id=f"ref-dup-{b.number}",
                    severity=Severity.WARNING,
                    category=IssueCategory.REFERENCES,
                    message=f"Reference [{b.number}] appears more than once.",
                    location=b.id,
                    suggested_action="Remove the duplicate reference entry.",
                )
            )
        seen.add(b.number)
        listed.append(b.number)

    listed_set = set(listed)
    for c in sorted(cited - listed_set):
        issues.append(
            Issue(
                id=f"cite-missing-{c}",
                severity=Severity.ERROR,
                category=IssueCategory.REFERENCES,
                message=f"Citation [{c}] has no matching entry in the reference list.",
                suggested_action="Add the missing reference, or correct the citation number.",
            )
        )
    for r in sorted(listed_set - cited):
        issues.append(
            Issue(
                id=f"ref-uncited-{r}",
                severity=Severity.INFO,
                category=IssueCategory.REFERENCES,
                message=f"Reference [{r}] is listed but never cited in the text.",
                suggested_action="Cite the reference where relevant, or remove it.",
            )
        )

    if listed:
        gaps = sorted(set(range(1, max(listed) + 1)) - listed_set)
        if gaps:
            pretty = ", ".join(f"[{g}]" for g in gaps)
            issues.append(
                Issue(
                    id="ref-gaps",
                    severity=Severity.WARNING,
                    category=IssueCategory.REFERENCES,
                    message=f"Reference numbering has gaps: missing {pretty}.",
                    suggested_action="Renumber the reference list consecutively.",
                )
            )

    return issues
