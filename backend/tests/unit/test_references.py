from app.domain.elements import Block, ElementType, SourceRef
from app.domain.manuscript import Manuscript, Metadata
from app.validation.references import check_references


def _ms(blocks):
    return Manuscript(id="d", source_filename="p.docx", metadata=Metadata.empty(), body=blocks)


def _para(bid, text):
    return Block(id=bid, kind=ElementType.PARAGRAPH, text=text, source_ref=SourceRef("document", 0))


def _ref(bid, number):
    return Block(
        id=bid,
        kind=ElementType.REFERENCE_ITEM,
        text=f"[{number}] Some Author, A work, 2020.",
        number=number,
        source_ref=SourceRef("document", 0),
    )


def test_citation_without_reference_is_an_error():
    ms = _ms([_para("b0", "As shown in [1], [2] and [5]."), _ref("b1", 1), _ref("b2", 2)])
    issues = check_references(ms)
    assert any(i.id == "cite-missing-5" and i.severity == "error" for i in issues)


def test_uncited_reference_is_info():
    ms = _ms([_para("b0", "Only [1] is cited."), _ref("b1", 1), _ref("b2", 2), _ref("b3", 3)])
    ids = {i.id for i in check_references(ms)}
    assert "ref-uncited-2" in ids
    assert "ref-uncited-3" in ids


def test_duplicate_reference_flagged():
    ms = _ms([_para("b0", "See [1] and [2]."), _ref("b1", 1), _ref("b2", 2), _ref("b3", 2)])
    assert any(i.id == "ref-dup-2" for i in check_references(ms))


def test_numbering_gap_flagged():
    ms = _ms([_para("b0", "See [1] and [3]."), _ref("b1", 1), _ref("b2", 3)])
    assert any(i.id == "ref-gaps" for i in check_references(ms))


def test_range_citation_expands():
    ms = _ms([_para("b0", "See [1-3]."), _ref("b1", 1), _ref("b2", 2), _ref("b3", 3)])
    assert not any(i.id.startswith("cite-missing") for i in check_references(ms))
