import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import {
  FileText,
  Plus,
  Search,
  Filter,
  Eye,
  Clock,
  AlertTriangle,
  CheckCircle,
  X,
  FileCheck
} from 'lucide-react';

export const Applications = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isInstitution } = useAuth();
  
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [programmeFilter, setProgrammeFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  // New Draft Form state
  const [formData, setFormData] = useState({
    programme: 'Engineering & Technology',
    academic_year: '2026-27',
    intake_requested: 120,
    faculty_count: 24,
    built_up_area_sqm: 7500,
    labs_count: 12
  });

  // Read URL query params
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const s = params.get('status');
    if (s) setStatusFilter(s);
  }, [location.search]);

  const loadApplications = async () => {
    setLoading(true);
    try {
      let query = [];
      if (statusFilter) query.push(`status=${statusFilter}`);
      if (programmeFilter) query.push(`programme=${encodeURIComponent(programmeFilter)}`);
      const qs = query.length ? `?${query.join('&')}` : '';
      const data = await api.get(`/applications${qs}`);
      setApplications(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, [statusFilter, programmeFilter]);

  const handleCreateDraft = async (e) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const newApp = await api.post('/applications', {
        programme: formData.programme,
        academic_year: formData.academic_year,
        form_data: {
          intake_requested: Number(formData.intake_requested),
          faculty_count: Number(formData.faculty_count),
          built_up_area_sqm: Number(formData.built_up_area_sqm),
          labs_count: Number(formData.labs_count)
        }
      });
      setShowCreateModal(false);
      navigate(`/applications/${newApp.id}`);
    } catch (err) {
      setCreateError(err.message || 'Failed to create application');
    } finally {
      setCreating(false);
    }
  };

  const filteredApps = applications.filter(a => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      a.app_no?.toLowerCase().includes(s) ||
      a.institution_name?.toLowerCase().includes(s) ||
      a.programme?.toLowerCase().includes(s)
    );
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'DRAFT': return <span className="badge badge-info">DRAFT</span>;
      case 'UNDER_SCRUTINY': return <span className="badge badge-purple">UNDER SCRUTINY</span>;
      case 'DEFICIENCY_RAISED': return <span className="badge badge-warning">DEFICIENCY RAISED</span>;
      case 'RESUBMITTED': return <span className="badge badge-info">RESUBMITTED</span>;
      case 'EVC_REQUIRED': return <span className="badge badge-warning">EVC REQUIRED</span>;
      case 'EVC_SCHEDULED': return <span className="badge badge-info">EVC SCHEDULED</span>;
      case 'COMMITTEE_REVIEW': return <span className="badge badge-purple">COMMITTEE REVIEW</span>;
      case 'DECISION_PENDING': return <span className="badge badge-warning">DECISION PENDING</span>;
      case 'APPROVED': return <span className="badge badge-success">APPROVED</span>;
      case 'APPROVED_WITH_CONDITIONS': return <span className="badge badge-warning">APPROVED (CONDITIONS)</span>;
      case 'REJECTED': return <span className="badge badge-danger">REJECTED</span>;
      case 'CLOSED': return <span className="badge badge-success">CLOSED</span>;
      default: return <span className="badge badge-info">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px', color: '#0f172a' }}>Approval Applications</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Comprehensive case registry with SLA countdowns and owner attribution.
          </p>
        </div>

        {isInstitution && (
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            <Plus size={16} />
            New Application
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel" style={{ padding: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <input
            type="text"
            className="input-field"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Application No, College or Programme..."
            style={{ paddingLeft: '36px' }}
          />
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '13px' }} />
        </div>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field"
          style={{ width: 'auto', minWidth: '180px' }}
        >
          <option value="">All Statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="UNDER_SCRUTINY">Under Scrutiny</option>
          <option value="DEFICIENCY_RAISED">Deficiency Raised</option>
          <option value="RESUBMITTED">Resubmitted</option>
          <option value="EVC_REQUIRED">EVC Required</option>
          <option value="EVC_SCHEDULED">EVC Scheduled</option>
          <option value="COMMITTEE_REVIEW">Committee Review</option>
          <option value="APPROVED_WITH_CONDITIONS">Approved (Conditions)</option>
          <option value="APPROVED">Approved</option>
          <option value="CLOSED">Closed</option>
        </select>

        {/* Programme Filter */}
        <select
          value={programmeFilter}
          onChange={(e) => setProgrammeFilter(e.target.value)}
          className="input-field"
          style={{ width: 'auto', minWidth: '200px' }}
        >
          <option value="">All Programmes</option>
          <option value="Engineering & Technology">Engineering & Technology</option>
          <option value="Management">Management (MBA/PGDM)</option>
          <option value="Pharmacy">Pharmacy</option>
          <option value="Architecture & Planning">Architecture & Planning</option>
          <option value="Computer Applications (MCA)">Computer Applications (MCA)</option>
        </select>
      </div>

      {/* Applications Data Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>App Number</th>
              <th>Institution / College</th>
              <th>Programme</th>
              <th>Status</th>
              <th>Pending With (Rule 2C.3)</th>
              <th>Days Pending</th>
              <th>Risk Level</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredApps.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No applications found matching criteria.
                </td>
              </tr>
            ) : (
              filteredApps.map((app) => (
                <tr key={app.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#1d4ed8' }}>
                    {app.app_no}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{app.institution_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AY {app.academic_year}</div>
                  </td>
                  <td>{app.programme}</td>
                  <td>{getStatusBadge(app.status)}</td>
                  <td>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>{app.pending_with}</div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Clock size={13} color="var(--text-muted)" />
                      <span>{app.days_pending ?? 0} days</span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${app.risk_level === 'HIGH' ? 'badge-danger' : app.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success'}`}>
                      {app.risk_level} ({app.risk_score})
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => navigate(`/applications/${app.id}`)}
                      className="btn btn-secondary btn-sm"
                    >
                      <Eye size={13} />
                      View Case
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create New Draft Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.45)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '580px', padding: '28px', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#0f172a' }}>Create Approval Application Draft</h2>
              <button onClick={() => setShowCreateModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {createError && (
              <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '10px 14px', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '0.85rem' }}>
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateDraft} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="label">Academic Programme</label>
                <select
                  value={formData.programme}
                  onChange={(e) => setFormData({ ...formData, programme: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="Engineering & Technology">Engineering & Technology</option>
                  <option value="Management">Management</option>
                  <option value="Pharmacy">Pharmacy</option>
                  <option value="Architecture & Planning">Architecture & Planning</option>
                  <option value="Computer Applications (MCA)">Computer Applications (MCA)</option>
                </select>
              </div>

              <div>
                <label className="label">Academic Year</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.academic_year}
                  onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label className="label">Requested Intake Seats</label>
                  <input
                    type="number"
                    className="input-field"
                    value={formData.intake_requested}
                    onChange={(e) => setFormData({ ...formData, intake_requested: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Faculty Strength</label>
                  <input
                    type="number"
                    className="input-field"
                    value={formData.faculty_count}
                    onChange={(e) => setFormData({ ...formData, faculty_count: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label className="label">Built-up Area (Sq. Meters)</label>
                  <input
                    type="number"
                    className="input-field"
                    value={formData.built_up_area_sqm}
                    onChange={(e) => setFormData({ ...formData, built_up_area_sqm: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="label">Specialized Laboratories</label>
                  <input
                    type="number"
                    className="input-field"
                    value={formData.labs_count}
                    onChange={(e) => setFormData({ ...formData, labs_count: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '12px', marginTop: '6px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-gold)', marginBottom: '4px' }}>
                  REQUIRED DOCUMENTS CHECKLIST
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  After saving draft, attach certified <strong>Land Lease Deed</strong> and <strong>Fire Safety NOC</strong> prior to submission.
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={creating} className="btn btn-primary">
                  {creating ? 'Saving Draft...' : 'Create Draft Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
