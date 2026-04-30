<template>
  <div class="timeline-container" ref="timelineRef">
    <div class="timeline-header">
      <div class="header-left">
        <span class="current-year">{{ currentYear }}</span>
        <span class="current-age" v-if="currentAge >= 0">{{ currentAge }}岁</span>
        <span class="current-age" v-else>出生前</span>
      </div>
      <div class="header-right">
        <div class="year-jumper">
          <el-input
            v-model="jumpYearInput"
            type="number"
            :min="minYear"
            :max="maxYear"
            placeholder="输入年份"
            class="year-input"
            @keyup.enter="jumpToYear"
          />
          <el-button type="primary" size="small" @click="jumpToYear" class="jump-btn">
            跳转
          </el-button>
        </div>
        <div class="quick-jump" v-if="keyYears.length > 0">
          <span class="quick-label">关键年:</span>
          <span 
            v-for="ky in displayedKeyYears" 
            :key="ky.year"
            class="quick-year"
            :class="{ 
              'active': ky.year === currentYear,
              'saturn-return': ky.type === 'saturn_return',
              'jupiter-return': ky.type === 'jupiter_return',
              'outer-planet': ky.type === 'outer_planet',
              'firdaria': ky.type === 'firdaria'
            }"
            @click="selectYear(ky.year)"
          >
            {{ ky.year }}
          </span>
        </div>
      </div>
    </div>

    <div class="timeline-track-wrapper" @wheel="handleWheel">
      <div 
        class="timeline-track" 
        ref="trackRef"
        :style="trackStyle"
        @mousedown="startDrag"
        @touchstart="startDrag"
      >
        <div 
          v-for="year in visibleYears" 
          :key="year"
          class="year-marker"
          :class="{ 
            'active': year === currentYear,
            'key-year': isKeyYear(year),
            'saturn-return': isSaturnReturn(year),
            'jupiter-return': isJupiterReturn(year)
          }"
          @click="selectYear(year)"
        >
          <div class="year-label">
            <span class="year-number">{{ year }}</span>
            <span class="year-age" v-if="year >= birthYear">{{ year - birthYear }}岁</span>
            <span class="year-age" v-else>出生前</span>
          </div>
          <div class="year-tick"></div>
          <div 
            v-if="isKeyYear(year)" 
            class="key-indicator"
            :class="getKeyYearClass(year)"
          >
            <span class="key-dot"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="timeline-navigation">
      <button class="nav-btn prev" @click="navigateYears(-10)" title="后退10年">
        <span class="nav-icon">◀</span>
      </button>
      <button class="nav-btn prev-year" @click="navigateYears(-1)" title="后退1年">
        <span class="nav-icon">◁</span>
      </button>
      
      <el-slider
        v-model="sliderValue"
        :min="minYear"
        :max="maxYear"
        :step="1"
        :show-tooltip="false"
        class="year-slider"
        @input="onSliderChange"
      />
      
      <button class="nav-btn next-year" @click="navigateYears(1)" title="前进1年">
        <span class="nav-icon">▷</span>
      </button>
      <button class="nav-btn next" @click="navigateYears(10)" title="前进10年">
        <span class="nav-icon">▶</span>
      </button>
    </div>

    <div class="timeline-legend" v-if="showLegend">
      <div class="legend-item">
        <span class="legend-dot saturn-return"></span>
        <span class="legend-label">土星回归</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot jupiter-return"></span>
        <span class="legend-label">木星回归</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot outer-planet"></span>
        <span class="legend-label">外行星重要行运</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot firdaria"></span>
        <span class="legend-label">法达大运</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  birthYear: {
    type: Number,
    default: 1990
  },
  minYear: {
    type: Number,
    default: 1980
  },
  maxYear: {
    type: Number,
    default: 2050
  },
  modelValue: {
    type: Number,
    default: () => new Date().getFullYear()
  },
  keyYears: {
    type: Array,
    default: () => []
  },
  showLegend: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const timelineRef = ref(null)
const trackRef = ref(null)
const jumpYearInput = ref('')
const sliderValue = ref(props.modelValue)

const currentYear = computed(() => props.modelValue)
const currentAge = computed(() => currentYear.value - props.birthYear)

const visibleYears = computed(() => {
  const years = []
  const start = props.minYear - 5
  const end = props.maxYear + 5
  for (let y = start; y <= end; y++) {
    years.push(y)
  }
  return years
})

const displayedKeyYears = computed(() => {
  return props.keyYears.slice(0, 5)
})

const trackStyle = computed(() => {
  const yearWidth = 80
  const offset = (currentYear.value - props.minYear + 5) * yearWidth
  const containerWidth = timelineRef.value?.offsetWidth || 800
  const centerOffset = containerWidth / 2 - yearWidth / 2
  
  return {
    transform: `translateX(${centerOffset - offset}px)`,
    transition: isDragging.value ? 'none' : 'transform 0.3s ease-out'
  }
})

const isDragging = ref(false)
const startX = ref(0)
const startTranslate = ref(0)

function isKeyYear(year) {
  return props.keyYears.some(ky => ky.year === year)
}

function isSaturnReturn(year) {
  return props.keyYears.some(ky => ky.year === year && ky.type === 'saturn_return')
}

function isJupiterReturn(year) {
  return props.keyYears.some(ky => ky.year === year && ky.type === 'jupiter_return')
}

function getKeyYearClass(year) {
  const ky = props.keyYears.find(k => k.year === year)
  if (!ky) return ''
  return ky.type
}

function selectYear(year) {
  emit('update:modelValue', year)
  emit('change', year)
  sliderValue.value = year
}

function navigateYears(step) {
  const newYear = Math.max(props.minYear, Math.min(props.maxYear, currentYear.value + step))
  selectYear(newYear)
}

function jumpToYear() {
  const year = parseInt(jumpYearInput.value)
  if (!isNaN(year) && year >= props.minYear && year <= props.maxYear) {
    selectYear(year)
  }
}

function onSliderChange(val) {
  selectYear(val)
}

function handleWheel(e) {
  e.preventDefault()
  const step = e.deltaY > 0 ? 1 : -1
  navigateYears(step)
}

function startDrag(e) {
  isDragging.value = true
  startX.value = e.clientX || e.touches?.[0]?.clientX
  startTranslate.value = (currentYear.value - props.minYear + 5) * 80
  
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', endDrag)
  document.addEventListener('touchmove', handleDrag)
  document.addEventListener('touchend', endDrag)
}

function handleDrag(e) {
  if (!isDragging.value) return
  
  const currentX = e.clientX || e.touches?.[0]?.clientX
  const diff = currentX - startX.value
  const yearWidth = 80
  const yearDiff = Math.round(-diff / yearWidth)
  
  if (Math.abs(yearDiff) > 0) {
    const newYear = Math.max(props.minYear, Math.min(props.maxYear, currentYear.value + yearDiff))
    if (newYear !== currentYear.value) {
      selectYear(newYear)
      startX.value = currentX
    }
  }
}

function endDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', handleDrag)
  document.removeEventListener('touchend', endDrag)
}

watch(() => props.modelValue, (newVal) => {
  sliderValue.value = newVal
  jumpYearInput.value = newVal.toString()
})

onMounted(() => {
  sliderValue.value = props.modelValue
  jumpYearInput.value = props.modelValue.toString()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', handleDrag)
  document.removeEventListener('touchend', endDrag)
})
</script>

<style lang="scss" scoped>
.timeline-container {
  width: 100%;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.current-year {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.current-age {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.year-jumper {
  display: flex;
  gap: 8px;
  align-items: center;
}

.year-input {
  width: 120px;
}

.jump-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
}

.quick-jump {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.quick-year {
  padding: 4px 10px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  
  &:hover {
    background: rgba(139, 92, 246, 0.3);
    transform: translateY(-1px);
  }
  
  &.active {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    border-color: transparent;
    color: white;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
  }
  
  &.saturn-return {
    border-color: rgba(239, 68, 68, 0.5);
  }
  
  &.jupiter-return {
    border-color: rgba(34, 197, 94, 0.5);
  }
  
  &.outer-planet {
    border-color: rgba(245, 158, 11, 0.5);
  }
  
  &.firdaria {
    border-color: rgba(96, 165, 250, 0.5);
  }
}

.timeline-track-wrapper {
  position: relative;
  overflow: hidden;
  padding: 20px 0;
  margin: 0 -20px;
  cursor: grab;
  
  &:active {
    cursor: grabbing;
  }
}

.timeline-track {
  display: flex;
  align-items: center;
  padding: 0 20px;
  min-width: max-content;
}

.year-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &:hover {
    transform: scale(1.1);
  }
  
  &.active {
    .year-label {
      .year-number {
        color: #a78bfa;
        font-weight: 800;
        font-size: 18px;
      }
    }
    
    .year-tick {
      height: 24px;
      background: linear-gradient(180deg, #8b5cf6 0%, #6366f1 100%);
      width: 3px;
    }
  }
  
  &.key-year {
    .key-indicator {
      display: block;
    }
  }
  
  &.saturn-return {
    .key-dot {
      background: #ef4444;
      box-shadow: 0 0 10px rgba(239, 68, 68, 0.6);
    }
  }
  
  &.jupiter-return {
    .key-dot {
      background: #22c55e;
      box-shadow: 0 0 10px rgba(34, 197, 94, 0.6);
    }
  }
}

.year-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  margin-bottom: 8px;
}

.year-number {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.year-age {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.year-tick {
  width: 2px;
  height: 16px;
  background: rgba(139, 92, 246, 0.3);
  border-radius: 1px;
  transition: all 0.3s ease;
}

.key-indicator {
  display: none;
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
}

.key-dot {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
}

.timeline-navigation {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.nav-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.3);
    transform: scale(1.1);
  }
  
  .nav-icon {
    color: rgba(167, 139, 250, 0.9);
    font-size: 14px;
  }
  
  &.prev-year,
  &.next-year {
    width: 32px;
    height: 32px;
    
    .nav-icon {
      font-size: 12px;
    }
  }
}

.year-slider {
  flex: 1;
  
  :deep(.el-slider__runway) {
    background: rgba(139, 92, 246, 0.2);
  }
  
  :deep(.el-slider__bar) {
    background: linear-gradient(90deg, #8b5cf6 0%, #60a5fa 100%);
  }
  
  :deep(.el-slider__button) {
    width: 16px;
    height: 16px;
    border-color: #8b5cf6;
    
    &:hover,
    &.is-dragging {
      transform: scale(1.3);
      box-shadow: 0 0 10px rgba(139, 92, 246, 0.6);
    }
  }
}

.timeline-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  
  &.saturn-return {
    background: #ef4444;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
  }
  
  &.jupiter-return {
    background: #22c55e;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
  }
  
  &.outer-planet {
    background: #f59e0b;
    box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
  }
  
  &.firdaria {
    background: #60a5fa;
    box-shadow: 0 0 6px rgba(96, 165, 250, 0.5);
  }
}

.legend-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

@media (max-width: 768px) {
  .timeline-container {
    padding: 16px;
  }
  
  .timeline-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-right {
    align-items: flex-start;
    width: 100%;
  }
  
  .current-year {
    font-size: 28px;
  }
  
  .year-jumper {
    width: 100%;
    
    .year-input {
      flex: 1;
    }
  }
  
  .timeline-navigation {
    gap: 8px;
  }
  
  .nav-btn {
    width: 32px;
    height: 32px;
  }
}
</style>
