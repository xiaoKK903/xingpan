<template>
  <div class="interactive-chart-wrapper">
    <svg 
      ref="chartSvg"
      :viewBox="`0 0 ${viewBoxSize} ${viewBoxSize}`"
      class="chart-wheel-svg interactive"
      :width="size"
      :height="size"
      shape-rendering="geometricPrecision"
      text-rendering="geometricPrecision"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <defs>
        <radialGradient id="bgGrad2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" style="stop-color:#12122a;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#080814;stop-opacity:1" />
        </radialGradient>
        
        <filter id="softShadow2">
          <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#000" flood-opacity="0.5"/>
        </filter>
        
        <filter id="planetGlow2">
          <feGaussianBlur stdDeviation="1.5" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        
        <filter id="dragHighlight">
          <feGaussianBlur stdDeviation="2" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        
        <marker id="leaderArrow2" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <circle cx="3" cy="3" r="2" fill="rgba(255,255,255,0.4)"/>
        </marker>
        
        <radialGradient id="orbitGrad">
          <stop offset="0%" style="stop-color:rgba(147, 112, 219, 0.1);stop-opacity:1" />
          <stop offset="100%" style="stop-color:rgba(147, 112, 219, 0.02);stop-opacity:1" />
        </radialGradient>
      </defs>
      
      <circle :cx="center" :cy="center" :r="outerR" fill="url(#bgGrad2)" stroke="rgba(100, 80, 160, 0.25)" stroke-width="1"/>
      
      <template v-if="hasChartData">
        <circle 
          v-if="draggingPlanet"
          :cx="center" :cy="center" 
          :r="planetR" 
          fill="none" 
          stroke="rgba(147, 112, 219, 0.3)" 
          stroke-width="2"
          stroke-dasharray="10,5"
        />
        
        <g v-if="displayAspects.length > 0" class="aspect-lines">
          <line
            v-for="(aspect, index) in displayAspects"
            :key="'aspect-' + index"
            :x1="center + (aspectLineR) * cos(degToRad(getDisplayLongitude(aspect.planet1) - 90))"
            :y1="center + (aspectLineR) * sin(degToRad(getDisplayLongitude(aspect.planet1) - 90))"
            :x2="center + (aspectLineR) * cos(degToRad(getDisplayLongitude(aspect.planet2) - 90))"
            :y2="center + (aspectLineR) * sin(degToRad(getDisplayLongitude(aspect.planet2) - 90))"
            :stroke="getAspectColor(aspect.aspect)"
            :stroke-width="getAspectWidth(aspect.aspect)"
            :stroke-dasharray="getAspectDash(aspect.aspect)"
            :opacity="getAspectOrbOpacity(aspect)"
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
            stroke="rgba(100, 80, 160, 0.15)"
            stroke-width="0.5"
          />
          
          <text
            v-for="(sign, index) in zodiacSigns"
            :key="'zodiac-sym-' + index"
            :x="center + zodiacMidR * cos(degToRad(index * 30 + 15 - 90))"
            :y="center + zodiacMidR * sin(degToRad(index * 30 + 15 - 90))"
            :fill="sign.color"
            font-size="14"
            font-weight="500"
            text-anchor="middle"
            dominant-baseline="middle"
            opacity="0.6"
          >
            {{ sign.symbol }}
          </text>
          
          <text
            v-for="index in 12"
            :key="'zodiac-deg-' + index"
            :x="center + (zodiacOuterR - 3) * cos(degToRad(index * 30 - 90))"
            :y="center + (zodiacOuterR - 3) * sin(degToRad(index * 30 - 90))"
            fill="rgba(147, 112, 219, 0.3)"
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
            :stroke="isAscendantCusp(index) ? '#22c55e' : 'rgba(100, 80, 160, 0.15)'"
            :stroke-width="isAscendantCusp(index) ? 1.5 : 0.5"
            stroke-linecap="round"
          />
          
          <text
            v-for="index in 12"
            :key="'house-num-' + index"
            :x="center + houseMidR * cos(degToRad(getHouseMidAngle(index - 1) - 90))"
            :y="center + houseMidR * sin(degToRad(getHouseMidAngle(index - 1) - 90))"
            fill="rgba(147, 112, 219, 0.4)"
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
        
        <g 
          v-if="hoveredPlanet" 
          class="probe-indicator"
        >
          <circle
            :cx="center + planetR * cos(degToRad(hoveredPlanet.longitude - 90))"
            :cy="center + planetR * sin(degToRad(hoveredPlanet.longitude - 90))"
            :r="getPlanetSize(hoveredPlanet.name) + 8"
            fill="none"
            stroke="rgba(147, 112, 219, 0.6)"
            stroke-width="2"
            stroke-dasharray="5,3"
          />
        </g>
        
        <g 
          v-if="draggingPlanet && dragCurrentAngle != null" 
          class="drag-indicator"
        >
          <line
            :x1="center"
            :y1="center"
            :x2="center + (planetR + 20) * cos(degToRad(dragCurrentAngle - 90))"
            :y2="center + (planetR + 20) * sin(degToRad(dragCurrentAngle - 90))"
            stroke="rgba(147, 112, 219, 0.8)"
            stroke-width="2"
            stroke-dasharray="8,4"
          />
          
          <circle
            :cx="center + planetR * cos(degToRad(dragCurrentAngle - 90))"
            :cy="center + planetR * sin(degToRad(dragCurrentAngle - 90))"
            :r="getPlanetSize(draggingPlanet.name) + 5"
            fill="rgba(147, 112, 219, 0.1)"
            stroke="#9370db"
            stroke-width="3"
          />
        </g>
        
        <g class="planets">
          <g 
            v-for="planet in mainPlanets" 
            :key="'planet-grp-' + planet.name"
            :class="{ 
              'dragging': draggingPlanet?.name === planet.name,
              'hovered': hoveredPlanet?.name === planet.name
            }"
            @mousedown.stop="startDrag(planet, $event)"
            @mouseenter.stop="onPlanetHover(planet)"
            @mouseleave.stop="onPlanetLeave(planet)"
            @touchstart.stop="startDrag(planet, $event)"
            style="cursor: grab;"
          >
            <circle
              :cx="center + planetR * cos(degToRad(getDisplayLongitude(planet.name) - 90))"
              :cy="center + planetR * sin(degToRad(getDisplayLongitude(planet.name) - 90))"
              :r="getPlanetSize(planet.name) + 3"
              :fill="getPlanetInfo(planet.name).bg + '33'"
              stroke="transparent"
              stroke-width="0"
            />
            
            <circle
              :cx="center + planetR * cos(degToRad(getDisplayLongitude(planet.name) - 90))"
              :cy="center + planetR * sin(degToRad(getDisplayLongitude(planet.name) - 90))"
              :r="getPlanetSize(planet.name)"
              :fill="getPlanetInfo(planet.name).bg"
              :stroke="getPlanetInfo(planet.name).border"
              stroke-width="1.5"
              :filter="hoveredPlanet?.name === planet.name ? 'url(#dragHighlight)' : 'url(#planetGlow2)'"
            />
            <text
              :x="center + planetR * cos(degToRad(getDisplayLongitude(planet.name) - 90))"
              :y="center + planetR * sin(degToRad(getDisplayLongitude(planet.name) - 90))"
              :fill="getPlanetInfo(planet.name).text"
              :font-size="getPlanetSymbolSize(planet.name)"
              font-weight="bold"
              text-anchor="middle"
              dominant-baseline="middle"
              pointer-events="none"
            >
              {{ getPlanetInfo(planet.name).symbol }}
            </text>
            
            <g class="planet-degree-label">
              <text
                :x="center + (planetR + 15) * cos(degToRad(getDisplayLongitude(planet.name) - 90))"
                :y="center + (planetR + 15) * sin(degToRad(getDisplayLongitude(planet.name) - 90))"
                fill="rgba(255, 255, 255, 0.7)"
                font-size="8"
                font-weight="500"
                text-anchor="middle"
                dominant-baseline="middle"
              >
                {{ getPlanetDisplayInfo(planet.name).sign_symbol }} {{ getPlanetDisplayInfo(planet.name).degrees }}°
              </text>
            </g>
            
            <text
              v-if="planet.is_retrograde"
              :x="center + planetR * cos(degToRad(getDisplayLongitude(planet.name) - 90))"
              :y="center + planetR * sin(degToRad(getDisplayLongitude(planet.name) - 90)) + 16"
              fill="#ef4444"
              font-size="7"
              font-weight="bold"
              text-anchor="middle"
            >
              R
            </text>
          </g>
        </g>
        
        <circle :cx="center" :cy="center" :r="centerR" fill="url(#bgGrad2)" stroke="rgba(100, 80, 160, 0.15)" stroke-width="1"/>
        
        <g class="center-info">
          <text
            v-if="chartData.ascendant"
            :x="center"
            :y="center - 12"
            fill="rgba(255, 255, 255, 0.85)"
            font-size="10"
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
            font-size="10"
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
            font-size="10"
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
    
    <div class="interaction-hint" v-if="showHint && hasChartData">
      <span class="hint-icon">💡</span>
      <span class="hint-text">拖动行星可实时观察相位变化 | 悬停查看详细信息</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { CHART_WHEEL_CONSTANTS, ASPECT_CONFIG, MAJOR_ASPECT_NAMES, degToRad, normalizeAngle, getAngleDifference, isAscendant, getHouseMidAngle, calculateLocalAspect } from '@/constants/workbench.js'

const props = defineProps({
  chartData: {
    type: Object,
    default: null
  },
  size: {
    type: Number,
    default: 500
  },
  showHint: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['planet-drag-start', 'planet-drag', 'planet-drag-end', 'planet-hover', 'planet-leave'])

const { VIEWBOX_SIZE, RADIUS_CONFIG, PLANET_SIZES, PLANET_SYMBOL_SIZES, PLANET_MAP, MAJOR_PLANET_NAMES, ZODIAC_SIGNS, ASCENDANT_THRESHOLD } = CHART_WHEEL_CONSTANTS

const chartSvg = ref(null)
const viewBoxSize = VIEWBOX_SIZE
const center = viewBoxSize / 2

const outerR = computed(() => center - RADIUS_CONFIG.OUTER_MARGIN)
const zodiacOuterR = computed(() => center - RADIUS_CONFIG.ZODIAC_OUTER)
const zodiacMidR = computed(() => center - RADIUS_CONFIG.ZODIAC_MID)
const zodiacInnerR = computed(() => center - RADIUS_CONFIG.ZODIAC_INNER)
const houseOuterR = computed(() => center - RADIUS_CONFIG.HOUSE_OUTER)
const houseMidR = computed(() => center - RADIUS_CONFIG.HOUSE_MID)
const houseInnerR = computed(() => center - RADIUS_CONFIG.HOUSE_INNER)
const planetR = computed(() => center - RADIUS_CONFIG.PLANET)
const aspectLineR = computed(() => center - RADIUS_CONFIG.ASPECT_LINE)
const centerR = computed(() => center - RADIUS_CONFIG.CENTER)

const draggingPlanet = ref(null)
const dragStartAngle = ref(null)
const dragCurrentAngle = ref(null)
const hoveredPlanet = ref(null)

const zodiacSigns = ZODIAC_SIGNS
const planetMap = PLANET_MAP

const hasChartData = computed(() => props.chartData && props.chartData.planets)

const mainPlanets = computed(() => {
  if (!props.chartData?.planets) return []
  return props.chartData.planets.filter(p => MAJOR_PLANET_NAMES.includes(p.name))
})

const houseCusps = computed(() => props.chartData?.houses?.house_cusps || [])
const ascendantLongitude = computed(() => props.chartData?.houses?.ascendant_longitude)
const midheavenLongitude = computed(() => props.chartData?.houses?.midheaven_longitude)
const aspects = computed(() => props.chartData?.aspects || [])

const majorAspects = computed(() => {
  return aspects.value.filter(a => MAJOR_ASPECT_NAMES.includes(a.aspect))
})

const displayAspects = computed(() => {
  if (!draggingPlanet.value || dragCurrentAngle.value === null) {
    return majorAspects.value
  }
  
  const draggingName = draggingPlanet.value.name
  const draggingLongitude = dragCurrentAngle.value
  
  const currentAspects = []
  
  for (const aspect of majorAspects.value) {
    if (aspect.planet1 !== draggingName && aspect.planet2 !== draggingName) {
      currentAspects.push(aspect)
    }
  }
  
  for (const planet of mainPlanets.value) {
    if (planet.name === draggingName) continue
    
    const planetLongitude = planet.longitude
    
    const newAspect = calculateLocalAspect(
      draggingName,
      planet.name,
      draggingLongitude,
      planetLongitude
    )
    
    if (newAspect) {
      currentAspects.push(newAspect)
    }
  }
  
  return currentAspects
})

function cos(rad) {
  return Math.cos(rad)
}

function sin(rad) {
  return Math.sin(rad)
}

function getEventPoint(event) {
  if (event.touches && event.touches.length > 0) {
    return { x: event.touches[0].clientX, y: event.touches[0].clientY }
  }
  return { x: event.clientX, y: event.clientY }
}

function getAngleFromEvent(event) {
  if (!chartSvg.value) return null
  
  const rect = chartSvg.value.getBoundingClientRect()
  const point = getEventPoint(event)
  
  const scaleX = viewBoxSize / rect.width
  const scaleY = viewBoxSize / rect.height
  
  const svgX = (point.x - rect.left) * scaleX
  const svgY = (point.y - rect.top) * scaleY
  
  const dx = svgX - center
  const dy = svgY - center
  
  let angle = Math.atan2(dy, dx) * 180 / Math.PI
  angle = (angle + 90 + 360) % 360
  
  return angle
}

function getPlanetLongitude(name) {
  const planet = mainPlanets.value?.find(p => p.name === name)
  return planet?.longitude || 0
}

function getDisplayLongitude(name) {
  if (draggingPlanet.value && draggingPlanet.value.name === name && dragCurrentAngle.value !== null) {
    return dragCurrentAngle.value
  }
  return getPlanetLongitude(name)
}

function getPlanetDisplayInfo(name) {
  const planet = mainPlanets.value?.find(p => p.name === name)
  if (!planet) return { sign_symbol: '?', degrees: 0 }
  
  if (draggingPlanet.value && draggingPlanet.value.name === name && dragCurrentAngle.value !== null) {
    const signIndex = Math.floor(dragCurrentAngle.value / 30)
    const degrees = Math.floor(dragCurrentAngle.value % 30)
    const signs = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
    return {
      sign_symbol: signs[signIndex],
      degrees: degrees
    }
  }
  
  return {
    sign_symbol: planet.zodiac?.sign_symbol || '?',
    degrees: planet.zodiac?.dms?.degrees || 0
  }
}

function startDrag(planet, event) {
  event.preventDefault()
  event.stopPropagation()
  
  draggingPlanet.value = planet
  dragStartAngle.value = planet.longitude
  dragCurrentAngle.value = planet.longitude
  
  emit('planet-drag-start', {
    planet: planet,
    startLongitude: planet.longitude
  })
  
  document.body.style.cursor = 'grabbing'
}

function onMouseDown(event) {
}

function onMouseMove(event) {
  if (!draggingPlanet.value) return
  
  const newAngle = getAngleFromEvent(event)
  if (newAngle === null) return
  
  dragCurrentAngle.value = newAngle
  
  emit('planet-drag', {
    planet: draggingPlanet.value,
    currentLongitude: newAngle,
    startLongitude: dragStartAngle.value
  })
}

function onMouseUp(event) {
  if (!draggingPlanet.value) return
  
  const finalAngle = dragCurrentAngle.value
  
  emit('planet-drag-end', {
    planet: draggingPlanet.value,
    finalLongitude: finalAngle,
    startLongitude: dragStartAngle.value
  })
  
  draggingPlanet.value = null
  dragStartAngle.value = null
  dragCurrentAngle.value = null
  
  document.body.style.cursor = 'default'
}

function onTouchStart(event) {
}

function onTouchMove(event) {
  if (!draggingPlanet.value) return
  event.preventDefault()
  
  const newAngle = getAngleFromEvent(event)
  if (newAngle === null) return
  
  dragCurrentAngle.value = newAngle
  
  emit('planet-drag', {
    planet: draggingPlanet.value,
    currentLongitude: newAngle,
    startLongitude: dragStartAngle.value
  })
}

function onTouchEnd(event) {
  onMouseUp(event)
}

function onPlanetHover(planet) {
  hoveredPlanet.value = planet
  emit('planet-hover', planet)
}

function onPlanetLeave(planet) {
  if (hoveredPlanet.value?.name === planet.name) {
    hoveredPlanet.value = null
  }
  emit('planet-leave', planet)
}

function isAscendantCusp(index) {
  return isAscendant(houseCusps.value, ascendantLongitude.value, index, ASCENDANT_THRESHOLD)
}

function getPlanetInfo(name) {
  return planetMap[name] || { symbol: '★', bg: 'rgba(139, 92, 246, 0.9)', border: '#8b5cf6', text: '#fff' }
}

function getPlanetSize(name) {
  return PLANET_SIZES[name] || 7
}

function getPlanetSymbolSize(name) {
  return PLANET_SYMBOL_SIZES[name] || 8
}

function getAspectColor(aspectName) {
  const config = ASPECT_CONFIG[aspectName]
  return config?.color || 'rgba(234, 179, 8, 0.5)'
}

function getAspectWidth(aspectName) {
  const config = ASPECT_CONFIG[aspectName]
  return config?.width || 1
}

function getAspectDash(aspectName) {
  const config = ASPECT_CONFIG[aspectName]
  return config?.dash || 'none'
}

function getAspectBaseOpacity(aspectName) {
  const config = ASPECT_CONFIG[aspectName]
  return config?.baseOpacity || 0.2
}

function getAspectOrbOpacity(aspect) {
  const baseOpacity = getAspectBaseOpacity(aspect.aspect)
  const orb = aspect.orb || 0
  
  const maxOrb = 8
  const normalizedOrb = Math.min(orb / maxOrb, 1)
  
  const orbFactor = Math.pow(1 - normalizedOrb, 0.4)
  
  return Math.max(0.15, baseOpacity * orbFactor)
}
</script>

<style scoped>
.interactive-chart-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.chart-wheel-svg.interactive {
  filter: drop-shadow(0 0 20px rgba(0, 0, 0, 0.4));
  background: radial-gradient(circle at center, rgba(80, 60, 160, 0.03), transparent);
  border-radius: 50%;
  cursor: crosshair;
}

.planets g {
  transition: transform 0.1s ease;
}

.planets g.hovered circle {
  stroke-width: 2.5;
}

.planets g.dragging {
  opacity: 0.8;
}

.planets g.dragging circle:first-child {
  fill: rgba(147, 112, 219, 0.2);
}

.interaction-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(147, 112, 219, 0.1);
  border: 1px solid rgba(147, 112, 219, 0.2);
  border-radius: 8px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.hint-icon {
  font-size: 1rem;
}

.hint-text {
  line-height: 1.4;
}

.planet-degree-label text {
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
}

.probe-indicator circle {
  animation: pulse-ring 1.5s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% {
    opacity: 0.4;
    stroke-width: 2;
  }
  50% {
    opacity: 0.8;
    stroke-width: 3;
  }
}

.drag-indicator line {
  animation: dash-move 0.5s linear infinite;
}

@keyframes dash-move {
  to {
    stroke-dashoffset: -12;
  }
}
</style>
