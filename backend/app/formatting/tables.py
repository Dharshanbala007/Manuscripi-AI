"""Apply the profile table style; flag tables that may overflow (never shrink)."""

from __future__ import annotations

from app.domain.elements import ElementType
from app.domain.issues import Issue, IssueCategory, Severity
from app.profiles.base import PublisherProfile


def style_tables(doc, manuscript, profile: PublisherProfile) -> list[Issue]:
    issues: list[Issue] = []
    table_blocks = [b for b in manuscript.body if b.kind == ElementType.TABLE]

    for i, table in enumerate(doc.tables):
        try:
            table.style = doc.styles[profile.tables.style_name]
        except KeyError:
            pass

        if profile.tables.header_bold and len(table.rows) > 0:
            for cell in table.rows[0].cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.bold = True

        ncols = _column_count(table)
        if ncols > profile.validation.max_table_cols_before_flag:
            issues.append(
                Issue(
                    id=f"tbl-{i}-wide",
                    severity=Severity.WARNING,
                    category=IssueCategory.LAYOUT,
                    message=(
                        f"Table {i + 1} has {ncols} columns and may overflow the "
                        f"{profile.columns.count}-column layout."
                    ),
                    location=table_blocks[i].id if i < len(table_blocks) else None,
                    suggested_action="Split the table or place it across the full page width.",
                )
            )

    return issues


def _column_count(table) -> int:
    try:
        return len(table.columns)
    except Exception:  # noqa: BLE001 - irregular grid
        return len(table.rows[0].cells) if table.rows else 0
