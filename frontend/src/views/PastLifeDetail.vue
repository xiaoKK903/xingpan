<template>
  <div class="past-life-detail-page">
    <div class="stars-bg">
      <div 
        v-for="i in 50" 
        :key="i" 
        class="star"
        :style="getStarStyle(i)"
      ></div>
    </div>

    <div class="page-header">
      <div class="header-back" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </div>
      <h1 class="page-title" v-if="!isSynastry">
        <span class="title-icon">{{ getThemeIcon(recordData?.theme) }}</span>
        {{ recordData?.theme_name || '前世故事详情' }}
      </h1>
      <h1 class="page-title" v-else>
        <span class="title-icon">{{ getRelationshipIcon(recordData?.relationship_type) }}</span>
        {{ recordData?.relationship_name || '合盘前世故事详情' }}
      </h1>
    </div>

    <div class="content-section">
      <div v-if="loading" class="loading-placeholder">
        <div class="loading-animation">
          <div class="loading-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          <p class="loading-text">加载中...</p>
        </div>
      </div>

      <div v-else-if="error" class="error-card">
        <div class="error-icon">⚠️</div>
        <h3 class="error-title">加载失败</h3>
        <p class="error-message">{{ errorMessage }}</p>
        <el-button type="primary" @click="loadDetail">
          重新加载
        </el-button>
      </div>

      <div v-else-if="!recordData" class="empty-placeholder">
        <div class="empty-icon">📜</div>
        <h3 class="empty-title">记录不存在</h3>
        <p class="empty-desc">该前世记录不存在或已被删除</p>
        <el-button type="primary" @click="goToRecords">
          查看我的记录
        </el-button>
      </div>

      <div v-else class="detail-card">
        <div class="detail-header">
          <div class="theme-info">
            <div class="theme-badge">
              <span class="theme-icon">{{ isSynastry ? getRelationshipIcon(recordData.relationship_type) : getThemeIcon(recordData.theme) }}</span>
              <span class="theme-name">{{ isSynastry ? recordData.relationship_name : recordData.theme_name }}</span>
            </div>
            <div class="badges">
              <el-tag v-if="recordData.is_deep" type="success" size="small">
                深度版
              </el-tag>
              <el-tag v-else type="info" size="small">
                精简版
              </el-tag>
            </div>
          </div>
        </div>

        <div v-if="!isSynastry" class="person-info-section">
          <div class="person-card">
            <div class="person-avatar">👤</div>
            <div class="person-details">
              <div class="person-name">{{ recordData.name || '未知' }}</div>
              <div class="person-meta">
                <span class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  {{ recordData.birth_date }}
                </span>
                <span class="meta-item" v-if="recordData.birth_place">
                  <el-icon><Location /></el-icon>
                  {{ recordData.birth_place }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="persons-info-section">
          <div class="person-card person-a">
            <div class="person-avatar">A</div>
            <div class="person-details">
              <div class="person-name">{{ recordData.person_a_name || '未知' }}</div>
              <div class="person-meta">
                <span class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  {{ recordData.person_a_birth_date || '-' }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="vs-divider">
            <span class="vs-text">✨</span>
          </div>
          
          <div class="person-card person-b">
            <div class="person-avatar">B</div>
            <div class="person-details">
              <div class="person-name">{{ recordData.person_b_name || '未知' }}</div>
              <div class="person-meta">
                <span class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  {{ recordData.person_b_birth_date || '-' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="theme-description-section" v-if="recordData.theme_description || recordData.relationship_description">
          <div class="section-header">
            <span class="section-icon">💫</span>
            <span class="section-title">{{ isSynastry ? '前世缘分' : '前世主题解读' }}</span>
          </div>
          <div class="description-content">
            <p>{{ isSynastry ? recordData.relationship_description : recordData.theme_description }}</p>
          </div>
        </div>

        <div class="story-section">
          <div class="section-header">
            <span class="section-icon">📖</span>
            <span class="section-title">前世故事</span>
          </div>
          
          <div class="story-content">
            <div class="story-content-inner" v-html="renderStoryContent(recordData.story)"></div>
          </div>
        </div>

        <div v-if="!recordData.is_deep" class="upgrade-section">
          <div class="upgrade-banner">
            <div class="upgrade-icon">👑</div>
            <div class="upgrade-info">
              <h3 class="upgrade-title">解锁深度版前世故事</h3>
              <p class="upgrade-desc">
                深度版包含更详细的前世经历描写、重要事件的完整脉络、前世与今生的关联分析
              </p>
            </div>
            <el-button 
              type="warning" 
              size="large"
              :loading="loadingOrders"
              @click="handleUpgrade"
              class="upgrade-btn"
            >
              <el-icon><Star /></el-icon>
              解锁深度版 (¥9.9)
            </el-button>
          </div>
        </div>

        <div class="detail-footer">
          <div class="footer-info">
            <div class="info-item">
              <el-icon><Clock /></el-icon>
              <span>生成时间：{{ formatDate(recordData.created_at) }}</span>
            </div>
            <div class="info-item" v-if="recordData.share_count">
              <el-icon><Share /></el-icon>
              <span>已分享 {{ recordData.share_count }} 次</span>
            </div>
          </div>
          
          <div class="footer-actions">
            <el-button 
              type="primary"
              @click="shareRecord"
              v-if="recordData.share_code"
            >
              <el-icon><Share /></el-icon>
              分享故事
            </el-button>
            <el-button 
              @click="goToRecords"
            >
              <el-icon><Document /></el-icon>
              我的记录
            </el-button>
            <el-button 
              @click="goToGenerate"
            >
              <el-icon><MagicStick /></el-icon>
              生成新故事
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="shareDialogVisible"
      title="分享你的前世故事"
      width="500px"
      center
    >
      <div class="share-content" v-if="recordData">
        <div class="share-info">
          <p class="share-label">分享链接</p>
          <div class="share-link">
            <el-input 
              :model-value="shareLink"
              readonly
            />
            <el-button type="primary" @click="copyShareLink">
              复制链接
            </el-button>
          </div>
        </div>
        
        <div class="share-info" v-if="recordData.share_code">
          <p class="share-label">分享码</p>
          <div class="share-code">{{ recordData.share_code }}</div>
        </div>

        <div class="share-hint">
          <p>将链接分享给好友，他们可以查看你的前世故事</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="upgradeDialogVisible"
      title="解锁深度版"
      width="400px"
      center
    >
      <div class="upgrade-content">
        <div class="upgrade-icon-large">👑</div>
        <h3 class="upgrade-title-large">解锁深度版前世故事</h3>
        <p class="upgrade-desc-large">
          深度版包含：<br/>
          • 更详细的前世经历描写<br/>
          • 重要事件的完整脉络<br/>
          • 前世与今生的关联分析
        </p>
        <div class="upgrade-price-large">
          <span class="price-symbol">¥</span>
          <span class="price-value">9.9</span>
        </div>
        <el-button 
          type="primary" 
          size="large"
          :loading="loadingOrders"
          @click="confirmUpgrade"
          class="upgrade-btn-large"
        >
          立即解锁
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Calendar, Location, Clock, Share, Document, MagicStick, Star } from '@element-plus/icons-vue'
import { usePastLifeAnalysis, getPastLifeStarStyle } from '@/composables/usePastLifeAnalysis'
import { pastLifeApi } from '@/api'

const router = useRouter()
const route = useRoute()

const {
  loadingOrders,
  isLoggedIn,
  createOrder,
  getThemeIcon,
  getRelationshipIcon
} = usePastLifeAnalysis()

const loading = ref(false)
const error = ref(false)
const errorMessage = ref('')
const recordData = ref(null)
const shareDialogVisible = ref(false)
const shareLink = ref('')
const upgradeDialogVisible = ref(false)

const isSynastry = computed(() => {
  return route.path.includes('/synastry/')
})

function getStarStyle(index) {
  return getPastLifeStarStyle(index)
}

function goBack() {
  router.back()
}

function goToRecords() {
  router.push('/past-life/records')
}

function goToGenerate() {
  router.push('/past-life')
}

async function loadDetail() {
  const recordId = route.params.id
  if (!recordId) {
    error.value = true
    errorMessage.value = '记录ID无效'
    return
  }

  loading.value = true
  error.value = false
  errorMessage.value = ''

  try {
    let result
    if (isSynastry.value) {
      result = await pastLifeApi.getSynastryRecordDetail(recordId)
    } else {
      result = await pastLifeApi.getSingleRecordDetail(recordId)
    }
    
    recordData.value = result
  } catch (err) {
    console.error('加载记录详情失败:', err)
    error.value = true
    errorMessage.value = err.message || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function shareRecord() {
  if (!recordData.value?.share_code) {
    ElMessage.warning('该故事暂不支持分享')
    return
  }
  
  const baseUrl = window.location.origin
  shareLink.value = `${baseUrl}/past-life/share/${recordData.value.share_code}`
  shareDialogVisible.value = true
}

function copyShareLink() {
  navigator.clipboard.writeText(shareLink.value).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

function handleUpgrade() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再解锁深度版')
    return
  }
  
  upgradeDialogVisible.value = true
}

async function confirmUpgrade() {
  if (!recordData.value) return
  
  const order = await createOrder(
    recordData.value.id, 
    isSynastry.value ? 'synastry' : 'single'
  )
  
  if (order) {
    ElMessage.success('订单创建成功！')
    upgradeDialogVisible.value = false
    
    ElMessage.info('正在刷新故事...')
    await loadDetail()
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function renderStoryContent(content) {
  if (!content) return ''
  
  let html = content
    .replace(/^# (.+)$/gm, '<h1 class="story-h1">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 class="story-h2">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="story-h3">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="story-strong">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="story-em">$1</em>')
    .replace(/^- (.+)$/gm, '<li class="story-li">$1</li>')
    .replace(/\n\n/g, '</p><p class="story-p">')
    .replace(/\n/g, '<br/>')
  
  return `<p class="story-p">${html}</p>`
}

onMounted(() => {
  loadDetail()
})

watch(
  () => route.params.id,
  () => {
    loadDetail()
  }
)
</script>

<style lang="scss" scoped>
.past-life-detail-page {
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
  position: relative;
}

.header-back {
  position: absolute;
  left: 0;
  top: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: color 0.3s;
  font-size: 14px;
  
  &:hover {
    color: #a78bfa;
  }
}

.page-title {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 28px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.content-section {
  max-width: 800px;
  margin: 0 auto;
}

.loading-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 100px 20px;
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
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
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
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.error-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 24px;
  padding: 60px 40px;
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 12px 0;
}

.error-message {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 24px 0;
  line-height: 1.6;
}

.empty-placeholder {
  text-align: center;
  padding: 100px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 12px 0;
}

.empty-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px 0;
}

.detail-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 24px;
  overflow: hidden;
}

.detail-header {
  padding: 24px 28px;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.08) 0%, transparent 100%);
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
}

.theme-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.theme-badge {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-icon {
  font-size: 32px;
}

.theme-name {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.person-info-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.persons-info-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}

.person-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(168, 85, 247, 0.05);
  padding: 16px 20px;
  border-radius: 16px;
  border: 1px solid rgba(168, 85, 247, 0.1);
}

.person-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  font-weight: 700;
}

.person-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.person-name {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.person-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.vs-divider {
  text-align: center;
  position: relative;
  padding: 0 12px;
}

.vs-text {
  font-size: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.theme-description-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.description-content {
  p {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.8;
    margin: 0;
    padding: 16px;
    background: rgba(168, 85, 247, 0.05);
    border-radius: 12px;
    border-left: 3px solid #f59e0b;
  }
}

.story-section {
  padding: 24px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.story-content {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 24px;
}

.story-content-inner {
  :deep(.story-h1) {
    font-size: 22px;
    font-weight: 800;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(168, 85, 247, 0.2);
  }
  
  :deep(.story-h2) {
    font-size: 18px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 24px 0 12px 0;
  }
  
  :deep(.story-h3) {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.8);
    margin: 16px 0 8px 0;
  }
  
  :deep(.story-p) {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.9;
    margin: 0 0 12px 0;
    text-indent: 2em;
  }
  
  :deep(.story-strong) {
    color: #f59e0b;
    font-weight: 700;
  }
  
  :deep(.story-em) {
    color: rgba(255, 255, 255, 0.85);
    font-style: italic;
  }
  
  :deep(.story-li) {
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
      color: #f59e0b;
    }
  }
}

.upgrade-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.upgrade-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 16px;
  flex-wrap: wrap;
}

.upgrade-icon {
  font-size: 40px;
}

.upgrade-info {
  flex: 1;
  min-width: 200px;
}

.upgrade-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 6px 0;
}

.upgrade-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  line-height: 1.6;
}

.upgrade-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  border: none;
  white-space: nowrap;
  
  &:hover {
    background: linear-gradient(135deg, #d97706 0%, #dc2626 100%);
  }
}

.detail-footer {
  padding: 24px 28px;
}

.footer-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
  flex-wrap: wrap;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.footer-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.share-content {
  text-align: center;
  
  .share-info {
    margin-bottom: 20px;
    
    .share-label {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin-bottom: 8px;
    }
    
    .share-link {
      display: flex;
      gap: 8px;
    }
    
    .share-code {
      font-size: 32px;
      font-weight: 800;
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 4px;
    }
  }
  
  .share-hint {
    p {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
  }
}

.upgrade-content {
  text-align: center;
  
  .upgrade-icon-large {
    font-size: 64px;
    margin-bottom: 16px;
  }
  
  .upgrade-title-large {
    font-size: 20px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 12px 0;
  }
  
  .upgrade-desc-large {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.8;
    margin: 0 0 20px 0;
  }
  
  .upgrade-price-large {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 4px;
    margin-bottom: 24px;
    
    .price-symbol {
      font-size: 18px;
      color: #f59e0b;
      font-weight: 600;
    }
    
    .price-value {
      font-size: 42px;
      font-weight: 800;
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
  
  .upgrade-btn-large {
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
    border: none;
    width: 100%;
    
    &:hover {
      background: linear-gradient(135deg, #d97706 0%, #dc2626 100%);
    }
  }
}

.page-title,
.theme-name,
.person-name,
.story-h1,
.story-h2,
.story-h3,
.empty-title,
.error-title {
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.empty-desc,
.error-message,
.description-content,
.story-p,
.loading-text {
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .past-life-detail-page {
    padding: 24px 16px;
  }
  
  .page-header {
    .header-back {
      position: relative;
      margin-bottom: 16px;
      justify-content: center;
    }
  }
  
  .page-title {
    font-size: 24px;
    flex-direction: column;
    gap: 8px;
  }
  
  .title-icon {
    font-size: 28px;
  }
  
  .theme-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .persons-info-section {
    flex-direction: column;
    gap: 16px;
  }
  
  .upgrade-banner {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .footer-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>
