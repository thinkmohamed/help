"""Copernicus Dataspace connector.

Provides access to:
- Sentinel-2 (optical 10m)
- Sentinel-1 SAR (radar)
- Sentinel-3 OLCI (thermal)
- Sentinel-5P (gases)
"""

from __future__ import annotations

from typing import Any

import httpx
import numpy as np

from ...config import COPERNICUS_CLIENT_ID, COPERNICUS_CLIENT_SECRET


COPERNICUS_API_URL = "https://dataspace.copernicus.eu/odata/v1"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

LAYER_CONFIGS = {
    "sentinel2_optical": {
        "collection": "SENTINEL-2",
        "product_type": "S2MSI2A",
        "resolution": 10,
        "bands": ["B02", "B03", "B04", "B08", "B11", "B12"],
        "description_ar": "بصري 10م",
    },
    "sentinel1_sar": {
        "collection": "SENTINEL-1",
        "product_type": "GRD",
        "resolution": 10,
        "bands": ["VV", "VH"],
        "description_ar": "رادار SAR",
    },
    "sentinel3_thermal": {
        "collection": "SENTINEL-3",
        "product_type": "SL_2_LST",
        "resolution": 1000,
        "bands": ["LST"],
        "description_ar": "حراري OLCI",
    },
    "sentinel5p_gas": {
        "collection": "SENTINEL-5P",
        "product_type": "L2__CH4___",
        "resolution": 5500,
        "bands": ["CH4", "CO", "NO2"],
        "description_ar": "غازات",
    },
}


async def get_access_token() -> str | None:
    if not COPERNICUS_CLIENT_ID or not COPERNICUS_CLIENT_SECRET:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": COPERNICUS_CLIENT_ID,
                "client_secret": COPERNICUS_CLIENT_SECRET,
            },
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    return None


async def search_products(
    bbox: tuple[float, float, float, float],
    layer: str,
    date_from: str | None = None,
    date_to: str | None = None,
    max_cloud_cover: float = 20.0,
) -> list[dict[str, Any]]:
    """Search for satellite products in the Copernicus catalog."""
    config = LAYER_CONFIGS.get(layer)
    if not config:
        return []

    west, south, east, north = bbox
    footprint = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"

    filters = [
        f"Collection/Name eq '{config['collection']}'",
        f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}')",
    ]
    if date_from:
        filters.append(f"ContentDate/Start ge {date_from}T00:00:00.000Z")
    if date_to:
        filters.append(f"ContentDate/Start le {date_to}T23:59:59.999Z")
    if config["collection"] == "SENTINEL-2":
        filters.append(
            f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq "
            f"'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {max_cloud_cover})"
        )

    query = " and ".join(filters)
    url = f"{COPERNICUS_API_URL}/Products?$filter={query}&$top=10&$orderby=ContentDate/Start desc"

    token = await get_access_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json().get("value", [])
        except httpx.RequestError:
            pass
    return []


def simulate_sentinel2_data(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate Sentinel-2 multi-spectral data for demo purposes."""
    np.random.seed(42)
    bands = {}
    for band_name in ["B02", "B03", "B04", "B08", "B11", "B12"]:
        bands[band_name] = np.random.uniform(0, 1, (height, width)).astype(
            np.float32
        )
    return bands


def simulate_sentinel1_data(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate Sentinel-1 SAR data."""
    np.random.seed(43)
    return {
        "VV": np.random.uniform(-25, 0, (height, width)).astype(np.float32),
        "VH": np.random.uniform(-30, -5, (height, width)).astype(np.float32),
    }


def simulate_sentinel3_thermal(
    width: int = 64, height: int = 64
) -> dict[str, np.ndarray]:
    """Simulate Sentinel-3 thermal data."""
    np.random.seed(44)
    return {
        "LST": np.random.uniform(280, 330, (height, width)).astype(np.float32),
    }


def simulate_sentinel5p_gas(
    width: int = 32, height: int = 32
) -> dict[str, np.ndarray]:
    """Simulate Sentinel-5P gas concentration data."""
    np.random.seed(45)
    return {
        "CH4": np.random.uniform(1700, 1900, (height, width)).astype(np.float32),
        "CO": np.random.uniform(0, 200, (height, width)).astype(np.float32),
        "NO2": np.random.uniform(0, 100, (height, width)).astype(np.float32),
    }
