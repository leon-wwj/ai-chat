export interface ChatSettings {
  apiKey: string
  baseURL: string
  model: string
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface Message extends ChatMessage {
  id: number
  error?: boolean
  system?: boolean
}
