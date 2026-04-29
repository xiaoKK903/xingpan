import { ref, computed, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { synastryApi, chartApi } from '@/api'
import { useUserStore } from '@/stores/user'

const DEFAULT_PERSON = {
  name: '',
  birthDate: '1990-01-01',
  birthTime: '12:00',
  cityInput: '北京',
  birthPlace: '北京',
  latitude: 39.9042,
  longitude: 116.4074,
  houseSystem: 'placidus'
}

export function useSynastryAnalysis() {
  const router = useRouter()
  const route = useRoute()
  const userStore = useUserStore()

  const calculating = ref(false)
  const saving = ref(false)
  const loadingRecord = ref(false)
  const showResult = ref(false)
  const showShareDialog = ref(false)
  const copied = ref(false)

  const selectedChartA = ref(null)
  const selectedChartB = ref(null)
  const savedRecordId = ref(null)
  const shareLink = ref('')
  const myCharts = ref([])

  const personA = reactive({ ...DEFAULT_PERSON })
  const personB = reactive({
    ...DEFAULT_PERSON,
    birthDate: '1992-06-15',
    birthTime: '10:30',
    cityInput: '上海',
    birthPlace: '上海',
    latitude: 31.2304,
    longitude: 121.4737
  })

  const analysisData = ref(null)
  const originalSynastryData = ref(null)

  const isLoggedIn = computed(() => userStore.isLoggedIn)

  const canCalculate = computed(() => {
    return personA.birthDate && personA.birthTime && personB.birthDate && personB.birthTime
  })

  const personALabel = computed(() => personA.name || '人物 A')
  const personBLabel = computed(() => personB.name || '人物 B')

  const totalScore = computed(() => {
    return analysisData.value?.compatibility?.total_score ?? 60
  })

  const scoreLevel = computed(() => {
    return analysisData.value?.compatibility?.score_level || {}
  })

  const scoreLevelColor = computed(() => {
    return scoreLevel.value?.color || '#8b5cf6'
  })

  const scoreLevelSecondaryColor = computed(() => {
    return scoreLevelColor.value + 'aa'
  })

  const dimensions = computed(() => {
    return analysisData.value?.compatibility?.dimensions || {}
  })

  const dimensionsArray = computed(() => {
    const dims = dimensions.value
    if (!dims || typeof dims !== 'object') return []
    
    const result = []
    for (const [key, dim] of Object.entries(dims)) {
      if (dim && typeof dim.score === 'number') {
        result.push({
          name: dim.name || key,
          score: dim.score,
          key
        })
      }
    }
    return result
  })

  const elementAnalysis = computed(() => {
    return analysisData.value?.personality_analysis?.element_analysis || {}
  })

  const elementCompatibilityScore = computed(() => {
    const score = elementAnalysis.value?.compatibility_score
    return typeof score === 'number' ? score : 60
  })

  const interactionData = computed(() => {
    return analysisData.value?.personality_analysis?.interaction_style || {}
  })

  const interactionStyles = computed(() => {
    const styles = interactionData.value?.style_names
    return Array.isArray(styles) ? styles : []
  })

  const strengths = computed(() => {
    const items = analysisData.value?.personality_analysis?.strengths
    return Array.isArray(items) ? items : []
  })

  const challenges = computed(() => {
    const items = analysisData.value?.personality_analysis?.challenges
    return Array.isArray(items) ? items : []
  })

  const keyAspects = computed(() => {
    const aspects = analysisData.value?.compatibility?.key_aspects
    return Array.isArray(aspects) ? aspects : []
  })

  const futureAdvice = computed(() => {
    const advice = analysisData.value?.personality_analysis?.future_advice
    return Array.isArray(advice) ? advice : []
  })

  const summaryText = computed(() => {
    return analysisData.value?.personality_analysis?.summary?.text || ''
  })

  function getScoreColor(score) {
    const num = typeof score === 'number' ? score : 60
    if (num >= 85) return '#22c55e'
    if (num >= 70) return '#eab308'
    if (num >= 55) return '#f97316'
    return '#ef4444'
  }

  function getScoreGradient(score) {
    const num = typeof score === 'number' ? score : 60
    if (num >= 85) return 'linear-gradient(90deg, #22c55e, #16a34a)'
    if (num >= 70) return 'linear-gradient(90deg, #eab308, #ca8a04)'
    if (num >= 55) return 'linear-gradient(90deg, #f97316, #ea580c)'
    return 'linear-gradient(90deg, #ef4444, #dc2626)'
  }

  function getStrokeDasharray(score) {
    const circumference = 502.65
    const safeScore = Math.max(0, Math.min(100, typeof score === 'number' ? score : 60))
    const dasharray = (safeScore / 100) * circumference
    return `${dasharray} ${circumference}`
  }

  async function loadMyCharts() {
    if (!isLoggedIn.value) return
    
    try {
      const result = await chartApi.getMyCharts({ page: 1, page_size: 20 })
      myCharts.value = Array.isArray(result?.records) ? result.records : []
    } catch (err) {
      console.error('加载星盘列表失败:', err)
    }
  }

  function applyChartToPerson(chartId, person) {
    if (!chartId) return
    
    const chart = myCharts.value.find(c => c.id === chartId)
    if (!chart) return
    
    person.name = chart.name || ''
    person.birthDate = chart.birth_date
    person.birthTime = chart.birth_time
    person.cityInput = chart.birth_place || ''
    person.birthPlace = chart.birth_place || ''
    person.latitude = chart.latitude
    person.longitude = chart.longitude
    person.houseSystem = 'placidus'
  }

  function applyChartToPersonA(chartId) {
    applyChartToPerson(chartId, personA)
  }

  function applyChartToPersonB(chartId) {
    applyChartToPerson(chartId, personB)
  }

  async function calculateAnalysis() {
    if (!canCalculate.value) {
      ElMessage.warning('请填写完整的出生信息')
      return
    }
    
    calculating.value = true
    savedRecordId.value = null
    
    try {
      const result = await synastryApi.calculateAndAnalyze({
        person_a: {
          name: personA.name || '人物A',
          birth_date: personA.birthDate,
          birth_time: personA.birthTime,
          birth_place: personA.birthPlace,
          latitude: personA.latitude,
          longitude: personA.longitude,
          house_system: personA.houseSystem
        },
        person_b: {
          name: personB.name || '人物B',
          birth_date: personB.birthDate,
          birth_time: personB.birthTime,
          birth_place: personB.birthPlace,
          latitude: personB.latitude,
          longitude: personB.longitude,
          house_system: personB.houseSystem
        }
      })
      
      analysisData.value = result?.analysis
      originalSynastryData.value = result?.synastry
      showResult.value = true
      
      ElMessage.success('分析完成')
      
    } catch (error) {
      console.error('分析失败:', error)
      ElMessage.error(error.message || '分析失败，请稍后重试')
    } finally {
      calculating.value = false
    }
  }

  function goBack() {
    showResult.value = false
    savedRecordId.value = null
  }

  async function saveRecord() {
    if (!isLoggedIn.value) {
      ElMessage.warning('请先登录后再保存报告')
      router.push('/login')
      return
    }
    
    if (!analysisData.value) {
      ElMessage.warning('没有可保存的分析数据')
      return
    }
    
    saving.value = true
    
    try {
      const result = await synastryApi.saveRecord({
        name: `${personALabel.value} & ${personBLabel.value}`,
        person_a_name: personA.name || '人物A',
        person_a_birth_date: personA.birthDate,
        person_a_birth_time: personA.birthTime,
        person_a_birth_place: personA.birthPlace,
        person_a_latitude: personA.latitude,
        person_a_longitude: personA.longitude,
        person_b_name: personB.name || '人物B',
        person_b_birth_date: personB.birthDate,
        person_b_birth_time: personB.birthTime,
        person_b_birth_place: personB.birthPlace,
        person_b_latitude: personB.latitude,
        person_b_longitude: personB.longitude,
        synastry_data: originalSynastryData.value,
        analysis_data: analysisData.value
      })
      
      savedRecordId.value = result?.id
      ElMessage.success('报告保存成功')
      
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error(error.message || '保存失败')
    } finally {
      saving.value = false
    }
  }

  async function shareRecord() {
    if (!savedRecordId.value) {
      ElMessage.warning('请先保存报告后再分享')
      return
    }
    
    try {
      const result = await synastryApi.generateShare(savedRecordId.value)
      const baseUrl = window.location.origin
      shareLink.value = `${baseUrl}/synastry/share/${result.share_code}`
      showShareDialog.value = true
    } catch (error) {
      console.error('生成分享链接失败:', error)
      ElMessage.error(error.message || '生成分享链接失败')
    }
  }

  async function copyShareLink() {
    try {
      await navigator.clipboard.writeText(shareLink.value)
      copied.value = true
      ElMessage.success('链接已复制')
      setTimeout(() => {
        copied.value = false
      }, 2000)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
    }
  }

  function applyRecordData(record) {
    if (!record) return
    
    if (record.analysis_data) {
      analysisData.value = record.analysis_data
    }
    if (record.synastry_data) {
      originalSynastryData.value = record.synastry_data
    }
    
    if (record.person_a_name !== undefined) {
      personA.name = record.person_a_name || '人物A'
    }
    if (record.person_a_birth_date) {
      personA.birthDate = record.person_a_birth_date
    }
    if (record.person_a_birth_time) {
      personA.birthTime = record.person_a_birth_time
    }
    if (record.person_a_birth_place) {
      personA.birthPlace = record.person_a_birth_place
      personA.cityInput = record.person_a_birth_place
    }
    if (typeof record.person_a_latitude === 'number') {
      personA.latitude = record.person_a_latitude
    }
    if (typeof record.person_a_longitude === 'number') {
      personA.longitude = record.person_a_longitude
    }
    
    if (record.person_b_name !== undefined) {
      personB.name = record.person_b_name || '人物B'
    }
    if (record.person_b_birth_date) {
      personB.birthDate = record.person_b_birth_date
    }
    if (record.person_b_birth_time) {
      personB.birthTime = record.person_b_birth_time
    }
    if (record.person_b_birth_place) {
      personB.birthPlace = record.person_b_birth_place
      personB.cityInput = record.person_b_birth_place
    }
    if (typeof record.person_b_latitude === 'number') {
      personB.latitude = record.person_b_latitude
    }
    if (typeof record.person_b_longitude === 'number') {
      personB.longitude = record.person_b_longitude
    }
    
    if (record.id) {
      savedRecordId.value = record.id
    }
    showResult.value = true
  }

  async function loadRecordById(id) {
    if (!id) return
    
    loadingRecord.value = true
    try {
      const result = await synastryApi.getById(id)
      applyRecordData(result)
      ElMessage.success('加载成功')
    } catch (error) {
      console.error('加载记录失败:', error)
      ElMessage.error(error.message || '加载失败，请稍后重试')
    } finally {
      loadingRecord.value = false
    }
  }

  async function loadRecordByShareCode(shareCode) {
    if (!shareCode) return
    
    loadingRecord.value = true
    try {
      const result = await synastryApi.getByShareCode(shareCode)
      applyRecordData(result)
      ElMessage.success('加载成功')
    } catch (error) {
      console.error('加载分享记录失败:', error)
      ElMessage.error(error.message || '链接无效或已过期')
    } finally {
      loadingRecord.value = false
    }
  }

  watch(isLoggedIn, (newVal) => {
    if (newVal) {
      loadMyCharts()
    }
  })

  return {
    calculating,
    saving,
    loadingRecord,
    showResult,
    showShareDialog,
    copied,
    selectedChartA,
    selectedChartB,
    savedRecordId,
    shareLink,
    myCharts,
    personA,
    personB,
    analysisData,
    originalSynastryData,
    isLoggedIn,
    canCalculate,
    personALabel,
    personBLabel,
    totalScore,
    scoreLevel,
    scoreLevelColor,
    scoreLevelSecondaryColor,
    dimensions,
    dimensionsArray,
    elementAnalysis,
    elementCompatibilityScore,
    interactionData,
    interactionStyles,
    strengths,
    challenges,
    keyAspects,
    futureAdvice,
    summaryText,
    loadMyCharts,
    applyChartToPersonA,
    applyChartToPersonB,
    calculateAnalysis,
    goBack,
    saveRecord,
    shareRecord,
    copyShareLink,
    loadRecordById,
    loadRecordByShareCode,
    getScoreColor,
    getScoreGradient,
    getStrokeDasharray
  }
}

export function getStarStyle(index) {
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
