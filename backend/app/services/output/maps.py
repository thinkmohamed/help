"""Probability map generation.

خرائط احتمالية - Generate visual probability maps and heatmaps
for each detection category.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from ...config import OUTPUTS_DIR


CATEGORY_COLORS = {
    "groundwater": (0, 119, 190),       # Blue
    "excavation": (255, 87, 51),         # Orange-red
    "ancient_ruins": (255, 195, 0),      # Gold
    "dissolved_minerals": (46, 204, 113), # Green
    "underground_voids": (155, 89, 182),  # Purple
}


def create_heatmap(
    data: np.ndarray,
    colormap: str = "viridis",
) -> np.ndarray:
    """Create a heatmap image from a 2D array."""
    normalized = (data - data.min()) / (data.max() - data.min() + 1e-10)

    colormaps = {
        "viridis": [
            (68, 1, 84), (72, 35, 116), (64, 67, 135), (52, 94, 141),
            (33, 145, 140), (94, 201, 98), (253, 231, 37),
        ],
        "hot": [
            (0, 0, 0), (128, 0, 0), (255, 0, 0), (255, 128, 0),
            (255, 255, 0), (255, 255, 128), (255, 255, 255),
        ],
        "cool": [
            (0, 0, 128), (0, 0, 255), (0, 128, 255), (0, 255, 255),
            (128, 255, 128), (255, 255, 0), (255, 128, 0),
        ],
    }

    colors = colormaps.get(colormap, colormaps["viridis"])
    h, w = normalized.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    n_colors = len(colors)
    for i in range(h):
        for j in range(w):
            val = normalized[i, j]
            idx = val * (n_colors - 1)
            idx_low = int(idx)
            idx_high = min(idx_low + 1, n_colors - 1)
            frac = idx - idx_low
            for c in range(3):
                rgb[i, j, c] = int(
                    colors[idx_low][c] * (1 - frac) + colors[idx_high][c] * frac
                )

    return rgb


def generate_category_map(
    probability_map: np.ndarray,
    category_idx: int,
    category_name: str,
    job_id: str,
) -> str:
    """Generate and save a probability heatmap for a single category."""
    class_map = probability_map[:, :, category_idx]
    color = CATEGORY_COLORS.get(category_name, (128, 128, 128))

    h, w = class_map.shape
    rgb = np.zeros((h, w, 4), dtype=np.uint8)

    normalized = (class_map - class_map.min()) / (
        class_map.max() - class_map.min() + 1e-10
    )

    for c in range(3):
        rgb[:, :, c] = (normalized * color[c]).astype(np.uint8)
    rgb[:, :, 3] = (normalized * 200 + 55).astype(np.uint8)

    img = Image.fromarray(rgb, "RGBA")
    filename = f"{job_id}_{category_name}.png"
    filepath = OUTPUTS_DIR / filename
    img.save(str(filepath))

    return filename


def generate_combined_map(
    probability_map: np.ndarray,
    job_id: str,
) -> str:
    """Generate a combined probability map showing all categories."""
    h, w, n_classes = probability_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    categories = list(CATEGORY_COLORS.keys())

    for c in range(min(n_classes, len(categories))):
        color = CATEGORY_COLORS[categories[c]]
        class_map = probability_map[:, :, c]
        for ch in range(3):
            rgb[:, :, ch] += class_map * color[ch]

    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB")
    filename = f"{job_id}_combined.png"
    filepath = OUTPUTS_DIR / filename
    img.save(str(filepath))

    return filename


def generate_all_maps(
    probability_map: np.ndarray,
    job_id: str,
) -> dict[str, str]:
    """Generate all probability maps and return file paths."""
    map_files: dict[str, str] = {}

    categories = list(CATEGORY_COLORS.keys())
    for c in range(min(probability_map.shape[2], len(categories))):
        filename = generate_category_map(
            probability_map, c, categories[c], job_id
        )
        map_files[categories[c]] = filename

    map_files["combined"] = generate_combined_map(probability_map, job_id)

    return map_files
