import { NavLink } from 'react-router-dom'

export default function Layout({ children }) {
  const linkClass = ({ isActive }) => (isActive ? 'nav-link nav-link-active' : 'nav-link')

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <h1>Agentic Research</h1>
            <p>Researcher and editor agents, working a topic end to end.</p>
          </div>
        </div>
        <nav aria-label="Main">
          <NavLink to="/" className={linkClass} end>
            New research
          </NavLink>
          <NavLink to="/history" className={linkClass}>
            History
          </NavLink>
        </nav>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <span>Briefs are generated from live web search and saved locally.</span>
      </footer>
    </div>
  )
}
