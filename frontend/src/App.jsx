import React, { useState } from 'react';
import axios from 'axios';

// In dev (vite), the backend runs separately on localhost:8000.
// In production the frontend is served by the backend itself (same origin).
const API_BASE = import.meta.env.DEV ? 'http://localhost:8000/api' : '/api';

function severityClass(severity = '') {
  const s = String(severity).toLowerCase();
  if (s.includes('high')) return 'risk-high';
  if (s.includes('medium')) return 'risk-medium';
  return 'risk-low';
}

function statusLabel(status) {
  const map = {
    completed: 'Completed',
    limited: 'Limited data',
    degraded: 'Fallback mode (Ollama unavailable)',
    unavailable: 'Unavailable',
  };
  return map[status] || status || 'Unknown';
}

function num(value) {
  return value === null || value === undefined ? 'N/A' : Number(value).toLocaleString();
}

function truncate(text, n = 160) {
  if (!text) return 'Unavailable';
  const s = String(text);
  return s.length > n ? s.slice(0, n - 3) + '...' : s;
}

// Build the isolated simulator's hypothetical AccountRisk from analysis results.
// The simulator is a standalone hypothetical tool: this derived risk object is
// sent only to the local /api/simulate endpoint, never to Instagram.
function buildRisk(analysis) {
  const cats = (analysis && analysis.policy_categories) || [];
  const top = cats[0] || null;
  const observations = (analysis && analysis.overall_observations) || [];
  return {
    overall_score: top ? Math.round(Math.max(2, Math.min(98, top.confidence))) / 100 : 0.1,
    detected_categories: cats.map((c) => c.category),
    severity: top ? top.severity : 'low',
    confidence: top ? Math.max(0.2, top.confidence / 100) : 0.2,
    items_analyzed: observations.length,
    summary: cats.length
      ? 'Derived from analysis: ' + cats.map((c) => c.category).join(', ')
      : 'No policy category met the evidence bar in the analysis.',
  };
}

function App() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [simInputs, setSimInputs] = useState({
    violation_reports: 0,
    spam_reports: 0,
    impersonation_reports: 0,
    reporting_sources: 0,
  });
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  const analyzeAccount = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError('');
    setSimResult(null);
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { username });
      setData(res.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Error analyzing account. Make sure the backend is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    if (!data) return;
    setSimLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_BASE}/simulate`, {
        risk: buildRisk(data.analysis || {}),
        inputs: simInputs,
      });
      setSimResult(res.data);
    } catch (err) {
      setError('Error running simulation.');
    } finally {
      setSimLoading(false);
    }
  };

  const onSimNumber = (key) => (e) => {
    const value = Math.max(0, parseInt(e.target.value, 10) || 0);
    setSimInputs((prev) => ({ ...prev, [key]: value }));
  };

  const analysis = data ? data.analysis || {} : {};
  const categories = analysis.policy_categories || [];
  const observations = analysis.overall_observations || [];
  const uncertainties = analysis.uncertainties || [];
  const notes = analysis.notes || [];

  return (
    <div className="container">
      <div className="header">
        <h1>Sonics Dashboard</h1>
        <p>Read-only Instagram public-content policy &amp; evidence analysis</p>
      </div>

      <div className="input-group">
        <input
          type="text"
          placeholder="@username or profile URL"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && analyzeAccount()}
        />
        <button onClick={analyzeAccount} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Account'}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <div className="results">
          <div className="grid">
            <div className="card">
              <h2>Account Overview</h2>
              <p><strong>Username:</strong> @{data.profile.username}</p>
              <p><strong>Display Name:</strong> {data.profile.display_name || 'Unavailable'}</p>
              <p><strong>Bio:</strong> {truncate(data.profile.bio)}</p>
              <p><strong>Account Status:</strong> {data.access_status || 'Unavailable'}</p>
              <p><strong>Followers:</strong> {num(data.profile.follower_count)}</p>
              <p><strong>Following:</strong> {num(data.profile.following_count)}</p>
              <p><strong>Posts:</strong> {num(data.profile.post_count)}</p>
              {data.profile.is_private && (
                <p className="private-note">
                  Limited analysis: this account is private or has limited publicly
                  accessible information.
                </p>
              )}
            </div>

            <div className="card">
              <h2>Analysis Status</h2>
              <p>
                <strong>Status:</strong>{' '}
                <span className="status-badge">{statusLabel(analysis.analysis_status)}</span>
              </p>
              <p><strong>Provider:</strong> {analysis.provider || 'ollama'}</p>
              {notes.length > 0 && (
                <div className="note-list">
                  <strong>Notes:</strong>
                  <ul>{notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
                </div>
              )}
              <p className="disclaimer">
                <em>Read-only analysis of publicly accessible information.</em>
              </p>
            </div>
          </div>

          {categories.length > 0 && (
            <div className="card">
              <h2>Policy Categories</h2>
              <div className="analysis-scroll">
                {categories.map((cat) => (
                  <div key={cat.category} className="analysis-item">
                    <h4>#{cat.rank} {cat.category}</h4>
                    <p className={severityClass(cat.severity)}>Severity: {cat.severity}</p>
                    <p>Confidence: {cat.confidence}%</p>
                    <p>Verification: {cat.verification}</p>
                    {cat.context && <p className="explanation">Context: {cat.context}</p>}
                    <p className="explanation">{cat.reasoning}</p>
                    {cat.evidence.length > 0 && (
                      <div>
                        <strong>Evidence</strong>
                        {cat.evidence.map((ev, i) => (
                          <div key={i} className="evidence">
                            <p><em>&ldquo;{ev.quote}&rdquo;</em></p>
                            <p>source: {ev.source} ({ev.reference})</p>
                            <p>strength: {ev.strength} | relevance: {Math.round(ev.relevance * 100)}% | {ev.verification}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {categories.length === 0 && analysis.analysis_status !== 'unavailable' && (
            <div className="card">
              <p>
                No policy category met the evidence bar. Absence of detected signals
                is not confirmation of compliance.
              </p>
            </div>
          )}

          {observations.length > 0 && (
            <div className="card">
              <h2>Overall Observations</h2>
              <ul>
                {observations.map((o, i) => (
                  <li key={i} className="summary-text">
                    <strong>{o.aspect}</strong> &mdash; {o.detail}
                    {o.reference ? ` (${o.reference})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {uncertainties.length > 0 && (
            <div className="card">
              <h2>Uncertainties</h2>
              <ul>
                {uncertainties.map((u, i) => (
                  <li key={i} className="summary-text">
                    <strong>{u.factor}:</strong> {u.detail}
                  </li>
                ))}
              </ul>
            </div>
          )}


          <div className="card simulator-box">
            <h2>Enforcement Prediction Simulator</h2>
            <p className="disclaimer">
              <em>
                Hypothetical model estimate &mdash; not an official Instagram
                enforcement probability. Report counts are simulation variables
                only and are never sent to Instagram.
              </em>
            </p>

            <div className="grid">
              <div className="sim-inputs">
                <label>Violation Reports:</label>
                <input
                  type="number" min="0"
                  value={simInputs.violation_reports}
                  onChange={onSimNumber('violation_reports')}
                />
                <label>Spam Reports:</label>
                <input
                  type="number" min="0"
                  value={simInputs.spam_reports}
                  onChange={onSimNumber('spam_reports')}
                />
                <label>Impersonation Reports:</label>
                <input
                  type="number" min="0"
                  value={simInputs.impersonation_reports}
                  onChange={onSimNumber('impersonation_reports')}
                />
                <label>Hypothetical Sources:</label>
                <input
                  type="number" min="0"
                  value={simInputs.reporting_sources}
                  onChange={onSimNumber('reporting_sources')}
                />
                <button className="dark-btn" onClick={runSimulation} disabled={simLoading}>
                  {simLoading ? 'Running...' : 'Run Simulation'}
                </button>
              </div>

              <div>
                {simResult ? (
                  <div className="sim-result">
                    <h3>Estimated Enforcement Likelihood</h3>
                    <h1 className="sim-number">{simResult.estimated_likelihood}%</h1>
                    <p>Model Confidence: {simResult.confidence}%</p>
                    <p>Uncertainty: &plusmn;{simResult.uncertainty}%</p>
                    <p className="disclaimer">Result Type: Hypothetical Model Estimate</p>
                    {simResult.factors.length > 0 && (
                      <div className="factor-list">
                        <strong>Factors considered:</strong>
                        <ul>
                          {simResult.factors.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                      </div>
                    )}
                    <p className="scenario">{simResult.scenario_description}</p>
                  </div>
                ) : (
                  <div className="sim-placeholder">
                    Run a simulation to see the hypothetical model estimate.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
