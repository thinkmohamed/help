"""Copernicus Dataspace connector — Sentinel-1/2/3/5P.

If credentials are not configured, returns deterministic synthetic layers.
A real implementation would call the OData API at
https://catalogue.dataspace.copernicus.eu/odata/v1/Products and use Sentinel Hub
processing API for AOI clipping.
"""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, SourceLayer, synth_field


class CopernicusConnector(BaseConnector):
    provider = "copernicus"

    def fetch(self, aoi: dict[str, Any], source_id: str, grid: tuple[int, int]) -> SourceLayer:
        # NOTE: real implementation would authenticate against Copernicus Identity
        # and download products via OData/STAC. We always fall back to synthetic
        # data when not authenticated so the pipeline is exercisable.
        salt = f"copernicus-{source_id}"
        arr = synth_field(aoi, salt, grid)
        band = {
            "sentinel-2": "NDVI",
            "sentinel-1": "VV-backscatter",
            "sentinel-3": "LST",
            "sentinel-5p": "NO2",
        }.get(source_id, "raw")
        return SourceLayer(
            source_id=source_id,
            provider=self.provider,
            band_name=band,
            array=arr,
            units="normalised",
            is_synthetic=not self.is_authenticated(),
        )
