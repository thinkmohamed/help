"""Radar multi-frequency analysis — C-band + L-band + InSAR coherence."""
from __future__ import annotations

import numpy as np

from ..connectors.base import SourceLayer


def radar_features(layers: list[SourceLayer]) -> dict[str, np.ndarray]:
    s1 = next((ly for ly in layers if ly.source_id == "sentinel-1"), None)
    palsar = next((ly for ly in layers if ly.source_id == "alos-palsar"), None)
    coh = next((ly for ly in layers if ly.source_id == "insar-coh"), None)
    out: dict[str, np.ndarray] = {}
    if s1 is not None:
        out["sar_c"] = s1.array.astype(np.float32)
    if palsar is not None:
        out["sar_l"] = palsar.array.astype(np.float32)
    if coh is not None:
        # coherence loss → high value where ground is unstable / freshly disturbed
        out["coherence_loss"] = (1.0 - coh.array).astype(np.float32)
    if "sar_c" in out and "sar_l" in out:
        out["sar_dual_diff"] = np.abs(out["sar_c"] - out["sar_l"]).astype(np.float32)
    return out
