// src/pages/Dashboard.js

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getStats as getChatStats,
  getHistory as getChatHistory,
} from '../api/thinkmateApi';
import {
  getQuizStats,
  getQuizHistory,
} from '../api/thinkmateApi';

import StatCard from '../components/StatCard';
import SessionList from '../components/SessionList';
import './Dashboard.css';

const Dashboard = () => {
  // ─── Chat (Conversation) state ───────────────────────────────────────────────────
  const [chatStats, setChatStats] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);

  // ─── Quiz state ────────────────────────────────────────────────────────────────────
  const [quizStats, setQuizStats] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);

  useEffect(() => {
    // Fetch conversation (chat) stats + history
    getChatStats()
      .then((res) => setChatStats(res.data))
      .catch((err) => console.error('Error fetching chat stats:', err));

    getChatHistory()
      .then((res) => setChatHistory(res.data))
      .catch((err) => console.error('Error fetching chat history:', err));

    // Fetch quiz stats + history
    getQuizStats()
      .then((res) => setQuizStats(res.data))
      .catch((err) => console.error('Error fetching quiz stats:', err));

    getQuizHistory()
      .then((res) => setQuizHistory(res.data))
      .catch((err) => console.error('Error fetching quiz history:', err));
  }, []);

  return (
    <div className="dashboard-container">
      <h1>Welcome back to LearnLoop!</h1>

      {/* ─── Conversation Statistics ─────────────────────────────────────────────── */}
      <section className="dashboard-section">
        <h2>Conversation Statistics</h2>

        {chatStats ? (
          <div className="cards-container">
            <StatCard
              icon="📘"
              title="Total Chat Sessions"
              value={chatStats.total_conversations}
              bgColor="#e0f7fa"
            />
            <StatCard
              icon="⏳"
              title="Total Turns"
              value={chatStats.total_turns}
              bgColor="#e8f5e9"
            />
            <StatCard
              icon="🧠"
              title="Unique Topics"
              value={chatStats.unique_topics}
              bgColor="#f3e5f5"
            />
            <StatCard
              icon="📅"
              title="Today's Chat Sessions"
              value={chatStats.today_sessions}
              bgColor="#fff3e0"
            />
          </div>
        ) : (
          <p>Loading conversation stats…</p>
        )}

        <h3>Recent Chat Sessions</h3>
        <SessionList sessions={chatHistory} />
      </section>

      {/* ─── Quiz Statistics ────────────────────────────────────────────────────────── */}
      <section className="dashboard-section">
        <h2>Quiz Statistics</h2>

        {quizStats ? (
          <div className="cards-container">
            <StatCard
              icon="✏️"
              title="Total Quizzes Taken"
              value={quizStats.total_quizzes}
              bgColor="#e3f2fd"
            />
            <StatCard
              icon="📊"
              title="Total Questions Generated"
              value={quizStats.total_questions}
              bgColor="#f1f8e9"
            />
            <StatCard
              icon="⭐"
              title="Average Score"
              value={quizStats.average_score}
              bgColor="#fce4ec"
            />
            <StatCard
              icon="🗓️"
              title="Quizzes Today"
              value={quizStats.quizzes_today}
              bgColor="#fff8e1"
            />
          </div>
        ) : (
          <p>Loading quiz stats…</p>
        )}

        <h3>Recent Quiz Sessions</h3>
        <ul className="history-list">
          {quizHistory.map((q) => (
            <li key={q.id} className="history-item">
              {/* Wrap the entire item in a Link to /quiz/:quizId */}
              <Link to={`/quiz/${q.id}`} className="history-link">
                <span role="img" aria-label="quiz">
                  📝
                </span>{' '}
                {q.topic ? (
                  <strong>Topic: {q.topic}</strong>
                ) : (
                  <strong>Content-Based Quiz</strong>
                )}
                <br />
                <small>
                  {q.timestamp} — Score: {q.score} / {q.num_questions}
                </small>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default Dashboard;
