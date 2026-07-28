import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import {
  generateFlashcards,
  getFlashcardSet,
  getFlashcardSets,
  getSessions,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, PageHeader, SelectField, StatusNotice } from '../components/UI';

function Flashcards() {
  const { setId } = useParams();
  const [searchParams] = useSearchParams();
  const [sets, setSets] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedSet, setSelectedSet] = useState(null);
  const [sessionId, setSessionId] = useState(searchParams.get('session') || '');
  const [sourceMode, setSourceMode] = useState(searchParams.get('session') ? 'session' : 'topic');
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(5);
  const [cardIndex, setCardIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getFlashcardSets(), getSessions()])
      .then(async ([setData, sessionData]) => {
        setSets(setData);
        setSessions(sessionData);
        if (sessionData.length) setSessionId((current) => current || sessionData[0].id);
        const initialId = setId || setData[0]?.id;
        if (initialId) setSelectedSet(await getFlashcardSet(initialId));
      })
      .catch(() => setError('Flashcards could not be loaded.'))
      .finally(() => setLoading(false));
  }, [setId]);

  async function handleGenerate(event) {
    event.preventDefault();
    setGenerating(true);
    setError('');
    try {
      const payload = { num_cards: Number(count) };
      if (sourceMode === 'session') payload.session_id = sessionId;
      if (sourceMode === 'topic') payload.topic = topic;
      const created = await generateFlashcards(payload);
      const complete = { ...created, topic: topic || sessions.find((item) => item.id === sessionId)?.title || 'Study material' };
      setSelectedSet(complete);
      setCardIndex(0);
      setFlipped(false);
      setSets(await getFlashcardSets());
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'Flashcard generation failed.');
    } finally {
      setGenerating(false);
    }
  }

  async function chooseSet(id) {
    setSelectedSet(await getFlashcardSet(id));
    setCardIndex(0);
    setFlipped(false);
  }

  const cards = selectedSet?.flashcards || [];
  const card = cards[cardIndex];

  return (
    <div className="page">
      <PageHeader
        eyebrow="Flashcards"
        title="Review one concept at a time."
        description="Generate a focused set from a study journey or topic, then move through it without distractions."
      />
      {error && <StatusNotice type="error">{error}</StatusNotice>}
      {loading ? <LoadingBlock /> : (
        <div className="flashcard-layout">
          <aside className="flashcard-sidebar card-panel">
            <h2>Saved sets</h2>
            {sets.length ? sets.map((set) => (
              <button className={selectedSet?.id === set.id ? 'set-row active' : 'set-row'} type="button" key={set.id} onClick={() => chooseSet(set.id)}>
                <span>{set.topic}</span>
                <small>{set.num_cards} cards · {new Date(set.timestamp).toLocaleDateString()}</small>
              </button>
            )) : <p className="muted-copy">No saved sets yet.</p>}
            <hr />
            <h2>Create a set</h2>
            <form className="form-stack" onSubmit={handleGenerate}>
              <div className="segmented-control">
                <button className={sourceMode === 'session' ? 'active' : ''} type="button" onClick={() => setSourceMode('session')}>Journey</button>
                <button className={sourceMode === 'topic' ? 'active' : ''} type="button" onClick={() => setSourceMode('topic')}>Topic</button>
              </div>
              {sourceMode === 'session' ? (
                <SelectField
                  label="Study journey"
                  value={sessionId}
                  onChange={setSessionId}
                  options={sessions.map((session) => ({ value: session.id, label: session.title }))}
                  disabled={!sessions.length}
                />
              ) : (
                <label>Topic<input value={topic} onChange={(event) => setTopic(event.target.value)} required /></label>
              )}
              <label>Number of cards<input type="number" min="1" max="10" value={count} onChange={(event) => setCount(event.target.value)} /></label>
              <button className="button primary full" type="submit" disabled={generating}>{generating ? 'Generating...' : 'Generate set'}</button>
            </form>
          </aside>

          <section className="flashcard-review">
            {card ? (
              <>
                <div className="review-heading">
                  <div><p className="eyebrow">Reviewing</p><h2>{selectedSet.topic}</h2></div>
                  <span>{cardIndex + 1} / {cards.length}</span>
                </div>
                <button
                  type="button"
                  className={`review-card ${flipped ? 'flipped' : ''}`}
                  onClick={() => setFlipped((current) => !current)}
                  aria-label={flipped ? 'Show term' : 'Show definition'}
                >
                  <span className="card-face-label">{flipped ? 'Definition' : 'Term'}</span>
                  <strong>{flipped ? card.definition : card.term}</strong>
                  <small>Click to flip</small>
                </button>
                <div className="review-controls">
                  <button className="button secondary" type="button" disabled={cardIndex === 0} onClick={() => { setCardIndex((current) => current - 1); setFlipped(false); }}>Previous</button>
                  <div className="coming-soon">Mark known / needs review <span>Coming soon</span></div>
                  <button className="button primary" type="button" disabled={cardIndex === cards.length - 1} onClick={() => { setCardIndex((current) => current + 1); setFlipped(false); }}>Next</button>
                </div>
              </>
            ) : (
              <EmptyState title="Choose or create a flashcard set" description="A focused review card will appear here." />
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default Flashcards;
