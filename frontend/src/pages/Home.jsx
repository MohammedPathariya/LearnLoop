import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from '../router';
import {
  addMaterial,
  createSession,
  deleteSession,
  getProgress,
  getSessions,
  openDemo,
  updateSession,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, MetricCard, Modal, PageHeader, ScoreBar, StatusNotice } from '../components/UI';

function Home() {
  const navigate = useNavigate();
  const initialLoadStarted = useRef(false);
  const [sessions, setSessions] = useState([]);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('');
  const [domain, setDomain] = useState('');
  const [materialTitle, setMaterialTitle] = useState('');
  const [materialContent, setMaterialContent] = useState('');
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  useEffect(() => {
    if (initialLoadStarted.current) return;
    initialLoadStarted.current = true;
    loadHome();
  }, []);

  async function loadHome() {
    setLoading(true);
    setError('');
    try {
      await openDemo();
      const nextSessions = await getSessions();
      const nextProgress = await getProgress();
      setSessions(nextSessions);
      setProgress(nextProgress);
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'LearnLoop could not load your study workspace.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    setError('');
    try {
      const session = await createSession({ title, domain });
      if (materialContent.trim()) {
        await addMaterial(session.id, {
          title: materialTitle.trim() || `${title} notes`,
          content: materialContent,
        });
      }
      setShowCreate(false);
      navigate(`/learn/${session.id}`);
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'The learning space could not be created.');
    }
  }

  async function handleRename(event) {
    event.preventDefault();
    await updateSession(renameTarget.id, { title: renameValue });
    setRenameTarget(null);
    await loadHome();
  }

  async function handleDelete(session) {
    if (!window.confirm(`Delete "${session.title}" and its saved study activity?`)) return;
    await deleteSession(session.id);
    await loadHome();
  }

  const demo = sessions.find((session) => session.is_demo);
  const latestSession = sessions[0] || demo;
  const recommendation = progress?.needs_review?.[0];

  return (
    <div className="page home-page">
      <PageHeader
        eyebrow="Your learning home"
        title="Pick up where you left off."
        description="Ask questions, take a quiz, or review flashcards inside one learning space."
        actions={(
          <>
            {latestSession && (
              <Link className="button primary" to={`/learn/${latestSession.id}`}>
                Continue learning
              </Link>
            )}
            <button className="button secondary" type="button" onClick={() => setShowCreate(true)}>
              Start something new
            </button>
          </>
        )}
      />

      {error && <StatusNotice type="error">{error}</StatusNotice>}

      {loading ? (
        <LoadingBlock label="Loading home" />
      ) : (
        <>
          <section className="section-block">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Continue learning</p>
                <h2>Your learning spaces</h2>
              </div>
              <Link className="text-link" to="/history">View history</Link>
            </div>
            {sessions.length ? (
              <div className="session-grid">
                {sessions.slice(0, 3).map((session) => {
                  const activity = session.material_count + session.quiz_count + session.flashcard_count;
                  const progressValue = Math.min(100, 20 + activity * 12);
                  return (
                    <article className="session-card" key={session.id}>
                      <div className="card-topline">
                        <span className={session.is_demo ? 'badge brand' : 'badge neutral'}>
                          {session.is_demo ? 'Guided demo' : session.domain || 'Learning space'}
                        </span>
                        <span>{new Date(session.updated_at).toLocaleDateString()}</span>
                      </div>
                      <h3>{session.title}</h3>
                      <p>{session.material_count} sources · {session.quiz_count} quizzes · {session.flashcard_count} card sets</p>
                      <ScoreBar value={progressValue} label={`${progressValue}% activity`} />
                      <div className="session-card-controls">
                        <Link className="button secondary" to={`/learn/${session.id}`}>Continue</Link>
                        {session.is_demo ? (
                          <Link className="text-link" to="/settings">Reset options</Link>
                        ) : (
                          <>
                            <button className="text-button" type="button" onClick={() => { setRenameTarget(session); setRenameValue(session.title); }}>Rename</button>
                            <button className="text-button destructive" type="button" onClick={() => handleDelete(session)}>Delete</button>
                          </>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                title="Start your first learning space"
                description="Name what you are studying, add your notes, and begin learning."
                action={<button className="button primary" type="button" onClick={() => setShowCreate(true)}>Start learning</button>}
              />
            )}
          </section>

          <section className="home-lower-grid">
            <div className="recommendation-card">
              <p className="eyebrow">Recommended next</p>
              <h2>{recommendation ? `Review ${recommendation.topic}` : 'Continue Machine Learning Foundations'}</h2>
              <p>
                {recommendation
                  ? `Your current average is ${recommendation.score}%. A focused quiz will reinforce this topic.`
                  : 'Return to your latest material and build on the questions you have already explored.'}
              </p>
              <Link className="button primary" to={demo ? `/learn/${demo.id}?mode=quiz` : '/learn'}>
                Start focused practice
              </Link>
            </div>
            <div className="progress-summary">
              <div className="section-heading compact">
                <h2>Progress summary</h2>
                <Link className="text-link" to="/progress">Details</Link>
              </div>
              <div className="metric-grid compact">
                <MetricCard label="Quiz average" value={`${progress?.average_score || 0}%`} />
                <MetricCard label="Learning spaces" value={progress?.sessions || 0} />
                <MetricCard label="Sources" value={progress?.materials || 0} />
                <MetricCard label="Card sets" value={progress?.flashcard_sets || 0} />
              </div>
            </div>
          </section>
        </>
      )}

      {showCreate && (
        <Modal title="Start something new" wide onClose={() => setShowCreate(false)}>
          <form className="form-stack" onSubmit={handleCreate}>
            <label>
              What are you learning?
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Neural network fundamentals" required autoFocus />
            </label>
            <label>
              Subject (optional)
              <input value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="e.g. Machine Learning" />
            </label>
            <label>
              Source title (optional)
              <input value={materialTitle} onChange={(event) => setMaterialTitle(event.target.value)} placeholder="e.g. Lecture notes" />
            </label>
            <label>
              Paste study material (optional)
              <textarea rows="7" value={materialContent} onChange={(event) => setMaterialContent(event.target.value)} placeholder="Paste notes now, or add sources later inside Learn." />
            </label>
            <div className="form-actions">
              <button className="button secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="button primary" type="submit">Open learning space</button>
            </div>
          </form>
        </Modal>
      )}

      {renameTarget && (
        <Modal title="Rename learning space" onClose={() => setRenameTarget(null)}>
          <form className="form-stack" onSubmit={handleRename}>
            <label>Name<input value={renameValue} onChange={(event) => setRenameValue(event.target.value)} required /></label>
            <div className="form-actions">
              <button className="button secondary" type="button" onClick={() => setRenameTarget(null)}>Cancel</button>
              <button className="button primary" type="submit">Save name</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

export default Home;
