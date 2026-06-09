// src/pages/SurveyConfig.jsx — Page 1: Survey definition builder
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Upload, Download, Play } from 'lucide-react';
import api from '../api';

const DEFAULT_SURVEY = {
  title: 'E-Commerce Customer Satisfaction Survey',
  questions: [
    { id: 'q1', type: 'rating',        label: 'Overall satisfaction?',      scale: [1, 5] },
    { id: 'q2', type: 'nps',           label: 'Likelihood to recommend?',   scale: [0, 10] },
    { id: 'q3', type: 'single_choice', label: 'Category purchased?',        options: ['Electronics', 'Clothing', 'Home', 'Other'] },
    { id: 'q4', type: 'single_choice', label: 'Was delivery on time?',      options: ['Yes', 'No'] },
    { id: 'q5', type: 'open_text',     label: 'What could we improve?' },
  ],
  n: 200,
};

const TYPE_LABELS = {
  rating: '⭐ Rating Scale',
  nps: '📊 NPS Score',
  single_choice: '☑️ Single Choice',
  open_text: '📝 Open Text',
};

export default function SurveyConfig() {
  const [survey, setSurvey] = useState(DEFAULT_SURVEY);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const updateQuestion = (idx, patch) => {
    setSurvey(s => ({
      ...s,
      questions: s.questions.map((q, i) => i === idx ? { ...q, ...patch } : q),
    }));
  };

  const addQuestion = () => {
    const id = `q${survey.questions.length + 1}`;
    setSurvey(s => ({
      ...s,
      questions: [...s.questions, { id, type: 'open_text', label: 'New question' }],
    }));
  };

  const removeQuestion = (idx) => {
    setSurvey(s => ({ ...s, questions: s.questions.filter((_, i) => i !== idx) }));
  };

  const handleImport = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target.result);
        setSurvey(parsed);
        setError('');
      } catch {
        setError('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(survey, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'survey.json'; a.click();
  };

  const handleSave = async () => {
    setSaving(true); setError('');
    try {
      const { data } = await api.post('/api/surveys/', { survey });
      navigate(`/generate?survey_id=${data.survey_id}&n=${survey.n}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Validation failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header flex-between">
        <div>
          <h1>Survey Configuration</h1>
          <p>Define your survey schema and set the generation parameters.</p>
        </div>
        <div className="flex gap-8">
          <label className="btn btn-ghost" style={{ cursor: 'pointer' }}>
            <Upload size={14} /> Import JSON
            <input type="file" accept=".json" onChange={handleImport} style={{ display: 'none' }} />
          </label>
          <button className="btn btn-ghost" onClick={handleExport}><Download size={14} /> Export</button>
          <button className="btn btn-primary btn-lg" onClick={handleSave} disabled={saving}>
            <Play size={14} /> {saving ? 'Saving…' : 'Start Generation →'}
          </button>
        </div>
      </div>

      <div className="grid-2 mb-24">
        <div className="form-group">
          <label className="form-label">Survey Title</label>
          <input className="form-input" value={survey.title}
            onChange={e => setSurvey(s => ({ ...s, title: e.target.value }))} />
        </div>
        <div className="form-group">
          <label className="form-label">Number of Responses (N)</label>
          <input className="form-input" type="number" min={1} max={10000} value={survey.n}
            onChange={e => setSurvey(s => ({ ...s, n: parseInt(e.target.value) || 200 }))} />
        </div>
      </div>

      {error && (
        <div className="card mb-24" style={{ borderColor: 'var(--accent-red)', background: 'rgba(247,129,102,0.05)' }}>
          <span className="text-danger">⚠ {error}</span>
        </div>
      )}

      <div className="flex-between mb-16">
        <h2>Questions ({survey.questions.length})</h2>
        <button className="btn btn-ghost btn-sm" onClick={addQuestion}><Plus size={13} /> Add Question</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {survey.questions.map((q, idx) => (
          <div key={q.id} className="card" style={{ position: 'relative' }}>
            <div className="flex-between mb-16">
              <div className="flex flex-center gap-8">
                <span className="badge badge-blue">{q.id.toUpperCase()}</span>
                <select className="form-select" style={{ width: 'auto', padding: '4px 8px', fontSize: '0.78rem' }}
                  value={q.type}
                  onChange={e => updateQuestion(idx, { type: e.target.value, scale: undefined, options: undefined })}>
                  {Object.entries(TYPE_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => removeQuestion(idx)} style={{ color: 'var(--accent-red)' }}>
                <Trash2 size={13} />
              </button>
            </div>

            <div className="form-group">
              <label className="form-label">Question Label</label>
              <input className="form-input" value={q.label}
                onChange={e => updateQuestion(idx, { label: e.target.value })} />
            </div>

            {(q.type === 'rating' || q.type === 'nps') && (
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Scale Min</label>
                  <input className="form-input" type="number" value={q.scale?.[0] ?? 1}
                    onChange={e => updateQuestion(idx, { scale: [parseInt(e.target.value), q.scale?.[1] ?? 5] })} />
                </div>
                <div className="form-group">
                  <label className="form-label">Scale Max</label>
                  <input className="form-input" type="number" value={q.scale?.[1] ?? 5}
                    onChange={e => updateQuestion(idx, { scale: [q.scale?.[0] ?? 0, parseInt(e.target.value)] })} />
                </div>
              </div>
            )}

            {q.type === 'single_choice' && (
              <div className="form-group">
                <label className="form-label">Options (comma-separated)</label>
                <input className="form-input"
                  value={(q.options || []).join(', ')}
                  onChange={e => updateQuestion(idx, { options: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
