<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { Message } from '@/types'
import ChatMessage from '@/components/ChatMessage.vue'

const props = defineProps<{
  messages: Message[]
  isLoading?: boolean
}>()

const messagesContainer = ref<HTMLElement | null>(null)

watch(
  () => props.messages.length,
  async () => {
    await nextTick()

    if (messagesContainer.value) {
      messagesContainer.value.scrollTop =
        messagesContainer.value.scrollHeight
    }
  }
)
</script>

<template>
  <main
    ref="messagesContainer"
    class="chat-window"
  >
    <div
      v-if="messages.length === 0"
      class="empty"
    >
      开始一段新的对话
    </div>

    <ChatMessage
      v-for="message in messages"
      :key="message.id"
      :message="message"
    />
    <div
      v-if="isLoading"
      class="loading"
    > 
      AI 正在思考...
    </div>
  </main>
</template>

<style scoped>
.chat-window {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
}

.empty {
  text-align: center;
}
.loading {
  margin-bottom: 16px;
}
</style>
