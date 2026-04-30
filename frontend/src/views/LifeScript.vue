<template>
  <div class="life-script-page">
    <div class="stars-bg">
      <div 
        v-for="i in 50" 
        :key="i" 
        class="star"
        :style="getStarStyle(i)"
      ></div>
    </div>

    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">⏳</span>
        人生剧本时空穿梭机
      </h1>
      <p class="page-description">
        滑动时间轴，探索你的人生剧本。结合行运、法达、次限三种推运算法，用AI讲述你的人生故事。
      </p>
    </div>

    <div class="input-section">
      <div class="input-card">
        <div class="input-header">
          <span class="input-title-icon">🗓️</span>
          <span class="input-title">出生信息</span>
        </div>
        
        <div class="input-content">
          <div class="existing-charts" v-if="isLoggedIn && myCharts.length > 0">
            <div class="form-row">
              <div class="form-item select-chart">
                <label class="form-label">从存档中选择</label>
                <el-select 
                  v-model="selectedChartId" 
                  placeholder="选择已保存的星盘"
                  @change="handleChartSelect"
                  class="chart-select"
                >
                  <el-option
                    v-for="chart in myCharts"
                    :key="chart.id"
                    :label="`${chart.name || '未命名'} - ${chart.birth_date}`"
                    :value="chart.id"
                  />
                </el-select>
              </div>
            </div>
            <div class="divider">或手动输入</div>
          </div>

          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">姓名/称呼</label>
              <el-input 
                v-model="chartData.name" 
                placeholder="输入姓名或称呼"
              />
            </div>

            <div class="form-item">
              <label class="form-label">出生日期</label>
              <el-date-picker
                v-model="chartData.birthDate"
                type="date"
                placeholder="选择出生日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="full-width"
              />
            </div>

            <div class="form-item">
              <label class="form-label">出生时间</label>
              <el-time-picker
                v-model="chartData.birthTime"
                placeholder="选择出生时间"
                format="HH:mm"
                value-format="HH:mm"
                class="full-width"
              />
            </div>

            <div class="form-item">
              <label class="form-label">出生地点</label>
              <el-autocomplete
                v-model="chartData.cityInput"
                :fetch-suggestions="searchCity"
                :trigger-on-focus="false"
                placeholder="搜索城市"
                @select="handleCitySelect"
                class="full-width"
              >
                <template #default="{ item }">
                  <div class="city-item">
                    <span class="city-name">{{ item.name }}</span>
                    <span class="city-region">{{ item.admin1 || item.country }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </div>

            <div class="form-item">
              <label class="form-label">经度</label>
              <el-input-number
                v-model="chartData.longitude"
                :min="-180"
                :max="180"
                :precision="4"
                :step="0.0001"
                class="full-width"
              />
            </div>

            <div class="form-item">
              <label class="form-label">纬度</label>
              <el-input-number
                v-model="chartData.latitude"
                :min="-90"
                :max="90"
                :precision="4"
                :step="0.0001"
                class="full-width"
              />
            </div>

            <div class="form-item">
              <label class="form-label">分宫制</label>
              <el-select v-model="chartData.houseSystem" class="full-width">
                <el-option label="Placidus" value="placidus" />
                <el-option label="Koch" value="koch" />
                <el-option label="Whole Sign" value="whole_sign" />
                <el-option label="Equal" value="equal" />
                <el-option label="Porphyry" value="porphyry" />
              </el-select>
            </div>
          </div>

          <div class="input-actions">
            <el-button 
              type="primary" 
              :loading="loading"
              :disabled="!hasValidChart"
              @click="analyzeCurrentYear"
              class="analyze-btn"
            >
              <el-icon class="btn-icon"><Search /></el-icon>
              开始探索
            </el-button>
            
            <el-button 
              :loading="loadingKeyYears"
              :disabled="!hasValidChart"
              @click="loadKeyYears"
            >
              发现关键年份
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="timeline-section" v-if="analysisResult || keyYears">
      <div class="section-header">
        <span class="section-icon">⌛</span>
        <span class="section-title">时间轴</span>
      </div>
      
      <TimelineSlider
        v-model="selectedYear"
        :birth-year="currentBirthYear"
        :min-year="minYear"
        :max-year="maxYear"
        :key-years="keyYearsList"
        @change="handleYearChange"
      />
    </div>

    <div class="analysis-section" v-if="analysisResult">
      <div class="overview-card">
        <div class="overview-header">
          <div class="year-badge">
            <span class="year-badge-icon">{{ getMoodEmoji(analysisResult.year_overview?.overall_mood) }}</span>
            <span class="year-badge-year">{{ selectedYear }}年</span>
            <span class="year-badge-age">{{ currentAge }}岁</span>
          </div>
          
          <div class="mood-indicator" :style="{ background: getMoodColor(analysisResult.year_overview?.overall_mood) }">
            <span class="mood-label">{{ analysisResult.year_overview?.overall_mood_label }}</span>
          </div>
        </div>

        <div class="overview-content">
          <div class="mood-description">
            <h3 class="mood-title">{{ analysisResult.year_overview?.overall_mood_description }}</h3>
          </div>

          <div class="domains-summary">
            <div 
              v-for="domain in analysisResult.domains_summary" 
              :key="domain.domain"
              class="domain-item"
            >
              <div class="domain-header">
                <span class="domain-name">{{ domain.name }}</span>
                <span 
                  class="domain-intensity"
                  :style="{ background: getIntensityColor(domain.intensity) }"
                >
                  强度: {{ domain.intensity }}/10
                </span>
              </div>
              <p class="domain-description">{{ domain.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="multi-astrology-section">
        <div class="section-header">
          <span class="section-icon">✨</span>
          <span class="section-title">多重推运分析</span>
        </div>

        <el-tabs v-model="activeAstrologyTab" class="astrology-tabs">
          <el-tab-pane label="行运 Transit" name="transit">
            <div class="astrology-content" v-if="analysisResult?.transit_analysis">
              <div class="analysis-summary">
                <p class="summary-text">{{ analysisResult.transit_analysis?.overall_summary }}</p>
              </div>
              
              <div class="key-aspects">
                <h4 class="aspects-title">重要相位</h4>
                <div 
                  v-for="(aspect, index) in analysisResult.transit_analysis?.key_aspects" 
                  :key="index"
                  class="aspect-item"
                >
                  <div class="aspect-header">
                    <span class="aspect-planet">{{ aspect.transit_planet }} 与 {{ aspect.natal_planet }}</span>
                    <span 
                      class="aspect-type"
                      :class="aspect.aspect_type"
                    >
                      {{ aspect.aspect_name }}
                    </span>
                  </div>
                  <p class="aspect-influence">{{ aspect.influence }}</p>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="法达 Firdaria" name="firdaria">
            <div class="astrology-content" v-if="analysisResult?.firdaria_analysis">
              <div class="firdaria-period">
                <div class="period-main">
                  <span class="period-label">主星周期</span>
                  <span class="period-planet">{{ analysisResult.firdaria_analysis?.major_lord }}</span>
                </div>
                <div class="period-sub" v-if="analysisResult.firdaria_analysis?.minor_lord">
                  <span class="period-label">副星周期</span>
                  <span class="period-planet">{{ analysisResult.firdaria_analysis?.minor_lord }}</span>
                </div>
              </div>
              
              <div class="analysis-summary">
                <p class="summary-text">{{ analysisResult.firdaria_analysis?.overall_summary }}</p>
              </div>
              
              <div class="key-themes">
                <h4 class="themes-title">核心主题</h4>
                <div class="themes-list">
                  <span 
                    v-for="(theme, index) in analysisResult.firdaria_analysis?.key_themes" 
                    :key="index"
                    class="theme-tag"
                  >
                    {{ theme }}
                  </span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="次限推运" name="progression">
            <div class="astrology-content" v-if="analysisResult?.progression_analysis">
              <div class="analysis-summary">
                <p class="summary-text">{{ analysisResult.progression_analysis?.overall_summary }}</p>
              </div>
              
              <div class="key-changes">
                <h4 class="changes-title">重要变化</h4>
                <div 
                  v-for="(change, index) in analysisResult.progression_analysis?.key_changes" 
                  :key="index"
                  class="change-item"
                >
                  <div class="change-header">
                    <span class="change-planet">{{ change.planet }}</span>
                    <span class="change-type">{{ change.type }}</span>
                  </div>
                  <p class="change-influence">{{ change.influence }}</p>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="key-events-section" v-if="analysisResult?.key_events && analysisResult.key_events.length > 0">
        <div class="section-header">
          <span class="section-icon">🎯</span>
          <span class="section-title">年度关键事件</span>
        </div>
        
        <div class="events-timeline">
          <div 
            v-for="(event, index) in analysisResult.key_events" 
            :key="index"
            class="event-item"
            :class="event.category"
          >
            <div class="event-icon">
              {{ getCategoryIcon(event.category) }}
            </div>
            <div class="event-content">
              <div class="event-header">
                <span class="event-category">{{ getCategoryName(event.category) }}</span>
                <span 
                  class="event-intensity"
                  :style="{ background: getIntensityColor(event.intensity) }"
                >
                  {{ event.intensity }}/10
                </span>
              </div>
              <h4 class="event-title">{{ event.title }}</h4>
              <p class="event-description">{{ event.description }}</p>
              <div class="event-timing" v-if="event.timing">
                <el-tag size="small">{{ event.timing }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="script-section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <span class="section-title">人生剧本文案</span>
        </div>
        
        <div v-if="scriptResult" class="script-content">
          <div class="script-content-inner" v-html="renderScriptContent(scriptResult.script_content)"></div>
        </div>
        
        <div v-else-if="loadingScript" class="script-loading">
          <div class="loading-animation">
            <div class="loading-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
            <p class="loading-text">AI正在撰写你的人生剧本...</p>
            <p class="loading-hint">正在结合行运、法达、次限三种推运算法</p>
          </div>
        </div>
        
        <div v-else class="script-prompt">
          <p class="prompt-text">点击下方按钮，让 AI 为你生成 {{ selectedYear }} 年的人生剧本文案</p>
          <el-button 
            type="primary" 
            :loading="loadingScript"
            @click="generateCurrentYearScript"
            class="generate-btn"
          >
            <el-icon class="btn-icon"><MagicStick /></el-icon>
            生成人生剧本
          </el-button>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="error-section">
      <div class="error-card">
        <div class="error-icon">⚠️</div>
        <h3 class="error-title">分析出错了</h3>
        <p class="error-message">{{ errorMessage }}</p>
        <el-button type="primary" @click="retryAnalysis">
          重新尝试
        </el-button>
      </div>
    </div>

    <el-empty 
      v-else-if="!hasValidChart" 
      description="请先填写出生信息开始探索"
      class="empty-state"
    >
      <template #image>
        <div class="empty-icon">🌌</div>
      </template>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, h } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, MagicStick } from '@element-plus/icons-vue'
import { useLifeScriptAnalysis, getLifeScriptStarStyle } from '@/composables/useLifeScriptAnalysis'
import { geoApi } from '@/api'
import TimelineSlider from '@/components/life-script/TimelineSlider.vue'

const {
  loading,
  loadingScript,
  loadingKeyYears,
  error,
  errorMessage,
  selectedChartId,
  myCharts,
  chartData,
  analysisResult,
  scriptResult,
  keyYearsResult,
  selectedYear,
  isLoggedIn,
  hasValidChart,
  currentBirthYear,
  currentAge,
  minYear,
  maxYear,
  loadMyCharts,
  applyChartToForm,
  analyzeYear,
  generateScript,
  getKeyYears,
  preloadNearbyYears,
  getMoodColor,
  getMoodEmoji,
  getIntensityColor,
  resetAnalysis,
  clearLifeScriptCache
} = useLifeScriptAnalysis()

const activeAstrologyTab = ref('transit')

const keyYearsList = computed(() => {
  if (!keyYearsResult?.all && !keyYearsResult?.key_years) return []
  return keyYearsResult.all || keyYearsResult.key_years
})

const keyYears = computed(() => keyYearsResult)

function getStarStyle(index) {
  return getLifeScriptStarStyle(index)
}

async function searchCity(queryString, callback) {
  if (!queryString) {
    callback([])
    return
  }
  
  try {
    const result = await geoApi.searchCity(queryString)
    if (result?.results) {
      callback(result.results)
    } else {
      callback([])
    }
  } catch (err) {
    console.error('搜索城市失败:', err)
    callback([])
  }
}

function handleCitySelect(item) {
  chartData.cityInput = item.name
  chartData.birthPlace = item.name
  if (item.latitude) {
    chartData.latitude = item.latitude
  }
  if (item.longitude) {
    chartData.longitude = item.longitude
  }
}

function handleChartSelect(chartId) {
  if (chartId) {
    applyChartToForm(chartId)
  }
}

async function analyzeCurrentYear() {
  if (!hasValidChart.value) {
    ElMessage.warning('请先填写完整的出生信息')
    return
  }
  
  const result = await analyzeYear(selectedYear.value)
  if (result) {
    await loadKeyYears()
  }
}

async function loadKeyYears() {
  if (!hasValidChart.value) {
    ElMessage.warning('请先填写完整的出生信息')
    return
  }
  
  await getKeyYears(0, 80)
}

async function generateCurrentYearScript() {
  if (!hasValidChart.value) {
    ElMessage.warning('请先填写完整的出生信息')
    return
  }
  
  if (!analysisResult.value) {
    await analyzeCurrentYear()
  }
  
  await generateScript(selectedYear.value)
}

async function handleYearChange(year) {
  if (year === selectedYear.value && analysisResult.value) return
  
  await analyzeYear(year)
}

function retryAnalysis() {
  resetAnalysis()
  clearLifeScriptCache()
  ElMessage.info('正在重新分析...')
  analyzeCurrentYear()
}

function getCategoryIcon(category) {
  const icons = {
    career: '💼',
    romance: '❤️',
    finance: '💰',
    family: '🏠',
    health: '🏥',
    travel: '✈️',
    education: '📚',
    spiritual: '🧘',
    social: '👥'
  }
  return icons[category] || '✨'
}

function getCategoryName(category) {
  const names = {
    career: '事业',
    romance: '感情',
    finance: '财运',
    family: '家庭',
    health: '健康',
    travel: '旅行',
    education: '学业',
    spiritual: '灵性',
    social: '社交'
  }
  return names[category] || '其他'
}

function renderScriptContent(content) {
  if (!content) return ''
  
  let html = content
    .replace(/^# (.+)$/gm, '<h1 class="script-h1">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 class="script-h2">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="script-h3">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="script-strong">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="script-em">$1</em>')
    .replace(/^- (.+)$/gm, '<li class="script-li">$1</li>')
    .replace(/\n\n/g, '</p><p class="script-p">')
    .replace(/\n/g, '<br/>')
  
  return `<p class="script-p">${html}</p>`
}

onMounted(async () => {
  if (isLoggedIn.value) {
    await loadMyCharts()
  }
})
</script>

<style lang="scss" scoped>
.life-script-page {
  position: relative;
  min-height: 100vh;
  padding: 40px 24px;
  overflow-x: hidden;
}

.stars-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
  z-index: -1;
}

.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  animation: twinkle 4s infinite ease-in-out;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.2); }
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 42px;
  font-weight: 800;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #f472b6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.page-description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.input-section {
  max-width: 1000px;
  margin: 0 auto 40px;
}

.input-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  overflow: hidden;
}

.input-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 28px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.15) 0%, transparent 100%);
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.input-title-icon {
  font-size: 20px;
}

.input-title {
  font-size: 18px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.input-content {
  padding: 28px;
}

.existing-charts {
  margin-bottom: 20px;
}

.form-row {
  margin-bottom: 16px;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px 24px;
}

.full-width {
  width: 100%;
}

.divider {
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  margin: 8px 0;
  position: relative;
  
  &::before,
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: rgba(139, 92, 246, 0.2);
  }
  
  &::before {
    left: 0;
  }
  
  &::after {
    right: 0;
  }
}

.input-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.analyze-btn,
.generate-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  
  &:hover {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
  }
}

.btn-icon {
  margin-right: 6px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.section-icon {
  font-size: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.timeline-section,
.analysis-section {
  max-width: 1000px;
  margin: 0 auto 40px;
}

.overview-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  padding: 28px;
  margin-bottom: 32px;
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.year-badge {
  display: flex;
  align-items: center;
  gap: 12px;
}

.year-badge-icon {
  font-size: 28px;
}

.year-badge-year {
  font-size: 28px;
  font-weight: 800;
  color: white;
}

.year-badge-age {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.5);
}

.mood-indicator {
  padding: 8px 20px;
  border-radius: 20px;
  
  .mood-label {
    font-size: 14px;
    font-weight: 600;
    color: white;
  }
}

.mood-description {
  margin-bottom: 24px;
}

.mood-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  line-height: 1.6;
}

.domains-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.domain-item {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  padding: 16px 20px;
}

.domain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.domain-name {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}

.domain-intensity {
  font-size: 11px;
  font-weight: 600;
  color: white;
  padding: 3px 10px;
  border-radius: 10px;
}

.domain-description {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.5;
}

.multi-astrology-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  padding: 28px;
  margin-bottom: 32px;
}

.astrology-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    background: rgba(139, 92, 246, 0.2);
  }
  
  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.5);
    
    &.is-active {
      color: #a78bfa;
    }
    
    &:hover {
      color: rgba(167, 139, 250, 0.8);
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background: linear-gradient(90deg, #8b5cf6, #60a5fa);
  }
}

.astrology-content {
  padding-top: 16px;
}

.analysis-summary {
  margin-bottom: 24px;
}

.summary-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.7;
  margin: 0;
  padding: 16px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  border-left: 3px solid #8b5cf6;
}

.key-aspects,
.key-changes {
  .aspects-title,
  .changes-title {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.85);
    margin: 0 0 16px 0;
  }
}

.aspect-item,
.change-item {
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.12);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.aspect-header,
.change-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.aspect-planet,
.change-planet {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}

.aspect-type {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 8px;
  
  &.conjunction {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
  }
  
  &.trine,
  &.sextile {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }
  
  &.square,
  &.opposition {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
  }
}

.change-type {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 10px;
  border-radius: 8px;
}

.aspect-influence,
.change-influence {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
  margin: 0;
}

.firdaria-period {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.period-main,
.period-sub {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 20px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 12px;
}

.period-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.period-planet {
  font-size: 18px;
  font-weight: 800;
  color: #a78bfa;
}

.key-themes {
  .themes-title {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.85);
    margin: 0 0 12px 0;
  }
}

.themes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.theme-tag {
  font-size: 13px;
  padding: 6px 14px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(96, 165, 250, 0.2) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.75);
}

.key-events-section {
  margin-bottom: 32px;
}

.events-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.event-item {
  display: flex;
  gap: 16px;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateX(4px);
    border-color: rgba(139, 92, 246, 0.4);
  }
  
  &.career {
    border-left: 3px solid #f59e0b;
  }
  
  &.romance {
    border-left: 3px solid #f472b6;
  }
  
  &.finance {
    border-left: 3px solid #22c55e;
  }
  
  &.family {
    border-left: 3px solid #60a5fa;
  }
  
  &.health {
    border-left: 3px solid #ef4444;
  }
  
  &.travel {
    border-left: 3px solid #8b5cf6;
  }
  
  &.education {
    border-left: 3px solid #06b6d4;
  }
  
  &.spiritual {
    border-left: 3px solid #a855f7;
  }
  
  &.social {
    border-left: 3px solid #ec4899;
  }
}

.event-icon {
  font-size: 28px;
  display: flex;
  align-items: flex-start;
  padding-top: 4px;
}

.event-content {
  flex: 1;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.event-category {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-intensity {
  font-size: 11px;
  font-weight: 600;
  color: white;
  padding: 2px 8px;
  border-radius: 8px;
}

.event-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px 0;
}

.event-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.script-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  padding: 28px;
}

.script-content {
  background: rgba(139, 92, 246, 0.05);
  border-radius: 16px;
  padding: 24px;
}

.script-content-inner {
  :deep(.script-h1) {
    font-size: 26px;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  }
  
  :deep(.script-h2) {
    font-size: 20px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 24px 0 12px 0;
  }
  
  :deep(.script-h3) {
    font-size: 16px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.8);
    margin: 16px 0 8px 0;
  }
  
  :deep(.script-p) {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.8;
    margin: 0 0 12px 0;
  }
  
  :deep(.script-strong) {
    color: #a78bfa;
    font-weight: 700;
  }
  
  :deep(.script-em) {
    color: rgba(255, 255, 255, 0.85);
    font-style: italic;
  }
  
  :deep(.script-li) {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.7;
    padding-left: 16px;
    position: relative;
    margin: 4px 0;
    
    &::before {
      content: '•';
      position: absolute;
      left: 0;
      color: #8b5cf6;
    }
  }
}

.script-loading {
  text-align: center;
  padding: 40px 20px;
}

.loading-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #8b5cf6 0%, #60a5fa 100%);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
  
  &:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  &:nth-child(2) {
    animation-delay: -0.16s;
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.loading-text {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}

.loading-hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

.script-prompt {
  text-align: center;
  padding: 24px;
}

.prompt-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 20px 0;
}

.empty-state {
  margin-top: 60px;
  
  .empty-icon {
    font-size: 80px;
    margin-bottom: 20px;
  }
}

.city-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.city-name {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.city-region {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .life-script-page {
    padding: 24px 16px;
  }
  
  .page-title {
    font-size: 28px;
    flex-direction: column;
    gap: 8px;
  }
  
  .title-icon {
    font-size: 32px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .input-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
  
  .overview-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .domains-summary {
    grid-template-columns: 1fr;
  }
  
  .event-item {
    flex-direction: column;
    gap: 12px;
  }
}

.error-section {
  max-width: 600px;
  margin: 60px auto;
  text-align: center;
}

.error-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 24px;
  padding: 40px;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
  margin: 0 0 12px 0;
}

.error-message {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
  margin: 0 0 24px 0;
  line-height: 1.6;
}

.page-title,
.section-title,
.year-badge-year,
.mood-title,
.domain-name,
.aspect-planet,
.change-planet,
.event-title,
.period-planet,
.script-h2,
.script-h3 {
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.page-description,
.domain-description,
.aspect-influence,
.change-influence,
.event-description,
.script-p,
.script-li,
.loading-text,
.loading-hint,
.prompt-text {
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
}
</style>
