<template>
  <div class="gift-shop-container">
    <div class="shop-header">
      <div class="header-left">
        <span class="shop-icon">🎁</span>
        <span class="shop-title">礼物商城</span>
      </div>
      <div class="header-info" v-if="isVip">
        <span class="vip-badge-small">
          ⭐ 会员专享折扣
        </span>
      </div>
    </div>

    <div class="shop-tabs">
      <div
        class="tab-item"
        :class="{ 'tab-active': activeTab === 'all' }"
        @click="activeTab = 'all'"
      >
        全部礼物
      </div>
      <div
        class="tab-item"
        :class="{ 'tab-active': activeTab === 'sent' }"
        @click="activeTab = 'sent'"
      >
        我送出的
      </div>
      <div
        class="tab-item"
        :class="{ 'tab-active': activeTab === 'received' }"
        @click="activeTab = 'received'"
      >
        我收到的
      </div>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'all'" class="all-gifts">
        <div class="gifts-grid">
          <div
            class="gift-card"
            v-for="gift in gifts"
            :key="gift.id"
            @click="selectGift(gift)"
          >
            <div class="gift-image">
              <span class="gift-emoji">{{ gift.icon }}</span>
              <div class="gift-overlay" v-if="gift.sold_count > 0">
                <span class="sold-text">已送 {{ gift.sold_count }} 份</span>
              </div>
            </div>
            <div class="gift-info">
              <span class="gift-name">{{ gift.name }}</span>
              <p class="gift-desc">{{ gift.description }}</p>
            </div>
            <div class="gift-price">
              <span class="price-symbol">¥</span>
              <span class="price-value" :class="{ 'price-discount': gift.discount_price }">
                {{ gift.discount_price || gift.price }}
              </span>
              <span class="price-original" v-if="gift.discount_price">
                原价 ¥{{ gift.price }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'sent'" class="sent-gifts">
        <el-empty v-if="sentGifts.length === 0" description="您还没有送出过礼物">
          <template #image>
            <span class="empty-emoji">🎁</span>
          </template>
        </el-empty>
        <div class="gifts-list" v-else>
          <div class="gift-item" v-for="item in sentGifts" :key="item.id">
            <div class="gift-avatar">
              <span class="gift-emoji-small">{{ item.gift?.icon || '🎁' }}</span>
            </div>
            <div class="gift-detail">
              <div class="gift-row">
                <span class="gift-name">{{ item.gift?.name }}</span>
                <span class="gift-date">{{ formatDate(item.sent_at) }}</span>
              </div>
              <p class="gift-message" v-if="item.message">{{ item.message }}</p>
              <div class="gift-to">
                <span>送给：</span>
                <span class="receiver-name">{{ item.receiver?.username || '未知用户' }}</span>
              </div>
            </div>
            <div class="gift-price-small">
              ¥{{ item.gift?.price || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'received'" class="received-gifts">
        <el-empty v-if="receivedGifts.length === 0" description="您还没有收到过礼物">
          <template #image>
            <span class="empty-emoji">🎁</span>
          </template>
        </el-empty>
        <div class="gifts-list" v-else>
          <div class="gift-item" v-for="item in receivedGifts" :key="item.id">
            <div class="gift-avatar">
              <span class="gift-emoji-small">{{ item.gift?.icon || '🎁' }}</span>
            </div>
            <div class="gift-detail">
              <div class="gift-row">
                <span class="gift-name">{{ item.gift?.name }}</span>
                <span class="gift-date">{{ formatDate(item.sent_at) }}</span>
              </div>
              <p class="gift-message" v-if="item.message">{{ item.message }}</p>
              <div class="gift-from">
                <span>来自：</span>
                <span class="sender-name">
                  {{ item.is_anonymous ? '匿名用户' : (item.sender?.username || '未知用户') }}
                </span>
              </div>
            </div>
            <div class="gift-actions">
              <el-button
                size="small"
                type="primary"
                @click="displayGift(item)"
              >
                {{ item.is_displayed ? '已展示' : '展示到主页' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <el-dialog
    v-model="sendDialogVisible"
    title="赠送礼物"
    width="450px"
  >
    <div class="send-gift-form">
      <div class="gift-preview">
        <span class="gift-emoji-large">{{ selectedGift?.icon }}</span>
        <div class="gift-info-preview">
          <span class="gift-name-preview">{{ selectedGift?.name }}</span>
          <p class="gift-desc-preview">{{ selectedGift?.description }}</p>
          <div class="gift-price-preview">
            <span class="price-symbol">¥</span>
            <span class="price-value">{{ selectedGift?.discount_price || selectedGift?.price }}</span>
          </div>
        </div>
      </div>

      <el-form label-position="top">
        <el-form-item label="接收用户">
          <el-input
            v-model="sendForm.receiverId"
            placeholder="请输入用户ID或用户名"
          />
        </el-form-item>

        <el-form-item label="留言（可选）">
          <el-input
            v-model="sendForm.message"
            type="textarea"
            :rows="3"
            placeholder="想对TA说的话..."
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="sendForm.isAnonymous">
            匿名赠送
          </el-checkbox>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="sendDialogVisible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="sendingGift"
        @click="confirmSendGift"
      >
        确认赠送
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { giftApi, paymentApi } from '@/api'

const activeTab = ref('all')
const gifts = ref([])
const sentGifts = ref([])
const receivedGifts = ref([])
const isVip = ref(false)

const sendDialogVisible = ref(false)
const selectedGift = ref(null)
const sendingGift = ref(false)
const sendForm = ref({
  receiverId: '',
  message: '',
  isAnonymous: false
})

onMounted(async () => {
  await loadGifts()
  await loadGiftHistory()
})

async function loadGifts() {
  try {
    const response = await giftApi.getShop()
    gifts.value = response.gifts || []
  } catch (error) {
    console.error('加载礼物失败:', error)
  }
}

async function loadGiftHistory() {
  try {
    const [sentRes, receivedRes] = await Promise.all([
      giftApi.getSent(20, 0),
      giftApi.getReceived(20, 0)
    ])
    sentGifts.value = sentRes.items || []
    receivedGifts.value = receivedRes.items || []
  } catch (error) {
    console.error('加载礼物记录失败:', error)
  }
}

function selectGift(gift) {
  selectedGift.value = gift
  sendForm.value = {
    receiverId: '',
    message: '',
    isAnonymous: false
  }
  sendDialogVisible.value = true
}

async function confirmSendGift() {
  if (!sendForm.value.receiverId) {
    ElMessage.warning('请输入接收用户')
    return
  }

  sendingGift.value = true
  try {
    const response = await giftApi.sendGift({
      receiver_identifier: sendForm.value.receiverId,
      gift_id: selectedGift.value.id,
      quantity: 1,
      message: sendForm.value.message || undefined,
      is_anonymous: sendForm.value.isAnonymous
    })

    if (response.payment_url) {
      const win = window.open(response.payment_url, '_blank', 'width=600,height=700')
      
      const checkInterval = setInterval(async () => {
        try {
          const orderResult = await paymentApi.getOrder(response.order_no)
          if (orderResult.status === 'paid') {
            clearInterval(checkInterval)
            ElMessage.success('礼物赠送成功！')
            sendDialogVisible.value = false
            await loadGiftHistory()
          }
        } catch (e) {
          console.error('检查订单状态失败:', e)
        }
      }, 3000)
      
      setTimeout(() => {
        clearInterval(checkInterval)
      }, 120000)
    }
  } catch (error) {
    console.error('赠送礼物失败:', error)
    ElMessage.error(error.response?.data?.detail || '赠送失败，请稍后重试')
  } finally {
    sendingGift.value = false
  }
}

async function displayGift(item) {
  if (item.is_displayed) {
    try {
      await giftApi.removeDisplayed(item.display_id)
      ElMessage.success('已从主页移除')
      item.is_displayed = false
    } catch (error) {
      console.error('移除展示失败:', error)
      ElMessage.error('操作失败')
    }
  } else {
    try {
      const response = await giftApi.displayGift(item.id, false)
      ElMessage.success('已展示到主页')
      item.is_displayed = true
      item.display_id = response.id
    } catch (error) {
      console.error('展示礼物失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.gift-shop-container {
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.95), rgba(15, 15, 35, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  overflow: hidden;
}

.shop-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.1), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.shop-icon {
  font-size: 1.2rem;
}

.shop-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.vip-badge-small {
  padding: 4px 12px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
}

.shop-tabs {
  display: flex;
  padding: 12px 20px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.tab-item {
  padding: 10px 20px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
  
  &:hover {
    color: rgba(255, 255, 255, 0.8);
  }
  
  &.tab-active {
    color: #a78bfa;
    border-bottom-color: #a78bfa;
  }
}

.tab-content {
  padding: 20px;
}

.gifts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.gift-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.08);
    border-color: rgba(139, 92, 246, 0.3);
    transform: translateY(-4px);
  }
}

.gift-image {
  position: relative;
  text-align: center;
  padding: 20px 0;
  margin-bottom: 12px;
}

.gift-emoji {
  font-size: 3rem;
}

.gift-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
}

.sold-text {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 8px;
  border-radius: 8px;
}

.gift-info {
  margin-bottom: 12px;
}

.gift-name {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.gift-desc {
  margin: 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

.gift-price {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px;
}

.price-symbol {
  font-size: 0.8rem;
  color: #a78bfa;
}

.price-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #a78bfa;
  
  &.price-discount {
    color: #fbbf24;
  }
}

.price-original {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.3);
  text-decoration: line-through;
}

.gifts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gift-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.gift-avatar {
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
}

.gift-emoji-small {
  font-size: 1.5rem;
}

.gift-detail {
  flex: 1;
  min-width: 0;
}

.gift-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.gift-date {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.gift-message {
  margin: 4px 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.4;
}

.gift-to,
.gift-from {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.receiver-name,
.sender-name {
  color: #a78bfa;
  font-weight: 500;
}

.gift-price-small {
  flex-shrink: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #a78bfa;
}

.gift-actions {
  flex-shrink: 0;
}

.empty-emoji {
  font-size: 3rem;
}

.send-gift-form {
  .gift-preview {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: rgba(139, 92, 246, 0.05);
    border-radius: 12px;
    margin-bottom: 20px;
  }
  
  .gift-emoji-large {
    font-size: 3rem;
  }
  
  .gift-info-preview {
    flex: 1;
  }
  
  .gift-name-preview {
    display: block;
    font-size: 1.1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 4px;
  }
  
  .gift-desc-preview {
    margin: 0 0 8px;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .price-value {
    font-size: 1.2rem;
    color: #a78bfa;
  }
}

@media (max-width: 768px) {
  .gifts-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .gifts-grid {
    grid-template-columns: 1fr;
  }
}
</style>