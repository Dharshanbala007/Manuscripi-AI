from __future__ import annotations

from pydantic import BaseModel

from app.profiles.loader import ProfileSummary


class ProfileSummaryOut(BaseModel):
    id: str
    name: str
    summary: str
    features: list[str]
    status: str

    @classmethod
    def from_summary(cls, summary: ProfileSummary) -> ProfileSummaryOut:
        return cls(
            id=summary.id,
            name=summary.name,
            summary=summary.summary,
            features=list(summary.features),
            status=summary.status,
        )
