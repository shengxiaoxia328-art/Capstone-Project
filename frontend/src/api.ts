const API_BASE = '/api'

function getSessionId(): string | null {
  return sessionStorage.getItem('photo_story_session_id')
}

function setSessionId(id: string) {
  sessionStorage.setItem('photo_story_session_id', id)
}

function headers(): HeadersInit {
  const h: HeadersInit = { 'Content-Type': 'application/json' }
  const sid = getSessionId()
  if (sid) (h as Record<string, string>)['X-Session-Id'] = sid
  return h
}

export const api = {
  getSessionId,
  setSessionId,

  async init(mode: 'single' | 'multi') {
    const res = await fetch(`${API_BASE}/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || res.statusText)
    }
    const data = await res.json()
    setSessionId(data.session_id)
    return data
  },

  async analyze(file: File) {
    const sid = getSessionId()
    if (!sid) throw new Error('请先选择模式')
    const form = new FormData()
    form.append('image', file)
    form.append('session_id', sid)
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'X-Session-Id': sid },
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || res.statusText)
    }
    return res.json()
  },

  async answer(question: string, answer: string) {
    const res = await fetch(`${API_BASE}/answer`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ question, answer }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || res.statusText)
    }
    return res.json()
  },

  async finishPhoto() {
    const res = await fetch(`${API_BASE}/finish_photo`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({}),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || res.statusText)
    }
    return res.json()
  },

  async generateStory() {
    const res = await fetch(`${API_BASE}/generate_story`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({}),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || res.statusText)
    }
    return res.json()
  },
}
