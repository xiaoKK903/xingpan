<template>
  <el-dialog 
    v-model="visible" 
    title="分享此刻的星光" 
    width="520px"
    :close-on-click-modal="false"
    class="create-post-dialog"
  >
    <div class="dialog-content">
      <div class="topic-link-section" v-if="activeTopic">
        <div class="topic-link-badge">
          <span class="badge-icon">🔥</span>
          <span class="badge-text">参与本周话题挑战</span>
        </div>
        <div class="topic-link-info">
          <span class="topic-tag">{{ activeTopic.topic_tag }}</span>
          <span class="topic-title">{{ activeTopic.title }}</span>
        </div>
        <div class="topic-link-toggle">
          <el-switch 
            v-model="linkToTopic" 
            active-text="关联话题"
            inactive-text="不关联"
            :disabled="!canLinkTopic"
          />
        </div>
      </div>
      
      <div class="post-type-selector">
        <div class="section-label">选择分享类型</div>
        <div class="type-grid">
          <div 
            v-for="type in postTypes" 
            :key="type.key"
            class="type-item" 
            :class="{ active: form.post_type === type.key }"
            @click="selectType(type.key)"
          >
            <span class="type-icon">{{ type.icon }}</span>
            <span class="type-name">{{ type.name }}</span>
            <span class="type-desc">{{ type.description }}</span>
          </div>
        </div>
      </div>
      
      <div class="form-section">
        <el-input
          v-model="form.title"
          placeholder="给你的内容起个温柔的标题..."
          maxlength="50"
          show-word-limit
          class="title-input"
        />
      </div>
      
      <div class="form-section">
        <el-input
          v-model="form.content"
          type="textarea"
          placeholder="想说些什么呢... ✨"
          :rows="4"
          maxlength="500"
          show-word-limit
          resize="none"
          class="content-input"
        />
      </div>
      
      <div class="form-section">
        <div class="section-label">添加图片（暂不可用）</div>
        <div class="image-disabled-notice">
          <el-icon :size="32"><InfoFilled /></el-icon>
          <p>图片上传功能暂未开放，请先分享文字内容。</p>
        </div>
      </div>
      
      <div class="form-section" v-if="showTags">
        <div class="section-label">添加标签（可选）</div>
        <div class="tags-container">
          <el-tag
            v-for="(tag, index) in form.tags"
            :key="index"
            class="tag-item"
            closable
            @close="removeTag(index)"
            effect="plain"
          >
            {{ tag }}
          </el-tag>
          <el-input
            v-if="showTagInput"
            v-model="newTag"
            size="small"
            class="tag-input"
            @keyup.enter="addTag"
            @blur="hideTagInput"
            ref="tagInputRef"
          />
          <button v-else class="add-tag-btn" @click="showTagInput = true">
            <el-icon><Plus /></el-icon>
            添加标签
          </button>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="submitting"
          :disabled="!canSubmit"
          @click="handleSubmit"
        >
          发布 ✨
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Plus, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { socialPlazaApi, topicChallengeApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  topic_challenge_id: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const postTypes = ref([])
const loading = ref(false)
const submitting = ref(false)
const newTag = ref('')
const showTagInput = ref(false)
const tagInputRef = ref(null)

const activeTopic = ref(null)
const linkToTopic = ref(false)

const showTags = computed(() => form.value.post_type === 'daily_horoscope' || form.value.post_type === 'past_life_story')

const canLinkTopic = computed(() => {
  if (!activeTopic.value) return false
  if (activeTopic.value.time_status !== 'active') return false
  if (activeTopic.value.user_participation) return false
  return true
})

const form = ref({
  post_type: '',
  title: '',
  content: '',
  tags: []
})

const canSubmit = computed(() => {
  return !!(form.value.post_type && (form.value.content || form.value.title))
})

watch(visible, async (val) => {
  if (val) {
    resetForm()
    await loadPostTypes()
    await loadActiveTopic()
  }
})

function resetForm() {
  form.value = {
    post_type: '',
    title: '',
    content: '',
    tags: []
  }
  newTag.value = ''
  showTagInput.value = false
  activeTopic.value = null
  linkToTopic.value = false
}

async function loadActiveTopic() {
  try {
    if (props.topic_challenge_id) {
      const result = await topicChallengeApi.getTopicDetail(props.topic_challenge_id)
      activeTopic.value = result?.topic || null
    } else {
      const result = await topicChallengeApi.getActiveTopic()
      activeTopic.value = result?.topic || null
    }
    
    if (activeTopic.value && canLinkTopic.value) {
      linkToTopic.value = true
    }
  } catch (error) {
    console.error('加载活跃话题失败:', error)
    activeTopic.value = null
  }
}

async function loadPostTypes() {
  try {
    loading.value = true
    const result = await socialPlazaApi.getPostTypes()
    postTypes.value = result.types || []
    if (postTypes.value.length > 0 && !form.value.post_type) {
      form.value.post_type = postTypes.value[0].key
    }
  } catch (error) {
    console.error('获取内容类型失败:', error)
  } finally {
    loading.value = false
  }
}

function selectType(typeKey) {
  form.value.post_type = typeKey
}

async function addTag() {
  const tag = newTag.value.trim()
  if (tag && !form.value.tags.includes(tag)) {
    if (form.value.tags.length >= 5) {
      ElMessage.warning('最多添加5个标签')
      return
    }
    form.value.tags.push(tag)
  }
  newTag.value = ''
  hideTagInput()
}

function removeTag(index) {
  form.value.tags.splice(index, 1)
}

function hideTagInput() {
  showTagInput.value = false
  newTag.value = ''
}

watch(showTagInput, (val) => {
  if (val && tagInputRef.value) {
    nextTick(() => {
      tagInputRef.value.focus()
    })
  }
})

async function handleSubmit() {
  if (!canSubmit.value) {
    ElMessage.warning('请至少填写标题或内容')
    return
  }
  
  try {
    submitting.value = true
    
    const postData = {
      post_type: form.value.post_type,
      title: form.value.title || null,
      content: form.value.content || null,
      tags: form.value.tags.length > 0 ? form.value.tags : null
    }
    
    if (linkToTopic.value && activeTopic.value) {
      postData.topic_challenge_id = activeTopic.value.id
    }
    
    await socialPlazaApi.createPost(postData)
    
    if (linkToTopic.value && activeTopic.value) {
      ElMessage.success(`发布成功！已参与话题 ${activeTopic.value.topic_tag}`)
    } else {
      ElMessage.success('发布成功！')
    }
    emit('success')
    visible.value = false
    
  } catch (error) {
    console.error('发布失败:', error)
    ElMessage.error(error.message || '发布失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
:deep(.create-post-dialog .el-dialog) {
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.98) 0%, rgba(12, 12, 35, 0.98) 100%);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

:deep(.create-post-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  padding: 20px 24px;
  margin-right: 0;
}

:deep(.create-post-dialog .el-dialog__title) {
  background: linear-gradient(135deg, #a78bfa, #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 18px;
  font-weight: 600;
}

.dialog-content {
  padding: 20px 0;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
}

.post-type-selector {
  margin-bottom: 20px;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.type-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
  }
  
  &.active {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.15));
    border-color: rgba(139, 92, 246, 0.5);
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
  }
}

.type-icon {
  font-size: 28px;
}

.type-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.type-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.form-section {
  margin-bottom: 20px;
}

.title-input {
  :deep(.el-input__wrapper) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: none;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &.is-focus {
      border-color: rgba(139, 92, 246, 0.5);
      box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
    }
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9);
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
  }
  
  :deep(.el-input__count) {
    color: rgba(255, 255, 255, 0.5);
  }
}

.content-input {
  :deep(.el-textarea__inner) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    padding: 12px 16px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    line-height: 1.7;
    resize: none;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &:focus {
      border-color: rgba(139, 92, 246, 0.5);
      box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
    }
  }
  
  :deep(.el-input__count) {
    color: rgba(255, 255, 255, 0.5);
  }
}

.image-uploader {
  :deep(.el-upload--picture-card) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px dashed rgba(139, 92, 246, 0.3);
    border-radius: 12px;
    width: 100px;
    height: 100px;
  }
  
  :deep(.el-upload-list--picture-card .el-upload-list__item) {
    width: 100px;
    height: 100px;
    border-radius: 12px;
    overflow: hidden;
  }
}

.upload-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: rgba(139, 92, 246, 0.6);
}

.upload-text {
  font-size: 12px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-item {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
}

.tag-input {
  width: 120px;
  
  :deep(.el-input__wrapper) {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.2);
    box-shadow: none;
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9);
  }
}

.add-tag-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px dashed rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  color: rgba(139, 92, 246, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.4);
    color: #c4b5fd;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.create-post-dialog .el-dialog__footer) {
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  padding-top: 16px;
}

.topic-link-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(139, 92, 246, 0.08) 100%);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 12px;
  margin-bottom: 20px;
}

.topic-link-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.1));
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  flex-shrink: 0;
}

.badge-icon {
  font-size: 14px;
}

.badge-text {
  font-size: 12px;
  font-weight: 600;
  color: #f87171;
}

.topic-link-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.topic-link-info .topic-tag {
  padding: 2px 8px;
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #fbbf24;
  flex-shrink: 0;
}

.topic-link-info .topic-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topic-link-toggle {
  flex-shrink: 0;
}

:deep(.topic-link-toggle .el-switch) {
  --el-switch-on-color: rgba(139, 92, 246, 0.8);
  --el-switch-off-color: rgba(255, 255, 255, 0.2);
}

:deep(.topic-link-toggle .el-switch__label) {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

:deep(.topic-link-toggle .el-switch__label.is-active) {
  color: #c4b5fd;
}
</style>
