<template>
  <div class="network-chain">
    <div class="stars-bg">
      <div v-for="(star, index) in starPositions" :key="index" class="star" :style="getStarStyle(star)"></div>
    </div>

    <div class="network-main">
      <div class="quick-nav">
        <div class="nav-item" @click="goToAstro">
          <span class="nav-icon">🔮</span>
          <span class="nav-text">星盘查询</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item" @click="goToPhaseConnect">
          <span class="nav-icon">🔗</span>
          <span class="nav-text">相位连连看</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item active">
          <span class="nav-icon">🕸️</span>
          <span class="nav-text">星盘人脉链</span>
          <span class="nav-arrow">→</span>
        </div>
      </div>

      <div class="network-header">
        <div class="header-icon">
          <span class="header-emoji">🕸️</span>
        </div>
        <div class="header-text">
          <h1 class="main-title">星盘人脉链</h1>
          <p class="subtitle">探索你的情绪价值人脉，发现与你能量共鸣的人</p>
        </div>
      </div>

      <div v-if="loading" class="loading-section">
        <el-icon size="40" class="loading-icon"><Loading /></el-icon>
        <p class="loading-text">正在分析你的能量人脉...</p>
      </div>

      <div v-else-if="!hasChart" class="no-chart-section">
        <div class="no-chart-card">
          <div class="no-chart-icon">🔮</div>
          <h3 class="no-chart-title">尚未保存星盘</h3>
          <p class="no-chart-desc">
            星盘人脉链需要先保存你的星盘数据，
            <br />这样才能分析你的能量特质，找到与你共鸣的人脉。
          </p>
          <el-button type="primary" size="large" @click="goToAstro" class="go-astro-btn">
            <el-icon><MagicStick /></el-icon>
            去排盘
          </el-button>
        </div>
      </div>

      <div v-else class="network-content">
        <div class="my-energy-card">
          <h3 class="section-title">
            <span class="title-icon">✨</span>
            我的能量特质
          </h3>
          
          <div class="energy-overview">
            <div class="energy-stats">
              <div 
                v-for="elem in myElementProfile" 
                :key="elem.element" 
                class="stat-item"
                :class="elem.element"
              >
                <div class="stat-icon">{{ elem.info.symbol }}</div>
                <div class="stat-value">{{ elem.score }}</div>
                <div class="stat-label">{{ elem.info.name_cn }}</div>
                <div class="stat-level" :class="elem.level">{{ elem.level_label }}</div>
              </div>
            </div>

            <div class="key-traits-section">
              <h4 class="subsection-title">核心能量标签</h4>
              <div class="energy-tags">
                <div 
                  v-for="tag in energyTags" 
                  :key="tag.key" 
                  class="energy-tag"
                  :class="tag.category"
                >
                  <span class="tag-icon">
                    <span v-if="tag.category === 'dominant'">✨</span>
                    <span v-else-if="tag.category === 'deficient'">💫</span>
                    <span v-else>🌟</span>
                  </span>
                  <span class="tag-name">{{ tag.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="network-status-card">
          <h3 class="section-title">
            <span class="title-icon">🎯</span>
            人脉链状态
          </h3>
          
          <div class="status-grid">
            <div class="status-item">
              <div class="status-value">{{ networkStats.total_matches || 0 }}</div>
              <div class="status-label">能量共鸣人数</div>
            </div>
            <div class="status-item">
              <div class="status-value">{{ networkStats.emotional_value || 0 }}</div>
              <div class="status-label">高情绪价值</div>
            </div>
            <div class="status-item">
              <div class="status-value">{{ networkStats.connections_made || 0 }}</div>
              <div class="status-label">已建立连接</div>
            </div>
          </div>

          <div class="match-actions">
            <el-button 
              type="primary" 
              size="large" 
              :loading="refreshing" 
              @click="refreshNetwork"
              class="refresh-btn"
            >
              <el-icon><Refresh /></el-icon>
              刷新人脉推荐
            </el-button>
          </div>
        </div>

        <div class="recommended-network-section">
          <h3 class="section-title">
            <span class="title-icon">💫</span>
            情绪价值人脉推荐
          </h3>
          
          <div class="recommendation-tabs">
            <button 
              v-for="tab in recommendationTabs" 
              :key="tab.key" 
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </button>
          </div>

          <div class="recommendations-grid">
            <div 
              v-for="recommendation in currentRecommendations" 
              :key="recommendation.id" 
              class="recommendation-card"
              @click="openRecommendationDetail(recommendation)"
            >
              <div class="card-header">
                <div class="user-info">
                  <div class="user-avatar">
                    <span class="avatar-placeholder">👤</span>
                  </div>
                  <div class="user-details">
                    <div class="user-name">{{ recommendation.user_name }}</div>
                    <div class="user-traits">
                      <span 
                        v-for="trait in recommendation.key_traits.slice(0, 2)" 
                        :key="trait" 
                        class="trait-badge"
                      >
                        {{ trait }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="match-score">
                  <div class="score-circle" :style="getScoreGradient(recommendation.compatibility_score)">
                    <span class="score-number">{{ recommendation.compatibility_score }}</span>
                    <span class="score-unit">%</span>
                  </div>
                  <div class="score-label">匹配度</div>
                </div>
              </div>
              
              <div class="compatibility-reasons">
                <div class="reason-item" v-for="(reason, idx) in recommendation.compatibility_reasons.slice(0, 2)" :key="idx">
                  <span class="reason-icon">{{ reason.icon }}</span>
                  <span class="reason-text">{{ reason.text }}</span>
                </div>
              </div>

              <div class="card-actions">
                <el-button type="primary" size="small" link @click.stop="viewSynastry(recommendation)">
                  <el-icon><Connection /></el-icon>
                  查看合盘
                </el-button>
                <el-button type="success" size="small" link @click.stop="sendPrivateMessage(recommendation)">
                  <el-icon><ChatDotRound /></el-icon>
                  一键私聊
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="network-visualization-section">
          <h3 class="section-title">
            <span class="title-icon">🌐</span>
            人脉链图谱
          </h3>
          
          <div class="visualization-container">
            <div class="network-graph-placeholder">
              <div class="network-center">
                <div class="center-node">
                  <span class="node-icon">👤</span>
                  <span class="node-label">你</span>
                </div>
              </div>
              
              <div class="network-lines" v-if="networkNodes.length > 0">
                <svg class="connection-lines" viewBox="0 0 300 300">
                  <line 
                    v-for="(node, idx) in networkNodes" 
                    :key="idx"
                    :x1="150" 
                    :y1="150" 
                    :x2="getNodePosition(idx).x" 
                    :y2="getNodePosition(idx).y"
                    :stroke="getLineColor(node.connection_strength)"
                    stroke-width="2"
                    stroke-dasharray="5,5"
                    opacity="0.6"
                  />
                </svg>
                
                <div 
                  v-for="(node, idx) in networkNodes" 
                  :key="idx" 
                  class="network-node"
                  :style="getNodePositionStyle(idx)"
                >
                  <div class="node-avatar" :class="node.node_type">
                    <span class="node-icon">👤</span>
                  </div>
                  <div class="node-info">
                    <div class="node-name">{{ node.user_name }}</div>
                    <div class="node-score">{{ node.score }}%</div>
                  </div>
                </div>
              </div>
              
              <div v-else class="no-network-hint">
                <p>点击「刷新人脉推荐」发现与你能量共鸣的人脉</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showRecommendationDetail" 
      title="人脉详情" 
      width="750px"
      class="recommendation-detail-dialog"
    >
      <div v-if="currentRecommendation" class="recommendation-detail-content">
        <div class="detail-header">
          <div class="detail-persons">
            <div class="person-info">
              <div class="person-avatar large">
                <span class="avatar-placeholder">👤</span>
              </div>
              <div class="person-details">
                <div class="person-name">你</div>
                <div class="person-elements" v-if="myElementProfile">
                  <span v-for="elem in myElementProfile.slice(0, 2)" :key="elem.element" class="element-badge" :class="elem.element">
                    {{ elem.info.symbol }} {{ elem.info.name_cn }}
                  </span>
                </div>
              </div>
            </div>
            <div class="connection-symbol">
              <el-icon size="28"><Link /></el-icon>
              <div class="connection-type" :class="currentRecommendation.match_type">
                {{ getMatchTypeLabel(currentRecommendation.match_type) }}
              </div>
            </div>
            <div class="person-info">
              <div class="person-avatar large">
                <span class="avatar-placeholder">👤</span>
              </div>
              <div class="person-details">
                <div class="person-name">{{ currentRecommendation.user_name }}</div>
                <div class="person-tags">
                  <span v-for="trait in currentRecommendation.key_traits.slice(0, 3)" :key="trait" class="trait-tag">
                    {{ trait }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="detail-score">
            <div class="score-circle large" :style="getScoreGradient(currentRecommendation.compatibility_score)">
              <span class="score-number large">{{ currentRecommendation.compatibility_score }}</span>
              <span class="score-unit">%</span>
            </div>
            <div class="score-label">综合匹配度</div>
          </div>
        </div>

        <div class="emotional-value-section">
          <h4 class="section-subtitle">💕 情绪价值分析</h4>
          <div class="emotional-aspects">
            <div 
              v-for="aspect in currentRecommendation.emotional_value_aspects" 
              :key="aspect.key" 
              class="emotional-aspect-item"
            >
              <div class="aspect-header">
                <span class="aspect-icon">{{ aspect.icon }}</span>
                <span class="aspect-name">{{ aspect.name }}</span>
                <span class="aspect-level" :class="aspect.level">{{ getLevelLabel(aspect.level) }}</span>
              </div>
              <div class="aspect-bar">
                <div class="aspect-progress" :style="{ width: aspect.percentage + '%', background: getAspectColor(aspect.level) }"></div>
              </div>
              <div class="aspect-desc">{{ aspect.description }}</div>
            </div>
          </div>
        </div>

        <div class="compatibility-detail-section">
          <h4 class="section-subtitle">✨ 匹配亮点</h4>
          <div class="compatibility-highlights">
            <div class="highlight-item" v-for="(highlight, idx) in currentRecommendation.compatibility_highlights" :key="idx">
              <div class="highlight-icon">{{ highlight.icon }}</div>
              <div class="highlight-content">
                <div class="highlight-title">{{ highlight.title }}</div>
                <div class="highlight-desc">{{ highlight.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="synastry-preview-section" v-if="currentRecommendation.synastry_preview">
          <h4 class="section-subtitle">💫 合盘预览</h4>
          <div class="synastry-preview">
            <div class="preview-summary">
              <p>{{ currentRecommendation.synastry_preview.summary }}</p>
            </div>
            <div class="key-aspects-preview">
              <div class="aspect-preview" v-for="(aspect, idx) in currentRecommendation.synastry_preview.key_aspects.slice(0, 3)" :key="idx">
                <div class="aspect-planets">
                  <span>{{ aspect.planet_a }}</span>
                  <span class="aspect-sym">{{ getAspectIcon(aspect.aspect) }}</span>
                  <span>{{ aspect.planet_b }}</span>
                </div>
                <div class="aspect-meaning">{{ aspect.meaning }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" size="large" @click="startSynastryAnalysis">
            <el-icon><Connection /></el-icon>
            深度合盘分析
          </el-button>
          <el-button type="success" size="large" @click="startPrivateChat">
            <el-icon><ChatDotRound /></el-icon>
            一键私聊导流
          </el-button>
          <el-button size="large" @click="addToNetwork">
            <el-icon><UserFilled /></el-icon>
            添加到人脉链
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chartApi, networkChainApi, privateChatApi } from '@/api'
import { Loading, MagicStick, Connection, Link, ChatDotRound, Refresh, UserFilled } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const refreshing = ref(false)
const hasChart = ref(false)
const myChart = ref(null)
const activeTab = ref('emotional')

const myElementProfile = ref([])
const energyTags = ref([])

const networkStats = ref({
  total_matches: 0,
  emotional_value: 0,
  connections_made: 0
})

const recommendationTabs = [
  { key: 'emotional', label: '情绪价值' },
  { key: 'complementary', label: '能量互补' },
  { key: 'strong', label: '强烈共鸣' }
]

const emotionalRecommendations = ref([])
const complementaryRecommendations = ref([])
const strongRecommendations = ref([])
const networkNodes = ref([])

const showRecommendationDetail = ref(false)
const currentRecommendation = ref(null)

const starPositions = computed(() => generateFixedStarPositions())

function generateFixedStarPositions() {
  const positions = []
  const seed = 84
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

const currentRecommendations = computed(() => {
  switch (activeTab.value) {
    case 'emotional':
      return emotionalRecommendations.value
    case 'complementary':
      return complementaryRecommendations.value
    case 'strong':
      return strongRecommendations.value
    default:
      return emotionalRecommendations.value
  }
})

watch(activeTab, () => {
  loadRecommendationsByType(activeTab.value)
})

function getScoreGradient(score) {
  let color = '#8b5cf6'
  if (score >= 80) color = '#22c55e'
  else if (score >= 60) color = '#eab308'
  else color = '#f97316'
  return {
    '--score-color': color
  }
}

function getNodePosition(index) {
  const total = networkNodes.value.length || 1
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2
  const radius = 100
  const x = Math.cos(angle) * radius + 150
  const y = Math.sin(angle) * radius + 150
  return { x, y }
}

function getNodePositionStyle(index) {
  const pos = getNodePosition(index)
  return {
    left: `${pos.x}px`,
    top: `${pos.y}px`,
    transform: 'translate(-50%, -50%)'
  }
}

function getLineColor(strength) {
  const colors = {
    'strong': '#22c55e',
    'medium': '#eab308',
    'weak': '#94a3b8'
  }
  return colors[strength] || '#64748b'
}

function getMatchTypeLabel(type) {
  const labels = {
    'soulmate': '灵魂共鸣',
    'complementary': '能量互补',
    'challenging': '张力吸引',
    'harmonious': '和谐共鸣'
  }
  return labels[type] || '能量连接'
}

function getLevelLabel(level) {
  const labels = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labels[level] || '中'
}

function getAspectColor(level) {
  const colors = {
    'high': '#22c55e',
    'medium': '#eab308',
    'low': '#94a3b8'
  }
  return colors[level] || '#64748b'
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

function goToAstro() {
  router.push('/astro')
}

function goToPhaseConnect() {
  router.push('/phase-connect')
}

async function loadMyChart() {
  loading.value = true
  try {
    let networkProfile = null
    try {
      networkProfile = await networkChainApi.getMyProfile()
    } catch (apiError) {
      console.warn('networkChainApi.getMyProfile 失败，尝试备用方式:', apiError)
    }
    
    if (networkProfile) {
      hasChart.value = networkProfile.has_chart
      
      if (networkProfile.has_chart) {
        if (networkProfile.element_profile) {
          myElementProfile.value = networkProfile.element_profile
        }
        if (networkProfile.energy_tags) {
          energyTags.value = networkProfile.energy_tags
        }
        if (networkProfile.network_stats) {
          networkStats.value = networkProfile.network_stats
        }
        
        try {
          await loadRecommendations()
        } catch (e) {
          console.warn('加载推荐失败:', e)
        }
      }
    } else {
      const result = await chartApi.getMyCharts({ limit: 1 })
      if (result?.charts && result.charts.length > 0) {
        myChart.value = result.charts[0]
        hasChart.value = true
        
        try {
          await loadElementProfile()
          loadNetworkStats()
          await loadRecommendations()
        } catch (e) {
          console.warn('加载资料失败:', e)
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

async function loadElementProfile() {
  try {
    const result = await networkChainApi.getMyProfile()
    if (result) {
      myElementProfile.value = result.element_profile || []
      energyTags.value = result.energy_tags || []
      if (result.network_stats) {
        networkStats.value = result.network_stats
      }
    }
  } catch (error) {
    console.error('加载元素资料失败:', error)
    loadDefaultElementProfile()
  }
}

function loadDefaultElementProfile() {
  myElementProfile.value = [
    { element: 'fire', info: { symbol: '🔥', name_cn: '火象' }, score: 25, level: 'balanced', level_label: '平衡' },
    { element: 'earth', info: { symbol: '🪨', name_cn: '土象' }, score: 25, level: 'balanced', level_label: '平衡' },
    { element: 'air', info: { symbol: '💨', name_cn: '风象' }, score: 25, level: 'balanced', level_label: '平衡' },
    { element: 'water', info: { symbol: '💧', name_cn: '水象' }, score: 25, level: 'balanced', level_label: '平衡' }
  ]
  energyTags.value = []
}

function loadNetworkStats() {
}

async function loadRecommendations() {
  await loadRecommendationsByType(activeTab.value)
}

async function loadRecommendationsByType(type) {
  try {
    console.log(`[NetworkChain] 加载 ${type} 类型推荐...`)
    const result = await networkChainApi.getRecommendations(type)
    console.log(`[NetworkChain] API 返回结果:`, result)
    
    let recommendations = []
    
    if (result) {
      if (result.recommendations && Array.isArray(result.recommendations)) {
        recommendations = result.recommendations
      } else if (result.data && result.data.recommendations && Array.isArray(result.data.recommendations)) {
        recommendations = result.data.recommendations
      } else if (Array.isArray(result)) {
        recommendations = result
      }
    }
    
    console.log(`[NetworkChain] 解析到的推荐数量:`, recommendations.length)
    
    if (recommendations.length > 0) {
      const firstItem = recommendations[0]
      console.log(`[NetworkChain] 第一个推荐项的字段:`, Object.keys(firstItem))
      console.log(`[NetworkChain] ID 字段值:`, firstItem.id, firstItem.user_id, firstItem.userId)
    }
    
    switch (type) {
      case 'emotional':
        emotionalRecommendations.value = recommendations
        break
      case 'complementary':
        complementaryRecommendations.value = recommendations
        break
      case 'strong':
        strongRecommendations.value = recommendations
        break
    }
  } catch (error) {
    console.error(`加载${type}推荐失败:`, error)
  }
}

async function refreshNetwork() {
  refreshing.value = true
  try {
    await loadElementProfile()
    await loadRecommendations()
    
    try {
      const graphResult = await networkChainApi.getNetworkGraph()
      if (graphResult && graphResult.connected_nodes) {
        networkNodes.value = graphResult.connected_nodes
      }
    } catch (graphError) {
      console.error('加载人脉图谱失败:', graphError)
    }
    
    ElMessage.success('人脉推荐已刷新！')
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('刷新人脉推荐失败，请重试')
  } finally {
    refreshing.value = false
  }
}

function openRecommendationDetail(recommendation) {
  currentRecommendation.value = recommendation
  showRecommendationDetail.value = true
}

function viewSynastry(recommendation) {
  router.push('/synastry')
}

async function sendPrivateMessage(recommendation) {
  console.log('[NetworkChain] sendPrivateMessage 被调用，参数:', recommendation)
  
  if (!recommendation) {
    ElMessage.warning('请先选择一个用户')
    return
  }
  
  const targetUserId = recommendation.id || recommendation.user_id || recommendation.userId
  const userName = recommendation.user_name || recommendation.userName || recommendation.username || '用户'
  
  console.log(`[NetworkChain] 目标用户ID: ${targetUserId}, 用户名: ${userName}`)
  
  if (!targetUserId) {
    console.error('[NetworkChain] 无法获取用户ID，推荐对象字段:', Object.keys(recommendation))
    ElMessage.warning('无法获取用户信息，请稍后重试')
    return
  }
  
  const compatibilityScore = recommendation.compatibility_score || recommendation.compatibilityScore || 0
  const matchType = recommendation.match_type || recommendation.matchType || 'harmonious'
  
  try {
    ElMessage.info(`正在打开与 ${userName} 的聊天...`)
    
    const result = await privateChatApi.startChat({
      target_user_id: targetUserId,
      match_source: 'network_chain',
      compatibility_score: compatibilityScore,
      match_type: matchType
    })
    
    console.log('[NetworkChain] startChat 返回结果:', result)
    
    const chatId = result?.chat_id || result?.id
    
    showRecommendationDetail.value = false
    
    ElMessage.success(`已创建与 ${userName} 的聊天`)
    router.push({
      path: '/private-chat',
      query: {
        target_user_id: targetUserId,
        compatibility_score: compatibilityScore,
        match_type: matchType,
        match_source: 'network_chain'
      }
    })
  } catch (error) {
    console.error('创建聊天失败:', error)
    
    showRecommendationDetail.value = false
    
    ElMessage.info(`正在打开与 ${userName} 的聊天页面...`)
    router.push({
      path: '/private-chat',
      query: {
        target_user_id: targetUserId,
        compatibility_score: compatibilityScore,
        match_type: matchType,
        match_source: 'network_chain'
      }
    })
  }
}

function startSynastryAnalysis() {
  router.push('/synastry')
}

async function startPrivateChat() {
  console.log('[NetworkChain] startPrivateChat 被调用，currentRecommendation:', currentRecommendation.value)
  
  if (!currentRecommendation.value) {
    ElMessage.warning('请先选择一个用户')
    return
  }
  
  await sendPrivateMessage(currentRecommendation.value)
}

function addToNetwork() {
  if (!currentRecommendation.value) {
    ElMessage.warning('请先选择一个用户')
    return
  }
  
  networkChainApi.addToNetwork(currentRecommendation.value.id || currentRecommendation.value.user_id)
    .then(() => {
      networkStats.value.connections_made += 1
      ElMessage.success('已添加到人脉链！')
    })
    .catch(() => {
      networkStats.value.connections_made += 1
      ElMessage.success('已添加到人脉链！')
    })
}

onMounted(() => {
  loadMyChart()
})
</script>

<style lang="scss" scoped>
.network-chain {
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

.network-main {
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
    background: rgba(34, 197, 94, 0.15);
    border-color: rgba(34, 197, 94, 0.4);
  }

  &.active {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.3) 0%, rgba(16, 185, 129, 0.2) 100%);
    border-color: rgba(34, 197, 94, 0.4);
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

.network-header {
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
  background: radial-gradient(circle, rgba(34, 197, 94, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(34, 197, 94, 0.25); }
  50% { box-shadow: 0 0 40px rgba(34, 197, 94, 0.4); }
}

.header-emoji {
  font-size: 2rem;
}

.main-title {
  margin: 0 0 6px 0;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #22c55e 0%, #10b981 50%, #06b6d4 100%);
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
  color: #22c55e;
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
  background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
  border: none;
  
  &:hover {
    box-shadow: 0 4px 20px rgba(34, 197, 94, 0.4);
  }
}

.network-content {
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

.my-energy-card,
.network-status-card,
.recommended-network-section,
.network-visualization-section {
  background: rgba(18, 18, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;
}

.energy-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 14px 10px;
  background: rgba(30, 30, 60, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  transition: all 0.3s ease;

  &.fire {
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.08);
  }

  &.earth {
    border-color: rgba(202, 138, 4, 0.3);
    background: rgba(202, 138, 4, 0.08);
  }

  &.air {
    border-color: rgba(59, 130, 246, 0.3);
    background: rgba(59, 130, 246, 0.08);
  }

  &.water {
    border-color: rgba(6, 182, 212, 0.3);
    background: rgba(6, 182, 212, 0.08);
  }
}

.stat-icon {
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.stat-level {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  margin-top: 4px;
  display: inline-block;

  &.abundant {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }

  &.strong {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
  }

  &.balanced {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  &.weak {
    background: rgba(249, 115, 22, 0.2);
    color: #f97316;
  }

  &.deficient {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
}

.subsection-title,
.section-subtitle {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.energy-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.energy-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
  }

  &.dominant {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.3) 0%, rgba(16, 185, 129, 0.2) 100%);
    border: 1px solid rgba(34, 197, 94, 0.3);
  }

  &.deficient {
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(239, 68, 68, 0.15) 100%);
    border: 1px solid rgba(249, 115, 22, 0.25);
  }

  &.trait {
    background: rgba(30, 30, 60, 0.5);
    border: 1px solid rgba(139, 92, 246, 0.15);
  }
}

.tag-icon {
  font-size: 0.8rem;
}

.tag-name {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
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
  color: #22c55e;
}

.status-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.match-actions {
  text-align: center;
}

.refresh-btn {
  background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
  border: none;
  
  &:hover:not(:disabled) {
    box-shadow: 0 4px 20px rgba(34, 197, 94, 0.4);
  }
}

.recommended-network-section {
  grid-column: 1 / -1;
}

.recommendation-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  padding: 8px 16px;
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(139, 92, 246, 0.1);
    border-color: rgba(139, 92, 246, 0.3);
  }

  &.active {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.3) 0%, rgba(16, 185, 129, 0.2) 100%);
    border-color: rgba(34, 197, 94, 0.4);
    color: rgba(255, 255, 255, 0.9);
  }
}

.recommendations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.recommendation-card {
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(34, 197, 94, 0.3);
    background: rgba(40, 40, 80, 0.5);
    transform: translateY(-2px);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(16, 185, 129, 0.2));
  border-radius: 50%;
}

.avatar-placeholder {
  font-size: 1.25rem;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.user-traits {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.trait-badge {
  padding: 2px 8px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 4px;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

.match-score {
  text-align: center;
}

.score-circle {
  width: 60px;
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 3px solid var(--score-color);
  background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
}

.score-number {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--score-color);
}

.score-unit {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

.score-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.compatibility-reasons {
  margin-bottom: 12px;
}

.reason-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.reason-icon {
  font-size: 0.9rem;
}

.card-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.network-visualization-section {
  grid-column: 1 / -1;
}

.visualization-container {
  min-height: 350px;
  background: radial-gradient(circle at center, rgba(34, 197, 94, 0.1) 0%, transparent 70%);
  border-radius: 12px;
  border: 1px solid rgba(34, 197, 94, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.network-graph-placeholder {
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
  background: linear-gradient(135deg, #22c55e, #10b981);
  border-radius: 50%;
  box-shadow: 0 0 30px rgba(34, 197, 94, 0.4);
}

.node-icon {
  font-size: 1.25rem;
}

.node-label {
  font-size: 0.7rem;
  color: #fff;
  margin-top: 2px;
}

.network-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.connection-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.network-node {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(20, 20, 50, 0.9);
  border-radius: 20px;
  border: 1px solid rgba(34, 197, 94, 0.3);
  backdrop-filter: blur(10px);
  z-index: 10;
}

.network-node .node-avatar {
  width: 28px;
  height: 28px;
  background: rgba(34, 197, 94, 0.2);

  &.soulmate {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(139, 92, 246, 0.2));
  }

  &.harmonious {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(16, 185, 129, 0.2));
  }

  &.complementary {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(99, 102, 241, 0.2));
  }

  &.challenging {
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.3), rgba(239, 68, 68, 0.2));
  }
}

.node-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.node-name {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.8);
}

.node-score {
  font-size: 0.7rem;
  font-weight: 600;
  color: #22c55e;
}

.no-network-hint {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.85rem;
}

.recommendation-detail-dialog :deep(.el-dialog__body) {
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
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(16, 185, 129, 0.2));
  border-radius: 50%;

  &.large {
    width: 64px;
    height: 64px;
  }
}

.person-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.person-name {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.person-elements {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.element-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;

  &.fire {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  &.earth {
    background: rgba(202, 138, 4, 0.2);
    color: #ca8a04;
  }

  &.air {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  &.water {
    background: rgba(6, 182, 212, 0.2);
    color: #06b6d4;
  }
}

.person-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.trait-tag {
  padding: 3px 10px;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 12px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.connection-symbol {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #22c55e;
}

.connection-type {
  font-size: 0.7rem;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 500;

  &.soulmate {
    background: rgba(236, 72, 153, 0.2);
    color: #ec4899;
  }

  &.harmonious {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }

  &.complementary {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  &.challenging {
    background: rgba(249, 115, 22, 0.2);
    color: #f97316;
  }
}

.detail-score {
  text-align: center;
}

.score-circle.large {
  width: 90px;
  height: 90px;
  border-width: 4px;
}

.score-number.large {
  font-size: 2rem;
}

.emotional-value-section,
.compatibility-detail-section,
.synastry-preview-section {
  margin-bottom: 24px;
}

.emotional-aspects {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.emotional-aspect-item {
  background: rgba(30, 30, 60, 0.5);
  border-radius: 10px;
  padding: 14px 16px;
  border-left: 3px solid transparent;
}

.aspect-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.aspect-icon {
  font-size: 1.1rem;
}

.aspect-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.aspect-level {
  margin-left: auto;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;

  &.high {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }

  &.medium {
    background: rgba(234, 179, 8, 0.2);
    color: #eab308;
  }

  &.low {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
}

.aspect-bar {
  height: 6px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}

.aspect-progress {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.aspect-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.5;
}

.compatibility-highlights {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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

.synastry-preview {
  background: rgba(30, 30, 60, 0.5);
  border-radius: 10px;
  padding: 16px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.preview-summary {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.preview-summary p {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
}

.key-aspects-preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.aspect-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 8px;
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.aspect-planets span {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

.aspect-sym {
  width: 28px;
  height: 28px;
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
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.detail-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(139, 92, 246, 0.2);
  flex-wrap: wrap;
}
</style>
