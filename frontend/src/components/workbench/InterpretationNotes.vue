<template>
  <div class="interpretation-notes">
    <div class="notes-header">
      <div class="notes-title">
        <span class="notes-icon">📝</span>
        <span class="title-text">解盘笔记</span>
      </div>
      <div class="notes-actions">
        <button 
          class="action-btn" 
          @click="regenerateNotes"
          :disabled="isGenerating"
        >
          <span v-if="isGenerating">生成中...</span>
          <span v-else>重新生成</span>
        </button>
        <button class="action-btn secondary" @click="exportNotes">
          导出
        </button>
      </div>
    </div>
    
    <div v-if="!notesData" class="notes-empty">
      <div class="empty-icon">📋</div>
      <div class="empty-text">
        <p>计算星盘后自动生成解盘笔记</p>
        <button class="generate-btn" @click="$emit('request-notes')">
          生成草稿
        </button>
      </div>
    </div>
    
    <div v-else class="notes-content">
      <div class="notes-section executive-section">
        <div class="section-header">
          <span class="section-icon">📊</span>
          <span class="section-title">执行摘要</span>
          <button class="edit-toggle" @click="toggleEdit('executive_summary')">
            {{ editModes.executive_summary ? '完成' : '编辑' }}
          </button>
        </div>
        <div class="section-content">
          <textarea
            v-if="editModes.executive_summary"
            v-model="editableNotes.executive_summary"
            class="edit-textarea"
            rows="3"
          ></textarea>
          <p v-else class="summary-text">
            {{ notesData.executive_summary || '暂无摘要' }}
          </p>
        </div>
      </div>
      
      <div class="notes-section planets-section">
        <div class="section-header">
          <span class="section-icon">🌍</span>
          <span class="section-title">行星分析</span>
          <span class="count-badge">{{ notesData.planets_analysis?.length || 0 }}</span>
        </div>
        <div class="planets-list">
          <div 
            v-for="(planet, index) in sortedPlanets" 
            :key="index"
            class="planet-note"
            :class="{ 'expanded': expandedPlanets.includes(planet.planet) }"
          >
            <div class="planet-header" @click="togglePlanet(planet.planet)">
              <span class="expand-icon">{{ expandedPlanets.includes(planet.planet) ? '▼' : '▶' }}</span>
              <span class="planet-sym">{{ getPlanetSymbol(planet.planet) }}</span>
              <span class="planet-name">{{ planet.planet }}</span>
              <span class="planet-sign">{{ planet.sign }} 第{{ planet.house }}宫</span>
              <span v-if="planet.dignity_notes?.length > 0" class="dignity-indicator">
                ⭐
              </span>
            </div>
            <div v-if="expandedPlanets.includes(planet.planet)" class="planet-details">
              <div v-if="planet.dignity_notes?.length > 0" class="dignity-notes">
                <div class="detail-label">庙旺弱陷:</div>
                <ul class="detail-list">
                  <li v-for="(note, idx) in planet.dignity_notes" :key="idx">
                    {{ note }}
                  </li>
                </ul>
              </div>
              <div class="antiscia-note">
                <span class="detail-label">映点:</span>
                <span>{{ planet.antiscia_note }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="notesData.aspects_analysis?.length > 0" class="notes-section aspects-section">
        <div class="section-header">
          <span class="section-icon">🔗</span>
          <span class="section-title">相位分析</span>
          <span class="count-badge">{{ notesData.aspects_analysis?.length || 0 }}</span>
        </div>
        <div class="aspects-list">
          <div 
            v-for="(aspect, index) in notesData.aspects_analysis" 
            :key="index"
            class="aspect-note"
            :class="aspect.nature?.toLowerCase() || 'neutral'"
          >
            <div class="aspect-main">
              <span class="aspect-planets">{{ aspect.planets }}</span>
              <span class="aspect-type">{{ aspect.aspect_type }}</span>
            </div>
            <div class="aspect-meta">
              <span class="aspect-nature" :class="aspect.nature?.toLowerCase()">
                {{ aspect.nature }}
              </span>
              <span class="aspect-orb">容许度: {{ aspect.orb }}°</span>
              <span class="aspect-applying">{{ aspect.applying }}</span>
            </div>
            <p class="aspect-interpretation">{{ aspect.interpretation }}</p>
          </div>
        </div>
      </div>
      
      <div v-if="notesData.receptions_analysis?.length > 0" class="notes-section receptions-section">
        <div class="section-header">
          <span class="section-icon">🤝</span>
          <span class="section-title">接纳与互容</span>
          <span class="count-badge">{{ notesData.receptions_analysis?.length || 0 }}</span>
        </div>
        <div class="receptions-list">
          <div 
            v-for="(reception, index) in notesData.receptions_analysis" 
            :key="index"
            class="reception-note"
            :class="{ 'mutual': reception.type === '互容' }"
          >
            <div class="reception-header">
              <span class="reception-type-badge">{{ reception.type }}</span>
              <span class="reception-planets">{{ reception.planets }}</span>
            </div>
            <p class="reception-desc">{{ reception.description }}</p>
            <div class="strength-bar">
              <div 
                class="strength-fill" 
                :style="{ width: (reception.strength || 0.5) * 100 + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="notesData.special_indicators?.length > 0" class="notes-section special-section">
        <div class="section-header">
          <span class="section-icon">✨</span>
          <span class="section-title">特殊征象</span>
          <span class="count-badge">{{ notesData.special_indicators?.length || 0 }}</span>
        </div>
        <div class="special-list">
          <div 
            v-for="(indicator, index) in notesData.special_indicators" 
            :key="index"
            class="special-note"
            :class="indicator.type?.toLowerCase().replace(/\s/g, '-')"
          >
            <span class="special-type">{{ indicator.type }}:</span>
            <span class="special-desc">{{ indicator.description }}</span>
          </div>
        </div>
      </div>
      
      <div v-if="notesData.key_themes?.length > 0" class="notes-section themes-section">
        <div class="section-header">
          <span class="section-icon">🎯</span>
          <span class="section-title">核心主题</span>
        </div>
        <div class="themes-tags">
          <span 
            v-for="(theme, index) in notesData.key_themes" 
            :key="index"
            class="theme-tag"
          >
            {{ theme }}
          </span>
        </div>
      </div>
      
      <div class="notes-section freeform-section">
        <div class="section-header">
          <span class="section-icon">✏️</span>
          <span class="section-title">自由笔记</span>
        </div>
        <textarea
          v-model="freeNotes"
          class="free-textarea"
          placeholder="在此添加您的专业解盘笔记..."
          rows="8"
        ></textarea>
      </div>
    </div>
    
    <div class="notes-footer">
      <div class="footer-info">
        <span class="generated-at">
          生成时间: {{ formatTime(generatedAt) }}
        </span>
      </div>
      <div class="footer-actions">
        <button class="footer-btn" @click="copyNotes">
          复制全部
        </button>
        <button class="footer-btn primary" @click="saveNotes">
          保存笔记
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  notesData: {
    type: Object,
    default: null
  },
  isGenerating: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['request-notes', 'save-notes'])

const editModes = ref({
  executive_summary: false
})

const editableNotes = ref({
  executive_summary: ''
})

const expandedPlanets = ref([])
const freeNotes = ref('')
const generatedAt = ref(null)

const sortedPlanets = computed(() => {
  if (!props.notesData?.planets_analysis) return []
  const order = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']
  return [...props.notesData.planets_analysis].sort((a, b) => {
    return order.indexOf(a.planet) - order.indexOf(b.planet)
  })
})

const planetSymbols = {
  '太阳': '☉',
  '月亮': '☽',
  '水星': '☿',
  '金星': '♀',
  '火星': '♂',
  '木星': '♃',
  '土星': '♄',
  '天王星': '♅',
  '海王星': '♆',
  '冥王星': '♇'
}

watch(() => props.notesData, (newData) => {
  if (newData) {
    editableNotes.value.executive_summary = newData.executive_summary || ''
    generatedAt.value = new Date()
  }
}, { deep: true })

function getPlanetSymbol(name) {
  return planetSymbols[name] || '★'
}

function toggleEdit(field) {
  editModes.value[field] = !editModes.value[field]
}

function togglePlanet(planetName) {
  const index = expandedPlanets.value.indexOf(planetName)
  if (index > -1) {
    expandedPlanets.value.splice(index, 1)
  } else {
    expandedPlanets.value.push(planetName)
  }
}

function regenerateNotes() {
  emit('request-notes')
}

function formatTime(date) {
  if (!date) return '未知'
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

function exportNotes() {
  if (!props.notesData) return
  
  let text = `【解盘笔记】
================

执行摘要：
${editableNotes.value.executive_summary || props.notesData.executive_summary || ''}

行星分析：
${sortedPlanets.value.map(p => `
${p.planet} ${p.sign} 第${p.house}宫
${p.dignity_notes?.join('\n') || ''}
`).join('')}

自由笔记：
${freeNotes.value || '无'}
`
  
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `解盘笔记_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

function copyNotes() {
  if (!props.notesData) return
  
  let text = `【解盘笔记】

执行摘要：
${editableNotes.value.executive_summary || props.notesData.executive_summary || ''}

自由笔记：
${freeNotes.value || '无'}
`
  
  navigator.clipboard.writeText(text).then(() => {
    alert('已复制到剪贴板')
  })
}

function saveNotes() {
  const saveData = {
    ...props.notesData,
    edited_summary: editableNotes.value.executive_summary,
    free_notes: freeNotes.value,
    saved_at: new Date().toISOString()
  }
  emit('save-notes', saveData)
}
</script>

<style scoped>
.interpretation-notes {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(12, 12, 28, 0.95);
  border-radius: 12px;
  border: 1px solid rgba(147, 112, 219, 0.2);
  overflow: hidden;
}

.notes-header {
  padding: 16px;
  border-bottom: 1px solid rgba(147, 112, 219, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notes-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notes-icon {
  font-size: 1.2rem;
}

.title-text {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.notes-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  background: rgba(147, 112, 219, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.3);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: rgba(147, 112, 219, 0.3);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.secondary {
  background: rgba(100, 100, 120, 0.2);
  border-color: rgba(100, 100, 120, 0.3);
}

.notes-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.4);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text p {
  margin: 4px 0 16px;
  font-size: 0.85rem;
  text-align: center;
}

.generate-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #9370db, #7c3aed);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.generate-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(147, 112, 219, 0.4);
}

.notes-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.notes-section {
  margin-bottom: 16px;
  background: rgba(147, 112, 219, 0.05);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid rgba(147, 112, 219, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.section-icon {
  font-size: 1rem;
}

.section-title {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.85rem;
}

.count-badge {
  margin-left: auto;
  padding: 2px 8px;
  background: rgba(147, 112, 219, 0.2);
  border-radius: 10px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.edit-toggle {
  margin-left: 8px;
  padding: 2px 8px;
  background: rgba(147, 112, 219, 0.15);
  border: 1px solid rgba(147, 112, 219, 0.2);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.7rem;
  cursor: pointer;
}

.edit-toggle:hover {
  background: rgba(147, 112, 219, 0.25);
}

.section-content {
  padding: 8px;
  background: rgba(147, 112, 219, 0.08);
  border-radius: 6px;
}

.edit-textarea {
  width: 100%;
  min-height: 60px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.2);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.8rem;
  line-height: 1.5;
  resize: vertical;
}

.summary-text {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.6;
  margin: 0;
}

.planets-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.planet-note {
  background: rgba(147, 112, 219, 0.06);
  border-radius: 6px;
  overflow: hidden;
}

.planet-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.planet-header:hover {
  background: rgba(147, 112, 219, 0.1);
}

.expand-icon {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.4);
  width: 10px;
}

.planet-sym {
  font-size: 1rem;
}

.planet-name {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.planet-sign {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 8px;
}

.dignity-indicator {
  margin-left: auto;
  font-size: 0.8rem;
}

.planet-details {
  padding: 8px 12px 12px;
  border-top: 1px solid rgba(147, 112, 219, 0.1);
  background: rgba(0, 0, 0, 0.1);
}

.dignity-notes {
  margin-bottom: 8px;
}

.detail-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-right: 4px;
}

.detail-list {
  margin: 4px 0 0 16px;
  padding: 0;
}

.detail-list li {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
}

.antiscia-note {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-note {
  padding: 10px 12px;
  background: rgba(147, 112, 219, 0.06);
  border-radius: 6px;
  border-left: 3px solid rgba(147, 112, 219, 0.3);
}

.aspect-note.harmonious {
  border-left-color: #22c55e;
}

.aspect-note.challenging {
  border-left-color: #ef4444;
}

.aspect-main {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.aspect-planets {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.aspect-type {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.aspect-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
}

.aspect-nature {
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: 8px;
}

.aspect-nature.harmonious {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.aspect-nature.challenging {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.aspect-nature.neutral {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.aspect-orb,
.aspect-applying {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
}

.aspect-interpretation {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.4;
  margin: 0;
}

.receptions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reception-note {
  padding: 10px 12px;
  background: rgba(147, 112, 219, 0.06);
  border-radius: 6px;
  border: 1px solid rgba(147, 112, 219, 0.15);
}

.reception-note.mutual {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.05);
}

.reception-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.reception-type-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  background: rgba(147, 112, 219, 0.2);
  color: #a78bfa;
}

.reception-note.mutual .reception-type-badge {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.reception-planets {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.reception-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.4;
  margin: 0 0 8px;
}

.strength-bar {
  height: 4px;
  background: rgba(147, 112, 219, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  background: linear-gradient(90deg, #9370db, #a78bfa);
}

.special-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.special-note {
  padding: 8px 10px;
  background: rgba(147, 112, 219, 0.06);
  border-radius: 6px;
  font-size: 0.75rem;
}

.special-type {
  color: #9370db;
  font-weight: 500;
  margin-right: 6px;
}

.special-desc {
  color: rgba(255, 255, 255, 0.65);
}

.themes-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.theme-tag {
  padding: 4px 12px;
  background: rgba(147, 112, 219, 0.15);
  border: 1px solid rgba(147, 112, 219, 0.25);
  border-radius: 16px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.free-textarea {
  width: 100%;
  min-height: 120px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(147, 112, 219, 0.2);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.8rem;
  line-height: 1.5;
  resize: vertical;
}

.free-textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.notes-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(147, 112, 219, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-info {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.footer-btn {
  padding: 6px 14px;
  background: rgba(100, 100, 120, 0.2);
  border: 1px solid rgba(100, 100, 120, 0.3);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.footer-btn:hover {
  background: rgba(100, 100, 120, 0.3);
}

.footer-btn.primary {
  background: linear-gradient(135deg, #9370db, #7c3aed);
  border-color: transparent;
  color: white;
}

.footer-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(147, 112, 219, 0.4);
}

::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: rgba(147, 112, 219, 0.05);
}

::-webkit-scrollbar-thumb {
  background: rgba(147, 112, 219, 0.2);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(147, 112, 219, 0.3);
}
</style>
