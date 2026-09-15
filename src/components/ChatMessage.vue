<script setup lang="ts">
import type { Message } from '@/types'

defineProps<{ message: Message }>()
</script>

<template>
  <div
    class="message"
    :class="[message.role, { error: message.error }]"
  >
    {{ message.content }}
    <span
      v-if="message.model && !message.error"
      class="model-tag"
    >
      {{ message.model }}
    </span>
  </div>
</template>

<style scoped>
.message {
  width: fit-content;
  max-width: 70%;
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 10px;
}

.user {
  margin-left: auto;
  background: #e3f2fd;
}

.assistant {
  margin-right: auto;
  background: #f5f5f5;
}

.message.error {
  background: #fff1f0;
  border: 1px solid #ffa39e;
  color: #cf1322;
}

.model-tag {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: #999;
  text-align: right;
}
</style>