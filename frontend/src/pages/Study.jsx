import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from '../router';
import {
  addMaterial,
  askQuestion,
  createSession,
  getMessages,
  getSession,
  getSessions,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, Modal, PageHeader, StatusNotice } from '../components/UI';
import Flashcards from './Flashcards';
import Practice from './Practice';

function Study() {
  const { sessionId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [selectedSources, setSelectedSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [answering, setAnswering] = useState(false);
  const [error, setError] = useState('');
  const [showMaterial, setShowMaterial] = useState(false);
  const [materialTitle, setMaterialTitle] = useState('');
  const [materialContent, setMaterialContent] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [journeyTitle, setJourneyTitle] = useState('');
  const [showSources, setShowSources] = useState(false);
  const [showGuide, setShowGuide] = useState(() => localStorage.getItem('learnloop-guide-dismissed') !== 'true');
  const mode = ['ask', 'quiz', 'flashcards'].includes(searchParams.get('mode')) ? searchParams.get('mode') : 'ask';

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    } else {
      getSessions().then(setSessions).catch(() => setError('Learning spaces could not be loaded.')).finally(() => setLoading(false));
    }
  }, [sessionId]);

  async function loadSession(id) {
    setLoading(true);
    setError('');
    try {
      const [sessionData, messageData] = await Promise.all([getSession(id), getMessages(id)]);
      setSession(sessionData);
      setMessages(messageData);
      const lastGrounded = [...messageData].reverse().find((message) => message.grounded);
      setSelectedSources(lastGrounded?.sources || []);
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'This learning space could not be loaded.');
    } finally {
      setLoading(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    if (!question.trim() || answering) return;
    const nextQuestion = question.trim();
    setQuestion('');
    setError('');
    setAnswering(true);
    setMessages((current) => [...current, { id: `local-${Date.now()}`, role: 'user', content: nextQuestion, grounded: false }]);
    try {
      const answer = await askQuestion(session.id, nextQuestion);
      setMessages((current) => [...current, answer]);
      setSelectedSources(answer.sources || []);
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'The answer could not be generated.');
    } finally {
      setAnswering(false);
    }
  }

  async function handleAddMaterial(event) {
    event.preventDefault();
    setError('');
    try {
      await addMaterial(session.id, { title: materialTitle, content: materialContent });
      setShowMaterial(false);
      setMaterialTitle('');
      setMaterialContent('');
      await loadSession(session.id);
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'The material could not be indexed.');
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    const created = await createSession({ title: journeyTitle });
    navigate(`/learn/${created.id}`);
  }

  function changeMode(nextMode) {
    setSearchParams(nextMode === 'ask' ? {} : { mode: nextMode });
  }

  function dismissGuide() {
    localStorage.setItem('learnloop-guide-dismissed', 'true');
    setShowGuide(false);
  }

  const recentQuestions = useMemo(
    () => messages.filter((message) => message.role === 'user').slice(-4).reverse(),
    [messages],
  );

  if (loading) return <div className="page"><LoadingBlock label="Loading study workspace" /></div>;
  if (sessionId && (!session || session.id !== sessionId)) {
    return <div className="page"><LoadingBlock label="Opening learning space" /></div>;
  }

  if (!sessionId) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Learn"
          title="Choose a learning space"
          description="Questions, quizzes, flashcards, and sources stay together in one place."
          actions={<button className="button primary" type="button" onClick={() => setShowCreate(true)}>New learning space</button>}
        />
        {error && <StatusNotice type="error">{error}</StatusNotice>}
        {sessions.length ? (
          <div className="session-grid">
            {sessions.map((item) => (
              <article className="session-card" key={item.id}>
                <span className={item.is_demo ? 'badge brand' : 'badge neutral'}>{item.is_demo ? 'Guided demo' : item.domain || 'Learning space'}</span>
                <h2>{item.title}</h2>
                <p>{item.material_count} sources · {item.message_count} conversation messages</p>
                <Link className="button primary full" to={`/learn/${item.id}`}>Open</Link>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No learning spaces yet" description="Create one to add sources and begin learning." />
        )}
        {showCreate && (
          <Modal title="New learning space" onClose={() => setShowCreate(false)}>
            <form className="form-stack" onSubmit={handleCreate}>
              <label>What are you learning?<input value={journeyTitle} onChange={(event) => setJourneyTitle(event.target.value)} required /></label>
              <div className="form-actions">
                <button className="button secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
                <button className="button primary" type="submit">Create</button>
              </div>
            </form>
          </Modal>
        )}
      </div>
    );
  }

  return (
    <div className="study-page">
      {error && <StatusNotice type="error">{error}</StatusNotice>}
      {session?.is_demo && showGuide && (
        <section className="learn-guide">
          <div>
            <p className="eyebrow">Guided demo</p>
            <strong>Try the full flow: ask a question, take a quiz, then review flashcards.</strong>
          </div>
          <button className="text-button" type="button" onClick={dismissGuide}>Got it</button>
        </section>
      )}
      <div className="study-layout">
        <aside className="study-sidebar">
          <div>
            <p className="eyebrow">{session?.is_demo ? 'Guided demo' : session?.domain || 'Learning space'}</p>
            <h1>{session?.title}</h1>
            <Link className="text-link" to="/learn">Switch learning space</Link>
          </div>
          <section>
            <div className="sidebar-heading">
              <h2>Sources</h2>
              <button type="button" onClick={() => setShowMaterial(true)}>Add</button>
            </div>
            {session?.materials?.length ? session.materials.map((material) => (
              <div className="material-mini" key={material.id}>
                <span className={`status-dot ${material.status}`} />
                <div><strong>{material.title}</strong><small>{material.chunk_count} chunks</small></div>
              </div>
            )) : <p className="muted-copy">Add a source before asking grounded questions.</p>}
            <Link className="text-link sidebar-link" to={`/materials?session=${session.id}`}>Manage sources</Link>
          </section>
          {mode === 'ask' && <section>
            <h2>Recent questions</h2>
            {recentQuestions.length ? recentQuestions.map((message) => (
              <button className="recent-question" type="button" key={message.id} onClick={() => setQuestion(message.content)}>
                {message.content}
              </button>
            )) : <p className="muted-copy">Your questions will appear here.</p>}
          </section>}
        </aside>

        <section className="learn-main">
          <nav className="learn-mode-tabs" aria-label="Learning mode">
            {[
              ['ask', 'Ask'],
              ['quiz', 'Quiz'],
              ['flashcards', 'Flashcards'],
            ].map(([value, label]) => (
              <button className={mode === value ? 'active' : ''} type="button" key={value} onClick={() => changeMode(value)}>
                {label}
              </button>
            ))}
          </nav>

          {mode === 'ask' && (
            <section className="conversation-panel">
              <div className="conversation-heading">
                <div>
                  <p className="eyebrow">Ask</p>
                  <h2>Learn from your sources</h2>
                </div>
                <button className="button secondary compact-button" type="button" onClick={() => setShowSources(true)}>
                  View sources
                </button>
              </div>
              <div className="message-list" aria-live="polite">
                {messages.length === 0 && (
                  <EmptyState
                    title="Start with a question"
                    description="LearnLoop will answer from this learning space and show the supporting sources."
                  />
                )}
                {messages.map((message) => (
                  <article className={`message ${message.role}`} key={message.id}>
                    <span className="message-role">{message.role === 'user' ? 'You' : 'learnloop'}</span>
                    <p>{message.content}</p>
                    {message.grounded && (
                      <button
                        className="grounding-line"
                        type="button"
                        onClick={() => {
                          setSelectedSources(message.sources || []);
                          setShowSources(true);
                        }}
                      >
                        View {message.source_count || message.sources?.length || 0} supporting sources
                      </button>
                    )}
                  </article>
                ))}
                {answering && <div className="answering-state"><span /><span /><span /> Reading your sources</div>}
              </div>
              <form className="question-composer" onSubmit={handleAsk}>
                <label className="sr-only" htmlFor="study-question">Ask a question</label>
                <textarea
                  id="study-question"
                  rows="2"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="Ask a question about your sources..."
                  disabled={answering || !session?.materials?.length}
                />
                <button className="button primary" type="submit" disabled={answering || !question.trim()}>Ask</button>
              </form>
            </section>
          )}
          {mode === 'quiz' && <Practice embedded sessionIdOverride={session.id} />}
          {mode === 'flashcards' && <Flashcards embedded sessionIdOverride={session.id} />}
        </section>
      </div>

      {showMaterial && (
        <Modal title="Add a source" wide onClose={() => setShowMaterial(false)}>
          <form className="form-stack" onSubmit={handleAddMaterial}>
            <label>Source title<input value={materialTitle} onChange={(event) => setMaterialTitle(event.target.value)} required /></label>
            <label>Paste study text<textarea rows="10" value={materialContent} onChange={(event) => setMaterialContent(event.target.value)} required /></label>
            <p className="field-note">Text paste is supported today. File upload is not available yet.</p>
            <div className="form-actions">
              <button className="button secondary" type="button" onClick={() => setShowMaterial(false)}>Cancel</button>
              <button className="button primary" type="submit">Add source</button>
            </div>
          </form>
        </Modal>
      )}

      {showSources && (
        <Modal title="Supporting sources" wide onClose={() => setShowSources(false)}>
          <div className="source-drawer-list">
            {selectedSources.length ? selectedSources.map((source, index) => (
              <details className="source-card" key={source.id || `${source.source_id}-${index}`} open={index === 0}>
                <summary>
                  <span>Source {index + 1}</span>
                  <strong>{source.title || 'Study source'}</strong>
                  <small>Chunk {Number(source.chunk_index || 0) + 1}</small>
                </summary>
                {source.text && <p>{source.text}</p>}
              </details>
            )) : (
              <EmptyState title="No answer sources selected" description="Ask a question, then open the sources attached to the answer." />
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}

export default Study;
