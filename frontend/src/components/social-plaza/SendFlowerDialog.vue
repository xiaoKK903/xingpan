<template>
  <el-dialog 
    v-model="visible" 
    title="送一朵花给TA" 
    width="420px"
    class="send-flower-dialog"
  >
    <div class="dialog-content">
      <div class="user-preview" v-if="postData">
        <div class="avatar">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="info">
          <div class="username-row">
            <span class="username">{{ postData.username || '神秘用户' }}</span>
            <VIPBadge 
              v-if="postData.is_vip" 
              :is-vip="true" 
              :show-text="false" 
              size="small" 
            />
          </div>
          <span class="content-preview">{{ postData.content || '分享了一条内容' }}</span>
        </div>
      </div>
      
      <div class="section-title">选择礼物</div>
      <div class="gift-grid">
        <div 
          v-for="gift in gifts" 
          :key="gift.id"
          class="gift-item" 
          :class="{ active: selectedGift?.id === gift.id }"
          @click="selectGift(gift)"
        >
          <div class="gift-icon">{{ gift.icon || '🌸' }}</div>
          <div class="gift-name">{{ gift.name }}</div>
          <div class="gift-price">
            <span class="price">{{ gift.price }}</span>
            <span class="currency">{{ gift.currency_label }}</span>
          </div>
        </div>
      </div>
      
      <div class="quantity-section">
        <span class="label">数量</span>
        <el-input-number 
          v-model="quantity" 
          :min="1" 
          :max="99"
          size="small"
        />
      </div>
      
      <div class="message-section">
        <span class="label">留言（可选）</span>
        <el-input
          v-model="message"
          type="textarea"
          placeholder="写下想说的话..."
          :rows="2"
          maxlength="100"
          show-word-limit
          class="message-input"
        />
      </div>
      
      <div class="anonymous-section">
        <el-checkbox v-model="isAnonymous">匿名送花</el-checkbox>
      </div>
      
      <div class="summary-section" v-if="selectedGift">
        <div class="summary-row">
          <span>礼物：{{ selectedGift.name }} × {{ quantity }}</span>
          <span class="total-price">
            {{ selectedGift.price * quantity }} {{ selectedGift.currency_label }}
          </span>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="submitting"
          :disabled="!selectedGift"
          @click="handleSend"
        >
          送出 🌸
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { socialPlazaApi, giftApi } from '@/api'
import VIPBadge from '@/components/VIPBadge.vue'

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

const emit = defineEmits(['update:modelValue', 'sent'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const gifts = ref([
  { id: 1, name: '星尘花', icon: '🌸', price: 10, currency_type: 'stardust_point', currency_label: '星尘点' },
  { id: 2, name: '月光花', icon: '🌙', price: 50, currency_type: 'stardust_point', currency_label: '星尘点' },
  { id: 3, name: '星光花', icon: '✨', price: 100, currency_type: 'stardust_point', currency_label: '星尘点' },
  { id: 4, name: '玫瑰礼盒', icon: '🌹', price: 10, currency_type: 'stardust_fragment', currency_label: '星尘碎片' },
])

const selectedGift = ref(null)
const quantity = ref(1)
const message = ref('')
const isAnonymous = ref(false)
const submitting = ref(false)
const postData = ref(null)

watch(visible, async (val) => {
  if (val && props.postId) {
    await loadPostData()
    resetForm()
  }
})

function resetForm() {
  selectedGift.value = null
  quantity.value = 1
  message.value = ''
  isAnonymous.value = false
}

async function loadPostData() {
  try {
    postData.value = await socialPlazaApi.getPostDetail(props.postId)
  } catch (error) {
    console.error('获取内容详情失败:', error)
  }
}

function selectGift(gift) {
  selectedGift.value = gift
}

async function handleSend() {
  if (!selectedGift.value) {
    ElMessage.warning('请选择礼物')
    return
  }
  
  try {
    submitting.value = true
    
    const data = {
      gift_id: selectedGift.value.id,
      quantity: quantity.value,
      message: message.value || null,
      is_anonymous: isAnonymous.value
    }
    
    await socialPlazaApi.sendFlower(props.postId, data)
    
    ElMessage.success(`成功送出 ${quantity.value} 朵${selectedGift.value.name}！`)
    emit('sent', {
      gift_id: selectedGift.value.id,
      gift_name: selectedGift.value.name,
      quantity: quantity.value
    })
    visible.value = false
    
  } catch (error) {
    console.error('送花失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
:deep(.send-flower-dialog .el-dialog) {
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(30, 27, 75, 0.98) 0%, rgba(12, 12, 35, 0.98) 100%);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

:deep(.send-flower-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  padding: 20px 24px;
  margin-right: 0;
}

:deep(.send-flower-dialog .el-dialog__title) {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 600;
}

.dialog-content {
  padding: 16px 0;
}

.user-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  margin-bottom: 20px;
}

.user-preview .avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.user-preview .info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.username-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.content-preview {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
}

.gift-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.gift-item {
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
  
  &.active {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(139, 92, 246, 0.1));
    border-color: rgba(251, 191, 36, 0.5);
    box-shadow: 0 0 15px rgba(251, 191, 36, 0.15);
  }
}

.gift-icon {
  font-size: 28px;
}

.gift-name {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.gift-price {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.gift-price .price {
  font-size: 14px;
  font-weight: 600;
  color: #fbbf24;
}

.gift-price .currency {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.quantity-section,
.message-section,
.anonymous-section {
  margin-bottom: 16px;
}

.label {
  display: inline-block;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.anonymous-section {
  :deep(.el-checkbox__label) {
    color: rgba(255, 255, 255, 0.7);
  }
}

.message-input {
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

.summary-section {
  padding: 12px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.total-price {
  font-weight: 600;
  color: #fbbf24;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.send-flower-dialog .el-dialog__footer) {
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  padding-top: 16px;
}
</style>
