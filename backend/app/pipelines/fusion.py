"""Data Fusion engine — stacks all analytical features into a single (H, W, C) tensor."""
from __future__ import annotations

import numpy as np


def fuse_features(*feature_dicts: dict[str, np.ndarray]) -> tuple[np.ndarray, list[str]]:
    """Concatenate every feature into a (H, W, C) float32 stack with consistent ordering."""
    stack: list[np.ndarray] = []
    names: list[str] = []
    for fd in feature_dicts:
        for name in sorted(fd):
            arr = fd[name]
            if arr.ndim != 2:
                continue
            stack.append(arr.astype(np.float32))
            names.append(name)
    if not stack:
        return np.zeros((0, 0, 0), dtype=np.float32), []
    h, w = stack[0].shape
    aligned = [a if a.shape == (h, w) else _resize_to(a, (h, w)) for a in stack]
    return np.stack(aligned, axis=-1), names


def _resize_to(arr: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    sh, sw = arr.shape
    yi = (np.linspace(0, sh - 1, h)).astype(np.int32)
    xi = (np.linspace(0, sw - 1, w)).astype(np.int32)
    return arr[np.ix_(yi, xi)].astype(np.float32)
