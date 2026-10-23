import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
  LayoutDashboard,
  FileText,
  CheckSquare,
  Calendar,
  Users,
  ShieldCheck,
  AlertTriangle,
  History,
  Sliders,
  FolderOpen
} from 'lucide-react';

export const Sidebar = () => {
  const { user, isInstitution, isAdmin } = useAuth();

  const navItems = [
    { label: 'Executive Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: 'ALL' },
    { label: 'Applications', path: '/applications', icon: FileText, roles: 'ALL' },
    { label: 'My Tasks Queue', path: '/tasks', icon: CheckSquare, hideFor: ['INSTITUTION'] },
    { label: 'EVC Inspections', path: '/evc', icon: Calendar, roles: ['EVC_COORDINATOR', 'ADMIN', 'AUTHORISED_OFFICIAL', 'AUDITOR'] },
    { label: 'Committee Reviews', path: '/committee', icon: Users, roles: ['COMMITTEE_MEMBER', 'ADMIN', 'AUTHORISED_OFFICIAL', 'AUDITOR'] },
    { label: 'Compliance & Undertakings', path: '/compliance', icon: ShieldCheck, roles: 'ALL' },
    { label: 'Risk Oversight (0-100)', path: '/risk', icon: AlertTriangle, hideFor: ['INSTITUTION'] },
    { label: 'Tamper Audit Trail', path: '/audit', icon: History, roles: ['ADMIN', 'AUDITOR', 'AUTHORISED_OFFICIAL'] },
    { label: 'Rules & Configuration', path: '/admin/config', icon: Sliders, roles: ['ADMIN'] }
  ];

  const filteredNav = navItems.filter(item => {
    if (item.hideFor && user?.role && item.hideFor.includes(user.role)) return false;
    if (!item.roles || item.roles === 'ALL') return true;
    return user?.role ? item.roles.includes(user.role) : false;
  });

  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      height: 'calc(100vh - var(--header-height))',
      background: '#ffffff',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px 14px',
      position: 'sticky',
      top: 'var(--header-height)',
      overflowY: 'auto'
    }}>
      <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 12px 10px' }}>
        Navigation
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {filteredNav.map(item => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                color: isActive ? '#1d4ed8' : 'var(--text-secondary)',
                background: isActive ? '#eff6ff' : 'transparent',
                border: isActive ? '1px solid #bfdbfe' : '1px solid transparent',
                fontSize: '0.85rem',
                fontWeight: isActive ? 700 : 500,
                transition: 'all 0.15s ease'
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Institution Details Badge (if college) */}
      {isInstitution && (
        <div className="glass-panel" style={{ marginTop: 'auto', padding: '14px', borderRadius: 'var(--radius-md)', background: '#f8fafc' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontSize: '0.75rem', fontWeight: 700, marginBottom: '4px' }}>
            <FolderOpen size={14} />
            COLLEGE PORTAL
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Institution isolation active. Access limited to your college records.
          </div>
        </div>
      )}
    </aside>
  );
};
