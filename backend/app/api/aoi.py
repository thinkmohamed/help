"""AOI management endpoints."""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core import storage

router = APIRouter(prefix="/api/aoi", tags=["aoi"])


class AOICreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    geometry: dict[str, Any]  # GeoJSON polygon
    description: str | None = None


class AOIOut(BaseModel):
    id: str
    name: str
    description: str | None
    geometry: dict[str, Any]
    bbox: list[float]
    created_at: float


def _bbox_of(geometry: dict[str, Any]) -> list[float]:
    coords = geometry.get("coordinates", [])
    pts: list[tuple[float, float]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            if (
                len(node) == 2
                and all(isinstance(x, (int, float)) for x in node)
            ):
                pts.append((float(node[0]), float(node[1])))
            else:
                for child in node:
                    walk(child)

    walk(coords)
    if not pts:
        raise HTTPException(400, "Geometry has no coordinates")
    xs, ys = zip(*pts, strict=False)
    return [min(xs), min(ys), max(xs), max(ys)]


@router.post("", response_model=AOIOut)
def create_aoi(payload: AOICreate) -> AOIOut:
    aoi_id = uuid.uuid4().hex[:12]
    bbox = _bbox_of(payload.geometry)
    record = {
        "id": aoi_id,
        "name": payload.name,
        "description": payload.description,
        "geometry": payload.geometry,
        "bbox": bbox,
        "created_at": time.time(),
    }
    storage.save("aoi", aoi_id, record)
    return AOIOut(**record)


@router.get("", response_model=list[AOIOut])
def list_aoi() -> list[AOIOut]:
    return [AOIOut(**r) for r in storage.list_all("aoi")]


@router.get("/{aoi_id}", response_model=AOIOut)
def get_aoi(aoi_id: str) -> AOIOut:
    record = storage.load("aoi", aoi_id)
    if not record:
        raise HTTPException(404, "AOI not found")
    return AOIOut(**record)


@router.delete("/{aoi_id}")
def delete_aoi(aoi_id: str) -> dict[str, bool]:
    return {"deleted": storage.delete("aoi", aoi_id)}
