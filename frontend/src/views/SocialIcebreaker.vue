<template>
  <div class="social-icebreaker-container">
    <div class="stars-bg">
      <div v-for="i in 80" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <div class="main-content">
      <div class="page-header">
        <div class="header-icon">
          <el-icon size="32"><Connection /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">社交破冰助手</h1>
          <p class="page-subtitle">基于星盘性格画像，生成专属社交名片</p>
        </div>
      </div>

      <div class="content-wrapper">
        <div class="input-section">
          <div class="input-card">
            <div class="card-header">
              <div class="card-icon">
                <el-icon><Edit /></el-icon>
              </div>
              <span class="card-title">输入出生信息</span>
            </div>

            <div class="form-content">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">
                    <span class="label-icon"><el-icon><User /></el-icon></span>
                    <span>姓名/昵称</span>
                  </label>
                  <div class="input-wrapper">
                    <input 
                      type="text" 
                      v-model="form.name" 
                      placeholder="请输入您的姓名或昵称"
                      class="astro-input"
                    />
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-icon"><el-icon><Location /></el-icon></span>
                  <span>出生城市</span>
                </label>
                <div class="city-input-wrapper">
                  <el-autocomplete
                    v-model="cityInput"
                    :fetch-suggestions="queryCitySuggestions"
                    :trigger-on-focus="true"
                    :clearable="true"
                    @select="onCitySelect"
                    @input="onCityInput"
                    placeholder="输入城市名称"
                    class="city-autocomplete"
                  >
                    <template #default="{ item }">
                      <div class="option-content">
                        <span class="option-name">{{ item.name }}</span>
                        <span class="option-location" v-if="item.country">{{ item.country }}</span>
                      </div>
                    </template>
                  </el-autocomplete>
                </div>
                <div class="input-hint">
                  已选: {{ form.birthPlace || '未选择' }} | 经度: {{ form.longitude.toFixed(2) }}° | 纬度: {{ form.latitude.toFixed(2) }}°
                </div>
              </div>

              <div class="quick-cities">
                <span class="quick-label">常用:</span>
                <div class="city-buttons">
                  <button 
                    v-for="city in quickCities" 
                    :key="city.id"
                    type="button" 
                    class="city-btn"
                    @click="selectQuickCity(city)"
                  >
                    {{ city.name }}
                  </button>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">
                    <span class="label-icon"><el-icon><Calendar /></el-icon></span>
                    <span>出生日期</span>
                  </label>
                  <el-date-picker
                    v-model="form.birthDate"
                    type="date"
                    placeholder="选择出生日期"
                    format="YYYY年MM月DD日"
                    value-format="YYYY-MM-DD"
                    class="astro-date-input"
                  />
                </div>

                <div class="form-group">
                  <label class="form-label">
                    <span class="label-icon"><el-icon><Clock /></el-icon></span>
                    <span>出生时间</span>
                  </label>
                  <el-time-picker
                    v-model="form.birthTime"
                    placeholder="选择出生时间"
                    format="HH:mm"
                    value-format="HH:mm"
                    class="astro-time-input"
                  />
                </div>
              </div>

              <div class="form-row" v-if="showManualCoords">
                <div class="form-group">
                  <label class="form-label">经度</label>
                  <input 
                    type="number" 
                    step="0.01"
                    v-model="form.longitude" 
                    class="astro-input"
                  />
                  <div class="input-hint">东经为正</div>
                </div>
                <div class="form-group">
                  <label class="form-label">纬度</label>
                  <input 
                    type="number" 
                    step="0.01"
                    v-model="form.latitude" 
                    class="astro-input"
                  />
                  <div class="input-hint">北纬为正</div>
                </div>
              </div>

              <div class="form-row">
                <button 
                  type="button" 
                  class="toggle-manual-btn"
                  @click="showManualCoords = !showManualCoords"
                >
                  {{ showManualCoords ? '隐藏手动输入' : '手动输入经纬度' }}
                </button>
              </div>

              <div class="submit-section">
                <button 
                  type="button" 
                  class="generate-btn"
                  :class="{ 'btn-loading': generating }"
                  :disabled="generating || !canGenerate"
                  @click="generateSocialCard"
                >
                  <el-icon v-if="generating" class="loading-icon"><Loading /></el-icon>
                  <el-icon v-else><MagicStick /></el-icon>
                  <span>{{ generating ? '生成中...' : '生成社交名片' }}</span>
                </button>
              </div>
            </div>
          </div>

          <div class="info-card" v-if="!cardData">
            <div class="info-icon">
              <el-icon size="40"><InfoFilled /></el-icon>
            </div>
            <h3 class="info-title">什么是社交破冰助手？</h3>
            <ul class="info-features">
              <li>
                <span class="feature-icon">✨</span>
                <span>基于您的星盘，提取性格核心关键词</span>
              </li>
              <li>
                <span class="feature-icon">⚠️</span>
                <span>生成专属「避雷指南」，避免社交雷区</span>
              </li>
              <li>
                <span class="feature-icon">💬</span>
                <span>推荐共同话题，快速拉近距离</span>
              </li>
              <li>
                <span class="feature-icon">🤝</span>
                <span>处理性格对冲，避免刻板印象</span>
              </li>
            </ul>
          </div>
        </div>

        <Transition name="slide-right" mode="out-in">
          <div v-if="cardData" key="card" class="result-section">
            <div class="result-actions">
              <button class="regenerate-btn" @click="regenerateCard">
                <el-icon><Refresh /></el-icon>
                <span>重新生成</span>
              </button>
            </div>
            
            <SocialCard :card-data="cardData.social_card" />
          </div>

          <div v-else-if="displayState === 'loading'" key="loading" class="loading-section">
            <div class="loading-content">
              <div class="loading-spinner"></div>
              <div class="loading-text">
                <p class="loading-title">正在分析您的星盘...</p>
                <p class="loading-desc">提取性格特质、检测对冲配置、生成社交标签</p>
              </div>
            </div>
          </div>

          <div v-else-if="displayState === 'error'" key="error" class="error-section">
            <div class="error-content">
              <div class="error-icon">
                <el-icon size="48"><Warning /></el-icon>
              </div>
              <p class="error-title">生成失败</p>
              <p class="error-message">{{ errorMessage }}</p>
              <button class="retry-btn" @click="retryGenerate">
                <el-icon><Refresh /></el-icon>
                <span>重新尝试</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection, Edit, User, Location, Calendar, Clock, Loading, MagicStick, InfoFilled, Warning, Refresh } from '@element-plus/icons-vue'
import SocialCard from '@/components/SocialCard.vue'
import { geoApi } from '@/api'

const router = useRouter()

const CITIES_DB = [
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
]

const quickCities = [
  { id: 'beijing', name: '北京', latitude: 39.9042, longitude: 116.4074 },
  { id: 'shanghai', name: '上海', latitude: 31.2304, longitude: 121.4737 },
  { id: 'guangzhou', name: '广州', latitude: 23.1291, longitude: 113.2644 },
  { id: 'shenzhen', name: '深圳', latitude: 22.5431, longitude: 114.0579 },
  { id: 'chengdu', name: '成都', latitude: 30.5728, longitude: 104.0668 },
  { id: 'hangzhou', name: '杭州', latitude: 30.2741, longitude: 120.1551 },
]

const form = reactive({
  name: '',
  birthDate: '1990-01-01',
  birthTime: '12:00',
  birthPlace: '北京',
  latitude: 39.9042,
  longitude: 116.4074,
  houseSystem: 'placidus'
})

const cityInput = ref('北京')
const showManualCoords = ref(false)
const generating = ref(false)
const cardData = ref(null)
const errorMessage = ref('')

const displayState = computed(() => {
  if (generating.value) {
    return 'loading'
  }
  if (errorMessage.value) {
    return 'error'
  }
  if (cardData.value) {
    return 'result'
  }
  return 'empty'
})

const canGenerate = computed(() => {
  return form.birthDate && form.birthTime && form.latitude !== null && form.longitude !== null
})

function getStarStyle(index) {
  const size = Math.random() * 2 + 1
  return {
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${Math.random() * 4}s`,
    opacity: Math.random() * 0.4 + 0.2
  }
}

function queryCitySuggestions(queryString, callback) {
  if (!queryString || queryString.trim().length === 0) {
    callback(CITIES_DB.slice(0, 15))
    return
  }
  
  const q = queryString.toLowerCase()
  const results = CITIES_DB.filter(city => 
    city.name.includes(queryString) || 
    city.name.toLowerCase().includes(q) ||
    (city.nameEn && city.nameEn.toLowerCase().includes(q))
  )
  
  callback(results.slice(0, 15))
}

function onCitySelect(item) {
  if (item) {
    cityInput.value = item.name
    form.birthPlace = item.name
    form.latitude = item.latitude
    form.longitude = item.longitude
  }
}

function onCityInput(value) {
  if (!value || value.trim().length === 0) return
  
  const localCity = CITIES_DB.find(c => c.name === value.trim())
  if (localCity) {
    form.birthPlace = localCity.name
    form.latitude = localCity.latitude
    form.longitude = localCity.longitude
  }
}

function selectQuickCity(city) {
  cityInput.value = city.name
  form.birthPlace = city.name
  form.latitude = city.latitude
  form.longitude = city.longitude
}

async function generateSocialCard() {
  if (!canGenerate.value) {
    ElMessage.warning('请填写完整的出生信息')
    return
  }
  
  generating.value = true
  errorMessage.value = ''
  cardData.value = null
  
  try {
    const requestData = {
      name: form.name || '用户',
      birth_date: form.birthDate,
      birth_time: form.birthTime,
      latitude: form.latitude,
      longitude: form.longitude,
      birth_place: form.birthPlace,
      house_system: form.houseSystem
    }
    
    console.log('发送社交名片请求:', requestData)
    
    const response = await fetch('/api/social-icebreaker/card', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    })
    
    const result = await response.json()
    
    console.log('收到社交名片响应:', result)
    
    if (result.code === 200 && result.data && result.data.success) {
      cardData.value = result.data
      ElMessage.success('社交名片生成成功！')
    } else {
      const error = result.data?.error || result.message || '生成失败'
      errorMessage.value = getFriendlyErrorMessage(error)
      ElMessage.error(errorMessage.value)
    }
  } catch (err) {
    console.error('生成社交名片失败:', err)
    
    let msg = '网络连接失败，请检查网络连接'
    if (err.message) {
      if (err.message.includes('Network Error')) {
        msg = '无法连接到服务器，请确保后端服务已启动'
      } else {
        msg = err.message
      }
    }
    
    errorMessage.value = msg
    ElMessage.error(msg)
  } finally {
    generating.value = false
  }
}

function getFriendlyErrorMessage(error) {
  if (!error) return '生成失败，请稍后重试'
  
  if (error.includes('API key') || error.includes('认证') || error.includes('401')) {
    return 'AI服务配置错误：请联系管理员检查API配置'
  }
  if (error.includes('余额') || error.includes('403')) {
    return 'AI服务暂时不可用：账户余额不足'
  }
  if (error.includes('超时') || error.includes('timeout')) {
    return '请求超时，请稍后重试'
  }
  if (error.includes('网络') || error.includes('连接')) {
    return '网络连接失败，请检查网络'
  }
  
  return error
}

function regenerateCard() {
  cardData.value = null
  generateSocialCard()
}

function retryGenerate() {
  errorMessage.value = ''
  generateSocialCard()
}

onMounted(() => {
})
</script>

<style lang="scss" scoped>
.social-icebreaker-container {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0a0a1a, #0f0f2a);
}

.stars-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle 4s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}

.glow-orbs {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.35;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation: float-1 25s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation: float-2 20s ease-in-out infinite;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 30%;
  left: 20%;
  animation: pulse 10s ease-in-out infinite;
}

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-80px, 50px); }
}

@keyframes float-2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(60px, -40px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.25; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(1.3); }
}

.main-content {
  position: relative;
  z-index: 10;
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3), transparent);
  border-radius: 16px;
  color: #a78bfa;
}

.header-text {
  .page-title {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(90deg, #fff, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .page-subtitle {
    margin: 4px 0 0;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.5);
  }
}

.content-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  flex: 1;
  
  @media (max-width: 1000px) {
    grid-template-columns: 1fr;
  }
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-card,
.info-card {
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.95), rgba(15, 15, 35, 0.98));
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.08), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.card-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 10px;
  color: #a78bfa;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.form-content {
  padding: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
  
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  
  .label-icon {
    color: #a78bfa;
  }
}

.input-wrapper {
  position: relative;
}

.astro-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  color: #fff;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
  
  &:focus {
    outline: none;
    border-color: rgba(139, 92, 246, 0.5);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }
}

.astro-date-input,
.astro-time-input {
  width: 100%;
  
  :deep(.el-input__wrapper) {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(139, 92, 246, 0.2);
    box-shadow: none;
    padding: 8px 12px;
    border-radius: 10px;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4);
    }
    
    &.is-focus {
      border-color: rgba(139, 92, 246, 0.5);
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }
  }
  
  :deep(.el-input__inner) {
    color: #fff;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
  }
  
  :deep(.el-input__prefix-inner),
  :deep(.el-input__suffix-inner) {
    color: #a78bfa;
  }
}

.city-autocomplete {
  width: 100%;
  
  :deep(.el-input__wrapper) {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(139, 92, 246, 0.2);
    box-shadow: none;
    padding: 8px 12px;
    border-radius: 10px;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4);
    }
    
    &.is-focus {
      border-color: rgba(139, 92, 246, 0.5);
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }
  }
  
  :deep(.el-input__inner) {
    color: #fff;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
  }
}

.input-hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.quick-cities {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  
  .quick-label {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .city-buttons {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .city-btn {
    padding: 6px 14px;
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 20px;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba(139, 92, 246, 0.2);
      color: #a78bfa;
    }
  }
}

.toggle-manual-btn {
  background: transparent;
  border: none;
  color: rgba(167, 139, 250, 0.7);
  font-size: 0.8rem;
  cursor: pointer;
  transition: color 0.3s ease;
  
  &:hover {
    color: #a78bfa;
  }
}

.submit-section {
  margin-top: 8px;
}

.generate-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &.btn-loading {
    .loading-icon {
      animation: spin 1s linear infinite;
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.info-card {
  padding: 24px;
  
  .info-icon {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.2), transparent);
    border-radius: 50%;
    margin: 0 auto 16px;
    color: #a78bfa;
  }
  
  .info-title {
    margin: 0 0 20px;
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    text-align: center;
  }
  
  .info-features {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
    
    li {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      
      .feature-icon {
        font-size: 1.2rem;
        flex-shrink: 0;
      }
      
      span:last-child {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.6;
      }
    }
  }
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
}

.regenerate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 10px;
  color: #a78bfa;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
  }
}

.loading-section,
.error-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.loading-content,
.error-content {
  text-align: center;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(139, 92, 246, 0.2);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 24px;
}

.loading-title,
.error-title {
  margin: 0 0 8px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #fff;
}

.loading-desc,
.error-message {
  margin: 0 0 24px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
}

.error-icon {
  color: #f87171;
  margin-bottom: 16px;
}

.retry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
  border-radius: 10px;
  color: #f87171;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 0 auto;
  
  &:hover {
    background: rgba(248, 113, 113, 0.2);
  }
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
