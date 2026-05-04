<template>
  <el-dialog
    v-model="visible"
    title="🌟 新手成长任务"
    width="680px"
    class="growth-task-popup"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @closed="handleClosed"
  >
    <div class="popup-content">
      <div class="welcome-section">
        <div class="welcome-icon">🎉</div>
        <div class="welcome-text">
          <h3>欢迎来到星盘世界！</h3>
          <p>完成以下任务，获取丰厚奖励，开启您的占星之旅</p>
        </div>
      </div>
      
      <div class="progress-overview">
        <div class="progress-info">
          <span class="progress-text">任务进度</span>
          <span class="progress-count">{{ completedCount }}/{{ tasks.length }}</span>
        </div>
        <el-progress 
          :percentage="progressPercent" 
          :color="progressColor"
          :stroke-width="8"
        />
      </div>
      
      <div class="task-list">
        <div 
          v-for="task in tasks" 
          :key="task.id || task.task_key"
          class="task-card"
          :class="getTaskCardClass(task)"
        >
          <div class="task-icon">
            <span>{{ task.icon || '📋' }}</span>
          </div>
          
          <div class="task-info">
            <h4 class="task-title">
              {{ task.title }}
              <el-tag v-if="isTaskCompleted(task)" type="success" size="small" effect="dark">
                已完成
              </el-tag>
              <el-tag v-else-if="isTaskClaimed(task)" type="info" size="small" effect="dark">
                已领取
              </el-tag>
              <el-tag v-else type="warning" size="small" effect="plain">
                进行中
              </el-tag>
            </h4>
            <p class="task-description">{{ task.short_description || task.description }}</p>
            
            <div class="task-progress" v-if="!isTaskClaimed(task)">
              <el-progress 
                :percentage="task.progress_percent || 0" 
                :stroke-width="4"
                :status="isTaskCompleted(task) ? 'success' : ''"
                style="width: 150px; margin-right: 12px;"
              />
              <span class="progress-text-small">
                {{ task.progress_current || 0 }}/{{ task.progress_target || 1 }}
              </span>
            </div>
          </div>
          
          <div class="task-action">
            <div class="reward-info">
              <span class="reward-icon">🎁</span>
              <span class="reward-text">{{ task.reward_name || task.reward_amount }}</span>
            </div>
            
            <el-button 
              v-if="isTaskCompleted(task) && !isTaskClaimed(task)"
              type="primary" 
              size="small"
              :loading="claimingTaskId === task.id"
              @click="claimReward(task)"
            >
              领取奖励
            </el-button>
            
            <el-button 
              v-else-if="isTaskClaimed(task)"
              type="success" 
              size="small"
              disabled
            >
              已领取
            </el-button>
            
            <el-button 
              v-else
              type="primary" 
              size="small"
              plain
              @click="goToTask(task)"
            >
              去完成
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="tips-section">
        <el-alert
          title="💡 小贴士"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <p>• 完成所有任务可获得丰厚奖励</p>
            <p>• 任务完成后奖励会自动发放到您的账户</p>
            <p>• 点击"去完成"按钮可直接跳转到任务页面</p>
          </template>
        </el-alert>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleClose" class="skip-btn">
        稍后查看
      </el-button>
      <el-button type="primary" @click="handleClose" class="confirm-btn">
        我知道了
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { growthTasksApi } from '@/api'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'closed'])

const router = useRouter()
const userStore = useUserStore()

const visible = ref(false)
const tasks = ref([])
const claimingTaskId = ref(null)
const loading = ref(false)

const completedCount = computed(() => {
  return tasks.value.filter(t => isTaskCompleted(t) || isTaskClaimed(t)).length
})

const progressPercent = computed(() => {
  if (tasks.value.length === 0) return 0
  return Math.round((completedCount.value / tasks.value.length) * 100)
})

const progressColor = computed(() => {
  if (progressPercent.value >= 100) return '#10b981'
  if (progressPercent.value >= 50) return '#f59e0b'
  return '#8b5cf6'
})

function isTaskCompleted(task) {
  return task.status === 'completed'
}

function isTaskClaimed(task) {
  return task.status === 'claimed'
}

function getTaskCardClass(task) {
  if (isTaskClaimed(task)) return 'task-card--claimed'
  if (isTaskCompleted(task)) return 'task-card--completed'
  return ''
}

async function loadTasks() {
  try {
    loading.value = true
    const response = await growthTasksApi.getMyTasks()
    tasks.value = response || []
  } catch (error) {
    console.error('加载任务失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

async function claimReward(task) {
  try {
    claimingTaskId.value = task.id
    const response = await growthTasksApi.claimReward(task.id)
    ElMessage.success('奖励领取成功！')
    
    task.status = 'claimed'
    task.reward_claimed = true
  } catch (error) {
    console.error('领取奖励失败:', error)
    ElMessage.error('领取奖励失败，请稍后重试')
  } finally {
    claimingTaskId.value = null
  }
}

function goToTask(task) {
  const taskType = task.task_type || task.task_key
  
  const routeMap = {
    'complete_chart': '/astro',
    'complete_synastry': '/synastry',
    'join_group': '/group-matrix',
    'daily_checkin': null,
    'first_share': '/my-charts'
  }
  
  const targetPath = routeMap[taskType]
  if (targetPath) {
    router.push(targetPath)
  } else {
    ElMessage.info('请继续探索，完成更多任务')
  }
  
  handleClose()
}

function handleClose() {
  visible.value = false
  emit('update:modelValue', false)
}

function handleClosed() {
  emit('closed')
}

watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal
    if (newVal) {
      loadTasks()
    }
  }
)

onMounted(() => {
  visible.value = props.modelValue
  if (visible.value) {
    loadTasks()
  }
})
</script>

<style lang="scss" scoped>
.growth-task-popup {
  :deep(.el-dialog) {
    border-radius: 16px;
    overflow: hidden;
    
    .el-dialog__header {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
      padding: 20px 24px;
      margin: 0;
      
      .el-dialog__title {
        font-size: 18px;
        font-weight: 600;
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
    
    .el-dialog__body {
      padding: 0;
    }
    
    .el-dialog__footer {
      background: #fafafa;
      padding: 16px 24px;
      border-top: 1px solid #f0f0f0;
    }
  }
}

.popup-content {
  max-height: 500px;
  overflow-y: auto;
  padding: 0;
}

.welcome-section {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, transparent 100%);
  
  .welcome-icon {
    width: 56px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
    border-radius: 16px;
    font-size: 28px;
  }
  
  .welcome-text {
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 4px 0;
    }
    
    p {
      font-size: 14px;
      color: #6b7280;
      margin: 0;
    }
  }
}

.progress-overview {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  
  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    
    .progress-text {
      font-size: 14px;
      font-weight: 500;
      color: #374151;
    }
    
    .progress-count {
      font-size: 14px;
      font-weight: 600;
      color: #8b5cf6;
    }
  }
}

.task-list {
  padding: 16px 24px;
}

.task-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  &--completed {
    background: rgba(16, 185, 129, 0.05);
    border-color: rgba(16, 185, 129, 0.2);
  }
  
  &--claimed {
    background: rgba(107, 114, 128, 0.03);
    border-color: rgba(107, 114, 128, 0.1);
    opacity: 0.8;
  }
  
  .task-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
    border-radius: 12px;
    font-size: 24px;
    flex-shrink: 0;
  }
  
  .task-info {
    flex: 1;
    min-width: 0;
    
    .task-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 4px 0;
      
      .el-tag {
        font-size: 11px;
        height: 22px;
        line-height: 20px;
      }
    }
    
    .task-description {
      font-size: 13px;
      color: #6b7280;
      margin: 0 0 8px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .task-progress {
      display: flex;
      align-items: center;
      
      .progress-text-small {
        font-size: 12px;
        color: #9ca3af;
        flex-shrink: 0;
      }
    }
  }
  
  .task-action {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
    flex-shrink: 0;
    
    .reward-info {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #8b5cf6;
      
      .reward-icon {
        font-size: 14px;
      }
      
      .reward-text {
        font-weight: 500;
      }
    }
  }
}

.tips-section {
  padding: 0 24px 24px 24px;
  
  :deep(.el-alert) {
    border-radius: 12px;
    border: none;
    
    .el-alert__title {
      font-size: 14px;
      font-weight: 600;
    }
    
    .el-alert__description {
      font-size: 13px;
      margin-top: 4px;
      
      p {
        margin: 4px 0;
        line-height: 1.6;
      }
    }
  }
}

.skip-btn {
  color: #9ca3af;
  
  &:hover {
    color: #6b7280;
  }
}

.confirm-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  
  &:hover {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
  }
}
</style>
