<template>
  <div class="synastry-container">
    <div class="stars-bg">
      <div v-for="i in 40" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="synastry-main">
      <div class="synastry-header">
        <h1 class="main-title">双人合盘</h1>
        <p class="subtitle">分析两个人星盘之间的互动相位</p>
      </div>

      <div class="synastry-content">
        <SynastryPersonForm
          v-model:person="personA"
          label="外圈 - 人物 A"
          color="#ff8c32"
          :cities="CITIES_DB"
          :quick-cities="QUICK_CITIES"
        />

        <div class="swap-btn-wrapper">
          <button class="swap-btn" @click="swapPersons" title="交换两人位置">
            ⇄
          </button>
        </div>

        <SynastryPersonForm
          v-model:person="personB"
          label="内圈 - 人物 B"
          color="#50c8ff"
          :cities="CITIES_DB"
          :quick-cities="QUICK_CITIES"
        />
      </div>

      <div class="submit-section">
        <button 
          type="button" 
          class="submit-btn"
          :class="{ 'btn-loading': calculating }"
          :disabled="calculating"
          @click="calculateSynastry"
        >
          <span v-if="!calculating">开始计算合盘</span>
          <span v-else>计算中...</span>
        </button>
      </div>

      <Transition name="fade">
        <div v-if="showResult" class="result-section">
          <SynastryResult
            :synastry-data="synastryData"
            :person-a-name="personA.name || '人物 A'"
            :person-b-name="personB.name || '人物 B'"
          />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { synastryApi } from '@/api'
import { CITIES_DB, QUICK_CITIES } from '@/constants/chart'
import SynastryPersonForm from '@/components/synastry/SynastryPersonForm.vue'
import SynastryResult from '@/components/synastry/SynastryResult.vue'

const calculating = ref(false)
const showResult = ref(false)
const synastryData = ref(null)

const personA = reactive({
  name: '',
  birthDate: '1990-01-01',
  birthTime: '12:00',
  cityInput: '北京',
  birthPlace: '北京',
  latitude: 39.9042,
  longitude: 116.4074,
  houseSystem: 'placidus'
})

const personB = reactive({
  name: '',
  birthDate: '1992-06-15',
  birthTime: '10:30',
  cityInput: '上海',
  birthPlace: '上海',
  latitude: 31.2304,
  longitude: 121.4737,
  houseSystem: 'placidus'
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

function swapPersons() {
  const temp = { ...personA }
  Object.assign(personA, personB)
  Object.assign(personB, temp)
}

async function calculateSynastry() {
  if (!personA.birthDate || !personA.birthTime) {
    ElMessage.warning('请选择人物A的出生日期和时间')
    return
  }
  if (!personB.birthDate || !personB.birthTime) {
    ElMessage.warning('请选择人物B的出生日期和时间')
    return
  }
  
  calculating.value = true
  
  try {
    const result = await synastryApi.calculateSynastry({
      person_a: {
        name: personA.name || 'A',
        birth_date: personA.birthDate,
        birth_time: personA.birthTime,
        birth_place: personA.birthPlace,
        latitude: personA.latitude,
        longitude: personA.longitude,
        house_system: personA.houseSystem
      },
      person_b: {
        name: personB.name || 'B',
        birth_date: personB.birthDate,
        birth_time: personB.birthTime,
        birth_place: personB.birthPlace,
        latitude: personB.latitude,
        longitude: personB.longitude,
        house_system: personB.houseSystem
      }
    })
    
    synastryData.value = result
    showResult.value = true
    ElMessage.success('合盘计算完成')
    
  } catch (error) {
    console.error('合盘计算失败:', error)
    ElMessage.error(error.message || '合盘计算失败')
  } finally {
    calculating.value = false
  }
}
</script>

<style lang="scss" scoped>
.synastry-container {
  min-height: 100vh;
  width: 100%;
  position: relative;
  background: linear-gradient(180deg, #0a0a1a 0%, #0d0d25 100%);
  overflow-x: hidden;
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

.synastry-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.synastry-header {
  text-align: center;
  margin-bottom: 20px;
}

.main-title {
  font-size: 1.6rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ff8c32 0%, #50c8ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 6px;
}

.subtitle {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.synastry-content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: flex-start;
}

.swap-btn-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 60px;
}

.swap-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 50%;
  color: #c4b5fd;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.3);
    transform: rotate(180deg);
  }
}

.submit-section {
  display: flex;
  justify-content: center;
  margin: 8px 0;
}

.submit-btn {
  padding: 14px 48px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  border-radius: 30px;
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.result-section {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 900px) {
  .synastry-content {
    grid-template-columns: 1fr;
  }
  
  .swap-btn-wrapper {
    padding-top: 0;
    padding-bottom: 8px;
    
    .swap-btn {
      transform: rotate(90deg);
      
      &:hover {
        transform: rotate(270deg);
      }
    }
  }
}
</style>
