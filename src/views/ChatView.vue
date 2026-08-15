<script setup>
import { ref } from 'vue'

import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import ChatInput from '@/components/ChatInput.vue'

const messages = ref([])

let nextId = 1

function handleSend(message) {
  messages.value.push({
    id: nextId++,
    role: 'user',
    content: message
  })
   messages.value.push({
    id: nextId++,
    role: 'assistant',
    content: '这是 AI 的模拟回复。'
  })
}
</script>

<template>
  <div class="chat-view">
    <ChatSidebar />

    <div class="chat-main">
      <ChatWindow :messages="messages" />

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