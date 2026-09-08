from docx import Document
from docx.text.paragraph import Paragraph

from app.formatting.engine import format_document
from app.parsing.ooxml import iter_block_items
from app.profiles.loader import load_profile
from app.validation.preservation import check_preservation
from tests.fixtures.gen import academic_docx, manuscript_from, write_docx

PROFILE = load_profile("ieee")


def test_preservation_passes_after_faithful_format(tmp_path):
    src = write_docx(tmp_path, academic_docx(), "source.docx")
    ms = manuscript_from(src)
    out = tmp_path / "formatted.docx"
    format_document(ms, src, out, PROFILE)

    result = check_preservation(ms, out)
    assert result.passed is True
    assert result.text_match is True
    assert result.details == []


def test_preservation_detects_a_dropped_body_paragraph(tmp_path):
    src = write_docx(tmp_path, academic_docx(), "source.docx")
    ms = manuscript_from(src)
    out = tmp_path / "formatted.docx"
    format_document(ms, src, out, PROFILE)

    doc = Document(str(out))
    paragraphs = [
        it for it in iter_block_items(doc) if isinstance(it, Paragraph) and it.text.strip()
    ]
    victim = paragraphs[-3]
    victim._p.getparent().remove(victim._p)
    doc.save(str(out))

    result = check_preservation(ms, out)
    assert result.passed is False
    assert result.text_match is False
    assert result.details
