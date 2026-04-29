<template>
  <div class="chart-wheel-wrapper">
    <svg 
      :viewBox="`0 0 ${viewBoxSize} ${viewBoxSize}`"
      class="chart-wheel-svg"
      :width="size"
      :height="size"
      shape-rendering="geometricPrecision"
      text-rendering="geometricPrecision"
    >
      <defs>
        <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" style="stop-color:#12122a;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#080814;stop-opacity:1" />
        </radialGradient>
        
        <filter id="softShadow">
          <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#000" flood-opacity="0.5"/>
        </filter>
        
        <filter id="planetGlow">
          <feGaussianBlur stdDeviation="1.5" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        
        <marker id="leaderArrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <circle cx="3" cy="3" r="2" fill="rgba(255,255,255,0.4)"/>
        </marker>
      </defs>
      
      <circle :cx="center" :cy="center" :r="outerR" fill="url(#bgGrad)" stroke="rgba(100, 80, 160, 0.25)" stroke-width="1"/>
      
      <template v-if="hasChartData">
        <g v-if="majorAspects.length > 0" class="aspect-lines">
          <line
            v-for="(aspect, index) in majorAspects"
            :key="'aspect-' + index"
            :x1="center + (aspectLineR) * cos(degToRad(getPlanetLongitude(aspect.planet1) - 90))"
            :y1="center + (aspectLineR) * sin(degToRad(getPlanetLongitude(aspect.planet1) - 90))"
            :x2="center + (aspectLineR) * cos(degToRad(getPlanetLongitude(aspect.planet2) - 90))"
            :y2="center + (aspectLineR) * sin(degToRad(getPlanetLongitude(aspect.planet2) - 90))"
            :stroke="getAspectColor(aspect.aspect)"
            :stroke-width="getAspectWidth(aspect.aspect)"
            :stroke-dasharray="getAspectDash(aspect.aspect)"
            :opacity="getAspectOrbOpacity(aspect)"
            :style="{'z-index': 1}"
          />
        </g>
        
        <circle :cx="center" :cy="center" :r="zodiacOuterR" fill="none" stroke="rgba(80, 60, 140, 0.06)" stroke-width="0.5"/>
        <circle :cx="center" :cy="center" :r="zodiacInnerR" fill="none" stroke="rgba(80, 60, 140, 0.08)" stroke-width="0.5"/>
        
        <g class="zodiac-signs">
          <line
            v-for="index in 12"
            :key="'zodiac-line-' + index"
            :x1="center + zodiacOuterR * cos(degToRad(index * 30 - 90))"
            :y1="center + zodiacOuterR * sin(degToRad(index * 30 - 90))"
            :x2="center + zodiacInnerR * cos(degToRad(index * 30 - 90))"
            :y2="center + zodiacInnerR * sin(degToRad(index * 30 - 90))"
            stroke="rgba(100, 80, 160, 0.1)"
            stroke-width="0.5"
          />
          
          <text
            v-for="(sign, index) in zodiacSigns"
            :key="'zodiac-sym-' + index"
            :x="center + zodiacMidR * cos(degToRad(index * 30 + 15 - 90))"
            :y="center + zodiacMidR * sin(degToRad(index * 30 + 15 - 90))"
            :fill="sign.color"
            font-size="15"
            font-weight="500"
            text-anchor="middle"
            dominant-baseline="middle"
            opacity="0.5"
          >
            {{ sign.symbol }}
          </text>
          
          <text
            v-for="index in 12"
            :key="'zodiac-deg-' + index"
            :x="center + (zodiacOuterR - 3) * cos(degToRad(index * 30 - 90))"
            :y="center + (zodiacOuterR - 3) * sin(degToRad(index * 30 - 90))"
            fill="rgba(147, 112, 219, 0.2)"
            font-size="6"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ index * 30 }}°
          </text>
        </g>
        
        <circle :cx="center" :cy="center" :r="houseOuterR" fill="none" stroke="rgba(80, 60, 140, 0.06)" stroke-width="0.5"/>
        <circle :cx="center" :cy="center" :r="houseInnerR" fill="none" stroke="rgba(80, 60, 140, 0.04)" stroke-width="0.5"/>
        
        <g class="houses">
          <line
            v-for="(cusp, index) in houseCusps"
            :key="'house-line-' + index"
            :x1="center + houseOuterR * cos(degToRad(cusp - 90))"
            :y1="center + houseOuterR * sin(degToRad(cusp - 90))"
            :x2="center + houseInnerR * cos(degToRad(cusp - 90))"
            :y2="center + houseInnerR * sin(degToRad(cusp - 90))"
            :stroke="isAscendant(index) ? '#22c55e' : 'rgba(100, 80, 160, 0.12)'"
            :stroke-width="isAscendant(index) ? 1.5 : 0.5"
            stroke-linecap="round"
          />
          
          <text
            v-for="index in 12"
            :key="'house-num-' + index"
            :x="center + houseMidR * cos(degToRad(getHouseMidAngle(index - 1) - 90))"
            :y="center + houseMidR * sin(degToRad(getHouseMidAngle(index - 1) - 90))"
            fill="rgba(147, 112, 219, 0.35)"
            font-size="9"
            font-weight="500"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ index }}
          </text>
        </g>
        
        <g class="angles">
          <g v-if="ascendantLongitude != null">
            <line
              :x1="center + (houseOuterR + 5) * cos(degToRad(ascendantLongitude - 90))"
              :y1="center + (houseOuterR + 5) * sin(degToRad(ascendantLongitude - 90))"
              :x2="center + (centerR + 25) * cos(degToRad(ascendantLongitude - 90))"
              :y2="center + (centerR + 25) * sin(degToRad(ascendantLongitude - 90))"
              stroke="#22c55e"
              stroke-width="3"
              stroke-linecap="round"
              opacity="0.95"
            />
            <line
              :x1="center + (houseOuterR + 5) * cos(degToRad(ascendantLongitude - 90))"
              :y1="center + (houseOuterR + 5) * sin(degToRad(ascendantLongitude - 90))"
              :x2="center + (zodiacOuterR - 10) * cos(degToRad(ascendantLongitude - 90))"
              :y2="center + (zodiacOuterR - 10) * sin(degToRad(ascendantLongitude - 90))"
              stroke="#22c55e"
              stroke-width="2"
              stroke-linecap="round"
              stroke-dasharray="8,4"
              opacity="0.7"
            />
            <g>
              <circle
                :cx="center + (centerR + 20) * cos(degToRad(ascendantLongitude - 90))"
                :cy="center + (centerR + 20) * sin(degToRad(ascendantLongitude - 90))"
                r="15"
                fill="rgba(15, 15, 35, 0.98)"
                stroke="#22c55e"
                stroke-width="2"
              />
              <text
                :x="center + (centerR + 20) * cos(degToRad(ascendantLongitude - 90))"
                :y="center + (centerR + 20) * sin(degToRad(ascendantLongitude - 90))"
                fill="#22c55e"
                font-size="12"
                font-weight="bold"
                text-anchor="middle"
                dominant-baseline="middle"
              >
                AC
              </text>
            </g>
          </g>
          
          <g v-if="midheavenLongitude != null">
            <line
              :x1="center + (houseOuterR + 5) * cos(degToRad(midheavenLongitude - 90))"
              :y1="center + (houseOuterR + 5) * sin(degToRad(midheavenLongitude - 90))"
              :x2="center + (centerR + 25) * cos(degToRad(midheavenLongitude - 90))"
              :y2="center + (centerR + 25) * sin(degToRad(midheavenLongitude - 90))"
              stroke="#f59e0b"
              stroke-width="3"
              stroke-linecap="round"
              opacity="0.95"
            />
            <line
              :x1="center + (houseOuterR + 5) * cos(degToRad(midheavenLongitude - 90))"
              :y1="center + (houseOuterR + 5) * sin(degToRad(midheavenLongitude - 90))"
              :x2="center + (zodiacOuterR - 10) * cos(degToRad(midheavenLongitude - 90))"
              :y2="center + (zodiacOuterR - 10) * sin(degToRad(midheavenLongitude - 90))"
              stroke="#f59e0b"
              stroke-width="2"
              stroke-linecap="round"
              stroke-dasharray="8,4"
              opacity="0.7"
            />
            <g>
              <circle
                :cx="center + (centerR + 20) * cos(degToRad(midheavenLongitude - 90))"
                :cy="center + (centerR + 20) * sin(degToRad(midheavenLongitude - 90))"
                r="15"
                fill="rgba(15, 15, 35, 0.98)"
                stroke="#f59e0b"
                stroke-width="2"
              />
              <text
                :x="center + (centerR + 20) * cos(degToRad(midheavenLongitude - 90))"
                :y="center + (centerR + 20) * sin(degToRad(midheavenLongitude - 90))"
                fill="#f59e0b"
                font-size="12"
                font-weight="bold"
                text-anchor="middle"
                dominant-baseline="middle"
              >
                MC
              </text>
            </g>
          </g>
        </g>
        
        <g class="planet-leader-lines" v-if="planetLayouts.length > 0">
          <line
            v-for="layout in planetLayouts.filter(l => l.needsLeader)"
            :key="'leader-' + layout.planet.name"
            :x1="layout.leaderStartX"
            :y1="layout.leaderStartY"
            :x2="layout.leaderEndX"
            :y2="layout.leaderEndY"
            stroke="rgba(255, 255, 255, 0.25)"
            stroke-width="0.8"
            stroke-dasharray="3,3"
            stroke-linecap="round"
          />
          <circle
            v-for="layout in planetLayouts.filter(l => l.needsLeader)"
            :key="'leader-dot-' + layout.planet.name"
            :cx="layout.leaderStartX"
            :cy="layout.leaderStartY"
            r="2.5"
            fill="rgba(255, 255, 255, 0.4)"
          />
        </g>
        
        <g class="planets">
          <g v-for="layout in planetLayouts" :key="'planet-grp-' + layout.planet.name">
            <circle
              :cx="center + planetR * cos(degToRad(layout.planet.longitude - 90))"
              :cy="center + planetR * sin(degToRad(layout.planet.longitude - 90))"
              :r="getPlanetSize(layout.planet.name)"
              :fill="getPlanetInfo(layout.planet.name).bg"
              :stroke="getPlanetInfo(layout.planet.name).border"
              stroke-width="1.5"
              filter="url(#planetGlow)"
            />
            <text
              :cx="center + planetR * cos(degToRad(layout.planet.longitude - 90))"
              :cy="center + planetR * sin(degToRad(layout.planet.longitude - 90))"
              :fill="getPlanetInfo(layout.planet.name).text"
              :font-size="getPlanetSymbolSize(layout.planet.name)"
              font-weight="bold"
              text-anchor="middle"
              dominant-baseline="middle"
            >
              {{ getPlanetInfo(layout.planet.name).symbol }}
            </text>
            
            <g v-if="layout.planet.zodiac" class="planet-label">
              <g :transform="getLayoutTransform(layout)">
                <rect
                  x="-36"
                  y="-9"
                  width="72"
                  height="18"
                  rx="5"
                  fill="rgba(15, 15, 35, 0.98)"
                  :stroke="layout.needsLeader ? 'rgba(255, 255, 255, 0.15)' : 'rgba(100, 80, 160, 0.2)'"
                  stroke-width="0.8"
                />
                <text
                  x="0"
                  y="1"
                  fill="rgba(255, 255, 255, 0.95)"
                  font-size="9"
                  font-weight="600"
                  text-anchor="middle"
                  dominant-baseline="middle"
                >
                  {{ layout.planet.zodiac?.sign_symbol }} {{ layout.planet.zodiac?.dms?.degrees }}°{{ layout.planet.zodiac?.dms?.minutes }}'
                </text>
              </g>
            </g>
            
            <text
              v-if="layout.planet.is_retrograde"
              :x="center + planetR * cos(degToRad(layout.planet.longitude - 90))"
              :y="center + planetR * sin(degToRad(layout.planet.longitude - 90)) + 18"
              fill="#ef4444"
              font-size="8"
              font-weight="bold"
              text-anchor="middle"
            >
              R
            </text>
          </g>
        </g>
        
        <circle :cx="center" :cy="center" :r="centerR" fill="url(#bgGrad)" stroke="rgba(100, 80, 160, 0.15)" stroke-width="1"/>
        
        <g class="center-info">
          <text
            v-if="chartData.ascendant"
            :x="center"
            :y="center - 12"
            fill="rgba(255, 255, 255, 0.85)"
            font-size="11"
            font-weight="600"
            text-anchor="middle"
          >
            AC {{ chartData.ascendant.sign_symbol }}
          </text>
          <text
            v-if="chartData.sun_sign"
            :x="center"
            :y="center + 3"
            fill="#f97316"
            font-size="11"
            font-weight="600"
            text-anchor="middle"
          >
            ☉ {{ chartData.sun_sign.sign_symbol }}
          </text>
          <text
            v-if="chartData.moon_sign"
            :x="center"
            :y="center + 18"
            fill="#60a5fa"
            font-size="11"
            font-weight="600"
            text-anchor="middle"
          >
            ☽ {{ chartData.moon_sign.sign_symbol }}
          </text>
        </g>
      </template>
      
      <g v-else>
        <text :x="center" :y="center" fill="rgba(255, 255, 255, 0.4)" font-size="16" text-anchor="middle" dominant-baseline="middle">
          暂无星盘数据
        </text>
      </g>
    </svg>
    
    <div v-if="showLegend && hasChartData" class="chart-legend">
      <div class="legend-section">
        <div class="legend-title">行星位置</div>
        <div class="legend-grid">
          <div class="legend-item" v-for="planet in mainPlanets" :key="planet.name">
            <span class="legend-sym-wrap" :style="{ background: getPlanetInfo(planet.name).bg }">
              <span class="legend-symbol" :style="{ color: getPlanetInfo(planet.name).text }">
                {{ getPlanetInfo(planet.name).symbol }}
              </span>
            </span>
            <div class="legend-info">
              <span class="legend-name">{{ planet.name }}</span>
              <span class="legend-detail">
                {{ planet.zodiac?.sign_symbol }} {{ planet.zodiac?.dms?.degrees }}°{{ planet.zodiac?.dms?.minutes }}'
                <span class="legend-house">第{{ planet.house }}宫</span>
                <span v-if="planet.is_retrograde" class="legend-retro">R</span>
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="majorAspects.length > 0" class="legend-section">
        <div class="legend-title">主要相位 (按容许度排序)</div>
        <div class="legend-grid">
          <div class="legend-item aspect-item" v-for="(aspect, index) in sortedAspects.slice(0, 12)" :key="index">
            <div class="aspect-planets">
              <span class="legend-sym-wrap small" :style="{ background: getPlanetInfo(aspect.planet1)?.bg }">
                <span class="legend-symbol small" :style="{ color: getPlanetInfo(aspect.planet1)?.text }">
                  {{ getPlanetInfo(aspect.planet1)?.symbol }}
                </span>
              </span>
              <span class="aspect-arrow" :style="{ color: getAspectColor(aspect.aspect), opacity: getAspectOrbOpacity(aspect) }">
                {{ getAspectSymbol(aspect.aspect) }}
              </span>
              <span class="legend-sym-wrap small" :style="{ background: getPlanetInfo(aspect.planet2)?.bg }">
                <span class="legend-symbol small" :style="{ color: getPlanetInfo(aspect.planet2)?.text }">
                  {{ getPlanetInfo(aspect.planet2)?.symbol }}
                </span>
              </span>
            </div>
            <div class="aspect-info">
              <span class="aspect-name">{{ aspect.aspect }}</span>
              <span class="aspect-orb" :style="{ opacity: 0.3 + 0.5 * (1 - aspect.orb / 8) }">容许度: {{ aspect.orb.toFixed(1) }}°</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  chartData: {
    type: Object,
    default: null
  },
  size: {
    type: Number,
    default: 500
  },
  showLegend: {
    type: Boolean,
    default: true
  }
})

const viewBoxSize = 600
const center = viewBoxSize / 2

const outerR = computed(() => center - 10)
const zodiacOuterR = computed(() => center - 25)
const zodiacMidR = computed(() => center - 50)
const zodiacInnerR = computed(() => center - 78)
const houseOuterR = computed(() => center - 88)
const houseMidR = computed(() => center - 112)
const houseInnerR = computed(() => center - 155)
const planetR = computed(() => center - 132)
const aspectLineR = computed(() => center - 175)
const centerR = computed(() => center - 195)

const LABEL_WIDTH = 72
const LABEL_HEIGHT = 18
const LABEL_PADDING = 4

const LEVEL_OFFSETS = [
  { r: 42, angleAdjust: 0, priority: 1 },
  { r: -35, angleAdjust: 0, priority: 2 },
  { r: 65, angleAdjust: 4, priority: 0 },
  { r: -55, angleAdjust: -4, priority: 3 }
]

const planetLayouts = ref([])

const zodiacSigns = [
  { name: '白羊座', symbol: '♈', color: 'rgba(239, 68, 68, 0.7)' },
  { name: '金牛座', symbol: '♉', color: 'rgba(34, 197, 94, 0.7)' },
  { name: '双子座', symbol: '♊', color: 'rgba(234, 179, 8, 0.7)' },
  { name: '巨蟹座', symbol: '♋', color: 'rgba(59, 130, 246, 0.7)' },
  { name: '狮子座', symbol: '♌', color: 'rgba(249, 115, 22, 0.7)' },
  { name: '处女座', symbol: '♍', color: 'rgba(34, 197, 94, 0.7)' },
  { name: '天秤座', symbol: '♎', color: 'rgba(236, 72, 153, 0.7)' },
  { name: '天蝎座', symbol: '♏', color: 'rgba(239, 68, 68, 0.7)' },
  { name: '射手座', symbol: '♐', color: 'rgba(249, 115, 22, 0.7)' },
  { name: '摩羯座', symbol: '♑', color: 'rgba(107, 114, 128, 0.7)' },
  { name: '水瓶座', symbol: '♒', color: 'rgba(6, 182, 212, 0.7)' },
  { name: '双鱼座', symbol: '♓', color: 'rgba(59, 130, 246, 0.7)' }
]

const planetMap = {
  '太阳': { symbol: '☉', bg: 'rgba(249, 115, 22, 0.98)', border: '#f97316', text: '#fff', priority: 10 },
  '月亮': { symbol: '☽', bg: 'rgba(96, 165, 250, 0.98)', border: '#60a5fa', text: '#fff', priority: 9 },
  '水星': { symbol: '☿', bg: 'rgba(234, 179, 8, 0.98)', border: '#eab308', text: '#fff', priority: 7 },
  '金星': { symbol: '♀', bg: 'rgba(236, 72, 153, 0.98)', border: '#ec4899', text: '#fff', priority: 8 },
  '火星': { symbol: '♂', bg: 'rgba(239, 68, 68, 0.98)', border: '#ef4444', text: '#fff', priority: 6 },
  '木星': { symbol: '♃', bg: 'rgba(249, 115, 22, 0.98)', border: '#f97316', text: '#fff', priority: 5 },
  '土星': { symbol: '♄', bg: 'rgba(139, 92, 246, 0.98)', border: '#8b5cf6', text: '#fff', priority: 4 },
  '天王星': { symbol: '♅', bg: 'rgba(6, 182, 212, 0.98)', border: '#06b6d4', text: '#fff', priority: 3 },
  '海王星': { symbol: '♆', bg: 'rgba(59, 130, 246, 0.98)', border: '#3b82f6', text: '#fff', priority: 2 },
  '冥王星': { symbol: '♇', bg: 'rgba(107, 114, 128, 0.98)', border: '#6b7280', text: '#fff', priority: 1 },
  '北交点': { symbol: '☊', bg: 'rgba(34, 197, 94, 0.95)', border: '#22c55e', text: '#fff', priority: 0 },
  '南交点': { symbol: '☋', bg: 'rgba(239, 68, 68, 0.95)', border: '#ef4444', text: '#fff', priority: 0 }
}

const majorPlanetNames = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']

const hasChartData = computed(() => props.chartData && props.chartData.planets)

const mainPlanets = computed(() => {
  if (!props.chartData?.planets) return []
  return props.chartData.planets.filter(p => majorPlanetNames.includes(p.name))
})

const sortedPlanets = computed(() => {
  return [...mainPlanets.value].sort((a, b) => a.longitude - b.longitude)
})

const houseCusps = computed(() => props.chartData?.houses?.house_cusps || [])

const ascendantLongitude = computed(() => props.chartData?.houses?.ascendant_longitude)

const midheavenLongitude = computed(() => props.chartData?.houses?.midheaven_longitude)

const aspects = computed(() => props.chartData?.aspects || [])

const majorAspects = computed(() => {
  const majorAspectNames = ['合相', '对分相', '四分相', '三分相', '六分相']
  return aspects.value.filter(a => majorAspectNames.includes(a.aspect))
})

const sortedAspects = computed(() => {
  return [...majorAspects.value].sort((a, b) => a.orb - b.orb)
})

function calculateLocalDensity(planet, allPlanets) {
  const threshold = 45
  let density = 0
  allPlanets.forEach(p => {
    if (p.name === planet.name) return
    let dist = Math.abs(planet.longitude - p.longitude)
    if (dist > 180) dist = 360 - dist
    if (dist < threshold) {
      density += Math.max(0, 1 - dist / threshold)
    }
  })
  return density
}

function findClusters(planets) {
  if (planets.length === 0) return []
  
  const clusters = []
  let currentCluster = [planets[0]]
  
  for (let i = 1; i < planets.length; i++) {
    const prev = planets[i - 1]
    const curr = planets[i]
    let dist = Math.abs(curr.longitude - prev.longitude)
    if (dist > 180) dist = 360 - dist
    
    if (dist < 20) {
      currentCluster.push(curr)
    } else {
      if (currentCluster.length > 0) {
        clusters.push([...currentCluster])
      }
      currentCluster = [curr]
    }
  }
  
  if (currentCluster.length > 0) {
    clusters.push(currentCluster)
  }
  
  return clusters
}

function getLabelCollisionBox(planet, level, rOffset, angleAdjust) {
  const longitude = planet.longitude + angleAdjust
  const r = planetR.value + rOffset
  
  const centerX = center + r * cos(degToRad(longitude - 90))
  const centerY = center + r * sin(degToRad(longitude - 90))
  
  const halfW = LABEL_WIDTH / 2 + LABEL_PADDING
  const halfH = LABEL_HEIGHT / 2 + LABEL_PADDING
  
  const angleRad = degToRad(longitude - 90)
  const cosA = Math.cos(angleRad)
  const sinA = Math.sin(angleRad)
  
  const corners = [
    { x: -halfW, y: -halfH },
    { x: halfW, y: -halfH },
    { x: halfW, y: halfH },
    { x: -halfW, y: halfH }
  ].map(c => ({
    x: centerX + c.x * cosA - c.y * sinA,
    y: centerY + c.x * sinA + c.y * cosA
  }))
  
  const xs = corners.map(c => c.x)
  const ys = corners.map(c => c.y)
  
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
    centerX,
    centerY,
    r,
    longitude
  }
}

function boxesOverlap(box1, box2) {
  const padding = 2
  return !(box1.maxX + padding < box2.minX || 
           box2.maxX + padding < box1.minX || 
           box1.maxY + padding < box2.minY || 
           box2.maxY + padding < box1.minY)
}

function calculateLayouts() {
  const planets = sortedPlanets.value
  if (planets.length === 0) {
    planetLayouts.value = []
    return
  }
  
  const clusters = findClusters(planets)
  const layouts = []
  const usedBoxes = []
  
  planets.forEach(planet => {
    const density = calculateLocalDensity(planet, planets)
    const isInCluster = density > 0.5
    
    let bestLevel = 0
    let bestBox = null
    let needsLeader = false
    
    const planetPriority = planetMap[planet.name]?.priority || 0
    
    const levelsToTry = [...LEVEL_OFFSETS].sort((a, b) => {
      if (planetPriority >= 8) {
        return a.priority - b.priority
      }
      return a.r > 0 ? -1 : 1
    })
    
    for (const level of levelsToTry) {
      const testBox = getLabelCollisionBox(planet, 0, level.r, level.angleAdjust)
      
      let hasCollision = false
      for (const usedBox of usedBoxes) {
        if (boxesOverlap(testBox, usedBox)) {
          hasCollision = true
          break
        }
      }
      
      if (!hasCollision) {
        bestLevel = LEVEL_OFFSETS.indexOf(level)
        bestBox = testBox
        needsLeader = Math.abs(level.angleAdjust) > 0 || bestLevel > 1
        break
      }
    }
    
    if (!bestBox) {
      const level = LEVEL_OFFSETS[2]
      bestBox = getLabelCollisionBox(planet, 2, level.r, level.angleAdjust)
      bestLevel = 2
      needsLeader = true
    }
    
    const level = LEVEL_OFFSETS[bestLevel]
    
    const trueX = center + planetR.value * cos(degToRad(planet.longitude - 90))
    const trueY = center + planetR.value * sin(degToRad(planet.longitude - 90))
    
    const leaderOffset = level.r > 0 ? 15 : -15
    const leaderStartX = center + (planetR.value + leaderOffset) * cos(degToRad(planet.longitude - 90))
    const leaderStartY = center + (planetR.value + leaderOffset) * sin(degToRad(planet.longitude - 90))
    
    const labelCenterX = bestBox.centerX
    const labelCenterY = bestBox.centerY
    
    const angleToCenter = Math.atan2(labelCenterY - center, labelCenterX - center)
    const leaderEndR = level.r > 0 
      ? planetR.value + level.r - 20 
      : planetR.value + level.r + 20
    
    const leaderEndX = center + leaderEndR * Math.cos(angleToCenter)
    const leaderEndY = center + leaderEndR * Math.sin(angleToCenter)
    
    const layout = {
      planet,
      level: bestLevel,
      rOffset: level.r,
      angleAdjust: level.angleAdjust,
      box: bestBox,
      needsLeader: needsLeader && isInCluster,
      trueX,
      trueY,
      leaderStartX,
      leaderStartY,
      leaderEndX,
      leaderEndY,
      labelCenterX,
      labelCenterY
    }
    
    layouts.push(layout)
    usedBoxes.push(bestBox)
  })
  
  planetLayouts.value = layouts
}

watch([sortedPlanets, planetR], () => {
  calculateLayouts()
}, { immediate: true, deep: true })

function degToRad(deg) {
  return deg * Math.PI / 180
}

function cos(rad) {
  return Math.cos(rad)
}

function sin(rad) {
  return Math.sin(rad)
}

function isAscendant(index) {
  if (houseCusps.value.length === 0 || ascendantLongitude.value == null) return false
  return Math.abs(houseCusps.value[index] - ascendantLongitude.value) < 0.1
}

function getHouseMidAngle(index) {
  const cusps = houseCusps.value
  if (cusps.length === 0) return index * 30
  const currentCusp = cusps[index]
  const nextCusp = cusps[(index + 1) % 12]
  let mid = (currentCusp + nextCusp) / 2
  if (Math.abs(nextCusp - currentCusp) > 180) {
    mid = (currentCusp + nextCusp + 360) / 2
  }
  return mid % 360
}

function getPlanetLongitude(name) {
  const planet = mainPlanets.value?.find(p => p.name === name)
  return planet?.longitude || 0
}

function getPlanetInfo(name) {
  return planetMap[name] || { symbol: '★', bg: 'rgba(139, 92, 246, 0.9)', border: '#8b5cf6', text: '#fff' }
}

function getPlanetSize(name) {
  const sizes = {
    '太阳': 12,
    '月亮': 11,
    '水星': 7,
    '金星': 8,
    '火星': 7,
    '木星': 10,
    '土星': 9,
    '天王星': 7,
    '海王星': 7,
    '冥王星': 6
  }
  return sizes[name] || 7
}

function getPlanetSymbolSize(name) {
  const sizes = {
    '太阳': 13,
    '月亮': 12,
    '水星': 8,
    '金星': 9,
    '火星': 8,
    '木星': 11,
    '土星': 10,
    '天王星': 8,
    '海王星': 8,
    '冥王星': 7
  }
  return sizes[name] || 8
}

function getLayoutTransform(layout) {
  return `translate(${layout.labelCenterX}, ${layout.labelCenterY})`
}

function getLabelTransform(planet, index) {
  const longitude = planet.longitude
  const planetIdx = sortedPlanets.value.findIndex(p => p.name === planet.name)
  
  const nearbyPlanets = []
  sortedPlanets.value.forEach((p, i) => {
    if (i === planetIdx) return
    let dist = Math.abs(longitude - p.longitude)
    if (dist > 180) dist = 360 - dist
    if (dist < 45) {
      nearbyPlanets.push({ ...p, index: i, dist })
    }
  })
  
  const nearbyCount = nearbyPlanets.length
  let offsetR = 0
  let angleOffset = 0
  
  if (nearbyCount > 0) {
    const sortedNearby = nearbyPlanets.sort((a, b) => a.dist - b.dist)
    const closestDist = sortedNearby[0].dist
    
    if (closestDist < 20) {
      const offsetLevel = planetIdx % 3
      if (offsetLevel === 0) {
        offsetR = 38
      } else if (offsetLevel === 1) {
        offsetR = -38
        angleOffset = (planetIdx % 2 === 0 ? 1 : -1) * 3
      } else {
        offsetR = 55
        angleOffset = (planetIdx % 2 === 0 ? -1 : 1) * 5
      }
    } else if (closestDist < 35) {
      const offsetLevel = planetIdx % 2
      if (offsetLevel === 0) {
        offsetR = 38
      } else {
        offsetR = -28
      }
    }
  } else {
    offsetR = 38
  }
  
  const actualR = planetR.value + offsetR
  const adjustedLongitude = longitude + angleOffset
  
  return `translate(${center + actualR * cos(degToRad(adjustedLongitude - 90))}, ${center + actualR * sin(degToRad(adjustedLongitude - 90))})`
}

function getAspectColor(aspectName) {
  const colors = {
    '合相': '#fbbf24',
    '对分相': '#ef4444',
    '四分相': '#f97316',
    '三分相': '#22c55e',
    '六分相': '#3b82f6'
  }
  return colors[aspectName] || 'rgba(234, 179, 8, 0.5)'
}

function getAspectWidth(aspectName) {
  if (aspectName === '合相') return 2.5
  if (aspectName === '对分相') return 2
  if (aspectName === '四分相') return 2
  if (aspectName === '三分相') return 2
  if (aspectName === '六分相') return 1.5
  return 1
}

function getAspectBaseOpacity(aspectName) {
  if (aspectName === '合相') return 0.85
  if (aspectName === '对分相') return 0.75
  if (aspectName === '四分相') return 0.7
  if (aspectName === '三分相') return 0.7
  if (aspectName === '六分相') return 0.55
  return 0.2
}

function getAspectOrbOpacity(aspect) {
  const baseOpacity = getAspectBaseOpacity(aspect.aspect)
  const orb = aspect.orb || 0
  
  const maxOrb = 8
  const normalizedOrb = Math.min(orb / maxOrb, 1)
  
  const orbFactor = Math.pow(1 - normalizedOrb, 0.4)
  
  return Math.max(0.15, baseOpacity * orbFactor)
}

function getAspectOpacity(aspectName) {
  return getAspectBaseOpacity(aspectName)
}

function getAspectDash(aspectName) {
  if (aspectName === '合相') return 'none'
  if (aspectName === '对分相') return '10,5'
  if (aspectName === '四分相') return '5,5'
  if (aspectName === '三分相') return '15,8'
  if (aspectName === '六分相') return '8,6'
  return 'none'
}

function getAspectSymbol(aspectName) {
  const symbols = {
    '合相': '☌',
    '六分相': '⚹',
    '四分相': '□',
    '三分相': '△',
    '对分相': '☍'
  }
  return symbols[aspectName] || '○'
}
</script>

<style scoped>
.chart-wheel-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  width: 100%;
}

.chart-wheel-svg {
  filter: drop-shadow(0 0 20px rgba(0, 0, 0, 0.4));
  background: radial-gradient(circle at center, rgba(80, 60, 160, 0.03), transparent);
  border-radius: 50%;
}

.chart-legend {
  width: 100%;
  max-width: 600px;
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
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 10px;
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
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);
}

.legend-sym-wrap.small {
  width: 24px;
  height: 24px;
}

.legend-symbol {
  font-size: 14px;
  font-weight: bold;
}

.legend-symbol.small {
  font-size: 11px;
}

.legend-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.legend-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.82);
}

.legend-detail {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.5);
}

.legend-house {
  color: rgba(147, 112, 219, 0.65);
  margin-left: 4px;
}

.legend-retro {
  color: #ef4444;
  font-weight: bold;
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
  font-size: 14px;
  font-weight: bold;
}

.aspect-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.aspect-name {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.7);
}

.aspect-orb {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.4);
}
</style>
