"""3D morphology — TPI, slope proxy, micro-relief from DEMs + CORONA stereo."""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from ..connectors.base import SourceLayer


def _tpi(arr: np.ndarray, radius: int = 5) -> np.ndarray:
    """Topographic Position Index = z - mean(z in neighbourhood)."""
    smoothed = ndi.uniform_filter(arr, size=radius * 2 + 1)
    return (arr - smoothed).astype(np.float32)


def _slope(arr: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(arr)
    return np.hypot(gx, gy).astype(np.float32)


def morphology_features(layers: list[SourceLayer]) -> dict[str, np.ndarray]:
    dems = [ly for ly in layers if ly.source_id in {"srtm", "aster-gdem", "corona-stereo"}]
    if not dems:
        return {}
    elev = np.mean(np.stack([dem.array for dem in dems]), axis=0).astype(np.float32)
    return {
        "elevation": elev,
        "tpi_5": _tpi(elev, 5),
        "tpi_15": _tpi(elev, 15),
        "slope": _slope(elev),
        "micro_relief": np.abs(_tpi(elev, 3)).astype(np.float32),
    }
