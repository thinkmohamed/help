"""Multi-frequency radar analysis module.

التحليل الراداري متعدد التردد - SAR data processing for subsurface
feature detection using Sentinel-1 and ALOS PALSAR.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def compute_backscatter_ratio(
    vv: np.ndarray, vh: np.ndarray
) -> np.ndarray:
    """VV/VH backscatter ratio for surface characterization."""
    vh_safe = vh.copy()
    vh_safe[vh_safe == 0] = 1e-10
    return vv / vh_safe


def compute_radar_roughness(data: np.ndarray, window: int = 5) -> np.ndarray:
    """Surface roughness estimation from SAR backscatter variance."""
    mean = ndimage.uniform_filter(data, size=window)
    sq_mean = ndimage.uniform_filter(data**2, size=window)
    variance = sq_mean - mean**2
    return np.sqrt(np.maximum(variance, 0))


def compute_polarimetric_entropy(
    vv: np.ndarray, vh: np.ndarray
) -> np.ndarray:
    """Simplified polarimetric entropy for scattering mechanism classification."""
    total = np.abs(vv) + np.abs(vh)
    total[total == 0] = 1e-10
    p1 = np.abs(vv) / total
    p2 = np.abs(vh) / total
    p1 = np.clip(p1, 1e-10, 1)
    p2 = np.clip(p2, 1e-10, 1)
    return -(p1 * np.log2(p1) + p2 * np.log2(p2))


def compute_coherence_change(
    coh_before: np.ndarray, coh_after: np.ndarray
) -> np.ndarray:
    """InSAR coherence change detection for recent disturbances."""
    return coh_after - coh_before


def detect_subsurface_features(
    l_band_hh: np.ndarray, l_band_hv: np.ndarray
) -> np.ndarray:
    """Detect potential subsurface features using L-band penetration.

    L-band SAR can penetrate dry soil up to ~2m, revealing buried structures.
    """
    ratio = compute_backscatter_ratio(l_band_hh, l_band_hv)
    roughness = compute_radar_roughness(l_band_hh)

    ratio_norm = (ratio - ratio.min()) / (ratio.max() - ratio.min() + 1e-10)
    rough_norm = (roughness - roughness.min()) / (
        roughness.max() - roughness.min() + 1e-10
    )

    return 0.6 * ratio_norm + 0.4 * rough_norm


def run_radar_analysis(
    sar_data: dict[str, np.ndarray],
    l_band_data: dict[str, np.ndarray] | None = None,
    coherence_data: dict[str, np.ndarray] | None = None,
) -> dict[str, np.ndarray]:
    """Run full radar analysis pipeline."""
    results: dict[str, np.ndarray] = {}

    vv = sar_data.get("VV")
    vh = sar_data.get("VH")

    if vv is not None and vh is not None:
        results["backscatter_ratio"] = compute_backscatter_ratio(vv, vh)
        results["polarimetric_entropy"] = compute_polarimetric_entropy(vv, vh)
        results["surface_roughness_vv"] = compute_radar_roughness(vv)
        results["surface_roughness_vh"] = compute_radar_roughness(vh)

    if l_band_data:
        hh = l_band_data.get("HH")
        hv = l_band_data.get("HV")
        if hh is not None and hv is not None:
            results["subsurface_features"] = detect_subsurface_features(hh, hv)
            results["l_band_roughness"] = compute_radar_roughness(hh)

    if coherence_data and "coherence" in coherence_data:
        results["coherence"] = coherence_data["coherence"]

    return results
