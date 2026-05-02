<template>
  <div class="star-resonance-pool">
    <div class="stars-bg">
      <div v-for="i in 120" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="nebula-container">
      <div 
        class="nebula-main"
        :style="nebulaStyle"
      >
        <div class="nebula-layer nebula-core"></div>
        <div class="nebula-layer nebula-ring-1"></div>
        <div class="nebula-layer nebula-ring-2"></div>
        <div class="nebula-layer nebula-sparkles">
          <div 
            v-for="sparkle in sparkles" 
            :key="sparkle.id" 
            class="sparkle"
            :style="sparkle.style"
          ></div>
        </div>
      </div>
      
      <div class="nebula-glow" :style="glowStyle"></div>
    </div>

    <div class="resonance-main">
      <div class="header-section">
        <div class="back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回气象站</span>
        </div>
        <div class="header-text">
          <h1 class="main-title">星能共鸣池</h1>
          <p class="subtitle">全服星云能量汇聚之所</p>
        </div>
      </div>

      <div class="content-grid">
        <div class="main-panel">
          <div class="pool-status-card">
            <div class="tier-display">
              <div class="tier-badge" :class="currentTier">
                <span class="tier-name">{{ currentTierInfo?.name }}</span>
                <span class="tier-num">{{ currentTierNum }}/{{ totalTiers }}</span>
              </div>
              
              <div class="progress-section">
                <div class="progress-labels">
                  <span class="current-energy">{{ formatEnergy(poolStatus?.current_energy || 0) }}</span>
                  <span class="next-tier" v-if="poolStatus?.next_tier">
                    下一挡位需 {{ formatEnergy(poolStatus.next_tier.energy_needed) }}
                  </span>
                </div>
                <el-progress 
                  :percentage="poolStatus?.tier_progress || 0" 
                  :show-text="false"
                  :stroke-width="12"
                  :color="tierProgressColor"
                />
              </div>
            </div>

            <div class="element-distribution">
              <h3 class="section-title">元素能量分布</h3>
              <div class="element-bars">
                <div 
                  v-for="(elem, key) in elementDistribution" 
                  :key="key"
                  class="element-bar-row"
                >
                  <div class="element-header">
                    <span class="element-icon" :style="{ color: elem.color }">
                      {{ getElementIcon(key) }}
                    </span>
                    <span class="element-name">{{ elem.name }}</span>
                    <span class="element-energy">{{ formatEnergy(elem.energy) }}</span>
                  </div>
                  <el-progress 
                    :percentage="elem.percentage" 
                    :show-text="false"
                    :stroke-width="6"
                    :color="elem.color"
                  />
                  <div class="element-effects" v-if="elem.effects">
                    <span 
                      v-for="(value, effectKey) in elem.effects" 
                      :key="effectKey"
                      class="effect-tag"
                    >
                      {{ getEffectLabel(effectKey) }}: +{{ formatEffect(value, effectKey) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="active-effects" v-if="poolStatus?.active_effects">
              <h3 class="section-title">全服增益效果</h3>
              <div class="effects-grid">
                <div 
                  v-for="(value, key) in poolStatus.active_effects" 
                  :key="key"
                  class="effect-card"
                >
                  <span class="effect-icon">{{ getEffectIcon(key) }}</span>
                  <span class="effect-label">{{ getEffectLabel(key) }}</span>
                  <span class="effect-value">+{{ formatEffect(value, key) }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="refine-card" v-if="isLoggedIn">
            <h3 class="section-title">炼化能量</h3>
            
            <div class="fragment-info">
              <div class="balance-display">
                <span class="balance-icon">💎</span>
                <span class="balance-label">星元碎片余额</span>
                <span class="balance-value">{{ userAssets?.stardust_fragment_balance || 0 }}</span>
              </div>
              <div class="base-cost">
                每颗行星基础消耗: <span class="cost-highlight">{{ BASE_FRAGMENT_COST }}</span> 碎片
              </div>
            </div>

            <div class="strong-planets-section" v-if="strongPlanets.length > 0">
              <p class="section-desc">选择您星盘中的强势行星进行炼化</p>
              <div class="planets-grid">
                <div 
                  v-for="planet in strongPlanets" 
                  :key="planet.name"
                  class="planet-card"
                  :class="{ selected: selectedPlanet?.name === planet.name }"
                  @click="selectPlanet(planet)"
                >
                  <div class="planet-icon" :style="{ color: planet.element_color }">
                    {{ getPlanetSymbol(planet.name) }}
                  </div>
                  <div class="planet-info">
                    <div class="planet-name">{{ planet.name }}在{{ planet.sign }}</div>
                    <div class="planet-element">{{ planet.element_name }}</div>
                  </div>
                  <div class="planet-multiplier">
                    <span class="multiplier-label">能量倍数</span>
                    <span class="multiplier-value">×{{ planet.multiplier }}</span>
                  </div>
                  <div class="planet-tags">
                    <span class="tag dignity" v-if="planet.dignity_score > 0">
                      庙旺 +{{ planet.dignity_score }}
                    </span>
                    <span class="tag stellium" v-if="planet.is_stellium">
                      群星配置 ×1.5
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="no-chart-message" v-else-if="!hasChart">
              <div class="message-icon">🔮</div>
              <p class="message-text">请先创建您的星盘数据</p>
              <el-button type="primary" @click="goToCreateChart">
                创建星盘
              </el-button>
            </div>

            <div class="no-strong-planets" v-else-if="strongPlanets.length === 0 && hasChart">
              <div class="message-icon">🌙</div>
              <p class="message-text">您的星盘尚未发现强势行星，系统将自动选择</p>
            </div>

            <div class="refine-preview" v-if="selectedPlanet || strongPlanets.length > 0">
              <div class="preview-header">
                <span class="preview-label">炼化预览</span>
                <div class="fragment-selector">
                  <span class="selector-label">碎片数量:</span>
                  <el-select v-model="refineAmount" @change="updatePreview">
                    <el-option :value="10" label="10 碎片" />
                    <el-option :value="20" label="20 碎片" />
                    <el-option :value="50" label="50 碎片" />
                    <el-option :value="100" label="100 碎片" />
                  </el-select>
                </div>
              </div>
              
              <div class="preview-content" v-if="previewResult">
                <div class="preview-rows">
                  <div class="preview-row">
                    <span class="preview-key">基础能量</span>
                    <span class="preview-value">{{ formatEnergy(previewResult.base_energy) }}</span>
                  </div>
                  <div class="preview-row">
                    <span class="preview-key">能量倍数</span>
                    <span class="preview-value highlight">×{{ previewResult.multiplier }}</span>
                  </div>
                  <div class="preview-row total">
                    <span class="preview-key">注入总能量</span>
                    <span class="preview-value total">{{ formatEnergy(previewResult.total_energy) }}</span>
                  </div>
                </div>
              </div>

              <el-button 
                type="primary" 
                size="large" 
                class="contribute-btn"
                :loading="contributing"
                :disabled="!canContribute"
                @click="doContribute"
              >
                <el-icon><Star /></el-icon>
                注入共鸣池
              </el-button>
            </div>
          </div>

          <div class="login-prompt" v-else>
            <div class="prompt-icon">✨</div>
            <p class="prompt-text">登录后可使用星元碎片炼化能量</p>
            <el-button type="primary" @click="goToLogin">
              立即登录
            </el-button>
          </div>
        </div>

        <div class="side-panel">
          <div class="tickets-card">
            <h3 class="section-title">预言券</h3>
            <div class="tickets-display">
              <div class="ticket-count">
                <span class="ticket-icon">🎫</span>
                <span class="ticket-num">{{ ticketsPending }}</span>
              </div>
              <p class="ticket-desc">可用于预言家礼堂投票</p>
            </div>
            
            <el-button 
              type="primary" 
              class="enter-auditorium-btn"
              @click="enterAuditorium"
              :loading="enteringAuditorium"
            >
              <el-icon><Trophy /></el-icon>
              进入预言家礼堂
            </el-button>
            
            <div class="tier-rewards">
              <p class="reward-title">档位奖励</p>
              <div class="tier-list">
                <div 
                  v-for="(config, tier) in tierConfig" 
                  :key="tier"
                  class="tier-item"
                  :class="{ current: currentTier === tier, past: isTierPast(tier) }"
                >
                  <span class="tier-name-small">{{ config.name }}</span>
                  <span class="tier-reward">🎫 ×{{ config.ticket_reward }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="recent-contributions-card">
            <h3 class="section-title">最近注入</h3>
            <div class="contributions-list">
              <div 
                v-for="(contrib, index) in recentContributions" 
                :key="index"
                class="contribution-item"
              >
                <div class="contrib-avatar">
                  {{ contrib.username?.charAt(0) || '?' }}
                </div>
                <div class="contrib-info">
                  <div class="contrib-user">{{ contrib.username || '匿名用户' }}</div>
                  <div class="contrib-detail">
                    <span class="contrib-element" :style="{ color: getElementColor(contrib.element) }">
                      {{ getElementName(contrib.element) }}
                    </span>
                    <span class="contrib-energy">{{ formatEnergy(contrib.total_energy) }}</span>
                  </div>
                </div>
                <div class="contrib-time">
                  {{ formatTime(contrib.created_at) }}
                </div>
              </div>
              
              <div class="no-contributions" v-if="recentContributions.length === 0">
                暂无注入记录
              </div>
            </div>
          </div>

          <div class="element-info-card">
            <h3 class="section-title">元素说明</h3>
            <div class="elements-info">
              <div class="element-info-row" v-for="(info, key) in elementsInfo" :key="key">
                <span class="elem-icon" :style="{ color: info.color }">{{ getElementIcon(key) }}</span>
                <span class="elem-name">{{ info.name }}</span>
                <div class="elem-effects">
                  <span class="mini-effect" v-for="(val, k) in info.effects" :key="k">
                    {{ getEffectLabel(k) }}
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
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Star, Trophy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { energyWeatherApi } from '@/api'

const router = useRouter()

const BASE_FRAGMENT_COST = 10

const isLoggedIn = ref(localStorage.getItem('token') !== null)
const hasChart = ref(true)

const poolStatus = ref(null)
const strongPlanets = ref([])
const selectedPlanet = ref(null)
const refineAmount = ref(10)
const previewResult = ref(null)
const contributing = ref(false)
const enteringAuditorium = ref(false)
const ticketsPending = ref(0)
const recentContributions = ref([])
const elementsInfo = ref({})
const tierConfig = ref({})
const userAssets = ref(null)

const sparkles = ref([])

const currentTier = computed(() => poolStatus.value?.current_tier || 'dormant')
const currentTierNum = computed(() => {
  const order = ['dormant', 'awakening', 'glowing', 'radiant', 'transcendent']
  return order.indexOf(currentTier.value) + 1
})
const totalTiers = computed(() => 5)

const currentTierInfo = computed(() => {
  const config = tierConfig.value?.[currentTier.value]
  if (!config) {
    const names = {
      dormant: '沉寂',
      awakening: '觉醒',
      glowing: '辉光',
      radiant: '璀璨',
      transcendent: '超凡'
    }
    return { name: names[currentTier.value] || '未知' }
  }
  return config
})

const tierProgressColor = computed(() => {
  const colors = {
    dormant: '#6B7280',
    awakening: '#3B82F6',
    glowing: '#8B5CF6',
    radiant: '#F59E0B',
    transcendent: '#EF4444'
  }
  return colors[currentTier.value] || '#6B7280'
})

const nebulaStyle = computed(() => {
  const color = poolStatus.value?.nebula?.color || '#1F2937'
  const intensity = poolStatus.value?.nebula?.intensity || 0.1
  
  return {
    '--nebula-color': color,
    '--nebula-intensity': intensity,
    transform: `scale(${0.8 + intensity * 0.4})`
  }
})

const glowStyle = computed(() => {
  const color = poolStatus.value?.nebula?.color || '#1F2937'
  const intensity = poolStatus.value?.nebula?.intensity || 0.1
  
  return {
    background: `radial-gradient(circle, ${color}${Math.round(intensity * 60).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
    opacity: intensity * 2
  }
})

const elementDistribution = computed(() => {
  if (!poolStatus.value?.element_distribution) return {}
  
  const result = {}
  const dist = poolStatus.value.element_distribution
  const total = Object.values(dist).reduce((sum, item) => sum + (item.energy || 0), 0)
  
  for (const [key, item] of Object.entries(dist)) {
    result[key] = {
      ...item,
      percentage: total > 0 ? Math.round((item.energy / total) * 100) : 0
    }
  }
  
  return result
})

const canContribute = computed(() => {
  if (!userAssets.value) return false
  return userAssets.value.stardust_fragment_balance >= refineAmount.value
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

function generateSparkles() {
  const newSparkles = []
  for (let i = 0; i < 20; i++) {
    newSparkles.push({
      id: i,
      style: {
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 3}s`,
        animationDuration: `${2 + Math.random() * 2}s`
      }
    })
  }
  sparkles.value = newSparkles
}

function formatEnergy(energy) {
  const num = Number(energy)
  if (isNaN(num)) {
    return '0'
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toFixed(1)
}

function formatEffect(value, key) {
  const num = Number(value)
  if (isNaN(num)) {
    return '0'
  }
  if (key && key.includes('bonus') && num < 1) {
    return (num * 100).toFixed(0) + '%'
  }
  return num.toFixed(1)
}

function getElementIcon(element) {
  const icons = {
    fire: '🔥',
    earth: '🌍',
    air: '💨',
    water: '💧'
  }
  return icons[element] || '✨'
}

function getElementName(element) {
  const names = {
    fire: '火象',
    earth: '土象',
    air: '风象',
    water: '水象'
  }
  return names[element] || element
}

function getElementColor(element) {
  const colors = {
    fire: '#EF4444',
    earth: '#84CC16',
    air: '#3B82F6',
    water: '#06B6D4'
  }
  return colors[element] || '#6B7280'
}

function getEffectLabel(effectKey) {
  const labels = {
    action_bonus: '行动力',
    crit_bonus: '暴击率',
    healing_bonus: '治愈力',
    match_bonus: '缘分匹配',
    stability_bonus: '稳定性',
    wealth_bonus: '运势加成',
    thinking_bonus: '思维敏捷',
    communication_bonus: '沟通效率'
  }
  return labels[effectKey] || effectKey
}

function getEffectIcon(effectKey) {
  const icons = {
    action_bonus: '⚡',
    crit_bonus: '💥',
    healing_bonus: '💚',
    match_bonus: '💕',
    stability_bonus: '🛡️',
    wealth_bonus: '💰',
    thinking_bonus: '🧠',
    communication_bonus: '💬'
  }
  return icons[effectKey] || '✨'
}

function getPlanetSymbol(planetName) {
  const symbols = {
    '太阳': '☉',
    '月亮': '☽',
    '水星': '☿',
    '金星': '♀',
    '火星': '♂',
    '木星': '♃',
    '土星': '♄',
    '天王星': '♅',
    '海王星': '♆',
    '冥王星': '♇',
    '上升点': 'A'
  }
  return symbols[planetName] || '☆'
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = (now - date) / 1000
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  
  return date.toLocaleDateString('zh-CN')
}

function isTierPast(tier) {
  const order = ['dormant', 'awakening', 'glowing', 'radiant', 'transcendent']
  const currentIdx = order.indexOf(currentTier.value)
  const tierIdx = order.indexOf(tier)
  return tierIdx < currentIdx
}

function selectPlanet(planet) {
  selectedPlanet.value = selectedPlanet.value?.name === planet.name ? null : planet
  updatePreview()
}

async function updatePreview() {
  if (!refineAmount.value) return
  
  try {
    const params = {
      fragment_amount: refineAmount.value
    }
    if (selectedPlanet.value) {
      params.selected_planet_name = selectedPlanet.value.name
    }
    
    const result = await energyWeatherApi._refinePreview ? 
      await energyWeatherApi._refinePreview(params) :
      await fetch('/api/star-resonance/refine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(params)
      }).then(r => r.json()).then(r => r.data)
    
    previewResult.value = result
  } catch (error) {
    console.error('预览失败:', error)
  }
}

async function doContribute() {
  if (!canContribute.value) {
    ElMessage.warning('星元碎片不足')
    return
  }
  
  contributing.value = true
  
  try {
    const params = {
      fragment_amount: refineAmount.value
    }
    if (selectedPlanet.value) {
      params.selected_planet_name = selectedPlanet.value.name
    }
    
    const result = await fetch('/api/star-resonance/contribute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(params)
    }).then(r => r.json())
    
    if (result.code === 200 || result.code === 201) {
      ElMessage.success({
        message: result.data.tickets_awarded > 0 
          ? `注入成功！获得 ${result.data.tickets_awarded} 张预言券` 
          : '注入成功！',
        duration: 3000
      })
      
      await loadPoolStatus()
      await loadUserAssets()
      await loadStrongPlanets()
      await loadRecentContributions()
    } else {
      ElMessage.error(result.message || '注入失败')
    }
  } catch (error) {
    console.error('注入失败:', error)
    ElMessage.error('注入失败，请稍后重试')
  } finally {
    contributing.value = false
  }
}

async function loadPoolStatus() {
  try {
    const result = await fetch('/api/star-resonance/status', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    }).then(r => r.json())
    
    if (result.code === 200 || result.code === 201) {
      poolStatus.value = result.data
      ticketsPending.value = result.data.tickets_pending || 0
    }
  } catch (error) {
    console.error('加载状态失败:', error)
  }
}

async function loadStrongPlanets() {
  if (!isLoggedIn.value) return
  
  try {
    const result = await fetch('/api/star-resonance/my-strong-planets', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    }).then(r => r.json())
    
    if (result.code === 200 || result.code === 201) {
      hasChart.value = result.data.has_chart
      strongPlanets.value = result.data.strong_planets || []
    }
  } catch (error) {
    console.error('加载强势行星失败:', error)
  }
}

async function loadUserAssets() {
  if (!isLoggedIn.value) return
  
  try {
    const result = await fetch('/api/star-resonance/status', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    }).then(r => r.json())
    
    if (result.data?.user_assets) {
      userAssets.value = result.data.user_assets
    }
  } catch (error) {
    console.error('加载用户资产失败:', error)
  }
}

async function loadRecentContributions() {
  try {
    const result = await fetch('/api/star-resonance/recent-contributions?limit=10')
      .then(r => r.json())
    
    if (result.code === 200 || result.code === 201) {
      recentContributions.value = result.data.contributions || []
    }
  } catch (error) {
    console.error('加载注入记录失败:', error)
  }
}

async function loadElementInfo() {
  try {
    const result = await fetch('/api/star-resonance/element-info')
      .then(r => r.json())
    
    if (result.code === 200 || result.code === 201) {
      elementsInfo.value = result.data.elements || {}
      tierConfig.value = result.data.tier_config || {}
    }
  } catch (error) {
    console.error('加载元素信息失败:', error)
  }
}

function goBack() {
  router.push('/transit')
}

function goToLogin() {
  router.push({ name: 'Login', query: { redirect: '/star-resonance' } })
}

function goToCreateChart() {
  router.push('/astro')
}

function enterAuditorium() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后进入预言家礼堂')
    router.push({ name: 'Login', query: { redirect: '/prediction' } })
    return
  }
  
  enteringAuditorium.value = true
  setTimeout(() => {
    router.push('/prediction')
    enteringAuditorium.value = false
  }, 300)
}

watch(refineAmount, () => {
  updatePreview()
})

watch(selectedPlanet, () => {
  updatePreview()
})

onMounted(() => {
  generateSparkles()
  loadPoolStatus()
  loadElementInfo()
  loadRecentContributions()
  
  if (isLoggedIn.value) {
    loadStrongPlanets()
    loadUserAssets()
  }
})
</script>

<style lang="scss" scoped>
.star-resonance-pool {
  min-height: 100%;
  width: 100%;
  position: relative;
  overflow-x: hidden;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a2a 100%);
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

.nebula-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80vw;
  height: 80vw;
  max-width: 800px;
  max-height: 800px;
  pointer-events: none;
  z-index: 2;
}

.nebula-main {
  width: 100%;
  height: 100%;
  position: relative;
  transition: all 0.5s ease;
}

.nebula-layer {
  position: absolute;
  border-radius: 50%;
}

.nebula-core {
  top: 25%;
  left: 25%;
  width: 50%;
  height: 50%;
  background: radial-gradient(
    circle,
    var(--nebula-color, #1F2937) 0%,
    transparent 70%
  );
  opacity: calc(var(--nebula-intensity, 0.1) * 3);
  animation: pulse-slow 8s ease-in-out infinite;
}

.nebula-ring-1 {
  top: 15%;
  left: 15%;
  width: 70%;
  height: 70%;
  border: 2px solid var(--nebula-color, #1F2937);
  opacity: calc(var(--nebula-intensity, 0.1) * 2);
  animation: rotate-slow 60s linear infinite;
}

.nebula-ring-2 {
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  border: 1px solid var(--nebula-color, #1F2937);
  opacity: calc(var(--nebula-intensity, 0.1) * 1.5);
  animation: rotate-slow 90s linear infinite reverse;
}

.nebula-sparkles {
  position: absolute;
  width: 100%;
  height: 100%;
}

.sparkle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: var(--nebula-color, #fff);
  border-radius: 50%;
  opacity: 0;
  animation: sparkle-fade 3s ease-in-out infinite;
}

@keyframes sparkle-fade {
  0%, 100% { opacity: 0; transform: scale(0); }
  50% { opacity: 0.8; transform: scale(1); }
}

@keyframes pulse-slow {
  0%, 100% { transform: scale(1); opacity: calc(var(--nebula-intensity, 0.1) * 3); }
  50% { transform: scale(1.1); opacity: calc(var(--nebula-intensity, 0.1) * 4); }
}

@keyframes rotate-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.nebula-glow {
  position: absolute;
  top: -20%;
  left: -20%;
  width: 140%;
  height: 140%;
  border-radius: 50%;
  transition: all 0.5s ease;
}

.resonance-main {
  position: relative;
  z-index: 10;
  padding: 16px 20px 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.header-section {
  margin-bottom: 24px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  color: #a78bfa;
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.4);
  }
}

.header-text {
  .main-title {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #06b6d4 100%);
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

.content-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 20px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.main-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.pool-status-card,
.refine-card,
.tickets-card,
.recent-contributions-card,
.element-info-card {
  background: rgba(15, 15, 40, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 16px 0;
}

.section-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 16px 0;
}

.tier-display {
  margin-bottom: 24px;
}

.tier-badge {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 12px;
  margin-bottom: 16px;
  
  &.dormant {
    border-left: 3px solid #6B7280;
  }
  &.awakening {
    border-left: 3px solid #3B82F6;
  }
  &.glowing {
    border-left: 3px solid #8B5CF6;
  }
  &.radiant {
    border-left: 3px solid #F59E0B;
  }
  &.transcendent {
    border-left: 3px solid #EF4444;
  }
}

.tier-name {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.tier-num {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.progress-section {
  .progress-labels {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
  }
  
  .current-energy {
    font-size: 24px;
    font-weight: 700;
    color: #a78bfa;
  }
  
  .next-tier {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.element-distribution {
  margin-bottom: 24px;
}

.element-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.element-bar-row {
  .element-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  
  .element-icon {
    font-size: 18px;
  }
  
  .element-name {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .element-energy {
    margin-left: auto;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .element-effects {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
  }
  
  .effect-tag {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 8px;
    border-radius: 4px;
  }
}

.active-effects {
  .effects-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    
    @media (max-width: 600px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  .effect-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 12px;
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
  }
  
  .effect-icon {
    font-size: 20px;
  }
  
  .effect-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .effect-value {
    font-size: 14px;
    font-weight: 700;
    color: #84CC16;
  }
}

.fragment-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 12px;
  margin-bottom: 20px;
  
  .balance-display {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .balance-icon {
    font-size: 24px;
  }
  
  .balance-label {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .balance-value {
    font-size: 20px;
    font-weight: 700;
    color: #FBBF24;
  }
  
  .base-cost {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
  
  .cost-highlight {
    color: #F59E0B;
    font-weight: 600;
  }
}

.planets-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.planet-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: rgba(20, 20, 50, 0.6);
  border: 2px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
    background: rgba(20, 20, 50, 0.8);
    transform: translateY(-2px);
  }
  
  &.selected {
    border-color: #8B5CF6;
    background: rgba(139, 92, 246, 0.15);
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
  }
}

.planet-icon {
  font-size: 28px;
}

.planet-info {
  .planet-name {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.85);
  }
  
  .planet-element {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.planet-multiplier {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 4px;
  
  .multiplier-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
  
  .multiplier-value {
    font-size: 18px;
    font-weight: 700;
    color: #84CC16;
  }
}

.planet-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  
  .tag {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  .tag.dignity {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
  }
  
  .tag.stellium {
    background: rgba(245, 158, 11, 0.2);
    color: #F59E0B;
  }
}

.no-chart-message,
.no-strong-planets,
.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  
  .message-icon,
  .prompt-icon {
    font-size: 48px;
  }
  
  .message-text,
  .prompt-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
    text-align: center;
  }
}

.refine-preview {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .preview-label {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .fragment-selector {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .selector-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.preview-content {
  background: rgba(139, 92, 246, 0.05);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.preview-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .preview-key {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .preview-value {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.85);
    
    &.highlight {
      color: #84CC16;
    }
  }
  
  &.total {
    padding-top: 8px;
    margin-top: 8px;
    border-top: 1px dashed rgba(255, 255, 255, 0.1);
    
    .preview-key {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .preview-value {
      font-size: 20px;
      color: #FBBF24;
    }
  }
}

.contribute-btn {
  width: 100%;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  border: none;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  
  &:hover {
    box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4);
  }
}

.tickets-card {
  .tickets-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px;
    background: rgba(139, 92, 246, 0.08);
    border-radius: 12px;
    margin-bottom: 16px;
  }
  
  .ticket-count {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .ticket-icon {
    font-size: 32px;
  }
  
  .ticket-num {
    font-size: 36px;
    font-weight: 700;
    background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .ticket-desc {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    text-align: center;
  }
  
  .enter-auditorium-btn {
    width: 100%;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%);
    border: none;
    padding: 12px;
    font-size: 14px;
    font-weight: 600;
    
    &:hover {
      box-shadow: 0 8px 32px rgba(245, 158, 11, 0.4);
    }
  }
}

.tier-rewards {
  .reward-title {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    margin: 0 0 12px 0;
  }
  
  .tier-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .tier-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    opacity: 0.5;
    transition: all 0.3s ease;
    
    &.current {
      background: rgba(139, 92, 246, 0.15);
      border: 1px solid rgba(139, 92, 246, 0.3);
      opacity: 1;
    }
    
    &.past {
      opacity: 0.8;
    }
    
    .tier-name-small {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .tier-reward {
      font-size: 12px;
      color: #FBBF24;
    }
  }
}

.recent-contributions-card {
  .contributions-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .contribution-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px;
    background: rgba(20, 20, 50, 0.5);
    border-radius: 10px;
  }
  
  .contrib-avatar {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    color: #fff;
  }
  
  .contrib-info {
    flex: 1;
    
    .contrib-user {
      font-size: 13px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.8);
    }
    
    .contrib-detail {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 2px;
    }
    
    .contrib-element {
      font-size: 11px;
      font-weight: 600;
    }
    
    .contrib-energy {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .contrib-time {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.3);
  }
  
  .no-contributions {
    text-align: center;
    padding: 20px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.3);
  }
}

.element-info-card {
  .elements-info {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .element-info-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: rgba(20, 20, 50, 0.5);
    border-radius: 10px;
  }
  
  .elem-icon {
    font-size: 18px;
  }
  
  .elem-name {
    font-size: 13px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.75);
    width: 40px;
  }
  
  .elem-effects {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .mini-effect {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
  }
}

@media (max-width: 768px) {
  .resonance-main {
    padding: 12px 16px 30px;
  }
  
  .header-text {
    .main-title {
      font-size: 24px;
    }
  }
  
  .pool-status-card,
  .refine-card,
  .tickets-card,
  .recent-contributions-card,
  .element-info-card {
    padding: 16px;
  }
}
</style>
