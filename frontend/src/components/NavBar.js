// ========== src/components/NavBar.js ==========
import React from 'react';
import { NavLink } from 'react-router-dom';
import './NavBar.css';

const NavBar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">LearnLoop</div>
      <div className="navbar-links">
        <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
        <NavLink to="/thinkmate" className={({ isActive }) => isActive ? 'active' : ''}>Chat</NavLink>
        <NavLink to="/quiz" className={({ isActive }) => isActive ? 'active' : ''}>Quiz</NavLink>
        <NavLink to="/flashcards" className={({ isActive }) => isActive ? 'active' : ''}>Flashcards</NavLink>
      </div>
    </nav>
  );
};

export default NavBar;
