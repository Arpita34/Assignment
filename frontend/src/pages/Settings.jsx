// src/pages/Settings.jsx — Page 8
import { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, Loader2, KeyRound, Cpu, Sliders } from 'lucide-react';
import api from '../api';

const MODELS = [
  { id: 'llama3-8b-8192',   label: 'Llama 3 8B',   cost: 'FREE',  speed: 'Fast' },
  { id: 'llama3-70b-8192',  label: 'Llama 3 70B',  cost: 'FREE',  speed: 'Medium' },
  { id: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B', cost: 'FREE', speed: 'Medium' },
];

export default function Settings() {
  const [settings, setSettings] = useState({
    groq_configured: false,
    model_name: 'llama3-8b-8192',
    n: 200,
    max_concurrent: 10,
    coherence_threshold: 0.6,
  });
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/settings/').then(r => setSettings(r.data)).finally(() => setLoading(false));
  }, []);

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const { data } = await api.post('/api/settings/test-connection');
      setTestResult(data);
    } catch (e) {
      setTestResult({ success: false, message: e.message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure your API keys, model, and generation parameters.</p>
      </div>

      {/* API Key Status */}
      <div className="card mb-24">
        <div className="flex flex-center gap-12 mb-20">
          <KeyRound size={18} color="var(--accent-blue)" />
          <h2>API Configuration</h2>
        </div>

        <div
          className="card"
          style={{
            background: settings.groq_configured ? 'rgba(63,185,80,0.05)' : 'rgba(247,129,102,0.05)',
            borderColor: settings.groq_configured ? 'var(--accent-green)' : 'var(--accent-red)',
            marginBottom: 16,
          }}
        >
          <div className="flex flex-center gap-12">
            {settings.groq_configured
              ? <CheckCircle2 size={20} color="var(--accent-green)" />
              : <XCircle size={20} color="var(--accent-red)" />
            }
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                Groq API Key — {settings.groq_configured ? 'Configured ✓' : 'Not Set ✗'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                {settings.groq_configured
                  ? 'Key loaded from .env file successfully'
                  : 'Add GROQ_API_KEY to your .env file and restart the server'
                }
              </div>
            </div>
          </div>
        </div>

        {!settings.groq_configured && (
          <div
            className="card"
            style={{ background: 'var(--bg-base)', fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--accent-blue)' }}
          >
            <div className="text-muted" style={{ marginBottom: 6, fontSize: '0.72rem' }}># f:\AssignSS\.env</div>
            GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx<br />
            MODEL_NAME=llama3-8b-8192<br />
            N=200
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={testConnection} disabled={testing || !settings.groq_configured}>
            {testing ? <Loader2 size={14} className="spin" /> : <CheckCircle2 size={14} />}
            {testing ? 'Testing…' : 'Test Connection'}
          </button>

          {testResult && (
            <div
              className="card"
              style={{
                marginTop: 12,
                borderColor: testResult.success ? 'var(--accent-green)' : 'var(--accent-red)',
                background: testResult.success ? 'rgba(63,185,80,0.05)' : 'rgba(247,129,102,0.05)',
              }}
            >
              {testResult.success
                ? <span className="text-success">✓ Connected — {testResult.model} — {testResult.latency_ms}ms latency</span>
                : <span className="text-danger">✗ {testResult.message}</span>
              }
            </div>
          )}
        </div>
      </div>

      {/* Model Selection */}
      <div className="card mb-24">
        <div className="flex flex-center gap-12 mb-20">
          <Cpu size={18} color="var(--accent-purple)" />
          <h2>Model Selection</h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {MODELS.map(m => (
            <div
              key={m.id}
              className="card"
              style={{
                cursor: 'pointer',
                borderColor: settings.model_name === m.id ? 'var(--accent-blue)' : undefined,
                background: settings.model_name === m.id ? 'rgba(88,166,255,0.05)' : undefined,
                transition: 'all 0.15s',
              }}
              onClick={() => setSettings(s => ({ ...s, model_name: m.id }))}
            >
              <div className="flex-between">
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.label}</div>
                  <div className="text-mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{m.id}</div>
                </div>
                <div className="flex gap-8">
                  <span className="badge badge-green">{m.cost}</span>
                  <span className="badge badge-blue">{m.speed}</span>
                  {settings.model_name === m.id && <span className="badge badge-purple">Selected</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Generation Parameters */}
      <div className="card mb-24">
        <div className="flex flex-center gap-12 mb-20">
          <Sliders size={18} color="var(--accent-orange)" />
          <h2>Generation Parameters</h2>
        </div>
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Default N (responses)</label>
            <input
              className="form-input"
              type="number" min={1} max={10000}
              value={settings.n}
              onChange={e => setSettings(s => ({ ...s, n: parseInt(e.target.value) || 200 }))}
            />
            <span className="text-muted" style={{ fontSize: '0.72rem', marginTop: 4 }}>
              Estimated cost at N=200: $0.00 (free)
            </span>
          </div>
          <div className="form-group">
            <label className="form-label">Max Concurrent LLM Calls</label>
            <input
              className="form-input"
              type="number" min={1} max={50}
              value={settings.max_concurrent}
              onChange={e => setSettings(s => ({ ...s, max_concurrent: parseInt(e.target.value) || 10 }))}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Coherence Threshold (0.0 – 1.0)</label>
            <input
              className="form-input"
              type="number" min={0} max={1} step={0.05}
              value={settings.coherence_threshold}
              onChange={e => setSettings(s => ({ ...s, coherence_threshold: parseFloat(e.target.value) || 0.6 }))}
            />
            <span className="text-muted" style={{ fontSize: '0.72rem', marginTop: 4 }}>
              Responses below this score are regenerated (max 3 retries)
            </span>
          </div>
        </div>
      </div>

      {/* Cost Summary */}
      <div className="card" style={{ borderColor: 'var(--accent-green)', background: 'rgba(63,185,80,0.03)' }}>
        <h3 className="mb-16">💰 Cost Estimate</h3>
        <div className="grid-4">
          {[
            { label: 'Provider', value: 'Groq' },
            { label: 'Model', value: settings.model_name.split('-').slice(0,2).join(' ') },
            { label: `${settings.n} Responses`, value: '$0.00' },
            { label: 'Budget remaining', value: '$2.00' },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="stat-label">{label}</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-green)', marginTop: 4 }}>{value}</div>
            </div>
          ))}
        </div>
        <p className="text-muted" style={{ fontSize: '0.75rem', marginTop: 12 }}>
          Groq operates on a free tier — zero cost for Q5 generation. Budget constraint ($2.00) is met with significant margin.
        </p>
      </div>
    </div>
  );
}
