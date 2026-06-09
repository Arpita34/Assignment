// src/pages/ResponseExplorer.jsx — Page 3
import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Download, X, ChevronLeft, ChevronRight } from 'lucide-react';
import api from '../api';

const ARCHETYPES = {
  happy_customer: { label: 'Happy', cls: 'badge-green' },
  neutral_passive: { label: 'Neutral', cls: 'badge-blue' },
  frustrated_detractor: { label: 'Frustrated', cls: 'badge-red' },
  delivery_focused: { label: 'Delivery', cls: 'badge-orange' },
  value_seeker: { label: 'Value', cls: 'badge-purple' },
};

function CoherenceScore({ score }) {
  const cls = score >= 0.8 ? 'score-high' : score >= 0.6 ? 'score-medium' : 'score-low';
  return <span className={cls}>{(score * 100).toFixed(0)}%</span>;
}

function ResponseDrawer({ row, onClose }) {
  if (!row) return null;
  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="flex-between mb-24">
          <h2>Response Detail</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={14} /></button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="stat-label mb-16">Persona</div>
            <div className="flex flex-center gap-8">
              <span className={`badge ${ARCHETYPES[row.persona_archetype]?.cls || 'badge-blue'}`}>
                {ARCHETYPES[row.persona_archetype]?.label || row.persona_archetype}
              </span>
              <span className="text-muted text-mono" style={{ fontSize: '0.7rem' }}>{row.persona_id?.slice(0, 8)}…</span>
            </div>
          </div>
          {[
            { label: 'Q1 — Satisfaction', value: `${row.q1_satisfaction}/5`, color: row.q1_satisfaction >= 4 ? 'var(--accent-green)' : row.q1_satisfaction <= 2 ? 'var(--accent-red)' : 'var(--accent-orange)' },
            { label: 'Q2 — NPS Score', value: `${row.q2_nps}/10` },
            { label: 'Q3 — Category', value: row.q3_category },
            { label: 'Q4 — Delivery', value: row.q4_delivery_on_time ? '✅ On Time' : '❌ Late' },
          ].map(({ label, value, color }) => (
            <div key={label} className="card">
              <div className="stat-label">{label}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, color: color || 'var(--text-primary)', marginTop: 4 }}>{value}</div>
            </div>
          ))}
          <div className="card">
            <div className="stat-label mb-8">Q5 — Open Text Feedback</div>
            <p style={{ color: 'var(--text-primary)', lineHeight: 1.7, fontStyle: 'italic' }}>"{row.q5_open_text}"</p>
            <div className="flex gap-8" style={{ marginTop: 12 }}>
              <span className="text-muted" style={{ fontSize: '0.72rem' }}>VADER: {row.sentiment_compound?.toFixed(3)}</span>
              <span className="text-muted" style={{ fontSize: '0.72rem' }}>|</span>
              <CoherenceScore score={row.coherence_score} />
            </div>
          </div>
          {row.violations?.length > 0 && (
            <div className="card" style={{ borderColor: 'var(--accent-red)' }}>
              <div className="stat-label mb-8" style={{ color: 'var(--accent-red)' }}>Violations</div>
              {row.violations.map((v, i) => <div key={i} className="text-mono" style={{ fontSize: '0.72rem', color: 'var(--accent-orange)' }}>{v}</div>)}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default function ResponseExplorer() {
  const [params] = useSearchParams();
  const runId = params.get('run_id');
  const [data, setData] = useState({ results: [], total: 0 });
  const [filters, setFilters] = useState({ search: '', q3: '', q1_min: '', q1_max: '' });
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const LIMIT = 20;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/responses/', {
        params: {
          run_id: runId || undefined,
          search: filters.search || undefined,
          q3: filters.q3 || undefined,
          q1_min: filters.q1_min || undefined,
          q1_max: filters.q1_max || undefined,
          limit: LIMIT,
          offset: page * LIMIT,
        },
      });
      setData(res.data);
    } finally {
      setLoading(false);
    }
  }, [runId, filters, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleExport = (format) => {
    window.open(`http://localhost:8000/api/responses/export?run_id=${runId || ''}&format=${format}`);
  };

  const totalPages = Math.ceil(data.total / LIMIT);

  return (
    <div className="page fade-in">
      <div className="page-header flex-between">
        <div>
          <h1>Response Explorer</h1>
          <p>{data.total} responses {runId ? `from run ${runId.slice(0, 8)}` : '(all runs)'}</p>
        </div>
        <div className="flex gap-8">
          <button className="btn btn-ghost btn-sm" onClick={() => handleExport('csv')}><Download size={13} /> CSV</button>
          <button className="btn btn-ghost btn-sm" onClick={() => handleExport('json')}><Download size={13} /> JSON</button>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-16">
        <div className="flex gap-12" style={{ flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 200px' }}>
            <div className="form-label mb-16">Search Q5</div>
            <div className="flex flex-center" style={{ position: 'relative' }}>
              <Search size={13} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
              <input className="form-input" style={{ paddingLeft: 30 }} placeholder="Search feedback…"
                value={filters.search} onChange={e => { setFilters(f => ({ ...f, search: e.target.value })); setPage(0); }} />
            </div>
          </div>
          <div>
            <div className="form-label mb-16">Category (Q3)</div>
            <select className="form-select" style={{ width: 160 }} value={filters.q3}
              onChange={e => { setFilters(f => ({ ...f, q3: e.target.value })); setPage(0); }}>
              <option value="">All</option>
              {['Electronics', 'Clothing', 'Home', 'Other'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <div className="form-label mb-16">Satisfaction Min</div>
            <select className="form-select" style={{ width: 100 }} value={filters.q1_min}
              onChange={e => { setFilters(f => ({ ...f, q1_min: e.target.value })); setPage(0); }}>
              <option value="">Any</option>
              {[1,2,3,4,5].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="table-container mb-16">
        <table className="table">
          <thead>
            <tr>
              <th>Archetype</th>
              <th>Q1 Sat</th>
              <th>Q2 NPS</th>
              <th>Q3 Category</th>
              <th>Q4 Delivery</th>
              <th>Q5 Feedback</th>
              <th>Coherence</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Loading…</td></tr>
            ) : data.results.map(row => {
              const rowCls = row.coherence_score < 0.4 ? 'row-danger' : row.coherence_score < 0.6 ? 'row-warn' : '';
              return (
                <tr key={row.response_id} className={rowCls} onClick={() => setSelected(row)}>
                  <td><span className={`badge ${ARCHETYPES[row.persona_archetype]?.cls || 'badge-blue'}`}>{ARCHETYPES[row.persona_archetype]?.label || row.persona_archetype}</span></td>
                  <td><span style={{ fontWeight: 700, color: row.q1_satisfaction >= 4 ? 'var(--accent-green)' : row.q1_satisfaction <= 2 ? 'var(--accent-red)' : 'var(--accent-orange)' }}>{row.q1_satisfaction}/5</span></td>
                  <td>{row.q2_nps}/10</td>
                  <td>{row.q3_category}</td>
                  <td>{row.q4_delivery_on_time ? <span className="text-success">✓ On time</span> : <span className="text-danger">✗ Late</span>}</td>
                  <td className="truncate">{row.q5_open_text}</td>
                  <td><CoherenceScore score={row.coherence_score} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex-between">
          <span className="text-muted" style={{ fontSize: '0.8rem' }}>
            Page {page + 1} of {totalPages} ({data.total} total)
          </span>
          <div className="flex gap-8">
            <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}><ChevronLeft size={13} /></button>
            <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}><ChevronRight size={13} /></button>
          </div>
        </div>
      )}

      <ResponseDrawer row={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
