"""USGS EarthExplorer connector.

Provides access to:
- Landsat 8/9 (optical 30m)
- Landsat 1972 (archive)
- ASTER (thermal 90m)
- ASTER GDEM (elevations 30m)
"""

from __future__ import annotations

from typing import Any

import httpx
import numpy as np

from ...config import USGS_USERNAME, USGS_PASSWORD


USGS_API_URL = "https://m2m.cr.usgs.gov/api/api/json/stable"

LAYER_CONFIGS = {
    "landsat89_optical": {
        "dataset": "landsat_ot_c2_l2",
        "resolution": 30,
        "bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
        "description_ar": "بصري 30م",
    },
    "landsat_archive": {
        "dataset": "landsat_mss_c2_l1",
        "resolution": 60,
        "bands": ["B4", "B5", "B6", "B7"],
        "description_ar": "أرشيف 1972",
    },
    "aster_thermal": {
        "dataset": "aster_l1t",
        "resolution": 90,
        "bands": ["TIR_Band10", "TIR_Band11", "TIR_Band12", "TIR_Band13", "TIR_Band14"],
        "description_ar": "حراري 90م",
    },
    "aster_gdem": {
        "dataset": "astgtmv003",
        "resolution": 30,
        "bands": ["DEM"],
        "description_ar": "ارتفاعات 30م",
    },
}


async def authenticate() -> str | None:
    """Get USGS API key."""
    if not USGS_USERNAME or not USGS_PASSWORD:
        return None
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{USGS_API_URL}/login",
                json={
                    "username": USGS_USERNAME,
                    "password": USGS_PASSWORD,
                },
            )
            if resp.status_code == 200:
                return resp.json().get("data")
        except httpx.RequestError:
            pass
    return None


async def search_scenes(
    bbox: tuple[float, float, float, float],
    layer: str,
    date_from: str | None = None,
    date_to: str | None = None,
    max_cloud_cover: float = 20.0,
) -> list[dict[str, Any]]:
    """Search for scenes in USGS EarthExplorer."""
    config = LAYER_CONFIGS.get(layer)
    if not config:
        return []

    west, south, east, north = bbox
    api_key = await authenticate()
    headers = {"X-Auth-Token": api_key} if api_key else {}

    search_params: dict[str, Any] = {
        "datasetName": config["dataset"],
        "spatialFilter": {
            "filterType": "mbr",
            "lowerLeft": {"latitude": south, "longitude": west},
            "upperRight": {"latitude": north, "longitude": east},
        },
        "maxResults": 10,
    }
    if date_from and date_to:
        search_params["temporalFilter"] = {
            "startDate": date_from,
            "endDate": date_to,
        }
    if config["dataset"].startswith("landsat"):
        search_params["cloudCoverFilter"] = {"max": max_cloud_cover}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{USGS_API_URL}/scene-search",
                json=search_params,
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return data.get("results", [])
        except httpx.RequestError:
            pass
    return []


def simulate_landsat_data(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate Landsat 8/9 multi-spectral data."""
    np.random.seed(50)
    bands = {}
    for name in ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]:
        bands[name] = np.random.uniform(0, 1, (height, width)).astype(np.float32)
    return bands


def simulate_aster_thermal(
    width: int = 128, height: int = 128
) -> dict[str, np.ndarray]:
    """Simulate ASTER thermal data."""
    np.random.seed(51)
    bands = {}
    for name in ["TIR_Band10", "TIR_Band11", "TIR_Band12", "TIR_Band13", "TIR_Band14"]:
        bands[name] = np.random.uniform(270, 340, (height, width)).astype(np.float32)
    return bands


def simulate_aster_gdem(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate ASTER GDEM elevation data."""
    np.random.seed(52)
    x = np.linspace(0, 4 * np.pi, width)
    y = np.linspace(0, 4 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    dem = (
        200
        + 100 * np.sin(xx / 2) * np.cos(yy / 3)
        + 50 * np.random.randn(height, width)
    )
    return {"DEM": dem.astype(np.float32)}


def simulate_landsat_archive(
    width: int = 128, height: int = 128
) -> dict[str, np.ndarray]:
    """Simulate historical Landsat MSS data from 1972."""
    np.random.seed(53)
    bands = {}
    for name in ["B4", "B5", "B6", "B7"]:
        bands[name] = np.random.uniform(0, 1, (height, width)).astype(np.float32)
    return bands
