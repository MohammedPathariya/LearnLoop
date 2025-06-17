// src/pages/QuizPage.js

import React, { useState } from 'react';
import { generateQuiz, saveQuizSession } from '../api/thinkmateApi';
import './QuizPage.css'; // ← Import the updated QuizPage.css

const QuizPage = () => {
  const [topic, setTopic] = useState('');
  const [content, setContent] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);

  const [quizResult, setQuizResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // For interactive mode:
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(0);

  // ─── Step 1: Generate a quiz from topic/content ─────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setQuizResult(null);
    setShowResults(false);
    setUserAnswers({});
    setScore(0);

    if (!topic.trim() && !content.trim()) {
      setError('Please provide either a topic or some content.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        num_questions: numQuestions,
        ...(topic.trim() ? { topic: topic.trim() } : {}),
        ...(content.trim() ? { content: content.trim() } : {}),
      };
      const data = await generateQuiz(payload);

      // DEBUG: inspect raw API response
      console.log('🔍 generateQuiz response:', data);

      if (data.error) {
        setError(data.error);
      } else if (Array.isArray(data.quiz)) {
        setQuizResult(data.quiz);

        // Initialize userAnswers so each question index has an empty string
        const initAnswers = {};
        data.quiz.forEach((_, idx) => {
          initAnswers[idx] = '';
        });
        setUserAnswers(initAnswers);
      } else {
        setError('Unexpected quiz format: ' + JSON.stringify(data));
      }
    } catch (err) {
      console.error(err);
      setError('Failed to generate quiz. Try again.');
    }
    setLoading(false);
  };

  // ─── Step 2: Track user selections or typed answers ─────────────────────────────────
  const handleAnswerChange = (qIndex, value) => {
    setUserAnswers((prev) => ({
      ...prev,
      [qIndex]: value,
    }));
  };

  // ─── Step 3: Check answers, compute score, and save to DB ─────────────────────────────
  const handleCheckAnswers = async () => {
    if (!quizResult) return;
    let correctCount = 0;

    // Build an array of correct answers for each question (just the string)
    const correctArr = quizResult.map((q) => {
      const ans = (q.correct_answer ?? q.answer ?? '').toString().trim();
      return ans;
    });

    quizResult.forEach((q, idx) => {
      const userAnsRaw = (userAnswers[idx] || '').toString().trim();
      const correctAnsRaw = (q.correct_answer ?? q.answer ?? '').toString().trim();

      if (q.type === 'Fill-in-the-blank') {
        // Case-insensitive substring match:
        const ua = userAnsRaw.toLowerCase();
        const ca = correctAnsRaw.toLowerCase();
        if (ua.includes(ca) || ca.includes(ua)) {
          correctCount++;
        }
      } else {
        // MCQ or True/False: must match exactly (e.g. "B" === "B")
        if (userAnsRaw === correctAnsRaw) {
          correctCount++;
        }
      }
    });

    setScore(correctCount);
    setShowResults(true);

    // ─── SAVE QUIZ to the backend ─────────────────────────────────────────────────────
    try {
      const payload = {
        topic: topic.trim() || null,
        content: content.trim() || null,
        num_questions: numQuestions,
        quiz: quizResult,            // entire quiz array
        user_answers: userAnswers,   // { "0": "B", "1": "True", ... }
        correct_answers: correctArr, // [ "B", "True", "tuning", ... ]
        score: correctCount,
      };

      const resp = await saveQuizSession(payload);
      console.log('Quiz session saved, ID:', resp.data.quiz_session_id);
    } catch (err) {
      console.error('Failed to save quiz session:', err);
      // We let the user still see their score even if saving fails.
    }
  };

  // ─── Step 4: Render each question with the appropriate form control ────────────────────
  const renderQuestion = (q, idx) => {
    const userAns = userAnswers[idx] || '';
    const correctAns = (q.correct_answer ?? q.answer ?? '').toString().trim();

    // Determine if correct/wrong (after showResults = true)
    const isCorrect = showResults && (() => {
      if (q.type === 'Fill-in-the-blank') {
        const ua = userAns.toLowerCase();
        const ca = correctAns.toLowerCase();
        return ua.includes(ca) || ca.includes(ua);
      } else {
        return userAns === correctAns;
      }
    })();

    const isWrong =
      showResults &&
      userAns.trim().length > 0 &&
      !(
        q.type === 'Fill-in-the-blank'
          ? userAns.toLowerCase().includes(correctAns.toLowerCase()) ||
            correctAns.toLowerCase().includes(userAns.toLowerCase())
          : userAns === correctAns
      );

    const questionText = q.question || '(No question text returned)';

    // CSS classes for correct vs. wrong
    const containerClass = showResults
      ? isCorrect
        ? 'question-container correct'
        : isWrong
        ? 'question-container wrong'
        : 'question-container'
      : 'question-container';

    return (
      <div key={idx} className={containerClass}>
        <div className="quiz-q">
          Q{idx + 1}. {questionText}
        </div>

        {/* ─── MCQ ────────────────────────────────────────────────────────────────────── */}
        {q.type === 'MCQ' && (
          <div className="quiz-options">
            {q.options.map((opt, i) => {
              // Extract letter A/B/C/D from the option string
              const letterMatch = opt.trim().match(/^([A-D])/i);
              const letter = letterMatch ? letterMatch[1].toUpperCase() : '';
              return (
                <label key={i} className="quiz-option-item">
                  <input
                    type="radio"
                    name={`q-${idx}`}
                    value={letter}               // e.g. "A" or "B"
                    checked={userAns === letter}
                    disabled={showResults}
                    onChange={(e) => handleAnswerChange(idx, e.target.value)}
                  />
                  <span className="option-text">{opt.trim()}</span>
                </label>
              );
            })}
          </div>
        )}

        {/* ─── True/False ──────────────────────────────────────────────────────────────── */}
        {q.type === 'True/False' && (
          <div className="quiz-options tf-options">
            {['True', 'False'].map((opt, i) => (
              <label key={i} className="quiz-option-item">
                <input
                  type="radio"
                  name={`q-${idx}`}
                  value={opt}                   // "True" or "False"
                  checked={userAns === opt}
                  disabled={showResults}
                  onChange={(e) => handleAnswerChange(idx, e.target.value)}
                />
                <span className="option-text">{opt}</span>
              </label>
            ))}
          </div>
        )}

        {/* ─── Fill-in-the-Blank ───────────────────────────────────────────────────────── */}
        {q.type === 'Fill-in-the-blank' && (
          <div className="quiz-options fib-options">
            <input
              type="text"
              placeholder="Your answer…"
              value={userAns}
              disabled={showResults}
              onChange={(e) => handleAnswerChange(idx, e.target.value)}
            />
          </div>
        )}

        {/* ─── Explanation (shown only after Check Answers) ────────────────────────────── */}
        {showResults && (
          <div className="quiz-explanation">
            {isCorrect ? (
              <span className="explanation-correct">
                ✔ Correct! {q.explanation}
              </span>
            ) : (
              <span className="explanation-wrong">
                ✖ Wrong. <strong>Correct:</strong> {correctAns}.<br />
                <em>{q.explanation}</em>
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="page-bg-wrapper">
      <div className="quiz-container">
        <h2>Practice Quizzes for Deeper Understanding</h2>
        <p className="subtitle">Generate topic-based quizzes and check your answers instantly.</p>


        <form className="quiz-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="topic-input">Topic (short string)</label>
            <input
              id="topic-input"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Photosynthesis"
            />
          </div>

          <div className="form-group">
            <label htmlFor="content-input">Or paste Content (long text)</label>
            <textarea
              id="content-input"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste an article or notes here…"
              rows={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="num-questions-input">Number of Questions</label>
            <input
              id="num-questions-input"
              type="number"
              min="1"
              max="20"
              value={numQuestions}
              onChange={(e) => setNumQuestions(e.target.value)}
            />
          </div>

          <button type="submit" className="generate-btn" disabled={loading}>
            {loading ? 'Generating Quiz…' : 'Generate Quiz'}
          </button>
        </form>

        {error && <div className="quiz-error">{error}</div>}

        {quizResult && (
          <div className="quiz-test-area">
            {quizResult.map((q, idx) => renderQuestion(q, idx))}

            {!showResults && (
              <button
                className="check-answers-btn"
                onClick={handleCheckAnswers}
                disabled={Object.values(userAnswers).some((ans) => ans === '')}
              >
                Check Answers
              </button>
            )}

            {showResults && (
              <div className="quiz-score">
                Your Score: {score} / {quizResult.length}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizPage;
