from app.domain.elements import SourceRef
from app.extraction.metadata import extract_metadata
from app.parsing.blocks import ParsedBlock, RunFormat


def pb(text, *, size=11, bold=False, align=None, style=None, kind="paragraph", level=None, idx=0):
    return ParsedBlock(
        kind_hint=kind,
        text=text,
        runs=[RunFormat(text=text, size_pt=size, bold=bold)] if text else [],
        style_name=style,
        alignment=align,
        outline_level=level,
        source_ref=SourceRef("document", idx),
    )


def front_matter():
    return [
        pb(
            "Deep Learning for Manuscript Structure Detection",
            size=20,
            bold=True,
            align="center",
            style="Title",
            idx=0,
        ),
        pb("Ada Lovelace, Alan Turing and Grace Hopper", size=11, idx=1),
        pb("Department of Computing, University of Somewhere", size=10, idx=2),
        pb("ada@uni.edu", size=10, idx=3),
        pb("Abstract", size=11, bold=True, level=0, idx=4),
        pb(
            "This paper presents a rule based system for detecting the structure of "
            "academic manuscripts and reports strong results across several datasets.",
            size=10,
            idx=5,
        ),
        pb("Index Terms— formatting, parsing, classification", size=10, idx=6),
        pb("1. Introduction", size=12, bold=True, level=0, idx=7),
        pb("Academic writing follows conventions.", size=10, idx=8),
    ]


def test_title_detected_with_confidence():
    md = extract_metadata(front_matter(), 0.6)
    assert md.title.value.startswith("Deep Learning for Manuscript")
    assert md.title.confidence >= 0.6
    assert md.title.source_ref.index == 0


def test_authors_split_into_three():
    md = extract_metadata(front_matter(), 0.6)
    assert [a.name for a in md.authors.value] == ["Ada Lovelace", "Alan Turing", "Grace Hopper"]


def test_affiliation_and_email_detected():
    md = extract_metadata(front_matter(), 0.6)
    assert any("University of Somewhere" in a.text for a in md.affiliations)
    assert md.authors.value[0].email == "ada@uni.edu"


def test_abstract_from_heading():
    md = extract_metadata(front_matter(), 0.6)
    assert md.abstract.value.startswith("This paper presents a rule based system")
    assert md.abstract.confidence >= 0.6


def test_keywords_from_index_terms():
    md = extract_metadata(front_matter(), 0.6)
    assert md.keywords.value == ["formatting", "parsing", "classification"]
    assert md.keywords.confidence >= 0.6


def test_inline_abstract_lead_in():
    blocks = [
        pb("A Concise Descriptive Title", size=18, bold=True, align="center", idx=0),
        pb("Jane Roe", idx=1),
        pb("Abstract— " + "signal " * 30, size=10, idx=2),
    ]
    md = extract_metadata(blocks, 0.6)
    assert md.abstract.value.strip().startswith("signal")
    assert md.abstract.confidence >= 0.6
    assert [a.name for a in md.authors.value] == ["Jane Roe"]


def test_authors_with_superscript_markers_and_affiliation_lines():
    blocks = [
        pb("A Clear Title", size=18, bold=True, align="center", idx=0),
        pb("Ada Lovelace¹, Alan Turing², Grace Hopper¹ and Katherine Johnson³", idx=1),
        pb("¹ Department of Computing, University of Somewhere", idx=2),
        pb("² Institute for Advanced Study, Elsewhere", idx=3),
        pb("³ Numerical Analysis Laboratory, Farfield College", idx=4),
    ]
    md = extract_metadata(blocks, 0.6)
    assert [a.name for a in md.authors.value] == [
        "Ada Lovelace",
        "Alan Turing",
        "Grace Hopper",
        "Katherine Johnson",
    ]
    aff_text = " | ".join(a.text for a in md.affiliations)
    assert "Institute for Advanced Study" in aff_text
    assert "University of Somewhere" in aff_text
    assert "Elsewhere" not in [a.name for a in md.authors.value]


def test_keywords_plain_label_semicolons():
    blocks = [pb("Keywords: alpha; beta ; gamma", idx=0)]
    md = extract_metadata(blocks, 0.6)
    assert md.keywords.value == ["alpha", "beta", "gamma"]


def test_weak_title_gets_low_confidence():
    blocks = [
        pb(
            "In this work we consider the following long rambling sentence that is "
            "clearly not a title and simply keeps going well past any reasonable point.",
            size=11,
            idx=0,
        ),
        pb("More body text continuing the paragraph above without pause.", size=11, idx=1),
    ]
    md = extract_metadata(blocks, 0.6)
    assert md.title.confidence < 0.6
