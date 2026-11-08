const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(
  /\/$/,
  '',
)

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        detail = body.detail
      } else if (Array.isArray(body.detail) && body.detail.length > 0) {
        detail = body.detail.map((item) => item.msg).join('; ')
      }
    } catch {
      // Response had no JSON body; the status-based message stands.
    }
    throw new Error(detail)
  }

  if (response.status === 204) return null
  return response.json()
}

export function createSession(payload) {
  return request('/api/sessions', { method: 'POST', body: JSON.stringify(payload) })
}

export function listSessions() {
  return request('/api/sessions')
}

export function getSession(sessionId) {
  return request(`/api/sessions/${encodeURIComponent(sessionId)}`)
}

export function deleteSession(sessionId) {
  return request(`/api/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
}

export function getHealth() {
  return request('/health')
}

export function eventsUrl(sessionId) {
  return `${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}/events`
}
