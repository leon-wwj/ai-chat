<script setup>
import { ref, reactive } from 'vue'

import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import ChatInput from '@/components/ChatInput.vue'
import ChatSettings from '@/components/ChatSettings.vue'
import { streamChat } from '@/service/chat'

const DEFAULT_SETTINGS = {
  apiKey: '',
  baseURL: 'https://api.deepseek.com',
  model: 'deepseek-v4-flash'
}

const SYSTEM_PROMPT = '你是一个专业、准确、简洁的 AI 助手。'

function loadSettings() {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem('ai-chat-settings')) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

const messages = ref([])
const settings = reactive(loadSettings())
const showSettings = ref(false)

let nextId = 1
const isLoading = ref(false)

function handleSaveSettings(newSettings) {
  Object.assign(settings, newSettings)
  localStorage.setItem('ai-chat-settings', JSON.stringify(settings))
  showSettings.value = false
}

async function handleSend(message) {
  if (!settings.apiKey) {
    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: '请先点击"API 设置"填入你的 API Key。',
      system: true
    })
    return
  }

  messages.value.push({
    id: nextId++,
    role: 'user',
    content: message
  })

  const assistantId = nextId++
  messages.value.push({
    id: assistantId,
    role: 'assistant',
    content: ''
  })

  isLoading.value = true

  try {
    const history = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages.value
        .filter((m) => m.id !== assistantId && !m.system)
        .map((m) => ({ role: m.role, content: m.content }))
    ]

    await streamChat(history, settings, {
      onDelta: (delta) => {
        const target = messages.value.find((m) => m.id === assistantId)
        if (target) target.content += delta
      },
      onError: (err) => {
        const target = messages.value.find((m) => m.id === assistantId)
        if (target) {
          target.content = err
          target.error = true
          target.system = true
        }
      }
    })
  } catch (error) {
    const target = messages.value.find((m) => m.id === assistantId)
    const detail = error.response?.data?.error || error.message || '未知错误'
    if (target) {
      target.content = `请求失败：${detail}`
      target.error = true
      target.system = true
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chat-view">
    <ChatSidebar />

    <div class="chat-main">
      <div class="chat-header">
        <button
          class="settings-btn"
          @click="showSettings = true"
        >
          API 设置
        </button>
      </div>

      <ChatWindow
        :messages="messages"
        :is-loading="isLoading"
      />

      <ChatInput @send="handleSend" />
    </div>

    <ChatSettings
      v-if="showSettings"
      :settings="settings"
      @save="handleSaveSettings"
      @close="showSettings = false"
    />
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  height: 100vh;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.settings-btn {
  padding: 6px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}
</style>
