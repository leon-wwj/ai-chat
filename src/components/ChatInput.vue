<script setup lang="ts">
import { ref } from 'vue'

const message = ref('')
const emit = defineEmits<{ send: [message: string] }>()

function handleSend() {
  if (!message.value.trim()) return

  emit('send', message.value)

  message.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-input">
    <textarea
      v-model="message"
      placeholder="输入消息..."
      @keydown="handleKeydown"
    />

    <button @click="handleSend">
      发送
    </button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 10px;
  padding: 16px;
  border-top: 1px solid #eee;
}

.chat-input textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
}

.chat-input button {
  padding: 0 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
</style>