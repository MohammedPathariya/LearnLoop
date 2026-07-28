import { BrowserRouter, Route, Routes } from 'react-router-dom';
import AppShell from './components/AppShell';
import Benchmarks from './pages/Benchmarks';
import Flashcards from './pages/Flashcards';
import History from './pages/History';
import Home from './pages/Home';
import Materials from './pages/Materials';
import Practice from './pages/Practice';
import Progress from './pages/Progress';
import QuizResult from './pages/QuizResult';
import Settings from './pages/Settings';
import Study from './pages/Study';
import './index.css';

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Home />} />
          <Route path="/learn" element={<Study />} />
          <Route path="/learn/:sessionId" element={<Study />} />
          <Route path="/study" element={<Study />} />
          <Route path="/study/:sessionId" element={<Study />} />
          <Route path="/materials" element={<Materials />} />
          <Route path="/practice" element={<Practice />} />
          <Route path="/practice/results/:quizId" element={<QuizResult />} />
          <Route path="/flashcards" element={<Flashcards />} />
          <Route path="/flashcards/:setId" element={<Flashcards />} />
          <Route path="/progress" element={<Progress />} />
          <Route path="/history" element={<History />} />
          <Route path="/benchmarks" element={<Benchmarks />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function NotFound() {
  return (
    <div className="page empty-state">
      <h1>Page not found</h1>
      <p>The study page you requested does not exist.</p>
      <a className="button primary" href="/">Return home</a>
    </div>
  );
}

export default App;
