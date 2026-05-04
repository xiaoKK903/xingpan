<template>
  <div class="leaderboards-container">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>
    
    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
    </div>

    <div class="leaderboards-main">
      <div class="leaderboards-header">
        <div class="header-icon">
          <el-icon size="36"><Trophy /></el-icon>
        </div>
        <h1 class="main-title">荣誉排行榜</h1>
        <p class="subtitle">登上榜单，获得限定荣誉奖励</p>
      </div>

      <div class="tabs-container">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane 
            v-for="board in boardConfigs" 
            :key="board.board_key" 
            :label="board.name"
            :name="board.board_key"
          >
            <template #label>
              <span class="tab-label">
                <span class="tab-icon">{{ getBoardIcon(board.board_key) }}</span>
                {{ board.name }}
              </span>
            </template>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="board-content" v-loading="loading">
        <div v-if="currentBoard" class="board-info">
          <div class="board-description">
            <p>{{ currentBoard.description || '查看排行榜排名，争夺限定荣誉奖励' }}</p>
          </div>
          
          <div class="my-rank-card" v-if="myRank">
            <div class="my-rank-header">
              <span class="my-rank-title">我的排名</span>
              <el-tag 
                :type="getRankTagType(myRank.rank)" 
                size="large"
                effect="dark"
              >
                {{ getRankDisplay(myRank.rank) }}
              </el-tag>
            </div>
            
            <div class="my-rank-info">
              <div class="info-item">
                <span class="info-label">分数</span>
                <span class="info-value">{{ myRank.score }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">累计</span>
                <span class="info-value">{{ myRank.entries_count }} 次上榜</span>
              </div>
            </div>
          </div>
        </div>

        <div class="rank-list">
          <div 
            v-for="(entry, index) in leaderboardData" 
            :key="entry.id || index"
            class="rank-item"
            :class="getRankItemClass(index)"
          >
            <div class="rank-position">
              <template v-if="index < 3">
                <div class="top-badge" :class="'top-' + (index + 1)">
                  <span class="badge-number">{{ index + 1 }}</span>
                  <div class="badge-glow"></div>
                </div>
              </template>
              <template v-else>
                <span class="rank-number">{{ index + 1 }}</span>
              </template>
            </div>
            
            <div class="user-info">
              <div class="user-avatar">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="user-details">
                <span class="username">{{ entry.username || '匿名用户' }}</span>
                <div class="user-badges">
                  <el-tag v-if="entry.is_vip" type="warning" size="small" effect="dark" class="vip-tag">
                    VIP
                  </el-tag>
                  <el-tag 
                    v-if="entry.rank_data?.title_name" 
                    type="primary" 
                    size="small" 
                    effect="plain"
                  >
                    {{ entry.rank_data.title_name }}
                  </el-tag>
                </div>
              </div>
            </div>
            
            <div class="score-info">
              <span class="score-value">{{ entry.score }}</span>
              <span class="score-label">{{ getScoreLabel(activeTab) }}</span>
            </div>
          </div>
          
          <el-empty v-if="!loading && leaderboardData.length === 0" description="暂无数据" />
        </div>

        <div class="rewards-section" v-if="currentRewards && currentRewards.length > 0">
          <div class="section-header">
            <span class="section-icon">🎁</span>
            <span class="section-title">上榜奖励</span>
          </div>
          <div class="rewards-grid">
            <div 
              v-for="(reward, index) in currentRewards" 
              :key="reward.id || index"
              class="reward-card"
            >
              <div class="reward-range">
                第 {{ reward.rank_start }}-{{ reward.rank_end }} 名
              </div>
              <div class="reward-content">
                <div class="reward-item" v-if="reward.badge_key">
                  <span class="reward-icon">🏅</span>
                  <span class="reward-text">{{ reward.badge_name || '限定挂件' }}</span>
                </div>
                <div class="reward-item" v-if="reward.title_key">
                  <span class="reward-icon">👑</span>
                  <span class="reward-text">{{ reward.title_name || '专属称号' }}</span>
                </div>
                <div class="reward-item" v-if="reward.card_key">
                  <span class="reward-icon">🃏</span>
                  <span class="reward-text">{{ reward.card_name || '限定卡牌' }}</span>
                </div>
                <div class="reward-item" v-if="reward.reward_amount">
                  <span class="reward-icon">✨</span>
                  <span class="reward-text">{{ reward.reward_amount }} {{ getRewardTypeText(reward.reward_type) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="tabs-container" v-if="myBadges && myBadges.length > 0">
          <el-tabs type="border-card">
            <el-tab-pane label="我的徽章">
              <div class="my-collection">
                <div 
                  v-for="badge in myBadges" 
                  :key="badge.id"
                  class="collection-item"
                >
                  <div class="item-icon" :class="{ 'equipped': badge.is_equipped }">
                    <span class="icon-emoji">{{ badge.badge_icon || '🏅' }}</span>
                  </div>
                  <div class="item-info">
                    <span class="item-name">{{ badge.badge_name }}</span>
                    <span class="item-desc">{{ badge.badge_description }}</span>
                  </div>
                  <el-tag 
                    v-if="badge.is_equipped" 
                    type="success" 
                    size="small"
                  >
                    已装备
                  </el-tag>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="我的称号" v-if="myTitles && myTitles.length > 0">
              <div class="my-collection">
                <div 
                  v-for="title in myTitles" 
                  :key="title.id"
                  class="collection-item"
                >
                  <div class="item-icon" :class="{ 'equipped': title.is_equipped }">
                    <span class="icon-emoji">👑</span>
                  </div>
                  <div class="item-info">
                    <span class="item-name">{{ title.title_name }}</span>
                    <span class="item-desc">{{ title.title_description }}</span>
                  </div>
                  <el-tag 
                    v-if="title.is_equipped" 
                    type="success" 
                    size="small"
                  >
                    已装备
                  </el-tag>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Trophy, UserFilled } from '@element-plus/icons-vue'
import { leaderboardApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const activeTab = ref('weekly_energy')
const boardConfigs = ref([])
const leaderboardData = ref([])
const myRank = ref(null)
const myBadges = ref([])
const myTitles = ref([])
const allRewards = ref([])

const currentBoard = computed(() => {
  return boardConfigs.value.find(b => b.board_key === activeTab.value)
})

const currentRewards = computed(() => {
  if (!allRewards.value || !activeTab.value) return []
  return allRewards.value.filter(r => r.board_key === activeTab.value)
})

function getStarStyle(index) {
  const size = Math.random() * 2 + 1
  return {
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${Math.random() * 4}s`,
    opacity: Math.random() * 0.4 + 0.2
  }
}

function getBoardIcon(boardKey) {
  const iconMap = {
    'weekly_energy': '⚡',
    'prediction_hit': '🔮',
    'friend_network': '🤝'
  }
  return iconMap[boardKey] || '🏆'
}

function getRankTagType(rank) {
  if (rank <= 3) return 'warning'
  if (rank <= 10) return 'info'
  return ''
}

function getRankDisplay(rank) {
  if (!rank) return '未上榜'
  if (rank === 1) return '第1名 🥇'
  if (rank === 2) return '第2名 🥈'
  if (rank === 3) return '第3名 🥉'
  return `第${rank}名`
}

function getRankItemClass(index) {
  if (index === 0) return 'rank-item--gold'
  if (index === 1) return 'rank-item--silver'
  if (index === 2) return 'rank-item--bronze'
  return ''
}

function getScoreLabel(boardKey) {
  const labelMap = {
    'weekly_energy': '能量值',
    'prediction_hit': '命中次数',
    'friend_network': '好友数'
  }
  return labelMap[boardKey] || '分数'
}

function getRewardTypeText(rewardType) {
  const textMap = {
    'stardust_fragment': '星元碎片',
    'stardust_point': '星元点数',
    'prophecy_ticket': '预言券',
    'coupon': '优惠券'
  }
  return textMap[rewardType] || ''
}

async function loadConfigs() {
  try {
    const response = await leaderboardApi.getConfigs()
    boardConfigs.value = response.configs || []
    
    if (boardConfigs.value.length > 0 && !activeTab.value) {
      activeTab.value = boardConfigs.value[0].board_key
    }
  } catch (error) {
    console.error('加载排行榜配置失败:', error)
    boardConfigs.value = [
      { board_key: 'weekly_energy', name: '周能量榜', description: '每周能量贡献排行榜' },
      { board_key: 'prediction_hit', name: '预言家命中榜', description: '预言竞猜命中排行榜' },
      { board_key: 'friend_network', name: '人脉好友榜', description: '人脉好友数量排行榜' }
    ]
  }
}

async function loadBoardData(boardKey) {
  try {
    loading.value = true
    const response = await leaderboardApi.getBoard(boardKey)
    leaderboardData.value = response.entries || []
  } catch (error) {
    console.error('加载排行榜数据失败:', error)
    leaderboardData.value = []
  } finally {
    loading.value = false
  }
}

async function loadMyRank(boardKey) {
  if (!userStore.isLoggedIn) {
    myRank.value = null
    return
  }
  
  try {
    const response = await leaderboardApi.getMyRank(boardKey)
    myRank.value = response
  } catch (error) {
    console.error('加载我的排名失败:', error)
    myRank.value = null
  }
}

async function loadMyBadges() {
  if (!userStore.isLoggedIn) return
  
  try {
    const response = await leaderboardApi.getMyBadges()
    myBadges.value = response.badges || []
  } catch (error) {
    console.error('加载我的徽章失败:', error)
    myBadges.value = []
  }
}

async function loadMyTitles() {
  if (!userStore.isLoggedIn) return
  
  try {
    const response = await leaderboardApi.getMyTitles()
    myTitles.value = response.titles || []
  } catch (error) {
    console.error('加载我的称号失败:', error)
    myTitles.value = []
  }
}

async function handleTabChange(boardKey) {
  activeTab.value = boardKey
  await Promise.all([
    loadBoardData(boardKey),
    loadMyRank(boardKey)
  ])
}

onMounted(async () => {
  await loadConfigs()
  await loadBoardData(activeTab.value)
  await loadMyRank(activeTab.value)
  await loadMyBadges()
  await loadMyTitles()
})
</script>

<style lang="scss" scoped>
.leaderboards-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-y: auto;
  background: linear-gradient(180deg, #0c0c23 0%, #1a1a3e 50%, #0c0c23 100%);
}

.stars-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle 3s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.glow-orbs {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
  pointer-events: none;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: #8b5cf6;
  top: -100px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: #06b6d4;
  bottom: -50px;
  left: -50px;
  animation: float 15s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, 30px); }
}

.leaderboards-main {
  position: relative;
  z-index: 1;
  padding: 40px 20px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.leaderboards-header {
  text-align: center;
  margin-bottom: 40px;
  
  .header-icon {
    width: 72px;
    height: 72px;
    margin: 0 auto 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(6, 182, 212, 0.2) 100%);
    border-radius: 20px;
    color: #c4b5fd;
    animation: pulse-glow 3s ease-in-out infinite;
  }
  
  .main-title {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #c4b5fd 0%, #67e8f9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 12px 0;
  }
  
  .subtitle {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
  }
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 30px rgba(139, 92, 246, 0.3); }
  50% { box-shadow: 0 0 50px rgba(139, 92, 246, 0.5); }
}

.tabs-container {
  margin-bottom: 24px;
  
  :deep(.el-tabs__header) {
    margin-bottom: 0;
    border-bottom: none;
  }
  
  :deep(.el-tabs__nav-wrap) {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    padding: 8px;
    border: 1px solid rgba(139, 92, 246, 0.1);
  }
  
  :deep(.el-tabs__nav) {
    background: transparent;
  }
  
  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.6);
    height: 44px;
    line-height: 44px;
    padding: 0 24px;
    border-radius: 12px;
    margin-right: 4px;
    
    &:hover {
      color: rgba(255, 255, 255, 0.9);
    }
    
    &.is-active {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(6, 182, 212, 0.2) 100%);
      color: #c4b5fd;
    }
    
    &:last-child {
      margin-right: 0;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    display: none;
  }
  
  .tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    
    .tab-icon {
      font-size: 16px;
    }
  }
}

.board-content {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.1);
  overflow: hidden;
}

.board-info {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  background: rgba(139, 92, 246, 0.05);
  
  .board-description {
    p {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
      margin: 0;
    }
  }
}

.my-rank-card {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  
  .my-rank-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    .my-rank-title {
      font-size: 14px;
      font-weight: 500;
      color: rgba(255, 255, 255, 0.8);
    }
  }
  
  .my-rank-info {
    display: flex;
    gap: 24px;
    
    .info-item {
      .info-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        display: block;
        margin-bottom: 4px;
      }
      
      .info-value {
        font-size: 16px;
        font-weight: 600;
        color: #c4b5fd;
      }
    }
  }
}

.rank-list {
  padding: 16px 24px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  &--gold {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
    border-color: rgba(245, 158, 11, 0.3);
  }
  
  &--silver {
    background: linear-gradient(135deg, rgba(148, 163, 184, 0.15) 0%, rgba(148, 163, 184, 0.05) 100%);
    border-color: rgba(148, 163, 184, 0.3);
  }
  
  &--bronze {
    background: linear-gradient(135deg, rgba(194, 139, 93, 0.15) 0%, rgba(194, 139, 93, 0.05) 100%);
    border-color: rgba(194, 139, 93, 0.3);
  }
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    transform: translateX(4px);
  }
  
  .rank-position {
    width: 48px;
    display: flex;
    justify-content: center;
    
    .rank-number {
      font-size: 18px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .top-badge {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      
      .badge-number {
        font-size: 18px;
        font-weight: 700;
        color: #fff;
        position: relative;
        z-index: 1;
      }
      
      .badge-glow {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 50%;
        animation: badge-pulse 2s ease-in-out infinite;
      }
      
      &.top-1 {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        
        .badge-glow {
          background: rgba(245, 158, 11, 0.4);
        }
      }
      
      &.top-2 {
        background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
        
        .badge-glow {
          background: rgba(148, 163, 184, 0.4);
        }
      }
      
      &.top-3 {
        background: linear-gradient(135deg, #c2885d 0%, #a16f4b 100%);
        
        .badge-glow {
          background: rgba(194, 139, 93, 0.4);
        }
      }
    }
  }
  
  .user-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    
    .user-avatar {
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(6, 182, 212, 0.1) 100%);
      border-radius: 50%;
      color: #c4b5fd;
      flex-shrink: 0;
    }
    
    .user-details {
      min-width: 0;
      
      .username {
        font-size: 15px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        display: block;
        margin-bottom: 6px;
      }
      
      .user-badges {
        display: flex;
        gap: 6px;
        
        .vip-tag {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }
      }
    }
  }
  
  .score-info {
    text-align: right;
    flex-shrink: 0;
    
    .score-value {
      font-size: 20px;
      font-weight: 700;
      color: #c4b5fd;
      display: block;
      margin-bottom: 2px;
    }
    
    .score-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

@keyframes badge-pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.2); opacity: 0.3; }
}

.rewards-section {
  padding: 20px 24px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  background: rgba(139, 92, 246, 0.02);
  
  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    
    .section-icon {
      font-size: 18px;
    }
    
    .section-title {
      font-size: 15px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  .rewards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }
  
  .reward-card {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(139, 92, 246, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.2);
    }
    
    .reward-range {
      font-size: 13px;
      font-weight: 600;
      color: #c4b5fd;
      margin-bottom: 10px;
    }
    
    .reward-content {
      .reward-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 6px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .reward-icon {
          font-size: 14px;
        }
      }
    }
  }
}

.my-collection {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  padding: 16px 0;
  
  .collection-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 12px;
    border: 1px solid rgba(139, 92, 246, 0.1);
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba(139, 92, 246, 0.08);
    }
    
    .item-icon {
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(139, 92, 246, 0.1);
      border-radius: 12px;
      flex-shrink: 0;
      
      &.equipped {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.1) 100%);
        border: 2px solid rgba(16, 185, 129, 0.3);
      }
      
      .icon-emoji {
        font-size: 24px;
      }
    }
    
    .item-info {
      flex: 1;
      min-width: 0;
      
      .item-name {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        display: block;
        margin-bottom: 4px;
      }
      
      .item-desc {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

:deep(.el-empty) {
  padding: 40px 0;
  
  .el-empty__description {
    color: rgba(255, 255, 255, 0.5);
  }
}
</style>
