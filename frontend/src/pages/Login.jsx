import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { ShieldAlert, Key, Mail, ArrowRight, Lock, Check, Eye, EyeOff } from 'lucide-react';

const DEMO_PRESETS = [
  { role: 'INSTITUTION', label: 'College Representative', email: 'college@demo.aicte.gov.in', desc: 'Delhi Inst of Tech' },
  { role: 'SCRUTINY_OFFICER', label: 'Scrutiny Officer', email: 'scrutiny@demo.aicte.gov.in', desc: 'Dr. A. K. Sharma' },
  { role: 'EVC_COORDINATOR', label: 'EVC Coordinator', email: 'evc@demo.aicte.gov.in', desc: 'Er. Rajesh Verma' },
  { role: 'COMMITTEE_MEMBER', label: 'SAC Committee Member', email: 'committee@demo.aicte.gov.in', desc: 'Prof. Swaminathan' },
  { role: 'AUTHORISED_OFFICIAL', label: 'Authorised Official', email: 'official@demo.aicte.gov.in', desc: 'Dr. Rekha Gupta' },
  { role: 'ADMIN', label: 'System Admin', email: 'admin@demo.aicte.gov.in', desc: 'Full System Control' },
  { role: 'AUDITOR', label: 'Chief Auditor', email: 'auditor@demo.aicte.gov.in', desc: 'Read-only Oversight' },
];

export const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('college@demo.aicte.gov.in');
  const [password, setPassword] = useState('Password@123');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPreset = (presetEmail) => {
    setEmail(presetEmail);
    setPassword('Password@123');
    setError(null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)'
    }}>
      <div style={{ width: '100%', maxWidth: '980px', display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '32px' }}>
        
        {/* Left: Presentation Info & Quick Role Switcher */}
        <div className="glass-panel" style={{ padding: '36px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', boxShadow: 'var(--shadow-md)' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: 'var(--radius-full)', background: '#eff6ff', border: '1px solid #bfdbfe', marginBottom: '16px' }}>
              <ShieldAlert size={16} color="#2563eb" />
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#1d4ed8', letterSpacing: '0.04em' }}>AICTE WATCHTOWER · OFFICIAL PORTAL</span>
            </div>
            <h1 style={{ fontSize: '2rem', lineHeight: 1.2, marginBottom: '12px', color: '#0f172a' }}>
              Approval Workflow Automation & Risk Oversight
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px' }}>
              Zero-stall approval tracking with proactive SLA watching, condition compliance, document validity renewal, and 2-level hierarchical escalations.
            </p>

            <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-gold)', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Demo Quick-Switch (Select any Role to Test):
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
              {DEMO_PRESETS.map((p) => {
                const selected = email === p.email;
                return (
                  <button
                    key={p.role}
                    type="button"
                    onClick={() => handleSelectPreset(p.email)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      background: selected ? '#eff6ff' : '#f8fafc',
                      border: selected ? '2px solid #2563eb' : '1px solid #e2e8f0',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: selected ? '#1d4ed8' : '#0f172a' }}>
                        {p.label}
                      </span>
                      {selected && <Check size={14} color="#2563eb" />}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {p.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div style={{ marginTop: '24px', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
            Official AICTE rules, deadlines and stage names live in dynamic configuration. Demo data is clearly labelled.
          </div>
        </div>

        {/* Right: Login Form */}
        <div className="glass-panel" style={{ padding: '36px', display: 'flex', flexDirection: 'column', justifyContent: 'center', boxShadow: 'var(--shadow-lg)' }}>
          <h2 style={{ fontSize: '1.4rem', marginBottom: '6px', color: '#0f172a' }}>Portal Sign In</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '24px' }}>
            Enter authorized credentials to access your workflow queue
          </p>

          {error && (
            <div style={{
              background: '#fff1f2',
              border: '1px solid #fecdd3',
              color: '#be123c',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              marginBottom: '18px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label className="label">Official Email Address</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  className="input-field"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@demo.aicte.gov.in"
                  required
                  style={{ paddingLeft: '38px' }}
                />
                <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '13px' }} />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-field"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  style={{ paddingLeft: '38px', paddingRight: '40px' }}
                />
                <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', pointerEvents: 'none' }} />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  title={showPassword ? 'Hide password' : 'Show password'}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '6px',
                    borderRadius: '6px',
                    transition: 'color 0.15s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Protected by account lockout (5 attempts) & tamper-resistant append-only audit trail.
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px', fontSize: '0.95rem', marginTop: '8px' }}
            >
              {loading ? 'Authenticating...' : 'Sign In to Watchtower'}
              <ArrowRight size={16} />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
};
