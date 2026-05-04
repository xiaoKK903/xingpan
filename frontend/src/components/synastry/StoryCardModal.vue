<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="handleClose"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    custom-class="story-card-modal"
    destroy-on-close
  >
    <template #header>
      <div class="modal-header">
        <span class="header-icon">✨</span>
        <span class="header-title">合盘故事卡生成成功!</span>
      </div>
    </template>
    
    <div class="modal-content">
      <div class="loading-container" v-if="isGenerating">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">{{ loadingText }}</p>
      </div>
      
      <div class="card-display" v-else-if="storyCard">
        <StoryCard
          :card-data="storyCard"
          :show-actions="false"
          :show-meta="true"
          @view-detail="handleViewDetail"
        />
        
        <div class="card-actions" v-if="!isDetailMode">
          <div class="action-row">
            <el-button
              type="primary"
              size="large"
              :class="{ 'is-mounted': isMounted }"
              :loading="isMounting"
              @click="handleMountCard"
              class="mount-action-btn"
            >
              <template #icon>
                <span v-if="isMounted">✓</span>
                <span v-else>📌</span>
              </template>
              {{ isMounted ? '已挂载到故事墙' : '一键挂载到故事墙' }}
            </el-button>
          </div>
          
          <div class="action-row secondary-actions">
            <el-button
              type="default"
              size="large"
              :loading="isSharing"
              @click="handleShareCard"
              class="secondary-btn"
            >
              <template #icon>
                <span>📤</span>
              </template>
              分享故事卡
            </el-button>
            
            <el-button
              type="default"
              size="large"
              @click="handleViewDetail"
              class="secondary-btn"
            >
              <template #icon>
                <span>📖</span>
              </template>
              查看完整故事
            </el-button>
          </div>
          
          <div class="tips-text">
            <span class="tips-icon">💡</span>
            挂载后的故事卡将在您的故事墙中展示，其他用户可以通过您的个人主页浏览。
          </div>
        </div>
        
        <div class="detail-mode-content" v-else>
          <div class="story-full-content">
            <h4 class="detail-section-title">完整故事内容</h4>
            <div class="story-text">
              {{ storyCard.story_content }}
            </div>
          </div>
          
          <div class="match-details" v-if="storyCard.metadata?.matched_conditions?.length">
            <h4 class="detail-section-title">匹配条件</h4>
            <div class="match-conditions-list">
              <div 
                v-for="(condition, index) in storyCard.metadata.matched_conditions" 
                :key="index"
                class="match-condition-item"
              >
                <span class="check-icon">✓</span>
                <span class="condition-text">{{ condition }}</span>
              </div>
            </div>
          </div>
          
          <div class="action-row back-row">
            <el-button
              type="default"
              size="large"
              @click="isDetailMode = false"
            >
              返回故事卡
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="error-container" v-else-if="hasError">
        <div class="error-icon">😢</div>
        <p class="error-text">故事卡生成失败</p>
        <p class="error-detail">{{ errorMessage }}</p>
        <el-button type="primary" @click="retryGenerate">重新生成</el-button>
      </div>
    </div>
    
    <template #footer v-if="!isGenerating && storyCard">
      <div class="modal-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button 
          type="primary" 
          @click="handleGoToStoryWall"
          v-if="isMounted"
        >
          前往故事墙查看
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import StoryCard from './StoryCard.vue'
import { storyCardApi, synastryApi } from '@/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  storyCard: {
    type: Object,
    default: null
  },
  synastryRecordId: {
    type: Number,
    default: null
  },
  synastryData: {
    type: Object,
    default: null
  },
  analysisData: {
    type: Object,
    default: null
  },
  personAName: {
    type: String,
    default: '人物A'
  },
  personBName: {
    type: String,
    default: '人物B'
  },
  autoGenerate: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:visible', 'mounted', 'shared', 'go-to-story-wall'])

const router = useRouter()

const isGenerating = ref(false)
const isMounting = ref(false)
const isSharing = ref(false)
const isDetailMode = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const storyCard = ref(null)
const isMounted = ref(false)

const loadingTexts = [
  '正在分析合盘相位...',
  '匹配前世羁绊模板...',
  '生成专属故事内容...',
  '确定故事卡稀有度...',
  '即将完成...'
]
const loadingIndex = ref(0)
const loadingInterval = ref(null)

const loadingText = computed(() => {
  return loadingTexts[loadingIndex.value] || '正在生成故事卡...'
})

watch(() => props.storyCard, (newVal) => {
  if (newVal) {
    storyCard.value = newVal
    isMounted.value = newVal.is_mounted || false
    isGenerating.value = false
  }
}, { immediate: true })

watch(() => props.visible, (newVal) => {
  if (newVal) {
    if (props.storyCard) {
      storyCard.value = props.storyCard
      isMounted.value = props.storyCard.is_mounted || false
    } else if (props.autoGenerate && !storyCard.value) {
      generateStoryCard()
    }
  }
  if (!newVal) {
    clearLoadingInterval()
    isDetailMode.value = false
  }
})

onBeforeUnmount(() => {
  clearLoadingInterval()
})

function startLoadingAnimation() {
  loadingIndex.value = 0
  clearLoadingInterval()
  loadingInterval.value = setInterval(() => {
    loadingIndex.value = (loadingIndex.value + 1) % loadingTexts.length
  }, 1500)
}

function clearLoadingInterval() {
  if (loadingInterval.value) {
    clearInterval(loadingInterval.value)
    loadingInterval.value = null
  }
}

async function generateStoryCard() {
  if (!props.synastryData && !props.synastryRecordId) {
    hasError.value = true
    errorMessage.value = '缺少合盘数据'
    return
  }
  
  isGenerating.value = true
  hasError.value = false
  startLoadingAnimation()
  
  try {
    const requestData = {
      synastry_record_id: props.synastryRecordId,
      synastry_data: props.synastryData,
      analysis_data: props.analysisData,
      person_a_name: props.personAName,
      person_b_name: props.personBName,
      auto_save: true
    }
    
    const result = await storyCardApi.generate(requestData)
    
    storyCard.value = result
    isMounted.value = result.is_mounted || false
    
    ElMessage.success('故事卡生成成功!')
    
  } catch (error) {
    console.error('生成故事卡失败:', error)
    hasError.value = true
    errorMessage.value = error.message || '生成失败，请稍后重试'
  } finally {
    isGenerating.value = false
    clearLoadingInterval()
  }
}

async function handleMountCard() {
  if (!storyCard.value?.id) return
  
  isMounting.value = true
  
  try {
    const newMountState = !isMounted.value
    await storyCardApi.toggleMount(storyCard.value.id, newMountState)
    
    isMounted.value = newMountState
    storyCard.value.is_mounted = newMountState
    
    if (newMountState) {
      ElMessage.success('已成功挂载到故事墙!')
      emit('mounted', { ...storyCard.value })
    } else {
      ElMessage.info('已从故事墙移除')
    }
    
  } catch (error) {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    isMounting.value = false
  }
}

async function handleShareCard() {
  if (!storyCard.value?.id) return
  
  isSharing.value = true
  
  try {
    const result = await storyCardApi.share(storyCard.value.id)
    
    const shareUrl = `${window.location.origin}/story-card/share/${result.share_code}`
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: storyCard.value.headline || '合盘故事卡',
          text: storyCard.value.story_short || `${storyCard.value.person_a_name} 与 ${storyCard.value.person_b_name} 的合盘故事卡`,
          url: shareUrl
        })
      } catch (err) {
        if (err.name !== 'AbortError') {
          await copyShareLink(shareUrl)
        }
      }
    } else {
      await copyShareLink(shareUrl)
    }
    
    storyCard.value.share_code = result.share_code
    storyCard.value.share_count = result.share_count || (storyCard.value.share_count || 0) + 1
    
    emit('shared', { ...storyCard.value, share_code: result.share_code })
    
  } catch (error) {
    ElMessage.error('分享失败，请稍后重试')
  } finally {
    isSharing.value = false
  }
}

async function copyShareLink(url) {
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('分享链接已复制到剪贴板')
  } catch {
    ElMessage.info('您的浏览器不支持自动复制，请手动复制')
  }
}

function handleViewDetail() {
  if (!storyCard.value) return
  
  if (storyCard.value.story_content) {
    isDetailMode.value = true
  } else {
    loadFullDetail()
  }
}

async function loadFullDetail() {
  if (!storyCard.value?.id) return
  
  isGenerating.value = true
  
  try {
    const result = await storyCardApi.getDetail(storyCard.value.id)
    storyCard.value = result
    isDetailMode.value = true
  } catch (error) {
    ElMessage.error('获取详情失败')
  } finally {
    isGenerating.value = false
  }
}

function retryGenerate() {
  hasError.value = false
  generateStoryCard()
}

function handleClose() {
  emit('update:visible', false)
}

function handleGoToStoryWall() {
  handleClose()
  router.push('/story-wall')
  emit('go-to-story-wall')
}

defineExpose({
  generateStoryCard,
  handleMountCard,
  handleShareCard
})
</script>

<style lang="scss" scoped>
:deep(.story-card-modal) {
  .el-dialog__header {
    padding: 20px 24px 16px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  }
  
  .el-dialog__body {
    padding: 20px 24px;
  }
  
  .el-dialog__footer {
    padding: 16px 24px 20px;
    border-top: 1px solid rgba(139, 92, 246, 0.1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  
  .header-icon {
    font-size: 1.5rem;
  }
  
  .header-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }
}

.modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 300px;
}

.loading-spinner {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 20px;
  
  .spinner-ring {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 4px solid rgba(139, 92, 246, 0.1);
    border-top-color: rgba(139, 92, 246, 0.8);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    
    &::before {
      content: '';
      position: absolute;
      top: 8px;
      left: 8px;
      right: 8px;
      bottom: 8px;
      border: 4px solid rgba(167, 139, 250, 0.1);
      border-top-color: rgba(167, 139, 250, 0.6);
      border-radius: 50%;
      animation: spin 0.8s linear infinite reverse;
    }
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.card-display {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.card-actions {
  width: 100%;
  margin-top: 20px;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  
  &.secondary-actions {
    .secondary-btn {
      flex: 1;
    }
  }
  
  &.back-row {
    justify-content: center;
  }
}

.mount-action-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  
  &:hover {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
  }
  
  &.is-mounted {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    
    &:hover {
      background: linear-gradient(135deg, #16a34a, #15803d);
    }
  }
}

.tips-text {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 10px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.5;
  
  .tips-icon {
    font-size: 1rem;
    flex-shrink: 0;
  }
}

.detail-mode-content {
  width: 100%;
  margin-top: 20px;
}

.story-full-content {
  margin-bottom: 20px;
}

.detail-section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.story-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.8;
  padding: 16px;
  background: rgba(139, 92, 246, 0.03);
  border-radius: 10px;
  white-space: pre-line;
}

.match-details {
  margin-bottom: 20px;
}

.match-conditions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.match-condition-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(34, 197, 94, 0.05);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 8px;
  
  .check-icon {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(34, 197, 94, 0.2);
    border-radius: 50%;
    color: #22c55e;
    font-size: 0.8rem;
    font-weight: 600;
  }
  
  .condition-text {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.75);
  }
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 300px;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.error-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px;
}

.error-detail {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
