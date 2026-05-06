"""Data source connectors. Each connector implements `fetch(aoi, source)` and returns a SourceLayer.

If real credentials are not configured, fall back to deterministic synthetic
generators seeded by the AOI bounding box so the rest of the pipeline runs end-to-end.
"""
from .base import BaseConnector, SourceLayer  # noqa: F401
from .copernicus import CopernicusConnector  # noqa: F401
from .corona import CoronaConnector  # noqa: F401
from .earth_engine import EarthEngineConnector  # noqa: F401
from .registry import SOURCES, get_connector  # noqa: F401
from .usgs import USGSConnector  # noqa: F401
