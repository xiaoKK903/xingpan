<template>
  <div class="ai-interpretation">
    <div class="interpretation-header">
      <h3 class="interpretation-title">
        <span class="title-icon">🔮</span>
        AI动态解读
      </h3>
      <div class="interpretation-meta">
        <span class="meta-item">
          <span class="meta-icon">📅</span>
          <span class="meta-text">{{ targetDate }}</span>
        </span>
        <span class="meta-item" v-if="interpretationData">
          <span class="meta-icon">⚡</span>
          <span class="meta-text">{{ interpretationData.mood }} {{ interpretationData.mood_label }}</span>
        </span>
      </div>
    </div>

    <div class="interpretation-content">
      <div v-if="loading" class="loading-container">
        <div class="loading-visual">
          <div class="ai-pulse">
            <div class="pulse-ring"></div>
            <div class="pulse-ring delay-1"></div>
            <div class="pulse-ring delay-2"></div>
          </div>
          <div class="ai-icon">🤖</div>
        </div>
        <div class="loading-text">
          <p class="loading-main">正在为您解析今日星象...</p>
          <p class="loading-sub">结合行运相位生成专属解读</p>
        </div>
      </div>

      <div v-else-if="error" class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-content">
          <p class="error-title">解读生成失败</p>
          <p class="error-text">{{ errorMessage }}</p>
          <el-button type="primary" size="small" @click="$emit('retry')" class="retry-btn">
            重新生成
          </el-button>
        </div>
      </div>

      <div v-else-if="interpretationData?.interpretation" class="interpretation-text">
        <div class="dimensions-summary" v-if="interpretationData.dimensions_summary?.length">
          <div 
            v-for="dim in interpretationData.dimensions_summary" 
            :key="dim.name"
            class="dimension-badge"
            :style="{ '--dim-color': dim.color }"
          >
            <span class="dim-badge-icon">{{ dim.icon }}</span>
            <span class="dim-badge-name">{{ dim.name }}</span>
            <div class="dim-badge-score">
              <span class="score-number">{{ dim.score }}</span>
              <span class="score-label">分</span>
            </div>
            <span class="dim-badge-level" :style="{ color: getLevelColor(dim.level) }">
              {{ dim.level_label }}
            </span>
          </div>
        </div>

        <div class="interpretation-body" v-html="formattedInterpretation"></div>

        <div class="interpretation-footer">
          <div class="footer-info">
            <span class="footer-label">生成时间</span>
            <span class="footer-value">{{ generateTime }}</span>
          </div>
          <div class="footer-actions">
            <el-button size="small" @click="copyInterpretation" class="copy-btn">
              <el-icon><DocumentCopy /></el-icon>
              复制解读
            </el-button>
            <el-button size="small" @click="shareInterpretation" class="share-btn">
              <el-icon><Share /></el-icon>
              分享
            </el-button>
          </div>
        </div>
      </div>

      <div v-else class="empty-container">
        <div class="empty-icon">✨</div>
        <p class="empty-text">暂无解读内容</p>
        <p class="empty-desc">请先计算行运数据以生成解读</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { DocumentCopy, Share } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  interpretationData: {
    type: Object,
    default: () => null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  },
  errorMessage: {
    type: String,
    default: ''
  },
  targetDate: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['retry', 'share'])

const generateTime = computed(() => {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
})

const formattedInterpretation = computed(() => {
  if (!props.interpretationData?.interpretation) return ''
  
  let content = props.interpretationData.interpretation
  
  content = content.replace(/##\s+([^\n]+)/g, '<h4 class="section-title">$1</h4>')
  content = content.replace(/###\s+([^\n]+)/g, '<h5 class="subsection-title">$1</h5>')
  
  content = content.replace(/\d+\.\s+([^\n]+)/g, '<li class="interpretation-item">$1</li>')
  
  content = content.replace(/\n\n/g, '</p><p class="interpretation-paragraph">')
  content = `<p class="interpretation-paragraph">${content}</p>`
  
  return content
})

function getLevelColor(level) {
  const colors = {
    high: '#22c55e',
    medium_high: '#eab308',
    medium: '#60a5fa',
    medium_low: '#f97316',
    low: '#ef4444'
  }
  return colors[level] || '#8b5cf6'
}

async function copyInterpretation() {
  if (!props.interpretationData?.interpretation) return
  
  try {
    await navigator.clipboard.writeText(props.interpretationData.interpretation)
    ElMessage.success('解读内容已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败，请手动复制')
  }
}

function shareInterpretation() {
  emit('share')
}
</script>

<style lang="scss" scoped>
.ai-interpretation {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  padding: 24px;
}

.interpretation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.interpretation-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.title-icon {
  font-size: 20px;
}

.interpretation-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.meta-icon {
  font-size: 14px;
}

.meta-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.interpretation-content {
  min-height: 200px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-visual {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 20px;
}

.ai-pulse {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.pulse-ring {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid rgba(139, 92, 246, 0.3);
  border-radius: 50%;
  animation: pulse-expand 2s ease-out infinite;
}

.pulse-ring.delay-1 {
  animation-delay: 0.5s;
}

.pulse-ring.delay-2 {
  animation-delay: 1s;
}

@keyframes pulse-expand {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

.ai-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 36px;
}

.loading-text {
  text-align: center;
}

.loading-main {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 4px 0;
}

.loading-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

.error-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.error-icon {
  font-size: 32px;
}

.error-content {
  flex: 1;
}

.error-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(248, 113, 113, 0.9);
  margin: 0 0 4px 0;
}

.error-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 12px 0;
}

.retry-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
}

.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 4px 0;
}

.empty-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  margin: 0;
}

.dimensions-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.dimension-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(20, 20, 50, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--dim-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.15);
  }
}

.dim-badge-icon {
  font-size: 18px;
}

.dim-badge-name {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
}

.dim-badge-score {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-left: 4px;
  padding-left: 8px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.score-number {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
}

.score-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

.dim-badge-level {
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
}

.interpretation-body {
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.75);
}

.interpretation-paragraph {
  margin: 0 0 16px 0;
  font-size: 14px;
  text-indent: 2em;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(167, 139, 250, 0.95);
  margin: 24px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 16px 0 8px 0;
}

.interpretation-item {
  list-style: none;
  position: relative;
  padding-left: 20px;
  margin: 8px 0;
  font-size: 14px;
  
  &::before {
    content: '•';
    position: absolute;
    left: 0;
    color: rgba(139, 92, 246, 0.8);
    font-weight: bold;
  }
}

.interpretation-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(139, 92, 246, 0.15);
}

.footer-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
}

.footer-value {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.copy-btn,
.share-btn {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  color: rgba(167, 139, 250, 0.9);
  
  &:hover {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.15) 100%);
    border-color: rgba(139, 92, 246, 0.4);
  }
}

@media (max-width: 768px) {
  .ai-interpretation {
    padding: 16px;
  }
  
  .interpretation-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .dimensions-summary {
    gap: 8px;
  }
  
  .dimension-badge {
    padding: 8px 10px;
  }
  
  .interpretation-footer {
    flex-direction: column;
    gap: 12px;
  }
  
  .footer-actions {
    width: 100%;
    
    .el-button {
      flex: 1;
      justify-content: center;
    }
  }
}
</style>
