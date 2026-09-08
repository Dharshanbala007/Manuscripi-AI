"""Supported publication formats — honest about what is available vs planned."""

from __future__ import annotations

from fastapi import APIRouter

from app.profiles.loader import list_profiles
from app.schemas.formats import ProfileSummaryOut

router = APIRouter(tags=["formats"])


@router.get("/formats", response_model=list[ProfileSummaryOut])
def get_formats() -> list[ProfileSummaryOut]:
    return [ProfileSummaryOut.from_summary(s) for s in list_profiles()]
