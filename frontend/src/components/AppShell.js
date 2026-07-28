import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import logo from '../assets/learnloop-logo.svg';

const primaryLinks = [
  ['/', 'Home'],
  ['/study', 'Study'],
  ['/materials', 'Materials'],
  ['/practice', 'Practice'],
  ['/flashcards', 'Flashcards'],
  ['/progress', 'Progress'],
  ['/history', 'History'],
];

const mobileLinks = [
  ['/', 'Home'],
  ['/study', 'Study'],
  ['/practice', 'Practice'],
  ['/progress', 'Progress'],
];

function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="app-shell">
      <header className="top-nav">
        <NavLink className="brand-lockup" to="/" aria-label="learnloop home">
          <img src={logo} alt="" />
          <span>learnloop</span>
        </NavLink>

        <nav className="desktop-nav" aria-label="Primary navigation">
          {primaryLinks.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'}>
              {label}
            </NavLink>
          ))}
          <NavLink className="benchmark-link" to="/benchmarks">Benchmarks</NavLink>
        </nav>

        <div className="utility-nav">
          <a
            href="https://github.com/MohammedPathariya/LearnLoop"
            target="_blank"
            rel="noreferrer"
            aria-label="Open LearnLoop source on GitHub"
            title="Source on GitHub"
          >
            GH
          </a>
          <NavLink to="/settings" aria-label="Open system settings" title="System settings">
            SYS
          </NavLink>
          <button
            className="mobile-menu-button"
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
          >
            Menu
          </button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="mobile-bottom-nav" aria-label="Mobile navigation">
        {mobileLinks.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === '/'}>
            <span className="mobile-nav-mark" aria-hidden="true">{label[0]}</span>
            {label}
          </NavLink>
        ))}
        <button type="button" onClick={() => setDrawerOpen(true)}>
          <span className="mobile-nav-mark" aria-hidden="true">+</span>
          More
        </button>
      </nav>

      {drawerOpen && (
        <div className="drawer-backdrop" onMouseDown={() => setDrawerOpen(false)}>
          <aside
            className="mobile-drawer"
            onMouseDown={(event) => event.stopPropagation()}
            aria-label="All navigation"
          >
            <div className="drawer-heading">
              <span>Navigate</span>
              <button type="button" onClick={() => setDrawerOpen(false)}>Close</button>
            </div>
            {[...primaryLinks, ['/benchmarks', 'Benchmarks'], ['/settings', 'System']].map(([to, label]) => (
              <NavLink key={to} to={to} onClick={() => setDrawerOpen(false)}>
                {label}
              </NavLink>
            ))}
          </aside>
        </div>
      )}
    </div>
  );
}

export default AppShell;
