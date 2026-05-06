"""Geomorphological analysis module.

التحليل الجيومورفولوجي - Terrain and landform analysis from DEM data
for identifying archaeological and geological features.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def compute_slope(dem: np.ndarray, cell_size: float = 30.0) -> np.ndarray:
    """Compute terrain slope in degrees."""
    dy, dx = np.gradient(dem, cell_size)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope_rad)


def compute_aspect(dem: np.ndarray, cell_size: float = 30.0) -> np.ndarray:
    """Compute terrain aspect (direction of steepest slope) in degrees."""
    dy, dx = np.gradient(dem, cell_size)
    aspect = np.degrees(np.arctan2(-dy, dx))
    aspect[aspect < 0] += 360
    return aspect


def compute_curvature(dem: np.ndarray, cell_size: float = 30.0) -> np.ndarray:
    """Compute terrain curvature (profile + plan curvature)."""
    gy, gx = np.gradient(dem, cell_size)
    gyy, _ = np.gradient(gy, cell_size)
    _, gxx = np.gradient(gx, cell_size)
    return gxx + gyy


def compute_tpi(dem: np.ndarray, radius: int = 10) -> np.ndarray:
    """Topographic Position Index - identifies ridges, valleys, flat areas."""
    mean_elev = ndimage.uniform_filter(dem, size=2 * radius + 1)
    return dem - mean_elev


def compute_hillshade(
    dem: np.ndarray,
    azimuth: float = 315.0,
    altitude: float = 45.0,
    cell_size: float = 30.0,
) -> np.ndarray:
    """Compute analytical hillshade for visualization."""
    dy, dx = np.gradient(dem, cell_size)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dy, dx)

    az_rad = np.radians(azimuth)
    alt_rad = np.radians(altitude)

    hillshade = np.sin(alt_rad) * np.cos(slope) + np.cos(alt_rad) * np.sin(
        slope
    ) * np.cos(az_rad - aspect)
    return np.clip(hillshade, 0, 1)


def detect_linear_features(dem: np.ndarray) -> np.ndarray:
    """Detect linear features (walls, roads, channels) from DEM.

    Uses directional Sobel filters to identify linear anomalies.
    """
    sobel_x = ndimage.sobel(dem, axis=1)
    sobel_y = ndimage.sobel(dem, axis=0)
    edges = np.sqrt(sobel_x**2 + sobel_y**2)
    edges_norm = edges / (edges.max() + 1e-10)
    return edges_norm


def detect_circular_features(dem: np.ndarray) -> np.ndarray:
    """Detect circular/mound features that may indicate buried structures."""
    curvature = compute_curvature(dem)
    tpi = compute_tpi(dem)

    curvature_norm = np.abs(curvature) / (np.abs(curvature).max() + 1e-10)
    tpi_norm = np.abs(tpi) / (np.abs(tpi).max() + 1e-10)

    return 0.5 * curvature_norm + 0.5 * tpi_norm


def run_geomorphological_analysis(
    dem_data: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Run full geomorphological analysis pipeline."""
    results: dict[str, np.ndarray] = {}

    dem = dem_data.get("elevation", dem_data.get("DEM"))
    if dem is None:
        dsm = dem_data.get("DSM")
        if dsm is not None:
            dem = dsm

    if dem is None:
        return results

    results["slope"] = compute_slope(dem)
    results["aspect"] = compute_aspect(dem)
    results["curvature"] = compute_curvature(dem)
    results["tpi"] = compute_tpi(dem)
    results["hillshade"] = compute_hillshade(dem)
    results["linear_features"] = detect_linear_features(dem)
    results["circular_features"] = detect_circular_features(dem)

    return results
