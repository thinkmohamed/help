"""Isolation Forest anomaly detection.

للشذوذات Isolation Forest - Unsupervised anomaly detection to identify
unusual spectral/spatial patterns that may indicate hidden features.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest


def run_isolation_forest(
    fused_data: np.ndarray,
    contamination: float = 0.05,
) -> np.ndarray:
    """Run Isolation Forest anomaly detection on fused data.

    Args:
        fused_data: Shape (height, width, n_features)
        contamination: Expected proportion of anomalies

    Returns:
        Anomaly score map of shape (height, width) in [0, 1],
        where higher values indicate more anomalous pixels.
    """
    h, w, n_feat = fused_data.shape
    feature_vectors = fused_data.reshape(-1, n_feat)

    n_samples = feature_vectors.shape[0]
    max_samples = min(n_samples, 10000)

    if n_samples > max_samples:
        indices = np.random.RandomState(42).choice(
            n_samples, max_samples, replace=False
        )
        train_data = feature_vectors[indices]
    else:
        train_data = feature_vectors

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        max_samples=min(max_samples, 256),
        random_state=42,
        n_jobs=-1,
    )
    model.fit(train_data)

    scores = model.decision_function(feature_vectors)

    anomaly_scores = -scores
    anomaly_scores = (anomaly_scores - anomaly_scores.min()) / (
        anomaly_scores.max() - anomaly_scores.min() + 1e-10
    )

    return anomaly_scores.reshape(h, w).astype(np.float32)


def classify_anomalies(
    anomaly_map: np.ndarray,
    fused_data: np.ndarray,
    n_classes: int = 5,
) -> np.ndarray:
    """Convert anomaly scores to class probabilities.

    Uses the anomaly map combined with feature signatures to estimate
    which category each anomalous pixel likely belongs to.
    """
    h, w = anomaly_map.shape
    n_feat = fused_data.shape[2]
    class_probs = np.zeros((h, w, n_classes), dtype=np.float32)

    feature_ranges = [
        (0, min(2, n_feat)),     # groundwater: first 2 features
        (min(2, n_feat), min(4, n_feat)),  # excavation
        (min(4, n_feat), min(6, n_feat)),  # ancient ruins
        (min(6, n_feat), min(8, n_feat)),  # minerals
        (min(8, n_feat), n_feat),          # voids
    ]

    for c in range(n_classes):
        start, end = feature_ranges[c]
        if start < end:
            feature_intensity = np.mean(fused_data[:, :, start:end], axis=2)
        else:
            feature_intensity = np.mean(fused_data, axis=2)
        class_probs[:, :, c] = anomaly_map * feature_intensity

    total = np.sum(class_probs, axis=2, keepdims=True)
    total[total == 0] = 1e-10
    class_probs /= total

    return class_probs
