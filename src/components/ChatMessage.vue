<script setup>
defineProps({
  message: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <div
    class="message"
    :class="[message.role, { error: message.error }]"
  >
    {{ message.content }}
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
</style>