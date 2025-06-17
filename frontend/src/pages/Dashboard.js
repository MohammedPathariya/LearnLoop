// ========== src/pages/Dashboard.js ==========
import React, { useEffect, useState } from 'react';

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

  const [chatView, setChatView] = useState("recent");
  const [quizView, setQuizView] = useState("recent");
  const [flashView, setFlashView] = useState("recent");

  useEffect(() => {
    getChatStats().then((res) => setChatStats(res.data)).catch(console.error);
    getChatHistory().then((res) => setChatHistory(res.data)).catch(console.error);
    getQuizStats().then((res) => setQuizStats(res.data)).catch(console.error);
    getQuizHistory().then((res) => setQuizHistory(res.data)).catch(console.error);
    getFlashcardStats().then((res) => setFlashStats(res.data)).catch(console.error);
    getFlashcardHistory().then((history) => setFlashHistory(history)).catch(console.error);
  }, []);

  const renderTabs = (view, setView) => (
    <div className="tab-buttons">
      <button className={view === "recent" ? "active" : ""} onClick={() => setView("recent")}>
        Recent
      </button>
      <button className={view === "all" ? "active" : ""} onClick={() => setView("all")}>
        All
      </button>
    </div>
  );

  return (
    <div className="dashboard-bg-wrapper">
      <div className="dashboard-container">
        <h1>Ready to Learn Something New Today?</h1>

        {/* ─── Chat Section ───────────────────────────────────────────── */}
        <section className="dashboard-section">
          <h2>Chat Statistics</h2>
          {chatStats ? (
            <div className="cards-container">
              <StatCard icon="📘" title="Total Chat Sessions" value={chatStats.total_conversations} bgColor="#e0f7fa" />
              <StatCard icon="🧠" title="Unique Topics" value={chatStats.unique_topics} bgColor="#f3e5f5" />
              <StatCard icon="📆" title="Today's Chat Sessions" value={chatStats.today_sessions} bgColor="#fff3e0" />
            </div>
          ) : (
            <p>Loading conversation stats…</p>
          )}
          <div className="section-header">
            <h3>Chats</h3>
            {renderTabs(chatView, setChatView)}
          </div>
          <SessionList
            sessions={chatView === "recent" ? chatHistory.slice(0, 3) : chatHistory}
            emoji="👩‍🎓"
            basePath="/conversations"
          />
        </section>

        {/* ─── Quiz Section ───────────────────────────────────────────── */}
        <section className="dashboard-section">
          <h2>Quiz Statistics</h2>
          {quizStats ? (
            <div className="cards-container">
              <StatCard icon="✏️" title="Total Quizzes Taken" value={quizStats.total_quizzes} bgColor="#e3f2fd" />
              <StatCard icon="⭐" title="Average Score" value={quizStats.average_score} bgColor="#fce4ec" />
              <StatCard icon="📆" title="Quizzes Today" value={quizStats.quizzes_today} bgColor="#fff8e1" />
            </div>
          ) : (
            <p>Loading quiz stats…</p>
          )}
          <div className="section-header">
            <h3>Quizzes</h3>
            {renderTabs(quizView, setQuizView)}
          </div>
          <SessionList
            sessions={quizView === "recent" ? quizHistory.slice(0, 3) : quizHistory}
            emoji="📝"
            basePath="/quiz"
          />
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
          <div className="section-header">
            <h3>Flashcards</h3>
            {renderTabs(flashView, setFlashView)}
          </div>
          <SessionList
            sessions={flashView === "recent" ? flashHistory.slice(0, 3) : flashHistory}
            emoji="🗂️"
            basePath="/flashcards"
          />
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
