<template>
  <div class="my-charts-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Document /></el-icon>
        我的星盘
      </h1>
      <p class="page-desc">查看和管理您的历史星盘记录</p>
    </div>

    <div class="feature-entrances">
      <div class="quest-entrance network-chain-entrance">
        <div class="entrance-content">
          <div class="entrance-icon">🌐</div>
          <div class="entrance-info">
            <h5>星盘人脉链</h5>
            <p>探索你的情绪价值人脉，发现与你能量共鸣的人</p>
          </div>
          <button class="entrance-btn network-chain-btn" @click="goToNetworkChain">
            发现人脉
            <span class="arrow">→</span>
          </button>
        </div>
      </div>
    </div>

    <div class="charts-container" v-loading="loading">
      <template v-if="charts.length > 0">
        <div class="charts-grid">
          <div 
            v-for="chart in charts" 
            :key="chart.id" 
            class="chart-card"
            @click="viewChart(chart)"
          >
            <div class="card-header">
              <div class="card-icon">
                <el-icon><Star /></el-icon>
              </div>
              <div class="card-info">
                <h3 class="card-name">{{ chart.name || '未命名星盘' }}</h3>
                <p class="card-date">{{ chart.birth_date }} {{ chart.birth_time }}</p>
              </div>
            </div>
            
            <div class="card-detail">
              <div class="detail-row" v-if="chart.birth_place">
                <span class="detail-label">出生地:</span>
                <span class="detail-value">{{ chart.birth_place }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">宫位系统:</span>
                <span class="detail-value">{{ chart.house_system === 'placidus' ? 'Placidus分宫制' : '整宫制' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">创建时间:</span>
                <span class="detail-value">{{ formatDate(chart.created_at) }}</span>
              </div>
            </div>

            <div class="card-actions" @click.stop>
              <el-button 
                size="small" 
                type="primary" 
                link
                @click="viewChart(chart)"
              >
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button 
                size="small" 
                type="success" 
                link
                @click="exportChartAsPDF(chart.id, chart.name, chart)"
                :loading="exporting"
              >
                <el-icon><Download /></el-icon>
                导出报告
              </el-button>
              <el-button 
                size="small" 
                type="warning" 
                link
                @click="editChart(chart)"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                link
                @click="deleteChart(chart)"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="empty-state">
        <el-icon class="empty-icon"><Star /></el-icon>
        <h3 class="empty-title">暂无星盘记录</h3>
        <p class="empty-desc">去星盘查询页面创建您的第一个星盘吧！</p>
        <el-button type="primary" @click="goToAstro">
          <el-icon><Plus /></el-icon>
          开始排盘
        </el-button>
      </div>
    </div>

    <el-dialog
      v-model="viewDialogVisible"
      title="星盘详情"
      width="90%"
      :fullscreen="$isMobile"
      custom-class="chart-detail-dialog"
    >
      <div v-if="selectedChart && selectedChart.chart_data" class="chart-detail-content">
        <div class="detail-header">
          <div class="detail-info">
            <h2>{{ selectedChart.name || '未命名星盘' }}</h2>
            <p>
              {{ selectedChart.birth_date }} {{ selectedChart.birth_time }}
              <span v-if="selectedChart.birth_place"> · {{ selectedChart.birth_place }}</span>
            </p>
            <p class="detail-system">
              宫位系统: {{ selectedChart.house_system === 'placidus' ? 'Placidus分宫制' : '整宫制' }}
            </p>
          </div>
          <div class="main-three">
            <div class="three-item">
              <div class="three-label">太阳</div>
              <div class="three-value">
                <span class="three-sign">{{ selectedChart.chart_data.sun_sign?.sign }}</span>
                <span class="three-degree">{{ selectedChart.chart_data.sun_sign?.dms?.formatted }}</span>
              </div>
            </div>
            <div class="three-item">
              <div class="three-label">月亮</div>
              <div class="three-value">
                <span class="three-sign">{{ selectedChart.chart_data.moon_sign?.sign }}</span>
                <span class="three-degree">{{ selectedChart.chart_data.moon_sign?.dms?.formatted }}</span>
              </div>
            </div>
            <div class="three-item">
              <div class="three-label">上升</div>
              <div class="three-value">
                <span class="three-sign">{{ selectedChart.chart_data.ascendant?.sign }}</span>
                <span class="three-degree">{{ selectedChart.chart_data.ascendant?.dms?.formatted }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-wheel">
          <ChartWheel :chartData="selectedChart.chart_data" :size="450" />
        </div>

        <div class="detail-tabs">
          <el-tabs v-model="activeTab" type="border-card">
            <el-tab-pane label="行星位置" name="planets">
              <div class="table-wrapper">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>行星</th>
                      <th>星座</th>
                      <th>度数</th>
                      <th>宫位</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="planet in selectedChart.chart_data.planets" :key="planet.name">
                      <td>
                        <span class="planet-symbol" :style="{ color: getPlanetColor(planet.name) }">
                          {{ getPlanetSymbol(planet.name) }}
                        </span>
                        {{ planet.name }}
                      </td>
                      <td>{{ planet.zodiac.sign }}</td>
                      <td>{{ planet.zodiac.dms.formatted }}</td>
                      <td>第{{ planet.house }}宫</td>
                      <td>
                        <span v-if="planet.is_retrograde" class="retro-badge">逆行</span>
                        <span v-else class="normal-badge">顺行</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </el-tab-pane>

            <el-tab-pane label="宫位信息" name="houses">
              <div class="houses-grid">
                <div 
                  v-for="(house, index) in selectedChart.chart_data.houses?.houses" 
                  :key="index"
                  class="house-item"
                >
                  <div class="house-number">第{{ index + 1 }}宫</div>
                  <div class="house-sign">{{ house.sign }}</div>
                  <div class="house-degree">{{ house.dms.formatted }}</div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="相位关系" name="aspects">
              <div class="table-wrapper">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>行星1</th>
                      <th>相位</th>
                      <th>行星2</th>
                      <th>容许度</th>
                      <th>类型</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(aspect, index) in selectedChart.chart_data.aspects" :key="index">
                      <td>
                        <span class="planet-symbol">{{ aspect.planet1_symbol }}</span>
                        {{ aspect.planet1 }}
                      </td>
                      <td>
                        <span class="aspect-symbol" :class="getAspectClass(aspect.aspect)">
                          {{ aspect.aspect_symbol }}
                        </span>
                        {{ aspect.aspect }}
                      </td>
                      <td>
                        <span class="planet-symbol">{{ aspect.planet2_symbol }}</span>
                        {{ aspect.planet2 }}
                      </td>
                      <td>{{ aspect.orb }}°</td>
                      <td>
                        <span :class="getAspectTypeClass(aspect.aspect)">
                          {{ getAspectType(aspect.aspect) }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑星盘"
      width="500px"
    >
      <el-form 
        :model="editForm" 
        label-width="80px"
        class="edit-form"
      >
        <el-form-item label="名称">
          <el-input v-model="editForm.name" placeholder="为这个星盘起个名字（可选）" />
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker
            v-model="editForm.birth_date"
            type="date"
            placeholder="选择出生日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="出生时间">
          <el-time-picker
            v-model="editForm.birth_time"
            placeholder="选择出生时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="出生地点">
          <el-input v-model="editForm.birth_place" placeholder="如：北京" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number 
            v-model="editForm.longitude" 
            :precision="6" 
            :step="0.01"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number 
            v-model="editForm.latitude" 
            :precision="6" 
            :step="0.01"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="宫位系统">
          <el-select v-model="editForm.house_system" style="width: 100%">
            <el-option label="Placidus 分宫制" value="placidus" />
            <el-option label="整宫制" value="whole_sign" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chartApi, reportApi } from '@/api'
import { useUserStore } from '@/stores/user'
import ChartWheel from '@/components/ChartWheel.vue'
import { downloadBlob, generateChartFilename } from '@/utils/exportUtils'
import { Download } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn || !!localStorage.getItem('token'))

const loading = ref(false)
const charts = ref([])

const viewDialogVisible = ref(false)
const editDialogVisible = ref(false)
const selectedChart = ref(null)
const activeTab = ref('planets')
const saving = ref(false)
const exporting = ref(false)
const showExportMenu = ref(false)
const selectedReportTemplate = ref('detailed')

const reportTemplates = [
  { id: 'detailed', name: '详细版', description: '包含完整解读' },
  { id: 'simple', name: '简洁版', description: '快速概览' }
]

const editForm = reactive({
  id: null,
  name: '',
  birth_date: '',
  birth_time: '',
  birth_place: '',
  longitude: 0,
  latitude: 0,
  house_system: 'placidus'
})

const planetColors = {
  '太阳': '#f97316',
  '月亮': '#60a5fa',
  '水星': '#eab308',
  '金星': '#ec4899',
  '火星': '#ef4444',
  '木星': '#f97316',
  '土星': '#8b5cf6',
  '天王星': '#06b6d4',
  '海王星': '#3b82f6',
  '冥王星': '#8b5cf6',
  '北交点': '#22c55e',
  '南交点': '#ef4444'
}

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
  '冥王星': '♇',
  '北交点': '☊',
  '南交点': '☋'
}

const harmoniousAspects = ['六分相', '三分相', '合相']

const aspectTypes = {
  '合相': '中性',
  '六分相': '和谐',
  '四分相': '挑战',
  '三分相': '和谐',
  '对分相': '挑战'
}

function getPlanetColor(name) {
  return planetColors[name] || '#8b5cf6'
}

function getPlanetSymbol(name) {
  return planetSymbols[name] || '★'
}

function getAspectType(aspect) {
  return aspectTypes[aspect] || '中性'
}

function getAspectTypeClass(aspect) {
  if (aspect === '六分相' || aspect === '三分相') return 'aspect-harmonious'
  if (aspect === '四分相' || aspect === '对分相') return 'aspect-challenging'
  return 'aspect-neutral'
}

function getAspectClass(aspect) {
  if (aspect === '六分相' || aspect === '三分相') return 'harmonious'
  if (aspect === '四分相' || aspect === '对分相') return 'challenging'
  return 'neutral'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

async function loadCharts() {
  loading.value = true
  try {
    const result = await chartApi.getMyCharts()
    charts.value = result?.charts || []
  } catch (error) {
    console.error('加载星盘失败:', error)
  } finally {
    loading.value = false
  }
}

async function viewChart(chart) {
  try {
    const result = await chartApi.getChartById(chart.id)
    selectedChart.value = result
    viewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载星盘详情失败')
  }
}

function editChart(chart) {
  editForm.id = chart.id
  editForm.name = chart.name || ''
  editForm.birth_date = chart.birth_date
  editForm.birth_time = chart.birth_time
  editForm.birth_place = chart.birth_place || ''
  editForm.longitude = chart.longitude
  editForm.latitude = chart.latitude
  editForm.house_system = chart.house_system
  
  editDialogVisible.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    await chartApi.updateChart(editForm.id, editForm)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadCharts()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteChart(chart) {
  try {
    await ElMessageBox.confirm('确定要删除这个星盘吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await chartApi.deleteChart(chart.id)
    ElMessage.success('删除成功')
    loadCharts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function exportChartAsPDF(chartId, chartName, chartData) {
  if (!chartId) {
    ElMessage.warning('无法导出此星盘')
    return
  }
  
  exporting.value = true
  
  try {
    const blob = await reportApi.getPdfReport(chartId, selectedReportTemplate.value)
    
    const templateName = selectedReportTemplate.value === 'detailed' ? '详细版' : '简洁版'
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

function toggleExportMenu() {
  showExportMenu.value = !showExportMenu.value
}

function goToAstro() {
  router.push('/astro')
}

function goToNetworkChain() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再查看星盘人脉链')
    router.push({ path: '/login', query: { redirect: '/network-chain' } })
    return
  }
  router.push('/network-chain')
}

onMounted(() => {
  loadCharts()
})
</script>

<style scoped>
.my-charts-page {
  padding: 24px;
  min-height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 8px 0;
}

.page-desc {
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  font-size: 0.9rem;
}

.charts-container {
  position: relative;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.chart-card {
  background: rgba(20, 20, 50, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.chart-card:hover {
  border-color: rgba(139, 92, 246, 0.4);
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.2));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
  font-size: 1.25rem;
}

.card-info h3 {
  margin: 0 0 4px 0;
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.card-date {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.card-detail {
  margin-bottom: 12px;
}

.detail-row {
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
  margin-bottom: 4px;
}

.detail-label {
  color: rgba(255, 255, 255, 0.4);
}

.detail-value {
  color: rgba(255, 255, 255, 0.7);
}

.card-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  color: rgba(139, 92, 246, 0.3);
  margin-bottom: 16px;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 8px 0;
}

.empty-desc {
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 20px 0;
}

.chart-detail-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #0a0a1a, #1a1a3e);
}

.chart-detail-content {
  padding: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.detail-info h2 {
  margin: 0 0 8px 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.detail-info p {
  margin: 0 0 4px 0;
  color: rgba(255, 255, 255, 0.6);
}

.detail-system {
  color: #a78bfa !important;
}

.main-three {
  display: flex;
  gap: 16px;
}

.three-item {
  text-align: center;
  padding: 12px 20px;
  background: rgba(20, 20, 50, 0.6);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.three-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.three-value {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.three-sign {
  font-size: 1.1rem;
  font-weight: 600;
  color: #a78bfa;
}

.three-degree {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.detail-wheel {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.detail-tabs {
  background: rgba(20, 20, 50, 0.4);
  border-radius: 12px;
  overflow: hidden;
}

:deep(.detail-tabs .el-tabs__header) {
  background: rgba(139, 92, 246, 0.1);
  margin: 0;
  padding: 0 16px;
}

:deep(.detail-tabs .el-tabs__item) {
  color: rgba(255, 255, 255, 0.5);
}

:deep(.detail-tabs .el-tabs__item.is-active) {
  color: #a78bfa;
}

:deep(.detail-tabs .el-tabs__content) {
  padding: 16px;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: rgba(139, 92, 246, 0.1);
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  font-size: 0.85rem;
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
}

.data-table tr:hover td {
  background: rgba(139, 92, 246, 0.05);
}

.planet-symbol {
  margin-right: 6px;
  font-weight: bold;
}

.retro-badge {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.normal-badge {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.aspect-symbol {
  margin-right: 6px;
  font-size: 1rem;
}

.aspect-symbol.harmonious {
  color: #22c55e;
}

.aspect-symbol.challenging {
  color: #ef4444;
}

.aspect-symbol.neutral {
  color: #eab308;
}

.aspect-harmonious {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.aspect-challenging {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.aspect-neutral {
  background: rgba(234, 179, 8, 0.2);
  color: #eab308;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.houses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.house-item {
  background: rgba(20, 20, 50, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.house-item:hover {
  border-color: rgba(139, 92, 246, 0.4);
  background: rgba(139, 92, 246, 0.1);
}

.house-number {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 4px;
}

.house-sign {
  font-size: 1rem;
  font-weight: 600;
  color: #a78bfa;
  margin-bottom: 2px;
}

.house-degree {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.edit-form {
  padding: 20px 0;
}

:deep(.edit-form .el-form-item__label) {
  color: rgba(255, 255, 255, 0.7);
}

:deep(.edit-form .el-input__wrapper) {
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

:deep(.edit-form .el-input__wrapper:hover) {
  border-color: rgba(139, 92, 246, 0.4);
}

:deep(.edit-form .el-input__wrapper.is-focus) {
  border-color: rgba(139, 92, 246, 0.6);
}

:deep(.edit-form .el-input__inner) {
  color: rgba(255, 255, 255, 0.9);
}

:deep(.edit-form .el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.feature-entrances {
  margin-bottom: 24px;
}

.quest-entrance {
  margin-top: 8px;
}

.entrance-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.15) 100%);
  border-radius: 10px;
  border: 1px solid rgba(139, 92, 246, 0.25);
  transition: all 0.3s ease;
}

.entrance-content:hover {
  border-color: rgba(139, 92, 246, 0.4);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(99, 102, 241, 0.2) 100%);
}

.entrance-icon {
  font-size: 1.8rem;
}

.entrance-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.entrance-info h5 {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.entrance-info p {
  margin: 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.entrance-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.entrance-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}

.entrance-btn:active {
  transform: translateY(0);
}

.arrow {
  font-size: 0.9rem;
  transition: transform 0.3s ease;
}

.entrance-btn:hover .arrow {
  transform: translateX(2px);
}

.network-chain-entrance .entrance-content {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.network-chain-entrance .entrance-content:hover {
  border-color: rgba(34, 197, 94, 0.4);
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(16, 185, 129, 0.2) 100%);
}

.network-chain-btn {
  background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
}

.network-chain-btn:hover {
  box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
}
</style>
