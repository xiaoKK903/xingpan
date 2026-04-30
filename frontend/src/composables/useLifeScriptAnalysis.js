import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { lifeScriptApi, chartApi } from '@/api'
import { useUserStore } from '@/stores/user'

const LIFE_SCRIPT_CACHE = new Map()
const CACHE_MAX_AGE = 7 * 24 * 60 * 60 * 1000

function getCacheKey(type, params) {
  return `${type}:${JSON.stringify(params)}`
}

function getCachedData(key) {
  if (LIFE_SCRIPT_CACHE.has(key)) {
    const cached = LIFE_SCRIPT_CACHE.get(key)
    if (Date.now() - cached.timestamp < CACHE_MAX_AGE) {
      return cached.data
    }
    LIFE_SCRIPT_CACHE.delete(key)
  }
  return null
}

function setCachedData(key, data) {
  if (LIFE_SCRIPT_CACHE.size > 100) {
    const keys = LIFE_SCRIPT_CACHE.keys()
    let oldestKey = keys.next().value
    LIFE_SCRIPT_CACHE.delete(oldestKey)
  }
  LIFE_SCRIPT_CACHE.set(key, {
    data,
    timestamp: Date.now()
  })
}

function clearLifeScriptCache() {
  LIFE_SCRIPT_CACHE.clear()
  ElMessage.success('人生剧本缓存已清除')
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

export function useLifeScriptAnalysis() {
  const userStore = useUserStore()

  const loading = ref(false)
  const loadingScript = ref(false)
  const loadingRange = ref(false)
  const loadingKeyYears = ref(false)
  const error = ref(false)
  const errorMessage = ref('')

  const selectedChartId = ref(null)
  const myCharts = ref([])
  
  const chartData = reactive({ ...DEFAULT_CHART })

  const analysisResult = ref(null)
  const scriptResult = ref(null)
  const rangeResult = ref(null)
  const keyYearsResult = ref(null)

  const selectedYear = ref(new Date().getFullYear())
  const isLoggedIn = computed(() => userStore.isLoggedIn)

  const hasValidChart = computed(() => {
    return chartData.birthDate && chartData.birthTime && 
           chartData.latitude && chartData.longitude
  })

  const currentBirthYear = computed(() => {
    if (chartData.birthDate) {
      return parseInt(chartData.birthDate.split('-')[0])
    }
    return 1990
  })

  const currentAge = computed(() => {
    return selectedYear.value - currentBirthYear.value
  })

  const minYear = computed(() => currentBirthYear.value)
  const maxYear = computed(() => currentBirthYear.value + 100)

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

  async function analyzeYear(year) {
    if (!hasValidChart.value) {
      error.value = true
      errorMessage.value = '请填写完整的出生信息'
      return null
    }

    const cacheKey = getCacheKey('analyze', { ...getApiParams(), year })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      analysisResult.value = cached
      selectedYear.value = year
      return cached
    }

    loading.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const params = {
        ...getApiParams(),
        target_year: year
      }
      
      let result
      if (isLoggedIn.value && selectedChartId.value) {
        result = await lifeScriptApi.getPersonalAnalysis(year)
      } else {
        result = await lifeScriptApi.analyzeYear(params)
      }
      
      analysisResult.value = result
      selectedYear.value = year
      setCachedData(cacheKey, result)
      
      return result
      
    } catch (err) {
      error.value = true
      errorMessage.value = err.message || '分析失败，请稍后重试'
      console.error('分析年份失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function generateScript(year) {
    if (!hasValidChart.value) {
      error.value = true
      errorMessage.value = '请填写完整的出生信息'
      return null
    }

    const cacheKey = getCacheKey('script', { ...getApiParams(), year })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      scriptResult.value = cached
      error.value = false
      errorMessage.value = ''
      return cached
    }

    loadingScript.value = true
    error.value = false
    errorMessage.value = ''

    try {
      let result
      if (isLoggedIn.value && selectedChartId.value) {
        result = await lifeScriptApi.getPersonalScript(year)
      } else {
        const params = {
          ...getApiParams(),
          target_year: year
        }
        result = await lifeScriptApi.generateScript(params)
      }
      
      const scriptData = result?.script
      if (scriptData && !scriptData.success) {
        const errorType = scriptData.error_type || 'unknown'
        const errorMsg = scriptData.error || '生成失败'
        
        let userMessage = '生成人生剧本失败'
        switch (errorType) {
          case 'timeout':
            userMessage = 'AI生成时间过长，请稍后重试。如果问题持续，请检查网络连接。'
            break
          case 'auth':
            userMessage = 'AI服务配置错误，请联系管理员。'
            break
          case 'quota':
            userMessage = 'AI服务额度不足，请联系管理员充值。'
            break
          case 'rate_limit':
            userMessage = '请求太频繁，请稍后再试。'
            break
          case 'network':
            userMessage = '网络连接失败，请检查您的网络。'
            break
          default:
            userMessage = errorMsg
        }
        
        error.value = true
        errorMessage.value = userMessage
        
        if (scriptData.analysis) {
          analysisResult.value = scriptData.analysis
        }
        
        ElMessage.error(userMessage)
        return null
      }
      
      scriptResult.value = result
      setCachedData(cacheKey, result)
      
      return result
      
    } catch (err) {
      console.error('生成剧本失败:', err)
      
      let errorMsg = '生成人生剧本失败'
      if (err.message && err.message.includes('timeout')) {
        errorMsg = '请求超时：AI服务响应时间过长，请稍后重试。'
      } else if (err.message && err.message.includes('网络')) {
        errorMsg = '网络连接失败，请检查您的网络连接。'
      } else if (err.message) {
        errorMsg = err.message
      }
      
      error.value = true
      errorMessage.value = errorMsg
      ElMessage.error(errorMsg)
      
      return null
    } finally {
      loadingScript.value = false
    }
  }

  async function analyzeRange(startYear, endYear) {
    if (!hasValidChart.value) {
      return null
    }

    const cacheKey = getCacheKey('range', { ...getApiParams(), startYear, endYear })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      rangeResult.value = cached
      return cached
    }

    loadingRange.value = true

    try {
      const params = {
        ...getApiParams(),
        start_year: startYear,
        end_year: endYear
      }
      
      const result = await lifeScriptApi.analyzeRange(params)
      
      rangeResult.value = result
      setCachedData(cacheKey, result)
      
      return result
      
    } catch (err) {
      console.error('分析年份范围失败:', err)
      ElMessage.error(err.message || '分析年份范围失败')
      return null
    } finally {
      loadingRange.value = false
    }
  }

  async function getKeyYears(startAge = 0, endAge = 80) {
    if (!hasValidChart.value) {
      return null
    }

    const cacheKey = getCacheKey('keyYears', { ...getApiParams(), startAge, endAge })
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      keyYearsResult.value = cached
      return cached
    }

    loadingKeyYears.value = true

    try {
      const params = {
        ...getApiParams(),
        start_age: startAge,
        end_age: endAge
      }
      
      const result = await lifeScriptApi.getKeyYears(params)
      
      keyYearsResult.value = result
      setCachedData(cacheKey, result)
      
      return result
      
    } catch (err) {
      console.error('获取关键年份失败:', err)
      return null
    } finally {
      loadingKeyYears.value = false
    }
  }

  async function analyzeAndGenerateScript(year) {
    const analysis = await analyzeYear(year)
    if (!analysis) return null
    
    const script = await generateScript(year)
    return { analysis, script }
  }

  function preloadNearbyYears(baseYear, range = 2) {
    if (!hasValidChart.value) return
    
    for (let i = -range; i <= range; i++) {
      const year = baseYear + i
      if (year >= minYear.value && year <= maxYear.value) {
        const cacheKey = getCacheKey('analyze', { ...getApiParams(), year })
        if (!getCachedData(cacheKey)) {
          analyzeYear(year).catch(() => {})
        }
      }
    }
  }

  function getMoodColor(mood) {
    const colors = {
      optimistic: '#22c55e',
      challenging: '#ef4444',
      serious: '#64748b',
      harmonious: '#8b5cf6',
      transformative: '#f59e0b',
      neutral: '#60a5fa'
    }
    return colors[mood] || colors.neutral
  }

  function getMoodEmoji(mood) {
    const emojis = {
      optimistic: '🌟',
      challenging: '⚡',
      serious: '🌑',
      harmonious: '🌸',
      transformative: '🦋',
      neutral: '🌤️'
    }
    return emojis[mood] || emojis.neutral
  }

  function getIntensityColor(intensity) {
    if (intensity >= 9) return '#ef4444'
    if (intensity >= 7) return '#f59e0b'
    if (intensity >= 5) return '#60a5fa'
    if (intensity >= 3) return '#22c55e'
    return '#64748b'
  }

  function updateChartData(field, value) {
    chartData[field] = value
    selectedChartId.value = null
    clearLifeScriptCache()
  }

  function resetAnalysis() {
    analysisResult.value = null
    scriptResult.value = null
    rangeResult.value = null
    keyYearsResult.value = null
  }

  return {
    loading,
    loadingScript,
    loadingRange,
    loadingKeyYears,
    error,
    errorMessage,
    
    selectedChartId,
    myCharts,
    chartData,
    
    analysisResult,
    scriptResult,
    rangeResult,
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
    analyzeRange,
    getKeyYears,
    analyzeAndGenerateScript,
    preloadNearbyYears,
    getMoodColor,
    getMoodEmoji,
    getIntensityColor,
    updateChartData,
    resetAnalysis,
    clearLifeScriptCache
  }
}

export function getLifeScriptStarStyle(index) {
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
