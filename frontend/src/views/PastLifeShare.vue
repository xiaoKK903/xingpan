<template>
  <div class="past-life-share-page">
    <div class="stars-bg">
      <div 
        v-for="i in 60" 
        :key="i" 
        class="star"
        :style="getStarStyle(i)"
      ></div>
    </div>

    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">🌙</span>
        前世故事分享
      </h1>
      <p class="page-description">
        这是来自好友分享的前世故事
      </p>
    </div>

    <div class="content-section">
      <div v-if="loading" class="loading-placeholder">
        <div class="loading-animation">
          <div class="loading-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          <p class="loading-text">正在加载分享的故事...</p>
        </div>
      </div>

      <div v-else-if="error" class="error-card">
        <div class="error-icon">🔒</div>
        <h3 class="error-title">分享链接无效</h3>
        <p class="error-message">{{ errorMessage || '该分享链接不存在或已失效' }}</p>
        <el-button type="primary" @click="goToHome">
          去探索自己的前世故事
        </el-button>
      </div>

      <div v-else-if="!sharedData" class="empty-placeholder">
        <div class="empty-icon">📜</div>
        <h3 class="empty-title">分享内容不存在</h3>
        <p class="empty-desc">该分享的前世故事不存在或已被删除</p>
        <el-button type="primary" @click="goToHome">
          生成自己的前世故事
        </el-button>
      </div>

      <div v-else class="share-card">
        <div class="share-header">
          <div class="share-info">
            <div class="theme-badge">
              <span class="theme-icon">{{ getThemeIconByType(sharedData.theme) }}</span>
              <span class="theme-name">{{ sharedData.theme_name || sharedData.theme }}</span>
            </div>
            <div class="badges">
              <el-tag v-if="sharedData.is_deep" type="success" size="small">
                深度版
              </el-tag>
              <el-tag v-else type="info" size="small">
                精简版
              </el-tag>
            </div>
          </div>
        </div>

        <div class="sharer-info" v-if="sharedData.name">
          <div class="sharer-avatar">{{ sharedData.name.charAt(0).toUpperCase() }}</div>
          <div class="sharer-details">
            <div class="sharer-name">{{ sharedData.name }}</div>
            <div class="sharer-meta">分享了 TA 的前世故事</div>
          </div>
        </div>

        <div class="theme-description-section" v-if="sharedData.theme_description">
          <div class="section-header">
            <span class="section-icon">💫</span>
            <span class="section-title">前世主题解读</span>
          </div>
          <div class="description-content">
            <p>{{ sharedData.theme_description }}</p>
          </div>
        </div>

        <div class="story-section">
          <div class="section-header">
            <span class="section-icon">📖</span>
            <span class="section-title">前世故事</span>
          </div>
          
          <div class="story-content">
            <div class="story-content-inner" v-html="renderStoryContent(sharedData.story)"></div>
          </div>
        </div>

        <div v-if="!sharedData.is_deep" class="upgrade-section">
          <div class="upgrade-banner">
            <div class="upgrade-icon">👑</div>
            <div class="upgrade-info">
              <h3 class="upgrade-title">这是精简版故事</h3>
              <p class="upgrade-desc">
                解锁深度版可查看更详细的前世经历描写、重要事件的完整脉络
              </p>
            </div>
            <el-button 
              type="warning" 
              size="large"
              @click="goToHome"
              class="upgrade-btn"
            >
              <el-icon><MagicStick /></el-icon>
              探索自己的前世
            </el-button>
          </div>
        </div>

        <div class="share-footer">
          <div class="footer-actions">
            <el-button 
              type="primary"
              size="large"
              @click="goToHome"
              class="create-btn"
            >
              <el-icon><MagicStick /></el-icon>
              生成自己的前世故事
            </el-button>
          </div>
          
          <div class="share-count" v-if="sharedData.share_count">
            <span>已有 {{ sharedData.share_count }} 人查看过这个故事</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { usePastLifeShare, getPastLifeStarStyle } from '@/composables/usePastLifeAnalysis'

const router = useRouter()
const route = useRoute()

const {
  loading,
  sharedData,
  error,
  errorMessage,
  loadSharedStory
} = usePastLifeShare()

function getStarStyle(index) {
  return getPastLifeStarStyle(index)
}

function goToHome() {
  router.push('/past-life')
}

function getThemeIconByType(theme) {
  const icons = {
    warrior: '⚔️',
    scholar: '📜',
    artist: '🎨',
    royal: '👑',
    monk: '🧘',
    merchant: '💰',
    healer: '💚',
    adventurer: '🧭'
  }
  return icons[theme] || '✨'
}

function renderStoryContent(content) {
  if (!content) return ''
  
  let html = content
    .replace(/^# (.+)$/gm, '<h1 class="story-h1">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 class="story-h2">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="story-h3">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="story-strong">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="story-em">$1</em>')
    .replace(/^- (.+)$/gm, '<li class="story-li">$1</li>')
    .replace(/\n\n/g, '</p><p class="story-p">')
    .replace(/\n/g, '<br/>')
  
  return `<p class="story-p">${html}</p>`
}

onMounted(async () => {
  const shareCode = route.params.code
  if (!shareCode) {
    router.push('/past-life')
    return
  }
  
  await loadSharedStory(shareCode)
})
</script>

<style lang="scss" scoped>
.past-life-share-page {
  position: relative;
  min-height: 100vh;
  padding: 40px 24px;
  overflow-x: hidden;
}

.stars-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
  z-index: -1;
}

.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  animation: twinkle 4s infinite ease-in-out;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.2); }
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 32px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.page-description {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.6);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.content-section {
  max-width: 800px;
  margin: 0 auto;
}

.loading-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 100px 20px;
}

.loading-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
  
  &:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  &:nth-child(2) {
    animation-delay: -0.16s;
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.loading-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.error-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 24px;
  padding: 60px 40px;
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 12px 0;
}

.error-message {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 24px 0;
  line-height: 1.6;
}

.empty-placeholder {
  text-align: center;
  padding: 100px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 12px 0;
}

.empty-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px 0;
}

.share-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 24px;
  overflow: hidden;
}

.share-header {
  padding: 24px 28px;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.08) 0%, transparent 100%);
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
}

.share-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.theme-badge {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-icon {
  font-size: 32px;
}

.theme-name {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sharer-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
  background: rgba(168, 85, 247, 0.03);
}

.sharer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.sharer-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sharer-name {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.sharer-meta {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.theme-description-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.description-content {
  p {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.8;
    margin: 0;
    padding: 16px;
    background: rgba(168, 85, 247, 0.05);
    border-radius: 12px;
    border-left: 3px solid #f59e0b;
  }
}

.story-section {
  padding: 24px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.story-content {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 24px;
}

.story-content-inner {
  :deep(.story-h1) {
    font-size: 22px;
    font-weight: 800;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(168, 85, 247, 0.2);
  }
  
  :deep(.story-h2) {
    font-size: 18px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 24px 0 12px 0;
  }
  
  :deep(.story-h3) {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.8);
    margin: 16px 0 8px 0;
  }
  
  :deep(.story-p) {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.9;
    margin: 0 0 12px 0;
    text-indent: 2em;
  }
  
  :deep(.story-strong) {
    color: #f59e0b;
    font-weight: 700;
  }
  
  :deep(.story-em) {
    color: rgba(255, 255, 255, 0.85);
    font-style: italic;
  }
  
  :deep(.story-li) {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.7;
    padding-left: 16px;
    position: relative;
    margin: 4px 0;
    
    &::before {
      content: '•';
      position: absolute;
      left: 0;
      color: #f59e0b;
    }
  }
}

.upgrade-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.05);
}

.upgrade-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 16px;
  flex-wrap: wrap;
}

.upgrade-icon {
  font-size: 40px;
}

.upgrade-info {
  flex: 1;
  min-width: 200px;
}

.upgrade-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 6px 0;
}

.upgrade-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  line-height: 1.6;
}

.upgrade-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  border: none;
  white-space: nowrap;
  
  &:hover {
    background: linear-gradient(135deg, #d97706 0%, #dc2626 100%);
  }
}

.share-footer {
  padding: 24px 28px;
  text-align: center;
}

.footer-actions {
  margin-bottom: 20px;
}

.create-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  border: none;
  padding: 14px 32px;
  font-size: 16px;
  
  &:hover {
    background: linear-gradient(135deg, #d97706 0%, #dc2626 100%);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
  }
}

.share-count {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  
  span {
    background: rgba(168, 85, 247, 0.1);
    padding: 6px 16px;
    border-radius: 20px;
  }
}

.page-title,
.theme-name,
.sharer-name,
.story-h1,
.story-h2,
.story-h3,
.empty-title,
.error-title {
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.empty-desc,
.error-message,
.description-content,
.story-p,
.loading-text {
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .past-life-share-page {
    padding: 24px 16px;
  }
  
  .page-title {
    font-size: 24px;
    flex-direction: column;
    gap: 8px;
  }
  
  .title-icon {
    font-size: 28px;
  }
  
  .share-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .upgrade-banner {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .create-btn {
    width: 100%;
  }
}
</style>
