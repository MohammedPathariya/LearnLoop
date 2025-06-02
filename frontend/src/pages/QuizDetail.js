// src/pages/QuizDetail.js

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getQuizById } from '../api/thinkmateApi';
import './QuizDetail.css'; // create this file for styling if you like

const QuizDetail = () => {
  const { quizId } = useParams(); // /quiz/:quizId
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const res = await getQuizById(quizId);
        setQuizData(res.data);
      } catch (err) {
        console.error('Error fetching quiz details:', err);
        setError('Failed to load quiz details.');
      }
      setLoading(false);
    };
    fetchQuiz();
  }, [quizId]);

  if (loading) {
    return (
      <div className="quiz-detail-container">
        <p>Loading quiz details…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="quiz-detail-container">
        <p className="error">{error}</p>
      </div>
    );
  }
  if (!quizData) {
    return null; // or “No data”
  }

  const {
    timestamp,
    topic,
    num_questions,
    quiz: questions,
    user_answers,
    correct_answers,
    score,
  } = quizData;

  return (
    <div className="quiz-detail-container">
      <h2>Quiz Details (ID: {quizId})</h2>
      <div className="quiz-meta">
        {topic ? (
          <p>
            <strong>Topic:</strong> {topic}
          </p>
        ) : (
          <p>
            <strong>Content‐Based Quiz</strong>
          </p>
        )}
        <p>
          <strong>Generated on:</strong> {timestamp}
        </p>
        <p>
          <strong>Number of Questions:</strong> {num_questions}
        </p>
        <p>
          <strong>Your Score:</strong> {score} / {num_questions}
        </p>
      </div>

      <hr />

      {/* Loop over each question */}
      {questions.map((q, idx) => {
        const userAns = (user_answers[idx] || '').toString().trim();
        const correctAns = (correct_answers[idx] || '').toString().trim();
        const questionText = q.question || '(No question text)';

        // Detect correctness
        let isCorrect = false;
        if (q.type === 'Fill-in-the-blank') {
          const ua = userAns.toLowerCase();
          const ca = correctAns.toLowerCase();
          if (ua.includes(ca) || ca.includes(ua)) {
            isCorrect = true;
          }
        } else {
          if (userAns === correctAns) {
            isCorrect = true;
          }
        }

        return (
          <div
            key={idx}
            className={`quiz-detail-question ${
              isCorrect ? 'correct' : 'wrong'
            }`}
          >
            <h3>
              Q{idx + 1}. {questionText}
            </h3>

            {/* Display MCQ options and highlight the user's choice */}
            {q.type === 'MCQ' && (
              <ul className="options-list">
                {q.options.map((opt, i) => {
                  // Extract letter A–D from opt
                  const letterMatch = opt.trim().match(/^([A-D])/i);
                  const letter = letterMatch
                    ? letterMatch[1].toUpperCase()
                    : '';
                  // Mark which option the user picked
                  const userPicked = userAns === letter;
                  // Mark which option is correct
                  const isThisCorrect = correctAns === letter;

                  return (
                    <li
                      key={i}
                      className={`option-item ${
                        userPicked ? 'user-picked' : ''
                      } ${isThisCorrect ? 'correct-answer' : ''}`}
                    >
                      {opt.trim()}
                    </li>
                  );
                })}
              </ul>
            )}

            {/* Display True/False user choice */}
            {q.type === 'True/False' && (
              <ul className="options-list">
                {['True', 'False'].map((opt, i) => {
                  const userPicked = userAns === opt;
                  const isThisCorrect = correctAns === opt;
                  return (
                    <li
                      key={i}
                      className={`option-item ${
                        userPicked ? 'user-picked' : ''
                      } ${isThisCorrect ? 'correct-answer' : ''}`}
                    >
                      {opt}
                    </li>
                  );
                })}
              </ul>
            )}

            {/* Display fill-in-the-blank typed answer */}
            {q.type === 'Fill-in-the-blank' && (
              <div className="fib-answer">
                <p>
                  <strong>Your answer:</strong>{' '}
                  <span className={isCorrect ? 'correct' : 'wrong'}>
                    {userAns || <em>(no answer given)</em>}
                  </span>
                </p>
                {!isCorrect && (
                  <p>
                    <strong>Correct answer:</strong> {correctAns}
                  </p>
                )}
              </div>
            )}

            {/* Show the explanation */}
            <div className="explanation-block">
              <strong>Explanation:</strong> {q.explanation}
            </div>
          </div>
        );
      })}

    </div>
  );
};

export default QuizDetail;
