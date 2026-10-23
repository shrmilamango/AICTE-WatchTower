import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Sliders, CheckCircle, Save, Layers, Clock, Bell, ShieldAlert } from 'lucide-react';

export const AdminConfig = () => {
  const [slaConfig, setSlaConfig] = useState(null);
  const [reminderConfig, setReminderConfig] = useState(null);
  const [escalationConfig, setEscalationConfig] = useState(null);
  const [escalationLadder, setEscalationLadder] = useState({
    TASK: { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 },
    UNDERTAKING: { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 },
    DOCUMENT: { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 }
  });
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const [sla, rem, esc, tpl, escRules] = await Promise.all([
        api.get('/config/workflow_sla_days'),
        api.get('/config/reminder_offsets'),
        api.get('/config/escalation_thresholds'),
        api.get('/workflow-templates'),
        api.get('/escalation-rules').catch(() => [])
      ]);
      setSlaConfig(sla.value || {});
      setReminderConfig(rem.value || {});
      setEscalationConfig(esc.value || {});
      setTemplates(tpl || []);

      if (escRules && escRules.length > 0) {
        const ladderState = {
          TASK: { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 },
          UNDERTAKING: { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 },
          DOCUMENT: { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 }
        };
        escRules.forEach(r => {
          if (ladderState[r.target_type]) {
            if (r.level === 1) {
              ladderState[r.target_type].l1_role = r.escalate_to_role;
              ladderState[r.target_type].l1_days = r.after_overdue_days;
            } else if (r.level === 2) {
              ladderState[r.target_type].l2_role = r.escalate_to_role;
              ladderState[r.target_type].l2_days = r.after_overdue_days;
            }
          }
        });
        setEscalationLadder(ladderState);
      }
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

  const handleSaveEscalationLadder = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      // Validate: days > 0, and Level 2 days > Level 1 days
      for (const [type, item] of Object.entries(escalationLadder)) {
        if (Number(item.l1_days) <= 0 || Number(item.l2_days) <= 0) {
          throw new Error(`Overdue days must be greater than 0 for ${type}`);
        }
        if (Number(item.l2_days) <= Number(item.l1_days)) {
          throw new Error(`Level 2 days (${item.l2_days}) must be strictly greater than Level 1 days (${item.l1_days}) for ${type}`);
        }
      }

      const payload = {
        items: Object.entries(escalationLadder).map(([target_type, data]) => ({
          target_type,
          l1_role: data.l1_role,
          l1_days: Number(data.l1_days),
          l2_role: data.l2_role,
          l2_days: Number(data.l2_days)
        }))
      };

      await api.put('/escalation-rules/ladder', payload);
      setMsg('Escalation Ladder saved to escalation_rules table and logged to audit trail.');
      setTimeout(() => setMsg(null), 4000);
    } catch (err) {
      alert(`Validation error: ${err.message}`);
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

      {/* Escalation Ladder Card (TASK, UNDERTAKING, DOCUMENT) */}
      <div className="glass-panel" style={{ padding: '24px', borderLeft: '4px solid #b45309' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
              <ShieldAlert size={18} color="#b45309" />
              Escalation Ladder
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Configure 2-level hierarchical overdue escalation rules for Tasks, Undertakings, and Documents (saved in escalation_rules table).
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: '#fef3c7', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid #fde68a' }}>
            Defaults: L1 &rarr; 2 days, L2 &rarr; 5 days
          </span>
        </div>

        <form onSubmit={handleSaveEscalationLadder} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {['TASK', 'UNDERTAKING', 'DOCUMENT'].map((type) => {
              const ladder = escalationLadder[type] || { l1_role: 'AUTHORISED_OFFICIAL', l1_days: 2, l2_role: 'AUTHORISED_OFFICIAL', l2_days: 5 };
              const typeLabel = {
                TASK: 'Application Tasks',
                UNDERTAKING: 'Compliance Undertakings',
                DOCUMENT: 'Compliance Documents'
              }[type];

              return (
                <div
                  key={type}
                  style={{
                    background: '#f8fafc',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #e2e8f0',
                    padding: '16px'
                  }}
                >
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px', color: '#0f172a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>{typeLabel}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{type}</span>
                  </div>

                  {/* Level 1 */}
                  <div style={{ background: '#ffffff', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0', marginBottom: '10px' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#b45309', marginBottom: '8px' }}>
                      LEVEL 1 ESCALATION
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '8px' }}>
                      <div>
                        <label className="label" style={{ fontSize: '0.7rem' }}>Escalate To Role</label>
                        <select
                          className="input-field"
                          value={ladder.l1_role}
                          onChange={(e) => setEscalationLadder({
                            ...escalationLadder,
                            [type]: { ...ladder, l1_role: e.target.value }
                          })}
                          style={{ fontSize: '0.75rem', padding: '6px' }}
                        >
                          <option value="AUTHORISED_OFFICIAL">AUTHORISED_OFFICIAL</option>
                          <option value="ADMIN">ADMIN</option>
                          <option value="AUDITOR">AUDITOR</option>
                          <option value="SCRUTINY_OFFICER">SCRUTINY_OFFICER</option>
                          <option value="EVC_COORDINATOR">EVC_COORDINATOR</option>
                          <option value="COMMITTEE_MEMBER">COMMITTEE_MEMBER</option>
                        </select>
                      </div>
                      <div>
                        <label className="label" style={{ fontSize: '0.7rem' }}>After Overdue Days</label>
                        <input
                          type="number"
                          className="input-field"
                          min="1"
                          value={ladder.l1_days}
                          onChange={(e) => setEscalationLadder({
                            ...escalationLadder,
                            [type]: { ...ladder, l1_days: Number(e.target.value) }
                          })}
                          style={{ fontSize: '0.75rem', padding: '6px', textAlign: 'center' }}
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* Level 2 */}
                  <div style={{ background: '#ffffff', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#dc2626', marginBottom: '8px' }}>
                      LEVEL 2 ESCALATION
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '8px' }}>
                      <div>
                        <label className="label" style={{ fontSize: '0.7rem' }}>Escalate To Role</label>
                        <select
                          className="input-field"
                          value={ladder.l2_role}
                          onChange={(e) => setEscalationLadder({
                            ...escalationLadder,
                            [type]: { ...ladder, l2_role: e.target.value }
                          })}
                          style={{ fontSize: '0.75rem', padding: '6px' }}
                        >
                          <option value="AUTHORISED_OFFICIAL">AUTHORISED_OFFICIAL</option>
                          <option value="ADMIN">ADMIN</option>
                          <option value="AUDITOR">AUDITOR</option>
                          <option value="SCRUTINY_OFFICER">SCRUTINY_OFFICER</option>
                          <option value="EVC_COORDINATOR">EVC_COORDINATOR</option>
                          <option value="COMMITTEE_MEMBER">COMMITTEE_MEMBER</option>
                        </select>
                      </div>
                      <div>
                        <label className="label" style={{ fontSize: '0.7rem' }}>After Overdue Days</label>
                        <input
                          type="number"
                          className="input-field"
                          min="2"
                          value={ladder.l2_days}
                          onChange={(e) => setEscalationLadder({
                            ...escalationLadder,
                            [type]: { ...ladder, l2_days: Number(e.target.value) }
                          })}
                          style={{ fontSize: '0.75rem', padding: '6px', textAlign: 'center' }}
                          required
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button type="submit" disabled={saving} className="btn btn-primary">
              <Save size={14} /> Save Escalation Ladder Rules
            </button>
          </div>
        </form>
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
