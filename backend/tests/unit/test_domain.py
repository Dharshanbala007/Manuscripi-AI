from app.domain.elements import Block, ElementType, SourceRef
from app.domain.issues import HealthScore, clamp_score
from app.domain.manuscript import Field, Manuscript, Metadata


def test_manuscript_construction():
    md = Metadata.empty()
    md.title.value = "A Study of Things"
    blocks = [
        Block(
            id="b1",
            kind=ElementType.HEADING,
            text="Introduction",
            level=1,
            source_ref=SourceRef("document", 0),
        ),
        Block(
            id="b2",
            kind=ElementType.PARAGRAPH,
            text="Body.",
            source_ref=SourceRef("document", 1),
        ),
    ]
    ms = Manuscript(id="d1", source_filename="x.docx", metadata=md, body=blocks)
    assert ms.body[0].kind == "heading"
    assert ms.body[0].level == 1
    assert str(ms.body[1].source_ref) == "document[1]"
    assert ms.metadata.title.edited_by_user is False


def test_field_set_by_user_locks_confidence():
    f: Field[str] = Field(value="")
    f.set_by_user("Corrected Title")
    assert f.value == "Corrected Title"
    assert f.confidence == 1.0
    assert f.edited_by_user is True


def test_element_type_members_match_spec():
    expected = {
        "title",
        "author",
        "affiliation",
        "abstract",
        "keywords",
        "heading",
        "subheading",
        "paragraph",
        "numbered_list_item",
        "bullet_list_item",
        "table",
        "figure",
        "caption",
        "equation",
        "reference_item",
        "acknowledgement",
        "appendix",
        "other",
    }
    assert {e.value for e in ElementType} == expected


def test_clamp_score():
    assert clamp_score(120) == 100
    assert clamp_score(-5) == 0
    assert clamp_score(87.4) == 87
    assert 0 <= HealthScore().total <= 100
