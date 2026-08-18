<script setup>
import { ref } from 'vue'

import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import ChatInput from '@/components/ChatInput.vue'
import { sendMessage } from '@/service/chat'

const messages = ref([])

let nextId = 1
const isLoading = ref(false)
async function handleSend(message) {
  messages.value.push({
    id: nextId++,
    role: 'user',
    content: message
  })

  isLoading.value = true

  try {
    const response = await sendMessage(message)

    messages.value.push({
      id: nextId++,
      role: response.data.role,
      content: response.data.content
    })
  } catch (error) {
    console.error('发送消息失败:', error)

    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: '请求失败，请检查后端服务是否启动。'
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chat-view">
    <ChatSidebar />

    <div class="chat-main">
      <ChatWindow
        :messages="messages"
        :is-loading="isLoading"
      />

      <ChatInput @send="handleSend" />
    </div>
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
</style>