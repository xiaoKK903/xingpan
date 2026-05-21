<template>
  <div class="chart-wheel-wrapper">
    <button class="zoom-btn" @click="openFullscreenModal" title="全屏放大星盘">
      <span class="zoom-icon">🔍</span>
    </button>
    <svg
      :viewBox="`0 0 ${V} ${V}`"
      class="chart-svg"
      :width="size"
      :height="size"
      shape-rendering="geometricPrecision"
      text-rendering="geometricPrecision"
    >
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="1.5" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="planetGlow">
          <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <!-- 最外层背景 -->
      <circle :cx="CX" :cy="CY" :r="R + 35" fill="#000" />
      
      <!-- 外圈刻度圆环 -->
      <circle :cx="CX" :cy="CY" :r="R + 30" fill="none" stroke="#222" stroke-width="20"/>
      
      <!-- 外圈刻度线 -->
      <g v-for="i in 360" :key="'tick-'+i">
        <line
          v-if="i % 15 === 0"
          :x1="pol(R + 22, i).x" :y1="pol(R + 22, i).y"
          :x2="pol(R + 26, i).x" :y2="pol(R + 26, i).y"
          stroke="#333" stroke-width="0.5"
        />
      </g>
      
      <!-- 主盘背景 -->
      <circle :cx="CX" :cy="CY" :r="R" fill="#000" stroke="#333" stroke-width="2"/>

      <!-- 中心小圆 -->
      <circle :cx="CX" :cy="CY" r="2" fill="#666" stroke="#888" stroke-width="1"/>

      <template v-if="ready">
        <!-- 宫位分隔线（淡黄色，连到圆心） -->
        <line
          v-for="(h, i) in houses"
          :key="'hl'+i"
          :x1="CX" :y1="CY"
          :x2="pol(R + 25, h.cusp).x" :y2="pol(R + 25, h.cusp).y"
          :stroke="isAxisCusp(i) ? '#8a7500' : '#5a5000'" 
          :stroke-width="isAxisCusp(i) ? 1 : 0.6"
        />

        <!-- 星座刻度线 -->
        <line
          v-for="s in zodiacs"
          :key="'zn-line-'+s.name"
          :x1="pol(R + 15, s.deg).x" :y1="pol(R + 15, s.deg).y"
          :x2="pol(R + 25, s.deg).x" :y2="pol(R + 25, s.deg).y"
          stroke="#555" stroke-width="0.5"
        />

        <!-- 星座刻度标记（蓝色小菱形） -->
        <polygon
          v-for="s in zodiacs"
          :key="'zn-diamond-'+s.name"
          :points="diamond(s.deg)"
          fill="#444"
        />

        <!-- 外圈星座名称 -->
        <text
          v-for="s in zodiacs"
          :key="'zn-name-'+s.name"
          :x="pol(R + 20, s.deg).x" :y="pol(R + 20, s.deg).y"
          :fill="s.color" font-size="14" font-weight="bold"
          text-anchor="middle" dominant-baseline="central"
        >{{ s.name }}</text>

        <!-- 宫位编号 -->
        <text
          v-for="(h, i) in houses"
          :key="'hn'+i"
          :x="pol(R - 10, (h.cusp + nextCusp(i)) / 2).x"
          :y="pol(R - 10, (h.cusp + nextCusp(i)) / 2).y"
          :fill="getHouseNumberColor(i)" font-size="10" font-weight="bold"
          text-anchor="middle" dominant-baseline="central"
        >{{ i + 1 }}</text>

        <!-- 四角标记 -->
        <!-- 上升点 -->
        <template v-if="asc != null">
          <line :x1="CX" :y1="CY" :x2="pol(r - 15, asc).x" :y2="pol(r - 15, asc).y"
                stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
          <text :x="pol(r - 28, asc).x" :y="pol(r - 28, asc).y"
                fill="#ff6b6b" font-size="12" font-weight="bold" text-anchor="middle">升</text>
          <circle :cx="pol(r - 8, asc).x" :cy="pol(r - 8, asc).y" r="4" fill="#ff6b6b" stroke="#fff" stroke-width="1"/>
        </template>
        
        <!-- 下降点 -->
        <template v-if="asc != null">
          <line :x1="CX" :y1="CY" :x2="pol(r - 15, (asc + 180) % 360).x" :y2="pol(r - 15, (asc + 180) % 360).y"
                stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
          <text :x="pol(r - 28, (asc + 180) % 360).x" :y="pol(r - 28, (asc + 180) % 360).y"
                fill="#4ecdc4" font-size="12" font-weight="bold" text-anchor="middle">降</text>
          <circle :cx="pol(r - 8, (asc + 180) % 360).x" :cy="pol(r - 8, (asc + 180) % 360).y" r="4" fill="#4ecdc4" stroke="#fff" stroke-width="1"/>
        </template>

        <!-- 天顶 -->
        <template v-if="mc != null">
          <line :x1="CX" :y1="CY" :x2="pol(r - 15, mc).x" :y2="pol(r - 15, mc).y"
                stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
          <text :x="pol(r - 28, mc).x" :y="pol(r - 28, mc).y"
                fill="#ffe66d" font-size="12" font-weight="bold" text-anchor="middle">顶</text>
          <circle :cx="pol(r - 8, mc).x" :cy="pol(r - 8, mc).y" r="4" fill="#ffe66d" stroke="#fff" stroke-width="1"/>
        </template>
        
        <!-- 天底 -->
        <template v-if="mc != null">
          <line :x1="CX" :y1="CY" :x2="pol(r - 15, (mc + 180) % 360).x" :y2="pol(r - 15, (mc + 180) % 360).y"
                stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
          <text :x="pol(r - 28, (mc + 180) % 360).x" :y="pol(r - 28, (mc + 180) % 360).y"
                fill="#a29bfe" font-size="12" font-weight="bold" text-anchor="middle">底</text>
          <circle :cx="pol(r - 8, (mc + 180) % 360).x" :cy="pol(r - 8, (mc + 180) % 360).y" r="4" fill="#a29bfe" stroke="#fff" stroke-width="1"/>
        </template>

        <!-- 相位线 -->
        <line
          v-for="(a, i) in aspects"
          :key="'as'+i"
          :x1="pol(pR, a.x1).x" :y1="pol(pR, a.x1).y"
          :x2="pol(pR, a.x2).x" :y2="pol(pR, a.x2).y"
          :stroke="a.color" :stroke-width="a.width"
          :stroke-dasharray="a.dash"
          :opacity="a.opacity" stroke-linecap="round"
        />

        <!-- 行星连接线 -->
        <line
          v-for="p in displayPlanets"
          :key="'pl'+p.name"
          :x1="pol(pR, p.lng).x" :y1="pol(pR, p.lng).y"
          :x2="pol(pR + p.labelOffset + 8, p.lng).x" :y2="pol(pR + p.labelOffset + 8, p.lng).y"
          :stroke="p.color" stroke-width="1" stroke-linecap="round"
        />

        <!-- 行星 -->
        <g v-for="p in displayPlanets" :key="'p'+p.name">
          <circle
            :cx="pol(pR, p.lng).x" :cy="pol(pR, p.lng).y"
            :r="p.size" :fill="p.color" stroke="#fff" stroke-width="0.8"
            filter="url(#planetGlow)"
          />
          <text
            :x="pol(pR + p.labelOffset + 18, p.lng).x" :y="pol(pR + p.labelOffset + 18, p.lng).y"
            :fill="p.color" font-size="13" font-weight="bold"
            :text-anchor="anchor(p.lng)" dominant-baseline="central"
          >{{ p.label }}</text>
        </g>

        <!-- 中心点 -->
        <circle :cx="CX" :cy="CY" r="2.5" fill="#666" stroke="#888" stroke-width="1"/>
      </template>
    </svg>

    <!-- 全屏弹窗 -->
    <Transition name="modal">
      <div v-if="showModal" class="modal-overlay" @click="closeFullscreenModal">
        <div class="modal-content" @click.stop>
          <button class="close-btn" @click="closeFullscreenModal">
            <span class="close-icon">✕</span>
          </button>
          <div class="modal-chart-container">
            <svg
              :viewBox="`0 0 ${V} ${V}`"
              class="modal-chart-svg"
              :width="modalSize"
              :height="modalSize"
              shape-rendering="geometricPrecision"
              text-rendering="geometricPrecision"
            >
              <defs>
                <filter id="modalGlow">
                  <feGaussianBlur stdDeviation="1.5" result="b"/>
                  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
                <filter id="modalPlanetGlow">
                  <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>

              <circle :cx="CX" :cy="CY" :r="R + 35" fill="#000" />
              <circle :cx="CX" :cy="CY" :r="R + 30" fill="none" stroke="#222" stroke-width="20"/>
              <!-- 外圈刻度线 -->
              <g v-for="i in 360" :key="'modal-tick-'+i">
                <line
                  v-if="i % 15 === 0"
                  :x1="pol(R + 22, i).x" :y1="pol(R + 22, i).y"
                  :x2="pol(R + 26, i).x" :y2="pol(R + 26, i).y"
                  stroke="#333" stroke-width="0.5"
                />
              </g>
              <circle :cx="CX" :cy="CY" :r="R" fill="#000" stroke="#333" stroke-width="2"/>

              <!-- 中心小圆 -->
              <circle :cx="CX" :cy="CY" r="2" fill="#666" stroke="#888" stroke-width="1"/>

              <template v-if="ready">
                <!-- 宫位分隔线（淡黄色，连到圆心） -->
                <line
                  v-for="(h, i) in houses"
                  :key="'modal-hl'+i"
                  :x1="CX" :y1="CY"
                  :x2="pol(R + 25, h.cusp).x" :y2="pol(R + 25, h.cusp).y"
                  :stroke="isAxisCusp(i) ? '#8a7500' : '#5a5000'" 
                  :stroke-width="isAxisCusp(i) ? 1 : 0.6"
                />

                <!-- 星座刻度线 -->
                <line
                  v-for="s in zodiacs"
                  :key="'modal-zn-line-'+s.name"
                  :x1="pol(R + 15, s.deg).x" :y1="pol(R + 15, s.deg).y"
                  :x2="pol(R + 25, s.deg).x" :y2="pol(R + 25, s.deg).y"
                  stroke="#555" stroke-width="0.5"
                />

                <!-- 星座刻度标记（暗色小菱形） -->
                <polygon
                  v-for="s in zodiacs"
                  :key="'modal-zn-diamond-'+s.name"
                  :points="diamond(s.deg)"
                  fill="#444"
                />

                <text
                  v-for="s in zodiacs"
                  :key="'modal-zn-'+s.name"
                  :x="pol(R + 20, s.deg).x" :y="pol(R + 20, s.deg).y"
                  :fill="s.color" font-size="14" font-weight="bold"
                  text-anchor="middle" dominant-baseline="central"
                >{{ s.name }}</text>

                <text
                  v-for="(h, i) in houses"
                  :key="'modal-hn'+i"
                  :x="pol(R - 10, (h.cusp + nextCusp(i)) / 2).x"
                  :y="pol(R - 10, (h.cusp + nextCusp(i)) / 2).y"
                  :fill="getHouseNumberColor(i)" font-size="10" font-weight="bold"
                  text-anchor="middle" dominant-baseline="central"
                >{{ i + 1 }}</text>

                <template v-if="asc != null">
                  <line :x1="CX" :y1="CY" :x2="pol(r - 15, asc).x" :y2="pol(r - 15, asc).y"
                        stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
                  <text :x="pol(r - 28, asc).x" :y="pol(r - 28, asc).y"
                        fill="#ff6b6b" font-size="12" font-weight="bold" text-anchor="middle">升</text>
                  <circle :cx="pol(r - 8, asc).x" :cy="pol(r - 8, asc).y" r="4" fill="#ff6b6b" stroke="#fff" stroke-width="1"/>
                </template>

                <template v-if="asc != null">
                  <line :x1="CX" :y1="CY" :x2="pol(r - 15, (asc + 180) % 360).x" :y2="pol(r - 15, (asc + 180) % 360).y"
                        stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
                  <text :x="pol(r - 28, (asc + 180) % 360).x" :y="pol(r - 28, (asc + 180) % 360).y"
                        fill="#4ecdc4" font-size="12" font-weight="bold" text-anchor="middle">降</text>
                  <circle :cx="pol(r - 8, (asc + 180) % 360).x" :cy="pol(r - 8, (asc + 180) % 360).y" r="4" fill="#4ecdc4" stroke="#fff" stroke-width="1"/>
                </template>

                <template v-if="mc != null">
                  <line :x1="CX" :y1="CY" :x2="pol(r - 15, mc).x" :y2="pol(r - 15, mc).y"
                        stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
                  <text :x="pol(r - 28, mc).x" :y="pol(r - 28, mc).y"
                        fill="#ffe66d" font-size="12" font-weight="bold" text-anchor="middle">顶</text>
                  <circle :cx="pol(r - 8, mc).x" :cy="pol(r - 8, mc).y" r="4" fill="#ffe66d" stroke="#fff" stroke-width="1"/>
                </template>

                <template v-if="mc != null">
                  <line :x1="CX" :y1="CY" :x2="pol(r - 15, (mc + 180) % 360).x" :y2="pol(r - 15, (mc + 180) % 360).y"
                        stroke="#555" stroke-width="0.5" stroke-dasharray="4,3"/>
                  <text :x="pol(r - 28, (mc + 180) % 360).x" :y="pol(r - 28, (mc + 180) % 360).y"
                        fill="#a29bfe" font-size="12" font-weight="bold" text-anchor="middle">底</text>
                  <circle :cx="pol(r - 8, (mc + 180) % 360).x" :cy="pol(r - 8, (mc + 180) % 360).y" r="4" fill="#a29bfe" stroke="#fff" stroke-width="1"/>
                </template>

                <line
                  v-for="(a, i) in aspects"
                  :key="'modal-as'+i"
                  :x1="pol(pR, a.x1).x" :y1="pol(pR, a.x1).y"
                  :x2="pol(pR, a.x2).x" :y2="pol(pR, a.x2).y"
                  :stroke="a.color" :stroke-width="a.width"
                  :stroke-dasharray="a.dash"
                  :opacity="a.opacity" stroke-linecap="round"
                />

                <line
                  v-for="p in displayPlanets"
                  :key="'modal-pl'+p.name"
                  :x1="pol(pR, p.lng).x" :y1="pol(pR, p.lng).y"
                  :x2="pol(pR + p.labelOffset + 8, p.lng).x" :y2="pol(pR + p.labelOffset + 8, p.lng).y"
                  :stroke="p.color" stroke-width="1" stroke-linecap="round"
                />

                <g v-for="p in displayPlanets" :key="'modal-p'+p.name">
                  <circle
                    :cx="pol(pR, p.lng).x" :cy="pol(pR, p.lng).y"
                    :r="p.size" :fill="p.color" stroke="#fff" stroke-width="0.8"
                    filter="url(#modalPlanetGlow)"
                  />
                  <text
                    :x="pol(pR + p.labelOffset + 18, p.lng).x" :y="pol(pR + p.labelOffset + 18, p.lng).y"
                    :fill="p.color" font-size="13" font-weight="bold"
                    :text-anchor="anchor(p.lng)" dominant-baseline="central"
                  >{{ p.label }}</text>
                </g>

                <circle :cx="CX" :cy="CY" r="2.5" fill="#666" stroke="#888" stroke-width="1"/>
              </template>
            </svg>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  chartData: { type: Object, default: () => ({}) },
  size: { type: Number, default: 500 }
})

const V = ref(500)
const showModal = ref(false)
const modalSize = ref(600)

const CX = computed(() => V.value / 2)
const CY = computed(() => V.value / 2)
const R = computed(() => 220)
const r = computed(() => 80)
const pR = computed(() => r.value + (R.value - r.value) * 0.55)

function openFullscreenModal() {
  showModal.value = true
  document.body.style.overflow = 'hidden'
  updateModalSize()
}

function closeFullscreenModal() {
  showModal.value = false
  document.body.style.overflow = ''
}

function updateModalSize() {
  const maxSize = Math.min(window.innerWidth - 40, window.innerHeight - 40)
  modalSize.value = Math.min(maxSize, 700)
}

function handleKeydown(e) {
  if (e.key === 'Escape' && showModal.value) {
    closeFullscreenModal()
  }
}

onMounted(() => {
  window.addEventListener('resize', updateModalSize)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateModalSize)
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})

const zodiacs = [
  { name: '羊', deg: 0, color: '#ff6b6b' },
  { name: '牛', deg: 30, color: '#ffb347' },
  { name: '双', deg: 60, color: '#77dd77' },
  { name: '蟹', deg: 90, color: '#a29bfe' },
  { name: '狮', deg: 120, color: '#ff6b6b' },
  { name: '处', deg: 150, color: '#ffe66d' },
  { name: '秤', deg: 180, color: '#4ecdc4' },
  { name: '蝎', deg: 210, color: '#ff6b6b' },
  { name: '射', deg: 240, color: '#ffe66d' },
  { name: '摩', deg: 270, color: '#a29bfe' },
  { name: '瓶', deg: 300, color: '#77dd77' },
  { name: '鱼', deg: 330, color: '#4ecdc4' }
]

const PLANET_INFO = {
  '太阳': { label: '日', color: '#ffe66d', size: 3.5 },
  '月亮': { label: '月', color: '#a29bfe', size: 3.5 },
  '水星': { label: '水', color: '#77dd77', size: 3 },
  '金星': { label: '金', color: '#ffb347', size: 3 },
  '火星': { label: '火', color: '#ff6b6b', size: 3 },
  '木星': { label: '木', color: '#ffe66d', size: 3 },
  '土星': { label: '土', color: '#a29bfe', size: 3 },
  '天王星': { label: '天', color: '#77dd77', size: 2.5 },
  '海王星': { label: '海', color: '#4ecdc4', size: 2.5 },
  '冥王星': { label: '冥', color: '#ffb347', size: 2.5 },
  '北交点': { label: '北', color: '#4ecdc4', size: 2.5 },
  '南交点': { label: '南', color: '#ff6b6b', size: 2.5 },
  '婚神星': { label: '婚', color: '#ffb347', size: 2.5 },
  '天顶': { label: '顶', color: '#ffe66d', size: 3 },
  '福点': { label: '福', color: '#77dd77', size: 2.5 }
}

const ASPECT_INFO = {
  '合相': { color: '#ff6b6b', width: 2.5, dash: 'none', opacity: 0.85 },
  '对分相': { color: '#ff6b6b', width: 2, dash: 'none', opacity: 0.8 },
  '四分相': { color: '#ff6b6b', width: 2, dash: 'none', opacity: 0.8 },
  '三分相': { color: '#77dd77', width: 2, dash: 'none', opacity: 0.75 },
  '六分相': { color: '#4ecdc4', width: 1.8, dash: 'none', opacity: 0.7 }
}

const MAJOR_PLANETS = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星', '北交点', '南交点', '婚神星', '天顶', '福点']
const MAJOR_ASPECTS = ['合相', '对分相', '四分相', '三分相', '六分相']

const ready = computed(() => props.chartData?.planets?.length > 0)

const rawPlanets = computed(() => props.chartData?.planets || [])

const houses = computed(() => {
  const h = props.chartData?.houses
  if (!h) return defHouses()
  if (!Array.isArray(h)) {
    const arr = []
    for (let i = 1; i <= 12; i++) arr.push({ cusp: h[i] || (i - 1) * 30 })
    return arr
  }
  return h.map((v, i) => typeof v === 'object' && v.cusp != null ? v : { cusp: v || i * 30 })
})

const asc = computed(() => {
  const p = rawPlanets.value.find(p => p.name === '上升点' || p.name === 'Ascendant')
  return p?.longitude
})

const mc = computed(() => {
  const p = rawPlanets.value.find(p => p.name === '天顶' || p.name === 'Midheaven')
  return p?.longitude
})

const displayPlanets = computed(() => {
  const planets = rawPlanets.value
    .filter(p => MAJOR_PLANETS.includes(p.name))
    .map(p => ({
      name: p.name,
      lng: p.longitude,
      label: PLANET_INFO[p.name]?.label || p.name.charAt(0),
      color: PLANET_INFO[p.name]?.color || '#888',
      size: PLANET_INFO[p.name]?.size || 3,
      labelOffset: 0
    }))

  planets.sort((a, b) => a.lng - b.lng)

  for (let i = 0; i < planets.length; i++) {
    let offset = 0
    for (let j = 0; j < i; j++) {
      const diff = Math.abs(planets[i].lng - planets[j].lng)
      const normalizedDiff = Math.min(diff, 360 - diff)
      if (normalizedDiff < 8) {
        offset += 12
      }
    }
    planets[i].labelOffset = offset
  }

  return planets
})

const aspects = computed(() => {
  return (props.chartData?.aspects || [])
    .filter(a => MAJOR_ASPECTS.includes(a.aspect) && 
                 MAJOR_PLANETS.includes(a.planet1) && 
                 MAJOR_PLANETS.includes(a.planet2))
    .map(a => {
      const p1 = rawPlanets.value.find(p => p.name === a.planet1)
      const p2 = rawPlanets.value.find(p => p.name === a.planet2)
      const info = ASPECT_INFO[a.aspect]
      return { 
        x1: p1?.longitude || 0, 
        x2: p2?.longitude || 0, 
        color: info?.color || '#666', 
        width: info?.width || 1,
        dash: info?.dash || 'none',
        opacity: info?.opacity || 0.7
      }
    })
})

function defHouses() {
  return Array.from({ length: 12 }, (_, i) => ({ cusp: i * 30 }))
}

function pol(radius, deg) {
  const rad = (deg - 90) * Math.PI / 180
  return { x: CX.value + radius * Math.cos(rad), y: CY.value + radius * Math.sin(rad) }
}

function diamond(deg) {
  const center = pol(R + 20, deg)
  const rad = (deg - 90) * Math.PI / 180
  const perpRad = rad + Math.PI / 2
  const size = 4
  const p1 = { x: center.x + Math.cos(rad) * size, y: center.y + Math.sin(rad) * size }
  const p2 = { x: center.x + Math.cos(perpRad) * size, y: center.y + Math.sin(perpRad) * size }
  const p3 = { x: center.x - Math.cos(rad) * size, y: center.y - Math.sin(rad) * size }
  const p4 = { x: center.x - Math.cos(perpRad) * size, y: center.y - Math.sin(perpRad) * size }
  return `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`
}

function nextCusp(i) {
  return houses.value[(i + 1) % 12]?.cusp || 0
}

function anchor(lng) {
  const a = lng % 360
  if (a > 45 && a < 135) return 'start'
  if (a > 225 && a < 315) return 'end'
  return 'middle'
}

function getHouseNumberColor(index) {
  const colors = ['#ff6b6b', '#ffb347', '#77dd77', '#a29bfe', '#ffe66d', '#4ecdc4']
  return colors[index % 6]
}

function isAxisCusp(index) {
  const axisPositions = [0, 3, 6, 9]
  return axisPositions.includes(index)
}
</script>

<style scoped>
.chart-wheel-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  position: relative;
}

.zoom-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(30, 30, 30, 0.8);
  border: 1px solid #444;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
}

.zoom-btn:hover {
  background: rgba(50, 50, 50, 0.9);
  border-color: #666;
  transform: scale(1.1);
}

.zoom-icon {
  font-size: 18px;
}

.chart-svg {
  max-width: 100%;
  max-height: 100%;
  width: 100%;
  height: auto;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: pointer;
  overflow: hidden;
}

.modal-content {
  background: #000;
  border-radius: 0;
  padding: 0;
  position: relative;
  cursor: default;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(50, 50, 50, 0.8);
  border: 1px solid #555;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(70, 70, 70, 0.9);
  transform: scale(1.1);
}

.close-icon {
  color: #fff;
  font-size: 16px;
}

.modal-chart-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-chart-svg {
  max-width: 100%;
  max-height: 100%;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}
</style>