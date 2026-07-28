import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  addMaterial,
  askQuestion,
  createSession,
  getMessages,
  getSession,
  getSessions,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, Modal, PageHeader, StatusNotice } from '../components/UI';

function Study() {
  const { sessionId } = useParams();
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

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    } else {
      getSessions().then(setSessions).catch(() => setError('Study journeys could not be loaded.')).finally(() => setLoading(false));
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
      setError(requestError.response?.data?.error || 'This study journey could not be loaded.');
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
    navigate(`/study/${created.id}`);
  }

  const recentQuestions = useMemo(
    () => messages.filter((message) => message.role === 'user').slice(-4).reverse(),
    [messages],
  );

  if (loading) return <div className="page"><LoadingBlock label="Loading study workspace" /></div>;

  if (!sessionId) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Study"
          title="Choose a learning journey"
          description="Every journey keeps its materials, grounded conversation, quizzes, and flashcards together."
          actions={<button className="button primary" type="button" onClick={() => setShowCreate(true)}>New journey</button>}
        />
        {error && <StatusNotice type="error">{error}</StatusNotice>}
        {sessions.length ? (
          <div className="session-grid">
            {sessions.map((item) => (
              <article className="session-card" key={item.id}>
                <span className={item.is_demo ? 'badge brand' : 'badge neutral'}>{item.is_demo ? 'Demo journey' : item.domain || 'Journey'}</span>
                <h2>{item.title}</h2>
                <p>{item.material_count} materials · {item.message_count} conversation messages</p>
                <Link className="button primary full" to={`/study/${item.id}`}>Open workspace</Link>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No study journeys yet" description="Create one to begin adding material." />
        )}
        {showCreate && (
          <Modal title="New study journey" onClose={() => setShowCreate(false)}>
            <form className="form-stack" onSubmit={handleCreate}>
              <label>Journey name<input value={journeyTitle} onChange={(event) => setJourneyTitle(event.target.value)} required /></label>
              <div className="form-actions">
                <button className="button secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</button>
                <button className="button primary" type="submit">Create journey</button>
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
      <div className="study-layout">
        <aside className="study-sidebar">
          <div>
            <p className="eyebrow">{session?.is_demo ? 'Demo journey' : session?.domain || 'Study journey'}</p>
            <h1>{session?.title}</h1>
          </div>
          <section>
            <div className="sidebar-heading">
              <h2>Materials</h2>
              <button type="button" onClick={() => setShowMaterial(true)}>Add</button>
            </div>
            {session?.materials?.length ? session.materials.map((material) => (
              <div className="material-mini" key={material.id}>
                <span className={`status-dot ${material.status}`} />
                <div><strong>{material.title}</strong><small>{material.chunk_count} chunks</small></div>
              </div>
            )) : <p className="muted-copy">Add material before asking grounded questions.</p>}
          </section>
          <section>
            <h2>Recent questions</h2>
            {recentQuestions.length ? recentQuestions.map((message) => (
              <button className="recent-question" type="button" key={message.id} onClick={() => setQuestion(message.content)}>
                {message.content}
              </button>
            )) : <p className="muted-copy">Your questions will appear here.</p>}
          </section>
        </aside>

        <section className="conversation-panel">
          <div className="conversation-heading">
            <div>
              <p className="eyebrow">Grounded study</p>
              <h2>Ask from your materials</h2>
            </div>
            <span className="badge brand">{session?.materials?.length || 0} sources ready</span>
          </div>
          <div className="message-list" aria-live="polite">
            {messages.length === 0 && (
              <EmptyState
                title="Start with a question"
                description="LearnLoop will answer from the material in this journey and show the supporting sources."
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
                    onClick={() => setSelectedSources(message.sources || [])}
                  >
                    Based on your study material · {message.source_count || message.sources?.length || 0} sources
                  </button>
                )}
              </article>
            ))}
            {answering && <div className="answering-state"><span /><span /><span /> Reading your materials</div>}
          </div>
          <form className="question-composer" onSubmit={handleAsk}>
            <label className="sr-only" htmlFor="study-question">Ask a question</label>
            <textarea
              id="study-question"
              rows="2"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about this study material..."
              disabled={answering || !session?.materials?.length}
            />
            <button className="button primary" type="submit" disabled={answering || !question.trim()}>Ask</button>
          </form>
        </section>

        <aside className="evidence-panel">
          <div>
            <p className="eyebrow">Evidence</p>
            <h2>Supporting sources</h2>
          </div>
          {selectedSources.length ? selectedSources.map((source, index) => (
            <details className="source-card" key={source.id || `${source.source_id}-${index}`}>
              <summary>
                <span>Source {index + 1}</span>
                <strong>{source.title || 'Study material'}</strong>
                <small>Chunk {Number(source.chunk_index || 0) + 1}</small>
              </summary>
              {source.text && <p>{source.text}</p>}
            </details>
          )) : (
            <p className="muted-copy">Select a grounded answer to inspect its evidence.</p>
          )}
          <div className="evidence-actions">
            <Link className="button primary full" to={`/practice?session=${session.id}`}>Generate quiz</Link>
            <Link className="button secondary full" to={`/flashcards?session=${session.id}`}>Create flashcards</Link>
          </div>
        </aside>
      </div>

      {showMaterial && (
        <Modal title="Add study material" wide onClose={() => setShowMaterial(false)}>
          <form className="form-stack" onSubmit={handleAddMaterial}>
            <label>Material title<input value={materialTitle} onChange={(event) => setMaterialTitle(event.target.value)} required /></label>
            <label>Paste study text<textarea rows="10" value={materialContent} onChange={(event) => setMaterialContent(event.target.value)} required /></label>
            <p className="field-note">Text paste is supported today. File upload is not available yet.</p>
            <div className="form-actions">
              <button className="button secondary" type="button" onClick={() => setShowMaterial(false)}>Cancel</button>
              <button className="button primary" type="submit">Index material</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

export default Study;
