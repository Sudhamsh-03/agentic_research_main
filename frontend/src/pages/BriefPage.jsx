import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getSession } from '../api/client.js'
import AgentTimeline from '../components/AgentTimeline.jsx'
import BriefView from '../components/BriefView.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

function logsAsEvents(logs) {
  return logs.map((log) => ({
    type: 'node',
    agent: log.agent_name,
    status: log.node_status,
    message: log.step_output,
    ts: log.timestamp,
  }))
}

export default function BriefPage() {
  const { sessionId } = useParams()
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getSession(sessionId)
      .then((data) => {
        if (!cancelled) {
          setDetail(data)
          setError(null)
        }
      })
      .catch((caught) => {
        if (!cancelled) setError(caught.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  if (loading) return <p className="empty">Loading brief...</p>
  if (error) {
    return (
      <div className="stack">
        <p className="error">{error}</p>
        <Link className="link" to="/history">Back to history</Link>
      </div>
    )
  }

  return (
    <div className="stack">
      <section className="card run-summary">
        <div className="run-summary-head">
          <div>
            <h2>{detail.topic}</h2>
            <p className="muted">
              {detail.depth} round(s), {detail.tone} tone, about {detail.target_words} words
            </p>
          </div>
          <StatusBadge status={detail.status} />
        </div>
        {detail.error_message && <p className="error">{detail.error_message}</p>}
        <Link className="link" to="/history">Back to history</Link>
      </section>

      <AgentTimeline events={logsAsEvents(detail.logs)} status={detail.status} />

      {detail.report ? (
        <BriefView topic={detail.topic} report={detail.report} />
      ) : (
        <p className="empty">This run did not produce a brief.</p>
      )}
    </div>
  )
}
