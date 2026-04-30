<template>
  <div class="social-card-container" ref="cardContainer">
    <div class="card-main-card">
      <div class="card-header-section">
        <div class="card-avatar">
          <span class="avatar-text">{{ nameInitial }}</span>
        </div>
        <div class="card-info">
          <h3 class="card-name">{{ displayName }}</h3>
          <p class="card-big-three">{{ bigThreeSummary }}</p>
          <div class="card-element-tags" v-if="dominantElement">
            <span class="element-tag" :class="elementClass">{{ dominantElement }}象</span>
            <span class="quality-tag">{{ dominantQuality }}</span>
          </div>
        </div>
        <div class="card-share-actions" v-if="showActions">
          <button class="share-btn" @click="handleShare">
            <el-icon><Share /></el-icon>
          </button>
          <button class="download-btn" @click="handleDownload">
            <el-icon><Download /></el-icon>
          </button>
        </div>
      </div>

      <div class="card-ai-intro" v-if="aiIntro">
        <div class="intro-icon">
          <el-icon><MagicStick /></el-icon>
        </div>
        <div class="intro-content">
          <p>{{ aiIntro }}</p>
        </div>
      </div>

      <div class="card-soul-keywords" v-if="soulKeywords.length > 0">
        <div class="section-title">
          <span class="section-icon">✨</span>
          <span class="section-name">灵魂关键词</span>
        </div>
        <div class="keywords-container">
          <div 
            v-for="(keyword, index) in soulKeywords" 
            :key="index"
            class="keyword-tag"
            :class="getKeywordClass(keyword)"
            :title="keyword.description"
          >
            <span class="keyword-text">{{ keyword.word }}</span>
            <span class="keyword-type" v-if="keyword.type">{{ keyword.type }}</span>
          </div>
        </div>
      </div>

      <div class="card-avoid-guide" v-if="avoidGuide.length > 0">
        <div class="section-title">
          <span class="section-icon">⚠️</span>
          <span class="section-name">避雷指南</span>
          <span class="section-hint">了解这些，相处更融洽</span>
        </div>
        <div class="avoid-list">
          <div 
            v-for="(item, index) in avoidGuide" 
            :key="index"
            class="avoid-item"
            :class="getAvoidClass(item)"
          >
            <span class="avoid-severity" v-if="item.severity === '高'">
              <el-icon><Warning /></el-icon>
            </span>
            <span class="avoid-severity low" v-else>
              <el-icon><InfoFilled /></el-icon>
            </span>
            <div class="avoid-content">
              <span class="avoid-topic">{{ item.topic }}</span>
              <span class="avoid-reason" v-if="item.reason">{{ item.reason }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card-recommended-topics" v-if="recommendedTopics.length > 0">
        <div class="section-title">
          <span class="section-icon">💬</span>
          <span class="section-name">共同话题推荐</span>
          <span class="section-hint">聊这些，拉近彼此距离</span>
        </div>
        <div class="topics-container">
          <div 
            v-for="(topic, index) in recommendedTopics" 
            :key="index"
            class="topic-card"
            @click="toggleTopicExpand(index)"
          >
            <div class="topic-header">
              <span class="topic-interest" :class="getInterestClass(topic.interest_level)">
                {{ topic.interest_level }}
              </span>
              <span class="topic-name">{{ topic.topic }}</span>
              <el-icon class="topic-expand-icon" :class="{ expanded: expandedTopics.includes(index) }">
                <CaretBottom />
              </el-icon>
            </div>
            <Transition name="slide-down">
              <div v-if="expandedTopics.includes(index)" class="topic-starters">
                <p class="starters-title">开场白建议：</p>
                <ul class="starters-list">
                  <li v-for="(starter, sIndex) in topic.conversation_starters" :key="sIndex">
                    {{ starter }}
                  </li>
                </ul>
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <div v-if="hasConflicts" class="card-conflict-note">
        <div class="conflict-icon">
          <el-icon><InfoFilled /></el-icon>
        </div>
        <div class="conflict-content">
          <p class="conflict-summary">{{ conflictSummary }}</p>
          <p class="conflict-detail">性格中有多重特质的整合，让TA更加立体</p>
        </div>
      </div>

      <div class="card-footer">
        <p class="footer-text">基于星盘性格画像 · 社交破冰助手</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Share, Download, MagicStick, Warning, InfoFilled, CaretBottom } from '@element-plus/icons-vue'
import html2canvas from 'html2canvas'

const props = defineProps({
  cardData: {
    type: Object,
    default: null
  },
  showActions: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['share', 'download'])

const cardContainer = ref(null)
const expandedTopics = ref([])

const displayName = computed(() => {
  return props.cardData?.name || '用户'
})

const nameInitial = computed(() => {
  const name = displayName.value
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const bigThreeSummary = computed(() => {
  return props.cardData?.big_three?.summary || ''
})

const dominantElement = computed(() => {
  return props.cardData?.distribution?.dominant_element || ''
})

const dominantQuality = computed(() => {
  const quality = props.cardData?.distribution?.dominant_quality || ''
  const qualityMap = {
    '开创': '开创型',
    '固定': '固定型', 
    '变动': '变动型'
  }
  return qualityMap[quality] || quality
})

const elementClass = computed(() => {
  const map = {
    '火': 'fire',
    '土': 'earth',
    '风': 'air',
    '水': 'water'
  }
  return map[dominantElement.value] || ''
})

const aiIntro = computed(() => {
  return props.cardData?.ai_intro || ''
})

const soulKeywords = computed(() => {
  return props.cardData?.soul_keywords || []
})

const avoidGuide = computed(() => {
  return props.cardData?.avoid_guide || []
})

const recommendedTopics = computed(() => {
  return props.cardData?.recommended_topics || []
})

const hasConflicts = computed(() => {
  return props.cardData?.conflict_analysis?.has_conflicts || false
})

const conflictSummary = computed(() => {
  return props.cardData?.conflict_analysis?.resolution_summary || ''
})

function getKeywordClass(keyword) {
  const typeClass = {
    '核心特质': 'core',
    '内在需求': 'inner',
    '外在表现': 'outer',
    '能量集中': 'energy',
    '对冲整合': 'integrated',
    '元素风格': 'element'
  }
  return typeClass[keyword.type] || ''
}

function getAvoidClass(item) {
  return item.severity === '高' ? 'high' : 'low'
}

function getInterestClass(level) {
  const levelMap = {
    '高': 'high',
    '中高': 'medium-high',
    '中': 'medium'
  }
  return levelMap[level] || 'medium'
}

function toggleTopicExpand(index) {
  const idx = expandedTopics.value.indexOf(index)
  if (idx > -1) {
    expandedTopics.value.splice(idx, 1)
  } else {
    expandedTopics.value.push(index)
  }
}

async function handleShare() {
  emit('share', props.cardData)
  
  if (navigator.share) {
    try {
      await navigator.share({
        title: `${displayName.value}的社交名片`,
        text: bigThreeSummary.value,
        url: window.location.href
      })
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.log('分享已取消')
      }
    }
  } else {
    try {
      await navigator.clipboard.writeText(`${displayName.value}的社交名片：${bigThreeSummary.value}`)
      ElMessage.success('已复制到剪贴板')
    } catch {
      ElMessage.info('您的浏览器不支持分享功能')
    }
  }
}

async function handleDownload() {
  emit('download', props.cardData)
  
  if (!cardContainer.value) {
    ElMessage.error('无法找到名片元素')
    return
  }
  
  try {
    ElMessage.info('正在生成图片...')
    
    const canvas = await html2canvas(cardContainer.value, {
      scale: 2,
      useCORS: true,
      backgroundColor: null,
      logging: false
    })
    
    const link = document.createElement('a')
    link.download = `${displayName.value}_社交名片_${Date.now()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    
    ElMessage.success('名片已保存')
  } catch (error) {
    console.error('生成图片失败:', error)
    ElMessage.error('生成图片失败，请稍后重试')
  }
}
</script>

<style lang="scss" scoped>
.social-card-container {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
}

.card-main-card {
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.98), rgba(15, 15, 35, 0.99));
  border-radius: 24px;
  border: 1px solid rgba(139, 92, 246, 0.25);
  overflow: hidden;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.4),
    0 0 100px rgba(139, 92, 246, 0.1);
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #8b5cf6, #6366f1, #06b6d4);
  }
}

.card-header-section {
  display: flex;
  align-items: center;
  padding: 24px;
  background: linear-gradient(180deg, rgba(139, 92, 246, 0.1), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.card-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
  
  .avatar-text {
    font-size: 1.8rem;
    font-weight: 700;
    color: #fff;
  }
}

.card-info {
  flex: 1;
  margin-left: 16px;
}

.card-name {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
}

.card-big-three {
  margin: 4px 0 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.card-element-tags {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.element-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  
  &.fire {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.3);
  }
  
  &.earth {
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.3);
  }
  
  &.air {
    background: rgba(96, 165, 250, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(96, 165, 250, 0.3);
  }
  
  &.water {
    background: rgba(147, 197, 253, 0.15);
    color: #93c5fd;
    border: 1px solid rgba(147, 197, 253, 0.3);
  }
}

.quality-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(167, 139, 250, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(167, 139, 250, 0.3);
}

.card-share-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
}

.share-btn,
.download-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: #a78bfa;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    transform: translateY(-2px);
  }
}

.card-ai-intro {
  display: flex;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.05), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.intro-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.2), transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
  flex-shrink: 0;
}

.intro-content {
  flex: 1;
  
  p {
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.85);
  }
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  
  .section-icon {
    font-size: 1.1rem;
  }
  
  .section-name {
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
  }
  
  .section-hint {
    margin-left: auto;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
  }
}

.card-soul-keywords,
.card-avoid-guide,
.card-recommended-topics {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
}

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.keyword-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &.core {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1));
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.3);
  }
  
  &.inner {
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.2), rgba(96, 165, 250, 0.1));
    color: #60a5fa;
    border: 1px solid rgba(96, 165, 250, 0.3);
  }
  
  &.outer {
    background: linear-gradient(135deg, rgba(74, 222, 128, 0.2), rgba(74, 222, 128, 0.1));
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.3);
  }
  
  &.energy {
    background: linear-gradient(135deg, rgba(248, 113, 113, 0.2), rgba(248, 113, 113, 0.1));
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.3);
  }
  
  &.integrated {
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.2), rgba(167, 139, 250, 0.1));
    color: #a78bfa;
    border: 1px solid rgba(167, 139, 250, 0.3);
  }
  
  &.element {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.1));
    color: #c4b5fd;
    border: 1px solid rgba(139, 92, 246, 0.3);
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2);
  }
  
  .keyword-type {
    font-size: 0.7rem;
    opacity: 0.7;
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
}

.avoid-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.avoid-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  
  &.high {
    background: rgba(248, 113, 113, 0.08);
    border: 1px solid rgba(248, 113, 113, 0.2);
  }
  
  &.low {
    background: rgba(251, 191, 36, 0.05);
    border: 1px solid rgba(251, 191, 36, 0.15);
  }
}

.avoid-severity {
  flex-shrink: 0;
  margin-top: 2px;
  color: #f87171;
  
  &.low {
    color: #fbbf24;
  }
}

.avoid-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.avoid-topic {
  font-size: 0.95rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.avoid-reason {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.topics-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-card {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(99, 102, 241, 0.03));
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(99, 102, 241, 0.05));
  }
}

.topic-header {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  gap: 12px;
}

.topic-interest {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
  
  &.high {
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
  }
  
  &.medium-high {
    background: rgba(96, 165, 250, 0.15);
    color: #60a5fa;
  }
  
  &.medium {
    background: rgba(167, 139, 250, 0.15);
    color: #a78bfa;
  }
}

.topic-name {
  flex: 1;
  font-size: 0.95rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.topic-expand-icon {
  color: rgba(255, 255, 255, 0.4);
  transition: transform 0.3s ease;
  
  &.expanded {
    transform: rotate(180deg);
  }
}

.topic-starters {
  padding: 0 16px 16px;
  margin-top: -8px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  padding-top: 12px;
}

.starters-title {
  margin: 0 0 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.starters-list {
  margin: 0;
  padding-left: 16px;
  list-style-type: none;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  
  li {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.5;
    position: relative;
    padding-left: 16px;
    
    &::before {
      content: '💡';
      position: absolute;
      left: -4px;
      top: 0;
      font-size: 0.75rem;
    }
  }
}

.card-conflict-note {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.08), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
}

.conflict-icon {
  color: #a78bfa;
  flex-shrink: 0;
  margin-top: 2px;
}

.conflict-content {
  flex: 1;
}

.conflict-summary {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
  color: #a78bfa;
}

.conflict-detail {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.card-footer {
  padding: 16px 24px;
  text-align: center;
  background: rgba(0, 0, 0, 0.2);
}

.footer-text {
  margin: 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.3);
}

.slide-down-enter-active {
  transition: all 0.3s ease;
}

.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
