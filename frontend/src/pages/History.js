import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  deleteFlashcardSet,
  deleteQuiz,
  getHistory,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, PageHeader, StatusNotice } from '../components/UI';

function History() {
  const [items, setItems] = useState([]);
  const [type, setType] = useState('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getHistory()
      .then(setItems)
      .catch(() => setError('History could not be loaded.'))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(item) {
    if (!window.confirm(`Delete this ${item.type} record?`)) return;
    if (item.type === 'quiz') await deleteQuiz(item.id);
    if (item.type === 'flashcards') await deleteFlashcardSet(item.id);
    setItems(await getHistory());
  }

  const filtered = useMemo(() => items.filter((item) => (
    (type === 'all' || item.type === type)
    && item.title.toLowerCase().includes(query.toLowerCase())
  )), [items, type, query]);

  return (
    <div className="page">
      <PageHeader
        eyebrow="History"
        title="Return to the work you have already done."
        description="Learning spaces, quiz attempts, and flashcard sets are kept in one searchable timeline."
      />
      {error && <StatusNotice type="error">{error}</StatusNotice>}
      <div className="toolbar">
        <div className="filter-chips" aria-label="History type">
          {['all', 'session', 'quiz', 'flashcards'].map((value) => (
            <button className={type === value ? 'active' : ''} type="button" key={value} onClick={() => setType(value)}>
              {value === 'all' ? 'All activity' : value}
            </button>
          ))}
        </div>
        <label className="search-field"><span>Search history</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by topic or learning space" /></label>
      </div>
      {loading ? <LoadingBlock /> : filtered.length ? (
        <div className="history-list">
          {filtered.map((item) => (
            <article className="history-row" key={`${item.type}-${item.id}`}>
              <span className={`history-type type-${item.type}`}>{item.type.slice(0, 2).toUpperCase()}</span>
              <div className="history-main"><strong>{item.title}</strong><span>{new Date(item.timestamp).toLocaleString()}</span></div>
              <span className="history-metadata">{item.metadata}</span>
              <div className="history-actions">
                <Link className="button secondary" to={item.href}>{item.action}</Link>
                {item.type !== 'session' && <button className="text-button destructive" type="button" onClick={() => handleDelete(item)}>Delete</button>}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No matching history" description="Change the filter or complete a new study activity." />
      )}
    </div>
  );
}

export default History;
