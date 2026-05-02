<template>
  <div class="prediction-detail">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="detail-main">
      <div class="back-section" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回预言家礼堂</span>
      </div>

      <div class="content-grid">
        <div class="main-panel">
          <div v-if="loading" class="loading-section">
            <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
            <p class="loading-text">加载中...</p>
          </div>

          <div v-else-if="!predictionDetail" class="error-section">
            <div class="error-icon">❌</div>
            <p class="error-text">场次不存在或已被删除</p>
          </div>

          <div v-else class="session-detail">
            <div class="session-header">
              <div class="session-badges">
                <span class="type-badge" :class="predictionDetail.session_type">
                  {{ getSessionTypeLabel(predictionDetail.session_type) }}
                </span>
                <span class="status-badge" :class="sessionStatus">
                  {{ statusText }}
                </span>
              </div>
              
              <div class="session-title-section">
                <h1 class="session-title">{{ predictionDetail.title }}</h1>
                <p class="session-desc">{{ predictionDetail.description }}</p>
              </div>
              
              <div class="session-meta">
                <div class="meta-item" v-if="predictionDetail.voting_starts_at">
                  <el-icon><Calendar /></el-icon>
                  <span>开始: {{ formatDateTime(predictionDetail.voting_starts_at) }}</span>
                </div>
                <div class="meta-item" v-if="predictionDetail.voting_ends_at">
                  <el-icon><Timer /></el-icon>
                  <span>结束: {{ formatDateTime(predictionDetail.voting_ends_at) }}</span>
                </div>
                <div class="meta-item">
                  <el-icon><UserFilled /></el-icon>
                  <span>{{ predictionDetail.total_votes || 0 }} 人已投票</span>
                </div>
              </div>
            </div>

            <div class="reward-section" v-if="predictionDetail.base_reward_amount">
              <div class="reward-header">
                <span class="reward-icon">🏆</span>
                <span class="reward-title">奖励设置</span>
              </div>
              <div class="reward-info">
                <span class="reward-amount">{{ predictionDetail.base_reward_amount }}</span>
                <span class="reward-unit">{{ getAssetLabel(predictionDetail.reward_asset_type) }}</span>
                <span class="reward-note" v-if="predictionDetail.is_vip_enabled">
                  VIP 加成: ×{{ predictionDetail.vip_multiplier || 1.5 }}
                </span>
              </div>
            </div>

            <div class="tiered-cost-section" v-if="tieredCosts.length > 0 && isVotingOpen">
              <div class="section-header">
                <span class="section-icon">🎫</span>
                <span class="section-title">阶梯式投票规则</span>
              </div>
              <div class="tier-list">
                <div 
                  v-for="(tier, index) in tieredCosts" 
                  :key="index"
                  class="tier-item"
                  :class="{ current: tier.is_current_tier, past: userVoteCount >= tier.vote_tier }"
                >
                  <div class="tier-number">
                    <span class="tier-badge-num">{{ tier.vote_tier }}</span>
                  </div>
                  <div class="tier-info">
                    <div class="tier-assets">
                      <span class="asset-label">可用资产:</span>
                      <span 
                        v-for="(asset, aIndex) in tier.allowed_asset_types" 
                        :key="aIndex"
                        class="asset-tag"
                      >
                        {{ getAssetLabel(asset) }}
                      </span>
                    </div>
                    <div class="tier-costs" v-if="hasCost(tier)">
                      <span class="cost-item" v-if="tier.cost_fragment > 0">
                        💎 {{ tier.cost_fragment }} 碎片
                      </span>
                      <span class="cost-item" v-if="tier.cost_point > 0">
                        ⭐ {{ tier.cost_point }} 星尘
                      </span>
                      <span class="cost-item" v-if="tier.cost_ticket > 0">
                        🎫 {{ tier.cost_ticket }} 预言券
                      </span>
                    </div>
                    <div class="tier-costs free" v-else>
                      <span class="free-text">免费投票</span>
                    </div>
                  </div>
                  <div class="tier-multiplier">
                    <span class="multiplier-label">奖励倍数</span>
                    <span class="multiplier-value">×{{ tier.reward_multiplier }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="voting-section" v-if="isVotingOpen">
              <div class="section-header">
                <span class="section-icon">🎯</span>
                <span class="section-title">选择您的预测</span>
                <span class="vote-count-info">
                  您已投票: {{ userVoteCount }} / {{ predictionDetail.max_votes_per_user || 1 }} 次
                </span>
              </div>
              
              <div v-if="userVoteCount >= (predictionDetail.max_votes_per_user || 1)" class="vote-limit-warning">
                <el-icon><Warning /></el-icon>
                <span>您已达到该场次最大投票次数</span>
              </div>
              
              <div v-else class="options-grid">
                <div 
                  v-for="(option, index) in predictionOptions" 
                  :key="index"
                  class="option-card"
                  :class="{ 
                    selected: selectedOption === option.value,
                    disabled: votingInProgress 
                  }"
                  @click="selectOption(option.value)"
                >
                  <div class="option-icon" v-if="option.icon">
                    {{ option.icon }}
                  </div>
                  <div class="option-label">
                    {{ option.label }}
                  </div>
                  <div class="option-value" v-if="option.value !== option.label">
                    {{ option.value }}
                  </div>
                  <div class="option-check" v-if="selectedOption === option.value">
                    <el-icon><Check /></el-icon>
                  </div>
                </div>
              </div>

              <div class="vote-actions" v-if="selectedOption && canVote">
                <div class="vote-settings">
                  <div class="setting-item">
                    <span class="setting-label">信心值</span>
                    <el-slider 
                      v-model="voteConfidence" 
                      :min="0" 
                      :max="100" 
                      :step="10"
                      :disabled="votingInProgress"
                    />
                    <span class="setting-value">{{ voteConfidence }}%</span>
                  </div>
                  
                  <div class="setting-item" v-if="currentTier && hasCost(currentTier)">
                    <span class="setting-label">使用资产</span>
                    <el-select 
                      v-model="selectedAsset" 
                      placeholder="选择使用的资产"
                      :disabled="votingInProgress"
                      style="width: 180px"
                    >
                      <el-option 
                        v-if="currentTier.allowed_asset_types.includes('fragment')"
                        label="星元碎片" 
                        value="fragment"
                      />
                      <el-option 
                        v-if="currentTier.allowed_asset_types.includes('point')"
                        label="高阶星尘" 
                        value="point"
                      />
                      <el-option 
                        v-if="currentTier.allowed_asset_types.includes('ticket')"
                        label="预言券" 
                        value="ticket"
                      />
                    </el-select>
                  </div>
                </div>

                <el-button 
                  type="primary" 
                  size="large" 
                  class="vote-btn"
                  :loading="votingInProgress"
                  :disabled="!canSubmitVote"
                  @click="submitVote"
                >
                  <el-icon><Promotion /></el-icon>
                  确认投票
                </el-button>
              </div>
            </div>

            <div class="result-section" v-if="!isVotingOpen && predictionDetail.is_resolved">
              <div class="section-header result">
                <span class="section-icon">📊</span>
                <span class="section-title">结果公示</span>
              </div>
              
              <div class="correct-option-display">
                <span class="correct-label">正确选项:</span>
                <span class="correct-value">{{ predictionDetail.correct_option }}</span>
              </div>
              
              <div class="vote-distribution">
                <h4 class="dist-title">投票分布</h4>
                <div 
                  v-for="(option, index) in predictionOptions" 
                  :key="index"
                  class="dist-row"
                >
                  <div class="dist-label">
                    <span class="option-name">{{ option.label }}</span>
                    <span class="option-count">{{ voteDistribution[option.value] || 0 }} 票</span>
                  </div>
                  <el-progress 
                    :percentage="getOptionPercentage(option.value)" 
                    :stroke-width="10"
                    :color="getOptionColor(option.value, predictionDetail.correct_option)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="side-panel">
          <div class="my-votes-card" v-if="predictionDetail?.user_votes?.length > 0">
            <h3 class="section-title">我的投票</h3>
            <div class="my-votes-list">
              <div 
                v-for="(vote, index) in predictionDetail.user_votes" 
                :key="index"
                class="my-vote-item"
                :class="getVoteResultClass(vote)"
              >
                <div class="vote-number">
                  <span class="vote-num-badge">第{{ vote.vote_number }}票</span>
                </div>
                <div class="vote-info">
                  <div class="vote-option">
                    选择: <span class="option-highlight">{{ vote.selected_option }}</span>
                  </div>
                  <div class="vote-meta">
                    <span class="vote-confidence">信心: {{ vote.confidence }}%</span>
                    <span class="vote-multiplier" v-if="vote.applied_multiplier > 1">
                      加成: ×{{ vote.applied_multiplier }}
                    </span>
                  </div>
                  <div class="vote-time">
                    {{ formatTime(vote.created_at) }}
                  </div>
                </div>
                <div class="vote-result" v-if="predictionDetail.is_resolved">
                  <div class="result-icon" :class="vote.is_correct ? 'correct' : 'wrong'">
                    {{ vote.is_correct ? '✓' : '✗' }}
                  </div>
                  <div class="result-info" v-if="vote.is_correct">
                    <div class="reward-amount">
                      +{{ vote.reward_earned || predictionDetail.base_reward_amount || 10 }}
                    </div>
                    <el-button 
                      v-if="!vote.reward_claimed"
                      type="primary"
                      size="small"
                      class="claim-btn"
                      :loading="claimingVote === vote.id"
                      @click.stop="claimReward(vote.id)"
                    >
                      领取奖励
                    </el-button>
                    <span v-else class="claimed-text">已领取</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="no-votes-card" v-else-if="predictionDetail && !predictionDetail.is_resolved">
            <div class="no-vote-icon">📝</div>
            <p class="no-vote-text">您还没有参与投票</p>
            <p class="no-vote-hint">选择一个选项开始预测吧</p>
          </div>

          <div class="evidence-card" v-if="predictionDetail?.resolution_evidence">
            <h3 class="section-title">结算依据</h3>
            <div class="evidence-content">
              <p class="evidence-text">{{ predictionDetail.resolution_evidence }}</p>
            </div>
          </div>

          <div class="oracle-card" v-if="predictionDetail?.oracle_data_source">
            <h3 class="section-title">预言机数据源</h3>
            <div class="oracle-info">
              <span class="oracle-icon">{{ getOracleIcon(predictionDetail.oracle_data_source) }}</span>
              <span class="oracle-name">{{ getOracleLabel(predictionDetail.oracle_data_source) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  ArrowLeft, Loading, Calendar, Timer, UserFilled, 
  Warning, Check, Promotion
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { predictionApi, starResonanceApi } from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const votingInProgress = ref(false)
const claimingVote = ref(null)
const submittingVote = ref(false)

const predictionDetail = ref(null)
const tieredCosts = ref([])

const selectedOption = ref(null)
const voteConfidence = ref(50)
const selectedAsset = ref('fragment')

const userAssets = ref({
  stardust_point: 0,
  stardust_fragment: 0
})
const userTickets = ref(0)

const predictionId = computed(() => parseInt(route.params.id))

const userVoteCount = computed(() => {
  return predictionDetail.value?.user_vote_count || predictionDetail.value?.user_votes?.length || 0
})

const isVotingOpen = computed(() => {
  if (!predictionDetail.value) return false
  if (predictionDetail.value.is_resolved) return false
  
  const now = new Date()
  const startsAt = predictionDetail.value.voting_starts_at ? new Date(predictionDetail.value.voting_starts_at) : null
  const endsAt = predictionDetail.value.voting_ends_at ? new Date(predictionDetail.value.voting_ends_at) : null
  
  if (startsAt && now < startsAt) return false
  if (endsAt && now >= endsAt) return false
  
  return true
})

const sessionStatus = computed(() => {
  if (!predictionDetail.value) return 'unknown'
  if (predictionDetail.value.is_resolved) return 'resolved'
  
  const now = new Date()
  const startsAt = predictionDetail.value.voting_starts_at ? new Date(predictionDetail.value.voting_starts_at) : null
  const endsAt = predictionDetail.value.voting_ends_at ? new Date(predictionDetail.value.voting_ends_at) : null
  
  if (startsAt && now < startsAt) return 'upcoming'
  if (endsAt && now >= endsAt) return 'ended'
  
  return 'voting'
})

const statusText = computed(() => {
  const texts = {
    voting: '投票中',
    upcoming: '即将开始',
    ended: '投票结束',
    resolved: '已结算',
    unknown: '未知'
  }
  return texts[sessionStatus.value] || '未知'
})

const predictionOptions = computed(() => {
  if (!predictionDetail.value) return []
  
  const labels = predictionDetail.value.options || []
  const values = predictionDetail.value.option_values || []
  const icons = predictionDetail.value.option_icons || []
  
  return labels.map((label, index) => ({
    label,
    value: values[index] || label,
    icon: icons[index] || null
  }))
})

const voteDistribution = computed(() => {
  return predictionDetail.value?.vote_distribution || {}
})

const currentTier = computed(() => {
  const nextVoteNum = userVoteCount.value + 1
  return tieredCosts.value.find(t => t.vote_tier === nextVoteNum) || 
         tieredCosts.value[tieredCosts.value.length - 1]
})

const canVote = computed(() => {
  if (!isVotingOpen.value) return false
  const maxVotes = predictionDetail.value?.max_votes_per_user || 1
  return userVoteCount.value < maxVotes
})

const canSubmitVote = computed(() => {
  return selectedOption.value && canVote.value && !votingInProgress.value
})

function getStarStyle(index) {
  const size = Math.random() * 2 + 1
  return {
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${Math.random() * 3}s`,
    opacity: Math.random() * 0.5 + 0.2
  }
}

function getSessionTypeLabel(type) {
  const labels = {
    daily: '每日场次',
    weekly: '每周场次',
    special: '特殊场次',
    festival: '节日活动',
    brand: '品牌联名'
  }
  return labels[type] || type
}

function getAssetLabel(type) {
  const labels = {
    fragment: '星元碎片',
    point: '高阶星尘',
    ticket: '预言券'
  }
  return labels[type] || type
}

function getOracleLabel(type) {
  const labels = {
    weather: '能量气象站',
    resonance_pool: '星能共鸣池',
    manual: '人工判定'
  }
  return labels[type] || type
}

function getOracleIcon(type) {
  const icons = {
    weather: '🌤️',
    resonance_pool: '🌌',
    manual: '👤'
  }
  return icons[type] || '🔮'
}

function formatDateTime(dateStr) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}月${day}日 ${hours}:${minutes}`
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = (now - date) / 1000
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function hasCost(tier) {
  return tier.cost_fragment > 0 || tier.cost_point > 0 || tier.cost_ticket > 0
}

function getVoteResultClass(vote) {
  if (!predictionDetail.value?.is_resolved) return 'pending'
  return vote.is_correct ? 'correct' : 'wrong'
}

function getOptionPercentage(optionValue) {
  const total = predictionDetail.value?.total_votes || 0
  if (total === 0) return 0
  const count = voteDistribution.value[optionValue] || 0
  return Math.round((count / total) * 100)
}

function getOptionColor(optionValue, correctOption) {
  if (optionValue === correctOption) return '#84CC16'
  return '#6B7280'
}

function goBack() {
  router.push('/prediction')
}

function selectOption(value) {
  if (votingInProgress.value) return
  selectedOption.value = selectedOption.value === value ? null : value
}

async function loadPredictionDetail() {
  try {
    loading.value = true
    predictionDetail.value = await predictionApi.getDetail(predictionId.value)
    
    try {
      const tierResult = await predictionApi.getTieredCosts(predictionId.value)
      tieredCosts.value = tierResult.tiered_costs || []
      
      if (tieredCosts.value.length > 0) {
        const firstTier = tieredCosts.value[0]
        if (firstTier.allowed_asset_types?.includes('fragment')) {
          selectedAsset.value = 'fragment'
        } else if (firstTier.allowed_asset_types?.length > 0) {
          selectedAsset.value = firstTier.allowed_asset_types[0]
        }
      }
    } catch (e) {
      console.warn('加载阶梯费用失败:', e)
    }
    
  } catch (error) {
    console.error('加载场次详情失败:', error)
    ElMessage.error('加载场次详情失败')
  } finally {
    loading.value = false
  }
}

async function loadUserAssets() {
  try {
    const result = await starResonanceApi.getPoolStatus()
    userAssets.value = {
      stardust_point: result.user_assets?.stardust_point_balance || 0,
      stardust_fragment: result.user_assets?.stardust_fragment_balance || 0
    }
    
    try {
      const ticketsResult = await starResonanceApi.getMyTickets()
      userTickets.value = ticketsResult.tickets?.length || 0
    } catch (e) {
      console.warn('加载预言券失败:', e)
    }
  } catch (error) {
    console.error('加载用户资产失败:', error)
  }
}

function getCurrentCostInfo() {
  if (!currentTier.value) return null
  
  const tier = currentTier.value
  let costText = ''
  let costAmount = 0
  
  if (selectedAsset.value === 'fragment' && tier.cost_fragment > 0) {
    costAmount = tier.cost_fragment
    costText = `${costAmount} 星元碎片`
  } else if (selectedAsset.value === 'point' && tier.cost_point > 0) {
    costAmount = tier.cost_point
    costText = `${costAmount} 高阶星尘`
  } else if (selectedAsset.value === 'ticket' && tier.cost_ticket > 0) {
    costAmount = tier.cost_ticket
    costText = `${costAmount} 预言券`
  } else {
    costText = '免费'
  }
  
  return {
    costText,
    costAmount,
    rewardMultiplier: tier.reward_multiplier
  }
}

async function submitVote() {
  if (!selectedOption.value || !canSubmitVote.value) return
  
  const option = predictionOptions.value.find(o => o.value === selectedOption.value)
  const optionLabel = option?.label || selectedOption.value
  const costInfo = getCurrentCostInfo()
  
  let confirmMessage = `确定要选择「${optionLabel}」进行投票吗？`
  if (costInfo) {
    confirmMessage += `\n\n本次投票: ${costInfo.costText}`
    confirmMessage += `\n奖励倍数: ×${costInfo.rewardMultiplier}`
  }
  
  try {
    await ElMessageBox.confirm(
      confirmMessage,
      '确认投票',
      {
        confirmButtonText: '确认投票',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认框错误:', error)
    }
    return
  }
  
  try {
    votingInProgress.value = true
    submittingVote.value = true
    
    const result = await predictionApi.castVoteSecure({
      prediction_id: predictionId.value,
      selected_option: selectedOption.value,
      confidence: voteConfidence.value,
      use_asset: selectedAsset.value
    })
    
    if (result.success === false) {
      throw new Error(result.error || result.error_message || '投票失败')
    }
    
    const voteNumber = result.vote_number || (userVoteCount.value + 1)
    
    ElMessage.success({
      message: `第 ${voteNumber} 票投票成功！\n选择: ${optionLabel}`,
      duration: 3000
    })
    
    selectedOption.value = null
    voteConfidence.value = 50
    
    await Promise.all([
      loadPredictionDetail(),
      loadUserAssets()
    ])
    
  } catch (error) {
    console.error('投票失败:', error)
    
    let errorMessage = error.message || '投票失败'
    
    if (errorMessage.includes('INSUFFICIENT_ASSETS') || errorMessage.includes('不足')) {
      errorMessage = '资产不足，请检查您的余额'
    } else if (errorMessage.includes('MAX_VOTES_EXCEEDED') || errorMessage.includes('最大投票次数')) {
      errorMessage = '已达到该场次最大投票次数'
    } else if (errorMessage.includes('RATE_LIMIT_EXCEEDED') || errorMessage.includes('过于频繁')) {
      errorMessage = '请求过于频繁，请稍后再试'
    } else if (errorMessage.includes('VOTING_ENDED') || errorMessage.includes('投票已结束')) {
      errorMessage = '投票已结束'
    } else if (errorMessage.includes('VOTING_NOT_STARTED') || errorMessage.includes('尚未开始')) {
      errorMessage = '投票尚未开始'
    } else if (errorMessage.includes('ALREADY_RESOLVED') || errorMessage.includes('已结算')) {
      errorMessage = '场次已结算，无法投票'
    }
    
    ElMessage.error({
      message: errorMessage,
      duration: 3000
    })
  } finally {
    votingInProgress.value = false
    submittingVote.value = false
  }
}

async function claimReward(voteId) {
  if (!voteId) return
  
  try {
    await ElMessageBox.confirm(
      '确定要领取奖励吗？',
      '领取确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认框错误:', error)
    }
    return
  }
  
  try {
    claimingVote.value = voteId
    
    const result = await predictionApi.claimReward(voteId)
    
    if (result.success === false) {
      throw new Error(result.error || result.error_message || '领取失败')
    }
    
    const rewardAmount = result.reward_amount || 0
    const assetType = result.reward_asset_type === 'point' ? '高阶星尘' : 
                     result.reward_asset_type === 'fragment' ? '星元碎片' : '预言券'
    
    ElMessage.success({
      message: `奖励领取成功！\n获得 ${rewardAmount} ${assetType}`,
      duration: 3000
    })
    
    await Promise.all([
      loadPredictionDetail(),
      loadUserAssets()
    ])
    
  } catch (error) {
    console.error('领取奖励失败:', error)
    
    let errorMessage = error.message || '领取失败'
    
    if (errorMessage.includes('ALREADY_CLAIMED') || errorMessage.includes('已领取')) {
      errorMessage = '该奖励已领取'
    } else if (errorMessage.includes('NOT_CORRECT') || errorMessage.includes('未猜中')) {
      errorMessage = '未猜中场次，无法领取奖励'
    } else if (errorMessage.includes('NOT_RESOLVED') || errorMessage.includes('未结算')) {
      errorMessage = '场次尚未结算，无法领取奖励'
    }
    
    ElMessage.error({
      message: errorMessage,
      duration: 3000
    })
  } finally {
    claimingVote.value = null
  }
}

onMounted(() => {
  Promise.all([
    loadPredictionDetail(),
    loadUserAssets()
  ])
})
</script>

<style lang="scss" scoped>
.prediction-detail {
  min-height: 100vh;
  width: 100%;
  position: relative;
  background: linear-gradient(135deg, #0a0a2a 0%, #1a1a4a 50%, #0f0f3a 100%);
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
  animation: twinkle 3s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.detail-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.back-section {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    color: #a78bfa;
  }
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.main-panel {
  min-height: 500px;
}

.loading-section,
.error-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  gap: 12px;
  
  .loading-icon {
    color: #8B5CF6;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .loading-text,
  .error-text {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .error-icon {
    font-size: 48px;
  }
}

.session-detail {
  background: rgba(15, 15, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  overflow: hidden;
}

.session-header {
  padding: 24px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
  
  .session-badges {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    
    .type-badge {
      padding: 4px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      
      &.daily {
        background: rgba(132, 204, 22, 0.15);
        color: #84CC16;
      }
      
      &.weekly {
        background: rgba(59, 130, 246, 0.15);
        color: #3B82F6;
      }
      
      &.special {
        background: rgba(139, 92, 246, 0.15);
        color: #a78bfa;
      }
    }
    
    .status-badge {
      padding: 4px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      
      &.voting {
        background: rgba(132, 204, 22, 0.15);
        color: #84CC16;
      }
      
      &.upcoming {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
      }
      
      &.ended {
        background: rgba(251, 191, 36, 0.15);
        color: #FBBF24;
      }
      
      &.resolved {
        background: rgba(107, 114, 128, 0.15);
        color: #9CA3AF;
      }
    }
  }
  
  .session-title-section {
    margin-bottom: 16px;
    
    .session-title {
      font-size: 24px;
      font-weight: 700;
      color: rgba(255, 255, 255, 0.9);
      margin: 0 0 8px 0;
    }
    
    .session-desc {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
      line-height: 1.6;
    }
  }
  
  .session-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    
    .meta-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.reward-section {
  padding: 20px 24px;
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.05) 0%, rgba(245, 158, 11, 0.02) 100%);
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
  
  .reward-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    
    .reward-icon {
      font-size: 20px;
    }
    
    .reward-title {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.7);
    }
  }
  
  .reward-info {
    display: flex;
    align-items: baseline;
    gap: 8px;
    
    .reward-amount {
      font-size: 32px;
      font-weight: 700;
      background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .reward-unit {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .reward-note {
      margin-left: 20px;
      padding: 4px 10px;
      background: rgba(139, 92, 246, 0.1);
      border-radius: 6px;
      font-size: 12px;
      color: #a78bfa;
    }
  }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 0 24px;
  padding-top: 24px;
  
  .section-icon {
    font-size: 18px;
  }
  
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .vote-count-info {
    margin-left: auto;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
  
  &.result {
    padding-top: 0;
  }
}

.tiered-cost-section {
  padding-bottom: 20px;
  
  .tier-list {
    padding: 0 24px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .tier-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(139, 92, 246, 0.08);
    border-radius: 12px;
    transition: all 0.3s ease;
    
    &.current {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &.past {
      opacity: 0.6;
    }
  }
  
  .tier-number {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(139, 92, 246, 0.1);
    border-radius: 10px;
    
    .tier-badge-num {
      font-size: 18px;
      font-weight: 700;
      color: #a78bfa;
    }
  }
  
  .tier-info {
    flex: 1;
    
    .tier-assets {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
      
      .asset-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
      }
      
      .asset-tag {
        padding: 2px 8px;
        background: rgba(139, 92, 246, 0.1);
        border-radius: 4px;
        font-size: 11px;
        color: #a78bfa;
      }
    }
    
    .tier-costs {
      display: flex;
      gap: 12px;
      
      .cost-item {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
      }
      
      &.free {
        .free-text {
          padding: 2px 10px;
          background: rgba(132, 204, 22, 0.15);
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          color: #84CC16;
        }
      }
    }
  }
  
  .tier-multiplier {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    
    .multiplier-label {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
    }
    
    .multiplier-value {
      font-size: 18px;
      font-weight: 700;
      color: #84CC16;
    }
  }
}

.voting-section {
  padding-bottom: 24px;
  
  .vote-limit-warning {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 24px 16px;
    padding: 12px 16px;
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid rgba(251, 191, 36, 0.2);
    border-radius: 10px;
    font-size: 13px;
    color: #FBBF24;
  }
  
  .options-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    padding: 0 24px 20px;
  }
  
  .option-card {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.02);
    border: 2px solid rgba(139, 92, 246, 0.1);
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(.disabled) {
      border-color: rgba(139, 92, 246, 0.3);
      background: rgba(139, 92, 246, 0.05);
    }
    
    &.selected {
      border-color: #8B5CF6;
      background: rgba(139, 92, 246, 0.1);
      box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
    }
    
    &.disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .option-icon {
    font-size: 32px;
  }
  
  .option-label {
    font-size: 15px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.85);
    text-align: center;
  }
  
  .option-value {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .option-check {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #84CC16;
    border-radius: 50%;
    color: #fff;
  }
  
  .vote-actions {
    padding: 0 24px;
  }
  
  .vote-settings {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    padding: 20px;
    background: rgba(139, 92, 246, 0.03);
    border-radius: 12px;
    margin-bottom: 20px;
    
    .setting-item {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
      min-width: 250px;
      
      .setting-label {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        min-width: 60px;
      }
      
      .setting-value {
        font-size: 14px;
        font-weight: 600;
        color: #8B5CF6;
        min-width: 50px;
      }
    }
  }
  
  .vote-btn {
    width: 100%;
    background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
    border: none;
    padding: 16px;
    font-size: 16px;
    font-weight: 600;
    
    &:hover {
      box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4);
    }
  }
}

.result-section {
  padding: 24px;
  background: rgba(107, 114, 128, 0.05);
  border-top: 1px solid rgba(139, 92, 246, 0.08);
  
  .correct-option-display {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    background: rgba(132, 204, 22, 0.1);
    border: 1px solid rgba(132, 204, 22, 0.2);
    border-radius: 12px;
    margin-bottom: 20px;
    
    .correct-label {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .correct-value {
      font-size: 18px;
      font-weight: 700;
      color: #84CC16;
    }
  }
  
  .vote-distribution {
    .dist-title {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.7);
      margin: 0 0 16px 0;
    }
    
    .dist-row {
      margin-bottom: 16px;
      
      .dist-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .option-name {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.7);
        }
        
        .option-count {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
        }
      }
    }
  }
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.my-votes-card,
.no-votes-card,
.evidence-card,
.oracle-card {
  background: rgba(15, 15, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  padding: 20px;
  
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.75);
    margin: 0 0 16px 0;
  }
}

.no-votes-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  
  .no-vote-icon {
    font-size: 32px;
  }
  
  .no-vote-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .no-vote-hint {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.my-votes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.my-vote-item {
  position: relative;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(139, 92, 246, 0.08);
  border-radius: 12px;
  
  &.correct {
    border-left: 3px solid #84CC16;
  }
  
  &.wrong {
    border-left: 3px solid #6B7280;
    opacity: 0.7;
  }
  
  &.pending {
    border-left: 3px solid #3B82F6;
  }
  
  .vote-number {
    margin-bottom: 8px;
    
    .vote-num-badge {
      padding: 2px 8px;
      background: rgba(139, 92, 246, 0.1);
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      color: #a78bfa;
    }
  }
  
  .vote-info {
    .vote-option {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 4px;
      
      .option-highlight {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 500;
      }
    }
    
    .vote-meta {
      display: flex;
      gap: 12px;
      margin-bottom: 4px;
      
      .vote-confidence,
      .vote-multiplier {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
      }
    }
    
    .vote-time {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.3);
    }
  }
  
  .vote-result {
    position: absolute;
    top: 14px;
    right: 14px;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
    
    .result-icon {
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      font-size: 14px;
      font-weight: bold;
      
      &.correct {
        background: rgba(132, 204, 22, 0.15);
        color: #84CC16;
      }
      
      &.wrong {
        background: rgba(107, 114, 128, 0.1);
        color: #9CA3AF;
      }
    }
    
    .result-info {
      .reward-amount {
        font-size: 14px;
        font-weight: 700;
        color: #84CC16;
      }
      
      .claim-btn {
        padding: 4px 12px;
        font-size: 12px;
        margin-top: 4px;
      }
      
      .claimed-text {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
      }
    }
  }
}

.evidence-card {
  .evidence-content {
    .evidence-text {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      line-height: 1.6;
      margin: 0;
    }
  }
}

.oracle-card {
  .oracle-info {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .oracle-icon {
      font-size: 24px;
    }
    
    .oracle-name {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

@media (max-width: 768px) {
  .detail-main {
    padding: 16px;
  }
  
  .session-header {
    padding: 16px;
    
    .session-title {
      font-size: 20px;
    }
  }
  
  .options-grid {
    grid-template-columns: 1fr;
  }
  
  .tier-item {
    flex-wrap: wrap;
  }
  
  .vote-settings {
    flex-direction: column;
    
    .setting-item {
      min-width: auto;
      flex-wrap: wrap;
    }
  }
}
</style>
