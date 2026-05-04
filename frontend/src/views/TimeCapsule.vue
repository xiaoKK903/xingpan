<template>
  <div class="time-capsule-page">
    <div class="page-header">
      <div class="header-content">
        <div class="page-title-wrapper">
          <span class="page-icon">💫</span>
          <h1 class="page-title">时间胶囊</h1>
        </div>
        <p class="page-subtitle">将此刻的心意封存，等待未来的自己开启</p>
      </div>
      <div class="header-actions" v-if="!isEditMode && !isDetailMode">
        <el-button type="primary" class="btn-create" @click="goToCreate">
          <el-icon><Plus /></el-icon>
          封存新胶囊
        </el-button>
      </div>
    </div>

    <div class="quota-card" v-if="quota && !isEditMode && !isDetailMode">
      <div class="quota-info">
        <div class="quota-icon">📦</div>
        <div class="quota-text">
          <span class="used">{{ quota.total_used_all }}</span>
          <span class="separator">/</span>
          <span class="total">{{ quota.total_available }}</span>
          <span class="label">个胶囊已封存</span>
        </div>
        <div class="quota-progress">
          <el-progress 
            :percentage="quotaPercentage" 
            :show-text="false"
            :color="quotaPercentage > 80 ? '#f59e0b' : '#8b5cf6'"
          />
        </div>
        <el-tag type="warning" v-if="quota.remaining <= 1" class="quota-warning">
          仅剩 {{ quota.remaining }} 个名额
        </el-tag>
        <el-tag type="info" v-else>
          还可创建 {{ quota.remaining }} 个
        </el-tag>
      </div>
    </div>

    <div v-if="isEditMode || isCreateMode" class="form-section">
      <el-card class="form-card">
        <template #header>
          <div class="form-header">
            <span class="form-title">{{ isEditMode ? '编辑时间胶囊' : '封存新胶囊' }}</span>
            <el-button text @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回列表
            </el-button>
          </div>
        </template>

        <el-form
          ref="capsuleFormRef"
          :model="capsuleForm"
          :rules="capsuleRules"
          label-width="100px"
          class="capsule-form"
        >
          <el-form-item label="胶囊标题" prop="title">
            <el-input 
              v-model="capsuleForm.title" 
              placeholder="给胶囊起个名字，比如'致一年后的自己'"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="胶囊内容" prop="content">
            <el-input
              v-model="capsuleForm.content"
              type="textarea"
              :rows="8"
              placeholder="写下你想对未来说的话...\n\n时间会证明一切的价值，此刻的每一句话，都将成为未来珍贵的回忆。"
              maxlength="5000"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="收件对象">
            <el-radio-group v-model="capsuleForm.recipient_type">
              <el-radio value="self">
                <span class="radio-label">
                  <span class="radio-icon">💌</span>
                  写给未来的自己
                </span>
              </el-radio>
              <el-radio value="friend">
                <span class="radio-label">
                  <span class="radio-icon">👥</span>
                  写给指定好友
                </span>
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item 
            label="选择好友" 
            v-if="capsuleForm.recipient_type === 'friend'"
            prop="recipient_user_id"
          >
            <el-select 
              v-model="capsuleForm.recipient_user_id" 
              placeholder="请选择一位好友"
              filterable
              class="full-width"
            >
              <el-option
                v-for="friend in friendsList"
                :key="friend.id"
                :label="friend.username"
                :value="friend.id"
              />
            </el-select>
            <div class="form-tip">
              胶囊将在指定时间发送给该好友，他们将收到一条惊喜的时间胶囊通知
            </div>
          </el-form-item>

          <el-form-item label="开启时间">
            <el-radio-group v-model="capsuleForm.unlock_duration">
              <el-radio value="3months">
                <span class="duration-card">
                  <span class="duration-icon">🌸</span>
                  <span class="duration-text">3个月后</span>
                </span>
              </el-radio>
              <el-radio value="1year">
                <span class="duration-card active">
                  <span class="duration-icon">🌙</span>
                  <span class="duration-text">1年后</span>
                </span>
              </el-radio>
              <el-radio value="3years">
                <span class="duration-card">
                  <span class="duration-icon">✨</span>
                  <span class="duration-text">3年后</span>
                </span>
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="胶囊皮肤">
            <div class="skin-selector">
              <div 
                v-for="skin in availableSkins" 
                :key="skin.skin_key"
                class="skin-item"
                :class="{ 
                  'is-selected': capsuleForm.skin_key === skin.skin_key,
                  'is-locked': skin.is_locked 
                }"
                @click="selectSkin(skin)"
              >
                <div class="skin-preview" :class="'skin-' + skin.skin_key">
                  <span class="skin-emoji">{{ getSkinEmoji(skin.skin_key) }}</span>
                </div>
                <div class="skin-info">
                  <span class="skin-name">{{ skin.name }}</span>
                  <el-tag v-if="skin.is_vip_only" type="warning" size="small" class="skin-tag">
                    VIP专属
                  </el-tag>
                  <el-tag v-else-if="skin.is_premium" type="danger" size="small" class="skin-tag">
                    付费 {{ skin.price }} 星钻
                  </el-tag>
                </div>
              </div>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" @click="submitCapsule" :loading="submitting">
              {{ isEditMode ? '保存修改' : '封存胶囊' }}
            </el-button>
            <el-button size="large" @click="goBack">取消</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div v-else class="list-section">
      <el-tabs v-model="activeTab" class="capsule-tabs" @tab-change="onTabChange">
        <el-tab-pane label="我封存的" name="created">
          <div class="tab-header">
            <div class="filter-buttons">
              <el-radio-group v-model="statusFilter" size="small">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button value="pending">未开启</el-radio-button>
                <el-radio-button value="unlocked">已开启</el-radio-button>
                <el-radio-button value="expired">已过期</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          
          <div v-if="loading" class="loading-container">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span class="loading-text">加载中...</span>
          </div>

          <div v-else-if="createdCapsules.length === 0" class="empty-state">
            <div class="empty-icon">💫</div>
            <h3 class="empty-title">还没有时间胶囊</h3>
            <p class="empty-desc">给未来的自己写一封信，封存此刻的心情与期待</p>
            <el-button type="primary" @click="goToCreate">
              <el-icon><Plus /></el-icon>
              封存第一个胶囊
            </el-button>
          </div>

          <div v-else class="capsule-grid">
            <div 
              v-for="capsule in filteredCreatedCapsules" 
              :key="capsule.id"
              class="capsule-card"
              :class="'skin-' + capsule.skin_key"
              @click="viewCapsuleDetail(capsule)"
            >
              <div class="capsule-preview">
                <span class="capsule-emoji">{{ getSkinEmoji(capsule.skin_key) }}</span>
              </div>
              <div class="capsule-content">
                <h4 class="capsule-title">{{ capsule.title }}</h4>
                <div class="capsule-meta">
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    开启时间: {{ formatDate(capsule.unlock_at) }}
                  </span>
                </div>
                <div class="capsule-status">
                  <el-tag :type="getStatusTagType(capsule.status)" size="small">
                    {{ getStatusText(capsule.status, capsule.is_unlocked) }}
                  </el-tag>
                </div>
              </div>
              <div class="capsule-actions" v-if="capsule.status === 'pending'" @click.stop>
                <el-button text type="primary" size="small" @click="editCapsule(capsule)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button text type="danger" size="small" @click="deleteCapsule(capsule)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="我收到的" name="received">
          <div v-if="loadingReceived" class="loading-container">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span class="loading-text">加载中...</span>
          </div>

          <div v-else-if="receivedCapsules.length === 0" class="empty-state">
            <div class="empty-icon">📬</div>
            <h3 class="empty-title">还没有收到胶囊</h3>
            <p class="empty-desc">邀请好友给你写一封时间胶囊吧</p>
          </div>

          <div v-else class="capsule-grid">
            <div 
              v-for="capsule in receivedCapsules" 
              :key="capsule.id"
              class="capsule-card received"
              :class="'skin-' + capsule.skin_key"
              @click="viewCapsuleDetail(capsule)"
            >
              <div class="capsule-preview">
                <span class="capsule-emoji">{{ getSkinEmoji(capsule.skin_key) }}</span>
              </div>
              <div class="capsule-content">
                <h4 class="capsule-title">{{ capsule.title }}</h4>
                <div class="capsule-meta">
                  <span class="meta-item">
                    <el-icon><User /></el-icon>
                    来自: {{ capsule.sender_username || '匿名' }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    {{ formatDate(capsule.unlock_at) }}
                  </span>
                </div>
                <div class="capsule-status">
                  <el-tag :type="getStatusTagType(capsule.status)" size="small">
                    {{ getStatusText(capsule.status, capsule.is_unlocked) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="通知" name="notifications">
          <div v-if="loadingNotifications" class="loading-container">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span class="loading-text">加载中...</span>
          </div>

          <div v-else-if="notifications.length === 0" class="empty-state">
            <div class="empty-icon">🔔</div>
            <h3 class="empty-title">暂无通知</h3>
            <p class="empty-desc">当有胶囊开启或收到新胶囊时，会在这里显示</p>
          </div>

          <div v-else class="notification-list">
            <div 
              v-for="notification in notifications" 
              :key="notification.id"
              class="notification-item"
              :class="{ 'is-unread': !notification.is_read }"
              @click="markNotificationRead(notification)"
            >
              <div class="notification-icon" :class="notification.notification_type">
                {{ getNotificationIcon(notification.notification_type) }}
              </div>
              <div class="notification-content">
                <h4 class="notification-title">{{ notification.title }}</h4>
                <p class="notification-message">{{ notification.message }}</p>
                <span class="notification-time">{{ formatDate(notification.created_at) }}</span>
              </div>
              <div class="notification-badge" v-if="!notification.is_read"></div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog
      v-model="showDeleteDialog"
      title="确认删除"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="delete-dialog-content">
        <el-icon class="warning-icon"><Warning /></el-icon>
        <p>确定要删除这个时间胶囊吗？</p>
        <p class="delete-hint">删除后将无法恢复，且会释放一个胶囊配额。</p>
      </div>
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete" :loading="deleting">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, ArrowLeft, Calendar, User, Edit, Delete, 
  Loading, Warning, Clock, Lock, Unlock, Message
} from '@element-plus/icons-vue'
import { timeCapsuleApi, vipApi, networkChainApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeTab = ref('created')
const statusFilter = ref('')
const loading = ref(false)
const loadingReceived = ref(false)
const loadingNotifications = ref(false)
const submitting = ref(false)
const deleting = ref(false)

const quota = ref(null)
const createdCapsules = ref([])
const receivedCapsules = ref([])
const notifications = ref([])
const availableSkins = ref([])
const friendsList = ref([])

const capsuleFormRef = ref(null)
const capsuleToDelete = ref(null)
const showDeleteDialog = ref(false)

const isVip = computed(() => userStore.isVip)

const isCreateMode = computed(() => route.name === 'TimeCapsuleCreate')
const isEditMode = computed(() => route.name === 'TimeCapsuleEdit')

const quotaPercentage = computed(() => {
  if (!quota.value || quota.value.total_available === 0) return 0
  return Math.round((quota.value.total_used_all / quota.value.total_available) * 100)
})

const filteredCreatedCapsules = computed(() => {
  if (!statusFilter.value) return createdCapsules.value
  return createdCapsules.value.filter(c => c.status === statusFilter.value)
})

const capsuleForm = reactive({
  title: '',
  content: '',
  recipient_type: 'self',
  recipient_user_id: null,
  unlock_duration: '1year',
  skin_key: 'classic_star'
})

const capsuleRules = {
  title: [
    { required: true, message: '请输入胶囊标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入胶囊内容', trigger: 'blur' },
    { min: 10, max: 5000, message: '内容长度在 10 到 5000 个字符', trigger: 'blur' }
  ],
  recipient_user_id: [
    { 
      required: true, 
      message: '请选择一位好友', 
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (capsuleForm.recipient_type === 'friend' && !value) {
          callback(new Error('请选择一位好友'))
        } else {
          callback()
        }
      }
    }
  ]
}

const skinEmojis = {
  'classic_star': '⭐',
  'nebula_pink': '💗',
  'ocean_blue': '💙',
  'sunset_gold': '🌟',
  'cosmic_vip': '🌌',
  'aurora_vip': '🌈',
  'crystal_premium': '💎',
  'phoenix_legend': '🔥'
}

function getSkinEmoji(skinKey) {
  return skinEmojis[skinKey] || '⭐'
}

function getStatusTagType(status) {
  const types = {
    'pending': 'info',
    'unlocked': 'success',
    'opened': 'success',
    'expired': 'warning'
  }
  return types[status] || 'info'
}

function getStatusText(status, isUnlocked) {
  const texts = {
    'pending': isUnlocked ? '已开启' : '未开启',
    'unlocked': '已开启',
    'opened': '已查看',
    'expired': '已过期'
  }
  return texts[status] || status
}

function getNotificationIcon(type) {
  const icons = {
    'capsule_unlocked': '🔓',
    'capsule_received': '📬',
    'capsule_expired': '⏰',
    'capsule_opened': '📖'
  }
  return icons[type] || '🔔'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

async function loadQuota() {
  try {
    quota.value = await timeCapsuleApi.getQuota()
  } catch (error) {
    console.error('加载配额失败:', error)
    ElMessage.error('加载配额失败，请稍后重试')
  }
}

async function loadSkins() {
  try {
    const response = await timeCapsuleApi.getSkins()
    availableSkins.value = response.skins || []
  } catch (error) {
    console.error('加载皮肤失败:', error)
    ElMessage.error('加载皮肤列表失败，请稍后重试')
    availableSkins.value = [
      { skin_key: 'classic_star', name: '经典星盘', is_vip_only: false, is_premium: false, is_locked: false },
      { skin_key: 'nebula_pink', name: '星云粉', is_vip_only: false, is_premium: false, is_locked: false },
      { skin_key: 'ocean_blue', name: '深海蓝', is_vip_only: false, is_premium: false, is_locked: false },
      { skin_key: 'sunset_gold', name: '落日金', is_vip_only: false, is_premium: false, is_locked: false }
    ]
  }
}

async function loadCreatedCapsules() {
  loading.value = true
  try {
    const response = await timeCapsuleApi.getList({ limit: 50 })
    createdCapsules.value = response.capsules || []
  } catch (error) {
    console.error('加载我创建的胶囊失败:', error)
    ElMessage.error('加载胶囊列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function loadReceivedCapsules() {
  loadingReceived.value = true
  try {
    const response = await timeCapsuleApi.getReceived({ limit: 50 })
    receivedCapsules.value = response.capsules || []
  } catch (error) {
    console.error('加载我收到的胶囊失败:', error)
    ElMessage.error('加载收到的胶囊失败，请稍后重试')
  } finally {
    loadingReceived.value = false
  }
}

async function loadNotifications() {
  loadingNotifications.value = true
  try {
    const response = await timeCapsuleApi.getNotifications({ limit: 50 })
    notifications.value = response.notifications || []
  } catch (error) {
    console.error('加载通知失败:', error)
    ElMessage.error('加载通知失败，请稍后重试')
  } finally {
    loadingNotifications.value = false
  }
}

async function loadFriends() {
  try {
    const response = await networkChainApi.getRecommendations('emotional')
    const recommendations = response.recommendations || []
    friendsList.value = recommendations.map(r => ({
      id: r.user_id || r.id,
      username: r.username || r.target_username || `用户 ${r.user_id || r.id}`
    }))
  } catch (error) {
    console.error('加载推荐用户失败:', error)
    ElMessage.error('加载好友列表失败，请稍后重试')
    friendsList.value = []
  }
}

function selectSkin(skin) {
  if (skin.is_locked) {
    if (skin.is_vip_only) {
      ElMessage.warning('该皮肤为VIP专属，开通VIP后即可使用')
    } else if (skin.is_premium) {
      ElMessage.warning(`该皮肤为付费皮肤，需要 ${skin.price} 星钻购买`)
    }
    return
  }
  capsuleForm.skin_key = skin.skin_key
}

function resetForm() {
  capsuleForm.title = ''
  capsuleForm.content = ''
  capsuleForm.recipient_type = 'self'
  capsuleForm.recipient_user_id = null
  capsuleForm.unlock_duration = '1year'
  capsuleForm.skin_key = 'classic_star'
  capsuleFormRef.value?.resetFields()
}

async function submitCapsule() {
  const valid = await capsuleFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = { ...capsuleForm }
    
    if (data.recipient_type === 'self') {
      delete data.recipient_user_id
    } else if (data.recipient_user_id === null || data.recipient_user_id === undefined) {
      delete data.recipient_user_id
    }
    
    if (isEditMode.value) {
      const capsuleId = route.params.id
      if (!capsuleId || capsuleId === 'undefined' || capsuleId === 'null') {
        ElMessage.error('胶囊ID无效')
        return
      }
      await timeCapsuleApi.update(capsuleId, data)
      ElMessage.success('胶囊已更新')
    } else {
      await timeCapsuleApi.create(data)
      ElMessage.success('胶囊已封存！时间会守护这份心意')
    }
    
    router.push('/time-capsule')
  } catch (error) {
    console.error('提交胶囊失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

function viewCapsuleDetail(capsule) {
  router.push(`/time-capsule/detail/${capsule.id}`)
}

function editCapsule(capsule) {
  router.push(`/time-capsule/edit/${capsule.id}`)
}

function deleteCapsule(capsule) {
  capsuleToDelete.value = capsule
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (!capsuleToDelete.value) return
  
  deleting.value = true
  try {
    await timeCapsuleApi.delete(capsuleToDelete.value.id)
    ElMessage.success('胶囊已删除')
    showDeleteDialog.value = false
    capsuleToDelete.value = null
    await loadCreatedCapsules()
    await loadQuota()
  } catch (error) {
    console.error('删除胶囊失败:', error)
    ElMessage.error('删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

async function markNotificationRead(notification) {
  if (notification.is_read) return
  
  try {
    await timeCapsuleApi.markNotificationRead(notification.id)
    notification.is_read = true
  } catch (error) {
    console.error('标记通知已读失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  }
}

async function loadCapsuleForEdit() {
  if (!isEditMode.value) return
  
  const capsuleId = route.params.id
  if (!capsuleId || capsuleId === 'undefined' || capsuleId === 'null') {
    console.warn('无效的胶囊 ID:', capsuleId)
    router.push('/time-capsule')
    return
  }
  
  try {
    const response = await timeCapsuleApi.getDetail(capsuleId)
    let capsule = null
    if (response && response.capsule) {
      capsule = response.capsule
    } else {
      capsule = response
    }
    
    if (capsule) {
      capsuleForm.title = capsule.title
      capsuleForm.content = capsule.content
      capsuleForm.recipient_type = capsule.recipient_type
      capsuleForm.recipient_user_id = capsule.recipient_user_id
      capsuleForm.unlock_duration = capsule.unlock_duration
      capsuleForm.skin_key = capsule.skin_key || 'classic_star'
    }
  } catch (error) {
    console.error('加载胶囊详情失败:', error)
    ElMessage.error('胶囊不存在或已被删除')
    router.push('/time-capsule')
  }
}

async function handleRouteChange() {
  if (isEditMode.value) {
    await Promise.all([
      loadSkins(),
      loadFriends()
    ])
    await loadCapsuleForEdit()
  } else if (isCreateMode.value) {
    resetForm()
    await Promise.all([
      loadQuota(),
      loadSkins(),
      loadFriends()
    ])
  } else {
    await Promise.all([
      loadQuota(),
      loadCreatedCapsules(),
      loadSkins()
    ])
  }
}

function onTabChange(tabName) {
  if (tabName === 'created') {
    loadCreatedCapsules()
  } else if (tabName === 'received') {
    loadReceivedCapsules()
  } else if (tabName === 'notifications') {
    loadNotifications()
  }
}

function goToCreate() {
  if (quota.value && quota.value.remaining <= 0) {
    ElMessage.warning('胶囊配额已满，请升级VIP获取更多名额')
    return
  }
  router.push('/time-capsule/create')
}

function goBack() {
  router.push('/time-capsule')
}

watch(
  () => route.name,
  () => {
    handleRouteChange()
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.time-capsule-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content {
  .page-title-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }
  
  .page-icon {
    font-size: 2rem;
  }
  
  .page-title {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .page-subtitle {
    margin: 0;
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.btn-create {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  font-weight: 600;
  
  &:hover {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
  }
}

.quota-card {
  background: linear-gradient(145deg, rgba(30, 30, 60, 0.95), rgba(20, 20, 50, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  padding: 20px;
  margin-bottom: 24px;
  
  .quota-info {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  
  .quota-icon {
    font-size: 2rem;
  }
  
  .quota-text {
    .used {
      font-size: 1.5rem;
      font-weight: 700;
      color: #a78bfa;
    }
    
    .separator {
      color: rgba(255, 255, 255, 0.4);
      margin: 0 4px;
    }
    
    .total {
      font-size: 1.5rem;
      font-weight: 700;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .label {
      margin-left: 8px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
  
  .quota-progress {
    flex: 1;
    min-width: 200px;
  }
  
  .quota-warning {
    background: rgba(245, 158, 11, 0.1) !important;
    border-color: rgba(245, 158, 11, 0.3) !important;
    color: #f59e0b !important;
  }
}

.form-section {
  .form-card {
    background: linear-gradient(145deg, rgba(30, 30, 60, 0.95), rgba(20, 20, 50, 0.98));
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
    
    :deep(.el-card__header) {
      border-bottom-color: rgba(139, 92, 246, 0.15);
    }
  }
  
  .form-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .form-title {
      font-size: 1.2rem;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
  }
}

.capsule-form {
  max-width: 800px;
  
  :deep(.el-form-item__label) {
    color: rgba(255, 255, 255, 0.85);
  }
  
  :deep(.el-textarea__inner),
  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.9);
    
    &:hover, &:focus {
      border-color: rgba(139, 92, 246, 0.5);
    }
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
  }
  
  .radio-label {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .radio-icon {
      font-size: 1.2rem;
    }
  }
  
  .form-tip {
    margin-top: 8px;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.4);
  }
  
  .duration-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 12px 20px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
    
    .duration-icon {
      font-size: 1.5rem;
    }
    
    .duration-text {
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.7);
    }
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4);
      background: rgba(139, 92, 246, 0.1);
    }
    
    &.active {
      border-color: rgba(139, 92, 246, 0.5);
      background: rgba(139, 92, 246, 0.15);
    }
  }
  
  .skin-selector {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .skin-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border-radius: 12px;
    border: 2px solid transparent;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    
    &:hover {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &.is-selected {
      border-color: #8b5cf6;
      background: rgba(139, 92, 246, 0.15);
    }
    
    &.is-locked {
      opacity: 0.6;
      
      &:after {
        content: '🔒';
        position: absolute;
        top: 4px;
        right: 4px;
        font-size: 0.8rem;
      }
    }
  }
  
  .skin-preview {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.15));
    border: 1px solid rgba(139, 92, 246, 0.3);
  }
  
  .skin-emoji {
    font-size: 1.8rem;
  }
  
  .skin-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
  
  .skin-name {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .skin-tag {
    font-size: 0.7rem;
  }
}

.list-section {
  .capsule-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 20px;
      border-bottom-color: rgba(139, 92, 246, 0.15);
    }
    
    :deep(.el-tabs__item) {
      color: rgba(255, 255, 255, 0.5);
      
      &.is-active {
        color: #a78bfa;
      }
      
      &:hover {
        color: rgba(255, 255, 255, 0.8);
      }
    }
    
    :deep(.el-tabs__active-bar) {
      background-color: #8b5cf6;
    }
  }
  
  .tab-header {
    margin-bottom: 16px;
    
    .filter-buttons {
      :deep(.el-radio-button__inner) {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.7);
        
        &:hover {
          color: #a78bfa;
        }
      }
      
      :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        border-color: #8b5cf6;
      }
    }
  }
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  
  .loading-icon {
    font-size: 2rem;
    color: #8b5cf6;
    animation: spin 1s linear infinite;
  }
  
  .loading-text {
    margin-top: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
  }
  
  .empty-title {
    margin: 0 0 8px;
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .empty-desc {
    margin: 0 0 20px;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.capsule-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.capsule-card {
  background: linear-gradient(145deg, rgba(30, 30, 60, 0.95), rgba(20, 20, 50, 0.98));
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-4px);
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
  }
  
  &.received {
    border-color: rgba(34, 197, 94, 0.2);
    
    &:hover {
      border-color: rgba(34, 197, 94, 0.4);
      box-shadow: 0 8px 30px rgba(34, 197, 94, 0.1);
    }
  }
}

.capsule-preview {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(139, 92, 246, 0.3);
  margin-bottom: 12px;
}

.capsule-emoji {
  font-size: 2rem;
}

.capsule-content {
  .capsule-title {
    margin: 0 0 8px;
    font-size: 1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .capsule-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 12px;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .capsule-status {
    margin-bottom: 12px;
  }
}

.capsule-actions {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(145deg, rgba(30, 30, 60, 0.95), rgba(20, 20, 50, 0.98));
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
  }
  
  &.is-unread {
    background: linear-gradient(145deg, rgba(139, 92, 246, 0.15), rgba(20, 20, 50, 0.98));
    border-color: rgba(139, 92, 246, 0.3);
  }
}

.notification-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
  
  .notification-title {
    margin: 0 0 4px;
    font-size: 0.95rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .notification-message {
    margin: 0 0 8px;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .notification-time {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
  }
}

.notification-badge {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8b5cf6;
  flex-shrink: 0;
}

.delete-dialog-content {
  text-align: center;
  
  .warning-icon {
    font-size: 3rem;
    color: #f59e0b;
    margin-bottom: 16px;
  }
  
  p {
    margin: 8px 0;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .delete-hint {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.skin-classic_star .capsule-preview,
.skin-classic_star .skin-preview {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.15));
  border-color: rgba(251, 191, 36, 0.3);
}

.skin-nebula_pink .capsule-preview,
.skin-nebula_pink .skin-preview {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(219, 39, 119, 0.15));
  border-color: rgba(236, 72, 153, 0.3);
}

.skin-ocean_blue .capsule-preview,
.skin-ocean_blue .skin-preview {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.15));
  border-color: rgba(59, 130, 246, 0.3);
}

.skin-sunset_gold .capsule-preview,
.skin-sunset_gold .skin-preview {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.2), rgba(249, 115, 22, 0.15));
  border-color: rgba(251, 146, 60, 0.3);
}

.skin-cosmic_vip .capsule-preview,
.skin-cosmic_vip .skin-preview {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.25));
  border-color: rgba(139, 92, 246, 0.4);
}

.skin-aurora_vip .capsule-preview,
.skin-aurora_vip .skin-preview {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.25), rgba(59, 130, 246, 0.2));
  border-color: rgba(34, 197, 94, 0.35);
}

.skin-crystal_premium .capsule-preview,
.skin-crystal_premium .skin-preview {
  background: linear-gradient(135deg, rgba(147, 197, 253, 0.3), rgba(196, 181, 253, 0.25));
  border-color: rgba(147, 197, 253, 0.4);
}

.skin-phoenix_legend .capsule-preview,
.skin-phoenix_legend .skin-preview {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(251, 146, 60, 0.25));
  border-color: rgba(239, 68, 68, 0.4);
}

@media (max-width: 768px) {
  .time-capsule-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .capsule-grid {
    grid-template-columns: 1fr;
  }
  
  .skin-selector {
    justify-content: center;
  }
}
</style>
