// src/pages/PersonaInspector.jsx — Page 5
import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../api';

const ARCHETYPE_META = {
  happy_customer:        { label: 'Happy Customer',       cls: 'badge-green',  dot: 'dot-happy', color: '#3fb950', weight: '30%' },
  neutral_passive:       { label: 'Neutral Passive',      cls: 'badge-blue',   dot: 'dot-neutral', color: '#58a6ff', weight: '25%' },
  frustrated_detractor:  { label: 'Frustrated Detractor', cls: 'badge-red',    dot: 'dot-frustrated', color: '#f78166', weight: '20%' },
  delivery_focused:      { label: 'Delivery Focused',     cls: 'badge-orange', dot: 'dot-delivery', color: '#ffa657', weight: '15%' },
  value_seeker:          { label: 'Value Seeker',         cls: 'badge-purple', dot: 'dot-value', color: '#d2a8ff', weight: '10%' },
};

export default function PersonaInspector() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const runId = params.get('run_id');
  const [personas, setPersonas] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/personas/', { params: { run_id: runId || undefined, archetype: filter || undefined } })
      .then(r => setPersonas(r.data))
      .finally(() => setLoading(false));
  }, [runId, filter]);

  const counts = personas.reduce((acc, p) => { acc[p.archetype] = (acc[p.archetype] || 0) + 1; return acc; }, {});

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>Persona Inspector</h1>
        <p>{personas.length} personas generated</p>
      </div>

      {/* Archetype distribution */}
      <div className="grid-stat mb-24">
        {Object.entries(ARCHETYPE_META).map(([key, meta]) => (
          <div key={key} className="stat-card" style={{ cursor: 'pointer', border: filter === key ? `1px solid ${meta.color}` : undefined }}
            onClick={() => setFilter(f => f === key ? '' : key)}>
            <div className="flex flex-center gap-8">
              <span className={`dot ${meta.dot}`} />
              <span className="stat-label">{meta.label}</span>
            </div>
            <span className="stat-value" style={{ color: meta.color }}>{counts[key] || 0}</span>
            <span className="stat-sub">Target: {meta.weight}</span>
          </div>
        ))}
      </div>

      {filter && (
        <div className="flex-between mb-16">
          <span className="text-secondary">Filtered: <span className={`badge ${ARCHETYPE_META[filter]?.cls}`}>{ARCHETYPE_META[filter]?.label}</span></span>
          <button className="btn btn-ghost btn-sm" onClick={() => setFilter('')}>Clear filter</button>
        </div>
      )}

      {/* Persona Cards Grid */}
      {loading ? <p className="text-muted pulse">Loading personas…</p> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
          {personas.slice(0, 100).map(p => {
            const meta = ARCHETYPE_META[p.archetype] || {};
            return (
              <div key={p.id} className="card" style={{ cursor: 'pointer', transition: 'border-color 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = meta.color}
                onMouseLeave={e => e.currentTarget.style.borderColor = ''}
                onClick={() => navigate(`/responses?run_id=${runId}&persona_id=${p.id}`)}>
                <div className="flex-between mb-8">
                  <span className={`badge ${meta.cls}`}>{meta.label}</span>
                  <span className="text-muted text-mono" style={{ fontSize: '0.65rem' }}>{p.id?.slice(0, 6)}…</span>
                </div>
                <div className="flex flex-center gap-8 mb-8">
                  <span style={{ fontSize: '1.3rem' }}>
                    {p.age < 30 ? '🧑' : p.age < 50 ? '👤' : '🧓'}
                  </span>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Age {p.age}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{p.city}, {p.region}</div>
                  </div>
                </div>
                <div className="flex gap-4" style={{ flexWrap: 'wrap' }}>
                  <span className="badge badge-blue">{p.category_pref}</span>
                  <span className="badge" style={{ background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                    Sensitivity: {(p.delivery_sensitivity * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
      {personas.length > 100 && (
        <p className="text-muted" style={{ marginTop: 16, fontSize: '0.8rem' }}>
          Showing first 100 of {personas.length} personas.
        </p>
      )}
    </div>
  );
}
