import { useEffect, useState } from 'react';
import { getHealth, resetDemo } from '../api/learnloopApi';
import { useAuth } from '../auth/AuthContext';
import { PageHeader } from '../components/UI';

function Settings() {
  const [backend, setBackend] = useState('Checking');
  const { user } = useAuth();
  const [notice, setNotice] = useState('');

  useEffect(() => {
    getHealth().then(() => setBackend('Available')).catch(() => setBackend('Unavailable'));
  }, []);

  async function handleReset() {
    if (!window.confirm('Reset your browser’s Machine Learning Foundations demo journey?')) return;
    await resetDemo();
    setNotice('The demo journey has been restored to its original state.');
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="System"
        title="Application information"
        description="Manage your LearnLoop account and review the application boundaries."
      />
      {notice && <p className="status-notice success">{notice}</p>}
      <div className="settings-grid">
        <section className="card-panel">
          <h2>Service status</h2>
          <dl className="settings-list">
            <div><dt>Backend</dt><dd><span className={`status-dot ${backend === 'Available' ? 'indexed' : 'failed'}`} />{backend}</dd></div>
            <div><dt>Account</dt><dd>{user?.email || 'Guest session'}</dd></div>
            <div><dt>Source privacy</dt><dd>Sources are session-only</dd></div>
            <div><dt>Theme</dt><dd>Light</dd></div>
          </dl>
        </section>
        <section className="card-panel">
          <h2>Data boundaries</h2>
          <p>PDFs and pasted source material are used for the current study session and are not stored as permanent sources.</p>
        </section>
        {!user && (
          <section className="card-panel">
            <h2>Guest demo</h2>
            <p>Guests can explore the guided demo. It is scoped to this browser session and is not saved to an account.</p>
            <button className="button secondary" type="button" onClick={handleReset}>Reset demo journey</button>
          </section>
        )}
      </div>
    </div>
  );
}

export default Settings;
