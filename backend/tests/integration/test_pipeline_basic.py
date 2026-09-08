from app.analysis.pipeline import run_analysis
from app.parsing.docx_reader import parse_docx
from app.storage.base import DocumentRecord
from app.storage.history import InMemoryHistoryStore
from app.storage.memory import InMemoryDocumentStore
from tests.fixtures.gen import academic_docx, write_docx


def test_pipeline_builds_manuscript_from_real_docx(tmp_path):
    data = academic_docx()
    src = write_docx(tmp_path, data, "source.docx")

    store = InMemoryDocumentStore()
    history = InMemoryHistoryStore()
    store.create(DocumentRecord(id="d1", filename="paper.docx", size=len(data), source_path=src))

    run_analysis("d1", store, history, 0.6)
    record = store.get("d1")

    assert record.state == "analyzed"
    assert record.error is None
    assert history.get("d1").state == "analyzed"
    assert history.get("d1").paragraphs == record.manuscript.stats.paragraphs

    parsed = parse_docx(src)
    assert len(record.manuscript.body) == len(parsed.blocks)

    stats = record.manuscript.stats
    assert stats.references == 6
    assert stats.tables == 1
    assert stats.figures >= 1
    assert stats.headings >= 6
    assert stats.words > 50

    assert [s.status for s in record.analysis.stages] == ["done"] * 7
    assert record.manuscript.metadata.title.value.startswith("A Rule-Based Approach")
    assert len(record.manuscript.outline) >= 5
