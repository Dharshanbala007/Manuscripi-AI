"""In-memory DOCX/ZIP builders for tests. Keeps fixtures small and explicit."""

from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

from docx import Document
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
