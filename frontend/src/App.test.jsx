import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import App from './App';

const api = vi.hoisted(() => ({
  addMaterial: vi.fn(),
  askQuestion: vi.fn(),
  createSession: vi.fn(),
  deleteFlashcardSet: vi.fn(),
  deleteMaterial: vi.fn(),
  deleteQuiz: vi.fn(),
  deleteSession: vi.fn(),
  generateFlashcards: vi.fn(),
  generateQuiz: vi.fn(),
  getFlashcardSet: vi.fn(),
  getFlashcardSets: vi.fn(),
  getHealth: vi.fn(),
  getHistory: vi.fn(),
  getMaterial: vi.fn(),
  getMaterials: vi.fn(),
  getMessages: vi.fn(),
  getProgress: vi.fn(),
  getQuiz: vi.fn(),
  getSession: vi.fn(),
  getSessions: vi.fn(),
  openDemo: vi.fn(),
  renameMaterial: vi.fn(),
  resetDemo: vi.fn(),
  saveQuiz: vi.fn(),
  updateSession: vi.fn(),
}));

vi.mock('./api/learnloopApi', () => api);

const demoSession = {
  id: 'demo-session',
  title: 'Machine Learning Foundations',
  domain: 'Machine Learning',
  is_demo: true,
  material_count: 3,
  message_count: 2,
  quiz_count: 3,
  flashcard_count: 1,
  updated_at: '2026-07-28T16:30:00',
  materials: [{
    id: 'source-1',
    title: 'Generalization notes',
    status: 'indexed',
    chunk_count: 1,
  }],
};

const progress = {
  average_score: 80,
  sessions: 1,
  materials: 3,
  quizzes: 3,
  flashcard_sets: 1,
  score_trend: [],
  strong_topics: [],
  needs_review: [{ topic: 'Evaluation metrics', score: 60 }],
};

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  window.history.replaceState({}, '', '/');
  api.openDemo.mockResolvedValue(demoSession);
  api.getSessions.mockResolvedValue([demoSession]);
  api.getSession.mockResolvedValue(demoSession);
  api.getMessages.mockResolvedValue([]);
  api.getProgress.mockResolvedValue(progress);
  api.getHistory.mockResolvedValue([]);
  api.getFlashcardSets.mockResolvedValue([]);
  api.getHealth.mockResolvedValue({ status: 200 });
  api.generateQuiz.mockResolvedValue({
    quiz: [{
      type: 'MCQ',
      question: 'What does generalization measure?',
      options: ['A. Training speed', 'B. Performance on unseen data'],
      correct_answer: 'B',
      explanation: 'Generalization concerns unseen data.',
    }],
  });
});

afterEach(() => {
  cleanup();
});

describe('LearnLoop frontend workflows', () => {
  test('renders the simplified home and utility navigation', async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByText('Machine Learning Foundations')).toBeInTheDocument();
    expect(await screen.findByText('Backend online')).toBeInTheDocument();
    expect(screen.getByText('Free backend may take up to 60 seconds to wake')).toBeInTheDocument();
    expect(within(screen.getByRole('navigation', { name: 'Primary navigation' })).getByRole('link', { name: 'Learn' })).toBeInTheDocument();
    const mobileNavigation = document.querySelector('.mobile-bottom-nav');
    expect(mobileNavigation).toBeInTheDocument();
    expect(within(mobileNavigation).getByText('Learn')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Pick up where you left off/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Open more navigation' }));
    expect(screen.getByRole('link', { name: 'History' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Benchmarks' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'System' })).toBeInTheDocument();
  });

  test('shows when the backend is offline', async () => {
    api.getHealth.mockRejectedValueOnce(new Error('Backend unavailable'));

    render(<App />);

    expect(await screen.findByText('Backend offline')).toBeInTheDocument();
  });

  test('shows an amber waking state while the backend health check is pending', async () => {
    api.getHealth.mockReturnValueOnce(new Promise(() => {}));

    render(<App />);

    expect(screen.getByText('Backend waking')).toBeInTheDocument();
    expect(screen.getByText('Backend waking').closest('.backend-status-strip')).toHaveClass('waking');
    await screen.findByText('Machine Learning Foundations');
  });

  test('keeps optional labels on one line in the new learning-space flow', async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText('Machine Learning Foundations');
    await user.click(screen.getByRole('button', { name: 'Start something new' }));

    expect(screen.getByLabelText('Subject (optional)')).toBeInTheDocument();
    expect(screen.getByLabelText('Source title (optional)')).toBeInTheDocument();
    expect(screen.getByLabelText('Paste study material (optional)')).toBeInTheDocument();
  });

  test('opens a learning space and switches to its embedded quiz without crashing', async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, '', '/learn/demo-session');
    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Learn from your sources' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Quiz' }));

    expect(await screen.findByRole('heading', { name: 'Test this learning space' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate quiz' })).toBeInTheDocument();
  });

  test('renders quiz questions inside their cards without redundant option letters', async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, '', '/learn/demo-session?mode=quiz');
    render(<App />);

    await user.click(await screen.findByRole('button', { name: 'Generate quiz' }));
    const question = await screen.findByRole('heading', { name: 'What does generalization measure?' });
    const card = question.closest('.question-card');

    expect(card).not.toBeNull();
    expect(within(card).getByText('Training speed')).toBeInTheDocument();
    expect(within(card).getByText('Performance on unseen data')).toBeInTheDocument();
    expect(within(card).queryByText(/^A\./)).not.toBeInTheDocument();
    expect(within(card).queryByText(/^B\./)).not.toBeInTheDocument();
  });
});
