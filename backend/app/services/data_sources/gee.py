"""Google Earth Engine connector.

Provides access to:
- SRTM DEM 30m
- ALOS PALSAR (L-band radar)
- MODIS (daily thermal)
- InSAR Coherence
"""

from __future__ import annotations

import numpy as np


LAYER_CONFIGS = {
    "srtm_dem": {
        "collection": "USGS/SRTMGL1_003",
        "resolution": 30,
        "bands": ["elevation"],
        "description_ar": "نموذج ارتفاعات رقمي 30م",
    },
    "alos_palsar": {
        "collection": "JAXA/ALOS/PALSAR/YEARLY/SAR",
        "resolution": 25,
        "bands": ["HH", "HV"],
        "description_ar": "رادار L-band",
    },
    "modis_thermal": {
        "collection": "MODIS/061/MOD11A1",
        "resolution": 1000,
        "bands": ["LST_Day_1km", "LST_Night_1km"],
        "description_ar": "حراري يومي",
    },
    "insar_coherence": {
        "collection": "COPERNICUS/S1_GRD",
        "resolution": 10,
        "bands": ["coherence"],
        "description_ar": "تماسك InSAR",
    },
}


def simulate_srtm_dem(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate SRTM DEM data with realistic terrain."""
    np.random.seed(60)
    x = np.linspace(0, 6 * np.pi, width)
    y = np.linspace(0, 6 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    elevation = (
        300
        + 150 * np.sin(xx / 3) * np.cos(yy / 2)
        + 80 * np.sin(xx * 2) * np.sin(yy * 1.5)
        + 30 * np.random.randn(height, width)
    )
    return {"elevation": elevation.astype(np.float32)}


def simulate_alos_palsar(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate ALOS PALSAR L-band radar data."""
    np.random.seed(61)
    return {
        "HH": np.random.uniform(-30, 0, (height, width)).astype(np.float32),
        "HV": np.random.uniform(-35, -5, (height, width)).astype(np.float32),
    }


def simulate_modis_thermal(
    width: int = 64, height: int = 64
) -> dict[str, np.ndarray]:
    """Simulate MODIS daily thermal data."""
    np.random.seed(62)
    base_temp = 300 + 15 * np.random.randn(height, width)
    return {
        "LST_Day_1km": base_temp.astype(np.float32),
        "LST_Night_1km": (base_temp - 15 + 3 * np.random.randn(height, width)).astype(
            np.float32
        ),
    }


def simulate_insar_coherence(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate InSAR coherence data."""
    np.random.seed(63)
    coherence = np.random.uniform(0, 1, (height, width)).astype(np.float32)
    # Add some spatial structure
    x = np.linspace(0, 4 * np.pi, width)
    y = np.linspace(0, 4 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    coherence = np.clip(
        coherence * 0.5 + 0.5 * np.abs(np.sin(xx) * np.cos(yy)), 0, 1
    )
    return {"coherence": coherence.astype(np.float32)}
