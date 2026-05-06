"""Data source listing endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ..connectors.registry import SOURCES, get_connector

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
def list_sources() -> list[dict]:
    out: list[dict] = []
    auth_cache: dict[str, bool] = {}
    for s in SOURCES:
        prov = s["provider"]
        if prov not in auth_cache:
            auth_cache[prov] = get_connector(prov).is_authenticated()
        out.append({**s, "authenticated": auth_cache[prov]})
    return out
