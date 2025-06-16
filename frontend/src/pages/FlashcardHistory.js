import React, { useEffect, useState } from 'react';
import { getFlashcardHistory } from '../api/thinkmateApi';
import { Link } from 'react-router-dom';

const FlashcardHistory = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    (async () => {
      const data = await getFlashcardHistory();
      setHistory(data);
    })();
  }, []);

  return (
    <div className="container">
      <h2>🕓 Flashcard History</h2>
      <ul>
        {history.map((entry) => (
          <li key={entry.id}>
            <Link to={`/flashcards/${entry.id}`}>
              {entry.topic} ({entry.num_cards} cards) – {entry.timestamp}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FlashcardHistory;
