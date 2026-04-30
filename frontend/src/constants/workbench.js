export const CHART_WHEEL_CONSTANTS = {
  VIEWBOX_SIZE: 600,
  
  RADIUS_CONFIG: {
    OUTER_MARGIN: 10,
    ZODIAC_OUTER: 25,
    ZODIAC_MID: 50,
    ZODIAC_INNER: 78,
    HOUSE_OUTER: 88,
    HOUSE_MID: 112,
    HOUSE_INNER: 155,
    PLANET: 132,
    ASPECT_LINE: 175,
    CENTER: 195
  },
  
  PLANET_SIZES: {
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
  },
  
  PLANET_SYMBOL_SIZES: {
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
  },
  
  PLANET_MAP: {
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
  },
  
  MAJOR_PLANET_NAMES: ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星'],
  TRADITIONAL_PLANETS: ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星'],
  
  ZODIAC_SIGNS: [
    { name: '白羊座', symbol: '♈', color: 'rgba(239, 68, 68, 0.7)', element: 'fire', quality: 'cardinal' },
    { name: '金牛座', symbol: '♉', color: 'rgba(34, 197, 94, 0.7)', element: 'earth', quality: 'fixed' },
    { name: '双子座', symbol: '♊', color: 'rgba(234, 179, 8, 0.7)', element: 'air', quality: 'mutable' },
    { name: '巨蟹座', symbol: '♋', color: 'rgba(59, 130, 246, 0.7)', element: 'water', quality: 'cardinal' },
    { name: '狮子座', symbol: '♌', color: 'rgba(249, 115, 22, 0.7)', element: 'fire', quality: 'fixed' },
    { name: '处女座', symbol: '♍', color: 'rgba(34, 197, 94, 0.7)', element: 'earth', quality: 'mutable' },
    { name: '天秤座', symbol: '♎', color: 'rgba(236, 72, 153, 0.7)', element: 'air', quality: 'cardinal' },
    { name: '天蝎座', symbol: '♏', color: 'rgba(239, 68, 68, 0.7)', element: 'water', quality: 'fixed' },
    { name: '射手座', symbol: '♐', color: 'rgba(249, 115, 22, 0.7)', element: 'fire', quality: 'mutable' },
    { name: '摩羯座', symbol: '♑', color: 'rgba(107, 114, 128, 0.7)', element: 'earth', quality: 'cardinal' },
    { name: '水瓶座', symbol: '♒', color: 'rgba(6, 182, 212, 0.7)', element: 'air', quality: 'fixed' },
    { name: '双鱼座', symbol: '♓', color: 'rgba(59, 130, 246, 0.7)', element: 'water', quality: 'mutable' }
  ],
  
  ELEMENTS: {
    fire: { name: '火', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
    earth: { name: '土', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
    air: { name: '风', color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)' },
    water: { name: '水', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' }
  },
  
  ASCENDANT_THRESHOLD: 0.1,
  MAX_ASPECT_ORB: 8,
  DEBOUNCE_DELAY: 150,
  CACHE_TTL: 5000
}

export const ASPECT_CONFIG = {
  '合相': { 
    angle: 0, 
    color: '#fbbf24', 
    width: 2.5, 
    dash: 'none', 
    baseOpacity: 0.85,
    nature: 'neutral',
    label: '合',
    symbol: '☌',
    importance: 10
  },
  '对分相': { 
    angle: 180, 
    color: '#ef4444', 
    width: 2, 
    dash: '12,6', 
    baseOpacity: 0.75,
    nature: 'challenging',
    label: '冲',
    symbol: '☍',
    importance: 9
  },
  '四分相': { 
    angle: 90, 
    color: '#f97316', 
    width: 2, 
    dash: '6,6', 
    baseOpacity: 0.7,
    nature: 'challenging',
    label: '刑',
    symbol: '□',
    importance: 9
  },
  '三分相': { 
    angle: 120, 
    color: '#22c55e', 
    width: 2, 
    dash: 'none', 
    baseOpacity: 0.7,
    nature: 'harmonious',
    label: '拱',
    symbol: '△',
    importance: 9
  },
  '六分相': { 
    angle: 60, 
    color: '#3b82f6', 
    width: 1.5, 
    dash: '8,6', 
    baseOpacity: 0.55,
    nature: 'harmonious',
    label: '六合',
    symbol: '⚹',
    importance: 8
  }
}

export const ASPECT_NATURE = {
  harmonious: { 
    label: '和谐', 
    color: '#22c55e', 
    bg: 'rgba(34, 197, 94, 0.15)',
    borderColor: 'rgba(34, 197, 94, 0.3)'
  },
  challenging: { 
    label: '紧张', 
    color: '#ef4444', 
    bg: 'rgba(239, 68, 68, 0.15)',
    borderColor: 'rgba(239, 68, 68, 0.3)'
  },
  neutral: { 
    label: '中性', 
    color: '#eab308', 
    bg: 'rgba(234, 179, 8, 0.15)',
    borderColor: 'rgba(234, 179, 8, 0.3)'
  }
}

export const MAJOR_ASPECT_NAMES = ['合相', '对分相', '四分相', '三分相', '六分相']

export const DIGNITY_CONFIG = {
  RULER: { name: '守护星', score: 5, color: '#22c55e' },
  EXALTATION: { name: '旺势', score: 4, color: '#22c55e' },
  TRIPLICITY: { name: '三分性', score: 3, color: '#22c55e' },
  TERM: { name: '界', score: 2, color: '#22c55e' },
  FACE: { name: '面', score: 1, color: '#22c55e' },
  DETRIMENT: { name: '落陷', score: -5, color: '#ef4444' },
  FALL: { name: '弱势', score: -4, color: '#ef4444' }
}

export const ESSENTIAL_DIGNITIES = {
  RULING_PLANETS: {
    0: '火星',
    1: '金星',
    2: '水星',
    3: '月亮',
    4: '太阳',
    5: '水星',
    6: '金星',
    7: '火星',
    8: '木星',
    9: '土星',
    10: '土星',
    11: '木星'
  },
  
  EXALTATION_PLANETS: {
    0: '太阳',
    1: '月亮',
    2: '水星',
    3: '木星',
    4: '无',
    5: '水星',
    6: '土星',
    7: '无',
    8: '无',
    9: '火星',
    10: '无',
    11: '金星'
  },
  
  DETRIMENT_PLANETS: {
    0: '金星',
    1: '火星',
    2: '木星',
    3: '土星',
    4: '土星',
    5: '木星',
    6: '火星',
    7: '金星',
    8: '水星',
    9: '月亮',
    10: '太阳',
    11: '水星'
  },
  
  FALL_PLANETS: {
    0: '土星',
    1: '冥王星',
    2: '木星',
    3: '火星',
    4: '金星',
    5: '木星',
    6: '太阳',
    7: '月亮',
    8: '水星',
    9: '木星',
    10: '火星',
    11: '水星'
  }
}

export const ANTISCIA_SIGNS = {
  0: 5,
  1: 4,
  2: 3,
  3: 2,
  4: 1,
  5: 0,
  6: 11,
  7: 10,
  8: 9,
  9: 8,
  10: 7,
  11: 6
}

export const CONTRAANTISCIA_SIGNS = {
  0: 11,
  1: 10,
  2: 9,
  3: 8,
  4: 7,
  5: 6,
  6: 5,
  7: 4,
  8: 3,
  9: 2,
  10: 1,
  11: 0
}

const calculationCache = new Map()

export function degToRad(deg) {
  return deg * Math.PI / 180
}

export function normalizeAngle(angle) {
  return (angle % 360 + 360) % 360
}

export function getAngleDifference(a1, a2) {
  let diff = Math.abs(a1 - a2)
  if (diff > 180) diff = 360 - diff
  return diff
}

export function getSignIndex(longitude) {
  return Math.floor(normalizeAngle(longitude) / 30)
}

export function getDegreeInSign(longitude) {
  return normalizeAngle(longitude) % 30
}

export function getSignInfo(longitude) {
  const signIndex = getSignIndex(longitude)
  const degreeInSign = getDegreeInSign(longitude)
  const sign = CHART_WHEEL_CONSTANTS.ZODIAC_SIGNS[signIndex]
  
  return {
    signIndex,
    degreeInSign,
    signName: sign.name,
    signSymbol: sign.symbol,
    element: sign.element,
    quality: sign.quality
  }
}

export function isAscendant(cusps, ascendantLongitude, index, threshold = CHART_WHEEL_CONSTANTS.ASCENDANT_THRESHOLD) {
  if (cusps.length === 0 || ascendantLongitude == null) return false
  return Math.abs(cusps[index] - ascendantLongitude) < threshold
}

export function getHouseMidAngle(cusps, index) {
  if (cusps.length === 0) return index * 30
  const currentCusp = cusps[index]
  const nextCusp = cusps[(index + 1) % 12]
  let mid = (currentCusp + nextCusp) / 2
  if (Math.abs(nextCusp - currentCusp) > 180) {
    mid = (currentCusp + nextCusp + 360) / 2
  }
  return mid % 360
}

export function calculateLocalAspect(planet1, planet2, longitude1, longitude2) {
  const diff = getAngleDifference(longitude1, longitude2)
  
  for (const [aspectName, config] of Object.entries(ASPECT_CONFIG)) {
    const targetAngle = config.angle
    const maxOrb = aspectName === '六分相' ? 6 : 8
    
    if (targetAngle === 0) {
      if (diff <= maxOrb) {
        return {
          planet1: planet1,
          planet2: planet2,
          aspect: aspectName,
          aspect_symbol: config.symbol,
          orb: diff,
          nature: config.nature,
          applying: null,
          angle: targetAngle,
          actual_angle: diff
        }
      }
    } else {
      const orb = Math.abs(diff - targetAngle)
      if (orb <= maxOrb) {
        return {
          planet1: planet1,
          planet2: planet2,
          aspect: aspectName,
          aspect_symbol: config.symbol,
          orb: orb,
          nature: config.nature,
          applying: null,
          angle: targetAngle,
          actual_angle: diff
        }
      }
    }
  }
  return null
}

export function calculateAllAspects(planets, includeMinor = false) {
  const aspects = []
  const majorNames = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']
  const filteredPlanets = planets.filter(p => majorNames.includes(p.name))
  
  for (let i = 0; i < filteredPlanets.length; i++) {
    for (let j = i + 1; j < filteredPlanets.length; j++) {
      const p1 = filteredPlanets[i]
      const p2 = filteredPlanets[j]
      
      const aspect = calculateLocalAspect(
        p1.name,
        p2.name,
        p1.longitude,
        p2.longitude
      )
      
      if (aspect) {
        const influence = (1 - aspect.orb / (aspect.aspect === '六分相' ? 6 : 8)) * (ASPECT_CONFIG[aspect.aspect]?.importance || 5) / 10
        aspects.push({
          ...aspect,
          influence: Math.round(influence * 100) / 100,
          planet1_symbol: p1.symbol || '',
          planet2_symbol: p2.symbol || ''
        })
      }
    }
  }
  
  aspects.sort((a, b) => (b.influence || 0) - (a.influence || 0))
  return aspects
}

export function calculateEssentialDignities(planetName, longitude, useTraditional = true) {
  const signIndex = getSignIndex(longitude)
  const degreeInSign = getDegreeInSign(longitude)
  
  const ruler = ESSENTIAL_DIGNITIES.RULING_PLANETS[signIndex]
  const exaltation = ESSENTIAL_DIGNITIES.EXALTATION_PLANETS[signIndex]
  const detriment = ESSENTIAL_DIGNITIES.DETRIMENT_PLANETS[signIndex]
  const fall = ESSENTIAL_DIGNITIES.FALL_PLANETS[signIndex]
  
  const isInRuler = planetName === ruler
  const isInExaltation = planetName === exaltation
  const isInDetriment = planetName === detriment
  const isInFall = planetName === fall
  
  let dignityScore = 0
  let debilityScore = 0
  
  if (isInRuler) dignityScore += 5
  if (isInExaltation) dignityScore += 4
  if (isInDetriment) debilityScore += 5
  if (isInFall) debilityScore += 4
  
  const netScore = dignityScore - debilityScore
  let essentialDignity = 'neutral'
  
  if (netScore >= 5) essentialDignity = 'exalted'
  else if (netScore >= 3) essentialDignity = 'strong'
  else if (netScore >= 1) essentialDignity = 'moderate'
  else if (netScore >= -2) essentialDignity = 'neutral'
  else if (netScore >= -4) essentialDignity = 'weak'
  else essentialDignity = 'debilitated'
  
  return {
    ruler,
    exaltation,
    detriment,
    fall,
    is_in_ruler: isInRuler,
    is_in_exaltation: isInExaltation,
    is_in_detriment: isInDetriment,
    is_in_fall: isInFall,
    dignity_score: dignityScore,
    debility_score: debilityScore,
    essential_dignity: essentialDignity
  }
}

export function calculateAntiscia(longitude) {
  const signIndex = getSignIndex(longitude)
  const degreeInSign = getDegreeInSign(longitude)
  
  const antisciaSign = ANTISCIA_SIGNS[signIndex]
  const antisciaDegree = 30 - degreeInSign
  const antisciaLongitude = antisciaSign * 30 + antisciaDegree
  
  const contraSign = CONTRAANTISCIA_SIGNS[signIndex]
  const contraDegree = 30 - degreeInSign
  const contraLongitude = contraSign * 30 + contraDegree
  
  return {
    antiscia: {
      longitude: antisciaLongitude,
      sign_index: antisciaSign,
      sign: CHART_WHEEL_CONSTANTS.ZODIAC_SIGNS[antisciaSign]?.name,
      sign_symbol: CHART_WHEEL_CONSTANTS.ZODIAC_SIGNS[antisciaSign]?.symbol,
      degree_in_sign: antisciaDegree
    },
    contra_antiscia: {
      longitude: contraLongitude,
      sign_index: contraSign,
      sign: CHART_WHEEL_CONSTANTS.ZODIAC_SIGNS[contraSign]?.name,
      sign_symbol: CHART_WHEEL_CONSTANTS.ZODIAC_SIGNS[contraSign]?.symbol,
      degree_in_sign: contraDegree
    }
  }
}

export function checkReception(planetA, planetB, longitudeA, longitudeB) {
  const signA = getSignIndex(longitudeA)
  const signB = getSignIndex(longitudeB)
  
  const rulerA = ESSENTIAL_DIGNITIES.RULING_PLANETS[signA]
  const rulerB = ESSENTIAL_DIGNITIES.RULING_PLANETS[signB]
  const exaltationA = ESSENTIAL_DIGNITIES.EXALTATION_PLANETS[signA]
  const exaltationB = ESSENTIAL_DIGNITIES.EXALTATION_PLANETS[signB]
  
  const aReceivesBByRuler = planetB === rulerA
  const bReceivesAByRuler = planetA === rulerB
  const aReceivesBByExaltation = planetB === exaltationA && exaltationA !== '无'
  const bReceivesAByExaltation = planetA === exaltationB && exaltationB !== '无'
  
  const receptions = []
  
  if (aReceivesBByRuler) {
    const isMutual = bReceivesAByRuler
    receptions.push({
      planet_a: planetB,
      planet_b: planetA,
      reception_type: isMutual ? 'mutual_ruler' : 'single_ruler',
      dignity_type: 'ruler',
      is_mutual: isMutual,
      description: isMutual 
        ? `${planetB}与${planetA}形成守护星互容，双方通过守护星关系彼此接纳。`
        : `${planetB}被${planetA}通过守护星关系接纳。`,
      strength: isMutual ? 1.0 : 0.5
    })
  }
  
  if (aReceivesBByExaltation && !aReceivesBByRuler) {
    const isMutual = bReceivesAByExaltation
    receptions.push({
      planet_a: planetB,
      planet_b: planetA,
      reception_type: isMutual ? 'mutual_exaltation' : 'single_exaltation',
      dignity_type: 'exaltation',
      is_mutual: isMutual,
      description: isMutual
        ? `${planetB}与${planetA}形成旺势互容，双方通过旺势关系彼此接纳。`
        : `${planetB}被${planetA}通过旺势关系接纳。`,
      strength: isMutual ? 0.8 : 0.4
    })
  }
  
  if ((aReceivesBByRuler && bReceivesAByExaltation) || 
      (aReceivesBByExaltation && bReceivesAByRuler)) {
    receptions.push({
      planet_a: planetA,
      planet_b: planetB,
      reception_type: 'mixed_mutual',
      dignity_type: 'mixed',
      is_mutual: true,
      description: `${planetA}与${planetB}形成混合互容，一方通过守护星接纳另一方，另一方通过旺势接纳。`,
      strength: 0.9
    })
  }
  
  return receptions
}

export function calculateAllReceptions(planets) {
  const receptions = []
  const traditionalPlanets = planets.filter(p => 
    CHART_WHEEL_CONSTANTS.TRADITIONAL_PLANETS.includes(p.name)
  )
  
  for (let i = 0; i < traditionalPlanets.length; i++) {
    for (let j = i + 1; j < traditionalPlanets.length; j++) {
      const p1 = traditionalPlanets[i]
      const p2 = traditionalPlanets[j]
      
      const results = checkReception(
        p1.name,
        p2.name,
        p1.longitude,
        p2.longitude
      )
      
      receptions.push(...results)
    }
  }
  
  return receptions
}

export function getAspectColor(aspectName) {
  return ASPECT_CONFIG[aspectName]?.color || '#9370db'
}

export function getAspectWidth(aspectName) {
  return ASPECT_CONFIG[aspectName]?.width || 1
}

export function getAspectDash(aspectName) {
  return ASPECT_CONFIG[aspectName]?.dash || 'none'
}

export function getAspectSymbol(aspectName) {
  return ASPECT_CONFIG[aspectName]?.symbol || '○'
}

export function getNatureInfo(nature) {
  return ASPECT_NATURE[nature] || ASPECT_NATURE.neutral
}

export function getPlanetSymbol(name) {
  return CHART_WHEEL_CONSTANTS.PLANET_MAP[name]?.symbol || '★'
}

export function getPlanetInfo(name) {
  return CHART_WHEEL_CONSTANTS.PLANET_MAP[name] || { 
    symbol: '★', 
    bg: 'rgba(139, 92, 246, 0.9)', 
    border: '#8b5cf6', 
    text: '#fff' 
  }
}

export class CalculationCache {
  constructor(ttl = CHART_WHEEL_CONSTANTS.CACHE_TTL) {
    this.cache = new Map()
    this.ttl = ttl
  }
  
  _generateKey(...args) {
    return JSON.stringify(args)
  }
  
  get(key) {
    const entry = this.cache.get(key)
    if (!entry) return null
    
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key)
      return null
    }
    
    return entry.value
  }
  
  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    })
  }
  
  clear() {
    this.cache.clear()
  }
  
  getOrCalculate(key, calculator) {
    const cached = this.get(key)
    if (cached !== null) {
      return cached
    }
    
    const result = calculator()
    this.set(key, result)
    return result
  }
}

export const aspectCache = new CalculationCache()
export const dignityCache = new CalculationCache()

export function debounce(fn, delay) {
  let timeoutId = null
  return function(...args) {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    timeoutId = setTimeout(() => {
      fn.apply(this, args)
      timeoutId = null
    }, delay)
  }
}

export function throttle(fn, limit) {
  let lastCall = 0
  return function(...args) {
    const now = Date.now()
    if (now - lastCall >= limit) {
      lastCall = now
      fn.apply(this, args)
    }
  }
}
