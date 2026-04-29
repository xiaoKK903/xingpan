<template>
  <div class="radar-chart-container" v-if="hasValidData">
    <svg 
      :viewBox="`0 0 ${svgSize} ${svgSize}`" 
      class="radar-svg"
      :style="{ width: size + 'px', height: size + 'px' }"
    >
      <defs>
        <linearGradient id="radar-fill-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:0.4" />
          <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0.2" />
        </linearGradient>
        <linearGradient id="radar-line-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#8b5cf6" />
          <stop offset="100%" style="stop-color:#6366f1" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      
      <g 
        v-for="(level, levelIndex) in levels" 
        :key="`level-${levelIndex}`"
        class="radar-level"
      >
        <polygon
          :points="getLevelPoints(levelIndex)"
          fill="none"
          :stroke="levelStroke"
          :stroke-width="levelStrokeWidth"
          :opacity="levelOpacity"
        />
      </g>
      
      <g 
        v-for="(point, index) in axisPoints" 
        :key="`axis-${index}`"
        class="radar-axis"
      >
        <line
          :x1="centerX"
          :y1="centerY"
          :x2="point.x"
          :y2="point.y"
          :stroke="axisStroke"
          :stroke-width="axisStrokeWidth"
          :opacity="axisOpacity"
        />
      </g>
      
      <g 
        v-for="(label, index) in labelPoints" 
        :key="`label-${index}`"
        class="radar-label-group"
      >
        <text
          :x="label.x"
          :y="label.y"
          :text-anchor="label.anchor"
          :dy="label.dy"
          class="radar-label"
          :style="{ 
            fill: labelColor,
            fontSize: labelFontSize + 'px',
            fontFamily: labelFontFamily
          }"
        >
          {{ label.text }}
        </text>
      </g>
      
      <polygon
        :points="dataPoints"
        fill="url(#radar-fill-gradient)"
        :stroke="dataLineColor"
        :stroke-width="dataLineWidth"
        :stroke-linejoin="'round'"
        class="radar-polygon"
        :style="{ 
          opacity: dataFillOpacity,
          animation: `draw-radar ${animationDuration}s ease-out forwards`
        }"
      />
      
      <g 
        v-for="(point, index) in dataPointList" 
        :key="`point-${index}`"
        class="radar-point-group"
      >
        <circle
          :cx="point.x"
          :cy="point.y"
          :r="pointRadius"
          :fill="pointFill"
          :stroke="pointStroke"
          :stroke-width="pointStrokeWidth"
          class="radar-point"
          :style="{ 
            animation: `fade-in-point 0.5s ease-out ${animationDuration + index * 0.1}s both`
          }"
        >
          <title>{{ point.name }}: {{ point.score }}分</title>
        </circle>
      </g>
      
      <g 
        v-for="(point, index) in dataPointList" 
        :key="`score-${index}`"
        class="radar-score-group"
      >
        <text
          :x="point.x"
          :y="point.y"
          :dy="-18"
          text-anchor="middle"
          class="radar-score"
          :style="{ 
            fill: scoreColor,
            fontSize: scoreFontSize + 'px',
            fontWeight: scoreFontWeight,
            animation: `fade-in-point 0.5s ease-out ${animationDuration + index * 0.1 + 0.2}s both`
          }"
        >
          {{ point.score }}
        </text>
      </g>
    </svg>
  </div>
  <div class="radar-chart-empty" v-else>
    <slot name="empty">
      <span class="empty-text">暂无数据</span>
    </slot>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  dimensions: {
    type: Array,
    default: () => []
  },
  size: {
    type: Number,
    default: 300
  },
  radius: {
    type: Number,
    default: 100
  },
  levels: {
    type: Number,
    default: 5
  },
  levelStroke: {
    type: String,
    default: 'rgba(255, 255, 255, 0.1)'
  },
  levelStrokeWidth: {
    type: Number,
    default: 1
  },
  levelOpacity: {
    type: Number,
    default: 1
  },
  axisStroke: {
    type: String,
    default: 'rgba(255, 255, 255, 0.15)'
  },
  axisStrokeWidth: {
    type: Number,
    default: 1
  },
  axisOpacity: {
    type: Number,
    default: 1
  },
  labelColor: {
    type: String,
    default: 'rgba(255, 255, 255, 0.7)'
  },
  labelFontSize: {
    type: Number,
    default: 12
  },
  labelFontFamily: {
    type: String,
    default: 'inherit'
  },
  dataLineColor: {
    type: String,
    default: '#8b5cf6'
  },
  dataLineWidth: {
    type: Number,
    default: 2
  },
  dataFillOpacity: {
    type: Number,
    default: 1
  },
  pointRadius: {
    type: Number,
    default: 5
  },
  pointFill: {
    type: String,
    default: '#fff'
  },
  pointStroke: {
    type: String,
    default: '#8b5cf6'
  },
  pointStrokeWidth: {
    type: Number,
    default: 2
  },
  scoreColor: {
    type: String,
    default: '#a78bfa'
  },
  scoreFontSize: {
    type: Number,
    default: 10
  },
  scoreFontWeight: {
    type: [String, Number],
    default: 600
  },
  animationDuration: {
    type: Number,
    default: 1.5
  }
})

const svgSize = computed(() => props.size)
const centerX = computed(() => props.size / 2)
const centerY = computed(() => props.size / 2)
const effectiveRadius = computed(() => Math.min(props.radius, props.size / 2 - 40))

const hasValidData = computed(() => {
  const dims = props.dimensions
  if (!dims || !Array.isArray(dims) || dims.length === 0) {
    return false
  }
  return dims.every(d => 
    d && 
    typeof d.score === 'number' && 
    !isNaN(d.score) && 
    d.score >= 0 && 
    d.score <= 100
  )
})

const validDimensions = computed(() => {
  if (!hasValidData.value) return []
  return props.dimensions.map(d => ({
    name: d.name || '',
    score: Math.max(0, Math.min(100, isNaN(d.score) ? 50 : d.score))
  }))
})

const pointCount = computed(() => validDimensions.value.length)

const angleCache = computed(() => {
  const count = pointCount.value
  if (count === 0) return []
  const cache = []
  for (let i = 0; i < count; i++) {
    const angle = (i * 2 * Math.PI) / count - Math.PI / 2
    const cos = Math.cos(angle)
    const sin = Math.sin(angle)
    cache.push({ angle, cos, sin })
  }
  return cache
})

const axisPoints = computed(() => {
  const cache = angleCache.value
  const cx = centerX.value
  const cy = centerY.value
  const radius = effectiveRadius.value
  return cache.map(p => ({
    x: cx + p.cos * radius,
    y: cy + p.sin * radius
  }))
})

const labelPoints = computed(() => {
  const dims = validDimensions.value
  const cache = angleCache.value
  const cx = centerX.value
  const cy = centerY.value
  const labelDistance = effectiveRadius.value + 25
  
  return cache.map((p, index) => {
    const x = cx + p.cos * labelDistance
    const y = cy + p.sin * labelDistance
    
    let anchor = 'middle'
    let dy = '0.35em'
    
    if (Math.abs(p.cos) > 0.1) {
      anchor = p.cos > 0 ? 'start' : 'end'
    }
    
    if (Math.abs(p.sin) > 0.1) {
      if (p.sin > 0) {
        dy = '0.8em'
      } else {
        dy = '-0.2em'
      }
    }
    
    return {
      x,
      y,
      anchor,
      dy,
      text: dims[index]?.name || ''
    }
  })
})

function getLevelPoints(levelIndex) {
  const cache = angleCache.value
  const cx = centerX.value
  const cy = centerY.value
  const levelRadius = (levelIndex + 1) * (effectiveRadius.value / props.levels)
  
  const points = cache.map(p => 
    `${cx + p.cos * levelRadius},${cy + p.sin * levelRadius}`
  )
  
  return points.join(' ')
}

const dataPoints = computed(() => {
  const dims = validDimensions.value
  const cache = angleCache.value
  const cx = centerX.value
  const cy = centerY.value
  const radius = effectiveRadius.value
  
  const points = cache.map((p, index) => {
    const dim = dims[index]
    const score = dim?.score || 0
    const pointRadius = (score / 100) * radius
    return `${cx + p.cos * pointRadius},${cy + p.sin * pointRadius}`
  })
  
  return points.join(' ')
})

const dataPointList = computed(() => {
  const dims = validDimensions.value
  const cache = angleCache.value
  const cx = centerX.value
  const cy = centerY.value
  const radius = effectiveRadius.value
  
  return cache.map((p, index) => {
    const dim = dims[index]
    const score = dim?.score || 0
    const pointRadius = (score / 100) * radius
    return {
      x: cx + p.cos * pointRadius,
      y: cy + p.sin * pointRadius,
      name: dim?.name || '',
      score: score
    }
  })
})
</script>

<style lang="scss" scoped>
.radar-chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-chart-empty {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-text {
  color: rgba(255, 255, 255, 0.3);
  font-size: 14px;
}

.radar-svg {
  max-width: 100%;
  max-height: 100%;
}

.radar-polygon {
  transform-origin: center;
}

@keyframes draw-radar {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes fade-in-point {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.radar-point {
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:hover {
    r: 7;
    filter: drop-shadow(0 0 6px rgba(139, 92, 246, 0.6));
  }
}
</style>
