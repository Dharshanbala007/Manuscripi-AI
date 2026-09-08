"""Document lifecycle endpoints. Handlers stay thin; work lives in services."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile

from app.analysis.pipeline import run_analysis
from app.api.deps import get_settings_dep, get_store, get_workspaces
from app.api.errors import ApiError
from app.config import Settings
from app.domain.analysis import AnalysisProgress
from app.ingestion.receive import receive_upload
from app.ingestion.validate_upload import UploadValidationError
from app.schemas.analysis import (
    AnalysisOut,
    ElementOut,
    ElementPage,
    OutlineNodeOut,
    OutlineOut,
)
from app.schemas.document import DocumentOut
from app.storage.base import DocumentRecord, DocumentStore
from app.storage.workspace import WorkspaceManager
from app.utils.text import shorten

router = APIRouter(prefix="/documents", tags=["documents"])

_STATUS_BY_CODE = {"too_large": 413, "not_docx": 415, "corrupt": 400, "unsafe_zip": 400}
_BUSY_STATES = {"analyzing", "formatting", "validating", "exporting"}


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
) -> DocumentOut:
    try:
        record = await receive_upload(file, settings, store, workspaces)
    except UploadValidationError as exc:
        raise ApiError(_STATUS_BY_CODE.get(exc.code, 400), exc.code, exc.message) from None
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
) -> dict:
    record = _require(store, doc_id)
    if record.state in _BUSY_STATES:
        raise ApiError(409, "busy", f"The document is currently {record.state}.")

    record.state = "analyzing"
    record.analysis = AnalysisProgress()
    record.manuscript = None
    record.issues = []
    store.update(record)
    background.add_task(run_analysis, doc_id, store, settings.confidence_threshold)
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
    items = [
        ElementOut(
            id=b.id,
            kind=str(b.kind),
            confidence=b.confidence,
            text_preview=shorten(b.text, 160),
            needs_review=b.needs_review,
            level=b.level,
            number=b.number,
            section=b.section,
        )
        for b in window
    ]
    return ElementPage(items=items, total=len(body), offset=offset, limit=limit)
