<template>
  <div class="invite-container">
    <div class="invite-main">
      <el-row :gutter="24">
        <el-col :span="16">
          <el-card class="invite-card main-card">
            <template #header>
              <div class="card-header">
                <div class="header-icon">
                  <el-icon size="24"><Present /></el-icon>
                </div>
                <h3 class="card-title">邀请好友得奖励</h3>
              </div>
            </template>

            <div class="invite-code-section">
              <div class="invite-code-box">
                <div class="code-label">我的邀请码</div>
                <div class="code-value" v-if="inviteCode">
                  <span class="code-text">{{ inviteCode.invite_code }}</span>
                  <el-button type="primary" size="small" @click="copyInviteCode" :loading="copying">
                    <el-icon><CopyDocument /></el-icon>
                    {{ copying ? '已复制' : '复制' }}
                  </el-button>
                </div>
                <div class="code-loading" v-else>
                  <el-icon class="loading-icon"><Loading /></el-icon>
                  <span>加载中...</span>
                </div>
              </div>

              <div class="invite-link-box" v-if="inviteCode">
                <div class="link-label">邀请链接</div>
                <div class="link-value">
                  <input type="text" :value="inviteLink" readonly class="link-input" />
                  <el-button type="success" size="small" @click="copyInviteLink" :loading="copyingLink">
                    <el-icon><Share /></el-icon>
                    {{ copyingLink ? '已复制' : '复制链接' }}
                  </el-button>
                </div>
              </div>
            </div>

            <el-divider />

            <div class="reward-stages-section">
              <h4 class="section-title">三级邀请奖励规则</h4>
              <div class="reward-stages">
                <div class="stage-item stage-1">
                  <div class="stage-number">
                    <span>1</span>
                  </div>
                  <div class="stage-content">
                    <h5>分享邀请</h5>
                    <p class="stage-desc">分享 App 给好友，好友通过你的邀请码注册</p>
                    <div class="stage-reward">
                      <el-tag type="warning" effect="dark">双方各得 50 星元碎片</el-tag>
                    </div>
                  </div>
                </div>

                <div class="stage-connector">
                  <el-icon><ArrowRight /></el-icon>
                </div>

                <div class="stage-item stage-2">
                  <div class="stage-number">
                    <span>2</span>
                  </div>
                  <div class="stage-content">
                    <h5>完成星盘</h5>
                    <p class="stage-desc">好友注册后保存自己的第一个星盘</p>
                    <div class="stage-reward">
                      <el-tag type="primary" effect="dark">邀请人：1 张星图盲盒券</el-tag>
                      <el-tag type="success" effect="dark">被邀请人：3 天会员体验</el-tag>
                    </div>
                  </div>
                </div>

                <div class="stage-connector">
                  <el-icon><ArrowRight /></el-icon>
                </div>

                <div class="stage-item stage-3">
                  <div class="stage-number">
                    <span>3</span>
                  </div>
                  <div class="stage-content">
                    <h5>首次付费</h5>
                    <p class="stage-desc">好友首次任意付费消费</p>
                    <div class="stage-reward">
                      <el-tag type="danger" effect="dark">邀请人：付费金额 20% 返利</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <el-divider />

            <div class="invitees-section">
              <h4 class="section-title">我的邀请列表</h4>
              <div v-if="invitees.length > 0" class="invitees-list">
                <div class="invitee-item" v-for="invitee in invitees" :key="invitee.user_id">
                  <div class="invitee-avatar">
                    <el-icon size="20"><User /></el-icon>
                  </div>
                  <div class="invitee-info">
                    <div class="invitee-name">{{ invitee.username || '星友' }}</div>
                    <div class="invitee-time">{{ formatTime(invitee.created_at) }}</div>
                  </div>
                  <div class="invitee-status">
                    <el-tag :type="getInviteeStatusType(invitee)" size="small">
                      {{ getInviteeStatusText(invitee) }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无邀请记录，快去邀请好友吧！" :image-size="80">
                <template #description>
                  <span>暂无邀请记录</span>
                </template>
              </el-empty>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card class="invite-card stats-card">
            <template #header>
              <h3 class="card-title">邀请统计</h3>
            </template>

            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_invites || 0 }}</div>
                <div class="stat-label">总邀请数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value highlight">{{ stats.valid_invites || 0 }}</div>
                <div class="stat-label">有效邀请</div>
              </div>
              <div class="stat-item">
                <div class="stat-value premium">{{ stats.paid_invites || 0 }}</div>
                <div class="stat-label">付费邀请</div>
              </div>
              <div class="stat-item">
                <div class="stat-value reward">{{ stats.total_rewards_earned || 0 }}</div>
                <div class="stat-label">星元碎片</div>
              </div>
            </div>
          </el-card>

          <el-card class="invite-card share-tips-card">
            <template #header>
              <h3 class="card-title">分享提示</h3>
            </template>

            <div class="share-tips">
              <div class="tip-item">
                <el-icon class="tip-icon"><InfoFilled /></el-icon>
                <span>邀请码仅在好友注册时有效</span>
              </div>
              <div class="tip-item">
                <el-icon class="tip-icon"><InfoFilled /></el-icon>
                <span>每位好友只能使用一个邀请码</span>
              </div>
              <div class="tip-item">
                <el-icon class="tip-icon"><InfoFilled /></el-icon>
                <span>同IP设备重复注册可能被判定为刷邀请</span>
              </div>
              <div class="tip-item">
                <el-icon class="tip-icon"><InfoFilled /></el-icon>
                <span>合盘卡牌生成后可分享邀请好友</span>
              </div>
            </div>
          </el-card>

          <el-card class="invite-card quick-actions-card">
            <template #header>
              <h3 class="card-title">快捷操作</h3>
            </template>

            <div class="quick-actions">
              <el-button type="primary" class="action-btn" @click="goToSynastry">
                <el-icon><Connection /></el-icon>
                <span>做合盘得邀请</span>
              </el-button>
              <el-button type="success" class="action-btn" @click="goToMyCharts">
                <el-icon><Document /></el-icon>
                <span>我的星盘</span>
              </el-button>
              <el-button type="warning" class="action-btn" @click="goToVIP">
                <el-icon><Coin /></el-icon>
                <span>会员中心</span>
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Present, CopyDocument, Loading, ArrowRight, User, InfoFilled, Connection, Document, Coin } from '@element-plus/icons-vue'
import { inviteApi } from '@/api'

const router = useRouter()

const inviteCode = ref(null)
const stats = ref({})
const invitees = ref([])
const copying = ref(false)
const copyingLink = ref(false)

const inviteLink = computed(() => {
  if (!inviteCode.value?.invite_code) return ''
  const baseUrl = window.location.origin
  return `${baseUrl}/register?invite_code=${inviteCode.value.invite_code}`
})

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getInviteeStatusType = (invitee) => {
  if (invitee.has_first_payment) return 'danger'
  if (invitee.is_register_completed) return 'success'
  return 'warning'
}

const getInviteeStatusText = (invitee) => {
  if (invitee.has_first_payment) return '已付费'
  if (invitee.is_register_completed) return '已完成星盘'
  return '已注册'
}

const loadInviteCode = async () => {
  try {
    const result = await inviteApi.getCode()
    inviteCode.value = result
  } catch (error) {
    console.error('加载邀请码失败:', error)
  }
}

const loadStats = async () => {
  try {
    const result = await inviteApi.getStats()
    stats.value = result
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadInvitees = async () => {
  try {
    const result = await inviteApi.getMyInvitees(1, 20)
    invitees.value = result.invitees || result.items || []
  } catch (error) {
    console.error('加载邀请列表失败:', error)
  }
}

const copyInviteCode = async () => {
  if (!inviteCode.value?.invite_code) return
  
  copying.value = true
  try {
    await navigator.clipboard.writeText(inviteCode.value.invite_code)
    ElMessage.success('邀请码已复制')
    setTimeout(() => {
      copying.value = false
    }, 1500)
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
    copying.value = false
  }
}

const copyInviteLink = async () => {
  if (!inviteLink.value) return
  
  copyingLink.value = true
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    ElMessage.success('邀请链接已复制')
    setTimeout(() => {
      copyingLink.value = false
    }, 1500)
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
    copyingLink.value = false
  }
}

const goToSynastry = () => {
  router.push('/synastry')
}

const goToMyCharts = () => {
  router.push('/my-charts')
}

const goToVIP = () => {
  router.push('/vip-center')
}

onMounted(() => {
  loadInviteCode()
  loadStats()
  loadInvitees()
})
</script>

<style lang="scss" scoped>
.invite-container {
  width: 100%;
  min-height: calc(100vh - 140px);
  padding: 20px;
}

.invite-main {
  max-width: 1400px;
  margin: 0 auto;
}

.invite-card {
  background: rgba(20, 20, 50, 0.8) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2) !important;
  border-radius: 16px !important;
  margin-bottom: 20px;
  
  :deep(.el-card__header) {
    border-bottom: 1px solid rgba(139, 92, 246, 0.15) !important;
    padding: 16px 20px;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.2) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95) !important;
  margin: 0;
}

.invite-code-section {
  margin-bottom: 20px;
}

.invite-code-box {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.code-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
}

.code-value {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.code-text {
  font-size: 32px;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: 4px;
  font-family: 'Courier New', monospace;
}

.code-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.5);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.invite-link-box {
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 10px;
  padding: 16px;
}

.link-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 10px;
}

.link-value {
  display: flex;
  align-items: center;
  gap: 10px;
}

.link-input {
  flex: 1;
  padding: 10px 14px;
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  outline: none;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.35);
  }
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 16px 0;
}

.reward-stages-section {
  margin-bottom: 20px;
}

.reward-stages {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.stage-item {
  flex: 1;
  min-width: 200px;
  background: rgba(30, 30, 60, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 16px;
  position: relative;
}

.stage-1 {
  border-color: rgba(251, 191, 36, 0.3);
}

.stage-2 {
  border-color: rgba(34, 197, 94, 0.3);
}

.stage-3 {
  border-color: rgba(239, 68, 68, 0.3);
}

.stage-number {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  
  span {
    font-size: 18px;
    font-weight: 700;
    color: #fff;
  }
}

.stage-content h5 {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px 0;
}

.stage-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.stage-reward {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stage-connector {
  display: none;
  
  @media (min-width: 1024px) {
    display: flex;
    align-items: center;
    justify-content: center;
    padding-top: 30px;
    color: rgba(139, 92, 246, 0.5);
    font-size: 24px;
  }
}

.invitees-section {
  margin-top: 20px;
}

.invitees-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.invitee-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(30, 30, 60, 0.4);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 10px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
    background: rgba(30, 30, 60, 0.6);
  }
}

.invitee-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.2) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
}

.invitee-info {
  flex: 1;
}

.invitee-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.invitee-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
}

.invitee-status {
  flex-shrink: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px 8px;
  background: rgba(30, 30, 60, 0.4);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 4px;
  
  &.highlight {
    background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  &.premium {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  &.reward {
    background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.share-tips {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
}

.tip-icon {
  color: #a78bfa;
  flex-shrink: 0;
  margin-top: 2px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100% !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px !important;
  font-weight: 500;
}

:deep(.el-empty__description) {
  color: rgba(255, 255, 255, 0.5) !important;
}
</style>
