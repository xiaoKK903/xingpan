<template>
  <div class="story-card-wrapper" ref="cardWrapper">
    <div 
      class="story-card" 
      :class="[
        `rarity-${cardData?.rarity || 'common'}`,
        { 'is-mounting': isMounting, 'is-mounted': cardData?.is_mounted }
      ]"
      :style="cardStyle"
    >
      <div class="card-glow-effect" :style="glowStyle"></div>
      
      <div class="card-header">
        <div class="card-rarity-badge" :style="rarityBadgeStyle">
          <span class="rarity-icon">{{ rarityIcon }}</span>
          <span class="rarity-name">{{ cardData?.rarity_name || getRarityName(cardData?.rarity) }}</span>
        </div>
        <div class="card-template-icon" v-if="cardData?.metadata?.template_icon">
          {{ cardData.metadata.template_icon }}
        </div>
      </div>
      
      <div class="card-content">
        <div class="card-persons">
          <div class="person-badge">
            <span class="person-initials">{{ getInitials(cardData?.person_a_name) }}</span>
            <span class="person-name">{{ cardData?.person_a_name || '人物A' }}</span>
          </div>
          <div class="persons-connector">
            <span class="connector-icon">💕</span>
          </div>
          <div class="person-badge">
            <span class="person-initials">{{ getInitials(cardData?.person_b_name) }}</span>
            <span class="person-name">{{ cardData?.person_b_name || '人物B' }}</span>
          </div>
        </div>
        
        <h3 class="card-headline">{{ cardData?.headline || '特别的羁绊' }}</h3>
        <p class="card-subheadline" v-if="cardData?.subheadline">{{ cardData.subheadline }}</p>
        
        <div class="card-story-short" v-if="cardData?.story_short">
          <p>{{ cardData.story_short }}</p>
        </div>
        
        <div class="card-meta-info" v-if="showMeta">
          <div class="meta-item" v-if="cardData?.compatibility_score">
            <span class="meta-icon">💯</span>
            <span class="meta-value">{{ cardData.compatibility_score }}分</span>
          </div>
          <div class="meta-item" v-if="cardData?.dominant_element">
            <span class="meta-icon">{{ getElementIcon(cardData.dominant_element) }}</span>
            <span class="meta-value">{{ getElementName(cardData.dominant_element) }}</span>
          </div>
          <div class="meta-item" v-if="cardData?.key_aspect">
            <span class="meta-icon">✨</span>
            <span class="meta-value aspect-text">{{ cardData.key_aspect }}</span>
          </div>
        </div>
      </div>
      
      <div class="card-footer" v-if="showActions">
        <button 
          class="action-btn mount-btn"
          :class="{ mounted: cardData?.is_mounted }"
          @click="handleMountToggle"
          :disabled="isMounting"
        >
          <span class="btn-icon">{{ cardData?.is_mounted ? '✓' : '📌' }}</span>
          <span class="btn-text">{{ cardData?.is_mounted ? '已挂载' : '挂载到故事墙' }}</span>
        </button>
        <button class="action-btn share-btn" @click="handleShare">
          <span class="btn-icon">📤</span>
          <span class="btn-text">分享</span>
        </button>
        <button class="action-btn detail-btn" @click="handleViewDetail">
          <span class="btn-icon">📖</span>
          <span class="btn-text">查看详情</span>
        </button>
      </div>
      
      <div class="card-mounted-badge" v-if="cardData?.is_mounted && !showActions">
        <span class="mounted-icon">📌</span>
        <span>已挂载</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { storyCardApi } from '@/api'

const props = defineProps({
  cardData: {
    type: Object,
    default: null
  },
  showActions: {
    type: Boolean,
    default: true
  },
  showMeta: {
    type: Boolean,
    default: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['mount', 'share', 'view-detail', 'update'])

const cardWrapper = ref(null)
const isMounting = ref(false)

const RARITY_COLORS = {
  common: { color: '#94a3b8', glow: 'rgba(148, 163, 184, 0.3)', name: '普通' },
  rare: { color: '#3b82f6', glow: 'rgba(59, 130, 246, 0.4)', name: '稀有' },
  epic: { color: '#a855f7', glow: 'rgba(168, 85, 247, 0.5)', name: '史诗' },
  legendary: { color: '#f59e0b', glow: 'rgba(245, 158, 11, 0.6)', name: '传说' }
}

const RARITY_ICONS = {
  common: '⭐',
  rare: '💎',
  epic: '🌟',
  legendary: '👑'
}

const ELEMENT_ICONS = {
  fire: '🔥',
  earth: '🪨',
  air: '💨',
  water: '💧'
}

const ELEMENT_NAMES = {
  fire: '火象',
  earth: '土象',
  air: '风象',
  water: '水象'
}

const cardStyle = computed(() => {
  const rarity = props.cardData?.rarity || 'common'
  const config = RARITY_COLORS[rarity] || RARITY_COLORS.common
  
  return {
    '--rarity-color': config.color,
    '--rarity-glow': config.glow
  }
})

const glowStyle = computed(() => {
  const rarity = props.cardData?.rarity || 'common'
  const config = RARITY_COLORS[rarity] || RARITY_COLORS.common
  
  return {
    background: `radial-gradient(ellipse at center, ${config.glow} 0%, transparent 70%)`
  }
})

const rarityBadgeStyle = computed(() => {
  const rarity = props.cardData?.rarity || 'common'
  const config = RARITY_COLORS[rarity] || RARITY_COLORS.common
  
  return {
    backgroundColor: `${config.color}20`,
    borderColor: config.color,
    color: config.color
  }
})

const rarityIcon = computed(() => {
  const rarity = props.cardData?.rarity || 'common'
  return RARITY_ICONS[rarity] || '⭐'
})

function getRarityName(rarity) {
  return RARITY_COLORS[rarity]?.name || '普通'
}

function getElementIcon(element) {
  return ELEMENT_ICONS[element] || '✨'
}

function getElementName(element) {
  return ELEMENT_NAMES[element] || element
}

function getInitials(name) {
  if (!name) return '?'
  const firstChar = name.charAt(0)
  return firstChar.toUpperCase()
}

async function handleMountToggle() {
  if (!props.cardData?.id || isMounting.value) return
  
  isMounting.value = true
  try {
    const newMountState = !props.cardData.is_mounted
    await storyCardApi.toggleMount(props.cardData.id, newMountState)
    
    const updatedCard = {
      ...props.cardData,
      is_mounted: newMountState,
      mounted_at: newMountState ? new Date().toISOString() : null
    }
    
    ElMessage.success(newMountState ? '已挂载到故事墙' : '已从故事墙移除')
    emit('mount', updatedCard)
    emit('update', updatedCard)
  } catch (error) {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    isMounting.value = false
  }
}

async function handleShare() {
  if (!props.cardData?.id) return
  
  try {
    const result = await storyCardApi.share(props.cardData.id)
    
    const shareUrl = `${window.location.origin}/story-card/share/${result.share_code}`
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: props.cardData.headline || '合盘故事卡',
          text: props.cardData.story_short || `${props.cardData.person_a_name} 与 ${props.cardData.person_b_name} 的合盘故事卡`,
          url: shareUrl
        })
      } catch (err) {
        if (err.name !== 'AbortError') {
          await copyToClipboard(shareUrl)
        }
      }
    } else {
      await copyToClipboard(shareUrl)
    }
    
    emit('share', { ...props.cardData, share_code: result.share_code })
  } catch (error) {
    ElMessage.error('分享失败，请稍后重试')
  }
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('分享链接已复制到剪贴板')
  } catch {
    ElMessage.info('您的浏览器不支持自动复制，请手动复制')
  }
}

function handleViewDetail() {
  emit('view-detail', { ...props.cardData })
}

defineExpose({
  cardWrapper,
  handleMountToggle,
  handleShare,
  handleViewDetail
})
</script>

<style lang="scss" scoped>
.story-card-wrapper {
  width: 100%;
  max-width: 400px;
  perspective: 1000px;
}

.story-card {
  position: relative;
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.98), rgba(15, 15, 40, 0.99));
  border-radius: 20px;
  border: 2px solid var(--rarity-color, rgba(139, 92, 246, 0.3));
  overflow: hidden;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.4),
    0 0 40px var(--rarity-glow, rgba(139, 92, 246, 0.1));
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 
      0 30px 80px rgba(0, 0, 0, 0.5),
      0 0 60px var(--rarity-glow, rgba(139, 92, 246, 0.15));
  }
  
  &.rarity-legendary {
    animation: legendary-glow 3s ease-in-out infinite;
    
    &::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(
        45deg,
        transparent 30%,
        rgba(245, 158, 11, 0.1) 50%,
        transparent 70%
      );
      animation: legendary-shine 4s linear infinite;
      pointer-events: none;
    }
  }
  
  &.rarity-epic {
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.6), transparent);
      animation: epic-border-glow 2s ease-in-out infinite;
    }
  }
  
  &.is-mounted {
    border-style: dashed;
  }
}

@keyframes legendary-glow {
  0%, 100% { box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 40px rgba(245, 158, 11, 0.3); }
  50% { box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 80px rgba(245, 158, 11, 0.5); }
}

@keyframes legendary-shine {
  0% { transform: translateX(-50%) translateY(-50%) rotate(0deg); }
  100% { transform: translateX(-50%) translateY(-50%) rotate(360deg); }
}

@keyframes epic-border-glow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.card-glow-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  opacity: 0.5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(180deg, rgba(139, 92, 246, 0.08), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.card-rarity-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid;
  font-size: 0.8rem;
  font-weight: 600;
  
  .rarity-icon {
    font-size: 1rem;
  }
}

.card-template-icon {
  font-size: 1.5rem;
  opacity: 0.8;
}

.card-content {
  padding: 20px;
}

.card-persons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.person-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 100px;
}

.person-initials {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.2));
  border: 2px solid rgba(139, 92, 246, 0.4);
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
}

.person-name {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  text-align: center;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.persons-connector {
  display: flex;
  align-items: center;
  justify-content: center;
  
  .connector-icon {
    font-size: 1.8rem;
    animation: heartbeat 1.5s ease-in-out infinite;
  }
}

@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

.card-headline {
  margin: 0 0 8px;
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  text-align: center;
  line-height: 1.4;
}

.card-subheadline {
  margin: 0 0 16px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  line-height: 1.5;
}

.card-story-short {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.1);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
  
  p {
    margin: 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.7;
  }
}

.card-meta-info {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 16px;
  
  .meta-icon {
    font-size: 0.9rem;
  }
  
  .meta-value {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .aspect-text {
    font-size: 0.75rem;
    font-family: monospace;
  }
}

.card-footer {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.action-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.5);
    transform: translateY(-2px);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
  
  .btn-icon {
    font-size: 0.9rem;
  }
  
  .btn-text {
    white-space: nowrap;
  }
}

.mount-btn {
  &.mounted {
    background: rgba(34, 197, 94, 0.15);
    border-color: rgba(34, 197, 94, 0.4);
    color: rgba(34, 197, 94, 0.9);
    
    &:hover {
      background: rgba(34, 197, 94, 0.2);
    }
  }
}

.share-btn {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
  
  &:hover {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
  }
}

.detail-btn {
  background: rgba(139, 92, 246, 0.1);
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
  }
}

.card-mounted-badge {
  position: absolute;
  top: 12px;
  right: -28px;
  transform: rotate(45deg);
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  padding: 2px 36px;
  font-size: 0.65rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.4);
  z-index: 10;
  
  .mounted-icon {
    font-size: 0.7rem;
  }
}
</style>
