"""End-to-end orchestrator: AOI → connectors → pipelines → ML → ensemble → outputs."""
from __future__ import annotations

import base64
import io
import time
from typing import Any

import numpy as np
from PIL import Image

from .connectors import get_connector
from .connectors.base import SourceLayer
from .connectors.registry import source_meta
from .ml import (
    dbscan_cluster,
    ensemble_vote,
    isolation_forest_anomaly,
    random_forest_classify,
    unet_segmentation,
)
from .outputs.targets import TARGET_LABELS, TARGETS
from .pipelines import (
    fuse_features,
    historical_features,
    morphology_features,
    multispectral_features,
    radar_features,
    thermal_features,
)


def _fetch_layers(aoi: dict[str, Any], source_ids: list[str], grid: tuple[int, int]) -> list[SourceLayer]:
    layers: list[SourceLayer] = []
    for sid in source_ids:
        meta = source_meta(sid)
        connector = get_connector(meta["provider"])
        layer = connector.fetch(aoi, sid, grid)
        layers.append(layer)
    return layers


def _heatmap_png_base64(arr: np.ndarray, color_hex: str) -> str:
    """Render a single-channel probability map to a transparent PNG with a coloured overlay."""
    if arr.size == 0:
        return ""
    h, w = arr.shape
    r, g, b = (int(color_hex[i : i + 2], 16) for i in (1, 3, 5))
    alpha = (arr * 220).clip(0, 220).astype(np.uint8)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = r
    rgba[..., 1] = g
    rgba[..., 2] = b
    rgba[..., 3] = alpha
    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def run_pipeline(
    aoi: dict[str, Any],
    source_ids: list[str],
    *,
    grid: tuple[int, int] = (128, 128),
    use_torch: bool = True,
    progress_cb: Any = None,
) -> dict[str, Any]:
    """Run the entire pipeline synchronously and return a structured result dict."""
    t0 = time.time()
    timings: dict[str, float] = {}

    def _emit(stage: str, status: str, extra: dict[str, Any] | None = None) -> None:
        if progress_cb is not None:
            progress_cb({"stage": stage, "status": status, **(extra or {})})

    _emit("fetch", "running", {"sources": source_ids})
    layers = _fetch_layers(aoi, source_ids, grid)
    timings["fetch_s"] = time.time() - t0

    _emit("multispectral", "running")
    ms = multispectral_features(layers)
    _emit("radar", "running")
    rd = radar_features(layers)
    _emit("thermal", "running")
    th = thermal_features(layers)
    _emit("morphology", "running")
    mo = morphology_features(layers)
    _emit("historical", "running")
    hi = historical_features(layers)

    _emit("fusion", "running")
    stack, feature_names = fuse_features(ms, rd, th, mo, hi)
    timings["pipelines_s"] = time.time() - t0 - timings["fetch_s"]

    _emit("ml.unet", "running")
    unet_map = unet_segmentation(stack, use_torch=use_torch)
    _emit("ml.rf", "running")
    rf_vol = random_forest_classify(stack)
    _emit("ml.iso", "running")
    iso_map = isolation_forest_anomaly(stack)

    _emit("ensemble", "running")
    ensemble = ensemble_vote(unet_map, rf_vol, iso_map)

    _emit("clusters", "running")
    targets_payload: dict[str, Any] = {}
    for idx, key in enumerate(TARGETS):
        prob = ensemble[..., idx]
        clusters = dbscan_cluster(prob, threshold=0.55, eps=3.0, min_samples=8)
        meta = TARGET_LABELS[key]
        targets_payload[key] = {
            "key": key,
            "label_en": meta["en"],
            "label_ar": meta["ar"],
            "color": meta["color"],
            "summary": {
                "mean_prob": float(prob.mean()),
                "max_prob": float(prob.max()),
                "n_clusters": len(clusters["clusters"]),
                "high_confidence_px": int((prob >= 0.7).sum()),
            },
            "clusters": clusters["clusters"],
            "heatmap_png": _heatmap_png_base64(prob, meta["color"]),
        }

    timings["ml_s"] = time.time() - t0 - timings["fetch_s"] - timings["pipelines_s"]
    timings["total_s"] = time.time() - t0

    sources_used = [
        {
            "source_id": layer.source_id,
            "provider": layer.provider,
            "band": layer.band_name,
            "is_synthetic": layer.is_synthetic,
        }
        for layer in layers
    ]

    _emit("done", "completed")
    return {
        "aoi": aoi,
        "grid": list(grid),
        "sources_used": sources_used,
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "targets": targets_payload,
        "timings": timings,
    }
