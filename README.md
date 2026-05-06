# نظام التحليل الجيومكاني - Geospatial Analysis System

نظام متكامل للتحليل الجيومكاني والاستكشاف الأثري والجيولوجي باستخدام بيانات الأقمار الصناعية والذكاء الاصطناعي.

A comprehensive geospatial analysis system for archaeological and geological exploration using multi-source satellite data and AI/ML models.

## المميزات الرئيسية

### مصادر البيانات (4 مصادر - 14 طبقة)

| المصدر | الطبقات |
|--------|---------|
| **Copernicus Dataspace** | Sentinel-2 (بصري 10م), Sentinel-1 SAR (رادار), Sentinel-3 OLCI (حراري), Sentinel-5P (غازات) |
| **USGS EarthExplorer** | Landsat 8/9 (بصري 30م), Landsat 1972 (أرشيف), ASTER (حراري 90م), ASTER GDEM (ارتفاعات 30م) |
| **Google Earth Engine** | SRTM DEM 30m, ALOS PALSAR (رادار L-band), MODIS (حراري يومي), InSAR Coherence |
| **CORONA Atlas** | CORONA 1960-1972 (1.8م), Stereo 3D (تجسيم) |

### طبقات المعالجة (5 تحليلات)
- **التحليل المتعدد الطيفي** - NDVI, NDWI, NDBI, نسب المعادن الطينية والحديد
- **التحليل الراداري متعدد التردد** - نسبة الاستطارة الخلفية, التماسك الاستقطابي, كشف المعالم تحت السطحية
- **التحليل الحراري** - الشذوذات الحرارية, القصور الحراري, مؤشرات المياه الجوفية
- **التحليل الجيومورفولوجي** - الانحدار, الانحناء, TPI, كشف المعالم الخطية والدائرية
- **التحليل التاريخي (6 عقود)** - كشف التغييرات, المعالم المختفية, نشاط التنقيب

### نماذج الذكاء الاصطناعي (4 نماذج)
- **U-Net** - شبكة عصبية عميقة للتصنيف الدلالي
- **Random Forest** - مصنف متعدد الفئات
- **Isolation Forest** - كشف الشذوذات
- **DBSCAN** - التجميع المكاني

### نظام التصويت (Ensemble)
تصويت مرجح يجمع نتائج جميع النماذج لإنتاج تصنيفات موثوقة.

### فئات الاكتشاف (5 فئات)
1. 💧 **مياه جوفية** - Groundwater
2. 🔨 **حفر تنقيب حديثة** - Recent Excavation
3. 🏛️ **آثار قديمة** - Ancient Ruins
4. 💎 **معادن مذابة** - Dissolved Minerals
5. 🕳️ **فراغات تحت الأرض** - Underground Voids

## التثبيت والتشغيل

### المتطلبات
- Python 3.10+
- pip

### التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/thinkmohamed/help.git
cd help

# إنشاء بيئة افتراضية
python3 -m venv venv
source venv/bin/activate

# تثبيت التبعيات
pip install -r backend/requirements.txt

# تشغيل التطبيق
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### الاستخدام
1. افتح المتصفح على `http://localhost:8000`
2. ارسم مضلعًا على الخريطة لتحديد منطقة الاهتمام (AOI)
3. اختر مصادر البيانات والطبقات المطلوبة
4. حدد أنواع التحليل ونماذج الذكاء الاصطناعي
5. اضغط **بدء التحليل**
6. تابع التقدم عبر مخطط سير العمل
7. عند الانتهاء، استعرض النتائج وحمّل التقارير

## بنية المشروع

```
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Configuration
│   │   ├── api/routes.py           # API endpoints
│   │   ├── models/schemas.py       # Pydantic models
│   │   └── services/
│   │       ├── pipeline.py         # Pipeline orchestrator
│   │       ├── data_sources/       # Satellite data connectors
│   │       │   ├── copernicus.py   # Sentinel 1/2/3/5P
│   │       │   ├── usgs.py        # Landsat, ASTER
│   │       │   ├── gee.py         # SRTM, ALOS PALSAR, MODIS
│   │       │   └── corona.py      # CORONA Atlas
│   │       ├── processing/        # Analysis modules
│   │       │   ├── spectral.py    # Multi-spectral analysis
│   │       │   ├── radar.py       # Multi-frequency radar
│   │       │   ├── thermal.py     # Thermal analysis
│   │       │   ├── geomorphological.py
│   │       │   └── historical.py  # 6-decade historical
│   │       ├── fusion/
│   │       │   └── data_fusion.py # Data fusion engine
│   │       ├── ml/                # ML models
│   │       │   ├── unet.py        # U-Net neural network
│   │       │   ├── random_forest.py
│   │       │   ├── isolation_forest.py
│   │       │   └── dbscan.py      # Spatial clustering
│   │       ├── ensemble/
│   │       │   └── voting.py      # Ensemble voting system
│   │       └── output/
│   │           ├── maps.py        # Probability maps
│   │           └── reports.py     # JSON/HTML reports
│   └── requirements.txt
├── frontend/
│   ├── index.html                 # Main UI (Arabic RTL)
│   ├── css/style.css              # Dark theme styles
│   └── js/app.js                  # Map, analysis, results logic
└── static/outputs/                # Generated maps & reports
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/data-sources` | Available satellite data sources |
| `GET` | `/api/analysis-types` | Analysis types and ML models |
| `POST` | `/api/analyze` | Start analysis job |
| `GET` | `/api/status/{job_id}` | Get job status & results |
| `GET` | `/api/jobs` | List all jobs |

## التقنيات المستخدمة

- **Backend**: FastAPI, NumPy, SciPy, scikit-learn, Pillow
- **Frontend**: HTML5, CSS3, JavaScript, Leaflet.js
- **ML**: U-Net (custom), Random Forest, Isolation Forest, DBSCAN
