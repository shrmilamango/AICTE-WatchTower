import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import {
  ShieldCheck,
  Clock,
  FileWarning,
  Upload,
  CheckCircle,
  XCircle,
  Eye,
  RefreshCw,
  X,
  File
} from 'lucide-react';

export const CompliancePortal = () => {
  const { user, isInstitution, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState('undertakings');

  const [undertakings, setUndertakings] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState(null);

  // Evidence Modal state
  const [selectedUnd, setSelectedUnd] = useState(null);
  const [evidenceNotes, setEvidenceNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Verification Modal state
  const [verifyingUnd, setVerifyingUnd] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState('VERIFIED');
  const [verifyDays, setVerifyDays] = useState(15);

  // Document Renewal Modal state
  const [renewDoc, setRenewDoc] = useState(null);
  const [renewFile, setRenewFile] = useState(null);
  const [renewValidUntil, setRenewValidUntil] = useState('');
  const [renewing, setRenewing] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [uData, dData] = await Promise.all([
        api.get('/undertakings'),
        api.get('/documents')
      ]);
      setUndertakings(uData || []);
      setDocuments(dData || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmitEvidence = async (e) => {
    e.preventDefault();
    if (!selectedUnd) return;
    setSubmitting(true);
    try {
      await api.post(`/undertakings/${selectedUnd.id}/submit`, {
        evidence_notes: evidenceNotes
      });
      setMsg('Evidence submitted successfully. Awaiting official verification.');
      setSelectedUnd(null);
      setEvidenceNotes('');
      loadData();
    } catch (err) {
      alert(`Submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!verifyingUnd) return;
    try {
      await api.post(`/undertakings/${verifyingUnd.id}/verify`, {
        status: verifyStatus,
        new_due_days: verifyStatus === 'REJECTED' ? Number(verifyDays) : null
      });
      setMsg(`Undertaking successfully marked as ${verifyStatus}.`);
      setVerifyingUnd(null);
      loadData();
    } catch (err) {
      alert(`Verification failed: ${err.message}`);
    }
  };

  const handleRenewDocument = async (e) => {
    e.preventDefault();
    if (!renewDoc || !renewFile || !renewValidUntil) return;
    setRenewing(true);
    try {
      const formData = new FormData();
      formData.append('file', renewFile);
      formData.append('valid_from', new Date().toISOString());
      formData.append('valid_until', new Date(renewValidUntil).toISOString());

      await api.upload(`/documents/${renewDoc.id}/renew`, formData);
      setMsg(`Document ${renewDoc.doc_type} successfully renewed. Expiry alerts stopped.`);
      setRenewDoc(null);
      setRenewFile(null);
      loadData();
    } catch (err) {
      alert(`Renewal failed: ${err.message}`);
    } finally {
      setRenewing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px', color: '#0f172a' }}>Compliance & Document Validity Portal</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Post-approval undertakings verification and perpetual document expiry monitoring.
          </p>
        </div>

        <button onClick={loadData} className="btn btn-secondary btn-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {msg && (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', padding: '12px 16px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} />
          {msg}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('undertakings')}
          style={{
            background: activeTab === 'undertakings' ? '#eff6ff' : 'transparent',
            border: activeTab === 'undertakings' ? '1px solid #bfdbfe' : '1px solid transparent',
            color: activeTab === 'undertakings' ? '#1d4ed8' : 'var(--text-muted)',
            padding: '8px 18px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <ShieldCheck size={16} />
          Undertakings & Conditions ({undertakings.length})
        </button>

        <button
          onClick={() => setActiveTab('documents')}
          style={{
            background: activeTab === 'documents' ? '#eff6ff' : 'transparent',
            border: activeTab === 'documents' ? '1px solid #bfdbfe' : '1px solid transparent',
            color: activeTab === 'documents' ? '#1d4ed8' : 'var(--text-muted)',
            padding: '8px 18px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <FileWarning size={16} />
          Document Validity & Expiry Tracking ({documents.length})
        </button>
      </div>

      {/* Tab 1: Undertakings Table */}
      {activeTab === 'undertakings' && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Undertaking Title</th>
                <th>Application No</th>
                <th>College</th>
                <th>Due Date</th>
                <th>Status</th>
                <th>Evidence Notes</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {undertakings.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    No pending compliance undertakings recorded.
                  </td>
                </tr>
              ) : (
                undertakings.map((u) => (
                  <tr key={u.id} style={{ background: u.is_overdue ? '#fff1f2' : 'transparent' }}>
                    <td>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{u.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.description}</div>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#1d4ed8' }}>
                      {u.app_no}
                    </td>
                    <td>{u.institution_name}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: u.is_overdue ? '#be123c' : 'inherit' }}>
                        <Clock size={13} />
                        <span>{new Date(u.due_at).toLocaleDateString()}</span>
                      </div>
                    </td>
                    <td>
                      {u.status === 'VERIFIED' ? (
                        <span className="badge badge-success">VERIFIED</span>
                      ) : u.status === 'SUBMITTED' ? (
                        <span className="badge badge-purple">SUBMITTED</span>
                      ) : u.status === 'OVERDUE' ? (
                        <span className="badge badge-danger">OVERDUE</span>
                      ) : (
                        <span className="badge badge-warning">PENDING</span>
                      )}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {u.evidence_notes || '--'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        {isInstitution && u.status !== 'VERIFIED' && (
                          <button
                            onClick={() => setSelectedUnd(u)}
                            className="btn btn-primary btn-sm"
                          >
                            <Upload size={12} /> Submit Evidence
                          </button>
                        )}

                        {hasRole(['AUTHORISED_OFFICIAL', 'ADMIN', 'SCRUTINY_OFFICER']) && u.status === 'SUBMITTED' && (
                          <button
                            onClick={() => { setVerifyingUnd(u); setVerifyStatus('VERIFIED'); }}
                            className="btn btn-success btn-sm"
                          >
                            <CheckCircle size={12} /> Verify
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
      )}

      {/* Tab 2: Document Validity Table */}
      {activeTab === 'documents' && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Document Classification</th>
                <th>File Name</th>
                <th>Version</th>
                <th>Valid Until (Expiry)</th>
                <th>Days Remaining</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    No compliance documents found.
                  </td>
                </tr>
              ) : (
                documents.map((d) => (
                  <tr key={d.id} style={{ background: d.status === 'EXPIRED' ? '#fff1f2' : d.status === 'EXPIRING' ? '#fffbeb' : 'transparent' }}>
                    <td>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{d.doc_type}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <File size={15} color="#2563eb" />
                        <span>{d.file_name}</span>
                      </div>
                    </td>
                    <td><span className="badge badge-info">v{d.version_no}</span></td>
                    <td>
                      {d.valid_until ? new Date(d.valid_until).toLocaleDateString() : 'Perpetual'}
                    </td>
                    <td>
                      {d.days_until_expiry !== null ? (
                        <span style={{ fontWeight: 700, color: d.days_until_expiry <= 0 ? '#be123c' : d.days_until_expiry <= 30 ? '#b45309' : '#059669' }}>
                          {d.days_until_expiry <= 0 ? 'EXPIRED' : `${d.days_until_expiry} days`}
                        </span>
                      ) : '--'}
                    </td>
                    <td>
                      {d.status === 'EXPIRED' ? (
                        <span className="badge badge-danger">EXPIRED</span>
                      ) : d.status === 'EXPIRING' ? (
                        <span className="badge badge-warning">EXPIRING SOON</span>
                      ) : d.status === 'RENEWED' ? (
                        <span className="badge badge-purple">RENEWED</span>
                      ) : (
                        <span className="badge badge-success">VALID</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <a
                          href={`/api/v1/documents/${d.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline btn-sm"
                        >
                          View
                        </a>

                        {isInstitution && ['EXPIRING', 'EXPIRED'].includes(d.status) && (
                          <button
                            onClick={() => setRenewDoc(d)}
                            className="btn btn-primary btn-sm"
                          >
                            Renew Doc
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
      )}

      {/* Modal: Submit Undertaking Evidence */}
      {selectedUnd && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '28px', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', color: '#0f172a' }}>Submit Undertaking Evidence</h2>
              <button onClick={() => setSelectedUnd(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmitEvidence} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Undertaking: <strong>{selectedUnd.title}</strong>
              </div>

              <div>
                <label className="label">Compliance Evidence Remarks & Notarization Ref</label>
                <textarea
                  className="input-field"
                  rows={4}
                  value={evidenceNotes}
                  onChange={(e) => setEvidenceNotes(e.target.value)}
                  placeholder="Detail registration deed registration numbers, municipal officer approval refs, or notarized affidavits..."
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setSelectedUnd(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn btn-primary">
                  {submitting ? 'Submitting...' : 'Upload Compliance Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Verify Undertaking */}
      {verifyingUnd && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '480px', padding: '28px', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', color: '#0f172a' }}>Verify Undertaking Condition</h2>
              <button onClick={() => setVerifyingUnd(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Condition: <strong>{verifyingUnd.title}</strong>
              </div>

              <div style={{ background: '#f8fafc', padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SUBMITTED EVIDENCE:</div>
                <div style={{ fontSize: '0.85rem', color: '#0f172a', marginTop: '2px' }}>{verifyingUnd.evidence_notes}</div>
              </div>

              <div>
                <label className="label">Verification Determination</label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    type="button"
                    onClick={() => setVerifyStatus('VERIFIED')}
                    className={`btn ${verifyStatus === 'VERIFIED' ? 'btn-success' : 'btn-secondary'}`}
                    style={{ flex: 1 }}
                  >
                    VERIFY CONDITION
                  </button>
                  <button
                    type="button"
                    onClick={() => setVerifyStatus('REJECTED')}
                    className={`btn ${verifyStatus === 'REJECTED' ? 'btn-danger' : 'btn-secondary'}`}
                    style={{ flex: 1 }}
                  >
                    REJECT EVIDENCE
                  </button>
                </div>
              </div>

              {verifyStatus === 'REJECTED' && (
                <div>
                  <label className="label">Extension Days Allowed for Re-submission</label>
                  <input
                    type="number"
                    className="input-field"
                    value={verifyDays}
                    onChange={(e) => setVerifyDays(e.target.value)}
                    required
                  />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setVerifyingUnd(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Commit Verification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Document Renewal Flow */}
      {renewDoc && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '28px', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', color: '#0f172a' }}>Renew Expiring Document</h2>
              <button onClick={() => setRenewDoc(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleRenewDocument} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Renewing: <strong>{renewDoc.doc_type}</strong> ({renewDoc.file_name})
              </div>

              <div>
                <label className="label">New Valid Until Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={renewValidUntil}
                  onChange={(e) => setRenewValidUntil(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="label">Select Renewed Document (.PDF, .JPG, .PNG)</label>
                <input
                  type="file"
                  onChange={(e) => setRenewFile(e.target.files[0])}
                  className="input-field"
                  required
                />
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Rule 3.9: Old document will be marked as RENEWED, linked via replaced_by_id, and expiry alert reminders will immediately cease.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setRenewDoc(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={renewing} className="btn btn-primary">
                  {renewing ? 'Uploading Renewal...' : 'Submit Renewal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
