"""API routes for the geospatial analysis pipeline."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks

from ..models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatus,
    DataSourceType,
    SatelliteLayer,
    AnalysisType,
    MLModel,
    DetectionCategory,
)
from ..services.pipeline import run_full_pipeline, JOB_STORE

router = APIRouter(prefix="/api", tags=["analysis"])


@router.get("/data-sources")
async def get_data_sources():
    """Return available data sources and their layers."""
    return {
        "sources": [
            {
                "id": "copernicus",
                "name": "Copernicus Dataspace",
                "name_ar": "كوبرنيكوس",
                "layers": [
                    {"id": "sentinel2_optical", "name": "Sentinel-2", "name_ar": "بصري 10م", "resolution": "10m"},
                    {"id": "sentinel1_sar", "name": "Sentinel-1 SAR", "name_ar": "رادار SAR", "resolution": "10m"},
                    {"id": "sentinel3_thermal", "name": "Sentinel-3 OLCI", "name_ar": "حراري OLCI", "resolution": "1km"},
                    {"id": "sentinel5p_gas", "name": "Sentinel-5P", "name_ar": "غازات", "resolution": "5.5km"},
                ],
            },
            {
                "id": "usgs",
                "name": "USGS EarthExplorer",
                "name_ar": "USGS المسح الجيولوجي",
                "layers": [
                    {"id": "landsat89_optical", "name": "Landsat 8/9", "name_ar": "بصري 30م", "resolution": "30m"},
                    {"id": "landsat_archive", "name": "Landsat 1972", "name_ar": "أرشيف 1972", "resolution": "60m"},
                    {"id": "aster_thermal", "name": "ASTER", "name_ar": "حراري 90م", "resolution": "90m"},
                    {"id": "aster_gdem", "name": "ASTER GDEM", "name_ar": "ارتفاعات 30م", "resolution": "30m"},
                ],
            },
            {
                "id": "gee",
                "name": "Google Earth Engine",
                "name_ar": "محرك جوجل للأرض",
                "layers": [
                    {"id": "srtm_dem", "name": "SRTM DEM", "name_ar": "نموذج ارتفاعات 30م", "resolution": "30m"},
                    {"id": "alos_palsar", "name": "ALOS PALSAR", "name_ar": "رادار L-band", "resolution": "25m"},
                    {"id": "modis_thermal", "name": "MODIS", "name_ar": "حراري يومي", "resolution": "1km"},
                    {"id": "insar_coherence", "name": "InSAR Coherence", "name_ar": "تماسك InSAR", "resolution": "10m"},
                ],
            },
            {
                "id": "corona",
                "name": "CORONA Atlas",
                "name_ar": "أطلس كورونا",
                "layers": [
                    {"id": "corona_historical", "name": "CORONA 1960-1972", "name_ar": "صور تاريخية 1.8م", "resolution": "1.8m"},
                    {"id": "stereo_3d", "name": "Stereo 3D", "name_ar": "تجسيم ثلاثي الأبعاد", "resolution": "2m"},
                ],
            },
        ]
    }


@router.get("/analysis-types")
async def get_analysis_types():
    """Return available analysis types."""
    return {
        "analyses": [
            {"id": "spectral", "name_ar": "التحليل المتعدد الطيفي", "name": "Multi-spectral Analysis"},
            {"id": "radar", "name_ar": "التحليل الراداري متعدد التردد", "name": "Multi-frequency Radar Analysis"},
            {"id": "thermal", "name_ar": "التحليل الحراري", "name": "Thermal Analysis"},
            {"id": "geomorphological", "name_ar": "التحليل الجيومورفولوجي", "name": "Geomorphological Analysis"},
            {"id": "historical", "name_ar": "التحليل التاريخي (6 عقود)", "name": "Historical Analysis (6 Decades)"},
        ],
        "ml_models": [
            {"id": "unet", "name_ar": "شبكة عصبية عميقة U-Net", "name": "U-Net Deep Neural Network"},
            {"id": "random_forest", "name_ar": "متعدد الفئات Random Forest", "name": "Random Forest Multi-class"},
            {"id": "isolation_forest", "name_ar": "للشذوذات Isolation Forest", "name": "Isolation Forest Anomaly Detection"},
            {"id": "dbscan", "name_ar": "التجميع المكاني DBSCAN", "name": "DBSCAN Spatial Clustering"},
        ],
        "detection_categories": [
            {"id": "groundwater", "name_ar": "مياه جوفية", "color": "#0077BE"},
            {"id": "excavation", "name_ar": "حفر تنقيب حديثة", "color": "#FF5733"},
            {"id": "ancient_ruins", "name_ar": "آثار قديمة", "color": "#FFC300"},
            {"id": "dissolved_minerals", "name_ar": "معادن مذابة", "color": "#2ECC71"},
            {"id": "underground_voids", "name_ar": "فراغات تحت الأرض", "color": "#9B59B6"},
        ],
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new geospatial analysis job."""
    job_id = str(uuid.uuid4())[:8]

    JOB_STORE[job_id] = {
        "status": AnalysisStatus.PENDING,
        "progress": 0,
        "message": "تم استلام الطلب",
        "detections": [],
        "report_url": None,
        "map_url": None,
    }

    background_tasks.add_task(run_full_pipeline, job_id, request)

    return AnalysisResponse(
        job_id=job_id,
        status=AnalysisStatus.PENDING,
        progress=0,
        message="تم بدء التحليل",
    )


@router.get("/status/{job_id}", response_model=AnalysisResponse)
async def get_job_status(job_id: str):
    """Get the status of an analysis job."""
    job = JOB_STORE.get(job_id)
    if not job:
        return AnalysisResponse(
            job_id=job_id,
            status=AnalysisStatus.FAILED,
            message="المهمة غير موجودة",
        )

    return AnalysisResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        detections=job.get("detections", []),
        report_url=job.get("report_url"),
        map_url=job.get("map_url"),
    )


@router.get("/jobs")
async def list_jobs():
    """List all analysis jobs."""
    jobs = []
    for job_id, job in JOB_STORE.items():
        jobs.append({
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
        })
    return {"jobs": jobs}
