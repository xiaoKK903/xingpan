<template>
  <div class="vip-center-page">
    <div class="page-header">
      <h1 class="page-title">星钻会员中心</h1>
      <p class="page-subtitle">开通星钻会员，享受极致星盘体验</p>
    </div>

    <div class="vip-status-card" :class="{ 'vip-active': isVip }">
      <div class="status-header">
        <div class="user-avatar">
          <span class="avatar-text">{{ userInitial }}</span>
          <div class="vip-badge-wrapper" v-if="isVip">
            <VIPBadge :is-vip="true" :plan-type="vipPlanType" :size="'small'" />
          </div>
        </div>
        <div class="user-info">
          <h2 class="user-name">{{ username }}</h2>
          <div class="vip-status-text">
            <template v-if="isVip">
              <span class="vip-label">星钻{{ vipPlanName }}会员</span>
              <span class="vip-days" v-if="vipDaysRemaining > 0">
                有效期剩余 {{ vipDaysRemaining }} 天
              </span>
            </template>
            <template v-else>
              <span class="no-vip-text">您还不是星钻会员</span>
            </template>
          </div>
        </div>
        <div class="action-buttons">
          <el-button
            type="primary"
            class="btn-action"
            @click="showSubscribeDialog = true"
          >
            {{ isVip ? '立即续费' : '立即开通' }}
          </el-button>
        </div>
      </div>

      <div class="vip-benefits" v-if="isVip">
        <div class="benefit-item">
          <span class="benefit-icon">📄</span>
          <div class="benefit-info">
            <span class="benefit-value">{{ vipFreeReportsRemaining }}</span>
            <span class="benefit-label">本月免费报告剩余</span>
          </div>
        </div>
        <div class="benefit-item" v-if="vipAutoRenewEnabled">
          <span class="benefit-icon">🔄</span>
          <div class="benefit-info">
            <span class="benefit-value">已开启</span>
            <span class="benefit-label">自动续费</span>
          </div>
        </div>
        <div class="benefit-item">
          <router-link to="/gift-shop" class="benefit-link">
            <span class="benefit-icon">🎁</span>
            <div class="benefit-info">
              <span class="benefit-value">礼物商城</span>
              <span class="benefit-label">赠送好友心意</span>
            </div>
          </router-link>
        </div>
        <div class="benefit-item">
          <router-link to="/report-shop" class="benefit-link">
            <span class="benefit-icon">📊</span>
            <div class="benefit-info">
              <span class="benefit-value">报告商城</span>
              <span class="benefit-label">深度星盘分析</span>
            </div>
          </router-link>
        </div>
      </div>
    </div>

    <div class="content-section">
      <VIPPrivilegesPanel
        :is-vip="isVip"
        :plan-type="vipPlanType"
        :days-remaining="vipDaysRemaining"
        :privileges-data="vipPrivileges"
        :free-reports-remaining="vipFreeReportsRemaining"
        @open-vip="showSubscribeDialog = true"
      />
    </div>

    <div class="content-section">
      <div class="section-header">
        <h3 class="section-title">订阅记录</h3>
        <el-button type="text" @click="loadSubscriptions" :loading="loadingSubscriptions">
          刷新
        </el-button>
      </div>
      <div class="subscriptions-list">
        <el-empty v-if="subscriptions.length === 0" description="暂无订阅记录">
          <template #image>
            <span class="empty-emoji">📋</span>
          </template>
        </el-empty>
        <div class="subscription-item" v-else v-for="sub in subscriptions" :key="sub.id">
          <div class="sub-plan" :class="'plan-' + sub.plan_type">
            <span class="plan-name">{{ sub.plan_type === 'yearly' ? '年卡' : '月卡' }}</span>
          </div>
          <div class="sub-info">
            <div class="sub-dates">
              <span class="date-label">开始时间：</span>
              <span class="date-value">{{ formatDate(sub.start_time) }}</span>
            </div>
            <div class="sub-dates" v-if="sub.end_time">
              <span class="date-label">到期时间：</span>
              <span class="date-value">{{ formatDate(sub.end_time) }}</span>
            </div>
          </div>
          <div class="sub-status">
            <el-tag :type="getStatusType(sub.status)" size="small">
              {{ getStatusText(sub.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>

  <VIPSubscribeDialog
    v-model="showSubscribeDialog"
    :is-vip="isVip"
    :plan-type="vipPlanType"
    :days-remaining="vipDaysRemaining"
    @success="handleSubscribeSuccess"
    @close="showSubscribeDialog = false"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { vipApi } from '@/api'
import VIPBadge from '@/components/VIPBadge.vue'
import VIPPrivilegesPanel from '@/components/VIPPrivilegesPanel.vue'
import VIPSubscribeDialog from '@/components/VIPSubscribeDialog.vue'

const userStore = useUserStore()

const showSubscribeDialog = ref(false)
const subscriptions = ref([])
const loadingSubscriptions = ref(false)

const isVip = computed(() => userStore.isVip)
const vipPlanType = computed(() => userStore.vipPlanType)
const vipDaysRemaining = computed(() => userStore.vipDaysRemaining)
const vipFreeReportsRemaining = computed(() => userStore.vipFreeReportsRemaining)
const vipPrivileges = computed(() => userStore.vipPrivileges)
const username = computed(() => userStore.username || '用户')

const userInitial = computed(() => {
  const name = username.value
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const vipPlanName = computed(() => {
  return vipPlanType.value === 'yearly' ? '年卡' : '月卡'
})

const vipAutoRenewEnabled = computed(() => {
  return userStore.vipStatus?.auto_renew_enabled || false
})

onMounted(() => {
  loadSubscriptions()
})

async function loadSubscriptions() {
  if (!userStore.isLoggedIn) return
  loadingSubscriptions.value = true
  try {
    const response = await vipApi.getSubscriptions(10, 0)
    subscriptions.value = response.items || []
  } catch (error) {
    console.error('加载订阅记录失败:', error)
  } finally {
    loadingSubscriptions.value = false
  }
}

async function handleSubscribeSuccess() {
  await userStore.fetchVipStatus()
  await loadSubscriptions()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getStatusType(status) {
  const types = {
    'active': 'success',
    'expired': 'info',
    'cancelled': 'warning',
    'pending': 'primary'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    'active': '有效',
    'expired': '已过期',
    'cancelled': '已取消',
    'pending': '待生效'
  }
  return texts[status] || status
}
</script>

<style lang="scss" scoped>
.vip-center-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  margin: 0 0 8px;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fbbf24, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
}

.vip-status-card {
  background: linear-gradient(145deg, rgba(30, 30, 60, 0.95), rgba(20, 20, 50, 0.98));
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 24px;
  margin-bottom: 24px;
  transition: all 0.3s ease;
  
  &.vip-active {
    border-color: rgba(251, 191, 36, 0.3);
    box-shadow: 0 8px 40px rgba(251, 191, 36, 0.1);
  }
}

.status-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.user-avatar {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
}

.vip-badge-wrapper {
  position: absolute;
  bottom: -4px;
  right: -4px;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  margin: 0 0 8px;
  font-size: 1.3rem;
  font-weight: 600;
  color: #fff;
}

.vip-status-text {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.vip-label {
  padding: 4px 12px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}

.vip-days {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.no-vip-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
}

.action-buttons {
  flex-shrink: 0;
}

.btn-action {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border: none;
  font-weight: 600;
  
  &:hover {
    background: linear-gradient(135deg, #fbbf24, #d97706);
  }
}

.vip-benefits {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.benefit-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
}

.benefit-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  
  &:hover {
    .benefit-value {
      color: #a78bfa;
    }
  }
}

.benefit-icon {
  font-size: 1.5rem;
}

.benefit-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.benefit-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  transition: color 0.3s ease;
}

.benefit-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.content-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.subscriptions-list {
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.95), rgba(15, 15, 35, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.empty-emoji {
  font-size: 3rem;
}

.subscription-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  
  &:last-child {
    border-bottom: none;
  }
  
  &:hover {
    background: rgba(255, 255, 255, 0.02);
  }
}

.sub-plan {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &.plan-monthly {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1));
  }
  
  &.plan-yearly {
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.2), rgba(167, 139, 250, 0.1));
  }
}

.plan-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.sub-info {
  flex: 1;
  min-width: 0;
}

.sub-dates {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.date-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

.date-value {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.sub-status {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .vip-center-page {
    padding: 16px;
  }
  
  .status-header {
    flex-wrap: wrap;
  }
  
  .vip-benefits {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .subscription-item {
    flex-wrap: wrap;
  }
}
</style>