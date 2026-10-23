import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { AlertTriangle, ShieldCheck, RefreshCw, Eye, X, Info, ChevronRight } from 'lucide-react';

export const RiskMatrix = () => {
  const navigate = useNavigate();
  const [riskApps, setRiskApps] = useState([]);
  const [levelFilter, setLevelFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);

  const loadRiskData = async () => {
    setLoading(true);
    try {
      const qs = levelFilter ? `?level=${levelFilter}` : '';
      const data = await api.get(`/risk/applications${qs}`);
      setRiskApps(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRiskData();
  }, [levelFilter]);

  const handleRecompute = async () => {
    setRecomputing(true);
    try {
      await api.post('/risk/recompute');
      loadRiskData();
    } catch (err) {
      alert(`Recompute failed: ${err.message}`);
    } finally {
      setRecomputing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Explainable Delay-Risk Matrix</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Transparent 0–100 risk scoring with visible rule attribution (Rule 5.7 & 5.8). No hidden black-box logic.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="input-field"
            style={{ width: 'auto' }}
          >
            <option value="">All Risk Tiers</option>
            <option value="HIGH">HIGH RISK (60-100)</option>
            <option value="MEDIUM">MEDIUM RISK (30-59)</option>
            <option value="LOW">LOW RISK (0-29)</option>
          </select>

          <button onClick={handleRecompute} disabled={recomputing} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} className={recomputing ? 'pulse-glow' : ''} />
            {recomputing ? 'Recomputing...' : 'Recompute All Scores'}
          </button>
        </div>
      </div>

      {/* Risk Tier Explanations Ribbon */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
        <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '4px solid #dc2626' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#dc2626' }}>HIGH DELAY RISK (60-100 pts)</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Immediate intervention needed. Overdue tasks, multiple deficiency rounds, or unscheduled visits.
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '4px solid #d97706' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#b45309' }}>MEDIUM DELAY RISK (30-59 pts)</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Approaching critical SLA deadline (&gt;70% consumed) or expiring compliance documents.
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '4px solid #16a34a' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#15803d' }}>LOW DELAY RISK (0-29 pts)</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Pipeline moving normally within standard SLA parameters.
          </div>
        </div>
      </div>

      {/* Risk Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Risk Score</th>
              <th>Tier</th>
              <th>Application No</th>
              <th>Institution</th>
              <th>Primary Explanatory Factor (Why Text)</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {riskApps.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No open cases in this risk tier.
                </td>
              </tr>
            ) : (
              riskApps.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: r.level === 'HIGH' ? '#dc2626' : r.level === 'MEDIUM' ? '#d97706' : '#16a34a' }}>
                      {r.score}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${r.level === 'HIGH' ? 'badge-danger' : r.level === 'MEDIUM' ? 'badge-warning' : 'badge-success'}`}>
                      {r.level}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#1d4ed8' }}>
                    {r.app_no}
                  </td>
                  <td style={{ fontWeight: 600 }}>{r.institution_name}</td>
                  <td>
                    {r.factors && r.factors.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                          • {r.factors[0].explanation}
                        </span>
                        {r.factors.length > 1 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            +{r.factors.length - 1} additional delay factor(s) firing
                          </span>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No negative risk factors</span>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => setSelectedApp(r)}
                        className="btn btn-secondary btn-sm"
                        title="Click to view full factor breakdown"
                      >
                        <Info size={13} />
                        Explain
                      </button>
                      <button
                        onClick={() => navigate(`/applications/${r.application_id}`)}
                        className="btn btn-outline btn-sm"
                      >
                        <Eye size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Factor Breakdown Modal (Rule 5.7 & 5.8: Done when no score is shown without its reasons) */}
      {selectedApp && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '580px', padding: '28px', background: '#ffffff', boxShadow: 'var(--shadow-xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem' }}>Risk Score Attribution</h2>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Case: {selectedApp.app_no} · {selectedApp.institution_name}
                </div>
              </div>
              <button onClick={() => setSelectedApp(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', background: '#f8fafc', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', marginBottom: '18px' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: selectedApp.level === 'HIGH' ? '#dc2626' : selectedApp.level === 'MEDIUM' ? '#d97706' : '#16a34a' }}>
                {selectedApp.score}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge ${selectedApp.level === 'HIGH' ? 'badge-danger' : selectedApp.level === 'MEDIUM' ? 'badge-warning' : 'badge-success'}`}>
                    {selectedApp.level} RISK TIER
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Computed: {new Date(selectedApp.computed_at).toLocaleString()}
                </div>
              </div>
            </div>

            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '10px' }}>
              ACTIVE RISK FACTORS THAT FIRED:
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {selectedApp.factors && selectedApp.factors.length > 0 ? (
                selectedApp.factors.map((f, i) => (
                  <div key={i} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '12px 14px', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ paddingRight: '12px' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{f.explanation}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Rule: {f.rule}</div>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#dc2626', background: '#fee2e2', padding: '3px 8px', borderRadius: 'var(--radius-sm)', whiteSpace: 'nowrap' }}>
                      +{f.points} pts
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  No delay factors present. Application is on schedule.
                </div>
              )}
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setSelectedApp(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
