"""Random Forest multi-class classifier.

متعدد الفئات Random Forest - Ensemble tree-based classification
for multi-category detection from fused satellite features.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier


def create_training_data(
    n_samples: int = 5000, n_features: int = 10, n_classes: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data mimicking satellite feature patterns.

    Each class has distinct feature signatures:
    0: groundwater - high thermal inertia, low NDVI, valley position
    1: excavation - high change magnitude, surface roughness changes
    2: ancient_ruins - linear features, spectral anomalies, persistence
    3: dissolved_minerals - high clay/iron ratios, spectral signatures
    4: underground_voids - thermal anomalies, coherence changes, subsurface radar
    """
    np.random.seed(200)
    samples_per_class = n_samples // n_classes
    X_list = []
    y_list = []

    class_profiles = {
        0: {"mean": [0.2, 0.8, 0.7, 0.3, 0.1, 0.6, 0.8, 0.2, 0.5, 0.3], "std": 0.15},
        1: {"mean": [0.3, 0.4, 0.3, 0.5, 0.8, 0.2, 0.3, 0.7, 0.6, 0.4], "std": 0.15},
        2: {"mean": [0.5, 0.3, 0.4, 0.7, 0.6, 0.8, 0.5, 0.5, 0.7, 0.8], "std": 0.12},
        3: {"mean": [0.7, 0.6, 0.3, 0.8, 0.2, 0.4, 0.3, 0.3, 0.8, 0.5], "std": 0.15},
        4: {"mean": [0.4, 0.7, 0.8, 0.2, 0.3, 0.5, 0.7, 0.4, 0.3, 0.6], "std": 0.13},
    }

    for cls in range(n_classes):
        profile = class_profiles[cls]
        mean = np.array(profile["mean"][:n_features])
        if len(mean) < n_features:
            mean = np.pad(mean, (0, n_features - len(mean)), constant_values=0.5)
        X_cls = np.random.normal(
            loc=mean, scale=profile["std"], size=(samples_per_class, n_features)
        )
        X_cls = np.clip(X_cls, 0, 1)
        X_list.append(X_cls)
        y_list.append(np.full(samples_per_class, cls))

    X = np.vstack(X_list).astype(np.float32)
    y = np.concatenate(y_list).astype(np.int32)

    shuffle_idx = np.random.permutation(len(X))
    return X[shuffle_idx], y[shuffle_idx]


def train_random_forest(
    n_features: int = 10, n_classes: int = 5
) -> RandomForestClassifier:
    """Train a Random Forest classifier on synthetic satellite data."""
    X_train, y_train = create_training_data(
        n_samples=5000, n_features=n_features, n_classes=n_classes
    )
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    return clf


def run_random_forest_classification(
    fused_data: np.ndarray, n_classes: int = 5
) -> np.ndarray:
    """Run Random Forest classification on fused satellite data.

    Returns probability maps for each class.
    """
    h, w, n_feat = fused_data.shape
    feature_vectors = fused_data.reshape(-1, n_feat)

    clf = train_random_forest(n_features=n_feat, n_classes=n_classes)
    probabilities = clf.predict_proba(feature_vectors)

    return probabilities.reshape(h, w, n_classes).astype(np.float32)
