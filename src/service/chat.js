import request from '@/utils/request'

const API_BASE = request.defaults.baseURL || 'http://localhost:8000'

export function sendMessage(messages, settings) {
  return request.post('/chat', {
    messages,
    api_key: settings.apiKey,
    base_url: settings.baseURL,
    model: settings.model,
    stream: false,
  })
}

export async function streamChat(messages, settings, handlers) {
  const { onDelta, onError, onDone } = handlers || {}

  const resp = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      api_key: settings.apiKey,
      base_url: settings.baseURL,
      model: settings.model,
      stream: true,
    }),
  })

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    if (chunk.startsWith('__ERROR__:')) {
      onError && onError(chunk.slice('__ERROR__:'.length))
      break
    }
    if (chunk) onDelta && onDelta(chunk)
  }

  onDone && onDone()
}
