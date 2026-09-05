import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

function App() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [simInputs, setSimInputs] = useState({
    violation_reports: 0,
    spam_reports: 0,
    impersonation_reports: 0,
    reporting_sources: 0
  });
  const [simResult, setSimResult] = useState(null);

  const analyzeAccount = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { username });
      setData(res.data);
      setSimResult(res.data.enforcement_simulation);
    } catch (err) {
      alert("Error analyzing account. Make sure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    if (!data) return;
    try {
      const res = await axios.post(`${API_BASE}/simulate`, {
        risk: data.account_risk,
        inputs: simInputs
      });
      setSimResult(res.data);
    } catch (err) {
      alert("Error running simulation.");
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>Banning Tool Dashboard</h1>
        <p>AI-Powered Instagram Analysis & Enforcement Prediction</p>
      </div>

      <div className="input-group">
        <input 
          type="text" 
          placeholder="@username or profile URL" 
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button onClick={analyzeAccount} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Account'}
        </button>
      </div>

      {data && (
        <div className="results">
          <div className="grid">
            <div className="card">
              <h2>Account Overview</h2>
              <p><strong>Username:</strong> {data.profile.username}</p>
              <p><strong>Display Name:</strong> {data.profile.display_name}</p>
              <p><strong>Bio:</strong> {data.profile.bio}</p>
              <p><strong>Followers:</strong> {data.profile.follower_count || 'N/A'}</p>
              <p><strong>Posts:</strong> {data.profile.post_count || 'N/A'}</p>
              <p><strong>Status:</strong> {data.profile.access_status}</p>
              {data.profile.is_private && (
                <p style={{color: 'orange'}}>Limited analysis: this account is private.</p>
              )}
            </div>

            <div className="card">
              <h2>Account Risk</h2>
              <h3 className={data.account_risk.severity === 'High' ? 'risk-high' : 'risk-low'}>
                Overall Score: {(data.account_risk.overall_score * 100).toFixed(1)}%
              </h3>
              <p><strong>Severity:</strong> {data.account_risk.severity}</p>
              <p><strong>Confidence:</strong> {(data.account_risk.confidence * 100).toFixed(1)}%</p>

          <div className="card">
            <h2>Content Analysis</h2>
            <div style={{display: 'flex', overflowX: 'auto', gap: '10px'}}>
              {data.content_analysis.map((item, idx) => (
                <div key={idx} style={{minWidth: '200px', border: '1px solid #eee', padding: '10px'}}>
                  <h4>{item.category}</h4>
                  <p><strong>Result:</strong> {item.classification}</p>
                  <p><strong>Severity:</strong> {item.severity}</p>
                  <p><small>{item.explanation}</small></p>
                </div>
              ))}
              {data.content_analysis.length === 0 && <p>No content available for analysis.</p>}
            </div>
          </div>

          <div className="card simulator-box">
            <h2>Sonics Enforcement Prediction Simulator</h2>
            <p><small><em>Hypothetical model estimate — not an official Instagram enforcement probability.</em></small></p>
            
            <div className="grid" style={{marginTop: '20px'}}>
              <div>
                <label>Violation Reports:</label><br/>
                <input type="number" value={simInputs.violation_reports} 
                  onChange={e => setSimInputs({...simInputs, violation_reports: parseInt(e.target.value)})} /><br/>
                
                <label>Spam Reports:</label><br/>
                <input type="number" value={simInputs.spam_reports} 
                  onChange={e => setSimInputs({...simInputs, spam_reports: parseInt(e.target.value)})} /><br/>
                
                <label>Impersonation Reports:</label><br/>
                <input type="number" value={simInputs.impersonation_reports} 
                  onChange={e => setSimInputs({...simInputs, impersonation_reports: parseInt(e.target.value)})} /><br/>
                
                <label>Hypothetical Sources:</label><br/>
                <input type="number" value={simInputs.reporting_sources} 
                  onChange={e => setSimInputs({...simInputs, reporting_sources: parseInt(e.target.value)})} /><br/>
                
                <button onClick={runSimulation} style={{marginTop: '10px', background: '#262626'}}>Run Simulation</button>
              </div>

              {simResult && (
                <div style={{textAlign: 'center', border: '2px solid #0095f6', borderRadius: '8px', padding: '10px'}}>
                  <h3>Estimated Likelihood</h3>
                  <h1 style={{fontSize: '48px', margin: '10px 0'}}>{simResult.estimated_likelihood}%</h1>
                  <p>Confidence: {simResult.confidence}%</p>
                  <p>Uncertainty: ±{simResult.uncertainty}%</p>
                  <div style={{textAlign: 'left', fontSize: '14px'}}>
                    <strong>Factors:</strong>
                    <ul>
                      {simResult.factors.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>

              <p><strong>Summary:</strong> {data.account_risk.summary}</p>
            </div>
          </div>
          {/* Content continued in next edit */}
        </div>
      )}
    </div>
  );
}

export default App;
