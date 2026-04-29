<template>
  <g class="house-ring">
    <circle 
      :cx="center" 
      :cy="center" 
      :r="outerR" 
      fill="none" 
      :stroke="color" 
      stroke-width="0.5"
      :opacity="0.08"
    />
    <circle 
      :cx="center" 
      :cy="center" 
      :r="innerR" 
      fill="none" 
      :stroke="color" 
      stroke-width="0.5"
      :opacity="0.05"
    />
    
    <line
      v-for="(cusp, index) in cusps"
      :key="'house-line-' + index"
      :x1="center + outerR * cos(degToRad(cusp - 90))"
      :y1="center + outerR * sin(degToRad(cusp - 90))"
      :x2="center + innerR * cos(degToRad(cusp - 90))"
      :y2="center + innerR * sin(degToRad(cusp - 90))"
      :stroke="isAscendant(index) ? color : lineColor"
      :stroke-width="isAscendant(index) ? 1.2 * sizeMultiplier : 0.5"
      stroke-linecap="round"
      :opacity="isAscendant(index) ? 0.9 : 0.12"
    />
    
    <text
      v-for="index in 12"
      :key="'house-num-' + index"
      :x="center + midR * cos(degToRad(getHouseMidAngle(index - 1) - 90))"
      :y="center + midR * sin(degToRad(getHouseMidAngle(index - 1) - 90))"
      :fill="color"
      :font-size="8 * sizeMultiplier"
      font-weight="500"
      text-anchor="middle"
      dominant-baseline="middle"
      :opacity="0.35"
    >
      {{ index }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { degToRad, getHouseMidAngle as getMidAngle } from '@/constants/chart'

const props = defineProps({
  center: { type: Number, required: true },
  outerR: { type: Number, required: true },
  innerR: { type: Number, required: true },
  midR: { type: Number, required: true },
  cusps: { type: Array, default: () => [] },
  ascendant: { type: Number, default: null },
  color: { type: String, default: '#ff8c32' },
  sizeMultiplier: { type: Number, default: 1.0 }
})

const lineColor = computed(() => props.color)

function isAscendant(index) {
  if (props.cusps.length === 0 || props.ascendant == null) return false
  return Math.abs(props.cusps[index] - props.ascendant) < 0.1
}

function getHouseMidAngle(index) {
  return getMidAngle(props.cusps, index)
}

function cos(rad) {
  return Math.cos(rad)
}

function sin(rad) {
  return Math.sin(rad)
}
</script>
