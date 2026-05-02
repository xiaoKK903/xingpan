<template>
  <el-dialog
    v-model="visible"
    title="开通星钻会员"
    width="500px"
    :close-on-click-modal="false"
    class="vip-subscribe-dialog"
  >
    <div class="vip-dialog-content">
      <div class="vip-header">
        <div class="vip-logo">
          <span class="vip-icon">⭐</span>
          <span class="vip-title">星钻会员</span>
        </div>
        <p class="vip-subtitle">解锁全部特权，畅享极致星盘体验</p>
      </div>

      <div class="vip-plans">
        <div
          class="plan-card"
          :class="{ 'plan-selected': selectedPlan === 'monthly', 'plan-recommended': false }"
          @click="selectedPlan = 'monthly'"
        >
          <div class="plan-header">
            <span class="plan-name">月卡</span>
          </div>
          <div class="plan-price">
            <span class="price-symbol">¥</span>
            <span class="price-value">19</span>
            <span class="price-unit">/月</span>
          </div>
          <div class="plan-features">
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>全部VIP特权</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>3份免费报告/月</span>
            </div>
          </div>
        </div>

        <div
          class="plan-card plan-yearly"
          :class="{ 'plan-selected': selectedPlan === 'yearly' }"
          @click="selectedPlan = 'yearly'"
        >
          <div class="plan-recommend-badge">
            <span>推荐</span>
          </div>
          <div class="plan-header">
            <span class="plan-name">年卡</span>
          </div>
          <div class="plan-price">
            <span class="price-symbol">¥</span>
            <span class="price-value">168</span>
            <span class="price-unit">/年</span>
          </div>
          <div class="plan-save">
            <span class="save-text">省 60 元</span>
            <span class="save-discount">85折</span>
          </div>
          <div class="plan-features">
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>全部VIP特权</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>3份免费报告/月</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>专属年卡标识</span>
            </div>
          </div>
        </div>
      </div>

      <div class="vip-auto-renew" v-if="!isCurrentVip">
        <el-checkbox v-model="autoRenew" size="large">
          <span class="auto-renew-text">自动续费，到期前3天自动扣款</span>
        </el-checkbox>
      </div>

      <div class="vip-current-status" v-if="isCurrentVip">
        <el-alert
          :title="currentStatusText"
          type="info"
          :closable="false"
          show-icon
        >
          <template #icon>
            <el-icon><Star /></el-icon>
          </template>
        </el-alert>
      </div>

      <div class="vip-privileges-list">
        <div class="privileges-header">
          <span class="privileges-title">开通即享全部特权</span>
        </div>
        <div class="privileges-grid">
          <div class="privilege-item" v-for="privilege in privilegesList" :key="privilege.key">
            <span class="privilege-icon">{{ privilege.icon }}</span>
            <span class="privilege-name">{{ privilege.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-price">
          <span class="price-label">应付：</span>
          <span class="price-symbol">¥</span>
          <span class="price-amount">{{ selectedPlan === 'monthly' ? 19 : 168 }}</span>
        </div>
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="isCurrentVip && !isRenewal"
          class="btn-subscribe"
          @click="handleSubscribe"
        >
          {{ isCurrentVip ? '立即续费' : '立即开通' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Star } from '@element-plus/icons-vue'
import { vipApi, paymentApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  isVip: {
    type: Boolean,
    default: false
  },
  planType: {
    type: String,
    default: ''
  },
  daysRemaining: {
    type: Number,
    default: 0
  },
  isRenewal: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'close'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const selectedPlan = ref('yearly')
const autoRenew = ref(true)
const loading = ref(false)

const isCurrentVip = computed(() => props.isVip)

const currentStatusText = computed(() => {
  if (!props.isVip) return ''
  const planName = props.planType === 'yearly' ? '年卡' : '月卡'
  if (props.daysRemaining > 0) {
    return `您当前是星钻${planName}会员，有效期剩余 ${props.daysRemaining} 天`
  }
  return `您当前是星钻${planName}会员`
})

const privilegesList = [
  { key: 'no_ads', icon: '🚫', name: '全站免广告' },
  { key: 'blind_box_extra', icon: '🎁', name: '盲盒额外抽取' },
  { key: 'blind_box_discount', icon: '💰', name: '盲盒折扣' },
  { key: 'unlimited_synastry', icon: '💕', name: '合盘无限制' },
  { key: 'advanced_forecast', icon: '📅', name: '7天星运超前看' },
  { key: 'exclusive_skin', icon: '🎨', name: '专属皮肤挂件' },
  { key: 'social_priority', icon: '👑', name: '社交加权推荐' },
  { key: 'free_reports', icon: '📄', name: '每月免费报告' }
]

watch(visible, (val) => {
  if (val) {
    selectedPlan.value = 'yearly'
    loading.value = false
  }
})

function handleClose() {
  emit('close')
}

async function handleSubscribe() {
  loading.value = true
  try {
    const response = await vipApi.subscribe(selectedPlan.value)
    
    if (response.payment_url) {
      const win = window.open(response.payment_url, '_blank', 'width=600,height=700')
      
      const checkInterval = setInterval(async () => {
        try {
          const orderResult = await paymentApi.getOrder(response.order_no)
          if (orderResult.status === 'paid') {
            clearInterval(checkInterval)
            ElMessage.success('开通成功！')
            emit('success', { order: orderResult, planType: selectedPlan.value })
            handleClose()
          }
        } catch (e) {
          console.error('检查订单状态失败:', e)
        }
      }, 3000)
      
      setTimeout(() => {
        clearInterval(checkInterval)
      }, 120000)
    }
    
  } catch (error) {
    console.error('开通失败:', error)
    ElMessage.error(error.response?.data?.detail || '开通失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.vip-dialog-content {
  padding: 0;
}

.vip-header {
  text-align: center;
  padding: 20px 0;
  background: linear-gradient(180deg, rgba(251, 191, 36, 0.1), transparent);
  border-radius: 8px;
  margin-bottom: 20px;
}

.vip-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 8px;
}

.vip-icon {
  font-size: 2rem;
}

.vip-title {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.vip-subtitle {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
}

.vip-plans {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.plan-card {
  flex: 1;
  position: relative;
  padding: 20px;
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(251, 191, 36, 0.4);
  }
  
  &.plan-selected {
    border-color: #fbbf24;
    background: rgba(251, 191, 36, 0.08);
    box-shadow: 0 0 20px rgba(251, 191, 36, 0.2);
  }
  
  &.plan-yearly {
    border-color: rgba(167, 139, 250, 0.3);
    
    &:hover {
      border-color: rgba(167, 139, 250, 0.5);
    }
    
    &.plan-selected {
      border-color: #a78bfa;
      background: rgba(167, 139, 250, 0.08);
      box-shadow: 0 0 20px rgba(167, 139, 250, 0.2);
    }
  }
}

.plan-recommend-badge {
  position: absolute;
  top: -10px;
  right: 16px;
  background: linear-gradient(135deg, #a78bfa, #8b5cf6);
  padding: 2px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
}

.plan-header {
  margin-bottom: 12px;
}

.plan-name {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.plan-price {
  margin-bottom: 8px;
}

.price-symbol {
  font-size: 0.9rem;
  color: #fbbf24;
}

.price-value {
  font-size: 2rem;
  font-weight: 700;
  color: #fbbf24;
}

.plan-yearly .price-symbol,
.plan-yearly .price-value {
  color: #a78bfa;
}

.price-unit {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.plan-save {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.save-text {
  font-size: 0.85rem;
  color: #a78bfa;
  font-weight: 600;
}

.save-discount {
  padding: 2px 8px;
  background: rgba(167, 139, 250, 0.2);
  border-radius: 4px;
  font-size: 0.75rem;
  color: #a78bfa;
}

.plan-features {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  
  .el-icon {
    color: #4ade80;
    font-size: 0.9rem;
  }
}

.vip-auto-renew {
  margin-bottom: 20px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.auto-renew-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.vip-current-status {
  margin-bottom: 20px;
}

.vip-privileges-list {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.privileges-header {
  margin-bottom: 12px;
}

.privileges-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.privileges-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.privilege-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(251, 191, 36, 0.08);
  }
}

.privilege-icon {
  font-size: 1.2rem;
}

.privilege-name {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
}

.footer-price {
  display: flex;
  align-items: baseline;
  margin-right: auto;
}

.price-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.footer-price .price-symbol {
  font-size: 1rem;
  margin-left: 4px;
}

.footer-price .price-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fbbf24;
}

.btn-subscribe {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border: none;
  font-weight: 600;
  
  &:hover {
    background: linear-gradient(135deg, #fbbf24, #d97706);
  }
}
</style>