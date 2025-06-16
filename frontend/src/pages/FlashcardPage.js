import React, { useState } from 'react';
import { generateFlashcards } from '../api/thinkmateApi';
import './QuizPage.css';
import './Flashcard.css';

const FlashcardPage = () => {
  const [topic, setTopic] = useState('');
  const [numCards, setNumCards] = useState(5);
  const [flashcards, setFlashcards] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setFlashcards([]);

    try {
      const data = await generateFlashcards(topic, numCards);
      console.log("GPT flashcard response:", JSON.stringify(data, null, 2));
      setFlashcards(data.flashcards || []);
    } catch (err) {
      console.error("Error generating flashcards:", err);
    }

    setLoading(false);
  };

  return (
    <div className="container">
      <h2>📇 Generate Flashcards</h2>
      <form onSubmit={handleGenerate}>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter topic..."
        />
        <input
          type="number"
          value={numCards}
          onChange={(e) => setNumCards(e.target.value)}
          min={1}
          max={10}
        />
        <button type="submit">Generate</button>
      </form>

      {loading && <p>Generating...</p>}

      <div className="flashcard-grid">
        {flashcards.map((card, idx) => (
          <div
            key={idx}
            className="flashcard"
            onClick={(e) =>
              e.currentTarget.classList.toggle('flipped')
            }
          >
            <div className="flashcard-inner">
              <div className="flashcard-front">{card.term}</div>
              <div className="flashcard-back">{card.definition}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FlashcardPage;
