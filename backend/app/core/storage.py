"""Lightweight JSON-backed storage for AOI/jobs/results."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .config import settings

_lock = threading.RLock()


def _path(kind: str, key: str) -> Path:
    return settings.data_dir / kind / f"{key}.json"


def save(kind: str, key: str, value: dict[str, Any]) -> None:
    with _lock:
        _path(kind, key).write_text(json.dumps(value, default=str, ensure_ascii=False, indent=2))


def load(kind: str, key: str) -> dict[str, Any] | None:
    p = _path(kind, key)
    if not p.exists():
        return None
    with _lock:
        return json.loads(p.read_text())


def delete(kind: str, key: str) -> bool:
    p = _path(kind, key)
    if not p.exists():
        return False
    with _lock:
        p.unlink()
    return True


def list_all(kind: str) -> list[dict[str, Any]]:
    base = settings.data_dir / kind
    if not base.exists():
        return []
    out: list[dict[str, Any]] = []
    with _lock:
        for p in sorted(base.glob("*.json")):
            try:
                out.append(json.loads(p.read_text()))
            except json.JSONDecodeError:
                continue
    return out
