const NODES = [
  { key: 'researcher', label: 'Researcher', blurb: 'Plans queries and gathers sources' },
  { key: 'editor', label: 'Editor', blurb: 'Checks relevance and writes the brief' },
]

function nodeState(events, key, runStatus) {
  const forNode = events.filter((event) => event.agent === key)
  if (forNode.length === 0) {
    return runStatus === 'failed' ? 'skipped' : 'pending'
  }
  const last = forNode[forNode.length - 1]
  if (last.status === 'complete') return 'done'
  if (runStatus === 'failed') return 'failed'
  return 'active'
}

function formatTime(value) {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return ''
  return parsed.toLocaleTimeString()
}

export default function AgentTimeline({ events, status }) {
  const nodeEvents = events.filter((event) => event.agent)

  return (
    <section className="card timeline" aria-live="polite">
      <h2>Workflow</h2>

      <ol className="node-track">
        {NODES.map((node) => {
          const state = nodeState(nodeEvents, node.key, status)
          return (
            <li key={node.key} className={'node node-' + state}>
              <span className="node-dot" aria-hidden="true" />
              <div>
                <strong>{node.label}</strong>
                <p>{node.blurb}</p>
                <span className="node-state">{state}</span>
              </div>
            </li>
          )
        })}
      </ol>

      {events.length === 0 ? (
        <p className="empty">No activity yet. Start a run to see agent steps appear here.</p>
      ) : (
        <ul className="event-log">
          {events.map((event, index) => (
            <li key={index} className={'event event-' + (event.status || event.type)}>
              <span className="event-time">{formatTime(event.ts)}</span>
              <span className="event-agent">{event.agent || event.type}</span>
              <span className="event-message">{event.message}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
