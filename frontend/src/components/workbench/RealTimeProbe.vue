<template>
  <div class="real-time-probe">
    <div class="probe-header">
      <div class="probe-title">
        <span class="probe-icon">🔍</span>
        <span class="title-text">实时星盘探针</span>
      </div>
      <div v-if="selectedPlanet" class="selected-planet-badge">
        <span class="planet-symbol">{{ getPlanetSymbol(selectedPlanet.name) }}</span>
        <span class="planet-name">{{ selectedPlanet.name }}</span>
        <button class="clear-btn" @click="clearSelection">×</button>
      </div>
    </div>
    
    <div v-if="!selectedPlanet && !probeData" class="probe-empty">
      <div class="empty-icon">✨</div>
      <div class="empty-text">
        <p>点击星盘中的行星</p>
        <p>或拖动行星查看实时变化</p>
      </div>
    </div>
    
    <div v-else-if="probeData" class="probe-content">
      <div class="probe-section planet-section">
        <div class="section-header">
          <span class="section-icon">🌍</span>
          <span class="section-title">行星基本信息</span>
        </div>
        <div class="planet-info-grid">
          <div class="info-item">
            <span class="info-label">星座</span>
            <span class="info-value">
              {{ probeData.planet?.zodiac?.sign_symbol }} 
              {{ probeData.planet?.zodiac?.sign }}
              {{ probeData.planet?.zodiac?.dms?.degrees }}°{{ probeData.planet?.zodiac?.dms?.minutes }}'
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">宫位</span>
            <span class="info-value">第{{ probeData.planet?.house }}宫</span>
          </div>
          <div class="info-item">
            <span class="info-label">元素</span>
            <span class="info-value" :class="getElementClass(probeData.planet?.zodiac?.element)">
              {{ probeData.planet?.zodiac?.element }}象
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">模式</span>
            <span class="info-value">{{ probeData.planet?.zodiac?.quality }}</span>
          </div>
        </div>
      </div>
      
      <div class="probe-section dignity-section">
        <div class="section-header">
          <span class="section-icon">⭐</span>
          <span class="section-title">庙旺弱陷</span>
          <span 
            class="dignity-badge" 
            :class="getDignityBadgeClass(probeData.planet?.dignities?.essential_dignity)"
          >
            {{ getDignityLabel(probeData.planet?.dignities?.essential_dignity) }}
          </span>
        </div>
        
        <div class="dignity-grid">
          <div 
            class="dignity-item" 
            :class="{ 'has-dignity': probeData.planet?.dignities?.is_in_ruler }"
          >
            <span class="dignity-type">守护星</span>
            <span class="dignity-planet">{{ probeData.planet?.dignities?.ruler }}</span>
            <span v-if="probeData.planet?.dignities?.is_in_ruler" class="dignity-mark">✓ 入庙</span>
          </div>
          
          <div 
            class="dignity-item" 
            :class="{ 'has-dignity': probeData.planet?.dignities?.is_in_exaltation }"
          >
            <span class="dignity-type">旺势</span>
            <span class="dignity-planet">{{ probeData.planet?.dignities?.exaltation }}</span>
            <span v-if="probeData.planet?.dignities?.is_in_exaltation" class="dignity-mark">✓ 旺相</span>
          </div>
          
          <div 
            class="dignity-item" 
            :class="{ 'has-debility': probeData.planet?.dignities?.is_in_detriment }"
          >
            <span class="dignity-type">落陷</span>
            <span class="dignity-planet">{{ probeData.planet?.dignities?.detriment }}</span>
            <span v-if="probeData.planet?.dignities?.is_in_detriment" class="debility-mark">✗ 落陷</span>
          </div>
          
          <div 
            class="dignity-item" 
            :class="{ 'has-debility': probeData.planet?.dignities?.is_in_fall }"
          >
            <span class="dignity-type">弱势</span>
            <span class="dignity-planet">{{ probeData.planet?.dignities?.fall }}</span>
            <span v-if="probeData.planet?.dignities?.is_in_fall" class="debility-mark">✗ 弱势</span>
          </div>
        </div>
        
        <div class="dignity-scores">
          <div class="score-bar">
            <span class="score-label">力量评分</span>
            <div class="score-track">
              <div 
                class="score-fill positive" 
                :style="{ width: (probeData.planet?.dignities?.dignity_score || 0) * 10 + '%' }"
              ></div>
              <div 
                class="score-fill negative" 
                :style="{ width: (probeData.planet?.dignities?.debility_score || 0) * 10 + '%' }"
              ></div>
            </div>
            <span class="score-value">
              +{{ probeData.planet?.dignities?.dignity_score || 0 }} 
              / -{{ probeData.planet?.dignities?.debility_score || 0 }}
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="probeData.aspects && probeData.aspects.length > 0" class="probe-section aspects-section">
        <div class="section-header">
          <span class="section-icon">🔗</span>
          <span class="section-title">相位关系</span>
          <span class="count-badge">{{ probeData.aspects.length }}</span>
        </div>
        
        <div class="aspects-list">
          <div 
            v-for="(aspect, index) in sortedAspects" 
            :key="index"
            class="aspect-item"
            :class="aspect.nature"
          >
            <div class="aspect-planets">
              <span class="planet-sym main">{{ getPlanetSymbol(aspect.planet1 === selectedPlanet?.name ? aspect.planet2 : aspect.planet1) }}</span>
              <span 
                class="aspect-sym" 
                :style="{ color: getAspectColor(aspect.aspect) }"
              >
                {{ aspect.aspect_symbol }}
              </span>
              <span class="planet-sym">{{ getPlanetSymbol(aspect.planet1 === selectedPlanet?.name ? aspect.planet1 : aspect.planet2) }}</span>
            </div>
            
            <div class="aspect-details">
              <div class="aspect-main">
                <span class="aspect-name">{{ aspect.aspect }}</span>
                <span class="aspect-other">{{ aspect.planet1 === selectedPlanet?.name ? aspect.planet2 : aspect.planet1 }}</span>
              </div>
              <div class="aspect-meta">
                <span class="orb-info">容许度: {{ aspect.orb?.toFixed(2) }}°</span>
                <span class="applying-info" :class="{ 'is-applying': aspect.is_applying }">
                  {{ aspect.is_applying ? '入相' : '出相' }}
                </span>
              </div>
            </div>
            
            <div class="aspect-nature-indicator" :class="aspect.nature">
              {{ getNatureLabel(aspect.nature) }}
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="probeData.receptions && probeData.receptions.length > 0" class="probe-section receptions-section">
        <div class="section-header">
          <span class="section-icon">🤝</span>
          <span class="section-title">接纳与互容</span>
          <span class="count-badge">{{ probeData.receptions.length }}</span>
        </div>
        
        <div class="receptions-list">
          <div 
            v-for="(reception, index) in probeData.receptions" 
            :key="index"
            class="reception-item"
            :class="{ 'mutual': reception.is_mutual }"
          >
            <div class="reception-header">
              <span class="reception-type-badge" :class="reception.reception_type">
                {{ reception.is_mutual ? '互容' : '接纳' }}
              </span>
              <span class="reception-dignity">{{ reception.dignity_type === 'ruler' ? '守护星' : '旺势' }}</span>
            </div>
            
            <div class="reception-planets">
              <span class="planet-sym">{{ getPlanetSymbol(reception.planet_a) }}</span>
              <span class="reception-arrow">{{ reception.is_mutual ? '⇄' : '→' }}</span>
              <span class="planet-sym">{{ getPlanetSymbol(reception.planet_b) }}</span>
            </div>
            
            <p class="reception-desc">{{ reception.description }}</p>
            
            <div class="strength-bar">
              <div class="strength-fill" :style="{ width: reception.strength * 100 + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="probeData.light_translations && probeData.light_translations.length > 0" class="probe-section special-section">
        <div class="section-header">
          <span class="section-icon">💡</span>
          <span class="section-title">光线传递</span>
          <span class="count-badge">{{ probeData.light_translations.length }}</span>
        </div>
        
        <div class="special-list">
          <div 
            v-for="(translation, index) in probeData.light_translations" 
            :key="index"
            class="special-item light-translation"
          >
            <div class="special-title">
              <span class="translator">{{ translation.translator }}</span>
              <span class="light-label">作为传递者</span>
            </div>
            <div class="light-flow">
              <span class="planet-sym">{{ getPlanetSymbol(translation.planet_a) }}</span>
              <span class="light-arrow">{{ translation.aspect_from_a }}</span>
              <span class="planet-sym highlight">{{ getPlanetSymbol(translation.translator) }}</span>
              <span class="light-arrow">{{ translation.aspect_to_b }}</span>
              <span class="planet-sym">{{ getPlanetSymbol(translation.planet_b) }}</span>
            </div>
            <p class="special-desc">{{ translation.description }}</p>
          </div>
        </div>
      </div>
      
      <div v-if="probeData.besiegements && probeData.besiegements.length > 0" class="probe-section special-section">
        <div class="section-header">
          <span class="section-icon">⚔️</span>
          <span class="section-title">围攻</span>
          <span class="count-badge">{{ probeData.besiegements.length }}</span>
        </div>
        
        <div class="special-list">
          <div 
            v-for="(besiegement, index) in probeData.besiegements" 
            :key="index"
            class="special-item besiegement"
          >
            <div class="besiegement-info">
              <span class="besieged">{{ besiegement.besieged_planet }}</span>
              <span class="besiege-label">被</span>
              <span class="besiegers">{{ besiegement.besieging_planets?.join('、') }}</span>
              <span class="besiege-label">围攻</span>
            </div>
            <p class="special-desc">{{ besiegement.description }}</p>
          </div>
        </div>
      </div>
      
      <div v-if="probeData.antiscia_aspects && probeData.antiscia_aspects.length > 0" class="probe-section antiscia-section">
        <div class="section-header">
          <span class="section-icon">🔮</span>
          <span class="section-title">映点关系</span>
          <span class="count-badge">{{ probeData.antiscia_aspects.length }}</span>
        </div>
        
        <div class="antiscia-list">
          <div 
            v-for="(antiscia, index) in probeData.antiscia_aspects" 
            :key="index"
            class="antiscia-item"
            :class="antiscia.type"
          >
            <div class="antiscia-header">
              <span class="antiscia-type">{{ antiscia.type === 'antiscia' ? '映点' : '对照映点' }}</span>
            </div>
            <div class="antiscia-planets">
              <span class="planet-sym">{{ getPlanetSymbol(antiscia.planet_a) }}</span>
              <span class="antiscia-sym">{{ antiscia.type === 'antiscia' ? '⊙' : '⊖' }}</span>
              <span class="planet-sym">{{ getPlanetSymbol(antiscia.planet_b) }}</span>
            </div>
            <p class="antiscia-desc">{{ antiscia.description }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="changes && hasChanges" class="changes-panel">
      <div class="changes-header">
        <span class="changes-icon">📊</span>
        <span class="changes-title">实时变化检测</span>
      </div>
      
      <div class="change-groups-container">
        <div v-if="changes.aspects?.added?.length > 0" class="change-group added">
          <div class="change-group-header">
            <span class="change-icon">➕</span>
            <span>新增相位 ({{ changes.aspects.added.length }})</span>
          </div>
          <div class="change-items">
            <div v-for="(aspect, idx) in changes.aspects.added" :key="idx" class="change-item">
              {{ getPlanetSymbol(aspect.planet1) }} {{ aspect.aspect_symbol }} {{ getPlanetSymbol(aspect.planet2) }}
              <span class="change-detail">{{ aspect.aspect }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="changes.aspects?.removed?.length > 0" class="change-group removed">
          <div class="change-group-header">
            <span class="change-icon">➖</span>
            <span>消失相位 ({{ changes.aspects.removed.length }})</span>
          </div>
          <div class="change-items">
            <div v-for="(aspect, idx) in changes.aspects.removed" :key="idx" class="change-item">
              {{ getPlanetSymbol(aspect.planet1) }} {{ aspect.aspect_symbol }} {{ getPlanetSymbol(aspect.planet2) }}
              <span class="change-detail">{{ aspect.aspect }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="changes.receptions?.added?.length > 0 || changes.receptions?.removed?.length > 0" class="change-group receptions">
          <div class="change-group-header">
            <span class="change-icon">🤝</span>
            <span>接纳关系变化</span>
          </div>
          <div class="change-items">
            <div v-for="(r, idx) in changes.receptions.added" :key="'add-' + idx" class="change-item added">
              新增: {{ r.planet_a }} {{ r.is_mutual ? '⇄' : '→' }} {{ r.planet_b }}
            </div>
            <div v-for="(r, idx) in changes.receptions.removed" :key="'rem-' + idx" class="change-item removed">
              消失: {{ r.planet_a }} {{ r.is_mutual ? '⇄' : '→' }} {{ r.planet_b }}
            </div>
          </div>
        </div>
        
        <div v-if="changes.dignities" class="change-group dignity">
          <div class="change-group-header">
            <span class="change-icon">⭐</span>
            <span>庙旺弱陷变化</span>
          </div>
          <div class="dignity-compare">
            <div class="compare-item original">
              <span class="compare-label">原状态</span>
              <span class="dignity-badge" :class="getDignityBadgeClass(changes.dignities.original?.essential_dignity)">
                {{ getDignityLabel(changes.dignities.original?.essential_dignity) }}
              </span>
            </div>
            <span class="compare-arrow">→</span>
            <div class="compare-item new">
              <span class="compare-label">新状态</span>
              <span class="dignity-badge" :class="getDignityBadgeClass(changes.dignities.new?.essential_dignity)">
                {{ getDignityLabel(changes.dignities.new?.essential_dignity) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ASPECT_CONFIG, ASPECT_NATURE, getPlanetSymbol, getNatureInfo } from '@/constants/workbench.js'

const props = defineProps({
  selectedPlanet: {
    type: Object,
    default: null
  },
  probeData: {
    type: Object,
    default: null
  },
  changes: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['clear-selection'])

const hasChanges = computed(() => {
  if (!props.changes) return false
  return (
    (props.changes.aspects?.added?.length > 0) ||
    (props.changes.aspects?.removed?.length > 0) ||
    (props.changes.receptions?.added?.length > 0) ||
    (props.changes.receptions?.removed?.length > 0) ||
    props.changes.dignities
  )
})

const sortedAspects = computed(() => {
  if (!props.probeData?.aspects) return []
  return [...props.probeData.aspects].sort((a, b) => a.orb - b.orb)
})

function getElementClass(element) {
  const classes = {
    '火': 'fire-element',
    '土': 'earth-element',
    '风': 'air-element',
    '水': 'water-element'
  }
  return classes[element] || ''
}

function getDignityBadgeClass(dignity) {
  const classes = {
    'exalted': 'exalted',
    'strong': 'strong',
    'moderate': 'moderate',
    'neutral': 'neutral',
    'weak': 'weak',
    'debilitated': 'debilitated'
  }
  return classes[dignity] || 'neutral'
}

function getDignityLabel(dignity) {
  const labels = {
    'exalted': '擢升',
    'strong': '强势',
    'moderate': '中等',
    'neutral': '中性',
    'weak': '偏弱',
    'debilitated': '衰弱'
  }
  return labels[dignity] || '未知'
}

function getAspectColor(aspectName) {
  return ASPECT_CONFIG[aspectName]?.color || '#9370db'
}

function getNatureLabel(nature) {
  return ASPECT_NATURE[nature]?.label || '中性'
}

function clearSelection() {
  emit('clear-selection')
}
</script>

<style scoped>
.real-time-probe {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(12, 12, 28, 0.95);
  border-radius: 12px;
  border: 1px solid rgba(147, 112, 219, 0.2);
  overflow: hidden;
}

.probe-header {
  padding: 16px;
  border-bottom: 1px solid rgba(147, 112, 219, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.probe-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.probe-icon {
  font-size: 1.2rem;
}

.title-text {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.selected-planet-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(147, 112, 219, 0.15);
  border-radius: 20px;
  border: 1px solid rgba(147, 112, 219, 0.3);
}

.planet-symbol {
  font-size: 1rem;
  color: #9370db;
}

.planet-name {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

.clear-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1rem;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.clear-btn:hover {
  color: #ef4444;
}

.probe-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.4);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text p {
  margin: 4px 0;
  font-size: 0.85rem;
}

.probe-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 8px;
}

.probe-content > .probe-section {
  flex-shrink: 0;
}

.probe-content > .probe-section:last-child {
  flex-shrink: 1;
  overflow-y: auto;
}

.probe-section.aspects-section,
.probe-section.receptions-section {
  flex-shrink: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.aspects-list,
.receptions-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-right: 2px;
}

.probe-section {
  margin-bottom: 12px;
  background: rgba(147, 112, 219, 0.05);
  border-radius: 8px;
  padding: 10px;
  border: 1px solid rgba(147, 112, 219, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.section-icon {
  font-size: 0.9rem;
}

.section-title {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.8rem;
}

.count-badge {
  margin-left: auto;
  padding: 2px 6px;
  background: rgba(147, 112, 219, 0.2);
  border-radius: 10px;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.6);
}

.planet-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 6px;
}

.info-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.fire-element { color: #ef4444; }
.earth-element { color: #22c55e; }
.air-element { color: #eab308; }
.water-element { color: #3b82f6; }

.dignity-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.dignity-badge.exalted { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.dignity-badge.strong { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.dignity-badge.moderate { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.dignity-badge.neutral { background: rgba(147, 112, 219, 0.15); color: #a78bfa; }
.dignity-badge.weak { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.dignity-badge.debilitated { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.dignity-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.dignity-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 6px;
  border-left: 3px solid rgba(147, 112, 219, 0.3);
}

.dignity-item.has-dignity {
  border-left-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.dignity-item.has-debility {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.dignity-type {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

.dignity-planet {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.dignity-mark {
  font-size: 0.65rem;
  color: #22c55e;
}

.debility-mark {
  font-size: 0.65rem;
  color: #ef4444;
}

.dignity-scores {
  padding-top: 8px;
  border-top: 1px solid rgba(147, 112, 219, 0.1);
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  min-width: 60px;
}

.score-track {
  flex: 1;
  height: 8px;
  background: rgba(147, 112, 219, 0.1);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
}

.score-fill.positive {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.score-fill.negative {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.score-value {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  min-width: 80px;
  text-align: right;
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.aspect-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: rgba(147, 112, 219, 0.06);
  border-radius: 6px;
  border-left: 3px solid rgba(147, 112, 219, 0.3);
}

.aspect-item.harmonious {
  border-left-color: #22c55e;
}

.aspect-item.challenging {
  border-left-color: #ef4444;
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 4px;
}

.planet-sym {
  font-size: 1rem;
}

.planet-sym.main {
  color: #9370db;
}

.planet-sym.highlight {
  font-size: 1.2rem;
}

.aspect-sym {
  font-size: 0.9rem;
  font-weight: bold;
}

.aspect-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.aspect-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.aspect-name {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.aspect-other {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.aspect-meta {
  display: flex;
  gap: 8px;
}

.orb-info {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
}

.applying-info {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
}

.applying-info.is-applying {
  color: #f59e0b;
  font-weight: 500;
}

.aspect-nature-indicator {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 0.6rem;
  font-weight: 500;
  flex-shrink: 0;
}

.aspect-nature-indicator.harmonious {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.aspect-nature-indicator.challenging {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.aspect-nature-indicator.neutral {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.receptions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reception-item {
  padding: 10px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 6px;
  border: 1px solid rgba(147, 112, 219, 0.15);
}

.reception-item.mutual {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.08);
}

.reception-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.reception-type-badge {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 0.65rem;
  font-weight: 600;
}

.reception-type-badge.mutual_ruler,
.reception-type-badge.mutual_exaltation,
.reception-type-badge.mixed_mutual {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.reception-type-badge.single_ruler,
.reception-type-badge.single_exaltation {
  background: rgba(147, 112, 219, 0.2);
  color: #a78bfa;
}

.reception-dignity {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

.reception-planets {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.reception-arrow {
  font-size: 0.9rem;
  color: #9370db;
}

.reception-desc {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.4;
  margin-bottom: 6px;
}

.strength-bar {
  height: 3px;
  background: rgba(147, 112, 219, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  background: linear-gradient(90deg, #9370db, #a78bfa);
}

.special-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.special-item {
  padding: 12px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 8px;
}

.special-item.light-translation {
  border-left: 3px solid rgba(59, 130, 246, 0.5);
}

.special-item.besiegement {
  border-left: 3px solid rgba(239, 68, 68, 0.5);
}

.special-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.translator {
  font-size: 0.85rem;
  color: #3b82f6;
  font-weight: 600;
}

.light-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.light-flow {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.light-arrow {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.special-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.4;
}

.besiegement-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.besieged {
  font-size: 0.85rem;
  color: #ef4444;
  font-weight: 600;
}

.besiegers {
  font-size: 0.85rem;
  color: #f97316;
  font-weight: 600;
}

.besiege-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.antiscia-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.antiscia-item {
  padding: 10px;
  background: rgba(147, 112, 219, 0.06);
  border-radius: 8px;
}

.antiscia-item.antiscia {
  border-left: 3px solid rgba(168, 85, 247, 0.5);
}

.antiscia-item.contra_antiscia {
  border-left: 3px solid rgba(236, 72, 153, 0.5);
}

.antiscia-header {
  margin-bottom: 6px;
}

.antiscia-type {
  font-size: 0.7rem;
  color: #a78bfa;
  font-weight: 500;
}

.antiscia-planets {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.antiscia-sym {
  font-size: 0.9rem;
  color: #9370db;
}

.antiscia-desc {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.55);
}

.changes-panel {
  flex-shrink: 0;
  border-top: 1px solid rgba(147, 112, 219, 0.2);
  background: rgba(147, 112, 219, 0.05);
  display: flex;
  flex-direction: column;
  max-height: 45%;
}

.changes-header {
  flex-shrink: 0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(147, 112, 219, 0.1);
}

.changes-icon {
  font-size: 1rem;
}

.changes-title {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.85rem;
}

.change-groups-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.change-group {
  padding: 10px 16px;
  border-bottom: 1px solid rgba(147, 112, 219, 0.1);
  flex-shrink: 0;
}

.change-group.receptions {
  flex-shrink: 1;
  min-height: 0;
  overflow-y: auto;
}

.change-group:last-child {
  border-bottom: none;
}

.change-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.change-icon {
  font-size: 0.9rem;
}

.change-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.change-item {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  padding: 4px 8px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 4px;
}

.change-item.added {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.change-item.removed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  text-decoration: line-through;
  opacity: 0.7;
}

.change-detail {
  margin-left: 8px;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
}

.dignity-compare {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.compare-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 8px;
}

.compare-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

.compare-arrow {
  font-size: 1rem;
  color: #9370db;
}

::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: rgba(147, 112, 219, 0.05);
}

::-webkit-scrollbar-thumb {
  background: rgba(147, 112, 219, 0.2);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(147, 112, 219, 0.3);
}
</style>
