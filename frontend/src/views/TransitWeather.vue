<template>
  <div class="transit-weather">
    <div class="stars-bg">
      <div v-for="i in 100" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>
    
    <div class="zodiac-wheel-bg">
      <svg viewBox="0 0 200 200" class="zodiac-wheel">
        <circle cx="100" cy="100" r="95" fill="none" stroke="rgba(139, 92, 246, 0.15)" stroke-width="1" />
        <circle cx="100" cy="100" r="75" fill="none" stroke="rgba(139, 92, 246, 0.1)" stroke-width="0.5" />
        <circle cx="100" cy="100" r="55" fill="none" stroke="rgba(139, 92, 246, 0.08)" stroke-width="0.5" />
        <circle cx="100" cy="100" r="30" fill="rgba(139, 92, 246, 0.03)" stroke="rgba(139, 92, 246, 0.15)" stroke-width="1" />
      </svg>
    </div>

    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <div class="transit-main">
      <div class="transit-header">
        <div class="header-icon">
          <el-icon size="36"><Sunrise /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="main-title">星象气象站</h1>
          <p class="subtitle">实时行运能量分析 · {{ currentDateDisplay }}</p>
        </div>
      </div>

      <div class="chart-selector-section" v-if="isLoggedIn">
        <div class="selector-header">
          <span class="selector-label">选择本命盘</span>
          <span class="selector-hint" v-if="myCharts.length > 0">选择已保存的星盘快速计算</span>
          <span class="selector-hint" v-else>您还没有保存的星盘，可手动输入出生信息</span>
        </div>
        
        <div class="selector-content">
          <el-select 
            v-model="selectedChartId" 
            placeholder="选择已保存的星盘" 
            class="chart-select"
            @change="onChartSelect"
          >
            <el-option 
              v-for="chart in myCharts" 
              :key="chart.id" 
              :label="`${chart.name || '未命名星盘'} - ${chart.birth_date}`"
              :value="chart.id"
            />
          </el-select>
          
          <el-divider direction="vertical" />
          
          <span class="manual-option">
            或 <span class="link-text" @click="showManualForm = !showManualForm">手动输入出生信息</span>
          </span>
        </div>
      </div>

      <div class="manual-form-section" v-if="showManualForm || !isLoggedIn">
        <div class="form-header">
          <span class="form-label">出生信息</span>
          <span class="form-hint">用于计算您的本命盘与当前行运的相位</span>
        </div>
        
        <div class="form-grid">
          <div class="form-item">
            <label class="form-label-item">出生日期</label>
            <el-date-picker
              v-model="birthDate"
              type="date"
              placeholder="选择出生日期"
              value-format="YYYY-MM-DD"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label class="form-label-item">出生时间</label>
            <el-time-picker
              v-model="birthTime"
              placeholder="选择出生时间"
              value-format="HH:mm"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label class="form-label-item">出生地点</label>
            <div class="location-input">
              <el-input
                v-model="locationQuery"
                placeholder="搜索城市..."
                class="form-input"
                @input="searchLocation"
              />
              <el-select 
                v-if="locationResults.length > 0" 
                v-model="selectedLocation"
                placeholder="选择城市"
                class="location-select"
                @change="onLocationSelect"
              >
                <el-option 
                  v-for="loc in locationResults" 
                  :key="loc.id" 
                  :label="`${loc.name}, ${loc.country}`"
                  :value="loc"
                />
              </el-select>
            </div>
          </div>
          
          <div class="form-item">
            <label class="form-label-item">宫位系统</label>
            <el-select v-model="houseSystem" class="form-input">
              <el-option label="Placidus (普拉西度)" value="placidus" />
              <el-option label="Whole Sign (整宫制)" value="whole_sign" />
            </el-select>
          </div>
        </div>
        
        <div class="form-actions">
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            :disabled="!canCalculate"
            @click="calculateTransit"
            class="calculate-btn"
          >
            <el-icon><MagicStick /></el-icon>
            开始分析
          </el-button>
        </div>
      </div>

      <div class="main-content" v-if="transitData || trendData || interpretationData">
        <div class="tabs-section">
          <el-tabs v-model="activeTab" class="main-tabs">
            <el-tab-pane label="今日星象" name="today">
              <div class="tab-content">
                <TransitDashboard 
                  :overall="overallEnergy"
                  :dimensions="dimensions"
                  :moon-phase="moonPhase"
                  :mercury-status="mercuryStatus"
                  :date-display="currentDateDisplay"
                />
                
                <KeyEventsList 
                  :events="keyEvents"
                  :aspects="keyAspects"
                />
                
                <AIInterpretation
                  :interpretation-data="interpretationData"
                  :loading="loadingInterpretation"
                  :error="error"
                  :error-message="errorMessage"
                  :target-date="currentDateDisplay"
                  @retry="retryInterpretation"
                />
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="7天趋势" name="trend">
              <div class="tab-content">
                <EnergyTrendChart 
                  :chart-data="trendChartData"
                  :summary="trendSummary"
                  :height="400"
                />
                
                <div class="trend-details" v-if="trendData?.trend_data">
                  <h3 class="trend-details-title">每日详情</h3>
                  <div class="trend-cards">
                    <div 
                      v-for="(day, index) in trendData.trend_data" 
                      :key="index"
                      class="trend-day-card"
                      :style="{ '--score-color': getScoreColor(day.overall_score) }"
                    >
                      <div class="day-header">
                        <span class="day-mood">{{ day.mood }}</span>
                        <span class="day-date">{{ day.day_of_week }}</span>
                      </div>
                      <div class="day-score">
                        <span class="score-value">{{ day.overall_score }}</span>
                        <span class="score-unit">分</span>
                      </div>
                      <div class="day-mood-label">{{ day.mood_label }}</div>
                      <div class="day-key-aspects" v-if="day.key_aspects?.length">
                        <div 
                          v-for="(aspect, ai) in day.key_aspects.slice(0, 2)" 
                          :key="ai"
                          class="mini-aspect"
                        >
                          <span class="aspect-planets">
                            {{ aspect.transit_symbol }}{{ aspect.aspect_symbol }}{{ aspect.natal_symbol }}
                          </span>
                          <span 
                            class="aspect-nature"
                            :style="{ color: getNatureColor(aspect.nature) }"
                          >
                            {{ getNatureLabel(aspect.nature) }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <div class="welcome-section" v-else-if="!loading && !hasValidChart">
        <div class="welcome-icon">🌌</div>
        <h2 class="welcome-title">探索您的星象能量</h2>
        <p class="welcome-desc">
          输入您的出生信息，我们将为您计算本命盘与当前行运的相位关系，
          生成专属的能量指数和AI解读。
        </p>
        <div class="welcome-features">
          <div class="feature-item">
            <span class="feature-icon">☀️</span>
            <span class="feature-text">今日整体能量</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📊</span>
            <span class="feature-text">5维度能量分析</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📈</span>
            <span class="feature-text">7天趋势预测</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span class="feature-text">AI动态解读</span>
          </div>
        </div>
      </div>

      <div class="loading-section" v-else-if="loading && !transitData">
        <div class="loading-visual">
          <div class="loading-rings">
            <div class="ring ring-1"></div>
            <div class="ring ring-2"></div>
            <div class="ring ring-3"></div>
          </div>
          <div class="loading-icon">✨</div>
        </div>
        <p class="loading-text">正在计算行运相位...</p>
        <p class="loading-sub">分析本命盘与当前星象的能量互动</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Sunrise, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useTransitAnalysis } from '@/composables/useTransitAnalysis'
import { geoApi } from '@/api'

import TransitDashboard from '@/components/transit/TransitDashboard.vue'
import EnergyTrendChart from '@/components/transit/EnergyTrendChart.vue'
import KeyEventsList from '@/components/transit/KeyEventsList.vue'
import AIInterpretation from '@/components/transit/AIInterpretation.vue'

const router = useRouter()

const {
  loading,
  loadingTrend,
  loadingInterpretation,
  error,
  errorMessage,
  
  selectedChartId,
  myCharts,
  chartData,
  
  transitData,
  trendData,
  interpretationData,
  
  isLoggedIn,
  hasValidChart,
  currentDateDisplay,
  
  overallEnergy,
  dimensions,
  keyEvents,
  moonPhase,
  mercuryStatus,
  keyAspects,
  trendSummary,
  trendChartData,
  
  loadMyCharts,
  applyChartToForm,
  loadTransit,
  loadTrend,
  loadInterpretation,
  loadAllTransitData,
  updateChartData,
  
  getScoreColor,
  getNatureLabel,
  getNatureColor
} = useTransitAnalysis()

const activeTab = ref('today')
const showManualForm = ref(false)

const birthDate = ref('1990-01-01')
const birthTime = ref('12:00')
const locationQuery = ref('')
const selectedLocation = ref(null)
const locationResults = ref([])
const houseSystem = ref('placidus')

const canCalculate = computed(() => {
  return birthDate.value && birthTime.value && 
         (selectedChartId.value || (chartData.latitude && chartData.longitude))
})

watch(birthDate, (val) => {
  if (val) updateChartData('birthDate', val)
})

watch(birthTime, (val) => {
  if (val) updateChartData('birthTime', val)
})

watch(houseSystem, (val) => {
  updateChartData('houseSystem', val)
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

async function searchLocation(query) {
  if (!query || query.length < 2) {
    locationResults.value = []
    return
  }
  
  try {
    const result = await geoApi.searchCity(query)
    locationResults.value = Array.isArray(result) ? result : []
  } catch (err) {
    console.error('搜索城市失败:', err)
    locationResults.value = []
  }
}

function onLocationSelect(location) {
  if (!location) return
  
  updateChartData('cityInput', location.name || '')
  updateChartData('birthPlace', location.name || '')
  updateChartData('latitude', location.latitude)
  updateChartData('longitude', location.longitude)
  
  locationQuery.value = location.name || ''
  locationResults.value = []
}

function onChartSelect(chartId) {
  if (chartId) {
    applyChartToForm(chartId)
    birthDate.value = chartData.birthDate
    birthTime.value = chartData.birthTime
    houseSystem.value = chartData.houseSystem
    locationQuery.value = chartData.cityInput || chartData.birthPlace || ''
  }
}

async function calculateTransit() {
  if (!canCalculate.value) {
    ElMessage.warning('请填写完整的出生信息')
    return
  }
  
  await loadAllTransitData()
  
  if (!error.value) {
    ElMessage.success('行运分析完成')
  }
}

async function retryInterpretation() {
  await loadInterpretation()
}

onMounted(async () => {
  if (isLoggedIn.value) {
    await loadMyCharts()
  }
})
</script>

<style lang="scss" scoped>
.transit-weather {
  min-height: 100%;
  width: 100%;
  position: relative;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
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

.zodiac-wheel-bg {
  position: absolute;
  top: 50%;
  right: -10%;
  transform: translateY(-50%);
  width: 60vh;
  max-width: 500px;
  height: 60vh;
  max-height: 500px;
  pointer-events: none;
  z-index: 1;
  opacity: 0.25;
}

.zodiac-wheel {
  width: 100%;
  height: 100%;
  animation: rotate-slow 120s linear infinite;
}

@keyframes rotate-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.glow-orbs {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.35;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation: float-1 25s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation: float-2 20s ease-in-out infinite;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 30%;
  left: 20%;
  animation: pulse 10s ease-in-out infinite;
}

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-80px, 50px); }
}

@keyframes float-2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(60px, -40px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.25; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(1.3); }
}

.transit-main {
  position: relative;
  z-index: 10;
  flex: 1;
  padding: 16px 20px 40px;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.transit-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  color: #a78bfa;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.main-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.chart-selector-section,
.manual-form-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
}

.selector-header,
.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.selector-label,
.form-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.selector-hint,
.form-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.selector-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.chart-select {
  width: 320px;
  max-width: 100%;
}

.manual-option {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.link-text {
  color: #a78bfa;
  cursor: pointer;
  text-decoration: underline;
  
  &:hover {
    color: #c4b5fd;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  
  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label-item {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
}

.form-input {
  width: 100%;
}

.location-input {
  position: relative;
}

.location-select {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  z-index: 100;
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.calculate-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  padding: 12px 32px;
  font-size: 15px;
  font-weight: 600;
  
  &:hover {
    box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4);
  }
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tabs-section {
  :deep(.el-tabs__nav-wrap::after) {
    background: rgba(139, 92, 246, 0.2);
  }
  
  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.5);
    font-size: 15px;
    font-weight: 500;
    
    &.is-active {
      color: #a78bfa;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background: linear-gradient(90deg, #8b5cf6, #60a5fa);
  }
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 16px;
}

.trend-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.trend-details-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}

.trend-cards {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
  
  @media (max-width: 900px) {
    grid-template-columns: repeat(4, 1fr);
  }
  
  @media (max-width: 600px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.trend-day-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--score-color);
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.2);
  }
}

.day-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.day-mood {
  font-size: 24px;
}

.day-date {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
}

.day-score {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--score-color);
}

.score-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.day-mood-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.day-key-aspects {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  width: 100%;
}

.mini-aspect {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.aspect-planets {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.aspect-nature {
  font-size: 10px;
  font-weight: 500;
}

.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 12px 0;
}

.welcome-desc {
  font-size: 14px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.6);
  max-width: 600px;
  margin: 0 0 32px 0;
}

.welcome-features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 600px;
  
  @media (max-width: 600px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(20, 20, 50, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.feature-icon {
  font-size: 24px;
}

.feature-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-visual {
  position: relative;
  width: 120px;
  height: 120px;
  margin-bottom: 24px;
}

.loading-rings {
  position: absolute;
  width: 100%;
  height: 100%;
}

.ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ring-rotate 2s linear infinite;
}

.ring-1 {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-top-color: #8b5cf6;
}

.ring-2 {
  top: 8px;
  left: 8px;
  right: 8px;
  bottom: 8px;
  border-right-color: #60a5fa;
  animation-direction: reverse;
  animation-duration: 1.5s;
}

.ring-3 {
  top: 16px;
  left: 16px;
  right: 16px;
  bottom: 16px;
  border-bottom-color: #06b6d4;
  animation-duration: 2.5s;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.loading-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  animation: pulse-glow 2s ease-in-out infinite;
}

.loading-text {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 4px 0;
}

.loading-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

@media (max-width: 768px) {
  .transit-main {
    padding: 12px 16px 30px;
  }
  
  .main-title {
    font-size: 22px;
  }
  
  .transit-header {
    flex-direction: column;
    text-align: center;
  }
  
  .selector-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .chart-select {
    width: 100%;
  }
  
  .welcome-features {
    width: 100%;
  }
}
</style>
