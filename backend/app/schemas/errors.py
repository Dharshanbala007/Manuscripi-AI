from __future__ import annotations

from pydantic import BaseModel


class ErrorOut(BaseModel):
    error: str
    message: str
    detail: object | None = None
    hint: str | None = None
    error_id: str | None = None
