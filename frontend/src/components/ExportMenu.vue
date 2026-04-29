<template>
  <div class="export-dropdown" :class="{ open: isOpen }">
    <button 
      type="button" 
      class="export-btn primary"
      :class="{ 'btn-loading': isExporting }"
      @click="toggleMenu"
      :disabled="isExporting"
    >
      <el-icon v-if="isExporting"><Loading /></el-icon>
      <el-icon v-else><Download /></el-icon>
      <span>{{ isExporting ? '导出中...' : '导出' }}</span>
      <el-icon class="caret"><CaretBottom /></el-icon>
    </button>
    
    <div v-if="isOpen" class="export-menu" @click.stop>
      <div class="export-section">
        <div class="section-label">导出图片</div>
        <button 
          type="button"
          class="export-action-btn"
          v-for="format in imageFormats"
          :key="format.id"
          :disabled="isExporting"
          @click="handleExportImage(format)"
        >
          <span class="format-name">{{ format.name }}</span>
          <span class="format-desc">{{ format.description }}</span>
        </button>
      </div>
      
      <div class="export-divider"></div>
      
      <div class="export-section">
        <div class="section-label">导出 PDF 报告</div>
        <button 
          type="button"
          class="export-action-btn"
          v-for="template in pdfTemplates"
          :key="template.id"
          :disabled="isExporting"
          @click="handleExportPDF(template.id)"
        >
          <span class="format-name">{{ template.name }}</span>
          <span class="format-desc">{{ template.description }}</span>
        </button>
      </div>
    </div>
    
    <div 
      v-if="isOpen" 
      class="export-overlay"
      @click="closeMenu"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Download, CaretBottom, Loading } from '@element-plus/icons-vue'

const props = defineProps({
  isExporting: {
    type: Boolean,
    default: false
  },
  selectedImageFormat: {
    type: String,
    default: 'png_hd'
  },
  selectedPdfTemplate: {
    type: String,
    default: 'detailed'
  }
})

const emit = defineEmits(['export-image', 'export-pdf', 'update:selectedImageFormat', 'update:selectedPdfTemplate'])

const isOpen = ref(false)

const imageFormats = computed(() => [
  { id: 'png_hd', name: '高清 PNG', format: 'png', scale: 3, description: '3倍分辨率' },
  { id: 'png_standard', name: '标准 PNG', format: 'png', scale: 2, description: '2倍分辨率' },
  { id: 'jpg_hd', name: '高清 JPG', format: 'jpg', scale: 3, description: '高画质' }
])

const pdfTemplates = computed(() => [
  { id: 'detailed', name: '详细版', description: '包含完整解读' },
  { id: 'simple', name: '简洁版', description: '快速概览' }
])

function toggleMenu() {
  isOpen.value = !isOpen.value
}

function closeMenu() {
  isOpen.value = false
}

function handleExportImage(format) {
  emit('update:selectedImageFormat', format.id)
  emit('export-image', format)
  closeMenu()
}

function handleExportPDF(templateId) {
  emit('update:selectedPdfTemplate', templateId)
  emit('export-pdf', templateId)
  closeMenu()
}
</script>

<style lang="scss" scoped>
.export-dropdown {
  position: relative;
}

.export-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid transparent;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &.primary {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%);
    color: #fff;
    
    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
    }
  }
  
  &.btn-loading {
    cursor: not-allowed;
    opacity: 0.85;
  }
  
  &:disabled {
    cursor: not-allowed;
  }
  
  .caret {
    transition: transform 0.2s ease;
  }
}

.export-dropdown.open .export-btn .caret {
  transform: rotate(180deg);
}

.export-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
}

.export-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: rgba(20, 20, 40, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 60px rgba(139, 92, 246, 0.1);
  padding: 8px;
  z-index: 1000;
  animation: menuSlideDown 0.2s ease;
}

@keyframes menuSlideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.export-section {
  padding: 4px 0;
}

.section-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(167, 139, 250, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 12px 6px;
}

.export-action-btn {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  
  &:hover:not(:disabled) {
    background: rgba(139, 92, 246, 0.15);
  }
  
  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
}

.format-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.format-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.45);
}

.export-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.3), transparent);
  margin: 4px 8px;
}
</style>
