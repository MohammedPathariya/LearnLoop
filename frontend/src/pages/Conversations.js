// ========== src/pages/Conversations.js ==========
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getChatById } from '../api/thinkmateApi';
import './Conversations.css';

const Conversations = () => {
  const { id } = useParams();
  const [conv, setConv] = useState(null);

  useEffect(() => {
    getChatById(id).then(res => setConv(res.data));
  }, [id]);

  const renderComicChat = () => {
    if (!conv?.result) return null;
    const lines = conv.result.split(/\n|\r/).filter(Boolean);
    return lines.map((line, idx) => {
      const isStudent = line.toLowerCase().includes('student');
      return (
        <div
          key={idx}
          className={`comic-bubble ${isStudent ? 'student' : 'teacher'}`}
        >
          <div className="comic-avatar-circle">
            {isStudent ? '🧑‍🎓' : '👨‍🏫'}
          </div>
          <div className="comic-text">
            {line.replace(/\*\*(.*?)\*\*/g, '$1')}
          </div>
        </div>
      );
    });
  };

  if (!conv) return <p>Loading conversation...</p>;

  return (
    <div className="conversation">
      <h2>Topic: {conv.topic}</h2>
      <div className="comic-wrapper">
        {renderComicChat()}
      </div>
    </div>
  );
};

export default Conversations;