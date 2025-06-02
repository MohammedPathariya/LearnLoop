// ========== src/components/Placeholder.js ==========
import React from 'react';
import './Placeholder.css';

const Placeholder = ({ title }) => (
  <div className="placeholder">
    <h3>{title}</h3>
    <p>Coming soon...</p>
  </div>
);

export default Placeholder;