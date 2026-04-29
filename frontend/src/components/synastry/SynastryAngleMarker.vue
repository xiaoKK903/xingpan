<template>
  <g v-if="angle != null" class="angle-marker">
    <line
      :x1="center + startR * cos(degToRad(angle - 90))"
      :y1="center + startR * sin(degToRad(angle - 90))"
      :x2="center + endR * cos(degToRad(angle - 90))"
      :y2="center + endR * sin(degToRad(angle - 90))"
      :stroke="color"
      :stroke-width="strokeWidth"
      stroke-linecap="round"
      :opacity="0.9"
    />
    <g v-if="label">
      <circle
        :cx="center + (endR + labelOffset) * cos(degToRad(angle - 90))"
        :cy="center + (endR + labelOffset) * sin(degToRad(angle - 90))"
        :r="circleRadius"
        fill="rgba(15, 15, 35, 0.98)"
        :stroke="color"
        :stroke-width="1.5"
      />
      <text
        :cx="center + (endR + labelOffset) * cos(degToRad(angle - 90))"
        :cy="center + (endR + labelOffset) * sin(degToRad(angle - 90))"
        :fill="color"
        :font-size="labelFontSize"
        font-weight="bold"
        text-anchor="middle"
        dominant-baseline="middle"
      >
        {{ label }}
      </text>
    </g>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { degToRad } from '@/constants/chart'

const props = defineProps({
  center: { type: Number, required: true },
  angle: { type: Number, default: null },
  startR: { type: Number, required: true },
  endR: { type: Number, required: true },
  color: { type: String, default: '#ff8c32' },
  label: { type: String, default: '' },
  labelOffset: { type: Number, default: 10 },
  strokeWidth: { type: Number, default: 2 }
})

const circleRadius = computed(() => props.label.length > 1 ? 12 : 10)
const labelFontSize = computed(() => props.label.length > 1 ? 10 : 12)

function cos(rad) {
  return Math.cos(rad)
}

function sin(rad) {
  return Math.sin(rad)
}
</script>
