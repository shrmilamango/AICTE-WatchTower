import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import {
  FileText,
  Clock,
  User,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Upload,
  Calendar,
  Send,
  Plus,
  Trash2,
  FileCheck,
  Shield,
  History,
  X,
  File
} from 'lucide-react';

export const ApplicationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isInstitution, isAdmin, hasRole } = useAuth();

  const [app, setApp] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Modals state
  const [showScrutinyModal, setShowScrutinyModal] = useState(false);
  const [showEvcModal, setShowEvcModal] = useState(false);
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [showDocUploadModal, setShowDocUploadModal] = useState(false);

  // Scrutiny form state
  const [scrutinyOutcome, setScrutinyOutcome] = useState('PASS');
  const [scrutinyRemarks, setScrutinyRemarks] = useState('');
  const [deficienciesList, setDeficienciesList] = useState([
    { item: 'Cadre Ratio Norms', description: 'Faculty cadre ratio of Professor to Associate Professor does not satisfy APH norms', due_days: 7 }
  ]);

  // EVC form state
  const [evcDate, setEvcDate] = useState('');
  const [evcMembers, setEvcMembers] = useState([
    { name: 'Prof. S. R. Bose', affiliation: 'IIT Delhi', role: 'Chairman' },
    { name: 'Dr. K. Narayanan', affiliation: 'NIT Surathkal', role: 'Member' }
  ]);
  const [evcRemarks, setEvcRemarks] = useState('');

  // Decision form state
  const [decisionType, setDecisionType] = useState('APPROVED_WITH_CONDITIONS');
  const [orderRef, setOrderRef] = useState('AICTE/NWRO/2026/DEC-');
  const [decisionRemarks, setDecisionRemarks] = useState('');
  const [decisionConditions, setDecisionConditions] = useState([
    { title: 'Registered 30-Year Land Lease Deed', description: 'Provide certified sub-registrar registered lease deed within 30 days', due_days: 30 }
  ]);

  // Upload Doc state
  const [uploadDocType, setUploadDocType] = useState('LAND_LEASE');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadValidUntil, setUploadValidUntil] = useState('');

  const loadAllData = async () => {
    setLoading(true);
    setActionError(null);
    try {
      const [appData, timeData, docData] = await Promise.all([
        api.get(`/applications/${id}`),
        api.get(`/applications/${id}/timeline`),
        api.get(`/documents?application_id=${id}`)
      ]);
      setApp(appData);
      setTimeline(timeData || []);
      setDocuments(docData || []);
      setOrderRef(`AICTE/NWRO/2026/ORD-${appData.app_no?.split('-').pop() || '101'}`);
    } catch (err) {
      setActionError(err.message || 'Failed to load case');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [id]);

  const handleDocUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('doc_type', uploadDocType);
      formData.append('application_id', id);
      if (app?.institution_id) formData.append('institution_id', app.institution_id);
      if (uploadValidUntil) formData.append('valid_until', uploadValidUntil);

      await api.upload('/documents', formData);
      setShowDocUploadModal(false);
      setUploadFile(null);
      setActionSuccess('Document uploaded successfully');
      loadAllData();
    } catch (err) {
      setActionError(err.message || 'Upload failed');
    }
  };

  const handleSubmitApplication = async () => {
    if (!confirm('Submit application for official AICTE scrutiny review? This will lock the draft.')) return;
    try {
      await api.post(`/applications/${id}/submit`, {});
      setActionSuccess('Application submitted! Registration number issued & scrutiny allocated.');
      loadAllData();
    } catch (err) {
      setActionError(err.message || 'Submission failed');
    }
  };

  const handleScrutinySubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/applications/${id}/scrutiny`, {
        outcome: scrutinyOutcome,
        remarks: scrutinyRemarks,
        deficiencies: scrutinyOutcome === 'DEFICIENT' ? deficienciesList : []
      });
      setShowScrutinyModal(false);
      setActionSuccess(`Scrutiny completed with outcome: ${scrutinyOutcome}`);
      loadAllData();
    } catch (err) {
      setActionError(err.message || 'Scrutiny submission failed');
    }
  };

  const handleScheduleEvc = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/applications/${id}/evc/schedule`, {
        scheduled_date: new Date(evcDate).toISOString(),
        members: evcMembers,
        remarks: evcRemarks
      });
      setShowEvcModal(false);
      setActionSuccess('EVC visit scheduled! Institution and officials notified.');
      loadAllData();
    } catch (err) {
      setActionError(err.message || 'EVC scheduling failed');
    }
  };

  const handleDecisionSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/applications/${id}/decision`, {
        decision: decisionType,
        order_ref: orderRef,
        remarks: decisionRemarks,
        conditions: decisionType === 'APPROVED_WITH_CONDITIONS' ? decisionConditions : []
      });
      setShowDecisionModal(false);
      setActionSuccess(`Decision recorded: ${decisionType}. Conditions converted to undertakings.`);
      loadAllData();
    } catch (err) {
      setActionError(err.message || 'Decision failed');
    }
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading application records...</div>;
  }

  if (!app) {
    return <div style={{ padding: '40px', textAlign: 'center', color: '#e11d48' }}>{actionError || 'Application not found'}</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Breadcrumb & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <button onClick={() => navigate('/applications')} className="btn btn-outline btn-sm">
          <ArrowLeft size={14} />
          Back to Registry
        </button>

        {/* Action Buttons based on User Role & Stage */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Draft Submission (Institution) */}
          {app.status === 'DRAFT' && isInstitution && (
            <button onClick={handleSubmitApplication} className="btn btn-primary">
              <Send size={15} />
              Submit Application
            </button>
          )}

          {/* Scrutiny Review (Officer / Admin) */}
          {['UNDER_SCRUTINY', 'RESUBMITTED'].includes(app.status) && hasRole(['SCRUTINY_OFFICER', 'ADMIN']) && (
            <button onClick={() => setShowScrutinyModal(true)} className="btn btn-primary">
              <CheckCircle size={15} />
              Record Scrutiny Review
            </button>
          )}

          {/* EVC Scheduling (Coordinator) */}
          {app.status === 'EVC_REQUIRED' && hasRole(['EVC_COORDINATOR', 'ADMIN']) && (
            <button onClick={() => setShowEvcModal(true)} className="btn btn-primary">
              <Calendar size={15} />
              Schedule EVC Inspection
            </button>
          )}

          {/* Official Final Decision (Authorised Official / Admin) */}
          {['DECISION_PENDING', 'COMMITTEE_REVIEW', 'EVC_COMPLETED'].includes(app.status) && hasRole(['AUTHORISED_OFFICIAL', 'ADMIN']) && (
            <button onClick={() => setShowDecisionModal(true)} className="btn btn-success">
              <Shield size={15} />
              Record Official Decision
            </button>
          )}

          {/* Document Upload */}
          <button onClick={() => setShowDocUploadModal(true)} className="btn btn-secondary btn-sm">
            <Upload size={14} />
            Attach Document
          </button>
        </div>
      </div>

      {/* Action Notification Banners */}
      {actionSuccess && (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', padding: '12px 16px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} />
          {actionSuccess}
        </div>
      )}
      {actionError && (
        <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '12px 16px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} />
          {actionError}
        </div>
      )}

      {/* Case Header Card */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#1d4ed8' }}>
                {app.app_no}
              </span>
              <span className="badge badge-info">{app.status}</span>
              <span className={`badge ${app.risk_level === 'HIGH' ? 'badge-danger' : app.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success'}`}>
                Risk {app.risk_score}/100 ({app.risk_level})
              </span>
            </div>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '4px', color: '#0f172a' }}>{app.institution_name}</h2>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Programme: <strong>{app.programme}</strong> · Academic Year: <strong>{app.academic_year}</strong>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              PENDING WITH (RULE 2C.3)
            </div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#b45309', marginTop: '2px' }}>
              {app.pending_with}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Pending duration: {app.days_pending ?? 0} days
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Form Data & Attached Documents */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '20px' }}>
        
        {/* Form Details */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
            <FileText size={18} color="#2563eb" />
            Application Form & Infrastructure Data
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>REQUESTED INTAKE</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>{app.form_data?.intake_requested ?? 120} Seats</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FACULTY STRENGTH</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>{app.form_data?.faculty_count ?? 24} Members</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>BUILT-UP AREA</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>{app.form_data?.built_up_area_sqm ?? 7500} Sq. M</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>LABORATORIES</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a' }}>{app.form_data?.labs_count ?? 12} Dedicated</div>
            </div>
          </div>
        </div>

        {/* Attached Documents */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
              <FileCheck size={18} color="#059669" />
              Attached Documents ({documents.length})
            </h3>
            <button onClick={() => setShowDocUploadModal(true)} className="btn btn-secondary btn-sm">
              <Plus size={12} /> Add
            </button>
          </div>

          {documents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No documents attached yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: '#f8fafc',
                    border: '1px solid var(--border-subtle)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <File size={16} color="#2563eb" />
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>{doc.file_name}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {doc.doc_type} · v{doc.version_no} · {(doc.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  </div>
                  <a
                    href={`/api/v1/documents/${doc.id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-outline btn-sm"
                  >
                    View
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Case Timeline */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
          <History size={18} color="#7c3aed" />
          Interactive Chronological Timeline (Rule 2C.4)
        </h3>

        <div style={{ position: 'relative', paddingLeft: '28px' }}>
          {/* Timeline Vertical Line */}
          <div style={{
            position: 'absolute',
            left: '8px',
            top: '8px',
            bottom: '8px',
            width: '2px',
            background: '#e2e8f0'
          }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {timeline.map((item) => (
              <div key={item.id} style={{ position: 'relative' }}>
                {/* Bullet */}
                <div style={{
                  position: 'absolute',
                  left: '-24px',
                  top: '6px',
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: item.type === 'DECISION' ? '#059669' : item.type === 'SCRUTINY' ? '#7c3aed' : '#2563eb',
                  boxShadow: '0 0 0 3px #ffffff'
                }} />

                <div style={{ background: '#ffffff', padding: '14px 18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>{item.title}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(item.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                    {item.description}
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <User size={12} />
                    <span>Actor: {item.actor_name} ({item.actor_role})</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* --- Action Modals --- */}

      {/* Modal 1: Scrutiny Review */}
      {showScrutinyModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '620px', padding: '28px', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#0f172a' }}>Record Technical Scrutiny Review</h2>
              <button onClick={() => setShowScrutinyModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleScrutinySubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label className="label">Scrutiny Outcome</label>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    type="button"
                    onClick={() => setScrutinyOutcome('PASS')}
                    className={`btn ${scrutinyOutcome === 'PASS' ? 'btn-success' : 'btn-secondary'}`}
                    style={{ flex: 1 }}
                  >
                    PASS (Advance to EVC/Committee)
                  </button>
                  <button
                    type="button"
                    onClick={() => setScrutinyOutcome('DEFICIENT')}
                    className={`btn ${scrutinyOutcome === 'DEFICIENT' ? 'btn-danger' : 'btn-secondary'}`}
                    style={{ flex: 1 }}
                  >
                    RAISE DEFICIENCIES
                  </button>
                </div>
              </div>

              <div>
                <label className="label">Scrutiny Officer Remarks</label>
                <textarea
                  className="input-field"
                  rows={3}
                  value={scrutinyRemarks}
                  onChange={(e) => setScrutinyRemarks(e.target.value)}
                  placeholder="Summary remarks on verification of physical, land, faculty & document norms..."
                  required
                />
              </div>

              {/* Dynamic Deficiencies Builder */}
              {scrutinyOutcome === 'DEFICIENT' && (
                <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#be123c' }}>ITEMIZED DEFICIENCIES</span>
                    <button
                      type="button"
                      onClick={() => setDeficienciesList([...deficienciesList, { item: '', description: '', due_days: 7 }])}
                      className="btn btn-secondary btn-sm"
                    >
                      <Plus size={12} /> Add Item
                    </button>
                  </div>

                  {deficienciesList.map((d, idx) => (
                    <div key={idx} style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #fecdd3' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '8px', marginBottom: '6px' }}>
                        <input
                          type="text"
                          className="input-field"
                          placeholder="Deficiency Item (e.g. Fire NOC)"
                          value={d.item}
                          onChange={(e) => {
                            const copy = [...deficienciesList];
                            copy[idx].item = e.target.value;
                            setDeficienciesList(copy);
                          }}
                          required
                        />
                        <input
                          type="number"
                          className="input-field"
                          placeholder="Due Days"
                          value={d.due_days}
                          onChange={(e) => {
                            const copy = [...deficienciesList];
                            copy[idx].due_days = Number(e.target.value);
                            setDeficienciesList(copy);
                          }}
                          required
                        />
                        {deficienciesList.length > 1 && (
                          <button
                            type="button"
                            onClick={() => setDeficienciesList(deficienciesList.filter((_, i) => i !== idx))}
                            className="btn btn-outline btn-sm"
                            style={{ color: '#be123c' }}
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                      <input
                        type="text"
                        className="input-field"
                        placeholder="Detailed explanation of non-compliance..."
                        value={d.description}
                        onChange={(e) => {
                          const copy = [...deficienciesList];
                          copy[idx].description = e.target.value;
                          setDeficienciesList(copy);
                        }}
                        required
                      />
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setShowScrutinyModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Commit Scrutiny Evaluation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Schedule EVC Visit */}
      {showEvcModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '580px', padding: '28px', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#0f172a' }}>Schedule Expert Visit Committee (EVC)</h2>
              <button onClick={() => setShowEvcModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleScheduleEvc} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="label">Inspection Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={evcDate}
                  onChange={(e) => setEvcDate(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="label">Expert Committee Members</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {evcMembers.map((m, idx) => (
                    <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1.5fr 1.5fr 1fr', gap: '8px' }}>
                      <input
                        type="text"
                        className="input-field"
                        placeholder="Expert Name"
                        value={m.name}
                        onChange={(e) => {
                          const copy = [...evcMembers];
                          copy[idx].name = e.target.value;
                          setEvcMembers(copy);
                        }}
                      />
                      <input
                        type="text"
                        className="input-field"
                        placeholder="Affiliation / Institute"
                        value={m.affiliation}
                        onChange={(e) => {
                          const copy = [...evcMembers];
                          copy[idx].affiliation = e.target.value;
                          setEvcMembers(copy);
                        }}
                      />
                      <input
                        type="text"
                        className="input-field"
                        placeholder="Role"
                        value={m.role}
                        onChange={(e) => {
                          const copy = [...evcMembers];
                          copy[idx].role = e.target.value;
                          setEvcMembers(copy);
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="label">Coordinator Directives & Remarks</label>
                <textarea
                  className="input-field"
                  rows={2}
                  value={evcRemarks}
                  onChange={(e) => setEvcRemarks(e.target.value)}
                  placeholder="Specific instructions for physical inspection..."
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setShowEvcModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirm Inspection Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 3: Final Decision Recorder */}
      {showDecisionModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '640px', padding: '28px', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#0f172a' }}>Record Official AICTE Approval Decision</h2>
              <button onClick={() => setShowDecisionModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleDecisionSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="label">Final Determination</label>
                <select
                  value={decisionType}
                  onChange={(e) => setDecisionType(e.target.value)}
                  className="input-field"
                  required
                >
                  <option value="APPROVED_WITH_CONDITIONS">APPROVED WITH CONDITIONS (Generates Undertakings)</option>
                  <option value="APPROVED">APPROVE (Unconditional)</option>
                  <option value="REJECTED">REJECT APPLICATION</option>
                </select>
              </div>

              <div>
                <label className="label">Official Order Reference Number</label>
                <input
                  type="text"
                  className="input-field"
                  value={orderRef}
                  onChange={(e) => setOrderRef(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="label">Official Order Remarks</label>
                <textarea
                  className="input-field"
                  rows={2}
                  value={decisionRemarks}
                  onChange={(e) => setDecisionRemarks(e.target.value)}
                  placeholder="Executive approval order remarks and reasoning..."
                  required
                />
              </div>

              {/* Conditions to Undertakings Builder */}
              {decisionType === 'APPROVED_WITH_CONDITIONS' && (
                <div style={{ background: '#fffbeb', border: '1px solid #fde68a', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#b45309' }}>
                      MANDATORY UNDERTAKINGS (RULE 3.1)
                    </span>
                    <button
                      type="button"
                      onClick={() => setDecisionConditions([...decisionConditions, { title: '', description: '', due_days: 30 }])}
                      className="btn btn-secondary btn-sm"
                    >
                      <Plus size={12} /> Add Condition
                    </button>
                  </div>

                  {decisionConditions.map((cond, idx) => (
                    <div key={idx} style={{ marginBottom: '10px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '8px', marginBottom: '6px' }}>
                        <input
                          type="text"
                          className="input-field"
                          placeholder="Condition / Undertaking Title"
                          value={cond.title}
                          onChange={(e) => {
                            const copy = [...decisionConditions];
                            copy[idx].title = e.target.value;
                            setDecisionConditions(copy);
                          }}
                          required
                        />
                        <input
                          type="number"
                          className="input-field"
                          placeholder="Fulfillment Days"
                          value={cond.due_days}
                          onChange={(e) => {
                            const copy = [...decisionConditions];
                            copy[idx].due_days = Number(e.target.value);
                            setDecisionConditions(copy);
                          }}
                          required
                        />
                      </div>
                      <input
                        type="text"
                        className="input-field"
                        placeholder="Legal description and proof expected..."
                        value={cond.description}
                        onChange={(e) => {
                          const copy = [...decisionConditions];
                          copy[idx].description = e.target.value;
                          setDecisionConditions(copy);
                        }}
                        required
                      />
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowDecisionModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-success">
                  Affix Official Signature & Issue Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 4: Attach Document */}
      {showDocUploadModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '480px', padding: '28px', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#0f172a' }}>Upload Compliance Document</h2>
              <button onClick={() => setShowDocUploadModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleDocUpload} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="label">Document Classification</label>
                <select
                  value={uploadDocType}
                  onChange={(e) => setUploadDocType(e.target.value)}
                  className="input-field"
                  required
                >
                  <option value="LAND_LEASE">Registered Land Lease Deed (Has Validity)</option>
                  <option value="FIRE_SAFETY_NOC">Municipal Fire Safety NOC (Has Validity)</option>
                  <option value="AFFILIATION_DOC">University Affiliation Order</option>
                  <option value="BUILDING_SAFETY">Building Structural Safety Certificate</option>
                  <option value="EVC_REPORT">EVC Expert Visit Report</option>
                </select>
              </div>

              <div>
                <label className="label">Validity Expiration Date (Optional)</label>
                <input
                  type="date"
                  className="input-field"
                  value={uploadValidUntil}
                  onChange={(e) => setUploadValidUntil(e.target.value)}
                />
              </div>

              <div>
                <label className="label">Select File (.PDF, .JPG, .PNG max 10MB)</label>
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  className="input-field"
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowDocUploadModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Upload Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
