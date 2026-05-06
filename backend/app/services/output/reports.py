"""Report generation module.

تقارير - Generate detailed analysis reports in JSON and HTML formats.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ...config import OUTPUTS_DIR


def generate_json_report(
    job_id: str,
    aoi_name: str,
    classifications: dict,
    cluster_info: list[dict],
    map_files: dict[str, str],
    pipeline_stages: list[dict],
) -> str:
    """Generate a detailed JSON report."""
    report = {
        "report_id": job_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aoi": {"name": aoi_name},
        "summary": {
            "total_categories_detected": classifications.get("total_detections", 0),
            "total_clusters": len(cluster_info),
            "categories": classifications.get("categories", []),
        },
        "clusters": cluster_info,
        "maps": map_files,
        "pipeline": pipeline_stages,
        "methodology": {
            "data_sources": [
                "Copernicus Dataspace (Sentinel-1, 2, 3, 5P)",
                "USGS EarthExplorer (Landsat 8/9, ASTER)",
                "Google Earth Engine (SRTM, ALOS PALSAR, MODIS)",
                "CORONA Atlas (1960-1972)",
            ],
            "processing": [
                "التحليل المتعدد الطيفي (Multi-spectral Analysis)",
                "التحليل الراداري متعدد التردد (Multi-frequency Radar)",
                "التحليل الحراري (Thermal Analysis)",
                "التحليل الجيومورفولوجي (Geomorphological Analysis)",
                "التحليل التاريخي 6 عقود (Historical Analysis - 6 Decades)",
            ],
            "ml_models": [
                "U-Net شبكة عصبية عميقة",
                "Random Forest متعدد الفئات",
                "Isolation Forest للشذوذات",
                "DBSCAN التجميع المكاني",
            ],
            "ensemble": "نظام التصويت Ensemble (Weighted Voting)",
        },
    }

    filename = f"{job_id}_report.json"
    filepath = OUTPUTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return filename


def generate_html_report(
    job_id: str,
    aoi_name: str,
    classifications: dict,
    cluster_info: list[dict],
    map_files: dict[str, str],
) -> str:
    """Generate an HTML report with embedded maps."""
    categories = classifications.get("categories", [])

    category_rows = ""
    for cat in categories:
        confidence_color = {
            "high": "#27ae60", "medium": "#f39c12", "low": "#e74c3c"
        }.get(cat.get("confidence", "low"), "#95a5a6")

        category_rows += f"""
        <tr>
            <td>{cat['category_ar']}</td>
            <td>{cat['category']}</td>
            <td>{cat['mean_probability']:.2%}</td>
            <td>{cat['max_probability']:.2%}</td>
            <td style="color: {confidence_color}; font-weight: bold;">{cat['confidence']}</td>
            <td>{cat['n_pixels']:,}</td>
        </tr>"""

    cluster_rows = ""
    for cl in cluster_info[:20]:
        cluster_rows += f"""
        <tr>
            <td>{cl.get('cluster_id', 'N/A')}</td>
            <td>{cl.get('category_ar', 'غير محدد')}</td>
            <td>{cl.get('probability', 0):.2%}</td>
            <td>{cl.get('n_pixels', 0):,}</td>
            <td>({cl.get('center', [0, 0])[0]:.3f}, {cl.get('center', [0, 0])[1]:.3f})</td>
        </tr>"""

    map_images = ""
    for name, filename in map_files.items():
        map_images += f"""
        <div class="map-card">
            <h4>{name}</h4>
            <img src="/static/outputs/{filename}" alt="{name}" />
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تقرير التحليل - {aoi_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f6fa; direction: rtl; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #e67e22, #d35400); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .section {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        .section h2 {{ color: #e67e22; margin-bottom: 15px; font-size: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px 12px; text-align: right; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; color: #555; font-weight: 600; }}
        .maps-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
        .map-card {{ background: #f8f9fa; border-radius: 8px; padding: 10px; text-align: center; }}
        .map-card img {{ max-width: 100%; border-radius: 6px; }}
        .map-card h4 {{ margin-bottom: 8px; color: #333; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: #e67e22; }}
        .stat-card .label {{ color: #777; font-size: 13px; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>تقرير التحليل الجيومكاني</h1>
            <p>المنطقة: {aoi_name} | التاريخ: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
        </div>

        <div class="section">
            <h2>ملخص النتائج</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="value">{classifications.get('total_detections', 0)}</div>
                    <div class="label">فئات مكتشفة</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(cluster_info)}</div>
                    <div class="label">مجموعات مكانية</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(map_files)}</div>
                    <div class="label">خرائط احتمالية</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>التصنيفات المكتشفة</h2>
            <table>
                <thead>
                    <tr>
                        <th>الفئة</th>
                        <th>Category</th>
                        <th>متوسط الاحتمال</th>
                        <th>أعلى احتمال</th>
                        <th>الثقة</th>
                        <th>عدد النقاط</th>
                    </tr>
                </thead>
                <tbody>{category_rows}</tbody>
            </table>
        </div>

        <div class="section">
            <h2>المجموعات المكانية</h2>
            <table>
                <thead>
                    <tr>
                        <th>المجموعة</th>
                        <th>الفئة</th>
                        <th>الاحتمال</th>
                        <th>الحجم</th>
                        <th>الموقع</th>
                    </tr>
                </thead>
                <tbody>{cluster_rows}</tbody>
            </table>
        </div>

        <div class="section">
            <h2>خرائط الاحتمالية</h2>
            <div class="maps-grid">{map_images}</div>
        </div>
    </div>
</body>
</html>"""

    filename = f"{job_id}_report.html"
    filepath = OUTPUTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filename
