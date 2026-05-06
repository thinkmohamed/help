"""Connector base class & data structures."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SourceLayer:
    """A 2D raster layer normalised to the AOI grid."""

    source_id: str
    provider: str
    band_name: str
    array: np.ndarray  # 2D float32, normalised 0..1 (or signed for change/coh)
    units: str
    timestamp: str | None = None
    is_synthetic: bool = True


class BaseConnector:
    provider: str = "unknown"

    def __init__(self, **creds: Any) -> None:
        self.creds = {k: v for k, v in creds.items() if v is not None}

    def is_authenticated(self) -> bool:
        return bool(self.creds)

    def fetch(self, aoi: dict[str, Any], source_id: str, grid: tuple[int, int]) -> SourceLayer:
        raise NotImplementedError


def aoi_seed(aoi: dict[str, Any], salt: str) -> int:
    """Deterministic seed for synthetic generators."""
    s = f"{aoi.get('id','')}-{aoi.get('bbox', '')}-{salt}".encode()
    return int(hashlib.sha256(s).hexdigest()[:8], 16)


def synth_field(
    aoi: dict[str, Any],
    salt: str,
    grid: tuple[int, int],
    *,
    n_features: int = 6,
    smooth: int = 5,
) -> np.ndarray:
    """Generate a smooth, deterministic 2D field with embedded anomalies."""
    h, w = grid
    rng = np.random.default_rng(aoi_seed(aoi, salt))
    base = rng.standard_normal((h, w)).astype(np.float32)
    # box-blur
    for _ in range(smooth):
        base = (
            base
            + np.roll(base, 1, 0)
            + np.roll(base, -1, 0)
            + np.roll(base, 1, 1)
            + np.roll(base, -1, 1)
        ) / 5.0
    # Inject feature anomalies (Gaussian blobs)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for _ in range(n_features):
        cy = rng.uniform(h * 0.1, h * 0.9)
        cx = rng.uniform(w * 0.1, w * 0.9)
        sigma = rng.uniform(min(h, w) * 0.03, min(h, w) * 0.08)
        amp = rng.uniform(0.5, 1.5) * (1 if rng.random() > 0.4 else -1)
        base += amp * np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * sigma**2))
    # normalise to 0..1
    lo, hi = float(base.min()), float(base.max())
    if hi - lo < 1e-6:
        return np.zeros_like(base)
    return ((base - lo) / (hi - lo)).astype(np.float32)
