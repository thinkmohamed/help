"""60-year historical change detection — CORONA vs modern Landsat/Sentinel."""
from __future__ import annotations

import numpy as np

from ..connectors.base import SourceLayer


def historical_features(layers: list[SourceLayer]) -> dict[str, np.ndarray]:
    corona = next((ly for ly in layers if ly.source_id == "corona-1960"), None)
    landsat72 = next((ly for ly in layers if ly.source_id == "landsat-1972"), None)
    modern_candidates = [
        ly for ly in layers if ly.source_id in {"sentinel-2", "landsat-89"}
    ]
    if not modern_candidates or (corona is None and landsat72 is None):
        return {}
    modern = np.mean(
        np.stack([ly.array for ly in modern_candidates]), axis=0
    ).astype(np.float32)
    out: dict[str, np.ndarray] = {"modern_ref": modern}
    if corona is not None:
        out["change_corona_modern"] = np.abs(corona.array - modern).astype(np.float32)
    if landsat72 is not None:
        out["change_l72_modern"] = np.abs(landsat72.array - modern).astype(np.float32)
    if "change_corona_modern" in out and "change_l72_modern" in out:
        out["change_combined"] = (
            (out["change_corona_modern"] + out["change_l72_modern"]) / 2.0
        ).astype(np.float32)
    return out
