<template>
  <div class="horoscope-container">
    <div class="stars-bg">
      <div v-for="i in 80" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>
    
    <div class="zodiac-wheel-bg">
      <svg viewBox="0 0 200 200" class="zodiac-wheel">
        <circle cx="100" cy="100" r="95" fill="none" stroke="rgba(139, 92, 246, 0.15)" stroke-width="1" />
        <circle cx="100" cy="100" r="75" fill="none" stroke="rgba(139, 92, 246, 0.1)" stroke-width="0.5" />
        <circle cx="100" cy="100" r="55" fill="none" stroke="rgba(139, 92, 246, 0.08)" stroke-width="0.5" />
        <circle cx="100" cy="100" r="30" fill="rgba(139, 92, 246, 0.03)" stroke="rgba(139, 92, 246, 0.15)" stroke-width="1" />
      </svg>
    </div>

    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <div class="horoscope-main">
      <div class="horoscope-header">
        <div class="header-icon">
          <el-icon size="36"><Sunny /></el-icon>
        </div>
        <h1 class="main-title">每日星运</h1>
        <p class="subtitle">{{ currentDateDisplay }}</p>
      </div>

      <div class="mode-switcher" v-if="isLoggedIn">
        <div class="mode-buttons">
          <el-radio-group v-model="usePersonalMode" size="default" @change="onModeChange">
            <el-radio-button :value="true">
              <span class="mode-icon">✨</span>
              <span class="mode-text">专属运势</span>
            </el-radio-button>
            <el-radio-button :value="false">
              <span class="mode-icon">🌙</span>
              <span class="mode-text">切换星座</span>
            </el-radio-button>
          </el-radio-group>
        </div>
        
        <div v-if="usePersonalMode && horoscopeData?.is_personalized" class="personal-badge">
          <span class="badge-icon">🔮</span>
          <span class="badge-text">基于您的本命盘生成</span>
        </div>
      </div>

      <ZodiacSelector 
        v-if="!usePersonalMode"
        v-model="selectedSign" 
        :zodiac-signs="zodiacSigns" 
        @change="onSignChange"
      />

      <div v-if="!isLoggedIn" class="login-hint">
        <div class="hint-icon">💡</div>
        <div class="hint-content">
          <p class="hint-title">登录后可查看专属运势</p>
          <p class="hint-desc">基于您的太阳/月亮/上升星座，获取更精准的个性化运势</p>
          <el-button type="primary" size="small" @click="goToLogin" class="hint-btn">
            立即登录
          </el-button>
        </div>
      </div>

      <div class="horoscope-content">
        <div v-if="loading" class="loading-container">
          <div class="loading-visual">
            <div class="loading-rings">
              <div class="ring ring-1"></div>
              <div class="ring ring-2"></div>
              <div class="ring ring-3"></div>
            </div>
            <div class="loading-icon">✨</div>
          </div>
          <p class="loading-text">正在为您解析今日星运...</p>
        </div>

        <div v-else-if="error" class="error-container">
          <div class="error-visual">
            <div class="error-shape">
              <el-icon size="48"><WarningFilled /></el-icon>
            </div>
          </div>
          <p class="error-title">获取运势失败</p>
          <p class="error-text">{{ errorMessage }}</p>
          <div class="error-actions">
            <el-button type="primary" @click="reloadHoroscope" class="retry-btn">
              <el-icon><Refresh /></el-icon>
              重新加载
            </el-button>
          </div>
        </div>

        <div v-else-if="horoscopeData" class="horoscope-result">
          <div class="sign-header-card">
            <div class="sign-info">
              <div class="sign-symbol" :style="{ color: currentSignColor }">
                {{ horoscopeData.symbol }}
              </div>
              <div class="sign-details">
                <h2 class="sign-name">{{ horoscopeData.sign }}</h2>
                <p class="sign-date-range">{{ currentSignDateRange }}</p>
                
                <div v-if="horoscopeData.is_personalized" class="astro-tags">
                  <span v-if="horoscopeData.sun_sign" class="astro-tag sun-tag">
                    <span class="tag-icon">☀</span>
                    <span class="tag-text">太阳 {{ horoscopeData.sun_sign }}</span>
                  </span>
                  <span v-if="horoscopeData.moon_sign" class="astro-tag moon-tag">
                    <span class="tag-icon">☽</span>
                    <span class="tag-text">月亮 {{ horoscopeData.moon_sign }}</span>
                  </span>
                  <span v-if="horoscopeData.ascendant_sign" class="astro-tag asc-tag">
                    <span class="tag-icon">⬆</span>
                    <span class="tag-text">上升 {{ horoscopeData.ascendant_sign }}</span>
                  </span>
                </div>
              </div>
            </div>
            <div class="overall-score">
              <div class="score-circle">
                <svg class="score-svg" viewBox="0 0 100 100">
                  <circle class="score-bg" cx="50" cy="50" r="42" />
                  <circle 
                    class="score-progress" 
                    cx="50" 
                    cy="50" 
                    r="42"
                    :style="{ 
                      strokeDasharray: getStrokeDasharray(horoscopeData.overall_score),
                      stroke: getScoreColor(horoscopeData.overall_score)
                    }"
                  />
                </svg>
                <div class="score-inner">
                  <span class="score-value">{{ horoscopeData.overall_score }}</span>
                  <span class="score-unit">分</span>
                </div>
              </div>
              <span class="score-label">今日运势指数</span>
            </div>
          </div>

          <div v-if="horoscopeData.keywords && horoscopeData.keywords.length" class="keywords-section">
            <div class="section-header">
              <span class="section-icon">🔑</span>
              <h3 class="section-title">今日关键词</h3>
            </div>
            <div class="keywords-list">
              <div 
                v-for="(keyword, index) in horoscopeData.keywords" 
                :key="index"
                class="keyword-tag"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                {{ keyword }}
              </div>
            </div>
          </div>

          <div class="lucky-tags-section">
            <div class="lucky-tag">
              <span class="tag-icon-large">🎨</span>
              <span class="tag-label-large">幸运色</span>
              <span class="tag-value-large">{{ horoscopeData.lucky_color }}</span>
            </div>
            <div class="lucky-tag">
              <span class="tag-icon-large">🔢</span>
              <span class="tag-label-large">幸运数字</span>
              <span class="tag-value-large">{{ horoscopeData.lucky_number }}</span>
            </div>
            <div class="lucky-tag">
              <span class="tag-icon-large">🌟</span>
              <span class="tag-label-large">贵人星座</span>
              <span class="tag-value-large">{{ horoscopeData.lucky_zodiac }}</span>
            </div>
            <div class="lucky-tag">
              <span class="tag-icon-large">⚠️</span>
              <span class="tag-label-large">提防星座</span>
              <span class="tag-value-large">{{ horoscopeData.cautious_zodiac }}</span>
            </div>
            <div class="lucky-tag">
              <span class="tag-icon-large">⏰</span>
              <span class="tag-label-large">幸运时段</span>
              <span class="tag-value-large">{{ horoscopeData.lucky_time }}</span>
            </div>
            <div class="lucky-tag">
              <span class="tag-icon-large">🧭</span>
              <span class="tag-label-large">幸运方位</span>
              <span class="tag-value-large">{{ horoscopeData.lucky_direction }}</span>
            </div>
          </div>

          <div class="categories-section">
            <HoroscopeCategoryCard
              title="感情运势"
              icon="❤️"
              :score="horoscopeData.love_score"
              :opportunity="horoscopeData.love_opportunity"
              :challenge="horoscopeData.love_challenge"
              :advice="horoscopeData.love_advice"
              color="#ec4899"
            />
            <HoroscopeCategoryCard
              title="事业运势"
              icon="💼"
              :score="horoscopeData.career_score"
              :opportunity="horoscopeData.career_opportunity"
              :challenge="horoscopeData.career_challenge"
              :advice="horoscopeData.career_advice"
              color="#f97316"
            />
            <HoroscopeCategoryCard
              title="财运指数"
              icon="💰"
              :score="horoscopeData.wealth_score"
              :opportunity="horoscopeData.wealth_opportunity"
              :challenge="horoscopeData.wealth_challenge"
              :advice="horoscopeData.wealth_advice"
              color="#eab308"
            />
            <HoroscopeCategoryCard
              title="健康运势"
              icon="💪"
              :score="horoscopeData.health_score"
              :opportunity="horoscopeData.health_opportunity"
              :challenge="horoscopeData.health_challenge"
              :advice="horoscopeData.health_advice"
              color="#22c55e"
            />
          </div>

          <div v-if="horoscopeData.lucky_tips && horoscopeData.lucky_tips.length" class="lucky-tips-section">
            <div class="section-header">
              <span class="section-icon">🍀</span>
              <h3 class="section-title">今日开运小建议</h3>
            </div>
            <div class="tips-list">
              <div 
                v-for="(tip, index) in horoscopeData.lucky_tips" 
                :key="index"
                class="tip-item"
              >
                <span class="tip-number">{{ index + 1 }}</span>
                <span class="tip-text">{{ tip }}</span>
              </div>
            </div>
          </div>

          <div v-if="!usePersonalMode && isLoggedIn" class="personal-tip-section">
            <div class="tip-card">
              <span class="tip-card-icon">✨</span>
              <div class="tip-card-content">
                <h4 class="tip-card-title">查看您的专属运势</h4>
                <p class="tip-card-desc">基于您的本命盘数据，获取更精准的个性化运势解读</p>
              </div>
              <el-button type="primary" size="small" @click="switchToPersonal" class="tip-card-btn">
                切换到专属运势
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { horoscopeApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Sunny, WarningFilled, Refresh } from '@element-plus/icons-vue'
import ZodiacSelector from '@/components/horoscope/ZodiacSelector.vue'
import HoroscopeCategoryCard from '@/components/horoscope/HoroscopeCategoryCard.vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const error = ref(false)
const errorMessage = ref('')
const selectedSign = ref('白羊座')
const horoscopeData = ref(null)
const zodiacSigns = ref([])
const usePersonalMode = ref(true)

const isLoggedIn = computed(() => userStore.isLoggedIn)

const currentDateDisplay = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${year}年${month}月${day}日 ${weekdays[now.getDay()]}`
})

const currentSignColor = computed(() => {
  if (!zodiacSigns.value || !selectedSign.value) return '#8b5cf6'
  const sign = zodiacSigns.value.find(s => s.name === (horoscopeData.value?.sign || selectedSign.value))
  return sign?.color || '#8b5cf6'
})

const currentSignDateRange = computed(() => {
  if (!zodiacSigns.value || !horoscopeData.value?.sign) return ''
  const sign = zodiacSigns.value.find(s => s.name === horoscopeData.value.sign)
  return sign?.date_range || ''
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

function getScoreColor(score) {
  if (score >= 85) return '#22c55e'
  if (score >= 70) return '#eab308'
  if (score >= 55) return '#f97316'
  return '#ef4444'
}

function getStrokeDasharray(score) {
  const circumference = 263.89
  const dasharray = (score / 100) * circumference
  return `${dasharray} ${circumference}`
}

async function loadZodiacSigns() {
  try {
    const result = await horoscopeApi.getZodiacSigns()
    if (result?.zodiac_signs) {
      zodiacSigns.value = result.zodiac_signs
    }
  } catch (err) {
    console.error('加载星座列表失败:', err)
  }
}

async function loadPersonalHoroscope() {
  loading.value = true
  error.value = false
  
  try {
    const result = await horoscopeApi.getPersonalHoroscope()
    horoscopeData.value = result
    if (result?.sign) {
      selectedSign.value = result.sign
    }
  } catch (err) {
    console.error('获取个性化运势失败:', err)
    usePersonalMode.value = false
    await loadHoroscope()
  } finally {
    loading.value = false
  }
}

async function loadHoroscope() {
  if (!selectedSign.value) return
  
  loading.value = true
  error.value = false
  
  try {
    const result = await horoscopeApi.getDailyHoroscope(selectedSign.value)
    horoscopeData.value = result
  } catch (err) {
    error.value = true
    errorMessage.value = err.message || '获取运势失败，请稍后重试'
    console.error('加载运势失败:', err)
  } finally {
    loading.value = false
  }
}

async function reloadHoroscope() {
  if (usePersonalMode.value && isLoggedIn.value) {
    await loadPersonalHoroscope()
  } else {
    await loadHoroscope()
  }
}

function onSignChange(sign) {
  selectedSign.value = sign
  loadHoroscope()
}

async function onModeChange() {
  horoscopeData.value = null
  if (usePersonalMode.value && isLoggedIn.value) {
    await loadPersonalHoroscope()
  } else {
    await loadHoroscope()
  }
}

function goToLogin() {
  router.push('/login')
}

function switchToPersonal() {
  usePersonalMode.value = true
}

watch(usePersonalMode, () => {
  onModeChange()
})

watch(selectedSign, () => {
  if (!usePersonalMode.value) {
    loadHoroscope()
  }
})

onMounted(async () => {
  await loadZodiacSigns()
  
  if (isLoggedIn.value) {
    await loadPersonalHoroscope()
  } else {
    await loadHoroscope()
  }
})
</script>

<style lang="scss" scoped>
.horoscope-container {
  min-height: 100%;
  width: 100%;
  position: relative;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
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

.zodiac-wheel-bg {
  position: absolute;
  top: 50%;
  right: -10%;
  transform: translateY(-50%);
  width: 60vh;
  max-width: 500px;
  height: 60vh;
  max-height: 500px;
  pointer-events: none;
  z-index: 1;
  opacity: 0.25;
}

.zodiac-wheel {
  width: 100%;
  height: 100%;
  animation: rotate-slow 120s linear infinite;
}

@keyframes rotate-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

.horoscope-main {
  position: relative;
  z-index: 10;
  flex: 1;
  padding: 16px 20px 40px;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.horoscope-header {
  text-align: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.header-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  color: #a78bfa;
}

.main-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.mode-switcher {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.mode-buttons {
  :deep(.el-radio-group) {
    background: rgba(20, 20, 50, 0.8);
    border-radius: 12px;
    padding: 4px;
  }
  
  :deep(.el-radio-button__inner) {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: rgba(255, 255, 255, 0.5);
  }
  
  :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    color: #fff;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
  }
}

.mode-icon {
  font-size: 16px;
}

.mode-text {
  font-size: 14px;
  font-weight: 500;
}

.personal-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: 20px;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.badge-icon {
  font-size: 14px;
}

.badge-text {
  font-size: 12px;
  color: #a78bfa;
}

.login-hint {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  margin-bottom: 20px;
  align-items: center;
}

.hint-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.hint-content {
  flex: 1;
}

.hint-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 4px 0;
}

.hint-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.hint-btn {
  flex-shrink: 0;
}

.horoscope-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-visual {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-rings {
  position: absolute;
  width: 100%;
  height: 100%;
}

.ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ring-rotate 2s linear infinite;
}

.ring-1 {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-top-color: #8b5cf6;
}

.ring-2 {
  top: 8px;
  left: 8px;
  right: 8px;
  bottom: 8px;
  border-right-color: #60a5fa;
  animation-direction: reverse;
  animation-duration: 1.5s;
}

.ring-3 {
  top: 16px;
  left: 16px;
  right: 16px;
  bottom: 16px;
  border-bottom-color: #06b6d4;
  animation-duration: 2.5s;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.loading-icon {
  font-size: 32px;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

.loading-text {
  margin-top: 24px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.error-visual {
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(239, 68, 68, 0.2) 0%, transparent 70%);
  border-radius: 50%;
  margin-bottom: 20px;
}

.error-shape {
  color: #f87171;
}

.error-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px 0;
}

.error-text {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  margin: 0 0 20px 0;
}

.error-actions {
  display: flex;
  gap: 12px;
}

.retry-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.horoscope-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sign-header-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.sign-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sign-symbol {
  font-size: 48px;
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%);
  border-radius: 50%;
}

.sign-details {
  display: flex;
  flex-direction: column;
}

.sign-name {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 4px 0;
}

.sign-date-range {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 8px 0;
}

.astro-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.astro-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
}

.sun-tag {
  background: rgba(249, 115, 22, 0.15);
  color: #f97316;
}

.moon-tag {
  background: rgba(96, 165, 250, 0.15);
  color: #60a5fa;
}

.asc-tag {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.tag-icon {
  font-size: 12px;
}

.overall-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-circle {
  position: relative;
  width: 80px;
  height: 80px;
}

.score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 6;
  stroke-linecap: round;
}

.score-progress {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease;
}

.score-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.score-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.score-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.section-icon {
  font-size: 18px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.keywords-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 20px;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.keyword-tag {
  padding: 8px 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.1) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #a78bfa;
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.lucky-tags-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.lucky-tag {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
  cursor: default;
}

.lucky-tag:hover {
  border-color: rgba(139, 92, 246, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.15);
}

.tag-icon-large {
  font-size: 28px;
}

.tag-label-large {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.tag-value-large {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.categories-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.lucky-tips-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 20px;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 12px;
  border-left: 3px solid #8b5cf6;
}

.tip-number {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.tip-text {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.7);
}

.personal-tip-section {
  margin-top: 8px;
}

.tip-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  border-radius: 16px;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.tip-card-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.tip-card-content {
  flex: 1;
}

.tip-card-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 4px 0;
}

.tip-card-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.tip-card-btn {
  flex-shrink: 0;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: none;
}

@media (max-width: 768px) {
  .horoscope-main {
    padding: 12px 16px 30px;
  }

  .main-title {
    font-size: 22px;
  }

  .mode-switcher {
    gap: 10px;
  }

  .sign-header-card {
    flex-direction: column;
    gap: 20px;
    padding: 20px;
  }

  .sign-info {
    justify-content: center;
    flex-direction: column;
    text-align: center;
  }

  .astro-tags {
    justify-content: center;
  }

  .login-hint {
    flex-direction: column;
    text-align: center;
  }

  .lucky-tags-section {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .lucky-tag {
    padding: 12px;
  }

  .categories-section {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .sign-symbol {
    font-size: 40px;
    width: 60px;
    height: 60px;
  }

  .sign-name {
    font-size: 20px;
  }

  .score-circle {
    width: 70px;
    height: 70px;
  }

  .score-value {
    font-size: 20px;
  }

  .tip-card {
    flex-direction: column;
    text-align: center;
  }

  .keywords-list {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .lucky-tags-section {
    grid-template-columns: repeat(3, 1fr);
  }

  .tag-icon-large {
    font-size: 22px;
  }

  .tag-value-large {
    font-size: 12px;
  }

  .tag-label-large {
    display: none;
  }
}
</style>
