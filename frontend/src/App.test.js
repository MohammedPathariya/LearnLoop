import { render, screen } from '@testing-library/react';
import App from './App';
import { getProgress, getSessions } from './api/learnloopApi';

jest.mock('./api/learnloopApi', () => ({
  getSessions: jest.fn(),
  getProgress: jest.fn(),
  openDemo: jest.fn(),
  createSession: jest.fn(),
  updateSession: jest.fn(),
  deleteSession: jest.fn(),
  getHealth: jest.fn(),
}));

beforeEach(() => {
  getSessions.mockResolvedValue([{
    id: 'demo-session',
    title: 'Machine Learning Foundations',
    domain: 'Machine Learning',
    is_demo: true,
    material_count: 3,
    quiz_count: 3,
    flashcard_count: 1,
    updated_at: '2026-07-28T16:30:00',
  }]);
  getProgress.mockResolvedValue({
    average_score: 80,
    sessions: 1,
    materials: 3,
    quizzes: 3,
    flashcard_sets: 1,
    needs_review: [{ topic: 'Evaluation metrics', score: 60 }],
  });
});

test('renders the redesigned learnloop home', async () => {
  render(<App />);

  expect(await screen.findByText('Machine Learning Foundations')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'learnloop home' })).toHaveTextContent('learnloop');
  expect(screen.getAllByRole('link', { name: 'Learn' })).toHaveLength(2);
  expect(screen.getByRole('heading', { name: /Pick up where you left off/i })).toBeInTheDocument();
});
