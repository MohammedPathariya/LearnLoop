// src/pages/Dashboard.js

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getStats as getChatStats,
  getHistory as getChatHistory,
  getQuizStats,
  getQuizHistory,
  getFlashcardStats,
  getFlashcardHistory,
} from '../api/thinkmateApi';

import StatCard from '../components/StatCard';
import SessionList from '../components/SessionList';
import './Dashboard.css';

const Dashboard = () => {
  const [chatStats, setChatStats] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [quizStats, setQuizStats] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);
  const [flashStats, setFlashStats] = useState(null);
  const [flashHistory, setFlashHistory] = useState([]);

  useEffect(() => {
    getChatStats().then((res) => setChatStats(res.data)).catch(console.error);
    getChatHistory().then((res) => setChatHistory(res.data)).catch(console.error);
    getQuizStats().then((res) => setQuizStats(res.data)).catch(console.error);
    getQuizHistory().then((res) => setQuizHistory(res.data)).catch(console.error);
    getFlashcardStats().then((res) => setFlashStats(res.data)).catch(console.error);
    getFlashcardHistory().then((history) => setFlashHistory(history)).catch(console.error);
  }, []);

  return (
    <div className="dashboard-container">
      <h1>Welcome back to LearnLoop!</h1>

      {/* ─── Chat Section ───────────────────────────────────────────── */}
      <section className="dashboard-section">
        <h2>Conversation Statistics</h2>
        {chatStats ? (
          <div className="cards-container">
            <StatCard icon="📘" title="Total Chat Sessions" value={chatStats.total_conversations} bgColor="#e0f7fa" />
            <StatCard icon="⏳" title="Total Turns" value={chatStats.total_turns} bgColor="#e8f5e9" />
            <StatCard icon="🧠" title="Unique Topics" value={chatStats.unique_topics} bgColor="#f3e5f5" />
            <StatCard icon="📅" title="Today's Chat Sessions" value={chatStats.today_sessions} bgColor="#fff3e0" />
          </div>
        ) : (
          <p>Loading conversation stats…</p>
        )}
        <h3>Recent Chat Sessions</h3>
        <SessionList sessions={chatHistory} />
      </section>

      {/* ─── Quiz Section ───────────────────────────────────────────── */}
      <section className="dashboard-section">
        <h2>Quiz Statistics</h2>
        {quizStats ? (
          <div className="cards-container">
            <StatCard icon="✏️" title="Total Quizzes Taken" value={quizStats.total_quizzes} bgColor="#e3f2fd" />
            <StatCard icon="📊" title="Total Questions Generated" value={quizStats.total_questions} bgColor="#f1f8e9" />
            <StatCard icon="⭐" title="Average Score" value={quizStats.average_score} bgColor="#fce4ec" />
            <StatCard icon="🗓️" title="Quizzes Today" value={quizStats.quizzes_today} bgColor="#fff8e1" />
          </div>
        ) : (
          <p>Loading quiz stats…</p>
        )}
        <h3>Recent Quiz Sessions</h3>
        <ul className="history-list">
          {quizHistory.map((q) => (
            <li key={q.id} className="history-item">
              <Link to={`/quiz/${q.id}`} className="history-link">
                <span role="img" aria-label="quiz">📝</span>{' '}
                {q.topic ? <strong>Topic: {q.topic}</strong> : <strong>Content-Based Quiz</strong>}
                <br />
                <small>{q.timestamp} — Score: {q.score} / {q.num_questions}</small>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* ─── Flashcard Section ──────────────────────────────────────── */}
      <section className="dashboard-section">
        <h2>Flashcard Statistics</h2>
        {flashStats ? (
          <div className="cards-container">
            <StatCard icon="🃏" title="Total Flashcard Sets" value={flashStats.total_flashcard_sets} bgColor="#ede7f6" />
            <StatCard icon="📇" title="Total Cards Generated" value={flashStats.total_flashcards_generated} bgColor="#e8f5e9" />
            <StatCard icon="📆" title="Sets Created Today" value={flashStats.sets_created_today} bgColor="#fffde7" />
          </div>
        ) : (
          <p>Loading flashcard stats…</p>
        )}
        <h3>Recent Flashcard Sets</h3>
        {Array.isArray(flashHistory) && flashHistory.length > 0 ? (
          <ul className="history-list">
            {flashHistory.map((set) => (
              <li key={set.id} className="history-item">
                <Link to={`/flashcards/${set.id}`} className="history-link">
                  <span role="img" aria-label="flashcards">🗂️</span>{' '}
                  <strong>{set.topic || '(No topic)'}</strong>
                  <br />
                  <small>{set.timestamp} — {set.num_cards} cards</small>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ marginLeft: "1rem" }}>No flashcard sets found yet.</p>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
