<template>
  <div 
    class="three-astro-sphere" 
    ref="containerRef"
    :class="{ 'fullscreen-mode': isFullscreen, 'multi-mode': isMultiMemberMode }"
    @dblclick="handleDoubleClick"
  >
    <div class="control-panel">
      <button 
        class="control-btn" 
        @click="zoomIn"
        :title="'放大'"
      >
        <span class="btn-icon">🔍+</span>
      </button>
      <button 
        class="control-btn" 
        @click="zoomOut"
        :title="'缩小'"
      >
        <span class="btn-icon">🔍-</span>
      </button>
      <button 
        class="control-btn" 
        @click="resetView"
        :title="'重置视角'"
      >
        <span class="btn-icon">⟲</span>
      </button>
      <button 
        class="control-btn primary" 
        @click="toggleFullscreen"
        :title="isFullscreen ? '退出全屏' : '全屏查看'"
      >
        <span class="btn-icon">{{ isFullscreen ? '⛶' : '⛶' }}</span>
      </button>
    </div>
    
    <div v-if="isFullscreen" class="fullscreen-hint">
      <span>双击任意位置或点击右上角按钮退出全屏</span>
    </div>
    
    <div v-if="selectedPlanetInfo" class="planet-info-panel">
      <div class="panel-header">
        <span class="planet-name" v-if="selectedPlanetInfo.memberName">
          {{ selectedPlanetInfo.memberName }} - {{ selectedPlanetInfo.name }}
        </span>
        <span class="planet-name" v-else>{{ selectedPlanetInfo.name }}</span>
        <button class="close-btn" @click="handleDeselectPlanet">×</button>
      </div>
      <div class="panel-content">
        <div class="info-row">
          <span class="info-label">星座</span>
          <span class="info-value">{{ selectedPlanetInfo.zodiac }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">度数</span>
          <span class="info-value">{{ selectedPlanetInfo.degree }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">宫位</span>
          <span class="info-value">第{{ selectedPlanetInfo.house }}宫</span>
        </div>
        <div class="info-row" v-if="selectedPlanetInfo.isRetrograde">
          <span class="info-label">状态</span>
          <span class="info-value retro">逆行</span>
        </div>
        <div class="aspects-section" v-if="selectedPlanetInfo.aspects.length > 0">
          <div class="section-title">相位关系</div>
          <div 
            v-for="(aspect, idx) in selectedPlanetInfo.aspects" 
            :key="idx"
            class="aspect-item"
            :class="aspect.nature"
          >
            <span class="aspect-sym">{{ aspect.symbol }}</span>
            <span class="aspect-text">
              {{ aspect.otherMember ? aspect.otherMember + ' - ' : '' }}{{ aspect.otherPlanet }} {{ aspect.type }} (容许度 {{ aspect.orb }}°)
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="hoveredPlanetName && !selectedPlanetName" class="hover-tooltip">
      <span class="hover-sym">{{ hoveredPlanetSymbol }}</span>
      <span class="hover-name">{{ hoveredPlanetName }}</span>
      <span class="hover-member" v-if="hoveredMemberName">({{ hoveredMemberName }})</span>
    </div>

    <div v-if="isMultiMemberMode && members.length > 0" class="member-legend">
      <div class="legend-title">成员</div>
      <div class="legend-items">
        <div 
          v-for="(member, idx) in members" 
          :key="idx"
          class="legend-item"
          :class="{ 
            'highlighted': focusedMemberIndex === idx,
            'dimmed': focusedMemberIndex !== null && focusedMemberIndex !== idx && !isPairFocused(idx)
          }"
          @click="handleMemberLegendClick(idx)"
        >
          <div class="legend-dot" :style="{ background: getMemberColorHex(idx) }"></div>
          <span class="legend-name">{{ member.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as THREE from 'three'
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  useThreeScene,
  usePlanetRenderer,
  useAspectLineRenderer,
  useInteractionManager,
  useMultiMemberRenderer,
  PLANET_SYMBOLS,
  ASPECT_SYMBOLS
} from '@/composables/threeAstro'

const props = defineProps({
  chartData: {
    type: Object,
    default: null
  },
  members: {
    type: Array,
    default: null
  },
  matrix: {
    type: Object,
    default: null
  },
  size: {
    type: Number,
    default: 600
  },
  focusedMemberIndex: {
    type: Number,
    default: null
  },
  focusedPair: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['planet-select', 'member-focus', 'pair-focus'])

const containerRef = ref(null)

const hoveredPlanetName = ref('')
const hoveredPlanetSymbol = ref('')
const hoveredMemberName = ref('')
const selectedPlanetName = ref('')
const selectedPlanetInfo = ref(null)
const isFullscreen = ref(false)

let sceneManager = null
let planetRenderer = null
let aspectLineRenderer = null
let interactionManager = null
let multiMemberRenderer = null

const MEMBER_COLORS = [
  0xff8c32, 0x50c8ff, 0x22c55e, 0xef4444, 0x8b5cf6,
  0xf59e0b, 0x06b6d4, 0xec4899, 0x6366f1, 0x10b981
]

const isMultiMemberMode = computed(() => {
  return props.members && props.members.length > 0
})

const hasChartData = computed(() => {
  if (isMultiMemberMode.value) {
    return props.members.some(m => m.chart?.planets)
  }
  return props.chartData && props.chartData.planets
})

const isPairFocused = (idx) => {
  if (!props.focusedPair) return false
  return props.focusedPair.a === idx || props.focusedPair.b === idx
}

function getMemberColorHex(idx) {
  const color = MEMBER_COLORS[idx % MEMBER_COLORS.length]
  return '#' + color.toString(16).padStart(6, '0')
}

function init() {
  if (!containerRef.value) return
  
  sceneManager = useThreeScene()
  
  sceneManager.init(
    containerRef.value,
    { width: props.size, height: props.size }
  )
  
  if (isMultiMemberMode.value) {
    multiMemberRenderer = useMultiMemberRenderer(
      sceneManager.getScene,
      sceneManager.getCamera,
      sceneManager.registerForDispose
    )
    
    interactionManager = useInteractionManager(
      () => containerRef.value,
      sceneManager.getCamera,
      sceneManager.getRenderer,
      multiMemberRenderer.getAllMeshes,
      handleMultiMemberPlanetHighlight,
      handleMultiMemberPlanetReset,
      multiMemberRenderer.clearHighlights,
      handleMultiMemberPlanetSelect,
      handlePointerLeave
    )
  } else {
    planetRenderer = usePlanetRenderer(
      sceneManager.getScene,
      sceneManager.getCamera,
      sceneManager.registerForDispose
    )
    
    aspectLineRenderer = useAspectLineRenderer(
      sceneManager.getScene,
      planetRenderer.getPlanetMesh,
      sceneManager.registerForDispose
    )
    
    interactionManager = useInteractionManager(
      () => containerRef.value,
      sceneManager.getCamera,
      sceneManager.getRenderer,
      planetRenderer.getAllPlanetMeshes,
      planetRenderer.highlightPlanet,
      planetRenderer.resetPlanetHighlight,
      planetRenderer.resetAllPlanets,
      handlePlanetSelect,
      handlePointerLeave
    )
  }
  
  const renderer = sceneManager.getRenderer()
  if (renderer && renderer.domElement) {
    interactionManager.setupEventListeners(renderer.domElement)
  }
  
  sceneManager.startAnimation(onBeforeRender)
  
  window.addEventListener('resize', handleResize)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  
  if (hasChartData.value) {
    setTimeout(() => {
      updateChartContent()
    }, 100)
  }
}

function onBeforeRender(delta) {
  if (isMultiMemberMode.value && multiMemberRenderer) {
    multiMemberRenderer.updatePlanetAnimations()
  } else if (planetRenderer) {
    planetRenderer.updatePlanetAnimations()
  }
  
  const scene = sceneManager ? sceneManager.getScene() : null
  if (scene) {
    const zodiacRing = scene.children.find(child => child.userData?.type === 'zodiacRing')
    if (zodiacRing) {
      zodiacRing.rotation.y += 0.0005
    }
  }
  
  if (interactionManager) {
    const hoverResult = interactionManager.forceHoverCheck()
    if (hoverResult && hoverResult.hoveredPlanet && !selectedPlanetName.value) {
      hoveredPlanetName.value = hoverResult.hoveredPlanet
      hoveredPlanetSymbol.value = hoverResult.hoveredSymbol
      
      if (hoverResult.mesh?.userData?.memberIndex !== undefined && props.members) {
        const memberIdx = hoverResult.mesh.userData.memberIndex
        hoveredMemberName.value = props.members[memberIdx]?.name || ''
      } else {
        hoveredMemberName.value = ''
      }
    }
  }
}

function updateChartContent() {
  if (isMultiMemberMode.value) {
    if (!multiMemberRenderer || !props.members) return
    
    multiMemberRenderer.clearAll()
    multiMemberRenderer.renderMembers(props.members, props.focusedMemberIndex)
    
    if (props.matrix) {
      multiMemberRenderer.renderCrossMemberAspects(props.members, props.matrix)
    }
    
    if (props.focusedMemberIndex !== null) {
      multiMemberRenderer.highlightMember(props.focusedMemberIndex)
    } else if (props.focusedPair) {
      multiMemberRenderer.highlightPair(props.focusedPair.a, props.focusedPair.b)
    }
  } else {
    if (!props.chartData || !planetRenderer || !aspectLineRenderer) return
    
    planetRenderer.createPlanets(props.chartData)
    aspectLineRenderer.createAspectLines(props.chartData)
  }
}

function handleMultiMemberPlanetHighlight(planetName, mesh) {
  if (!mesh || !multiMemberRenderer) return
  
  const memberIndex = mesh.userData.memberIndex
  if (memberIndex !== undefined) {
    multiMemberRenderer.highlightMember(memberIndex)
  }
}

function handleMultiMemberPlanetReset(planetName, mesh) {
  if (!multiMemberRenderer) return
  
  if (props.focusedMemberIndex !== null) {
    multiMemberRenderer.highlightMember(props.focusedMemberIndex)
  } else if (props.focusedPair) {
    multiMemberRenderer.highlightPair(props.focusedPair.a, props.focusedPair.b)
  } else {
    multiMemberRenderer.clearHighlights()
  }
}

function handleMultiMemberPlanetSelect(planetData, planetName, mesh) {
  if (!planetData || !planetName || !mesh) {
    handleDeselectPlanet()
    return
  }
  
  const memberIndex = mesh.userData.memberIndex
  const memberName = props.members?.[memberIndex]?.name || ''
  
  const aspects = collectAspectsForPlanet(memberIndex, planetName)
  
  selectedPlanetName.value = planetName
  selectedPlanetInfo.value = {
    name: planetName,
    memberIndex: memberIndex,
    memberName: memberName,
    zodiac: planetData.zodiac?.sign || '未知',
    degree: planetData.zodiac?.dms?.formatted || '',
    house: planetData.house || 0,
    isRetrograde: planetData.is_retrograde || false,
    aspects: aspects
  }
  
  hoveredPlanetName.value = ''
  hoveredPlanetSymbol.value = ''
  hoveredMemberName.value = ''
  
  emit('planet-select', { 
    planetData, 
    planetName, 
    memberIndex,
    memberName 
  })
}

function collectAspectsForPlanet(memberIndex, planetName) {
  const aspects = []
  
  if (!props.matrix?.pairs) return aspects
  
  const currentMemberName = props.members?.[memberIndex]?.name
  if (!currentMemberName) return aspects
  
  props.matrix.pairs.forEach(pair => {
    const [nameA, nameB] = pair.pair
    const isPairMember = nameA === currentMemberName || nameB === currentMemberName
    
    if (!isPairMember) return
    
    const otherMemberName = nameA === currentMemberName ? nameB : nameA
    const otherMemberIndex = props.members?.findIndex(m => m.name === otherMemberName)
    
    pair.aspects?.forEach(aspect => {
      const isRelevant = 
        (aspect.planet_a === planetName && nameA === currentMemberName) ||
        (aspect.planet_b === planetName && nameB === currentMemberName) ||
        (aspect.planet_a === planetName && nameB === currentMemberName) ||
        (aspect.planet_b === planetName && nameA === currentMemberName)
      
      if (isRelevant) {
        const otherPlanet = (aspect.planet_a === planetName) ? aspect.planet_b : aspect.planet_a
        
        aspects.push({
          symbol: ASPECT_SYMBOLS[aspect.aspect] || '',
          otherPlanet: otherPlanet,
          otherMember: otherMemberName,
          otherMemberIndex: otherMemberIndex,
          type: aspect.aspect,
          orb: aspect.orb || 0,
          nature: aspect.nature || 'neutral'
        })
      }
    })
  })
  
  return aspects
}

function handlePlanetSelect(planetData, planetName) {
  if (isMultiMemberMode.value) {
    handleMultiMemberPlanetSelect(planetData, planetName, null)
    return
  }
  
  if (planetData && planetName) {
    if (aspectLineRenderer) {
      aspectLineRenderer.highlightAspectLinesForPlanet(planetName)
    }
    
    const planetAspects = aspectLineRenderer 
      ? aspectLineRenderer.getAspectsForPlanet(planetName, props.chartData)
      : []
    
    selectedPlanetName.value = planetName
    selectedPlanetInfo.value = {
      name: planetName,
      zodiac: planetData.zodiac?.sign || '未知',
      degree: planetData.zodiac?.dms?.formatted || '',
      house: planetData.house || 0,
      isRetrograde: planetData.is_retrograde || false,
      aspects: planetAspects
    }
    
    hoveredPlanetName.value = ''
    hoveredPlanetSymbol.value = ''
    
    emit('planet-select', { planetData, planetName })
  } else {
    handleDeselectPlanet()
  }
}

function handleDeselectPlanet() {
  if (isMultiMemberMode.value) {
    if (multiMemberRenderer) {
      if (props.focusedMemberIndex !== null) {
        multiMemberRenderer.highlightMember(props.focusedMemberIndex)
      } else if (props.focusedPair) {
        multiMemberRenderer.highlightPair(props.focusedPair.a, props.focusedPair.b)
      } else {
        multiMemberRenderer.clearHighlights()
      }
    }
  } else {
    if (planetRenderer) {
      planetRenderer.resetAllPlanets()
    }
    
    if (aspectLineRenderer) {
      aspectLineRenderer.clearHighlightedAspectLines()
    }
  }
  
  selectedPlanetName.value = ''
  selectedPlanetInfo.value = null
  
  emit('planet-select', null)
}

function handleMemberLegendClick(idx) {
  if (props.focusedMemberIndex === idx) {
    emit('member-focus', null)
  } else {
    emit('member-focus', idx)
  }
}

function handlePointerLeave() {
  if (!selectedPlanetName.value) {
    hoveredPlanetName.value = ''
    hoveredPlanetSymbol.value = ''
    hoveredMemberName.value = ''
  }
}

function handleResize() {
  if (sceneManager) {
    sceneManager.onResize()
  }
}

function zoomIn() {
  if (sceneManager) {
    const controls = sceneManager.getControls()
    const camera = sceneManager.getCamera()
    
    if (controls && camera) {
      const currentDistance = controls.getDistance()
      const targetDistance = Math.max(controls.minDistance, currentDistance - 2)
      
      const direction = new THREE.Vector3()
      camera.getWorldDirection(direction)
      direction.normalize()
      
      const distanceDiff = currentDistance - targetDistance
      camera.position.addScaledVector(direction, distanceDiff)
      
      controls.update()
    }
  }
}

function zoomOut() {
  if (sceneManager) {
    const controls = sceneManager.getControls()
    const camera = sceneManager.getCamera()
    
    if (controls && camera) {
      const currentDistance = controls.getDistance()
      const targetDistance = Math.min(controls.maxDistance, currentDistance + 2)
      
      const direction = new THREE.Vector3()
      camera.getWorldDirection(direction)
      direction.normalize()
      
      const distanceDiff = targetDistance - currentDistance
      camera.position.addScaledVector(direction, -distanceDiff)
      
      controls.update()
    }
  }
}

function resetView() {
  if (sceneManager) {
    const controls = sceneManager.getControls()
    const camera = sceneManager.getCamera()
    
    if (controls) {
      controls.reset()
    }
    
    if (camera) {
      camera.position.set(0, 6, 18)
      camera.lookAt(0, 0, 0)
    }
  }
}

function toggleFullscreen() {
  if (!containerRef.value) return
  
  if (!document.fullscreenElement) {
    containerRef.value.requestFullscreen().catch(err => {
      console.error('全屏请求失败:', err)
    })
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function handleDoubleClick() {
  if (isFullscreen.value) {
    toggleFullscreen()
  } else {
    if (sceneManager) {
      const camera = sceneManager.getCamera()
      const controls = sceneManager.getControls()
      
      if (camera && controls) {
        const currentDistance = controls.getDistance()
        const targetDistance = Math.max(controls.minDistance + 2, currentDistance * 0.6)
        
        const animateZoom = () => {
          const now = controls.getDistance()
          if (Math.abs(now - targetDistance) > 0.1) {
            const step = (targetDistance - now) * 0.1
            const cameraDirection = new THREE.Vector3()
            camera.getWorldDirection(cameraDirection)
            camera.position.addScaledVector(cameraDirection, step)
            requestAnimationFrame(animateZoom)
          }
        }
        animateZoom()
      }
    }
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

function dispose() {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  
  if (interactionManager) {
    interactionManager.dispose()
  }
  
  if (aspectLineRenderer) {
    aspectLineRenderer.dispose()
  }
  
  if (planetRenderer) {
    planetRenderer.dispose()
  }
  
  if (multiMemberRenderer) {
    multiMemberRenderer.dispose()
  }
  
  if (sceneManager) {
    sceneManager.dispose()
  }
  
  sceneManager = null
  planetRenderer = null
  aspectLineRenderer = null
  interactionManager = null
  multiMemberRenderer = null
}

watch(() => [props.members, props.matrix], () => {
  if (hasChartData.value && multiMemberRenderer) {
    nextTick(() => {
      updateChartContent()
    })
  }
}, { deep: true })

watch(() => props.chartData, (newData) => {
  if (newData && newData.planets && !isMultiMemberMode.value) {
    if (planetRenderer && aspectLineRenderer) {
      nextTick(() => {
        updateChartContent()
      })
    } else {
      const checkInterval = setInterval(() => {
        if (planetRenderer && aspectLineRenderer) {
          clearInterval(checkInterval)
          updateChartContent()
        }
      }, 50)
      setTimeout(() => clearInterval(checkInterval), 2000)
    }
  }
}, { deep: true })

watch(() => props.focusedMemberIndex, (newIdx) => {
  if (multiMemberRenderer) {
    if (newIdx !== null) {
      multiMemberRenderer.highlightMember(newIdx)
    } else if (props.focusedPair) {
      multiMemberRenderer.highlightPair(props.focusedPair.a, props.focusedPair.b)
    } else {
      multiMemberRenderer.clearHighlights()
    }
  }
})

watch(() => props.focusedPair, (newPair) => {
  if (multiMemberRenderer) {
    if (newPair) {
      multiMemberRenderer.highlightPair(newPair.a, newPair.b)
    } else if (props.focusedMemberIndex !== null) {
      multiMemberRenderer.highlightMember(props.focusedMemberIndex)
    } else {
      multiMemberRenderer.clearHighlights()
    }
  }
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    init()
  })
})

onUnmounted(() => {
  dispose()
})
</script>

<style scoped>
.three-astro-sphere {
  width: 100%;
  height: 550px;
  min-height: 500px;
  position: relative;
  background: radial-gradient(ellipse at center, #1a1a3a 0%, #080814 100%);
  border-radius: 12px;
  overflow: hidden;
}

.three-astro-sphere.multi-mode {
  height: 600px;
}

.three-astro-sphere :deep(canvas) {
  display: block !important;
  max-width: 100%;
  max-height: 100%;
}

.planet-info-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 300px;
  background: rgba(15, 15, 35, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  padding: 16px;
  z-index: 100;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.planet-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.close-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(139, 92, 246, 0.2);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.4);
  color: #fff;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.info-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
}

.info-value.retro {
  color: #ef4444;
}

.aspects-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.15);
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
}

.aspect-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(139, 92, 246, 0.1);
  margin-bottom: 4px;
}

.aspect-item.harmonious {
  border-left: 2px solid #22c55e;
}

.aspect-item.challenging {
  border-left: 2px solid #ef4444;
}

.aspect-item.neutral {
  border-left: 2px solid #fbbf24;
}

.aspect-sym {
  font-size: 1.1rem;
  font-weight: bold;
}

.aspect-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.75);
}

.hover-tooltip {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 15, 35, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 100;
  animation: fadeIn 0.2s ease;
  pointer-events: none;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.hover-sym {
  font-size: 1.3rem;
}

.hover-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.hover-member {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.control-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 100;
}

.control-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: rgba(15, 15, 35, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: rgba(139, 92, 246, 0.3);
  border-color: rgba(139, 92, 246, 0.5);
  color: #fff;
  transform: scale(1.05);
}

.control-btn:active {
  transform: scale(0.95);
}

.control-btn.primary {
  background: rgba(139, 92, 246, 0.4);
  border-color: rgba(139, 92, 246, 0.6);
}

.control-btn.primary:hover {
  background: rgba(139, 92, 246, 0.6);
}

.btn-icon {
  font-size: 16px;
  line-height: 1;
}

.member-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: rgba(15, 15, 35, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  z-index: 100;
}

.legend-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(139, 92, 246, 0.1);
}

.legend-item:hover {
  background: rgba(139, 92, 246, 0.2);
}

.legend-item.highlighted {
  background: rgba(139, 92, 246, 0.3);
  border: 1px solid rgba(139, 92, 246, 0.5);
}

.legend-item.dimmed {
  opacity: 0.3;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-name {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
}

.three-astro-sphere.fullscreen-mode {
  width: 100vw !important;
  height: 100vh !important;
  min-height: 100vh !important;
  border-radius: 0 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  z-index: 9999 !important;
}

.fullscreen-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px;
  padding: 10px 20px;
  z-index: 100;
  pointer-events: none;
  animation: fadeInOut 3s ease-in-out infinite;
}

.fullscreen-hint span {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.three-astro-sphere.fullscreen-mode .control-panel {
  top: 24px;
  right: 24px;
}

.three-astro-sphere.fullscreen-mode .control-btn {
  width: 48px;
  height: 48px;
}

.three-astro-sphere.fullscreen-mode .btn-icon {
  font-size: 18px;
}

.three-astro-sphere.fullscreen-mode .planet-info-panel {
  top: 24px;
  right: 90px;
}

.three-astro-sphere.fullscreen-mode .member-legend {
  bottom: 24px;
  left: 24px;
}
</style>
