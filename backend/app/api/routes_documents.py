"""Document lifecycle endpoints. Handlers stay thin; work lives in services."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_settings_dep, get_store, get_workspaces
from app.api.errors import ApiError
from app.config import Settings
from app.ingestion.receive import receive_upload
from app.ingestion.validate_upload import UploadValidationError
from app.schemas.document import DocumentOut
from app.storage.base import DocumentRecord, DocumentStore
from app.storage.workspace import WorkspaceManager

router = APIRouter(prefix="/documents", tags=["documents"])

_STATUS_BY_CODE = {"too_large": 413, "not_docx": 415, "corrupt": 400, "unsafe_zip": 400}


def _require(store: DocumentStore, doc_id: str) -> DocumentRecord:
    record = store.get(doc_id)
    if record is None:
        raise ApiError(404, "not_found", "Document not found.")
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
