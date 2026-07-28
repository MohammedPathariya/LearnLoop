import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getProgress } from '../api/learnloopApi';
import { EmptyState, LoadingBlock, MetricCard, PageHeader, ScoreBar, StatusNotice } from '../components/UI';

function Progress() {
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getProgress().then(setProgress).catch(() => setError('Progress could not be loaded.'));
  }, []);

  if (error) return <div className="page"><StatusNotice type="error">{error}</StatusNotice></div>;
  if (!progress) return <div className="page"><LoadingBlock label="Loading progress" /></div>;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Progress"
        title="See what is improving and what needs another pass."
        description="These results come from completed quiz attempts and saved study activity. No inferred mastery score is shown."
        actions={<Link className="button primary" to="/practice">Start practice</Link>}
      />
      <div className="metric-grid">
        <MetricCard label="Quiz average" value={`${progress.average_score}%`} detail={`${progress.quizzes} completed`} />
        <MetricCard label="Study journeys" value={progress.sessions} detail={`${progress.materials} indexed materials`} />
        <MetricCard label="Flashcard sets" value={progress.flashcard_sets} detail="Saved review sets" />
        <MetricCard label="Recorded attempts" value={progress.score_trend.length} detail="Real saved scores" />
      </div>

      <div className="progress-layout">
        <section className="card-panel trend-panel">
          <div className="section-heading">
            <div><p className="eyebrow">Quiz performance</p><h2>Score trend</h2></div>
          </div>
          {progress.score_trend.length ? (
            <TrendChart points={progress.score_trend} />
          ) : (
            <EmptyState title="No score trend yet" description="Complete a quiz to establish your first data point." />
          )}
        </section>
        <section className="topic-columns">
          <div className="card-panel">
            <p className="eyebrow success-text">Strong topics</p>
            <h2>Keep building</h2>
            {progress.strong_topics.length ? progress.strong_topics.map((topic) => (
              <div className="topic-row" key={topic.topic}>
                <div><strong>{topic.topic}</strong><ScoreBar value={topic.score} tone="success" /></div>
                <span className="score success-text">{topic.score}%</span>
              </div>
            )) : <p className="muted-copy">No topic is above the 75% threshold yet.</p>}
          </div>
          <div className="card-panel">
            <p className="eyebrow error-text">Needs review</p>
            <h2>Focus next</h2>
            {progress.needs_review.length ? progress.needs_review.map((topic) => (
              <div className="topic-row" key={topic.topic}>
                <div><strong>{topic.topic}</strong><ScoreBar value={topic.score} tone="error" /></div>
                <span className="score error-text">{topic.score}%</span>
              </div>
            )) : <p className="muted-copy">No saved topic currently falls below 75%.</p>}
            <Link className="button primary full" to="/practice">Review a weak topic</Link>
          </div>
        </section>
      </div>
    </div>
  );
}

function TrendChart({ points }) {
  const width = 640;
  const height = 230;
  const padding = 28;
  const step = points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0;
  const coordinates = points.map((point, index) => ({
    ...point,
    x: padding + index * step,
    y: height - padding - (point.percentage / 100) * (height - padding * 2),
  }));
  const polyline = coordinates.map((point) => `${point.x},${point.y}`).join(' ');

  return (
    <div className="trend-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Quiz score trend">
        {[25, 50, 75, 100].map((value) => {
          const y = height - padding - (value / 100) * (height - padding * 2);
          return <line key={value} x1={padding} x2={width - padding} y1={y} y2={y} className="chart-grid-line" />;
        })}
        <polyline points={polyline} className="chart-line" />
        {coordinates.map((point) => <circle key={point.id} cx={point.x} cy={point.y} r="6" className="chart-point" />)}
      </svg>
      <div className="trend-labels">
        {points.map((point) => <span key={point.id}><strong>{point.percentage}%</strong>{point.topic}</span>)}
      </div>
    </div>
  );
}

export default Progress;
