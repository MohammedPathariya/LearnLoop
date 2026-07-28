import { render, screen } from '@testing-library/react';
import App from './App';
import axios from 'axios';

jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

beforeEach(() => {
  axios.get.mockImplementation((url) => {
    if (url.includes('/analytics/stats')) {
      return Promise.resolve({
        data: {
          total_conversations: 0,
          unique_topics: 0,
          today_sessions: 0,
        },
      });
    }

    if (url.includes('/analytics/quiz_stats')) {
      return Promise.resolve({
        data: {
          total_quizzes: 0,
          average_score: 0,
          quizzes_today: 0,
        },
      });
    }

    if (url.includes('/analytics/flashcard_stats')) {
      return Promise.resolve({
        data: {
          total_flashcard_sets: 0,
          total_flashcards_generated: 0,
          sets_created_today: 0,
        },
      });
    }

    return Promise.resolve({ data: [] });
  });
});

test('renders the LearnLoop dashboard shell', async () => {
  render(<App />);

  expect(screen.getByText('LearnLoop')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /Ready to Learn Something New Today/i })).toBeInTheDocument();
  expect(await screen.findByText('Total Chat Sessions')).toBeInTheDocument();
});
