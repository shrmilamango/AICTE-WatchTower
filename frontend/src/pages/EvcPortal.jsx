import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Calendar, Clock, AlertTriangle, Eye, CheckCircle, FileText, User } from 'lucide-react';

export const EvcPortal = () => {
  const navigate = useNavigate();
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusTab, setStatusTab] = useState('ALL');

  const loadVisits = async () => {
    setLoading(true);
    try {
      const qs = statusTab !== 'ALL' ? `?status=${statusTab}` : '';
      const data = await api.get(`/evc${qs}`);
      setVisits(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVisits();
  }, [statusTab]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '4px', color: '#0f172a' }}>Expert Visit Committee (EVC) Portal</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Scheduling, expert team formation, and inspection report completion.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        {['ALL', 'REQUIRED', 'SCHEDULED', 'COMPLETED'].map(tab => (
          <button
            key={tab}
            onClick={() => setStatusTab(tab)}
            style={{
              background: statusTab === tab ? '#eff6ff' : 'transparent',
              border: statusTab === tab ? '1px solid #bfdbfe' : '1px solid transparent',
              color: statusTab === tab ? '#1d4ed8' : 'var(--text-muted)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.8rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Application No</th>
              <th>Institution</th>
              <th>Target Date</th>
              <th>Scheduled Visit Date</th>
              <th>Expert Committee Team</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {visits.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No EVC inspections matching this category.
                </td>
              </tr>
            ) : (
              visits.map(v => (
                <tr key={v.id} style={{ background: v.is_unscheduled_alert ? '#fff1f2' : 'transparent' }}>
                  <td>
                    {v.is_unscheduled_alert ? (
                      <span className="badge badge-danger">LATE UNSCHEDULED</span>
                    ) : v.status === 'COMPLETED' ? (
                      <span className="badge badge-success">COMPLETED</span>
                    ) : v.status === 'SCHEDULED' ? (
                      <span className="badge badge-info">SCHEDULED</span>
                    ) : (
                      <span className="badge badge-warning">REQUIRED</span>
                    )}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#1d4ed8' }}>
                    {v.app_no}
                  </td>
                  <td>{v.institution_name}</td>
                  <td>
                    {v.target_date ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: v.is_unscheduled_alert ? '#be123c' : 'inherit' }}>
                        <Clock size={13} />
                        <span>{new Date(v.target_date).toLocaleDateString()}</span>
                      </div>
                    ) : '--'}
                  </td>
                  <td>
                    {v.scheduled_date ? (
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>
                        {new Date(v.scheduled_date).toLocaleDateString()}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Unscheduled</span>
                    )}
                  </td>
                  <td>
                    {v.members && v.members.length > 0 ? (
                      <div style={{ fontSize: '0.8rem' }}>
                        {v.members.map((m, i) => (
                          <div key={i} style={{ color: 'var(--text-secondary)' }}>
                            • {m.name} ({m.affiliation})
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Team not finalized</span>
                    )}
                  </td>
                  <td>
                    <button
                      onClick={() => navigate(`/applications/${v.application_id}`)}
                      className="btn btn-secondary btn-sm"
                    >
                      <Eye size={13} /> Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
};
