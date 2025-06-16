// ========== src/components/SessionList.js ==========
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './SessionList.css';

const SessionList = ({ sessions, emoji = "👩‍🎓", basePath = "/conversations" }) => {
  const navigate = useNavigate();
  return (
    <div className="session-list">
      {sessions.length > 0 ? (
        sessions.map((s) => (
          <div
            key={s.id}
            className="session-card clickable"
            onClick={() => navigate(`${basePath}/${s.id}`)}
          >
            <div className="session-avatar">{emoji}</div>
            <div className="session-details">
              <div className="session-topic">{s.topic || "(No topic)"}</div>
              <div className="session-time">
                {s.timestamp}
                {s.score !== undefined && s.num_questions !== undefined
                  ? ` — Score: ${s.score} / ${s.num_questions}`
                  : s.num_cards !== undefined
                  ? ` — ${s.num_cards} cards`
                  : ""}
              </div>
            </div>
          </div>
        ))
      ) : (
        <p style={{ marginLeft: "1rem" }}>No sessions found yet.</p>
      )}
    </div>
  );
};

export default SessionList;
