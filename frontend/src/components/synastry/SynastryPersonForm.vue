<template>
  <div class="person-card" :style="{ borderTopColor: color }">
    <div class="card-header">
      <span class="person-label">{{ label }}</span>
      <span class="person-dot" :style="{ background: color }"></span>
    </div>
    <form class="person-form">
      <div class="form-group">
        <label class="form-label">姓名</label>
        <input 
          type="text" 
          v-model="person.name" 
          placeholder="请输入姓名"
          class="form-input"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">出生日期</label>
          <el-date-picker
            v-model="person.birthDate"
            type="date"
            placeholder="选择日期"
            format="YYYY年MM月DD日"
            value-format="YYYY-MM-DD"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label">出生时间</label>
          <el-time-picker
            v-model="person.birthTime"
            placeholder="选择时间"
            format="HH:mm"
            value-format="HH:mm"
            class="form-input"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">出生城市</label>
        <el-autocomplete
          v-model="person.cityInput"
          :fetch-suggestions="queryCitySuggestions"
          :trigger-on-focus="true"
          :clearable="true"
          @select="onCitySelect"
          placeholder="输入城市名称"
          class="form-input"
        >
          <template #default="{ item }">
            <div class="option-content">
              <span class="option-name">{{ item.name }}</span>
              <span class="option-location">{{ item.country }}</span>
            </div>
          </template>
        </el-autocomplete>
      </div>

      <div class="quick-cities">
        <button 
          v-for="city in quickCities" 
          :key="city.id"
          type="button" 
          class="city-btn"
          @click="selectQuickCity(city.id)"
        >
          {{ city.name }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
const props = defineProps({
  person: {
    type: Object,
    required: true
  },
  label: {
    type: String,
    default: '人物信息'
  },
  color: {
    type: String,
    default: '#8b5cf6'
  },
  cities: {
    type: Array,
    default: () => []
  },
  quickCities: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:person'])

function queryCitySuggestions(queryString, callback) {
  if (!queryString || queryString.trim().length === 0) {
    callback(props.cities.slice(0, 15))
    return
  }
  
  const q = queryString.toLowerCase()
  const results = props.cities.filter(city => 
    city.name.includes(queryString) || 
    city.name.toLowerCase().includes(q)
  )
  
  callback(results.slice(0, 15))
}

function onCitySelect(item) {
  emit('update:person', {
    ...props.person,
    cityInput: item.name,
    birthPlace: item.name,
    latitude: item.latitude,
    longitude: item.longitude
  })
}

function selectQuickCity(cityId) {
  const city = props.cities.find(c => c.id === cityId)
  if (city) {
    emit('update:person', {
      ...props.person,
      cityInput: city.name,
      birthPlace: city.name,
      latitude: city.latitude,
      longitude: city.longitude
    })
  }
}
</script>

<style lang="scss" scoped>
.person-card {
  background: rgba(12, 12, 28, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 12px;
  padding: 16px;
  border-top: 2px solid;
  position: relative;
  z-index: 10;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.1);
}

.person-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.person-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.person-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(20, 20, 40, 0.8);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: rgba(139, 92, 246, 0.5);
    background: rgba(20, 20, 50, 0.9);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }
}

.quick-cities {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 4px;
}

.city-btn {
  padding: 4px 10px;
  background: rgba(80, 60, 160, 0.1);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: rgba(255, 255, 255, 0.7);
  }
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-name {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
}

.option-location {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}
</style>
