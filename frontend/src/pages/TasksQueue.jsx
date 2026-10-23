import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import {
  CheckSquare,
  Clock,
  AlertTriangle,
  UserCheck,
  Eye,
  RefreshCw,
  X
} from 'lucide-react';

export const TasksQueue = () => {
  const navigate = useNavigate();
  const { user, isAdmin, hasRole } = useAuth();
  
  const [tasks, setTasks] = useState([]);
  const [officers, setOfficers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [newAssignee, setNewAssignee] = useState('');
  const [reassigning, setReassigning] = useState(false);
  const [message, setMessage] = useState(null);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const endpoint = (isAdmin || hasRole(['AUTHORISED_OFFICIAL'])) ? '/tasks' : '/tasks/my';
      const [tData, uData] = await Promise.all([
        api.get(endpoint),
        api.get('/users')
      ]);
      setTasks(tData || []);
      setOfficers((uData || []).filter(u => u.role !== 'INSTITUTION'));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleReassign = async (e) => {
    e.preventDefault();
    if (!selectedTask || !newAssignee) return;
    setReassigning(true);
    try {
      await api.patch(`/tasks/${selectedTask.id}/reassign`, { assigned_to: newAssignee });
      setMessage(`Task reassigned successfully.`);
      setSelectedTask(null);
      loadTasks();
    } catch (err) {
      alert(`Reassignment failed: ${err.message}`);
    } finally {
      setReassigning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px', color: '#0f172a' }}>Action Tasks & Case Queue</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Sorted strictly by SLA deadline — overdue items surfaced to the top.
          </p>
        </div>

        <button onClick={loadTasks} className="btn btn-secondary btn-sm">
          <RefreshCw size={14} /> Refresh Queue
        </button>
      </div>

      {message && (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: '0.85rem' }}>
          {message}
        </div>
      )}

      {/* Task Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Task Action</th>
              <th>Application No</th>
              <th>Institution</th>
              <th>Assigned Official</th>
              <th>SLA Due Date</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No open tasks in queue. All deadlines satisfied.
                </td>
              </tr>
            ) : (
              tasks.map((t) => (
                <tr key={t.id} style={{ background: t.is_overdue ? '#fff1f2' : 'transparent' }}>
                  <td>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{t.type}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Role: {t.role}</div>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#1d4ed8' }}>
                    {t.app_no}
                  </td>
                  <td>{t.institution_name}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{t.assigned_to_name}</div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: t.is_overdue ? '#be123c' : 'inherit', fontWeight: t.is_overdue ? 700 : 500 }}>
                      <Clock size={13} color={t.is_overdue ? '#be123c' : 'var(--text-muted)'} />
                      <span>{new Date(t.due_at).toLocaleDateString()}</span>
                    </div>
                  </td>
                  <td>
                    {t.status === 'OVERDUE' ? (
                      <span className="badge badge-danger">OVERDUE</span>
                    ) : t.status === 'ESCALATED' ? (
                      <span className="badge badge-danger">ESCALATED (L{t.escalation_level})</span>
                    ) : (
                      <span className="badge badge-info">{t.status}</span>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => navigate(`/applications/${t.application_id}`)}
                        className="btn btn-secondary btn-sm"
                      >
                        <Eye size={13} /> Open
                      </button>

                      {(isAdmin || hasRole(['AUTHORISED_OFFICIAL'])) && (
                        <button
                          onClick={() => { setSelectedTask(t); setNewAssignee(t.assigned_to || ''); }}
                          className="btn btn-outline btn-sm"
                          title="Reassign to another officer"
                        >
                          <UserCheck size={13} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Reassignment Modal */}
      {selectedTask && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '440px', padding: '24px', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.15rem', color: '#0f172a' }}>Reassign Case Task</h2>
              <button onClick={() => setSelectedTask(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleReassign} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Application: <strong>{selectedTask.app_no}</strong> ({selectedTask.type})
              </div>

              <div>
                <label className="label">Transfer Assignment To:</label>
                <select
                  value={newAssignee}
                  onChange={(e) => setNewAssignee(e.target.value)}
                  className="input-field"
                  required
                >
                  <option value="">Select official...</option>
                  {officers.map(o => (
                    <option key={o.id} value={o.id}>
                      {o.full_name} ({o.role} - {o.region || 'HQ'})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setSelectedTask(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={reassigning} className="btn btn-primary">
                  {reassigning ? 'Reassigning...' : 'Commit Transfer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
