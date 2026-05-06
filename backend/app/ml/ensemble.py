"""Ensemble soft-voting across U-Net / RF / IsoForest, calibrated per target.

Each model contributes evidence for each of the 5 target classes via a calibrated
weight matrix. Weights reflect the relative strength of each model on each class:
- U-Net (segmentation) — strong evidence for spatially extended anomalies
  (Modern excavations, Ancient ruins, Groundwater).
- Random Forest — multi-class classifier already aligned with the 5 targets.
- Isolation Forest — generic anomaly detector, weighted higher for rarer classes
  (Underground voids, Buried metals).

The output is a (H, W, n_targets) probability volume.
"""
from __future__ import annotations

import numpy as np

from ..outputs.targets import TARGETS

# Rows = [unet_seg, rf_per_class, iso_anomaly]; columns = TARGETS order
ENSEMBLE_WEIGHTS = np.array(
    [
        # voids, metals, ruins, excavations, groundwater
        [0.20, 0.20, 0.40, 0.50, 0.30],  # U-Net
        [0.50, 0.50, 0.45, 0.40, 0.50],  # Random Forest
        [0.30, 0.30, 0.15, 0.10, 0.20],  # Isolation Forest
    ],
    dtype=np.float32,
)


def ensemble_vote(
    unet_map: np.ndarray, rf_volume: np.ndarray, iso_map: np.ndarray
) -> np.ndarray:
    """Combine model outputs into per-target probability volume."""
    n_targets = len(TARGETS)
    if rf_volume.size == 0:
        return np.zeros((0, 0, n_targets), dtype=np.float32)
    h, w, _ = rf_volume.shape
    out = np.zeros((h, w, n_targets), dtype=np.float32)
    weights = ENSEMBLE_WEIGHTS / ENSEMBLE_WEIGHTS.sum(axis=0, keepdims=True)
    for t in range(n_targets):
        out[..., t] = (
            weights[0, t] * unet_map
            + weights[1, t] * rf_volume[..., t]
            + weights[2, t] * iso_map
        )
    # Clip to [0, 1]
    return np.clip(out, 0.0, 1.0).astype(np.float32)
