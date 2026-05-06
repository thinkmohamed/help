import type { Job } from '../api/client';

interface Props {
  job: Job | null;
}

const STAGES: { key: string; label_ar: string }[] = [
  { key: 'fetch', label_ar: 'جلب البيانات' },
  { key: 'multispectral', label_ar: 'تحليل متعدد الطيف' },
  { key: 'radar', label_ar: 'تحليل راداري' },
  { key: 'thermal', label_ar: 'تحليل حراري' },
  { key: 'morphology', label_ar: 'مورفولوجيا 3D' },
  { key: 'historical', label_ar: 'تحليل تاريخي 60 سنة' },
  { key: 'fusion', label_ar: 'دمج البيانات' },
  { key: 'ml.unet', label_ar: 'U-Net تجزئة' },
  { key: 'ml.rf', label_ar: 'Random Forest' },
  { key: 'ml.iso', label_ar: 'Isolation Forest' },
  { key: 'ensemble', label_ar: 'Ensemble' },
  { key: 'clusters', label_ar: 'تجميع DBSCAN' },
];

export function WorkflowPanel({ job }: Props) {
  const seen = new Set<string>();
  job?.progress.forEach((p) => seen.add(p.stage));

  return (
    <div className="section">
      <h2>سير المعالجة {job ? `(${job.status})` : ''}</h2>
      {!job && <div className="muted">قم بإنشاء مهمة لرؤية سير المعالجة.</div>}
      {job && (
        <div className="workflow">
          {STAGES.map((s) => {
            const isDone = seen.has(s.key);
            const last = job.progress.length > 0 ? job.progress[job.progress.length - 1] : null;
            const isLast = last?.stage === s.key && job.status === 'running';
            const cls = isLast ? 'running' : isDone ? 'completed' : '';
            return (
              <div key={s.key} className={`step ${cls}`}>
                <div className="name">{s.label_ar}</div>
                <div className="status">{isLast ? 'جارٍ…' : isDone ? 'تم' : 'بانتظار'}</div>
              </div>
            );
          })}
        </div>
      )}
      {job?.error && (
        <div style={{ marginTop: 10, padding: 8, background: 'rgba(239,68,68,0.15)', borderRadius: 6, fontSize: 12 }}>
          خطأ: {job.error.split('\n')[0]}
        </div>
      )}
    </div>
  );
}
