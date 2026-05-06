"""Pydantic models for request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    COPERNICUS = "copernicus"
    USGS = "usgs"
    GEE = "gee"
    CORONA = "corona"


class SatelliteLayer(str, Enum):
    # Copernicus
    SENTINEL2_OPTICAL = "sentinel2_optical"
    SENTINEL1_SAR = "sentinel1_sar"
    SENTINEL3_THERMAL = "sentinel3_thermal"
    SENTINEL5P_GAS = "sentinel5p_gas"
    # USGS
    LANDSAT89_OPTICAL = "landsat89_optical"
    LANDSAT_ARCHIVE = "landsat_archive"
    ASTER_THERMAL = "aster_thermal"
    ASTER_GDEM = "aster_gdem"
    # GEE
    SRTM_DEM = "srtm_dem"
    ALOS_PALSAR = "alos_palsar"
    MODIS_THERMAL = "modis_thermal"
    INSAR_COHERENCE = "insar_coherence"
    # CORONA
    CORONA_HISTORICAL = "corona_historical"
    STEREO_3D = "stereo_3d"


class AnalysisType(str, Enum):
    SPECTRAL = "spectral"
    RADAR = "radar"
    THERMAL = "thermal"
    GEOMORPHOLOGICAL = "geomorphological"
    HISTORICAL = "historical"


class MLModel(str, Enum):
    UNET = "unet"
    RANDOM_FOREST = "random_forest"
    ISOLATION_FOREST = "isolation_forest"
    DBSCAN = "dbscan"


class DetectionCategory(str, Enum):
    GROUNDWATER = "groundwater"
    EXCAVATION = "excavation"
    ANCIENT_RUINS = "ancient_ruins"
    DISSOLVED_MINERALS = "dissolved_minerals"
    UNDERGROUND_VOIDS = "underground_voids"


class AOIGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: list = Field(..., description="GeoJSON polygon coordinates")


class AOIInput(BaseModel):
    geometry: AOIGeometry
    name: Optional[str] = "Unnamed AOI"
    buffer_km: float = Field(default=5.0, ge=0, le=50)


class DataSourceConfig(BaseModel):
    sources: list[DataSourceType] = Field(
        default_factory=lambda: list(DataSourceType)
    )
    layers: list[SatelliteLayer] = Field(
        default_factory=lambda: list(SatelliteLayer)
    )
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    max_cloud_cover: float = Field(default=20.0, ge=0, le=100)


class AnalysisConfig(BaseModel):
    analyses: list[AnalysisType] = Field(
        default_factory=lambda: list(AnalysisType)
    )
    ml_models: list[MLModel] = Field(
        default_factory=lambda: list(MLModel)
    )
    ensemble_threshold: float = Field(default=0.5, ge=0, le=1)


class AnalysisRequest(BaseModel):
    aoi: AOIInput
    data_sources: DataSourceConfig = Field(default_factory=DataSourceConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)


class DetectionResult(BaseModel):
    category: DetectionCategory
    category_ar: str
    probability: float = Field(ge=0, le=1)
    location: dict
    details: str = ""


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    FETCHING_DATA = "fetching_data"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    FUSING = "fusing"
    CLASSIFYING = "classifying"
    GENERATING_OUTPUT = "generating_output"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisResponse(BaseModel):
    job_id: str
    status: AnalysisStatus
    progress: float = Field(default=0.0, ge=0, le=100)
    message: str = ""
    detections: list[DetectionResult] = Field(default_factory=list)
    report_url: Optional[str] = None
    map_url: Optional[str] = None


class PipelineStageResult(BaseModel):
    stage: str
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None
