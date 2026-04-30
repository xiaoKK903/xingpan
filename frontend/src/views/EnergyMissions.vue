<template>
  <div class="missions-page">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="missions-main">
      <div class="page-header">
        <div class="header-back" @click="router.back()">
          <el-icon><Connection /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">
          <div class="title-icon">
            <el-icon size="28"><Flag /></el-icon>
          </div>
          <div class="title-text">
            <h1>能量任务中心</h1>
            <p>参与集体共修，获取星尘奖励</p>
          </div>
        </div>
      </div>

      <div class="tabs-container">
        <el-tabs v-model="activeTab" class="mission-tabs">
          <el-tab-pane label="进行中" name="active">
            <div class="missions-list" v-if="activeMissions?.length > 0">
              <div class="mission-card" v-for="mission in activeMissions" :key="mission.id">
                <div class="mission-header">
                  <div class="mission-type-badge" :class="mission.mission_type">
                    {{ getMissionTypeLabel(mission.mission_type) }}
                  </div>
                  <div class="mission-time">
                    <el-icon><Clock /></el-icon>
                    <span>{{ getTimeRemaining(mission.ends_at) }}</span>
                  </div>
                </div>

                <div class="mission-body">
                  <div class="mission-main">
                    <div class="mission-icon" :class="mission.mission_type">
                      <el-icon :size="32">{{ getMissionIcon(mission.mission_type) }}</el-icon>
                    </div>
                    <div class="mission-info">
                      <h3 class="mission-title">{{ mission.title }}</h3>
                      <p class="mission-desc">{{ mission.description }}</p>
                      <div class="mission-triggers" v-if="mission.trigger_conditions">
                        <span class="trigger-label">触发条件：</span>
                        <span class="trigger-text">{{ parseTriggerConditions(mission.trigger_conditions) }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="mission-stats">
                    <div class="stat-item">
                      <span class="stat-label">参与人数</span>
                      <span class="stat-value">{{ mission.participant_count || 0 }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">基础奖励</span>
                      <span class="stat-value reward">
                        <el-icon><Star /></el-icon>
                        <span>{{ mission.base_reward }}</span>
                      </span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">难度</span>
                      <span class="stat-value difficulty" :class="mission.difficulty">
                        {{ getDifficultyLabel(mission.difficulty) }}
                      </span>
                    </div>
                  </div>
                </div>

                <div class="mission-footer">
                  <el-progress 
                    v-if="mission.participation?.progress !== undefined"
                    :percentage="mission.participation.progress" 
                    :stroke-width="6"
                    :color="getProgressColor(mission.difficulty)"
                  >
                    <template #default="{ percentage }">
                      <span class="progress-text">{{ percentage }}%</span>
                    </template>
                  </el-progress>
                  
                  <el-button 
                    type="primary" 
                    size="large"
                    :loading="joiningMission === mission.id"
                    :disabled="mission.participation?.progress >= 100"
                    @click="handleMissionAction(mission)"
                    class="mission-action-btn"
                  >
                    <template v-if="mission.participation">
                      <template v-if="mission.participation.progress >= 100">
                        已完成
                      </template>
                      <template v-else>
                        继续任务
                      </template>
                    </template>
                    <template v-else>
                      加入任务
                    </template>
                  </el-button>
                </div>
              </div>
            </div>
            
            <div class="empty-state" v-else>
              <el-icon size="64"><Flag /></el-icon>
              <h3>暂无进行中的任务</h3>
              <p>系统会根据星象能量自动触发任务，请稍后查看</p>
            </div>
          </el-tab-pane>

          <el-tab-pane label="即将开始" name="upcoming">
            <div class="missions-list" v-if="upcomingMissions?.length > 0">
              <div class="mission-card upcoming" v-for="mission in upcomingMissions" :key="mission.id">
                <div class="mission-header">
                  <div class="mission-type-badge upcoming">
                    即将开始
                  </div>
                  <div class="mission-time">
                    <el-icon><Clock /></el-icon>
                    <span>{{ getStartTime(mission.starts_at) }}</span>
                  </div>
                </div>

                <div class="mission-body">
                  <div class="mission-main">
                    <div class="mission-icon upcoming">
                      <el-icon :size="28"><Clock /></el-icon>
                    </div>
                    <div class="mission-info">
                      <h3 class="mission-title">{{ mission.title }}</h3>
                      <p class="mission-desc">{{ mission.description }}</p>
                    </div>
                  </div>

                  <div class="mission-stats">
                    <div class="stat-item">
                      <span class="stat-label">基础奖励</span>
                      <span class="stat-value reward">
                        <el-icon><Star /></el-icon>
                        <span>{{ mission.base_reward }}</span>
                      </span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">预计时长</span>
                      <span class="stat-value">{{ mission.estimated_duration_minutes || 30 }} 分钟</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="empty-state" v-else>
              <el-icon size="64"><Clock /></el-icon>
              <h3>暂无即将开始的任务</h3>
              <p>关注当前星象变化，新任务即将上线</p>
            </div>
          </el-tab-pane>

          <el-tab-pane label="已完成" name="completed">
            <div class="missions-list" v-if="completedMissions?.length > 0">
              <div class="mission-card completed" v-for="mission in completedMissions" :key="mission.id">
                <div class="mission-header">
                  <div class="mission-type-badge completed">
                    已完成
                  </div>
                  <div class="mission-time">
                    <el-icon><Checked /></el-icon>
                    <span>{{ formatDate(mission.participation?.completed_at || mission.ends_at) }}</span>
                  </div>
                </div>

                <div class="mission-body">
                  <div class="mission-main">
                    <div class="mission-icon completed">
                      <el-icon :size="28"><Checked /></el-icon>
                    </div>
                    <div class="mission-info">
                      <h3 class="mission-title">{{ mission.title }}</h3>
                      <p class="mission-desc">{{ mission.description }}</p>
                    </div>
                  </div>

                  <div class="mission-stats">
                    <div class="stat-item">
                      <span class="stat-label">获得奖励</span>
                      <span class="stat-value reward earned">
                        <el-icon><Star /></el-icon>
                        <span>+{{ mission.participation?.reward_earned || mission.base_reward }}</span>
                      </span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">完成进度</span>
                      <span class="stat-value">{{ mission.participation?.progress || 100 }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="empty-state" v-else>
              <el-icon size="64"><Trophy /></el-icon>
              <h3>暂无已完成的任务</h3>
              <p>开始参与任务，获取星尘奖励</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Connection, Clock, Search
} from '@element-plus/icons-vue'
import { energyCommunityApi } from '@/api'

const router = useRouter()

const activeTab = ref('active')
const activeMissions = ref([])
const upcomingMissions = ref([])
const completedMissions = ref([])
const loading = ref(false)
const joiningMission = ref(null)

const getStarStyle = (i) => {
  const left = Math.random() * 100
  const top = Math.random() * 100
  const delay = Math.random() * 5
  return {
    left: `${left}%`,
    top: `${top}%`,
    animationDelay: `${delay}s`
  }
}

const MISSION_TYPE_CONFIG = {
  meditation: { label: '冥想', icon: Moon },
  group_meditation: { label: '集体共修', icon: Connection },
  silent_mode: { label: '静音模式', icon: Bell },
  gratitude: { label: '感恩打卡', icon: Heart },
  focus: { label: '专注模式', icon: Coffee }
}

const DIFFICULTY_CONFIG = {
  easy: { label: '简单', color: '#22c55e' },
  medium: { label: '中等', color: '#f59e0b' },
  hard: { label: '困难', color: '#ef4444' }
}

const getMissionTypeLabel = (type) => MISSION_TYPE_CONFIG[type]?.label || type
const getMissionIcon = (type) => MISSION_TYPE_CONFIG[type]?.icon || Flag
const getDifficultyLabel = (diff) => DIFFICULTY_CONFIG[diff]?.label || '未知'

const getTimeRemaining = (endsAt) => {
  if (!endsAt) return '进行中'
  const end = new Date(endsAt)
  const now = new Date()
  const diff = end - now
  
  if (diff <= 0) return '即将结束'
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
}

const getStartTime = (startsAt) => {
  if (!startsAt) return '即将开始'
  const start = new Date(startsAt)
  const now = new Date()
  const diff = start - now
  
  if (diff <= 0) return '即将开始'
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (hours > 0) return `${hours}小时后开始`
  return `${minutes}分钟后开始`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const parseTriggerConditions = (conditions) => {
  if (!conditions) return ''
  try {
    const parsed = typeof conditions === 'string' ? JSON.parse(conditions) : conditions
    if (parsed.planet && parsed.aspect && parsed.relation) {
      return `${parsed.planet}${parsed.relation}${parsed.aspect}`
    }
    return JSON.stringify(conditions)
  } catch {
    return String(conditions)
  }
}

const getProgressColor = (difficulty) => {
  return DIFFICULTY_CONFIG[difficulty]?.color || '#a78bfa'
}

const loadMissions = async () => {
  loading.value = true
  try {
    const [activeData, upcomingData] = await Promise.all([
      energyCommunityApi.getActiveMissions(20),
      energyCommunityApi.getUpcomingMissions(48, 10)
    ])
    
    activeMissions.value = activeData?.missions || []
    upcomingMissions.value = upcomingData?.missions || []
    
    completedMissions.value = []
  } catch (error) {
    console.error('加载任务失败:', error)
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

const handleMissionAction = async (mission) => {
  if (mission.participation) {
    ElMessage.info('任务进行中，进度已保存')
    return
  }
  
  joiningMission.value = mission.id
  try {
    const result = await energyCommunityApi.joinMission(mission.id)
    
    if (result.success) {
      ElMessage.success('成功加入任务！')
      mission.participation = result.participation
    }
  } catch (error) {
    console.error('加入任务失败:', error)
    ElMessage.error('加入任务失败')
  } finally {
    joiningMission.value = null
  }
}

onMounted(() => {
  loadMissions()
})
</script>

<style scoped lang="scss">
.missions-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
  position: relative;
  overflow-x: hidden;
}

.stars-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.star {
  position: absolute;
  width: 2px;
  height: 2px;
  background: white;
  border-radius: 50%;
  animation: twinkle 3s infinite ease-in-out;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.missions-main {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;

  .header-back {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 16px;
    transition: color 0.2s;

    &:hover {
      color: #a78bfa;
    }
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 16px;

    .title-icon {
      width: 56px;
      height: 56px;
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(34, 197, 94, 0.1));
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #22c55e;
      border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .title-text {
      h1 {
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin: 0 0 4px;
      }

      p {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
      }
    }
  }
}

.tabs-container {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 24px;
}

:deep(.mission-tabs) {
  .el-tabs__header {
    margin-bottom: 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .el-tabs__nav-wrap::after {
    display: none;
  }

  .el-tabs__item {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.5);
    font-weight: 500;
    padding: 0 24px 16px;

    &.is-active {
      color: #a78bfa;
      font-weight: 600;
    }

    &:hover {
      color: rgba(255, 255, 255, 0.8);
    }
  }

  .el-tabs__active-bar {
    background: linear-gradient(90deg, #a78bfa, #f472b6);
    height: 3px;
    border-radius: 2px;
  }
}

.missions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.mission-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s;

  &:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(167, 139, 250, 0.3);
  }

  &.upcoming {
    opacity: 0.8;

    .mission-header,
    .mission-title,
    .mission-desc {
      opacity: 0.8;
    }
  }

  &.completed {
    opacity: 0.9;

    .mission-header,
    .mission-title,
    .mission-desc {
      opacity: 0.9;
    }
  }
}

.mission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .mission-type-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;

    &.meditation { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    &.group_meditation { background: rgba(139, 92, 246, 0.2); color: #a78bfa; }
    &.silent_mode { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    &.gratitude { background: rgba(236, 72, 153, 0.2); color: #ec4899; }
    &.focus { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    &.upcoming { background: rgba(96, 165, 250, 0.2); color: #60a5fa; }
    &.completed { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
  }

  .mission-time {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.mission-body {
  margin-bottom: 16px;
}

.mission-main {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;

  .mission-icon {
    width: 60px;
    height: 60px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.meditation { background: linear-gradient(135deg, rgba(34, 197, 94, 0.25), rgba(34, 197, 94, 0.1)); color: #22c55e; }
    &.group_meditation { background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(139, 92, 246, 0.1)); color: #a78bfa; }
    &.silent_mode { background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(239, 68, 68, 0.1)); color: #ef4444; }
    &.gratitude { background: linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(236, 72, 153, 0.1)); color: #ec4899; }
    &.focus { background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(245, 158, 11, 0.1)); color: #f59e0b; }
    &.upcoming { background: rgba(96, 165, 250, 0.1); color: #60a5fa; }
    &.completed { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
  }

  .mission-info {
    flex: 1;

    .mission-title {
      font-size: 18px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.95);
      margin: 0 0 6px;
    }

    .mission-desc {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0 0 8px;
      line-height: 1.5;
    }

    .mission-triggers {
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 6px 10px;
      background: rgba(167, 139, 250, 0.1);
      border-radius: 8px;
      width: fit-content;

      .trigger-label {
        color: rgba(255, 255, 255, 0.5);
      }

      .trigger-text {
        color: #a78bfa;
        font-weight: 500;
      }
    }
  }
}

.mission-stats {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .stat-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.4);
    }

    .stat-value {
      font-size: 15px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);

      &.reward {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #f59e0b;

        .el-icon {
          font-size: 14px;
        }
      }

      &.earned {
        color: #22c55e;
      }

      &.difficulty {
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 12px;

        &.easy { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
        &.medium { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
        &.hard { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
      }
    }
  }
}

.mission-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);

  .el-progress {
    flex: 1;

    .progress-text {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.6);
    }
  }

  .mission-action-btn {
    min-width: 100px;
    background: linear-gradient(135deg, #a78bfa, #8b5cf6);
    border: none;

    &:hover {
      background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    }

    &:disabled {
      background: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.3);
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.4);

  .el-icon {
    margin-bottom: 16px;
    opacity: 0.5;
  }

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 8px;
  }

  p {
    font-size: 13px;
    margin: 0;
    text-align: center;
  }
}
</style>
