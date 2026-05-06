"""Data Fusion Engine.

محرك دمج البيانات - Combines multi-source, multi-temporal analysis results
into unified feature matrices for ML classification.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def normalize_layer(data: np.ndarray) -> np.ndarray:
    """Min-max normalize a layer to [0, 1]."""
    dmin = np.nanmin(data)
    dmax = np.nanmax(data)
    if dmax - dmin < 1e-10:
        return np.zeros_like(data)
    return (data - dmin) / (dmax - dmin)


def resample_to_target(
    data: np.ndarray, target_h: int, target_w: int
) -> np.ndarray:
    """Resample a layer to a target resolution."""
    if data.shape[0] == target_h and data.shape[1] == target_w:
        return data
    zoom_h = target_h / data.shape[0]
    zoom_w = target_w / data.shape[1]
    return ndimage.zoom(data, (zoom_h, zoom_w), order=1)


def fuse_analysis_results(
    spectral_results: dict[str, np.ndarray] | None = None,
    radar_results: dict[str, np.ndarray] | None = None,
    thermal_results: dict[str, np.ndarray] | None = None,
    geomorphological_results: dict[str, np.ndarray] | None = None,
    historical_results: dict[str, np.ndarray] | None = None,
    target_size: tuple[int, int] = (256, 256),
) -> np.ndarray:
    """Fuse all analysis results into a multi-channel feature matrix.

    Returns:
        Feature matrix of shape (height, width, n_features) normalized to [0, 1].
    """
    target_h, target_w = target_size
    layers: list[np.ndarray] = []

    all_results = [
        spectral_results,
        radar_results,
        thermal_results,
        geomorphological_results,
        historical_results,
    ]

    for result_dict in all_results:
        if result_dict is None:
            continue
        for _name, data in result_dict.items():
            resampled = resample_to_target(data, target_h, target_w)
            normalized = normalize_layer(resampled)
            layers.append(normalized)

    if not layers:
        return np.zeros((target_h, target_w, 1), dtype=np.float32)

    return np.stack(layers, axis=-1).astype(np.float32)


def compute_feature_importance(
    fused_data: np.ndarray,
    feature_names: list[str],
) -> dict[str, float]:
    """Compute relative importance of each feature layer based on variance."""
    importances: dict[str, float] = {}
    n_features = fused_data.shape[2]
    total_var = 0.0

    variances = []
    for i in range(min(n_features, len(feature_names))):
        var = float(np.nanvar(fused_data[:, :, i]))
        variances.append(var)
        total_var += var

    if total_var < 1e-10:
        total_var = 1.0

    for i, name in enumerate(feature_names[:n_features]):
        importances[name] = variances[i] / total_var

    return importances


def extract_feature_vectors(
    fused_data: np.ndarray,
) -> np.ndarray:
    """Reshape fused data into feature vectors for ML models.

    Returns:
        Array of shape (n_pixels, n_features).
    """
    h, w, n_features = fused_data.shape
    return fused_data.reshape(-1, n_features)
