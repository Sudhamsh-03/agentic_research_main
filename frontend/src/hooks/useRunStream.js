import { useEffect, useState } from 'react'

import { eventsUrl } from '../api/client.js'

const TERMINAL = ['completed', 'failed']

/**
 * Subscribe to a run's Server-Sent Events and collect them in order.
 * The backend replays anything emitted before this subscription, so mounting late
 * still produces a complete timeline.
 */
export default function useRunStream(sessionId) {
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState(null)
  const [streamError, setStreamError] = useState(null)

  useEffect(() => {
    if (!sessionId) {
      setEvents([])
      setStatus(null)
      setStreamError(null)
      return undefined
    }

    setEvents([])
    setStatus('running')
    setStreamError(null)

    const source = new EventSource(eventsUrl(sessionId))

    const append = (event) => {
      const data = JSON.parse(event.data)
      setEvents((previous) => [...previous, data])
      return data
    }

    const onStatus = (event) => setStatus(append(event).status || 'running')
    const onNode = (event) => append(event)
    const onTerminal = (event) => {
      const data = append(event)
      setStatus(data.status || data.type)
      source.close()
    }

    source.addEventListener('status', onStatus)
    source.addEventListener('node', onNode)
    TERMINAL.forEach((name) => source.addEventListener(name, onTerminal))
    source.onerror = () => {
      if (source.readyState === EventSource.CLOSED) {
        setStreamError('Lost connection to the run stream.')
      }
    }

    return () => {
      source.removeEventListener('status', onStatus)
      source.removeEventListener('node', onNode)
      TERMINAL.forEach((name) => source.removeEventListener(name, onTerminal))
      source.close()
    }
  }, [sessionId])

  return { events, status, streamError }
}
