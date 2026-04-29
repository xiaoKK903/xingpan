<template>
  <div class="transit-dashboard">
    <div class="weather-header">
      <div class="weather-mood">
        <span class="mood-icon">{{ overall?.mood || '☀️' }}</span>
        <div class="mood-info">
          <span class="mood-label">{{ overall?.mood_label || '晴朗' }}</span>
          <span class="date-display">{{ dateDisplay }}</span>
        </div>
      </div>
      
      <div class="energy-score">
        <svg class="score-svg" viewBox="0 0 120 120">
          <defs>
            <linearGradient :id="`score-gradient-${uniqueId}`" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" :style="`stop-color:${scoreGradientStart};stop-opacity:1`" />
              <stop offset="100%" :style="`stop-color:${scoreGradientEnd};stop-opacity:1`" />
            </linearGradient>
          </defs>
          
          <circle class="score-bg" cx="60" cy="60" r="50" />
          <circle 
            class="score-progress" 
            cx="60" 
            cy="60" 
            r="50"
            :style="{ 
              strokeDasharray: getStrokeDasharray(overall?.overall_score || 50),
              stroke: `url(#score-gradient-${uniqueId})`
            }"
          />
        </svg>
        <div class="score-inner">
          <span class="score-value">{{ overall?.overall_score || 0 }}</span>
          <span class="score-unit">分</span>
          <span class="score-label">今日能量指数</span>
        </div>
      </div>
    </div>

    <div class="weather-description">
      <p>{{ overall?.description || '正在加载星象数据...' }}</p>
    </div>

    <div class="dimension-cards">
      <div 
        v-for="dim in dimensions" 
        :key="dim.dimension"
        class="dimension-card"
        :style="{ 
          '--dim-color': dim.color,
          '--dim-score': `${dim.score / 100}`
        }"
      >
        <div class="dim-header">
          <span class="dim-icon">{{ dim.icon }}</span>
          <span class="dim-name">{{ dim.name_cn }}</span>
        </div>
        
        <div class="dim-score-bar">
          <div class="score-track"></div>
          <div 
            class="score-fill" 
            :style="{ 
              width: `${dim.score}%`,
              backgroundColor: dim.color
            }"
          ></div>
          <div class="score-marker" :style="{ left: `${dim.score}%` }"></div>
        </div>
        
        <div class="dim-footer">
          <span class="dim-level" :style="{ color: getDimensionColor(dim.level) }">
            {{ dim.level_label }}
          </span>
          <span class="dim-score-value">{{ dim.score }}分</span>
        </div>
      </div>
    </div>

    <div class="astro-status-row">
      <div class="astro-status-card moon-phase">
        <div class="status-icon">{{ moonPhase?.phase_symbol || '🌑' }}</div>
        <div class="status-info">
          <span class="status-label">月相</span>
          <span class="status-value">{{ moonPhase?.phase_name || '新月' }}</span>
          <span class="status-detail">照亮 {{ moonPhase?.illumination || 0 }}%</span>
        </div>
      </div>
      
      <div class="astro-status-card mercury-status" :class="{ 'is-retrograde': mercuryStatus?.is_retrograde }">
        <div class="status-icon">☿</div>
        <div class="status-info">
          <span class="status-label">水星</span>
          <span class="status-value">{{ mercuryStatus?.status || '顺行' }}</span>
          <span class="status-detail" v-if="mercuryStatus?.is_retrograde">注意沟通细节</span>
        </div>
      </div>
      
      <div class="astro-status-card next-event">
        <div class="status-icon">📅</div>
        <div class="status-info">
          <span class="status-label">重要提醒</span>
          <span class="status-value" v-if="nextMoonEvent">
            {{ nextMoonEvent.type }}: {{ nextMoonEvent.days }}天后
          </span>
          <span class="status-value" v-else>暂无</span>
        </div>
      </div>
    </div>

    <div v-if="highDims.length || lowDims.length" class="energy-highlights">
      <div v-if="highDims.length" class="highlight-section positive">
        <div class="highlight-icon">✨</div>
        <div class="highlight-content">
          <span class="highlight-label">能量旺盛</span>
          <span class="highlight-value">{{ highDims.join('、') }}</span>
        </div>
      </div>
      <div v-if="lowDims.length" class="highlight-section caution">
        <div class="highlight-icon">⚠️</div>
        <div class="highlight-content">
          <span class="highlight-label">需要关注</span>
          <span class="highlight-value">{{ lowDims.join('、') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  overall: {
    type: Object,
    default: () => null
  },
  dimensions: {
    type: Array,
    default: () => []
  },
  moonPhase: {
    type: Object,
    default: () => null
  },
  mercuryStatus: {
    type: Object,
    default: () => null
  },
  dateDisplay: {
    type: String,
    default: ''
  }
})

const uniqueId = ref(Math.random().toString(36).substr(2, 9))

const scoreGradientStart = computed(() => {
  const score = props.overall?.overall_score || 50
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#eab308'
  if (score >= 40) return '#f97316'
  return '#ef4444'
})

const scoreGradientEnd = computed(() => {
  const score = props.overall?.overall_score || 50
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#ca8a04'
  if (score >= 40) return '#ea580c'
  return '#dc2626'
})

const highDims = computed(() => {
  return props.dimensions
    .filter(d => d.level === 'high' || d.level === 'medium_high')
    .map(d => d.name_cn)
})

const lowDims = computed(() => {
  return props.dimensions
    .filter(d => d.level === 'low' || d.level === 'medium_low')
    .map(d => d.name_cn)
})

const nextMoonEvent = computed(() => {
  if (!props.moonPhase) return null
  
  const fullMoonDays = props.moonPhase.next_full_moon_days
  const newMoonDays = props.moonPhase.next_new_moon_days
  
  if (fullMoonDays <= newMoonDays && fullMoonDays <= 7) {
    return { type: '满月', days: Math.round(fullMoonDays) }
  } else if (newMoonDays <= 7) {
    return { type: '新月', days: Math.round(newMoonDays) }
  }
  return null
})

function getStrokeDasharray(score) {
  const circumference = 314.16
  const dasharray = (score / 100) * circumference
  return `${dasharray} ${circumference}`
}

function getDimensionColor(level) {
  const colors = {
    high: '#22c55e',
    medium_high: '#eab308',
    medium: '#60a5fa',
    medium_low: '#f97316',
    low: '#ef4444'
  }
  return colors[level] || '#60a5fa'
}
</script>

<style lang="scss" scoped>
.transit-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  padding: 24px;
}

.weather-mood {
  display: flex;
  align-items: center;
  gap: 20px;
}

.mood-icon {
  font-size: 64px;
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.mood-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mood-label {
  font-size: 28px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.date-display {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.energy-score {
  position: relative;
  width: 120px;
  height: 120px;
}

.score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 8;
  stroke-linecap: round;
}

.score-progress {
  fill: none;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dasharray 1.5s ease;
}

.score-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.score-value {
  font-size: 28px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1;
}

.score-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.score-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.weather-description {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
  border-left: 3px solid #8b5cf6;
  border-radius: 0 12px 12px 0;
  padding: 16px 20px;
  
  p {
    margin: 0;
    font-size: 14px;
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.75);
  }
}

.dimension-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.dimension-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15);
  }
}

.dim-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dim-icon {
  font-size: 22px;
}

.dim-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.dim-score-bar {
  position: relative;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: visible;
}

.score-track {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.score-fill {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 3px;
  transition: width 1s ease;
}

.score-marker {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  background: #fff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.dim-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dim-level {
  font-size: 12px;
  font-weight: 500;
}

.dim-score-value {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.astro-status-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.astro-status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  padding: 16px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
  }
}

.astro-status-card.mercury-status.is-retrograde {
  border-color: rgba(249, 115, 22, 0.4);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(20, 20, 50, 0.8) 100%);
}

.status-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%);
  border-radius: 50%;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.status-value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.status-detail {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.energy-highlights {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.highlight-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
}

.highlight-section.positive {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.highlight-section.caution {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%);
  border: 1px solid rgba(249, 115, 22, 0.3);
}

.highlight-icon {
  font-size: 24px;
}

.highlight-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.highlight-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.highlight-value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

@media (max-width: 900px) {
  .dimension-cards {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .astro-status-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .weather-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .weather-mood {
    flex-direction: column;
  }
  
  .dimension-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .astro-status-row {
    grid-template-columns: 1fr;
  }
  
  .energy-highlights {
    grid-template-columns: 1fr;
  }
}
</style>
