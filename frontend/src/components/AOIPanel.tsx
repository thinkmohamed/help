import { useState } from 'react';
import type { AOI } from '../api/client';

interface Props {
  aois: AOI[];
  selectedId: string | null;
  drawnGeometry: GeoJSON.Polygon | null;
  onSelect: (id: string) => void;
  onSave: (name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onClearDrawing: () => void;
}

export function AOIPanel({
  aois,
  selectedId,
  drawnGeometry,
  onSelect,
  onSave,
  onDelete,
  onClearDrawing,
}: Props) {
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);

  const save = async () => {
    if (!name || !drawnGeometry) return;
    setBusy(true);
    try {
      await onSave(name);
      setName('');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="section">
      <h2>المنطقة الجغرافية AOI</h2>
      {drawnGeometry ? (
        <div className="row" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
          <input
            placeholder="اسم المنطقة (مثال: هضبة الجيزة)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <div className="row">
            <button onClick={save} disabled={!name || busy} style={{ flex: 1 }}>
              {busy ? 'جارٍ الحفظ…' : 'حفظ المنطقة'}
            </button>
            <button className="ghost" onClick={onClearDrawing}>إلغاء</button>
          </div>
        </div>
      ) : (
        <div className="muted">ارسم مضلعاً أو مستطيلاً على الخريطة لتحديد المنطقة.</div>
      )}

      <div style={{ height: 12 }} />

      {aois.length === 0 ? (
        <div className="empty">لا توجد مناطق محفوظة بعد</div>
      ) : (
        <div className="aoi-list">
          {aois.map((a) => (
            <div
              key={a.id}
              className={`aoi-item ${selectedId === a.id ? 'selected' : ''}`}
              onClick={() => onSelect(a.id)}
              role="button"
            >
              <div>
                <div className="name">{a.name}</div>
                <div className="muted">
                  {a.bbox[0].toFixed(3)}, {a.bbox[1].toFixed(3)} → {a.bbox[2].toFixed(3)},{' '}
                  {a.bbox[3].toFixed(3)}
                </div>
              </div>
              <button
                className="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(a.id);
                }}
              >
                حذف
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
