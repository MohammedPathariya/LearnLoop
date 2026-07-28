import { useEffect, useState } from 'react';
import { getHealth, resetDemo } from '../api/learnloopApi';
import { PageHeader, StatusNotice } from '../components/UI';

function Settings() {
  const [backend, setBackend] = useState('Checking');
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
        description="LearnLoop has no user accounts. These settings describe this browser’s demo workspace and service status."
      />
      {notice && <StatusNotice type="success">{notice}</StatusNotice>}
      <div className="settings-grid">
        <section className="card-panel">
          <h2>Service status</h2>
          <dl className="settings-list">
            <div><dt>Backend</dt><dd><span className={`status-dot ${backend === 'Available' ? 'indexed' : 'failed'}`} />{backend}</dd></div>
            <div><dt>Study data</dt><dd>Browser-scoped persistent sessions</dd></div>
            <div><dt>Material input</dt><dd>Text paste</dd></div>
            <div><dt>Theme</dt><dd>Light</dd></div>
          </dl>
        </section>
        <section className="card-panel">
          <h2>Demo workspace</h2>
          <p>Restore the seeded Machine Learning Foundations journey. This removes changes made to your isolated demo copy.</p>
          <button className="button secondary" type="button" onClick={handleReset}>Reset demo journey</button>
        </section>
        <section className="card-panel">
          <h2>Data boundaries</h2>
          <p>No account or avatar is created. A random browser identifier keeps this browser’s study journeys separate from other visitors.</p>
        </section>
      </div>
    </div>
  );
}

export default Settings;
