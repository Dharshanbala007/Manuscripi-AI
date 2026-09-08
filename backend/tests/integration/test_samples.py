import pytest
from docx import Document

from app.domain.elements import ElementType
from app.domain.issues import Issue
from app.formatting.engine import format_document
from app.formatting.figures import check_figures
from app.profiles.loader import load_profile
from app.validation.preservation import check_preservation
from app.validation.references import check_references
from app.validation.validators import validate
from tests.fixtures.gen import manuscript_from

PROFILE = load_profile("ieee")


def test_sample_runs_full_pipeline_and_preserves_content(sample_docx, tmp_path):
    ms = manuscript_from(sample_docx)
    assert ms.body

    out = tmp_path / "formatted.docx"
    format_document(ms, sample_docx, out, PROFILE)
    assert out.exists()

    preservation = check_preservation(ms, out)
    assert preservation.passed, preservation.details

    issues = validate(ms, out, PROFILE)
    assert all(isinstance(i, Issue) for i in issues)
    assert not any(i.id == "val-preservation" for i in issues)


def test_complex_sample_has_expected_shape(sample_dir):
    path = sample_dir / "sample_complex.docx"
    if not path.exists():
        pytest.skip("run scripts/gen_samples.py")
    ms = manuscript_from(path)

    tables = sum(1 for b in ms.body if b.kind == ElementType.TABLE)
    figures = sum(1 for b in ms.body if b.kind == ElementType.FIGURE)
    references = sum(1 for b in ms.body if b.kind == ElementType.REFERENCE_ITEM)

    assert tables >= 3
    assert figures >= 4
    assert references >= 20


def test_messy_sample_has_uncited_reference_and_missing_caption(sample_dir):
    path = sample_dir / "sample_messy.docx"
    if not path.exists():
        pytest.skip("run scripts/gen_samples.py")
    ms = manuscript_from(path)

    assert any(i.id.startswith("ref-uncited-") for i in check_references(ms))

    fig_issues = check_figures(Document(str(path)), ms, PROFILE)
    assert any("caption" in i.message.lower() for i in fig_issues)
