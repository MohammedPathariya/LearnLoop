import { useState } from 'react';
import { useNavigate } from '../router';
import { useAuth } from '../auth/AuthContext';
import { ConfirmDialog, PageHeader, StatusNotice } from '../components/UI';

function Account() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [error, setError] = useState('');
  const [signingOut, setSigningOut] = useState(false);
  const [confirmSignOut, setConfirmSignOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    setError('');
    try {
      await signOut();
      navigate('/');
    } catch (signOutError) {
      setError(signOutError.message || 'Could not sign out.');
      setSigningOut(false);
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Account"
        title="Your profile"
        description="Manage your signed-in session and understand what LearnLoop saves to your account."
      />
      {error && <StatusNotice type="error">{error}</StatusNotice>}
      <div className="settings-grid">
        <section className="card-panel">
          <h2>Profile</h2>
          <dl className="settings-list">
            <div><dt>Email</dt><dd>{user?.email || 'Not signed in'}</dd></div>
            <div><dt>Account status</dt><dd>Signed in</dd></div>
          </dl>
        </section>
        <section className="card-panel">
          <h2>Saved activity</h2>
          <p>Your learning spaces, conversation history, quiz results, and flashcard sets are associated with this account. Source material remains session-only.</p>
        </section>
        <section className="card-panel account-danger-zone">
          <h2>Session</h2>
          <p>Signing out returns you to guest mode. Guest activity is not associated with this account.</p>
          <button className="button secondary" type="button" onClick={() => setConfirmSignOut(true)} disabled={signingOut}>Sign out</button>
        </section>
      </div>
      {confirmSignOut && (
        <ConfirmDialog
          title="Sign out of LearnLoop?"
          description="Your saved account activity will remain available when you sign in again. Guest mode will open after you sign out."
          confirmLabel="Sign out"
          onClose={() => setConfirmSignOut(false)}
          onConfirm={handleSignOut}
          busy={signingOut}
        />
      )}
    </div>
  );
}

export default Account;
