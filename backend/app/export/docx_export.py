"""Produce the downloadable DOCX from the formatted working copy, verified openable."""

from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document


class ExportError(Exception):
    pass


def export_docx(formatted_path: Path | str, out_path: Path | str) -> Path:
    formatted_path = Path(formatted_path)
    out_path = Path(out_path)
    if not formatted_path.exists():
        raise ExportError("The formatted document is missing. Re-run formatting.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(formatted_path, out_path)

    try:
        Document(str(out_path))  # verify the output actually opens
    except Exception as exc:  # noqa: BLE001
        raise ExportError("The formatted document could not be generated.") from exc

    return out_path
