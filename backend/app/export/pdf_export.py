"""DOCX -> PDF via headless LibreOffice. Fully local; degrades cleanly when absent."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.config import Settings

_SOFFICE_NAMES = ("soffice.com", "soffice.exe", "soffice")
_WIN_DEFAULTS = (
    r"C:\Program Files\LibreOffice\program\soffice.com",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
)


class PdfExportError(Exception):
    """Raised when PDF generation fails. `unavailable` distinguishes 'no engine'."""

    def __init__(self, message: str, *, unavailable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.unavailable = unavailable


@dataclass
class PdfResult:
    path: Path
    page_count: int


def resolve_soffice(settings: Settings) -> str | None:
    if settings.soffice_path:
        p = Path(settings.soffice_path)
        return str(p) if p.exists() else None
    for name in _SOFFICE_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for candidate in _WIN_DEFAULTS:
        if Path(candidate).exists():
            return candidate
    return None


def pdf_available(settings: Settings) -> bool:
    return resolve_soffice(settings) is not None


def export_pdf(formatted_path: Path | str, out_dir: Path | str, settings: Settings) -> PdfResult:
    soffice = resolve_soffice(settings)
    if soffice is None:
        raise PdfExportError("PDF export is unavailable on this machine.", unavailable=True)

    formatted_path = Path(formatted_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile_uri = f"-env:UserInstallation=file:///{(out_dir / '.lo_profile').resolve().as_posix()}"

    try:
        subprocess.run(
            [
                soffice,
                "--headless",
                profile_uri,
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(formatted_path),
            ],
            check=True,
            capture_output=True,
            timeout=settings.pdf_timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfExportError("PDF conversion timed out.") from exc
    except subprocess.CalledProcessError as exc:
        raise PdfExportError("PDF conversion failed.") from exc
    except OSError as exc:
        raise PdfExportError("PDF conversion could not be started.") from exc

    pdf_path = out_dir / f"{formatted_path.stem}.pdf"
    if not pdf_path.exists():
        raise PdfExportError("PDF conversion produced no output file.")
    with pdf_path.open("rb") as fh:
        if fh.read(5) != b"%PDF-":
            raise PdfExportError("The generated file is not a valid PDF.")
    try:
        pages = len(PdfReader(str(pdf_path)).pages)
    except Exception as exc:  # noqa: BLE001 - any read failure means the PDF is unusable
        raise PdfExportError("The generated PDF could not be read.") from exc
    if pages < 1:
        raise PdfExportError("The generated PDF has no pages.")

    return PdfResult(path=pdf_path, page_count=pages)
