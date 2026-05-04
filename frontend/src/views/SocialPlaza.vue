<template>
  <div class="social-plaza-page">
    <div class="topic-banner" v-if="activeTopic" @click="goToTopicChallenge">
      <div class="banner-inner">
        <div class="banner-left">
          <span class="topic-badge">🔥 本周话题挑战</span>
          <span class="topic-tag">{{ activeTopic.topic_tag }}</span>
          <span class="topic-title">{{ activeTopic.title }}</span>
        </div>
        <div class="banner-right">
          <span class="participant-count">
            <el-icon><User /></el-icon>
            {{ activeTopic.participant_count || 0 }} 人参与
          </span>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
    
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">星光广场</h1>
          <p class="page-subtitle">✨ 分享你的星盘故事，遇见同好的灵魂</p>
        </div>
        <div class="header-actions">
          <el-button 
            type="primary" 
            :icon="EditPen"
            class="create-btn"
            @click="openCreateDialog"
          >
            分享内容
          </el-button>
        </div>
      </div>
    </div>
    
    <div class="filter-bar">
      <div class="sort-tabs">
        <button 
          class="sort-tab" 
          :class="{ active: sortBy === 'latest' }"
          @click="sortBy = 'latest'; reloadPosts()"
        >
          <el-icon><Clock /></el-icon>
          最新
        </button>
        <button 
          class="sort-tab" 
          :class="{ active: sortBy === 'hot' }"
          @click="sortBy = 'hot'; reloadPosts()"
        >
          <el-icon><TrendCharts /></el-icon>
          热门
        </button>
      </div>
      
      <div class="filter-right">
        <div class="topic-filter" v-if="activeTopic">
          <el-dropdown trigger="click" class="topic-dropdown">
            <span class="dropdown-trigger">
              <span class="filter-label">话题：</span>
              <span class="filter-value">
                {{ currentTopicLabel }}
              </span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="filterByTopic(null)">
                  全部内容
                </el-dropdown-item>
                <el-dropdown-item 
                  class="topic-dropdown-item"
                  @click="filterByTopic(activeTopic.id)"
                >
                  <span class="topic-icon">🔥</span>
                  <span class="topic-tag">{{ activeTopic.topic_tag }}</span>
                  <span class="topic-name">{{ activeTopic.title }}</span>
                </el-dropdown-item>
                <el-dropdown-item @click="goToTopicChallenge">
                  查看往期话题 →
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="type-filter">
          <el-dropdown trigger="click" class="type-dropdown">
            <span class="dropdown-trigger">
              <span>{{ currentTypeLabel }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="filterByType(null)">
                  全部类型
                </el-dropdown-item>
                <el-dropdown-item 
                  v-for="type in postTypes" 
                  :key="type.key"
                  @click="filterByType(type.key)"
                >
                  <span class="type-icon">{{ type.icon }}</span>
                  <span>{{ type.name }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
    
    <div class="content-container">
      <div class="posts-column">
        <div class="posts-list">
          <div 
            v-for="post in posts" 
            :key="post.id" 
            class="post-wrapper"
          >
            <SocialPlazaCard
              :post="post"
              @liked="onPostLiked"
              @deleted="onPostDeleted"
              @shared="onPostShared"
            />
          </div>
          
          <div v-if="loading && posts.length === 0" class="loading-state">
            <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          
          <div v-if="!loading && posts.length === 0 && totalCount === 0" class="empty-state">
            <div class="empty-icon">🌙</div>
            <p class="empty-title">星光广场还没有内容</p>
            <p class="empty-desc">来成为第一个分享的人吧！</p>
            <el-button 
              type="primary" 
              :icon="EditPen"
              @click="openCreateDialog"
            >
              发布第一条内容
            </el-button>
          </div>
          
          <div 
            v-if="!loading && posts.length > 0 && posts.length < totalCount" 
            class="load-more-section"
          >
            <el-button 
              class="load-more-btn"
              :loading="loadingMore"
              @click="loadMorePosts"
            >
              {{ loadingMore ? '加载中...' : '加载更多' }}
            </el-button>
          </div>
          
          <div 
            v-if="!loading && posts.length > 0 && posts.length >= totalCount" 
            class="no-more-section"
          >
            <el-icon><StarFilled /></el-icon>
            <span>已经到底啦，去发布你的内容吧 ✨</span>
          </div>
        </div>
      </div>
      
      <div class="sidebar">
        <div class="sidebar-card intro-card">
          <div class="card-icon">✨</div>
          <h3 class="card-title">关于星光广场</h3>
          <div class="card-content">
            <p>这里是星盘爱好者的聚集地，你可以：</p>
            <ul class="feature-list">
              <li>
                <span class="feature-icon">♊</span>
                <span>分享合盘卡牌，遇见同好</span>
              </li>
              <li>
                <span class="feature-icon">🌟</span>
                <span>记录每日运势，寻找共鸣</span>
              </li>
              <li>
                <span class="feature-icon">🌙</span>
                <span>讲述前世今生，探索缘分</span>
              </li>
              <li>
                <span class="feature-icon">🎴</span>
                <span>展示抽卡结果，交流心得</span>
              </li>
            </ul>
          </div>
          <div class="card-note">
            <el-icon><InfoFilled /></el-icon>
            <span>无评论区，让交流更纯粹</span>
          </div>
        </div>
        
        <div class="sidebar-card hot-tags-card" v-if="hotTags.length > 0">
          <h3 class="card-title">热门标签</h3>
          <div class="tags-cloud">
            <el-tag 
              v-for="tag in hotTags" 
              :key="tag"
              size="large"
              effect="plain"
              class="hot-tag"
              @click="searchByTag(tag)"
            >
              #{{ tag }}
            </el-tag>
          </div>
        </div>
        
        <div class="sidebar-card vip-card">
          <div class="vip-badge">
            <el-icon><Star /></el-icon>
            <span>星钻会员</span>
          </div>
          <p class="vip-desc">发布内容享专属金边卡片，彰显尊贵身份</p>
          <el-button 
            type="primary" 
            class="vip-btn"
            @click="goToVipCenter"
          >
            立即开通
          </el-button>
        </div>
      </div>
    </div>
    
    <CreatePostDialog 
      v-model="showCreateDialog"
      :topic_challenge_id="activeTopic?.id"
      @success="onPostCreated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Clock, TrendCharts, ArrowDown, ArrowRight, EditPen, 
  Loading, Star, StarFilled, InfoFilled, User
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { socialPlazaApi, topicChallengeApi } from '@/api'
import SocialPlazaCard from '@/components/social-plaza/SocialPlazaCard.vue'
import CreatePostDialog from '@/components/social-plaza/CreatePostDialog.vue'

const router = useRouter()
const userStore = useUserStore()

const posts = ref([])
const totalCount = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const sortBy = ref('latest')
const postType = ref(null)
const topicChallengeId = ref(null)
const showCreateDialog = ref(false)
const postTypes = ref([])
const activeTopic = ref(null)

const hotTags = ref(['合盘缘分', '今日运势', '前世故事', '星座抽卡', '星盘分析'])

const PAGE_SIZE = 20

const currentTypeLabel = computed(() => {
  if (!postType.value) return '全部类型'
  const type = postTypes.value.find(t => t.key === postType.value)
  return type ? `${type.icon} ${type.name}` : '全部类型'
})

const currentTopicLabel = computed(() => {
  if (!topicChallengeId.value || !activeTopic.value) return '全部内容'
  return activeTopic.value.topic_tag
})

onMounted(() => {
  loadPostTypes()
  loadPosts()
  loadActiveTopic()
})

async function loadActiveTopic() {
  try {
    const result = await topicChallengeApi.getActiveTopic()
    activeTopic.value = result?.topic || null
  } catch (error) {
    console.error('加载活跃话题失败:', error)
    activeTopic.value = null
  }
}

function goToTopicChallenge() {
  router.push('/topic-challenge')
}

async function loadPostTypes() {
  try {
    const result = await socialPlazaApi.getPostTypes()
    postTypes.value = result.types || []
  } catch (error) {
    console.error('获取内容类型失败:', error)
    postTypes.value = [
      { key: 'synastry_card', name: '合盘卡牌', icon: '♊', description: '分享你的合盘结果' },
      { key: 'daily_horoscope', name: '今日运势', icon: '🌟', description: '分享你的每日星运' },
      { key: 'past_life_story', name: '前世今生', icon: '🌙', description: '分享你的前世故事' },
      { key: 'card_draw', name: '星盘抽卡', icon: '🎴', description: '分享你的抽卡结果' },
    ]
  }
}

async function loadPosts(append = false) {
  if (append) {
    if (loadingMore.value) return
    loadingMore.value = true
  } else {
    if (loading.value) return
    loading.value = true
  }
  
  try {
    const params = {
      sort_by: sortBy.value,
      limit: PAGE_SIZE,
      offset: append ? posts.value.length : 0,
    }
    
    if (postType.value) {
      params.post_type = postType.value
    }
    
    if (topicChallengeId.value) {
      params.topic_challenge_id = topicChallengeId.value
    }
    
    const result = await socialPlazaApi.getPosts(params)
    
    totalCount.value = result.total_count || 0
    
    if (append) {
      posts.value = [...posts.value, ...(result.posts || [])]
    } else {
      posts.value = result.posts || []
    }
    
  } catch (error) {
    console.error('加载内容失败:', error)
    if (!append) {
      ElMessage.error(error.message || '加载内容失败，请稍后重试')
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function reloadPosts() {
  loadPosts(false)
}

function loadMorePosts() {
  loadPosts(true)
}

function filterByType(typeKey) {
  postType.value = typeKey
  reloadPosts()
}

function filterByTopic(topicId) {
  topicChallengeId.value = topicId
  reloadPosts()
}

function openCreateDialog() {
  if (!userStore.isLoggedIn && !localStorage.getItem('token')) {
    router.push('/login')
    return
  }
  showCreateDialog.value = true
}

function onPostCreated() {
  reloadPosts()
}

function onPostLiked({ isLiked, likeCount }) {
}

function onPostDeleted(postId) {
  posts.value = posts.value.filter(p => p.id !== postId)
  totalCount.value = Math.max(0, totalCount.value - 1)
}

function onPostShared(post) {
  try {
    socialPlazaApi.recordShare({
      post_id: post.id,
      share_type: 'link',
      share_text: post.content || post.title
    })
  } catch (e) {}
}

function searchByTag(tag) {
}

function goToVipCenter() {
  router.push('/vip-center')
}
</script>

<style lang="scss" scoped>
.social-plaza-page {
  width: 100%;
  min-height: 100%;
  padding: 0;
}

.topic-banner {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(139, 92, 246, 0.15) 50%, rgba(99, 102, 241, 0.1) 100%);
  border-bottom: 1px solid rgba(251, 191, 36, 0.2);
  padding: 12px 40px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.3) 0%, rgba(139, 92, 246, 0.2) 50%, rgba(99, 102, 241, 0.15) 100%);
  }
}

.banner-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topic-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(245, 158, 11, 0.15));
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #f87171;
}

.topic-tag {
  padding: 4px 10px;
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #fbbf24;
}

.topic-title {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.banner-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.participant-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.arrow-icon {
  color: rgba(255, 255, 255, 0.4);
  transition: transform 0.3s ease;
}

.topic-banner:hover .arrow-icon {
  transform: translateX(4px);
  color: #c4b5fd;
}

.page-header {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
  padding: 24px 40px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  .page-title {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa 0%, #fbbf24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 8px 0;
  }
  
  .page-subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0;
  }
}

.create-btn {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 12px;
  
  &:hover {
    background: linear-gradient(135deg, #a78bfa, #818cf8);
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
  }
}

.filter-bar {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
}

.sort-tabs {
  display: flex;
  gap: 8px;
}

.sort-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 20px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    color: #c4b5fd;
  }
  
  &.active {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.15));
    color: #c4b5fd;
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.15);
  }
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topic-filter,
.type-filter {
  .dropdown-trigger {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    color: rgba(255, 255, 255, 0.7);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba(139, 92, 246, 0.15);
      border-color: rgba(139, 92, 246, 0.3);
      color: #c4b5fd;
    }
    
    .arrow-icon {
      font-size: 12px;
    }
  }
}

.topic-filter {
  .dropdown-trigger {
    .filter-label {
      color: rgba(255, 255, 255, 0.5);
    }
    .filter-value {
      color: #fbbf24;
      font-weight: 600;
    }
  }
}

.topic-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .topic-icon {
    font-size: 14px;
  }
  .topic-tag {
    padding: 2px 8px;
    background: rgba(251, 191, 36, 0.15);
    border: 1px solid rgba(251, 191, 36, 0.3);
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    color: #fbbf24;
  }
  .topic-name {
    color: rgba(255, 255, 255, 0.8);
  }
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 40px;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 32px;
}

.posts-column {
  min-width: 0;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.6);
}

.loading-state {
  gap: 12px;
  
  .loading-icon {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  gap: 16px;
  
  .empty-icon {
    font-size: 48px;
  }
  
  .empty-title {
    font-size: 18px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
    margin: 0;
  }
  
  .empty-desc {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0;
  }
}

.load-more-section,
.no-more-section {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.load-more-btn {
  padding: 10px 32px;
  border-radius: 20px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  color: #c4b5fd;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.4);
    color: #ddd6fe;
  }
}

.no-more-section {
  gap: 8px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-card {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.1);
  border-radius: 16px;
  padding: 20px;
}

.intro-card {
  .card-icon {
    font-size: 32px;
    text-align: center;
    margin-bottom: 12px;
  }
  
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 12px 0;
    text-align: center;
  }
  
  .card-content {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.6;
    margin-bottom: 16px;
    
    > p {
      margin: 0 0 12px 0;
    }
  }
  
  .feature-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .feature-list li {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }
  
  .feature-icon {
    font-size: 16px;
    line-height: 1.5;
  }
  
  .card-note {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 12px;
    background: rgba(34, 197, 94, 0.08);
    border-radius: 10px;
    font-size: 12px;
    color: rgba(34, 197, 94, 0.8);
  }
}

.hot-tags-card {
  .card-title {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 16px 0;
  }
  
  .tags-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .hot-tag {
    cursor: pointer;
    transition: all 0.3s ease;
    background: rgba(139, 92, 246, 0.1);
    border-color: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
    
    &:hover {
      background: rgba(139, 92, 246, 0.2);
      border-color: rgba(139, 92, 246, 0.4);
      color: #ddd6fe;
    }
  }
}

.vip-card {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
  border-color: rgba(251, 191, 36, 0.2);
  text-align: center;
  
  .vip-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    border-radius: 20px;
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
  }
  
  .vip-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 16px 0;
    line-height: 1.5;
  }
  
  .vip-btn {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    border: none;
    width: 100%;
    border-radius: 10px;
    font-weight: 600;
    
    &:hover {
      box-shadow: 0 4px 15px rgba(251, 191, 36, 0.4);
    }
  }
}

@media (max-width: 960px) {
  .content-container {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    display: none;
  }
  
  .page-header {
    padding: 20px;
  }
  
  .filter-bar {
    padding: 12px 20px;
  }
  
  .content-container {
    padding: 16px 20px;
  }
}
</style>
