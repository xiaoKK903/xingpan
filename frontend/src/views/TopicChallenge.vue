<template>
  <div class="topic-challenge-page">
    <div class="topic-banner" v-if="topic">
      <div class="banner-content">
        <div class="topic-tag-badge">{{ topic.topic_tag }}</div>
        <h1 class="topic-title">{{ topic.title }}</h1>
        <p class="topic-desc">{{ topic.description }}</p>
        <div class="topic-meta">
          <span class="meta-item">
            <el-icon><User /></el-icon>
            {{ topic.participant_count || 0 }} 人参与
          </span>
          <span class="meta-item" v-if="topic.time_status === 'active'">
            <el-icon><Clock /></el-icon>
            进行中
          </span>
          <span class="meta-item" v-else-if="topic.time_status === 'ended'">
            <el-icon><Warning /></el-icon>
            已结束
          </span>
          <span class="meta-item" v-else>
            <el-icon><Timer /></el-icon>
            即将开始
          </span>
        </div>
        
        <div class="topic-actions">
          <el-button 
            type="primary" 
            :icon="EditPen"
            class="join-btn"
            @click="goToCreatePost"
            v-if="topic.time_status === 'active' && !topic.user_participation"
          >
            参与挑战
          </el-button>
          <el-button 
            class="check-rank-btn"
            @click="switchTab('leaderboard')"
            v-if="topic.time_status === 'ended'"
          >
            查看排行榜
          </el-button>
          <el-button 
            type="success"
            class="claim-btn"
            @click="handleClaimReward"
            v-if="topic.time_status === 'ended' && topic.user_participation && !topic.user_participation.reward_claimed && topic.user_participation.reward_type"
            :loading="claiming"
          >
            领取奖励
          </el-button>
          <div class="my-participation" v-if="topic.user_participation">
            <span class="participation-label">我的排名：</span>
            <span class="participation-value">#{{ topic.user_participation.final_rank || '未结算' }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="empty-banner" v-else>
      <div class="empty-icon">🌟</div>
      <h2>暂无活跃话题</h2>
      <p class="empty-subtitle">敬请期待下周的星座话题挑战</p>
      <div class="empty-actions">
        <el-button 
          type="primary" 
          :icon="StarFilled"
          class="empty-btn"
          @click="goToSocialPlaza"
        >
          去星光广场逛逛
        </el-button>
      </div>
    </div>
    
    <div class="content-container" v-if="topic">
      <div class="tabs-header">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'posts' }"
          @click="activeTab = 'posts'; reloadPosts()"
        >
          <el-icon><Document /></el-icon>
          参与帖子
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'leaderboard' }"
          @click="activeTab = 'leaderboard'; reloadLeaderboard()"
        >
          <el-icon><Trophy /></el-icon>
          排行榜
        </button>
      </div>
      
      <div class="tab-content">
        <div class="posts-section" v-if="activeTab === 'posts'">
          <div v-if="loading && posts.length === 0" class="loading-state">
            <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          
          <div class="posts-list" v-else>
            <SocialPlazaCard
              v-for="post in posts" 
              :key="post.id"
              :post="post"
              @liked="onPostLiked"
              @deleted="onPostDeleted"
              @shared="onPostShared"
            />
            
            <div v-if="!loading && posts.length === 0" class="empty-state">
              <div class="empty-icon">📝</div>
              <p class="empty-title">暂无参与内容</p>
              <p class="empty-desc">来成为第一个参与话题的人吧！</p>
              <el-button 
                type="primary" 
                :icon="EditPen"
                @click="goToCreatePost"
                v-if="topic.time_status === 'active'"
              >
                发布内容
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
              <span>已经到底啦 ✨</span>
            </div>
          </div>
        </div>
        
        <div class="leaderboard-section" v-else>
          <div v-if="loadingLeaderboard && leaderboard.length === 0" class="loading-state">
            <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
            <span>加载排行榜中...</span>
          </div>
          
          <div v-else class="leaderboard-content">
            <div class="top-three" v-if="leaderboard.length >= 3">
              <div class="rank-card rank-2" @click="scrollToRank(1)">
                <div class="rank-badge">2</div>
                <el-avatar :size="50" class="rank-avatar">
                  {{ leaderboard[1]?.username?.[0] || '?' }}
                </el-avatar>
                <div class="rank-username">{{ leaderboard[1]?.username || '匿名用户' }}</div>
                <div class="rank-score">{{ leaderboard[1]?.hot_score || 0 }} 热度</div>
              </div>
              
              <div class="rank-card rank-1" @click="scrollToRank(0)">
                <div class="rank-badge">1</div>
                <div class="crown">👑</div>
                <el-avatar :size="60" class="rank-avatar">
                  {{ leaderboard[0]?.username?.[0] || '?' }}
                </el-avatar>
                <div class="rank-username">{{ leaderboard[0]?.username || '匿名用户' }}</div>
                <div class="rank-score">{{ leaderboard[0]?.hot_score || 0 }} 热度</div>
              </div>
              
              <div class="rank-card rank-3" @click="scrollToRank(2)">
                <div class="rank-badge">3</div>
                <el-avatar :size="50" class="rank-avatar">
                  {{ leaderboard[2]?.username?.[0] || '?' }}
                </el-avatar>
                <div class="rank-username">{{ leaderboard[2]?.username || '匿名用户' }}</div>
                <div class="rank-score">{{ leaderboard[2]?.hot_score || 0 }} 热度</div>
              </div>
            </div>
            
            <div class="rank-list">
              <div 
                v-for="(item, index) in leaderboard" 
                :key="item.user_id"
                class="rank-item"
                :class="{ 'my-rank': item.user_id === currentUserId }"
                :data-rank="index + 1"
              >
                <div class="rank-number" :class="'rank-' + (index + 1)">
                  <span v-if="index < 3" class="top-badge">#{{ index + 1 }}</span>
                  <span v-else>{{ index + 1 }}</span>
                </div>
                <el-avatar :size="40" class="rank-item-avatar">
                  {{ item.username?.[0] || '?' }}
                </el-avatar>
                <div class="rank-item-info">
                  <div class="rank-item-username">
                    {{ item.username || '匿名用户' }}
                    <el-tag v-if="item.is_vip" size="small" type="warning" effect="dark">VIP</el-tag>
                    <el-tag v-if="item.user_id === currentUserId" size="small" type="primary">我</el-tag>
                  </div>
                  <div class="rank-item-post" v-if="item.post_title">
                    {{ item.post_title || item.post_content?.substring(0, 50) }}
                  </div>
                </div>
                <div class="rank-item-score">
                  <span class="score-value">{{ item.hot_score || 0 }}</span>
                  <span class="score-label">热度</span>
                </div>
              </div>
            </div>
            
            <div v-if="!loadingLeaderboard && leaderboard.length === 0" class="empty-state leaderboard-empty">
              <div class="empty-icon">🏆</div>
              <p class="empty-title">暂无排行数据</p>
              <p class="empty-desc">快来参与话题挑战吧！</p>
              <div class="empty-actions">
                <el-button 
                  type="primary" 
                  :icon="EditPen"
                  class="empty-btn"
                  @click="goToCreatePost"
                  v-if="topic?.time_status === 'active'"
                >
                  发布内容参与挑战
                </el-button>
                <el-button 
                  class="empty-btn-link"
                  @click="goToSocialPlaza"
                >
                  去星光广场逛逛
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <CreatePostDialog 
      v-model="showCreateDialog"
      :topic_challenge_id="topic?.id"
      @success="onPostCreated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Clock, User, Warning, Timer, EditPen, 
  Document, Trophy, Loading, StarFilled 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { topicChallengeApi, socialPlazaApi } from '@/api'
import SocialPlazaCard from '@/components/social-plaza/SocialPlazaCard.vue'
import CreatePostDialog from '@/components/social-plaza/CreatePostDialog.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const topic = ref(null)
const activeTab = ref('posts')
const posts = ref([])
const leaderboard = ref([])
const totalCount = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const loadingLeaderboard = ref(false)
const showCreateDialog = ref(false)
const claiming = ref(false)

const currentUserId = computed(() => userStore.user?.id || null)

const PAGE_SIZE = 20

watch(() => route.params, (newParams) => {
  loadTopic()
}, { immediate: true })

async function loadTopic() {
  try {
    const result = await topicChallengeApi.getActiveTopic()
    topic.value = result?.topic || null
    if (topic.value) {
      reloadPosts()
    }
  } catch (error) {
    console.error('加载话题失败:', error)
    topic.value = null
  }
}

function reloadPosts() {
  posts.value = []
  totalCount.value = 0
  loadPosts(false)
}

async function loadPosts(append = false) {
  if (!topic.value) return
  
  if (append) {
    if (loadingMore.value) return
    loadingMore.value = true
  } else {
    if (loading.value) return
    loading.value = true
  }
  
  try {
    const params = {
      limit: PAGE_SIZE,
      offset: append ? posts.value.length : 0,
    }
    
    const result = await topicChallengeApi.getTopicPosts(topic.value.id, params)
    
    totalCount.value = result.total_count || 0
    
    if (append) {
      posts.value = [...posts.value, ...(result.posts || [])]
    } else {
      posts.value = result.posts || []
    }
    
  } catch (error) {
    console.error('加载帖子失败:', error)
    if (!append) {
      ElMessage.error(error.message || '加载失败')
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMorePosts() {
  loadPosts(true)
}

function reloadLeaderboard() {
  leaderboard.value = []
  loadLeaderboard()
}

async function loadLeaderboard() {
  if (!topic.value) return
  
  loadingLeaderboard.value = true
  
  try {
    const result = await topicChallengeApi.getTopicLeaderboard(topic.value.id, { limit: 100 })
    leaderboard.value = result.leaderboard || []
  } catch (error) {
    console.error('加载排行榜失败:', error)
    ElMessage.error(error.message || '加载排行榜失败')
  } finally {
    loadingLeaderboard.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'leaderboard') {
    reloadLeaderboard()
  }
}

function goToCreatePost() {
  if (!userStore.isLoggedIn && !localStorage.getItem('token')) {
    router.push('/login')
    return
  }
  showCreateDialog.value = true
}

function onPostCreated() {
  ElMessage.success('发布成功，已参与话题挑战！')
  loadTopic()
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

async function handleClaimReward() {
  if (!topic.value) return
  
  claiming.value = true
  try {
    const result = await topicChallengeApi.claimReward(topic.value.id)
    ElMessage.success(`领取成功！${result.reward_description}`)
    loadTopic()
  } catch (error) {
    console.error('领取奖励失败:', error)
  } finally {
    claiming.value = false
  }
}

function scrollToRank(index) {
  const element = document.querySelector(`.rank-item[data-rank="${index + 1}"]`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function goToSocialPlaza() {
  router.push('/social-plaza')
}
</script>

<style lang="scss" scoped>
.topic-challenge-page {
  width: 100%;
  min-height: 100%;
}

.topic-banner {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(251, 191, 36, 0.2) 50%, rgba(99, 102, 241, 0.25) 100%);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  padding: 32px 40px;
}

.banner-content {
  max-width: 1200px;
  margin: 0 auto;
}

.topic-tag-badge {
  display: inline-block;
  padding: 6px 16px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.2));
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: #fbbf24;
  margin-bottom: 16px;
}

.topic-title {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #c4b5fd 0%, #fbbf24 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 12px 0;
}

.topic-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.topic-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.topic-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.join-btn,
.claim-btn {
  background: linear-gradient(135deg, #8b5cf6, #f59e0b);
  border: none;
  padding: 12px 32px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 25px;
  
  &:hover {
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.5);
  }
}

.check-rank-btn {
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  border-radius: 25px;
  padding: 10px 28px;
  
  &:hover {
    background: rgba(139, 92, 246, 0.25);
    border-color: rgba(139, 92, 246, 0.5);
  }
}

.my-participation {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 20px;
}

.participation-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.participation-value {
  font-size: 15px;
  font-weight: 700;
  color: #4ade80;
}

.empty-banner {
  background: rgba(139, 92, 246, 0.1);
  padding: 60px 40px;
  text-align: center;
}

.empty-banner .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-banner h2 {
  font-size: 24px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 8px 0;
}

.empty-banner .empty-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 24px 0;
}

.empty-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 8px;
}

.empty-btn {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  
  &:hover {
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
  }
}

.empty-btn-link {
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    border-color: rgba(139, 92, 246, 0.5);
  }
}

.leaderboard-empty {
  .empty-actions {
    margin-top: 16px;
  }
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 40px;
}

.tabs-header {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: transparent;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    color: #c4b5fd;
  }
  
  &.active {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.15));
    color: #c4b5fd;
    font-weight: 600;
  }
}

.tab-content {
  min-height: 400px;
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

.leaderboard-content {
  .top-three {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 24px;
    margin-bottom: 32px;
    padding: 24px 0;
  }
  
  .rank-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 20px;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-4px);
    }
    
    .rank-badge {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      font-weight: 700;
      font-size: 14px;
    }
    
    .rank-avatar {
      background: linear-gradient(135deg, #8b5cf6, #6366f1);
    }
    
    .rank-username {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
    
    .rank-score {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
    }
  }
  
  .rank-1 {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.1));
    border: 1px solid rgba(251, 191, 36, 0.3);
    order: 2;
    padding-bottom: 32px;
    
    .crown {
      font-size: 32px;
      margin-top: -20px;
    }
    
    .rank-badge {
      background: linear-gradient(135deg, #fbbf24, #f59e0b);
      color: #fff;
    }
  }
  
  .rank-2 {
    background: rgba(192, 192, 192, 0.15);
    border: 1px solid rgba(192, 192, 192, 0.3);
    order: 1;
    padding-bottom: 16px;
    
    .rank-badge {
      background: linear-gradient(135deg, #9ca3af, #6b7280);
      color: #fff;
    }
  }
  
  .rank-3 {
    background: rgba(205, 127, 50, 0.15);
    border: 1px solid rgba(205, 127, 50, 0.3);
    order: 3;
    padding-bottom: 16px;
    
    .rank-badge {
      background: linear-gradient(135deg, #cd7f32, #b8860b);
      color: #fff;
    }
  }
  
  .rank-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .rank-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 20px;
    background: rgba(139, 92, 246, 0.05);
    border: 1px solid rgba(139, 92, 246, 0.1);
    border-radius: 12px;
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.2);
    }
    
    &.my-rank {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(139, 92, 246, 0.08));
      border-color: rgba(34, 197, 94, 0.3);
    }
  }
  
  .rank-number {
    width: 40px;
    text-align: center;
    font-weight: 600;
    font-size: 15px;
    
    &.rank-1,
    &.rank-2,
    &.rank-3 {
      .top-badge {
        display: none;
      }
    }
    
    &.rank-1 { color: #fbbf24; }
    &.rank-2 { color: #9ca3af; }
    &.rank-3 { color: #cd7f32; }
  }
  
  .rank-item-avatar {
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
  }
  
  .rank-item-info {
    flex: 1;
    min-width: 0;
  }
  
  .rank-item-username {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 4px;
  }
  
  .rank-item-post {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .rank-item-score {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    
    .score-value {
      font-size: 18px;
      font-weight: 700;
      background: linear-gradient(135deg, #c4b5fd, #fbbf24);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .score-label {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

@media (max-width: 960px) {
  .topic-banner {
    padding: 24px 20px;
  }
  
  .content-container {
    padding: 16px 20px;
  }
  
  .topic-title {
    font-size: 24px;
  }
  
  .topic-meta {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .topic-actions {
    flex-wrap: wrap;
  }
  
  .leaderboard-content .top-three {
    flex-direction: column;
    align-items: center;
    gap: 16px;
    
    .rank-card {
      order: unset;
      width: 100%;
      max-width: 280px;
      
      &.rank-1 {
        order: 1;
      }
      
      &.rank-2 {
        order: 2;
      }
      
      &.rank-3 {
        order: 3;
      }
    }
  }
}
</style>
