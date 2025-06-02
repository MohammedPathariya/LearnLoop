// ========== src/components/SessionList.js ==========
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './SessionList.css';

const SessionList = ({ sessions }) => {
  const navigate = useNavigate();
  return (
    <div className="session-list">
  {sessions.map(s => (
    <div key={s.id}
            className="session-card clickable"
            onClick={() => navigate(`/conversations/${s.id}`)}
        >
          <div className="session-avatar">👩‍🎓</div>
          <div className="session-details">
            <div className="session-topic">{s.topic}</div>
            <div className="session-time">{s.timestamp}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SessionList;