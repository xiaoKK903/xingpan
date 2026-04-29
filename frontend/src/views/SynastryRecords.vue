<template>
  <div class="records-container">
    <div class="stars-bg">
      <div v-for="i in 40" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="records-main">
      <div class="records-header">
        <div class="header-back" @click="goBack">
          <el-icon size="20"><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">
          <h1 class="main-title">我的合盘记录</h1>
          <p class="subtitle">查看和管理您保存的合盘分析</p>
        </div>
        <router-link to="/synastry">
          <el-button type="primary" class="new-btn">
            <el-icon><Plus /></el-icon>
            <span>新建分析</span>
          </el-button>
        </router-link>
      </div>

      <div class="records-content">
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p class="loading-text">加载中...</p>
        </div>

        <div v-else-if="!loading && records.length === 0" class="empty-container">
          <div class="empty-icon">
            <el-icon size="64"><Document /></el-icon>
          </div>
          <h3 class="empty-title">暂无合盘记录</h3>
          <p class="empty-desc">保存您的合盘分析后，可以在这里查看和管理</p>
          <router-link to="/synastry">
            <el-button type="primary" size="large">
              <el-icon><MagicStick /></el-icon>
              开始分析
            </el-button>
          </router-link>
        </div>

        <div v-else class="records-list">
          <div 
            v-for="record in records" 
            :key="record.id"
            class="record-card"
            @click="viewRecord(record.id)"
          >
            <div class="record-basic">
              <div class="persons-info">
                <div class="person">
                  <div class="person-avatar" :style="{ background: 'linear-gradient(135deg, #ff8c32, #f97316)' }">
                    <span class="avatar-letter">{{ record.person_a_name?.[0] || 'A' }}</span>
                  </div>
                  <div class="person-details">
                    <div class="person-name">{{ record.person_a_name || '人物A' }}</div>
                    <div class="person-date">{{ record.person_a_birth_date }}</div>
                  </div>
                </div>
                
                <div class="connect-icon">
                  <el-icon size="20" color="#8b5cf6"><Link /></el-icon>
                </div>
                
                <div class="person">
                  <div class="person-avatar" :style="{ background: 'linear-gradient(135deg, #50c8ff, #3b82f6)' }">
                    <span class="avatar-letter">{{ record.person_b_name?.[0] || 'B' }}</span>
                  </div>
                  <div class="person-details">
                    <div class="person-name">{{ record.person_b_name || '人物B' }}</div>
                    <div class="person-date">{{ record.person_b_birth_date }}</div>
                  </div>
                </div>
              </div>
              
              <div class="record-score" :style="{ color: getScoreColor(record.total_score) }">
                <div class="score-circle">
                  <span class="score-value">{{ record.total_score || 60 }}</span>
                  <span class="score-unit">分</span>
                </div>
                <div class="score-level" v-if="record.score_level?.level">
                  {{ record.score_level.level }}
                </div>
              </div>
            </div>
            
            <div class="record-footer">
              <div class="record-info">
                <div class="record-name" v-if="record.name">
                  <el-icon size="12"><Folder /></el-icon>
                  <span>{{ record.name }}</span>
                </div>
                <div class="record-date">
                  <el-icon size="12"><Clock /></el-icon>
                  <span>{{ formatDate(record.created_at) }}</span>
                </div>
              </div>
              
              <div class="record-actions" @click.stop>
                <el-button 
                  type="primary" 
                  size="small" 
                  :icon="Share"
                  @click="shareRecord(record)"
                  :disabled="sharingId === record.id"
                >
                  {{ sharingId === record.id ? '生成中...' : '分享' }}
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  :icon="Delete"
                  @click="confirmDelete(record)"
                  :disabled="deletingId === record.id"
                >
                  {{ deletingId === record.id ? '删除中...' : '删除' }}
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!loading && records.length > 0 && total > pageSize" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="loadRecords"
          />
        </div>
      </div>

      <el-dialog
        v-model="showShareDialog"
        title="分享合盘报告"
        width="420px"
        center
      >
        <div class="share-dialog-content">
          <p class="share-tip">复制以下链接分享给好友，对方即可查看这份合盘分析报告：</p>
          <div class="share-link-wrapper">
            <el-input v-model="shareLink" readonly class="link-input" />
            <el-button type="primary" @click="copyShareLink" class="copy-btn">
              {{ copied ? '已复制' : '复制链接' }}
            </el-button>
          </div>
          <div class="share-settings">
            <div class="setting-item">
              <span class="setting-label">公开访问</span>
              <el-switch 
                v-model="sharePublic" 
                @change="togglePublic"
              />
            </div>
            <p class="setting-note" v-if="sharePublic">
              <el-icon><InfoFilled /></el-icon>
              开启后，任何人都可以通过此链接访问报告
            </p>
            <p class="setting-note" v-else>
              <el-icon><InfoFilled /></el-icon>
              关闭后，只有您可以查看此报告
            </p>
          </div>
        </div>
        <template #footer>
          <el-button @click="showShareDialog = false">关闭</el-button>
        </template>
      </el-dialog>

      <el-dialog
        v-model="showDeleteConfirm"
        title="确认删除"
        width="360px"
        center
      >
        <div class="delete-confirm-content">
          <el-icon size="48" color="#ef4444"><WarningFilled /></el-icon>
          <p class="confirm-text">确定要删除这份合盘记录吗？</p>
          <p class="confirm-note">删除后无法恢复</p>
        </div>
        <template #footer>
          <el-button @click="showDeleteConfirm = false">取消</el-button>
          <el-button type="danger" @click="executeDelete">确认删除</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Plus, Document, MagicStick, Link,
  Share, Delete, Folder, Clock, InfoFilled, WarningFilled
} from '@element-plus/icons-vue'
import { synastryApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const sharingId = ref(null)
const deletingId = ref(null)
const showShareDialog = ref(false)
const showDeleteConfirm = ref(false)
const currentShareRecord = ref(null)
const shareLink = ref('')
const sharePublic = ref(false)
const copied = ref(false)

const isLoggedIn = computed(() => userStore.isLoggedIn)

function getStarStyle(index) {
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

function getScoreColor(score) {
  if (!score) return '#8b5cf6'
  if (score >= 85) return '#22c55e'
  if (score >= 70) return '#eab308'
  if (score >= 55) return '#f97316'
  return '#ef4444'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goBack() {
  router.back()
}

function viewRecord(recordId) {
  router.push(`/synastry/${recordId}`)
}

async function loadRecords() {
  loading.value = true
  
  try {
    const result = await synastryApi.getList({
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    records.value = result?.records || []
    total.value = result?.total || 0
  } catch (error) {
    console.error('加载合盘记录失败:', error)
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function shareRecord(record) {
  sharingId.value = record.id
  
  try {
    const result = await synastryApi.generateShare(record.id)
    
    const baseUrl = window.location.origin
    shareLink.value = `${baseUrl}/synastry/share/${result.share_code}`
    currentShareRecord.value = record
    sharePublic.value = record.is_public
    showShareDialog.value = true
    
  } catch (error) {
    console.error('生成分享链接失败:', error)
    ElMessage.error(error.message || '生成分享链接失败')
  } finally {
    sharingId.value = null
  }
}

async function togglePublic(isPublic) {
  if (!currentShareRecord.value) return
  
  try {
    await synastryApi.update(currentShareRecord.value.id, {
      is_public: isPublic
    })
    
    ElMessage.success(isPublic ? '已设为公开' : '已设为私有')
  } catch (error) {
    console.error('更新分享设置失败:', error)
    ElMessage.error(error.message || '更新失败')
    sharePublic.value = !isPublic
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

function confirmDelete(record) {
  deletingId.value = record.id
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!deletingId.value) return
  
  try {
    await synastryApi.delete(deletingId.value)
    
    ElMessage.success('删除成功')
    showDeleteConfirm.value = false
    deletingId.value = null
    loadRecords()
    
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error(error.message || '删除失败')
  }
}

watch(isLoggedIn, (newVal) => {
  if (newVal) {
    loadRecords()
  } else {
    router.push('/login')
  }
})

onMounted(() => {
  if (isLoggedIn.value) {
    loadRecords()
  } else {
    router.push('/login')
  }
})
</script>

<style lang="scss" scoped>
.records-container {
  min-height: 100vh;
  width: 100%;
  position: relative;
  background: linear-gradient(180deg, #0a0a1a 0%, #0d0d25 100%);
  overflow-x: hidden;
}

.stars-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle 4s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}

.records-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.records-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.header-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    color: #a78bfa;
  }
}

.header-title {
  text-align: center;
}

.main-title {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #ff8c32 0%, #50c8ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px 0;
}

.subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.new-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  border-radius: 12px;
}

.records-content {
  min-height: 400px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(139, 92, 246, 0.2);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 16px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  text-align: center;
}

.empty-icon {
  color: rgba(255, 255, 255, 0.15);
  margin-bottom: 20px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 8px 0;
}

.empty-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 24px 0;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15);
  }
}

.record-basic {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.persons-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.person {
  display: flex;
  align-items: center;
  gap: 12px;
}

.person-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-letter {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.person-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.person-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.person-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.connect-icon {
  flex-shrink: 0;
}

.record-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.score-circle {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-size: 28px;
  font-weight: 700;
}

.score-unit {
  font-size: 14px;
  opacity: 0.7;
}

.score-level {
  font-size: 12px;
  padding: 4px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 12px;
}

.record-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.record-info {
  display: flex;
  gap: 20px;
}

.record-name,
.record-date {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.record-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.share-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.share-tip {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.share-link-wrapper {
  display: flex;
  gap: 10px;
}

.link-input {
  flex: 1;
}

.share-settings {
  margin-top: 10px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.setting-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.setting-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 8px 0 0 0;
}

.delete-confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 10px;
}

.confirm-text {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.confirm-note {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

@media (max-width: 768px) {
  .records-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .persons-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .connect-icon {
    transform: rotate(90deg);
  }
  
  .record-basic {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .record-score {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  .record-footer {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .record-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
