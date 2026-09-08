"""parse_docx: a .docx file -> ordered ParsedDocument. Never mutates the source."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table

from app.domain.elements import SourceRef
from app.parsing.blocks import ParsedBlock, ParsedDocument, RunFormat
from app.parsing.ooxml import (
    count_images,
    has_equation,
    has_numPr,
    iter_block_items,
    outline_level_val,
    page_break_before,
)

_HEADING_RE = re.compile(r"heading\s+(\d+)", re.IGNORECASE)


class DocxReadError(Exception):
    """The document could not be opened at all."""


def parse_docx(path: Path | str) -> ParsedDocument:
    try:
        document = Document(str(path))
    except (PackageNotFoundError, KeyError, ValueError, OSError) as exc:
        raise DocxReadError("Unable to read this document. The file may be corrupted.") from exc

    blocks: list[ParsedBlock] = []
    warnings: list[str] = []

    for index, item in enumerate(iter_block_items(document)):
        try:
            if isinstance(item, Table):
                blocks.append(_parse_table(item, index))
            else:
                blocks.append(_parse_paragraph(item, index))
        except Exception as exc:  # noqa: BLE001
            # Deliberate: spec requires one unreadable element not to abort the
            # whole parse. Recorded as a warning and surfaced to the user.
            warnings.append(f"element {index}: {type(exc).__name__}")
            blocks.append(
                ParsedBlock(
                    kind_hint="paragraph",
                    text=_best_effort_text(item),
                    source_ref=SourceRef("document", index),
                )
            )

    return ParsedDocument(blocks=blocks, parse_warnings=warnings)


def _parse_paragraph(paragraph, index: int) -> ParsedBlock:
    text = paragraph.text or ""
    runs = _extract_runs(paragraph)
    images = count_images(paragraph)
    style_name = paragraph.style.name if paragraph.style is not None else None

    kind = "image" if images and not text.strip() else "paragraph"

    return ParsedBlock(
        kind_hint=kind,
        text=text,
        runs=runs,
        style_name=style_name,
        outline_level=_outline_level(paragraph, style_name),
        numbering=_numbering(paragraph, style_name),
        alignment=_alignment(paragraph),
        source_ref=SourceRef("document", index),
        has_equation=has_equation(paragraph),
        page_break_before=page_break_before(paragraph),
        image_count=images,
    )


def _parse_table(table: Table, index: int) -> ParsedBlock:
    rows = len(table.rows)
    try:
        cols = len(table.columns)
    except Exception:  # noqa: BLE001 - irregular grids; fall back to first row
        cols = len(table.rows[0].cells) if rows else 0

    lines = []
    for row in table.rows:
        cells = [" ".join(cell.text.split()) for cell in row.cells]
        lines.append(" | ".join(cells))

    return ParsedBlock(
        kind_hint="table",
        text="\n".join(lines),
        source_ref=SourceRef("document", index),
        table_shape=(rows, cols),
    )


def _tri(run_value: bool | None, style_value: bool | None) -> bool:
    if run_value is not None:
        return bool(run_value)
    if style_value is not None:
        return bool(style_value)
    return False


def _extract_runs(paragraph) -> list[RunFormat]:
    style_font = style_size = style_bold = style_italic = None
    style = paragraph.style
    if style is not None and style.font is not None:
        style_font = style.font.name
        style_size = style.font.size
        style_bold = style.font.bold
        style_italic = style.font.italic

    out: list[RunFormat] = []
    for run in paragraph.runs:
        size = run.font.size or style_size
        out.append(
            RunFormat(
                text=run.text,
                font=run.font.name or style_font,
                size_pt=round(size.pt, 2) if size is not None else None,
                bold=_tri(run.bold, style_bold),
                italic=_tri(run.italic, style_italic),
            )
        )
    return out


def _outline_level(paragraph, style_name: str | None) -> int | None:
    explicit = outline_level_val(paragraph)
    if explicit is not None:
        return max(explicit, 0)
    if style_name:
        match = _HEADING_RE.match(style_name.strip())
        if match:
            return int(match.group(1)) - 1
    return None


def _numbering(paragraph, style_name: str | None) -> str | None:
    low = (style_name or "").lower()
    if "list bullet" in low:
        return "bullet"
    if "list number" in low:
        return "number"
    return "list" if has_numPr(paragraph) else None


def _alignment(paragraph) -> str | None:
    align = paragraph.alignment
    if align is None and paragraph.style is not None:
        try:
            align = paragraph.style.paragraph_format.alignment
        except Exception:  # noqa: BLE001
            align = None
    if align is None:
        return None
    name = getattr(align, "name", str(align)).lower()
    if "justif" in name:
        return "justify"
    if name in ("left", "center", "right"):
        return name
    return name


def _best_effort_text(item) -> str:
    try:
        return item.text or ""
    except Exception:  # noqa: BLE001
        return ""
