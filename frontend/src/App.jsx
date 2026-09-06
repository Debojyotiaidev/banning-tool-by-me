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

function num(value) {
  return value === null || value === undefined ? 'N/A' : Number(value).toLocaleString();
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
    reporting_sources: 0
  });
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  const analyzeAccount = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { username });
      setData(res.data);
      setSimResult(res.data.enforcement_simulation || null);
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
        risk: data.account_risk,
        inputs: simInputs
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

  const riskPct = data ? (data.account_risk.overall_score * 100) : 0;
  const riskConf = data ? (data.account_risk.confidence * 100) : 0;

  return (
    <div className="container">
      <div className="header">
        <h1>Sonics Dashboard</h1>
        <p>Instagram AI Account Analysis &amp; Hypothetical Enforcement Prediction Simulator</p>
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
              <p><strong>Bio:</strong> {data.profile.bio || 'Unavailable'}</p>
              <p><strong>Followers:</strong> {num(data.profile.follower_count)}</p>
              <p><strong>Following:</strong> {num(data.profile.following_count)}</p>
              <p><strong>Posts:</strong> {num(data.profile.post_count)}</p>
              <p><strong>Status:</strong> {data.profile.access_status || 'Unavailable'}</p>
              {data.profile.is_private && (
                <p className="private-note">
                  Limited analysis: this account is private or has limited publicly accessible information.
                </p>
              )}
            </div>

            <div className="card">
              <h2>Account Risk Summary</h2>
              <h3 className={severityClass(data.account_risk.severity)}>
                Overall Model Risk: {riskPct.toFixed(1)}%
              </h3>
              <p><strong>Severity:</strong> {data.account_risk.severity}</p>
              <p><strong>Model Confidence:</strong> {riskConf.toFixed(1)}%</p>
              <p><strong>Items Analyzed:</strong> {data.account_risk.items_analyzed}</p>
              {data.account_risk.detected_categories.length > 0 && (
                <p>
                  <strong>Detected Signals:</strong>{' '}
                  {data.account_risk.detected_categories.join(', ')}
                </p>
              )}
              <p className="summary-text"><strong>Summary:</strong> {data.account_risk.summary}</p>
              <p className="disclaimer">
                Application-generated risk assessment — not an official Instagram score.
              </p>
            </div>
          </div>

          <div className="card">
            <h2>Content Analysis</h2>
            <div className="analysis-scroll">
              {data.content_analysis.map((item, idx) => (
                <div key={idx} className="analysis-item">
                  <h4>{item.category}</h4>
                  <p><strong>Classification:</strong> {item.classification}</p>
                  <p className={severityClass(item.severity)}>
                    <strong>Severity:</strong> {item.severity}
                  </p>
                  <p><strong>Confidence:</strong> {(item.confidence * 100).toFixed(1)}%</p>
                  {item.evidence && item.evidence !== 'Unavailable' && (
                    <p className="evidence"><strong>Evidence:</strong> “{item.evidence}”</p>
                  )}
                  <p className="explanation">{item.explanation}</p>
                </div>
              ))}
              {data.content_analysis.length === 0 && (
                <p>No content available for analysis.</p>
              )}
            </div>
            {data.profile.is_private && (
              <p className="private-note">
                Limited analysis: this account is private or has limited publicly accessible information.
              </p>
            )}
          </div>

          <div className="card simulator-box">
            <h2>Sonics Enforcement Prediction Simulator</h2>
            <p className="disclaimer">
              <em>Hypothetical model estimate — not an official Instagram enforcement probability.
              Report counts are simulation variables only and are never sent to Instagram.</em>
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
                <button
                  className="dark-btn"
                  onClick={runSimulation}
                  disabled={simLoading}
                >
                  {simLoading ? 'Running...' : 'Run Simulation'}
                </button>
              </div>

              <div>
                {simResult ? (
                  <div className="sim-result">
                    <h3>Estimated Enforcement Likelihood</h3>
                    <h1 className="sim-number">{simResult.estimated_likelihood}%</h1>
                    <p>Model Confidence: {simResult.confidence}%</p>
                    <p>Uncertainty: ±{simResult.uncertainty}%</p>
                    <p className="disclaimer">
                      Result Type: Hypothetical Model Estimate
                    </p>
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
