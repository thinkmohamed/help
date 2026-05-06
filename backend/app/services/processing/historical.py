"""Historical analysis module (6 decades).

التحليل التاريخي - Multi-temporal change detection spanning 6 decades
using CORONA (1960s-1970s), Landsat archive, and modern imagery.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def compute_change_magnitude(
    old_image: np.ndarray, new_image: np.ndarray
) -> np.ndarray:
    """Compute pixel-level change magnitude between two epochs."""
    h = min(old_image.shape[0], new_image.shape[0])
    w = min(old_image.shape[1], new_image.shape[1])
    old_r = _resize_array(old_image, h, w)
    new_r = _resize_array(new_image, h, w)
    return np.abs(new_r - old_r)


def compute_change_vector(
    old_bands: dict[str, np.ndarray], new_bands: dict[str, np.ndarray]
) -> np.ndarray:
    """Multi-band change vector analysis."""
    common_bands = set(old_bands.keys()) & set(new_bands.keys())
    if not common_bands:
        return np.zeros((1, 1), dtype=np.float32)

    target_h = min(
        min(old_bands[b].shape[0] for b in common_bands),
        min(new_bands[b].shape[0] for b in common_bands),
    )
    target_w = min(
        min(old_bands[b].shape[1] for b in common_bands),
        min(new_bands[b].shape[1] for b in common_bands),
    )

    change_sum = np.zeros((target_h, target_w), dtype=np.float32)
    for band in common_bands:
        old_r = _resize_array(old_bands[band], target_h, target_w)
        new_r = _resize_array(new_bands[band], target_h, target_w)
        change_sum += (new_r - old_r) ** 2

    return np.sqrt(change_sum / len(common_bands))


def detect_disappeared_features(
    old_image: np.ndarray, new_image: np.ndarray, threshold: float = 0.3
) -> np.ndarray:
    """Detect features present in old imagery but absent in modern imagery.

    Useful for finding destroyed archaeological sites.
    """
    change = compute_change_magnitude(old_image, new_image)
    change_norm = change / (change.max() + 1e-10)
    return (change_norm > threshold).astype(np.float32) * change_norm


def detect_excavation_activity(
    images_timeline: list[np.ndarray],
) -> np.ndarray:
    """Detect progressive excavation activity across a timeline."""
    if len(images_timeline) < 2:
        h, w = images_timeline[0].shape if images_timeline else (256, 256)
        return np.zeros((h, w), dtype=np.float32)

    target_h = min(img.shape[0] for img in images_timeline)
    target_w = min(img.shape[1] for img in images_timeline)

    cumulative_change = np.zeros((target_h, target_w), dtype=np.float32)
    for i in range(1, len(images_timeline)):
        prev = _resize_array(images_timeline[i - 1], target_h, target_w)
        curr = _resize_array(images_timeline[i], target_h, target_w)
        cumulative_change += np.abs(curr - prev)

    return cumulative_change / len(images_timeline)


def compute_persistence_map(
    images_timeline: list[np.ndarray], threshold: float = 0.1
) -> np.ndarray:
    """Identify features that persist across all time periods.

    Persistent anomalies likely represent permanent structures.
    """
    if not images_timeline:
        return np.zeros((256, 256), dtype=np.float32)

    target_h = min(img.shape[0] for img in images_timeline)
    target_w = min(img.shape[1] for img in images_timeline)

    resized = [_resize_array(img, target_h, target_w) for img in images_timeline]
    stacked = np.stack(resized, axis=0)
    temporal_std = np.std(stacked, axis=0)
    temporal_mean = np.mean(stacked, axis=0)

    persistence = np.where(temporal_std < threshold, temporal_mean, 0)
    return persistence.astype(np.float32)


def _resize_array(arr: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
    """Simple resize using scipy zoom."""
    if arr.shape[0] == target_h and arr.shape[1] == target_w:
        return arr
    zoom_h = target_h / arr.shape[0]
    zoom_w = target_w / arr.shape[1]
    return ndimage.zoom(arr, (zoom_h, zoom_w), order=1)


def run_historical_analysis(
    corona_data: dict[str, np.ndarray] | None = None,
    archive_data: dict[str, np.ndarray] | None = None,
    modern_data: dict[str, np.ndarray] | None = None,
) -> dict[str, np.ndarray]:
    """Run full historical analysis pipeline spanning 6 decades."""
    results: dict[str, np.ndarray] = {}

    timeline_images: list[np.ndarray] = []

    if corona_data and "PAN" in corona_data:
        timeline_images.append(corona_data["PAN"])

    if archive_data:
        first_band = next(iter(archive_data.values()))
        timeline_images.append(first_band)

    if modern_data:
        first_band = next(iter(modern_data.values()))
        timeline_images.append(first_band)

    if len(timeline_images) >= 2:
        results["change_magnitude"] = compute_change_magnitude(
            timeline_images[0], timeline_images[-1]
        )
        results["disappeared_features"] = detect_disappeared_features(
            timeline_images[0], timeline_images[-1]
        )

    if len(timeline_images) >= 2:
        results["excavation_activity"] = detect_excavation_activity(timeline_images)
        results["persistence_map"] = compute_persistence_map(timeline_images)

    return results
