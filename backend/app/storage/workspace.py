"""Per-document working directories on the local filesystem, with TTL cleanup."""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

_SAFE_ID = re.compile(r"[^A-Za-z0-9_-]")


class WorkspaceManager:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, doc_id: str) -> Path:
        d = self._dir(doc_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def path(self, doc_id: str, *parts: str) -> Path:
        """Resolve a path inside a document's workspace, refusing to escape it."""
        base = self._dir(doc_id).resolve()
        target = base.joinpath(*parts).resolve()
        if target != base and base not in target.parents:
            raise ValueError("path escapes workspace")
        return target

    def delete(self, doc_id: str) -> None:
        shutil.rmtree(self._dir(doc_id), ignore_errors=True)

    def sweep_expired(self, ttl_minutes: int) -> int:
        cutoff = time.time() - ttl_minutes * 60
        removed = 0
        if not self.root.exists():
            return 0
        for child in self.root.iterdir():
            if child.is_dir() and child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
                removed += 1
        return removed

    def _dir(self, doc_id: str) -> Path:
        safe = _SAFE_ID.sub("", doc_id)
        if not safe:
            raise ValueError("invalid document id")
        return self.root / safe
