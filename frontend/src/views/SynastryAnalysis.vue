<template>
  <div class="synastry-analysis-container">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>
    
    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
    </div>

    <div class="analysis-main">
      <div class="analysis-header">
        <div class="header-icon">
          <el-icon size="36"><Connection /></el-icon>
        </div>
        <h1 class="main-title">缘分深度分析</h1>
        <p class="subtitle">探索你们的缘分匹配度</p>
      </div>

      <template v-if="loadingRecord">
        <div class="loading-container">
          <el-icon size="40" class="loading-icon" :class="{ 'is-loading': loadingRecord }"><Loading /></el-icon>
          <p class="loading-text">正在加载...</p>
        </div>
      </template>

      <template v-else-if="!showResult">
        <div class="input-section">
          <div class="persons-grid">
            <SynastryPersonForm
              v-model:person="personA"
              label="人物 A"
              color="#ff8c32"
              :cities="CITIES_DB"
              :quick-cities="QUICK_CITIES"
            />

            <div class="separator">
              <div class="separator-icon">
                <el-icon size="24"><Plus /></el-icon>
              </div>
              <div class="separator-line"></div>
            </div>

            <SynastryPersonForm
              v-model:person="personB"
              label="人物 B"
              color="#50c8ff"
              :cities="CITIES_DB"
              :quick-cities="QUICK_CITIES"
            />
          </div>

          <div class="my-charts-section" v-if="isLoggedIn && myCharts.length > 0">
            <div class="section-label">
              <el-icon size="16"><FolderOpened /></el-icon>
              <span>从已保存的星盘中选择</span>
            </div>
            <div class="charts-selector">
              <div class="chart-selector-group">
                <span class="selector-label">人物 A:</span>
                <el-select 
                  v-model="selectedChartA" 
                  placeholder="选择已保存的星盘" 
                  @change="applyChartToPersonA"
                  clearable
                  class="chart-select"
                >
                  <el-option
                    v-for="chart in myCharts"
                    :key="chart.id"
                    :label="chart.name || `${chart.birth_date} ${chart.birth_time}`"
                    :value="chart.id"
                  />
                </el-select>
              </div>
              <div class="chart-selector-group">
                <span class="selector-label">人物 B:</span>
                <el-select 
                  v-model="selectedChartB" 
                  placeholder="选择已保存的星盘" 
                  @change="applyChartToPersonB"
                  clearable
                  class="chart-select"
                >
                  <el-option
                    v-for="chart in myCharts"
                    :key="chart.id"
                    :label="chart.name || `${chart.birth_date} ${chart.birth_time}`"
                    :value="chart.id"
                  />
                </el-select>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <el-button 
              type="primary" 
              size="large"
              :loading="calculating"
              :disabled="!canCalculate"
              class="calculate-btn"
              @click="calculateAnalysis"
            >
              <el-icon v-if="!calculating"><MagicStick /></el-icon>
              <span>{{ calculating ? '正在分析...' : '开始深度分析' }}</span>
            </el-button>
            
            <router-link to="/synastry/records" v-if="isLoggedIn">
              <el-button size="large" class="records-btn">
                <el-icon><Document /></el-icon>
                <span>查看历史记录</span>
              </el-button>
            </router-link>
          </div>
        </div>
      </template>

      <Transition name="slide-up">
        <div v-if="showResult" class="result-section">
          <div class="result-actions">
            <el-button @click="goBack" class="back-btn">
              <el-icon><ArrowLeft /></el-icon>
              <span>重新分析</span>
            </el-button>
            <div class="result-actions-right">
              <el-button v-if="isLoggedIn && savedRecordId" type="success" @click="startPrivateChat" class="chat-btn">
                <el-icon><ChatDotRound /></el-icon>
                <span>开始私聊</span>
              </el-button>
              <el-button v-if="isLoggedIn" @click="saveRecord" :loading="saving" class="save-btn">
                <el-icon><Plus /></el-icon>
                <span>{{ saving ? '保存中...' : '保存报告' }}</span>
              </el-button>
              <el-button v-if="savedRecordId" @click="shareRecord" class="share-btn">
                <el-icon><Share /></el-icon>
                <span>分享报告</span>
              </el-button>
            </div>
          </div>

          <div class="basic-info-card">
            <div class="person-info">
              <div class="person-avatar" :style="{ background: 'linear-gradient(135deg, #ff8c32, #f97316)' }">
                <span class="avatar-letter">{{ personALabel[0] }}</span>
              </div>
              <div class="person-details">
                <div class="person-name">{{ personALabel }}</div>
                <div class="person-zodiacs">
                  <span class="zodiac-item">
                    <span class="zodiac-icon">☀</span>
                    {{ analysisData?.basic_info?.person_a?.sun_sign || '-' }}
                  </span>
                  <span class="zodiac-item">
                    <span class="zodiac-icon">☽</span>
                    {{ analysisData?.basic_info?.person_a?.moon_sign || '-' }}
                  </span>
                  <span class="zodiac-item">
                    <span class="zodiac-icon">⬆</span>
                    {{ analysisData?.basic_info?.person_a?.ascendant || '-' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="connect-symbol">
              <el-icon size="32" color="#8b5cf6"><Link /></el-icon>
            </div>

            <div class="person-info">
              <div class="person-avatar" :style="{ background: 'linear-gradient(135deg, #50c8ff, #3b82f6)' }">
                <span class="avatar-letter">{{ personBLabel[0] }}</span>
              </div>
              <div class="person-details">
                <div class="person-name">{{ personBLabel }}</div>
                <div class="person-zodiacs">
                  <span class="zodiac-item">
                    <span class="zodiac-icon">☀</span>
                    {{ analysisData?.basic_info?.person_b?.sun_sign || '-' }}
                  </span>
                  <span class="zodiac-item">
                    <span class="zodiac-icon">☽</span>
                    {{ analysisData?.basic_info?.person_b?.moon_sign || '-' }}
                  </span>
                  <span class="zodiac-item">
                    <span class="zodiac-icon">⬆</span>
                    {{ analysisData?.basic_info?.person_b?.ascendant || '-' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="total-score-card" :style="{ '--score-color': scoreLevelColor }">
            <div class="score-display">
              <div class="score-circle-container">
                <svg class="score-svg" viewBox="0 0 200 200">
                  <defs>
                    <linearGradient :id="scoreGradientId" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" :style="{ stopColor: scoreLevelColor }" />
                      <stop offset="100%" :style="{ stopColor: scoreLevelSecondaryColor }" />
                    </linearGradient>
                  </defs>
                  <circle class="score-bg" cx="100" cy="100" r="80" />
                  <circle 
                    class="score-progress" 
                    cx="100" 
                    cy="100" 
                    r="80"
                    :style="{ 
                      strokeDasharray: getStrokeDasharray(totalScore),
                      stroke: `url(#${scoreGradientId})`
                    }"
                  />
                </svg>
                <div class="score-inner">
                  <span class="score-value">{{ totalScore }}</span>
                  <span class="score-unit">分</span>
                </div>
              </div>
              <div class="score-info">
                <div class="score-level" :style="{ color: scoreLevelColor }">
                  {{ scoreLevel?.level || '中等契合' }}
                </div>
                <p class="score-desc">{{ scoreLevel?.description || '正在分析你们的缘分...' }}</p>
                <p class="score-recommendation" v-if="scoreLevel?.recommendation">
                  {{ scoreLevel.recommendation }}
                </p>
              </div>
            </div>
          </div>

          <div class="dimensions-section">
            <div class="section-header">
              <span class="section-icon">📊</span>
              <h3 class="section-title">各维度匹配度</h3>
            </div>
            
            <div class="dimensions-content">
              <div class="radar-chart-wrapper">
                <RadarChart :dimensions="dimensionsArray" :radius="120">
                  <template #empty>
                    <span class="empty-text">暂无匹配度数据</span>
                  </template>
                </RadarChart>
              </div>
              
              <div class="dimensions-list">
                <div 
                  v-for="(dim, key) in dimensions" 
                  :key="key"
                  class="dimension-item"
                  v-if="dim && typeof dim.score === 'number'"
                >
                  <div class="dimension-header">
                    <span class="dimension-name">{{ dim.name || '未知' }}</span>
                    <span class="dimension-score" :style="{ color: getScoreColor(dim.score) }">
                      {{ dim.score }}分
                    </span>
                  </div>
                  <div class="dimension-bar-wrapper">
                    <div class="dimension-bar-bg"></div>
                    <div 
                      class="dimension-bar-fill"
                      :style="{ 
                        width: `${dim.score}%`,
                        background: getScoreGradient(dim.score)
                      }"
                    ></div>
                  </div>
                  <p class="dimension-desc">{{ dim.description || '暂无描述' }}</p>
                  <div class="dimension-stats" v-if="dim.positive_count !== undefined">
                    <span class="stat-positive">
                      <el-icon><Check /></el-icon>
                      和谐相位 {{ dim.positive_count }} 个
                    </span>
                    <span class="stat-negative">
                      <el-icon><Warning /></el-icon>
                      挑战相位 {{ dim.negative_count }} 个
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="element-section" v-if="elementAnalysis?.description">
            <div class="section-header">
              <span class="section-icon">🔥</span>
              <h3 class="section-title">元素契合度分析</h3>
            </div>
            
            <div class="element-content">
              <div class="element-pair">
                <div class="element-person">
                  <div class="element-badge" :class="elementClass(elementAnalysis?.sun_element_a)">
                    {{ elementAnalysis?.sun_element_name_a || '未知' }}
                  </div>
                  <div class="element-desc">{{ elementAnalysis?.sun_element_desc_a || '' }}</div>
                  <div class="element-sign">
                    <span class="sign-label">太阳</span>
                    <span class="sign-name">{{ elementAnalysis?.sun_sign_a || '-' }}</span>
                  </div>
                </div>
                
                <div class="element-compat">
                  <div class="compat-score" :style="{ color: getScoreColor(elementCompatibilityScore) }">
                    {{ elementCompatibilityScore }}%
                  </div>
                  <div class="compat-label">元素契合度</div>
                </div>
                
                <div class="element-person">
                  <div class="element-badge" :class="elementClass(elementAnalysis?.sun_element_b)">
                    {{ elementAnalysis?.sun_element_name_b || '未知' }}
                  </div>
                  <div class="element-desc">{{ elementAnalysis?.sun_element_desc_b || '' }}</div>
                  <div class="element-sign">
                    <span class="sign-label">太阳</span>
                    <span class="sign-name">{{ elementAnalysis?.sun_sign_b || '-' }}</span>
                  </div>
                </div>
              </div>
              
              <p class="element-analysis-desc">{{ elementAnalysis?.description || '' }}</p>
            </div>
          </div>

          <div class="interaction-section" v-if="interactionStyles.length > 0 || interactionData?.description">
            <div class="section-header">
              <span class="section-icon">💫</span>
              <h3 class="section-title">感情互动模式</h3>
            </div>
            
            <div class="interaction-content">
              <div class="interaction-styles" v-if="interactionStyles.length > 0">
                <el-tag 
                  v-for="style in interactionStyles" 
                  :key="style"
                  class="style-tag"
                  effect="dark"
                >
                  {{ style }}
                </el-tag>
              </div>
              
              <div class="interaction-details" v-if="interactionData">
                <div class="detail-item" v-if="typeof interactionData.romantic_aspect_count !== undefined">
                  <span class="detail-label">浪漫相位数量:</span>
                  <span class="detail-value">{{ interactionData.romantic_aspect_count }}</span>
                </div>
                <div class="detail-item" v-if="typeof interactionData.harmonious_ratio === 'number'">
                  <span class="detail-label">和谐相位比例:</span>
                  <span class="detail-value">{{ interactionData.harmonious_ratio }}%</span>
                </div>
                <div class="detail-item" v-if="typeof interactionData.challenging_ratio === 'number'">
                  <span class="detail-label">挑战相位比例:</span>
                  <span class="detail-value">{{ interactionData.challenging_ratio }}%</span>
                </div>
              </div>
              
              <p class="interaction-desc">{{ interactionData?.description || '' }}</p>
            </div>
          </div>

          <div class="strengths-challenges-section" v-if="strengths.length > 0 || challenges.length > 0">
            <div class="strengths-card" :class="{ 'has-content': strengths.length > 0 }">
              <div class="section-header">
                <span class="section-icon">✅</span>
                <h3 class="section-title">相处优势</h3>
              </div>
              <div class="strengths-list" v-if="strengths.length > 0">
                <div v-for="(item, index) in strengths" :key="index" class="strength-item">
                  <div class="strength-score-badge">{{ item.score || 0 }}分</div>
                  <div class="strength-content">
                    <div class="strength-name">{{ item.dimension || '未知' }}</div>
                    <div class="strength-desc">{{ item.description || '' }}</div>
                  </div>
                </div>
              </div>
              <div class="empty-text" v-else>暂无明显的优势相位</div>
            </div>

            <div class="challenges-card" :class="{ 'has-content': challenges.length > 0 }">
              <div class="section-header">
                <span class="section-icon">⚠️</span>
                <h3 class="section-title">相处挑战</h3>
              </div>
              <div class="challenges-list" v-if="challenges.length > 0">
                <div v-for="(item, index) in challenges" :key="index" class="challenge-item">
                  <div class="challenge-score-badge">{{ item.score || 0 }}分</div>
                  <div class="challenge-content">
                    <div class="challenge-name">{{ item.dimension || '未知' }}</div>
                    <div class="challenge-desc">{{ item.description || '' }}</div>
                  </div>
                </div>
              </div>
              <div class="empty-text" v-else>暂无明显的挑战相位</div>
            </div>
          </div>

          <div class="key-aspects-section" v-if="keyAspects.length > 0">
            <div class="section-header">
              <span class="section-icon">⭐</span>
              <h3 class="section-title">关键相位解读</h3>
            </div>
            
            <div class="key-aspects-list">
              <div 
                v-for="(aspect, index) in keyAspects" 
                :key="index"
                class="aspect-item"
                :class="`aspect-${aspect.nature || 'neutral'}`"
              >
                <div class="aspect-header">
                  <div class="aspect-planets">
                    <span class="planet-name">{{ aspect.planet_a || '未知' }}</span>
                    <span class="aspect-symbol">{{ aspect.aspect_symbol || '' }}</span>
                    <span class="planet-name">{{ aspect.planet_b || '未知' }}</span>
                  </div>
                  <div class="aspect-info">
                    <el-tag 
                      :type="aspect.nature === 'harmonious' ? 'success' : aspect.nature === 'challenging' ? 'danger' : 'info'"
                      size="small"
                    >
                      {{ aspect.aspect || '未知' }}
                    </el-tag>
                    <span class="orb-text" v-if="aspect.orb_arcminutes !== undefined">容许度 {{ aspect.orb_arcminutes }}'</span>
                  </div>
                </div>
                <p class="aspect-interpretation">{{ aspect.interpretation || '暂无解读' }}</p>
              </div>
            </div>
          </div>

          <div class="advice-section" v-if="futureAdvice.length > 0">
            <div class="section-header">
              <span class="section-icon">💡</span>
              <h3 class="section-title">未来发展建议</h3>
            </div>
            
            <div class="advice-list">
              <div 
                v-for="(item, index) in futureAdvice" 
                :key="index"
                class="advice-item"
                :class="`advice-${item.type || 'neutral'}`"
              >
                <div class="advice-icon">
                  <el-icon v-if="item.type === 'strength'"><Star /></el-icon>
                  <el-icon v-else-if="item.type === 'improvement'"><Tools /></el-icon>
                  <el-icon v-else><Warning /></el-icon>
                </div>
                <div class="advice-content">
                  <div class="advice-title">{{ item.title || '建议' }}</div>
                  <div class="advice-desc">{{ item.content || '' }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="summary-section" v-if="summaryText">
            <div class="section-header">
              <span class="section-icon">📝</span>
              <h3 class="section-title">关系总结</h3>
            </div>
            
            <div class="summary-content">
              <p class="summary-text">{{ summaryText }}</p>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <SynastryShareDialog
      v-model="showShareDialog"
      :share-link="shareLink"
      @copy-share-link="handleCopyShareLink"
    />

    <SynastryRewardShareDialog
      v-model="showRewardShareDialog"
      :invite-code="inviteCode"
      :invite-link="inviteLink"
      :share-synastry-link="shareSynastryLink"
      :loading-invite-code="loadingInviteCode"
      @copy-invite-code="handleCopyInviteCode"
      @copy-invite-link="handleCopyInviteLink"
      @copy-synastry-share-link="handleCopySynastryShareLink"
    />

    <StoryCardModal
      v-model:visible="showStoryCardModal"
      :story-card="storyCardData"
      :synastry-data="originalSynastryData"
      :analysis-data="analysisData"
      :person-a-name="personALabel"
      :person-b-name="personBLabel"
      @go-to-story-wall="goToStoryWall"
    />
  </div>
</template>

<script setup>
import { onMounted, watch, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Connection, Plus, FolderOpened, MagicStick, Document,
  ArrowLeft, Share, Link, Check, Warning, Star,
  Tools, InfoFilled, Loading, ChatDotRound,
  CopyDocument, User, ArrowRight
} from '@element-plus/icons-vue'
import { CITIES_DB, QUICK_CITIES } from '@/constants/chart'
import SynastryPersonForm from '@/components/synastry/SynastryPersonForm.vue'
import RadarChart from '@/components/synastry/RadarChart.vue'
import SynastryShareDialog from '@/components/synastry/SynastryShareDialog.vue'
import SynastryRewardShareDialog from '@/components/synastry/SynastryRewardShareDialog.vue'
import StoryCardModal from '@/components/synastry/StoryCardModal.vue'
import { useSynastryAnalysis, getStarStyle } from '@/composables'
import { privateChatApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const {
  calculating,
  saving,
  loadingRecord,
  showResult,
  showShareDialog,
  copied,
  selectedChartA,
  selectedChartB,
  savedRecordId,
  shareLink,
  myCharts,
  inviteCode,
  inviteLink,
  inviteLinkCopied,
  inviteCodeCopied,
  shareSynastryLink,
  showRewardShareDialog,
  loadingInviteCode,
  personA,
  personB,
  analysisData,
  originalSynastryData,
  isLoggedIn,
  canCalculate,
  personALabel,
  personBLabel,
  totalScore,
  scoreLevel,
  scoreLevelColor,
  scoreLevelSecondaryColor,
  dimensions,
  dimensionsArray,
  elementAnalysis,
  elementCompatibilityScore,
  interactionData,
  interactionStyles,
  strengths,
  challenges,
  keyAspects,
  futureAdvice,
  summaryText,
  loadMyCharts,
  loadInviteCode,
  applyChartToPersonA,
  applyChartToPersonB,
  calculateAnalysis,
  goBack,
  saveRecord,
  shareRecord,
  copyShareLink,
  copyInviteCode,
  copyInviteLink,
  copySynastryShareLink,
  loadRecordById,
  loadRecordByShareCode,
  getScoreColor,
  getScoreGradient,
  getStrokeDasharray,
  showStoryCardModal,
  storyCardData,
  generatingStoryCard,
  generateStoryCard,
  closeStoryCardModal,
  goToStoryWall
} = useSynastryAnalysis()

const scoreGradientId = computed(() => `score-gradient-${Date.now()}`)

function elementClass(element) {
  if (!element) return 'element-未知'
  const lower = element.toLowerCase()
  if (lower === '火' || lower === 'fire') return 'element-火'
  if (lower === '土' || lower === 'earth') return 'element-土'
  if (lower === '风' || lower === 'air') return 'element-风'
  if (lower === '水' || lower === 'water') return 'element-水'
  return `element-${lower}`
}

watch(() => route.params, (newParams) => {
  if (newParams.id) {
    loadRecordById(newParams.id)
  } else if (newParams.code) {
    loadRecordByShareCode(newParams.code)
  }
}, { immediate: true })

watch(isLoggedIn, (newVal) => {
  if (newVal) {
    loadMyCharts()
  }
})

function handleCopyShareLink(link) {
  copyShareLink()
}

function handleCopyInviteCode(code) {
  copyInviteCode()
}

function handleCopyInviteLink(link) {
  copyInviteLink()
}

function handleCopySynastryShareLink(link) {
  copySynastryShareLink()
}

async function startPrivateChat() {
  console.log('[SynastryAnalysis] startPrivateChat 被调用，route.query:', route.query)
  
  const targetUserIdParam = route.query.target_user_id
  const compatibilityScore = route.query.compatibility_score ? parseInt(route.query.compatibility_score) : totalScore.value
  const matchType = route.query.match_type
  const matchSource = route.query.match_source || 'synastry'
  
  if (!targetUserIdParam) {
    console.log('[SynastryAnalysis] 没有 target_user_id 参数')
    ElMessage.info('请从人脉链或相位连连看页面发起私聊')
    router.push('/network-chain')
    return
  }
  
  const targetUserId = parseInt(targetUserIdParam)
  
  if (isNaN(targetUserId) || targetUserId <= 0) {
    console.error('[SynastryAnalysis] 无效的 target_user_id:', targetUserIdParam)
    ElMessage.warning('无效的用户信息')
    return
  }
  
  console.log(`[SynastryAnalysis] 准备创建聊天，目标用户ID: ${targetUserId}`)
  
  try {
    ElMessage.info('正在打开聊天...')
    
    const result = await privateChatApi.startChat({
      target_user_id: targetUserId,
      match_source: matchSource,
      compatibility_score: compatibilityScore,
      match_type: matchType
    })
    
    console.log('[SynastryAnalysis] startChat 返回结果:', result)
    
    ElMessage.success('正在打开聊天...')
    router.push({
      path: '/private-chat',
      query: {
        target_user_id: targetUserId,
        compatibility_score: compatibilityScore,
        match_type: matchType,
        match_source: matchSource
      }
    })
  } catch (error) {
    console.error('[SynastryAnalysis] 创建聊天失败:', error)
    ElMessage.info('正在打开聊天页面...')
    router.push({
      path: '/private-chat',
      query: {
        target_user_id: targetUserId,
        compatibility_score: compatibilityScore,
        match_type: matchType,
        match_source: matchSource
      }
    })
  }
}

onMounted(async () => {
  if (route.params.id) {
    await loadRecordById(route.params.id)
  } else if (route.params.code) {
    await loadRecordByShareCode(route.params.code)
  }
  
  if (isLoggedIn.value) {
    loadMyCharts()
  }
  
  if (showResult.value) {
    await nextTick()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
})
</script>

<style lang="scss" scoped>
.synastry-analysis-container {
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
  opacity: 0.25;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #ff8c32 0%, transparent 70%);
  top: 10%;
  left: 10%;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #50c8ff 0%, transparent 70%);
  bottom: 10%;
  right: 10%;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 16px;
}

.loading-icon {
  color: #a78bfa;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.analysis-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.analysis-header {
  text-align: center;
  margin-bottom: 30px;
}

.header-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  color: #a78bfa;
}

.main-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #ff8c32 0%, #50c8ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.input-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.persons-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: stretch;
  margin-bottom: 20px;
}

.separator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.separator-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 50%;
  color: #fff;
}

.separator-line {
  width: 2px;
  height: 60px;
  background: linear-gradient(180deg, rgba(139, 92, 246, 0.5) 0%, transparent 100%);
}

.my-charts-section {
  background: rgba(139, 92, 246, 0.05);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
}

.charts-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-selector-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selector-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.chart-select {
  width: 100%;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.calculate-btn {
  min-width: 200px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  border-radius: 30px;
  padding: 14px 32px;
  font-size: 15px;
  font-weight: 600;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
  }
}

.records-btn {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 30px;
  padding: 14px 24px;
  color: #a78bfa;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
  }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.result-actions-right {
  display: flex;
  gap: 12px;
}

.save-btn {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: none;
  border-radius: 12px;
}

.share-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 12px;
}

.basic-info-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.person-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.person-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-letter {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.person-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.person-name {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.person-zodiacs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.zodiac-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.zodiac-icon {
  font-size: 14px;
}

.connect-symbol {
  flex-shrink: 0;
}

.total-score-card {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 32px;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 40px;
}

.score-circle-container {
  position: relative;
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 12;
  stroke-linecap: round;
}

.score-progress {
  fill: none;
  stroke-width: 12;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease;
}

.score-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
}

.score-unit {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.5);
}

.score-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-level {
  font-size: 28px;
  font-weight: 700;
}

.score-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  line-height: 1.6;
}

.score-recommendation {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border-left: 3px solid var(--score-color);
}

.dimensions-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.section-icon {
  font-size: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.dimensions-content {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 30px;
  align-items: flex-start;
}

.radar-chart-wrapper {
  width: 300px;
  height: 300px;
  flex-shrink: 0;
}

.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dimension-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.dimension-score {
  font-size: 14px;
  font-weight: 600;
}

.dimension-bar-wrapper {
  position: relative;
  height: 8px;
}

.dimension-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.dimension-bar-fill {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 4px;
  transition: width 0.8s ease;
}

.dimension-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.dimension-stats {
  display: flex;
  gap: 16px;
}

.stat-positive,
.stat-negative {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.stat-positive {
  color: #22c55e;
}

.stat-negative {
  color: #ef4444;
}

.empty-text {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  text-align: center;
}

.element-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.element-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.element-pair {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.element-person {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
}

.element-badge {
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  
  &.element-火 { background: linear-gradient(135deg, #ef4444, #f97316); }
  &.element-土 { background: linear-gradient(135deg, #22c55e, #16a34a); }
  &.element-风 { background: linear-gradient(135deg, #3b82f6, #2563eb); }
  &.element-水 { background: linear-gradient(135deg, #06b6d4, #0891b2); }
  &.element-未知 { background: linear-gradient(135deg, #6b7280, #4b5563); }
}

.element-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.element-sign {
  display: flex;
  gap: 6px;
  font-size: 12px;
}

.sign-label {
  color: rgba(255, 255, 255, 0.4);
}

.sign-name {
  color: rgba(255, 255, 255, 0.7);
}

.element-compat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.compat-score {
  font-size: 32px;
  font-weight: 700;
}

.compat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.element-analysis-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  padding: 12px;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 12px;
  text-align: center;
}

.interaction-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.interaction-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.interaction-styles {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.style-tag {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.15) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  font-size: 13px;
}

.interaction-details {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.detail-value {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.interaction-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.7;
}

.strengths-challenges-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.strengths-card,
.challenges-card {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.strengths-list,
.challenges-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.strength-item,
.challenge-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
}

.strength-score-badge {
  padding: 4px 10px;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.challenge-score-badge {
  padding: 4px 10px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.strength-content,
.challenge-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.strength-name,
.challenge-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.strength-desc,
.challenge-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.key-aspects-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.key-aspects-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.aspect-item {
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border-left: 3px solid rgba(255, 255, 255, 0.1);
}

.aspect-harmonious {
  border-left-color: #22c55e;
  background: rgba(34, 197, 94, 0.05);
}

.aspect-challenging {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.aspect-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.aspect-planets {
  display: flex;
  align-items: center;
  gap: 8px;
}

.planet-name {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.aspect-symbol {
  font-size: 20px;
  color: #a78bfa;
}

.aspect-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.orb-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.aspect-interpretation {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  margin: 0;
  line-height: 1.7;
}

.advice-section {
  background: rgba(20, 20, 50, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.advice-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.advice-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
}

.advice-strength {
  background: rgba(34, 197, 94, 0.05);
  border-left: 3px solid #22c55e;
}

.advice-improvement {
  background: rgba(249, 115, 22, 0.05);
  border-left: 3px solid #f97316;
}

.advice-warning {
  background: rgba(239, 68, 68, 0.05);
  border-left: 3px solid #ef4444;
}

.advice-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
}

.advice-strength .advice-icon { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.advice-improvement .advice-icon { background: rgba(249, 115, 22, 0.2); color: #f97316; }
.advice-warning .advice-icon { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.advice-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.advice-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.advice-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.6;
}

.summary-section {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
}

.summary-content {
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
}

.summary-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.8;
  margin: 0;
}

.share-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.share-tip {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.share-link-wrapper {
  display: flex;
  gap: 10px;
}

.share-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

:deep(.reward-share-dialog) {
  .el-dialog {
    background: linear-gradient(180deg, rgba(15, 15, 35, 0.98) 0%, rgba(20, 20, 50, 0.98) 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 16px !important;
  }

  .el-dialog__header {
    border-bottom: 1px solid rgba(139, 92, 246, 0.15) !important;
    padding: 16px 20px !important;
    margin-right: 0 !important;
  }

  .el-dialog__body {
    padding: 20px !important;
  }

  .el-dialog__footer {
    border-top: 1px solid rgba(139, 92, 246, 0.15) !important;
    padding: 16px 20px !important;
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95) !important;
}

.reward-share-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reward-intro {
  text-align: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.intro-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.6;
}

.reward-stages {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.stage-card {
  flex: 1;
  min-width: 140px;
  background: rgba(30, 30, 60, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stage-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;

  &.stage-1 {
    background: linear-gradient(135deg, #f59e0b, #d97706);
  }

  &.stage-2 {
    background: linear-gradient(135deg, #22c55e, #16a34a);
  }

  &.stage-3 {
    background: linear-gradient(135deg, #ef4444, #dc2626);
  }
}

.stage-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.stage-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin: 0;
  line-height: 1.5;
}

.stage-reward {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
}

.stage-arrow {
  display: flex;
  align-items: center;
  padding-top: 12px;
  color: rgba(139, 92, 246, 0.4);
}

.share-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.share-option-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(30, 30, 60, 0.4);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 10px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.option-content {
  display: flex;
  gap: 10px;
  align-items: center;
}

.invite-code-display {
  flex: 1;
  padding: 10px 14px;
  background: rgba(30, 30, 60, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 8px;
  text-align: center;
}

.code-text {
  font-size: 20px;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: 3px;
  font-family: 'Courier New', monospace;
}

.link-input {
  flex: 1;

  :deep(.el-input__wrapper) {
    background: rgba(30, 30, 60, 0.6) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    box-shadow: none !important;
  }

  :deep(.el-input__inner) {
    color: rgba(255, 255, 255, 0.8) !important;
    font-size: 12px !important;
  }
}

.share-tips-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 8px;
}

.tips-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.5;
}

:deep(.el-divider) {
  --el-divider-border-color: rgba(139, 92, 246, 0.15) !important;
  margin: 8px 0 !important;
}

@media (max-width: 600px) {
  .reward-stages {
    flex-direction: column;
    gap: 12px;
  }

  .stage-arrow {
    justify-content: center;
    padding: 0;
    transform: rotate(90deg);
  }

  .option-content {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 900px) {
  .persons-grid {
    grid-template-columns: 1fr;
  }
  
  .separator {
    flex-direction: row;
  }
  
  .separator-line {
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent);
  }
  
  .charts-selector {
    grid-template-columns: 1fr;
  }
  
  .basic-info-card {
    flex-direction: column;
  }
  
  .score-display {
    flex-direction: column;
    text-align: center;
  }
  
  .dimensions-content {
    grid-template-columns: 1fr;
  }
  
  .radar-chart-wrapper {
    margin: 0 auto;
  }
  
  .strengths-challenges-section {
    grid-template-columns: 1fr;
  }
  
  .element-pair {
    flex-direction: column;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .calculate-btn,
  .records-btn {
    width: 100%;
  }
}
</style>
