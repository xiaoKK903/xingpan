<template>
  <el-dialog
    v-model="visible"
    :title="null"
    width="520px"
    :close-on-click-modal="true"
    :show-close="true"
    custom-class="checkin-dialog"
  >
    <div class="checkin-content">
      <div class="checkin-header">
        <div class="header-icon">
          <el-icon :size="48"><Calendar /></el-icon>
        </div>
        <h2 class="header-title">每日签到</h2>
        <div class="header-streak" v-if="checkinStatus">
          <span class="streak-label">连续签到</span>
          <span class="streak-days">{{ checkinStatus.current_streak }}天</span>
          <span class="streak-best" v-if="checkinStatus.best_streak > checkinStatus.current_streak">
            (最高{{ checkinStatus.best_streak }}天)
          </span>
        </div>
      </div>

      <div class="checkin-rewards-grid">
        <div
          v-for="reward in rewards"
          :key="reward.day_number"
          class="reward-item"
          :class="{
            'reward-item--completed': isDayCompleted(reward.day_number),
            'reward-item--today': isTodayReward(reward.day_number),
            'reward-item--next': isNextReward(reward.day_number)
          }"
        >
          <div class="reward-day">
            <span class="day-text">第{{ reward.day_number }}天</span>
            <el-icon v-if="isDayCompleted(reward.day_number)" class="check-icon"><Check /></el-icon>
          </div>
          
          <div class="reward-icon-wrapper">
            <div class="reward-icon" :class="'rarity-' + reward.rarity">
              <span class="icon-emoji">{{ reward.icon || '🎁' }}</span>
            </div>
          </div>
          
          <div class="reward-name" :title="reward.reward_name">
            {{ getRewardShortName(reward.reward_name) }}
          </div>
        </div>
      </div>

      <div class="checkin-action" v-if="checkinStatus">
        <template v-if="!checkinStatus.has_checked_in_today">
          <el-button
            type="primary"
            size="large"
            class="checkin-btn"
            :loading="isCheckingIn"
            @click="handleCheckIn"
          >
            <el-icon :size="20" class="btn-icon"><Present /></el-icon>
            立即签到领取奖励
          </el-button>
          <div class="next-reward-hint" v-if="checkinStatus.next_reward">
            今日签到可得：
            <span class="next-reward-name">{{ checkinStatus.next_reward.reward_name }}</span>
          </div>
        </template>
        <template v-else>
          <div class="checked-in-message">
            <el-icon :size="32" class="success-icon"><CircleCheckFilled /></el-icon>
            <div class="message-text">
              <p class="main-text">今日已签到</p>
              <p class="sub-text" v-if="checkinStatus.today_reward">
                已获得：{{ checkinStatus.today_reward.reward_name }}
              </p>
            </div>
          </div>
          <el-button
            type="default"
            size="large"
            class="close-btn"
            @click="visible = false"
          >
            关闭
          </el-button>
        </template>
      </div>

      <div class="checkin-stats" v-if="checkinStatus">
        <div class="stat-item">
          <span class="stat-value">{{ checkinStatus.total_checkins }}</span>
          <span class="stat-label">累计签到</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ checkinStatus.current_streak }}</span>
          <span class="stat-label">连续签到</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">{{ checkinStatus.best_streak }}</span>
          <span class="stat-label">最高纪录</span>
        </div>
      </div>
    </div>

    <div class="checkin-success-overlay" v-if="showSuccess">
      <div class="success-animation">
        <div class="success-icon-big">
          <el-icon :size="64"><CircleCheckFilled /></el-icon>
        </div>
        <h3 class="success-title">签到成功！</h3>
        <div class="success-reward" v-if="lastCheckInResult">
          <div class="reward-preview">
            <span class="reward-emoji">{{ getRewardIcon(lastCheckInResult.reward) }}</span>
          </div>
          <p class="reward-text">{{ lastCheckInResult.reward.reward_name }}</p>
          <p class="streak-update">
            连续签到 
            <span class="streak-number">{{ lastCheckInResult.current_streak }}</span>
            天
          </p>
        </div>
        <el-button type="primary" size="large" class="success-close-btn" @click="closeSuccess">
          太棒了！
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Calendar,
  Check,
  Present,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import { checkinApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'checked-in'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const checkinStatus = ref(null)
const rewards = ref([])
const isCheckingIn = ref(false)
const showSuccess = ref(false)
const lastCheckInResult = ref(null)

const loadData = async () => {
  try {
    const [statusData, rewardsData] = await Promise.all([
      checkinApi.getStatus(),
      checkinApi.getRewards()
    ])
    
    checkinStatus.value = statusData
    rewards.value = rewardsData?.rewards || []
  } catch (error) {
    console.error('加载签到数据失败:', error)
  }
}

watch(visible, (newVal) => {
  if (newVal) {
    loadData()
    showSuccess.value = false
  }
})

const isDayCompleted = (dayNumber) => {
  if (!checkinStatus.value) return false
  
  const currentStreak = checkinStatus.value.current_streak
  const hasCheckedInToday = checkinStatus.value.has_checked_in_today
  
  if (hasCheckedInToday) {
    return dayNumber <= currentStreak
  } else {
    return dayNumber < currentStreak
  }
}

const isTodayReward = (dayNumber) => {
  if (!checkinStatus.value) return false
  if (!checkinStatus.value.has_checked_in_today) return false
  
  return dayNumber === checkinStatus.value.current_streak
}

const isNextReward = (dayNumber) => {
  if (!checkinStatus.value) return false
  if (checkinStatus.value.has_checked_in_today) return false
  
  const nextDay = checkinStatus.value.current_streak + 1
  return dayNumber === (nextDay > 7 ? 1 : nextDay)
}

const getRewardShortName = (name) => {
  if (!name) return ''
  const match = name.match(/^([^x]+)/)
  return match ? match[1].trim() : name
}

const getRewardIcon = (reward) => {
  return reward?.icon || '🎁'
}

const handleCheckIn = async () => {
  if (isCheckingIn.value) return
  
  isCheckingIn.value = true
  
  try {
    const result = await checkinApi.performCheckin()
    
    lastCheckInResult.value = result
    showSuccess.value = true
    
    await loadData()
    
    emit('checked-in', result)
    
  } catch (error) {
    console.error('签到失败:', error)
    ElMessage.error(error.message || '签到失败，请重试')
  } finally {
    isCheckingIn.value = false
  }
}

const closeSuccess = () => {
  showSuccess.value = false
  visible.value = false
}

defineExpose({
  loadData
})
</script>

<style lang="scss" scoped>
.checkin-dialog {
  :deep(.el-dialog__header) {
    display: none;
  }
  
  :deep(.el-dialog__body) {
    padding: 0;
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
  }
}

.checkin-content {
  padding: 24px;
  position: relative;
}

.checkin-header {
  text-align: center;
  margin-bottom: 24px;
  
  .header-icon {
    width: 72px;
    height: 72px;
    margin: 0 auto 12px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a78bfa;
  }
  
  .header-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .header-streak {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    
    .streak-label,
    .streak-best {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .streak-days {
      font-size: 18px;
      font-weight: 600;
      color: #fbbf24;
    }
  }
}

.checkin-rewards-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 24px;
}

.reward-item {
  position: relative;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid transparent;
  text-align: center;
  transition: all 0.3s ease;
  
  .reward-day {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin-bottom: 8px;
    
    .day-text {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .check-icon {
      color: #10b981;
      font-size: 14px;
    }
  }
  
  .reward-icon-wrapper {
    margin-bottom: 8px;
    
    .reward-icon {
      width: 44px;
      height: 44px;
      margin: 0 auto;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.1);
      transition: all 0.3s ease;
      
      .icon-emoji {
        font-size: 24px;
      }
      
      &.rarity-common {
        background: linear-gradient(135deg, rgba(156, 163, 175, 0.2) 0%, rgba(156, 163, 175, 0.1) 100%);
      }
      
      &.rarity-uncommon {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%);
      }
      
      &.rarity-rare {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%);
      }
      
      &.rarity-epic {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(139, 92, 246, 0.1) 100%);
      }
      
      &.rarity-legendary {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%);
      }
    }
  }
  
  .reward-name {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.8);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  &.reward-item--completed {
    background: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.3);
    
    .reward-day .day-text {
      color: #10b981;
    }
    
    .reward-icon-wrapper .reward-icon {
      opacity: 0.7;
      filter: grayscale(0.3);
    }
  }
  
  &.reward-item--today {
    background: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.4);
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.2);
    
    .reward-day .day-text {
      color: #fbbf24;
      font-weight: 600;
    }
    
    .reward-icon-wrapper .reward-icon {
      animation: pulse-glow 2s ease-in-out infinite;
    }
  }
  
  &.reward-item--next {
    background: rgba(139, 92, 246, 0.1);
    border-color: rgba(139, 92, 246, 0.3);
    
    .reward-day .day-text {
      color: #a78bfa;
    }
  }
}

@keyframes pulse-glow {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(139, 92, 246, 0.5);
  }
}

.checkin-action {
  text-align: center;
  margin-bottom: 24px;
  
  .checkin-btn {
    width: 100%;
    max-width: 280px;
    height: 52px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 14px;
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    border: none;
    
    .btn-icon {
      margin-right: 8px;
    }
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
    }
  }
  
  .next-reward-hint {
    margin-top: 12px;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    
    .next-reward-name {
      color: #fbbf24;
      font-weight: 500;
    }
  }
  
  .checked-in-message {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-bottom: 20px;
    padding: 16px 24px;
    background: rgba(16, 185, 129, 0.1);
    border-radius: 12px;
    border: 1px solid rgba(16, 185, 129, 0.3);
    
    .success-icon {
      color: #10b981;
    }
    
    .message-text {
      text-align: left;
      
      .main-text {
        font-size: 16px;
        font-weight: 600;
        color: #10b981;
        margin: 0 0 4px;
      }
      
      .sub-text {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
        margin: 0;
      }
    }
  }
  
  .close-btn {
    width: 140px;
    height: 44px;
    border-radius: 10px;
  }
}

.checkin-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  
  .stat-item {
    text-align: center;
    flex: 1;
    
    .stat-value {
      display: block;
      font-size: 24px;
      font-weight: 700;
      background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .stat-label {
      display: block;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      margin-top: 4px;
    }
  }
  
  .stat-divider {
    width: 1px;
    height: 40px;
    background: rgba(255, 255, 255, 0.1);
    margin: 0 16px;
  }
}

.checkin-success-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  border-radius: 16px;
}

.success-animation {
  text-align: center;
  animation: zoom-in 0.4s ease-out;
  
  .success-icon-big {
    width: 96px;
    height: 96px;
    margin: 0 auto 20px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 70%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #10b981;
    animation: bounce 1s ease-in-out infinite;
  }
  
  .success-title {
    font-size: 28px;
    font-weight: 700;
    color: #fff;
    margin: 0 0 24px;
  }
  
  .success-reward {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    
    .reward-preview {
      width: 72px;
      height: 72px;
      margin: 0 auto 12px;
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .reward-emoji {
        font-size: 36px;
      }
    }
    
    .reward-text {
      font-size: 18px;
      font-weight: 600;
      color: #fbbf24;
      margin: 0 0 8px;
    }
    
    .streak-update {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
      margin: 0;
      
      .streak-number {
        color: #a78bfa;
        font-weight: 600;
        font-size: 18px;
      }
    }
  }
  
  .success-close-btn {
    width: 160px;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 12px;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: none;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
    }
  }
}

@keyframes zoom-in {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}
</style>
