<template>
  <div class="story-wall-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">📖</span>
          我的故事墙
        </h1>
        <p class="page-subtitle" v-if="!isVisitor">
          挂载的合盘故事卡将在这里展示，他人可以通过您的个人主页浏览
        </p>
        <p class="page-subtitle" v-else>
          {{ targetUserName || '用户' }}的故事墙
        </p>
      </div>
      
      <div class="header-actions" v-if="!isVisitor">
        <el-button type="primary" @click="handleGoToSynastry">
          <template #icon>
            <span>✨</span>
          </template>
          生成新故事卡
        </el-button>
      </div>
    </div>
    
    <div class="wall-stats" v-if="stats">
      <div class="stat-card">
        <span class="stat-value">{{ stats.total_mounted || 0 }}</span>
        <span class="stat-label">已挂载卡片</span>
      </div>
      <div class="stat-card rarity-legendary" v-if="stats.rarity_distribution?.legendary > 0">
        <span class="stat-icon">👑</span>
        <span class="stat-value">{{ stats.rarity_distribution.legendary }}</span>
        <span class="stat-label">传说卡</span>
      </div>
      <div class="stat-card rarity-epic" v-if="stats.rarity_distribution?.epic > 0">
        <span class="stat-icon">🌟</span>
        <span class="stat-value">{{ stats.rarity_distribution.epic }}</span>
        <span class="stat-label">史诗卡</span>
      </div>
      <div class="stat-card rarity-rare" v-if="stats.rarity_distribution?.rare > 0">
        <span class="stat-icon">💎</span>
        <span class="stat-value">{{ stats.rarity_distribution.rare }}</span>
        <span class="stat-label">稀有卡</span>
      </div>
    </div>
    
    <div class="content-section">
      <div class="section-tabs" v-if="!isVisitor">
        <el-radio-group v-model="activeTab" size="large">
          <el-radio-button value="mounted">
            <span class="tab-icon">📌</span>
            已挂载 ({{ mountedCards.length }})
          </el-radio-button>
          <el-radio-button value="all">
            <span class="tab-icon">🎴</span>
            全部卡片 ({{ allCards.length }})
          </el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="loading-state" v-if="isLoading">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">加载中...</p>
      </div>
      
      <div class="empty-state" v-else-if="displayCards.length === 0">
        <div class="empty-icon">
          <span v-if="activeTab === 'mounted'">📌</span>
          <span v-else>🎴</span>
        </div>
        <h3 class="empty-title">
          {{ activeTab === 'mounted' ? '暂无已挂载的故事卡' : '暂无故事卡' }}
        </h3>
        <p class="empty-description">
          {{ activeTab === 'mounted' 
            ? '去合盘页面生成故事卡，然后挂载到故事墙吧！' 
            : '去合盘页面与他人合盘，生成专属故事卡！' 
          }}
        </p>
        <el-button 
          type="primary" 
          size="large"
          @click="handleGoToSynastry"
          v-if="!isVisitor"
        >
          去合盘
        </el-button>
      </div>
      
      <div class="cards-grid" v-else>
        <div 
          v-for="card in displayCards" 
          :key="card.id"
          class="card-item"
        >
          <StoryCard
            :card-data="card"
            :show-actions="!isVisitor"
            :show-meta="true"
            @mount="handleCardMounted"
            @share="handleCardShared"
            @view-detail="handleViewCardDetail"
          />
        </div>
      </div>
      
      <div class="pagination-wrapper" v-if="!isVisitor && totalCards > 0 && totalCards > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalCards"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
    
    <el-dialog
      v-model="showDetailModal"
      width="520px"
      title="故事卡详情"
      :close-on-click-modal="true"
      custom-class="story-card-detail-modal"
    >
      <div class="detail-content" v-if="selectedCard">
        <div class="detail-card-wrapper">
          <StoryCard
            :card-data="selectedCard"
            :show-actions="false"
            :show-meta="true"
          />
        </div>
        
        <div class="detail-story-section" v-if="selectedCard.story_content">
          <h4 class="detail-section-title">完整故事</h4>
          <div class="detail-story-text">
            {{ selectedCard.story_content }}
          </div>
        </div>
        
        <div class="detail-meta-section" v-if="selectedCard.metadata?.matched_conditions?.length">
          <h4 class="detail-section-title">匹配条件</h4>
          <div class="detail-meta-list">
            <div 
              v-for="(condition, index) in selectedCard.metadata.matched_conditions" 
              :key="index"
              class="meta-condition-item"
            >
              <span class="check-icon">✓</span>
              <span class="condition-text">{{ condition }}</span>
            </div>
          </div>
        </div>
        
        <div class="detail-info-section">
          <div class="info-row">
            <span class="info-label">创建时间</span>
            <span class="info-value">{{ formatDate(selectedCard.created_at) }}</span>
          </div>
          <div class="info-row" v-if="selectedCard.mounted_at">
            <span class="info-label">挂载时间</span>
            <span class="info-value">{{ formatDate(selectedCard.mounted_at) }}</span>
          </div>
          <div class="info-row" v-if="selectedCard.share_count > 0">
            <span class="info-label">分享次数</span>
            <span class="info-value">{{ selectedCard.share_count }} 次</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="detail-footer">
          <el-button @click="showDetailModal = false">关闭</el-button>
          <el-button 
            v-if="!isVisitor"
            type="danger"
            :loading="isDeleting"
            @click="handleDeleteCard"
          >
            删除卡片
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import StoryCard from '@/components/synastry/StoryCard.vue'
import { storyCardApi } from '@/api'

const router = useRouter()
const route = useRoute()

const isLoading = ref(true)
const isDeleting = ref(false)
const activeTab = ref('mounted')
const showDetailModal = ref(false)
const selectedCard = ref(null)

const allCards = ref([])
const mountedCards = ref([])
const stats = ref(null)

const currentPage = ref(1)
const pageSize = ref(12)
const totalCards = ref(0)

const isVisitor = computed(() => {
  return !!route.params.userId
})

const targetUserId = computed(() => {
  return route.params.userId ? parseInt(route.params.userId) : null
})

const targetUserName = computed(() => {
  return route.query.name || ''
})

const displayCards = computed(() => {
  if (activeTab.value === 'mounted' || isVisitor.value) {
    return mountedCards.value
  }
  return allCards.value
})

onMounted(() => {
  loadData()
})

watch(() => route.params.userId, () => {
  loadData()
})

async function loadData() {
  isLoading.value = true
  
  try {
    if (isVisitor.value) {
      const result = await storyCardApi.getUserStoryWall(targetUserId.value)
      mountedCards.value = result.cards || []
      stats.value = result.stats
    } else {
      const [wallResult, cardsResult] = await Promise.all([
        storyCardApi.getMyStoryWall(),
        storyCardApi.getMyCards({ 
          page: currentPage.value, 
          page_size: pageSize.value 
        })
      ])
      
      mountedCards.value = wallResult.cards || []
      stats.value = wallResult.stats
      allCards.value = cardsResult.items || []
      totalCards.value = cardsResult.total || cardsResult.count || allCards.value.length
    }
  } catch (error) {
    console.error('加载故事墙失败:', error)
    ElMessage.error('加载失败，请稍后重试')
  } finally {
    isLoading.value = false
  }
}

function handleGoToSynastry() {
  router.push('/synastry')
}

function handleCardMounted(card) {
  const index = allCards.value.findIndex(c => c.id === card.id)
  if (index > -1) {
    allCards.value[index] = { ...card }
  }
  
  if (card.is_mounted) {
    const mountedIndex = mountedCards.value.findIndex(c => c.id === card.id)
    if (mountedIndex === -1) {
      mountedCards.value.unshift({ ...card })
    } else {
      mountedCards.value[mountedIndex] = { ...card }
    }
  } else {
    const mountedIndex = mountedCards.value.findIndex(c => c.id === card.id)
    if (mountedIndex > -1) {
      mountedCards.value.splice(mountedIndex, 1)
    }
  }
  
  if (selectedCard.value?.id === card.id) {
    selectedCard.value = { ...card }
  }
}

function handleCardShared(card) {
  const index = allCards.value.findIndex(c => c.id === card.id)
  if (index > -1) {
    allCards.value[index] = { ...card }
  }
  
  const mountedIndex = mountedCards.value.findIndex(c => c.id === card.id)
  if (mountedIndex > -1) {
    mountedCards.value[mountedIndex] = { ...card }
  }
}

function handleViewCardDetail(card) {
  selectedCard.value = { ...card }
  showDetailModal.value = true
}

async function handleDeleteCard() {
  const cardId = selectedCard.value?.id
  if (!cardId) return
  
  try {
    await ElMessageBox.confirm(
      '确定要删除这张故事卡吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    isDeleting.value = true
    
    await storyCardApi.delete(cardId)
    
    ElMessage.success('删除成功')
    
    allCards.value = allCards.value.filter(c => c.id !== cardId)
    mountedCards.value = mountedCards.value.filter(c => c.id !== cardId)
    
    showDetailModal.value = false
    selectedCard.value = null
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试')
    }
  } finally {
    isDeleting.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadData()
}

function handlePageSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}
</script>

<style lang="scss" scoped>
.story-wall-page {
  min-height: 100vh;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 24px;
}

.header-content {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.8rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px;
  
  .title-icon {
    font-size: 2rem;
  }
}

.page-subtitle {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.header-actions {
  flex-shrink: 0;
}

.wall-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(20, 20, 50, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
    transform: translateY(-2px);
  }
  
  &.rarity-legendary {
    border-color: rgba(245, 158, 11, 0.4);
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(20, 20, 50, 0.6));
  }
  
  &.rarity-epic {
    border-color: rgba(168, 85, 247, 0.4);
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(20, 20, 50, 0.6));
  }
  
  &.rarity-rare {
    border-color: rgba(59, 130, 246, 0.4);
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(20, 20, 50, 0.6));
  }
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.stat-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.content-section {
  background: rgba(12, 12, 28, 0.6);
  border-radius: 20px;
  border: 1px solid rgba(80, 60, 160, 0.15);
  padding: 24px;
}

.section-tabs {
  margin-bottom: 24px;
  
  :deep(.el-radio-group) {
    .el-radio-button__inner {
      background: rgba(139, 92, 246, 0.05);
      border-color: rgba(139, 92, 246, 0.2);
      color: rgba(255, 255, 255, 0.6);
      
      &:hover {
        color: rgba(255, 255, 255, 0.8);
      }
    }
    
    .el-radio-button__original-radio:checked + .el-radio-button__inner {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.3));
      border-color: rgba(139, 92, 246, 0.5);
      color: rgba(255, 255, 255, 0.9);
    }
  }
}

.tab-icon {
  margin-right: 6px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 12px;
}

.empty-description {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 24px;
  max-width: 400px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  justify-items: center;
}

.card-item {
  width: 100%;
  max-width: 400px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
  margin-bottom: 16px;
  
  .spinner-ring {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 4px solid rgba(139, 92, 246, 0.1);
    border-top-color: rgba(139, 92, 246, 0.8);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

:deep(.story-card-detail-modal) {
  .el-dialog__body {
    padding: 20px 24px;
  }
}

.detail-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.detail-card-wrapper {
  margin-bottom: 24px;
}

.detail-story-section,
.detail-meta-section,
.detail-info-section {
  width: 100%;
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

.detail-story-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.8;
  padding: 16px;
  background: rgba(139, 92, 246, 0.03);
  border-radius: 10px;
  white-space: pre-line;
}

.detail-meta-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-condition-item {
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

.detail-info-section {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  
  &:not(:last-child) {
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  }
}

.info-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  
  :deep(.el-pagination) {
    .el-pagination__total,
    .el-pagination__jump,
    .el-pagination__sizes {
      color: rgba(255, 255, 255, 0.6);
    }
    
    .btn-prev,
    .btn-next {
      background: rgba(139, 92, 246, 0.1);
      border: 1px solid rgba(139, 92, 246, 0.2);
      color: rgba(255, 255, 255, 0.7);
      
      &:hover:not(:disabled) {
        color: #fff;
        border-color: rgba(139, 92, 246, 0.5);
      }
      
      &:disabled {
        color: rgba(255, 255, 255, 0.3);
      }
    }
    
    .el-pager li {
      background: rgba(139, 92, 246, 0.1);
      border: 1px solid rgba(139, 92, 246, 0.2);
      color: rgba(255, 255, 255, 0.7);
      
      &:hover {
        color: #fff;
        border-color: rgba(139, 92, 246, 0.5);
      }
      
      &.active {
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        border-color: #8b5cf6;
        color: #fff;
      }
    }
    
    .el-select {
      .el-input__wrapper {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: none;
        
        .el-input__inner {
          color: rgba(255, 255, 255, 0.7);
        }
      }
    }
  }
}
</style>
