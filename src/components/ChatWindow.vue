<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { ChatStatus, Message } from '@/types'
import ChatMessage from '@/components/ChatMessage.vue'

const props = defineProps<{
  messages: Message[]
  status?: ChatStatus
}>()

const statusText = computed(() => {
  if (props.status === 'sending') return '正在请求…'
  if (props.status === 'streaming') return '正在生成…'
  return ''
})

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
      v-if="statusText"
      class="loading"
    >
      {{ statusText }}
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
