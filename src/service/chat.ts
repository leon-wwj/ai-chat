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
  handlers: StreamHandlers = {},
  signal?: AbortSignal
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
    signal,
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
  let headerPending = ''
  let markerTail = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      let chunk = decoder.decode(value, { stream: true })

      if (!headerDone) {
        headerPending += chunk
        if (headerPending.startsWith('__MODEL__:')) {
          const nl = headerPending.indexOf('\n')
          if (nl === -1) continue
          onModel?.(headerPending.slice('__MODEL__:'.length, nl).trim())
          chunk = headerPending.slice(nl + 1)
        } else if ('__MODEL__:'.startsWith(headerPending)) {
          continue // 还只是标记的一段前缀，等下一块补齐
        } else {
          chunk = headerPending
        }
        headerPending = ''
        headerDone = true
      } else {
        chunk = markerTail + chunk
        markerTail = ''
      }

      // __ERROR__: 可能出现在流中间（中途断流时它跟在已输出的内容后面），
      // 所以全串查找，而不是只看开头。
      const errorAt = chunk.indexOf('__ERROR__:')
      if (errorAt !== -1) {
        const before = chunk.slice(0, errorAt)
        if (before) onDelta?.(before)
        hasError = true
        onError?.(chunk.slice(errorAt + '__ERROR__:'.length))
        break
      }

      // 标记可能被网络从任意位置切断（不只是下划线处），所以尾部只要匹配
      // 标记的某个前缀，就先留到下一块再判断，否则标记会被当成正文输出。
      const marker = '__ERROR__:'
      let cut = 0
      for (let n = Math.min(marker.length - 1, chunk.length); n > 0; n--) {
        if (chunk.endsWith(marker.slice(0, n))) {
          cut = n
          break
        }
      }
      if (cut) {
        markerTail = chunk.slice(chunk.length - cut)
        chunk = chunk.slice(0, chunk.length - cut)
      }

      if (chunk) onDelta?.(chunk)
    }

    if (headerPending) onDelta?.(headerPending)
    if (markerTail) onDelta?.(markerTail)
  } finally {
    // 正常读完时流已结束，cancel 无副作用；提前 break（收到错误）时流还没消费完，
    // 主动取消，否则这条连接会一直挂着、无法复用。
    await reader.cancel().catch(() => {})
  }

  if (!hasError) onDone?.()
}
