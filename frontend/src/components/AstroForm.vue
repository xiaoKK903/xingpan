<template>
  <form class="astro-form">
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">
          <span class="label-icon"><el-icon><User /></el-icon></span>
          <span>姓名</span>
        </label>
        <div class="input-wrapper">
          <input 
            type="text" 
            v-model="localForm.name" 
            placeholder="请输入您的姓名"
            class="astro-input"
          />
          <div class="input-border-effect"></div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">
          <span class="label-icon"><el-icon><Location /></el-icon></span>
          <span>出生城市</span>
        </label>

        <div class="city-input-wrapper">
          <div class="city-input-row">
            <div class="input-wrapper autocomplete-wrapper">
              <el-autocomplete
                v-model="cityInput"
                :fetch-suggestions="queryCitySuggestions"
                :trigger-on-focus="true"
                :clearable="true"
                @select="handleCitySelect"
                @input="handleCityInput"
                placeholder="输入城市名称或下拉选择（支持中英文）"
                class="city-autocomplete"
                popper-class="city-popper"
              >
                <template #default="{ item }">
                  <div class="option-content">
                    <span class="option-name">{{ item.name }}</span>
                    <span class="option-en" v-if="item.nameEn">{{ item.nameEn }}</span>
                    <span class="option-location" v-if="item.country">
                      {{ item.state ? item.state + ', ' : '' }}{{ item.country }}
                    </span>
                  </div>
                </template>
              </el-autocomplete>
              <div class="input-border-effect"></div>
            </div>
            <button
              type="button"
              class="search-city-btn"
              @click="handleSearchCity"
              :disabled="citySearchStatus === 'searching'"
            >
              <el-icon v-if="citySearchStatus === 'searching'"><Loading /></el-icon>
              <span v-else>查询</span>
            </button>
          </div>
          <div class="query-status" :class="citySearchStatus">
            <span v-if="citySearchStatus === 'searching'">
              <el-icon class="loading-icon"><Loading /></el-icon>
              {{ citySearchMessage }}
            </span>
            <span v-else-if="citySearchStatus === 'valid'" class="success">
              ✓ {{ citySearchMessage }}
            </span>
            <span v-else-if="citySearchStatus === 'invalid'" class="error">
              ✗ {{ citySearchMessage }}
            </span>
            <span v-else class="hint">
              下拉选择或输入城市名，停止输入后1秒自动查询
            </span>
          </div>
        </div>

        <div class="input-hint">
          已选: {{ localForm.birthPlace }} | 经度: {{ localForm.longitude.toFixed(2) }}° | 纬度: {{ localForm.latitude.toFixed(2) }}°
        </div>
      </div>
    </div>

    <div class="quick-cities">
      <span class="quick-label">常用城市:</span>
      <div class="city-buttons">
        <button 
          type="button" 
          class="city-btn"
          v-for="city in quickCities" 
          :key="city.id"
          @click="handleQuickCitySelect(city.id)"
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
        <div class="input-wrapper date-input-wrapper">
          <el-date-picker
            v-model="localForm.birthDate"
            type="date"
            placeholder="选择出生日期"
            format="YYYY年MM月DD日"
            value-format="YYYY-MM-DD"
            popper-class="astro-date-picker"
            class="astro-date-input"
          >
          </el-date-picker>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">
          <span class="label-icon"><el-icon><Clock /></el-icon></span>
          <span>出生时间</span>
        </label>
        <div class="input-wrapper time-input-wrapper">
          <el-time-picker
            v-model="localForm.birthTime"
            placeholder="选择出生时间"
            format="HH:mm"
            value-format="HH:mm"
            popper-class="astro-time-picker"
            class="astro-time-input"
          >
          </el-time-picker>
        </div>
      </div>
    </div>

    <div class="form-row" v-if="showManualCoords">
      <div class="form-group">
        <label class="form-label">
          <span class="label-icon">📍</span>
          <span>经度（手动）</span>
        </label>
        <div class="input-wrapper">
          <input 
            type="number" 
            step="0.01"
            v-model="localForm.longitude" 
            placeholder="如: 116.40 (北京)"
            class="astro-input"
          />
          <div class="input-border-effect"></div>
        </div>
        <div class="input-hint">东经为正，西经为负</div>
      </div>

      <div class="form-group">
        <label class="form-label">
          <span class="label-icon">📍</span>
          <span>纬度（手动）</span>
        </label>
        <div class="input-wrapper">
          <input 
            type="number" 
            step="0.01"
            v-model="localForm.latitude" 
            placeholder="如: 39.90 (北京)"
            class="astro-input"
          />
          <div class="input-border-effect"></div>
        </div>
        <div class="input-hint">北纬为正，南纬为负</div>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group full-width">
        <label class="form-label">
          <span class="label-icon"><el-icon><Setting /></el-icon></span>
          <span>宫位系统</span>
        </label>
        <div class="radio-group">
          <label 
            class="radio-item"
            :class="{ active: localForm.houseSystem === 'placidus' }"
            @click="localForm.houseSystem = 'placidus'"
          >
            <span class="radio-circle"></span>
            <span class="radio-label">普拉西度分宫制 (Placidus)</span>
            <span class="radio-desc">最常用的宫位系统，根据经纬度精确计算</span>
          </label>
          <label 
            class="radio-item"
            :class="{ active: localForm.houseSystem === 'whole_sign' }"
            @click="localForm.houseSystem = 'whole_sign'"
          >
            <span class="radio-circle"></span>
            <span class="radio-label">整宫制 (Whole Sign)</span>
            <span class="radio-desc">每个星座完整对应一个宫位，传统占星常用</span>
          </label>
        </div>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <button
          type="button"
          class="toggle-manual-btn"
          @click="showManualCoords = !showManualCoords"
        >
          <el-icon><Setting /></el-icon>
          {{ showManualCoords ? '隐藏手动坐标' : '手动设置经纬度' }}
        </button>
      </div>
    </div>
  </form>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useCitySearch, CITIES_DB, QUICK_CITIES } from '@/composables'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const {
  cityInput,
  queryStatus: citySearchStatus,
  queryMessage: citySearchMessage,
  showManualCoords,
  majorCities,
  queryCitySuggestions,
  searchCityByName,
  onCitySelect,
  onCityInput,
  selectCityById
} = useCitySearch()

const quickCities = computed(() => QUICK_CITIES)

const localForm = reactive({
  name: props.modelValue.name || '',
  birthDate: props.modelValue.birthDate || '1990-01-01',
  birthTime: props.modelValue.birthTime || '12:00',
  birthPlace: props.modelValue.birthPlace || '北京',
  longitude: props.modelValue.longitude || 116.4074,
  latitude: props.modelValue.latitude || 39.9042,
  houseSystem: props.modelValue.houseSystem || 'placidus'
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      Object.assign(localForm, {
        name: newVal.name || '',
        birthDate: newVal.birthDate || '1990-01-01',
        birthTime: newVal.birthTime || '12:00',
        birthPlace: newVal.birthPlace || '北京',
        longitude: newVal.longitude || 116.4074,
        latitude: newVal.latitude || 39.9042,
        houseSystem: newVal.houseSystem || 'placidus'
      })
    }
  },
  { deep: true }
)

watch(
  localForm,
  (newVal) => {
    emit('update:modelValue', { ...newVal })
  },
  { deep: true }
)

function handleCitySelect(item) {
  const result = onCitySelect(item)
  if (result) {
    localForm.birthPlace = result.birthPlace
    localForm.latitude = result.latitude
    localForm.longitude = result.longitude
  }
}

function handleCityInput(value) {
  onCityInput(value)
}

async function handleSearchCity() {
  const city = await searchCityByName(cityInput.value)
  if (city) {
    localForm.birthPlace = city.name
    localForm.latitude = city.latitude
    localForm.longitude = city.longitude
  }
}

function handleQuickCitySelect(cityId) {
  const result = selectCityById(cityId)
  if (result) {
    cityInput.value = result.birthPlace
    localForm.birthPlace = result.birthPlace
    localForm.latitude = result.latitude
    localForm.longitude = result.longitude
  }
}
</script>

<style lang="scss" scoped>
.astro-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 12px;
  }
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  &.full-width {
    flex: 0 0 100%;
  }
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.85rem;
  font-weight: 500;
}

.label-icon {
  color: #a78bfa;
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.input-wrapper {
  position: relative;
}

.astro-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 10px;
  color: #fff;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  outline: none;
  box-sizing: border-box;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.35);
  }
  
  &:focus {
    border-color: rgba(139, 92, 246, 0.7);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.2), inset 0 0 15px rgba(139, 92, 246, 0.03);
  }
  
  &:hover:not(:focus) {
    border-color: rgba(139, 92, 246, 0.4);
  }
}

.input-border-effect {
  position: absolute;
  bottom: 1px;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #8b5cf6, #3b82f6);
  transition: all 0.3s ease;
  transform: translateX(-50%);
  border-radius: 0 0 10px 10px;
  pointer-events: none;
}

.input-wrapper:focus-within .input-border-effect {
  width: calc(100% - 2px);
}

.input-hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.city-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.city-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.autocomplete-wrapper {
  flex: 1;
}

.city-autocomplete {
  width: 100%;
  
  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.5);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 10px;
    box-shadow: none;
    padding: 0 16px;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4);
    }
    
    &.is-focus {
      border-color: rgba(139, 92, 246, 0.7);
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.2);
    }
  }
  
  :deep(.el-input__inner) {
    color: #fff;
    font-size: 0.9rem;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.35);
    }
  }
}

.search-city-btn {
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.3));
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 10px;
  color: #c4b5fd;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.5), rgba(99, 102, 241, 0.5));
    border-color: rgba(139, 92, 246, 0.6);
    color: #ddd6fe;
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.query-status {
  font-size: 0.75rem;
  padding: 4px 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  
  &.searching {
    color: #fbbf24;
    background: rgba(251, 191, 36, 0.1);
  }
  
  &.valid {
    color: #34d399;
    background: rgba(52, 211, 153, 0.1);
    
    .success {
      color: #34d399;
    }
  }
  
  &.invalid {
    color: #f87171;
    background: rgba(248, 113, 113, 0.1);
    
    .error {
      color: #f87171;
    }
  }
  
  &:not(.searching):not(.valid):not(.invalid) {
    color: rgba(255, 255, 255, 0.4);
  }
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.quick-cities {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.quick-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.city-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.city-btn {
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 6px;
  color: #c4b5fd;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.3);
    border-color: rgba(139, 92, 246, 0.5);
    color: #ddd6fe;
  }
}

.date-input-wrapper,
.time-input-wrapper {
  width: 100%;
  
  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.5);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 10px;
    box-shadow: none;
    padding: 0 16px;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4);
    }
    
    &.is-focus {
      border-color: rgba(139, 92, 246, 0.7);
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.2);
    }
  }
  
  :deep(.el-input__inner) {
    color: #fff;
    font-size: 0.9rem;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.35);
    }
  }
  
  :deep(.el-input__icon) {
    color: #a78bfa;
  }
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(30, 30, 60, 0.3);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.35);
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.6);
    
    .radio-circle {
      background: linear-gradient(135deg, #8b5cf6, #3b82f6);
      border-color: #8b5cf6;
      
      &::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 6px;
        height: 6px;
        background: #fff;
        border-radius: 50%;
      }
    }
    
    .radio-label {
      color: #ddd6fe;
      font-weight: 600;
    }
  }
}

.radio-circle {
  position: relative;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(139, 92, 246, 0.4);
  border-radius: 50%;
  margin-top: 2px;
  transition: all 0.3s ease;
}

.radio-label {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9rem;
  font-weight: 500;
}

.radio-desc {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.75rem;
  margin-top: 2px;
}

.toggle-manual-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: 1px dashed rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: rgba(167, 139, 250, 0.8);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.6);
    color: #a78bfa;
    background: rgba(139, 92, 246, 0.1);
  }
}

:deep(.option-content) {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

:deep(.option-name) {
  font-size: 0.9rem;
  font-weight: 500;
  color: #1f2937;
}

:deep(.option-en) {
  font-size: 0.75rem;
  color: #6b7280;
  margin-left: 6px;
}

:deep(.option-location) {
  font-size: 0.75rem;
  color: #9ca3af;
}
</style>
