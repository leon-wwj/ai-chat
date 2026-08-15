<script setup>
defineProps({
  messages: {
    type: Array,
    default: () => []
  }
})
</script>

<template>
  <main class="chat-window">
    <div v-if="messages.length === 0" class="empty">
      开始一段新的对话
    </div>

    <div
      v-for="message in messages"
      :key="message.id"
      class="message"
      :class="message.role"
    >
      {{ message.content }}
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

.message {
  width: fit-content;
  max-width: 70%;
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 10px;
}

.user {
  margin-left: auto;
}

.assistant {
  margin-right: auto;
}
</style>