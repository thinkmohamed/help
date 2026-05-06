"""Job submission & status endpoints."""
from __future__ import annotations

import threading
import time
import traceback
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ..core import storage
from ..orchestrator import run_pipeline

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_job_lock = threading.Lock()


class JobCreate(BaseModel):
    aoi_id: str
    sources: list[str] = Field(..., min_length=1)
    grid: tuple[int, int] = (128, 128)
    use_torch: bool = True


class JobOut(BaseModel):
    id: str
    aoi_id: str
    sources: list[str]
    status: str
    progress: list[dict[str, Any]]
    created_at: float
    started_at: float | None
    finished_at: float | None
    error: str | None


def _set_status(job_id: str, **patch: Any) -> None:
    with _job_lock:
        rec = storage.load("jobs", job_id)
        if not rec:
            return
        rec.update(patch)
        storage.save("jobs", job_id, rec)


def _push_progress(job_id: str, event: dict[str, Any]) -> None:
    with _job_lock:
        rec = storage.load("jobs", job_id) or {}
        progress = list(rec.get("progress", []))
        progress.append({**event, "ts": time.time()})
        rec["progress"] = progress
        storage.save("jobs", job_id, rec)


def _execute(job_id: str) -> None:
    rec = storage.load("jobs", job_id)
    if not rec:
        return
    aoi = storage.load("aoi", rec["aoi_id"])
    if not aoi:
        _set_status(job_id, status="failed", error="AOI not found", finished_at=time.time())
        return
    _set_status(job_id, status="running", started_at=time.time())
    try:
        result = run_pipeline(
            aoi,
            rec["sources"],
            grid=tuple(rec.get("grid", (128, 128))),
            use_torch=rec.get("use_torch", True),
            progress_cb=lambda e: _push_progress(job_id, e),
        )
        storage.save("results", job_id, result)
        _set_status(job_id, status="completed", finished_at=time.time())
    except Exception as exc:  # noqa: BLE001
        _set_status(
            job_id,
            status="failed",
            error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
            finished_at=time.time(),
        )


@router.post("", response_model=JobOut)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks) -> JobOut:
    if not storage.load("aoi", payload.aoi_id):
        raise HTTPException(404, "AOI not found")
    job_id = uuid.uuid4().hex[:12]
    record = {
        "id": job_id,
        "aoi_id": payload.aoi_id,
        "sources": payload.sources,
        "grid": list(payload.grid),
        "use_torch": payload.use_torch,
        "status": "queued",
        "progress": [],
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "error": None,
    }
    storage.save("jobs", job_id, record)
    background_tasks.add_task(_execute, job_id)
    return JobOut(**record)


@router.get("", response_model=list[JobOut])
def list_jobs() -> list[JobOut]:
    return [JobOut(**r) for r in storage.list_all("jobs")]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str) -> JobOut:
    rec = storage.load("jobs", job_id)
    if not rec:
        raise HTTPException(404, "Job not found")
    return JobOut(**rec)
