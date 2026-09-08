"""Define the named paragraph styles a profile needs. Styles-first formatting."""

from __future__ import annotations

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from app.profiles.base import PublisherProfile

STYLE_BODY = "MS Body"
STYLE_TITLE = "MS Title"
STYLE_AUTHOR = "MS Author"
STYLE_AFFILIATION = "MS Affiliation"
STYLE_ABSTRACT = "MS Abstract"
STYLE_KEYWORDS = "MS Keywords"
STYLE_CAPTION = "MS Caption"
STYLE_REFERENCE = "MS Reference"


def heading_style_name(level: int) -> str:
    return f"MS Heading {max(1, min(level, 3))}"


_ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def ensure_styles(doc, profile: PublisherProfile) -> None:
    """Create or update every MS-* paragraph style. Idempotent."""
    bf = profile.base_font

    _apply(
        _get_or_add(doc, STYLE_BODY),
        family=bf.family,
        size_pt=bf.size_pt,
        align=profile.paragraphs.align,
        line=profile.spacing.line,
        first_indent_in=profile.paragraphs.first_line_indent_in,
        space_before_pt=profile.spacing.paragraph_before_pt,
        space_after_pt=profile.spacing.paragraph_after_pt,
    )

    t = profile.title
    _apply(
        _get_or_add(doc, STYLE_TITLE),
        family=t.font_family or bf.family,
        size_pt=t.size_pt,
        bold=t.bold,
        italic=t.italic,
        align=t.align,
    )

    _apply(
        _get_or_add(doc, STYLE_AUTHOR),
        family=bf.family,
        size_pt=profile.author.size_pt,
        italic=profile.author.italic,
        align=profile.author.align,
    )
    _apply(
        _get_or_add(doc, STYLE_AFFILIATION),
        family=bf.family,
        size_pt=profile.affiliation.size_pt,
        italic=profile.affiliation.italic,
        align=profile.affiliation.align,
    )
    _apply(
        _get_or_add(doc, STYLE_ABSTRACT),
        family=bf.family,
        size_pt=profile.abstract.size_pt,
        italic=profile.abstract.italic_body,
        align=profile.abstract.align,
    )
    _apply(
        _get_or_add(doc, STYLE_KEYWORDS),
        family=bf.family,
        size_pt=profile.keywords.size_pt,
        italic=profile.keywords.italic,
        align="left",
    )

    for level, rule in profile.headings.levels.items():
        _apply(
            _get_or_add(doc, heading_style_name(level)),
            family=bf.family,
            size_pt=rule.size_pt,
            bold=rule.bold,
            italic=rule.italic,
            align=rule.align,
            space_before_pt=rule.space_before_pt,
            space_after_pt=rule.space_after_pt,
        )

    fig_cap = profile.captions.figure
    _apply(
        _get_or_add(doc, STYLE_CAPTION),
        family=bf.family,
        size_pt=fig_cap.size_pt,
        italic=fig_cap.italic,
        align=fig_cap.align,
    )

    ref = profile.references
    _apply(
        _get_or_add(doc, STYLE_REFERENCE),
        family=bf.family,
        size_pt=ref.size_pt,
        hanging_in=ref.hanging_indent_in,
    )


def _get_or_add(doc, name: str):
    styles = doc.styles
    try:
        return styles[name]
    except KeyError:
        style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        try:
            style.base_style = styles["Normal"]
        except KeyError:
            pass
        return style


def _apply(
    style,
    *,
    family: str | None = None,
    size_pt: float | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    align: str | None = None,
    space_before_pt: float | None = None,
    space_after_pt: float | None = None,
    line: float | None = None,
    first_indent_in: float | None = None,
    hanging_in: float | None = None,
) -> None:
    font = style.font
    if family:
        font.name = family
    if size_pt is not None:
        font.size = Pt(size_pt)
    if bold is not None:
        font.bold = bold
    if italic is not None:
        font.italic = italic

    pf = style.paragraph_format
    if align is not None:
        pf.alignment = _ALIGN.get(align, WD_ALIGN_PARAGRAPH.LEFT)
    if space_before_pt is not None:
        pf.space_before = Pt(space_before_pt)
    if space_after_pt is not None:
        pf.space_after = Pt(space_after_pt)
    if line is not None:
        pf.line_spacing = line
    if first_indent_in is not None:
        pf.first_line_indent = Inches(first_indent_in)
    if hanging_in is not None:
        pf.left_indent = Inches(hanging_in)
        pf.first_line_indent = Inches(-hanging_in)
