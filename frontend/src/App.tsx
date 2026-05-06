import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, AOI, Job, JobResult, Source } from './api/client';
import { MapView } from './components/MapView';
import { SourcePanel } from './components/SourcePanel';
import { AOIPanel } from './components/AOIPanel';
import { WorkflowPanel } from './components/WorkflowPanel';
import { ResultsPanel } from './components/ResultsPanel';

const DEFAULT_SELECTED_SOURCES = [
  'sentinel-2',
  'sentinel-1',
  'srtm',
  'modis',
  'corona-1960',
  'aster-gdem',
  'landsat-89',
  'landsat-1972',
];

export default function App() {
  const [aois, setAOIs] = useState<AOI[]>([]);
  const [selectedAOIId, setSelectedAOIId] = useState<string | null>(null);
  const [drawnGeometry, setDrawnGeometry] = useState<GeoJSON.Polygon | null>(null);

  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSources, setSelectedSources] = useState<Set<string>>(
    new Set(DEFAULT_SELECTED_SOURCES),
  );

  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<JobResult | null>(null);
  const [visibleTargets, setVisibleTargets] = useState<Set<string>>(
    new Set(['underground_voids', 'buried_metals', 'ancient_ruins', 'modern_excavations', 'groundwater']),
  );

  const [version, setVersion] = useState<string>('');

  const pollRef = useRef<number | null>(null);

  const refreshAOIs = useCallback(async () => {
    const list = await api.listAOI();
    setAOIs(list);
  }, []);

  useEffect(() => {
    api.health().then((h) => setVersion(h.version)).catch(() => undefined);
    api.listSources().then(setSources).catch(() => undefined);
    refreshAOIs();
  }, [refreshAOIs]);

  const selectedAOI = useMemo(
    () => aois.find((a) => a.id === selectedAOIId) ?? null,
    [aois, selectedAOIId],
  );

  const toggleSource = useCallback((id: string) => {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleTarget = useCallback((key: string) => {
    setVisibleTargets((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const saveAOI = useCallback(
    async (name: string) => {
      if (!drawnGeometry) return;
      const created = await api.createAOI(name, drawnGeometry);
      setDrawnGeometry(null);
      await refreshAOIs();
      setSelectedAOIId(created.id);
    },
    [drawnGeometry, refreshAOIs],
  );

  const deleteAOI = useCallback(
    async (id: string) => {
      await api.deleteAOI(id);
      if (selectedAOIId === id) setSelectedAOIId(null);
      await refreshAOIs();
    },
    [selectedAOIId, refreshAOIs],
  );

  const stopPoll = () => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startJob = useCallback(async () => {
    if (!selectedAOI || selectedSources.size === 0) return;
    stopPoll();
    setResult(null);
    const created = await api.createJob(
      selectedAOI.id,
      [...selectedSources],
      [128, 128],
    );
    setJob(created);
    pollRef.current = window.setInterval(async () => {
      try {
        const j = await api.getJob(created.id);
        setJob(j);
        if (j.status === 'completed') {
          stopPoll();
          const r = await api.getResult(j.id);
          setResult(r);
        } else if (j.status === 'failed') {
          stopPoll();
        }
      } catch {
        stopPoll();
      }
    }, 600);
  }, [selectedAOI, selectedSources]);

  useEffect(() => () => stopPoll(), []);

  const canRun = !!selectedAOI && selectedSources.size > 0 && job?.status !== 'running';

  return (
    <div className="app">
      <header className="app-header">
        <h1>
          <span className="dot" />
          GeoIntel — منصة الاستخبارات الجغرافية المكانية
        </h1>
        <div className="meta">
          <span className="tag">v{version || '—'}</span>
          <span>{aois.length} منطقة · {sources.length} مصدر</span>
        </div>
      </header>

      <aside className="sidebar right">
        <AOIPanel
          aois={aois}
          selectedId={selectedAOIId}
          drawnGeometry={drawnGeometry}
          onSelect={setSelectedAOIId}
          onSave={saveAOI}
          onDelete={deleteAOI}
          onClearDrawing={() => setDrawnGeometry(null)}
        />
        <SourcePanel
          sources={sources}
          selected={selectedSources}
          onToggle={toggleSource}
        />
      </aside>

      <main className="map-container">
        <div className="toolbar">
          {selectedAOI ? (
            <>
              <span className="badge">{selectedAOI.name}</span>
              <span className="muted">المصادر: {selectedSources.size}</span>
            </>
          ) : (
            <span className="muted">ارسم AOI أو اختر منطقة محفوظة</span>
          )}
        </div>

        <MapView
          selectedAOI={selectedAOI}
          drawnGeometry={drawnGeometry}
          onGeometryDrawn={setDrawnGeometry}
          result={result}
          visibleTargetKeys={visibleTargets}
        />

        <div className="run-bar">
          <span className="info">
            {job?.status === 'running' && 'جارٍ التنفيذ…'}
            {job?.status === 'completed' && `اكتمل في ${result?.timings.total_s?.toFixed(2)}ث`}
            {job?.status === 'failed' && 'فشل'}
            {!job && 'جاهز للتشغيل'}
          </span>
          <button onClick={startJob} disabled={!canRun}>
            {job?.status === 'running' ? '…' : 'تشغيل المعالجة'}
          </button>
        </div>
      </main>

      <aside className="sidebar">
        <WorkflowPanel job={job} />
        <ResultsPanel
          result={result}
          visible={visibleTargets}
          onToggleTarget={toggleTarget}
        />
      </aside>
    </div>
  );
}
