<template>
  <div class="key-events-list">
    <div class="events-header">
      <h3 class="events-title">
        <span class="title-icon">🌟</span>
        关键星象事件
      </h3>
      <div class="events-filter" v-if="events.length > 0">
        <span class="filter-label">筛选：</span>
        <el-radio-group v-model="currentFilter" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="high">重要</el-radio-button>
          <el-radio-button value="lunar">月相</el-radio-button>
          <el-radio-button value="aspect">相位</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="events-container">
      <template v-if="filteredEvents.length > 0">
        <div 
          v-for="(event, index) in filteredEvents" 
          :key="index"
          class="event-card"
          :class="[
            `importance-${event.importance}`,
            `type-${event.type}`,
            { 'is-new': event.isNew }
          ]"
        >
          <div class="event-icon-container">
            <span class="event-icon">{{ event.icon }}</span>
            <div class="importance-badge" v-if="event.importance === 'high'">
              <el-icon size="12"><Star /></el-icon>
            </div>
          </div>
          
          <div class="event-content">
            <div class="event-header-row">
              <h4 class="event-title">{{ event.title }}</h4>
              <span class="event-type-tag" :style="{ backgroundColor: getTypeColor(event.type) }">
                {{ getTypeLabel(event.type) }}
              </span>
            </div>
            
            <p class="event-description">{{ event.description }}</p>
            
            <div class="event-meta" v-if="event.aspect_info">
              <div class="aspect-detail" v-if="event.aspect_info">
                <span class="aspect-planets">
                  <span class="planet">{{ event.aspect_info.transit_planet }}</span>
                  <span class="aspect-symbol" :style="{ color: getNatureColor(event.aspect_info.nature) }">
                    {{ event.aspect_info.aspect_symbol }}
                  </span>
                  <span class="planet">{{ event.aspect_info.natal_planet }}</span>
                </span>
                <span class="aspect-nature" :style="{ color: getNatureColor(event.aspect_info.nature) }">
                  {{ getNatureLabel(event.aspect_info.nature) }}
                </span>
                <span class="aspect-influence">
                  影响力 {{ Math.round((event.aspect_info.influence || 0) * 100) }}%
                </span>
              </div>
            </div>
            
            <div class="event-suggestion" v-if="event.suggestion">
              <span class="suggestion-label">💡 建议：</span>
              <span class="suggestion-text">{{ event.suggestion }}</span>
            </div>
          </div>
        </div>
      </template>

      <div class="no-events" v-else>
        <div class="no-events-icon">✨</div>
        <p class="no-events-text">今日无特殊星象事件</p>
        <p class="no-events-desc">能量平稳，适合日常事务</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Star } from '@element-plus/icons-vue'

const props = defineProps({
  events: {
    type: Array,
    default: () => []
  },
  aspects: {
    type: Array,
    default: () => []
  }
})

const currentFilter = ref('all')

const enrichedEvents = computed(() => {
  let result = [...(props.events || [])]
  
  const aspectEvents = (props.aspects || [])
    .filter(a => (a.influence || 0) >= 0.6)
    .slice(0, 5)
    .map(aspect => ({
      type: 'aspect_event',
      title: `${aspect.transit_planet || aspect.transitPlanet} ${aspect.aspect} ${aspect.natal_planet || aspect.natalPlanet}`,
      icon: aspect.aspect_symbol || aspect.aspectSymbol || '◎',
      description: getAspectDescription(aspect),
      importance: (aspect.influence || 0) >= 0.8 ? 'high' : 'medium',
      aspect_info: aspect,
      suggestion: getAspectSuggestion(aspect)
    }))
  
  result = [...result, ...aspectEvents]
  
  return result.sort((a, b) => {
    const importanceMap = { high: 3, medium: 2, low: 1 }
    return (importanceMap[b.importance] || 0) - (importanceMap[a.importance] || 0)
  })
})

const filteredEvents = computed(() => {
  if (currentFilter.value === 'all') return enrichedEvents.value
  
  const typeMap = {
    high: 'importance',
    lunar: 'lunar',
    aspect: 'aspect'
  }
  
  if (currentFilter.value === 'high') {
    return enrichedEvents.value.filter(e => e.importance === 'high')
  }
  
  if (currentFilter.value === 'lunar') {
    return enrichedEvents.value.filter(e => e.type?.includes('lunar'))
  }
  
  if (currentFilter.value === 'aspect') {
    return enrichedEvents.value.filter(e => e.type?.includes('aspect'))
  }
  
  return enrichedEvents.value
})

function getAspectDescription(aspect) {
  const nature = aspect.nature
  const transit = aspect.transit_planet || aspect.transitPlanet || '行星'
  const natal = aspect.natal_planet || aspect.natalPlanet || '行星'
  
  if (nature === 'harmonious') {
    return `行运${transit}与本命${natal}形成和谐相位，能量流动顺畅，容易获得正面反馈。`
  } else if (nature === 'challenging') {
    return `行运${transit}与本命${natal}形成紧张相位，需要更多注意力来应对相关领域的挑战。`
  }
  return `行运${transit}与本命${natal}形成相位，影响着你的${natal}相关领域。`
}

function getAspectSuggestion(aspect) {
  const nature = aspect.nature
  const aspectName = aspect.aspect
  
  if (nature === 'harmonious') {
    return '把握这个和谐能量，可以积极推进相关事务，适合学习、合作和创意表达。'
  } else if (nature === 'challenging') {
    return '保持耐心和灵活性，避免冲动决策，这是学习和成长的机会。'
  }
  return '注意观察这个相位带来的变化，适当调整计划。'
}

function getTypeLabel(type) {
  const labels = {
    lunar_event: '月相',
    planetary_event: '行星',
    aspect_event: '相位'
  }
  return labels[type] || '星象'
}

function getTypeColor(type) {
  const colors = {
    lunar_event: 'rgba(96, 165, 250, 0.3)',
    planetary_event: 'rgba(249, 115, 22, 0.3)',
    aspect_event: 'rgba(139, 92, 246, 0.3)'
  }
  return colors[type] || 'rgba(139, 92, 246, 0.3)'
}

function getNatureLabel(nature) {
  const labels = {
    harmonious: '和谐',
    challenging: '紧张',
    neutral: '中性'
  }
  return labels[nature] || '中性'
}

function getNatureColor(nature) {
  const colors = {
    harmonious: '#22c55e',
    challenging: '#ef4444',
    neutral: '#eab308'
  }
  return colors[nature] || '#8b5cf6'
}
</script>

<style lang="scss" scoped>
.key-events-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.events-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.events-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.title-icon {
  font-size: 18px;
}

.events-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  
  :deep(.el-radio-button__inner) {
    background: rgba(20, 20, 50, 0.6);
    border: 1px solid rgba(139, 92, 246, 0.2);
    color: rgba(255, 255, 255, 0.5);
    padding: 6px 14px;
    font-size: 12px;
  }
  
  :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    border-color: transparent;
    color: #fff;
  }
}

.filter-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.events-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
    transform: translateX(4px);
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.15);
  }
  
  &.importance-high {
    border-left: 3px solid #fbbf24;
    background: linear-gradient(90deg, rgba(251, 191, 36, 0.08) 0%, rgba(20, 20, 50, 0.8) 100%);
    
    .event-title {
      color: #fbbf24;
    }
  }
  
  &.type-lunar_event {
    .event-icon-container {
      background: radial-gradient(circle, rgba(96, 165, 250, 0.2) 0%, transparent 70%);
    }
  }
  
  &.type-planetary_event {
    .event-icon-container {
      background: radial-gradient(circle, rgba(249, 115, 22, 0.2) 0%, transparent 70%);
    }
  }
  
  &.type-aspect_event {
    .event-icon-container {
      background: radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%);
    }
  }
}

.event-icon-container {
  position: relative;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
  flex-shrink: 0;
}

.event-icon {
  font-size: 32px;
}

.importance-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  border-radius: 50%;
  color: rgba(0, 0, 0, 0.8);
  box-shadow: 0 2px 8px rgba(251, 191, 36, 0.4);
}

.event-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.event-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.event-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.event-type-tag {
  font-size: 10px;
  padding: 3px 10px;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.event-description {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.65);
  margin: 0;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.aspect-detail {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 8px;
  flex-wrap: wrap;
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 4px;
}

.planet {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.aspect-symbol {
  font-size: 16px;
  font-weight: 700;
  margin: 0 2px;
}

.aspect-nature {
  font-size: 11px;
  font-weight: 600;
}

.aspect-influence {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.event-suggestion {
  display: flex;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 8px;
  border-left: 2px solid #22c55e;
}

.suggestion-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(34, 197, 94, 0.9);
}

.suggestion-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.no-events {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  background: rgba(20, 20, 50, 0.5);
  border-radius: 16px;
  border: 1px dashed rgba(139, 92, 246, 0.2);
}

.no-events-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.6;
}

.no-events-text {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 4px 0;
}

.no-events-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

@media (max-width: 600px) {
  .events-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .event-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .event-icon-container {
    width: 48px;
    height: 48px;
  }
  
  .event-icon {
    font-size: 28px;
  }
  
  .aspect-detail {
    width: 100%;
  }
}
</style>
