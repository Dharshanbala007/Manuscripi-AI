"""validate(): run every category of check against the formatted output."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from app.classification.classifier import classify_blocks
from app.domain.elements import ElementType
from app.domain.issues import Issue, IssueCategory, Severity
from app.domain.manuscript import Manuscript
from app.extraction.metadata import extract_metadata
from app.parsing.docx_reader import DocxReadError, parse_docx
from app.profiles.base import PublisherProfile
from app.utils.text import shorten
from app.validation.preservation import check_preservation
from app.validation.references import check_references

_CITE_RE = re.compile(r"\[\d+\]")
_HEADING_KINDS = {ElementType.HEADING, ElementType.SUBHEADING}
_CONTENTFUL_KINDS = {ElementType.TABLE, ElementType.FIGURE, ElementType.EQUATION}


def validate(
    original: Manuscript, formatted_path: Path | str, profile: PublisherProfile
) -> list[Issue]:
    issues: list[Issue] = []

    try:
        parsed = parse_docx(formatted_path)
    except DocxReadError:
        return [
            Issue(
                id="doc-unreadable",
                severity=Severity.ERROR,
                category=IssueCategory.DOCUMENT,
                message="The formatted document could not be opened.",
                suggested_action="Re-run formatting.",
            )
        ]

    fmt_md = extract_metadata(parsed.blocks, 0.6)
    fmt_blocks = classify_blocks(parsed.blocks, fmt_md, 0.6)

    issues += _check_structure(original, fmt_blocks, profile)
    issues += _check_formatting(formatted_path, profile)
    issues += _check_empty_sections(fmt_blocks)
    issues += check_references(original)

    preservation = check_preservation(original, formatted_path)
    if not preservation.passed:
        issues.append(
            Issue(
                id="val-preservation",
                severity=Severity.ERROR,
                category=IssueCategory.CONTENT,
                message="Formatted content differs from the original manuscript.",
                suggested_action="Review the What Changed panel before exporting.",
            )
        )

    return issues


def _check_structure(original: Manuscript, fmt_blocks, profile: PublisherProfile) -> list[Issue]:
    issues: list[Issue] = []
    md = original.metadata

    if not md.title.value:
        issues.append(
            _i(
                "val-no-title",
                Severity.ERROR,
                IssueCategory.STRUCTURE,
                "The manuscript has no title.",
                "Add a title in the metadata panel.",
            )
        )
    if not md.authors.value:
        issues.append(
            _i(
                "val-no-authors",
                Severity.ERROR,
                IssueCategory.STRUCTURE,
                "The manuscript has no authors.",
                "Add authors in the metadata panel.",
            )
        )
    if profile.validation.require_abstract and not md.abstract.value:
        issues.append(
            _i(
                "val-no-abstract",
                Severity.WARNING,
                IssueCategory.STRUCTURE,
                "No abstract was found.",
                "Add an abstract in the metadata panel.",
            )
        )
    if profile.validation.require_keywords and not md.keywords.value:
        issues.append(
            _i(
                "val-no-keywords",
                Severity.WARNING,
                IssueCategory.STRUCTURE,
                "No keywords were found.",
                "Add keywords in the metadata panel.",
            )
        )

    has_citations = any(
        _CITE_RE.search(b.text or "") for b in original.body if b.kind != ElementType.REFERENCE_ITEM
    )
    has_refs = any(b.kind == ElementType.REFERENCE_ITEM for b in original.body) or any(
        b.kind == ElementType.REFERENCE_ITEM for b in fmt_blocks
    )
    if has_citations and not has_refs:
        issues.append(
            _i(
                "val-no-refs",
                Severity.ERROR,
                IssueCategory.STRUCTURE,
                "The text has bracketed citations but no reference list.",
                "Add a References section.",
            )
        )
    return issues


def _check_formatting(path: Path | str, profile: PublisherProfile) -> list[Issue]:
    issues: list[Issue] = []
    doc = Document(str(path))
    section = doc.sections[0]

    if abs(section.left_margin.inches - profile.page.margin_left_in) > 0.05:
        issues.append(
            _i(
                "fmt-margins",
                Severity.WARNING,
                IssueCategory.FORMATTING,
                "Page margins do not match the selected profile.",
                "Re-apply formatting.",
            )
        )

    cols = section._sectPr.find(qn("w:cols"))
    if cols is None or cols.get(qn("w:num")) != str(profile.columns.count):
        issues.append(
            _i(
                "fmt-columns",
                Severity.WARNING,
                IssueCategory.FORMATTING,
                f"Column layout is not {profile.columns.count}-column.",
                "Re-apply formatting.",
            )
        )

    try:
        body_style = doc.styles["MS Body"]
        if body_style.font.name != profile.base_font.family:
            issues.append(
                _i(
                    "fmt-font",
                    Severity.INFO,
                    IssueCategory.FORMATTING,
                    "Body font does not match the profile.",
                    "Re-apply formatting.",
                )
            )
    except KeyError:
        issues.append(
            _i(
                "fmt-nostyle",
                Severity.WARNING,
                IssueCategory.FORMATTING,
                "Expected paragraph styles are missing from the output.",
                "Re-apply formatting.",
            )
        )
    return issues


def _check_empty_sections(blocks) -> list[Issue]:
    issues: list[Issue] = []
    for i, b in enumerate(blocks):
        if b.kind not in _HEADING_KINDS:
            continue
        has_content = False
        for nb in blocks[i + 1 :]:
            if nb.kind in _HEADING_KINDS:
                break
            if (nb.text or "").strip() or nb.kind in _CONTENTFUL_KINDS:
                has_content = True
                break
        if not has_content:
            issues.append(
                Issue(
                    id=f"empty-{b.id}",
                    severity=Severity.INFO,
                    category=IssueCategory.CONTENT,
                    message=f"Section “{shorten(b.text, 40)}” appears to have no content.",
                    location=b.id,
                    suggested_action="Add content, or remove the empty heading.",
                )
            )
    return issues


def _i(id_: str, severity: Severity, category: IssueCategory, message: str, action: str) -> Issue:
    return Issue(
        id=id_, severity=severity, category=category, message=message, suggested_action=action
    )
