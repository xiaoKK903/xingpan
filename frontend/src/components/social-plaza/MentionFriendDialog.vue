<template>
  <el-dialog 
    v-model="visible" 
    title="@好友，邀请一起合盘" 
    width="420px"
    class="mention-dialog"
  >
    <div class="dialog-content">
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索好友..."
          prefix-icon="Search"
          clearable
          @input="handleSearch"
          class="search-input"
        />
      </div>
      
      <div class="friends-list" v-if="filteredFriends.length > 0">
        <div 
          v-for="friend in filteredFriends" 
          :key="friend.id"
          class="friend-item" 
          :class="{ selected: selectedFriend?.id === friend.id }"
          @click="selectFriend(friend)"
        >
          <div class="avatar">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="info">
            <div class="username-row">
              <span class="username">{{ friend.username }}</span>
              <VIPBadge 
                v-if="friend.is_vip" 
                :is-vip="true" 
                :show-text="false" 
                size="small" 
              />
            </div>
            <span class="user-desc">{{ friend.desc || '一起探索星辰大海 ✨' }}</span>
          </div>
          <div v-if="selectedFriend?.id === friend.id" class="check-icon">
            <el-icon :size="20"><CircleCheckFilled /></el-icon>
          </div>
        </div>
      </div>
      
      <div class="empty-state" v-else-if="!searching">
        <div class="empty-icon">🔍</div>
        <span class="empty-text">{{ searchQuery ? '未找到匹配的好友' : '搜索想要邀请的好友' }}</span>
      </div>
      
      <div class="loading-state" v-else>
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>搜索中...</span>
      </div>
      
      <div class="message-section" v-if="selectedFriend">
        <div class="section-label">邀请留言（可选）</div>
        <el-input
          v-model="message"
          type="textarea"
          placeholder="写下你的邀请语..."
          :rows="2"
          maxlength="100"
          show-word-limit
          class="message-input"
        />
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="submitting"
          :disabled="!selectedFriend"
          @click="handleSend"
        >
          发送邀请 ✨
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { debounce } from '@/utils/util'
import { Search, UserFilled, CircleCheckFilled, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { socialPlazaApi } from '@/api'
import VIPBadge from '@/components/VIPBadge.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  postId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'sent'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const searchQuery = ref('')
const searching = ref(false)
const selectedFriend = ref(null)
const message = ref('')
const submitting = ref(false)

const friends = ref([
  { id: 1, username: '星光漫步', is_vip: true, desc: '喜欢研究合盘的星友' },
  { id: 2, username: '月亮少女', is_vip: false, desc: '每天看运势的小能手' },
  { id: 3, username: '占星师Leo', is_vip: true, desc: '专业占星爱好者' },
  { id: 4, username: '星星点灯', is_vip: false, desc: '一起探索星辰大海' },
  { id: 5, username: '星座控', is_vip: false, desc: '十二星座都喜欢' },
])

const filteredFriends = computed(() => {
  if (!searchQuery.value) return friends.value
  const query = searchQuery.value.toLowerCase()
  return friends.value.filter(f => 
    f.username.toLowerCase().includes(query)
  )
})

watch(visible, (val) => {
  if (val) {
    resetForm()
  }
})

function resetForm() {
  searchQuery.value = ''
  selectedFriend.value = null
  message.value = ''
}

const handleSearch = debounce(() => {
  searching.value = true
  setTimeout(() => {
    searching.value = false
  }, 300)
}, 200)

function selectFriend(friend) {
  if (selectedFriend.value?.id === friend.id) {
    selectedFriend.value = null
  } else {
    selectedFriend.value = friend
  }
}

async function handleSend() {
  if (!selectedFriend.value) {
    ElMessage.warning('请选择要邀请的好友')
    return
  }
  
  try {
    submitting.value = true
    
    const data = {
      invitee_id: selectedFriend.value.id,
      invitation_type: 'synastry',
      message: message.value || null
    }
    
    await socialPlazaApi.createMention(props.postId, data)
    
    ElMessage.success(`已向 ${selectedFriend.value.username} 发送邀请！`)
    emit('sent')
    visible.value = false
    
  } catch (error) {
    console.error('发送邀请失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
:deep(.mention-dialog .el-dialog) {
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.98) 0%, rgba(12, 12, 35, 0.98) 100%);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

:deep(.mention-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  padding: 20px 24px;
  margin-right: 0;
}

:deep(.mention-dialog .el-dialog__title) {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 600;
}

.dialog-content {
  padding: 16px 0;
}

.search-section {
  margin-bottom: 16px;
}

.search-input {
  :deep(.el-input__wrapper) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    box-shadow: none;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &.is-focus {
      border-color: rgba(139, 92, 246, 0.5);
    }
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9);
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

.friends-list {
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.friend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
  }
  
  &.selected {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.1));
    border: 1px solid rgba(139, 92, 246, 0.3);
  }
}

.friend-item .avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.friend-item .info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.username-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.user-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.check-icon {
  color: #4ade80;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
  color: rgba(255, 255, 255, 0.5);
}

.empty-icon {
  font-size: 36px;
}

.empty-text {
  font-size: 14px;
}

.loading-icon {
  font-size: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.section-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.message-section {
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.message-input {
  :deep(.el-textarea__inner) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    color: rgba(255, 255, 255, 0.9);
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.mention-dialog .el-dialog__footer) {
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  padding-top: 16px;
}
</style>
