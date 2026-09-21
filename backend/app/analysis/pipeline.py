"""run_analysis: the staged pipeline behind POST /documents/{id}/analyze.

Runs synchronously as a background task. Each stage records real counts on the
shared AnalysisProgress so a polling client sees genuine progress.
"""

from __future__ import annotations

import time

from app.analysis.stats import compute_stats
from app.classification.classifier import classify_blocks
from app.classification.structure import build_outline
from app.domain.analysis import AnalysisProgress, StageStatus
from app.domain.elements import ElementType
from app.domain.issues import Issue, IssueCategory, Severity
from app.domain.manuscript import Manuscript
from app.extraction.metadata import extract_metadata
from app.logging_config import log_stage, logger
from app.parsing.docx_reader import DocxReadError, parse_docx
from app.storage.base import DocumentStore
from app.storage.history import HistoryStore, record_history
from app.utils.ids import short_id
from app.utils.text import shorten

_HEADING_KINDS = (ElementType.HEADING, ElementType.SUBHEADING)


def run_analysis(
    doc_id: str,
    store: DocumentStore,
    history: HistoryStore,
    confidence_threshold: float = 0.6,
) -> None:
    record = store.get(doc_id)
    if record is None:
        return

    record.state = "analyzing"
    record.analysis = record.analysis or AnalysisProgress()
    record.error = None
    record.error_id = None
    store.update(record)

    started = time.perf_counter()
    try:
        _run(record, store, confidence_threshold)
        record.state = "analyzed"
    except DocxReadError:
        record.state = "error"
        record.error = "Unable to read this document. The file may be corrupted."
        record.error_id = short_id()
        log_stage("analyze_failed", document_id=doc_id, error_id=record.error_id)
    except Exception:  # noqa: BLE001 - pipeline must fail soft with a sanitized message
        record.state = "error"
        record.error = "Some document elements could not be interpreted."
        record.error_id = short_id()
        logger.exception(
            "analyze_error",
            extra={"extra_fields": {"error_id": record.error_id, "document_id": doc_id}},
        )
    finally:
        store.update(record)
        record_history(history, record)
        log_stage(
            "analyze_done",
            document_id=doc_id,
            stage=record.state,
            duration_ms=(time.perf_counter() - started) * 1000,
        )


def _run(record, store: DocumentStore, threshold: float) -> None:
    prog: AnalysisProgress = record.analysis

    with _stage(prog, store, record, "read") as done:
        parsed = parse_docx(record.source_path)
        done(f"{len(parsed.blocks)} elements")

    with _stage(prog, store, record, "extract") as done:
        text_blocks = [b for b in parsed.blocks if b.text.strip()]
        done(f"{len(text_blocks)} text blocks")

    with _stage(prog, store, record, "metadata") as done:
        metadata = extract_metadata(parsed.blocks, threshold)
        done(_metadata_detail(metadata))

    with _stage(prog, store, record, "classify") as done:
        blocks = classify_blocks(parsed.blocks, metadata, threshold)
        headings = [b for b in blocks if b.kind in _HEADING_KINDS]
        paragraphs = [b for b in blocks if b.kind == ElementType.PARAGRAPH]
        done(f"{len(headings)} headings, {len(paragraphs)} paragraphs")

    with _stage(prog, store, record, "figures") as done:
        figures = sum(1 for b in blocks if b.kind == ElementType.FIGURE)
        tables = sum(1 for b in blocks if b.kind == ElementType.TABLE)
        done(f"{figures} figures, {tables} tables")

    with _stage(prog, store, record, "references") as done:
        refs = sum(1 for b in blocks if b.kind == ElementType.REFERENCE_ITEM)
        done(f"{refs} references")

    with _stage(prog, store, record, "structure") as done:
        outline = build_outline(blocks)
        stats = compute_stats(blocks)
        done(f"{stats.sections} sections")

    record.manuscript = Manuscript(
        id=record.id,
        source_filename=record.filename,
        metadata=metadata,
        body=blocks,
        outline=outline,
        stats=stats,
        parse_warnings=parsed.parse_warnings,
    )
    record.issues = review_issues(record.manuscript)


class _stage:
    """Context manager: mark a stage active on enter, done (with detail) on exit."""

    def __init__(self, prog: AnalysisProgress, store: DocumentStore, record, key: str) -> None:
        self._stage_obj = prog.stage(key)
        self._store = store
        self._record = record
        self._detail = ""

    def __enter__(self):
        self._stage_obj.status = StageStatus.ACTIVE
        self._store.update(self._record)

        def done(detail: str = "") -> None:
            self._detail = detail

        return done

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self._stage_obj.status = StageStatus.DONE
            self._stage_obj.detail = self._detail
            self._store.update(self._record)


def _metadata_detail(md) -> str:
    bits = []
    if md.title.value:
        bits.append("title")
    if md.authors.value:
        bits.append(f"{len(md.authors.value)} authors")
    if md.abstract.value:
        bits.append("abstract")
    if md.keywords.value:
        bits.append(f"{len(md.keywords.value)} keywords")
    return ", ".join(bits) if bits else "no metadata detected"


def review_issues(ms: Manuscript) -> list[Issue]:
    issues: list[Issue] = []
    md = ms.metadata

    for key, field, label in (("title", md.title, "Title"), ("abstract", md.abstract, "Abstract")):
        if not field.value:
            issues.append(
                Issue(
                    id=f"meta-{key}-missing",
                    severity=Severity.WARNING,
                    category=IssueCategory.STRUCTURE,
                    message=f"{label} was not detected.",
                    suggested_action=f"Add the {label.lower()} in the metadata panel.",
                )
            )
        elif field.confidence < 0.6 and not field.edited_by_user:
            issues.append(
                Issue(
                    id=f"meta-{key}-lowconf",
                    severity=Severity.INFO,
                    category=IssueCategory.STRUCTURE,
                    message=f"{label} detection is uncertain ({field.confidence:.0%} confidence).",
                    suggested_action=f"Confirm the {label.lower()} in the metadata panel.",
                )
            )

    if not md.authors.value:
        issues.append(
            Issue(
                id="meta-authors-missing",
                severity=Severity.WARNING,
                category=IssueCategory.STRUCTURE,
                message="No authors were detected.",
                suggested_action="Add authors in the metadata panel.",
            )
        )
    if not md.keywords.value:
        issues.append(
            Issue(
                id="meta-keywords-missing",
                severity=Severity.INFO,
                category=IssueCategory.STRUCTURE,
                message="No keywords were detected.",
                suggested_action="Add keywords in the metadata panel.",
            )
        )

    for b in ms.body:
        if b.needs_review:
            issues.append(
                Issue(
                    id=f"cls-{b.id}",
                    severity=Severity.INFO,
                    category=IssueCategory.CONTENT,
                    message=f"“{shorten(b.text, 60)}” classified as {b.kind} with low confidence.",
                    location=b.id,
                    suggested_action="Review or reclassify this element.",
                )
            )

    return issues
