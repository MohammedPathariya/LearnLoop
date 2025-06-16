// ========== src/App.js ==========
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import ThinkMate from './pages/ThinkMate';
import Conversations from './pages/Conversations';
import Analytics from './pages/Analytics';
import QuizPage from './pages/QuizPage';
import QuizDetail from './pages/QuizDetail';
import FlashcardPage from './pages/FlashcardPage';
import FlashcardHistory from './pages/FlashcardHistory';
import FlashcardDetail from './pages/FlashcardDetail';

function App() {
  return (
    <Router>
      <NavBar />
      <div className="content-area">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/thinkmate" element={<ThinkMate />} />
          <Route path="/quiz" element={<QuizPage />} />
          <Route path="/quiz/:quizId" element={<QuizDetail />} /> 
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/conversations/:id" element={<Conversations />} />
          <Route path="/flashcards" element={<FlashcardPage />} />
          <Route path="/flashcards_history" element={<FlashcardHistory />} />
          <Route path="/flashcards/:id" element={<FlashcardDetail />} />
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
