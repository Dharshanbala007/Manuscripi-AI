"""format_document: apply a publisher profile to a *copy* of the source DOCX."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document

from app.domain.issues import ChangeLog, Issue
from app.domain.manuscript import Manuscript
from app.formatting.body import restyle_body
from app.formatting.figures import check_figures
from app.formatting.frontmatter import rebuild_frontmatter
from app.formatting.page import apply_page_layout
from app.formatting.styles import ensure_styles
from app.formatting.tables import style_tables
from app.profiles.base import PublisherProfile


@dataclass
class FormatResult:
    out_path: Path
    change_log: ChangeLog
    issues: list[Issue] = field(default_factory=list)


def format_document(
    manuscript: Manuscript,
    source_path: Path | str,
    out_path: Path | str,
    profile: PublisherProfile,
) -> FormatResult:
    source_path = Path(source_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, out_path)  # work on a copy; source is never opened for writing

    doc = Document(str(out_path))

    ensure_styles(doc, profile)
    apply_page_layout(doc, profile)

    changes: list[str] = [
        f"Applied {profile.name} page layout "
        f"({profile.columns.count}-column, {profile.page.size.upper()})"
    ]
    changes += restyle_body(doc, manuscript, profile)

    issues: list[Issue] = []
    issues += style_tables(doc, manuscript, profile)
    issues += check_figures(doc, manuscript, profile)

    # Front matter rebuilt last: it may add/remove leading paragraphs, so nothing
    # after it may depend on paragraph/block alignment.
    changes += rebuild_frontmatter(doc, manuscript, profile)

    doc.save(str(out_path))

    change_log = ChangeLog(
        formatting_changes=changes,
        content_changes=[],  # filled by the preservation check at the API layer
        warnings_remaining=len(issues),
    )
    return FormatResult(out_path=out_path, change_log=change_log, issues=issues)
