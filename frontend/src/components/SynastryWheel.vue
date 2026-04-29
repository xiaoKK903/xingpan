<template>
  <div class="synastry-wheel-container">
    <svg 
      :viewBox="`0 0 ${viewBoxSize} ${viewBoxSize}`"
      class="synastry-wheel-svg"
      :width="size"
      :height="size"
    >
      <defs>
        <radialGradient id="wheelBg" cx="50%" cy="50%" r="50%">
          <stop offset="0%" style="stop-color:#0d0d1a;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#050510;stop-opacity:1" />
        </radialGradient>
      </defs>
      
      <circle 
        :cx="center" 
        :cy="center" 
        :r="outerR + 8" 
        fill="url(#wheelBg)" 
        stroke="rgba(50, 40, 80, 0.15)" 
        stroke-width="0.5"
      />
      
      <template v-if="hasData">
        <g class="background-rings">
          <circle 
            :cx="center" 
            :cy="center" 
            :r="outerRingRadius + 15" 
            fill="none" 
            stroke="rgba(255, 140, 50, 0.04)" 
            stroke-width="12"
          />
          <circle 
            :cx="center" 
            :cy="center" 
            :r="outerRingRadius" 
            fill="none" 
            stroke="rgba(60, 50, 100, 0.08)" 
            stroke-width="0.5"
          />
          <circle 
            :cx="center" 
            :cy="center" 
            :r="innerRingRadius" 
            fill="none" 
            stroke="rgba(60, 50, 100, 0.06)" 
            stroke-width="0.5"
          />
        </g>
        
        <g v-if="keyAspects.length > 0" class="aspect-lines-group">
          <line
            v-for="(aspect, index) in keyAspects"
            :key="'aspect-' + index"
            :x1="calcX(aspect.planet_b_longitude, aspectOuterR)"
            :y1="calcY(aspect.planet_b_longitude, aspectOuterR)"
            :x2="calcX(aspect.planet_a_longitude, aspectInnerR)"
            :y2="calcY(aspect.planet_a_longitude, aspectInnerR)"
            :stroke="getAspectInfo(aspect.aspect).color"
            :stroke-width="getAspectInfo(aspect.aspect).width"
            :stroke-dasharray="getAspectInfo(aspect.aspect).dash"
            :opacity="calcAspectOpacity(aspect)"
            stroke-linecap="round"
          />
        </g>
        
        <g class="zodiac-background">
          <circle 
            :cx="center" 
            :cy="center" 
            :r="outerZodiacOuterR" 
            fill="none" 
            stroke="rgba(80, 70, 120, 0.08)" 
            stroke-width="0.4"
          />
          <circle 
            :cx="center" 
            :cy="center" 
            :r="outerZodiacInnerR" 
            fill="none" 
            stroke="rgba(80, 70, 120, 0.05)" 
            stroke-width="0.3"
          />
          
          <line
            v-for="i in 12"
            :key="'outer-zodiac-line-' + i"
            :x1="calcX(i * 30, outerZodiacOuterR)"
            :y1="calcY(i * 30, outerZodiacOuterR)"
            :x2="calcX(i * 30, outerZodiacInnerR)"
            :y2="calcY(i * 30, outerZodiacInnerR)"
            stroke="rgba(80, 70, 120, 0.06)"
            stroke-width="0.4"
          />
          
          <text
            v-for="(sign, i) in ZODIAC_SIGNS"
            :key="'outer-zodiac-sym-' + i"
            :x="calcX(i * 30 + 15, outerZodiacMidR)"
            :y="calcY(i * 30 + 15, outerZodiacMidR)"
            :fill="sign.color"
            font-size="14"
            text-anchor="middle"
            dominant-baseline="middle"
            opacity="0.35"
          >
            {{ sign.symbol }}
          </text>
        </g>
        
        <g class="outer-houses">
          <circle 
            :cx="center" 
            :cy="center" 
            :r="outerHouseOuterR" 
            fill="none" 
            stroke="rgba(255, 140, 50, 0.06)" 
            stroke-width="0.3"
          />
          <circle 
            :cx="center" 
            :cy="center" 
            :r="outerHouseInnerR" 
            fill="none" 
            stroke="rgba(255, 140, 50, 0.04)" 
            stroke-width="0.2"
          />
          
          <line
            v-for="(cusp, i) in outerHouseCusps"
            :key="'outer-house-line-' + i"
            :x1="calcX(cusp, outerHouseOuterR)"
            :y1="calcY(cusp, outerHouseOuterR)"
            :x2="calcX(cusp, outerHouseInnerR)"
            :y2="calcY(cusp, outerHouseInnerR)"
            :stroke="isOuterAscendant(i) ? '#ff8c32' : 'rgba(255, 140, 50, 0.06)'"
            :stroke-width="isOuterAscendant(i) ? 1 : 0.3"
            stroke-linecap="round"
            opacity="0.6"
          />
          
          <text
            v-for="i in 12"
            :key="'outer-house-num-' + i"
            :x="calcX(getOuterHouseMid(i - 1), outerHouseMidR)"
            :y="calcY(getOuterHouseMid(i - 1), outerHouseMidR)"
            fill="rgba(255, 140, 50, 0.2)"
            font-size="7"
            font-weight="400"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ i }}
          </text>
        </g>
        
        <circle 
          :cx="center" 
          :cy="center" 
          :r="middleRingR" 
          fill="none" 
          stroke="rgba(50, 40, 80, 0.08)" 
          stroke-width="0.5"
          stroke-dasharray="6,8"
          opacity="0.4"
        />
        
        <g class="inner-zodiac">
          <circle 
            :cx="center" 
            :cy="center" 
            :r="innerZodiacOuterR" 
            fill="none" 
            stroke="rgba(80, 180, 255, 0.06)" 
            stroke-width="0.3"
          />
          <circle 
            :cx="center" 
            :cy="center" 
            :r="innerZodiacInnerR" 
            fill="none" 
            stroke="rgba(80, 180, 255, 0.04)" 
            stroke-width="0.2"
          />
          
          <line
            v-for="i in 12"
            :key="'inner-zodiac-line-' + i"
            :x1="calcX(i * 30, innerZodiacOuterR)"
            :y1="calcY(i * 30, innerZodiacOuterR)"
            :x2="calcX(i * 30, innerZodiacInnerR)"
            :y2="calcY(i * 30, innerZodiacInnerR)"
            stroke="rgba(80, 180, 255, 0.05)"
            stroke-width="0.3"
          />
          
          <text
            v-for="(sign, i) in ZODIAC_SIGNS"
            :key="'inner-zodiac-sym-' + i"
            :x="calcX(i * 30 + 15, innerZodiacMidR)"
            :y="calcY(i * 30 + 15, innerZodiacMidR)"
            :fill="sign.color"
            font-size="11"
            text-anchor="middle"
            dominant-baseline="middle"
            opacity="0.25"
          >
            {{ sign.symbol }}
          </text>
        </g>
        
        <g class="inner-houses">
          <circle 
            :cx="center" 
            :cy="center" 
            :r="innerHouseOuterR" 
            fill="none" 
            stroke="rgba(80, 200, 255, 0.05)" 
            stroke-width="0.2"
          />
          <circle 
            :cx="center" 
            :cy="center" 
            :r="innerHouseInnerR" 
            fill="none" 
            stroke="rgba(80, 200, 255, 0.03)" 
            stroke-width="0.2"
          />
          
          <line
            v-for="(cusp, i) in innerHouseCusps"
            :key="'inner-house-line-' + i"
            :x1="calcX(cusp, innerHouseOuterR)"
            :y1="calcY(cusp, innerHouseOuterR)"
            :x2="calcX(cusp, innerHouseInnerR)"
            :y2="calcY(cusp, innerHouseInnerR)"
            :stroke="isInnerAscendant(i) ? '#50c8ff' : 'rgba(80, 200, 255, 0.05)'"
            :stroke-width="isInnerAscendant(i) ? 0.8 : 0.2"
            stroke-linecap="round"
            opacity="0.5"
          />
          
          <text
            v-for="i in 12"
            :key="'inner-house-num-' + i"
            :x="calcX(getInnerHouseMid(i - 1), innerHouseMidR)"
            :y="calcY(getInnerHouseMid(i - 1), innerHouseMidR)"
            fill="rgba(80, 200, 255, 0.15)"
            font-size="6"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ i }}
          </text>
        </g>
        
        <g class="outer-planets">
          <g
            v-for="planet in outerPlanets"
            :key="'outer-planet-' + planet.name"
          >
            <g :transform="`translate(${calcX(planet.longitude, outerRingRadius)}, ${calcY(planet.longitude, outerRingRadius)})`">
              <circle 
                :r="getPlanetSize(planet.name)" 
                fill="none" 
                stroke="rgba(255, 140, 50, 0.3)" 
                stroke-width="1"
                opacity="0.5"
              />
              <text
                x="0"
                y="0"
                :fill="getPlanetInfo(planet.name).color"
                :font-size="getPlanetSymbolSize(planet.name)"
                font-weight="500"
                text-anchor="middle"
                dominant-baseline="middle"
              >
                {{ getPlanetInfo(planet.name).symbol }}
              </text>
            </g>
          </g>
        </g>
        
        <g class="inner-planets">
          <g
            v-for="planet in innerPlanets"
            :key="'inner-planet-' + planet.name"
          >
            <g :transform="`translate(${calcX(planet.longitude, innerRingRadius)}, ${calcY(planet.longitude, innerRingRadius)})`">
              <circle 
                :r="getPlanetSize(planet.name) * 0.8" 
                fill="none" 
                stroke="rgba(80, 200, 255, 0.25)" 
                stroke-width="0.8"
                opacity="0.4"
              />
              <text
                x="0"
                y="0"
                :fill="getPlanetInfo(planet.name).color"
                :font-size="getPlanetSymbolSize(planet.name) * 0.85"
                font-weight="500"
                text-anchor="middle"
                dominant-baseline="middle"
              >
                {{ getPlanetInfo(planet.name).symbol }}
              </text>
            </g>
          </g>
        </g>
        
        <circle 
          :cx="center" 
          :cy="center" 
          :r="centerR" 
          fill="url(#wheelBg)" 
          stroke="rgba(40, 30, 60, 0.1)" 
          stroke-width="0.5"
        />
        
        <g class="center-labels">
          <text :x="center" :y="center - 8" fill="#ff8c32" font-size="10" font-weight="600" text-anchor="middle" opacity="0.6">
            {{ personBName }}
          </text>
          <text :x="center" :y="center + 8" fill="#50c8ff" font-size="10" font-weight="600" text-anchor="middle" opacity="0.6">
            {{ personAName }}
          </text>
        </g>
        
        <g v-if="outerAscendant != null" class="outer-ac-marker">
          <line
            :x1="calcX(outerAscendant, outerHouseOuterR + 3)"
            :y1="calcY(outerAscendant, outerHouseOuterR + 3)"
            :x2="calcX(outerAscendant, outerRingRadius + 15)"
            :y2="calcY(outerAscendant, outerRingRadius + 15)"
            stroke="#ff8c32"
            stroke-width="1.5"
            stroke-linecap="round"
            opacity="0.7"
          />
          <g :transform="`translate(${calcX(outerAscendant, outerRingRadius + 22)}, ${calcY(outerAscendant, outerRingRadius + 22)})`">
            <text x="0" y="0" fill="#ff8c32" font-size="9" font-weight="600" text-anchor="middle" dominant-baseline="middle" opacity="0.7">AC</text>
          </g>
        </g>
      </template>
      
      <g v-else>
        <text :x="center" :y="center" fill="rgba(255, 255, 255, 0.25)" font-size="16" text-anchor="middle" dominant-baseline="middle">
          暂无合盘数据
        </text>
      </g>
    </svg>
    
    <SynastryLegend
      v-if="showLegend && hasData"
      :inner-planets="innerPlanets"
      :outer-planets="outerPlanets"
      :aspects="keyAspects"
      :aspect-summary="aspectSummary"
      :person-a-name="personAName"
      :person-b-name="personBName"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  ZODIAC_SIGNS, 
  MAJOR_PLANET_NAMES,
  KEY_ASPECT_PLANETS,
  PLANET_CATEGORIES,
  getPlanetInfo, 
  getAspectInfo, 
  getAspectOpacity, 
  degToRad,
  getHouseMidAngle
} from '@/constants/chart'
import SynastryLegend from './synastry/SynastryLegend.vue'

const props = defineProps({
  synastryData: { type: Object, default: null },
  size: { type: Number, default: 650 },
  showLegend: { type: Boolean, default: true }
})

const viewBoxSize = 750
const center = viewBoxSize / 2

const outerR = computed(() => center - 35)
const outerRingRadius = computed(() => outerR.value * 0.92)

const outerZodiacOuterR = computed(() => outerRingRadius.value + 35)
const outerZodiacMidR = computed(() => outerRingRadius.value + 48)
const outerZodiacInnerR = computed(() => outerRingRadius.value + 18)

const outerHouseOuterR = computed(() => outerRingRadius.value)
const outerHouseMidR = computed(() => outerRingRadius.value - 12)
const outerHouseInnerR = computed(() => outerRingRadius.value - 24)

const middleRingR = computed(() => outerRingRadius.value - 35)

const aspectOuterR = computed(() => outerRingRadius.value - 8)
const aspectInnerR = computed(() => innerRingRadius.value + 8)

const innerRingRadius = computed(() => outerR.value * 0.7)

const innerZodiacOuterR = computed(() => innerRingRadius.value + 25)
const innerZodiacMidR = computed(() => innerRingRadius.value + 35)
const innerZodiacInnerR = computed(() => innerRingRadius.value + 12)

const innerHouseOuterR = computed(() => innerRingRadius.value)
const innerHouseMidR = computed(() => innerRingRadius.value - 10)
const innerHouseInnerR = computed(() => innerRingRadius.value - 18)

const centerR = computed(() => innerRingRadius.value - 30)

function calcX(longitude, radius) {
  return center + radius * Math.cos(degToRad(longitude - 90))
}

function calcY(longitude, radius) {
  return center + radius * Math.sin(degToRad(longitude - 90))
}

const hasData = computed(() => {
  return props.synastryData && 
         props.synastryData.person_a?.chart?.planets && 
         props.synastryData.person_b?.chart?.planets
})

const personAName = computed(() => props.synastryData?.person_a?.name || 'A盘')
const personBName = computed(() => props.synastryData?.person_b?.name || 'B盘')

const innerChart = computed(() => props.synastryData?.person_a?.chart || {})
const outerChart = computed(() => props.synastryData?.person_b?.chart || {})

const innerPlanets = computed(() => {
  const planets = innerChart.value?.planets || []
  return planets.filter(p => MAJOR_PLANET_NAMES.includes(p.name))
})

const outerPlanets = computed(() => {
  const planets = outerChart.value?.planets || []
  return planets.filter(p => MAJOR_PLANET_NAMES.includes(p.name))
})

const innerHouseCusps = computed(() => innerChart.value?.houses?.house_cusps || [])
const outerHouseCusps = computed(() => outerChart.value?.houses?.house_cusps || [])

const innerAscendant = computed(() => innerChart.value?.houses?.ascendant_longitude)
const outerAscendant = computed(() => outerChart.value?.houses?.ascendant_longitude)

const allAspects = computed(() => props.synastryData?.synastry?.aspects || [])

const keyAspects = computed(() => {
  return allAspects.value
    .filter(a => {
      const isKeyAspect = KEY_ASPECT_PLANETS.includes(a.planet_a) && 
                          KEY_ASPECT_PLANETS.includes(a.planet_b)
      return isKeyAspect
    })
    .sort((a, b) => {
      const aInfo = getAspectInfo(a.aspect)
      const bInfo = getAspectInfo(b.aspect)
      if (bInfo.importance !== aInfo.importance) {
        return bInfo.importance - aInfo.importance
      }
      return a.orb - b.orb
    })
})

const aspectSummary = computed(() => props.synastryData?.synastry?.aspect_summary || {
  total: 0, harmonious: 0, challenging: 0, neutral: 0
})

function getPlanetSize(name) {
  return getPlanetInfo(name).size
}

function getPlanetSymbolSize(name) {
  return getPlanetInfo(name).symbolSize
}

function isLuminaryOrPersonal(name) {
  return PLANET_CATEGORIES.LUMINARIES.includes(name) || 
         PLANET_CATEGORIES.PERSONAL.includes(name)
}

function isInnerAscendant(index) {
  if (innerHouseCusps.value.length === 0 || innerAscendant.value == null) return false
  return Math.abs(innerHouseCusps.value[index] - innerAscendant.value) < 0.1
}

function isOuterAscendant(index) {
  if (outerHouseCusps.value.length === 0 || outerAscendant.value == null) return false
  return Math.abs(outerHouseCusps.value[index] - outerAscendant.value) < 0.1
}

function getInnerHouseMid(index) {
  return getHouseMidAngle(innerHouseCusps.value, index)
}

function getOuterHouseMid(index) {
  return getHouseMidAngle(outerHouseCusps.value, index)
}

function calcAspectOpacity(aspect) {
  return getAspectOpacity(aspect)
}
</script>

<style scoped>
.synastry-wheel-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.synastry-wheel-svg {
  filter: drop-shadow(0 0 20px rgba(0, 0, 0, 0.4));
}

.aspect-lines-group {
  opacity: 0.9;
}

.zodiac-background text,
.inner-zodiac text {
  user-select: none;
}
</style>
