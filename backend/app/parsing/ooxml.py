"""Raw-XML helpers for things python-docx does not surface directly."""

from __future__ import annotations

from collections.abc import Iterator

from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(document) -> Iterator[Paragraph | Table]:
    """Yield paragraphs and tables in true document order (they interleave in the body)."""
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def count_images(paragraph: Paragraph) -> int:
    el = paragraph._p
    blips = el.findall(".//" + qn("a:blip"))
    if blips:
        return len(blips)
    picts = el.findall(".//" + qn("w:pict"))
    drawings = el.findall(".//" + qn("w:drawing"))
    return len(picts) + len(drawings)


def has_equation(paragraph: Paragraph) -> bool:
    el = paragraph._p
    return bool(el.findall(".//" + qn("m:oMath")) or el.findall(".//" + qn("m:oMathPara")))


def page_break_before(paragraph: Paragraph) -> bool:
    if paragraph.paragraph_format.page_break_before:
        return True
    for br in paragraph._p.findall(".//" + qn("w:br")):
        if br.get(qn("w:type")) == "page":
            return True
    return False


def outline_level_val(paragraph: Paragraph) -> int | None:
    pPr = paragraph._p.pPr
    if pPr is None:
        return None
    lvl = pPr.find(qn("w:outlineLvl"))
    if lvl is None:
        return None
    val = lvl.get(qn("w:val"))
    return int(val) if val is not None and val.lstrip("-").isdigit() else None


def has_numPr(paragraph: Paragraph) -> bool:
    pPr = paragraph._p.pPr
    return pPr is not None and pPr.find(qn("w:numPr")) is not None
