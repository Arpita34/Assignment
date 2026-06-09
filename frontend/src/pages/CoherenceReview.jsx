// src/pages/CoherenceReview.jsx — Page 6
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ShieldCheck, ShieldX, RefreshCw } from 'lucide-react';
import api from '../api';

export default function CoherenceReview() {
  const [params] = useSearchParams();
  const runId = params.get('run_id');
  const [flagged, setFlagged] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/responses/', { params: { run_id: runId || undefined, flagged: true, limit: 100 } })
      .then(r => setFlagged(r.data.results || []))
      .finally(() => setLoading(false));
  }, [runId]);

  const approve = async (id) => {
    await api.patch(`/api/responses/${id}`, { manually_approved: true });
    setFlagged(f => f.map(r => r.response_id === id ? { ...r, manually_approved: true } : r));
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>Coherence Review</h1>
        <p>Responses with coherence score &lt; 0.7 or multiple generation attempts.</p>
      </div>

      {loading ? <p className="text-muted pulse">Loading…</p> : flagged.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
          <ShieldCheck size={40} color="var(--accent-green)" style={{ margin: '0 auto 12px' }} />
          <p style={{ color: 'var(--accent-green)', fontWeight: 600 }}>All responses are coherent!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {flagged.map(row => (
            <div key={row.response_id} className="card" style={{
              borderColor: row.manually_approved ? 'var(--accent-green)' : row.coherence_score < 0.4 ? 'var(--accent-red)' : 'var(--accent-orange)',
            }}>
              <div className="flex-between mb-12">
                <div className="flex flex-center gap-8">
                  <ShieldX size={15} color={row.coherence_score < 0.4 ? 'var(--accent-red)' : 'var(--accent-orange)'} />
                  <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                    Coherence: {(row.coherence_score * 100).toFixed(0)}%
                  </span>
                  {row.manually_approved && <span className="badge badge-green">✓ Approved</span>}
                </div>
                <div className="flex gap-8">
                  {!row.manually_approved && (
                    <button className="btn btn-ghost btn-sm" onClick={() => approve(row.response_id)}>
                      <ShieldCheck size={13} /> Approve
                    </button>
                  )}
                </div>
              </div>

              <div className="grid-2">
                {/* Left: numeric answers */}
                <div>
                  <div className="stat-label mb-8">Numeric Answers</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.82rem' }}>
                    <span>Q1 Satisfaction: <strong>{row.q1_satisfaction}/5</strong></span>
                    <span>Q2 NPS: <strong>{row.q2_nps}/10</strong></span>
                    <span>Q3 Category: <strong>{row.q3_category}</strong></span>
                    <span>Q4 Delivery: <strong>{row.q4_delivery_on_time ? '✅ On Time' : '❌ Late'}</strong></span>
                  </div>
                </div>
                {/* Right: open text + violations */}
                <div>
                  <div className="stat-label mb-8">Q5 Feedback & Issues</div>
                  <p style={{ fontSize: '0.82rem', fontStyle: 'italic', color: 'var(--text-primary)', marginBottom: 10 }}>
                    "{row.q5_open_text}"
                  </p>
                  <div className="stat-label mb-4">Violations</div>
                  {(row.violations || []).map((v, i) => (
                    <div key={i} className="text-mono" style={{ fontSize: '0.7rem', color: 'var(--accent-orange)', marginBottom: 2 }}>{v}</div>
                  ))}
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 8 }}>
                    VADER: {row.sentiment_compound?.toFixed(3)} | Attempts: {row.generation_attempts}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
