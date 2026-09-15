import request from '@/utils/request'
import type { ChatMessage, ChatSettings, ChatResponse } from '@/types'

const API_BASE = request.defaults.baseURL || 'http://localhost:8000'

interface StreamHandlers {
  onModel?: (model: string) => void
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

export async function fetchModels(settings: ChatSettings): Promise<string[]> {
  const resp = await request.post<{ models: string[] }>('/models', {
    api_key: settings.apiKey,
    base_url: settings.baseURL,
  })
  return resp.data.models
}

export async function streamChat(
  messages: ChatMessage[],
  settings: ChatSettings,
  handlers: StreamHandlers = {}
): Promise<void> {
  const { onModel, onDelta, onError, onDone } = handlers

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
  let headerDone = false
  let pending = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    let chunk = decoder.decode(value, { stream: true })

    if (!headerDone) {
      pending += chunk
      if (pending.startsWith('__MODEL__:')) {
        const nl = pending.indexOf('\n')
        if (nl === -1) continue
        onModel?.(pending.slice('__MODEL__:'.length, nl).trim())
        chunk = pending.slice(nl + 1)
      } else {
        chunk = pending
      }
      pending = ''
      headerDone = true
    }

    if (chunk.startsWith('__ERROR__:')) {
      hasError = true
      onError?.(chunk.slice('__ERROR__:'.length))
      break
    }
    if (chunk) onDelta?.(chunk)
  }

  if (!hasError) onDone?.()
}
