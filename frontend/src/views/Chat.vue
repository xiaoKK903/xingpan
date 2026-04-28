<template>
  <el-container class="chat-container">
    <el-aside width="280px" class="conversation-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" class="new-chat-btn" @click="createNewChat">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
      </div>
      <el-scrollbar class="conversation-list">
        <div
          v-if="conversations.length === 0"
          class="empty-conversations"
        >
          <el-icon size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
          <p>暂无会话</p>
        </div>
        <div
          v-else
          v-for="item in conversations"
          :key="item.id"
          class="conversation-item"
          :class="{ active: currentConversationId === item.id }"
          @click="selectConversation(item.id)"
        >
          <div class="conversation-info">
            <div class="conversation-title">{{ item.title }}</div>
            <div class="conversation-time">{{ formatTime(item.updated_at) }}</div>
          </div>
          <el-button
            type="text"
            class="delete-btn"
            @click.stop="deleteConversation(item.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </el-scrollbar>
    </el-aside>
    <el-container class="chat-main">
      <div v-if="!currentConversationId" class="chat-welcome">
        <el-icon size="80" color="#409eff"><ChatDotRound /></el-icon>
        <h2>欢迎使用AI智能客服</h2>
        <p>点击左侧"新建对话"开始智能对话</p>
      </div>
      <template v-else>
        <el-header class="chat-header">
          <span class="chat-title">{{ currentConversation?.title || '新会话' }}</span>
        </el-header>
        <el-main class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-messages">
            <el-icon size="48" color="#c0c4cc"><Message /></el-icon>
            <p>开始和AI对话吧</p>
          </div>
          <div v-else class="message-list">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="message-item"
              :class="{ 'is-user': msg.role === 'user' }"
            >
              <div class="message-avatar">
                <el-icon v-if="msg.role === 'user'" size="32"><User /></el-icon>
                <el-icon v-else size="32" color="#409eff"><Service /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-bubble">
                  {{ msg.content }}
                </div>
                <div class="message-time">{{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
          </div>
        </el-main>
        <el-footer class="chat-input-area">
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="输入消息，按 Enter 发送，Shift + Enter 换行"
              resize="none"
              @keydown="handleKeydown"
              :disabled="sending"
            />
            <el-button
              type="primary"
              class="send-btn"
              :loading="sending"
              :disabled="!inputMessage.trim()"
              @click="sendMessage"
            >
              发送
            </el-button>
          </div>
        </el-footer>
      </template>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi, messageApi, chatApi } from '@/api'

const messagesContainer = ref(null)
const conversations = ref([])
const currentConversationId = ref(null)
const currentConversation = ref(null)
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)

const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } else {
    return `${date.getMonth() + 1}/${date.getDate()}`
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      const el = messagesContainer.value.$el || messagesContainer.value
      el.scrollTop = el.scrollHeight
    }
  })
}

const loadConversations = async () => {
  try {
    const res = await conversationApi.getList({ limit: 100 })
    conversations.value = res.items || []
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

const loadMessages = async (conversationId) => {
  if (!conversationId) return
  
  try {
    const res = await messageApi.getByConversationId(conversationId, { limit: 500 })
    messages.value = res.items || []
    scrollToBottom()
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

const selectConversation = async (conversationId) => {
  if (currentConversationId.value === conversationId) return
  
  currentConversationId.value = conversationId
  currentConversation.value = conversations.value.find(c => c.id === conversationId)
  messages.value = []
  await loadMessages(conversationId)
}

const createNewChat = async () => {
  try {
    const res = await conversationApi.create({ title: '新会话' })
    await loadConversations()
    selectConversation(res.conversation.id)
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

const deleteConversation = async (conversationId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await conversationApi.delete(conversationId)
    ElMessage.success('删除成功')
    
    if (currentConversationId.value === conversationId) {
      currentConversationId.value = null
      currentConversation.value = null
      messages.value = []
    }
    
    await loadConversations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
    }
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || sending.value) return
  
  let conversationId = currentConversationId.value
  
  if (!conversationId) {
    try {
      const res = await conversationApi.create({ title: '新会话' })
      conversationId = res.conversation.id
      currentConversationId.value = conversationId
      await loadConversations()
      currentConversation.value = conversations.value.find(c => c.id === conversationId)
    } catch (error) {
      console.error('创建会话失败:', error)
      return
    }
  }
  
  sending.value = true
  
  try {
    const res = await chatApi.send({
      conversation_id: conversationId,
      message: message
    })
    
    messages.value.push(res.user_message, res.assistant_message)
    inputMessage.value = ''
    
    scrollToBottom()
    
    await loadConversations()
    currentConversation.value = conversations.value.find(c => c.id === conversationId)
  } catch (error) {
    console.error('发送消息失败:', error)
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  loadConversations()
})
</script>

<style lang="scss" scoped>
.chat-container {
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  background-color: #fff;
}

.conversation-sidebar {
  background-color: #f8f9fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.new-chat-btn {
  width: 100%;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.empty-conversations {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
  
  p {
    margin-top: 10px;
  }
}

.conversation-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #eef2f6;
  }
  
  &.active {
    background-color: #ecf5ff;
  }
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.delete-btn {
  color: #909399;
  opacity: 0;
  transition: opacity 0.2s;
  
  &:hover {
    color: #f56c6c;
  }
}

.conversation-item:hover .delete-btn {
  opacity: 1;
}

.chat-main {
  display: flex;
  flex-direction: column;
}

.chat-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  
  h2 {
    margin: 20px 0 10px;
    color: #606266;
  }
}

.chat-header {
  height: 50px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
}

.chat-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-messages {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  
  p {
    margin-top: 10px;
  }
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  
  &.is-user {
    flex-direction: row-reverse;
    
    .message-content {
      align-items: flex-end;
    }
    
    .message-bubble {
      background-color: #409eff;
      color: #fff;
    }
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background-color: #f0f2f5;
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.send-btn {
  height: 40px;
  padding: 0 24px;
}
</style>
