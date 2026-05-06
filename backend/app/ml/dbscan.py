"""DBSCAN — spatial clustering of high-confidence pixels into discrete targets."""
from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN


def dbscan_cluster(prob_map: np.ndarray, *, threshold: float = 0.6, eps: float = 3.0, min_samples: int = 8) -> dict:
    """Cluster pixels with prob>threshold; returns label map and cluster summary."""
    if prob_map.size == 0:
        return {"labels": np.zeros((0, 0), dtype=np.int32), "clusters": []}
    h, w = prob_map.shape
    yy, xx = np.where(prob_map >= threshold)
    if yy.size == 0:
        return {"labels": -np.ones((h, w), dtype=np.int32), "clusters": []}
    pts = np.column_stack([yy, xx]).astype(np.float32)
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(pts)
    labels = -np.ones((h, w), dtype=np.int32)
    labels[yy, xx] = db.labels_
    clusters: list[dict] = []
    for cid in sorted(set(int(c) for c in db.labels_)):
        if cid < 0:
            continue
        mask = db.labels_ == cid
        cy = float(yy[mask].mean())
        cx = float(xx[mask].mean())
        size = int(mask.sum())
        score = float(prob_map[yy[mask], xx[mask]].mean())
        clusters.append(
            {"id": cid, "centroid_yx": [cy, cx], "size_px": size, "mean_score": score}
        )
    return {"labels": labels, "clusters": clusters}
