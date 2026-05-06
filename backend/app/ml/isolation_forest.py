"""Isolation Forest — unsupervised anomaly score per pixel."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest


def isolation_forest_anomaly(stack: np.ndarray) -> np.ndarray:
    """Return (H, W) anomaly score in [0, 1] (higher = more anomalous)."""
    if stack.size == 0:
        return np.zeros((0, 0), dtype=np.float32)
    h, w, c = stack.shape
    flat = stack.reshape(-1, c)
    # Fit on a sub-sample for speed
    rng = np.random.default_rng(42)
    n = flat.shape[0]
    sample_idx = rng.choice(n, size=min(n, 5000), replace=False)
    iso = IsolationForest(
        n_estimators=80, contamination=0.1, random_state=42, n_jobs=-1
    )
    iso.fit(flat[sample_idx])
    raw = -iso.score_samples(flat)  # higher = more anomalous
    lo, hi = float(raw.min()), float(raw.max())
    if hi - lo < 1e-6:
        return np.zeros((h, w), dtype=np.float32)
    norm = (raw - lo) / (hi - lo)
    return norm.reshape(h, w).astype(np.float32)
