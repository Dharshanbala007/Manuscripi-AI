"""Text normalization helpers used by stats, preservation checks, and hashing."""

from __future__ import annotations

import hashlib
import re

_WS_RE = re.compile(r"\s+")


def normalize_ws(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def count_words(text: str) -> int:
    norm = normalize_ws(text)
    return len(norm.split()) if norm else 0


def text_hash(text: str) -> str:
    return hashlib.sha256(normalize_ws(text).lower().encode("utf-8")).hexdigest()


def shorten(text: str, limit: int = 120) -> str:
    norm = normalize_ws(text)
    return norm if len(norm) <= limit else norm[: limit - 1].rstrip() + "…"
