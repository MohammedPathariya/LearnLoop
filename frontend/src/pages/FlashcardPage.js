// src/pages/FlashcardPage.js

import React, { useState } from 'react';
import { generateFlashcards } from '../api/thinkmateApi';
import './QuizPage.css';
import './Flashcard.css';

const FlashcardPage = () => {
  const [topic, setTopic] = useState('');
  const [numCards, setNumCards] = useState(5);
  const [flashcards, setFlashcards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setError(null);
    if (!topic.trim()) {
      setError('Please enter a topic to generate flashcards.');
      return;
    }
    setLoading(true);
    setFlashcards([]);

    try {
      const data = await generateFlashcards(topic, numCards);
      setFlashcards(data.flashcards || []);
    } catch (err) {
      console.error('Error generating flashcards:', err);
      setError('Failed to generate flashcards.');
    }

    setLoading(false);
  };

  return (
    <div className="page-bg-wrapper">
      <div className="quiz-container">
        <h2>Dynamic Flashcard Builder</h2>
        <p className="subtitle">Create topic-driven flashcards for efficient review. Tap to flip.</p>

        <form className="quiz-form" onSubmit={handleGenerate}>
          <div className="form-group">
            <label htmlFor="topic-input">Topic</label>
            <input
              id="topic-input"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Photosynthesis"
            />
          </div>

          <div className="form-group">
            <label htmlFor="num-cards-input">Number of Flashcards</label>
            <input
              id="num-cards-input"
              type="number"
              min="1"
              max="10"
              value={numCards}
              onChange={(e) => setNumCards(e.target.value)}
            />
          </div>

          <button type="submit" className="generate-btn" disabled={loading}>
            {loading ? 'Generating Flashcards…' : 'Generate Flashcards'}
          </button>
        </form>

        {error && <div className="quiz-error">{error}</div>}

        {flashcards.length > 0 && (
          <div className="quiz-test-area">
            <div className="flashcard-grid">
              {flashcards.map((card, idx) => (
                <div
                  key={idx}
                  className="flashcard"
                  onClick={(e) => e.currentTarget.classList.toggle('flipped')}
                >
                  <div className="flashcard-inner">
                    <div className="flashcard-front">{card.term}</div>
                    <div className="flashcard-back">{card.definition}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FlashcardPage;
