# GeoIntel Platform — Multi-Source Geospatial Intelligence

A unified platform for multi-source satellite data fusion and subsurface target detection, implementing the architecture:

```
AOI → [Copernicus | USGS | Earth Engine | CORONA] → Unified Processing →
      [Multispectral | Radar | Thermal | 3D Morphology | 60-Year History] →
      Data Fusion → [U-Net | Random Forest | Isolation Forest | DBSCAN] →
      Ensemble Voting → {Underground Voids, Buried Metals, Ancient Ruins,
                         Modern Excavations, Groundwater} → Probability Maps + Reports
```

## Architecture

- **Backend** — FastAPI (Python 3.11+), async job runner, pluggable connectors and ML models
- **Frontend** — React + Vite + TypeScript + Leaflet (AOI drawing, workflow visualization, results overlay)
- **Storage** — Filesystem-based job/results store (swap for Postgres/S3 in production)

## Quick start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## Data sources

| Provider | Sources | Auth |
|----------|---------|------|
| Copernicus Dataspace | Sentinel-1/2/3/5P | OAuth (set `COPERNICUS_USERNAME`, `COPERNICUS_PASSWORD`) |
| USGS EarthExplorer | Landsat 8/9, Landsat 1972, ASTER, ASTER GDEM | M2M API key (`USGS_API_KEY`) |
| Google Earth Engine | SRTM DEM, ALOS PALSAR, MODIS, InSAR Coherence | Service account (`GEE_SERVICE_ACCOUNT_JSON`) |
| CORONA Atlas | CORONA 1960–1972, Stereo 3D | CAST account (`CORONA_USERNAME`, `CORONA_PASSWORD`) |

When credentials are absent, connectors fall back to **deterministic synthetic generators** based on the AOI hash, so the full pipeline is exercised end-to-end. Replace each connector's `fetch()` method with the real provider call once credentials are available.

## Pipeline stages

1. **Multispectral analysis** — NDVI, NDWI, SWIR ratios for soil/water/vegetation features.
2. **Radar multi-frequency** — C-band (Sentinel-1) + L-band (PALSAR) backscatter and InSAR coherence loss for subsidence and disturbed ground.
3. **Thermal analysis** — Diurnal LST anomalies (MODIS day/night, ASTER, Sentinel-3 SLSTR) for thermal inertia anomalies (voids, metals).
4. **3D morphology** — SRTM + ASTER GDEM + CORONA stereo derived terrain metrics: TPI, slope, curvature, micro-relief.
5. **60-year history** — Time-series change detection between CORONA (1960–1972) and modern Landsat/Sentinel.

## ML models

- **U-Net** (PyTorch) — pixel-wise segmentation of disturbed/anomalous regions.
- **Random Forest** — multi-class classifier for the 5 target types using engineered features.
- **Isolation Forest** — unsupervised anomaly scoring for unknown subsurface signatures.
- **DBSCAN** — spatial clustering of high-confidence pixels into discrete targets.
- **Ensemble** — soft-voting across the four models, calibrated per target type.

## License

MIT
