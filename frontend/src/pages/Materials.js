import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  addMaterial,
  deleteMaterial,
  getMaterial,
  getMaterials,
  getSessions,
  renameMaterial,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, Modal, PageHeader, SelectField, StatusNotice } from '../components/UI';

function Materials() {
  const [sessions, setSessions] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [materials, setMaterials] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selected, setSelected] = useState(null);
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  useEffect(() => {
    getSessions()
      .then((items) => {
        setSessions(items);
        if (items.length) setSessionId(items[0].id);
      })
      .catch(() => setError('Study journeys could not be loaded.'))
      .finally(() => setLoading(false));
  }, []);

  const loadMaterials = useCallback(async () => {
    try {
      setMaterials(await getMaterials(sessionId, query));
    } catch {
      setError('Materials could not be loaded.');
    }
  }, [sessionId, query]);

  useEffect(() => {
    if (sessionId) loadMaterials();
  }, [sessionId, loadMaterials]);

  async function handleAdd(event) {
    event.preventDefault();
    setError('');
    try {
      await addMaterial(sessionId, { title, content });
      setTitle('');
      setContent('');
      setShowAdd(false);
      await loadMaterials();
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'Material indexing failed.');
    }
  }

  async function handleOpen(id) {
    setSelected(await getMaterial(id));
  }

  async function handleRename(event) {
    event.preventDefault();
    await renameMaterial(renameTarget.id, renameValue);
    setRenameTarget(null);
    await loadMaterials();
  }

  async function handleDelete(material) {
    if (!window.confirm(`Remove "${material.title}" from this journey?`)) return;
    await deleteMaterial(material.id);
    await loadMaterials();
  }

  const activeSession = sessions.find((session) => session.id === sessionId);

  return (
    <div className="page">
      <PageHeader
        eyebrow="Materials"
        title="Your source library"
        description="Every answer, quiz, and flashcard can trace back to material you added."
        actions={<button className="button primary" type="button" onClick={() => setShowAdd(true)} disabled={!sessionId}>Add material</button>}
      />
      {error && <StatusNotice type="error">{error}</StatusNotice>}

      <div className="toolbar">
        <SelectField
          label="Study journey"
          value={sessionId}
          onChange={setSessionId}
          options={sessions.map((session) => ({ value: session.id, label: session.title }))}
          disabled={!sessions.length}
        />
        <label className="search-field">
          <span>Search materials</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by title" />
        </label>
        {query && <button className="button secondary" type="button" onClick={() => setQuery('')}>Clear</button>}
      </div>

      {loading ? <LoadingBlock /> : materials.length ? (
        <div className="material-grid">
          {materials.map((material) => (
            <article className="material-card" key={material.id}>
              <div className="card-topline">
                <span className={`badge ${material.status === 'indexed' ? 'brand' : 'warning'}`}>
                  {material.status === 'indexed' ? 'Indexed' : material.status}
                </span>
                <span>{new Date(material.created_at).toLocaleDateString()}</span>
              </div>
              <h2>{material.title}</h2>
              <p>{material.chunk_count} searchable chunks · {activeSession?.title}</p>
              <div className="card-actions">
                <button className="text-button" type="button" onClick={() => handleOpen(material.id)}>Open</button>
                <button className="text-button" type="button" onClick={() => { setRenameTarget(material); setRenameValue(material.title); }}>Rename</button>
                <button className="text-button destructive" type="button" onClick={() => handleDelete(material)}>Remove</button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          title={query ? 'No matching materials' : 'No material in this journey'}
          description={query ? 'Try another title or clear the search.' : 'Paste your notes or study text to make grounded learning possible.'}
          action={!query && sessionId ? <button className="button primary" type="button" onClick={() => setShowAdd(true)}>Add material</button> : null}
        />
      )}

      <div className="page-footer-action">
        {activeSession && <Link className="button secondary" to={`/study/${activeSession.id}`}>Open study workspace</Link>}
      </div>

      {showAdd && (
        <Modal title="Add study material" wide onClose={() => setShowAdd(false)}>
          <form className="form-stack" onSubmit={handleAdd}>
            <label>Material title<input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
            <label>Study text<textarea rows="12" value={content} onChange={(event) => setContent(event.target.value)} required /></label>
            <p className="field-note">Text paste is supported. File upload has not been implemented.</p>
            <div className="form-actions">
              <button className="button secondary" type="button" onClick={() => setShowAdd(false)}>Cancel</button>
              <button className="button primary" type="submit">Index material</button>
            </div>
          </form>
        </Modal>
      )}

      {selected && (
        <Modal title={selected.title} wide onClose={() => setSelected(null)}>
          <div className="material-content">{selected.content}</div>
        </Modal>
      )}

      {renameTarget && (
        <Modal title="Rename material" onClose={() => setRenameTarget(null)}>
          <form className="form-stack" onSubmit={handleRename}>
            <label>Title<input value={renameValue} onChange={(event) => setRenameValue(event.target.value)} required /></label>
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

export default Materials;
