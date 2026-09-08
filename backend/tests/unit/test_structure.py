from app.classification.structure import build_outline, canonicalize_heading
from app.domain.elements import Block, ElementType, SourceRef


def test_canonicalize_direct_and_synonyms():
    assert canonicalize_heading("Introduction") == "introduction"
    assert canonicalize_heading("Background") == "introduction"
    assert canonicalize_heading("Experimental Setup") == "methods"
    assert canonicalize_heading("Findings") == "results"
    assert canonicalize_heading("REFERENCES") == "references"


def test_canonicalize_strips_numbering_prefix():
    assert canonicalize_heading("2. Related Work") == "related_work"
    assert canonicalize_heading("IV. Results") == "results"


def test_canonicalize_unknown_returns_none():
    assert canonicalize_heading("A Wholly Novel Contribution") is None
    assert canonicalize_heading("") is None


def _heading(bid, text, level, canonical=None):
    return Block(
        id=bid,
        kind=ElementType.HEADING,
        text=text,
        level=level,
        section=canonical,
        source_ref=SourceRef("document", int(bid[1:])),
    )


def test_build_outline_nests_by_level():
    blocks = [
        _heading("b0", "1 Introduction", 1, "introduction"),
        _heading("b1", "1.1 Motivation", 2),
        _heading("b2", "2 Methods", 1, "methods"),
        Block(
            id="b3", kind=ElementType.PARAGRAPH, text="body", source_ref=SourceRef("document", 3)
        ),
    ]
    outline = build_outline(blocks)
    assert [n.label for n in outline] == ["1 Introduction", "2 Methods"]
    assert [c.label for c in outline[0].children] == ["1.1 Motivation"]
    assert outline[0].canonical == "introduction"
