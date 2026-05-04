<template>
  <el-dialog
    v-model="dialogVisibleModel"
    width="520px"
    center
    :close-on-click-modal="false"
    class="reward-share-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <el-icon size="24" color="#a78bfa"><Present /></el-icon>
        <span class="dialog-title">分享邀请得奖励</span>
      </div>
    </template>

    <div class="reward-share-content">
      <div class="reward-intro">
        <p class="intro-text">
          合盘卡牌已生成！分享给好友，双方都能获得丰厚奖励！
        </p>
      </div>

      <div class="reward-stages">
        <div class="stage-card">
          <div class="stage-header">
            <span class="stage-badge stage-1">1</span>
            <span class="stage-title">分享邀请</span>
          </div>
          <p class="stage-desc">分享 App 给好友，好友通过你的邀请码注册</p>
          <div class="stage-reward">
            <el-tag type="warning" effect="dark" size="small">双方各得 50 星元碎片</el-tag>
          </div>
        </div>

        <div class="stage-arrow">
          <el-icon size="20" color="#a78bfa"><ArrowRight /></el-icon>
        </div>

        <div class="stage-card">
          <div class="stage-header">
            <span class="stage-badge stage-2">2</span>
            <span class="stage-title">完成星盘</span>
          </div>
          <p class="stage-desc">好友注册后保存自己的第一个星盘</p>
          <div class="stage-reward">
            <el-tag type="primary" effect="dark" size="small">邀请人：1 张星图盲盒券</el-tag>
            <el-tag type="success" effect="dark" size="small">被邀请人：3 天会员体验</el-tag>
          </div>
        </div>

        <div class="stage-arrow">
          <el-icon size="20" color="#a78bfa"><ArrowRight /></el-icon>
        </div>

        <div class="stage-card">
          <div class="stage-header">
            <span class="stage-badge stage-3">3</span>
            <span class="stage-title">首次付费</span>
          </div>
          <p class="stage-desc">好友首次任意付费消费</p>
          <div class="stage-reward">
            <el-tag type="danger" effect="dark" size="small">邀请人：付费金额 20% 返利</el-tag>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="share-options">
        <h4 class="share-title">选择分享方式</h4>

        <div class="share-option-item">
          <div class="option-label">
            <el-icon size="18"><User /></el-icon>
            <span>我的邀请码</span>
          </div>
          <div class="option-content">
            <div class="invite-code-display" :class="inviteCodeStatusClass">
              <span class="code-text" v-if="inviteCodeStatus === 'loading'">加载中...</span>
              <span class="code-text" v-else-if="inviteCodeStatus === 'error'">获取失败</span>
              <span class="code-text" v-else>{{ inviteCode?.invite_code }}</span>
            </div>
            <el-button 
              type="primary" 
              size="small" 
              :icon="CopyDocument"
              @click="handleCopyInviteCode"
              :disabled="inviteCodeStatus !== 'success'"
            >
              {{ localInviteCodeCopied ? '已复制' : '复制' }}
            </el-button>
          </div>
        </div>

        <div class="share-option-item">
          <div class="option-label">
            <el-icon size="18"><Link /></el-icon>
            <span>邀请链接</span>
          </div>
          <div class="option-content">
            <el-input 
              :model-value="inviteLink" 
              readonly 
              placeholder="加载中..."
              class="link-input"
            />
            <el-button 
              type="success" 
              size="small" 
              :icon="Share"
              @click="handleCopyInviteLink"
            >
              {{ localInviteLinkCopied ? '已复制' : '复制链接' }}
            </el-button>
          </div>
        </div>

        <div class="share-option-item" v-if="shareSynastryLink">
          <div class="option-label">
            <el-icon size="18"><Connection /></el-icon>
            <span>合盘报告链接</span>
          </div>
          <div class="option-content">
            <el-input 
              :model-value="shareSynastryLink" 
              readonly 
              class="link-input"
            />
            <el-button 
              type="info" 
              size="small" 
              :icon="Share"
              @click="handleCopySynastryShareLink"
            >
              {{ localSynastryCopied ? '已复制' : '复制链接' }}
            </el-button>
          </div>
        </div>
      </div>

      <div class="share-tips-box">
        <el-icon size="16" color="#a78bfa"><InfoFilled /></el-icon>
        <span class="tips-text">
          每位好友只能使用一个邀请码；同IP设备重复注册可能被判定为刷邀请
        </span>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose" size="large">
        稍后再说
      </el-button>
      <el-button 
        type="primary" 
        size="large"
        :icon="Share"
        @click="handleQuickShare"
      >
        立即分享邀请
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Present, ArrowRight, User, CopyDocument, Link, Share, Connection, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  inviteCode: {
    type: Object,
    default: null
  },
  inviteLink: {
    type: String,
    default: ''
  },
  shareSynastryLink: {
    type: String,
    default: ''
  },
  loadingInviteCode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:modelValue',
  'copyInviteCode',
  'copyInviteLink',
  'copySynastryShareLink'
])

const localInviteCodeCopied = ref(false)
const localInviteLinkCopied = ref(false)
const localSynastryCopied = ref(false)

const inviteCodeStatus = computed(() => {
  if (props.loadingInviteCode) {
    return 'loading'
  }
  if (props.inviteCode?.invite_code) {
    return 'success'
  }
  return 'error'
})

const inviteCodeStatusClass = computed(() => {
  if (inviteCodeStatus.value === 'loading') {
    return 'status-loading'
  }
  if (inviteCodeStatus.value === 'error') {
    return 'status-error'
  }
  return 'status-success'
})

const dialogVisibleModel = computed({
  get: () => props.modelValue,
  set: (value) => {
    if (!value) {
      handleClose()
    }
  }
})

function resetAllStates() {
  localInviteCodeCopied.value = false
  localInviteLinkCopied.value = false
  localSynastryCopied.value = false
}

function handleClose() {
  resetAllStates()
  emit('update:modelValue', false)
}

function handleCopyInviteCode() {
  if (localInviteCodeCopied.value || inviteCodeStatus.value !== 'success') return
  localInviteCodeCopied.value = true
  emit('copyInviteCode', props.inviteCode?.invite_code)
  setTimeout(() => {
    localInviteCodeCopied.value = false
  }, 2000)
}

function handleCopyInviteLink() {
  if (localInviteLinkCopied.value) return
  localInviteLinkCopied.value = true
  emit('copyInviteLink', props.inviteLink)
  setTimeout(() => {
    localInviteLinkCopied.value = false
  }, 2000)
}

function handleCopySynastryShareLink() {
  if (localSynastryCopied.value) return
  localSynastryCopied.value = true
  emit('copySynastryShareLink', props.shareSynastryLink)
  setTimeout(() => {
    localSynastryCopied.value = false
  }, 2000)
}

function handleQuickShare() {
  if (props.inviteLink) {
    handleCopyInviteLink()
  } else if (props.shareSynastryLink) {
    handleCopySynastryShareLink()
  } else {
    handleCopyInviteCode()
  }
}

watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    resetAllStates()
  }
})
</script>

<style lang="scss" scoped>
:deep(.reward-share-dialog) {
  .el-dialog {
    background: linear-gradient(180deg, rgba(15, 15, 35, 0.98) 0%, rgba(20, 20, 50, 0.98) 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 16px !important;
  }

  .el-dialog__header {
    border-bottom: 1px solid rgba(139, 92, 246, 0.15) !important;
    padding: 16px 20px !important;
    margin-right: 0 !important;
  }

  .el-dialog__body {
    padding: 20px !important;
  }

  .el-dialog__footer {
    border-top: 1px solid rgba(139, 92, 246, 0.15) !important;
    padding: 16px 20px !important;
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95) !important;
}

.reward-share-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reward-intro {
  text-align: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.intro-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.6;
}

.reward-stages {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.stage-card {
  flex: 1;
  min-width: 140px;
  background: rgba(30, 30, 60, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stage-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;

  &.stage-1 {
    background: linear-gradient(135deg, #f59e0b, #d97706);
  }

  &.stage-2 {
    background: linear-gradient(135deg, #22c55e, #16a34a);
  }

  &.stage-3 {
    background: linear-gradient(135deg, #ef4444, #dc2626);
  }
}

.stage-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.stage-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin: 0;
  line-height: 1.5;
}

.stage-reward {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
}

.stage-arrow {
  display: flex;
  align-items: center;
  padding-top: 12px;
  color: rgba(139, 92, 246, 0.4);
}

.share-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.share-option-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(30, 30, 60, 0.4);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 10px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.option-content {
  display: flex;
  gap: 10px;
  align-items: center;
}

.invite-code-display {
  flex: 1;
  padding: 10px 14px;
  background: rgba(30, 30, 60, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 8px;
  text-align: center;
  
  &.status-loading {
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  &.status-error {
    border-color: rgba(239, 68, 68, 0.5);
    background: rgba(239, 68, 68, 0.1);
  }
  
  &.status-success {
    border-color: rgba(34, 197, 94, 0.3);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.code-text {
  font-size: 20px;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: 3px;
  font-family: 'Courier New', monospace;
}

.link-input {
  flex: 1;

  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.6) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    box-shadow: none !important;
  }

  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.8) !important;
    font-size: 12px !important;
  }
}

.share-tips-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 8px;
}

.tips-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.5;
}

:deep(.el-divider) {
  --el-divider-border-color: rgba(139, 92, 246, 0.15) !important;
  margin: 8px 0 !important;
}

@media (max-width: 600px) {
  .reward-stages {
    flex-direction: column;
    gap: 12px;
  }

  .stage-arrow {
    justify-content: center;
    padding: 0;
    transform: rotate(90deg);
  }

  .option-content {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
