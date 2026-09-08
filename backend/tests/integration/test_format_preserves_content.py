from app.classification.classifier import classify_blocks
from app.domain.elements import ElementType
from app.extraction.metadata import extract_metadata
from app.formatting.engine import format_document
from app.formatting.frontmatter import frontmatter_end
from app.parsing.docx_reader import parse_docx
from app.profiles.loader import load_profile
from app.utils.text import normalize_ws, text_hash
from tests.fixtures.gen import academic_docx, manuscript_from, write_docx

PROFILE = load_profile("ieee")


def _body_after_frontmatter(blocks) -> str:
    start = frontmatter_end(blocks)
    return normalize_ws(" ".join(b.text for b in blocks[start:]))


def _reclassify(path):
    parsed = parse_docx(path)
    md = extract_metadata(parsed.blocks, 0.6)
    return parsed, classify_blocks(parsed.blocks, md, 0.6)


def _run(tmp_path, *, messy: bool):
    src = write_docx(tmp_path, academic_docx(messy=messy), "source.docx")
    ms = manuscript_from(src)
    out = tmp_path / "formatted.docx"
    result = format_document(ms, src, out, PROFILE)
    assert out.exists()

    reparsed, re_blocks = _reclassify(out)

    before = _body_after_frontmatter(ms.body)
    after = _body_after_frontmatter(re_blocks)
    assert text_hash(before) == text_hash(after), (
        f"body text changed\nBEFORE: {before[:200]}\nAFTER : {after[:200]}"
    )

    tables_before = sum(1 for b in ms.body if b.kind == ElementType.TABLE)
    tables_after = sum(1 for b in reparsed.blocks if b.kind_hint == "table")
    assert tables_after == tables_before

    images_after = sum(b.image_count for b in reparsed.blocks)
    assert images_after >= 1

    assert result.change_log.formatting_changes
    return result


def test_formatting_preserves_body_on_clean_manuscript(tmp_path):
    _run(tmp_path, messy=False)


def test_formatting_preserves_body_on_messy_manuscript(tmp_path):
    _run(tmp_path, messy=True)


def test_source_file_is_not_modified(tmp_path):
    src = write_docx(tmp_path, academic_docx(), "source.docx")
    before = src.read_bytes()
    ms = manuscript_from(src)
    format_document(ms, src, tmp_path / "formatted.docx", PROFILE)
    assert src.read_bytes() == before
