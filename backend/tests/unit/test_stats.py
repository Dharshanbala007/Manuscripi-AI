from app.analysis.stats import compute_stats
from app.domain.elements import Block, ElementType, SourceRef


def _b(kind, text="", *, idx=0):
    return Block(id=f"b{idx}", kind=kind, text=text, source_ref=SourceRef("document", idx))


def test_compute_stats_counts_by_kind():
    blocks = [
        _b(ElementType.HEADING, "1 Introduction", idx=0),
        _b(ElementType.PARAGRAPH, "one two three", idx=1),
        _b(ElementType.PARAGRAPH, "four five", idx=2),
        _b(ElementType.SUBHEADING, "1.1 Detail", idx=3),
        _b(ElementType.TABLE, "a | b", idx=4),
        _b(ElementType.FIGURE, "", idx=5),
        _b(ElementType.CAPTION, "Fig. 1.", idx=6),
        _b(ElementType.REFERENCE_ITEM, "[1] Author, Work.", idx=7),
        _b(ElementType.REFERENCE_ITEM, "[2] Author, Work.", idx=8),
    ]
    stats = compute_stats(blocks)

    assert stats.paragraphs == 2
    assert stats.headings == 2  # heading + subheading
    assert stats.sections == 1  # top-level headings only
    assert stats.tables == 1
    assert stats.figures == 1
    assert stats.references == 2
    assert stats.words == 20  # sum of word counts across every block's text
