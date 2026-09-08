from docx import Document
from docx.oxml.ns import qn

from app.formatting.engine import format_document
from app.profiles.loader import load_profile
from app.validation.preservation import check_preservation
from tests.fixtures.gen import academic_docx, manuscript_from, write_docx

PROFILE = load_profile("springer")


def _format(tmp_path, *, messy: bool):
    src = write_docx(tmp_path, academic_docx(messy=messy), "source.docx")
    ms = manuscript_from(src)
    out = tmp_path / "formatted.docx"
    format_document(ms, src, out, PROFILE)
    return ms, out


def test_springer_output_is_single_column_and_preserves_content(tmp_path):
    ms, out = _format(tmp_path, messy=False)

    cols = Document(str(out)).sections[0]._sectPr.find(qn("w:cols"))
    assert cols is not None
    assert cols.get(qn("w:num")) == "1"

    result = check_preservation(ms, out)
    assert result.passed, result.details


def test_springer_preserves_messy_manuscript(tmp_path):
    ms, out = _format(tmp_path, messy=True)
    assert check_preservation(ms, out).passed
