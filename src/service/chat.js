import request from '@/utils/request'

export function sendMessage(message) {
  return request.post('/chat', {
    message
  })
}