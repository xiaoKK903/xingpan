<template>
  <div class="zodiac-selector">
    <div class="selector-header">
      <span class="selector-label">选择星座</span>
      <span class="current-sign" v-if="currentSignInfo">
        {{ currentSignInfo.symbol }} {{ currentSignInfo.name }}
      </span>
    </div>
    <div class="zodiac-grid">
      <div 
        v-for="sign in zodiacSigns" 
        :key="sign.index"
        class="zodiac-item"
        :class="{ active: isSelected(sign.name) }"
        @click="selectSign(sign.name)"
      >
        <span class="zodiac-symbol" :style="{ color: sign.color }">
          {{ sign.symbol }}
        </span>
        <span class="zodiac-name">{{ sign.name }}</span>
        <span class="zodiac-dates">{{ sign.date_range.split(' - ')[0] }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '白羊座'
  },
  zodiacSigns: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const currentSignInfo = computed(() => {
  return props.zodiacSigns.find(s => s.name === props.modelValue) || null
})

function isSelected(signName) {
  return props.modelValue === signName
}

function selectSign(signName) {
  if (props.modelValue !== signName) {
    emit('update:modelValue', signName)
    emit('change', signName)
  }
}
</script>

<style lang="scss" scoped>
.zodiac-selector {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.selector-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

.current-sign {
  font-size: 14px;
  color: #a78bfa;
  font-weight: 500;
}

.zodiac-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.zodiac-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 10px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.zodiac-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.zodiac-item:hover::before {
  opacity: 1;
}

.zodiac-item:hover {
  border-color: rgba(139, 92, 246, 0.3);
  transform: translateY(-2px);
}

.zodiac-item.active {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.2);
}

.zodiac-symbol {
  font-size: 28px;
  margin-bottom: 6px;
  transition: transform 0.3s ease;
}

.zodiac-item:hover .zodiac-symbol {
  transform: scale(1.1);
}

.zodiac-name {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 2px;
}

.zodiac-item.active .zodiac-name {
  color: #a78bfa;
  font-weight: 600;
}

.zodiac-dates {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 768px) {
  .zodiac-selector {
    padding: 16px;
  }

  .zodiac-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
  }

  .zodiac-item {
    padding: 12px 8px;
  }

  .zodiac-symbol {
    font-size: 24px;
  }

  .zodiac-name {
    font-size: 12px;
  }

  .zodiac-dates {
    display: none;
  }
}

@media (max-width: 480px) {
  .zodiac-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
