import { useEffect, useState } from 'react';
import { Link, useParams } from '../router';
import { getQuiz } from '../api/learnloopApi';
import { LoadingBlock, PageHeader, StatusNotice } from '../components/UI';

function QuizResult() {
  const { quizId } = useParams();
  const [quiz, setQuiz] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getQuiz(quizId).then(setQuiz).catch(() => setError('This quiz result could not be loaded.'));
  }, [quizId]);

  if (error) return <div className="page"><StatusNotice type="error">{error}</StatusNotice></div>;
  if (!quiz) return <div className="page"><LoadingBlock label="Loading quiz result" /></div>;

  const percentage = Math.round((quiz.score / quiz.num_questions) * 100);

  return (
    <div className="page">
      <PageHeader
        eyebrow="Quiz complete"
        title={`${quiz.score} out of ${quiz.num_questions}`}
        description={`${percentage}% · ${quiz.topic || 'Study material quiz'} · ${new Date(quiz.timestamp).toLocaleDateString()}`}
        actions={(
          <>
            <Link className="button primary" to="/flashcards">Generate flashcards</Link>
            <Link className="button secondary" to="/practice">Retry with a new quiz</Link>
          </>
        )}
      />
      <div className="result-summary-line">
        <span className="result-score">{percentage}%</span>
        <div>
          <strong>{percentage >= 75 ? 'Strong result' : 'Review recommended'}</strong>
          <p>Review each explanation below, then turn the weak concepts into another practice round.</p>
        </div>
      </div>
      <section className="result-list">
        {quiz.quiz.map((question, index) => {
          const actual = String(quiz.user_answers[index] || '').trim();
          const expected = String(quiz.correct_answers[index] || '').trim();
          const correct = isAnswerCorrect(question.type, actual, expected);
          return (
            <article className={`result-row ${correct ? 'correct' : 'incorrect'}`} key={`${question.question}-${index}`}>
              <div className="result-index">{correct ? 'Correct' : 'Review'}</div>
              <div>
                <h2>{index + 1}. {question.question}</h2>
                <p><strong>Your answer:</strong> {actual || 'No answer'}</p>
                {!correct && <p><strong>Correct answer:</strong> {expected}</p>}
                <div className="explanation"><strong>Why:</strong> {question.explanation}</div>
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}

function isAnswerCorrect(type, actual, expected) {
  if (type === 'Fill-in-the-blank') {
    const left = actual.toLowerCase();
    const right = expected.toLowerCase();
    return Boolean(left) && (left.includes(right) || right.includes(left));
  }
  return actual.toLowerCase() === expected.toLowerCase();
}

export default QuizResult;
