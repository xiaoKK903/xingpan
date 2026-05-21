<template>
  <div class="time-capsule-detail-page">
    <div class="page-back" @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      <span>返回列表</span>
    </div>

    <div v-if="loading" class="loading-container">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span class="loading-text">加载中...</span>
    </div>

    <div v-else-if="!capsule" class="empty-state">
      <div class="empty-icon">❓</div>
      <h3 class="empty-title">胶囊不存在</h3>
      <p class="empty-desc">该胶囊可能已被删除或您没有权限查看</p>
      <el-button type="primary" @click="goBack">返回列表</el-button>
    </div>

    <div v-else class="detail-content" :class="'skin-' + capsule.skin_key">
      <div class="capsule-header">
        <div class="capsule-preview">
          <span class="capsule-emoji">{{ getSkinEmoji(capsule.skin_key) }}</span>
        </div>
        <div class="capsule-info">
          <h1 class="capsule-title">{{ capsule.title }}</h1>
          <div class="capsule-meta">
            <div class="meta-row">
              <span class="meta-item">
                <el-icon><User /></el-icon>
                <span v-if="capsule.recipient_type === 'self'">写给未来的自己</span>
                <span v-else>写给: {{ capsule.recipient_username || '好友' }}</span>
              </span>
              <span class="meta-item">
                <el-icon><Calendar /></el-icon>
                封存时间: {{ formatDate(capsule.created_at) }}
              </span>
            </div>
            <div class="meta-row">
              <span class="meta-item">
                <el-icon><Clock /></el-icon>
                解锁时间: {{ formatDate(capsule.unlock_at) }}
              </span>
              <el-tag :type="getStatusTagType(capsule.status)" size="large">
                {{ getStatusText(capsule.status, capsule.is_unlocked) }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <div class="capsule-body">
        <div v-if="!capsule.is_unlocked && !capsule.is_opened" class="locked-overlay">
          <div class="locked-content">
            <div class="locked-icon">
              <el-icon size="64"><Lock /></el-icon>
            </div>
            <h2 class="locked-title">时间胶囊尚未开启</h2>
            <p class="locked-desc">
              这颗胶囊将在 <strong>{{ formatDate(capsule.unlock_at) }}</strong> 自动开启
            </p>
            <div class="countdown" v-if="daysRemaining > 0">
              <div class="countdown-item">
                <span class="countdown-value">{{ daysRemaining }}</span>
                <span class="countdown-label">天</span>
              </div>
              <div class="countdown-item">
                <span class="countdown-value">{{ hoursRemaining }}</span>
                <span class="countdown-label">小时</span>
              </div>
              <div class="countdown-item">
                <span class="countdown-value">{{ minutesRemaining }}</span>
                <span class="countdown-label">分钟</span>
              </div>
            </div>
            <div class="locked-hint">
              <el-icon><ChatDotSquare /></el-icon>
              请耐心等待，时间会证明一切的价值
            </div>
          </div>
        </div>

        <div v-else class="capsule-content-wrapper">
          <div class="content-header">
            <h3 class="content-title">
              <el-icon><Document /></el-icon>
              胶囊内容
            </h3>
            <div v-if="!capsule.is_opened" class="open-hint">
              <el-button type="primary" @click="openCapsule">
                <el-icon><Unlock /></el-icon>
                打开胶囊
              </el-button>
            </div>
          </div>
          
          <div class="capsule-content">
            <div class="content-text">{{ capsule.content }}</div>
          </div>

          <div v-if="capsule.is_opened" class="opened-info">
            <el-icon><CircleCheck /></el-icon>
            <span>已于 {{ formatDate(capsule.opened_at) }} 打开</span>
          </div>
        </div>
      </div>

      <div class="capsule-actions" v-if="capsule.status === 'pending' && !capsule.is_unlocked">
        <el-button type="primary" @click="editCapsule">
          <el-icon><Edit /></el-icon>
          编辑胶囊
        </el-button>
        <el-button type="danger" @click="showDeleteDialog = true">
          <el-icon><Delete /></el-icon>
          删除胶囊
        </el-button>
      </div>

      <div v-if="capsule.sender_info" class="sender-info">
        <el-divider />
        <div class="sender-section">
          <h4 class="section-title">发送者信息</h4>
          <div class="sender-card">
            <div class="sender-avatar">
              <el-icon size="32"><UserFilled /></el-icon>
            </div>
            <div class="sender-details">
              <div class="sender-name">{{ capsule.sender_info.username }}</div>
              <div class="sender-time">于 {{ formatDate(capsule.created_at) }} 封存</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showDeleteDialog"
      title="确认删除"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="delete-dialog-content">
        <el-icon class="warning-icon"><Warning /></el-icon>
        <p>确定要删除这个时间胶囊吗？</p>
        <p class="delete-hint">删除后将无法恢复，且会释放一个胶囊配额。</p>
      </div>
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete" :loading="deleting">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, Loading, Lock, Unlock, User, Calendar, 
  Clock, Edit, Delete, Warning, ChatDotSquare, 
  Document, CircleCheck, UserFilled
} from '@element-plus/icons-vue'
import { timeCapsuleApi } from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const deleting = ref(false)
const opening = ref(false)
const capsule = ref(null)
const showDeleteDialog = ref(false)

const countdownTimer = ref(null)
const daysRemaining = ref(0)
const hoursRemaining = ref(0)
const minutesRemaining = ref(0)

const skinEmojis = {
  'classic_star': '⭐',
  'nebula_pink': '💗',
  'ocean_blue': '💙',
  'sunset_gold': '🌟',
  'cosmic_vip': '🌌',
  'aurora_vip': '🌈',
  'crystal_premium': '💎',
  'phoenix_legend': '🔥'
}

function getSkinEmoji(skinKey) {
  return skinEmojis[skinKey] || '⭐'
}

function getStatusTagType(status) {
  const types = {
    'pending': 'info',
    'unlocked': 'success',
    'opened': 'success',
    'expired': 'warning'
  }
  return types[status] || 'info'
}

function getStatusText(status, isUnlocked) {
  if (status === 'pending' && isUnlocked) {
    return '已开启'
  }
  const texts = {
    'pending': '未开启',
    'unlocked': '已开启',
    'opened': '已查看',
    'expired': '已过期'
  }
  return texts[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function updateCountdown() {
  if (!capsule.value || capsule.value.is_unlocked) {
    return
  }
  
  const now = new Date()
  const unlockAt = new Date(capsule.value.unlock_at)
  const diff = unlockAt - now
  
  if (diff <= 0) {
    daysRemaining.value = 0
    hoursRemaining.value = 0
    minutesRemaining.value = 0
    return
  }
  
  daysRemaining.value = Math.floor(diff / (1000 * 60 * 60 * 24))
  hoursRemaining.value = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  minutesRemaining.value = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
}

async function loadCapsule() {
  const capsuleId = route.params.id
  if (!capsuleId) {
    ElMessage.error('胶囊ID无效')
    router.push('/time-capsule')
    return
  }
  
  loading.value = true
  try {
    const response = await timeCapsuleApi.getDetail(capsuleId)
    if (response && response.capsule) {
      capsule.value = response.capsule
    } else {
      capsule.value = response
    }
    updateCountdown()
  } catch (error) {
    console.error('加载胶囊详情失败:', error)
    ElMessage.error('胶囊不存在或您没有权限查看')
  } finally {
    loading.value = false
  }
}

async function openCapsule() {
  if (!capsule.value) return
  
  opening.value = true
  try {
    await timeCapsuleApi.open(capsule.value.id)
    capsule.value.is_opened = true
    capsule.value.opened_at = new Date().toISOString()
    ElMessage.success('胶囊已打开！请仔细阅读这份来自过去的心意')
  } catch (error) {
    console.error('打开胶囊失败:', error)
    ElMessage.error('打开胶囊失败，请稍后重试')
  } finally {
    opening.value = false
  }
}

function editCapsule() {
  if (!capsule.value) return
  router.push(`/time-capsule/edit/${capsule.value.id}`)
}

async function confirmDelete() {
  if (!capsule.value) return
  
  deleting.value = true
  try {
    await timeCapsuleApi.delete(capsule.value.id)
    ElMessage.success('胶囊已删除')
    router.push('/time-capsule')
  } catch (error) {
    console.error('删除胶囊失败:', error)
    ElMessage.error('删除胶囊失败，请稍后重试')
  } finally {
    deleting.value = false
    showDeleteDialog.value = false
  }
}

function goBack() {
  router.push('/time-capsule')
}

onMounted(() => {
  loadCapsule()
  
  countdownTimer.value = setInterval(() => {
    updateCountdown()
  }, 60000)
})

onUnmounted(() => {
  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
  }
})
</script>

<style lang="scss" scoped>
.time-capsule-detail-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  margin-bottom: 20px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    color: #a78bfa;
  }
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  
  .loading-icon {
    font-size: 2.5rem;
    color: #8b5cf6;
    animation: spin 1s linear infinite;
  }
  
  .loading-text {
    margin-top: 16px;
    color: rgba(255, 255, 255, 0.5);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  text-align: center;
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: 20px;
  }
  
  .empty-title {
    margin: 0 0 12px;
    font-size: 1.3rem;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .empty-desc {
    margin: 0 0 24px;
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.detail-content {
  background: linear-gradient(145deg, rgba(30, 30, 60, 0.95), rgba(20, 20, 50, 0.98));
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(139, 92, 246, 0.1);
}

.capsule-header {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  padding: 32px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(99, 102, 241, 0.1));
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.capsule-preview {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.25));
  border: 2px solid rgba(139, 92, 246, 0.4);
  flex-shrink: 0;
}

.capsule-emoji {
  font-size: 2.5rem;
}

.capsule-info {
  flex: 1;
  min-width: 0;
  
  .capsule-title {
    margin: 0 0 16px;
    font-size: 1.5rem;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.95);
  }
  
  .capsule-meta {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
    
    strong {
      color: rgba(255, 255, 255, 0.9);
      font-weight: 500;
    }
  }
}

.capsule-body {
  position: relative;
  min-height: 300px;
}

.locked-overlay {
  position: relative;
  padding: 60px 40px;
  background: linear-gradient(135deg, rgba(20, 20, 50, 0.9), rgba(15, 15, 35, 0.95));
}

.locked-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.locked-icon {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.15));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  color: #8b5cf6;
  animation: pulse-lock 2s ease-in-out infinite;
}

@keyframes pulse-lock {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.3);
  }
  50% {
    box-shadow: 0 0 0 20px rgba(139, 92, 246, 0);
  }
}

.locked-title {
  margin: 0 0 12px;
  font-size: 1.4rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.locked-desc {
  margin: 0 0 32px;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
  
  strong {
    color: #a78bfa;
    font-weight: 600;
  }
}

.countdown {
  display: flex;
  gap: 20px;
  margin-bottom: 32px;
}

.countdown-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.15));
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  min-width: 80px;
}

.countdown-value {
  font-size: 2rem;
  font-weight: 700;
  color: #a78bfa;
}

.countdown-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.locked-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 8px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
}

.capsule-content-wrapper {
  padding: 32px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.content-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.open-hint {
  .el-button {
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border: none;
    font-weight: 600;
    
    &:hover {
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
    }
  }
}

.capsule-content {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(99, 102, 241, 0.03));
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.content-text {
  font-size: 1.05rem;
  line-height: 2;
  color: rgba(255, 255, 255, 0.85);
  white-space: pre-wrap;
  word-break: break-word;
}

.opened-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  padding: 12px 16px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 8px;
  color: rgba(34, 197, 94, 0.8);
  font-size: 0.9rem;
}

.capsule-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  background: rgba(139, 92, 246, 0.05);
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.sender-info {
  padding: 0 32px 32px;
  
  :deep(.el-divider) {
    --el-border-color: rgba(139, 92, 246, 0.15);
  }
}

.sender-section {
  .section-title {
    margin: 0 0 16px;
    font-size: 1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }
}

.sender-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.sender-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.sender-details {
  .sender-name {
    font-size: 1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 4px;
  }
  
  .sender-time {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.delete-dialog-content {
  text-align: center;
  
  .warning-icon {
    font-size: 3rem;
    color: #f59e0b;
    margin-bottom: 16px;
  }
  
  p {
    margin: 8px 0;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .delete-hint {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.skin-classic_star {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.2));
    border-color: rgba(251, 191, 36, 0.4);
  }
}

.skin-nebula_pink {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(219, 39, 119, 0.2));
    border-color: rgba(236, 72, 153, 0.4);
  }
}

.skin-ocean_blue {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(37, 99, 235, 0.2));
    border-color: rgba(59, 130, 246, 0.4);
  }
}

.skin-sunset_gold {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(251, 146, 60, 0.3), rgba(249, 115, 22, 0.2));
    border-color: rgba(251, 146, 60, 0.4);
  }
}

.skin-cosmic_vip {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(99, 102, 241, 0.35));
    border-color: rgba(139, 92, 246, 0.5);
  }
}

.skin-aurora_vip {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.35), rgba(59, 130, 246, 0.3));
    border-color: rgba(34, 197, 94, 0.45);
  }
}

.skin-crystal_premium {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(147, 197, 253, 0.4), rgba(196, 181, 253, 0.35));
    border-color: rgba(147, 197, 253, 0.5);
  }
}

.skin-phoenix_legend {
  .capsule-preview {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.4), rgba(251, 146, 60, 0.35));
    border-color: rgba(239, 68, 68, 0.5);
  }
}

@media (max-width: 768px) {
  .time-capsule-detail-page {
    padding: 16px;
  }
  
  .capsule-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 24px 20px;
  }
  
  .meta-row {
    justify-content: center;
  }
  
  .countdown {
    gap: 12px;
  }
  
  .countdown-item {
    padding: 12px 16px;
    min-width: 60px;
  }
  
  .countdown-value {
    font-size: 1.5rem;
  }
  
  .capsule-content-wrapper {
    padding: 20px 16px;
  }
  
  .content-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>
