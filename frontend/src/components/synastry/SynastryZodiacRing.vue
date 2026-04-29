<template>
  <g class="zodiac-ring">
    <circle 
      :cx="center" 
      :cy="center" 
      :r="outerR" 
      fill="none" 
      :stroke="strokeColor" 
      stroke-width="0.5"
      :opacity="0.1 * opacityMultiplier"
    />
    <circle 
      :cx="center" 
      :cy="center" 
      :r="innerR" 
      fill="none" 
      :stroke="strokeColor" 
      stroke-width="0.5"
      :opacity="0.08 * opacityMultiplier"
    />
    
    <line
      v-for="index in 12"
      :key="'zodiac-line-' + index"
      :x1="center + outerR * cos(degToRad(index * 30 - 90))"
      :y1="center + outerR * sin(degToRad(index * 30 - 90))"
      :x2="center + innerR * cos(degToRad(index * 30 - 90))"
      :y2="center + innerR * sin(degToRad(index * 30 - 90))"
      :stroke="strokeColor"
      stroke-width="0.5"
      :opacity="0.15 * opacityMultiplier"
    />
    
    <text
      v-for="(sign, index) in zodiacSigns"
      :key="'zodiac-sym-' + index"
      :x="center + midR * cos(degToRad(index * 30 + 15 - 90))"
      :y="center + midR * sin(degToRad(index * 30 + 15 - 90))"
      :fill="sign.color"
      :font-size="14 * sizeMultiplier"
      font-weight="500"
      text-anchor="middle"
      dominant-baseline="middle"
      :opacity="0.5 * opacityMultiplier"
    >
      {{ sign.symbol }}
    </text>
  </g>
</template>

<script setup>
import { degToRad } from '@/constants/chart'

const props = defineProps({
  center: { type: Number, required: true },
  outerR: { type: Number, required: true },
  innerR: { type: Number, required: true },
  midR: { type: Number, required: true },
  zodiacSigns: { type: Array, required: true },
  strokeColor: { type: String, default: 'rgba(80, 60, 140, 1)' },
  opacityMultiplier: { type: Number, default: 1.0 },
  sizeMultiplier: { type: Number, default: 1.0 }
})

function cos(rad) {
  return Math.cos(rad)
}

function sin(rad) {
  return Math.sin(rad)
}
</script>
