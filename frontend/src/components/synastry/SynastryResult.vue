<template>
  <div class="result-section">
    <div class="result-header">
      <h3 class="result-title">
        {{ personAName }}
        <span class="vs-text"> & </span>
        {{ personBName }}
      </h3>
      <p class="result-subtitle">合盘互动相位分析</p>
    </div>

    <div class="chart-section">
      <SynastryWheel 
        v-if="synastryData" 
        :synastry-data="synastryData" 
        :size="550"
      />
    </div>

    <div v-if="synastryData?.synastry?.aspects" class="aspects-detail-section">
      <div class="section-title">详细相位列表</div>
      
      <div class="aspect-stats">
        <div class="stat-card harmonious">
          <div class="stat-value">{{ aspectSummary.harmonious }}</div>
          <div class="stat-label">和谐相位</div>
        </div>
        <div class="stat-card challenging">
          <div class="stat-value">{{ aspectSummary.challenging }}</div>
          <div class="stat-label">紧张相位</div>
        </div>
        <div class="stat-card neutral">
          <div class="stat-value">{{ aspectSummary.neutral }}</div>
          <div class="stat-label">中性相位</div>
        </div>
      </div>

      <div class="aspects-tabs">
        <button 
          class="tab-btn"
          :class="{ active: activeTab === 'all' }"
          @click="activeTab = 'all'"
        >
          全部 ({{ totalAspects }})
        </button>
        <button 
          class="tab-btn"
          :class="{ active: activeTab === 'harmonious' }"
          @click="activeTab = 'harmonious'"
        >
          和谐 ({{ aspectSummary.harmonious }})
        </button>
        <button 
          class="tab-btn"
          :class="{ active: activeTab === 'challenging' }"
          @click="activeTab = 'challenging'"
        >
          紧张 ({{ aspectSummary.challenging }})
        </button>
      </div>

      <div class="aspects-list">
        <div 
          v-for="(aspect, index) in filteredAspects" 
          :key="index"
          class="aspect-item"
          :class="aspect.nature"
        >
          <div class="aspect-planets">
            <div class="planet-info outer">
              <span 
                class="planet-sym" 
                :style="{ background: getPlanetInfo(aspect.planet_a)?.bg, borderColor: '#ff8c32' }"
              >
                {{ getPlanetInfo(aspect.planet_a)?.symbol }}
              </span>
              <span class="planet-name">{{ aspect.planet_a }}</span>
            </div>
            <div class="aspect-icon-wrapper">
              <span 
                class="aspect-icon" 
                :style="{ color: getAspectColor(aspect.aspect), opacity: getAspectOpacity(aspect) }"
              >
                {{ getAspectSymbol(aspect.aspect) }}
              </span>
            </div>
            <div class="planet-info inner">
              <span 
                class="planet-sym" 
                :style="{ background: getPlanetInfo(aspect.planet_b)?.bg, borderColor: '#50c8ff' }"
              >
                {{ getPlanetInfo(aspect.planet_b)?.symbol }}
              </span>
              <span class="planet-name">{{ aspect.planet_b }}</span>
            </div>
          </div>
          <div class="aspect-details">
            <span class="aspect-name" :style="{ color: getAspectColor(aspect.aspect) }">
              {{ aspect.aspect }}
            </span>
            <span class="aspect-orb">容许度: {{ aspect.orb_arcminutes }}'</span>
            <span class="aspect-nature" :class="aspect.nature">
              {{ getNatureLabel(aspect.nature) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { 
  getPlanetInfo, 
  getAspectInfo, 
  getAspectOpacity, 
  getNatureLabel 
} from '@/constants/chart'
import SynastryWheel from '@/components/SynastryWheel.vue'

const props = defineProps({
  synastryData: {
    type: Object,
    default: null
  },
  personAName: {
    type: String,
    default: '人物 A'
  },
  personBName: {
    type: String,
    default: '人物 B'
  }
})

const activeTab = ref('all')

const aspectSummary = computed(() => {
  if (!props.synastryData?.synastry?.aspect_summary) {
    return { harmonious: 0, challenging: 0, neutral: 0 }
  }
  return props.synastryData.synastry.aspect_summary
})

const totalAspects = computed(() => {
  return props.synastryData?.synastry?.aspects?.length || 0
})

const filteredAspects = computed(() => {
  if (!props.synastryData?.synastry?.aspects) return []
  
  const aspects = props.synastryData.synastry.aspects
  
  if (activeTab.value === 'harmonious') {
    return aspects.filter(a => a.nature === 'harmonious')
  } else if (activeTab.value === 'challenging') {
    return aspects.filter(a => a.nature === 'challenging')
  }
  return aspects
})

function getAspectColor(aspectName) {
  return getAspectInfo(aspectName).color
}

function getAspectSymbol(aspectName) {
  return getAspectInfo(aspectName).symbol
}
</script>

<style lang="scss" scoped>
.result-header {
  text-align: center;
  padding: 12px;
  background: rgba(12, 12, 28, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(80, 60, 160, 0.15);
  margin-bottom: 16px;
}

.result-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 4px;
}

.vs-text {
  color: rgba(139, 92, 246, 0.8);
}

.result-subtitle {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.chart-section {
  display: flex;
  justify-content: center;
  padding: 8px;
}

.aspects-detail-section {
  background: rgba(12, 12, 28, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.15);
}

.aspect-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
  }
  
  &.challenging {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
  }
  
  &.neutral {
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid rgba(251, 191, 36, 0.2);
  }
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  
  .stat-card.harmonious & { color: rgba(34, 197, 94, 0.9); }
  .stat-card.challenging & { color: rgba(239, 68, 68, 0.9); }
  .stat-card.neutral & { color: rgba(251, 191, 36, 0.9); }
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.aspects-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tab-btn {
  padding: 6px 14px;
  background: rgba(80, 60, 160, 0.1);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: rgba(255, 255, 255, 0.7);
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.3);
    border-color: rgba(139, 92, 246, 0.4);
    color: rgba(255, 255, 255, 0.9);
  }
}

.aspects-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

.aspect-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(80, 60, 160, 0.04);
  border-radius: 8px;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(80, 60, 160, 0.08);
  }
  
  &.harmonious {
    border-left: 3px solid rgba(34, 197, 94, 0.6);
  }
  
  &.challenging {
    border-left: 3px solid rgba(239, 68, 68, 0.6);
  }
  
  &.neutral {
    border-left: 3px solid rgba(251, 191, 36, 0.6);
  }
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 8px;
}

.planet-info {
  display: flex;
  align-items: center;
  gap: 6px;
  
  &.outer .planet-sym {
    border: 1.5px solid #ff8c32;
  }
  
  &.inner .planet-sym {
    border: 1.5px solid #50c8ff;
  }
}

.planet-sym {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 11px;
  font-weight: bold;
  color: #fff;
}

.planet-name {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

.aspect-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.aspect-icon {
  font-size: 1rem;
  font-weight: bold;
}

.aspect-details {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.aspect-name {
  font-size: 0.78rem;
  font-weight: 500;
}

.aspect-orb {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.aspect-nature {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 8px;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.15);
    color: rgba(34, 197, 94, 0.8);
  }
  
  &.challenging {
    background: rgba(239, 68, 68, 0.15);
    color: rgba(239, 68, 68, 0.8);
  }
  
  &.neutral {
    background: rgba(251, 191, 36, 0.15);
    color: rgba(251, 191, 36, 0.8);
  }
}
</style>
