<template>
  <div class="ai-interpretation-container">
    <div class="interpretation-header">
      <div class="header-icon">
        <el-icon size="24"><MagicStick /></el-icon>
      </div>
      <div class="header-title">
        <h3>AI智能解读</h3>
        <p class="subtitle">基于千问大模型的专业星盘分析</p>
      </div>
      <div class="header-actions">
        <button
          class="regenerate-btn"
          :class="{ 'btn-loading': loading }"
          :disabled="loading || !hasChartData"
          @click="handleRegenerate"
        >
          <el-icon v-if="loading"><Loading /></el-icon>
          <el-icon v-else><Refresh /></el-icon>
          <span>{{ loading ? '解读中...' : '重新生成' }}</span>
        </button>
      </div>
    </div>

    <Transition name="fade" mode="out-in">
      <div v-if="displayState === 'empty'" key="empty" class="empty-state">
        <div class="empty-icon">
          <el-icon size="48"><Star /></el-icon>
        </div>
        <p class="empty-text">请先计算星盘后再进行AI解读</p>
      </div>

      <div v-else-if="displayState === 'loading'" key="loading" class="loading-state">
        <div class="loading-content">
          <div class="loading-spinner"></div>
          <div class="loading-text">
            <p class="loading-title">AI正在分析您的星盘...</p>
            <p class="loading-desc">正在结合行星位置、星座、宫位和相位进行综合解读</p>
          </div>
        </div>
      </div>

      <div v-else-if="displayState === 'error'" key="error" class="error-state">
        <div class="error-content">
          <div class="error-icon">
            <el-icon size="40"><Warning /></el-icon>
          </div>
          <p class="error-title">解读生成失败</p>
          <p class="error-message">{{ error }}</p>
          <button class="retry-btn" @click="handleRegenerate">
            <el-icon><Refresh /></el-icon>
            <span>重新尝试</span>
          </button>
        </div>
      </div>

      <div v-else-if="displayState === 'content'" key="content" class="interpretation-content">
        <div class="interpretation-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>

        <div class="tab-panels">
          <Transition name="slide-fade" mode="out-in">
            <div :key="activeTab" class="tab-panel">
              <template v-if="activeTab === 'all'">
                <div v-for="(section, sectionKey) in formattedSections" :key="sectionKey" class="section-block">
                  <div class="section-header">
                    <span class="section-icon">{{ getSectionIcon(sectionKey) }}</span>
                    <h4 class="section-title">{{ getSectionTitle(sectionKey) }}</h4>
                  </div>
                  <div class="section-content" v-html="formatContent(section)"></div>
                </div>
              </template>
              <template v-else>
                <div v-if="formattedSections[activeTab]" class="section-block">
                  <div class="section-header">
                    <span class="section-icon">{{ getSectionIcon(activeTab) }}</span>
                    <h4 class="section-title">{{ getSectionTitle(activeTab) }}</h4>
                  </div>
                  <div class="section-content" v-html="formatContent(formattedSections[activeTab])"></div>
                </div>
                <div v-else class="no-section-data">
                  <p>该板块暂无详细解读</p>
                </div>
              </template>
            </div>
          </Transition>
        </div>
      </div>

      <div v-else-if="displayState === 'prompt'" key="prompt" class="prompt-state">
        <div class="prompt-content">
          <div class="prompt-icon">
            <el-icon size="40"><MagicStick /></el-icon>
          </div>
          <p class="prompt-title">准备好开始AI解读了吗？</p>
          <p class="prompt-desc">点击下方按钮，AI将为您生成专业的星盘解读</p>
          <button
            class="generate-btn"
            :class="{ 'btn-loading': loading }"
            :disabled="loading"
            @click="handleGenerate"
          >
            <el-icon v-if="loading"><Loading /></el-icon>
            <el-icon v-else><MagicStick /></el-icon>
            <span>{{ loading ? '解读中...' : '开始AI解读' }}</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { aiInterpretationApi } from '@/api'
import { MagicStick, Loading, Refresh, Star, Warning } from '@element-plus/icons-vue'

const props = defineProps({
  chartData: {
    type: Object,
    default: null
  },
  chartInput: {
    type: Object,
    default: null
  },
  autoGenerate: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['generated', 'error'])

const loading = ref(false)
const error = ref(null)
const interpretationData = ref(null)
const activeTab = ref('all')

const hasChartData = computed(() => {
  return props.chartData && props.chartData.planets && props.chartData.planets.length > 0
})

const displayState = computed(() => {
  if (!hasChartData.value) {
    return 'empty'
  }
  if (loading.value) {
    return 'loading'
  }
  if (error.value) {
    return 'error'
  }
  if (interpretationData.value) {
    return 'content'
  }
  return 'prompt'
})

const tabs = [
  { key: 'all', label: '全部解读', icon: '📋' },
  { key: 'personality', label: '性格特质', icon: '🧠' },
  { key: 'career', label: '事业发展', icon: '💼' },
  { key: 'love', label: '感情婚姻', icon: '❤️' },
  { key: 'fortune', label: '运势趋势', icon: '🌟' }
]

const sectionTitles = {
  personality: '性格特质分析',
  career: '事业发展分析',
  love: '感情婚姻分析',
  fortune: '运势趋势分析',
  raw: '综合解读'
}

const sectionIcons = {
  personality: '🧠',
  career: '💼',
  love: '❤️',
  fortune: '🌟',
  raw: '📖'
}

const formattedSections = computed(() => {
  if (!interpretationData.value?.sections) {
    return {}
  }
  
  const sections = interpretationData.value.sections
  const result = {}
  
  for (const [key, value] of Object.entries(sections)) {
    if (value && value.trim()) {
      result[key] = value
    }
  }
  
  return result
})

function getSectionTitle(key) {
  return sectionTitles[key] || '解读'
}

function getSectionIcon(key) {
  return sectionIcons[key] || '📖'
}

function escapeHtml(text) {
  if (typeof text !== 'string') return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const ListType = {
  NONE: null,
  UL: 'ul',
  OL: 'ol'
}

function formatContent(content) {
  if (!content) return ''
  
  let formatted = content
    .replace(/\n{3,}/g, '\n\n')
    .trim()
  
  const lines = formatted.split('\n')
  const result = []
  let currentListType = ListType.NONE
  
  const closeCurrentList = () => {
    if (currentListType === ListType.UL) {
      result.push('</ul>')
    } else if (currentListType === ListType.OL) {
      result.push('</ol>')
    }
    currentListType = ListType.NONE
  }
  
  const startNewList = (type) => {
    closeCurrentList()
    currentListType = type
    if (type === ListType.UL) {
      result.push('<ul class="interpret-list">')
    } else if (type === ListType.OL) {
      result.push('<ol class="interpret-ol">')
    }
  }
  
  for (const line of lines) {
    const trimmed = line.trim()
    
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
      if (currentListType !== ListType.UL) {
        startNewList(ListType.UL)
      }
      const itemContent = trimmed.replace(/^[-•*]\s+/, '')
      result.push(`<li>${escapeHtml(itemContent)}</li>`)
    } else if (trimmed.match(/^\d+\.\s/)) {
      if (currentListType !== ListType.OL) {
        startNewList(ListType.OL)
      }
      const itemContent = trimmed.replace(/^\d+\.\s*/, '')
      result.push(`<li>${escapeHtml(itemContent)}</li>`)
    } else if (trimmed) {
      closeCurrentList()
      
      if (trimmed.match(/^[一二三四五六七八九十]+[、\.]/) || trimmed.match(/^[（(][一二三四五六七八九十\d]+[）)]/)) {
        result.push(`<p class="sub-title">${escapeHtml(trimmed)}</p>`)
      } else {
        result.push(`<p>${escapeHtml(trimmed)}</p>`)
      }
    } else {
      closeCurrentList()
    }
  }
  
  closeCurrentList()
  
  return result.join('')
}

function getFriendlyErrorMessage(errorType, errorMessage) {
  const errorMessages = {
    configuration_error: 'API配置错误：请检查后端的 DASHSCOPE_API_KEY 是否正确配置。',
    invalid_input: `输入数据错误：${errorMessage || '请检查星盘数据是否完整。'}`,
    chart_error: `星盘数据错误：${errorMessage || '无法获取星盘数据，请重新计算星盘。'}`,
    api_error: `API调用失败：${errorMessage || '无法连接到AI服务，请稍后重试。'}`,
    not_found: `资源不存在：${errorMessage || '请求的资源不存在。'}`,
    server_error: `服务器错误：${errorMessage || '服务器内部错误，请稍后重试。'}`
  }
  
  if (errorType && errorMessages[errorType]) {
    return errorMessages[errorType]
  }
  
  if (errorMessage) {
    if (errorMessage.includes('401') || errorMessage.includes('认证') || errorMessage.includes('API key')) {
      return 'API认证失败：请检查 DASHSCOPE_API_KEY 是否正确配置。'
    }
    if (errorMessage.includes('403') || errorMessage.includes('余额') || errorMessage.includes('权限')) {
      return 'API访问被拒绝：可能是账户余额不足或权限问题。'
    }
    if (errorMessage.includes('429') || errorMessage.includes('频率')) {
      return 'API调用频率超限：请稍后再试。'
    }
    if (errorMessage.includes('网络') || errorMessage.includes('连接') || errorMessage.includes('Connect')) {
      return '网络连接失败：无法连接到AI服务，请检查网络连接。'
    }
    if (errorMessage.includes('超时') || errorMessage.includes('timeout')) {
      return 'API请求超时：服务器响应时间过长，请稍后重试。'
    }
    return errorMessage
  }
  
  return 'AI解读生成失败，请稍后重试。'
}

async function generateInterpretation() {
  if (!hasChartData.value) {
    ElMessage.warning('请先计算星盘')
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    const requestData = {
      chart_data: props.chartData
    }
    
    if (props.chartInput) {
      requestData.name = props.chartInput.name
      requestData.birth_date = props.chartInput.birthDate
      requestData.birth_time = props.chartInput.birthTime
      requestData.latitude = props.chartInput.latitude
      requestData.longitude = props.chartInput.longitude
      requestData.birth_place = props.chartInput.birthPlace
      requestData.house_system = props.chartInput.houseSystem
    }
    
    console.log('发送AI解读请求:', requestData)
    
    const result = await aiInterpretationApi.generateInterpretationDirect(requestData)
    
    console.log('收到AI解读响应:', result)
    
    if (result && result.success) {
      interpretationData.value = {
        content: result.content,
        sections: result.sections
      }
      emit('generated', interpretationData.value)
      ElMessage.success('AI解读生成成功')
    } else {
      const errorType = result?.error_type || 'unknown'
      const errorMsg = result?.error || '生成失败'
      const friendlyError = getFriendlyErrorMessage(errorType, errorMsg)
      throw new Error(friendlyError)
    }
  } catch (err) {
    console.error('AI解读生成失败:', err)
    
    let errorMessage = err.message || '生成失败，请稍后重试'
    
    if (err.response) {
      const detail = err.response.data?.detail
      if (detail) {
        errorMessage = getFriendlyErrorMessage('api_error', detail)
      }
    }
    
    if (err.message && err.message.includes('Network Error')) {
      errorMessage = '网络连接失败：无法连接到后端服务器，请检查后端服务是否启动。'
    }
    
    error.value = errorMessage
    emit('error', err)
    ElMessage.error({
      message: errorMessage,
      duration: 5000,
      showClose: true
    })
  } finally {
    loading.value = false
  }
}

function handleGenerate() {
  generateInterpretation()
}

function handleRegenerate() {
  interpretationData.value = null
  error.value = null
  generateInterpretation()
}

watch(
  () => props.chartData,
  (newVal) => {
    if (newVal && props.autoGenerate && !interpretationData.value && !loading.value) {
      generateInterpretation()
    }
  },
  { deep: true }
)
</script>

<style lang="scss" scoped>
.ai-interpretation-container {
  width: 100%;
  background: linear-gradient(135deg, rgba(15, 15, 35, 0.95), rgba(20, 20, 45, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.interpretation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.1), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
  
  .header-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.3), transparent);
    border-radius: 12px;
    color: #a78bfa;
  }
  
  .header-title {
    flex: 1;
    margin-left: 16px;
    
    h3 {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 600;
      color: #fff;
    }
    
    .subtitle {
      margin: 4px 0 0;
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .header-actions {
    display: flex;
    align-items: center;
  }
  
  .regenerate-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border: none;
    border-radius: 10px;
    color: #fff;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    &.btn-loading {
      .el-icon {
        animation: spin 1s linear infinite;
      }
    }
  }
}

.empty-state,
.loading-state,
.error-state,
.prompt-state {
  padding: 60px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-state,
.prompt-state {
  .empty-icon,
  .prompt-icon {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.15), transparent);
    border-radius: 50%;
    color: rgba(139, 92, 246, 0.6);
    margin-bottom: 20px;
  }
  
  .empty-text,
  .prompt-title {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }
  
  .prompt-desc {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
    margin: 8px 0 24px;
  }
  
  .generate-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 32px;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border: none;
    border-radius: 12px;
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    &.btn-loading {
      .el-icon {
        animation: spin 1s linear infinite;
      }
    }
  }
}

.loading-state {
  .loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .loading-spinner {
      width: 50px;
      height: 50px;
      border: 3px solid rgba(139, 92, 246, 0.2);
      border-top-color: #8b5cf6;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 24px;
    }
    
    .loading-text {
      .loading-title {
        font-size: 1rem;
        color: #fff;
        margin: 0 0 8px;
      }
      
      .loading-desc {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
      }
    }
  }
}

.error-state {
  .error-content {
    .error-icon {
      color: #f87171;
      margin-bottom: 16px;
    }
    
    .error-title {
      font-size: 1rem;
      color: #f87171;
      margin: 0 0 8px;
    }
    
    .error-message {
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.6);
      margin: 0 0 20px;
      max-width: 400px;
    }
    
    .retry-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 24px;
      background: rgba(248, 113, 113, 0.1);
      border: 1px solid rgba(248, 113, 113, 0.3);
      border-radius: 10px;
      color: #f87171;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background: rgba(248, 113, 113, 0.2);
      }
    }
  }
}

.interpretation-content {
  padding: 0;
  
  .interpretation-tabs {
    display: flex;
    gap: 4px;
    padding: 16px 20px;
    background: rgba(0, 0, 0, 0.2);
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
    overflow-x: auto;
    
    .tab-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 10px 16px;
      background: transparent;
      border: none;
      border-radius: 8px;
      color: rgba(255, 255, 255, 0.6);
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.3s ease;
      white-space: nowrap;
      
      .tab-icon {
        font-size: 1rem;
      }
      
      &:hover {
        color: rgba(255, 255, 255, 0.8);
        background: rgba(139, 92, 246, 0.1);
      }
      
      &.active {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.2));
        color: #a78bfa;
      }
    }
  }
  
  .tab-panels {
    padding: 24px;
    
    .tab-panel {
      .section-block {
        margin-bottom: 28px;
        padding: 20px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(99, 102, 241, 0.03));
        border-radius: 12px;
        border: 1px solid rgba(139, 92, 246, 0.1);
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .section-header {
          display: flex;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(139, 92, 246, 0.15);
          
          .section-icon {
            font-size: 1.5rem;
            margin-right: 12px;
          }
          
          .section-title {
            margin: 0;
            font-size: 1rem;
            font-weight: 600;
            color: #a78bfa;
          }
        }
        
        .section-content {
          line-height: 1.8;
          color: rgba(255, 255, 255, 0.85);
          font-size: 0.95rem;
          
          p {
            margin: 0 0 12px;
            
            &:last-child {
              margin-bottom: 0;
            }
          }
          
          .sub-title {
            font-weight: 600;
            color: #a78bfa;
            margin: 16px 0 8px;
          }
          
          .interpret-list,
          .interpret-ol {
            margin: 12px 0;
            padding-left: 24px;
            
            li {
              margin: 8px 0;
              color: rgba(255, 255, 255, 0.8);
              
              &::marker {
                color: #a78bfa;
              }
            }
          }
        }
      }
      
      .no-section-data {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(10px);
  opacity: 0;
}
</style>
