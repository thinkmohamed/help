"""Application configuration."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUTS_DIR = STATIC_DIR / "outputs"
FRONTEND_DIR = BASE_DIR / "frontend"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Data source API keys (set via environment variables)
COPERNICUS_CLIENT_ID = os.getenv("COPERNICUS_CLIENT_ID", "")
COPERNICUS_CLIENT_SECRET = os.getenv("COPERNICUS_CLIENT_SECRET", "")
USGS_USERNAME = os.getenv("USGS_USERNAME", "")
USGS_PASSWORD = os.getenv("USGS_PASSWORD", "")
GEE_SERVICE_ACCOUNT = os.getenv("GEE_SERVICE_ACCOUNT", "")

# Processing defaults
DEFAULT_BUFFER_KM = 5
MAX_AOI_AREA_KM2 = 10000
TILE_SIZE = 256
