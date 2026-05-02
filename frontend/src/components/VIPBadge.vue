<template>
  <div class="vip-badge-container" :class="badgeClass">
    <el-tooltip :content="tooltipContent" placement="top" :disabled="!showTooltip">
      <div class="vip-badge" :class="{ 'clickable': clickable }" @click="handleClick">
        <span class="vip-icon">
          <component v-if="customIcon" :is="customIcon" />
          <span v-else>⭐</span>
        </span>
        <span class="vip-text" v-if="showText">{{ badgeText }}</span>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'

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
  showText: {
    type: Boolean,
    default: true
  },
  size: {
    type: String,
    default: 'medium'
  },
  customIcon: {
    type: [Object, String],
    default: null
  },
  showTooltip: {
    type: Boolean,
    default: true
  },
  clickable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const badgeClass = computed(() => {
  return {
    'vip-badge-small': props.size === 'small',
    'vip-badge-large': props.size === 'large',
    'vip-badge-yearly': props.planType === 'yearly'
  }
})

const badgeText = computed(() => {
  if (props.planType === 'yearly') {
    return '星钻年卡'
  }
  return '星钻会员'
})

const tooltipContent = computed(() => {
  if (!props.isVip) {
    return '开通星钻会员，享受专属特权'
  }
  if (props.daysRemaining > 0) {
    return `星钻会员有效期剩余 ${props.daysRemaining} 天`
  }
  return '星钻会员'
})

function handleClick() {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style lang="scss" scoped>
.vip-badge-container {
  display: inline-flex;
  align-items: center;
}

.vip-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #fff;
  font-weight: 600;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(251, 191, 36, 0.3);
  transition: all 0.3s ease;
  
  &.clickable {
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
    }
  }
  
  &.vip-badge-small {
    padding: 2px 8px;
    font-size: 0.75rem;
    
    .vip-icon {
      font-size: 0.9rem;
    }
  }
  
  &.vip-badge-large {
    padding: 6px 14px;
    font-size: 1rem;
    
    .vip-icon {
      font-size: 1.2rem;
    }
  }
  
  &.vip-badge-yearly {
    background: linear-gradient(135deg, #a78bfa, #8b5cf6);
    box-shadow: 0 2px 8px rgba(167, 139, 250, 0.3);
    
    &:hover {
      box-shadow: 0 4px 12px rgba(167, 139, 250, 0.4);
    }
  }
}

.vip-icon {
  font-size: 1rem;
  display: flex;
  align-items: center;
}

.vip-text {
  white-space: nowrap;
}
</style>