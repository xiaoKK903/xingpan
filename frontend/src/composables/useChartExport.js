import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { reportApi, chartApi } from '@/api'
import { exportAsPNG, exportAsJPG, generateChartFilename, downloadBlob } from '@/utils/exportUtils'
import { nextTick } from 'vue'

export const EXPORT_FORMATS_CONFIG = [
  { id: 'png_hd', name: '高清 PNG', format: 'png', scale: 3, description: '3倍分辨率' },
  { id: 'png_standard', name: '标准 PNG', format: 'png', scale: 2, description: '2倍分辨率' },
  { id: 'jpg_hd', name: '高清 JPG', format: 'jpg', scale: 3, description: '高画质' }
]

export const REPORT_TEMPLATES_CONFIG = [
  { id: 'detailed', name: '详细版', description: '包含完整解读' },
  { id: 'simple', name: '简洁版', description: '快速概览' }
]

export function useChartExport() {
  const exporting = ref(false)
  const showExportMenu = ref(false)
  const selectedExportFormat = ref('png_hd')
  const selectedReportTemplate = ref('detailed')
  
  const exportFormats = computed(() => EXPORT_FORMATS_CONFIG)
  const reportTemplates = computed(() => REPORT_TEMPLATES_CONFIG)
  
  function toggleExportMenu() {
    showExportMenu.value = !showExportMenu.value
  }
  
  async function exportChartAsImage({
    chartData,
    astroForm,
    selector = '.chart-wheel-wrapper'
  }) {
    if (!chartData) {
      ElMessage.warning('请先计算星盘')
      return
    }
    
    exporting.value = true
    
    try {
      await nextTick()
      
      const chartContainer = document.querySelector(selector)
      if (!chartContainer) {
        ElMessage.error('未找到星盘元素')
        return
      }
      
      const formatInfo = exportFormats.value.find(f => f.id === selectedExportFormat.value)
      const format = formatInfo || exportFormats.value[0]
      
      const chartDataForFilename = {
        name: astroForm?.name || '星盘',
        input: {
          date: astroForm?.birthDate
        }
      }
      const filename = generateChartFilename(chartDataForFilename, format.format)
      
      if (format.format === 'jpg') {
        await exportAsJPG(chartContainer, filename, 0.9, { scale: format.scale })
      } else {
        await exportAsPNG(chartContainer, filename, { scale: format.scale })
      }
      
      ElMessage.success(`已导出: ${filename}`)
    } catch (error) {
      console.error('导出图片失败:', error)
      ElMessage.error('导出图片失败: ' + error.message)
    } finally {
      exporting.value = false
      showExportMenu.value = false
    }
  }
  
  async function exportChartAsPDF({
    chartData,
    astroForm,
    selectedChartId,
    isLoggedIn
  }) {
    if (!chartData) {
      ElMessage.warning('请先计算星盘')
      return
    }
    
    exporting.value = true
    
    try {
      let blob
      const templateName = selectedReportTemplate.value === 'detailed' ? '详细版' : '简洁版'
      const chartDataForFilename = {
        name: astroForm?.name || '星盘',
        birth_date: astroForm?.birthDate
      }
      const filename = generateChartFilename(chartDataForFilename, 'pdf').replace('.pdf', `_${templateName}.pdf`)
      
      if (isLoggedIn && selectedChartId) {
        blob = await reportApi.getPdfReport(selectedChartId, selectedReportTemplate.value)
      } else {
        const reportInput = {
          name: astroForm?.name || '星盘',
          birth_date: astroForm?.birthDate,
          birth_time: astroForm?.birthTime,
          latitude: astroForm?.latitude,
          longitude: astroForm?.longitude,
          birth_place: astroForm?.birthPlace || '',
          house_system: astroForm?.houseSystem
        }
        
        blob = await reportApi.generatePdfDirect(reportInput, selectedReportTemplate.value)
      }
      
      downloadBlob(blob, filename)
      ElMessage.success(`PDF 报告已导出: ${filename}`)
    } catch (error) {
      console.error('导出 PDF 失败:', error)
      ElMessage.error('导出 PDF 报告失败: ' + (error.message || '未知错误'))
    } finally {
      exporting.value = false
      showExportMenu.value = false
    }
  }
  
  async function exportSavedChartAsPDF({
    chartId,
    chartName,
    chartData,
    template = 'detailed'
  }) {
    if (!chartId) {
      ElMessage.warning('无法导出此星盘')
      return
    }
    
    exporting.value = true
    
    try {
      const blob = await reportApi.getPdfReport(chartId, template)
      
      const templateName = template === 'detailed' ? '详细版' : '简洁版'
      const chartDataForFilename = {
        name: chartName || '星盘',
        birth_date: chartData?.birth_date || ''
      }
      const filename = generateChartFilename(chartDataForFilename, 'pdf').replace('.pdf', `_${templateName}.pdf`)
      
      downloadBlob(blob, filename)
      ElMessage.success(`PDF 报告已导出: ${filename}`)
    } catch (error) {
      console.error('导出 PDF 失败:', error)
      ElMessage.error('导出 PDF 报告失败: ' + error.message)
    } finally {
      exporting.value = false
      showExportMenu.value = false
    }
  }
  
  return {
    exporting,
    showExportMenu,
    selectedExportFormat,
    selectedReportTemplate,
    exportFormats,
    reportTemplates,
    toggleExportMenu,
    exportChartAsImage,
    exportChartAsPDF,
    exportSavedChartAsPDF
  }
}

export default useChartExport
