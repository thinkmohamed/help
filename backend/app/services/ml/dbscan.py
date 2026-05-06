"""DBSCAN spatial clustering.

التجميع المكاني DBSCAN - Density-based spatial clustering to group
detected anomalies into meaningful spatial clusters.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN


def run_spatial_clustering(
    anomaly_map: np.ndarray,
    threshold: float = 0.5,
    eps: float = 5.0,
    min_samples: int = 10,
) -> tuple[np.ndarray, list[dict]]:
    """Run DBSCAN clustering on anomalous pixels.

    Args:
        anomaly_map: 2D anomaly score map
        threshold: minimum anomaly score to consider
        eps: DBSCAN epsilon (max distance between samples)
        min_samples: minimum cluster size

    Returns:
        Tuple of (cluster_map, cluster_info)
        - cluster_map: same shape as anomaly_map with cluster labels
        - cluster_info: list of dicts with cluster statistics
    """
    h, w = anomaly_map.shape
    cluster_map = np.full((h, w), -1, dtype=np.int32)

    anomalous_pixels = np.where(anomaly_map > threshold)
    if len(anomalous_pixels[0]) == 0:
        return cluster_map, []

    coords = np.column_stack([anomalous_pixels[0], anomalous_pixels[1]])
    scores = anomaly_map[anomalous_pixels]

    max_points = 50000
    if len(coords) > max_points:
        indices = np.random.RandomState(42).choice(
            len(coords), max_points, replace=False
        )
        coords = coords[indices]
        scores = scores[indices]
        anomalous_pixels = (coords[:, 0], coords[:, 1])

    db = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean", n_jobs=-1)
    labels = db.fit_predict(coords)

    cluster_map[anomalous_pixels] = labels

    cluster_info = []
    unique_labels = set(labels)
    unique_labels.discard(-1)

    for label in sorted(unique_labels):
        mask = labels == label
        cluster_coords = coords[mask]
        cluster_scores = scores[mask]

        center_y = float(np.mean(cluster_coords[:, 0]))
        center_x = float(np.mean(cluster_coords[:, 1]))

        cluster_info.append({
            "cluster_id": int(label),
            "center": [center_y / h, center_x / w],
            "n_pixels": int(np.sum(mask)),
            "mean_score": float(np.mean(cluster_scores)),
            "max_score": float(np.max(cluster_scores)),
            "area_fraction": float(np.sum(mask)) / (h * w),
            "bbox": {
                "min_y": float(np.min(cluster_coords[:, 0]) / h),
                "min_x": float(np.min(cluster_coords[:, 1]) / w),
                "max_y": float(np.max(cluster_coords[:, 0]) / h),
                "max_x": float(np.max(cluster_coords[:, 1]) / w),
            },
        })

    return cluster_map, cluster_info


def assign_clusters_to_categories(
    cluster_map: np.ndarray,
    cluster_info: list[dict],
    class_probs: np.ndarray,
    n_classes: int = 5,
) -> list[dict]:
    """Assign detected clusters to detection categories based on class probabilities."""
    category_names = [
        "groundwater",
        "excavation",
        "ancient_ruins",
        "dissolved_minerals",
        "underground_voids",
    ]
    category_names_ar = [
        "مياه جوفية",
        "حفر تنقيب حديثة",
        "آثار قديمة",
        "معادن مذابة",
        "فراغات تحت الأرض",
    ]

    for info in cluster_info:
        cluster_id = info["cluster_id"]
        mask = cluster_map == cluster_id

        if not np.any(mask):
            continue

        mean_probs = []
        for c in range(min(n_classes, class_probs.shape[2])):
            mean_probs.append(float(np.mean(class_probs[:, :, c][mask])))

        best_class = int(np.argmax(mean_probs))
        info["category"] = category_names[best_class]
        info["category_ar"] = category_names_ar[best_class]
        info["probability"] = mean_probs[best_class]
        info["class_probabilities"] = {
            category_names[i]: mean_probs[i]
            for i in range(len(mean_probs))
        }

    return cluster_info
