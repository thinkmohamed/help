"""CORONA Atlas connector — declassified 1960-1972 panchromatic + stereo DSM."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, SourceLayer, synth_field


class CoronaConnector(BaseConnector):
    provider = "corona"

    def fetch(self, aoi: dict[str, Any], source_id: str, grid: tuple[int, int]) -> SourceLayer:
        salt = f"corona-{source_id}"
        arr = synth_field(aoi, salt, grid)
        band = {
            "corona-1960": "panchromatic",
            "corona-stereo": "dsm",
        }.get(source_id, "raw")
        return SourceLayer(
            source_id=source_id,
            provider=self.provider,
            band_name=band,
            array=arr,
            units="normalised",
            is_synthetic=not self.is_authenticated(),
        )
