import { BrowserRouter, Route, Routes } from './router';
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
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/"><Home /></Route>
          <Route path="/learn"><Study /></Route>
          <Route path="/learn/:sessionId"><Study /></Route>
          <Route path="/study"><Study /></Route>
          <Route path="/study/:sessionId"><Study /></Route>
          <Route path="/materials"><Materials /></Route>
          <Route path="/practice"><Practice /></Route>
          <Route path="/practice/results/:quizId"><QuizResult /></Route>
          <Route path="/flashcards"><Flashcards /></Route>
          <Route path="/flashcards/:setId"><Flashcards /></Route>
          <Route path="/progress"><Progress /></Route>
          <Route path="/history"><History /></Route>
          <Route path="/benchmarks"><Benchmarks /></Route>
          <Route path="/settings"><Settings /></Route>
          <Route><NotFound /></Route>
        </Routes>
      </AppShell>
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
