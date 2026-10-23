import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import {
  FileText,
  Clock,
  Calendar,
  AlertOctagon,
  ShieldCheck,
  FileWarning,
  Download,
  Filter,
  RefreshCw,
  BarChart3,
  CheckCircle,
  Eye,
  AlertTriangle,
  FolderOpen,
  ArrowRight,
  Users,
  CheckSquare
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';

export const Dashboard = () => {
  const navigate = useNavigate();
  const { user, isInstitution, isAdmin } = useAuth();
  const role = user?.role || 'AUTHORISED_OFFICIAL';

  const [summary, setSummary] = useState(null);
  const [stagePendency, setStagePendency] = useState([]);
  const [regionPendency, setRegionPendency] = useState([]);
  const [agePendency, setAgePendency] = useState([]);
  const [workloads, setWorkloads] = useState([]);
  const [institutionApps, setInstitutionApps] = useState([]);
  const [institutionUndertakings, setInstitutionUndertakings] = useState([]);
  const [institutionDocs, setInstitutionDocs] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const regionParam = selectedRegion ? `?region=${selectedRegion}` : '';
      
      if (role === 'INSTITUTION') {
        // Institution specific requests
        const [sumData, appsData, undData, docsData] = await Promise.all([
          api.get(`/dashboard/summary`),
          api.get('/applications'),
          api.get('/undertakings'),
          api.get('/documents')
        ]);
        setSummary(sumData);
        setInstitutionApps(appsData || []);
        setInstitutionUndertakings(undData || []);
        setInstitutionDocs(docsData || []);
      } else {
        // Official / Admin requests
        const promises = [
          api.get(`/dashboard/summary${regionParam}`),
          api.get('/dashboard/pendency?group_by=stage'),
          api.get('/dashboard/pendency?group_by=region'),
          api.get('/dashboard/pendency?group_by=age')
        ];

        if (['AUTHORISED_OFFICIAL', 'ADMIN', 'AUDITOR'].includes(role)) {
          promises.push(api.get('/dashboard/officer-workload'));
        }

        const [sumData, stageData, regData, ageData, wlData] = await Promise.all(promises);
        setSummary(sumData);
        setStagePendency(stageData || []);
        setRegionPendency(regData || []);
        setAgePendency(ageData || []);
        if (wlData) setWorkloads(wlData || []);
      }
    } catch (e) {
      console.error('Error fetching dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedRegion, role]);

  const handleExportCSV = async (type) => {
    try {
      const blob = await api.get(`/reports/export?report_type=${type}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `watchtower_${type}_report.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    }
  };

  // Header content by role
  const getHeaderInfo = () => {
    switch (role) {
      case 'INSTITUTION':
        return {
          title: 'Institutional Approval Dashboard',
          subtitle: `Welcome, ${user?.full_name || 'Institution'}. Real-time tracking of your AICTE approval filings, active deficiencies, and compliance validity.`,
          showRegionFilter: false,
          showExport: false
        };
      case 'SCRUTINY_OFFICER':
        return {
          title: 'Scrutiny Officer Workspace',
          subtitle: `Welcome, ${user?.full_name || 'Officer'}. Document scrutiny queue, deficiency issuance, and stage SLA compliance monitoring.`,
          showRegionFilter: true,
          showExport: true
        };
      case 'EVC_COORDINATOR':
        return {
          title: 'EVC Inspection Operations',
          subtitle: `Welcome, ${user?.full_name || 'Coordinator'}. Inspection scheduling, expert committee team allocations, and report uploads.`,
          showRegionFilter: true,
          showExport: true
        };
      case 'COMMITTEE_MEMBER':
        return {
          title: 'SAC / SHC Review Committee',
          subtitle: `Welcome, ${user?.full_name || 'Committee Member'}. Review hearings, deficiency appeals, and final recommendation sign-offs.`,
          showRegionFilter: true,
          showExport: true
        };
      default:
        return {
          title: 'AICTE Watchtower Executive Dashboard',
          subtitle: 'Real-time pipeline monitoring, SLA compliance, regional workload, and delay oversight.',
          showRegionFilter: true,
          showExport: true
        };
    }
  };

  const header = getHeaderInfo();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px', color: '#0f172a' }}>{header.title}</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{header.subtitle}</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {header.showRegionFilter && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Filter size={15} color="var(--text-muted)" />
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="input-field"
                style={{ padding: '6px 12px', fontSize: '0.85rem', width: 'auto' }}
              >
                <option value="">All Regions</option>
                <option value="NORTH">North Region</option>
                <option value="WEST">West Region</option>
                <option value="SOUTH">South Region</option>
                <option value="EAST">East Region</option>
              </select>
            </div>
          )}

          <button onClick={fetchDashboardData} className="btn btn-secondary btn-sm" title="Refresh Live Data">
            <RefreshCw size={14} className={loading ? 'pulse-glow' : ''} />
            Refresh
          </button>

          {header.showExport && (
            <button onClick={() => handleExportCSV('pendency')} className="btn btn-outline btn-sm">
              <Download size={14} />
              Export CSV
            </button>
          )}

          {role === 'INSTITUTION' && (
            <button onClick={() => navigate('/applications')} className="btn btn-primary btn-sm">
              <FolderOpen size={14} />
              View My Applications
            </button>
          )}
        </div>
      </div>

      {/* Role-Specific Metric Cards */}
      {role === 'INSTITUTION' && (
        <div className="grid-cards">
          {/* Card 1: My Applications */}
          <div
            onClick={() => navigate('/applications')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #2563eb' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>MY APPLICATIONS</span>
              <FileText size={18} color="#2563eb" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.total_applications ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Click to view your submitted cases</div>
          </div>

          {/* Card 2: In Active Review */}
          <div
            onClick={() => navigate('/applications')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #7c3aed' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>UNDER SCRUTINY</span>
              <Clock size={18} color="#7c3aed" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.under_scrutiny ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Being verified by scrutiny committee</div>
          </div>

          {/* Card 3: Deficiencies to Resolve */}
          <div
            onClick={() => navigate('/applications')}
            className="glass-panel"
            style={{
              padding: '20px',
              cursor: 'pointer',
              borderLeft: `4px solid ${summary?.institution_deficiencies > 0 ? '#dc2626' : '#d97706'}`,
              background: summary?.institution_deficiencies > 0 ? '#fff1f2' : '#ffffff'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: summary?.institution_deficiencies > 0 ? '#be123c' : 'var(--text-secondary)' }}>
                DEFICIENCIES RAISED
              </span>
              <AlertOctagon size={18} color={summary?.institution_deficiencies > 0 ? '#dc2626' : '#d97706'} />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: summary?.institution_deficiencies > 0 ? '#be123c' : '#b45309' }}>
              {summary?.institution_deficiencies ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: summary?.institution_deficiencies > 0 ? '#be123c' : 'var(--text-muted)' }}>
              {summary?.institution_deficiencies > 0 ? 'Action required: submit clarifications' : 'No pending deficiencies'}
            </div>
          </div>

          {/* Card 4: Compliance Undertakings */}
          <div
            onClick={() => navigate('/compliance')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #059669' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>PENDING UNDERTAKINGS</span>
              <ShieldCheck size={18} color="#059669" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.compliance_pending ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Post-approval condition items to fulfill</div>
          </div>

          {/* Card 5: Mandatory Certificates */}
          <div
            onClick={() => navigate('/compliance')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #0891b2' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>EXPIRING CERTIFICATES</span>
              <FileWarning size={18} color="#0891b2" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0e7490' }}>
              {summary?.documents_expiring_soon ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Land lease, Fire NOC & building safety</div>
          </div>
        </div>
      )}

      {/* SCRUTINY OFFICER CARDS */}
      {role === 'SCRUTINY_OFFICER' && (
        <div className="grid-cards">
          <div
            onClick={() => navigate('/tasks')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #2563eb' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>MY SCRUTINY QUEUE</span>
              <CheckSquare size={18} color="#2563eb" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.my_open_tasks ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Active scrutiny tasks assigned to you</div>
          </div>

          <div
            onClick={() => navigate('/applications?status=UNDER_SCRUTINY')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #7c3aed' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>PIPELINE UNDER SCRUTINY</span>
              <Clock size={18} color="#7c3aed" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.under_scrutiny ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total applications awaiting clearance</div>
          </div>

          <div
            onClick={() => navigate('/applications?status=DEFICIENCY_RAISED')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #d97706' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>DEFICIENCIES PENDING</span>
              <AlertTriangle size={18} color="#d97706" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#b45309' }}>
              {summary?.institution_deficiencies ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deficiencies awaiting college reply</div>
          </div>

          <div
            onClick={() => navigate('/tasks')}
            className="glass-panel"
            style={{
              padding: '20px',
              cursor: 'pointer',
              borderLeft: '4px solid #e11d48',
              background: summary?.my_overdue_tasks > 0 ? '#fff1f2' : '#ffffff'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: summary?.my_overdue_tasks > 0 ? '#be123c' : 'var(--text-secondary)' }}>
                OVERDUE TASKS
              </span>
              <AlertOctagon size={18} color="#e11d48" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: summary?.my_overdue_tasks > 0 ? '#be123c' : '#0f172a' }}>
              {summary?.my_overdue_tasks ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: summary?.my_overdue_tasks > 0 ? '#be123c' : 'var(--text-muted)' }}>
              Tasks exceeding Stage SLA limit
            </div>
          </div>
        </div>
      )}

      {/* EVC COORDINATOR CARDS */}
      {role === 'EVC_COORDINATOR' && (
        <div className="grid-cards">
          <div
            onClick={() => navigate('/evc?status=REQUIRED')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #d97706' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>EVCS UNSCHEDULED</span>
              <Calendar size={18} color="#d97706" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#b45309' }}>
              {summary?.evc_awaiting_scheduling ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Inspection visits requiring scheduling</div>
          </div>

          <div
            onClick={() => navigate('/evc?status=SCHEDULED')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #2563eb' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>SCHEDULED VISITS</span>
              <Clock size={18} color="#2563eb" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.evc_scheduled ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Inspection dates confirmed</div>
          </div>

          <div
            onClick={() => navigate('/evc')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #7c3aed' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>REPORTS PENDING</span>
              <FileText size={18} color="#7c3aed" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.evc_reports_pending ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Expert reports awaiting submission</div>
          </div>

          <div
            onClick={() => navigate('/tasks')}
            className="glass-panel"
            style={{
              padding: '20px',
              cursor: 'pointer',
              borderLeft: '4px solid #e11d48',
              background: summary?.my_overdue_tasks > 0 ? '#fff1f2' : '#ffffff'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: summary?.my_overdue_tasks > 0 ? '#be123c' : 'var(--text-secondary)' }}>
                OVERDUE / ALERT
              </span>
              <AlertOctagon size={18} color="#e11d48" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: summary?.my_overdue_tasks > 0 ? '#be123c' : '#0f172a' }}>
              {summary?.my_overdue_tasks ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: summary?.my_overdue_tasks > 0 ? '#be123c' : 'var(--text-muted)' }}>
              Inspections exceeding allocated SLA
            </div>
          </div>
        </div>
      )}

      {/* COMMITTEE MEMBER CARDS */}
      {role === 'COMMITTEE_MEMBER' && (
        <div className="grid-cards">
          <div
            onClick={() => navigate('/committee')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #7c3aed' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>CASES IN SAC REVIEW</span>
              <Users size={18} color="#7c3aed" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.committee_review_count ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Appellate cases requiring hearing</div>
          </div>

          <div
            onClick={() => navigate('/tasks')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #2563eb' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>MY DELIBERATIONS</span>
              <CheckSquare size={18} color="#2563eb" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.my_open_tasks ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Assigned recommendations pending</div>
          </div>

          <div
            onClick={() => navigate('/applications?status=APPROVED')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #059669' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>CASES CLEARED</span>
              <CheckCircle size={18} color="#059669" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.institution_approved ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Decisions finalized for approval</div>
          </div>

          <div
            onClick={() => navigate('/tasks')}
            className="glass-panel"
            style={{
              padding: '20px',
              cursor: 'pointer',
              borderLeft: '4px solid #e11d48',
              background: summary?.my_overdue_tasks > 0 ? '#fff1f2' : '#ffffff'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: summary?.my_overdue_tasks > 0 ? '#be123c' : 'var(--text-secondary)' }}>
                OVERDUE DELIBERATIONS
              </span>
              <AlertOctagon size={18} color="#e11d48" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: summary?.my_overdue_tasks > 0 ? '#be123c' : '#0f172a' }}>
              {summary?.my_overdue_tasks ?? 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: summary?.my_overdue_tasks > 0 ? '#be123c' : 'var(--text-muted)' }}>
              Hearings past standard timeline
            </div>
          </div>
        </div>
      )}

      {/* EXECUTIVE / ADMIN / OFFICIAL CARDS */}
      {['AUTHORISED_OFFICIAL', 'ADMIN', 'AUDITOR'].includes(role) && (
        <div className="grid-cards">
          {/* Card 1: Total Applications */}
          <div
            onClick={() => navigate('/applications')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #2563eb' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>TOTAL APPLICATIONS</span>
              <FileText size={18} color="#2563eb" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.total_applications ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Click to view all submissions</div>
          </div>

          {/* Card 2: Under Scrutiny */}
          <div
            onClick={() => navigate('/applications?status=UNDER_SCRUTINY')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #7c3aed' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>UNDER SCRUTINY</span>
              <Clock size={18} color="#7c3aed" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.under_scrutiny ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Assigned to scrutiny officers</div>
          </div>

          {/* Card 3: EVC Awaiting Scheduling */}
          <div
            onClick={() => navigate('/evc?status=REQUIRED')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #d97706' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>EVCS UNSCHEDULED</span>
              <Calendar size={18} color="#d97706" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#b45309' }}>
              {summary?.evc_awaiting_scheduling ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Awaiting visit dates</div>
          </div>

          {/* Card 4: Overdue Applications */}
          <div
            onClick={() => navigate('/tasks')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #e11d48', background: '#fff1f2' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#be123c' }}>OVERDUE / ESCALATED</span>
              <AlertOctagon size={18} color="#e11d48" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#be123c' }}>
              {summary?.overdue_applications ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#be123c' }}>Overdue past stage SLA</div>
          </div>

          {/* Card 5: Compliance Pending */}
          <div
            onClick={() => navigate('/compliance')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #059669' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>PENDING UNDERTAKINGS</span>
              <ShieldCheck size={18} color="#059669" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0f172a' }}>
              {summary?.compliance_pending ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Post-approval condition items</div>
          </div>

          {/* Card 6: Documents Expiring Soon */}
          <div
            onClick={() => navigate('/compliance?tab=documents')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', borderLeft: '4px solid #0891b2' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)' }}>EXPIRING DOCUMENTS</span>
              <FileWarning size={18} color="#0891b2" />
            </div>
            <div style={{ fontSize: '2.1rem', fontWeight: 800, margin: '8px 0 4px', color: '#0e7490' }}>
              {summary?.documents_expiring_soon ?? '--'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Lease / Fire NOC &lt; 30d</div>
          </div>
        </div>
      )}

      {/* Role-Specific Lower Dashboard Widgets */}
      {role === 'INSTITUTION' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
          {/* Institutional Active Filings Table */}
          <div className="glass-panel" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', color: '#0f172a' }}>My Applications & Current Stage</h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Active approval tracking for your college
                </p>
              </div>
              <button onClick={() => navigate('/applications')} className="btn btn-outline btn-sm">
                View All
              </button>
            </div>

            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>App No</th>
                    <th>Programme</th>
                    <th>Academic Year</th>
                    <th>Current Stage</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {institutionApps.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                        No applications filed yet.
                      </td>
                    </tr>
                  ) : (
                    institutionApps.map(app => (
                      <tr key={app.id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#1d4ed8' }}>
                          {app.app_no}
                        </td>
                        <td>{app.programme || 'Engineering'}</td>
                        <td>{app.academic_year || '2026-27'}</td>
                        <td>
                          <span className={`badge ${app.status === 'APPROVED' ? 'badge-success' : app.status === 'DEFICIENCY_RAISED' ? 'badge-danger' : 'badge-info'}`}>
                            {app.status}
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => navigate(`/applications/${app.id}`)}
                            className="btn btn-outline btn-sm"
                            title="View Application Details"
                          >
                            <Eye size={12} /> View
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Institutional Document Validity & Conditions Tracker */}
          <div className="glass-panel" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', color: '#0f172a' }}>Mandatory Certificates & Conditions</h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Fire Safety, Land Titles & Undertakings
                </p>
              </div>
              <button onClick={() => navigate('/compliance')} className="btn btn-outline btn-sm">
                Compliance Portal
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {institutionDocs.slice(0, 4).map(doc => (
                <div key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{doc.doc_type}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Valid Until: {doc.valid_until ? new Date(doc.valid_until).toLocaleDateString() : 'Permanent'}
                    </div>
                  </div>
                  <span className={`badge ${doc.status === 'VALID' ? 'badge-success' : doc.status === 'EXPIRING' ? 'badge-warning' : 'badge-danger'}`}>
                    {doc.status}
                  </span>
                </div>
              ))}

              {institutionDocs.length === 0 && (
                <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  No documents uploaded yet.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* OFFICIAL & EXECUTIVE CHARTS */
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
            
            {/* Stage Pendency Bar Chart */}
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
                  <BarChart3 size={18} color="#2563eb" />
                  Applications by Stage
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Active Pipeline</span>
              </div>
              <div style={{ height: '260px', minWidth: 0 }}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={stagePendency} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" stroke="#64748b" fontSize={10} angle={-25} textAnchor="end" />
                    <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ background: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', color: '#0f172a', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                    />
                    <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Age Bucket Pendency Chart */}
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
                  <Clock size={18} color="#7c3aed" />
                  Pendency by Age Bucket
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Days Elapsed</span>
              </div>
              <div style={{ height: '260px', minWidth: 0 }}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={agePendency} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ background: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', color: '#0f172a', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                    />
                    <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          {/* Officer Workload Matrix (Only visible to Authorised Official, Admin, Auditor) */}
          {['AUTHORISED_OFFICIAL', 'ADMIN', 'AUDITOR'].includes(role) && (
            <div className="glass-panel" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', color: '#0f172a' }}>Officer Workload & Task Distribution</h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Open, overdue, and escalated assignments per official (Rule 5.6)
                  </p>
                </div>
              </div>

              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Officer</th>
                      <th>Designated Role</th>
                      <th>Region</th>
                      <th>Open Tasks</th>
                      <th>Overdue</th>
                      <th>Escalated</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workloads.map((w) => (
                      <tr key={w.officer_id}>
                        <td style={{ fontWeight: 600 }}>{w.officer_name}</td>
                        <td><span className="badge badge-info">{w.role}</span></td>
                        <td>{w.region || 'HQ'}</td>
                        <td><span style={{ fontWeight: 700 }}>{w.open_tasks}</span></td>
                        <td>
                          {w.overdue_tasks > 0 ? (
                            <span className="badge badge-danger">{w.overdue_tasks} OVERDUE</span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>0</span>
                          )}
                        </td>
                        <td>
                          {w.escalated_tasks > 0 ? (
                            <span className="badge badge-danger">L{w.escalated_tasks}</span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>0</span>
                          )}
                        </td>
                        <td>
                          {w.overdue_tasks > 0 ? (
                            <span style={{ color: '#be123c', fontSize: '0.8rem', fontWeight: 600 }}>Attention Needed</span>
                          ) : (
                            <span style={{ color: '#059669', fontSize: '0.8rem', fontWeight: 600 }}>Normal</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

    </div>
  );
};
