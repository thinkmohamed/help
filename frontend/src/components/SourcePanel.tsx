import { useMemo } from 'react';
import type { Source } from '../api/client';

interface Props {
  sources: Source[];
  selected: Set<string>;
  onToggle: (id: string) => void;
}

const PROVIDER_LABELS: Record<string, string> = {
  copernicus: 'Copernicus Dataspace',
  usgs: 'USGS EarthExplorer',
  gee: 'Google Earth Engine',
  corona: 'CORONA Atlas',
};

export function SourcePanel({ sources, selected, onToggle }: Props) {
  const grouped = useMemo(() => {
    const m = new Map<string, Source[]>();
    sources.forEach((s) => {
      if (!m.has(s.provider)) m.set(s.provider, []);
      m.get(s.provider)!.push(s);
    });
    return m;
  }, [sources]);

  return (
    <div className="section">
      <h2>مصادر البيانات ({selected.size}/{sources.length})</h2>
      {[...grouped.entries()].map(([provider, items]) => (
        <div className="source-group" key={provider}>
          <div className="group-title">
            {PROVIDER_LABELS[provider] ?? provider}
            {' '}
            <span className={`tag ${items[0].authenticated ? 'ok' : 'warn'}`}>
              {items[0].authenticated ? 'مسجّل' : 'تجريبي'}
            </span>
          </div>
          {items.map((s) => (
            <div
              key={s.id}
              className={`source-item ${selected.has(s.id) ? 'selected' : ''}`}
              onClick={() => onToggle(s.id)}
            >
              <input
                type="checkbox"
                checked={selected.has(s.id)}
                onChange={() => onToggle(s.id)}
                onClick={(e) => e.stopPropagation()}
              />
              <div>
                <div className="label">{s.label}</div>
                <div className="meta">
                  {s.category} · {s.bands.join(', ')}
                </div>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
