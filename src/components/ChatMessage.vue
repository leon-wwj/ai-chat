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
    :class="message.role"
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
}

.assistant {
  margin-right: auto;
}
</style>