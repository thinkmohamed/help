"""USGS EarthExplorer M2M connector — Landsat 8/9, Landsat 1972, ASTER, ASTER GDEM."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, SourceLayer, synth_field


class USGSConnector(BaseConnector):
    provider = "usgs"

    def fetch(self, aoi: dict[str, Any], source_id: str, grid: tuple[int, int]) -> SourceLayer:
        salt = f"usgs-{source_id}"
        arr = synth_field(aoi, salt, grid)
        band = {
            "landsat-89": "NDVI",
            "landsat-1972": "MSS-NDVI",
            "aster": "TIR-LST",
            "aster-gdem": "elevation",
        }.get(source_id, "raw")
        return SourceLayer(
            source_id=source_id,
            provider=self.provider,
            band_name=band,
            array=arr,
            units="normalised",
            is_synthetic=not self.is_authenticated(),
        )
