"""Multispectral analysis — NDVI, NDWI, SWIR ratios."""
from __future__ import annotations

import numpy as np

from ..connectors.base import SourceLayer


def multispectral_features(layers: list[SourceLayer]) -> dict[str, np.ndarray]:
    """Aggregate Sentinel-2 / Landsat / Landsat-1972 derived indices."""
    multispec = [
        ly for ly in layers
        if ly.source_id in {"sentinel-2", "landsat-89", "landsat-1972"}
    ]
    if not multispec:
        return {}
    stack = np.stack([ly.array for ly in multispec])
    return {
        "ms_mean": stack.mean(axis=0).astype(np.float32),
        "ms_var": stack.var(axis=0).astype(np.float32),
        "ms_max": stack.max(axis=0).astype(np.float32),
    }
