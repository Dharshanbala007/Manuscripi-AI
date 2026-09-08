"""Take an UploadFile, validate it, and land it in a fresh workspace as source.docx."""

from __future__ import annotations

from fastapi import UploadFile

from app.config import Settings
from app.ingestion.validate_upload import UploadValidationError, validate_docx_bytes
from app.logging_config import log_stage
from app.storage.base import DocumentRecord, DocumentStore
from app.storage.workspace import WorkspaceManager
from app.utils.ids import new_id

_CHUNK = 1024 * 1024


async def receive_upload(
    upload: UploadFile,
    settings: Settings,
    store: DocumentStore,
    workspaces: WorkspaceManager,
) -> DocumentRecord:
    original_name = upload.filename or "manuscript.docx"
    if not original_name.lower().endswith(".docx"):
        raise UploadValidationError("not_docx", "Only .docx Word documents are supported.")

    max_bytes = settings.max_upload_bytes
    data = await _read_capped(upload, max_bytes)
    validate_docx_bytes(data, max_bytes)

    doc_id = new_id()
    workspaces.create(doc_id)
    source_path = workspaces.path(doc_id, "source.docx")
    source_path.write_bytes(data)

    record = DocumentRecord(
        id=doc_id,
        filename=_display_name(original_name),
        size=len(data),
        state="uploaded",
        source_path=source_path,
    )
    store.create(record)
    log_stage("upload", document_id=doc_id, bytes=len(data))
    return record


async def _read_capped(upload: UploadFile, cap: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(_CHUNK):
        total += len(chunk)
        if total > cap:
            limit_mb = cap / (1024 * 1024)
            raise UploadValidationError(
                "too_large", f"This file is larger than the {limit_mb:.0f} MB upload limit."
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _display_name(name: str) -> str:
    """Basename only, for display. Never used as a filesystem path."""
    base = name.replace("\\", "/").split("/")[-1].strip()
    return base[:255] or "manuscript.docx"
