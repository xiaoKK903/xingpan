<template>
  <div class="phase-connect">
    <div class="stars-bg">
      <div v-for="(star, index) in starPositions" :key="index" class="star" :style="getStarStyle(star)"></div>
    </div>

    <div class="connect-main">
      <div class="quick-nav">
        <div class="nav-item" @click="goToAstro">
          <span class="nav-icon">🔮</span>
          <span class="nav-text">星盘查询</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item active">
          <span class="nav-icon">🔗</span>
          <span class="nav-text">相位连连看</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item" @click="goToNetworkChain">
          <span class="nav-icon">🕸️</span>
          <span class="nav-text">星盘人脉链</span>
          <span class="nav-arrow">→</span>
        </div>
      </div>

      <div class="connect-header">
        <div class="header-icon">
          <span class="header-emoji">🔗</span>
        </div>
        <div class="header-text">
          <h1 class="main-title">相位连连看</h1>
          <p class="subtitle">探索你的相位能量，寻找与你产生奇妙化学反应的人</p>
        </div>
      </div>

      <div v-if="loading" class="loading-section">
        <el-icon size="40" class="loading-icon"><Loading /></el-icon>
        <p class="loading-text">正在分析你的相位能量...</p>
      </div>

      <div v-else-if="!hasChart" class="no-chart-section">
        <div class="no-chart-card">
          <div class="no-chart-icon">🔮</div>
          <h3 class="no-chart-title">尚未保存星盘</h3>
          <p class="no-chart-desc">
            相位连连看需要先保存你的星盘数据，
            <br />这样才能分析你的相位能量，找到与你产生连接的人。
          </p>
          <el-button type="primary" size="large" @click="goToAstro" class="go-astro-btn">
            <el-icon><MagicStick /></el-icon>
            去排盘
          </el-button>
        </div>
      </div>

      <div v-else class="connect-content">
        <div class="my-phases-card">
          <h3 class="section-title">
            <span class="title-icon">✨</span>
            我的相位能量
          </h3>
          
          <div v-if="myAspects.length === 0" class="no-aspects">
            <p>暂无主要相位数据</p>
          </div>
          
          <div v-else class="phases-overview">
            <div class="aspect-stats">
              <div class="stat-item harmonious">
                <div class="stat-value">{{ harmoniousCount }}</div>
                <div class="stat-label">和谐相位</div>
              </div>
              <div class="stat-item challenging">
                <div class="stat-value">{{ challengingCount }}</div>
                <div class="stat-label">挑战相位</div>
              </div>
              <div class="stat-item neutral">
                <div class="stat-value">{{ neutralCount }}</div>
                <div class="stat-label">中性相位</div>
              </div>
            </div>

            <div class="key-aspects-section">
              <h4 class="subsection-title">关键相位</h4>
              <div class="aspects-list">
                <div 
                  v-for="(aspect, index) in keyAspects" 
                  :key="index" 
                  class="aspect-item"
                  :class="getAspectClass(aspect)"
                >
                  <div class="aspect-planets">
                    <span class="planet-symbol">{{ aspect.planet1_symbol || '?' }}</span>
                    <span class="aspect-symbol">{{ getAspectDisplaySymbol(aspect) }}</span>
                    <span class="planet-symbol">{{ aspect.planet2_symbol || '?' }}</span>
                  </div>
                  <div class="aspect-info">
                    <div class="aspect-name">{{ aspect.aspect }}</div>
                    <div class="aspect-planets-name">{{ aspect.planet1 }} - {{ aspect.planet2 }}</div>
                  </div>
                  <div class="aspect-orb">
                    容许度: {{ aspect.orb }}°
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="match-status-card">
          <h3 class="section-title">
            <span class="title-icon">🎯</span>
            相位连接状态
          </h3>
          
          <div class="status-grid">
            <div class="status-item">
              <div class="status-value">{{ matchStatus.available_matches || 0 }}</div>
              <div class="status-label">可连接人数</div>
            </div>
            <div class="status-item">
              <div class="status-value">{{ matchStatus.connections_made || 0 }}</div>
              <div class="status-label">已建立连接</div>
            </div>
            <div class="status-item">
              <div class="status-value">{{ matchStatus.pending_reveals || 0 }}</div>
              <div class="status-label">待揭示</div>
            </div>
          </div>

          <div class="match-actions">
            <el-button 
              type="primary" 
              size="large" 
              :loading="matching" 
              :disabled="!canMatch"
              @click="startPhaseMatch"
              class="match-btn"
            >
              <el-icon><Connection /></el-icon>
              寻找相位连接
            </el-button>
          </div>
        </div>

        <div class="recent-matches-section" v-if="recentMatches.length > 0">
          <h3 class="section-title">
            <span class="title-icon">💫</span>
            近期相位连接
          </h3>
          
          <div class="matches-grid">
            <div 
              v-for="match in recentMatches" 
              :key="match.id" 
              class="match-card"
              @click="openMatchDetail(match)"
            >
              <div class="match-header">
                <div class="match-users">
                  <div class="user-avatar small">
                    <span class="avatar-placeholder">👤</span>
                  </div>
                  <div class="connect-arrow">↔</div>
                  <div class="user-avatar small">
                    <span class="avatar-placeholder">👤</span>
                  </div>
                </div>
                <div class="match-score">
                  <span class="score-label">匹配度</span>
                  <span class="score-value">{{ match.compatibility_score || 0 }}%</span>
                </div>
              </div>
              
              <div class="match-aspects" v-if="match.shared_aspects && match.shared_aspects.length > 0">
                <div class="match-aspect" v-for="(aspect, idx) in match.shared_aspects.slice(0, 2)" :key="idx">
                  <span class="aspect-text">{{ aspect }}</span>
                </div>
                <span v-if="match.shared_aspects.length > 2" class="more-aspects">
                  +{{ match.shared_aspects.length - 2 }} 更多
                </span>
              </div>

              <div class="match-footer">
                <span class="match-time">{{ formatMatchTime(match.created_at) }}</span>
                <el-button type="primary" size="small" link @click.stop="viewSynastry(match)">
                  查看合盘
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="phase-visualization-section">
          <h3 class="section-title">
            <span class="title-icon">🌐</span>
            相位连接图谱
          </h3>
          
          <div class="visualization-container">
            <div class="phase-network-placeholder">
              <div class="network-center">
                <div class="center-node">
                  <span class="node-icon">👤</span>
                  <span class="node-label">你</span>
                </div>
              </div>
              
              <div class="connecting-lines" v-if="networkNodes.length > 0">
                <div 
                  v-for="(node, idx) in networkNodes" 
                  :key="idx" 
                  class="connected-node"
                  :style="getNodePosition(idx)"
                >
                  <div class="node-avatar">
                    <span class="node-icon">👤</span>
                  </div>
                  <div class="node-info">
                    <div class="connection-type" :class="node.connection_type">
                      {{ getConnectionLabel(node.connection_type) }}
                    </div>
                    <div class="node-score">{{ node.score }}%</div>
                  </div>
                </div>
              </div>
              
              <div v-else class="no-connections-hint">
                <p>点击「寻找相位连接」发现与你产生相位共鸣的人</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showMatchDetail" 
      title="相位连接详情" 
      width="700px"
      class="match-detail-dialog"
    >
      <div v-if="currentMatch" class="match-detail-content">
        <div class="detail-header">
          <div class="detail-persons">
            <div class="person-info">
              <div class="person-avatar">
                <span class="avatar-placeholder">👤</span>
              </div>
              <div class="person-details">
                <div class="person-name">你</div>
              </div>
            </div>
            <div class="connection-symbol">
              <el-icon size="24"><Link /></el-icon>
            </div>
            <div class="person-info">
              <div class="person-avatar">
                <span class="avatar-placeholder">👤</span>
              </div>
              <div class="person-details">
                <div class="person-name">{{ currentMatch.matched_user_name || '神秘用户' }}</div>
              </div>
            </div>
          </div>
          
          <div class="detail-score">
            <div class="score-circle" :style="getScoreGradient(currentMatch.compatibility_score)">
              <span class="score-number">{{ currentMatch.compatibility_score || 0 }}</span>
              <span class="score-unit">%</span>
            </div>
            <div class="score-label">相位匹配度</div>
          </div>
        </div>

        <div class="shared-aspects-section">
          <h4 class="section-subtitle">✨ 共同相位能量</h4>
          <div class="shared-aspects-list">
            <div 
              v-for="(aspect, idx) in currentMatch.shared_aspects_details" 
              :key="idx" 
              class="shared-aspect-item"
              :class="aspect.type"
            >
              <div class="aspect-display">
                <span class="planet">{{ aspect.planet_a }}</span>
                <span class="aspect-icon">{{ getAspectIcon(aspect.aspect) }}</span>
                <span class="planet">{{ aspect.planet_b }}</span>
              </div>
              <div class="aspect-meaning">{{ aspect.meaning }}</div>
            </div>
          </div>
        </div>

        <div class="synastry-preview-section" v-if="currentMatch.synastry_preview">
          <h4 class="section-subtitle">💫 合盘亮点</h4>
          <div class="synastry-highlights">
            <div class="highlight-item" v-for="(highlight, idx) in currentMatch.synastry_preview.highlights" :key="idx">
              <div class="highlight-icon">{{ highlight.icon }}</div>
              <div class="highlight-content">
                <div class="highlight-title">{{ highlight.title }}</div>
                <div class="highlight-desc">{{ highlight.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" size="large" @click="startSynastryWithMatch">
            <el-icon><Connection /></el-icon>
            深入合盘分析
          </el-button>
          <el-button size="large" @click="sendPrivateMessage">
            <el-icon><ChatDotRound /></el-icon>
            私聊连接
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chartApi, synastryApi, phaseConnectApi, privateChatApi } from '@/api'
import { Loading, MagicStick, Connection, Link, ChatDotRound } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const matching = ref(false)
const hasChart = ref(false)
const myChart = ref(null)
const myAspects = ref([])
const matchStatus = ref({
  available_matches: 0,
  connections_made: 0,
  pending_reveals: 0
})
const recentMatches = ref([])
const networkNodes = ref([])

const showMatchDetail = ref(false)
const currentMatch = ref(null)

const starPositions = computed(() => generateFixedStarPositions())

function generateFixedStarPositions() {
  const positions = []
  const seed = 42
  const modulus = 233280
  const multiplier = 9301
  const increment = 49297
  const starsCount = 80
  
  for (let i = 0; i < starsCount; i++) {
    const pseudoRandom1 = ((seed * (i + 1) * multiplier + increment) % modulus) / modulus
    const pseudoRandom2 = ((seed * (i + 2) * multiplier + increment) % modulus) / modulus
    const pseudoRandom3 = ((seed * (i + 3) * multiplier + increment) % modulus) / modulus
    const pseudoRandom4 = ((seed * (i + 4) * multiplier + increment) % modulus) / modulus
    
    positions.push({
      left: (pseudoRandom1 * 100) + '%',
      top: (pseudoRandom2 * 100) + '%',
      size: pseudoRandom3 * 2 + 1,
      delay: (pseudoRandom4 * 4) + 's',
      opacity: pseudoRandom1 * 0.4 + 0.2
    })
  }
  return positions
}

const harmoniousCount = computed(() => {
  return myAspects.value.filter(a => {
    const nature = a.nature || getAspectNature(a.aspect)
    return nature === 'harmonious'
  }).length
})

const challengingCount = computed(() => {
  return myAspects.value.filter(a => {
    const nature = a.nature || getAspectNature(a.aspect)
    return nature === 'challenging'
  }).length
})

const neutralCount = computed(() => {
  return myAspects.value.filter(a => {
    const nature = a.nature || getAspectNature(a.aspect)
    return nature === 'neutral'
  }).length
})

const ASPECT_NATURE_MAP = {
  '合相': 'neutral',
  '六分相': 'harmonious',
  '四分相': 'challenging',
  '三分相': 'harmonious',
  '对分相': 'challenging'
}

function getAspectNature(aspectName) {
  return ASPECT_NATURE_MAP[aspectName] || 'neutral'
}

const keyAspects = computed(() => {
  return myAspects.value.slice(0, 8)
})

const canMatch = computed(() => {
  return hasChart.value && !matching.value
})

function getStarStyle(star) {
  return {
    left: star.left,
    top: star.top,
    width: `${star.size}px`,
    height: `${star.size}px`,
    animationDelay: star.delay,
    opacity: star.opacity
  }
}

function getAspectClass(aspect) {
  const nature = aspect.nature || getAspectNature(aspect.aspect)
  return nature
}

function getAspectDisplaySymbol(aspect) {
  const symbols = {
    '合相': '☌',
    '六分相': '⚹',
    '四分相': '□',
    '三分相': '△',
    '对分相': '☍'
  }
  return symbols[aspect.aspect] || aspect.aspect_symbol || '?'
}

function getNodePosition(index) {
  const total = networkNodes.value.length || 1
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2
  const radius = 120
  const x = Math.cos(angle) * radius + 150
  const y = Math.sin(angle) * radius + 150
  return {
    left: `${x}px`,
    top: `${y}px`,
    transform: 'translate(-50%, -50%)'
  }
}

function getConnectionLabel(type) {
  const labels = {
    'harmonious': '和谐共鸣',
    'challenging': '张力吸引',
    'mixed': '复杂连接',
    'strong': '强烈相位'
  }
  return labels[type] || '相位连接'
}

function getScoreGradient(score) {
  let color = '#8b5cf6'
  if (score >= 80) color = '#22c55e'
  else if (score >= 60) color = '#eab308'
  else color = '#f97316'
  return {
    '--score-color': color
  }
}

function getAspectIcon(aspectName) {
  const icons = {
    '合相': '☌',
    '六分相': '⚹',
    '四分相': '□',
    '三分相': '△',
    '对分相': '☍'
  }
  return icons[aspectName] || '✦'
}

function formatMatchTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

function goToAstro() {
  router.push('/astro')
}

function goToNetworkChain() {
  router.push('/network-chain')
}

async function loadMyChart() {
  loading.value = true
  try {
    let phaseStatus = null
    try {
      phaseStatus = await phaseConnectApi.getMyStatus()
    } catch (apiError) {
      console.warn('phaseConnectApi.getMyStatus 失败，尝试备用方式:', apiError)
    }
    
    if (phaseStatus) {
      hasChart.value = phaseStatus.has_chart
      
      if (phaseStatus.has_chart) {
        if (phaseStatus.key_aspects) {
          myAspects.value = phaseStatus.key_aspects
        }
        
        if (phaseStatus.match_status) {
          matchStatus.value = phaseStatus.match_status
        }
      }
      
      try {
        await loadRecentMatches()
      } catch (e) {
        console.warn('加载近期连接失败:', e)
      }
    } else {
      const result = await chartApi.getMyCharts({ limit: 1 })
      if (result?.charts && result.charts.length > 0) {
        myChart.value = result.charts[0]
        hasChart.value = true
        
        const chartDetail = await chartApi.getChartById(myChart.value.id)
        if (chartDetail?.chart_data) {
          const chartData = typeof chartDetail.chart_data === 'string' 
            ? JSON.parse(chartDetail.chart_data) 
            : chartDetail.chart_data
          myAspects.value = chartData.aspects || []
        }
        
        try {
          await loadMatchStatus()
          await loadRecentMatches()
        } catch (e) {
          console.warn('加载匹配状态失败:', e)
        }
      } else {
        hasChart.value = false
      }
    }
  } catch (error) {
    console.error('加载星盘失败:', error)
    hasChart.value = false
  } finally {
    loading.value = false
  }
}

async function loadMatchStatus() {
  try {
    const result = await phaseConnectApi.getMyStatus()
    if (result) {
      matchStatus.value = result.match_status || {
        available_matches: 0,
        connections_made: 0,
        pending_reveals: 0
      }
      if (result.aspect_summary) {
      }
    }
  } catch (error) {
    console.error('加载匹配状态失败:', error)
  }
}

async function loadRecentMatches() {
  try {
    const result = await phaseConnectApi.getRecentConnections()
    if (result && result.connections) {
      recentMatches.value = result.connections
    }
  } catch (error) {
    console.error('加载近期连接失败:', error)
  }
}

async function startPhaseMatch() {
  if (!canMatch.value) return
  
  matching.value = true
  try {
    const result = await phaseConnectApi.searchMatches({
      match_type: 'all',
      search_radius_km: 50
    })
    
    if (result && result.matches && result.matches.length > 0) {
      const matches = result.matches
      
      networkNodes.value = matches.slice(0, 5).map(m => ({
        connection_type: m.match_type,
        score: m.compatibility_score,
        user_name: m.matched_user_name
      }))
      
      ElMessage.success(`发现了 ${matches.length} 个与你产生相位共鸣的人！`)
    } else {
      ElMessage.info('暂时没有找到匹配的用户，请稍后再试')
    }
  } catch (error) {
    console.error('匹配失败:', error)
    ElMessage.error('寻找相位连接失败，请重试')
  } finally {
    matching.value = false
  }
}

function openMatchDetail(match) {
  currentMatch.value = {
    ...match,
    shared_aspects_details: [
      {
        planet_a: '太阳',
        planet_b: '月亮',
        aspect: '三分相',
        type: 'harmonious',
        meaning: '你们的情感能够自然地相互支持，彼此理解对方的核心需求'
      },
      {
        planet_a: '金星',
        planet_b: '火星',
        aspect: '六分相',
        type: 'harmonious',
        meaning: '在爱情和激情方面有着和谐的能量流动，吸引力自然产生'
      }
    ],
    synastry_preview: {
      highlights: [
        {
          icon: '💕',
          title: '情感共鸣',
          description: '月亮与金星形成和谐相位，能够深度理解对方的情感需求'
        },
        {
          icon: '⚡',
          title: '化学反应',
          description: '火星与太阳的互动带来强烈的吸引力和行动力'
        },
        {
          icon: '🧠',
          title: '思维契合',
          description: '水星相位显示你们在沟通上有着天然的默契'
        }
      ]
    }
  }
  showMatchDetail.value = true
}

function startSynastryWithMatch() {
  router.push('/synastry')
}

function viewSynastry(match) {
  router.push('/synastry')
}

async function sendPrivateMessage() {
  console.log('[PhaseConnect] sendPrivateMessage 被调用，currentMatch:', currentMatch.value)
  
  if (!currentMatch.value) {
    ElMessage.warning('请先选择一个匹配用户')
    return
  }
  
  const match = currentMatch.value
  
  const targetUserId = match.matched_user_id || match.user_id || match.id || match.userId
  const userName = match.matched_user_name || match.user_name || match.userName || match.username || '用户'
  
  console.log(`[PhaseConnect] 目标用户ID: ${targetUserId}, 用户名: ${userName}`)
  console.log(`[PhaseConnect] 当前匹配对象的字段:`, Object.keys(match))
  
  if (!targetUserId || typeof targetUserId !== 'number' || targetUserId <= 0) {
    console.error('[PhaseConnect] 无法获取有效的用户ID，匹配对象:', match)
    
    const synastryRecordId = match.id || match.synastry_record_id
    if (synastryRecordId) {
      ElMessage.warning('该记录没有关联用户信息，请从人脉链或相位连连看页面发起私聊')
      return
    }
    
    ElMessage.warning('无法获取用户信息，请稍后重试')
    return
  }
  
  const compatibilityScore = match.compatibility_score || match.compatibilityScore || 0
  const matchType = match.match_type || match.matchType || 'harmonious'
  
  showMatchDetail.value = false
  
  try {
    ElMessage.info(`正在打开与 ${userName} 的聊天...`)
    
    const result = await privateChatApi.startChat({
      target_user_id: targetUserId,
      match_source: 'phase_connect',
      compatibility_score: compatibilityScore,
      match_type: matchType
    })
    
    console.log('[PhaseConnect] startChat 返回结果:', result)
    
    ElMessage.success(`已创建与 ${userName} 的聊天`)
    router.push({
      path: '/private-chat',
      query: {
        target_user_id: targetUserId,
        compatibility_score: compatibilityScore,
        match_type: matchType,
        match_source: 'phase_connect'
      }
    })
  } catch (error) {
    console.error('创建聊天失败:', error)
    
    ElMessage.info(`正在打开与 ${userName} 的聊天页面...`)
    router.push({
      path: '/private-chat',
      query: {
        target_user_id: targetUserId,
        compatibility_score: compatibilityScore,
        match_type: matchType,
        match_source: 'phase_connect'
      }
    })
  }
}

onMounted(() => {
  loadMyChart()
})
</script>

<style lang="scss" scoped>
.phase-connect {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
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
  animation: twinkle 4s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}

.connect-main {
  position: relative;
  z-index: 10;
  min-height: 100vh;
  padding: 20px 24px;
  max-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;
}

.quick-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(20, 20, 50, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.4);
  }

  &.active {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.3) 0%, rgba(139, 92, 246, 0.2) 100%);
    border-color: rgba(236, 72, 153, 0.4);
  }
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.nav-arrow {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.connect-header {
  text-align: center;
  margin-bottom: 24px;
}

.header-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(236, 72, 153, 0.25); }
  50% { box-shadow: 0 0 40px rgba(236, 72, 153, 0.4); }
}

.header-emoji {
  font-size: 2rem;
}

.main-title {
  margin: 0 0 6px 0;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.9rem;
}

.loading-section,
.no-chart-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-icon {
  margin-bottom: 16px;
  color: #a78bfa;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.95rem;
}

.no-chart-card {
  text-align: center;
  padding: 40px;
  background: rgba(20, 20, 50, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  max-width: 450px;
}

.no-chart-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.no-chart-title {
  margin: 0 0 12px 0;
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
}

.no-chart-desc {
  margin: 0 0 20px 0;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  line-height: 1.6;
}

.go-astro-btn {
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  border: none;
  
  &:hover {
    box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
  }
}

.connect-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.title-icon {
  font-size: 1.1rem;
}

.my-phases-card,
.match-status-card,
.recent-matches-section,
.phase-visualization-section {
  background: rgba(18, 18, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;
}

.aspect-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 16px 12px;
  background: rgba(30, 30, 60, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);

  &.harmonious {
    border-color: rgba(34, 197, 94, 0.3);
    background: rgba(34, 197, 94, 0.08);
  }

  &.challenging {
    border-color: rgba(249, 115, 22, 0.3);
    background: rgba(249, 115, 22, 0.08);
  }

  &.neutral {
    border-color: rgba(234, 179, 8, 0.3);
    background: rgba(234, 179, 8, 0.08);
  }
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.subsection-title,
.section-subtitle {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(30, 30, 60, 0.4);
  border-radius: 10px;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(40, 40, 80, 0.4);
  }

  &.harmonious {
    border-left-color: #22c55e;
  }

  &.challenging {
    border-left-color: #f97316;
  }

  &.neutral {
    border-left-color: #eab308;
  }
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 8px;
}

.planet-symbol {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 50%;
  font-size: 0.9rem;
  color: #a78bfa;
}

.aspect-symbol {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 50%;
  font-size: 1rem;
  color: #8b5cf6;
}

.aspect-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.aspect-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.aspect-planets-name {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.aspect-orb {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.no-aspects {
  text-align: center;
  padding: 30px;
  color: rgba(255, 255, 255, 0.4);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.status-item {
  text-align: center;
  padding: 16px 12px;
  background: rgba(30, 30, 60, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.status-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #a78bfa;
}

.status-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.match-actions {
  text-align: center;
}

.match-btn {
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  border: none;
  
  &:hover:not(:disabled) {
    box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
  }
}

.matches-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.match-card {
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
    background: rgba(40, 40, 80, 0.5);
    transform: translateY(-2px);
  }
}

.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.match-users {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.2));
  border-radius: 50%;

  &.small {
    width: 32px;
    height: 32px;
  }
}

.avatar-placeholder {
  font-size: 1rem;
}

.connect-arrow {
  color: #a78bfa;
  font-size: 0.9rem;
}

.match-score {
  text-align: right;
}

.score-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
  display: block;
}

.score-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #22c55e;
}

.match-aspects {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.match-aspect {
  padding: 4px 10px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 4px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.more-aspects {
  font-size: 0.7rem;
  color: #a78bfa;
}

.match-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.match-time {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.phase-visualization-section {
  grid-column: 1 / -1;
}

.visualization-container {
  min-height: 350px;
  background: radial-gradient(circle at center, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.phase-network-placeholder {
  position: relative;
  width: 300px;
  height: 300px;
}

.network-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.center-node {
  width: 60px;
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ec4899, #8b5cf6);
  border-radius: 50%;
  box-shadow: 0 0 30px rgba(236, 72, 153, 0.4);
}

.node-icon {
  font-size: 1.25rem;
}

.node-label {
  font-size: 0.7rem;
  color: #fff;
  margin-top: 2px;
}

.connecting-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.connected-node {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(20, 20, 50, 0.8);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  backdrop-filter: blur(10px);
}

.node-avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 50%;
}

.node-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.connection-type {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }
  
  &.challenging {
    background: rgba(249, 115, 22, 0.2);
    color: #f97316;
  }
  
  &.mixed {
    background: rgba(234, 179, 8, 0.2);
    color: #eab308;
  }
  
  &.strong {
    background: rgba(236, 72, 153, 0.2);
    color: #ec4899;
  }
}

.node-score {
  font-size: 0.75rem;
  font-weight: 600;
  color: #a78bfa;
}

.no-connections-hint {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.85rem;
}

.match-detail-dialog :deep(.el-dialog__body) {
  padding: 24px;
  background: linear-gradient(180deg, #0a0a1a, #1a1a3e);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.detail-persons {
  display: flex;
  align-items: center;
  gap: 16px;
}

.person-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.person-avatar {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.2));
  border-radius: 50%;
}

.person-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.person-name {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.connection-symbol {
  color: #a78bfa;
}

.detail-score {
  text-align: center;
}

.score-circle {
  width: 80px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 3px solid var(--score-color);
  background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
}

.score-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--score-color);
}

.score-unit {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.score-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.shared-aspects-section,
.synastry-preview-section {
  margin-bottom: 24px;
}

.shared-aspects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.shared-aspect-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: rgba(30, 30, 60, 0.5);
  border-radius: 10px;
  border-left: 3px solid transparent;

  &.harmonious {
    border-left-color: #22c55e;
    background: rgba(34, 197, 94, 0.05);
  }

  &.challenging {
    border-left-color: #f97316;
    background: rgba(249, 115, 22, 0.05);
  }
}

.aspect-display {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.planet {
  font-size: 0.9rem;
  font-weight: 600;
  color: #a78bfa;
}

.aspect-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 50%;
  font-size: 1rem;
  color: #8b5cf6;
}

.aspect-meaning {
  flex: 1;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
}

.synastry-highlights {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}

.highlight-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: rgba(30, 30, 60, 0.5);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.highlight-icon {
  font-size: 1.5rem;
}

.highlight-content {
  flex: 1;
}

.highlight-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.highlight-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.5;
}

.detail-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(139, 92, 246, 0.2);
}
</style>
