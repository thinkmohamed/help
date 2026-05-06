"""Ensemble Voting System.

نظام التصويت Ensemble - Combines predictions from multiple ML models
using weighted voting to produce robust final classifications.
"""

from __future__ import annotations

import numpy as np


CATEGORY_NAMES = [
    "groundwater",
    "excavation",
    "ancient_ruins",
    "dissolved_minerals",
    "underground_voids",
]

CATEGORY_NAMES_AR = [
    "مياه جوفية",
    "حفر تنقيب حديثة",
    "آثار قديمة",
    "معادن مذابة",
    "فراغات تحت الأرض",
]

DEFAULT_WEIGHTS = {
    "unet": 0.30,
    "random_forest": 0.30,
    "isolation_forest": 0.25,
    "dbscan": 0.15,
}


def weighted_vote(
    model_predictions: dict[str, np.ndarray],
    weights: dict[str, float] | None = None,
) -> np.ndarray:
    """Combine model predictions using weighted voting.

    Args:
        model_predictions: Dict mapping model name to probability maps
                          of shape (height, width, n_classes)
        weights: Optional weight for each model

    Returns:
        Combined probability map of shape (height, width, n_classes)
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    all_names = list(model_predictions.keys())
    if not all_names:
        return np.zeros((256, 256, len(CATEGORY_NAMES)), dtype=np.float32)

    ref = model_predictions[all_names[0]]
    h, w, n_classes = ref.shape
    combined = np.zeros((h, w, n_classes), dtype=np.float32)
    total_weight = 0.0

    for name, preds in model_predictions.items():
        weight = weights.get(name, 1.0 / len(model_predictions))
        if preds.shape != (h, w, n_classes):
            from scipy import ndimage

            resized = np.zeros((h, w, n_classes), dtype=np.float32)
            for c in range(n_classes):
                resized[:, :, c] = ndimage.zoom(
                    preds[:, :, c],
                    (h / preds.shape[0], w / preds.shape[1]),
                    order=1,
                )
            preds = resized
        combined += weight * preds
        total_weight += weight

    if total_weight > 0:
        combined /= total_weight

    return combined


def apply_threshold(
    probability_map: np.ndarray,
    threshold: float = 0.5,
) -> np.ndarray:
    """Apply confidence threshold to produce binary detection maps."""
    return (probability_map > threshold).astype(np.float32) * probability_map


def get_final_classifications(
    probability_map: np.ndarray,
    threshold: float = 0.3,
) -> dict:
    """Extract final detection results from ensemble probability map.

    Returns structured detection results for each category.
    """
    h, w, n_classes = probability_map.shape
    results = {
        "categories": [],
        "summary": {},
        "total_detections": 0,
    }

    for c in range(min(n_classes, len(CATEGORY_NAMES))):
        class_map = probability_map[:, :, c]
        high_prob_mask = class_map > threshold

        n_pixels = int(np.sum(high_prob_mask))
        if n_pixels == 0:
            continue

        mean_prob = float(np.mean(class_map[high_prob_mask]))
        max_prob = float(np.max(class_map))

        max_loc = np.unravel_index(np.argmax(class_map), class_map.shape)
        center_y = float(max_loc[0]) / h
        center_x = float(max_loc[1]) / w

        category_result = {
            "category": CATEGORY_NAMES[c],
            "category_ar": CATEGORY_NAMES_AR[c],
            "n_pixels": n_pixels,
            "area_fraction": n_pixels / (h * w),
            "mean_probability": mean_prob,
            "max_probability": max_prob,
            "peak_location": {"y": center_y, "x": center_x},
            "confidence": "high" if max_prob > 0.7 else "medium" if max_prob > 0.5 else "low",
        }
        results["categories"].append(category_result)
        results["total_detections"] += 1

    results["summary"] = {
        "total_categories_detected": results["total_detections"],
        "map_size": {"height": h, "width": w},
        "threshold_used": threshold,
    }

    return results
