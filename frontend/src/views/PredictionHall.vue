<template>
  <div class="prediction-hall">
    <div class="stars-bg">
      <div v-for="i in 80" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="hall-main">
      <div class="quick-nav">
        <div class="nav-item" @click="goToResonance">
          <span class="nav-icon">🌌</span>
          <span class="nav-text">星能共鸣池</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item active">
          <span class="nav-icon">🏛️</span>
          <span class="nav-text">预言家礼堂</span>
          <span class="nav-arrow">→</span>
        </div>
      </div>

      <div class="hall-header">
        <div class="header-icon">
          <el-icon size="40"><Trophy /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="main-title">预言家礼堂</h1>
          <p class="subtitle">每日竞猜 · 赢取高阶星尘奖励</p>
        </div>
        <div class="user-assets" v-if="userAssets">
          <div class="asset-item">
            <span class="asset-icon">⭐</span>
            <span class="asset-value">{{ userAssets.stardust_point || 0 }}</span>
            <span class="asset-label">高阶星尘</span>
          </div>
          <div class="asset-item">
            <span class="asset-icon">💎</span>
            <span class="asset-value">{{ userAssets.stardust_fragment || 0 }}</span>
            <span class="asset-label">星元碎片</span>
          </div>
          <div class="asset-item">
            <span class="asset-icon">🎫</span>
            <span class="asset-value">{{ userTickets || 0 }}</span>
            <span class="asset-label">预言券</span>
          </div>
        </div>
      </div>

      <div class="tab-section">
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'open' }"
          @click="activeTab = 'open'"
        >
          <span class="tab-icon">🎯</span>
          <span class="tab-text">开放投票</span>
          <span class="tab-badge" v-if="openSessions.length > 0">{{ openSessions.length }}</span>
        </div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'upcoming' }"
          @click="activeTab = 'upcoming'"
        >
          <span class="tab-icon">📅</span>
          <span class="tab-text">即将开始</span>
          <span class="tab-badge" v-if="upcomingSessions.length > 0">{{ upcomingSessions.length }}</span>
        </div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'history' }"
          @click="activeTab = 'history'"
        >
          <span class="tab-icon">📊</span>
          <span class="tab-text">历史记录</span>
        </div>
      </div>

      <div class="sessions-section">
        <div class="open-sessions" v-if="activeTab === 'open'">
          <div v-if="loading" class="loading-section">
            <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
            <p class="loading-text">加载中...</p>
          </div>
          
          <div v-else-if="openSessions.length === 0" class="empty-section">
            <div class="empty-icon">🎪</div>
            <p class="empty-text">当前没有开放的投票场次</p>
            <p class="empty-hint">请关注即将开始的场次</p>
          </div>
          
          <div v-else class="sessions-grid">
            <div 
              v-for="session in openSessions" 
              :key="session.id"
              class="session-card voting"
              @click="goToDetail(session.id)"
            >
              <div class="card-header">
                <div class="session-type">
                  <span class="type-badge" :class="session.session_type">
                    {{ getSessionTypeLabel(session.session_type) }}
                  </span>
                </div>
                <div class="countdown">
                  <el-icon><Timer /></el-icon>
                  <span>剩余: {{ getCountdown(session) }}</span>
                </div>
              </div>
              
              <div class="card-body">
                <h3 class="session-title">{{ session.title }}</h3>
                <p class="session-desc">{{ session.description }}</p>
                
                <div class="session-stats">
                  <div class="stat-item">
                    <span class="stat-icon">👥</span>
                    <span class="stat-value">{{ session.total_votes || 0 }}</span>
                    <span class="stat-label">人已投票</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-icon">🏆</span>
                    <span class="stat-value">{{ session.base_reward_amount || 10 }}</span>
                    <span class="stat-label">{{ getAssetLabel(session.reward_asset_type) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="card-footer">
                <span class="enter-btn">
                  立即投票
                  <el-icon><ArrowRight /></el-icon>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="upcoming-sessions" v-if="activeTab === 'upcoming'">
          <div v-if="loading" class="loading-section">
            <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
            <p class="loading-text">加载中...</p>
          </div>
          
          <div v-else-if="upcomingSessions.length === 0" class="empty-section">
            <div class="empty-icon">📭</div>
            <p class="empty-text">暂无即将开始的场次</p>
            <p class="empty-hint">请稍后再来查看</p>
          </div>
          
          <div v-else class="sessions-grid">
            <div 
              v-for="session in upcomingSessions" 
              :key="session.id"
              class="session-card upcoming"
            >
              <div class="card-header">
                <div class="session-type">
                  <span class="type-badge upcoming">
                    即将开始
                  </span>
                </div>
                <div class="start-time">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDateTime(session.voting_starts_at) }}</span>
                </div>
              </div>
              
              <div class="card-body">
                <h3 class="session-title">{{ session.title }}</h3>
                <p class="session-desc">{{ session.description }}</p>
                
                <div class="session-reward">
                  <span class="reward-label">奖励预览:</span>
                  <span class="reward-value">
                    {{ session.base_reward_amount || 10 }} {{ getAssetLabel(session.reward_asset_type) }}
                  </span>
                </div>
              </div>
              
              <div class="card-footer">
                <span class="notify-btn">
                  <el-icon><Bell /></el-icon>
                  开始时通知我
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="history-section" v-if="activeTab === 'history'">
          <div v-if="loadingHistory" class="loading-section">
            <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
            <p class="loading-text">加载历史记录...</p>
          </div>
          
          <div v-else-if="voteHistory.length === 0" class="empty-section">
            <div class="empty-icon">📜</div>
            <p class="empty-text">您还没有参与过投票</p>
            <p class="empty-hint">去参与开放的投票场次吧</p>
          </div>
          
          <div v-else class="history-list">
            <div 
              v-for="(record, index) in voteHistory" 
              :key="index"
              class="history-item"
              @click="handleHistoryClick(record)"
            >
              <div class="history-left">
                <div class="status-icon" :class="getVoteStatusClass(record)">
                  {{ getVoteStatusIcon(record) }}
                </div>
                <div class="history-info">
                  <h4 class="history-title">{{ record.prediction?.title || '未知场次' }}</h4>
                  <p class="history-detail">
                    选择: <span class="option-text">{{ record.vote?.selected_option || '-' }}</span>
                    <span class="vote-time">{{ formatDate(record.vote?.created_at) }}</span>
                  </p>
                </div>
              </div>
              
              <div class="history-right">
                <div class="result-badge" :class="getResultClass(record)">
                  {{ getResultText(record) }}
                </div>
                <div class="reward-info" v-if="record.vote?.is_correct">
                  <span v-if="record.vote?.reward_claimed" class="claimed">
                    已领取: +{{ record.vote?.reward_earned || 0 }}
                  </span>
                  <span v-else class="unclaimed" @click.stop="claimReward(record.vote?.id)">
                    点击领取
                    <el-icon><Coin /></el-icon>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Trophy, Timer, ArrowRight, Calendar, Bell, Loading, Coin } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { predictionApi, starResonanceApi } from '@/api'

const router = useRouter()

const activeTab = ref('open')
const loading = ref(false)
const loadingHistory = ref(false)

const openSessions = ref([])
const upcomingSessions = ref([])
const voteHistory = ref([])

const userAssets = ref(null)
const userTickets = ref(0)

function getStarStyle(index) {
  const size = Math.random() * 2 + 1
  return {
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${Math.random() * 3}s`,
    opacity: Math.random() * 0.5 + 0.2
  }
}

function getSessionTypeLabel(type) {
  const labels = {
    daily: '每日场次',
    weekly: '每周场次',
    special: '特殊场次',
    festival: '节日活动',
    brand: '品牌联名'
  }
  return labels[type] || type
}

function getAssetLabel(type) {
  const labels = {
    fragment: '星元碎片',
    point: '高阶星尘',
    ticket: '预言券'
  }
  return labels[type] || '奖励'
}

function getCountdown(session) {
  if (!session.voting_ends_at) return '--:--'
  
  const now = new Date()
  const end = new Date(session.voting_ends_at)
  const diff = end - now
  
  if (diff <= 0) return '已结束'
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  return `${minutes}分钟`
}

function formatDateTime(dateStr) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}月${day}日 ${hours}:${minutes}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function getVoteStatusClass(record) {
  if (!record.prediction?.is_resolved) return 'pending'
  if (record.vote?.is_correct) return 'correct'
  return 'incorrect'
}

function getVoteStatusIcon(record) {
  if (!record.prediction?.is_resolved) return '⏳'
  if (record.vote?.is_correct) return '✓'
  return '✗'
}

function getResultClass(record) {
  if (!record.prediction?.is_resolved) return 'pending'
  if (record.vote?.is_correct) return 'correct'
  return 'incorrect'
}

function getResultText(record) {
  if (!record.prediction?.is_resolved) return '待结算'
  if (record.vote?.is_correct) return '猜中了!'
  return '未猜中'
}

function goToResonance() {
  router.push('/star-resonance')
}

function goToDetail(predictionId) {
  router.push(`/prediction/detail/${predictionId}`)
}

function handleHistoryClick(record) {
  if (record.prediction?.is_resolved) {
    router.push(`/prediction/result/${record.prediction?.id}`)
  } else {
    router.push(`/prediction/detail/${record.prediction?.id}`)
  }
}

async function loadOpenSessions() {
  try {
    loading.value = true
    const result = await predictionApi.getOpen()
    openSessions.value = result.predictions || []
  } catch (error) {
    console.error('加载开放场次失败:', error)
    ElMessage.error('加载场次失败')
  } finally {
    loading.value = false
  }
}

async function loadUpcomingSessions() {
  try {
    loading.value = true
    const result = await predictionApi.getUpcoming()
    upcomingSessions.value = result.predictions || []
  } catch (error) {
    console.error('加载即将开始场次失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  try {
    loadingHistory.value = true
    const result = await predictionApi.getMyHistory()
    voteHistory.value = result.history || []
  } catch (error) {
    console.error('加载历史记录失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

async function loadUserAssets() {
  try {
    const result = await starResonanceApi.getPoolStatus()
    
    userAssets.value = {
      stardust_point: result.user_assets?.stardust_point_balance || 
                      result.user_assets?.stardust_point || 0,
      stardust_fragment: result.user_assets?.stardust_fragment_balance || 
                         result.user_assets?.stardust_fragment || 0
    }
    
    try {
      const ticketsResult = await starResonanceApi.getMyTickets()
      userTickets.value = ticketsResult.tickets?.length || 0
    } catch (e) {
      console.warn('加载预言券失败:', e)
      userTickets.value = 0
    }
  } catch (error) {
    console.error('加载用户资产失败:', error)
    userAssets.value = {
      stardust_point: 0,
      stardust_fragment: 0
    }
  }
}

async function claimReward(voteId) {
  if (!voteId) return
  
  try {
    await ElMessageBox.confirm(
      '确定要领取奖励吗？',
      '领取确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认框错误:', error)
    }
    return
  }
  
  try {
    const result = await predictionApi.claimReward(voteId)
    
    if (result.success === false) {
      throw new Error(result.error || result.error_message || '领取失败')
    }
    
    const rewardAmount = result.reward_amount || 0
    const assetType = result.reward_asset_type === 'point' ? '高阶星尘' : 
                     result.reward_asset_type === 'fragment' ? '星元碎片' : '预言券'
    
    ElMessage.success({
      message: `领取成功！\n获得 ${rewardAmount} ${assetType}`,
      duration: 3000
    })
    
    await Promise.all([
      loadHistory(),
      loadUserAssets()
    ])
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('领取奖励失败:', error)
      
      let errorMessage = error.message || '领取失败'
      
      if (errorMessage.includes('ALREADY_CLAIMED') || errorMessage.includes('已领取')) {
        errorMessage = '该奖励已领取'
      } else if (errorMessage.includes('NOT_CORRECT') || errorMessage.includes('未猜中')) {
        errorMessage = '未猜中场次，无法领取奖励'
      } else if (errorMessage.includes('NOT_RESOLVED') || errorMessage.includes('未结算')) {
        errorMessage = '场次尚未结算，无法领取奖励'
      }
      
      ElMessage.error({
        message: errorMessage,
        duration: 3000
      })
    }
  }
}

function refreshData() {
  Promise.all([
    loadOpenSessions(),
    loadUpcomingSessions(),
    loadHistory(),
    loadUserAssets()
  ])
}

watch(activeTab, (newTab) => {
  if (newTab === 'open' && openSessions.value.length === 0) {
    loadOpenSessions()
  } else if (newTab === 'upcoming' && upcomingSessions.value.length === 0) {
    loadUpcomingSessions()
  } else if (newTab === 'history' && voteHistory.value.length === 0) {
    loadHistory()
  }
})

onMounted(() => {
  refreshData()
})
</script>

<style lang="scss" scoped>
.prediction-hall {
  min-height: 100vh;
  width: 100%;
  position: relative;
  background: linear-gradient(135deg, #0a0a2a 0%, #1a1a4a 50%, #0f0f3a 100%);
  overflow-x: hidden;
}

.stars-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle 3s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.hall-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.quick-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  
  .nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(.active) {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &.active {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%);
      border-color: rgba(139, 92, 246, 0.4);
    }
  }
  
  .nav-icon {
    font-size: 18px;
  }
  
  .nav-text {
    font-size: 14px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.75);
  }
  
  .nav-arrow {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.hall-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(15, 15, 40, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  
  .header-icon {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(239, 68, 68, 0.2) 100%);
    border-radius: 16px;
    color: #FBBF24;
  }
  
  .header-text {
    flex: 1;
    
    .main-title {
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 50%, #EF4444 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0 0 4px 0;
    }
    
    .subtitle {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
  }
  
  .user-assets {
    display: flex;
    gap: 20px;
    
    .asset-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      
      .asset-icon {
        font-size: 20px;
      }
      
      .asset-value {
        font-size: 18px;
        font-weight: 700;
        color: #FBBF24;
      }
      
      .asset-label {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
      }
    }
  }
}

.tab-section {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  
  .tab-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(139, 92, 246, 0.1);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    
    &:hover:not(.active) {
      background: rgba(139, 92, 246, 0.08);
    }
    
    &.active {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%);
      border-color: rgba(139, 92, 246, 0.3);
      
      .tab-text {
        color: #a78bfa;
        font-weight: 600;
      }
    }
  }
  
  .tab-icon {
    font-size: 18px;
  }
  
  .tab-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .tab-badge {
    padding: 2px 8px;
    background: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%);
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    color: #fff;
  }
}

.sessions-section {
  min-height: 400px;
}

.loading-section,
.empty-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 12px;
  
  .loading-icon {
    color: #8B5CF6;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .loading-text,
  .empty-text {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .empty-hint {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.4);
  }
  
  .empty-icon {
    font-size: 48px;
  }
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.session-card {
  background: rgba(15, 15, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 12px 40px rgba(139, 92, 246, 0.15);
  }
  
  &.voting {
    border-top: 3px solid #84CC16;
  }
  
  &.upcoming {
    border-top: 3px solid #3B82F6;
    opacity: 0.9;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: rgba(139, 92, 246, 0.05);
    border-bottom: 1px solid rgba(139, 92, 246, 0.08);
    
    .type-badge {
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 600;
      
      &.daily {
        background: rgba(132, 204, 22, 0.15);
        color: #84CC16;
      }
      
      &.weekly {
        background: rgba(59, 130, 246, 0.15);
        color: #3B82F6;
      }
      
      &.special {
        background: rgba(139, 92, 246, 0.15);
        color: #a78bfa;
      }
      
      &.upcoming {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
      }
    }
    
    .countdown,
    .start-time {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .card-body {
    padding: 16px;
    
    .session-title {
      font-size: 16px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
      margin: 0 0 8px 0;
    }
    
    .session-desc {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0 0 16px 0;
      line-height: 1.5;
    }
    
    .session-stats {
      display: flex;
      gap: 20px;
      
      .stat-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        .stat-icon {
          font-size: 14px;
        }
        
        .stat-value {
          font-size: 20px;
          font-weight: 700;
          color: #FBBF24;
        }
        
        .stat-label {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.4);
        }
      }
    }
    
    .session-reward {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px;
      background: rgba(251, 191, 36, 0.05);
      border-radius: 8px;
      
      .reward-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }
      
      .reward-value {
        font-size: 14px;
        font-weight: 600;
        color: #FBBF24;
      }
    }
  }
  
  .card-footer {
    padding: 12px 16px;
    background: rgba(139, 92, 246, 0.03);
    border-top: 1px solid rgba(139, 92, 246, 0.08);
    display: flex;
    justify-content: flex-end;
    
    .enter-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 13px;
      font-weight: 600;
      color: #8B5CF6;
      transition: all 0.2s ease;
      
      &:hover {
        color: #a78bfa;
      }
    }
    
    .notify-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      
      &:hover {
        color: #60a5fa;
      }
    }
  }
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .history-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: rgba(15, 15, 40, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(139, 92, 246, 0.1);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.2);
      background: rgba(15, 15, 40, 0.8);
    }
  }
  
  .history-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .status-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 10px;
      font-size: 18px;
      font-weight: bold;
      
      &.pending {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
      }
      
      &.correct {
        background: rgba(132, 204, 22, 0.15);
        color: #84CC16;
      }
      
      &.incorrect {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
      }
    }
    
    .history-info {
      .history-title {
        font-size: 15px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.85);
        margin: 0 0 4px 0;
      }
      
      .history-detail {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
        
        .option-text {
          color: #8B5CF6;
          font-weight: 500;
        }
        
        .vote-time {
          margin-left: 12px;
        }
      }
    }
  }
  
  .history-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
    
    .result-badge {
      padding: 4px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      
      &.pending {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
      }
      
      &.correct {
        background: rgba(132, 204, 22, 0.15);
        color: #84CC16;
      }
      
      &.incorrect {
        background: rgba(239, 68, 68, 0.1);
        color: rgba(255, 255, 255, 0.5);
      }
    }
    
    .reward-info {
      .claimed {
        font-size: 12px;
        color: #84CC16;
      }
      
      .unclaimed {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 12px;
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.2) 100%);
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        color: #FBBF24;
        cursor: pointer;
        transition: all 0.2s ease;
        
        &:hover {
          background: linear-gradient(135deg, rgba(251, 191, 36, 0.3) 0%, rgba(245, 158, 11, 0.3) 100%);
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .hall-main {
    padding: 16px;
  }
  
  .hall-header {
    flex-direction: column;
    align-items: flex-start;
    
    .user-assets {
      width: 100%;
      justify-content: space-around;
    }
  }
  
  .tab-section {
    overflow-x: auto;
    padding-bottom: 8px;
  }
  
  .sessions-grid {
    grid-template-columns: 1fr;
  }
  
  .history-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    
    .history-right {
      width: 100%;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
