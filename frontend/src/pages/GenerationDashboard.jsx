// src/pages/GenerationDashboard.jsx — Page 2
import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Play, Square, Zap, Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

const STAGES = ['Personas', 'Profiles', 'Responses', 'Validation', 'Export'];

export default function GenerationDashboard() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  const [state, setState] = useState('idle'); // idle | running | done | error | cancelled
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({ generated: 0, rejected: 0, cost: 0, duration: 0 });
  const [runId, setRunId] = useState(null);
  const [currentStage, setCurrentStage] = useState(0);

  const surveyId = params.get('survey_id') || 'ecommerce';
  const n = parseInt(params.get('n') || '200');
  const logsRef = useRef(null);
  const esRef = useRef(null);

  const addLog = (msg, type = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs(l => [...l.slice(-50), { msg, type, time }]);
  };

  const startGeneration = () => {
    setState('running');
    setProgress(0);
    setLogs([]);
    setStats({ generated: 0, rejected: 0, cost: 0, duration: 0 });
    setCurrentStage(0);

    addLog(`Starting generation: N=${n}, model from environment variables`, 'info');

    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const es = new EventSource(
      `${baseUrl}/api/generate/?survey_id=${surveyId}&n=${n}`,
    );
    esRef.current = es;

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === 'started') {
        setRunId(data.run_id);
        addLog(`Run started: ${data.run_id}`, 'info');
        setCurrentStage(1);
      } else if (data.type === 'progress') {
        const pct = Math.round((data.completed / n) * 100);
        setProgress(pct);
        setStats(s => ({ ...s, generated: data.completed }));
        const stage = Math.min(4, Math.floor((pct / 100) * 5));
        setCurrentStage(stage);
        if (data.completed % 25 === 0) addLog(`Generated ${data.completed}/${n} responses (${pct}%)`, 'info');
      } else if (data.type === 'completed') {
        setState('done');
        setProgress(100);
        setCurrentStage(4);
        setStats({ generated: data.n_generated, rejected: data.n_rejected, cost: 0.00, duration: data.duration_seconds });
        addLog(`✅ Complete: ${data.n_generated} responses in ${data.duration_seconds.toFixed(1)}s`, 'success');
        setRunId(data.run_id);
        es.close();
        setTimeout(() => navigate(`/responses?run_id=${data.run_id}`), 2500);
      } else if (data.type === 'error') {
        setState('error');
        addLog(`❌ Error: ${data.message}`, 'error');
        es.close();
      } else if (data.type === 'cancelled') {
        setState('cancelled');
        addLog('⚠ Generation cancelled.', 'error');
        es.close();
      }
    };

    es.onerror = () => {
      setState('error');
      addLog('Connection error — is the backend running?', 'error');
      es.close();
    };
  };

  const cancelGeneration = async () => {
    if (runId) {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await fetch(`${baseUrl}/api/generate/${runId}`, { method: 'DELETE' });
    }
    esRef.current?.close();
    setState('cancelled');
  };

  useEffect(() => {
    if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight;
  }, [logs]);

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>Generation Dashboard</h1>
        <p>Run the 7-stage pipeline and monitor live progress.</p>
      </div>

      {/* Stage Pipeline */}
      <div className="card mb-24">
        <div className="flex gap-8" style={{ overflowX: 'auto', paddingBottom: 4 }}>
          {STAGES.map((s, i) => (
            <div key={s} className="flex flex-center gap-8" style={{ flexShrink: 0 }}>
              <div style={{
                padding: '6px 16px',
                borderRadius: 999,
                fontSize: '0.78rem',
                fontWeight: 600,
                background: i < currentStage ? 'rgba(63,185,80,0.15)' :
                            i === currentStage && state === 'running' ? 'rgba(88,166,255,0.15)' :
                            'var(--bg-elevated)',
                color: i < currentStage ? 'var(--accent-green)' :
                       i === currentStage && state === 'running' ? 'var(--accent-blue)' :
                       'var(--text-muted)',
                border: `1px solid ${i === currentStage && state === 'running' ? 'var(--accent-blue)' : 'transparent'}`,
              }}>
                {i < currentStage ? '✓ ' : i === currentStage && state === 'running' ? '● ' : `${i + 1}. `}
                {s}
              </div>
              {i < STAGES.length - 1 && (
                <span style={{ color: 'var(--text-muted)' }}>→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid-4 mb-24">
        <div className="stat-card">
          <span className="stat-label">Generated</span>
          <span className="stat-value text-accent">{stats.generated}</span>
          <span className="stat-sub">of {n} target</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Rejected</span>
          <span className="stat-value" style={{ color: stats.rejected > 0 ? 'var(--accent-orange)' : 'var(--accent-green)' }}>{stats.rejected}</span>
          <span className="stat-sub">low coherence</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">API Cost</span>
          <span className="stat-value text-success">$0.00</span>
          <span className="stat-sub">Groq free tier</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Duration</span>
          <span className="stat-value">{stats.duration ? `${stats.duration.toFixed(1)}s` : '—'}</span>
          <span className="stat-sub">total time</span>
        </div>
      </div>

      {/* Progress */}
      <div className="card mb-24">
        <div className="flex-between mb-16">
          <h3>Progress</h3>
          <span className="text-mono" style={{ fontSize: '0.85rem', color: 'var(--accent-blue)' }}>{progress}%</span>
        </div>
        <div className="progress-bar-track">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-12 mb-24">
        {state === 'idle' || state === 'done' || state === 'error' || state === 'cancelled' ? (
          <button className="btn btn-success btn-lg" onClick={startGeneration}>
            <Play size={16} /> {state === 'idle' ? 'Start Generation' : 'Run Again'}
          </button>
        ) : (
          <button className="btn btn-danger btn-lg" onClick={cancelGeneration}>
            <Square size={16} /> Cancel
          </button>
        )}
        {state === 'done' && runId && (
          <button className="btn btn-primary" onClick={() => navigate(`/responses?run_id=${runId}`)}>
            View Responses →
          </button>
        )}
      </div>

      {/* Log Stream */}
      <div className="card">
        <h3 className="mb-16">Live Logs</h3>
        <div className="log-stream" ref={logsRef}>
          {logs.length === 0 && (
            <span style={{ color: 'var(--text-muted)' }}>Logs will appear here when generation starts…</span>
          )}
          {logs.map((log, i) => (
            <div key={i} className={`log-entry ${log.type}`}>
              <span style={{ color: 'var(--text-muted)' }}>[{log.time}]</span> {log.msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
