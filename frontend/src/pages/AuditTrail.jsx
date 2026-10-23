import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { History, Download, Search, Filter, Eye, X, Shield } from 'lucide-react';

export const AuditTrail = () => {
  const [logs, setLogs] = useState([]);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      let query = [];
      if (actionFilter) query.push(`action=${actionFilter}`);
      if (entityFilter) query.push(`entity_type=${entityFilter}`);
      const qs = query.length ? `?${query.join('&')}` : '';
      const data = await api.get(`/audit-logs${qs}`);
      setLogs(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [actionFilter, entityFilter]);

  const handleExportCSV = async () => {
    try {
      const blob = await api.get('/audit-logs/export');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'aicte_watchtower_audit_trail.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    }
  };

  const filteredLogs = logs.filter(l => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      l.action?.toLowerCase().includes(s) ||
      l.entity_type?.toLowerCase().includes(s) ||
      l.entity_id?.toLowerCase().includes(s) ||
      l.actor_name?.toLowerCase().includes(s)
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Tamper-Resistant Audit Trail</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Append-only legal record of all logins, workflow transitions, decisions, and uploads (Rule 6.5 & 6.6).
          </p>
        </div>

        <button onClick={handleExportCSV} className="btn btn-primary btn-sm">
          <Download size={14} />
          Export Audit Trail (CSV)
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel" style={{ padding: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <input
            type="text"
            className="input-field"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Action, Entity ID or Actor..."
            style={{ paddingLeft: '36px' }}
          />
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '13px' }} />
        </div>

        <select
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="input-field"
          style={{ width: 'auto' }}
        >
          <option value="">All Entities</option>
          <option value="APPLICATION">APPLICATION</option>
          <option value="USER">USER</option>
          <option value="TASK">TASK</option>
          <option value="SCRUTINY_REVIEW">SCRUTINY_REVIEW</option>
          <option value="EVC_VISIT">EVC_VISIT</option>
          <option value="UNDERTAKING">UNDERTAKING</option>
          <option value="DOCUMENT">DOCUMENT</option>
          <option value="CONFIG_RULE">CONFIG_RULE</option>
          <option value="SYSTEM">SYSTEM</option>
        </select>
      </div>

      {/* Audit Log Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Action Code</th>
              <th>Entity</th>
              <th>Entity Identifier</th>
              <th>Actor (User)</th>
              <th>IP Address</th>
              <th>State Diff</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No audit logs found.
                </td>
              </tr>
            ) : (
              filteredLogs.map((l) => (
                <tr key={l.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {new Date(l.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span className="badge badge-purple">{l.action}</span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{l.entity_type}</span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#1d4ed8' }}>
                    {l.entity_id}
                  </td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{l.actor_name}</span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {l.ip_address || '127.0.0.1'}
                  </td>
                  <td>
                    {(l.before_state || l.after_state) ? (
                      <button
                        onClick={() => setSelectedLog(l)}
                        className="btn btn-outline btn-sm"
                      >
                        <Eye size={12} /> View Diff
                      </button>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>--</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* JSON Diff Modal */}
      {selectedLog && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '640px', padding: '28px', maxHeight: '90vh', overflowY: 'auto', background: '#ffffff', boxShadow: 'var(--shadow-xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem' }}>State Change Record</h2>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Action: {selectedLog.action} · Entity: {selectedLog.entity_type} ({selectedLog.entity_id})
                </div>
              </div>
              <button onClick={() => setSelectedLog(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: selectedLog.before_state ? '1fr 1fr' : '1fr', gap: '14px', marginBottom: '16px' }}>
              {selectedLog.before_state && (
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#dc2626', marginBottom: '6px' }}>BEFORE STATE:</div>
                  <pre style={{ background: '#fff1f2', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '0.75rem', color: '#991b1b', overflowX: 'auto', border: '1px solid #fecdd3' }}>
                    {JSON.stringify(selectedLog.before_state, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.after_state && (
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#16a34a', marginBottom: '6px' }}>AFTER STATE:</div>
                  <pre style={{ background: '#f0fdf4', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '0.75rem', color: '#166534', overflowX: 'auto', border: '1px solid #bbf7d0' }}>
                    {JSON.stringify(selectedLog.after_state, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setSelectedLog(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
