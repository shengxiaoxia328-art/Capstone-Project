const API_BASE = '/api'

export type ThinkingCallback = (text: string) => void
export type StreamChunkCallback = (text: string) => void

/** 流式解析 SSE，每收到一条 data 就解析并回调 onThinking / onStream / onError，最后返回 result */
async function consumeSSE(
  res: Response,
  onThinking: ThinkingCallback,
  onError: (err: string) => void,
  onStream?: StreamChunkCallback
): Promise<Record<string, unknown>> {
  const reader = res.body?.getReader()
  const decoder = new TextDecoder()
  if (!reader) {
    const text = await res.text()
    throw new Error(text || 'No response body')
  }
  let buffer = ''
  let result: Record<string, unknown> = {}
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6)) as { event: string; text?: string; error?: string; [k: string]: unknown }
          if (data.event === 'thinking' && typeof data.text === 'string') {
            onThinking(data.text)
          } else if (data.event === 'stream' && typeof data.text === 'string' && onStream) {
            onStream(data.text)
          } else if (data.event === 'result') {
            const { event: _, ...rest } = data
            result = rest as Record<string, unknown>
          } else if (data.event === 'error' && typeof data.error === 'string') {
            onError(data.error)
          }
        } catch (_) {
          // ignore parse errors
        }
      }
    }
  }
  return result
}

function getSessionId(): string | null {
  return sessionStorage.getItem('photo_story_session_id')
}

function setSessionId(id: string) {
  sessionStorage.setItem('photo_story_session_id', id)
}

/** 收到会话无效时清除本地 session，避免后续请求继续用旧 id */
function clearSessionIfInvalid(res: Response, errBody: { error?: string }) {
  if (res.status === 400 && /缺少或无效的\s*session_id/.test(errBody?.error || '')) {
    sessionStorage.removeItem('photo_story_session_id')
  }
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
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
    }
    return res.json()
  },

  /** 流式分析：onThinking 显示阶段提示，onStream 显示解析/生成问题的实时内容 */
  async analyzeStream(
    file: File,
    onThinking: ThinkingCallback,
    onStream?: StreamChunkCallback
  ): Promise<{ photo_id: string; analysis_result: Record<string, unknown>; questions: string[] }> {
    const sid = getSessionId()
    if (!sid) throw new Error('请先选择模式')
    const form = new FormData()
    form.append('image', file)
    form.append('session_id', sid)
    const res = await fetch(`${API_BASE}/analyze/stream`, {
      method: 'POST',
      headers: { 'X-Session-Id': sid },
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
    }
    let errMsg = ''
    const out = await consumeSSE(res, onThinking, (e) => { errMsg = e }, onStream)
    if (errMsg) throw new Error(errMsg)
    return out as { photo_id: string; analysis_result: Record<string, unknown>; questions: string[] }
  },

  async answer(question: string, answer: string) {
    const res = await fetch(`${API_BASE}/answer`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ question, answer }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
    }
    return res.json()
  },

  async answerStream(
    question: string,
    answer: string,
    onThinking: ThinkingCallback,
    onStream?: StreamChunkCallback
  ): Promise<{ next_question: string | null; qa_history: { question: string; answer: string }[] }> {
    const res = await fetch(`${API_BASE}/answer/stream`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ question, answer }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
    }
    let errMsg = ''
    const out = await consumeSSE(res, onThinking, (e) => { errMsg = e }, onStream)
    if (errMsg) throw new Error(errMsg)
    return out as { next_question: string | null; qa_history: { question: string; answer: string }[] }
  },

  async finishPhoto() {
    const res = await fetch(`${API_BASE}/finish_photo`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({}),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
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
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
    }
    return res.json()
  },

  async generateStoryStream(
    onThinking: ThinkingCallback,
    onStream?: StreamChunkCallback
  ): Promise<{ story: string }> {
    const res = await fetch(`${API_BASE}/generate_story/stream`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({}),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      clearSessionIfInvalid(res, err)
      throw new Error(err.error === '缺少或无效的 session_id' ? '会话已过期或服务已重启，请重新选择模式' : (err.error || res.statusText))
    }
    let errMsg = ''
    const out = await consumeSSE(res, onThinking, (e) => { errMsg = e }, onStream)
    if (errMsg) throw new Error(errMsg)
    return out as { story: string }
  },
}
