import request from '@/utils/request'
import type { ChatMessage, ChatSettings, ChatResponse } from '@/types'

const API_BASE = request.defaults.baseURL || 'http://localhost:8000'

interface StreamHandlers {
  onDelta?: (delta: string) => void
  onError?: (err: string) => void
  onDone?: () => void
}

export function sendMessage(messages: ChatMessage[], settings: ChatSettings) {
  return request.post<ChatResponse>('/chat', {
    messages,
    api_key: settings.apiKey,
    base_url: settings.baseURL,
    model: settings.model,
    stream: false,
  })
}

export async function streamChat(
  messages: ChatMessage[],
  settings: ChatSettings,
  handlers: StreamHandlers = {}
): Promise<void> {
  const { onDelta, onError, onDone } = handlers

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
  if (!resp.body) {
    throw new Error('响应没有内容')
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()

  let hasError = false

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    if (chunk.startsWith('__ERROR__:')) {
      hasError = true
      onError?.(chunk.slice('__ERROR__:'.length))
      break
    }
    if (chunk) onDelta?.(chunk)
  }

  if (!hasError) onDone?.()
}
