"""Rebuild the leading title/author/affiliation/abstract/keywords block.

This is the only place the engine regenerates content, and only from metadata
the user has had a chance to review. Any leading paragraph whose text is *not*
represented in that metadata is preserved verbatim, never dropped.
"""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

from app.domain.elements import Block, ElementType
from app.domain.manuscript import Metadata
from app.formatting.styles import (
    STYLE_ABSTRACT,
    STYLE_AFFILIATION,
    STYLE_AUTHOR,
    STYLE_BODY,
    STYLE_KEYWORDS,
    STYLE_TITLE,
    heading_style_name,
)
from app.parsing.ooxml import iter_block_items
from app.profiles.base import PublisherProfile

_FM_KINDS = {
    ElementType.TITLE,
    ElementType.AUTHOR,
    ElementType.AFFILIATION,
    ElementType.ABSTRACT,
    ElementType.KEYWORDS,
}
_STOP_KINDS = {ElementType.HEADING, ElementType.SUBHEADING}
_MAX_FM = 20


def frontmatter_end(body: list[Block]) -> int:
    """Index of the first block that is *not* front matter.

    Front matter is everything before the first section heading (or, absent
    headings, before the first reference item; or a short leading run of
    metadata-kind blocks). Stable across the format transform, which is what
    lets the preservation check rely on it.
    """
    for i, b in enumerate(body):
        if b.kind in _STOP_KINDS:
            return min(i, _MAX_FM)
    for i, b in enumerate(body):
        if b.kind == ElementType.REFERENCE_ITEM:
            return min(i, _MAX_FM)
    end = 0
    for b in body:
        if b.kind in _FM_KINDS:
            end += 1
        else:
            break
    return min(end, _MAX_FM)


def rebuild_frontmatter(doc, manuscript, profile: PublisherProfile) -> list[str]:
    body = manuscript.body
    end = frontmatter_end(body)
    if end == 0:
        return []

    items = list(iter_block_items(doc))
    existing = [it for it in items[:end] if isinstance(it, Paragraph)]
    if not existing:
        return []

    md = manuscript.metadata
    desired: list[_Spec] = []
    changes: list[str] = []

    if md.title.value:
        desired.append(_Spec(_cased(md.title.value, profile.title.case), STYLE_TITLE))
        changes.append("Rebuilt the title block")

    if md.authors.value:
        names = ", ".join(a.name for a in md.authors.value)
        desired.append(_Spec(names, STYLE_AUTHOR))
        changes.append("Normalised the author block")

    for aff in md.affiliations:
        desired.append(_Spec(aff.text, STYLE_AFFILIATION))
    if md.affiliations:
        changes.append("Normalised affiliations")

    if md.abstract.value:
        if profile.abstract.inline_lead_in:
            desired.append(
                _Spec(
                    None,
                    STYLE_ABSTRACT,
                    runs=[
                        ("Abstract—", {"bold": profile.abstract.bold_label}),
                        (md.abstract.value, {"italic": profile.abstract.italic_body}),
                    ],
                )
            )
        else:
            desired.append(_Spec(profile.abstract.heading_text, heading_style_name(1)))
            desired.append(_Spec(md.abstract.value, STYLE_ABSTRACT))
        changes.append("Reformatted the abstract")

    if md.keywords.value:
        kw = profile.keywords.separator.join(md.keywords.value)
        desired.append(
            _Spec(
                None,
                STYLE_KEYWORDS,
                runs=[
                    (f"{profile.keywords.label}—", {"italic": True}),
                    (kw, {"italic": profile.keywords.italic}),
                ],
            )
        )
        changes.append("Standardised keywords")

    preserved = [p.text for p in existing if p.text.strip() and not _is_captured(p.text, md)]
    for text in preserved:
        desired.append(_Spec(text, STYLE_BODY))
    if preserved:
        changes.append(f"Kept {len(preserved)} unrecognised front-matter line(s) as body text")

    if not desired:
        return []

    _write_sequence(doc, existing, desired)
    return changes


class _Spec:
    def __init__(self, text: str | None, style: str, runs: list[tuple[str, dict]] | None = None):
        self.text = text
        self.style = style
        self.runs = runs


def _write_sequence(doc, existing: list[Paragraph], desired: list[_Spec]) -> None:
    used: list[Paragraph] = []
    for i, spec in enumerate(desired):
        para = existing[i] if i < len(existing) else _insert_after(used[-1])
        _rewrite(doc, para, spec)
        used.append(para)
    for para in existing[len(desired) :]:
        _delete(para)


def _rewrite(doc, para: Paragraph, spec: _Spec) -> None:
    for run in list(para.runs):
        run._element.getparent().remove(run._element)
    try:
        para.style = doc.styles[spec.style]
    except KeyError:
        pass
    if spec.runs:
        for text, opts in spec.runs:
            run = para.add_run(text)
            if opts.get("bold"):
                run.bold = True
            if opts.get("italic"):
                run.italic = True
    elif spec.text is not None:
        para.add_run(spec.text)


def _insert_after(paragraph: Paragraph) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    return Paragraph(new_p, paragraph._parent)


def _delete(paragraph: Paragraph) -> None:
    paragraph._p.getparent().remove(paragraph._p)


def _norm(s: str) -> str:
    return " ".join((s or "").split()).lower()


def _is_captured(text: str, md: Metadata) -> bool:
    n = _norm(text)
    if not n:
        return True
    if md.title.value and (n in _norm(md.title.value) or _norm(md.title.value) in n):
        return True
    for a in md.authors.value:
        if _norm(a.name) and (_norm(a.name) in n or n in _norm(a.name)):
            return True
        if a.email and a.email.lower() in n:
            return True
    if md.abstract.value and (n in _norm(md.abstract.value) or _norm(md.abstract.value) in n):
        return True
    if any(_norm(a.text) == n for a in md.affiliations):
        return True
    if md.keywords.value and any(_norm(k) and _norm(k) in n for k in md.keywords.value):
        return len(n) < 120
    return False


def _cased(text: str, mode: str) -> str:
    if mode == "upper":
        return text.upper()
    if mode == "sentence" and text:
        return text[:1].upper() + text[1:]
    return text
