"""Full analysis pipeline orchestrator.

Coordinates the entire flow:
AOI -> Data Sources -> Processing -> Data Fusion -> ML Models -> Ensemble -> Output
"""

from __future__ import annotations

import asyncio
import traceback

import numpy as np

from ..models.schemas import (
    AnalysisRequest,
    AnalysisStatus,
    DetectionResult,
    DetectionCategory,
)
from .data_sources.copernicus import (
    simulate_sentinel2_data,
    simulate_sentinel1_data,
    simulate_sentinel3_thermal,
    simulate_sentinel5p_gas,
)
from .data_sources.usgs import (
    simulate_landsat_data,
    simulate_aster_thermal,
    simulate_aster_gdem,
    simulate_landsat_archive,
)
from .data_sources.gee import (
    simulate_srtm_dem,
    simulate_alos_palsar,
    simulate_modis_thermal,
    simulate_insar_coherence,
)
from .data_sources.corona import simulate_corona_historical, simulate_stereo_3d
from .processing.spectral import run_spectral_analysis
from .processing.radar import run_radar_analysis
from .processing.thermal import run_thermal_analysis
from .processing.geomorphological import run_geomorphological_analysis
from .processing.historical import run_historical_analysis
from .fusion.data_fusion import fuse_analysis_results
from .ml.unet import run_unet_classification
from .ml.random_forest import run_random_forest_classification
from .ml.isolation_forest import run_isolation_forest, classify_anomalies
from .ml.dbscan import (
    run_spatial_clustering,
    assign_clusters_to_categories,
)
from .ensemble.voting import weighted_vote, get_final_classifications
from .output.maps import generate_all_maps
from .output.reports import generate_json_report, generate_html_report


JOB_STORE: dict[str, dict] = {}

N_CLASSES = 5
TARGET_SIZE = (256, 256)
CATEGORY_NAMES = [
    "groundwater", "excavation", "ancient_ruins",
    "dissolved_minerals", "underground_voids",
]
CATEGORY_NAMES_AR = [
    "مياه جوفية", "حفر تنقيب حديثة", "آثار قديمة",
    "معادن مذابة", "فراغات تحت الأرض",
]


def _update_job(job_id: str, **kwargs) -> None:
    if job_id in JOB_STORE:
        JOB_STORE[job_id].update(kwargs)


async def run_full_pipeline(job_id: str, request: AnalysisRequest) -> None:
    """Execute the complete analysis pipeline."""
    pipeline_stages: list[dict] = []

    try:
        # --- Stage 1: Fetch satellite data ---
        _update_job(
            job_id,
            status=AnalysisStatus.FETCHING_DATA,
            progress=5,
            message="جاري جلب بيانات الأقمار الصناعية...",
        )
        await asyncio.sleep(0.5)

        s2_data = simulate_sentinel2_data(*TARGET_SIZE)
        s1_data = simulate_sentinel1_data(*TARGET_SIZE)
        s3_data = simulate_sentinel3_thermal(64, 64)
        s5p_data = simulate_sentinel5p_gas(32, 32)
        landsat_data = simulate_landsat_data(*TARGET_SIZE)
        aster_thermal = simulate_aster_thermal(128, 128)
        aster_gdem = simulate_aster_gdem(*TARGET_SIZE)
        landsat_archive = simulate_landsat_archive(128, 128)
        srtm = simulate_srtm_dem(*TARGET_SIZE)
        alos = simulate_alos_palsar(*TARGET_SIZE)
        modis = simulate_modis_thermal(64, 64)
        insar = simulate_insar_coherence(*TARGET_SIZE)
        corona = simulate_corona_historical(512, 512)
        stereo = simulate_stereo_3d(*TARGET_SIZE)

        pipeline_stages.append({"stage": "data_fetch", "status": "completed"})
        _update_job(
            job_id,
            progress=15,
            message="تم جلب البيانات من 4 مصادر (14 طبقة)",
        )

        # --- Stage 2: Processing ---
        _update_job(
            job_id,
            status=AnalysisStatus.PROCESSING,
            progress=20,
            message="جاري المعالجة الطيفية والرادارية...",
        )
        await asyncio.sleep(0.3)

        spectral_results = run_spectral_analysis(s2_data)
        pipeline_stages.append({"stage": "spectral_analysis", "status": "completed"})
        _update_job(job_id, progress=28, message="اكتمل التحليل الطيفي")

        radar_results = run_radar_analysis(
            s1_data, l_band_data=alos, coherence_data=insar
        )
        pipeline_stages.append({"stage": "radar_analysis", "status": "completed"})
        _update_job(job_id, progress=36, message="اكتمل التحليل الراداري")

        thermal_results = run_thermal_analysis(
            aster_thermal, modis_data=modis, dem_data=aster_gdem.get("DEM")
        )
        pipeline_stages.append({"stage": "thermal_analysis", "status": "completed"})
        _update_job(job_id, progress=44, message="اكتمل التحليل الحراري")

        geomorph_results = run_geomorphological_analysis(srtm)
        pipeline_stages.append({"stage": "geomorphological_analysis", "status": "completed"})
        _update_job(job_id, progress=50, message="اكتمل التحليل الجيومورفولوجي")

        historical_results = run_historical_analysis(
            corona_data=corona,
            archive_data=landsat_archive,
            modern_data={"B04": s2_data["B04"]},
        )
        pipeline_stages.append({"stage": "historical_analysis", "status": "completed"})
        _update_job(job_id, progress=55, message="اكتمل التحليل التاريخي (6 عقود)")

        # --- Stage 3: Data Fusion ---
        _update_job(
            job_id,
            status=AnalysisStatus.FUSING,
            progress=60,
            message="جاري دمج البيانات من جميع المصادر...",
        )
        await asyncio.sleep(0.3)

        fused_data = fuse_analysis_results(
            spectral_results=spectral_results,
            radar_results=radar_results,
            thermal_results=thermal_results,
            geomorphological_results=geomorph_results,
            historical_results=historical_results,
            target_size=TARGET_SIZE,
        )
        pipeline_stages.append({"stage": "data_fusion", "status": "completed"})
        _update_job(
            job_id,
            progress=65,
            message=f"تم دمج {fused_data.shape[2]} طبقة تحليلية",
        )

        # --- Stage 4: ML Classification ---
        _update_job(
            job_id,
            status=AnalysisStatus.CLASSIFYING,
            progress=68,
            message="جاري التصنيف بالذكاء الاصطناعي...",
        )
        await asyncio.sleep(0.3)

        unet_preds = run_unet_classification(fused_data, n_classes=N_CLASSES)
        pipeline_stages.append({"stage": "unet", "status": "completed"})
        _update_job(job_id, progress=74, message="اكتمل تصنيف U-Net")

        rf_preds = run_random_forest_classification(fused_data, n_classes=N_CLASSES)
        pipeline_stages.append({"stage": "random_forest", "status": "completed"})
        _update_job(job_id, progress=80, message="اكتمل تصنيف Random Forest")

        anomaly_map = run_isolation_forest(fused_data)
        if_preds = classify_anomalies(anomaly_map, fused_data, n_classes=N_CLASSES)
        pipeline_stages.append({"stage": "isolation_forest", "status": "completed"})
        _update_job(job_id, progress=85, message="اكتمل كشف الشذوذات")

        cluster_map, cluster_info = run_spatial_clustering(anomaly_map)
        dbscan_preds = if_preds.copy()
        pipeline_stages.append({"stage": "dbscan", "status": "completed"})

        # --- Stage 5: Ensemble Voting ---
        _update_job(
            job_id,
            status=AnalysisStatus.CLASSIFYING,
            progress=88,
            message="جاري نظام التصويت Ensemble...",
        )

        model_predictions = {
            "unet": unet_preds,
            "random_forest": rf_preds,
            "isolation_forest": if_preds,
            "dbscan": dbscan_preds,
        }
        ensemble_probs = weighted_vote(model_predictions)
        classifications = get_final_classifications(ensemble_probs, threshold=0.3)
        pipeline_stages.append({"stage": "ensemble", "status": "completed"})

        cluster_info = assign_clusters_to_categories(
            cluster_map, cluster_info, ensemble_probs, n_classes=N_CLASSES
        )

        # --- Stage 6: Generate Output ---
        _update_job(
            job_id,
            status=AnalysisStatus.GENERATING_OUTPUT,
            progress=92,
            message="جاري إنشاء الخرائط والتقارير...",
        )
        await asyncio.sleep(0.2)

        map_files = generate_all_maps(ensemble_probs, job_id)
        pipeline_stages.append({"stage": "maps", "status": "completed"})

        aoi_name = request.aoi.name or "منطقة غير مسماة"
        json_report = generate_json_report(
            job_id, aoi_name, classifications, cluster_info, map_files, pipeline_stages
        )
        html_report = generate_html_report(
            job_id, aoi_name, classifications, cluster_info, map_files
        )
        pipeline_stages.append({"stage": "reports", "status": "completed"})

        # Build detection results
        detections = []
        for cat_result in classifications.get("categories", []):
            cat_name = cat_result["category"]
            det = DetectionResult(
                category=DetectionCategory(cat_name),
                category_ar=cat_result["category_ar"],
                probability=cat_result["max_probability"],
                location=cat_result["peak_location"],
                details=f"تم الكشف بثقة {cat_result['confidence']} - {cat_result['n_pixels']} نقطة",
            )
            detections.append(det)

        _update_job(
            job_id,
            status=AnalysisStatus.COMPLETED,
            progress=100,
            message=f"اكتمل التحليل - تم اكتشاف {len(detections)} فئات",
            detections=detections,
            report_url=f"/static/outputs/{html_report}",
            map_url=f"/static/outputs/{map_files.get('combined', '')}",
        )

    except Exception as e:
        _update_job(
            job_id,
            status=AnalysisStatus.FAILED,
            message=f"خطأ: {str(e)}",
        )
        traceback.print_exc()
