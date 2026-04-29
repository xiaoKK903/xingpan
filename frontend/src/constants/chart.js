export const ZODIAC_SIGNS = [
  { name: '白羊座', symbol: '♈', color: 'rgba(239, 68, 68, 0.7)', element: '火' },
  { name: '金牛座', symbol: '♉', color: 'rgba(34, 197, 94, 0.7)', element: '土' },
  { name: '双子座', symbol: '♊', color: 'rgba(234, 179, 8, 0.7)', element: '风' },
  { name: '巨蟹座', symbol: '♋', color: 'rgba(59, 130, 246, 0.7)', element: '水' },
  { name: '狮子座', symbol: '♌', color: 'rgba(249, 115, 22, 0.7)', element: '火' },
  { name: '处女座', symbol: '♍', color: 'rgba(34, 197, 94, 0.7)', element: '土' },
  { name: '天秤座', symbol: '♎', color: 'rgba(236, 72, 153, 0.7)', element: '风' },
  { name: '天蝎座', symbol: '♏', color: 'rgba(239, 68, 68, 0.7)', element: '水' },
  { name: '射手座', symbol: '♐', color: 'rgba(249, 115, 22, 0.7)', element: '火' },
  { name: '摩羯座', symbol: '♑', color: 'rgba(107, 114, 128, 0.7)', element: '土' },
  { name: '水瓶座', symbol: '♒', color: 'rgba(6, 182, 212, 0.7)', element: '风' },
  { name: '双鱼座', symbol: '♓', color: 'rgba(59, 130, 246, 0.7)', element: '水' }
]

export const PLANET_CATEGORIES = {
  LUMINARIES: ['太阳', '月亮'],
  PERSONAL: ['水星', '金星', '火星'],
  SOCIAL: ['木星', '土星'],
  TRANS_PERSONAL: ['天王星', '海王星', '冥王星']
}

export const PLANET_INFO = {
  '太阳': { 
    symbol: '☉', 
    color: '#ffc832',
    size: 22, 
    symbolSize: 20, 
    priority: 10,
    category: 'luminary',
    isMajor: true
  },
  '月亮': { 
    symbol: '☽', 
    color: '#b4c8ff',
    size: 20, 
    symbolSize: 18, 
    priority: 9,
    category: 'luminary',
    isMajor: true
  },
  '水星': { 
    symbol: '☿', 
    color: '#ffdc64',
    size: 17, 
    symbolSize: 15, 
    priority: 7,
    category: 'personal',
    isMajor: true
  },
  '金星': { 
    symbol: '♀', 
    color: '#ff8cb4',
    size: 18, 
    symbolSize: 16, 
    priority: 8,
    category: 'personal',
    isMajor: true
  },
  '火星': { 
    symbol: '♂', 
    color: '#ff5a5a',
    size: 17, 
    symbolSize: 15, 
    priority: 6,
    category: 'personal',
    isMajor: true
  },
  '木星': { 
    symbol: '♃', 
    color: '#ffb464',
    size: 19, 
    symbolSize: 17, 
    priority: 5,
    category: 'social',
    isMajor: true
  },
  '土星': { 
    symbol: '♄', 
    color: '#a08cc8',
    size: 18, 
    symbolSize: 16, 
    priority: 4,
    category: 'social',
    isMajor: true
  },
  '天王星': { 
    symbol: '♅', 
    color: '#64c8dc',
    size: 15, 
    symbolSize: 13, 
    priority: 3,
    category: 'transpersonal',
    isMajor: true
  },
  '海王星': { 
    symbol: '♆', 
    color: '#78a0f0',
    size: 15, 
    symbolSize: 13, 
    priority: 2,
    category: 'transpersonal',
    isMajor: true
  },
  '冥王星': { 
    symbol: '♇', 
    color: '#8a8a9a',
    size: 14, 
    symbolSize: 12, 
    priority: 1,
    category: 'transpersonal',
    isMajor: true
  },
  '北交点': { 
    symbol: '☊', 
    color: '#50b478',
    size: 12, 
    symbolSize: 10, 
    priority: 0,
    category: 'node',
    isMajor: false
  },
  '南交点': { 
    symbol: '☋', 
    color: '#b46464',
    size: 12, 
    symbolSize: 10, 
    priority: 0,
    category: 'node',
    isMajor: false
  }
}

export const MAJOR_PLANET_NAMES = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']

export const ASPECT_TYPES = {
  '合相': { 
    symbol: '☌', 
    color: '#fbbf24', 
    width: 2.5, 
    dash: 'none', 
    baseOpacity: 0.9, 
    nature: 'neutral',
    importance: 10,
    label: '合相',
    angle: 0
  },
  '三分相': { 
    symbol: '△', 
    color: '#22c55e', 
    width: 2.2, 
    dash: 'none', 
    baseOpacity: 0.75, 
    nature: 'harmonious',
    importance: 9,
    label: '拱',
    angle: 120
  },
  '六分相': { 
    symbol: '⚹', 
    color: '#3b82f6', 
    width: 1.8, 
    dash: '8,6', 
    baseOpacity: 0.65, 
    nature: 'harmonious',
    importance: 8,
    label: '六合',
    angle: 60
  },
  '对分相': { 
    symbol: '☍', 
    color: '#ef4444', 
    width: 2.2, 
    dash: '12,6', 
    baseOpacity: 0.8, 
    nature: 'challenging',
    importance: 9,
    label: '冲',
    angle: 180
  },
  '四分相': { 
    symbol: '□', 
    color: '#f97316', 
    width: 2.2, 
    dash: '6,6', 
    baseOpacity: 0.8, 
    nature: 'challenging',
    importance: 9,
    label: '刑',
    angle: 90
  }
}

export const KEY_ASPECT_PLANETS = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星']

export const MAIN_PLANET_NAMES = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']

export const CITIES_DB = [
  { id: 'beijing', name: '北京', country: '中国', latitude: 39.9042, longitude: 116.4074 },
  { id: 'shanghai', name: '上海', country: '中国', latitude: 31.2304, longitude: 121.4737 },
  { id: 'guangzhou', name: '广州', country: '中国', latitude: 23.1291, longitude: 113.2644 },
  { id: 'shenzhen', name: '深圳', country: '中国', latitude: 22.5431, longitude: 114.0579 },
  { id: 'chengdu', name: '成都', country: '中国', latitude: 30.5728, longitude: 104.0668 },
  { id: 'hangzhou', name: '杭州', country: '中国', latitude: 30.2741, longitude: 120.1551 },
  { id: 'nanjing', name: '南京', country: '中国', latitude: 32.0603, longitude: 118.7969 },
  { id: 'wuhan', name: '武汉', country: '中国', latitude: 30.5928, longitude: 114.3055 },
  { id: 'xian', name: '西安', country: '中国', latitude: 34.3416, longitude: 108.9398 },
  { id: 'chongqing', name: '重庆', country: '中国', latitude: 29.4316, longitude: 106.9123 },
  { id: 'tianjin', name: '天津', country: '中国', latitude: 39.0842, longitude: 117.2009 },
  { id: 'suzhou', name: '苏州', country: '中国', latitude: 31.2989, longitude: 120.5853 },
  { id: 'hongkong', name: '香港', country: '中国', latitude: 22.3193, longitude: 114.1694 },
  { id: 'taipei', name: '台北', country: '中国', latitude: 25.0330, longitude: 121.5654 },
  { id: 'tokyo', name: '东京', country: '日本', latitude: 35.6762, longitude: 139.6503 },
  { id: 'seoul', name: '首尔', country: '韩国', latitude: 37.5665, longitude: 126.9780 },
  { id: 'newyork', name: '纽约', country: '美国', latitude: 40.7128, longitude: -74.0060 },
  { id: 'losangeles', name: '洛杉矶', country: '美国', latitude: 34.0522, longitude: -118.2437 },
  { id: 'london', name: '伦敦', country: '英国', latitude: 51.5074, longitude: -0.1278 },
  { id: 'paris', name: '巴黎', country: '法国', latitude: 48.8566, longitude: 2.3522 },
]

export const QUICK_CITIES = [
  { id: 'beijing', name: '北京' },
  { id: 'shanghai', name: '上海' },
  { id: 'guangzhou', name: '广州' },
  { id: 'shenzhen', name: '深圳' },
  { id: 'chengdu', name: '成都' },
  { id: 'hangzhou', name: '杭州' },
]

export function getPlanetInfo(name) {
  return PLANET_INFO[name] || { 
    symbol: '★', 
    bg: 'rgba(139, 92, 246, 0.9)', 
    border: '#8b5cf6', 
    text: '#fff', 
    size: 7, 
    symbolSize: 8 
  }
}

export function getAspectInfo(name) {
  return ASPECT_TYPES[name] || { 
    symbol: '○', 
    color: 'rgba(234, 179, 8, 0.5)', 
    width: 1, 
    dash: 'none', 
    baseOpacity: 0.2 
  }
}

export function getAspectOpacity(aspect) {
  const info = getAspectInfo(aspect.aspect)
  const orb = aspect.orb || 0
  const maxOrb = 8
  const normalizedOrb = Math.min(orb / maxOrb, 1)
  const orbFactor = Math.pow(1 - normalizedOrb, 0.4)
  return Math.max(0.15, info.baseOpacity * orbFactor)
}

export function getNatureLabel(nature) {
  const labels = {
    harmonious: '和谐',
    challenging: '紧张',
    neutral: '中性'
  }
  return labels[nature] || nature
}

export function degToRad(deg) {
  return deg * Math.PI / 180
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

export function isAscendant(cusps, ascendantLongitude, index) {
  if (cusps.length === 0 || ascendantLongitude == null) return false
  return Math.abs(cusps[index] - ascendantLongitude) < 0.1
}
