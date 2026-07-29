import { useEffect, useState } from 'react';
import { Link, useNavigate } from '../router';
import { useAuth } from '../auth/AuthContext';
import { PageHeader, StatusNotice } from '../components/UI';

function Login() {
  const navigate = useNavigate();
  const { configured, loading, user, signIn, signUp } = useAuth();
  const [mode, setMode] = useState('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    if (!loading && user) navigate('/');
  }, [loading, navigate, user]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setSubmitting(true);
    try {
      if (mode === 'sign-in') {
        await signIn(email.trim(), password);
        navigate('/');
      } else {
        const result = await signUp(email.trim(), password);
        if (!result.session) {
          setNotice('Account created. You can sign in now.');
          setMode('sign-in');
          setPassword('');
        } else {
          navigate('/');
        }
      }
    } catch (requestError) {
      setError(requestError.message || 'Authentication failed.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page auth-page">
      <PageHeader
        eyebrow="Your account"
        title={mode === 'sign-in' ? 'Welcome back.' : 'Create your account.'}
        description="Save your learning history and scores while keeping your source material session-only."
      />
      {!configured && <StatusNotice type="error">Supabase authentication is not configured in this environment.</StatusNotice>}
      {error && <StatusNotice type="error">{error}</StatusNotice>}
      {notice && <StatusNotice type="success">{notice}</StatusNotice>}
      <section className="auth-card card-panel">
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'} />
          </label>
          <button className="button primary full" type="submit" disabled={submitting || !configured}>
            {submitting ? 'Working...' : mode === 'sign-in' ? 'Sign in' : 'Create account'}
          </button>
        </form>
        <div className="auth-switch">
          <span>{mode === 'sign-in' ? 'New to LearnLoop?' : 'Already have an account?'}</span>
          <button className="text-button" type="button" onClick={() => { setMode(mode === 'sign-in' ? 'sign-up' : 'sign-in'); setError(''); setNotice(''); }}>
            {mode === 'sign-in' ? 'Create an account' : 'Sign in'}
          </button>
        </div>
        <Link className="text-link" to="/">Continue as guest</Link>
      </section>
    </div>
  );
}

export default Login;
