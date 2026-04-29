import { ref, computed, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { transitApi, chartApi } from '@/api'
import { useUserStore } from '@/stores/user'

const TRANSIT_CACHE = new Map()
const CACHE_MAX_AGE = 30 * 60 * 1000

function getCacheKey(type, params) {
  return `${type}:${JSON.stringify(params)}`
}

function getCachedData(key) {
  if (TRANSIT_CACHE.has(key)) {
    const cached = TRANSIT_CACHE.get(key)
    if (Date.now() - cached.timestamp < CACHE_MAX_AGE) {
      return cached.data
    }
    TRANSIT_CACHE.delete(key)
  }
  return null
}

function setCachedData(key, data) {
  if (TRANSIT_CACHE.size > 50) {
    const oldestKey = TRANSIT_CACHE.keys().next().value
    TRANSIT_CACHE.delete(oldestKey)
  }
  TRANSIT_CACHE.set(key, {
    data,
    timestamp: Date.now()
  })
}

const DEFAULT_CHART = {
  name: '',
  birthDate: '1990-01-01',
  birthTime: '12:00',
  cityInput: '北京',
  birthPlace: '北京',
  latitude: 39.9042,
  longitude: 116.4074,
  houseSystem: 'placidus'
}

export function useTransitAnalysis() {
  const router = useRouter()
  const route = useRoute()
  const userStore = useUserStore()

  const loading = ref(false)
  const loadingTrend = ref(false)
  const loadingInterpretation = ref(false)
  const error = ref(false)
  const errorMessage = ref('')

  const selectedChartId = ref(null)
  const myCharts = ref([])
  
  const chartData = reactive({ ...DEFAULT_CHART })

  const transitData = ref(null)
  const trendData = ref(null)
  const interpretationData = ref(null)

  const isLoggedIn = computed(() => userStore.isLoggedIn)

  const hasValidChart = computed(() => {
    return chartData.birthDate && chartData.birthTime && 
           chartData.latitude && chartData.longitude
  })

  const currentDateDisplay = computed(() => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
    return `${year}年${month}月${day}日 ${weekdays[now.getDay()]}`
  })

  const overallEnergy = computed(() => {
    if (!transitData.value?.overall) return null
    return transitData.value.overall
  })

  const dimensions = computed(() => {
    if (!transitData.value?.dimensions) return []
    return transitData.value.dimensions
  })

  const keyEvents = computed(() => {
    if (!transitData.value?.key_events) return []
    return transitData.value.key_events
  })

  const moonPhase = computed(() => {
    if (!transitData.value?.moon_phase) return null
    return transitData.value.moon_phase
  })

  const mercuryStatus = computed(() => {
    if (!transitData.value?.mercury_retrograde) return null
    return transitData.value.mercury_retrograde
  })

  const keyAspects = computed(() => {
    if (!transitData.value?.aspects) return []
    return transitData.value.aspects.slice(0, 10)
  })

  const trendSummary = computed(() => {
    if (!trendData.value?.summary) return null
    return trendData.value.summary
  })

  const trendChartData = computed(() => {
    if (!trendData.value?.trend_data) return null
    
    const data = trendData.value.trend_data
    return {
      labels: data.map(d => {
        const date = new Date(d.date)
        return `${date.getMonth() + 1}/${date.getDate()} ${d.day_of_week}`
      }),
      overall: data.map(d => d.overall_score),
      dimensions: {
        communication: data.map(d => d.dimensions?.communication?.score || 50),
        social: data.map(d => d.dimensions?.social?.score || 50),
        career: data.map(d => d.dimensions?.career?.score || 50),
        wealth: data.map(d => d.dimensions?.wealth?.score || 50),
        emotion: data.map(d => d.dimensions?.emotion?.score || 50)
      },
      moods: data.map(d => d.mood),
      turningPoints: trendSummary.value?.turning_points || []
    }
  })

  function getScoreColor(score) {
    const num = typeof score === 'number' ? score : 60
    if (num >= 80) return '#22c55e'
    if (num >= 60) return '#eab308'
    if (num >= 40) return '#f97316'
    return '#ef4444'
  }

  function getLevelLabel(level) {
    const labels = {
      high: '旺盛',
      medium_high: '活跃',
      medium: '平稳',
      medium_low: '低迷',
      low: '停滞'
    }
    return labels[level] || '平稳'
  }

  function getNatureLabel(nature) {
    const labels = {
      harmonious: '和谐',
      challenging: '紧张',
      neutral: '中性'
    }
    return labels[nature] || '中性'
  }

  function getNatureColor(nature) {
    const colors = {
      harmonious: '#22c55e',
      challenging: '#ef4444',
      neutral: '#eab308'
    }
    return colors[nature] || '#eab308'
  }

  async function loadMyCharts() {
    if (!isLoggedIn.value) return
    
    try {
      const result = await chartApi.getMyCharts({ skip: 0, limit: 20 })
      if (result?.charts && Array.isArray(result.charts)) {
        myCharts.value = result.charts
      } else if (result?.records && Array.isArray(result.records)) {
        myCharts.value = result.records
      } else if (Array.isArray(result)) {
        myCharts.value = result
      } else {
        myCharts.value = []
      }
    } catch (err) {
      console.error('加载星盘列表失败:', err)
      myCharts.value = []
    }
  }

  function applyChartToForm(chartId) {
    if (!chartId) return
    
    const chart = myCharts.value.find(c => c.id === chartId)
    if (!chart) return
    
    chartData.name = chart.name || ''
    chartData.birthDate = chart.birth_date
    chartData.birthTime = chart.birth_time
    chartData.cityInput = chart.birth_place || ''
    chartData.birthPlace = chart.birth_place || ''
    chartData.latitude = chart.latitude
    chartData.longitude = chart.longitude
    chartData.houseSystem = chart.house_system || 'placidus'
    
    selectedChartId.value = chartId
  }

  function getApiParams() {
    return {
      birth_date: chartData.birthDate,
      birth_time: chartData.birthTime,
      latitude: chartData.latitude,
      longitude: chartData.longitude,
      house_system: chartData.houseSystem
    }
  }

  async function loadTransit(targetDate = null) {
    if (!hasValidChart.value) {
      error.value = true
      errorMessage.value = '请填写完整的出生信息'
      return
    }

    const cacheKey = getCacheKey('transit', { ...getApiParams(), targetDate })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      transitData.value = cached
      return
    }

    loading.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const params = {
        ...getApiParams(),
        target_date: targetDate
      }
      
      let result
      if (isLoggedIn.value && selectedChartId.value) {
        result = await transitApi.getPersonalTransit(targetDate)
      } else {
        result = await transitApi.calculateTransit(params)
      }
      
      transitData.value = result
      setCachedData(cacheKey, result)
      
    } catch (err) {
      error.value = true
      errorMessage.value = err.message || '加载行运数据失败，请稍后重试'
      console.error('加载行运数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadTrend(startDate = null) {
    if (!hasValidChart.value) {
      return
    }

    const cacheKey = getCacheKey('trend', { ...getApiParams(), startDate })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      trendData.value = cached
      return
    }

    loadingTrend.value = true

    try {
      let result
      if (isLoggedIn.value && selectedChartId.value) {
        result = await transitApi.getPersonalTrend(startDate)
      } else {
        const params = {
          ...getApiParams(),
          start_date: startDate
        }
        result = await transitApi.get7DayTrend(params)
      }
      
      trendData.value = result
      setCachedData(cacheKey, result)
      
    } catch (err) {
      console.error('加载趋势数据失败:', err)
      ElMessage.error(err.message || '加载趋势数据失败')
    } finally {
      loadingTrend.value = false
    }
  }

  async function loadInterpretation(targetDate = null) {
    if (!hasValidChart.value) {
      return
    }

    const cacheKey = getCacheKey('interpretation', { ...getApiParams(), targetDate })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      interpretationData.value = cached
      return
    }

    loadingInterpretation.value = true

    try {
      const params = {
        ...getApiParams(),
        target_date: targetDate
      }
      
      let result
      if (isLoggedIn.value && selectedChartId.value) {
        result = await transitApi.getAIInterpretation(params)
      } else {
        result = await transitApi.getAIInterpretation(params)
      }
      
      interpretationData.value = result
      setCachedData(cacheKey, result)
      
    } catch (err) {
      console.error('加载AI解读失败:', err)
      ElMessage.error(err.message || '加载AI解读失败')
    } finally {
      loadingInterpretation.value = false
    }
  }

  async function loadAllTransitData() {
    if (!hasValidChart.value) return
    
    await Promise.all([
      loadTransit(),
      loadTrend(),
      loadInterpretation()
    ])
  }

  function clearCache() {
    TRANSIT_CACHE.clear()
    ElMessage.success('缓存已清除')
  }

  function updateChartData(field, value) {
    chartData[field] = value
    selectedChartId.value = null
  }

  watch(selectedChartId, (newVal) => {
    if (newVal) {
      applyChartToForm(newVal)
    }
  })

  return {
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
    clearCache,
    updateChartData,
    
    getScoreColor,
    getLevelLabel,
    getNatureLabel,
    getNatureColor
  }
}

export function getTransitStarStyle(index) {
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

export const DIMENSION_CONFIG = {
  communication: {
    name: '沟通',
    nameCn: '沟通',
    icon: '💬',
    color: '#60a5fa',
    description: '影响思维、表达、学习和短途旅行'
  },
  social: {
    name: '社交',
    nameCn: '社交',
    icon: '👥',
    color: '#f472b6',
    description: '影响人际关系、合作、约会和社交活动'
  },
  career: {
    name: '事业',
    nameCn: '事业',
    icon: '💼',
    color: '#f97316',
    description: '影响职业发展、领导能力和长期目标'
  },
  wealth: {
    name: '财运',
    nameCn: '财运',
    icon: '💰',
    color: '#eab308',
    description: '影响财务状况、投资和物质资源'
  },
  emotion: {
    name: '情绪',
    nameCn: '情绪',
    icon: '❤️',
    color: '#ec4899',
    description: '影响内心感受、直觉和情绪稳定性'
  }
}
