"""Page geometry: size, margins, and column layout on every section."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches

from app.profiles.base import PublisherProfile

_PAGE_SIZES = {
    "letter": (Inches(8.5), Inches(11.0)),
    "a4": (Inches(8.27), Inches(11.69)),
}


def apply_page_layout(doc, profile: PublisherProfile) -> None:
    width, height = _PAGE_SIZES.get(profile.page.size, _PAGE_SIZES["letter"])
    for section in doc.sections:
        section.page_width = width
        section.page_height = height
        section.top_margin = Inches(profile.page.margin_top_in)
        section.bottom_margin = Inches(profile.page.margin_bottom_in)
        section.left_margin = Inches(profile.page.margin_left_in)
        section.right_margin = Inches(profile.page.margin_right_in)
        _set_columns(section, profile.columns.count, profile.columns.spacing_in)


def _set_columns(section, count: int, spacing_in: float) -> None:
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.append(cols)
    cols.set(qn("w:num"), str(max(1, count)))
    cols.set(qn("w:space"), str(int(Inches(spacing_in).twips)))
    cols.set(qn("w:equalWidth"), "1")
