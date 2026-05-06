"""Google Earth Engine connector — SRTM DEM, ALOS PALSAR, MODIS, InSAR Coherence."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, SourceLayer, synth_field


class EarthEngineConnector(BaseConnector):
    provider = "gee"

    def fetch(self, aoi: dict[str, Any], source_id: str, grid: tuple[int, int]) -> SourceLayer:
        salt = f"gee-{source_id}"
        arr = synth_field(aoi, salt, grid)
        band = {
            "srtm": "elevation",
            "alos-palsar": "HH-backscatter",
            "modis": "LST-anomaly",
            "insar-coh": "coherence",
        }.get(source_id, "raw")
        return SourceLayer(
            source_id=source_id,
            provider=self.provider,
            band_name=band,
            array=arr,
            units="normalised",
            is_synthetic=not self.is_authenticated(),
        )
