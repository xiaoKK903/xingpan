<template>
  <div class="private-chat-container">
    <div class="chat-layout">
      <div class="chat-sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">
            <el-icon><ChatDotRound /></el-icon>
            我的消息
          </h3>
          <div class="unread-badge" v-if="totalUnread > 0">
            {{ totalUnread > 99 ? '99+' : totalUnread }}
          </div>
        </div>
        
        <el-scrollbar class="chat-list-scroll">
          <div v-if="chatList.length === 0 && !loadingChats" class="empty-chats">
            <el-icon size="48" color="#c0c4cc"><Message /></el-icon>
            <p>暂无聊天记录</p>
            <p class="hint">从人脉链或相位连连看开始聊天吧</p>
          </div>
          
          <div v-else-if="loadingChats" class="loading-chats">
            <el-icon class="loading-icon" size="32"><Loading /></el-icon>
            <p>加载中...</p>
          </div>
          
          <div v-else class="chat-list">
            <div
              v-for="chat in chatList"
              :key="chat.chat_id"
              class="chat-item"
              :class="{ active: activeChatId === chat.chat_id }"
              @click="selectChat(chat)"
            >
              <div class="chat-avatar">
                <span class="avatar-icon">👤</span>
              </div>
              <div class="chat-info">
                <div class="chat-header">
                  <span class="chat-name">{{ chat.target_user?.name || '用户' }}</span>
                  <span class="chat-time">{{ formatChatTime(chat.last_message?.at) }}</span>
                </div>
                <div class="chat-preview-row">
                  <span class="chat-preview" v-if="chat.last_message?.content">
                    {{ chat.last_message.sender_id === currentUserId ? '你: ' : '' }}
                    {{ chat.last_message.content.length > 30 ? chat.last_message.content.substring(0, 30) + '...' : chat.last_message.content }}
                  </span>
                  <span v-else class="chat-preview-empty">开始聊天</span>
                  
                  <div v-if="chat.unread_count > 0" class="chat-unread">
                    {{ chat.unread_count > 99 ? '99+' : chat.unread_count }}
                  </div>
                </div>
                
                <div v-if="chat.compatibility_score" class="chat-match-info">
                  <span class="match-score">
                    匹配度 <strong :style="{ color: getScoreColor(chat.compatibility_score) }">{{ chat.compatibility_score }}%</strong>
                  </span>
                  <span v-if="chat.match_type" class="match-type">
                    {{ getMatchTypeLabel(chat.match_type) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      
      <div class="chat-main">
        <div v-if="!activeChatId" class="chat-welcome">
          <el-icon size="80" color="#8b5cf6"><ChatDotRound /></el-icon>
          <h2>选择一个聊天开始对话</h2>
          <p>从左侧列表选择联系人，或者从人脉链发现新的缘分</p>
          <el-button type="primary" @click="goToNetworkChain">
            <el-icon><User /></el-icon>
            前往人脉链
          </el-button>
        </div>
        
        <template v-else>
          <div class="chat-main-header">
            <div class="header-info">
              <div class="header-avatar">
                <span class="avatar-icon">👤</span>
              </div>
              <div class="header-details">
                <div class="header-name">{{ activeChat?.target_user?.name || '用户' }}</div>
                <div class="header-status">
                  <span class="status-dot online"></span>
                  在线
                </div>
              </div>
            </div>
            
            <div class="header-actions" v-if="activeChat?.compatibility_score">
              <div class="header-match">
                <span class="match-label">星盘匹配</span>
                <span class="match-value" :style="{ color: getScoreColor(activeChat.compatibility_score) }">
                  {{ activeChat.compatibility_score }}%
                </span>
              </div>
            </div>
          </div>
          
          <div class="chat-messages" ref="messagesContainer">
            <div v-if="loadingMessages" class="loading-messages">
              <el-icon class="loading-icon" size="24"><Loading /></el-icon>
              <span>加载消息中...</span>
            </div>
            
            <div v-else-if="messages.length === 0" class="empty-messages">
              <el-icon size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
              <p>还没有消息</p>
              <p class="hint">发送第一条消息开始聊天吧</p>
            </div>
            
            <div v-else class="message-list">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message-item"
                :class="{ 'is-me': msg.sender_id === currentUserId }"
              >
                <div class="message-avatar">
                  <span class="avatar-icon-small">👤</span>
                </div>
                <div class="message-content">
                  <div class="message-bubble">
                    {{ msg.content }}
                  </div>
                  <div class="message-time">
                    {{ formatMessageTime(msg.created_at) }}
                    <span v-if="msg.is_me && msg.is_read" class="read-status">已读</span>
                  </div>
                </div>
              </div>
              
              <div v-if="loadingMore" class="loading-more">
                <el-icon class="loading-icon" size="16"><Loading /></el-icon>
                <span>加载更多...</span>
              </div>
            </div>
          </div>
          
          <div class="chat-input-area">
            <div class="input-container">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="2"
                placeholder="输入消息..."
                resize="none"
                @keydown="handleKeydown"
                :disabled="sending"
              />
              <div class="input-actions">
                <span class="input-hint">按 Enter 发送，Shift + Enter 换行</span>
                <el-button
                  type="primary"
                  :loading="sending"
                  :disabled="!inputMessage.trim()"
                  @click="sendMessage"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { privateChatApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { ChatDotRound, Message, User, Loading } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const chatList = ref([])
const activeChatId = ref(null)
const activeChat = ref(null)
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const loadingChats = ref(false)
const loadingMessages = ref(false)
const loadingMore = ref(false)

const messagesContainer = ref(null)

const currentUserId = computed(() => userStore.userId || 0)

const totalUnread = computed(() => {
  return chatList.value.reduce((sum, chat) => sum + (chat.unread_count || 0), 0)
})

const formatChatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const formatMessageTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const getScoreColor = (score) => {
  if (score >= 85) return '#22c55e'
  if (score >= 70) return '#3b82f6'
  if (score >= 55) return '#f59e0b'
  return '#ef4444'
}

const getMatchTypeLabel = (type) => {
  const labels = {
    'soulmate': '灵魂共鸣',
    'harmonious': '和谐共鸣',
    'complementary': '能量互补',
    'challenging': '张力吸引'
  }
  return labels[type] || '能量连接'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      const el = messagesContainer.value.$el || messagesContainer.value
      if (el) {
        el.scrollTop = el.scrollHeight
      }
    }
  })
}

const loadChatList = async () => {
  loadingChats.value = true
  try {
    const result = await privateChatApi.getChatList(0, 50)
    if (result && result.items) {
      chatList.value = result.items
    }
  } catch (error) {
    console.error('加载聊天列表失败:', error)
  } finally {
    loadingChats.value = false
  }
}

const selectChat = async (chat) => {
  if (activeChatId.value === chat.chat_id) return
  
  activeChatId.value = chat.chat_id
  activeChat.value = chat
  messages.value = []
  inputMessage.value = ''
  
  await loadMessages(chat.chat_id, true)
}

const loadMessages = async (chatId, markAsRead = true) => {
  if (!chatId) return
  
  loadingMessages.value = true
  try {
    const result = await privateChatApi.getMessages(chatId, null, 50, markAsRead)
    if (result && result.messages) {
      messages.value = result.messages.map(msg => ({
        ...msg,
        is_me: msg.sender_id === currentUserId.value
      }))
      
      scrollToBottom()
      
      if (markAsRead) {
        const chat = chatList.value.find(c => c.chat_id === chatId)
        if (chat) {
          chat.unread_count = 0
        }
      }
    }
  } catch (error) {
    console.error('加载消息失败:', error)
  } finally {
    loadingMessages.value = false
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
  if (!message || sending.value || !activeChatId.value) return
  
  sending.value = true
  try {
    const result = await privateChatApi.sendMessage({
      chat_id: activeChatId.value,
      content: message
    })
    
    if (result && result.message_id) {
      const newMessage = {
        id: result.message_id || Date.now(),
        chat_id: activeChatId.value,
        sender_id: currentUserId.value,
        receiver_id: activeChat.value?.target_user?.id,
        content: message,
        message_type: 'text',
        is_read: false,
        is_me: true,
        created_at: new Date().toISOString()
      }
      
      messages.value.push(newMessage)
      inputMessage.value = ''
      
      scrollToBottom()
      
      const chat = chatList.value.find(c => c.chat_id === activeChatId.value)
      if (chat) {
        chat.last_message = {
          content: message,
          sender_id: currentUserId.value,
          at: new Date().toISOString()
        }
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送失败，请重试')
  } finally {
    sending.value = false
  }
}

const goToNetworkChain = () => {
  router.push('/network-chain')
}

const startChatWithTarget = async (targetUserId, matchInfo = {}) => {
  console.log('[PrivateChat] startChatWithTarget 被调用:', { targetUserId, matchInfo })
  
  if (!targetUserId || typeof targetUserId !== 'number' || targetUserId <= 0) {
    console.error('[PrivateChat] 无效的目标用户ID:', targetUserId)
    ElMessage.warning('无效的用户信息')
    return
  }
  
  try {
    ElMessage.info('正在创建聊天会话...')
    
    const result = await privateChatApi.startChat({
      target_user_id: targetUserId,
      match_source: matchInfo.match_source || 'manual',
      compatibility_score: matchInfo.compatibility_score,
      match_type: matchInfo.match_type
    })
    
    console.log('[PrivateChat] startChat 返回结果:', result)
    
    const chatId = result?.chat_id || result?.id
    const targetUser = result?.target_user
    
    if (!chatId) {
      console.error('[PrivateChat] 无法获取聊天ID，返回结果:', result)
      ElMessage.error('创建聊天失败，请稍后重试')
      return
    }
    
    activeChatId.value = chatId
    
    ElMessage.success('聊天会话已创建')
    
    await loadChatList()
    
    let newChat = chatList.value.find(c => c.chat_id === chatId)
    
    if (!newChat) {
      const targetUserIdFromResult = targetUser?.id || 
        (result.target_user_id ? parseInt(result.target_user_id) : null) ||
        targetUserId
      
      newChat = {
        chat_id: chatId,
        chat_identifier: result.chat_identifier,
        target_user: targetUser || {
          id: targetUserIdFromResult || targetUserId,
          name: '用户'
        },
        compatibility_score: matchInfo.compatibility_score,
        match_type: matchInfo.match_type,
        unread_count: 0,
        created_at: new Date().toISOString()
      }
    }
    
    if (newChat) {
      activeChat.value = newChat
      await loadMessages(chatId, true)
    }
    
  } catch (error) {
    console.error('[PrivateChat] 创建聊天失败:', error)
    ElMessage.error('创建聊天失败，请稍后重试')
  }
}

const initFromRoute = async () => {
  console.log('[PrivateChat] initFromRoute 被调用，route.query:', route.query)
  
  const targetUserIdParam = route.query.target_user_id
  const compatibilityScore = route.query.compatibility_score ? parseInt(route.query.compatibility_score) : null
  const matchType = route.query.match_type
  const matchSource = route.query.match_source
  
  if (!targetUserIdParam) {
    console.log('[PrivateChat] 没有 target_user_id 参数，跳过初始化')
    return
  }
  
  const targetUserId = parseInt(targetUserIdParam)
  
  if (isNaN(targetUserId) || targetUserId <= 0) {
    console.error('[PrivateChat] 无效的 target_user_id:', targetUserIdParam)
    ElMessage.warning('无效的用户信息')
    return
  }
  
  console.log(`[PrivateChat] 准备创建聊天，目标用户ID: ${targetUserId}`)
  
  await startChatWithTarget(targetUserId, {
    compatibility_score: compatibilityScore,
    match_type: matchType,
    match_source: matchSource
  })
}

onMounted(async () => {
  console.log('[PrivateChat] onMounted 被调用')
  
  await loadChatList()
  await initFromRoute()
})

watch(() => route.query, async (newQuery) => {
  console.log('[PrivateChat] route.query 变化:', newQuery)
  if (newQuery.target_user_id) {
    await initFromRoute()
  }
}, { deep: true })

defineExpose({
  startChatWithTarget
})
</script>

<style lang="scss" scoped>
.private-chat-container {
  height: 100%;
  width: 100%;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #2d1b69 100%);
  overflow: hidden;
}

.chat-layout {
  display: flex;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  overflow: hidden;
}

.chat-sidebar {
  width: 320px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.unread-badge {
  background: #ef4444;
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.chat-list-scroll {
  flex: 1;
  overflow-y: auto;
}

.empty-chats, .loading-chats {
  padding: 60px 20px;
  text-align: center;
  color: #94a3b8;
  
  p {
    margin-top: 12px;
    font-size: 14px;
  }
  
  .hint {
    color: #64748b;
    font-size: 12px;
    margin-top: 8px;
  }
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chat-list {
  padding: 8px 0;
}

.chat-item {
  display: flex;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
  
  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.15);
    border-left-color: #8b5cf6;
  }
}

.chat-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
}

.avatar-icon {
  font-size: 24px;
}

.chat-info {
  flex: 1;
  min-width: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}

.chat-name {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 14px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-time {
  font-size: 11px;
  color: #64748b;
  flex-shrink: 0;
}

.chat-preview-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-preview {
  font-size: 12px;
  color: #94a3b8;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-preview-empty {
  font-size: 12px;
  color: #64748b;
  font-style: italic;
}

.chat-unread {
  background: #ef4444;
  color: white;
  font-size: 11px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  margin-left: 8px;
  flex-shrink: 0;
}

.chat-match-info {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 11px;
}

.match-score {
  color: #94a3b8;
  
  strong {
    color: #22c55e;
    margin-left: 4px;
  }
}

.match-type {
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.1);
}

.chat-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  
  h2 {
    margin: 20px 0 10px;
    color: #e2e8f0;
    font-size: 20px;
  }
  
  p {
    color: #64748b;
    margin-bottom: 20px;
  }
}

.chat-main-header {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-details {
  display: flex;
  flex-direction: column;
}

.header-name {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 16px;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #22c55e;
  margin-top: 2px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  
  &.online {
    box-shadow: 0 0 6px #22c55e;
  }
}

.header-actions {
  display: flex;
  align-items: center;
}

.header-match {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(139, 92, 246, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
}

.match-label {
  font-size: 12px;
  color: #94a3b8;
}

.match-value {
  font-size: 16px;
  font-weight: bold;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.loading-messages, .loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #64748b;
  font-size: 14px;
}

.empty-messages {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #64748b;
  
  p {
    margin-top: 12px;
  }
  
  .hint {
    font-size: 12px;
    color: #475569;
    margin-top: 8px;
  }
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 10px;
  
  &.is-me {
    flex-direction: row-reverse;
    
    .message-content {
      align-items: flex-end;
    }
    
    .message-bubble {
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
      color: white;
      border-radius: 16px 4px 16px 16px;
    }
  }
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-icon-small {
  font-size: 18px;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 4px 16px 16px 16px;
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-time {
  font-size: 11px;
  color: #475569;
  margin-top: 4px;
  
  .read-status {
    color: #22c55e;
    margin-left: 8px;
  }
}

.chat-input-area {
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-hint {
  font-size: 11px;
  color: #475569;
}

:deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
  resize: none;
  
  &:focus, &:hover {
    border-color: rgba(139, 92, 246, 0.5);
    background: rgba(255, 255, 255, 0.08);
  }
  
  &::placeholder {
    color: #475569;
  }
}
</style>
