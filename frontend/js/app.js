/* =============================================
   Geospatial Analysis System - Frontend Logic
   نظام التحليل الجيومكاني
   ============================================= */

const API_BASE = window.location.origin;

// --- State ---
let map;
let drawnItems;
let aoiGeometry = null;
let currentJobId = null;
let pollInterval = null;
let selectedSources = new Set(["copernicus", "usgs", "gee", "corona"]);
let selectedLayers = new Set();
let dataSources = [];

// --- Initialize ---
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadDataSources();
  loadAnalysisTypes();
});

// --- Map ---
function initMap() {
  map = L.map("map", {
    center: [29.9792, 31.1342], // Giza, Egypt
    zoom: 6,
    zoomControl: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "OpenStreetMap",
    maxZoom: 19,
  }).addTo(map);

  drawnItems = new L.FeatureGroup();
  map.addLayer(drawnItems);

  const drawControl = new L.Control.Draw({
    draw: {
      polygon: {
        allowIntersection: false,
        shapeOptions: {
          color: "#e67e22",
          weight: 2,
          fillOpacity: 0.15,
        },
      },
      rectangle: {
        shapeOptions: {
          color: "#e67e22",
          weight: 2,
          fillOpacity: 0.15,
        },
      },
      circle: false,
      circlemarker: false,
      marker: false,
      polyline: false,
    },
    edit: {
      featureGroup: drawnItems,
    },
  });
  map.addControl(drawControl);

  map.on(L.Draw.Event.CREATED, (e) => {
    drawnItems.clearLayers();
    drawnItems.addLayer(e.layer);
    aoiGeometry = e.layer.toGeoJSON().geometry;
    updateAOIStatus(true);
  });

  map.on(L.Draw.Event.DELETED, () => {
    aoiGeometry = null;
    updateAOIStatus(false);
  });
}

function updateAOIStatus(hasAOI) {
  const box = document.getElementById("aoi-status");
  box.classList.remove("hidden", "success", "error");
  if (hasAOI) {
    box.classList.add("success");
    box.innerHTML =
      '<span class="status-icon">&#9679;</span><span class="status-text">تم تحديد المنطقة الجغرافية</span>';
  } else {
    box.classList.add("error");
    box.innerHTML =
      '<span class="status-icon">&#9679;</span><span class="status-text">لم يتم تحديد منطقة</span>';
  }
}

// --- Data Sources ---
async function loadDataSources() {
  try {
    const resp = await fetch(`${API_BASE}/api/data-sources`);
    const data = await resp.json();
    dataSources = data.sources;
    renderDataSources(dataSources);
  } catch {
    renderDefaultSources();
  }
}

function renderDataSources(sources) {
  const container = document.getElementById("data-sources-list");
  container.innerHTML = "";

  sources.forEach((src) => {
    const isActive = selectedSources.has(src.id);
    const div = document.createElement("div");
    div.className = `source-item${isActive ? " active" : ""}`;
    div.id = `source-${src.id}`;

    let layerTags = src.layers
      .map((l) => {
        selectedLayers.add(l.id);
        return `<span class="layer-tag selected" data-layer="${l.id}" onclick="toggleLayer(this, '${l.id}')">${l.name_ar} (${l.resolution})</span>`;
      })
      .join("");

    div.innerHTML = `
      <div class="source-header" onclick="toggleSource('${src.id}')">
        <input type="checkbox" ${isActive ? "checked" : ""} />
        <span class="source-name">${src.name_ar} <span class="source-name-en">${src.name}</span></span>
      </div>
      <div class="source-layers">${layerTags}</div>
    `;
    container.appendChild(div);
  });
}

function renderDefaultSources() {
  const defaults = [
    {
      id: "copernicus",
      name: "Copernicus Dataspace",
      name_ar: "كوبرنيكوس",
      layers: [
        { id: "sentinel2_optical", name_ar: "بصري 10م", resolution: "10m" },
        { id: "sentinel1_sar", name_ar: "رادار SAR", resolution: "10m" },
        { id: "sentinel3_thermal", name_ar: "حراري OLCI", resolution: "1km" },
        { id: "sentinel5p_gas", name_ar: "غازات", resolution: "5.5km" },
      ],
    },
    {
      id: "usgs",
      name: "USGS EarthExplorer",
      name_ar: "USGS المسح الجيولوجي",
      layers: [
        { id: "landsat89_optical", name_ar: "بصري 30م", resolution: "30m" },
        { id: "landsat_archive", name_ar: "أرشيف 1972", resolution: "60m" },
        { id: "aster_thermal", name_ar: "حراري 90م", resolution: "90m" },
        { id: "aster_gdem", name_ar: "ارتفاعات 30م", resolution: "30m" },
      ],
    },
    {
      id: "gee",
      name: "Google Earth Engine",
      name_ar: "محرك جوجل للأرض",
      layers: [
        { id: "srtm_dem", name_ar: "ارتفاعات 30م", resolution: "30m" },
        { id: "alos_palsar", name_ar: "رادار L-band", resolution: "25m" },
        { id: "modis_thermal", name_ar: "حراري يومي", resolution: "1km" },
        { id: "insar_coherence", name_ar: "تماسك InSAR", resolution: "10m" },
      ],
    },
    {
      id: "corona",
      name: "CORONA Atlas",
      name_ar: "أطلس كورونا",
      layers: [
        {
          id: "corona_historical",
          name_ar: "صور تاريخية 1.8م",
          resolution: "1.8m",
        },
        { id: "stereo_3d", name_ar: "تجسيم 3D", resolution: "2m" },
      ],
    },
  ];
  renderDataSources(defaults);
}

function toggleSource(sourceId) {
  const el = document.getElementById(`source-${sourceId}`);
  const cb = el.querySelector('input[type="checkbox"]');

  if (selectedSources.has(sourceId)) {
    selectedSources.delete(sourceId);
    el.classList.remove("active");
    cb.checked = false;
    el.querySelectorAll(".layer-tag").forEach((tag) => {
      selectedLayers.delete(tag.dataset.layer);
      tag.classList.remove("selected");
    });
  } else {
    selectedSources.add(sourceId);
    el.classList.add("active");
    cb.checked = true;
    el.querySelectorAll(".layer-tag").forEach((tag) => {
      selectedLayers.add(tag.dataset.layer);
      tag.classList.add("selected");
    });
  }
}

function toggleLayer(el, layerId) {
  if (selectedLayers.has(layerId)) {
    selectedLayers.delete(layerId);
    el.classList.remove("selected");
  } else {
    selectedLayers.add(layerId);
    el.classList.add("selected");
  }
}

// --- Analysis Types ---
async function loadAnalysisTypes() {
  try {
    const resp = await fetch(`${API_BASE}/api/analysis-types`);
    const data = await resp.json();
    renderAnalysisTypes(data);
  } catch {
    renderDefaultAnalysisTypes();
  }
}

function renderAnalysisTypes(data) {
  const analysisContainer = document.getElementById("analysis-types");
  analysisContainer.innerHTML = data.analyses
    .map(
      (a) => `
    <label class="checkbox-item">
      <input type="checkbox" value="${a.id}" checked />
      <span>${a.name_ar}</span>
    </label>
  `
    )
    .join("");

  const mlContainer = document.getElementById("ml-models");
  mlContainer.innerHTML = data.ml_models
    .map(
      (m) => `
    <label class="checkbox-item">
      <input type="checkbox" value="${m.id}" checked />
      <span>${m.name_ar}</span>
    </label>
  `
    )
    .join("");
}

function renderDefaultAnalysisTypes() {
  const analyses = [
    { id: "spectral", name_ar: "التحليل المتعدد الطيفي" },
    { id: "radar", name_ar: "التحليل الراداري متعدد التردد" },
    { id: "thermal", name_ar: "التحليل الحراري" },
    { id: "geomorphological", name_ar: "التحليل الجيومورفولوجي" },
    { id: "historical", name_ar: "التحليل التاريخي (6 عقود)" },
  ];
  const models = [
    { id: "unet", name_ar: "شبكة عصبية عميقة U-Net" },
    { id: "random_forest", name_ar: "متعدد الفئات Random Forest" },
    { id: "isolation_forest", name_ar: "للشذوذات Isolation Forest" },
    { id: "dbscan", name_ar: "التجميع المكاني DBSCAN" },
  ];
  renderAnalysisTypes({ analyses, ml_models: models });
}

// --- Analysis ---
async function startAnalysis() {
  if (!aoiGeometry) {
    updateAOIStatus(false);
    return;
  }

  const runBtn = document.getElementById("btn-run");
  runBtn.disabled = true;
  runBtn.innerHTML = "جاري التحليل...";

  const selectedAnalyses = [
    ...document.querySelectorAll('#analysis-types input[type="checkbox"]:checked'),
  ].map((cb) => cb.value);
  const selectedModels = [
    ...document.querySelectorAll('#ml-models input[type="checkbox"]:checked'),
  ].map((cb) => cb.value);

  const requestBody = {
    aoi: {
      geometry: aoiGeometry,
      name: document.getElementById("aoi-name").value || "منطقة تحليل",
      buffer_km: parseFloat(document.getElementById("aoi-buffer").value) || 5,
    },
    data_sources: {
      sources: [...selectedSources],
      layers: [...selectedLayers],
      date_from: document.getElementById("date-from").value || null,
      date_to: document.getElementById("date-to").value || null,
      max_cloud_cover: parseInt(document.getElementById("cloud-cover").value),
    },
    analysis: {
      analyses: selectedAnalyses,
      ml_models: selectedModels,
      ensemble_threshold:
        parseInt(document.getElementById("threshold").value) / 100,
    },
  };

  try {
    const resp = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    const data = await resp.json();
    currentJobId = data.job_id;

    showProgress();
    startPolling();
  } catch (err) {
    runBtn.disabled = false;
    runBtn.innerHTML =
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> بدء التحليل';
    alert("خطأ في بدء التحليل: " + err.message);
  }
}

function showProgress() {
  document.getElementById("progress-panel").classList.remove("hidden");
  document.getElementById("results-panel").classList.add("hidden");
}

function startPolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(pollStatus, 1500);
}

async function pollStatus() {
  if (!currentJobId) return;

  try {
    const resp = await fetch(`${API_BASE}/api/status/${currentJobId}`);
    const data = await resp.json();

    updateProgress(data);
    updateFlowDiagram(data);

    if (data.status === "completed" || data.status === "failed") {
      clearInterval(pollInterval);
      pollInterval = null;

      const runBtn = document.getElementById("btn-run");
      runBtn.disabled = false;
      runBtn.innerHTML =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> بدء التحليل';

      if (data.status === "completed") {
        showResults(data);
      }
    }
  } catch {
    // retry next interval
  }
}

function updateProgress(data) {
  const fill = document.getElementById("progress-fill");
  const percent = document.getElementById("progress-percent");
  const message = document.getElementById("progress-message");

  fill.style.width = data.progress + "%";
  percent.textContent = Math.round(data.progress) + "%";
  message.textContent = data.message || "";

  // Pipeline stages
  const stagesEl = document.getElementById("pipeline-stages");
  const stageNames = {
    pending: "في الانتظار",
    fetching_data: "جلب البيانات",
    processing: "المعالجة",
    analyzing: "التحليل",
    fusing: "دمج البيانات",
    classifying: "التصنيف",
    generating_output: "إنشاء المخرجات",
    completed: "مكتمل",
    failed: "فشل",
  };

  const statusName = stageNames[data.status] || data.status;
  const stageOrder = [
    "fetching_data",
    "processing",
    "fusing",
    "classifying",
    "generating_output",
  ];
  const currentIdx = stageOrder.indexOf(data.status);

  stagesEl.innerHTML = stageOrder
    .map((s, i) => {
      let cls = "stage-tag";
      if (i < currentIdx) cls += " completed";
      else if (i === currentIdx) cls += " active";
      return `<span class="${cls}">${stageNames[s]}</span>`;
    })
    .join("");
}

function updateFlowDiagram(data) {
  const stageMap = {
    pending: "aoi",
    fetching_data: "data",
    processing: "process",
    fusing: "fusion",
    classifying: "ml",
    generating_output: "output",
    completed: "output",
  };

  const flowOrder = [
    "aoi",
    "data",
    "process",
    "fusion",
    "ml",
    "ensemble",
    "output",
  ];
  const currentStage = stageMap[data.status] || "aoi";
  const currentIdx = flowOrder.indexOf(currentStage);

  document.querySelectorAll(".flow-step").forEach((el) => {
    const stage = el.dataset.stage;
    const idx = flowOrder.indexOf(stage);
    el.classList.remove("active", "completed");

    if (data.status === "completed") {
      el.classList.add("completed");
    } else if (idx < currentIdx) {
      el.classList.add("completed");
    } else if (idx === currentIdx) {
      el.classList.add("active");
    }
  });
}

// --- Results ---
function showResults(data) {
  document.getElementById("progress-panel").classList.add("hidden");
  const resultsPanel = document.getElementById("results-panel");
  resultsPanel.classList.remove("hidden");

  const detectionsGrid = document.getElementById("detections-grid");
  const categoryColors = {
    groundwater: "#0077BE",
    excavation: "#FF5733",
    ancient_ruins: "#FFC300",
    dissolved_minerals: "#2ECC71",
    underground_voids: "#9B59B6",
  };

  if (data.detections && data.detections.length > 0) {
    detectionsGrid.innerHTML = data.detections
      .map((det) => {
        const color = categoryColors[det.category] || "#888";
        const prob = (det.probability * 100).toFixed(1);
        const confClass =
          det.probability > 0.7
            ? "high"
            : det.probability > 0.5
            ? "medium"
            : "low";
        const confText =
          det.probability > 0.7
            ? "عالية"
            : det.probability > 0.5
            ? "متوسطة"
            : "منخفضة";

        return `
        <div class="detection-card" style="border-right: 3px solid ${color}">
          <div class="category-name">${det.category_ar}</div>
          <div class="category-en">${det.category}</div>
          <div class="probability" style="color: ${color}">${prob}%</div>
          <div class="details">${det.details}</div>
          <span class="confidence-badge confidence-${confClass}">ثقة ${confText}</span>
        </div>
      `;
      })
      .join("");
  } else {
    detectionsGrid.innerHTML =
      '<p style="color: var(--text-muted); padding: 10px;">لم يتم اكتشاف أي نتائج</p>';
  }

  // Maps gallery
  const mapsGallery = document.getElementById("maps-gallery");
  if (data.map_url) {
    const mapNames = {
      combined: "خريطة مدمجة",
      groundwater: "مياه جوفية",
      excavation: "حفر تنقيب",
      ancient_ruins: "آثار قديمة",
      dissolved_minerals: "معادن مذابة",
      underground_voids: "فراغات تحت الأرض",
    };

    const mapTypes = [
      "combined",
      "groundwater",
      "excavation",
      "ancient_ruins",
      "dissolved_minerals",
      "underground_voids",
    ];
    mapsGallery.innerHTML = mapTypes
      .map((type) => {
        const url = `/static/outputs/${currentJobId}_${type}.png`;
        return `
        <div class="map-thumb" onclick="window.open('${url}', '_blank')">
          <img src="${url}" alt="${type}" onerror="this.parentElement.style.display='none'" />
          <div class="map-label">${mapNames[type] || type}</div>
        </div>
      `;
      })
      .join("");
  }
}

function downloadReport(format) {
  if (!currentJobId) return;
  const ext = format === "json" ? "json" : "html";
  window.open(`/static/outputs/${currentJobId}_report.${ext}`, "_blank");
}

function resetAnalysis() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  currentJobId = null;
  aoiGeometry = null;

  if (drawnItems) drawnItems.clearLayers();

  document.getElementById("aoi-name").value = "";
  document.getElementById("aoi-status").classList.add("hidden");
  document.getElementById("progress-panel").classList.add("hidden");
  document.getElementById("results-panel").classList.add("hidden");

  const runBtn = document.getElementById("btn-run");
  runBtn.disabled = false;
  runBtn.innerHTML =
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> بدء التحليل';

  document.querySelectorAll(".flow-step").forEach((el) => {
    el.classList.remove("active", "completed");
  });
}
