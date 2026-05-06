"""Multi-spectral analysis module.

التحليل المتعدد الطيفي - Spectral indices and feature extraction from
optical satellite imagery (Sentinel-2, Landsat).
"""

from __future__ import annotations

import numpy as np


def compute_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index."""
    denom = nir + red
    denom[denom == 0] = 1e-10
    return (nir - red) / denom


def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Water Index."""
    denom = green + nir
    denom[denom == 0] = 1e-10
    return (green - nir) / denom


def compute_ndbi(swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Built-up Index."""
    denom = swir + nir
    denom[denom == 0] = 1e-10
    return (swir - nir) / denom


def compute_clay_mineral_ratio(
    swir1: np.ndarray, swir2: np.ndarray
) -> np.ndarray:
    """Clay mineral ratio for archaeological soil detection."""
    swir2_safe = swir2.copy()
    swir2_safe[swir2_safe == 0] = 1e-10
    return swir1 / swir2_safe


def compute_iron_oxide_ratio(
    red: np.ndarray, blue: np.ndarray
) -> np.ndarray:
    """Iron oxide ratio for mineral detection."""
    blue_safe = blue.copy()
    blue_safe[blue_safe == 0] = 1e-10
    return red / blue_safe


def compute_soil_brightness(bands: dict[str, np.ndarray]) -> np.ndarray:
    """Soil brightness index from multiple bands."""
    values = list(bands.values())
    stacked = np.stack(values, axis=0)
    return np.mean(stacked, axis=0)


def run_spectral_analysis(bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Run full spectral analysis suite on multi-band data.

    Expected bands: B02 (blue), B03 (green), B04 (red), B08 (NIR),
                    B11 (SWIR1), B12 (SWIR2)
    """
    results: dict[str, np.ndarray] = {}

    blue = bands.get("B02", bands.get("SR_B2"))
    green = bands.get("B03", bands.get("SR_B3"))
    red = bands.get("B04", bands.get("SR_B4"))
    nir = bands.get("B08", bands.get("SR_B5"))
    swir1 = bands.get("B11", bands.get("SR_B6"))
    swir2 = bands.get("B12", bands.get("SR_B7"))

    if red is not None and nir is not None:
        results["ndvi"] = compute_ndvi(nir, red)
    if green is not None and nir is not None:
        results["ndwi"] = compute_ndwi(green, nir)
    if swir1 is not None and nir is not None:
        results["ndbi"] = compute_ndbi(swir1, nir)
    if swir1 is not None and swir2 is not None:
        results["clay_ratio"] = compute_clay_mineral_ratio(swir1, swir2)
    if red is not None and blue is not None:
        results["iron_oxide"] = compute_iron_oxide_ratio(red, blue)

    results["soil_brightness"] = compute_soil_brightness(bands)

    return results
