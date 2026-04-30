<template>
  <div class="energy-weather">
    <div class="stars-bg">
      <div v-for="i in 80" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>
    
    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <div class="energy-main">
      <div class="energy-header">
        <div class="header-icon">
          <el-icon size="40"><Sunny /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="main-title">能量天气共同体</h1>
          <p class="subtitle">社区集体星盘能量场 · 实时聚合全站在线用户</p>
        </div>
      </div>

      <div class="scope-selector">
        <el-radio-group v-model="selectedScope" size="large" @change="loadAllData">
          <el-radio-button value="global">
            <el-icon><Search /></el-icon>
            <span>全站能量</span>
          </el-radio-button>
          <el-radio-button value="local" v-if="currentUserCity">
            <el-icon><Location /></el-icon>
            <span>同城能量 ({{ currentUserCity }})</span>
          </el-radio-button>
        </el-radio-group>
      </div>

      <div class="main-grid">
        <div class="weather-card">
          <div class="card-header">
            <span class="card-title">当前能量天气</span>
            <span class="refresh-btn" @click="loadWeatherData">
              <el-icon><Refresh /></el-icon>
            </span>
          </div>
          
          <div class="weather-display" v-if="weatherData">
            <div class="weather-icon">
              <span class="icon-text">{{ weatherData.weather_type?.icon || '☀️' }}</span>
            </div>
            <div class="weather-info">
              <div class="weather-label">{{ weatherData.weather_type?.label || '加载中...' }}</div>
              <div class="weather-desc">{{ weatherData.weather_type?.description || '' }}</div>
              <div class="energy-score">
                <span class="score-value">{{ Math.round(weatherData.overall_energy_score || 0) }}</span>
                <span class="score-unit">/ 100</span>
              </div>
            </div>
          </div>
          
          <div class="mood-indicator" v-if="weatherData">
            <div class="mood-label">集体情绪：</div>
            <div class="mood-badge" :class="weatherData.mood">
              <span class="mood-icon">{{ getMoodIcon(weatherData.mood) }}</span>
              <span class="mood-text">{{ getMoodLabel(weatherData.mood) }}</span>
            </div>
          </div>
          
          <div class="energy-meters" v-if="weatherData">
            <div class="meter-item">
              <div class="meter-header">
                <span class="meter-label">和谐能量</span>
                <span class="meter-value">{{ Math.round(weatherData.harmony_ratio || 0) }}%</span>
              </div>
              <el-progress 
                :percentage="Math.round(weatherData.harmony_ratio || 0)" 
                :stroke-width="8"
                :color="'#22c55e'"
              />
            </div>
            <div class="meter-item">
              <div class="meter-header">
                <span class="meter-label">紧张能量</span>
                <span class="meter-value">{{ Math.round(weatherData.challenge_ratio || 0) }}%</span>
              </div>
              <el-progress 
                :percentage="Math.round(weatherData.challenge_ratio || 0)" 
                :stroke-width="8"
                :color="'#ef4444'"
              />
            </div>
          </div>
        </div>

        <div class="community-card">
          <div class="card-header">
            <span class="card-title">社区在线用户</span>
            <span class="online-count">
              <el-icon><User /></el-icon>
              <span>{{ onlineUsers?.count || 0 }} 人在线</span>
            </span>
          </div>
          
          <div class="user-list" v-if="onlineUsers?.users?.length > 0">
            <div class="user-item" v-for="(user, index) in onlineUsers.users.slice(0, 8)" :key="index">
              <el-avatar :size="36">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-info">
                <span class="user-name">{{ user.username || '匿名用户' }}</span>
                <span class="user-status online">在线</span>
              </div>
            </div>
          </div>
          
          <div class="empty-state" v-else>
            <el-icon size="48"><User /></el-icon>
            <p>暂无在线用户</p>
          </div>
          
          <div class="stat-bar" v-if="weatherData">
            <div class="stat-item">
              <span class="stat-label">活跃星盘</span>
              <span class="stat-value">{{ weatherData.total_users_analyzed || 0 }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">相位统计</span>
              <span class="stat-value">{{ weatherData.total_aspects || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="dimensions-section">
        <div class="card-header">
          <span class="card-title">维度能量分布</span>
        </div>
        
        <div class="dimensions-grid" v-if="weatherData?.dimension_energies">
          <div 
            class="dimension-card" 
            v-for="dim in weatherData.dimension_energies" 
            :key="dim.dimension"
            :style="{ '--dim-color': getDimensionColor(dim.dimension) }"
          >
            <div class="dimension-icon">
              <span>{{ getDimensionIcon(dim.dimension) }}</span>
            </div>
            <div class="dimension-info">
              <div class="dimension-name">{{ getDimensionName(dim.dimension) }}</div>
              <div class="dimension-score">
                <span class="score">{{ Math.round(dim.score || 0) }}</span>
                <span class="level">{{ getEnergyLevel(dim.score) }}</span>
              </div>
            </div>
            <div class="dimension-bar">
              <div 
                class="bar-fill" 
                :style="{ width: `${Math.min(100, (dim.score || 0) / 80 * 100)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div class="quick-actions">
        <div class="action-card" @click="navigateTo('missions')">
          <div class="action-icon missions">
            <el-icon><Search /></el-icon>
          </div>
          <div class="action-info">
            <span class="action-title">能量任务</span>
            <span class="action-desc">参与集体共修，获取星尘奖励</span>
          </div>
          <el-icon><Connection /></el-icon>
        </div>
        
        <div class="action-card" @click="navigateTo('contribute')">
          <div class="action-icon contribute">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="action-info">
            <span class="action-title">能量注入</span>
            <span class="action-desc">分享你的行星能量，加持社区</span>
          </div>
          <el-icon><Connection /></el-icon>
        </div>
        
        <div class="action-card" @click="navigateTo('predictions')">
          <div class="action-icon predictions">
            <el-icon><Search /></el-icon>
          </div>
          <div class="action-info">
            <span class="action-title">预测竞猜</span>
            <span class="action-desc">预判明日星象，平分星尘大奖</span>
          </div>
          <el-icon><Connection /></el-icon>
        </div>
      </div>

      <div class="contributions-section" v-if="activeContributions?.contributions?.length > 0">
        <div class="card-header">
          <span class="card-title">活跃能量贡献</span>
          <div class="bonus-info">
            <span class="bonus-label">社区能量加成</span>
            <span class="bonus-value">+{{ Math.round((activeContributions.bonus?.bonus_percentage || 0)) }}%</span>
          </div>
        </div>
        
        <div class="contributions-list">
          <div class="contribution-item" v-for="(contrib, index) in activeContributions.contributions.slice(0, 5)" :key="index">
            <el-avatar :size="32" :style="{ backgroundColor: contrib.color }">
              <span>{{ contrib.planet_icon }}</span>
            </el-avatar>
            <div class="contrib-info">
              <span class="contrib-name">{{ contrib.name }}</span>
              <span class="contrib-remaining">剩余 {{ contrib.remaining_minutes }} 分钟</span>
            </div>
            <div class="contrib-energy">+{{ Math.round(contrib.energy_amount) }}</div>
          </div>
        </div>
      </div>

      <div class="missions-preview" v-if="activeMissions?.missions?.length > 0">
        <div class="card-header">
          <span class="card-title">进行中的任务</span>
          <span class="view-all" @click="navigateTo('missions')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </span>
        </div>
        
        <div class="missions-list">
          <div class="mission-card" v-for="mission in activeMissions.missions.slice(0, 3)" :key="mission.id">
            <div class="mission-icon" :class="mission.mission_type">
              <el-icon><Search /></el-icon>
            </div>
            <div class="mission-body">
              <div class="mission-title">{{ mission.title }}</div>
              <div class="mission-desc">{{ mission.description }}</div>
              <div class="mission-meta">
                <span class="reward">
                  <el-icon><Search /></el-icon>
                  <span>{{ mission.base_reward }} 星尘</span>
                </span>
                <span class="difficulty">{{ getDifficultyLabel(mission.difficulty) }}</span>
              </div>
            </div>
            <el-button type="primary" size="small" @click="navigateTo('missions')">
              参与
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Sunny, Refresh, Location, User, 
  MagicStick, Search, Connection, Clock 
} from '@element-plus/icons-vue'
import { energyCommunityApi } from '@/api'

const router = useRouter()

const selectedScope = ref('global')
const currentUserCity = ref(null)
const weatherData = ref(null)
const onlineUsers = ref(null)
const activeMissions = ref(null)
const activeContributions = ref(null)
const loading = ref(false)

let refreshInterval = null

const DIMENSION_CONFIG = {
  communication: { name: '沟通', icon: '💬', color: '#60a5fa' },
  social: { name: '社交', icon: '👥', color: '#f472b6' },
  career: { name: '事业', icon: '💼', color: '#f97316' },
  wealth: { name: '财运', icon: '💰', color: '#eab308' },
  emotion: { name: '情绪', icon: '❤️', color: '#ec4899' }
}

const MOOD_CONFIG = {
  harmonious: { icon: '😊', label: '和谐', color: '#22c55e' },
  balanced: { icon: '😐', label: '平稳', color: '#64748b' },
  challenging: { icon: '😰', label: '紧张', color: '#ef4444' }
}

const DIFFICULTY_CONFIG = {
  easy: { label: '简单', color: '#22c55e' },
  medium: { label: '中等', color: '#f59e0b' },
  hard: { label: '困难', color: '#ef4444' }
}

const getStarStyle = (i) => {
  const left = Math.random() * 100
  const top = Math.random() * 100
  const delay = Math.random() * 5
  const opacity = 0.3 + Math.random() * 0.7
  return {
    left: `${left}%`,
    top: `${top}%`,
    animationDelay: `${delay}s`,
    opacity: opacity
  }
}

const getMoodIcon = (mood) => MOOD_CONFIG[mood]?.icon || '😐'
const getMoodLabel = (mood) => MOOD_CONFIG[mood]?.label || '平稳'

const getDimensionColor = (dim) => DIMENSION_CONFIG[dim]?.color || '#9370db'
const getDimensionIcon = (dim) => DIMENSION_CONFIG[dim]?.icon || '✨'
const getDimensionName = (dim) => DIMENSION_CONFIG[dim]?.name || dim

const getDifficultyLabel = (diff) => DIFFICULTY_CONFIG[diff]?.label || '未知'

const getEnergyLevel = (score) => {
  if (score >= 70) return '旺盛'
  if (score >= 50) return '活跃'
  if (score >= 30) return '平稳'
  return '低迷'
}

const loadWeatherData = async () => {
  try {
    const data = await energyCommunityApi.getCurrentWeather(
      selectedScope.value,
      selectedScope.value === 'local' ? currentUserCity.value : null
    )
    weatherData.value = data
  } catch (error) {
    console.error('加载天气数据失败:', error)
  }
}

const loadOnlineUsers = async () => {
  try {
    const data = await energyCommunityApi.getOnlineUsers(
      selectedScope.value,
      selectedScope.value === 'local' ? currentUserCity.value : null
    )
    onlineUsers.value = data
  } catch (error) {
    console.error('加载在线用户失败:', error)
  }
}

const loadActiveMissions = async () => {
  try {
    const data = await energyCommunityApi.getActiveMissions(5)
    activeMissions.value = data
  } catch (error) {
    console.error('加载任务失败:', error)
  }
}

const loadActiveContributions = async () => {
  try {
    const data = await energyCommunityApi.getActiveContributions(
      selectedScope.value,
      selectedScope.value === 'local' ? currentUserCity.value : null
    )
    activeContributions.value = data
  } catch (error) {
    console.error('加载贡献失败:', error)
  }
}

const loadAllData = async () => {
  loading.value = true
  await Promise.all([
    loadWeatherData(),
    loadOnlineUsers(),
    loadActiveMissions(),
    loadActiveContributions()
  ])
  loading.value = false
}

const sendHeartbeat = async () => {
  try {
    await energyCommunityApi.updatePresence({})
  } catch (error) {
    console.error('心跳失败:', error)
  }
}

const navigateTo = (route) => {
  const routes = {
    missions: '/energy-community/missions',
    contribute: '/energy-community/contribute',
    predictions: '/energy-community/predictions'
  }
  router.push(routes[route] || '/energy-community')
}

onMounted(() => {
  loadAllData()
  sendHeartbeat()
  
  refreshInterval = setInterval(() => {
    loadWeatherData()
    loadOnlineUsers()
    sendHeartbeat()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped lang="scss">
.energy-weather {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
  position: relative;
  overflow-x: hidden;
  padding: 20px 0 60px;
}

.stars-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.star {
  position: absolute;
  width: 2px;
  height: 2px;
  background: white;
  border-radius: 50%;
  animation: twinkle 3s infinite ease-in-out;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.glow-orbs {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.orb-1 {
  background: linear-gradient(135deg, #8b5cf6, #ec4899);
  top: -100px;
  right: -100px;
}

.orb-2 {
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  bottom: -150px;
  left: -150px;
}

.orb-3 {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.energy-main {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.energy-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding: 30px 0;

  .header-icon {
    width: 72px;
    height: 72px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(236, 72, 153, 0.3));
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a78bfa;
    border: 1px solid rgba(139, 92, 246, 0.3);
  }

  .header-text {
    .main-title {
      font-size: 32px;
      font-weight: 700;
      background: linear-gradient(135deg, #a78bfa, #f472b6);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0 0 8px;
    }

    .subtitle {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
      margin: 0;
    }
  }
}

.scope-selector {
  margin-bottom: 30px;

  :deep(.el-radio-group) {
    display: flex;
    gap: 4px;
  }

  :deep(.el-radio-button__inner) {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.7);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    border-radius: 12px !important;

    &:hover {
      color: #a78bfa;
    }
  }

  :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(236, 72, 153, 0.3));
    border-color: #a78bfa;
    color: #a78bfa;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
  }
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.weather-card,
.community-card,
.dimensions-section,
.quick-actions,
.contributions-section,
.missions-preview {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }

  .refresh-btn, .view-all {
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    color: #a78bfa;
    font-size: 13px;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.8;
    }
  }
}

.weather-display {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;

  .weather-icon {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2));
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;

    .icon-text {
      font-size: 48px;
    }
  }

  .weather-info {
    flex: 1;

    .weather-label {
      font-size: 24px;
      font-weight: 700;
      color: white;
      margin-bottom: 4px;
    }

    .weather-desc {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 12px;
    }

    .energy-score {
      display: flex;
      align-items: baseline;
      gap: 4px;

      .score-value {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .score-unit {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

.mood-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 20px;

  .mood-label {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
  }

  .mood-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;

    &.harmonious {
      background: rgba(34, 197, 94, 0.2);
      color: #22c55e;
    }

    &.balanced {
      background: rgba(100, 116, 139, 0.2);
      color: #94a3b8;
    }

    &.challenging {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
    }
  }
}

.energy-meters {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .meter-item {
    .meter-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;

      .meter-label {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
      }

      .meter-value {
        font-size: 13px;
        font-weight: 600;
        color: white;
      }
    }
  }
}

.online-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #22c55e;
  font-weight: 500;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;

  .user-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    transition: background 0.2s;

    &:hover {
      background: rgba(255, 255, 255, 0.06);
    }

    .user-info {
      flex: 1;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .user-name {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.9);
      }

      .user-status {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 10px;

        &.online {
          background: rgba(34, 197, 94, 0.15);
          color: #22c55e;
        }
      }
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

.stat-bar {
  display: flex;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);

  .stat-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .stat-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #a78bfa;
    }
  }

  .stat-divider {
    width: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 0 16px;
  }
}

.dimensions-section {
  margin-bottom: 24px;
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.dimension-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px;
  transition: all 0.3s;

  &:hover {
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-2px);
  }

  .dimension-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    font-size: 20px;
  }

  .dimension-info {
    margin-bottom: 12px;

    .dimension-name {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
      margin-bottom: 4px;
    }

    .dimension-score {
      display: flex;
      align-items: baseline;
      gap: 6px;

      .score {
        font-size: 24px;
        font-weight: 700;
        color: var(--dim-color);
      }

      .level {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }

  .dimension-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;

    .bar-fill {
      height: 100%;
      background: var(--dim-color);
      border-radius: 2px;
      transition: width 0.5s ease;
    }
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  background: transparent;
  border: none;
  padding: 0;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-2px);
    border-color: rgba(167, 139, 250, 0.4);
  }

  .action-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;

    &.missions {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1));
      color: #22c55e;
    }

    &.contribute {
      background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.1));
      color: #ec4899;
    }

    &.predictions {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.1));
      color: #a78bfa;
    }
  }

  .action-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;

    .action-title {
      font-size: 15px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }

    .action-desc {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }

  .el-icon {
    color: rgba(255, 255, 255, 0.4);
    font-size: 16px;
    transition: color 0.2s;
  }

  &:hover .el-icon {
    color: #a78bfa;
  }
}

.contributions-section,
.missions-preview {
  margin-bottom: 24px;
}

.bonus-info {
  display: flex;
  align-items: center;
  gap: 8px;

  .bonus-label {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }

  .bonus-value {
    font-size: 14px;
    font-weight: 600;
    color: #22c55e;
    padding: 4px 10px;
    background: rgba(34, 197, 94, 0.15);
    border-radius: 12px;
  }
}

.contributions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .contribution-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;

    .contrib-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;

      .contrib-name {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 500;
      }

      .contrib-remaining {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }
    }

    .contrib-energy {
      font-size: 16px;
      font-weight: 700;
      color: #22c55e;
    }
  }
}

.missions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .mission-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;

    .mission-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, rgba(167, 139, 250, 0.2), rgba(167, 139, 250, 0.1));
      color: #a78bfa;
      font-size: 18px;
    }

    .mission-body {
      flex: 1;

      .mission-title {
        font-size: 15px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 4px;
      }

      .mission-desc {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .mission-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12px;

        .reward {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #f59e0b;

          .el-icon {
            font-size: 14px;
          }
        }

        .difficulty {
          padding: 2px 8px;
          border-radius: 8px;
          font-weight: 500;

          &.easy {
            background: rgba(34, 197, 94, 0.15);
            color: #22c55e;
          }

          &.medium {
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
          }

          &.hard {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
          }
        }
      }
    }
  }
}

@media (max-width: 900px) {
  .main-grid {
    grid-template-columns: 1fr;
  }

  .dimensions-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .quick-actions {
    grid-template-columns: 1fr;
  }

  .energy-header {
    flex-direction: column;
    text-align: center;
    padding: 20px 0;
  }

  .main-title {
    font-size: 24px !important;
  }
}

@media (max-width: 600px) {
  .dimensions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
