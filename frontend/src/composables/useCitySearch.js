import { ref, reactive, computed } from 'vue'
import { geoApi } from '@/api'

export const CITIES_DB = [
  { id: 'beijing', name: '北京', nameEn: 'Beijing', country: '中国', state: '北京市', latitude: 39.9042, longitude: 116.4074 },
  { id: 'shanghai', name: '上海', nameEn: 'Shanghai', country: '中国', state: '上海市', latitude: 31.2304, longitude: 121.4737 },
  { id: 'guangzhou', name: '广州', nameEn: 'Guangzhou', country: '中国', state: '广东省', latitude: 23.1291, longitude: 113.2644 },
  { id: 'shenzhen', name: '深圳', nameEn: 'Shenzhen', country: '中国', state: '广东省', latitude: 22.5431, longitude: 114.0579 },
  { id: 'chengdu', name: '成都', nameEn: 'Chengdu', country: '中国', state: '四川省', latitude: 30.5728, longitude: 104.0668 },
  { id: 'hangzhou', name: '杭州', nameEn: 'Hangzhou', country: '中国', state: '浙江省', latitude: 30.2741, longitude: 120.1551 },
  { id: 'nanjing', name: '南京', nameEn: 'Nanjing', country: '中国', state: '江苏省', latitude: 32.0603, longitude: 118.7969 },
  { id: 'wuhan', name: '武汉', nameEn: 'Wuhan', country: '中国', state: '湖北省', latitude: 30.5928, longitude: 114.3055 },
  { id: 'xian', name: '西安', nameEn: "Xi'an", country: '中国', state: '陕西省', latitude: 34.3416, longitude: 108.9398 },
  { id: 'chongqing', name: '重庆', nameEn: 'Chongqing', country: '中国', state: '重庆市', latitude: 29.4316, longitude: 106.9123 },
  { id: 'tianjin', name: '天津', nameEn: 'Tianjin', country: '中国', state: '天津市', latitude: 39.0842, longitude: 117.2009 },
  { id: 'suzhou', name: '苏州', nameEn: 'Suzhou', country: '中国', state: '江苏省', latitude: 31.2989, longitude: 120.5853 },
  { id: 'changsha', name: '长沙', nameEn: 'Changsha', country: '中国', state: '湖南省', latitude: 28.2282, longitude: 112.9388 },
  { id: 'zhengzhou', name: '郑州', nameEn: 'Zhengzhou', country: '中国', state: '河南省', latitude: 34.7466, longitude: 113.6254 },
  { id: 'qingdao', name: '青岛', nameEn: 'Qingdao', country: '中国', state: '山东省', latitude: 36.0671, longitude: 120.3826 },
  { id: 'dalian', name: '大连', nameEn: 'Dalian', country: '中国', state: '辽宁省', latitude: 38.9140, longitude: 121.6147 },
  { id: 'shenyang', name: '沈阳', nameEn: 'Shenyang', country: '中国', state: '辽宁省', latitude: 41.8057, longitude: 123.4315 },
  { id: 'harbin', name: '哈尔滨', nameEn: 'Harbin', country: '中国', state: '黑龙江省', latitude: 45.8038, longitude: 126.5350 },
  { id: 'hongkong', name: '香港', nameEn: 'Hong Kong', country: '中国', state: '香港特别行政区', latitude: 22.3193, longitude: 114.1694 },
  { id: 'taipei', name: '台北', nameEn: 'Taipei', country: '中国', state: '台湾省', latitude: 25.0330, longitude: 121.5654 },
  { id: 'tokyo', name: '东京', nameEn: 'Tokyo', country: '日本', state: '东京都', latitude: 35.6762, longitude: 139.6503 },
  { id: 'seoul', name: '首尔', nameEn: 'Seoul', country: '韩国', state: '首尔特别市', latitude: 37.5665, longitude: 126.9780 },
  { id: 'singapore', name: '新加坡', nameEn: 'Singapore', country: '新加坡', state: '', latitude: 1.3521, longitude: 103.8198 },
  { id: 'bangkok', name: '曼谷', nameEn: 'Bangkok', country: '泰国', state: '曼谷', latitude: 13.7563, longitude: 100.5018 },
  { id: 'newdelhi', name: '新德里', nameEn: 'New Delhi', country: '印度', state: '德里', latitude: 28.6139, longitude: 77.2090 },
  { id: 'newyork', name: '纽约', nameEn: 'New York', country: '美国', state: '纽约州', latitude: 40.7128, longitude: -74.0060 },
  { id: 'losangeles', name: '洛杉矶', nameEn: 'Los Angeles', country: '美国', state: '加利福尼亚州', latitude: 34.0522, longitude: -118.2437 },
  { id: 'chicago', name: '芝加哥', nameEn: 'Chicago', country: '美国', state: '伊利诺伊州', latitude: 41.8781, longitude: -87.6298 },
  { id: 'washington', name: '华盛顿', nameEn: 'Washington', country: '美国', state: '华盛顿哥伦比亚特区', latitude: 38.9072, longitude: -77.0369 },
  { id: 'sanfrancisco', name: '旧金山', nameEn: 'San Francisco', country: '美国', state: '加利福尼亚州', latitude: 37.7749, longitude: -122.4194 },
  { id: 'boston', name: '波士顿', nameEn: 'Boston', country: '美国', state: '马萨诸塞州', latitude: 42.3601, longitude: -71.0589 },
  { id: 'miami', name: '迈阿密', nameEn: 'Miami', country: '美国', state: '佛罗里达州', latitude: 25.7617, longitude: -80.1918 },
  { id: 'houston', name: '休斯顿', nameEn: 'Houston', country: '美国', state: '德克萨斯州', latitude: 29.7604, longitude: -95.3698 },
  { id: 'london', name: '伦敦', nameEn: 'London', country: '英国', state: '英格兰', latitude: 51.5074, longitude: -0.1278 },
  { id: 'paris', name: '巴黎', nameEn: 'Paris', country: '法国', state: '法兰西岛', latitude: 48.8566, longitude: 2.3522 },
  { id: 'berlin', name: '柏林', nameEn: 'Berlin', country: '德国', state: '柏林', latitude: 52.5200, longitude: 13.4050 },
  { id: 'rome', name: '罗马', nameEn: 'Rome', country: '意大利', state: '拉齐奥', latitude: 41.9028, longitude: 12.4964 },
  { id: 'madrid', name: '马德里', nameEn: 'Madrid', country: '西班牙', state: '马德里自治区', latitude: 40.4168, longitude: -3.7038 },
  { id: 'amsterdam', name: '阿姆斯特丹', nameEn: 'Amsterdam', country: '荷兰', state: '北荷兰省', latitude: 52.3676, longitude: 4.9041 },
  { id: 'moscow', name: '莫斯科', nameEn: 'Moscow', country: '俄罗斯', state: '莫斯科', latitude: 55.7558, longitude: 37.6173 },
  { id: 'vienna', name: '维也纳', nameEn: 'Vienna', country: '奥地利', state: '维也纳', latitude: 48.2082, longitude: 16.3738 },
  { id: 'prague', name: '布拉格', nameEn: 'Prague', country: '捷克', state: '布拉格', latitude: 50.0755, longitude: 14.4378 },
  { id: 'istanbul', name: '伊斯坦布尔', nameEn: 'Istanbul', country: '土耳其', state: '伊斯坦布尔', latitude: 41.0082, longitude: 28.9784 },
  { id: 'sydney', name: '悉尼', nameEn: 'Sydney', country: '澳大利亚', state: '新南威尔士州', latitude: -33.8688, longitude: 151.2093 },
  { id: 'melbourne', name: '墨尔本', nameEn: 'Melbourne', country: '澳大利亚', state: '维多利亚州', latitude: -37.8136, longitude: 144.9631 },
  { id: 'auckland', name: '奥克兰', nameEn: 'Auckland', country: '新西兰', state: '奥克兰大区', latitude: -36.8485, longitude: 174.7633 },
  { id: 'perth', name: '珀斯', nameEn: 'Perth', country: '澳大利亚', state: '西澳大利亚州', latitude: -31.9505, longitude: 115.8605 },
  { id: 'dubai', name: '迪拜', nameEn: 'Dubai', country: '阿联酋', state: '迪拜', latitude: 25.2048, longitude: 55.2708 },
  { id: 'cairo', name: '开罗', nameEn: 'Cairo', country: '埃及', state: '开罗省', latitude: 30.0444, longitude: 31.2357 },
  { id: 'johannesburg', name: '约翰内斯堡', nameEn: 'Johannesburg', country: '南非', state: '豪登省', latitude: -26.2041, longitude: 28.0473 },
  { id: 'mumbai', name: '孟买', nameEn: 'Mumbai', country: '印度', state: '马哈拉施特拉邦', latitude: 19.0760, longitude: 72.8777 },
  { id: 'jakarta', name: '雅加达', nameEn: 'Jakarta', country: '印度尼西亚', state: '雅加达', latitude: -6.2088, longitude: 106.8456 },
  { id: 'manila', name: '马尼拉', nameEn: 'Manila', country: '菲律宾', state: '马尼拉', latitude: 14.5995, longitude: 120.9842 },
  { id: 'hanoi', name: '河内', nameEn: 'Hanoi', country: '越南', state: '河内', latitude: 21.0278, longitude: 105.8342 },
  { id: 'kualalumpur', name: '吉隆坡', nameEn: 'Kuala Lumpur', country: '马来西亚', state: '吉隆坡', latitude: 3.1390, longitude: 101.6869 },
  { id: 'riodejaneiro', name: '里约热内卢', nameEn: 'Rio de Janeiro', country: '巴西', state: '里约热内卢州', latitude: -22.9068, longitude: -43.1729 },
  { id: 'saopaulo', name: '圣保罗', nameEn: 'Sao Paulo', country: '巴西', state: '圣保罗州', latitude: -23.5505, longitude: -46.6333 },
  { id: 'mexicocity', name: '墨西哥城', nameEn: 'Mexico City', country: '墨西哥', state: '墨西哥城', latitude: 19.4326, longitude: -99.1332 },
  { id: 'buenosaires', name: '布宜诺斯艾利斯', nameEn: 'Buenos Aires', country: '阿根廷', state: '布宜诺斯艾利斯', latitude: -34.6037, longitude: -58.3816 },
  { id: 'santiago', name: '圣地亚哥', nameEn: 'Santiago', country: '智利', state: '圣地亚哥首都大区', latitude: -33.4489, longitude: -70.6693 },
  { id: 'bogota', name: '波哥大', nameEn: 'Bogota', country: '哥伦比亚', state: '波哥大', latitude: 4.7110, longitude: -74.0721 },
  { id: 'lima', name: '利马', nameEn: 'Lima', country: '秘鲁', state: '利马', latitude: -12.0464, longitude: -77.0428 },
  { id: 'toronto', name: '多伦多', nameEn: 'Toronto', country: '加拿大', state: '安大略省', latitude: 43.6532, longitude: -79.3832 },
  { id: 'vancouver', name: '温哥华', nameEn: 'Vancouver', country: '加拿大', state: '不列颠哥伦比亚省', latitude: 49.2827, longitude: -123.1207 },
  { id: 'montreal', name: '蒙特利尔', nameEn: 'Montreal', country: '加拿大', state: '魁北克省', latitude: 45.5017, longitude: -73.5673 },
]

export const QUICK_CITIES = [
  { id: 'beijing', name: '北京' },
  { id: 'shanghai', name: '上海' },
  { id: 'guangzhou', name: '广州' },
  { id: 'shenzhen', name: '深圳' },
  { id: 'chengdu', name: '成都' },
  { id: 'hangzhou', name: '杭州' },
]

export function useCitySearch() {
  const cityInput = ref('北京')
  const queryStatus = ref('')
  const queryMessage = ref('')
  const showManualCoords = ref(false)
  
  let debounceTimer = null
  
  const majorCities = computed(() => CITIES_DB.slice(0, 8))
  
  function searchInLocalDB(cityName) {
    if (!cityName || cityName.trim().length === 0) return null
    
    const query = cityName.trim().toLowerCase()
    
    for (const city of CITIES_DB) {
      if (city.name === cityName.trim()) {
        return city
      }
      if (city.name.toLowerCase().includes(query)) {
        return city
      }
      if (city.nameEn && city.nameEn.toLowerCase().includes(query)) {
        return city
      }
    }
    
    return null
  }
  
  async function searchViaAPI(cityName) {
    if (!cityName || cityName.trim().length === 0) return null
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    try {
      const result = await geoApi.geocodeCity(cityName.trim())
      clearTimeout(timeoutId)
      
      if (result?.found) {
        return {
          name: result.city || cityName,
          nameEn: '',
          country: result.country || '',
          state: result.state || '',
          latitude: result.latitude,
          longitude: result.longitude
        }
      }
    } catch (error) {
      clearTimeout(timeoutId)
      console.log('API查询失败，使用本地数据库:', error.message)
    }
    
    return null
  }
  
  async function searchCityByName(cityName) {
    if (!cityName || cityName.trim().length === 0) {
      queryStatus.value = ''
      queryMessage.value = ''
      return null
    }
    
    queryStatus.value = 'searching'
    queryMessage.value = '正在查询...'
    
    let city = searchInLocalDB(cityName)
    
    if (city) {
      queryStatus.value = 'valid'
      queryMessage.value = `已找到: ${city.name} (${city.country || ''})`
      return city
    }
    
    city = await searchViaAPI(cityName)
    
    if (city) {
      queryStatus.value = 'valid'
      queryMessage.value = `已找到: ${city.name} (${city.country || ''})`
      return city
    }
    
    queryStatus.value = 'invalid'
    queryMessage.value = '未找到该城市，请检查输入或手动设置经纬度'
    return null
  }
  
  async function queryCitySuggestions(queryString, callback) {
    if (!queryString || queryString.trim().length === 0) {
      callback([])
      return
    }
    
    const suggestions = []
    const query = queryString.trim().toLowerCase()
    
    for (const city of CITIES_DB) {
      if (city.name.toLowerCase().includes(query) ||
          (city.nameEn && city.nameEn.toLowerCase().includes(query))) {
        suggestions.push({
          value: city.name,
          ...city
        })
      }
      
      if (suggestions.length >= 10) break
    }
    
    callback(suggestions)
  }
  
  async function triggerSearch() {
    if (!cityInput.value || cityInput.value.trim().length === 0) {
      return
    }
    
    const city = await searchCityByName(cityInput.value)
    return city
  }
  
  function onCitySelect(item) {
    if (item) {
      cityInput.value = item.name
      queryStatus.value = 'valid'
      queryMessage.value = `已选择: ${item.name} (${item.country || ''})`
      
      return {
        birthPlace: item.name,
        latitude: item.latitude,
        longitude: item.longitude
      }
    }
    return null
  }
  
  function onCityInput(value) {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    
    debounceTimer = setTimeout(async () => {
      if (value && value.trim().length > 0) {
        await searchCityByName(value)
      }
    }, 1000)
  }
  
  function selectCityById(cityId) {
    const found = CITIES_DB.find(c => c.id === cityId)
    if (found) {
      cityInput.value = found.name
      queryStatus.value = 'valid'
      queryMessage.value = `已选择: ${found.name} (${found.country || ''})`
      
      return {
        birthPlace: found.name,
        latitude: found.latitude,
        longitude: found.longitude
      }
    }
    return null
  }
  
  return {
    cityInput,
    queryStatus,
    queryMessage,
    showManualCoords,
    majorCities,
    searchCityByName,
    queryCitySuggestions,
    triggerSearch,
    onCitySelect,
    onCityInput,
    selectCityById
  }
}

export default useCitySearch
