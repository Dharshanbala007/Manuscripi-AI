from app.analysis.comparison import build_comparison
from app.analysis.pipeline import run_analysis
from app.formatting.run import run_format
from app.storage.base import DocumentRecord
from app.storage.history import InMemoryHistoryStore
from app.storage.memory import InMemoryDocumentStore
from app.storage.workspace import WorkspaceManager
from tests.fixtures.gen import academic_docx


def _formatted_record(tmp_path):
    data = academic_docx()
    workspaces = WorkspaceManager(tmp_path / "ws")
    workspaces.create("d1")
    src = workspaces.path("d1", "source.docx")
    src.write_bytes(data)

    store = InMemoryDocumentStore()
    history = InMemoryHistoryStore()
    store.create(DocumentRecord(id="d1", filename="paper.docx", size=len(data), source_path=src))
    run_analysis("d1", store, history, 0.6)

    record = store.get("d1")
    run_format(record, workspaces, "ieee")
    return record


def test_comparison_matches_content_counts_and_preservation(tmp_path):
    record = _formatted_record(tmp_path)
    comparison = build_comparison(record)

    assert comparison.original.stats.tables == comparison.formatted.stats.tables
    assert comparison.deltas["tables"] == 0
    assert comparison.deltas["figures"] == 0
    assert comparison.deltas["references"] == 0

    assert comparison.summary.preservation_passed is True
    assert comparison.summary.formatting_changes == len(record.change_log.formatting_changes)
    assert comparison.summary.content_changes == 0

    assert comparison.original.metadata.title.startswith("A Rule-Based Approach")
    assert comparison.original.sections
    assert comparison.formatted.sections
