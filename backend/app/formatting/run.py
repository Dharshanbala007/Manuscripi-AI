"""Orchestrate format + validate for the API layer. Keeps route handlers thin."""

from __future__ import annotations

from app.domain.issues import ChangeLog, HealthScore, Issue, PreservationResult
from app.logging_config import log_stage
from app.profiles.loader import PLANNED_PROFILES, ProfileNotFound, load_profile
from app.storage.base import DocumentRecord
from app.storage.workspace import WorkspaceManager
from app.validation.health import score
from app.validation.preservation import check_preservation
from app.validation.validators import validate

_STALE_ARTIFACTS = ("export_docx", "export_pdf", "preview_pdf")


class ProfileUnavailable(Exception):
    def __init__(self, profile_id: str, *, planned: bool) -> None:
        super().__init__(profile_id)
        self.profile_id = profile_id
        self.planned = planned


def run_format(
    record: DocumentRecord, workspaces: WorkspaceManager, profile_id: str
) -> tuple[ChangeLog, HealthScore, list[Issue], PreservationResult]:
    if profile_id in PLANNED_PROFILES:
        raise ProfileUnavailable(profile_id, planned=True)
    try:
        profile = load_profile(profile_id)
    except ProfileNotFound:
        raise ProfileUnavailable(profile_id, planned=False) from None

    from app.formatting.engine import format_document

    out_path = workspaces.path(record.id, "formatted.docx")
    result = format_document(record.manuscript, record.source_path, out_path, profile)

    preservation = check_preservation(record.manuscript, out_path)
    result.change_log.content_changes = (
        [] if preservation.passed else (list(preservation.details) or ["Content review required."])
    )

    issues = validate(record.manuscript, out_path, profile)
    health = score(issues, record.manuscript)

    record.artifacts["formatted"] = out_path
    for key in _STALE_ARTIFACTS:
        record.artifacts.pop(key, None)
    record.profile_id = profile_id
    record.change_log = result.change_log
    record.issues = issues
    record.health = health
    record.preservation = preservation
    record.state = "formatted"

    log_stage(
        "format",
        document_id=record.id,
        stage=profile_id,
        issues=len(issues),
        health=health.total,
    )
    return result.change_log, health, issues, preservation


def run_validate(
    record: DocumentRecord, workspaces: WorkspaceManager
) -> tuple[list[Issue], HealthScore, PreservationResult]:
    profile = load_profile(record.profile_id or "ieee")
    out_path = record.artifacts["formatted"]

    issues = validate(record.manuscript, out_path, profile)
    preservation = check_preservation(record.manuscript, out_path)
    health = score(issues, record.manuscript)

    record.issues = issues
    record.health = health
    record.preservation = preservation
    record.state = "validated"

    log_stage("validate", document_id=record.id, issues=len(issues), health=health.total)
    return issues, health, preservation
