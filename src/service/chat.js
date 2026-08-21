import request from '@/utils/request'

export function sendMessage(messages, settings) {
  return request.post('/chat', {
    messages,
    api_key: settings.apiKey,
    base_url: settings.baseURL,
    model: settings.model,
  })
}
