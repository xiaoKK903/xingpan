import * as THREE from 'three'

export const THREE_ASTRO_CONFIG = {
  PLANET_ORBIT_RADIUS: 6.5,
  ZODIAC_RADIUS: 13.5,
  HOUSE_RADIUS: 11.0,
  STAR_RADIUS: 60,
  CAMERA_DISTANCE: 25,
  CAMERA_HEIGHT: 12,
  MIN_ZOOM: 5,
  MAX_ZOOM: 80,
  AUTO_ROTATE_SPEED: 0.15,
  DAMPING_FACTOR: 0.05,
  STAR_COUNT: 3000,
  PLANET_SEGMENTS: 32,
  ASPECT_LINE_SEGMENTS: 24,
  ZODIAC_TILT: -Math.PI / 5,
  ORBIT_TILT: -Math.PI / 6
}

export const PLANET_ORBIT_RADII = {
  '太阳': 6.0,
  '月亮': 4.5,
  '水星': 3.8,
  '金星': 4.3,
  '火星': 5.2,
  '木星': 7.8,
  '土星': 9.2,
  '天王星': 10.5,
  '海王星': 11.5,
  '冥王星': 12.8,
  '北交点': 3.0,
  '南交点': 3.0
}

export const PLANET_Y_OFFSETS = {
  '太阳': 0,
  '月亮': 0.5,
  '水星': 0.8,
  '金星': -0.6,
  '火星': -0.3,
  '木星': 1.5,
  '土星': -1.3,
  '天王星': 1.0,
  '海王星': -0.8,
  '冥王星': 0.6,
  '北交点': 1.8,
  '南交点': -1.8
}

export const PLANET_SCALE = {
  '太阳': 1.0,
  '月亮': 0.85,
  '水星': 0.55,
  '金星': 0.65,
  '火星': 0.55,
  '木星': 0.85,
  '土星': 0.75,
  '天王星': 0.5,
  '海王星': 0.5,
  '冥王星': 0.4,
  '北交点': 0.35,
  '南交点': 0.35
}

export const PLANET_COLORS = {
  '太阳': { color: 0xffc832, emissive: 0xff6600 },
  '月亮': { color: 0xb4c8ff, emissive: 0x4466aa },
  '水星': { color: 0xffdc64, emissive: 0x665500 },
  '金星': { color: 0xff8cb4, emissive: 0x662244 },
  '火星': { color: 0xff5a5a, emissive: 0x662222 },
  '木星': { color: 0xffb464, emissive: 0x664422 },
  '土星': { color: 0xa08cc8, emissive: 0x443366 },
  '天王星': { color: 0x64c8dc, emissive: 0x224466 },
  '海王星': { color: 0x78a0f0, emissive: 0x223366 },
  '冥王星': { color: 0x8a8a9a, emissive: 0x333344 },
  '北交点': { color: 0x50b478, emissive: 0x224433 },
  '南交点': { color: 0xb46464, emissive: 0x442222 }
}

export const ZODIAC_COLORS = [
  0xef4444,
  0x22c55e,
  0xeab308,
  0x3b82f6,
  0xf97316,
  0x22c55e,
  0xec4899,
  0xef4444,
  0xf97316,
  0x6b7280,
  0x06b6d4,
  0x3b82f6
]

export const ASPECT_CONFIG = {
  '合相': { 
    color: 0xfbbf24, 
    baseWidth: 0.15, 
    baseOpacity: 0.35, 
    highlightedOpacity: 0.95,
    maxOrb: 10,
    priority: 1
  },
  '对分相': { 
    color: 0xef4444, 
    baseWidth: 0.12, 
    baseOpacity: 0.3, 
    highlightedOpacity: 0.9,
    maxOrb: 8,
    priority: 2
  },
  '四分相': { 
    color: 0xf97316, 
    baseWidth: 0.12, 
    baseOpacity: 0.3, 
    highlightedOpacity: 0.9,
    maxOrb: 8,
    priority: 2
  },
  '三分相': { 
    color: 0x22c55e, 
    baseWidth: 0.10, 
    baseOpacity: 0.25, 
    highlightedOpacity: 0.85,
    maxOrb: 8,
    priority: 3
  },
  '六分相': { 
    color: 0x3b82f6, 
    baseWidth: 0.08, 
    baseOpacity: 0.2, 
    highlightedOpacity: 0.75,
    maxOrb: 6,
    priority: 4
  }
}

export const ASPECT_PATTERN_CONFIG = {
  '大三角': {
    color: 0x22c55e,
    glowColor: 0x44ff88,
    lineWidth: 0.2,
    opacity: 0.6,
    fillColor: 0x22c55e,
    fillOpacity: 0.15
  },
  '大十字': {
    color: 0xef4444,
    glowColor: 0xff6666,
    lineWidth: 0.2,
    opacity: 0.6,
    fillColor: 0xef4444,
    fillOpacity: 0.12
  },
  'T三角': {
    color: 0xf97316,
    glowColor: 0xffaa44,
    lineWidth: 0.18,
    opacity: 0.55,
    fillColor: 0xf97316,
    fillOpacity: 0.1
  },
  'Yod': {
    color: 0xa855f7,
    glowColor: 0xcc88ff,
    lineWidth: 0.16,
    opacity: 0.5,
    fillColor: 0xa855f7,
    fillOpacity: 0.1
  }
}

export const HOUSE_COLORS = [
  0xff6b6b, 0xff8566, 0xffa066,
  0xffbb66, 0xffd666, 0xfff166,
  0xe6ff66, 0xccff66, 0xb3ff66,
  0x99ff66, 0x80ff66, 0x66ff66
]

export const PLANET_SYMBOLS = {
  '太阳': '☉',
  '月亮': '☽',
  '水星': '☿',
  '金星': '♀',
  '火星': '♂',
  '木星': '♃',
  '土星': '♄',
  '天王星': '♅',
  '海王星': '♆',
  '冥王星': '♇',
  '北交点': '☊',
  '南交点': '☋'
}

export const ASPECT_SYMBOLS = {
  '合相': '☌',
  '六分相': '⚹',
  '四分相': '□',
  '三分相': '△',
  '对分相': '☍'
}

export const ASPECT_NATURES = {
  '合相': 'neutral',
  '三分相': 'harmonious',
  '六分相': 'harmonious',
  '对分相': 'challenging',
  '四分相': 'challenging'
}

export const MAIN_PLANET_NAMES = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']

export function degToRad(deg) {
  return deg * Math.PI / 180
}

export function longitudeTo3DPosition(longitude, radius, yOffset = 0) {
  const angle = longitude * Math.PI / 180
  const x = radius * Math.cos(angle)
  const z = radius * Math.sin(angle)
  const y = yOffset

  return new THREE.Vector3(x, y, z)
}

export function getAspectLineWidth(aspectType, orb) {
  const config = ASPECT_CONFIG[aspectType] || ASPECT_CONFIG['合相']
  const maxOrb = config.maxOrb
  
  if (orb <= 0) {
    return config.baseWidth * 1.5
  }
  
  const orbRatio = Math.max(0, 1 - orb / maxOrb)
  const widthMultiplier = 0.5 + orbRatio * 1.5
  
  return config.baseWidth * widthMultiplier
}

export function getAspectLineOpacity(aspectType, orb, isHighlighted = false) {
  const config = ASPECT_CONFIG[aspectType] || ASPECT_CONFIG['合相']
  
  if (isHighlighted) {
    return config.highlightedOpacity
  }
  
  const maxOrb = config.maxOrb
  
  if (orb <= 0) {
    return config.baseOpacity * 1.3
  }
  
  const orbRatio = Math.max(0, 1 - orb / maxOrb)
  const opacityMultiplier = 0.6 + orbRatio * 0.8
  
  return config.baseOpacity * opacityMultiplier
}

export function disposeResource(resource) {
  if (!resource) return
  
  if (resource.dispose) {
    resource.dispose()
  }
  
  if (resource.geometry) {
    resource.geometry.dispose()
  }
  
  if (resource.material) {
    if (Array.isArray(resource.material)) {
      resource.material.forEach(m => m.dispose())
    } else {
      resource.material.dispose()
    }
  }
  
  if (resource.texture) {
    resource.texture.dispose()
  }
  
  if (resource.map) {
    resource.map.dispose()
  }
}

export function createCanvasTexture(width, height, drawCallback) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  
  if (drawCallback) {
    drawCallback(ctx, canvas)
  }
  
  const texture = new THREE.CanvasTexture(canvas)
  texture.needsUpdate = true
  
  return { canvas, texture }
}

export function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}

export function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(x => {
    const hex = Math.round(Math.max(0, Math.min(255, x))).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('')
}
