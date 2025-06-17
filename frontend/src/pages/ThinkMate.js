// src/pages/ThinkMate.js

import React, { useState } from 'react';
import { startConversation } from '../api/thinkmateApi';
import './ThinkMate.css';

const ThinkMate = () => {
  const [topic, setTopic] = useState('');
  const [turns, setTurns] = useState(3);
  const [tone, setTone] = useState('Natural');
  const [speaker, setSpeaker] = useState('Student First');
  const [conversation, setConversation] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        topic,
        turns: parseInt(turns),
        style: tone.toLowerCase(),
        mode: speaker.toLowerCase().replace(' ', '-'),
      };
      const res = await startConversation(payload);
      setConversation(res.data.conversation);
    } catch {
      alert('Failed to generate conversation');
    }
    setLoading(false);
  };

  const renderChat = () => {
    if (!conversation) return null;
    const blocks = conversation
      .split(/\n\s*\n/)
      .filter((blk) => blk.trim() !== '');

    return (
      <div className="chat-messages">
        {blocks.map((blk, idx) => {
          let role = 'teacher';
          let text = blk.trim();

          if (/^\*\*student:\*\*/i.test(text)) {
            role = 'student';
            text = text.replace(/^\*\*student:\*\*/i, '').trim();
          } else if (/^\*\*teacher:\*\*/i.test(text)) {
            role = 'teacher';
            text = text.replace(/^\*\*teacher:\*\*/i, '').trim();
          }

          return (
            <div
              key={idx}
              className={`message-container ${
                role === 'student' ? 'chat-student' : 'chat-teacher'
              }`}
            >
              <div className="message-icon">
                {role === 'student' ? '👩‍🎓' : '👨‍🏫'}
              </div>
              <div className="chat-bubble">{text}</div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="page-bg-wrapper">
      <div className="thinkmate-container">
        <h2>Concept Breakdown Through Dialogue</h2>
        <p className="subtitle">
          Learn any topic through a natural student–teacher style conversation.
        </p>

        <form className="thinkmate-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="topic-input">Topic</label>
            <input
              id="topic-input"
              type="text"
              placeholder="Enter a topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="turns-input">Number of Exchanges</label>
            <input
              id="turns-input"
              type="number"
              placeholder="Exchanges"
              min="1"
              value={turns}
              onChange={(e) => setTurns(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="tone-select">Tone / Style</label>
            <select
              id="tone-select"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            >
              <option>Natural</option>
              <option>Formal</option>
              <option>Humorous</option>
              <option>Technical</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="speaker-select">Who Goes First</label>
            <select
              id="speaker-select"
              value={speaker}
              onChange={(e) => setSpeaker(e.target.value)}
            >
              <option>Student First</option>
              <option>Teacher First</option>
            </select>
          </div>

          {/* Updated button uses the new palette */}
          <button
            type="submit"
            className="generate-btn"
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate'}
          </button>
        </form>

        {renderChat()}
      </div>
    </div>
  );
};

export default ThinkMate;
