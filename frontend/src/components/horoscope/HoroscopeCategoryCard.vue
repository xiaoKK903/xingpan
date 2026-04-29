<template>
  <div class="category-card" :style="{ '--card-color': color }">
    <div class="card-header">
      <div class="icon-wrapper">
        <span class="card-icon">{{ icon }}</span>
      </div>
      <div class="header-content">
        <h4 class="card-title">{{ title }}</h4>
        <div class="score-display">
          <div class="score-bar-wrapper">
            <div class="score-bar-background"></div>
            <div 
              class="score-bar-fill" 
              :style="{ 
                width: `${displayScore}%`,
                background: `linear-gradient(90deg, ${color}, ${color}aa)`
              }"
            ></div>
          </div>
          <span class="score-value">{{ score }}分</span>
        </div>
      </div>
    </div>
    
    <div class="card-sections">
      <div class="section-item opportunity-section">
        <div class="section-label-wrapper">
          <span class="section-bullet opportunity-bullet"></span>
          <span class="section-label">今日机遇</span>
        </div>
        <p class="section-content">{{ opportunity }}</p>
      </div>
      
      <div class="section-item challenge-section">
        <div class="section-label-wrapper">
          <span class="section-bullet challenge-bullet"></span>
          <span class="section-label">今日挑战</span>
        </div>
        <p class="section-content">{{ challenge }}</p>
      </div>
      
      <div class="section-item advice-section">
        <div class="section-label-wrapper">
          <span class="section-bullet advice-bullet"></span>
          <span class="section-label">今日建议</span>
        </div>
        <p class="section-content">{{ advice }}</p>
      </div>
    </div>
    
    <div class="card-glow" :style="{ background: `radial-gradient(circle at 0 0, ${color}20 0%, transparent 50%)` }"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: '✨'
  },
  score: {
    type: Number,
    default: 0
  },
  opportunity: {
    type: String,
    default: ''
  },
  challenge: {
    type: String,
    default: ''
  },
  advice: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: '#8b5cf6'
  }
})

const displayScore = ref(0)

watch(() => props.score, (newScore) => {
  animateScore(newScore)
})

function animateScore(targetScore) {
  const duration = 800
  const startScore = displayScore.value
  const startTime = Date.now()
  
  function update() {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    const easeOut = 1 - Math.pow(1 - progress, 3)
    displayScore.value = Math.round(startScore + (targetScore - startScore) * easeOut)
    
    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }
  
  update()
}

onMounted(() => {
  animateScore(props.score)
})
</script>

<style lang="scss" scoped>
.category-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: default;
}

.category-card:hover {
  border-color: var(--card-color);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.category-card:hover .card-glow {
  opacity: 1;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.icon-wrapper {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  flex-shrink: 0;
}

.card-icon {
  font-size: 22px;
}

.header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-bar-wrapper {
  flex: 1;
  position: relative;
  height: 6px;
}

.score-bar-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
}

.score-bar-fill {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 3px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px var(--card-color);
}

.score-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--card-color);
  min-width: 32px;
  text-align: right;
}

.card-sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.opportunity-bullet {
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
}

.challenge-bullet {
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
}

.advice-bullet {
  background: #3b82f6;
  box-shadow: 0 0 6px #3b82f6;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
}

.section-content {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
  padding-left: 12px;
}

@media (max-width: 768px) {
  .category-card {
    padding: 16px;
  }

  .card-header {
    margin-bottom: 12px;
    padding-bottom: 12px;
    flex-direction: column;
    align-items: flex-start;
  }

  .icon-wrapper {
    width: 40px;
    height: 40px;
  }

  .card-icon {
    font-size: 20px;
  }

  .card-title {
    font-size: 14px;
  }

  .header-content {
    width: 100%;
  }

  .section-content {
    font-size: 12px;
  }
}
</style>
