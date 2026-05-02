<template>
  <div class="prediction-result">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="result-main">
      <div class="back-section" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回预言家礼堂</span>
      </div>

      <div v-if="loading" class="loading-section">
        <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
        <p class="loading-text">加载中...</p>
      </div>

      <div v-else-if="!predictionDetail" class="error-section">
        <div class="error-icon">❌</div>
        <p class="error-text">结果不存在或场次未结算</p>
      </div>

      <div v-else class="result-content">
        <div class="result-header">
          <div class="result-badge">
            <span class="badge-icon">🏆</span>
            <span class="badge-text">结果公示</span>
          </div>
          <h1 class="result-title">{{ predictionDetail.title }}</h1>
          <p class="result-desc">{{ predictionDetail.description }}</p>
          <div class="result-meta">
            <span class="meta-item">
              <el-icon><Calendar /></el-icon>
              结算时间: {{ formatDateTime(predictionDetail.resolved_at) }}
            </span>
            <span class="meta-item">
              <el-icon><UserFilled /></el-icon>
              参与人数: {{ predictionDetail.total_votes || 0 }}
            </span>
          </div>
        </div>

        <div class="correct-option-section">
          <div class="section-header">
            <span class="section-icon">✨</span>
            <span class="section-title">正确答案</span>
          </div>
          <div class="correct-option-display">
            <div class="option-card correct">
              <div class="option-icon">✓</div>
              <div class="option-info">
                <div class="option-value">{{ predictionDetail.correct_option }}</div>
                <div class="option-stats">
                  {{ voteDistribution[predictionDetail.correct_option] || 0 }} 人猜中
                  <span class="correct-rate">
                    ({{ correctRate }}%)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="my-votes-section" v-if="myVotes.length > 0">
          <div class="section-header">
            <span class="section-icon">📋</span>
            <span class="section-title">我的投票</span>
            <span class="vote-summary">
              共 {{ myVotes.length }} 票，
              猜中 {{ correctVotesCount }} 票
            </span>
          </div>
          
          <div class="my-votes-list">
            <div 
              v-for="(vote, index) in myVotes" 
              :key="index"
              class="my-vote-card"
              :class="vote.is_correct ? 'correct' : 'wrong'"
            >
              <div class="vote-status">
                <div class="status-icon" :class="vote.is_correct ? 'correct' : 'wrong'">
                  {{ vote.is_correct ? '✓' : '✗' }}
                </div>
                <div class="status-text">
                  {{ vote.is_correct ? '猜中了!' : '未猜中' }}
                </div>
              </div>
              
              <div class="vote-detail">
                <div class="vote-info">
                  <div class="vote-number">第{{ vote.vote_number }}票</div>
                  <div class="vote-option">
                    选择: <span class="option-highlight">{{ vote.selected_option }}</span>
                  </div>
                  <div class="vote-meta">
                    <span>信心: {{ vote.confidence }}%</span>
                    <span v-if="vote.applied_multiplier > 1">加成: ×{{ vote.applied_multiplier }}</span>
                    <span>时间: {{ formatTime(vote.created_at) }}</span>
                  </div>
                </div>
                
                <div class="vote-reward" v-if="vote.is_correct">
                  <div class="reward-info">
                    <span class="reward-label">奖励:</span>
                    <span class="reward-amount">+{{ vote.reward_earned || predictionDetail.base_reward_amount || 10 }}</span>
                    <span class="reward-unit">{{ getAssetLabel(predictionDetail.reward_asset_type) }}</span>
                  </div>
                  
                  <el-button 
                    v-if="!vote.reward_claimed"
                    type="primary"
                    size="large"
                    class="claim-btn"
                    :loading="claimingVote === vote.id"
                    @click="claimReward(vote.id)"
                  >
                    <el-icon><Coin /></el-icon>
                    领取奖励
                  </el-button>
                  <div v-else class="claimed-status">
                    <span class="claimed-icon">✓</span>
                    <span class="claimed-text">已领取</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="total-reward" v-if="correctVotesCount > 0">
            <span class="total-label">您总计可获得:</span>
            <span class="total-amount">{{ totalReward }}</span>
            <span class="total-unit">{{ getAssetLabel(predictionDetail.reward_asset_type) }}</span>
          </div>
        </div>

        <div class="no-vote-section" v-else>
          <div class="no-vote-icon">📭</div>
          <p class="no-vote-text">您没有参与本次投票</p>
        </div>

        <div class="distribution-section">
          <div class="section-header">
            <span class="section-icon">📊</span>
            <span class="section-title">投票分布</span>
          </div>
          
          <div class="distribution-chart">
            <div 
              v-for="(option, index) in predictionOptions" 
              :key="index"
              class="distribution-row"
              :class="{ correct: option.value === predictionDetail.correct_option }"
            >
              <div class="option-info">
                <span class="option-label">{{ option.label }}</span>
                <span class="option-count">
                  {{ voteDistribution[option.value] || 0 }} 票
                  <span v-if="option.value === predictionDetail.correct_option" class="correct-mark">
                    (正确答案)
                  </span>
                </span>
              </div>
              <div class="progress-wrapper">
                <div 
                  class="progress-bar"
                  :style="{ 
                    width: getOptionPercentage(option.value) + '%',
                    background: option.value === predictionDetail.correct_option 
                      ? 'linear-gradient(90deg, #84CC16 0%, #22C55E 100%)' 
                      : 'linear-gradient(90deg, #6B7280 0%, #9CA3AF 100%)'
                  }"
                >
                  <span class="progress-percent">{{ getOptionPercentage(option.value) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="evidence-section" v-if="predictionDetail.resolution_evidence">
          <div class="section-header">
            <span class="section-icon">📜</span>
            <span class="section-title">结算依据</span>
          </div>
          <div class="evidence-content">
            <div class="evidence-icon">
              {{ getOracleIcon(predictionDetail.oracle_data_source) }}
            </div>
            <div class="evidence-text">
              <div class="oracle-source">
                数据来源: {{ getOracleLabel(predictionDetail.oracle_data_source) }}
              </div>
              <p class="evidence-desc">{{ predictionDetail.resolution_evidence }}</p>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <div class="section-header">
            <span class="section-icon">📈</span>
            <span class="section-title">场次统计</span>
          </div>
          
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-value">{{ predictionDetail.total_votes || 0 }}</div>
              <div class="stat-label">总投票数</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">✅</div>
              <div class="stat-value">{{ correctVotesTotal }}</div>
              <div class="stat-label">猜中人数</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📊</div>
              <div class="stat-value">{{ correctRate }}%</div>
              <div class="stat-label">整体正确率</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🏆</div>
              <div class="stat-value">{{ totalRewardDistributed }}</div>
              <div class="stat-label">发放奖励总额</div>
            </div>
          </div>
        </div>

        <div class="action-section">
          <el-button type="primary" size="large" class="back-hall-btn" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回预言家礼堂
          </el-button>
          <el-button type="default" size="large" class="view-history-btn" @click="goToHistory">
            <el-icon><Document /></el-icon>
            查看历史记录
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  ArrowLeft, Loading, Calendar, Timer, UserFilled, 
  Coin, Document
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { predictionApi } from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const claimingVote = ref(null)

const predictionDetail = ref(null)

const predictionId = computed(() => parseInt(route.params.id))

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

const myVotes = computed(() => {
  return predictionDetail.value?.user_votes || []
})

const correctVotesCount = computed(() => {
  return myVotes.value.filter(v => v.is_correct).length
})

const correctVotesTotal = computed(() => {
  return voteDistribution.value[predictionDetail.value?.correct_option] || 0
})

const totalReward = computed(() => {
  return myVotes.value
    .filter(v => v.is_correct)
    .reduce((sum, v) => sum + (v.reward_earned || predictionDetail.value?.base_reward_amount || 10), 0)
})

const correctRate = computed(() => {
  const total = predictionDetail.value?.total_votes || 0
  if (total === 0) return 0
  const correct = correctVotesTotal.value
  return Math.round((correct / total) * 100)
})

const totalRewardDistributed = computed(() => {
  const baseAmount = predictionDetail.value?.base_reward_amount || 10
  return correctVotesTotal.value * baseAmount
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

function getOptionPercentage(optionValue) {
  const total = predictionDetail.value?.total_votes || 0
  if (total === 0) return 0
  const count = voteDistribution.value[optionValue] || 0
  return Math.round((count / total) * 100)
}

function goBack() {
  router.push('/prediction')
}

function goToHistory() {
  router.push({ 
    path: '/prediction', 
    query: { tab: 'history' } 
  })
}

async function loadPredictionDetail() {
  try {
    loading.value = true
    predictionDetail.value = await predictionApi.getDetail(predictionId.value)
  } catch (error) {
    console.error('加载结果详情失败:', error)
    ElMessage.error('加载结果详情失败')
  } finally {
    loading.value = false
  }
}

async function claimReward(voteId) {
  if (!voteId) return
  
  try {
    await ElMessageBox.confirm(
      '确定要领取奖励吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    claimingVote.value = voteId
    
    const result = await predictionApi.claimReward(voteId)
    
    ElMessage.success({
      message: `领取成功！获得 ${result.reward_amount || 0} ${result.reward_asset_type === 'point' ? '高阶星尘' : '星元碎片'}`,
      duration: 3000
    })
    
    await loadPredictionDetail()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('领取奖励失败:', error)
      ElMessage.error(error.message || '领取失败')
    }
  } finally {
    claimingVote.value = null
  }
}

onMounted(() => {
  loadPredictionDetail()
})
</script>

<style lang="scss" scoped>
.prediction-result {
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

.result-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 900px;
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

.result-content {
  background: rgba(15, 15, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  overflow: hidden;
}

.result-header {
  padding: 32px;
  background: linear-gradient(135deg, rgba(132, 204, 22, 0.05) 0%, rgba(34, 197, 94, 0.02) 100%);
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
  text-align: center;
  
  .result-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: rgba(132, 204, 22, 0.15);
    border-radius: 20px;
    margin-bottom: 16px;
    
    .badge-icon {
      font-size: 18px;
    }
    
    .badge-text {
      font-size: 14px;
      font-weight: 600;
      color: #84CC16;
    }
  }
  
  .result-title {
    font-size: 28px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 8px 0;
  }
  
  .result-desc {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0 0 16px 0;
  }
  
  .result-meta {
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    
    .meta-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 0 32px;
  padding-top: 24px;
  
  .section-icon {
    font-size: 18px;
  }
  
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .vote-summary {
    margin-left: auto;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.correct-option-section {
  padding-bottom: 24px;
  
  .correct-option-display {
    padding: 0 32px;
    
    .option-card {
      display: flex;
      align-items: center;
      gap: 20px;
      padding: 24px;
      background: linear-gradient(135deg, rgba(132, 204, 22, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%);
      border: 2px solid rgba(132, 204, 22, 0.3);
      border-radius: 16px;
      
      &.correct {
        animation: pulse-correct 2s ease-in-out infinite;
      }
      
      @keyframes pulse-correct {
        0%, 100% { box-shadow: 0 0 20px rgba(132, 204, 22, 0.2); }
        50% { box-shadow: 0 0 40px rgba(132, 204, 22, 0.4); }
      }
      
      .option-icon {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #84CC16 0%, #22C55E 100%);
        border-radius: 50%;
        font-size: 24px;
        font-weight: bold;
        color: #fff;
      }
      
      .option-info {
        .option-value {
          font-size: 24px;
          font-weight: 700;
          color: #84CC16;
          margin-bottom: 4px;
        }
        
        .option-stats {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.6);
          
          .correct-rate {
            margin-left: 8px;
            color: #84CC16;
            font-weight: 600;
          }
        }
      }
    }
  }
}

.my-votes-section {
  padding-bottom: 24px;
  
  .my-votes-list {
    padding: 0 32px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .my-vote-card {
    display: flex;
    align-items: stretch;
    gap: 16px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(139, 92, 246, 0.08);
    border-radius: 12px;
    transition: all 0.3s ease;
    
    &.correct {
      border-left: 4px solid #84CC16;
      background: rgba(132, 204, 22, 0.05);
    }
    
    &.wrong {
      border-left: 4px solid #6B7280;
      opacity: 0.8;
    }
    
    .vote-status {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 0 12px;
      border-right: 1px solid rgba(139, 92, 246, 0.08);
      
      .status-icon {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 8px;
        
        &.correct {
          background: rgba(132, 204, 22, 0.15);
          color: #84CC16;
        }
        
        &.wrong {
          background: rgba(107, 114, 128, 0.1);
          color: #9CA3AF;
        }
      }
      
      .status-text {
        font-size: 12px;
        font-weight: 600;
        
        .correct & { color: #84CC16; }
        .wrong & { color: #9CA3AF; }
      }
    }
    
    .vote-detail {
      flex: 1;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      
      .vote-info {
        .vote-number {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 6px;
        }
        
        .vote-option {
          font-size: 15px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 6px;
          
          .option-highlight {
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
          }
        }
        
        .vote-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
        }
      }
      
      .vote-reward {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
        
        .reward-info {
          display: flex;
          align-items: baseline;
          gap: 6px;
          
          .reward-label {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.4);
          }
          
          .reward-amount {
            font-size: 20px;
            font-weight: 700;
            color: #84CC16;
          }
          
          .reward-unit {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
          }
        }
        
        .claim-btn {
          background: linear-gradient(135deg, #84CC16 0%, #22C55E 100%);
          border: none;
          padding: 10px 20px;
          font-size: 14px;
          font-weight: 600;
          
          &:hover {
            box-shadow: 0 4px 16px rgba(132, 204, 22, 0.3);
          }
        }
        
        .claimed-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: rgba(132, 204, 22, 0.1);
          border-radius: 8px;
          
          .claimed-icon {
            color: #84CC16;
          }
          
          .claimed-text {
            font-size: 13px;
            color: #84CC16;
          }
        }
      }
    }
  }
  
  .total-reward {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 8px;
    margin-top: 20px;
    padding: 16px 24px;
    margin-left: 32px;
    margin-right: 32px;
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
    border-radius: 12px;
    border: 1px solid rgba(251, 191, 36, 0.2);
    
    .total-label {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
    }
    
    .total-amount {
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .total-unit {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.no-vote-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  
  .no-vote-icon {
    font-size: 48px;
  }
  
  .no-vote-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
  }
}

.distribution-section {
  padding-bottom: 24px;
  
  .distribution-chart {
    padding: 0 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .distribution-row {
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 12px;
    
    &.correct {
      background: rgba(132, 204, 22, 0.05);
      border: 1px solid rgba(132, 204, 22, 0.2);
    }
    
    .option-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      
      .option-label {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.75);
      }
      
      .option-count {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
        
        .correct-mark {
          margin-left: 8px;
          padding: 2px 8px;
          background: rgba(132, 204, 22, 0.15);
          border-radius: 4px;
          color: #84CC16;
          font-weight: 600;
        }
      }
    }
    
    .progress-wrapper {
      width: 100%;
      height: 24px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      overflow: hidden;
      position: relative;
    }
    
    .progress-bar {
      height: 100%;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      padding-right: 12px;
      transition: width 0.5s ease;
      min-width: 40px;
      
      .progress-percent {
        font-size: 12px;
        font-weight: 600;
        color: #fff;
      }
    }
  }
}

.evidence-section {
  padding-bottom: 24px;
  
  .evidence-content {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 0 32px;
    
    .evidence-icon {
      font-size: 32px;
    }
    
    .evidence-text {
      flex: 1;
      
      .oracle-source {
        font-size: 13px;
        font-weight: 600;
        color: #a78bfa;
        margin-bottom: 8px;
      }
      
      .evidence-desc {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.6);
        line-height: 1.6;
        margin: 0;
      }
    }
  }
}

.stats-section {
  padding-bottom: 24px;
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    padding: 0 32px;
    
    @media (max-width: 600px) {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .stat-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 20px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(139, 92, 246, 0.08);
      border-radius: 12px;
      
      .stat-icon {
        font-size: 24px;
      }
      
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: #8B5CF6;
      }
      
      .stat-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
      }
    }
  }
}

.action-section {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px 32px 32px;
  border-top: 1px solid rgba(139, 92, 246, 0.08);
  
  .back-hall-btn,
  .view-history-btn {
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 600;
    
    &.back-hall-btn {
      background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
      border: none;
      
      &:hover {
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4);
      }
    }
  }
}

@media (max-width: 768px) {
  .result-main {
    padding: 16px;
  }
  
  .result-header {
    padding: 24px 16px;
    
    .result-title {
      font-size: 22px;
    }
  }
  
  .section-header {
    padding-left: 16px;
    padding-right: 16px;
  }
  
  .correct-option-display,
  .my-votes-list,
  .distribution-chart,
  .evidence-content,
  .stats-grid,
  .action-section {
    padding-left: 16px;
    padding-right: 16px;
  }
  
  .my-vote-card {
    flex-direction: column;
    
    .vote-status {
      flex-direction: row;
      border-right: none;
      border-bottom: 1px solid rgba(139, 92, 246, 0.08);
      padding-bottom: 12px;
      padding-right: 0;
      
      .status-icon {
        margin-bottom: 0;
        margin-right: 12px;
      }
    }
    
    .vote-detail {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      
      .vote-reward {
        align-self: stretch;
        align-items: center;
        flex-direction: row;
        justify-content: space-between;
      }
    }
  }
  
  .action-section {
    flex-direction: column;
    
    .back-hall-btn,
    .view-history-btn {
      width: 100%;
    }
  }
}
</style>
