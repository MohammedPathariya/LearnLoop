import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
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
  const [sessions, setSessions] = useState([]);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('');
  const [domain, setDomain] = useState('');
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  useEffect(() => {
    loadHome();
  }, []);

  async function loadHome() {
    setLoading(true);
    setError('');
    try {
      let nextSessions = await getSessions();
      if (nextSessions.length === 0) {
        await openDemo();
        nextSessions = await getSessions();
      }
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
    const session = await createSession({ title, domain });
    setShowCreate(false);
    navigate(`/study/${session.id}`);
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
  const recommendation = progress?.needs_review?.[0];

  return (
    <div className="page home-page">
      <PageHeader
        eyebrow="Your study workspace"
        title="Learn from your own material, then prove what stuck."
        description="Bring in a topic, ask source-grounded questions, and turn the same material into quizzes and flashcards."
        actions={(
          <>
            <button className="button primary" type="button" onClick={() => setShowCreate(true)}>
              Start a study journey
            </button>
            {demo && (
              <Link className="button secondary" to={`/study/${demo.id}`}>
                Explore demo journey
              </Link>
            )}
          </>
        )}
      />

      {error && <StatusNotice type="error">{error}</StatusNotice>}

      <section className="quick-actions" aria-label="Quick actions">
        <Link to={demo ? `/study/${demo.id}` : '/study'}>
          <span>01</span><strong>Ask a question</strong><small>Study with grounded answers</small>
        </Link>
        <Link to="/materials">
          <span>02</span><strong>Add material</strong><small>Paste and index study notes</small>
        </Link>
        <Link to={demo ? `/practice?session=${demo.id}` : '/practice'}>
          <span>03</span><strong>Generate a quiz</strong><small>Test the current material</small>
        </Link>
        <Link to={demo ? `/flashcards?session=${demo.id}` : '/flashcards'}>
          <span>04</span><strong>Create flashcards</strong><small>Turn concepts into review cards</small>
        </Link>
      </section>

      {loading ? (
        <LoadingBlock label="Loading home" />
      ) : (
        <>
          <section className="section-block">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Continue learning</p>
                <h2>Recent journeys</h2>
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
                          {session.is_demo ? 'Demo journey' : session.domain || 'Study journey'}
                        </span>
                        <span>{new Date(session.updated_at).toLocaleDateString()}</span>
                      </div>
                      <h3>{session.title}</h3>
                      <p>{session.material_count} materials · {session.quiz_count} quizzes · {session.flashcard_count} card sets</p>
                      <ScoreBar value={progressValue} label={`${progressValue}% journey activity`} />
                      <div className="session-card-controls">
                        <Link className="button secondary" to={`/study/${session.id}`}>Continue</Link>
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
                title="Start your first study journey"
                description="Create a session, add material, and ask your first grounded question."
                action={<button className="button primary" type="button" onClick={() => setShowCreate(true)}>Create session</button>}
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
              <Link className="button primary" to={demo ? `/practice?session=${demo.id}` : '/practice'}>
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
                <MetricCard label="Study journeys" value={progress?.sessions || 0} />
                <MetricCard label="Materials" value={progress?.materials || 0} />
                <MetricCard label="Card sets" value={progress?.flashcard_sets || 0} />
              </div>
            </div>
          </section>
        </>
      )}

      {showCreate && (
        <Modal title="Start a study journey" onClose={() => setShowCreate(false)}>
          <form className="form-stack" onSubmit={handleCreate}>
            <label>
              Journey name
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Neural network fundamentals" required />
            </label>
            <label>
              Domain
              <input value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="e.g. Machine Learning" />
            </label>
            <div className="form-actions">
              <button className="button secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="button primary" type="submit">Create journey</button>
            </div>
          </form>
        </Modal>
      )}

      {renameTarget && (
        <Modal title="Rename study journey" onClose={() => setRenameTarget(null)}>
          <form className="form-stack" onSubmit={handleRename}>
            <label>Journey name<input value={renameValue} onChange={(event) => setRenameValue(event.target.value)} required /></label>
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
