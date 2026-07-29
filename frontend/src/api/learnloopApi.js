import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5050';
const VISITOR_KEY = 'learnloop-visitor-id';

function getVisitorId() {
  let visitorId = window.localStorage.getItem(VISITOR_KEY);
  if (!visitorId) {
    visitorId = window.crypto?.randomUUID?.()
      || `visitor-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    window.localStorage.setItem(VISITOR_KEY, visitorId);
  }
  return visitorId;
}

const api = axios.create({ baseURL: BASE_URL });
api.interceptors.request.use((config) => {
  config.headers['X-LearnLoop-Visitor'] = getVisitorId();
  return config;
});

const data = (request) => request.then((response) => response.data);

export const getHealth = () => api.get('/healthz', { timeout: 65000 });
export const getSessions = () => data(api.get('/study/sessions'));
export const getSession = (id) => data(api.get(`/study/sessions/${id}`));
export const createSession = (payload) => data(api.post('/study/sessions', payload));
export const updateSession = (id, payload) => data(api.patch(`/study/sessions/${id}`, payload));
export const deleteSession = (id) => data(api.delete(`/study/sessions/${id}`));
export const openDemo = () => data(api.post('/study/demo'));
export const resetDemo = () => data(api.post('/study/demo/reset'));

export const getMaterials = (sessionId, query = '') => data(
  api.get(`/study/sessions/${sessionId}/materials`, { params: { query } }),
);
export const getMaterial = (id) => data(api.get(`/study/materials/${id}`));
export const addMaterial = (sessionId, payload) => data(
  api.post(`/study/sessions/${sessionId}/materials`, payload),
);
export const addPdfMaterial = (sessionId, file, title = '') => {
  const form = new FormData();
  form.append('file', file);
  if (title.trim()) form.append('title', title.trim());
  return data(api.post(`/study/sessions/${sessionId}/materials`, form));
};
export const renameMaterial = (id, title) => data(
  api.patch(`/study/materials/${id}`, { title }),
);
export const deleteMaterial = (id) => data(api.delete(`/study/materials/${id}`));

export const getMessages = (sessionId) => data(
  api.get(`/study/sessions/${sessionId}/messages`),
);
export const askQuestion = (sessionId, question) => data(
  api.post(`/study/sessions/${sessionId}/ask`, { question }),
);

export const generateQuiz = (payload) => data(api.post('/quiz', payload));
export const saveQuiz = (payload) => data(api.post('/quiz_results', payload));
export const getQuiz = (id) => data(api.get(`/quiz_results/${id}`));
export const deleteQuiz = (id) => data(api.delete(`/quiz_results/${id}`));

export const generateFlashcards = (payload) => data(api.post('/flashcards', payload));
export const getFlashcardSets = () => data(api.get('/study/flashcards'));
export const getFlashcardSet = (id) => data(api.get(`/flashcards/${id}`));
export const deleteFlashcardSet = (id) => data(api.delete(`/flashcards/${id}`));

export const getProgress = () => data(api.get('/study/progress'));
export const getHistory = () => data(api.get('/study/history'));
