"""Validate an uploaded DOCX before it is trusted. DOCX is a ZIP; treat it as hostile."""

from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath

# ponytail: generous ceilings; a real manuscript zip has ~10-150 entries and
# unpacks to a few MB. Raise these if a legitimate document ever trips them.
MAX_ZIP_ENTRIES = 2000
MAX_UNCOMPRESSED_BYTES = 300 * 1024 * 1024

_ZIP_MAGIC = b"PK\x03\x04"
_REQUIRED_PARTS = ("[Content_Types].xml", "word/document.xml")


class UploadValidationError(Exception):
    """Raised when an upload is not a safe, readable .docx.

    `code` is one of: too_large, not_docx, corrupt, unsafe_zip.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_docx_bytes(
    data: bytes,
    max_bytes: int,
    *,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_uncompressed: int = MAX_UNCOMPRESSED_BYTES,
) -> None:
    """Return None if `data` is a safe, readable DOCX; otherwise raise
    UploadValidationError. Inspects the ZIP central directory only — never
    decompresses entry contents (that is what the uncompressed-size cap protects)."""
    if len(data) > max_bytes:
        limit_mb = max_bytes / (1024 * 1024)
        raise UploadValidationError(
            "too_large", f"This file is larger than the {limit_mb:.0f} MB upload limit."
        )

    if data[:4] != _ZIP_MAGIC:
        raise UploadValidationError("not_docx", "This does not look like a Word .docx file.")

    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise UploadValidationError(
            "corrupt",
            "Unable to read this document. The file may be corrupted or not a valid .docx.",
        ) from None

    infos = zf.infolist()

    if len(infos) > max_entries:
        raise UploadValidationError(
            "unsafe_zip", "This document's internal structure looks unsafe and was rejected."
        )

    total_uncompressed = 0
    for info in infos:
        name = info.filename
        parts = PurePosixPath(name.replace("\\", "/")).parts
        if name.startswith(("/", "\\")) or ".." in parts:
            raise UploadValidationError(
                "unsafe_zip", "This document contains an unsafe file path and was rejected."
            )
        total_uncompressed += info.file_size
        if total_uncompressed > max_uncompressed:
            raise UploadValidationError(
                "unsafe_zip", "This document expands to an unsafe size and was rejected."
            )

    names = {i.filename for i in infos}
    if not all(part in names for part in _REQUIRED_PARTS):
        raise UploadValidationError(
            "corrupt", "This .docx is missing required Word document parts."
        )
