<template>
  <div 
    class="plaza-card" 
    :class="{ 'vip-card': post.is_vip, 'liked-by-me': post.is_liked }"
  >
    <div v-if="post.is_vip" class="vip-corner">
      <span class="vip-icon">⭐</span>
      <span class="vip-text">会员</span>
    </div>
    
    <div class="card-header">
      <div class="user-info">
        <div class="avatar" :class="{ 'vip-avatar': post.is_vip }">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="user-details">
          <div class="username-row">
            <span class="username">{{ post.username || '神秘用户' }}</span>
            <VIPBadge 
              v-if="post.is_vip" 
              :is-vip="true" 
              :show-text="false" 
              size="small" 
            />
          </div>
          <span class="post-time">{{ formatTime(post.created_at) }}</span>
        </div>
      </div>
      <div class="post-type-badge" :class="post.post_type">
        <span class="type-icon">{{ getTypeIcon(post.post_type) }}</span>
        <span class="type-label">{{ post.post_type_label }}</span>
      </div>
    </div>
    
    <div v-if="post.title" class="card-title">{{ post.title }}</div>
    
    <div v-if="post.content" class="card-content">{{ post.content }}</div>
    
    <div v-if="validImageUrls.length > 0" class="card-images">
      <div 
        class="image-grid" 
        :class="getImageGridClass(validImageUrls.length)"
      >
        <div 
          v-for="(img, index) in validImageUrls.slice(0, maxDisplayImages)" 
          :key="index"
          class="image-item"
          @click="previewImage(index)"
        >
          <img :src="img" :alt="`图片 ${index + 1}`" @error="handleImageError(index)" />
          <div 
            v-if="index === 3 && validImageUrls.length > 4" 
            class="more-overlay"
          >
            <span>+{{ validImageUrls.length - 4 }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="card-footer">
      <div class="action-buttons">
        <button 
          class="action-btn like-btn" 
          :class="{ active: post.is_liked }"
          @click="handleLike"
        >
          <el-icon v-if="post.is_liked"><StarFilled /></el-icon>
          <el-icon v-else><Star /></el-icon>
          <span>{{ post.like_count }}</span>
        </button>
        
        <button class="action-btn flower-btn" @click="handleSendFlower">
          <el-icon><Sunny /></el-icon>
          <span>{{ post.flower_count }}</span>
        </button>
        
        <button class="action-btn mention-btn" @click="handleMention">
          <el-icon><ChatDotRound /></el-icon>
          <span v-if="post.mention_count > 0">{{ post.mention_count }}</span>
          <span v-else>@好友</span>
        </button>
        
        <el-dropdown trigger="click" class="more-dropdown">
          <button class="action-btn more-btn">
            <el-icon><MoreFilled /></el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleShare">
                <el-icon><Share /></el-icon>
                分享
              </el-dropdown-item>
              <el-dropdown-item @click="handleReport">
                <el-icon><Warning /></el-icon>
                举报
              </el-dropdown-item>
              <el-dropdown-item 
                v-if="isMyPost" 
                divided
                @click="handleDelete"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <SendFlowerDialog 
      v-model="showFlowerDialog"
      :post-id="post.id"
      @sent="onFlowerSent"
    />
    
    <MentionFriendDialog 
      v-model="showMentionDialog"
      :post-id="post.id"
      @sent="onMentionSent"
    />
    
    <ReportDialog 
      v-model="showReportDialog"
      :post-id="post.id"
    />
    
    <el-image-viewer
      v-if="showImageViewer"
      :url-list="post.image_urls"
      :initial-index="previewIndex"
      @close="showImageViewer = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  Star, StarFilled, Sunny, ChatDotRound, MoreFilled, 
  UserFilled, Share, Warning, Delete 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { socialPlazaApi } from '@/api'
import VIPBadge from '@/components/VIPBadge.vue'
import SendFlowerDialog from './SendFlowerDialog.vue'
import MentionFriendDialog from './MentionFriendDialog.vue'
import ReportDialog from './ReportDialog.vue'

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['liked', 'deleted', 'shared'])

const userStore = useUserStore()

const showFlowerDialog = ref(false)
const showMentionDialog = ref(false)
const showReportDialog = ref(false)
const showImageViewer = ref(false)
const previewIndex = ref(0)
const maxDisplayImages = ref(4)
const validImageUrls = ref([])

const isMyPost = computed(() => {
  return userStore.user?.id === props.post.user_id
})

const postTypeIcons = {
  synastry_card: '♊',
  daily_horoscope: '🌟',
  past_life_story: '🌙',
  card_draw: '🎴'
}

function getTypeIcon(type) {
  return postTypeIcons[type] || '✨'
}

function getImageGridClass(count) {
  if (count === 1) return 'single-image'
  if (count === 2) return 'two-images'
  if (count === 3) return 'three-images'
  return 'four-images'
}

function isValidImageUrl(url) {
  if (!url) return false
  if (url.startsWith('blob:')) return false
  if (url.startsWith('http://') || url.startsWith('https://')) return true
  if (url.startsWith('data:')) return true
  return false
}

function filterValidImages() {
  if (!props.post.image_urls || props.post.image_urls.length === 0) {
    validImageUrls.value = []
    return
  }
  validImageUrls.value = props.post.image_urls.filter(url => isValidImageUrl(url))
}

watch(() => props.post.image_urls, () => {
  filterValidImages()
}, { immediate: true, deep: true })

function formatTime(timeStr) {
  if (!timeStr) return ''
  
  const now = new Date()
  const postTime = new Date(timeStr)
  
  if (isNaN(postTime.getTime())) {
    return ''
  }
  
  const diff = now - postTime
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return postTime.toLocaleDateString('zh-CN')
}

function handleImageError(index) {
  validImageUrls.value.splice(index, 1)
}

function previewImage(index) {
  previewIndex.value = index
  showImageViewer.value = true
}

async function handleLike() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  
  try {
    const result = await socialPlazaApi.likePost(props.post.id)
    props.post.is_liked = result.is_liked
    props.post.like_count = result.like_count
    emit('liked', { isLiked: result.is_liked, likeCount: result.like_count })
  } catch (error) {
    console.error('点赞失败:', error)
  }
}

function handleSendFlower() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  showFlowerDialog.value = true
}

function onFlowerSent(flowerData) {
  props.post.flower_count += flowerData.quantity
}

function handleMention() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  showMentionDialog.value = true
}

function onMentionSent() {
  props.post.mention_count++
}

function handleShare() {
  emit('shared', props.post)
  ElMessage.success('已复制分享链接')
}

function handleReport() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  showReportDialog.value = true
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条内容吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await socialPlazaApi.deletePost(props.post.id)
    emit('deleted', props.post.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}
</script>

<style lang="scss" scoped>
.plaza-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid rgba(139, 92, 246, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(139, 92, 246, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }
  
  &.vip-card {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.05) 0%, rgba(139, 92, 246, 0.03) 100%);
    border: 2px solid transparent;
    background-clip: padding-box;
    
    &::before {
      content: '';
      position: absolute;
      top: -2px;
      left: -2px;
      right: -2px;
      bottom: -2px;
      border-radius: 18px;
      background: linear-gradient(135deg, #fbbf24, #8b5cf6, #fbbf24);
      z-index: -1;
      opacity: 0.6;
    }
    
    &:hover::before {
      opacity: 0.8;
      animation: shimmer 2s infinite;
    }
  }
}

@keyframes shimmer {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.vip-corner {
  position: absolute;
  top: 0;
  right: 0;
  width: 70px;
  height: 70px;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: -35px;
    right: -35px;
    width: 100px;
    height: 100px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    transform: rotate(45deg);
  }
  
  .vip-icon {
    position: absolute;
    top: 10px;
    right: 12px;
    font-size: 16px;
  }
  
  .vip-text {
    position: absolute;
    top: 26px;
    right: 8px;
    font-size: 10px;
    color: #fff;
    font-weight: 600;
    transform: rotate(45deg);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  flex-shrink: 0;
  
  &.vip-avatar {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    box-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
    border: 2px solid #fcd34d;
  }
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.username {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.post-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.post-type-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  
  &.synastry_card {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(168, 85, 247, 0.2));
    color: #f472b6;
  }
  
  &.daily_horoscope {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.2));
    color: #fbbf24;
  }
  
  &.past_life_story {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.2));
    color: #a78bfa;
  }
  
  &.card_draw {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
    color: #4ade80;
  }
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 8px;
  line-height: 1.5;
}

.card-content {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.7;
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.card-images {
  margin-bottom: 16px;
}

.image-grid {
  display: grid;
  gap: 8px;
  
  &.single-image {
    grid-template-columns: 1fr;
    
    .image-item {
      max-height: 300px;
    }
  }
  
  &.two-images {
    grid-template-columns: repeat(2, 1fr);
    
    .image-item {
      aspect-ratio: 1;
    }
  }
  
  &.three-images {
    grid-template-columns: repeat(3, 1fr);
    
    .image-item {
      aspect-ratio: 1;
    }
  }
  
  &.four-images {
    grid-template-columns: repeat(2, 1fr);
    
    .image-item {
      aspect-ratio: 1;
    }
  }
}

.image-item {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
  }
  
  &:hover img {
    transform: scale(1.05);
  }
}

.more-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  
  span {
    font-size: 24px;
    font-weight: 600;
    color: #fff;
  }
}

.card-footer {
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 20px;
  border: none;
  background: rgba(139, 92, 246, 0.1);
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
  }
  
  &.like-btn {
    &.active {
      background: linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(244, 63, 94, 0.2));
      color: #f472b6;
    }
  }
  
  &.flower-btn {
    &:hover {
      background: rgba(251, 191, 36, 0.15);
      color: #fbbf24;
    }
  }
}

.more-dropdown {
  margin-left: auto;
}

.more-btn {
  padding: 8px;
}
</style>
