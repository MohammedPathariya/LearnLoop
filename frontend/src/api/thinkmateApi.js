// --------- src/api/thinkmateApi.js ---------

import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5050';

// ─── Conversation Endpoints ────────────────────────────────────

// Fetch analytics stats
export const getStats = () => {
  return axios.get(`${BASE_URL}/analytics/stats`);
};

// Fetch recent chat history (up to 20 items)
export const getHistory = () => {
  return axios.get(`${BASE_URL}/history`);
};

// Fetch a single conversation by ID
export const getChatById = (id) => {
  return axios.get(`${BASE_URL}/conversations/${id}`);
};

// Search conversations by query string
export const searchChats = (q) => {
  return axios.get(`${BASE_URL}/search?query=${encodeURIComponent(q)}`);
};

// Start a new teacher-student conversation
// payload: { topic, turns, style, mode }
export const startConversation = (payload) => {
  return axios.post(`${BASE_URL}/chat`, payload);
};

export const generateQuiz = async (payload) => {
  const response = await axios.post(`${BASE_URL}/quiz`, payload);
  return response.data;
};


export const saveQuizSession = (payload) => {
    return axios.post(`${BASE_URL}/quiz_results`, payload);
};
  
export const getQuizHistory = () => {
    return axios.get(`${BASE_URL}/quiz_history`);
};

export const getQuizStats = () => {
    return axios.get(`${BASE_URL}/analytics/quiz_stats`);
};

export const getQuizById = (quizId) => {
    return axios.get(`${BASE_URL}/quiz_results/${quizId}`);
  };

export const generateFlashcards = async (topic, numCards = 5) => {
  const res = await axios.post(`${BASE_URL}/flashcards`, { topic, num_cards: numCards });
  return res.data;
};

export const getFlashcardStats = async () => {
  const res = await axios.get(`${BASE_URL}/analytics/flashcard_stats`);
  return res;
};

export const getFlashcardHistory = async () => {
  const res = await axios.get(`${BASE_URL}/flashcards_history`);
  return res.data;
};

export const getFlashcardSetById = async (id) => {
  const res = await axios.get(`${BASE_URL}/flashcards/${id}`);
  return res.data;
};
