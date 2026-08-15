<template>
  <aside class="sidebar">
    <button class="new-chat">
      + 新建对话
    </button>

    <div class="conversation-list">
      <div class="conversation active">
        新的对话
      </div>

      <div class="conversation">
        Vue3 学习
      </div>

      <div class="conversation">
        JavaScript 问题
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  padding: 16px;
  background: #f5f5f5;
}

.new-chat {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
}

.conversation-list {
  margin-top: 20px;
}

.conversation {
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
}

.conversation:hover,
.conversation.active {
  background: #e5e5e5;
}
</style>