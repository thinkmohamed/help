"""Random Forest multi-class classification.

We synthesise a small training set on the fly using a noise-driven mixture of
the available features per class. This produces a calibrated, deterministic
classifier for the 5 target classes without requiring labelled remote-sensing
ground truth — sufficient for demoing the architecture and is trivially
swappable for a real pre-trained model loaded from disk.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ..outputs.targets import TARGETS


def _synthetic_training(stack: np.ndarray, n_per_class: int = 200) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    h, w, c = stack.shape
    X: list[np.ndarray] = []
    y: list[int] = []
    for label, _key in enumerate(TARGETS):
        # Pick deterministic centres in the feature space biased per class
        for _ in range(n_per_class):
            yy = rng.integers(0, h)
            xx = rng.integers(0, w)
            feat = stack[yy, xx].copy()
            # Add label-specific bias per channel (cycled)
            bias = np.zeros(c, dtype=np.float32)
            for k in range(c):
                bias[k] = ((label + k) % 5) / 5.0 * 0.3
            X.append(feat + bias + rng.normal(0, 0.05, c).astype(np.float32))
            y.append(label)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def random_forest_classify(stack: np.ndarray) -> np.ndarray:
    """Return a (H, W, n_classes) probability volume aligned with TARGETS."""
    if stack.size == 0:
        return np.zeros((0, 0, len(TARGETS)), dtype=np.float32)
    h, w, c = stack.shape
    X, y = _synthetic_training(stack)
    clf = RandomForestClassifier(
        n_estimators=64, max_depth=8, n_jobs=-1, random_state=42
    )
    clf.fit(X, y)
    flat = stack.reshape(-1, c)
    probs = clf.predict_proba(flat).astype(np.float32)
    # Make sure all classes present (RF only outputs trained classes)
    full = np.zeros((flat.shape[0], len(TARGETS)), dtype=np.float32)
    for idx, cls in enumerate(clf.classes_):
        full[:, int(cls)] = probs[:, idx]
    return full.reshape(h, w, len(TARGETS))
