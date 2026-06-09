// src/components/Sidebar.jsx
import { NavLink } from 'react-router-dom';
import {
  Settings2, BarChart3, Table2, LineChart,
  Users2, ShieldCheck, History, Settings, Zap
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: Settings2, label: 'Survey Config' },
  { to: '/generate', icon: Zap, label: 'Generate' },
  { to: '/responses', icon: Table2, label: 'Responses' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/personas', icon: Users2, label: 'Personas' },
  { to: '/review', icon: ShieldCheck, label: 'Coherence Review' },
  { to: '/history', icon: History, label: 'Run History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

const ARCHETYPE_COLORS = {
  happy_customer: 'dot-happy',
  neutral_passive: 'dot-neutral',
  frustrated_detractor: 'dot-frustrated',
  delivery_focused: 'dot-delivery',
  value_seeker: 'dot-value',
};

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h2>⚡ SurveyGen AI</h2>
        <p>Synthetic Response Generator</p>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section-label">Pipeline</div>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
          Powered by Groq • Free Tier<br />
          <span style={{ color: 'var(--accent-green)' }}>$0.00</span> per 200 responses
        </div>
      </div>
    </aside>
  );
}
