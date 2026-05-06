import type { JobResult, TargetResult } from '../api/client';

interface Props {
  result: JobResult | null;
  visible: Set<string>;
  onToggleTarget: (key: string) => void;
}

export function ResultsPanel({ result, visible, onToggleTarget }: Props) {
  if (!result) {
    return (
      <div className="section">
        <h2>النتائج</h2>
        <div className="empty">شغّل المهمة للحصول على خرائط احتمالية.</div>
      </div>
    );
  }

  const targets = Object.values(result.targets) as TargetResult[];
  const totalTime = result.timings.total_s ?? 0;

  return (
    <div className="section">
      <h2>النتائج · {result.n_features} ميزة · {totalTime.toFixed(2)}ث</h2>
      {targets.map((t) => (
        <div
          key={t.key}
          className="target-card"
          style={{ borderLeftColor: t.color, cursor: 'pointer', opacity: visible.has(t.key) ? 1 : 0.55 }}
          onClick={() => onToggleTarget(t.key)}
        >
          <div className="head">
            <div>
              <div className="label-ar" style={{ color: t.color }}>{t.label_ar}</div>
              <div className="label-en">{t.label_en}</div>
            </div>
            <div className={`tag ${visible.has(t.key) ? 'ok' : ''}`}>
              {visible.has(t.key) ? 'ظاهر' : 'مخفي'}
            </div>
          </div>
          <div className="stats">
            <div className="stat"><div className="k">أعلى احتمال</div><div className="v">{(t.summary.max_prob * 100).toFixed(0)}%</div></div>
            <div className="stat"><div className="k">متوسط</div><div className="v">{(t.summary.mean_prob * 100).toFixed(1)}%</div></div>
            <div className="stat"><div className="k">تجمعات</div><div className="v">{t.summary.n_clusters}</div></div>
            <div className="stat"><div className="k">ثقة عالية</div><div className="v">{t.summary.high_confidence_px}px</div></div>
          </div>
          <div className="legend-bar" style={{ color: t.color }} />
        </div>
      ))}
      <div className="muted" style={{ marginTop: 10 }}>
        مصادر مستخدمة: {result.sources_used.length}
        {' · '}
        {result.sources_used.some((s) => s.is_synthetic) ? 'بعض البيانات تجريبية' : 'بيانات حقيقية'}
      </div>
    </div>
  );
}
