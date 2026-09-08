"""Document lifecycle endpoints. Handlers stay thin; work lives in services."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.analysis.corrections import apply_element, apply_metadata
from app.analysis.pipeline import run_analysis
from app.api.deps import get_history, get_settings_dep, get_store, get_workspaces
from app.api.errors import ApiError
from app.config import Settings
from app.domain.analysis import AnalysisProgress
from app.export.docx_export import ExportError, export_docx
from app.export.pdf_export import PdfExportError, export_pdf, pdf_available
from app.export.preview import render_structured_html
from app.formatting.run import ProfileUnavailable, run_format, run_validate
from app.ingestion.receive import receive_upload
from app.ingestion.validate_upload import UploadValidationError
from app.schemas.analysis import (
    AnalysisOut,
    ElementOut,
    ElementPage,
    ElementPatchIn,
    OutlineNodeOut,
    OutlineOut,
)
from app.schemas.document import DocumentOut
from app.schemas.formatting import (
    ChangeLogOut,
    FormatIn,
    FormatOut,
    ValidateOut,
)
from app.schemas.metadata import MetadataIn, MetadataOut
from app.schemas.validation import HealthScoreOut, IssueOut, PreservationOut
from app.storage.base import DocumentRecord, DocumentStore
from app.storage.history import HistoryEntry, HistoryStore
from app.storage.workspace import WorkspaceManager
from app.utils.text import shorten


def _record_history(history: HistoryStore, record: DocumentRecord) -> None:
    history.upsert(HistoryEntry.from_record(record))


router = APIRouter(prefix="/documents", tags=["documents"])

_STATUS_BY_CODE = {"too_large": 413, "not_docx": 415, "corrupt": 400, "unsafe_zip": 400}
_BUSY_STATES = {"analyzing", "formatting", "validating", "exporting"}
_EDITABLE_STATES = {"analyzed", "formatted", "validated"}


def _require(store: DocumentStore, doc_id: str) -> DocumentRecord:
    record = store.get(doc_id)
    if record is None:
        raise ApiError(404, "not_found", "Document not found.")
    return record


def _require_analyzed(store: DocumentStore, doc_id: str) -> DocumentRecord:
    record = _require(store, doc_id)
    if record.manuscript is None:
        raise ApiError(409, "not_analyzed", "Analyze the document before requesting this.")
    return record


@router.post("/upload", status_code=201, response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings_dep),
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
    history: HistoryStore = Depends(get_history),
) -> DocumentOut:
    try:
        record = await receive_upload(file, settings, store, workspaces)
    except UploadValidationError as exc:
        raise ApiError(_STATUS_BY_CODE.get(exc.code, 400), exc.code, exc.message) from None
    _record_history(history, record)
    return DocumentOut.from_record(record)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, store: DocumentStore = Depends(get_store)) -> DocumentOut:
    return DocumentOut.from_record(_require(store, doc_id))


@router.post("/{doc_id}/analyze", status_code=202)
def analyze_document(
    doc_id: str,
    background: BackgroundTasks,
    settings: Settings = Depends(get_settings_dep),
    store: DocumentStore = Depends(get_store),
    history: HistoryStore = Depends(get_history),
) -> dict:
    record = _require(store, doc_id)
    if record.state in _BUSY_STATES:
        raise ApiError(409, "busy", f"The document is currently {record.state}.")

    record.state = "analyzing"
    record.analysis = AnalysisProgress()
    record.manuscript = None
    record.issues = []
    store.update(record)
    background.add_task(run_analysis, doc_id, store, history, settings.confidence_threshold)
    return {"id": doc_id, "state": "analyzing"}


@router.get("/{doc_id}/analysis", response_model=AnalysisOut)
def get_analysis(doc_id: str, store: DocumentStore = Depends(get_store)) -> AnalysisOut:
    return AnalysisOut.from_record(_require(store, doc_id))


@router.get("/{doc_id}/outline", response_model=OutlineOut)
def get_outline(doc_id: str, store: DocumentStore = Depends(get_store)) -> OutlineOut:
    record = _require_analyzed(store, doc_id)
    return OutlineOut(nodes=[OutlineNodeOut.from_node(n) for n in record.manuscript.outline])


@router.get("/{doc_id}/elements", response_model=ElementPage)
def get_elements(
    doc_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    store: DocumentStore = Depends(get_store),
) -> ElementPage:
    record = _require_analyzed(store, doc_id)
    body = record.manuscript.body
    window = body[offset : offset + limit]
    return ElementPage(
        items=[_element_out(b) for b in window],
        total=len(body),
        offset=offset,
        limit=limit,
    )


def _element_out(b) -> ElementOut:
    return ElementOut(
        id=b.id,
        kind=str(b.kind),
        confidence=b.confidence,
        text_preview=shorten(b.text, 160),
        needs_review=b.needs_review,
        level=b.level,
        number=b.number,
        section=b.section,
    )


def _require_editable(store: DocumentStore, doc_id: str) -> DocumentRecord:
    record = _require_analyzed(store, doc_id)
    if record.state not in _EDITABLE_STATES:
        raise ApiError(409, "wrong_state", f"Cannot edit a document in state '{record.state}'.")
    return record


@router.put("/{doc_id}/metadata", response_model=MetadataOut)
def update_metadata(
    doc_id: str, body: MetadataIn, store: DocumentStore = Depends(get_store)
) -> MetadataOut:
    record = _require_editable(store, doc_id)
    md = apply_metadata(record, body)
    store.update(record)
    return MetadataOut.from_domain(md)


@router.patch("/{doc_id}/elements/{block_id}", response_model=ElementOut)
def update_element(
    doc_id: str,
    block_id: str,
    body: ElementPatchIn,
    store: DocumentStore = Depends(get_store),
) -> ElementOut:
    record = _require_editable(store, doc_id)
    try:
        block = apply_element(record, block_id, body.kind, body.level)
    except ValueError:
        raise ApiError(422, "bad_kind", f"'{body.kind}' is not a valid element kind.") from None
    if block is None:
        raise ApiError(404, "not_found", "Element not found.")
    store.update(record)
    return _element_out(block)


@router.post("/{doc_id}/format", response_model=FormatOut)
def format_document_endpoint(
    doc_id: str,
    body: FormatIn,
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
    history: HistoryStore = Depends(get_history),
) -> FormatOut:
    record = _require_analyzed(store, doc_id)
    if record.state not in ("analyzed", "formatted", "validated"):
        raise ApiError(409, "wrong_state", f"Cannot format a document in state '{record.state}'.")

    try:
        change_log, health, issues, preservation = run_format(record, workspaces, body.profile_id)
    except ProfileUnavailable as exc:
        message = (
            f"The '{exc.profile_id}' profile is planned but not available yet."
            if exc.planned
            else f"Unknown format profile '{exc.profile_id}'."
        )
        raise ApiError(422, "profile_unavailable", message) from None

    store.update(record)
    _record_history(history, record)
    return FormatOut(
        state=record.state,
        profile_id=body.profile_id,
        change_log=ChangeLogOut.from_domain(change_log),
        health=HealthScoreOut.from_domain(health),
        issues=[IssueOut.from_domain(i) for i in issues],
        preservation=PreservationOut.from_domain(preservation),
    )


@router.post("/{doc_id}/validate", response_model=ValidateOut)
def validate_document_endpoint(
    doc_id: str,
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
    history: HistoryStore = Depends(get_history),
) -> ValidateOut:
    record = _require_analyzed(store, doc_id)
    if record.state not in ("formatted", "validated"):
        raise ApiError(409, "wrong_state", "Format the document before validating.")

    issues, health, preservation = run_validate(record, workspaces)
    store.update(record)
    _record_history(history, record)
    return ValidateOut(
        state=record.state,
        issues=[IssueOut.from_domain(i) for i in issues],
        health=HealthScoreOut.from_domain(health),
        preservation=PreservationOut.from_domain(preservation),
    )


_DOCX_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _require_formatted(store: DocumentStore, doc_id: str) -> DocumentRecord:
    record = _require(store, doc_id)
    if "formatted" not in record.artifacts:
        raise ApiError(409, "not_formatted", "Apply a format before exporting or previewing.")
    return record


def _export_basename(record: DocumentRecord, ext: str) -> str:
    return f"manuscript_{record.profile_id or 'ieee'}_formatted.{ext}"


@router.get("/{doc_id}/export/docx")
def export_document_docx(
    doc_id: str,
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
    history: HistoryStore = Depends(get_history),
) -> FileResponse:
    record = _require_formatted(store, doc_id)
    out = workspaces.path(record.id, _export_basename(record, "docx"))
    try:
        export_docx(record.artifacts["formatted"], out)
    except ExportError as exc:
        raise ApiError(500, "export_failed", str(exc)) from None

    record.artifacts["export_docx"] = out
    record.state = "exported"
    store.update(record)
    _record_history(history, record)
    return FileResponse(str(out), media_type=_DOCX_MEDIA, filename=out.name)


@router.get("/{doc_id}/export/pdf")
def export_document_pdf(
    doc_id: str,
    settings: Settings = Depends(get_settings_dep),
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
    history: HistoryStore = Depends(get_history),
) -> FileResponse:
    record = _require_formatted(store, doc_id)
    if not pdf_available(settings):
        raise ApiError(
            503,
            "pdf_unavailable",
            "PDF export is unavailable on this machine. Install LibreOffice to enable it.",
        )
    try:
        result = export_pdf(record.artifacts["formatted"], workspaces.path(record.id), settings)
    except PdfExportError as exc:
        if exc.unavailable:
            raise ApiError(503, "pdf_unavailable", exc.message) from None
        raise ApiError(500, "export_failed", "The PDF could not be generated.") from None

    target = workspaces.path(record.id, _export_basename(record, "pdf"))
    if Path(result.path) != target:
        shutil.copyfile(result.path, target)
    record.artifacts["export_pdf"] = target
    record.page_count = result.page_count
    record.state = "exported"
    store.update(record)
    _record_history(history, record)
    return FileResponse(str(target), media_type="application/pdf", filename=target.name)


@router.get("/{doc_id}/preview")
def preview_document(
    doc_id: str,
    settings: Settings = Depends(get_settings_dep),
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
):
    record = _require_formatted(store, doc_id)

    if pdf_available(settings):
        cached = record.artifacts.get("preview_pdf")
        try:
            if cached is None or not Path(cached).exists():
                result = export_pdf(
                    record.artifacts["formatted"], workspaces.path(record.id), settings
                )
                cached = result.path
                record.artifacts["preview_pdf"] = cached
                record.page_count = result.page_count
                store.update(record)
            return FileResponse(str(cached), media_type="application/pdf")
        except PdfExportError:
            pass  # fall through to the structured preview

    label = (record.profile_id or "ieee").upper()
    return HTMLResponse(content=render_structured_html(record.manuscript, label))


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: str,
    store: DocumentStore = Depends(get_store),
    workspaces: WorkspaceManager = Depends(get_workspaces),
) -> None:
    _require(store, doc_id)
    workspaces.delete(doc_id)
    store.delete(doc_id)
