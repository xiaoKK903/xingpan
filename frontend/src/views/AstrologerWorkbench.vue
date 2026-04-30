<template>
  <div class="astrologer-workbench">
    <div class="workbench-header">
      <div class="header-title">
        <span class="title-icon">🔮</span>
        <span class="title-text">占星师 AI 助手工作台</span>
      </div>
      <div class="header-subtitle">
        古典占星专业 Copilot · 实时星盘数据探针
      </div>
    </div>
    
    <div class="workbench-container">
      <div class="input-section" v-if="!chartData">
        <div class="input-card">
          <div class="card-header">
            <span class="card-icon">🌅</span>
            <span class="card-title">输入出生信息</span>
          </div>
          
          <form @submit.prevent="calculateChart" class="input-form">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">姓名</label>
                <input 
                  v-model="birthForm.name"
                  type="text"
                  class="form-input"
                  placeholder="可留空"
                />
              </div>
              <div class="form-group">
                <label class="form-label">出生日期</label>
                <input 
                  v-model="birthForm.birth_date"
                  type="date"
                  class="form-input"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">出生时间</label>
                <input 
                  v-model="birthForm.birth_time"
                  type="time"
                  class="form-input"
                  required
                />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group full-width">
                <label class="form-label">出生地点</label>
                <div class="location-input-wrapper">
                  <input 
                    v-model="birthForm.birth_place"
                    type="text"
                    class="form-input location-input"
                    placeholder="输入城市名称搜索..."
                    @input="searchCity"
                    @focus="showCityDropdown = true"
                    @blur="setTimeout(() => showCityDropdown = false, 200)"
                  />
                  <div v-if="showCityDropdown && citySuggestions.length > 0" class="city-dropdown">
                    <div 
                      v-for="(city, idx) in citySuggestions" 
                      :key="idx"
                      class="city-option"
                      @mousedown="selectCity(city)"
                    >
                      <span class="city-name">{{ city.name }}</span>
                      <span class="city-region">{{ city.region || '' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">纬度</label>
                <input 
                  v-model="birthForm.latitude"
                  type="number"
                  step="0.0001"
                  class="form-input"
                  placeholder="如: 39.9042"
                />
              </div>
              <div class="form-group">
                <label class="form-label">经度</label>
                <input 
                  v-model="birthForm.longitude"
                  type="number"
                  step="0.0001"
                  class="form-input"
                  placeholder="如: 116.4074"
                />
              </div>
              <div class="form-group">
                <label class="form-label">宫位系统</label>
                <select v-model="birthForm.house_system" class="form-select">
                  <option value="placidus">Placidus 分宫制</option>
                  <option value="whole_sign">整宫制</option>
                </select>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">日夜盘类型</label>
                <select v-model="birthForm.chart_time_type" class="form-select">
                  <option value="auto">自动判断</option>
                  <option value="day">日盘</option>
                  <option value="night">夜盘</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">守护星系统</label>
                <select v-model="birthForm.dignity_system" class="form-select">
                  <option value="traditional">传统守护星</option>
                  <option value="modern">现代守护星</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">相位包含</label>
                <select v-model="birthForm.aspect_include" class="form-select">
                  <option value="major">仅主相位</option>
                  <option value="all">包含次要相位</option>
                </select>
              </div>
            </div>
            
            <div class="form-actions">
              <button 
                type="button"
                class="btn-secondary"
                @click="loadExample"
              >
                加载示例
              </button>
              <button 
                type="submit"
                class="btn-primary"
                :disabled="isCalculating"
              >
                <span v-if="isCalculating">计算中...</span>
                <span v-else>计算星盘</span>
              </button>
            </div>
          </form>
        </div>
        
        <div class="features-card">
          <div class="card-header">
            <span class="card-icon">✨</span>
            <span class="card-title">工作台核心功能</span>
          </div>
          
          <div class="features-list">
            <div class="feature-item">
              <span class="feature-icon">🔍</span>
              <div class="feature-info">
                <span class="feature-title">实时星盘数据探针</span>
                <span class="feature-desc">拖动行星，实时观察相位、互容、接纳、映点等征象变化</span>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">📜</span>
              <div class="feature-info">
                <span class="feature-title">古典占星规则引擎</span>
                <span class="feature-desc">内置希腊占星等专业规则，保证判断逻辑严谨无错</span>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">💡</span>
              <div class="feature-info">
                <span class="feature-title">光线传递可视化</span>
                <span class="feature-desc">清晰呈现光线传递、围攻等专业术语的能量流动</span>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">📝</span>
              <div class="feature-info">
                <span class="feature-title">自动解盘笔记</span>
                <span class="feature-desc">生成标准化解盘笔记草稿，支持直接编辑和导出</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="workbench-main">
        <div class="workbench-toolbar">
          <div class="toolbar-left">
            <button class="toolbar-btn" @click="resetChart">
              <span class="btn-icon">↩️</span>
              <span>重新输入</span>
            </button>
            <div class="chart-info">
              <span v-if="chartName" class="chart-name">{{ chartName }}</span>
              <span class="chart-time">{{ chartInput?.birth_date }} {{ chartInput?.birth_time }}</span>
              <span class="day-indicator" :class="{ day: isDayChart, night: !isDayChart }">
                {{ isDayChart ? '☀️ 日盘' : '🌙 夜盘' }}
              </span>
            </div>
          </div>
          <div class="toolbar-right">
            <div class="view-tabs">
              <button 
                class="tab-btn" 
                :class="{ active: activeTab === 'probe' }"
                @click="activeTab = 'probe'"
              >
                <span class="tab-icon">🔍</span>
                <span>实时探针</span>
              </button>
              <button 
                class="tab-btn" 
                :class="{ active: activeTab === 'notes' }"
                @click="activeTab = 'notes'"
              >
                <span class="tab-icon">📝</span>
                <span>解盘笔记</span>
              </button>
            </div>
          </div>
        </div>
        
        <div class="workbench-content">
          <div class="chart-panel">
            <InteractiveChartWheel
              :chart-data="chartData"
              :size="chartSize"
              :show-hint="true"
              @planet-drag-start="onPlanetDragStart"
              @planet-drag="onPlanetDrag"
              @planet-drag-end="onPlanetDragEnd"
              @planet-hover="onPlanetHover"
              @planet-leave="onPlanetLeave"
            />
            
            <div v-if="isDragging" class="drag-indicator-bar">
              <span class="drag-info">
                正在拖动: <span class="dragging-planet">{{ draggingPlanet?.name }}</span>
                当前角度: <span class="current-angle">{{ dragCurrentAngle?.toFixed(2) }}°</span>
                <span v-if="hasAspectChanges" class="change-indicator changed">
                  相位已变化
                </span>
                <span v-else class="change-indicator stable">
                  相位稳定
                </span>
              </span>
              <span class="drag-hint">松开鼠标完成调整</span>
            </div>
          </div>
          
          <div class="side-panel">
            <RealTimeProbe
              v-if="activeTab === 'probe'"
              :selected-planet="selectedPlanet"
              :probe-data="probeData"
              :changes="changes"
              @clear-selection="clearSelection"
            />
            
            <InterpretationNotes
              v-else-if="activeTab === 'notes'"
              :notes-data="notesData"
              :is-generating="isGeneratingNotes"
              @request-notes="generateNotes"
              @save-notes="saveNotes"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import InteractiveChartWheel from '@/components/workbench/InteractiveChartWheel.vue'
import RealTimeProbe from '@/components/workbench/RealTimeProbe.vue'
import InterpretationNotes from '@/components/workbench/InterpretationNotes.vue'
import { geoApi, workbenchApi } from '@/api'
import { 
  calculateAllAspects, 
  calculateEssentialDignities,
  calculateAllReceptions,
  debounce,
  throttle,
  getAngleDifference,
  getSignIndex,
  getDegreeInSign,
  CHART_WHEEL_CONSTANTS,
  ASPECT_CONFIG,
  aspectCache,
  dignityCache
} from '@/constants/workbench.js'

const birthForm = ref({
  name: '',
  birth_date: '',
  birth_time: '',
  birth_place: '',
  latitude: 39.9042,
  longitude: 116.4074,
  house_system: 'placidus',
  chart_time_type: 'auto',
  dignity_system: 'traditional',
  aspect_include: 'major'
})

const citySuggestions = ref([])
const showCityDropdown = ref(false)
const isCalculating = ref(false)

const chartData = ref(null)
const chartName = ref('')
const chartInput = ref(null)
const isDayChart = ref(true)

const activeTab = ref('probe')
const chartSize = ref(520)

const selectedPlanet = ref(null)
const probeData = ref(null)
const notesData = ref(null)
const isGeneratingNotes = ref(false)

const isDragging = ref(false)
const draggingPlanet = ref(null)
const dragStartAngle = ref(null)
const dragCurrentAngle = ref(null)
const changes = ref(null)

const dragDebounceTimer = ref(null)
const localAspectCache = ref(new Map())
const originalAspects = ref([])
const currentAspects = ref([])

const hasAspectChanges = computed(() => {
  if (!isDragging.value) return false
  const originalSet = new Set(originalAspects.value.map(a => `${a.planet1}-${a.planet2}-${a.aspect}`))
  const currentSet = new Set(currentAspects.value.map(a => `${a.planet1}-${a.planet2}-${a.aspect}`))
  return originalSet.size !== currentSet.size || 
    ![...originalSet].every(v => currentSet.has(v))
})

watch(() => selectedPlanet.value, async (planet) => {
  if (planet && chartData.value) {
    await loadProbeData(planet)
  }
})

watch(() => isDragging.value, (isDrag) => {
  if (isDrag) {
    originalAspects.value = chartData.value?.aspects?.filter(a => 
      ['合相', '对分相', '四分相', '三分相', '六分相'].includes(a.aspect)
    ) || []
    currentAspects.value = [...originalAspects.value]
  }
})

async function searchCity() {
  if (!birthForm.value.birth_place || birthForm.value.birth_place.length < 2) {
    citySuggestions.value = []
    return
  }
  
  try {
    const result = await geoApi.searchCity(birthForm.value.birth_place)
    citySuggestions.value = result || []
  } catch (e) {
    console.error('搜索城市失败:', e)
  }
}

function selectCity(city) {
  birthForm.value.birth_place = city.name
  if (city.latitude !== undefined && city.longitude !== undefined) {
    birthForm.value.latitude = city.latitude
    birthForm.value.longitude = city.longitude
  }
  citySuggestions.value = []
}

function loadExample() {
  birthForm.value = {
    name: '示例命盘',
    birth_date: '1988-05-15',
    birth_time: '10:30',
    birth_place: '北京',
    latitude: 39.9042,
    longitude: 116.4074,
    house_system: 'placidus',
    chart_time_type: 'auto',
    dignity_system: 'traditional',
    aspect_include: 'major'
  }
}

async function calculateChart() {
  if (!birthForm.value.birth_date || !birthForm.value.birth_time) {
    ElMessage.warning('请填写出生日期和时间')
    return
  }
  
  isCalculating.value = true
  aspectCache.clear()
  dignityCache.clear()
  
  try {
    const result = await workbenchApi.calculateChart({
      name: birthForm.value.name,
      birth_date: birthForm.value.birth_date,
      birth_time: birthForm.value.birth_time,
      latitude: birthForm.value.latitude,
      longitude: birthForm.value.longitude,
      birth_place: birthForm.value.birth_place,
      house_system: birthForm.value.house_system,
      chart_time_type: birthForm.value.chart_time_type,
      dignity_system: birthForm.value.dignity_system,
      aspect_include: birthForm.value.aspect_include
    })
    
    chartData.value = result.chart
    chartName.value = result.name || '命盘'
    chartInput.value = {
      birth_date: birthForm.value.birth_date,
      birth_time: birthForm.value.birth_time,
      birth_place: birthForm.value.birth_place
    }
    isDayChart.value = result.is_day_chart
    
    if (result.analysis?.planets) {
      chartData.value.planets = result.analysis.planets
    }
    if (result.analysis?.aspects) {
      chartData.value.aspects = result.analysis.aspects
    }
    if (result.analysis?.receptions) {
      chartData.value.receptions = result.analysis.receptions
    }
    if (result.analysis?.light_translations) {
      chartData.value.light_translations = result.analysis.light_translations
    }
    if (result.analysis?.besiegements) {
      chartData.value.besiegements = result.analysis.besiegements
    }
    if (result.analysis?.antiscia_aspects) {
      chartData.value.antiscia_aspects = result.analysis.antiscia_aspects
    }
    
    ElMessage.success('星盘计算成功')
    
  } catch (e) {
    ElMessage.error(e.message || '计算失败')
  } finally {
    isCalculating.value = false
  }
}

async function loadProbeData(planet) {
  if (!chartData.value || !planet) return
  
  try {
    const result = await workbenchApi.probePlanet({
      chart_data: chartData.value,
      planet_name: planet.name,
      chart_time_type: birthForm.value.chart_time_type,
      dignity_system: birthForm.value.dignity_system
    })
    
    probeData.value = result
    
  } catch (e) {
    console.error('加载探针数据失败:', e)
  }
}

async function generateNotes() {
  if (!chartData.value) return
  
  isGeneratingNotes.value = true
  
  try {
    const analysis = chartData.value.analysis || {}
    
    const result = await workbenchApi.generateNotes({
      analysis_data: analysis
    })
    
    notesData.value = result.notes
    
    ElMessage.success('解盘笔记生成成功')
    
  } catch (e) {
    ElMessage.error('生成笔记失败')
  } finally {
    isGeneratingNotes.value = false
  }
}

function saveNotes(notes) {
  console.log('保存笔记:', notes)
  ElMessage.success('笔记已保存')
}

function onPlanetDragStart(event) {
  isDragging.value = true
  draggingPlanet.value = event.planet
  dragStartAngle.value = event.startLongitude
  dragCurrentAngle.value = event.startLongitude
  changes.value = null
}

const debouncedAdjust = debounce(async (planet, longitude, isFinal) => {
  await adjustPlanetPosition(planet, longitude, isFinal)
}, 200)

const throttledLocalCalc = throttle((planet, longitude) => {
  calculateLocalChanges(planet, longitude)
}, 50)

function onPlanetDrag(event) {
  dragCurrentAngle.value = event.currentLongitude
  
  throttledLocalCalc(event.planet, event.currentLongitude)
  debouncedAdjust(event.planet, event.currentLongitude, false)
}

function calculateLocalChanges(planet, newLongitude) {
  if (!chartData.value) return
  
  const draggingName = planet.name
  const cacheKey = `${draggingName}-${newLongitude.toFixed(1)}`
  
  const cached = localAspectCache.value.get(cacheKey)
  if (cached) {
    currentAspects.value = cached.aspects
    return
  }
  
  const tempPlanets = chartData.value.planets.map(p => {
    if (p.name === draggingName) {
      return { ...p, longitude: newLongitude }
    }
    return p
  })
  
  const newAspects = calculateAllAspects(tempPlanets)
  currentAspects.value = newAspects
  
  const localDignities = calculateEssentialDignities(draggingName, newLongitude)
  const tempReceptions = calculateAllReceptions(tempPlanets)
  
  localAspectCache.value.set(cacheKey, {
    aspects: newAspects,
    dignities: localDignities,
    receptions: tempReceptions,
    timestamp: Date.now()
  })
  
  if (localAspectCache.value.size > 50) {
    const keys = [...localAspectCache.value.keys()]
    keys.slice(0, 20).forEach(k => localAspectCache.value.delete(k))
  }
}

async function onPlanetDragEnd(event) {
  isDragging.value = false
  
  if (dragDebounceTimer.value) {
    clearTimeout(dragDebounceTimer.value)
  }
  
  await adjustPlanetPosition(event.planet, event.finalLongitude, true)
  
  draggingPlanet.value = null
  dragStartAngle.value = null
  dragCurrentAngle.value = null
}

async function adjustPlanetPosition(planet, newLongitude, isFinal) {
  if (!chartData.value) return
  
  try {
    const result = await workbenchApi.adjustPlanet({
      original_chart: chartData.value,
      planet_name: planet.name,
      new_longitude: newLongitude
    })
    
    if (result.adjusted_chart) {
      chartData.value = result.adjusted_chart
    }
    
    if (result.changes) {
      changes.value = result.changes
    }
    
    if (selectedPlanet.value?.name === planet.name) {
      const updatedPlanet = chartData.value.planets.find(p => p.name === planet.name)
      if (updatedPlanet) {
        await loadProbeData(updatedPlanet)
      }
    }
    
    if (isFinal) {
      const hasChanges = 
        (result.changes?.aspects?.added?.length > 0) ||
        (result.changes?.aspects?.removed?.length > 0) ||
        (result.changes?.receptions?.added?.length > 0)
      
      if (hasChanges) {
        ElMessage.info('检测到征象变化')
      }
    }
    
  } catch (e) {
    console.error('调整行星位置失败:', e)
  }
}

function onPlanetHover(planet) {
  selectedPlanet.value = planet
}

function onPlanetLeave() {
}

function clearSelection() {
  selectedPlanet.value = null
  probeData.value = null
}

function resetChart() {
  chartData.value = null
  chartName.value = ''
  chartInput.value = null
  selectedPlanet.value = null
  probeData.value = null
  notesData.value = null
  changes.value = null
  activeTab.value = 'probe'
  aspectCache.clear()
  dignityCache.clear()
  localAspectCache.value.clear()
}

onUnmounted(() => {
  if (dragDebounceTimer.value) {
    clearTimeout(dragDebounceTimer.value)
  }
})
</script>

<style scoped>
.astrologer-workbench {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a1a 0%, #12122a 50%, #0a0a1a 100%);
}

.workbench-header {
  padding: 20px 32px;
  background: rgba(12, 12, 28, 0.95);
  border-bottom: 1px solid rgba(147, 112, 219, 0.2);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.title-icon {
  font-size: 1.8rem;
}

.title-text {
  font-size: 1.4rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 0 20px rgba(147, 112, 219, 0.3);
}

.header-subtitle {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin-left: calc(1.8rem + 12px);
}

.workbench-container {
  padding: 20px 32px;
}

.input-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.input-card,
.features-card {
  background: rgba(12, 12, 28, 0.9);
  border: 1px solid rgba(147, 112, 219, 0.2);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: linear-gradient(90deg, rgba(147, 112, 219, 0.12), transparent);
  border-bottom: 1px solid rgba(147, 112, 219, 0.1);
}

.card-icon {
  font-size: 1.2rem;
}

.card-title {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.input-form {
  padding: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.form-input,
.form-select {
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(147, 112, 219, 0.25);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: rgba(147, 112, 219, 0.6);
  box-shadow: 0 0 0 3px rgba(147, 112, 219, 0.1);
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.location-input-wrapper {
  position: relative;
}

.city-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: rgba(20, 20, 40, 0.98);
  border: 1px solid rgba(147, 112, 219, 0.3);
  border-radius: 8px;
  margin-top: 4px;
  z-index: 100;
}

.city-option {
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.city-option:hover {
  background: rgba(147, 112, 219, 0.1);
}

.city-name {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.city-region {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-secondary,
.btn-primary {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-secondary {
  background: rgba(100, 100, 120, 0.3);
  color: rgba(255, 255, 255, 0.8);
}

.btn-secondary:hover {
  background: rgba(100, 100, 120, 0.4);
}

.btn-primary {
  background: linear-gradient(135deg, #9370db, #7c3aed);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(147, 112, 219, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.features-list {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(147, 112, 219, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(147, 112, 219, 0.1);
  transition: all 0.2s ease;
}

.feature-item:hover {
  background: rgba(147, 112, 219, 0.1);
  border-color: rgba(147, 112, 219, 0.2);
}

.feature-icon {
  font-size: 1.4rem;
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
}

.feature-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.feature-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

.workbench-main {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

.workbench-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(147, 112, 219, 0.15);
  border: 1px solid rgba(147, 112, 219, 0.25);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toolbar-btn:hover {
  background: rgba(147, 112, 219, 0.25);
}

.btn-icon {
  font-size: 0.9rem;
}

.chart-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.chart-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.day-indicator {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.day-indicator.day {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.day-indicator.night {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 10px;
  border: 1px solid rgba(147, 112, 219, 0.15);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: rgba(255, 255, 255, 0.7);
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(147, 112, 219, 0.3), rgba(124, 58, 237, 0.3));
  color: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 8px rgba(147, 112, 219, 0.2);
}

.tab-icon {
  font-size: 0.9rem;
}

.workbench-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.chart-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(12, 12, 28, 0.6);
  border: 1px solid rgba(147, 112, 219, 0.15);
  border-radius: 16px;
  padding: 20px;
}

.drag-indicator-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 520px;
  margin-top: 16px;
  padding: 10px 16px;
  background: linear-gradient(90deg, rgba(147, 112, 219, 0.15), rgba(124, 58, 237, 0.15));
  border: 1px solid rgba(147, 112, 219, 0.3);
  border-radius: 10px;
}

.drag-info {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  gap: 8px;
}

.dragging-planet {
  color: #9370db;
  font-weight: 600;
}

.current-angle {
  color: #f59e0b;
  font-weight: 600;
}

.change-indicator {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 500;
}

.change-indicator.changed {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  animation: pulse-change 1s ease-in-out infinite;
}

.change-indicator.stable {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

@keyframes pulse-change {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.drag-hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.side-panel {
  background: rgba(12, 12, 28, 0.6);
  border: 1px solid rgba(147, 112, 219, 0.15);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
