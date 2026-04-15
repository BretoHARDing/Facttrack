import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const result = await login(email, password, totp || undefined);
      if (result.mfaRequired && !totp) {
        setMfaRequired(true);
      } else {
        navigate('/cases');
      }
    } catch {
      setError('Invalid credentials or TOTP code.');
    }
  };

  return (
    <div style={{ maxWidth: 380, margin: '6rem auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>FACTTRACK</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '0.75rem' }}>
          <label>Email<br />
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ width: '100%' }} />
          </label>
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <label>Password<br />
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: '100%' }} />
          </label>
        </div>
        {mfaRequired && (
          <div style={{ marginBottom: '0.75rem' }}>
            <label>Authenticator code<br />
              <input type="text" inputMode="numeric" value={totp} onChange={e => setTotp(e.target.value)} required style={{ width: '100%' }} />
            </label>
          </div>
        )}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" style={{ width: '100%', padding: '0.5rem' }}>
          {mfaRequired ? 'Verify' : 'Log in'}
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '1rem' }}>
        No account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}
