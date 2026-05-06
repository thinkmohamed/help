"""Thermal analysis — diurnal LST anomalies + thermal inertia proxy."""
from __future__ import annotations

import numpy as np

from ..connectors.base import SourceLayer


def thermal_features(layers: list[SourceLayer]) -> dict[str, np.ndarray]:
    aster = next((ly for ly in layers if ly.source_id == "aster"), None)
    s3 = next((ly for ly in layers if ly.source_id == "sentinel-3"), None)
    modis = next((ly for ly in layers if ly.source_id == "modis"), None)
    out: dict[str, np.ndarray] = {}
    if aster is not None:
        out["thermal_aster"] = aster.array.astype(np.float32)
    if s3 is not None:
        out["thermal_s3"] = s3.array.astype(np.float32)
    if modis is not None:
        # treat MODIS as proxy for diurnal amplitude (high amplitude = thin/hard
        # surface, low amplitude can indicate void / metal / water)
        out["thermal_diurnal"] = modis.array.astype(np.float32)
        out["thermal_inertia_anomaly"] = (1.0 - modis.array).astype(np.float32)
    return out
