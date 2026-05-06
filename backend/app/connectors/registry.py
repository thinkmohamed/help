"""Source registry — maps source_id → (provider, label, band)."""
from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import BaseConnector
from .copernicus import CopernicusConnector
from .corona import CoronaConnector
from .earth_engine import EarthEngineConnector
from .usgs import USGSConnector

SOURCES: list[dict[str, Any]] = [
    # Copernicus
    {"id": "sentinel-2", "provider": "copernicus", "label": "Sentinel-2 (10m optical)", "bands": ["B2", "B3", "B4", "B8", "B11", "B12"], "category": "multispectral"},
    {"id": "sentinel-1", "provider": "copernicus", "label": "Sentinel-1 SAR (C-band)", "bands": ["VV", "VH"], "category": "radar"},
    {"id": "sentinel-3", "provider": "copernicus", "label": "Sentinel-3 OLCI/SLSTR", "bands": ["LST", "OLCI"], "category": "thermal"},
    {"id": "sentinel-5p", "provider": "copernicus", "label": "Sentinel-5P TROPOMI", "bands": ["NO2", "CH4", "CO"], "category": "atmosphere"},
    # USGS
    {"id": "landsat-89", "provider": "usgs", "label": "Landsat 8/9 (30m optical)", "bands": ["B2", "B3", "B4", "B5", "B6", "B10"], "category": "multispectral"},
    {"id": "landsat-1972", "provider": "usgs", "label": "Landsat 1972 archive", "bands": ["MSS4", "MSS5", "MSS6", "MSS7"], "category": "historical"},
    {"id": "aster", "provider": "usgs", "label": "ASTER (90m thermal)", "bands": ["TIR10", "TIR11", "TIR12"], "category": "thermal"},
    {"id": "aster-gdem", "provider": "usgs", "label": "ASTER GDEM (30m elevation)", "bands": ["dem"], "category": "morphology"},
    # GEE
    {"id": "srtm", "provider": "gee", "label": "SRTM DEM 30m", "bands": ["elev"], "category": "morphology"},
    {"id": "alos-palsar", "provider": "gee", "label": "ALOS PALSAR (L-band SAR)", "bands": ["HH", "HV"], "category": "radar"},
    {"id": "modis", "provider": "gee", "label": "MODIS daily LST", "bands": ["LST_Day", "LST_Night"], "category": "thermal"},
    {"id": "insar-coh", "provider": "gee", "label": "InSAR Coherence", "bands": ["coh"], "category": "radar"},
    # CORONA
    {"id": "corona-1960", "provider": "corona", "label": "CORONA 1960-1972 (1.8m pan)", "bands": ["pan"], "category": "historical"},
    {"id": "corona-stereo", "provider": "corona", "label": "CORONA Stereo 3D", "bands": ["dsm"], "category": "morphology"},
]


def get_connector(provider: str) -> BaseConnector:
    if provider == "copernicus":
        return CopernicusConnector(
            username=settings.copernicus_username, password=settings.copernicus_password
        )
    if provider == "usgs":
        return USGSConnector(api_key=settings.usgs_api_key)
    if provider == "gee":
        return EarthEngineConnector(service_account_json=settings.gee_service_account_json)
    if provider == "corona":
        return CoronaConnector(
            username=settings.corona_username, password=settings.corona_password
        )
    raise ValueError(f"Unknown provider: {provider}")


def source_meta(source_id: str) -> dict[str, Any]:
    for s in SOURCES:
        if s["id"] == source_id:
            return s
    raise KeyError(source_id)
