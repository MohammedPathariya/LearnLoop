// ========== src/components/StatCard.js ==========
import React from 'react';
import './StatCard.css';

const StatCard = ({ title, value, icon, bgColor }) => (
  <div className="stat-card" style={{ backgroundColor: bgColor }}>
    <div className="stat-icon">{icon}</div>
    <div className="stat-content">
      <h4>{title}</h4>
      <p>{value}</p>
    </div>
  </div>
);

export default StatCard;