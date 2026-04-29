<template>
  <div class="astro-container">
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

    <div class="astro-main">
      <div class="astro-header">
        <div class="header-icon">
          <el-icon size="36"><Star /></el-icon>
        </div>
        <h1 class="main-title">星盘查询</h1>
        <p class="subtitle">基于 Swiss Ephemeris 精准星盘计算</p>
      </div>

      <div class="astro-content-wrapper">
        <div class="astro-card-wrapper">
          <div class="astro-card">
            <div class="card-border-glow"></div>
            <div class="card-glow"></div>
            
            <div class="card-content">
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
                        v-model="astroForm.name" 
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
                            @select="onCitySelect"
                            @input="onCityInput"
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
                          @click="triggerSearch"
                          :disabled="queryStatus === 'searching'"
                        >
                          <el-icon v-if="queryStatus === 'searching'"><Loading /></el-icon>
                          <span v-else>查询</span>
                        </button>
                      </div>
                      <div class="query-status" :class="queryStatus">
                        <span v-if="queryStatus === 'searching'">
                          <el-icon class="loading-icon"><Loading /></el-icon>
                          {{ queryMessage }}
                        </span>
                        <span v-else-if="queryStatus === 'valid'" class="success">
                          ✓ {{ queryMessage }}
                        </span>
                        <span v-else-if="queryStatus === 'invalid'" class="error">
                          ✗ {{ queryMessage }}
                        </span>
                        <span v-else class="hint">
                          下拉选择或输入城市名，停止输入后1秒自动查询
                        </span>
                      </div>
                    </div>

                    <div class="input-hint">
                      已选: {{ astroForm.birthPlace }} | 经度: {{ astroForm.longitude.toFixed(2) }}° | 纬度: {{ astroForm.latitude.toFixed(2) }}°
                    </div>
                  </div>
                </div>

                <div class="quick-cities">
                  <span class="quick-label">常用城市:</span>
                  <div class="city-buttons">
                    <button 
                      type="button" 
                      class="city-btn"
                      v-for="city in QUICK_CITIES" 
                      :key="city.id"
                      @click="selectCityById(city.id)"
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
                        v-model="astroForm.birthDate"
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
                        v-model="astroForm.birthTime"
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
                        v-model="astroForm.longitude" 
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
                        v-model="astroForm.latitude" 
                        placeholder="如: 39.90 (北京)"
                        class="astro-input"
                      />
                      <div class="input-border-effect"></div>
                    </div>
                    <div class="input-hint">北纬为正，南纬为负</div>
                  </div>
                </div>

                <div class="form-row">
                  <button 
                    type="button" 
                    class="toggle-manual-btn"
                    @click="showManualCoords = !showManualCoords"
                  >
                    {{ showManualCoords ? '隐藏手动输入' : '手动输入经纬度' }}
                  </button>
                </div>

                <div class="form-group">
                  <label class="form-label">
                    <span class="label-icon">🔮</span>
                    <span>宫位系统</span>
                  </label>
                  <div class="house-system-options">
                    <label 
                      class="radio-option"
                      :class="{ active: astroForm.houseSystem === 'placidus' }"
                    >
                      <input 
                        type="radio" 
                        v-model="astroForm.houseSystem" 
                        value="placidus"
                        class="radio-input"
                      />
                      <span class="radio-label">
                        <span class="radio-name">Placidus 分宫制</span>
                        <span class="radio-desc">最常用的现代占星宫位系统</span>
                      </span>
                    </label>
                    <label 
                      class="radio-option"
                      :class="{ active: astroForm.houseSystem === 'whole_sign' }"
                    >
                      <input 
                        type="radio" 
                        v-model="astroForm.houseSystem" 
                        value="whole_sign"
                        class="radio-input"
                      />
                      <span class="radio-label">
                        <span class="radio-name">整宫制</span>
                        <span class="radio-desc">传统占星，每一星座完整对应一宫</span>
                      </span>
                    </label>
                  </div>
                </div>

                <div class="quick-cities">
                  <span class="quick-label">快速选择:</span>
                  <div class="city-buttons">
                    <button 
                      type="button" 
                      class="city-btn"
                      v-for="city in majorCities" 
                      :key="city.name"
                      @click="selectQuickCity(city)"
                    >
                      {{ city.name }}
                    </button>
                  </div>
                </div>

                <div class="submit-section">
                  <button 
                    type="button" 
                    class="submit-btn"
                    :class="{ 'btn-loading': calculating }"
                    :disabled="calculating"
                    @click="calculateAstro"
                  >
                    <span class="btn-content">
                      <span class="btn-icon" v-if="!calculating">
                        <el-icon><MagicStick /></el-icon>
                      </span>
                      <span class="btn-spinner" v-else></span>
                      <span>{{ calculating ? '计算星盘中...' : '开始计算星盘' }}</span>
                    </span>
                    <div class="btn-glow"></div>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <Transition name="fade">
          <div v-if="showResult" class="result-card-wrapper">
            <div class="result-card">
              <div class="result-card-border-glow"></div>
              <div class="result-content">
                <div class="result-header">
                  <div class="result-icon">
                    <el-icon size="24"><Star /></el-icon>
                  </div>
                  <div class="result-title-wrapper">
                    <h3 class="result-title">你的星盘解读</h3>
                    <p class="result-subtitle">{{ astroForm.name || '用户' }} · {{ astroForm.birthPlace || '未知地点' }}</p>
                  </div>
                  <div class="result-actions">
                    <button 
                      v-if="isLoggedIn"
                      class="save-chart-btn"
                      :class="{ 'btn-loading': saving }"
                      :disabled="saving"
                      @click="saveChart"
                    >
                      <el-icon v-if="saving"><Loading /></el-icon>
                      <span v-else>保存星盘</span>
                    </button>
                    <button 
                      v-else
                      class="login-hint-btn"
                      @click="router.push('/login')"
                    >
                      登录保存
                    </button>
                    
                    <div class="export-dropdown" :class="{ active: showExportMenu }">
                      <button 
                        class="export-btn"
                        :class="{ 'btn-loading': exporting }"
                        :disabled="exporting"
                        @click="toggleExportMenu"
                      >
                        <el-icon><Download /></el-icon>
                        <span>导出</span>
                        <el-icon class="caret-icon" :class="{ rotated: showExportMenu }">
                          <CaretBottom />
                        </el-icon>
                      </button>
                      
                      <Transition name="fade">
                        <div v-if="showExportMenu" class="export-menu">
                          <div class="export-section">
                            <div class="export-section-title">导出图片</div>
                            <div class="export-options">
                              <label 
                                v-for="fmt in exportFormats" 
                                :key="fmt.id"
                                class="export-option"
                                :class="{ selected: selectedExportFormat === fmt.id }"
                              >
                                <input 
                                  type="radio" 
                                  :value="fmt.id" 
                                  v-model="selectedExportFormat"
                                  class="option-input"
                                />
                                <span class="option-label">{{ fmt.name }}</span>
                                <span class="option-desc">{{ fmt.description }}</span>
                              </label>
                            </div>
                            <button 
                              class="export-action-btn"
                              :disabled="exporting"
                              @click="exportChartAsImage"
                            >
                              <el-icon v-if="exporting"><Loading /></el-icon>
                              <span v-else>导出图片</span>
                            </button>
                          </div>
                          
                          <div class="export-divider"></div>
                          
                          <div class="export-section">
                            <div class="export-section-title">导出 PDF 报告</div>
                            <div class="export-options">
                              <label 
                                v-for="tpl in reportTemplates" 
                                :key="tpl.id"
                                class="export-option"
                                :class="{ selected: selectedReportTemplate === tpl.id }"
                              >
                                <input 
                                  type="radio" 
                                  :value="tpl.id" 
                                  v-model="selectedReportTemplate"
                                  class="option-input"
                                />
                                <span class="option-label">{{ tpl.name }}</span>
                                <span class="option-desc">{{ tpl.description }}</span>
                              </label>
                            </div>
                            <button 
                              class="export-action-btn primary"
                              :disabled="exporting || !selectedChartId"
                              @click="exportChartAsPDF"
                            >
                              <el-icon v-if="exporting"><Loading /></el-icon>
                              <span v-else>导出 PDF 报告</span>
                            </button>
                            <p v-if="!selectedChartId" class="export-hint">
                              请先保存星盘后再导出 PDF 报告
                            </p>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>

                <div class="chart-wheel-section">
                  <div class="chart-wheel-container">
                    <ChartWheel v-if="chartData" :chart-data="chartData" />
                  </div>
                </div>

                <div class="big-three-section">
                  <div class="big-three-grid">
                    <div class="big-three-item sun">
                      <div class="big-three-icon">☉</div>
                      <div class="big-three-info">
                        <div class="big-three-label">太阳星座</div>
                        <div class="big-three-value">
                          <span class="zodiac-symbol">{{ sunSignData?.sign_symbol || '✨' }}</span>
                          <span class="zodiac-name">{{ sunSignData?.sign || '未知' }}</span>
                        </div>
                        <div class="big-three-degree">{{ sunSignData?.dms?.formatted || '' }}</div>
                      </div>
                    </div>

                    <div class="big-three-item moon">
                      <div class="big-three-icon">☽</div>
                      <div class="big-three-info">
                        <div class="big-three-label">月亮星座</div>
                        <div class="big-three-value">
                          <span class="zodiac-symbol">{{ moonSignData?.sign_symbol || '✨' }}</span>
                          <span class="zodiac-name">{{ moonSignData?.sign || '未知' }}</span>
                        </div>
                        <div class="big-three-degree">{{ moonSignData?.dms?.formatted || '' }}</div>
                      </div>
                    </div>

                    <div class="big-three-item asc">
                      <div class="big-three-icon">AC</div>
                      <div class="big-three-info">
                        <div class="big-three-label">上升星座</div>
                        <div class="big-three-value">
                          <span class="zodiac-symbol">{{ ascendantData?.sign_symbol || '✨' }}</span>
                          <span class="zodiac-name">{{ ascendantData?.sign || '未知' }}</span>
                        </div>
                        <div class="big-three-degree">{{ ascendantData?.dms?.formatted || '' }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="tabs-container">
                  <div class="tabs">
                    <button 
                      class="tab-btn"
                      :class="{ active: activeTab === 'planets' }"
                      @click="activeTab = 'planets'"
                    >
                      行星位置
                    </button>
                    <button 
                      class="tab-btn"
                      :class="{ active: activeTab === 'houses' }"
                      @click="activeTab = 'houses'"
                    >
                      宫位信息
                    </button>
                    <button 
                      class="tab-btn"
                      :class="{ active: activeTab === 'aspects' }"
                      @click="activeTab = 'aspects'"
                    >
                      相位关系
                    </button>
                  </div>

                  <div class="tab-content">
                    <div v-if="activeTab === 'planets'" class="planets-tab">
                      <div class="planets-table">
                        <div class="table-header">
                          <span class="col-planet">行星</span>
                          <span class="col-sign">星座</span>
                          <span class="col-degree">度数</span>
                          <span class="col-house">宫位</span>
                          <span class="col-status">状态</span>
                        </div>
                        <div 
                          v-for="planet in mainPlanets" 
                          :key="planet.name"
                          class="table-row"
                        >
                          <span class="col-planet">
                            <span class="planet-sym">{{ planet.symbol }}</span>
                            <span class="planet-name">{{ planet.name }}</span>
                          </span>
                          <span class="col-sign">
                            <span class="zodiac-sym">{{ planet.zodiac?.sign_symbol }}</span>
                            {{ planet.zodiac?.sign }}
                          </span>
                          <span class="col-degree">{{ planet.zodiac?.dms?.formatted }}</span>
                          <span class="col-house">第{{ planet.house }}宫</span>
                          <span class="col-status">
                            <span v-if="planet.is_retrograde" class="retrograde">
                              ↺ 逆行
                            </span>
                            <span v-else class="direct">顺行</span>
                          </span>
                        </div>
                      </div>
                    </div>

                    <div v-if="activeTab === 'houses'" class="houses-tab">
                      <div class="houses-grid">
                        <div 
                          v-for="(house, index) in chartData?.houses?.houses || []" 
                          :key="index"
                          class="house-item"
                        >
                          <div class="house-number">第{{ index + 1 }}宫</div>
                          <div class="house-sign">
                            <span class="house-sign-sym">{{ house.sign_symbol }}</span>
                            {{ house.sign }}
                          </div>
                          <div class="house-cusp">{{ house.dms?.formatted }} 起</div>
                          <div class="house-planets" v-if="getPlanetsInHouse(index + 1).length > 0">
                            <span class="house-planet-sym" v-for="p in getPlanetsInHouse(index + 1)" :key="p.name">
                              {{ p.symbol }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div v-if="activeTab === 'aspects'" class="aspects-tab">
                      <div v-if="chartData?.aspects?.length > 0" class="aspects-list">
                        <div 
                          v-for="(aspect, index) in chartData.aspects" 
                          :key="index"
                          class="aspect-item"
                          :class="getAspectClass(aspect)"
                        >
                          <div class="aspect-planets">
                            <span class="aspect-planet">{{ aspect.planet1_symbol }} {{ aspect.planet1 }}</span>
                            <span class="aspect-sym">{{ aspect.aspect_symbol }}</span>
                            <span class="aspect-planet">{{ aspect.planet2 }} {{ aspect.planet2_symbol }}</span>
                          </div>
                          <div class="aspect-info">
                            <span class="aspect-name">{{ aspect.aspect }}</span>
                            <span class="aspect-orb">容许度: {{ aspect.orb }}°</span>
                          </div>
                        </div>
                      </div>
                      <div v-else class="no-aspects">
                        暂无主要相位
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>

        <Transition name="fade">
          <div v-if="showResult" class="ai-interpretation-wrapper">
            <AIInterpretation
              :chart-data="chartData"
              :chart-input="astroForm"
            />
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { astroApi, geoApi, chartApi, reportApi } from '@/api'
import { useUserStore } from '@/stores/user'
import ChartWheel from '@/components/ChartWheel.vue'
import AIInterpretation from '@/components/AIInterpretation.vue'
import { exportAsPNG, exportAsJPG, generateChartFilename, downloadBlob } from '@/utils/exportUtils'
import { Download, CaretBottom, Loading } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn || !!localStorage.getItem('token'))

const saving = ref(false)
const calculating = ref(false)
const exporting = ref(false)
const showResult = ref(false)
const activeTab = ref('planets')
const chartData = ref(null)
const selectedChartId = ref(null)

const showExportMenu = ref(false)
const selectedExportFormat = ref('png_hd')
const selectedReportTemplate = ref('detailed')

const exportFormats = [
  { id: 'png_hd', name: '高清 PNG', format: 'png', scale: 3, description: '3倍分辨率' },
  { id: 'png_standard', name: '标准 PNG', format: 'png', scale: 2, description: '2倍分辨率' },
  { id: 'jpg_hd', name: '高清 JPG', format: 'jpg', scale: 3, description: '高画质' }
]

const reportTemplates = [
  { id: 'detailed', name: '详细版', description: '包含完整解读' },
  { id: 'simple', name: '简洁版', description: '快速概览' }
]

const cityInput = ref('北京')
const queryStatus = ref('')
const queryMessage = ref('')
const showManualCoords = ref(false)
let debounceTimer = null

const CITIES_DB = [
  { id: 'beijing', name: '北京', nameEn: 'Beijing', country: '中国', state: '北京市', latitude: 39.9042, longitude: 116.4074 },
  { id: 'shanghai', name: '上海', nameEn: 'Shanghai', country: '中国', state: '上海市', latitude: 31.2304, longitude: 121.4737 },
  { id: 'guangzhou', name: '广州', nameEn: 'Guangzhou', country: '中国', state: '广东省', latitude: 23.1291, longitude: 113.2644 },
  { id: 'shenzhen', name: '深圳', nameEn: 'Shenzhen', country: '中国', state: '广东省', latitude: 22.5431, longitude: 114.0579 },
  { id: 'chengdu', name: '成都', nameEn: 'Chengdu', country: '中国', state: '四川省', latitude: 30.5728, longitude: 104.0668 },
  { id: 'hangzhou', name: '杭州', nameEn: 'Hangzhou', country: '中国', state: '浙江省', latitude: 30.2741, longitude: 120.1551 },
  { id: 'nanjing', name: '南京', nameEn: 'Nanjing', country: '中国', state: '江苏省', latitude: 32.0603, longitude: 118.7969 },
  { id: 'wuhan', name: '武汉', nameEn: 'Wuhan', country: '中国', state: '湖北省', latitude: 30.5928, longitude: 114.3055 },
  { id: 'xian', name: '西安', nameEn: "Xi'an", country: '中国', state: '陕西省', latitude: 34.3416, longitude: 108.9398 },
  { id: 'chongqing', name: '重庆', nameEn: 'Chongqing', country: '中国', state: '重庆市', latitude: 29.4316, longitude: 106.9123 },
  { id: 'tianjin', name: '天津', nameEn: 'Tianjin', country: '中国', state: '天津市', latitude: 39.0842, longitude: 117.2009 },
  { id: 'suzhou', name: '苏州', nameEn: 'Suzhou', country: '中国', state: '江苏省', latitude: 31.2989, longitude: 120.5853 },
  { id: 'changsha', name: '长沙', nameEn: 'Changsha', country: '中国', state: '湖南省', latitude: 28.2282, longitude: 112.9388 },
  { id: 'zhengzhou', name: '郑州', nameEn: 'Zhengzhou', country: '中国', state: '河南省', latitude: 34.7466, longitude: 113.6254 },
  { id: 'qingdao', name: '青岛', nameEn: 'Qingdao', country: '中国', state: '山东省', latitude: 36.0671, longitude: 120.3826 },
  { id: 'dalian', name: '大连', nameEn: 'Dalian', country: '中国', state: '辽宁省', latitude: 38.9140, longitude: 121.6147 },
  { id: 'shenyang', name: '沈阳', nameEn: 'Shenyang', country: '中国', state: '辽宁省', latitude: 41.8057, longitude: 123.4315 },
  { id: 'harbin', name: '哈尔滨', nameEn: 'Harbin', country: '中国', state: '黑龙江省', latitude: 45.8038, longitude: 126.5350 },
  { id: 'hongkong', name: '香港', nameEn: 'Hong Kong', country: '中国', state: '香港特别行政区', latitude: 22.3193, longitude: 114.1694 },
  { id: 'taipei', name: '台北', nameEn: 'Taipei', country: '中国', state: '台湾省', latitude: 25.0330, longitude: 121.5654 },
  
  { id: 'tokyo', name: '东京', nameEn: 'Tokyo', country: '日本', state: '东京都', latitude: 35.6762, longitude: 139.6503 },
  { id: 'seoul', name: '首尔', nameEn: 'Seoul', country: '韩国', state: '首尔特别市', latitude: 37.5665, longitude: 126.9780 },
  { id: 'singapore', name: '新加坡', nameEn: 'Singapore', country: '新加坡', state: '', latitude: 1.3521, longitude: 103.8198 },
  { id: 'bangkok', name: '曼谷', nameEn: 'Bangkok', country: '泰国', state: '曼谷', latitude: 13.7563, longitude: 100.5018 },
  { id: 'newdelhi', name: '新德里', nameEn: 'New Delhi', country: '印度', state: '德里', latitude: 28.6139, longitude: 77.2090 },
  
  { id: 'newyork', name: '纽约', nameEn: 'New York', country: '美国', state: '纽约州', latitude: 40.7128, longitude: -74.0060 },
  { id: 'losangeles', name: '洛杉矶', nameEn: 'Los Angeles', country: '美国', state: '加利福尼亚州', latitude: 34.0522, longitude: -118.2437 },
  { id: 'chicago', name: '芝加哥', nameEn: 'Chicago', country: '美国', state: '伊利诺伊州', latitude: 41.8781, longitude: -87.6298 },
  { id: 'washington', name: '华盛顿', nameEn: 'Washington', country: '美国', state: '华盛顿哥伦比亚特区', latitude: 38.9072, longitude: -77.0369 },
  { id: 'sanfrancisco', name: '旧金山', nameEn: 'San Francisco', country: '美国', state: '加利福尼亚州', latitude: 37.7749, longitude: -122.4194 },
  { id: 'boston', name: '波士顿', nameEn: 'Boston', country: '美国', state: '马萨诸塞州', latitude: 42.3601, longitude: -71.0589 },
  { id: 'miami', name: '迈阿密', nameEn: 'Miami', country: '美国', state: '佛罗里达州', latitude: 25.7617, longitude: -80.1918 },
  { id: 'houston', name: '休斯顿', nameEn: 'Houston', country: '美国', state: '德克萨斯州', latitude: 29.7604, longitude: -95.3698 },
  
  { id: 'london', name: '伦敦', nameEn: 'London', country: '英国', state: '英格兰', latitude: 51.5074, longitude: -0.1278 },
  { id: 'paris', name: '巴黎', nameEn: 'Paris', country: '法国', state: '法兰西岛', latitude: 48.8566, longitude: 2.3522 },
  { id: 'berlin', name: '柏林', nameEn: 'Berlin', country: '德国', state: '柏林', latitude: 52.5200, longitude: 13.4050 },
  { id: 'rome', name: '罗马', nameEn: 'Rome', country: '意大利', state: '拉齐奥', latitude: 41.9028, longitude: 12.4964 },
  { id: 'madrid', name: '马德里', nameEn: 'Madrid', country: '西班牙', state: '马德里自治区', latitude: 40.4168, longitude: -3.7038 },
  { id: 'amsterdam', name: '阿姆斯特丹', nameEn: 'Amsterdam', country: '荷兰', state: '北荷兰省', latitude: 52.3676, longitude: 4.9041 },
  { id: 'moscow', name: '莫斯科', nameEn: 'Moscow', country: '俄罗斯', state: '莫斯科', latitude: 55.7558, longitude: 37.6173 },
  { id: 'vienna', name: '维也纳', nameEn: 'Vienna', country: '奥地利', state: '维也纳', latitude: 48.2082, longitude: 16.3738 },
  { id: 'prague', name: '布拉格', nameEn: 'Prague', country: '捷克', state: '布拉格', latitude: 50.0755, longitude: 14.4378 },
  { id: 'istanbul', name: '伊斯坦布尔', nameEn: 'Istanbul', country: '土耳其', state: '伊斯坦布尔', latitude: 41.0082, longitude: 28.9784 },
  
  { id: 'sydney', name: '悉尼', nameEn: 'Sydney', country: '澳大利亚', state: '新南威尔士州', latitude: -33.8688, longitude: 151.2093 },
  { id: 'melbourne', name: '墨尔本', nameEn: 'Melbourne', country: '澳大利亚', state: '维多利亚州', latitude: -37.8136, longitude: 144.9631 },
  { id: 'auckland', name: '奥克兰', nameEn: 'Auckland', country: '新西兰', state: '奥克兰大区', latitude: -36.8485, longitude: 174.7633 },
  { id: 'perth', name: '珀斯', nameEn: 'Perth', country: '澳大利亚', state: '西澳大利亚州', latitude: -31.9505, longitude: 115.8605 },
  
  { id: 'dubai', name: '迪拜', nameEn: 'Dubai', country: '阿联酋', state: '迪拜', latitude: 25.2048, longitude: 55.2708 },
  { id: 'cairo', name: '开罗', nameEn: 'Cairo', country: '埃及', state: '开罗省', latitude: 30.0444, longitude: 31.2357 },
  { id: 'johannesburg', name: '约翰内斯堡', nameEn: 'Johannesburg', country: '南非', state: '豪登省', latitude: -26.2041, longitude: 28.0473 },
  { id: 'mumbai', name: '孟买', nameEn: 'Mumbai', country: '印度', state: '马哈拉施特拉邦', latitude: 19.0760, longitude: 72.8777 },
  { id: 'jakarta', name: '雅加达', nameEn: 'Jakarta', country: '印度尼西亚', state: '雅加达', latitude: -6.2088, longitude: 106.8456 },
  { id: 'manila', name: '马尼拉', nameEn: 'Manila', country: '菲律宾', state: '马尼拉', latitude: 14.5995, longitude: 120.9842 },
  { id: 'hanoi', name: '河内', nameEn: 'Hanoi', country: '越南', state: '河内', latitude: 21.0278, longitude: 105.8342 },
  { id: 'kualalumpur', name: '吉隆坡', nameEn: 'Kuala Lumpur', country: '马来西亚', state: '吉隆坡', latitude: 3.1390, longitude: 101.6869 },
  
  { id: 'riodejaneiro', name: '里约热内卢', nameEn: 'Rio de Janeiro', country: '巴西', state: '里约热内卢州', latitude: -22.9068, longitude: -43.1729 },
  { id: 'saopaulo', name: '圣保罗', nameEn: 'Sao Paulo', country: '巴西', state: '圣保罗州', latitude: -23.5505, longitude: -46.6333 },
  { id: 'mexicocity', name: '墨西哥城', nameEn: 'Mexico City', country: '墨西哥', state: '墨西哥城', latitude: 19.4326, longitude: -99.1332 },
  { id: 'buenosaires', name: '布宜诺斯艾利斯', nameEn: 'Buenos Aires', country: '阿根廷', state: '布宜诺斯艾利斯', latitude: -34.6037, longitude: -58.3816 },
  { id: 'santiago', name: '圣地亚哥', nameEn: 'Santiago', country: '智利', state: '圣地亚哥首都大区', latitude: -33.4489, longitude: -70.6693 },
  { id: 'bogota', name: '波哥大', nameEn: 'Bogota', country: '哥伦比亚', state: '波哥大', latitude: 4.7110, longitude: -74.0721 },
  { id: 'lima', name: '利马', nameEn: 'Lima', country: '秘鲁', state: '利马', latitude: -12.0464, longitude: -77.0428 },
  
  { id: 'toronto', name: '多伦多', nameEn: 'Toronto', country: '加拿大', state: '安大略省', latitude: 43.6532, longitude: -79.3832 },
  { id: 'vancouver', name: '温哥华', nameEn: 'Vancouver', country: '加拿大', state: '不列颠哥伦比亚省', latitude: 49.2827, longitude: -123.1207 },
  { id: 'montreal', name: '蒙特利尔', nameEn: 'Montreal', country: '加拿大', state: '魁北克省', latitude: 45.5017, longitude: -73.5673 },
]

const QUICK_CITIES = [
  { id: 'beijing', name: '北京' },
  { id: 'shanghai', name: '上海' },
  { id: 'guangzhou', name: '广州' },
  { id: 'shenzhen', name: '深圳' },
  { id: 'chengdu', name: '成都' },
  { id: 'hangzhou', name: '杭州' },
]

const majorCities = computed(() => CITIES_DB.slice(0, 8))

const astroForm = reactive({
  name: '',
  birthDate: '1990-01-01',
  birthTime: '12:00',
  birthPlace: '北京',
  longitude: 116.4074,
  latitude: 39.9042,
  houseSystem: 'placidus'
})

function searchInLocalDB(cityName) {
  if (!cityName || cityName.trim().length === 0) return null
  
  const query = cityName.trim().toLowerCase()
  
  for (const city of CITIES_DB) {
    if (city.name === cityName.trim()) {
      return city
    }
    if (city.name.toLowerCase().includes(query)) {
      return city
    }
    if (city.nameEn && city.nameEn.toLowerCase().includes(query)) {
      return city
    }
  }
  
  return null
}

async function searchViaAPI(cityName) {
  if (!cityName || cityName.trim().length === 0) return null
  
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 5000)
  
  try {
    const result = await geoApi.geocodeCity(cityName.trim())
    clearTimeout(timeoutId)
    
    if (result?.found) {
      return {
        name: result.city || cityName,
        nameEn: '',
        country: result.country || '',
        state: result.state || '',
        latitude: result.latitude,
        longitude: result.longitude
      }
    }
  } catch (error) {
    clearTimeout(timeoutId)
    console.log('API查询失败，使用本地数据库:', error.message)
  }
  
  return null
}

async function searchCityByName(cityName) {
  if (!cityName || cityName.trim().length === 0) {
    queryStatus.value = ''
    queryMessage.value = ''
    return null
  }
  
  queryStatus.value = 'searching'
  queryMessage.value = '正在查询...'
  
  let city = searchInLocalDB(cityName)
  
  if (city) {
    queryStatus.value = 'valid'
    queryMessage.value = `已匹配到: ${city.name} (${city.country || ''})`
    
    astroForm.birthPlace = city.name
    astroForm.latitude = city.latitude
    astroForm.longitude = city.longitude
    
    return city
  }
  
  city = await searchViaAPI(cityName)
  
  if (city) {
    queryStatus.value = 'valid'
    queryMessage.value = `已找到: ${city.name} (${city.country || ''})`
    
    astroForm.birthPlace = city.name
    astroForm.latitude = city.latitude
    astroForm.longitude = city.longitude
    
    return city
  }
  
  queryStatus.value = 'invalid'
  queryMessage.value = `未找到城市 "${cityName}"，请检查拼写或手动输入经纬度`
  
  return null
}

function queryCitySuggestions(queryString, callback) {
  if (!queryString || queryString.trim().length === 0) {
    callback(CITIES_DB.slice(0, 20))
    return
  }
  
  const q = queryString.toLowerCase()
  const results = CITIES_DB.filter(city => 
    city.name.includes(queryString) || 
    city.name.toLowerCase().includes(q) ||
    city.nameEn.toLowerCase().includes(q)
  )
  
  callback(results.slice(0, 20))
}

function onCitySelect(item) {
  if (item) {
    cityInput.value = item.name
    queryStatus.value = 'valid'
    queryMessage.value = `已选择: ${item.name} (${item.country || ''})`
    
    astroForm.birthPlace = item.name
    astroForm.latitude = item.latitude
    astroForm.longitude = item.longitude
  }
}

function onCityInput(value) {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  
  if (!value || value.trim().length === 0) {
    queryStatus.value = ''
    queryMessage.value = ''
    return
  }
  
  const localCity = searchInLocalDB(value)
  if (localCity) {
    queryStatus.value = 'valid'
    queryMessage.value = `已匹配到: ${localCity.name} (${localCity.country || ''})`
    
    astroForm.birthPlace = localCity.name
    astroForm.latitude = localCity.latitude
    astroForm.longitude = localCity.longitude
    return
  }
  
  queryStatus.value = 'searching'
  queryMessage.value = '正在查询...'
  
  debounceTimer = setTimeout(() => {
    searchCityByName(value)
  }, 1000)
}

async function triggerSearch() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  
  if (!cityInput.value || cityInput.value.trim().length === 0) {
    ElMessage.warning('请输入城市名称')
    return
  }
  
  await searchCityByName(cityInput.value)
}

function selectCityById(cityId) {
  const city = CITIES_DB.find(c => c.id === cityId)
  if (city) {
    cityInput.value = city.name
    queryStatus.value = 'valid'
    queryMessage.value = `已选择: ${city.name} (${city.country || ''})`
    
    astroForm.birthPlace = city.name
    astroForm.latitude = city.latitude
    astroForm.longitude = city.longitude
  }
}

const mainPlanets = computed(() => {
  if (!chartData.value?.planets) return []
  const mainNames = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星', '北交点', '南交点']
  return chartData.value.planets.filter(p => mainNames.includes(p.name))
})

const sunSignData = computed(() => {
  const sun = chartData.value?.planets?.find(p => p.name === '太阳')
  return sun?.zodiac || null
})

const moonSignData = computed(() => {
  const moon = chartData.value?.planets?.find(p => p.name === '月亮')
  return moon?.zodiac || null
})

const ascendantData = computed(() => {
  return chartData.value?.ascendant || null
})

function getPlanetsInHouse(houseNum) {
  return mainPlanets.value.filter(p => p.house === houseNum)
}

function getAspectClass(aspect) {
  const harmonious = ['三分相', '六分相', '合相']
  const challenging = ['四分相', '对分相']
  
  if (harmonious.includes(aspect.aspect)) {
    return 'harmonious'
  } else if (challenging.includes(aspect.aspect)) {
    return 'challenging'
  }
  return ''
}

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

async function calculateAstro() {
  if (!astroForm.birthDate || !astroForm.birthTime) {
    ElMessage.warning('请选择出生日期和时间')
    return
  }
  
  calculating.value = true
  
  try {
    const result = await astroApi.calculateChart({
      name: astroForm.name,
      birth_date: astroForm.birthDate,
      birth_time: astroForm.birthTime,
      latitude: astroForm.latitude,
      longitude: astroForm.longitude,
      birth_place: astroForm.birthPlace,
      house_system: astroForm.houseSystem
    })
    
    chartData.value = result.chart
    showResult.value = true
    ElMessage.success('星盘计算完成')
    
  } catch (error) {
    console.error('计算失败:', error)
    ElMessage.error(error.message || '星盘计算失败')
  } finally {
    calculating.value = false
  }
}

async function saveChart() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再保存星盘')
    return
  }
  
  if (!chartData.value) {
    ElMessage.warning('请先计算星盘')
    return
  }
  
  saving.value = true
  
  try {
    const result = await chartApi.saveChart({
      name: astroForm.name || '未命名星盘',
      birth_date: astroForm.birthDate,
      birth_time: astroForm.birthTime,
      birth_place: astroForm.birthPlace,
      latitude: astroForm.latitude,
      longitude: astroForm.longitude,
      house_system: astroForm.houseSystem,
      chart_data: JSON.stringify(chartData.value)
    })
    
    if (result?.id) {
      selectedChartId.value = result.id
    }
    
    ElMessage.success('星盘已保存到「我的星盘」')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function exportChartAsImage() {
  if (!chartData.value) {
    ElMessage.warning('请先计算星盘')
    return
  }
  
  exporting.value = true
  
  try {
    await nextTick()
    
    const chartContainer = document.querySelector('.chart-wheel-wrapper')
    if (!chartContainer) {
      ElMessage.error('未找到星盘元素')
      return
    }
    
    const formatInfo = exportFormats.find(f => f.id === selectedExportFormat.value)
    const format = formatInfo || exportFormats[0]
    
    const chartDataForFilename = {
      name: astroForm.name || '星盘',
      input: {
      date: astroForm.birthDate
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

async function exportChartAsPDF() {
  if (!chartData.value) {
    ElMessage.warning('请先计算星盘')
    return
  }
  
  exporting.value = true
  
  try {
    let blob
    const templateName = selectedReportTemplate.value === 'detailed' ? '详细版' : '简洁版'
    const chartDataForFilename = {
      name: astroForm.name || '星盘',
      birth_date: astroForm.birthDate
    }
    const filename = generateChartFilename(chartDataForFilename, 'pdf').replace('.pdf', `_${templateName}.pdf`)
    
    if (isLoggedIn.value && selectedChartId.value) {
      blob = await reportApi.getPdfReport(selectedChartId.value, selectedReportTemplate.value)
    } else {
      const reportInput = {
        name: astroForm.name || '星盘',
        birth_date: astroForm.birthDate,
        birth_time: astroForm.birthTime,
        latitude: astroForm.latitude,
        longitude: astroForm.longitude,
        birth_place: astroForm.birthPlace || '',
        house_system: astroForm.houseSystem
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

function toggleExportMenu() {
  showExportMenu.value = !showExportMenu.value
}

function selectQuickCity(city) {
  const found = CITIES_DB.find(c => c.id === city.id)
  if (found) {
    cityInput.value = found.name
    queryStatus.value = 'valid'
    queryMessage.value = `已选择: ${found.name} (${found.country || ''})`
    
    astroForm.birthPlace = found.name
    astroForm.latitude = found.latitude
    astroForm.longitude = found.longitude
  }
}
</script>

<style lang="scss" scoped>
.astro-container {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
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

.astro-main {
  position: relative;
  z-index: 10;
  flex: 1;
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.astro-header {
  text-align: center;
  margin-bottom: 16px;
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
  animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.25); }
  50% { box-shadow: 0 0 40px rgba(139, 92, 246, 0.4); }
}

.main-title {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px 0;
}

.subtitle {
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.85rem;
  margin: 0;
  font-weight: 300;
}

.astro-content-wrapper {
  flex: 1;
  display: flex;
  gap: 20px;
  align-items: flex-start;
  justify-content: center;
  min-height: 0;
  overflow-y: auto;
  padding-bottom: 10px;
  
  @media (max-width: 900px) {
    flex-direction: column;
    align-items: center;
  }
}

.astro-card-wrapper {
  flex-shrink: 0;
  width: 480px;
  
  @media (max-width: 500px) {
    width: 100%;
    max-width: 480px;
  }
}

.astro-card {
  position: relative;
  background: rgba(18, 18, 40, 0.7);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 
    0 0 30px rgba(139, 92, 246, 0.08),
    0 0 60px rgba(139, 92, 246, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.25);
}

.card-border-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px solid transparent;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(99, 102, 241, 0.2), rgba(59, 130, 246, 0.3)) border-box;
  -webkit-mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
}

.card-glow {
  position: absolute;
  top: -30%;
  left: -30%;
  width: 160%;
  height: 160%;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
  pointer-events: none;
  z-index: 1;
}

.card-content {
  position: relative;
  z-index: 10;
  padding: 24px 28px;
}

.astro-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  
  @media (max-width: 500px) {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.input-hint {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.35);
  margin-top: 2px;
}

.hint-text {
  margin-left: auto;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  gap: 4px;
  
  &.success {
    color: #22c55e;
  }
  
  &.error {
    color: #ef4444;
  }
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}

.city-select-wrapper {
  width: 100%;
  
  :deep(.el-autocomplete) {
    width: 100%;
  }
  
  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.5) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px);
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4) !important;
    }
    
    &.is-focus,
    &:focus-within {
      border-color: rgba(139, 92, 246, 0.7) !important;
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.2) !important;
    }
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 0.9rem !important;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.35) !important;
    }
  }
  
  :deep(.el-input__prefix),
  :deep(.el-input__suffix) {
    color: #a78bfa !important;
  }
  
  :deep(.el-autocomplete-suggestion) {
    background: rgba(20, 20, 50, 0.95) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    
    li {
      border-radius: 8px !important;
      color: rgba(255, 255, 255, 0.8) !important;
      
      &:hover,
      &.highlighted {
        background: rgba(139, 92, 246, 0.2) !important;
      }
    }
  }
}

.city-select-wrapper {
  width: 100%;
  
  :deep(.el-select) {
    width: 100%;
  }
  
  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.5) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px);
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4) !important;
    }
    
    &.is-focus,
    &:focus-within {
      border-color: rgba(139, 92, 246, 0.7) !important;
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.2) !important;
    }
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 0.9rem !important;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.35) !important;
    }
  }
  
  :deep(.el-input__suffix-inner) {
    width: 100%;
  }
  
  :deep(.el-select__caret) {
    color: #a78bfa !important;
  }
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-name {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 500;
}

.option-en {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.7rem;
}

.option-location {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.7rem;
}

.quick-cities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0;
}

.quick-label {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.75rem;
  display: flex;
  align-items: center;
}

.city-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.city-btn {
  padding: 4px 10px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 6px;
  color: rgba(167, 139, 250, 0.8);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.25);
    border-color: rgba(139, 92, 246, 0.5);
    color: #fff;
  }
}

.toggle-manual-btn {
  background: transparent;
  border: 1px dashed rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: rgba(167, 139, 250, 0.7);
  font-size: 0.75rem;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  width: fit-content;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.6);
    color: #c4b5fd;
    background: rgba(139, 92, 246, 0.05);
  }
}

.city-input-wrapper {
  width: 100%;
}

.city-input-row {
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.autocomplete-wrapper {
  flex: 1;
  
  :deep(.el-autocomplete) {
    width: 100%;
  }
  
  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.5) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px);
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4) !important;
    }
    
    &.is-focus,
    &:focus-within {
      border-color: rgba(139, 92, 246, 0.7) !important;
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.2) !important;
    }
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 0.9rem !important;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.35) !important;
    }
  }
  
  :deep(.el-input__suffix-inner) {
    width: 100%;
  }
}

:deep(.city-popper) {
  background: rgba(20, 20, 50, 0.95) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.3) !important;
  border-radius: 10px !important;
  padding: 4px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
  
  li {
    border-radius: 8px !important;
    color: rgba(255, 255, 255, 0.8) !important;
    padding: 8px 12px !important;
    
    &:hover,
    &.highlighted {
      background: rgba(139, 92, 246, 0.2) !important;
    }
  }
}

.search-city-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 10px;
  color: #c4b5fd;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.3));
    border-color: rgba(139, 92, 246, 0.6);
    color: #fff;
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.query-status {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  
  .loading-icon {
    animation: rotate 1s linear infinite;
  }
  
  &.searching {
    color: rgba(167, 139, 250, 0.8);
  }
  
  &.valid {
    color: #22c55e;
  }
  
  &.invalid {
    color: #ef4444;
  }
  
  .hint {
    color: rgba(255, 255, 255, 0.4);
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

.date-input-wrapper,
.time-input-wrapper {
  width: 100%;
  
  :deep(.el-date-editor),
  :deep(.el-time-editor) {
    width: 100%;
  }
  
  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.5) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px);
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.4) !important;
    }
    
    &.is-focus,
    &:focus-within {
      border-color: rgba(139, 92, 246, 0.7) !important;
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.2) !important;
    }
  }
  
  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 0.9rem !important;
    
    &::placeholder {
      color: rgba(255, 255, 255, 0.35) !important;
    }
  }
  
  :deep(.el-input__prefix),
  :deep(.el-input__suffix) {
    color: #a78bfa !important;
  }
}

.house-system-options {
  display: flex;
  gap: 12px;
  
  @media (max-width: 500px) {
    flex-direction: column;
  }
}

.radio-option {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  background: rgba(30, 30, 60, 0.4);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.35);
    background: rgba(40, 40, 80, 0.4);
  }
  
  &.active {
    border-color: rgba(139, 92, 246, 0.6);
    background: rgba(139, 92, 246, 0.1);
  }
}

.radio-input {
  display: none;
}

.radio-label {
  display: flex;
  flex-direction: column;
}

.radio-name {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  font-weight: 500;
}

.radio-desc {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.75rem;
  margin-top: 2px;
}

.quick-cities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0;
}

.quick-label {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.75rem;
  display: flex;
  align-items: center;
}

.city-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.city-btn {
  padding: 4px 10px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 6px;
  color: rgba(167, 139, 250, 0.8);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
  }
}

.submit-section {
  margin-top: 6px;
}

.submit-btn {
  position: relative;
  width: 100%;
  padding: 14px 28px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.35);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &.btn-loading {
    cursor: not-allowed;
    opacity: 0.85;
  }
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  z-index: 2;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  transition: left 0.6s ease;
  pointer-events: none;
}

.submit-btn:hover .btn-glow {
  left: 100%;
}

.result-card-wrapper {
  flex-shrink: 0;
  width: 520px;
  
  @media (max-width: 900px) {
    width: 100%;
    max-width: 520px;
  }
}

.result-card {
  position: relative;
  background: rgba(18, 18, 40, 0.7);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border-radius: 20px;
  overflow: hidden;
  animation: fadeInUp 0.4s ease;
  box-shadow: 
    0 0 30px rgba(59, 130, 246, 0.08),
    0 0 60px rgba(59, 130, 246, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.25);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-card-border-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px solid transparent;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(139, 92, 246, 0.2), rgba(52, 211, 153, 0.3)) border-box;
  -webkit-mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
}

.result-content {
  position: relative;
  z-index: 10;
  padding: 20px 24px;
  max-height: 560px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(139, 92, 246, 0.3);
    border-radius: 2px;
  }
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.result-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.25) 0%, transparent 70%);
  border-radius: 50%;
  color: #a78bfa;
}

.result-title-wrapper {
  flex: 1;
}

.result-title {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
  font-weight: 600;
}

.result-subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.75rem;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.save-chart-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
  border: 1px solid rgba(34, 197, 94, 0.4);
  border-radius: 8px;
  color: #4ade80;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(16, 185, 129, 0.3));
    border-color: rgba(34, 197, 94, 0.6);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &.btn-loading {
    .el-icon {
      animation: spin 1s linear infinite;
    }
  }
}

.login-hint-btn {
  padding: 8px 16px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.5);
  }
}

.export-dropdown {
  position: relative;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 8px;
  color: #60a5fa;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(99, 102, 241, 0.3));
    border-color: rgba(59, 130, 246, 0.6);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &.btn-loading {
    .el-icon {
      animation: spin 1s linear infinite;
    }
  }
}

.caret-icon {
  transition: transform 0.3s ease;
  
  &.rotated {
    transform: rotate(180deg);
  }
}

.export-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  width: 280px;
  background: rgba(15, 15, 35, 0.98);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  padding: 16px;
  z-index: 1000;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 60px rgba(139, 92, 246, 0.1);
  animation: fadeInDown 0.2s ease;
}

@keyframes fadeInDown {
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
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.export-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.export-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    border-color: rgba(139, 92, 246, 0.3);
  }
  
  &.selected {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.5);
  }
}

.option-input {
  margin: 0;
  accent-color: #8b5cf6;
}

.option-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.option-desc {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  margin-left: auto;
}

.export-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.3), transparent);
  margin: 12px 0;
}

.export-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px;
  color: #a78bfa;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 6px;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.3));
    border-color: rgba(139, 92, 246, 0.6);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &.primary {
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border-color: transparent;
    color: #fff;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
    }
  }
}

.export-hint {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  margin-top: 8px;
  margin-bottom: 0;
}

.chart-wheel-section {
  margin-bottom: 16px;
  padding: 12px;
  background: radial-gradient(circle at center, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.15);
}

.chart-wheel-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.big-three-section {
  margin-bottom: 16px;
}

.big-three-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.big-three-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  
  &.sun {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
  }
  
  &.moon {
    background: linear-gradient(135deg, rgba(192, 132, 252, 0.15) 0%, rgba(168, 85, 247, 0.05) 100%);
  }
  
  &.asc {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.05) 100%);
  }
}

.big-three-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  font-size: 1rem;
  font-weight: 700;
  color: #fff;
}

.big-three-info {
  flex: 1;
}

.big-three-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 2px;
}

.big-three-value {
  display: flex;
  align-items: center;
  gap: 4px;
}

.big-three-value .zodiac-symbol {
  font-size: 1.2rem;
}

.big-three-value .zodiac-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #fff;
}

.big-three-degree {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.45);
}

.tabs-container {
  border-top: 1px solid rgba(139, 92, 246, 0.15);
  padding-top: 14px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.tab-btn {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    color: rgba(255, 255, 255, 0.7);
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
    color: #a78bfa;
  }
}

.tab-content {
  min-height: 200px;
}

.planets-table {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.table-header {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 0.7fr 0.7fr;
  gap: 8px;
  padding: 8px 10px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.7rem;
  font-weight: 500;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.table-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 0.7fr 0.7fr;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background 0.2s ease;
  font-size: 0.8rem;
  
  &:hover {
    background: rgba(139, 92, 246, 0.08);
  }
}

.col-planet {
  display: flex;
  align-items: center;
  gap: 6px;
}

.planet-sym {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 4px;
  font-size: 0.9rem;
  color: #a78bfa;
}

.planet-name {
  color: rgba(255, 255, 255, 0.85);
}

.col-sign {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.8);
}

.zodiac-sym {
  font-size: 1rem;
  color: #a78bfa;
}

.col-degree {
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.75rem;
}

.col-house {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
}

.col-status {
  text-align: right;
}

.retrograde {
  color: #f97316;
  font-size: 0.7rem;
}

.direct {
  color: #22c55e;
  font-size: 0.7rem;
}

.houses-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.house-item {
  padding: 10px 8px;
  background: rgba(30, 30, 60, 0.4);
  border: 1px solid rgba(139, 92, 246, 0.12);
  border-radius: 10px;
  text-align: center;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
    background: rgba(40, 40, 80, 0.4);
  }
}

.house-number {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 2px;
}

.house-sign {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #fff;
}

.house-sign-sym {
  font-size: 0.9rem;
  color: #a78bfa;
}

.house-cusp {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.house-planets {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
}

.house-planet-sym {
  font-size: 0.75rem;
  color: #a78bfa;
  margin: 0 1px;
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(30, 30, 60, 0.4);
  border: 1px solid rgba(139, 92, 246, 0.12);
  border-radius: 10px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.25);
  }
  
  &.harmonious {
    border-left: 3px solid #22c55e;
  }
  
  &.challenging {
    border-left: 3px solid #f97316;
  }
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 8px;
}

.aspect-planet {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

.aspect-sym {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 50%;
  font-size: 1rem;
  color: #a78bfa;
}

.aspect-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.aspect-name {
  font-size: 0.8rem;
  color: #fff;
  font-weight: 500;
}

.aspect-orb {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.45);
}

.no-aspects {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.85rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.ai-interpretation-wrapper {
  flex-shrink: 0;
  width: 520px;
  
  @media (max-width: 900px) {
    width: 100%;
    max-width: 520px;
  }
}
</style>
