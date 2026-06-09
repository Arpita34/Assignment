// src/pages/Analytics.jsx — Page 4: Charts
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, Legend,
} from 'recharts';
import api from '../api';

const COLORS = ['#58a6ff', '#3fb950', '#f78166', '#ffa657', '#d2a8ff'];
const CATEGORY_COLORS = {
  Electronics: '#58a6ff', Clothing: '#3fb950', Home: '#ffa657', Other: '#d2a8ff',
};
const CHART_STYLE = {
  fontSize: '0.72rem',
  fill: '#8b949e',
};
const TooltipStyle = {
  backgroundColor: '#1e2438',
  border: '1px solid #2a3050',
  borderRadius: 8,
  color: '#e6edf3',
  fontSize: '0.8rem',
};

function StatCard({ label, value, sub, color }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <span className="stat-value" style={{ color: color || 'var(--text-primary)' }}>{value}</span>
      {sub && <span className="stat-sub">{sub}</span>}
    </div>
  );
}

export default function Analytics() {
  const [params] = useSearchParams();
  const runId = params.get('run_id');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!runId) { setLoading(false); return; }
    api.get(`/api/analytics/${runId}`)
      .then(r => setData(r.data))
      .finally(() => setLoading(false));
  }, [runId]);

  if (!runId) return (
    <div className="page fade-in">
      <div className="page-header"><h1>Analytics</h1></div>
      <div className="card" style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
        No run selected. Go to <a href="/history" style={{ color: 'var(--accent-blue)' }}>Run History</a> and select a run.
      </div>
    </div>
  );

  if (loading) return <div className="page fade-in"><p className="text-muted pulse">Loading analytics…</p></div>;
  if (!data)   return <div className="page fade-in"><p className="text-danger">No data for this run.</p></div>;

  const q1Data = Object.entries(data.q1_dist).map(([k, v]) => ({ name: `⭐${k}`, value: v }));
  const q3Data = Object.entries(data.q3_dist).map(([k, v]) => ({ name: k, value: v }));
  const q4Data = [
    { name: 'On Time', value: data.q4_dist.on_time },
    { name: 'Late', value: data.q4_dist.late },
  ];
  const npsData = [
    { name: 'Detractors (0–6)', value: data.q2_nps.detractors, color: '#f78166' },
    { name: 'Passives (7–8)',   value: data.q2_nps.passives,   color: '#ffa657' },
    { name: 'Promoters (9–10)', value: data.q2_nps.promoters,  color: '#3fb950' },
  ];

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h1>Analytics Overview</h1>
        <p>Quality distribution report for run {runId?.slice(0, 8)}…</p>
      </div>

      {/* Stat Cards */}
      <div className="grid-stat mb-24">
        <StatCard label="Total Responses" value={data.total} color="var(--accent-blue)" />
        <StatCard label="Mean Satisfaction" value={`${data.mean_satisfaction}/5`} color="var(--accent-green)" sub="Q1 average" />
        <StatCard label="Mean NPS" value={`${data.mean_nps}/10`} color="var(--accent-purple)" sub="Q2 average" />
        <StatCard label="Sat↔NPS Corr." value={`r=${data.corr_sat_nps}`} color="var(--accent-orange)" sub="Pearson r (target >0.6)" />
        <StatCard label="Mean Coherence" value={`${(data.coherence_stats.mean * 100).toFixed(0)}%`} color="var(--accent-cyan)" sub="target >60%" />
        <StatCard label="API Cost" value="$0.00" color="var(--accent-green)" sub="Groq free tier" />
      </div>

      <div className="grid-2 mb-24">
        {/* Q1 Satisfaction */}
        <div className="card">
          <h3 className="mb-16">Q1 — Satisfaction Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={q1Data}>
              <XAxis dataKey="name" tick={CHART_STYLE} axisLine={false} tickLine={false} />
              <YAxis tick={CHART_STYLE} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TooltipStyle} />
              <Bar dataKey="value" radius={[4,4,0,0]}>
                {q1Data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* NPS Groups */}
        <div className="card">
          <h3 className="mb-16">Q2 — NPS Breakdown</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={npsData} layout="vertical">
              <XAxis type="number" tick={CHART_STYLE} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={CHART_STYLE} axisLine={false} tickLine={false} width={110} />
              <Tooltip contentStyle={TooltipStyle} />
              <Bar dataKey="value" radius={[0,4,4,0]}>
                {npsData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Q3 Category Donut */}
        <div className="card">
          <h3 className="mb-16">Q3 — Category Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={q3Data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} label={({name, percent}) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                {q3Data.map((d, i) => <Cell key={i} fill={CATEGORY_COLORS[d.name] || COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={TooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Q4 Delivery Donut */}
        <div className="card">
          <h3 className="mb-16">Q4 — Delivery Status</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={q4Data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} label={({name, percent}) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                <Cell fill="#3fb950" />
                <Cell fill="#f78166" />
              </Pie>
              <Tooltip contentStyle={TooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Scatter: Q1 vs Q2 */}
      <div className="card">
        <h3 className="mb-16">Q1 vs Q2 — Satisfaction ↔ NPS Correlation (r = {data.corr_sat_nps})</h3>
        <ResponsiveContainer width="100%" height={240}>
          <ScatterChart>
            <XAxis dataKey="x" name="Satisfaction" type="number" domain={[1,5]} tick={CHART_STYLE} label={{ value: 'Q1 Satisfaction', position: 'insideBottom', offset: -4, fill: '#8b949e', fontSize: 11 }} />
            <YAxis dataKey="y" name="NPS" type="number" domain={[0,10]} tick={CHART_STYLE} label={{ value: 'Q2 NPS', angle: -90, position: 'insideLeft', fill: '#8b949e', fontSize: 11 }} />
            <Tooltip contentStyle={TooltipStyle} cursor={{ stroke: '#2a3050' }} />
            <Scatter data={data.scatter_sat_nps} fill="#58a6ff" opacity={0.5} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
