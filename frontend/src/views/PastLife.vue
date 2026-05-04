<template>
  <div class="past-life-page">
    <div class="stars-bg">
      <div 
        v-for="i in 60" 
        :key="i" 
        class="star"
        :style="getStarStyle(i)"
      ></div>
    </div>

    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">🌙</span>
        前世故事
      </h1>
      <p class="page-description">
        穿越时空，探索你的前世今生。基于星盘数据，由 AI 为你生成专属的古风仙侠前世叙事。
      </p>
    </div>

    <div class="tab-section">
      <el-tabs v-model="activeTab" class="main-tabs">
        <el-tab-pane label="单人前世" name="single">
          <div class="input-section">
            <div class="input-card">
              <div class="input-header">
                <span class="input-title-icon">👤</span>
                <span class="input-title">你的出生信息</span>
              </div>
              
              <div class="input-content">
                <div class="existing-charts" v-if="isLoggedIn && myCharts.length > 0">
                  <div class="form-row">
                    <div class="form-item select-chart">
                      <label class="form-label">从存档中选择</label>
                      <el-select 
                        v-model="selectedChartId" 
                        placeholder="选择已保存的星盘"
                        @change="handleChartSelect"
                        class="chart-select"
                      >
                        <el-option
                          v-for="chart in myCharts"
                          :key="chart.id"
                          :label="`${chart.name || '未命名'} - ${chart.birth_date}`"
                          :value="chart.id"
                        />
                      </el-select>
                    </div>
                  </div>
                  <div class="divider">或手动输入</div>
                </div>

                <div class="form-grid">
                  <div class="form-item">
                    <label class="form-label">姓名/称呼</label>
                    <el-input 
                      v-model="chartData.name" 
                      placeholder="输入姓名或称呼（用于故事中）"
                    />
                  </div>

                  <div class="form-item">
                    <label class="form-label">出生日期</label>
                    <el-date-picker
                      v-model="chartData.birthDate"
                      type="date"
                      placeholder="选择出生日期"
                      format="YYYY-MM-DD"
                      value-format="YYYY-MM-DD"
                      class="full-width"
                    />
                  </div>

                  <div class="form-item">
                    <label class="form-label">出生时间</label>
                    <el-time-picker
                      v-model="chartData.birthTime"
                      placeholder="选择出生时间"
                      format="HH:mm"
                      value-format="HH:mm"
                      class="full-width"
                    />
                  </div>

                  <div class="form-item">
                    <label class="form-label">出生地点</label>
                    <el-autocomplete
                      v-model="chartData.cityInput"
                      :fetch-suggestions="searchCity"
                      :trigger-on-focus="false"
                      placeholder="搜索城市"
                      @select="handleCitySelect"
                      class="full-width"
                    >
                      <template #default="{ item }">
                        <div class="city-item">
                          <span class="city-name">{{ item.name }}</span>
                          <span class="city-region">{{ item.admin1 || item.country }}</span>
                        </div>
                      </template>
                    </el-autocomplete>
                  </div>

                  <div class="form-item">
                    <label class="form-label">经度</label>
                    <el-input-number
                      v-model="chartData.longitude"
                      :min="-180"
                      :max="180"
                      :precision="4"
                      :step="0.0001"
                      class="full-width"
                    />
                  </div>

                  <div class="form-item">
                    <label class="form-label">纬度</label>
                    <el-input-number
                      v-model="chartData.latitude"
                      :min="-90"
                      :max="90"
                      :precision="4"
                      :step="0.0001"
                      class="full-width"
                    />
                  </div>

                  <div class="form-item">
                    <label class="form-label">分宫制</label>
                    <el-select v-model="chartData.houseSystem" class="full-width">
                      <el-option label="Placidus" value="placidus" />
                      <el-option label="Koch" value="koch" />
                      <el-option label="Whole Sign" value="whole_sign" />
                      <el-option label="Equal" value="equal" />
                    </el-select>
                  </div>
                </div>

                <div class="input-actions">
                  <el-button 
                    type="primary" 
                    :loading="loadingStory"
                    :disabled="!hasValidChart"
                    @click="handleGenerateSingleStory"
                    class="generate-btn"
                  >
                    <el-icon class="btn-icon"><MagicStick /></el-icon>
                    生成前世故事
                  </el-button>
                  
                  <el-button 
                    v-if="isLoggedIn"
                    @click="goToRecords"
                  >
                    <el-icon class="btn-icon"><Document /></el-icon>
                    我的记录
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <div class="result-section" v-if="storyResult || error">
            <div v-if="error" class="error-card">
              <div class="error-icon">⚠️</div>
              <h3 class="error-title">出错了</h3>
              <p class="error-message">{{ errorMessage }}</p>
              <el-button type="primary" @click="resetSingle">
                重新尝试
              </el-button>
            </div>

            <div v-else-if="storyResult" class="result-card">
              <div class="result-header">
                <div class="theme-badge">
                  <span class="theme-icon">{{ getThemeIcon(themeResult?.theme) }}</span>
                  <span class="theme-name">{{ themeResult?.theme_name || storyResult.theme_name }}</span>
                </div>
                <div class="badges">
                  <el-tag v-if="storyResult.is_deep" type="success" size="small">
                    深度版
                  </el-tag>
                  <el-tag v-else type="info" size="small">
                    精简版
                  </el-tag>
                </div>
              </div>

              <div class="theme-description" v-if="themeResult?.description || storyResult.theme_description">
                <p>{{ themeResult?.description || storyResult.theme_description }}</p>
              </div>

              <div class="story-content">
                <div class="story-content-inner" v-html="renderStoryContent(storyResult.story)"></div>
              </div>

              <div class="result-actions">
                <el-button 
                  v-if="!storyResult.is_deep && isLoggedIn"
                  type="warning"
                  :loading="loadingOrders"
                  @click="handleUpgrade(storyResult.record_id, 'single')"
                >
                  <el-icon class="btn-icon"><Star /></el-icon>
                  解锁深度版 (¥9.9)
                </el-button>
                
                <el-button 
                  type="primary"
                  @click="shareStory(storyResult)"
                >
                  <el-icon class="btn-icon"><Share /></el-icon>
                  分享故事
                </el-button>

                <el-button 
                  @click="resetSingle"
                >
                  重新生成
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="双人前世合盘" name="synastry">
          <div class="input-section">
            <div class="input-card">
              <div class="input-header">
                <span class="input-title-icon">👥</span>
                <span class="input-title">两人出生信息</span>
              </div>
              
              <div class="input-content">
                <div class="person-section">
                  <div class="person-header">
                    <span class="person-icon">A</span>
                    <span class="person-label">第一个人</span>
                  </div>
                  
                  <div class="form-grid">
                    <div class="form-item">
                      <label class="form-label">称呼</label>
                      <el-input 
                        v-model="synastryData.personA.name" 
                        placeholder="输入称呼"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">出生日期</label>
                      <el-date-picker
                        v-model="synastryData.personA.birthDate"
                        type="date"
                        placeholder="选择出生日期"
                        format="YYYY-MM-DD"
                        value-format="YYYY-MM-DD"
                        class="full-width"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">出生时间</label>
                      <el-time-picker
                        v-model="synastryData.personA.birthTime"
                        placeholder="选择出生时间"
                        format="HH:mm"
                        value-format="HH:mm"
                        class="full-width"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">出生地点</label>
                      <el-autocomplete
                        v-model="synastryData.personA.cityInput"
                        :fetch-suggestions="searchCityPersonA"
                        :trigger-on-focus="false"
                        placeholder="搜索城市"
                        @select="handleCitySelectPersonA"
                        class="full-width"
                      >
                        <template #default="{ item }">
                          <div class="city-item">
                            <span class="city-name">{{ item.name }}</span>
                            <span class="city-region">{{ item.admin1 || item.country }}</span>
                          </div>
                        </template>
                      </el-autocomplete>
                    </div>
                    <div class="form-item">
                      <label class="form-label">经度</label>
                      <el-input-number
                        v-model="synastryData.personA.longitude"
                        :min="-180"
                        :max="180"
                        :precision="4"
                        class="full-width"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">纬度</label>
                      <el-input-number
                        v-model="synastryData.personA.latitude"
                        :min="-90"
                        :max="90"
                        :precision="4"
                        class="full-width"
                      />
                    </div>
                  </div>
                </div>

                <div class="vs-divider">
                  <span class="vs-text">✨</span>
                </div>

                <div class="person-section">
                  <div class="person-header">
                    <span class="person-icon">B</span>
                    <span class="person-label">第二个人</span>
                  </div>
                  
                  <div class="form-grid">
                    <div class="form-item">
                      <label class="form-label">称呼</label>
                      <el-input 
                        v-model="synastryData.personB.name" 
                        placeholder="输入称呼"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">出生日期</label>
                      <el-date-picker
                        v-model="synastryData.personB.birthDate"
                        type="date"
                        placeholder="选择出生日期"
                        format="YYYY-MM-DD"
                        value-format="YYYY-MM-DD"
                        class="full-width"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">出生时间</label>
                      <el-time-picker
                        v-model="synastryData.personB.birthTime"
                        placeholder="选择出生时间"
                        format="HH:mm"
                        value-format="HH:mm"
                        class="full-width"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">出生地点</label>
                      <el-autocomplete
                        v-model="synastryData.personB.cityInput"
                        :fetch-suggestions="searchCityPersonB"
                        :trigger-on-focus="false"
                        placeholder="搜索城市"
                        @select="handleCitySelectPersonB"
                        class="full-width"
                      >
                        <template #default="{ item }">
                          <div class="city-item">
                            <span class="city-name">{{ item.name }}</span>
                            <span class="city-region">{{ item.admin1 || item.country }}</span>
                          </div>
                        </template>
                      </el-autocomplete>
                    </div>
                    <div class="form-item">
                      <label class="form-label">经度</label>
                      <el-input-number
                        v-model="synastryData.personB.longitude"
                        :min="-180"
                        :max="180"
                        :precision="4"
                        class="full-width"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">纬度</label>
                      <el-input-number
                        v-model="synastryData.personB.latitude"
                        :min="-90"
                        :max="90"
                        :precision="4"
                        class="full-width"
                      />
                    </div>
                  </div>
                </div>

                <div class="input-actions">
                  <el-button 
                    type="primary" 
                    :loading="loadingSynastry"
                    :disabled="!hasValidSynastry"
                    @click="handleGenerateSynastryStory"
                    class="generate-btn"
                  >
                    <el-icon class="btn-icon"><MagicStick /></el-icon>
                    生成合盘前世故事
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <div class="result-section" v-if="synastryStoryResult">
            <div class="result-card">
              <div class="result-header">
                <div class="theme-badge">
                  <span class="theme-icon">{{ getRelationshipIcon(synastryThemeResult?.relationship_type) }}</span>
                  <span class="theme-name">{{ synastryThemeResult?.relationship_name || synastryStoryResult.relationship_name }}</span>
                </div>
                <div class="badges">
                  <el-tag v-if="synastryStoryResult.is_deep" type="success" size="small">
                    深度版
                  </el-tag>
                  <el-tag v-else type="info" size="small">
                    精简版
                  </el-tag>
                </div>
              </div>

              <div class="persons-info" v-if="synastryStoryResult.person_a_name || synastryStoryResult.person_b_name">
                <span class="person-name">{{ synastryStoryResult.person_a_name || 'A' }}</span>
                <span class="person-connector">与</span>
                <span class="person-name">{{ synastryStoryResult.person_b_name || 'B' }}</span>
              </div>

              <div class="theme-description" v-if="synastryThemeResult?.description || synastryStoryResult.relationship_description">
                <p>{{ synastryThemeResult?.description || synastryStoryResult.relationship_description }}</p>
              </div>

              <div class="story-content">
                <div class="story-content-inner" v-html="renderStoryContent(synastryStoryResult.story)"></div>
              </div>

              <div class="result-actions">
                <el-button 
                  v-if="!synastryStoryResult.is_deep && isLoggedIn"
                  type="warning"
                  :loading="loadingOrders"
                  @click="handleUpgrade(synastryStoryResult.record_id, 'synastry')"
                >
                  <el-icon class="btn-icon"><Star /></el-icon>
                  解锁深度版 (¥9.9)
                </el-button>
                
                <el-button 
                  type="primary"
                  @click="shareStory(synastryStoryResult, true)"
                >
                  <el-icon class="btn-icon"><Share /></el-icon>
                  分享故事
                </el-button>

                <el-button 
                  @click="resetSynastry"
                >
                  重新生成
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog
      v-model="shareDialogVisible"
      title="分享你的前世故事"
      width="500px"
      center
    >
      <div class="share-content" v-if="currentShareData">
        <div class="share-info">
          <p class="share-label">分享链接</p>
          <div class="share-link">
            <el-input 
              :model-value="shareLink"
              readonly
            />
            <el-button type="primary" @click="copyShareLink">
              复制链接
            </el-button>
          </div>
        </div>
        
        <div class="share-info" v-if="currentShareData.share_code">
          <p class="share-label">分享码</p>
          <div class="share-code">{{ currentShareData.share_code }}</div>
        </div>

        <div class="share-hint">
          <p>将链接分享给好友，他们可以查看你的前世故事</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="upgradeDialogVisible"
      title="解锁深度版"
      width="400px"
      center
    >
      <div class="upgrade-content">
        <div class="upgrade-icon">👑</div>
        <h3 class="upgrade-title">解锁深度版前世故事</h3>
        <p class="upgrade-desc">
          深度版包含：<br/>
          • 更详细的前世经历描写<br/>
          • 重要事件的完整脉络<br/>
          • 前世与今生的关联分析
        </p>
        <div class="upgrade-price">
          <span class="price-symbol">¥</span>
          <span class="price-value">9.9</span>
        </div>
        <el-button 
          type="primary" 
          size="large"
          :loading="loadingOrders"
          @click="confirmUpgrade"
          class="upgrade-btn"
        >
          立即解锁
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick, Document, Share, Star } from '@element-plus/icons-vue'
import { usePastLifeAnalysis, getPastLifeStarStyle } from '@/composables/usePastLifeAnalysis'
import { geoApi } from '@/api'

const router = useRouter()

const {
  loading,
  loadingStory,
  loadingSynastry,
  loadingOrders,
  error,
  errorMessage,
  activeTab,
  selectedChartId,
  myCharts,
  chartData,
  synastryData,
  themeResult,
  storyResult,
  synastryThemeResult,
  synastryStoryResult,
  isLoggedIn,
  hasValidChart,
  hasValidSynastry,
  loadMyCharts,
  applyChartToForm,
  analyzeTheme,
  generateStory,
  analyzeSynastryTheme,
  generateSynastryStory,
  createOrder,
  resetSingle,
  resetSynastry,
  getThemeIcon,
  getRelationshipIcon
} = usePastLifeAnalysis()

const shareDialogVisible = ref(false)
const currentShareData = ref(null)
const shareLink = ref('')

const upgradeDialogVisible = ref(false)
const currentUpgradeRecord = ref(null)
const currentUpgradeType = ref('single')

function getStarStyle(index) {
  return getPastLifeStarStyle(index)
}

async function searchCity(queryString, callback) {
  if (!queryString) {
    callback([])
    return
  }
  
  try {
    const result = await geoApi.searchCity(queryString)
    if (result?.results) {
      callback(result.results)
    } else {
      callback([])
    }
  } catch (err) {
    console.error('搜索城市失败:', err)
    callback([])
  }
}

async function searchCityPersonA(queryString, callback) {
  return searchCity(queryString, callback)
}

async function searchCityPersonB(queryString, callback) {
  return searchCity(queryString, callback)
}

function handleCitySelect(item, target = 'single') {
  const data = target === 'personA' ? synastryData.personA : 
               target === 'personB' ? synastryData.personB : chartData
  data.cityInput = item.name
  data.birthPlace = item.name
  if (item.latitude) data.latitude = item.latitude
  if (item.longitude) data.longitude = item.longitude
}

function handleCitySelectPersonA(item) {
  handleCitySelect(item, 'personA')
}

function handleCitySelectPersonB(item) {
  handleCitySelect(item, 'personB')
}

function handleChartSelect(chartId) {
  if (chartId) {
    applyChartToForm(chartId, 'single')
  }
}

async function handleGenerateSingleStory() {
  if (!hasValidChart.value) {
    ElMessage.warning('请先填写完整的出生信息')
    return
  }
  
  await analyzeTheme()
  await generateStory()
}

async function handleGenerateSynastryStory() {
  if (!hasValidSynastry.value) {
    ElMessage.warning('请先填写完整的两人出生信息')
    return
  }
  
  await generateSynastryStory()
}

function shareStory(data, isSynastry = false) {
  if (!data.share_code) {
    ElMessage.warning('该故事暂不支持分享')
    return
  }
  
  currentShareData.value = data
  const baseUrl = window.location.origin
  shareLink.value = `${baseUrl}/past-life/share/${data.share_code}`
  shareDialogVisible.value = true
}

function copyShareLink() {
  navigator.clipboard.writeText(shareLink.value).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

function handleUpgrade(recordId, recordType) {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再解锁深度版')
    return
  }
  
  currentUpgradeRecord.value = recordId
  currentUpgradeType.value = recordType
  upgradeDialogVisible.value = true
}

async function confirmUpgrade() {
  if (!currentUpgradeRecord.value) return
  
  const order = await createOrder(currentUpgradeRecord.value, currentUpgradeType.value)
  
  if (order) {
    ElMessage.success('订单创建成功！')
    upgradeDialogVisible.value = false
    
    ElMessage.info('正在刷新故事...')
    if (currentUpgradeType.value === 'synastry') {
      await generateSynastryStory()
    } else {
      await generateStory()
    }
  }
}

function goToRecords() {
  router.push('/past-life/records')
}

function renderStoryContent(content) {
  if (!content) return ''
  
  let html = content
    .replace(/^# (.+)$/gm, '<h1 class="story-h1">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 class="story-h2">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="story-h3">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="story-strong">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="story-em">$1</em>')
    .replace(/^- (.+)$/gm, '<li class="story-li">$1</li>')
    .replace(/\n\n/g, '</p><p class="story-p">')
    .replace(/\n/g, '<br/>')
  
  return `<p class="story-p">${html}</p>`
}

onMounted(async () => {
  if (isLoggedIn.value) {
    await loadMyCharts()
  }
})
</script>

<style lang="scss" scoped>
.past-life-page {
  position: relative;
  min-height: 100vh;
  padding: 40px 24px;
  overflow-x: hidden;
}

.stars-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
  z-index: -1;
}

.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  animation: twinkle 4s infinite ease-in-out;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.2); }
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 42px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.page-description {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.tab-section {
  max-width: 1000px;
  margin: 0 auto;
}

.main-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    background: rgba(168, 85, 247, 0.2);
  }
  
  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.5);
    font-size: 16px;
    font-weight: 600;
    
    &.is-active {
      color: #f59e0b;
    }
    
    &:hover {
      color: rgba(245, 158, 11, 0.8);
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background: linear-gradient(90deg, #f59e0b, #ef4444);
  }
}

.input-section {
  margin-top: 24px;
}

.input-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 24px;
  overflow: hidden;
}

.input-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 28px;
  background: linear-gradient(90deg, rgba(168, 85, 247, 0.15) 0%, transparent 100%);
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
}

.input-title-icon {
  font-size: 20px;
}

.input-title {
  font-size: 18px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.input-content {
  padding: 28px;
}

.person-section {
  background: rgba(168, 85, 247, 0.05);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(168, 85, 247, 0.1);
}

.person-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
}

.person-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.person-label {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.vs-divider {
  text-align: center;
  margin: 0 0 20px 0;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.3), transparent);
  }
}

.vs-text {
  font-size: 24px;
  background: rgba(20, 20, 50, 0.9);
  padding: 0 16px;
  position: relative;
}

.existing-charts {
  margin-bottom: 20px;
}

.form-row {
  margin-bottom: 16px;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px 24px;
}

.full-width {
  width: 100%;
}

.divider {
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  margin: 8px 0;
  position: relative;
  
  &::before,
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: rgba(168, 85, 247, 0.2);
  }
  
  &::before {
    left: 0;
  }
  
  &::after {
    right: 0;
  }
}

.input-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(168, 85, 247, 0.1);
  flex-wrap: wrap;
}

.generate-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  border: none;
  
  &:hover {
    background: linear-gradient(135deg, #d97706 0%, #dc2626 100%);
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
  }
}

.btn-icon {
  margin-right: 6px;
}

.result-section {
  margin-top: 32px;
}

.error-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 24px;
  padding: 40px;
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 12px 0;
}

.error-message {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 24px 0;
  line-height: 1.6;
}

.result-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 24px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px 28px;
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border-bottom: 1px solid rgba(168, 85, 247, 0.1);
}

.theme-badge {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-icon {
  font-size: 32px;
}

.theme-name {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.persons-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 28px 0;
  
  .person-name {
    font-size: 18px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .person-connector {
    color: rgba(255, 255, 255, 0.5);
  }
}

.theme-description {
  padding: 16px 28px;
  
  p {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.7;
    margin: 0;
    padding: 16px;
    background: rgba(168, 85, 247, 0.05);
    border-radius: 12px;
    border-left: 3px solid #f59e0b;
  }
}

.story-content {
  padding: 24px 28px;
}

.story-content-inner {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 24px;
  
  :deep(.story-h1) {
    font-size: 22px;
    font-weight: 800;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(168, 85, 247, 0.2);
  }
  
  :deep(.story-h2) {
    font-size: 18px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 24px 0 12px 0;
  }
  
  :deep(.story-h3) {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.8);
    margin: 16px 0 8px 0;
  }
  
  :deep(.story-p) {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.9;
    margin: 0 0 12px 0;
    text-indent: 2em;
  }
  
  :deep(.story-strong) {
    color: #f59e0b;
    font-weight: 700;
  }
  
  :deep(.story-em) {
    color: rgba(255, 255, 255, 0.85);
    font-style: italic;
  }
  
  :deep(.story-li) {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.7;
    padding-left: 16px;
    position: relative;
    margin: 4px 0;
    
    &::before {
      content: '•';
      position: absolute;
      left: 0;
      color: #f59e0b;
    }
  }
}

.result-actions {
  display: flex;
  gap: 12px;
  padding: 20px 28px 28px;
  border-top: 1px solid rgba(168, 85, 247, 0.1);
  flex-wrap: wrap;
}

.share-content {
  text-align: center;
  
  .share-info {
    margin-bottom: 20px;
    
    .share-label {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin-bottom: 8px;
    }
    
    .share-link {
      display: flex;
      gap: 8px;
    }
    
    .share-code {
      font-size: 32px;
      font-weight: 800;
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 4px;
    }
  }
  
  .share-hint {
    p {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
  }
}

.upgrade-content {
  text-align: center;
  
  .upgrade-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }
  
  .upgrade-title {
    font-size: 20px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 12px 0;
  }
  
  .upgrade-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.8;
    margin: 0 0 20px 0;
  }
  
  .upgrade-price {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 4px;
    margin-bottom: 24px;
    
    .price-symbol {
      font-size: 18px;
      color: #f59e0b;
      font-weight: 600;
    }
    
    .price-value {
      font-size: 42px;
      font-weight: 800;
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
  
  .upgrade-btn {
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
    border: none;
    width: 100%;
    
    &:hover {
      background: linear-gradient(135deg, #d97706 0%, #dc2626 100%);
    }
  }
}

.city-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.city-name {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.city-region {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.page-title,
.theme-name,
.person-name,
.story-h1,
.story-h2,
.story-h3 {
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.page-description,
.theme-description,
.story-p,
.story-li {
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
  .past-life-page {
    padding: 24px 16px;
  }
  
  .page-title {
    font-size: 28px;
    flex-direction: column;
    gap: 8px;
  }
  
  .title-icon {
    font-size: 32px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .input-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
  
  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .result-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>
