from app.domain.issues import IssueCategory
from app.formatting.engine import format_document
from app.profiles.loader import load_profile
from app.validation.health import score
from app.validation.validators import validate
from tests.fixtures.gen import academic_docx, manuscript_from, write_docx

PROFILE = load_profile("ieee")


def _format(tmp_path, *, messy: bool):
    src = write_docx(tmp_path, academic_docx(messy=messy), "source.docx")
    ms = manuscript_from(src)
    out = tmp_path / "formatted.docx"
    format_document(ms, src, out, PROFILE)
    return ms, out


def test_validate_clean_manuscript_has_no_document_or_preservation_errors(tmp_path):
    ms, out = _format(tmp_path, messy=False)
    issues = validate(ms, out, PROFILE)

    assert not any(i.category == IssueCategory.DOCUMENT for i in issues)
    assert not any(i.id == "val-preservation" for i in issues)
    assert not any(i.id in ("fmt-columns", "fmt-margins", "fmt-nostyle") for i in issues)

    health = score(issues, ms)
    assert 0 <= health.total <= 100


def test_validate_messy_manuscript_flags_missing_abstract_and_uncited_ref(tmp_path):
    ms, out = _format(tmp_path, messy=True)
    issues = validate(ms, out, PROFILE)
    ids = {i.id for i in issues}

    assert "val-no-abstract" in ids
    assert any(i.id.startswith("ref-uncited-") for i in issues)

    health = score(issues, ms)
    assert health.total < 100
    assert health.contributors
