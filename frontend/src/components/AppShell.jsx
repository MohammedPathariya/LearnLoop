import { useState } from 'react';
import { NavLink } from '../router';
import logo from '../assets/learnloop-logo.svg';

const primaryLinks = [
  ['/', 'Home'],
  ['/learn', 'Learn'],
  ['/progress', 'Progress'],
];

const mobileLinks = [
  ['/', 'Home'],
  ['/learn', 'Learn'],
  ['/progress', 'Progress'],
];

const utilityLinks = [
  ['/history', 'History'],
  ['/benchmarks', 'Benchmarks'],
  ['/settings', 'System'],
];

function AppShell({ children }) {
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
        </nav>

        <div className="utility-nav">
          <button
            className="utility-menu-button"
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open more navigation"
          >
            More
          </button>
        </div>
      </header>

      <main className="app-main">
        {children}
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
              <span>More</span>
              <button type="button" onClick={() => setDrawerOpen(false)}>Close</button>
            </div>
            {utilityLinks.map(([to, label]) => (
              <NavLink key={to} to={to} onClick={() => setDrawerOpen(false)}>
                {label}
              </NavLink>
            ))}
            <a
              href="https://github.com/MohammedPathariya/LearnLoop"
              target="_blank"
              rel="noreferrer"
              onClick={() => setDrawerOpen(false)}
            >
              GitHub repository
            </a>
          </aside>
        </div>
      )}
    </div>
  );
}

export default AppShell;
