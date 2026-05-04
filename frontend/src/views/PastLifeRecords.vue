<template>
  <template v-if="isLoggedIn">
    <div class="past-life-records-page">
      <div class="stars-bg">
        <div 
          v-for="i in 40" 
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
        <h1 class="page-title">
          <span class="title-icon">📜</span>
          我的前世记录
        </h1>
        <p class="page-description">
          查看你所有的前世故事记录
        </p>
      </div>

      <div class="tab-section">
        <el-tabs v-model="activeTab" class="main-tabs" @tab-change="handleTabChange">
          <el-tab-pane label="单人前世" name="single">
            <div class="records-section">
              <template v-if="loadingSingleRecords">
                <div class="loading-placeholder">
                  <div class="loading-animation">
                    <div class="loading-dots">
                      <span class="dot"></span>
                      <span class="dot"></span>
                      <span class="dot"></span>
                    </div>
                    <p class="loading-text">加载中...</p>
                  </div>
                </div>
              </template>

              <template v-else-if="myRecords.length === 0">
                <div class="empty-placeholder">
                  <div class="empty-icon">🌙</div>
                  <h3 class="empty-title">暂无前世记录</h3>
                  <p class="empty-desc">还没有生成过前世故事，快去探索你的前世吧！</p>
                  <el-button type="primary" @click="goToGenerate">
                    生成前世故事
                  </el-button>
                </div>
              </template>

              <template v-else>
                <div class="records-grid">
                  <div 
                    v-for="record in myRecords" 
                    :key="record.id" 
                    class="record-card"
                    @click="viewDetail(record, false)"
                  >
                    <div class="record-header">
                      <div class="theme-badge">
                        <span class="theme-icon">{{ getThemeIcon(record.theme) }}</span>
                        <span class="theme-name">{{ record.theme_name || record.theme }}</span>
                      </div>
                      <div class="badges">
                        <el-tag v-if="record.is_deep" type="success" size="small">深度版</el-tag>
                        <el-tag v-else type="info" size="small">精简版</el-tag>
                      </div>
                    </div>

                    <div class="record-info">
                      <div class="info-item" v-if="record.name">
                        <span class="info-label">姓名</span>
                        <span class="info-value">{{ record.name }}</span>
                      </div>
                      <div class="info-item">
                        <span class="info-label">出生日期</span>
                        <span class="info-value">{{ record.birth_date }}</span>
                      </div>
                    </div>

                    <div class="record-preview">
                      <p>{{ record.story_preview || record.story }}</p>
                    </div>

                    <div class="record-footer">
                      <div class="record-date">
                        <el-icon><Clock /></el-icon>
                        <span>{{ formatDate(record.created_at) }}</span>
                      </div>
                      <div class="record-stats" v-if="record.share_count">
                        <el-icon><Share /></el-icon>
                        <span>{{ record.share_count }} 分享</span>
                      </div>
                    </div>

                    <div class="record-actions" @click.stop>
                      <el-button type="primary" size="small" @click="viewDetail(record, false)">
                        查看详情
                      </el-button>
                      <el-button 
                        v-if="!record.is_deep"
                        type="warning" 
                        size="small"
                        @click="handleUpgrade(record.id, 'single')"
                      >
                        解锁深度版
                      </el-button>
                      <el-button 
                        v-if="record.share_code"
                        size="small"
                        @click="shareRecord(record)"
                      >
                        分享
                      </el-button>
                    </div>
                  </div>
                </div>

                <div v-if="totalRecords > singlePageSize" class="pagination-section">
                  <el-pagination
                    v-model:current-page="singlePage"
                    :page-size="singlePageSize"
                    :total="totalRecords"
                    :page-sizes="[20, 50, 100]"
                    layout="prev, pager, next, jumper, total"
                    @current-change="handleSinglePageChange"
                    @size-change="handleSingleSizeChange"
                  />
                </div>
              </template>
            </div>
          </el-tab-pane>

          <el-tab-pane label="双人前世合盘" name="synastry">
            <div class="records-section">
              <template v-if="loadingSynastryRecords">
                <div class="loading-placeholder">
                  <div class="loading-animation">
                    <div class="loading-dots">
                      <span class="dot"></span>
                      <span class="dot"></span>
                      <span class="dot"></span>
                    </div>
                    <p class="loading-text">加载中...</p>
                  </div>
                </div>
              </template>

              <template v-else-if="mySynastryRecords.length === 0">
                <div class="empty-placeholder">
                  <div class="empty-icon">👥</div>
                  <h3 class="empty-title">暂无合盘前世记录</h3>
                  <p class="empty-desc">还没有生成过合盘前世故事，快去探索你与TA的前世缘分吧！</p>
                  <el-button type="primary" @click="goToGenerate">
                    生成合盘前世故事
                  </el-button>
                </div>
              </template>

              <template v-else>
                <div class="records-grid">
                  <div 
                    v-for="record in mySynastryRecords" 
                    :key="record.id" 
                    class="record-card synastry-card"
                    @click="viewDetail(record, true)"
                  >
                    <div class="record-header">
                      <div class="theme-badge">
                        <span class="theme-icon">{{ getRelationshipIcon(record.relationship_type) }}</span>
                        <span class="theme-name">{{ record.relationship_name || record.relationship_type }}</span>
                      </div>
                      <div class="badges">
                        <el-tag v-if="record.is_deep" type="success" size="small">深度版</el-tag>
                        <el-tag v-else type="info" size="small">精简版</el-tag>
                      </div>
                    </div>

                    <div class="persons-info">
                      <div class="person-info">
                        <span class="person-label">A</span>
                        <span class="person-name">{{ record.person_a_name || '未知' }}</span>
                        <span class="person-birth">{{ record.person_a_birth_date || '' }}</span>
                      </div>
                      <div class="person-connector">✨</div>
                      <div class="person-info">
                        <span class="person-label">B</span>
                        <span class="person-name">{{ record.person_b_name || '未知' }}</span>
                        <span class="person-birth">{{ record.person_b_birth_date || '' }}</span>
                      </div>
                    </div>

                    <div class="record-preview">
                      <p>{{ record.story_preview || record.story }}</p>
                    </div>

                    <div class="record-footer">
                      <div class="record-date">
                        <el-icon><Clock /></el-icon>
                        <span>{{ formatDate(record.created_at) }}</span>
                      </div>
                      <div class="record-stats" v-if="record.share_count">
                        <el-icon><Share /></el-icon>
                        <span>{{ record.share_count }} 分享</span>
                      </div>
                    </div>

                    <div class="record-actions" @click.stop>
                      <el-button type="primary" size="small" @click="viewDetail(record, true)">
                        查看详情
                      </el-button>
                      <el-button 
                        v-if="!record.is_deep"
                        type="warning" 
                        size="small"
                        @click="handleUpgrade(record.id, 'synastry')"
                      >
                        解锁深度版
                      </el-button>
                      <el-button 
                        v-if="record.share_code"
                        size="small"
                        @click="shareRecord(record)"
                      >
                        分享
                      </el-button>
                    </div>
                  </div>
                </div>

                <div v-if="totalSynastryRecords > synastryPageSize" class="pagination-section">
                  <el-pagination
                    v-model:current-page="synastryPage"
                    :page-size="synastryPageSize"
                    :total="totalSynastryRecords"
                    :page-sizes="[20, 50, 100]"
                    layout="prev, pager, next, jumper, total"
                    @current-change="handleSynastryPageChange"
                    @size-change="handleSynastrySizeChange"
                  />
                </div>
              </template>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <el-dialog
        v-model="shareDialogVisible"
        title="分享你的前世故事"
        width="500px"
        center
      >
        <div class="share-content" v-if="currentShareRecord">
          <div class="share-info">
            <p class="share-label">分享链接</p>
            <div class="share-link">
              <el-input :model-value="shareLink" readonly />
              <el-button type="primary" @click="copyShareLink">复制链接</el-button>
            </div>
          </div>
          <div class="share-info" v-if="currentShareRecord.share_code">
            <p class="share-label">分享码</p>
            <div class="share-code">{{ currentShareRecord.share_code }}</div>
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
          <div class="upgrade-icon">👑</div>
          <h3 class="upgrade-title">解锁深度版前世故事</h3>
          <p class="upgrade-desc">
            深度版包含：<br/>
            • 更详细的前世经历描写<br/>
            • 重要事件的完整脉络<br/>
            • 前世与今生的关联分析
          </p>
          <div class="upgrade-price">
            <span class="price-symbol">¥</span>
            <span class="price-value">9.9</span>
          </div>
          <el-button 
            type="primary" 
            size="large"
            :loading="loadingOrders"
            @click="confirmUpgrade"
            class="upgrade-btn"
          >
            立即解锁
          </el-button>
        </div>
      </el-dialog>
    </div>
  </template>

  <template v-else>
    <div class="not-logged-page">
      <div class="stars-bg">
        <div 
          v-for="i in 20" 
          :key="i" 
          class="star"
          :style="getStarStyle(i)"
        ></div>
      </div>
      <div class="not-logged-content">
        <div class="not-logged-icon">🔒</div>
        <h2 class="not-logged-title">请先登录</h2>
        <p class="not-logged-desc">登录后即可查看你的前世故事记录</p>
        <el-button type="primary" size="large" @click="goToLogin">
          立即登录
        </el-button>
      </div>
    </div>
  </template>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Clock, Share } from '@element-plus/icons-vue'
import { usePastLifeAnalysis, getPastLifeStarStyle } from '@/composables/usePastLifeAnalysis'

const router = useRouter()

const {
  loadingOrders,
  loadingSingleRecords,
  loadingSynastryRecords,
  errorSingleRecords,
  errorSynastryRecords,
  hasLoadedSingleRecords,
  hasLoadedSynastryRecords,
  activeTab,
  myRecords,
  mySynastryRecords,
  totalRecords,
  totalSynastryRecords,
  singlePage,
  singlePageSize,
  synastryPage,
  synastryPageSize,
  isLoggedIn,
  loadMyRecords,
  loadMySynastryRecords,
  createOrder,
  getThemeIcon,
  getRelationshipIcon
} = usePastLifeAnalysis()

const shareDialogVisible = ref(false)
const currentShareRecord = ref(null)
const shareLink = ref('')

const upgradeDialogVisible = ref(false)
const currentUpgradeRecordId = ref(null)
const currentUpgradeType = ref('single')

function getStarStyle(index) {
  return getPastLifeStarStyle(index)
}

function goBack() {
  router.back()
}

function goToGenerate() {
  router.push('/past-life')
}

function goToLogin() {
  router.push('/login?redirect=/past-life/records')
}

function viewDetail(record, isSynastry) {
  if (isSynastry) {
    router.push(`/past-life/synastry/detail/${record.id}`)
  } else {
    router.push(`/past-life/detail/${record.id}`)
  }
}

function shareRecord(record) {
  if (!record.share_code) {
    ElMessage.warning('该记录暂不支持分享')
    return
  }
  currentShareRecord.value = record
  const baseUrl = window.location.origin
  shareLink.value = `${baseUrl}/past-life/share/${record.share_code}`
  shareDialogVisible.value = true
}

function copyShareLink() {
  navigator.clipboard.writeText(shareLink.value).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

function handleUpgrade(recordId, recordType) {
  currentUpgradeRecordId.value = recordId
  currentUpgradeType.value = recordType
  upgradeDialogVisible.value = true
}

async function confirmUpgrade() {
  if (!currentUpgradeRecordId.value) return
  const order = await createOrder(currentUpgradeRecordId.value, currentUpgradeType.value)
  if (order) {
    ElMessage.success('订单创建成功！')
    upgradeDialogVisible.value = false
    ElMessage.info('正在刷新记录...')
    if (currentUpgradeType.value === 'synastry') {
      await loadSynastryRecordsInternal(synastryPage.value)
    } else {
      await loadSingleRecordsInternal(singlePage.value)
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

async function loadSingleRecordsInternal(page, forceReload = false) {
  await loadMyRecords(page, singlePageSize.value, forceReload)
}

async function loadSynastryRecordsInternal(page, forceReload = false) {
  await loadMySynastryRecords(page, synastryPageSize.value, forceReload)
}

function handleTabChange(tabName) {
  if (tabName === 'single') {
    if (!hasLoadedSingleRecords.value || errorSingleRecords.value) {
      loadSingleRecordsInternal(singlePage.value, true)
    }
  } else if (tabName === 'synastry') {
    if (!hasLoadedSynastryRecords.value || errorSynastryRecords.value) {
      loadSynastryRecordsInternal(synastryPage.value, true)
    }
  }
}

function handleSinglePageChange(page) {
  singlePage.value = page
  loadSingleRecordsInternal(page, true)
}

function handleSingleSizeChange(size) {
  singlePageSize.value = size
  singlePage.value = 1
  loadSingleRecordsInternal(1, true)
}

function handleSynastryPageChange(page) {
  synastryPage.value = page
  loadSynastryRecordsInternal(page, true)
}

function handleSynastrySizeChange(size) {
  synastryPageSize.value = size
  synastryPage.value = 1
  loadSynastryRecordsInternal(1, true)
}

if (isLoggedIn.value) {
  loadSingleRecordsInternal(1, true)
}
</script>

<style lang="scss" scoped>
.past-life-records-page,
.not-logged-page {
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

.not-logged-content {
  text-align: center;
  padding: 120px 20px;
}

.not-logged-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.not-logged-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 12px 0;
}

.not-logged-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px 0;
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
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #a855f7 100%);
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
  font-size: 32px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.page-description {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.6);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.tab-section {
  max-width: 1200px;
  margin: 0 auto;
}

.main-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    background: rgba(168, 85, 247, 0.2);
  }
  
  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.5);
    font-size: 16px;
    font-weight: 600;
    
    &.is-active {
      color: #f59e0b;
    }
    
    &:hover {
      color: rgba(245, 158, 11, 0.8);
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background: linear-gradient(90deg, #f59e0b, #ef4444);
  }
}

.records-section {
  margin-top: 24px;
}

.loading-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 20px;
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

.empty-placeholder {
  text-align: center;
  padding: 80px 20px;
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

.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.record-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 20px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    border-color: rgba(245, 158, 11, 0.4);
    box-shadow: 0 12px 40px rgba(245, 158, 11, 0.15);
  }
}

.synastry-card {
  border-color: rgba(245, 158, 11, 0.2);
  
  &:hover {
    border-color: rgba(244, 114, 182, 0.4);
    box-shadow: 0 12px 40px rgba(244, 114, 182, 0.15);
  }
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.08) 0%, transparent 100%);
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
  flex-wrap: wrap;
  gap: 8px;
}

.theme-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.theme-icon {
  font-size: 24px;
}

.theme-name {
  font-size: 15px;
  font-weight: 700;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.record-info {
  padding: 12px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.info-value {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.persons-info {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
  flex-wrap: wrap;
}

.person-info {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(168, 85, 247, 0.1);
  padding: 8px 12px;
  border-radius: 12px;
}

.person-label {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: white;
}

.person-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.person-birth {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.person-connector {
  font-size: 20px;
}

.record-preview {
  padding: 16px 20px;
  
  p {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.6;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.record-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-top: 1px solid rgba(168, 85, 247, 0.05);
}

.record-date,
.record-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.record-actions {
  display: flex;
  gap: 8px;
  padding: 12px 20px 20px;
  flex-wrap: wrap;
}

.pagination-section {
  display: flex;
  justify-content: center;
  padding: 32px 0;
  
  :deep(.el-pagination) {
    .el-pagination__total,
    .el-pagination__jump,
    .el-pagination__editor {
      color: rgba(255, 255, 255, 0.6);
    }
    
    .el-pager li {
      background: rgba(255, 255, 255, 0.05);
      border: none;
      color: rgba(255, 255, 255, 0.6);
      
      &.active {
        background: linear-gradient(135deg, #f59e0b, #ef4444);
        color: white;
      }
      
      &:hover:not(.active) {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
      }
    }
    
    .btn-prev,
    .btn-next {
      background: rgba(255, 255, 255, 0.05);
      border: none;
      color: rgba(255, 255, 255, 0.6);
      
      &:hover {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
      }
      
      &.disabled {
        background: rgba(255, 255, 255, 0.02);
        color: rgba(255, 255, 255, 0.2);
      }
    }
  }
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
  
  .upgrade-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }
  
  .upgrade-title {
    font-size: 20px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 12px 0;
  }
  
  .upgrade-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.8;
    margin: 0 0 20px 0;
  }
  
  .upgrade-price {
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
  
  .upgrade-btn {
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
.empty-title,
.upgrade-title,
.not-logged-title {
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.page-description,
.empty-desc,
.record-preview,
.loading-text,
.upgrade-desc,
.not-logged-desc {
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .past-life-records-page,
  .not-logged-page {
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
  
  .records-grid {
    grid-template-columns: 1fr;
  }
  
  .record-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
  
  .persons-info {
    flex-direction: column;
  }
}
</style>
