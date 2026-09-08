from app.classification.classifier import classify_blocks
from app.domain.elements import ElementType, SourceRef
from app.domain.manuscript import Field, Metadata
from app.parsing.blocks import ParsedBlock, RunFormat


def pb(
    text,
    *,
    kind="paragraph",
    style=None,
    level=None,
    numbering=None,
    bold=False,
    size=11,
    equation=False,
    idx=0,
):
    return ParsedBlock(
        kind_hint=kind,
        text=text,
        runs=[RunFormat(text=text, size_pt=size, bold=bold)] if text else [],
        style_name=style,
        outline_level=level,
        numbering=numbering,
        has_equation=equation,
        source_ref=SourceRef("document", idx),
    )


def test_heading_from_style_sets_section():
    out = classify_blocks([pb("Introduction", style="Heading 1", level=0)], Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.HEADING
    assert out[0].level == 1
    assert out[0].section == "introduction"


def test_numbered_heading_without_style():
    out = classify_blocks([pb("1.2 Feature Extraction", bold=True)], Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.HEADING
    assert out[0].level == 2


def test_caption_next_to_image_keeps_number():
    blocks = [
        pb("", kind="image", idx=0),
        pb("Figure 3. System architecture overview.", idx=1),
    ]
    out = classify_blocks(blocks, Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.FIGURE
    assert out[1].kind == ElementType.CAPTION
    assert out[1].number == 3


def test_reference_items_only_inside_reference_section():
    blocks = [
        pb("[1] Early citation-looking line before the section.", idx=0),
        pb("References", style="Heading 1", level=0, idx=1),
        pb("[1] A. Author, A Great Paper, 2020.", idx=2),
        pb("[2] B. Writer, Another Paper, 2021.", idx=3),
    ]
    out = classify_blocks(blocks, Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.PARAGRAPH
    assert out[2].kind == ElementType.REFERENCE_ITEM
    assert out[2].number == 1
    assert out[3].number == 2


def test_list_items():
    blocks = [
        pb("first point", numbering="bullet", idx=0),
        pb("second point", numbering="number", idx=1),
    ]
    out = classify_blocks(blocks, Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.BULLET_LIST_ITEM
    assert out[1].kind == ElementType.NUMBERED_LIST_ITEM


def test_equation_only_paragraph():
    out = classify_blocks([pb("", equation=True)], Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.EQUATION


def test_metadata_blocks_tagged_from_source_ref():
    md = Metadata.empty()
    md.title = Field(value="A Fine Title", confidence=0.9, source_ref=SourceRef("document", 0))
    md.abstract = Field(
        value="This is the abstract body text spanning a sentence.",
        confidence=0.8,
        source_ref=SourceRef("document", 1),
    )
    blocks = [
        pb("A Fine Title", idx=0),
        pb("Abstract", idx=1),
        pb("This is the abstract body text spanning a sentence.", idx=2),
        pb("Normal body paragraph that is unrelated.", idx=3),
    ]
    out = classify_blocks(blocks, md, 0.6)
    assert out[0].kind == ElementType.TITLE
    assert out[1].kind == ElementType.ABSTRACT
    assert out[2].kind == ElementType.ABSTRACT
    assert out[3].kind == ElementType.PARAGRAPH


def test_ambiguous_allcaps_heading_is_flagged():
    out = classify_blocks([pb("SYSTEM DESIGN")], Metadata.empty(), 0.6)
    assert out[0].kind == ElementType.HEADING
    assert out[0].needs_review is True
