"""Results endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core import storage

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/{job_id}")
def get_result(job_id: str) -> dict:
    rec = storage.load("results", job_id)
    if not rec:
        raise HTTPException(404, "Result not found")
    return rec


@router.get("/{job_id}/summary")
def get_result_summary(job_id: str) -> dict:
    rec = storage.load("results", job_id)
    if not rec:
        raise HTTPException(404, "Result not found")
    targets = rec.get("targets", {})
    return {
        "aoi": rec.get("aoi", {}).get("name"),
        "n_features": rec.get("n_features"),
        "timings": rec.get("timings"),
        "sources_used": rec.get("sources_used"),
        "targets": {
            k: {
                "label_en": v["label_en"],
                "label_ar": v["label_ar"],
                "color": v["color"],
                "summary": v["summary"],
            }
            for k, v in targets.items()
        },
    }
