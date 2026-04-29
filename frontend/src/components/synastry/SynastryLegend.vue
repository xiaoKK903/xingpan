<template>
  <div class="synastry-legend">
    <div class="legend-section">
      <div class="legend-title">
        <span class="color-dot" style="background: #ff8c32"></span>
        {{ personBName }} (外圈 B盘)
      </div>
      <div class="legend-grid">
        <div class="legend-item" v-for="planet in outerPlanets" :key="'outer-' + planet.name">
          <span class="legend-sym-wrap outer" :style="{ background: getPlanetInfo(planet.name).bg }">
            <span class="legend-symbol" :style="{ color: getPlanetInfo(planet.name).text }">
              {{ getPlanetInfo(planet.name).symbol }}
            </span>
          </span>
          <div class="legend-info">
            <span class="legend-name">{{ planet.name }}</span>
            <span class="legend-detail">
              {{ planet.zodiac?.sign_symbol }} {{ planet.zodiac?.dms?.degrees }}°{{ planet.zodiac?.dms?.minutes }}'
              <span class="legend-house">第{{ planet.house }}宫</span>
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="legend-section">
      <div class="legend-title">
        <span class="color-dot" style="background: #50c8ff"></span>
        {{ personAName }} (内圈 A盘)
      </div>
      <div class="legend-grid">
        <div class="legend-item" v-for="planet in innerPlanets" :key="'inner-' + planet.name">
          <span class="legend-sym-wrap inner" :style="{ background: getPlanetInfo(planet.name).bg }">
            <span class="legend-symbol" :style="{ color: getPlanetInfo(planet.name).text }">
              {{ getPlanetInfo(planet.name).symbol }}
            </span>
          </span>
          <div class="legend-info">
            <span class="legend-name">{{ planet.name }}</span>
            <span class="legend-detail">
              {{ planet.zodiac?.sign_symbol }} {{ planet.zodiac?.dms?.degrees }}°{{ planet.zodiac?.dms?.minutes }}'
              <span class="legend-house">第{{ planet.house }}宫</span>
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="aspects.length > 0" class="legend-section">
      <div class="legend-title">互动相位 (按容许度排序)</div>
      <div class="aspect-stats">
        <span class="stat-item harmonious">和谐: {{ aspectSummary.harmonious }}</span>
        <span class="stat-item challenging">紧张: {{ aspectSummary.challenging }}</span>
        <span class="stat-item neutral">中性: {{ aspectSummary.neutral }}</span>
      </div>
      <div class="legend-grid aspects-grid">
        <div class="legend-item aspect-item" v-for="(aspect, index) in aspects.slice(0, 15)" :key="'aspect-' + index">
          <div class="aspect-planets">
            <span class="legend-sym-wrap small outer" :style="{ background: getPlanetInfo(aspect.planet_b)?.bg }">
              <span class="legend-symbol small" :style="{ color: getPlanetInfo(aspect.planet_b)?.text }">
                {{ getPlanetInfo(aspect.planet_b)?.symbol }}
              </span>
            </span>
            <span class="aspect-arrow" :style="{ color: getAspectInfo(aspect.aspect).color, opacity: calcOpacity(aspect) }">
              {{ getAspectInfo(aspect.aspect).symbol }}
            </span>
            <span class="legend-sym-wrap small inner" :style="{ background: getPlanetInfo(aspect.planet_a)?.bg }">
              <span class="legend-symbol small" :style="{ color: getPlanetInfo(aspect.planet_a)?.text }">
                {{ getPlanetInfo(aspect.planet_a)?.symbol }}
              </span>
            </span>
          </div>
          <div class="aspect-info">
            <span class="aspect-name" :style="{ color: getAspectInfo(aspect.aspect).color }">{{ aspect.aspect }}</span>
            <span class="aspect-orb">容许度: {{ aspect.orb_arcminutes }}'</span>
          </div>
        </div>
      </div>
      <div class="aspect-note">
        <span class="note-label">相位说明：</span>
        <span class="note-item"><span class="note-dot" style="background: #fbbf24"></span>合相 (0°)</span>
        <span class="note-item"><span class="note-dot" style="background: #22c55e"></span>拱 (120°)</span>
        <span class="note-item"><span class="note-dot" style="background: #3b82f6"></span>六合 (60°)</span>
        <span class="note-item"><span class="note-dot" style="background: #ef4444"></span>冲 (180°)</span>
        <span class="note-item"><span class="note-dot" style="background: #f97316"></span>刑 (90°)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getPlanetInfo, getAspectInfo, getAspectOpacity } from '@/constants/chart'

defineProps({
  innerPlanets: { type: Array, default: () => [] },
  outerPlanets: { type: Array, default: () => [] },
  aspects: { type: Array, default: () => [] },
  aspectSummary: { type: Object, default: () => ({ harmonious: 0, challenging: 0, neutral: 0 }) },
  personAName: { type: String, default: 'A盘' },
  personBName: { type: String, default: 'B盘' }
})

function calcOpacity(aspect) {
  return getAspectOpacity(aspect)
}
</script>

<style scoped>
.synastry-legend {
  width: 100%;
  max-width: 700px;
  background: rgba(12, 12, 28, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 12px;
  padding: 20px;
  margin-top: 8px;
}

.legend-section {
  margin-bottom: 20px;
}

.legend-section:last-child {
  margin-bottom: 0;
}

.legend-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.15);
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.aspect-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-item {
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.15);
    color: rgba(34, 197, 94, 0.9);
  }
  
  &.challenging {
    background: rgba(239, 68, 68, 0.15);
    color: rgba(239, 68, 68, 0.9);
  }
  
  &.neutral {
    background: rgba(251, 191, 36, 0.15);
    color: rgba(251, 191, 36, 0.9);
  }
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
}

.legend-grid.aspects-grid {
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(80, 60, 160, 0.04);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.legend-item:hover {
  background: rgba(80, 60, 160, 0.08);
}

.legend-sym-wrap {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);
  border: 1.5px solid;
}

.legend-sym-wrap.outer {
  border-color: #ff8c32;
}

.legend-sym-wrap.inner {
  border-color: #50c8ff;
}

.legend-sym-wrap.small {
  width: 22px;
  height: 22px;
}

.legend-symbol {
  font-size: 13px;
  font-weight: bold;
}

.legend-symbol.small {
  font-size: 10px;
}

.legend-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.legend-name {
  font-size: 0.78rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.82);
}

.legend-detail {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.legend-house {
  color: rgba(147, 112, 219, 0.65);
  margin-left: 4px;
}

.aspect-item {
  justify-content: space-between;
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 6px;
}

.aspect-arrow {
  font-size: 13px;
  font-weight: bold;
}

.aspect-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.aspect-name {
  font-size: 0.75rem;
  font-weight: 500;
}

.aspect-orb {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.4);
}

.aspect-note {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(80, 60, 160, 0.1);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.note-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.note-item {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: 4px;
}

.note-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
</style>
