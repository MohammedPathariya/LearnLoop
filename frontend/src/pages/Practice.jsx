import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from '../router';
import {
  generateQuiz,
  getHistory,
  getProgress,
  getSessions,
  saveQuiz,
} from '../api/learnloopApi';
import { EmptyState, LoadingBlock, MetricCard, PageHeader, SelectField, StatusNotice } from '../components/UI';

function Practice({ embedded = false, sessionIdOverride = '' }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [sessions, setSessions] = useState([]);
  const [history, setHistory] = useState([]);
  const [progress, setProgress] = useState(null);
  const [sourceMode, setSourceMode] = useState(embedded || searchParams.get('session') ? 'session' : 'topic');
  const [sessionId, setSessionId] = useState(sessionIdOverride || searchParams.get('session') || '');
  const [topic, setTopic] = useState('');
  const [content, setContent] = useState('');
  const [count, setCount] = useState(5);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getSessions(), getHistory(), getProgress()])
      .then(([sessionData, historyData, progressData]) => {
        setSessions(sessionData);
        setHistory(historyData.filter((item) => item.type === 'quiz'));
        setProgress(progressData);
        if (sessionData.length) setSessionId((current) => sessionIdOverride || current || sessionData[0].id);
      })
      .catch(() => setError('Practice data could not be loaded.'))
      .finally(() => setLoading(false));
  }, [sessionIdOverride]);

  async function handleGenerate(event) {
    event.preventDefault();
    setError('');
    setGenerating(true);
    try {
      const payload = { num_questions: Number(count) };
      if (sourceMode === 'session') payload.session_id = sessionId;
      if (sourceMode === 'topic') payload.topic = topic;
      if (sourceMode === 'content') payload.content = content;
      const result = await generateQuiz(payload);
      setQuiz(result.quiz);
      setAnswers({});
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'Quiz generation failed. Try again.');
    } finally {
      setGenerating(false);
    }
  }

  async function handleFinish() {
    const correctAnswers = quiz.map((question) => String(question.correct_answer || question.answer || '').trim());
    const score = quiz.reduce((total, question, index) => (
      isCorrect(question, answers[index]) ? total + 1 : total
    ), 0);
    try {
      const activeSession = sessions.find((session) => session.id === sessionId);
      const result = await saveQuiz({
        session_id: sourceMode === 'session' ? sessionId : '',
        topic: sourceMode === 'topic' ? topic : activeSession?.title || null,
        content: sourceMode === 'content' ? content : null,
        num_questions: quiz.length,
        quiz,
        user_answers: answers,
        correct_answers: correctAnswers,
        score,
      });
      navigate(`/practice/results/${result.quiz_session_id}`);
    } catch (requestError) {
      setError(requestError.response?.data?.error || 'Your score could not be saved.');
    }
  }

  if (loading) return <div className={embedded ? '' : 'page'}><LoadingBlock label="Loading practice" /></div>;

  if (quiz) {
    const answeredCount = Object.values(answers).filter((answer) => String(answer).trim()).length;
    return (
      <div className={embedded ? 'quiz-active-page embedded-tool' : 'page quiz-active-page'}>
        <div className="quiz-active-header">
          <div>
            <p className="eyebrow">Active quiz</p>
            <h1>{sessions.find((session) => session.id === sessionId)?.title || topic || 'Custom study quiz'}</h1>
          </div>
          <span>{answeredCount} of {quiz.length} answered</span>
        </div>
        <div className="quiz-progress"><span style={{ width: `${(answeredCount / quiz.length) * 100}%` }} /></div>
        {error && <StatusNotice type="error">{error}</StatusNotice>}
        <div className="question-stack">
          {quiz.map((question, index) => (
            <Question
              key={`${question.question}-${index}`}
              question={question}
              index={index}
              value={answers[index] || ''}
              onChange={(value) => setAnswers((current) => ({ ...current, [index]: value }))}
            />
          ))}
        </div>
        <div className="sticky-actions">
          <button className="button secondary" type="button" onClick={() => setQuiz(null)}>Exit quiz</button>
          <button className="button primary" type="button" onClick={handleFinish} disabled={answeredCount === 0}>Finish and score</button>
        </div>
      </div>
    );
  }

  return (
    <div className={embedded ? 'embedded-tool' : 'page'}>
      {!embedded && (
        <PageHeader
          eyebrow="Practice"
          title="Turn your material into a focused check."
          description="Generate a validated mixed-format quiz from a learning space, a topic, or pasted text."
        />
      )}
      {error && <StatusNotice type="error">{error}</StatusNotice>}
      <div className={embedded ? 'practice-layout embedded' : 'practice-layout'}>
        <section className="quiz-builder card-panel">
          <div className="section-heading"><div><p className="eyebrow">Quiz</p><h2>{embedded ? 'Test this learning space' : 'Choose what to test'}</h2></div></div>
          <form className="form-stack" onSubmit={handleGenerate}>
            {!embedded && (
              <div className="segmented-control" aria-label="Quiz source">
                {[
                  ['session', 'Learning space'],
                  ['topic', 'Topic'],
                  ['content', 'Paste text'],
                ].map(([value, label]) => (
                  <button className={sourceMode === value ? 'active' : ''} type="button" key={value} onClick={() => setSourceMode(value)}>
                    {label}
                  </button>
                ))}
              </div>
            )}
            {!embedded && sourceMode === 'session' && (
              <SelectField
                label="Learning space"
                value={sessionId}
                onChange={setSessionId}
                options={sessions.map((session) => ({ value: session.id, label: session.title }))}
                disabled={!sessions.length}
              />
            )}
            {sourceMode === 'topic' && <label>Topic<input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="e.g. Classification metrics" required /></label>}
            {sourceMode === 'content' && <label>Study text<textarea rows="7" value={content} onChange={(event) => setContent(event.target.value)} required /></label>}
            <label>Number of questions<input type="number" min="1" max="20" value={count} onChange={(event) => setCount(event.target.value)} /></label>
            <button className="button primary full" type="submit" disabled={generating}>
              {generating ? 'Generating validated quiz...' : 'Generate quiz'}
            </button>
          </form>
        </section>
        {!embedded && <aside className="practice-summary">
          <div className="metric-grid compact">
            <MetricCard label="Quiz average" value={`${progress?.average_score || 0}%`} />
            <MetricCard label="Completed" value={progress?.quizzes || 0} />
          </div>
          <section className="card-panel">
            <div className="section-heading compact"><h2>Recent attempts</h2><Link className="text-link" to="/history">All history</Link></div>
            {history.length ? history.slice(0, 4).map((item) => (
              <Link className="history-mini-row" key={`${item.type}-${item.id}`} to={item.href}>
                <div><strong>{item.title}</strong><small>{new Date(item.timestamp).toLocaleDateString()}</small></div>
                <span>{item.metadata}</span>
              </Link>
            )) : <EmptyState title="No attempts yet" description="Your completed quizzes will appear here." />}
          </section>
        </aside>}
      </div>
    </div>
  );
}

function Question({ question, index, value, onChange }) {
  const type = question.type;
  const options = type === 'True/False' ? ['True', 'False'] : question.options || [];
  return (
    <article className="question-card">
      <div className="question-heading">
        <span>Question {index + 1}</span>
        <h2>{question.question}</h2>
      </div>
      {(type === 'MCQ' || type === 'True/False') ? (
        <div className="answer-options">
          {options.map((option, optionIndex) => {
            const answerValue = type === 'MCQ'
              ? (String(option).match(/^([A-D])/i)?.[1] || String.fromCharCode(65 + optionIndex)).toUpperCase()
              : option;
            return (
              <label className={value === answerValue ? 'selected' : ''} key={option}>
                <input type="radio" name={`question-${index}`} value={answerValue} checked={value === answerValue} onChange={() => onChange(answerValue)} />
                <span>{type === 'MCQ' ? String(option).replace(/^\s*[A-D][.)]\s*/i, '') : option}</span>
              </label>
            );
          })}
        </div>
      ) : (
        <label className="fill-answer">Your answer<input value={value} onChange={(event) => onChange(event.target.value)} /></label>
      )}
    </article>
  );
}

function isCorrect(question, answer = '') {
  const expected = String(question.correct_answer || question.answer || '').trim().toLowerCase();
  const actual = String(answer).trim().toLowerCase();
  if (question.type === 'Fill-in-the-blank') {
    return Boolean(actual) && (actual.includes(expected) || expected.includes(actual));
  }
  return actual === expected;
}

export default Practice;
