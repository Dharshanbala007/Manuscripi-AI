"""Load publisher profiles from YAML and list what the product supports."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.profiles.base import PublisherProfile

_DATA_DIR = Path(__file__).parent / "data"

# Publishers we intend to support but do not yet ship a full profile for.
# Surfaced honestly in GET /api/formats and rejected by POST /format.
PLANNED_PROFILES: dict[str, dict] = {
    "springer": {
        "name": "Springer",
        "summary": "Springer-oriented manuscript structure with configurable layout.",
        "features": [
            "Single-column layout",
            "Structured headings",
            "Springer-style references",
        ],
    }
}


class ProfileNotFound(Exception):
    pass


@dataclass(frozen=True)
class ProfileSummary:
    id: str
    name: str
    summary: str
    features: list[str]
    status: str  # "available" | "planned"


@lru_cache
def load_profile(profile_id: str) -> PublisherProfile:
    path = _DATA_DIR / f"{profile_id}.yaml"
    if not path.exists():
        raise ProfileNotFound(profile_id)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PublisherProfile.model_validate(raw)


def list_profiles() -> list[ProfileSummary]:
    summaries: list[ProfileSummary] = []
    for path in sorted(_DATA_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        summaries.append(
            ProfileSummary(
                id=raw["id"],
                name=raw["name"],
                summary=raw["summary"],
                features=list(raw.get("features", [])),
                status=raw.get("status", "available"),
            )
        )
    known = {s.id for s in summaries}
    for pid, meta in PLANNED_PROFILES.items():
        if pid not in known:
            summaries.append(
                ProfileSummary(
                    id=pid,
                    name=meta["name"],
                    summary=meta["summary"],
                    features=list(meta["features"]),
                    status="planned",
                )
            )
    return sorted(summaries, key=lambda s: (s.status != "available", s.id))
