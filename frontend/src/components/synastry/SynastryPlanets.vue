<template>
  <g class="planets">
    <g v-for="planet in planets" :key="'planet-' + planet.name">
      <circle
        :cx="center + radius * cos(degToRad(planet.longitude - 90))"
        :cy="center + radius * sin(degToRad(planet.longitude - 90))"
        :r="getPlanetSize(planet.name)"
        :fill="getPlanetInfo(planet.name).bg"
        :stroke="planetColor"
        :stroke-width="1.5 * sizeMultiplier"
        :filter="'url(#synastryPlanetGlow)'"
      />
      <text
        :cx="center + radius * cos(degToRad(planet.longitude - 90))"
        :cy="center + radius * sin(degToRad(planet.longitude - 90))"
        :fill="getPlanetInfo(planet.name).text"
        :font-size="getPlanetSymbolSize(planet.name)"
        font-weight="bold"
        text-anchor="middle"
        dominant-baseline="middle"
      >
        {{ getPlanetInfo(planet.name).symbol }}
      </text>
    </g>
  </g>
</template>

<script setup>
import { degToRad, getPlanetInfo } from '@/constants/chart'

const props = defineProps({
  center: { type: Number, required: true },
  radius: { type: Number, required: true },
  planets: { type: Array, default: () => [] },
  planetColor: { type: String, default: '#8b5cf6' },
  sizeMultiplier: { type: Number, default: 1.0 }
})

function cos(rad) {
  return Math.cos(rad)
}

function sin(rad) {
  return Math.sin(rad)
}

function getPlanetSize(name) {
  const info = getPlanetInfo(name)
  return (info.size || 7) * props.sizeMultiplier
}

function getPlanetSymbolSize(name) {
  const info = getPlanetInfo(name)
  return (info.symbolSize || 8) * props.sizeMultiplier
}
</script>
