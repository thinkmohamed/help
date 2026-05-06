"""Backend smoke tests — verify the full pipeline executes end-to-end."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.outputs.targets import TARGETS


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="module")
def aoi_id(client: TestClient) -> str:
    geom = {
        "type": "Polygon",
        "coordinates": [
            [[31.10, 29.95], [31.20, 29.95], [31.20, 30.05], [31.10, 30.05], [31.10, 29.95]]
        ],
    }
    r = client.post("/api/aoi", json={"name": "Test AOI", "geometry": geom})
    assert r.status_code == 200
    return r.json()["id"]


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sources_listed(client: TestClient) -> None:
    r = client.get("/api/sources")
    assert r.status_code == 200
    sources = r.json()
    assert len(sources) == 14
    providers = {s["provider"] for s in sources}
    assert providers == {"copernicus", "usgs", "gee", "corona"}


def test_pipeline_end_to_end(client: TestClient, aoi_id: str) -> None:
    payload = {
        "aoi_id": aoi_id,
        "sources": [
            "sentinel-2",
            "sentinel-1",
            "srtm",
            "modis",
            "corona-1960",
            "aster-gdem",
            "landsat-89",
        ],
        "grid": [48, 48],
        "use_torch": False,
    }
    r = client.post("/api/jobs", json=payload)
    assert r.status_code == 200
    job_id = r.json()["id"]

    final_status = "queued"
    for _ in range(60):
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200
        final_status = r.json()["status"]
        if final_status in {"completed", "failed"}:
            break
        time.sleep(0.1)
    assert final_status == "completed", r.json().get("error")

    result = client.get(f"/api/results/{job_id}").json()
    assert set(result["targets"]) == set(TARGETS)
    for key in TARGETS:
        target = result["targets"][key]
        assert "summary" in target
        assert "heatmap_png" in target and target["heatmap_png"].startswith("data:image/png;base64,")
        assert 0.0 <= target["summary"]["mean_prob"] <= 1.0
        assert 0.0 <= target["summary"]["max_prob"] <= 1.0


def test_aoi_crud(client: TestClient) -> None:
    geom = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    r = client.post("/api/aoi", json={"name": "tmp", "geometry": geom})
    assert r.status_code == 200
    aid = r.json()["id"]
    assert client.get(f"/api/aoi/{aid}").status_code == 200
    assert any(a["id"] == aid for a in client.get("/api/aoi").json())
    assert client.delete(f"/api/aoi/{aid}").json()["deleted"] is True
    assert client.get(f"/api/aoi/{aid}").status_code == 404
