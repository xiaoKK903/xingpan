<template>
  <div class="energy-trend-chart">
    <div class="chart-header">
      <h3 class="chart-title">
        <span class="title-icon">📈</span>
        7天能量趋势
      </h3>
      <div class="chart-summary" v-if="summary">
        <div class="summary-item best" v-if="summary.max_day">
          <span class="summary-label">最佳日</span>
          <span class="summary-value">{{ summary.max_day.day_of_week }} ({{ summary.max_score }}分)</span>
        </div>
        <div class="summary-item caution" v-if="summary.min_day">
          <span class="summary-label">关注日</span>
          <span class="summary-value">{{ summary.min_day.day_of_week }} ({{ summary.min_score }}分)</span>
        </div>
        <div class="summary-item average">
          <span class="summary-label">平均</span>
          <span class="summary-value">{{ summary.avg_score }}分</span>
        </div>
      </div>
    </div>

    <div class="chart-container" :style="{ height: chartHeight + 'px' }">
      <svg 
        :viewBox="`0 0 ${svgWidth} ${svgHeight}`" 
        class="trend-svg"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:0.3" />
            <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:0.02" />
          </linearGradient>
          
          <linearGradient id="line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#8b5cf6" />
            <stop offset="50%" style="stop-color:#6366f1" />
            <stop offset="100%" style="stop-color:#8b5cf6" />
          </linearGradient>
          
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          
          <filter id="soft-shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.3"/>
          </filter>
        </defs>
        
        <g class="grid-lines">
          <line 
            v-for="(line, index) in gridLines" 
            :key="`grid-${index}`"
            :x1="paddingLeft"
            :y1="line.y"
            :x2="svgWidth - paddingRight"
            :y2="line.y"
            stroke="rgba(255, 255, 255, 0.05)"
            stroke-width="1"
          />
          <text 
            v-for="(line, index) in gridLines" 
            :key="`grid-label-${index}`"
            :x="paddingLeft - 8"
            :y="line.y + 4"
            text-anchor="end"
            fill="rgba(255, 255, 255, 0.3)"
            font-size="11"
          >
            {{ line.label }}
          </text>
        </g>
        
        <g class="x-axis">
          <line 
            :x1="paddingLeft"
            :y1="svgHeight - paddingBottom"
            :x2="svgWidth - paddingRight"
            :y2="svgHeight - paddingBottom"
            stroke="rgba(255, 255, 255, 0.1)"
            stroke-width="1"
          />
          <g 
            v-for="(point, index) in chartPoints" 
            :key="`x-label-${index}`"
          >
            <text 
              :x="point.x"
              :y="svgHeight - paddingBottom + 20"
              text-anchor="middle"
              fill="rgba(255, 255, 255, 0.5)"
              font-size="11"
              class="x-label"
            >
              {{ point.label }}
            </text>
            <text 
              :x="point.x"
              :y="svgHeight - paddingBottom + 34"
              text-anchor="middle"
              fill="rgba(255, 255, 255, 0.35)"
              font-size="10"
              class="x-label-day"
            >
              {{ point.weekday }}
            </text>
          </g>
        </g>
        
        <g class="dimension-lines">
          <template v-for="(dimConfig, dimKey) in dimensionConfig" :key="dimKey">
            <path 
              class="dimension-line"
              :d="getDimensionPath(dimKey)"
              :stroke="dimConfig.color"
              stroke-width="1.5"
              stroke-opacity="0.4"
              fill="none"
              :style="{ animationDelay: `${getDimDelay(dimKey)}s` }"
            />
          </template>
        </g>
        
        <path 
          class="area-path"
          :d="areaPath"
          fill="url(#area-gradient)"
          :style="{ animation: 'fade-in-area 1.5s ease-out forwards' }"
        />
        
        <path 
          class="line-path"
          :d="linePath"
          stroke="url(#line-gradient)"
          stroke-width="3"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
          filter="url(#glow)"
          :style="{ 
            strokeDasharray: lineLength,
            strokeDashoffset: lineLength,
            animation: 'draw-line 2s ease-out forwards'
          }"
        />
        
        <g class="turning-points" v-if="turningPoints?.length">
          <g 
            v-for="(tp, index) in turningPoints" 
            :key="`tp-${index}`"
            class="turning-point"
          >
            <circle 
              :cx="getTurningPointX(tp)"
              :cy="getTurningPointY(tp)"
              :r="tp.type === 'peak' ? 8 : 8"
              :fill="tp.type === 'peak' ? '#22c55e' : '#f97316'"
              opacity="0.9"
            />
            <text 
              :x="getTurningPointX(tp)"
              :y="getTurningPointY(tp) + (tp.type === 'peak' ? -15 : 25)"
              text-anchor="middle"
              :fill="tp.type === 'peak' ? '#22c55e' : '#f97316'"
              font-size="10"
              font-weight="600"
            >
              {{ tp.type === 'peak' ? '高点' : '低点' }}
            </text>
          </g>
        </g>
        
        <g class="data-points">
          <g 
            v-for="(point, index) in chartPoints" 
            :key="`point-${index}`"
            class="data-point-group"
            :style="{ animation: `fade-in-point 0.5s ease-out ${0.5 + index * 0.15}s both` }"
          >
            <circle 
              :cx="point.x"
              :cy="point.y"
              :r="6"
              fill="rgba(20, 20, 50, 1)"
              :stroke="getPointColor(point.score)"
              stroke-width="2"
              class="data-point-outer"
            />
            <circle 
              :cx="point.x"
              :cy="point.y"
              :r="3"
              :fill="getPointColor(point.score)"
              class="data-point-inner"
            />
            
            <text 
              :x="point.x"
              :y="point.y - 12"
              text-anchor="middle"
              :fill="getPointColor(point.score)"
              font-size="12"
              font-weight="600"
              class="score-label"
            >
              {{ point.score }}
            </text>
          </g>
        </g>
        
        <g class="mood-indicators">
          <g 
            v-for="(point, index) in chartPoints" 
            :key="`mood-${index}`"
          >
            <text 
              :x="point.x"
              :y="paddingTop - 5"
              text-anchor="middle"
              font-size="16"
              class="mood-icon"
            >
              {{ point.mood }}
            </text>
          </g>
        </g>
      </svg>
    </div>

    <div class="chart-legend">
      <div class="legend-item main">
        <div class="legend-line" style="background: linear-gradient(90deg, #8b5cf6, #6366f1)"></div>
        <span class="legend-text">整体能量</span>
      </div>
      <div 
        v-for="(config, key) in dimensionConfig" 
        :key="key"
        class="legend-item"
      >
        <div class="legend-line" :style="{ background: config.color, opacity: 0.6 }"></div>
        <span class="legend-text">{{ config.nameCn }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  chartData: {
    type: Object,
    default: () => null
  },
  summary: {
    type: Object,
    default: () => null
  },
  height: {
    type: Number,
    default: 350
  }
})

const paddingLeft = ref(50)
const paddingRight = ref(30)
const paddingTop = ref(40)
const paddingBottom = ref(60)

const svgWidth = ref(800)
const svgHeight = ref(props.height)

const chartHeight = computed(() => props.height)

const dimensionConfig = {
  communication: { nameCn: '沟通', color: '#60a5fa' },
  social: { nameCn: '社交', color: '#f472b6' },
  career: { nameCn: '事业', color: '#f97316' },
  wealth: { nameCn: '财运', color: '#eab308' },
  emotion: { nameCn: '情绪', color: '#ec4899' }
}

const chartPoints = computed(() => {
  if (!props.chartData?.labels?.length) return []
  
  const labels = props.chartData.labels
  const scores = props.chartData.overall
  const moods = props.chartData.moods || []
  
  const chartWidth = svgWidth.value - paddingLeft.value - paddingRight.value
  const chartHeight = svgHeight.value - paddingTop.value - paddingBottom.value
  
  return labels.map((label, index) => {
    const x = paddingLeft.value + (index / Math.max(labels.length - 1, 1)) * chartWidth
    const score = scores[index] || 50
    const y = paddingTop.value + chartHeight - (score / 100) * chartHeight
    
    const [date, weekday] = label.split(' ')
    
    return {
      x,
      y,
      score,
      label: date || label,
      weekday: weekday || '',
      mood: moods[index] || '☀️'
    }
  })
})

const turningPoints = computed(() => {
  return props.summary?.turning_points || props.chartData?.turningPoints || []
})

const linePath = computed(() => {
  if (chartPoints.value.length < 2) return ''
  
  let path = `M ${chartPoints.value[0].x} ${chartPoints.value[0].y}`
  
  for (let i = 1; i < chartPoints.value.length; i++) {
    const prev = chartPoints.value[i - 1]
    const curr = chartPoints.value[i]
    
    const cpX = (prev.x + curr.x) / 2
    
    path += ` C ${cpX} ${prev.y}, ${cpX} ${curr.y}, ${curr.x} ${curr.y}`
  }
  
  return path
})

const lineLength = computed(() => {
  if (chartPoints.value.length < 2) return 0
  
  let length = 0
  for (let i = 1; i < chartPoints.value.length; i++) {
    const dx = chartPoints.value[i].x - chartPoints.value[i - 1].x
    const dy = chartPoints.value[i].y - chartPoints.value[i - 1].y
    length += Math.sqrt(dx * dx + dy * dy)
  }
  return Math.max(length, 800)
})

const areaPath = computed(() => {
  if (chartPoints.value.length < 2) return ''
  
  const chartBottom = svgHeight.value - paddingBottom.value
  const firstPoint = chartPoints.value[0]
  const lastPoint = chartPoints.value[chartPoints.value.length - 1]
  
  return `M ${firstPoint.x} ${chartBottom} L ${linePath} L ${lastPoint.x} ${chartBottom} Z`
})

const gridLines = computed(() => {
  const chartHeight = svgHeight.value - paddingTop.value - paddingBottom.value
  const lines = []
  
  for (let i = 0; i <= 5; i++) {
    const value = i * 20
    const y = paddingTop.value + chartHeight - (value / 100) * chartHeight
    lines.push({
      y,
      label: `${value}`
    })
  }
  
  return lines
})

function getDimensionPath(dimKey) {
  if (!props.chartData?.dimensions?.[dimKey]) return ''
  
  const scores = props.chartData.dimensions[dimKey]
  const labels = props.chartData.labels
  
  if (!scores || !labels || scores.length < 2) return ''
  
  const chartWidth = svgWidth.value - paddingLeft.value - paddingRight.value
  const chartHeight = svgHeight.value - paddingTop.value - paddingBottom.value
  
  const points = labels.map((_, index) => {
    const x = paddingLeft.value + (index / Math.max(labels.length - 1, 1)) * chartWidth
    const score = scores[index] || 50
    const y = paddingTop.value + chartHeight - (score / 100) * chartHeight
    return { x, y }
  })
  
  let path = `M ${points[0].x} ${points[0].y}`
  
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const cpX = (prev.x + curr.x) / 2
    path += ` C ${cpX} ${prev.y}, ${cpX} ${curr.y}, ${curr.x} ${curr.y}`
  }
  
  return path
}

function getDimDelay(dimKey) {
  const keys = Object.keys(dimensionConfig)
  return 0.3 + keys.indexOf(dimKey) * 0.1
}

function getPointColor(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#eab308'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}

function getTurningPointX(tp) {
  if (!props.chartData?.labels) return paddingLeft.value
  
  const index = tp.index ?? 0
  const chartWidth = svgWidth.value - paddingLeft.value - paddingRight.value
  const count = props.chartData.labels.length
  
  return paddingLeft.value + (index / Math.max(count - 1, 1)) * chartWidth
}

function getTurningPointY(tp) {
  const chartHeight = svgHeight.value - paddingTop.value - paddingBottom.value
  const score = tp.score ?? 50
  return paddingTop.value + chartHeight - (score / 100) * chartHeight
}
</script>

<style lang="scss" scoped>
.energy-trend-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 24px;
  padding: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.chart-title {
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

.chart-summary {
  display: flex;
  gap: 24px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 16px;
  border-radius: 12px;
  background: rgba(139, 92, 246, 0.1);
}

.summary-item.best {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.summary-item.caution {
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.2);
}

.summary-item.average {
  background: rgba(96, 165, 250, 0.1);
  border: 1px solid rgba(96, 165, 250, 0.2);
}

.summary-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.summary-value {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.chart-container {
  width: 100%;
  overflow-x: auto;
}

.trend-svg {
  width: 100%;
  min-width: 600px;
  height: 100%;
}

@keyframes draw-line {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes fade-in-area {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fade-in-point {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.data-point-outer {
  transition: all 0.3s ease;
}

.data-point-group:hover .data-point-outer {
  r: 8;
  stroke-width: 3;
}

.score-label {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.data-point-group:hover .score-label {
  opacity: 1;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
  margin-top: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-item.main .legend-line {
  height: 3px;
}

.legend-line {
  width: 20px;
  height: 2px;
  border-radius: 2px;
}

.legend-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .energy-trend-chart {
    padding: 16px;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart-summary {
    width: 100%;
    justify-content: space-between;
  }
  
  .summary-item {
    flex: 1;
  }
  
  .chart-legend {
    gap: 12px;
  }
}
</style>
