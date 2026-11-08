import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { createSession, getSession } from '../api/client.js'
import AgentTimeline from '../components/AgentTimeline.jsx'
import BriefView from '../components/BriefView.jsx'
import ResearchForm from '../components/ResearchForm.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import useRunStream from '../hooks/useRunStream.js'

export default function ResearchPage() {
  const [session, setSession] = useState(null)
  const [detail, setDetail] = useState(null)
  const [submitError, setSubmitError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const { events, status, streamError } = useRunStream(session?.session_id)
  const running = Boolean(session) && !['completed', 'failed'].includes(status)

  useEffect(() => {
    if (!session || !['completed', 'failed'].includes(status)) return
    let cancelled = false
    getSession(session.session_id)
      .then((data) => {
        if (!cancelled) setDetail(data)
      })
      .catch((error) => {
        if (!cancelled) setSubmitError(error.message)
      })
    return () => {
      cancelled = true
    }
  }, [session, status])

  async function handleSubmit(payload) {
    setSubmitting(true)
    setSubmitError(null)
    setDetail(null)
    try {
      const created = await createSession(payload)
      setSession(created)
    } catch (error) {
      setSubmitError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="stack">
      <ResearchForm onSubmit={handleSubmit} disabled={submitting || running} />

      {submitError && <p className="error">{submitError}</p>}

      {session && (
        <section className="card run-summary">
          <div className="run-summary-head">
            <div>
              <h2>{session.topic}</h2>
              <p className="muted">
                {session.depth} round(s), {session.tone} tone, about {session.target_words} words
              </p>
            </div>
            <StatusBadge status={status || session.status} />
          </div>
          {streamError && <p className="error">{streamError}</p>}
          {detail?.error_message && <p className="error">{detail.error_message}</p>}
          {detail && (
            <Link className="link" to={'/briefs/' + session.session_id}>
              Open saved brief
            </Link>
          )}
        </section>
      )}

      {session && <AgentTimeline events={events} status={status} />}

      {detail?.report && <BriefView topic={detail.topic} report={detail.report} />}
    </div>
  )
}
