"""CORONA Atlas connector.

Provides access to:
- CORONA 1960-1972 (1.8m resolution historical imagery)
- Stereo 3D (stereoscopic reconstruction)
"""

from __future__ import annotations

import numpy as np


LAYER_CONFIGS = {
    "corona_historical": {
        "collection": "CORONA",
        "resolution": 1.8,
        "bands": ["PAN"],
        "description_ar": "صور تاريخية 1960-1972",
    },
    "stereo_3d": {
        "collection": "CORONA_STEREO",
        "resolution": 2.0,
        "bands": ["LEFT", "RIGHT", "DSM"],
        "description_ar": "تجسيم ثلاثي الأبعاد",
    },
}


def simulate_corona_historical(
    width: int = 512, height: int = 512
) -> dict[str, np.ndarray]:
    """Simulate CORONA historical panchromatic imagery."""
    np.random.seed(70)
    base = np.random.uniform(0, 1, (height, width)).astype(np.float32)
    # Add features simulating archaeological sites
    for _ in range(5):
        cx, cy = np.random.randint(50, width - 50), np.random.randint(50, height - 50)
        size = np.random.randint(10, 30)
        yy, xx = np.ogrid[
            max(0, cy - size) : min(height, cy + size),
            max(0, cx - size) : min(width, cx + size),
        ]
        mask = ((xx - cx) ** 2 + (yy - cy) ** 2) < size**2
        base[
            max(0, cy - size) : min(height, cy + size),
            max(0, cx - size) : min(width, cx + size),
        ][mask] *= 0.6
    return {"PAN": base}


def simulate_stereo_3d(
    width: int = 256, height: int = 256
) -> dict[str, np.ndarray]:
    """Simulate stereo 3D reconstruction from CORONA pairs."""
    np.random.seed(71)
    x = np.linspace(0, 4 * np.pi, width)
    y = np.linspace(0, 4 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    dsm = (
        100
        + 50 * np.sin(xx) * np.cos(yy)
        + 10 * np.random.randn(height, width)
    ).astype(np.float32)
    return {
        "LEFT": np.random.uniform(0, 1, (height, width)).astype(np.float32),
        "RIGHT": np.random.uniform(0, 1, (height, width)).astype(np.float32),
        "DSM": dsm,
    }
