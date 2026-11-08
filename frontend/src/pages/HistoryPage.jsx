import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { deleteSession, listSessions } from '../api/client.js'
import StatusBadge from '../components/StatusBadge.jsx'

function formatDate(value) {
  if (!value) return '-'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? '-' : parsed.toLocaleString()
}

export default function HistoryPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    listSessions()
      .then((data) => {
        setSessions(data)
        setError(null)
      })
      .catch((caught) => setError(caught.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  async function handleDelete(sessionId) {
    const confirmed = window.confirm('Delete this brief and its agent log?')
    if (!confirmed) return
    try {
      await deleteSession(sessionId)
      setSessions((previous) => previous.filter((item) => item.session_id !== sessionId))
    } catch (caught) {
      setError(caught.message)
    }
  }

  const filtered = sessions.filter((item) =>
    item.topic.toLowerCase().includes(query.trim().toLowerCase()),
  )

  return (
    <div className="stack">
      <section className="card">
        <div className="history-head">
          <h2>Saved briefs</h2>
          <input
            type="search"
            value={query}
            placeholder="Filter by topic"
            aria-label="Filter saved briefs by topic"
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        {loading && <p className="empty">Loading saved briefs...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && filtered.length === 0 && (
          <p className="empty">
            No briefs yet. <Link className="link" to="/">Start a research run</Link> and it will
            appear here.
          </p>
        )}

        {filtered.length > 0 && (
          <table className="history-table">
            <thead>
              <tr>
                <th scope="col">Topic</th>
                <th scope="col">Status</th>
                <th scope="col">Started</th>
                <th scope="col">Rounds</th>
                <th scope="col"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.session_id}>
                  <td>
                    <Link className="link" to={'/briefs/' + item.session_id}>
                      {item.topic}
                    </Link>
                  </td>
                  <td><StatusBadge status={item.status} /></td>
                  <td>{formatDate(item.started_at)}</td>
                  <td>{item.depth}</td>
                  <td className="row-actions">
                    <button
                      type="button"
                      className="button-danger"
                      onClick={() => handleDelete(item.session_id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
