<template>
  <div class="vip-privileges-panel">
    <div class="panel-header">
      <div class="header-left">
        <span class="panel-icon">⭐</span>
        <span class="panel-title">星钻会员特权</span>
      </div>
      <el-button
        type="primary"
        size="small"
        v-if="!isVip"
        class="btn-open-vip"
        @click="$emit('open-vip')"
      >
        立即开通
      </el-button>
      <VIPBadge
        v-else
        :is-vip="isVip"
        :plan-type="planType"
        :days-remaining="daysRemaining"
        :size="'small'"
      />
    </div>

    <div class="panel-content">
      <div class="privileges-list">
        <div
          class="privilege-card"
          v-for="privilege in privileges"
          :key="privilege.key"
          :class="{ 'privilege-active': isVip && privilege.active }"
        >
          <div class="privilege-icon-wrapper">
            <span class="privilege-icon">{{ privilege.icon }}</span>
            <div class="privilege-overlay" v-if="!isVip">
              <span class="lock-icon">🔒</span>
            </div>
          </div>
          <div class="privilege-info">
            <span class="privilege-name">{{ privilege.name }}</span>
            <p class="privilege-desc">{{ privilege.description }}</p>
            <span class="privilege-value" v-if="isVip && privilege.value">
              {{ privilege.value }}
            </span>
          </div>
          <div class="privilege-status" v-if="isVip && privilege.active">
            <el-icon class="check-icon"><Check /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <div class="panel-footer" v-if="!isVip">
      <p class="footer-text">开通星钻会员，解锁全部特权，享受极致星盘体验</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check } from '@element-plus/icons-vue'
import VIPBadge from './VIPBadge.vue'

const props = defineProps({
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
  privilegesData: {
    type: Array,
    default: () => []
  },
  freeReportsRemaining: {
    type: Number,
    default: 0
  },
  blindBoxExtraDraws: {
    type: Number,
    default: 0
  },
  blindBoxDiscount: {
    type: Number,
    default: 0
  }
})

defineEmits(['open-vip'])

const privileges = computed(() => {
  const allPrivileges = [
    {
      key: 'no_ads',
      icon: '🚫',
      name: '全站免广告',
      description: '享受纯净无广告的使用体验',
      active: true
    },
    {
      key: 'blind_box_extra',
      icon: '🎁',
      name: '盲盒额外抽取',
      description: '每月额外抽取次数',
      active: true,
      value: props.blindBoxExtraDraws > 0 ? `已额外抽取 ${props.blindBoxExtraDraws} 次` : null
    },
    {
      key: 'blind_box_discount',
      icon: '💰',
      name: '盲盒折扣优惠',
      description: '盲盒购买享受专属折扣',
      active: true,
      value: props.blindBoxDiscount > 0 ? `${props.blindBoxDiscount}% 折扣` : null
    },
    {
      key: 'unlimited_synastry',
      icon: '💕',
      name: '合盘无次数限制',
      description: '免费查看无限次双人合盘',
      active: true
    },
    {
      key: 'advanced_forecast',
      icon: '📅',
      name: '7天星运超前看',
      description: '提前查看未来7天的运势预测',
      active: true
    },
    {
      key: 'exclusive_skin',
      icon: '🎨',
      name: '专属皮肤挂件',
      description: '专属VIP主题和头像挂件',
      active: true
    },
    {
      key: 'social_priority',
      icon: '👑',
      name: '社交加权推荐',
      description: '社交匹配中获得更高优先级',
      active: true
    },
    {
      key: 'free_reports',
      icon: '📄',
      name: '每月免费报告',
      description: '每月可免费领取3份付费报告',
      active: true,
      value: `剩余 ${props.freeReportsRemaining || 0} 份`
    }
  ]

  if (props.privilegesData && props.privilegesData.length > 0) {
    return allPrivileges.map(p => {
      const found = props.privilegesData.find(pp => pp.privilege_key === p.key)
      if (found && found.value_data) {
        if (p.key === 'free_reports') {
          p.value = `剩余 ${props.freeReportsRemaining || found.value_data.free_reports_per_month || 3} 份`
        } else if (p.key === 'blind_box_extra') {
          p.value = `每月 ${found.value_data.extra_draws || 1} 次`
        } else if (p.key === 'blind_box_discount') {
          p.value = `${found.value_data.discount_percent || 10}% 折扣`
        }
      }
      return p
    })
  }

  return allPrivileges
})
</script>

<style lang="scss" scoped>
.vip-privileges-panel {
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.95), rgba(15, 15, 35, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(251, 191, 36, 0.2);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.1), transparent);
  border-bottom: 1px solid rgba(251, 191, 36, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon {
  font-size: 1.2rem;
}

.panel-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.btn-open-vip {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border: none;
  font-weight: 600;
  
  &:hover {
    background: linear-gradient(135deg, #fbbf24, #d97706);
  }
}

.panel-content {
  padding: 16px;
}

.privileges-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.privilege-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(251, 191, 36, 0.2);
  }
  
  &.privilege-active {
    background: rgba(251, 191, 36, 0.05);
    border-color: rgba(251, 191, 36, 0.3);
  }
}

.privilege-icon-wrapper {
  position: relative;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(251, 191, 36, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
}

.privilege-icon {
  font-size: 1.5rem;
}

.privilege-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.lock-icon {
  font-size: 1rem;
  opacity: 0.8;
}

.privilege-info {
  flex: 1;
  min-width: 0;
}

.privilege-name {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.privilege-desc {
  margin: 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

.privilege-value {
  display: inline-block;
  margin-top: 6px;
  padding: 2px 8px;
  background: rgba(74, 222, 128, 0.1);
  border-radius: 4px;
  font-size: 0.7rem;
  color: #4ade80;
}

.privilege-status {
  flex-shrink: 0;
}

.check-icon {
  color: #4ade80;
  font-size: 1.2rem;
}

.panel-footer {
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.2);
  text-align: center;
}

.footer-text {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 600px) {
  .privileges-list {
    grid-template-columns: 1fr;
  }
}
</style>