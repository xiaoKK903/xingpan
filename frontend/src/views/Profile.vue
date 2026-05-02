<template>
  <div class="profile-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="user-card">
          <div class="user-info">
            <div class="avatar">
              <el-icon size="64" color="#409eff"><UserFilled /></el-icon>
            </div>
            <div class="username">{{ userStore.username }}</div>
            <el-tag type="primary">普通用户</el-tag>
          </div>
          <el-divider />
          <div class="stats">
            <div class="stat-item">
              <div class="stat-value">{{ conversationsCount }}</div>
              <div class="stat-label">会话数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ messagesCount }}</div>
              <div class="stat-label">消息数</div>
            </div>
          </div>
          
          <el-divider />
          
          <div class="feature-entrances">
            <div class="quest-entrance network-chain-entrance">
              <div class="entrance-content" @click="goToNetworkChain">
                <div class="entrance-icon">🌐</div>
                <div class="entrance-info">
                  <h5>星盘人脉链</h5>
                  <p>发现与你能量共鸣的人脉</p>
                </div>
                <div class="entrance-arrow">
                  <span class="arrow">→</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <el-card class="settings-card">
          <template #header>
            <span class="card-title">个人设置</span>
          </template>
          
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="100px"
          >
            <el-form-item label="用户名">
              <el-input v-model="userStore.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateProfile" :loading="updating">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <div class="password-section">
            <h4>修改密码</h4>
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="120px"
            >
              <el-form-item label="当前密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  show-password
                  placeholder="请输入当前密码"
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  show-password
                  placeholder="请输入新密码"
                />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="请再次输入新密码"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="updatePassword" :loading="changingPassword">
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { conversationApi, messageApi } from '@/api'

const userStore = useUserStore()
const router = useRouter()

const isLoggedIn = computed(() => userStore.isLoggedIn || !!localStorage.getItem('token'))

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const updating = ref(false)
const changingPassword = ref(false)
const conversationsCount = ref(0)
const messagesCount = ref(0)

const profileForm = reactive({
  email: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const profileRules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const loadStats = async () => {
  try {
    const [convRes, msgRes] = await Promise.all([
      conversationApi.getList({ limit: 1 }),
      messageApi.getByConversationId(0, { limit: 1 }).catch(() => ({ total: 0 }))
    ])
    
    conversationsCount.value = convRes.total || 0
    
    let totalMessages = 0
    const convList = await conversationApi.getList({ limit: 100 })
    
    for (const conv of convList.items || []) {
      try {
        const msgRes = await messageApi.getByConversationId(conv.id, { limit: 1 })
        totalMessages += msgRes.total || 0
      } catch (e) {
        // ignore
      }
    }
    
    messagesCount.value = totalMessages
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const updateProfile = async () => {
  const valid = await profileFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  updating.value = true
  try {
    await userStore.updateProfile({ email: profileForm.email })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('更新个人信息失败:', error)
  } finally {
    updating.value = false
  }
}

const updatePassword = async () => {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  changingPassword.value = true
  try {
    ElMessage.info('密码修改功能需要后端支持，当前版本暂不提供')
  } catch (error) {
    console.error('修改密码失败:', error)
  } finally {
    changingPassword.value = false
  }
}

function goToNetworkChain() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再查看星盘人脉链')
    router.push({ path: '/login', query: { redirect: '/network-chain' } })
    return
  }
  router.push('/network-chain')
}

onMounted(() => {
  profileForm.email = userStore.email || ''
  loadStats()
})
</script>

<style lang="scss" scoped>
.profile-container {
  .user-card {
    background: rgba(20, 20, 50, 0.8) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    border-radius: 16px !important;
    box-shadow: 
      0 0 30px rgba(139, 92, 246, 0.06),
      0 0 60px rgba(139, 92, 246, 0.03),
      0 8px 32px rgba(0, 0, 0, 0.25);
    
    .user-info {
      text-align: center;
      padding: 20px 0;
      
      .avatar {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%) !important;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 16px;
        box-shadow: 0 6px 25px rgba(139, 92, 246, 0.35);
      }
      
      .username {
        font-size: 20px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.95) !important;
        margin-bottom: 12px;
      }
    }
    
    :deep(.el-divider) {
      --el-border-color: rgba(139, 92, 246, 0.15) !important;
    }
    
    .stats {
      display: flex;
      justify-content: space-around;
      
      .stat-item {
        text-align: center;
        
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .stat-label {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.5) !important;
          margin-top: 4px;
        }
      }
    }
    
    .feature-entrances {
      margin-top: 8px;
    }
    
    .quest-entrance {
      margin-top: 8px;
    }
    
    .entrance-content {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px;
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%);
      border-radius: 10px;
      border: 1px solid rgba(34, 197, 94, 0.25);
      transition: all 0.3s ease;
      cursor: pointer;
    }
    
    .entrance-content:hover {
      border-color: rgba(34, 197, 94, 0.4);
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(16, 185, 129, 0.2) 100%);
      transform: translateY(-1px);
    }
    
    .entrance-icon {
      font-size: 1.5rem;
    }
    
    .entrance-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    
    .entrance-info h5 {
      margin: 0;
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.9);
      font-weight: 600;
    }
    
    .entrance-info p {
      margin: 0;
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.5);
    }
    
    .entrance-arrow {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .arrow {
      font-size: 0.9rem;
      color: #22c55e;
      transition: transform 0.3s ease;
    }
    
    .entrance-content:hover .arrow {
      transform: translateX(2px);
    }
  }
  
  .settings-card {
    background: rgba(20, 20, 50, 0.8) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    border-radius: 16px !important;
    box-shadow: 
      0 0 30px rgba(139, 92, 246, 0.06),
      0 0 60px rgba(139, 92, 246, 0.03),
      0 8px 32px rgba(0, 0, 0, 0.25);
    
    :deep(.el-card__header) {
      border-bottom: 1px solid rgba(139, 92, 246, 0.15) !important;
    }
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.95) !important;
    }
    
    :deep(.el-form-item__label) {
      color: rgba(255, 255, 255, 0.85) !important;
    }
    
    :deep(.el-divider) {
      --el-border-color: rgba(139, 92, 246, 0.15) !important;
    }
    
    .password-section {
      h4 {
        margin-bottom: 20px 0;
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 15px;
        font-weight: 600;
      }
    }
  }
}
</style>
