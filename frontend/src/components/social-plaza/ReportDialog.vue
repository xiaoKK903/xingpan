<template>
  <el-dialog 
    v-model="visible" 
    title="举报内容" 
    width="400px"
    class="report-dialog"
  >
    <div class="dialog-content">
      <div class="section-label">选择举报类型</div>
      <div class="category-list">
        <div 
          v-for="cat in categories" 
          :key="cat.key"
          class="category-item" 
          :class="{ selected: selectedCategory === cat.key }"
          @click="selectedCategory = cat.key"
        >
          <span class="cat-icon">{{ cat.icon }}</span>
          <span class="cat-label">{{ cat.label }}</span>
        </div>
      </div>
      
      <div class="description-section">
        <div class="section-label">详细描述（可选）</div>
        <el-input
          v-model="reportReason"
          type="textarea"
          placeholder="请描述举报原因，帮助我们更好地处理..."
          :rows="3"
          maxlength="200"
          show-word-limit
          class="reason-input"
        />
      </div>
      
      <div class="tip-section">
        <el-icon><InfoFilled /></el-icon>
        <span>我们会认真处理每一条举报，感谢您维护良好的社区环境。</span>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="submitting"
          :disabled="!selectedCategory"
          @click="handleSubmit"
        >
          提交举报
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { socialPlazaApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  postId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const categories = ref([
  { key: 'spam', icon: '📧', label: '垃圾广告' },
  { key: 'violence', icon: '⚔️', label: '暴力内容' },
  { key: 'porn', icon: '🔞', label: '色情内容' },
  { key: 'fake', icon: '🎭', label: '虚假信息' },
  { key: 'insult', icon: '💬', label: '人身攻击' },
  { key: 'other', icon: '❓', label: '其他' },
])

const selectedCategory = ref('')
const reportReason = ref('')
const submitting = ref(false)

watch(visible, (val) => {
  if (val) {
    resetForm()
  }
})

function resetForm() {
  selectedCategory.value = ''
  reportReason.value = ''
}

async function handleSubmit() {
  if (!selectedCategory.value) {
    ElMessage.warning('请选择举报类型')
    return
  }
  
  try {
    submitting.value = true
    
    const data = {
      report_category: selectedCategory.value,
      report_reason: reportReason.value || null
    }
    
    await socialPlazaApi.reportPost(props.postId, data)
    
    ElMessage.success('举报已提交，感谢您的反馈')
    visible.value = false
    
  } catch (error) {
    console.error('举报失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
:deep(.report-dialog .el-dialog) {
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.98) 0%, rgba(12, 12, 35, 0.98) 100%);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

:deep(.report-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  padding: 20px 24px;
  margin-right: 0;
}

:deep(.report-dialog .el-dialog__title) {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 600;
}

.dialog-content {
  padding: 16px 0;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
}

.category-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
  }
  
  &.selected {
    background: linear-gradient(135deg, rgba(244, 63, 94, 0.15), rgba(139, 92, 246, 0.1));
    border-color: rgba(244, 63, 94, 0.4);
    box-shadow: 0 0 15px rgba(244, 63, 94, 0.1);
  }
}

.cat-icon {
  font-size: 20px;
}

.cat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.description-section {
  margin-bottom: 16px;
}

.reason-input {
  :deep(.el-textarea__inner) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    color: rgba(255, 255, 255, 0.9);
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

.tip-section {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: rgba(34, 197, 94, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(34, 197, 94, 0.15);
  color: rgba(34, 197, 94, 0.8);
  font-size: 12px;
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.report-dialog .el-dialog__footer) {
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  padding-top: 16px;
}
</style>
