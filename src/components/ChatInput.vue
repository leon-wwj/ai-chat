<script setup>
import { ref } from 'vue'

const message = ref('')

const emit = defineEmits(['send'])

function handleSend() {
  if (!message.value.trim()) return

  emit('send', message.value)

  message.value = ''
}
</script>

<template>
  <div class="chat-input">
    <input
      v-model="message"
      type="text"
      placeholder="输入消息..."
      @keyup.enter="handleSend"
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

.chat-input input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.chat-input button {
  padding: 0 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
</style>