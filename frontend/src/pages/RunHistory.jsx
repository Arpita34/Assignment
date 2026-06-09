// src/pages/RunHistory.jsx — Page 7
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, BarChart3, Table2, RefreshCw } from 'lucide-react';
import api from '../api';

const STATUS_BADGE = {
  done:      { cls: 'badge-green',  label: '✓ Done' },
  running:   { cls: 'badge-blue',   label: '⏳ Running' },
  pending:   { cls: 'badge-orange', label: '● Pending' },
  cancelled: { cls: 'badge-red',    label: '✗ Cancelled' },
  error:     { cls: 'badge-red',    label: '✗ Error' },
};

export default function RunHistory() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);

  const fetchRuns = () => {
    setLoading(true);
    api.get('/api/runs/')
      .then(r => setRuns(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchRuns(); }, []);

  const deleteRun = async (runId, e) => {
    e.stopPropagation();
    if (!confirm('Delete this run and all its responses?')) return;
    setDeleting(runId);
    await api.delete(`/api/runs/${runId}`);
    setRuns(r => r.filter(x => x.run_id !== runId));
    setDeleting(null);
  };

  const reRun = (run, e) => {
    e.stopPropagation();
    navigate(`/generate?n=${run.n_requested}`);
  };

  return (
    <div className="page fade-in">
      <div className="page-header flex-between">
        <div>
          <h1>Run History</h1>
          <p>{runs.length} total generation runs</p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={fetchRuns}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-muted pulse">Loading runs…</p>
      ) : runs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
          <p className="text-muted">No generation runs yet.</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/generate')}>
            Start First Generation →
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Survey</th>
                <th>Status</th>
                <th>Requested</th>
                <th>Generated</th>
                <th>Rejected</th>
                <th>Model</th>
                <th>Duration</th>
                <th>Cost</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => {
                const badge = STATUS_BADGE[run.status] || STATUS_BADGE.pending;
                return (
                  <tr key={run.run_id} onClick={() => navigate(`/responses?run_id=${run.run_id}`)}>
                    <td className="text-mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {run.run_id.slice(0, 8)}…
                    </td>
                    <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {run.survey_title || '—'}
                    </td>
                    <td><span className={`badge ${badge.cls}`}>{badge.label}</span></td>
                    <td>{run.n_requested}</td>
                    <td style={{ color: 'var(--accent-green)', fontWeight: 600 }}>{run.n_generated}</td>
                    <td style={{ color: run.n_rejected > 0 ? 'var(--accent-orange)' : 'var(--text-muted)' }}>
                      {run.n_rejected}
                    </td>
                    <td className="text-mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                      {run.model_used}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '—'}
                    </td>
                    <td style={{ color: 'var(--accent-green)' }}>
                      ${(run.cost_usd || 0).toFixed(4)}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td>
                      <div className="flex gap-4" onClick={e => e.stopPropagation()}>
                        <button
                          className="btn btn-ghost btn-sm"
                          title="View Analytics"
                          onClick={() => navigate(`/analytics?run_id=${run.run_id}`)}
                        >
                          <BarChart3 size={12} />
                        </button>
                        <button
                          className="btn btn-ghost btn-sm"
                          title="Re-run"
                          onClick={(e) => reRun(run, e)}
                        >
                          <RefreshCw size={12} />
                        </button>
                        <button
                          className="btn btn-ghost btn-sm"
                          title="Delete"
                          style={{ color: 'var(--accent-red)' }}
                          disabled={deleting === run.run_id}
                          onClick={(e) => deleteRun(run.run_id, e)}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
