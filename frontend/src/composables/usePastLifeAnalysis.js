import { ref, computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { pastLifeApi, chartApi, geoApi, synastryApi } from '@/api'
import { useUserStore } from '@/stores/user'

const PAST_LIFE_CACHE = new Map()
const CACHE_MAX_AGE = 24 * 60 * 60 * 1000

function getCacheKey(type, params) {
  return `${type}:${JSON.stringify(params)}`
}

function getCachedData(key) {
  if (PAST_LIFE_CACHE.has(key)) {
    const cached = PAST_LIFE_CACHE.get(key)
    if (Date.now() - cached.timestamp < CACHE_MAX_AGE) {
      return cached.data
    }
    PAST_LIFE_CACHE.delete(key)
  }
  return null
}

function setCachedData(key, data) {
  if (PAST_LIFE_CACHE.size > 50) {
    const keys = PAST_LIFE_CACHE.keys()
    const oldestKey = keys.next().value
    PAST_LIFE_CACHE.delete(oldestKey)
  }
  PAST_LIFE_CACHE.set(key, {
    data,
    timestamp: Date.now()
  })
}

function clearPastLifeCache() {
  PAST_LIFE_CACHE.clear()
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

const DEFAULT_SYNASTRY = {
  personA: { ...DEFAULT_CHART },
  personB: { ...DEFAULT_CHART, name: '' }
}

export function usePastLifeAnalysis() {
  const userStore = useUserStore()

  const loading = ref(false)
  const loadingStory = ref(false)
  const loadingSynastry = ref(false)
  const loadingRecords = ref(false)
  const loadingOrders = ref(false)
  const error = ref(false)
  const errorMessage = ref('')

  const activeTab = ref('single')
  const selectedChartId = ref(null)
  const myCharts = ref([])
  
  const chartData = reactive({ ...DEFAULT_CHART })
  const synastryData = reactive({
    personA: { ...DEFAULT_CHART },
    personB: { ...DEFAULT_CHART, name: '' }
  })

  const themeResult = ref(null)
  const storyResult = ref(null)
  const synastryThemeResult = ref(null)
  const synastryStoryResult = ref(null)
  const myRecords = ref([])
  const mySynastryRecords = ref([])
  const totalRecords = ref(0)
  const totalSynastryRecords = ref(0)
  const loadingSingleRecords = ref(false)
  const loadingSynastryRecords = ref(false)
  const errorSingleRecords = ref(false)
  const errorSynastryRecords = ref(false)
  const hasLoadedSingleRecords = ref(false)
  const hasLoadedSynastryRecords = ref(false)
  const singlePage = ref(1)
  const singlePageSize = ref(20)
  const synastryPage = ref(1)
  const synastryPageSize = ref(20)
  const currentPage = ref(1)
  const pageSize = ref(20)

  const currentOrder = ref(null)
  const orderStatus = ref(null)

  const isLoggedIn = computed(() => userStore.isLoggedIn)

  const hasValidChart = computed(() => {
    return chartData.birthDate && chartData.birthTime && 
           chartData.latitude && chartData.longitude
  })

  const hasValidSynastry = computed(() => {
    return synastryData.personA.birthDate && synastryData.personA.birthTime &&
           synastryData.personA.latitude && synastryData.personA.longitude &&
           synastryData.personB.birthDate && synastryData.personB.birthTime &&
           synastryData.personB.latitude && synastryData.personB.longitude
  })

  async function loadMyCharts() {
    if (!isLoggedIn.value) return
    
    try {
      const result = await chartApi.getMyCharts({ skip: 0, limit: 50 })
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

  function applyChartToForm(chartId, target = 'single') {
    if (!chartId) return
    
    const chart = myCharts.value.find(c => c.id === chartId)
    if (!chart) return
    
    const targetData = target === 'personA' ? synastryData.personA : 
                       target === 'personB' ? synastryData.personB : chartData
    
    targetData.name = chart.name || ''
    targetData.birthDate = chart.birth_date
    targetData.birthTime = chart.birth_time
    targetData.cityInput = chart.birth_place || ''
    targetData.birthPlace = chart.birth_place || ''
    targetData.latitude = chart.latitude
    targetData.longitude = chart.longitude
    targetData.houseSystem = chart.house_system || 'placidus'
    
    if (target === 'single') {
      selectedChartId.value = chartId
    }
  }

  function getApiParams(target = 'single') {
    const data = target === 'personA' ? synastryData.personA : 
                 target === 'personB' ? synastryData.personB : chartData
    
    return {
      name: data.name || undefined,
      birth_date: data.birthDate,
      birth_time: data.birthTime,
      birth_place: data.birthPlace || undefined,
      latitude: data.latitude,
      longitude: data.longitude,
      house_system: data.houseSystem
    }
  }

  async function analyzeTheme() {
    if (!hasValidChart.value) {
      error.value = true
      errorMessage.value = '请填写完整的出生信息'
      return null
    }

    const cacheKey = getCacheKey('theme', getApiParams())
    const cached = getCachedData(cacheKey)
    
    if (cached) {
      themeResult.value = cached
      error.value = false
      errorMessage.value = ''
      return cached
    }

    loading.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const params = getApiParams()
      const result = await pastLifeApi.analyzeTheme(params)
      
      themeResult.value = result
      setCachedData(cacheKey, result)
      
      return result
      
    } catch (err) {
      error.value = true
      errorMessage.value = err.message || '分析失败，请稍后重试'
      console.error('分析前世主题失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function generateStory() {
    if (!hasValidChart.value) {
      error.value = true
      errorMessage.value = '请填写完整的出生信息'
      return null
    }

    loadingStory.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const params = getApiParams()
      const result = await pastLifeApi.generateStory(params)
      
      storyResult.value = result
      
      if (isLoggedIn.value) {
        await loadMyRecords()
      }
      
      return result
      
    } catch (err) {
      console.error('生成前世故事失败:', err)
      
      let errorMsg = '生成前世故事失败'
      if (err.message && err.message.includes('超时')) {
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
      loadingStory.value = false
    }
  }

  async function analyzeAndGenerate() {
    const theme = await analyzeTheme()
    if (!theme) return null
    
    const story = await generateStory()
    return story
  }

  async function analyzeSynastryTheme() {
    if (!hasValidSynastry.value) {
      error.value = true
      errorMessage.value = '请填写完整的两人出生信息'
      return null
    }

    loading.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const params = {
        person_a: getApiParams('personA'),
        person_b: getApiParams('personB')
      }
      
      const result = await pastLifeApi.analyzeSynastry(params)
      
      synastryThemeResult.value = result
      
      return result
      
    } catch (err) {
      error.value = true
      errorMessage.value = err.message || '分析失败，请稍后重试'
      console.error('分析合盘前世关系失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function generateSynastryStory() {
    if (!hasValidSynastry.value) {
      error.value = true
      errorMessage.value = '请填写完整的两人出生信息'
      return null
    }

    loadingSynastry.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const params = {
        person_a: getApiParams('personA'),
        person_b: getApiParams('personB')
      }
      
      const result = await pastLifeApi.analyzeSynastry(params)
      synastryThemeResult.value = result
      
      const storyResult = await pastLifeApi.generateSynastryStory(params)
      synastryStoryResult.value = storyResult
      
      if (isLoggedIn.value) {
        await loadMySynastryRecords()
      }
      
      return storyResult
      
    } catch (err) {
      console.error('生成合盘前世故事失败:', err)
      
      let errorMsg = '生成合盘前世故事失败'
      if (err.message && err.message.includes('超时')) {
        errorMsg = '请求超时：AI服务响应时间过长，请稍后重试。'
      } else if (err.message) {
        errorMsg = err.message
      }
      
      error.value = true
      errorMessage.value = errorMsg
      ElMessage.error(errorMsg)
      
      return null
    } finally {
      loadingSynastry.value = false
    }
  }

  async function loadMyRecords(page = 1, size = null, forceReload = false) {
    if (!isLoggedIn.value) return null
    
    if (!forceReload && hasLoadedSingleRecords.value && !errorSingleRecords.value) {
      return { records: myRecords.value, total: totalRecords.value }
    }
    
    const useSize = size || singlePageSize.value
    loadingSingleRecords.value = true
    errorSingleRecords.value = false
    
    try {
      const offset = (page - 1) * useSize
      const result = await pastLifeApi.getMyRecords({
        limit: useSize,
        offset: offset
      })
      
      myRecords.value = result?.records || []
      totalRecords.value = result?.total || 0
      singlePage.value = page
      hasLoadedSingleRecords.value = true
      
      return result
      
    } catch (err) {
      console.error('加载我的前世记录失败:', err)
      errorSingleRecords.value = true
      return null
    } finally {
      loadingSingleRecords.value = false
    }
  }

  async function loadMySynastryRecords(page = 1, size = null, forceReload = false) {
    if (!isLoggedIn.value) return null
    
    if (!forceReload && hasLoadedSynastryRecords.value && !errorSynastryRecords.value) {
      return { records: mySynastryRecords.value, total: totalSynastryRecords.value }
    }
    
    const useSize = size || synastryPageSize.value
    loadingSynastryRecords.value = true
    errorSynastryRecords.value = false
    
    try {
      const offset = (page - 1) * useSize
      const result = await pastLifeApi.getMySynastryRecords({
        limit: useSize,
        offset: offset
      })
      
      mySynastryRecords.value = result?.records || []
      totalSynastryRecords.value = result?.total || 0
      synastryPage.value = page
      hasLoadedSynastryRecords.value = true
      
      return result
      
    } catch (err) {
      console.error('加载我的合盘前世记录失败:', err)
      errorSynastryRecords.value = true
      return null
    } finally {
      loadingSynastryRecords.value = false
    }
  }

  async function createOrder(recordId, recordType = 'single') {
    if (!isLoggedIn.value) {
      ElMessage.warning('请先登录')
      return null
    }

    loadingOrders.value = true
    
    try {
      const result = await pastLifeApi.createOrder({
        record_id: recordId,
        record_type: recordType
      })
      
      currentOrder.value = result
      
      return result
      
    } catch (err) {
      console.error('创建订单失败:', err)
      ElMessage.error(err.message || '创建订单失败')
      return null
    } finally {
      loadingOrders.value = false
    }
  }

  async function upgradeWithOrder(orderNo, recordId, recordType = 'single') {
    if (!isLoggedIn.value) {
      ElMessage.warning('请先登录')
      return null
    }

    loadingOrders.value = true
    
    try {
      const result = await pastLifeApi.upgradeWithOrder({
        order_no: orderNo,
        record_id: recordId,
        record_type: recordType
      })
      
      ElMessage.success('升级成功！已解锁深度版内容')
      
      return result
      
    } catch (err) {
      console.error('升级失败:', err)
      ElMessage.error(err.message || '升级失败')
      return null
    } finally {
      loadingOrders.value = false
    }
  }

  async function getRecordDetail(recordId, isSynastry = false) {
    try {
      if (isSynastry) {
        return await pastLifeApi.getSynastryRecordDetail(recordId)
      } else {
        return await pastLifeApi.getSingleRecordDetail(recordId)
      }
    } catch (err) {
      console.error('获取记录详情失败:', err)
      return null
    }
  }

  async function generateDeepStory(recordId, chartParams = null) {
    if (!isLoggedIn.value) {
      ElMessage.warning('请先登录')
      return null
    }

    loadingStory.value = true
    
    try {
      const params = chartParams || getApiParams()
      const result = await pastLifeApi.generateDeepStory(params)
      
      storyResult.value = result
      
      return result
      
    } catch (err) {
      console.error('生成深度版故事失败:', err)
      ElMessage.error(err.message || '生成深度版故事失败')
      return null
    } finally {
      loadingStory.value = false
    }
  }

  function resetSingle() {
    themeResult.value = null
    storyResult.value = null
    error.value = false
    errorMessage.value = ''
  }

  function resetSynastry() {
    synastryThemeResult.value = null
    synastryStoryResult.value = null
    error.value = false
    errorMessage.value = ''
  }

  function getThemeIcon(theme) {
    const icons = {
      warrior: '⚔️',
      scholar: '📜',
      artist: '🎨',
      royal: '👑',
      monk: '🧘',
      merchant: '💰',
      healer: '💚',
      adventurer: '🧭'
    }
    return icons[theme] || '✨'
  }

  function getRelationshipIcon(relType) {
    const icons = {
      lovers: '💕',
      mentor: '👨‍🏫',
      rival: '⚔️',
      soulmate: '✨',
      family: '👨‍👩‍👧‍👦',
      comrade: '🤝',
      stranger: '🌟'
    }
    return icons[relType] || '✨'
  }

  return {
    loading,
    loadingStory,
    loadingSynastry,
    loadingRecords,
    loadingSingleRecords,
    loadingSynastryRecords,
    errorSingleRecords,
    errorSynastryRecords,
    hasLoadedSingleRecords,
    hasLoadedSynastryRecords,
    loadingOrders,
    error,
    errorMessage,
    
    activeTab,
    selectedChartId,
    myCharts,
    chartData,
    synastryData,
    
    themeResult,
    storyResult,
    synastryThemeResult,
    synastryStoryResult,
    myRecords,
    mySynastryRecords,
    totalRecords,
    totalSynastryRecords,
    currentPage,
    pageSize,
    singlePage,
    singlePageSize,
    synastryPage,
    synastryPageSize,
    
    currentOrder,
    orderStatus,
    
    isLoggedIn,
    hasValidChart,
    hasValidSynastry,
    
    loadMyCharts,
    applyChartToForm,
    analyzeTheme,
    generateStory,
    analyzeAndGenerate,
    analyzeSynastryTheme,
    generateSynastryStory,
    loadMyRecords,
    loadMySynastryRecords,
    createOrder,
    upgradeWithOrder,
    getRecordDetail,
    generateDeepStory,
    resetSingle,
    resetSynastry,
    getThemeIcon,
    getRelationshipIcon,
    clearPastLifeCache
  }
}

export function usePastLifeShare() {
  const loading = ref(false)
  const sharedData = ref(null)
  const error = ref(false)
  const errorMessage = ref('')

  async function loadSharedStory(shareCode) {
    if (!shareCode) {
      error.value = true
      errorMessage.value = '分享码无效'
      return null
    }

    loading.value = true
    error.value = false
    errorMessage.value = ''

    try {
      const result = await pastLifeApi.getSharedByCode(shareCode)
      sharedData.value = result
      return result
    } catch (err) {
      console.error('获取分享故事失败:', err)
      error.value = true
      errorMessage.value = err.message || '分享链接不存在或已失效'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    sharedData,
    error,
    errorMessage,
    loadSharedStory
  }
}

export function getPastLifeStarStyle(index) {
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
