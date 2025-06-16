import React, { useEffect, useState } from 'react';
import { getFlashcardSetById } from '../api/thinkmateApi';
import { useParams } from 'react-router-dom';
import './Flashcard.css';

const FlashcardDetail = () => {
  const { id } = useParams();
  const [setData, setSetData] = useState(null);
  const [flippedIndex, setFlippedIndex] = useState(null);

  useEffect(() => {
    (async () => {
      const data = await getFlashcardSetById(id);
      setSetData(data);
    })();
  }, [id]);

  const handleFlip = (index) => {
    setFlippedIndex(index === flippedIndex ? null : index);
  };

  if (!setData) return <p>Loading...</p>;

  return (
    <div className="container">
      <h2>🧠 Flashcards for: {setData.topic}</h2>
      <div className="flashcard-grid">
        {setData.flashcards.map((card, idx) => (
          <div
            key={idx}
            className={`flashcard ${flippedIndex === idx ? 'flipped' : ''}`}
            onClick={() => handleFlip(idx)}
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

export default FlashcardDetail;
