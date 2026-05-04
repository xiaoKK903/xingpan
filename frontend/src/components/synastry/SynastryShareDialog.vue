<template>
  <el-dialog
    v-model="dialogVisibleModel"
    title="分享报告"
    width="400px"
    center
  >
    <div class="share-dialog-content">
      <p class="share-tip">复制以下分享链接发送给好友：</p>
      <div class="share-link-wrapper">
        <el-input :model-value="shareLink" readonly />
        <el-button type="primary" @click="handleCopyShareLink">
          {{ localCopied ? '已复制' : '复制' }}
        </el-button>
      </div>
      <p class="share-note">
        <el-icon><InfoFilled /></el-icon>
        对方可以通过此链接查看这份合盘分析报告
      </p>
    </div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  shareLink: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'copyShareLink'])

const localCopied = ref(false)

const dialogVisibleModel = computed({
  get: () => props.modelValue,
  set: (value) => {
    if (!value) {
      handleClose()
    }
  }
})

function resetAllStates() {
  localCopied.value = false
}

function handleClose() {
  resetAllStates()
  emit('update:modelValue', false)
}

function handleCopyShareLink() {
  if (localCopied.value) return
  localCopied.value = true
  emit('copyShareLink', props.shareLink)
  setTimeout(() => {
    localCopied.value = false
  }, 2000)
}

watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    resetAllStates()
  }
})
</script>

<style lang="scss" scoped>
.share-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.share-tip {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.share-link-wrapper {
  display: flex;
  gap: 10px;
}

.share-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}
</style>
