"""In-memory DOCX/ZIP builders for tests. Keeps fixtures small and explicit."""

from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Pt

# 1x1 transparent PNG — enough for python-docx to embed a picture.
_PNG_1x1 = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def minimal_docx_bytes(text: str = "Hello world") -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    return _to_bytes(doc)


def docx_bytes_from(build) -> bytes:
    """`build(doc)` receives a python-docx Document to populate; returns the bytes."""
    doc = Document()
    build(doc)
    return _to_bytes(doc)


def docx_with(
    *,
    title: str | None = None,
    headings: list[tuple[str, int]] | None = None,
    paragraphs: list[str] | None = None,
    styled_paragraph: tuple[str, dict] | None = None,
    table: tuple[int, int] | None = None,
    image: bool = False,
) -> bytes:
    doc = Document()
    if title:
        doc.add_heading(title, level=0)
    for text, level in headings or []:
        doc.add_heading(text, level=level)
    for text in paragraphs or []:
        doc.add_paragraph(text)
    if styled_paragraph:
        text, opts = styled_paragraph
        run = doc.add_paragraph().add_run(text)
        if opts.get("bold"):
            run.bold = True
        if opts.get("italic"):
            run.italic = True
        if opts.get("size"):
            run.font.size = Pt(opts["size"])
        if opts.get("font"):
            run.font.name = opts["font"]
    if table:
        rows, cols = table
        t = doc.add_table(rows=rows, cols=cols)
        for r in range(rows):
            for c in range(cols):
                t.cell(r, c).text = f"r{r}c{c}"
    if image:
        doc.add_picture(io.BytesIO(_PNG_1x1))
    return _to_bytes(doc)


def docx_with_equation(lead: str = "See equation:") -> bytes:
    doc = Document()
    para = doc.add_paragraph(lead)
    para._p.append(parse_xml(f"<m:oMath {nsdecls('m')}><m:r><m:t>x^2</m:t></m:r></m:oMath>"))
    return _to_bytes(doc)


def write_docx(tmp_path: Path, data: bytes, name: str = "in.docx") -> Path:
    path = Path(tmp_path) / name
    path.write_bytes(data)
    return path


def academic_docx(
    *,
    title: str = "A Rule-Based Approach to Manuscript Formatting",
    authors: str = "Ada Lovelace, Alan Turing and Grace Hopper",
    n_refs: int = 6,
    with_table: bool = True,
    with_figure: bool = True,
    messy: bool = False,
) -> bytes:
    """A small but realistic manuscript for pipeline/integration tests.

    `messy=True` drops the "Abstract" heading and the figure caption, and adds
    one reference that the body never cites.
    """
    doc = Document()

    heading = doc.add_paragraph()
    run = heading.add_run(title)
    run.bold = True
    run.font.size = Pt(20)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(authors)
    doc.add_paragraph("Department of Computing, University of Somewhere")
    doc.add_paragraph("ada@uni.edu")

    if not messy:
        doc.add_heading("Abstract", level=1)
    doc.add_paragraph(
        "This paper presents a rule based system for detecting and normalising the "
        "structure of academic manuscripts, evaluated across several datasets with "
        "strong results."
    )
    doc.add_paragraph("Index Terms— formatting, parsing, classification, IEEE")

    doc.add_heading("1. Introduction", level=1)
    doc.add_paragraph(
        "Academic manuscripts follow broadly shared conventions [1]. Prior tools [2] "
        "focus mainly on citation styles."
    )
    doc.add_heading("2. Related Work", level=1)
    doc.add_paragraph(
        "Earlier systems [3] handled layout only. Our approach also classifies elements [4]."
    )
    doc.add_heading("3. Methodology", level=1)
    doc.add_paragraph("We parse the document into an ordered stream and apply heuristics.")
    if with_table:
        table = doc.add_table(rows=2, cols=3)
        for c in range(3):
            table.cell(0, c).text = f"Header {c}"
            table.cell(1, c).text = f"value {c}"
        doc.add_paragraph("Table 1. Summary of configuration options.")
    doc.add_heading("4. Results", level=1)
    doc.add_paragraph("The system preserved content in all trials [5].")
    if with_figure:
        doc.add_picture(io.BytesIO(_PNG_1x1))
        if not messy:
            doc.add_paragraph("Figure 1. Overview of the processing pipeline.")
    doc.add_heading("5. Conclusion", level=1)
    doc.add_paragraph("Rule-based processing is sufficient for reliable formatting [6].")

    doc.add_heading("References", level=1)
    for i in range(1, n_refs + 1):
        doc.add_paragraph(f"[{i}] Author {i}, A relevant work number {i}, 20{10 + i}.")
    if messy:
        doc.add_paragraph(f"[{n_refs + 1}] Uncited Author, Never referenced in the body, 2099.")

    return _to_bytes(doc)


def zip_bytes(entries: dict[str, bytes] | None = None, *, include_required: bool = True) -> bytes:
    entries = dict(entries or {})
    if include_required:
        entries.setdefault("[Content_Types].xml", b"<?xml version='1.0'?><Types/>")
        entries.setdefault("word/document.xml", b"<?xml version='1.0'?><document/>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
