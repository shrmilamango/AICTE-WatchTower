import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import { Bell, Play, ShieldAlert, LogOut, CheckCircle, RefreshCw } from 'lucide-react';

export const Navbar = () => {
  const { user, logout, isAdmin, isOfficial } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [runningScheduler, setRunningScheduler] = useState(false);
  const [schedulerMsg, setSchedulerMsg] = useState(null);

  const fetchUnread = async () => {
    try {
      const data = await api.get('/notifications/unread-count');
      setUnreadCount(data.unread_count || 0);
    } catch (e) {
      // ignore
    }
  };

  const loadNotifications = async () => {
    try {
      const data = await api.get('/notifications');
      setNotifications(data || []);
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchUnread();
    const interval = setInterval(fetchUnread, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleNotifications = () => {
    if (!showNotifications) {
      loadNotifications();
    }
    setShowNotifications(!showNotifications);
  };

  const markAsRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, status: 'READ' } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (e) {
      // ignore
    }
  };

  const handleRunSchedulerNow = async () => {
    setRunningScheduler(true);
    setSchedulerMsg(null);
    try {
      const res = await api.post('/admin/scheduler/run-now', {});
      setSchedulerMsg(`Scheduler executed: ${res.results.tasks_overdue} overdue flagged, ${res.results.tasks_escalated} escalated.`);
      fetchUnread();
      setTimeout(() => setSchedulerMsg(null), 5000);
    } catch (err) {
      setSchedulerMsg(`Error running scheduler: ${err.message}`);
    } finally {
      setRunningScheduler(false);
    }
  };

  const roleColor = {
    ADMIN: 'badge-purple',
    AUDITOR: 'badge-demo',
    AUTHORISED_OFFICIAL: 'badge-warning',
    SCRUTINY_OFFICER: 'badge-info',
    EVC_COORDINATOR: 'badge-info',
    COMMITTEE_MEMBER: 'badge-info',
    INSTITUTION: 'badge-success'
  }[user?.role] || 'badge-info';

  return (
    <header style={{
      height: 'var(--header-height)',
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      boxShadow: 'var(--shadow-sm)'
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(37,99,235,0.3)'
        }}>
          <ShieldAlert size={22} color="#fff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.1rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#0f172a' }}>
              AICTE WATCHTOWER
            </span>
            <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>OFFICIAL</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Approval Workflow Automation & Risk Oversight
          </div>
        </div>
      </div>

      {/* Scheduler Trigger Notification Banner */}
      {schedulerMsg && (
        <div style={{
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          color: '#1d4ed8',
          padding: '6px 14px',
          borderRadius: 'var(--radius-full)',
          fontSize: '0.8rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <CheckCircle size={14} />
          {schedulerMsg}
        </div>
      )}

      {/* Actions & Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Presentation Trigger: Run Scheduler Now */}
        {(isAdmin || isOfficial) && (
          <button
            onClick={handleRunSchedulerNow}
            disabled={runningScheduler}
            className="btn btn-secondary btn-sm"
            style={{
              borderColor: '#fde68a',
              background: '#fffbeb',
              color: '#b45309'
            }}
            title="Checks deadlines, marks overdue items, triggers 2-level escalations"
          >
            <Play size={13} fill="#b45309" />
            {runningScheduler ? 'Running Checks...' : 'Run Scheduler Now'}
          </button>
        )}

        {/* Notifications Bell */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={handleToggleNotifications}
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '8px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                background: 'var(--accent-rose)',
                color: '#fff',
                fontSize: '0.65rem',
                fontWeight: 800,
                padding: '1px 5px',
                borderRadius: '9999px',
                boxShadow: '0 0 8px rgba(225, 29, 72, 0.4)'
              }}>
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="glass-panel" style={{
              position: 'absolute',
              right: 0,
              top: '45px',
              width: '360px',
              maxHeight: '450px',
              overflowY: 'auto',
              padding: '16px',
              zIndex: 100,
              boxShadow: 'var(--shadow-lg)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.875rem', color: '#0f172a' }}>Notifications</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{unreadCount} unread</span>
              </div>
              {notifications.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', padding: '20px 0' }}>
                  No notifications yet.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {notifications.map(n => (
                    <div
                      key={n.id}
                      onClick={() => markAsRead(n.id)}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-md)',
                        background: n.status === 'READ' ? '#f8fafc' : '#eff6ff',
                        border: n.status === 'READ' ? '1px solid var(--border-subtle)' : '1px solid #bfdbfe',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: n.status === 'READ' ? 'var(--text-secondary)' : '#1e40af', marginBottom: '4px' }}>
                        {n.subject}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>
                        {n.body}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* User Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: '#f8fafc',
          border: '1px solid var(--border-subtle)',
          padding: '4px 12px',
          borderRadius: 'var(--radius-full)'
        }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0f172a' }}>{user?.full_name}</div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
              <span className={`badge ${roleColor}`}>{user?.role}</span>
              {user?.region && <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>[{user.region}]</span>}
            </div>
          </div>
          <button
            onClick={logout}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};
