"""Thermal analysis module.

التحليل الحراري - Thermal anomaly detection from ASTER, Sentinel-3,
and MODIS data for underground feature identification.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def compute_thermal_anomaly(
    thermal: np.ndarray, window: int = 15
) -> np.ndarray:
    """Detect thermal anomalies by comparing local vs regional temperature."""
    regional_mean = ndimage.uniform_filter(thermal, size=window)
    regional_std = np.sqrt(
        ndimage.uniform_filter(thermal**2, size=window) - regional_mean**2
    )
    regional_std[regional_std == 0] = 1e-10
    return (thermal - regional_mean) / regional_std


def compute_thermal_inertia(
    day_temp: np.ndarray, night_temp: np.ndarray
) -> np.ndarray:
    """Estimate apparent thermal inertia from day/night temperature difference.

    Underground voids and water have high thermal inertia (small day-night diff).
    """
    diff = np.abs(day_temp - night_temp)
    diff[diff == 0] = 1e-10
    return 1.0 / diff


def compute_emissivity_anomaly(
    thermal_bands: dict[str, np.ndarray],
) -> np.ndarray:
    """Compute emissivity anomaly from multi-band thermal data.

    Uses temperature-emissivity separation approach.
    """
    values = list(thermal_bands.values())
    stacked = np.stack(values, axis=0)
    mean_temp = np.mean(stacked, axis=0)
    variance = np.var(stacked, axis=0)
    return variance / (mean_temp - mean_temp.min() + 1e-10)


def detect_groundwater_thermal(
    thermal: np.ndarray, dem: np.ndarray | None = None
) -> np.ndarray:
    """Detect potential groundwater zones from thermal anomalies.

    Cold anomalies in arid regions often indicate shallow groundwater.
    """
    anomaly = compute_thermal_anomaly(thermal)
    groundwater_indicator = np.where(anomaly < -1.5, np.abs(anomaly), 0).astype(
        np.float32
    )

    if dem is not None:
        h, w = thermal.shape
        dem_resized = _resize_array(dem, h, w)
        slope = _compute_slope(dem_resized)
        slope_norm = slope / (slope.max() + 1e-10)
        groundwater_indicator *= 1 - slope_norm * 0.5

    return groundwater_indicator


def _resize_array(arr: np.ndarray, target_h: int, target_w: int) -> np.ndarray:
    """Simple resize using scipy zoom."""
    zoom_h = target_h / arr.shape[0]
    zoom_w = target_w / arr.shape[1]
    return ndimage.zoom(arr, (zoom_h, zoom_w), order=1)


def _compute_slope(dem: np.ndarray) -> np.ndarray:
    """Compute terrain slope from DEM."""
    dy, dx = np.gradient(dem)
    return np.sqrt(dx**2 + dy**2)


def run_thermal_analysis(
    thermal_data: dict[str, np.ndarray],
    modis_data: dict[str, np.ndarray] | None = None,
    dem_data: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Run full thermal analysis pipeline."""
    results: dict[str, np.ndarray] = {}

    for name, data in thermal_data.items():
        results[f"anomaly_{name}"] = compute_thermal_anomaly(data)

    if len(thermal_data) > 1:
        results["emissivity_anomaly"] = compute_emissivity_anomaly(thermal_data)

    if modis_data:
        day = modis_data.get("LST_Day_1km")
        night = modis_data.get("LST_Night_1km")
        if day is not None and night is not None:
            results["thermal_inertia"] = compute_thermal_inertia(day, night)

    first_thermal = next(iter(thermal_data.values()))
    results["groundwater_thermal"] = detect_groundwater_thermal(
        first_thermal, dem_data
    )

    return results
