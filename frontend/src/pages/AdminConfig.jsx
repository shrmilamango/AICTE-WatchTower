import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Sliders, CheckCircle, Save, Layers, Clock, Bell, ShieldAlert } from 'lucide-react';

export const AdminConfig = () => {
  const [slaConfig, setSlaConfig] = useState(null);
  const [reminderConfig, setReminderConfig] = useState(null);
  const [escalationConfig, setEscalationConfig] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const [sla, rem, esc, tpl] = await Promise.all([
        api.get('/config/workflow_sla_days'),
        api.get('/config/reminder_offsets'),
        api.get('/config/escalation_thresholds'),
        api.get('/workflow-templates')
      ]);
      setSlaConfig(sla.value || {});
      setReminderConfig(rem.value || {});
      setEscalationConfig(esc.value || {});
      setTemplates(tpl || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  const handleSaveSLA = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put('/config/workflow_sla_days', { value: slaConfig, description: 'Updated stage SLAs' });
      setMsg('Stage SLA rules updated without application restart (Rule 6.1).');
      setTimeout(() => setMsg(null), 4000);
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveReminders = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put('/config/reminder_offsets', { value: reminderConfig, description: 'Updated reminder offsets' });
      setMsg('Reminder rules updated.');
      setTimeout(() => setMsg(null), 4000);
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>System Configuration & Ruleset Store</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Golden Rule: Stage names, SLAs, reminder offsets, and thresholds are never hardcoded (Rule 6.1).
        </p>
      </div>

      {msg && (
        <div style={{ background: '#dcfce7', border: '1px solid #86efac', color: '#166534', padding: '12px 16px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} />
          {msg}
        </div>
      )}

      {/* Grid: SLAs & Reminders */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
        
        {/* Stage SLAs Form */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={18} color="#2563eb" />
              Stage SLA Allotment (Days)
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Config Key: workflow_sla_days</span>
          </div>

          <form onSubmit={handleSaveSLA} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {slaConfig && Object.entries(slaConfig).map(([stage, days]) => (
              <div key={stage} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#f8fafc', padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{stage}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <input
                    type="number"
                    className="input-field"
                    value={days}
                    onChange={(e) => setSlaConfig({ ...slaConfig, [stage]: Number(e.target.value) })}
                    style={{ width: '80px', textAlign: 'center', padding: '6px' }}
                    required
                  />
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>days</span>
                </div>
              </div>
            ))}

            <button type="submit" disabled={saving} className="btn btn-primary" style={{ marginTop: '8px' }}>
              <Save size={14} /> Save SLA Rules
            </button>
          </form>
        </div>

        {/* Reminder Offsets & Escalation Thresholds */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bell size={18} color="#d97706" />
              Automated Reminder Offsets
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Days Before Due Date</span>
          </div>

          <form onSubmit={handleSaveReminders} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
              <label className="label">Task Reminders (Offsets in days)</label>
              <input
                type="text"
                className="input-field"
                value={reminderConfig?.tasks?.join(', ') || ''}
                onChange={(e) => setReminderConfig({
                  ...reminderConfig,
                  tasks: e.target.value.split(',').map(s => Number(s.trim()))
                })}
                placeholder="-2, -1, 0"
              />
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Default: [-2, -1, 0] days before task deadline
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
              <label className="label">Undertaking Reminders (Offsets in days)</label>
              <input
                type="text"
                className="input-field"
                value={reminderConfig?.undertakings?.join(', ') || ''}
                onChange={(e) => setReminderConfig({
                  ...reminderConfig,
                  undertakings: e.target.value.split(',').map(s => Number(s.trim()))
                })}
                placeholder="-15, -7, 0"
              />
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Default: [-15, -7, 0] days before condition deadline
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
              <label className="label">Document Expiry Reminders (Offsets in days)</label>
              <input
                type="text"
                className="input-field"
                value={reminderConfig?.documents?.join(', ') || ''}
                onChange={(e) => setReminderConfig({
                  ...reminderConfig,
                  documents: e.target.value.split(',').map(s => Number(s.trim()))
                })}
                placeholder="-30, -7, 0"
              />
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Default: [-30, -7, 0] days before lease / fire safety expiration
              </div>
            </div>

            <button type="submit" disabled={saving} className="btn btn-primary">
              <Save size={14} /> Save Reminder Rules
            </button>
          </form>
        </div>

      </div>

      {/* Active Workflow Template Stages (Rule 6.2) */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="#8b5cf6" />
              Active Workflow Template: AICTE Approval Process Handbook
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Template-driven stage ordering, owner roles, and permitted stage transitions (Rule 2B.1 & 6.2)
            </p>
          </div>
        </div>

        {templates.map(t => (
          <div key={t.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Stage Key</th>
                    <th>Public Name</th>
                    <th>Owner Role</th>
                    <th>SLA Days</th>
                    <th>Allowed Next Transitions</th>
                  </tr>
                </thead>
                <tbody>
                  {t.stages.map((st) => (
                    <tr key={st.id}>
                      <td style={{ fontWeight: 700 }}>{st.order_no}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: '#1d4ed8' }}>{st.stage_key}</td>
                      <td>{st.name}</td>
                      <td><span className="badge badge-info">{st.owner_role}</span></td>
                      <td>{st.sla_days} days</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {st.allowed_next && st.allowed_next.length > 0 ? (
                            st.allowed_next.map((n, i) => (
                              <span key={i} className="badge badge-purple" style={{ fontSize: '0.65rem' }}>{n}</span>
                            ))
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>End Stage</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
