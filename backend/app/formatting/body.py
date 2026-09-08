"""Restyle body elements (headings, paragraphs, lists, captions, references).

Paragraph styles do the work; run-level font family/size overrides are cleared
so the style actually takes effect, but bold/italic emphasis inside sentences
is left alone. Text is never edited except an optional heading case change.
"""

from __future__ import annotations

from docx.shared import Pt
from docx.table import Table

from app.domain.elements import ElementType
from app.formatting.frontmatter import frontmatter_end
from app.formatting.styles import STYLE_BODY, STYLE_CAPTION, STYLE_REFERENCE, heading_style_name
from app.parsing.ooxml import iter_block_items
from app.profiles.base import PublisherProfile

_HEADING_KINDS = {ElementType.HEADING, ElementType.SUBHEADING}
_BODY_LIKE = {
    ElementType.PARAGRAPH,
    ElementType.ACKNOWLEDGEMENT,
    ElementType.APPENDIX,
    ElementType.NUMBERED_LIST_ITEM,
    ElementType.BULLET_LIST_ITEM,
}


def restyle_body(doc, manuscript, profile: PublisherProfile) -> list[str]:
    body = manuscript.body
    start = frontmatter_end(body)
    items = list(iter_block_items(doc))

    counts = {"headings": 0, "paragraphs": 0, "captions": 0, "references": 0}

    for i in range(start, min(len(body), len(items))):
        block = body[i]
        item = items[i]
        if isinstance(item, Table):
            continue
        para = item

        if block.kind in _HEADING_KINDS:
            _set_style(doc, para, heading_style_name(block.level or 1))
            _apply_case(para, profile.headings.levels.get(block.level or 1))
            counts["headings"] += 1
        elif block.kind == ElementType.CAPTION:
            _set_style(doc, para, STYLE_CAPTION)
            _clear_run_overrides(para, profile.captions.figure.size_pt, profile.base_font.family)
            counts["captions"] += 1
        elif block.kind == ElementType.REFERENCE_ITEM:
            _set_style(doc, para, STYLE_REFERENCE)
            _clear_run_overrides(para, profile.references.size_pt, profile.base_font.family)
            counts["references"] += 1
        elif block.kind in _BODY_LIKE:
            _set_style(doc, para, STYLE_BODY)
            _clear_run_overrides(para, profile.base_font.size_pt, profile.base_font.family)
            counts["paragraphs"] += 1
        # EQUATION / FIGURE / stray TABLE-kind: left untouched

    changes = []
    if counts["headings"]:
        changes.append(f"Standardised heading hierarchy ({counts['headings']} headings)")
    if counts["paragraphs"]:
        changes.append(f"Applied body typography to {counts['paragraphs']} paragraphs")
    if counts["captions"]:
        changes.append(f"Updated {counts['captions']} figure/table captions")
    if counts["references"]:
        changes.append(f"Reformatted {counts['references']} references")
    return changes


def _set_style(doc, para, style_name: str) -> None:
    try:
        para.style = doc.styles[style_name]
    except KeyError:
        pass


def _clear_run_overrides(para, size_pt: float, family: str) -> None:
    for run in para.runs:
        run.font.name = family
        if run.font.size is not None:
            run.font.size = Pt(size_pt)


def _apply_case(para, rule) -> None:
    if rule is None or rule.case != "upper":
        return
    for run in para.runs:
        if run.text:
            run.text = run.text.upper()
