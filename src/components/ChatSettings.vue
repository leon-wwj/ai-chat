<script setup>
import { ref } from 'vue'

const props = defineProps({
  settings: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['save', 'close'])

const apiKey = ref(props.settings.apiKey)
const baseURL = ref(props.settings.baseURL)
const model = ref(props.settings.model)

function handleSave() {
  emit('save', {
    apiKey: apiKey.value.trim(),
    baseURL: baseURL.value.trim(),
    model: model.value.trim()
  })
}
</script>

<template>
  <div
    class="settings-overlay"
    @click.self="emit('close')"
  >
    <div class="settings-panel">
      <h3>API 设置</h3>

      <label>
        API Key
        <input
          v-model="apiKey"
          type="password"
          placeholder="sk-..."
        />
      </label>

      <label>
        接口地址
        <input
          v-model="baseURL"
          placeholder="https://api.deepseek.com"
        />
      </label>

      <label>
        模型名
        <input
          v-model="model"
          placeholder="deepseek-v4-flash"
        />
      </label>

      <div class="actions">
        <button @click="emit('close')">取消</button>
        <button @click="handleSave">保存</button>
      </div>

      <p class="hint">
        Key 仅保存在本浏览器 localStorage，请求时经本地后端转发，不会上传到任何第三方。
      </p>
    </div>
  </div>
</template>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.settings-panel {
  width: 360px;
  padding: 24px;
  background: white;
  border-radius: 12px;
}

.settings-panel h3 {
  margin: 0 0 16px;
}

.settings-panel label {
  display: block;
  margin-bottom: 14px;
  font-size: 14px;
}

.settings-panel input {
  display: block;
  width: 100%;
  margin-top: 6px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.actions button {
  padding: 8px 18px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.hint {
  margin-top: 16px;
  font-size: 12px;
  color: #888;
}
</style>
