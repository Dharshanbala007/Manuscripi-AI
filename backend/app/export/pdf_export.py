"""DOCX -> PDF via headless LibreOffice. Fully local; degrades cleanly when absent."""

from __future__ import annotations

import shutil
from pathlib import Path

from app.config import Settings


def resolve_soffice(settings: Settings) -> str | None:
    """Return a usable `soffice` path, or None if LibreOffice is not available."""
    if settings.soffice_path:
        p = Path(settings.soffice_path)
        return str(p) if p.exists() else None
    found = shutil.which("soffice") or shutil.which("soffice.exe")
    if found:
        return found
    # Common Windows install location not always on PATH.
    win_default = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
    return str(win_default) if win_default.exists() else None


def pdf_available(settings: Settings) -> bool:
    return resolve_soffice(settings) is not None
