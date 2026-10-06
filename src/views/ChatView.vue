<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import type { Message, ChatSettings as Settings, ChatMessage, ChatStatus } from '@/types'

import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import ChatInput from '@/components/ChatInput.vue'
import ChatSettings from '@/components/ChatSettings.vue'
import { fetchModels, streamChat } from '@/service/chat'

const DEFAULT_SETTINGS: Settings = {
  apiKey: '',
  baseURL: 'https://api.deepseek.com',
  model: 'deepseek-flash'
}

const SYSTEM_PROMPT = '你是一个专业、准确、简洁的 AI 助手。'

function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem('ai-chat-settings')
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<Settings>
      return { ...DEFAULT_SETTINGS, ...parsed }
    }
    return { ...DEFAULT_SETTINGS }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

const messages = ref<Message[]>([])
const settings = reactive<Settings>(loadSettings())
const showSettings = ref(false)

let nextId = 1
const status = ref<ChatStatus>('idle')

const isActive = computed(
  () => status.value === 'sending' || status.value === 'streaming'
)

let abortController: AbortController | null = null

function handleStop() {
  abortController?.abort()
}

onBeforeUnmount(() => {
  abortController?.abort()
})

function loadModels(): string[] {
  try {
    const raw = localStorage.getItem('ai-chat-models')
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

const MODEL_PRESETS = ['deepseek-flash', 'deepseek-v4-pro']
const models = ref<string[]>(loadModels())

const modelOptions = computed(() =>
  models.value.length ? models.value : MODEL_PRESETS
)

async function refreshModels() {
  if (!settings.apiKey) return
  try {
    const list = await fetchModels(settings)
    if (list.length) {
      models.value = list
      localStorage.setItem('ai-chat-models', JSON.stringify(list))
    }
  } catch (error) {
    // 拉取失败不阻断聊天：保留现有列表（回退到模型预设）即可。
    // 但要留痕，否则"模型列表为什么不是最新的"这类问题无从排查。
    console.warn('[ai-chat] 拉取模型列表失败，沿用本地列表', error)
  }
}

onMounted(() => {
  if (settings.apiKey && !models.value.length) refreshModels()
})

function handleSaveSettings(newSettings: Settings) {
  Object.assign(settings, newSettings)
  localStorage.setItem('ai-chat-settings', JSON.stringify(settings))
  showSettings.value = false
  refreshModels()
}

function handleModelChange() {
  localStorage.setItem('ai-chat-settings', JSON.stringify(settings))
}

async function handleSend(message: string) {
  if (isActive.value) return

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
    content: '',
    model: settings.model
  })

  status.value = 'sending'
  abortController = new AbortController()

  try {
    const history: ChatMessage[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages.value
        .filter((m) => m.id !== assistantId && !m.system)
        .map((m) => ({ role: m.role, content: m.content }))
    ]

    await streamChat(history, settings, {
      onModel: (model: string) => {
        const target = messages.value.find((m) => m.id === assistantId)
        if (target) target.model = model
      },
      onDelta: (delta: string) => {
        status.value = 'streaming'
        const target = messages.value.find((m) => m.id === assistantId)
        if (target) target.content += delta
      },
      onDone: () => {
        status.value = 'done'
      },
      onError: (err: string) => {
        status.value = 'error'
        const target = messages.value.find((m) => m.id === assistantId)
        if (target) {
          target.content = err
          target.error = true
          target.system = true
        }
      }
    }, abortController.signal)
  } catch (error) {
    const target = messages.value.find((m) => m.id === assistantId)

    if (error instanceof DOMException && error.name === 'AbortError') {
      status.value = 'aborted'
      if (target && !target.content) target.content = '（已停止）'
    } else {
      status.value = 'error'
      const detail = error instanceof Error ? error.message : '未知错误'
      if (target) {
        target.content = `请求失败：${detail}`
        target.error = true
        target.system = true
      }
    }
  } finally {
    abortController = null
  }
}
</script>

<template>
  <div class="chat-view">
    <ChatSidebar />

    <div class="chat-main">
      <div class="chat-header">
        <select
          v-model="settings.model"
          class="model-select"
          @change="handleModelChange"
        >
          <option
            v-for="m in modelOptions"
            :key="m"
            :value="m"
          >
            {{ m }}
          </option>
          <option
            v-if="!modelOptions.includes(settings.model)"
            :value="settings.model"
          >
            {{ settings.model }}
          </option>
        </select>

        <button
          v-if="isActive"
          class="stop-btn"
          @click="handleStop"
        >
          停止
        </button>

        <button
          class="settings-btn"
          @click="showSettings = true"
        >
          API 设置
        </button>
      </div>

      <ChatWindow
        :messages="messages"
        :status="status"
      />

      <ChatInput
        :disabled="isActive"
        @send="handleSend"
      />
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
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.model-select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.settings-btn {
  padding: 6px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.stop-btn {
  padding: 6px 14px;
  border: 1px solid #ffa39e;
  border-radius: 6px;
  background: #fff1f0;
  color: #cf1322;
  cursor: pointer;
}
</style>
