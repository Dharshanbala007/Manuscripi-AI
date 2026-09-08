from unittest.mock import patch

import pytest

from app.parsing import docx_reader
from app.parsing.docx_reader import DocxReadError, parse_docx
from tests.fixtures.gen import docx_with, docx_with_equation, write_docx


def test_parses_blocks_in_document_order(tmp_path):
    data = docx_with(
        headings=[("Introduction", 1)],
        paragraphs=["First paragraph.", "Second paragraph."],
        table=(2, 2),
        image=True,
    )
    doc = parse_docx(write_docx(tmp_path, data))

    assert [b.kind_hint for b in doc.blocks] == [
        "paragraph",
        "paragraph",
        "paragraph",
        "table",
        "image",
    ]
    assert doc.blocks[0].style_name.startswith("Heading")
    assert doc.blocks[0].outline_level == 0
    assert doc.blocks[3].table_shape == (2, 2)
    assert "r0c0" in doc.blocks[3].text
    assert doc.blocks[4].image_count >= 1
    assert [b.source_ref.index for b in doc.blocks] == [0, 1, 2, 3, 4]


def test_captures_run_formatting(tmp_path):
    data = docx_with(
        styled_paragraph=("Bold bit", {"bold": True, "size": 14, "font": "Arial"}),
    )
    doc = parse_docx(write_docx(tmp_path, data))
    run = doc.blocks[0].runs[0]
    assert run.bold is True
    assert run.size_pt == 14.0
    assert run.font == "Arial"
    assert doc.blocks[0].all_bold is True
    assert doc.blocks[0].max_size_pt == 14.0


def test_detects_equation_and_preserves_lead_text(tmp_path):
    doc = parse_docx(write_docx(tmp_path, docx_with_equation("Given:")))
    assert any(b.has_equation for b in doc.blocks)
    assert doc.blocks[0].text.startswith("Given:")


def test_bad_element_is_warned_not_fatal(tmp_path):
    data = docx_with(paragraphs=["ok one", "ok two"])
    real = docx_reader._extract_runs
    state = {"n": 0}

    def flaky(paragraph):
        state["n"] += 1
        if state["n"] == 1:
            raise ValueError("boom")
        return real(paragraph)

    with patch.object(docx_reader, "_extract_runs", flaky):
        doc = parse_docx(write_docx(tmp_path, data))

    assert len(doc.blocks) == 2
    assert doc.parse_warnings
    assert "element 0" in doc.parse_warnings[0]


def test_unreadable_file_raises(tmp_path):
    path = write_docx(tmp_path, b"definitely not a zip")
    with pytest.raises(DocxReadError):
        parse_docx(path)
