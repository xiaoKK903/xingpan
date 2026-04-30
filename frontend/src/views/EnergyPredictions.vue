<template>
  <div class="predictions-page">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="predictions-main">
      <div class="page-header">
        <div class="header-back" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">
          <div class="title-icon">
            <el-icon size="28"><Search /></el-icon>
          </div>
          <div class="title-text">
            <h1>预测竞技场</h1>
            <p>预判明日星象，平分星尘大奖</p>
          </div>
        </div>
      </div>

      <div class="stats-header">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ myStats.totalPredictions || 0 }}</div>
            <div class="stat-label">参与次数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon success">
            <el-icon><Checked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ myStats.correctCount || 0 }}</div>
            <div class="stat-label">猜对次数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon star">
            <el-icon><Star /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ myStats.totalRewards || 0 }}</div>
            <div class="stat-label">获得星尘</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon rate">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ myStats.accuracyRate || 0 }}%</div>
            <div class="stat-label">准确率</div>
          </div>
        </div>
      </div>

      <div class="tabs-container">
        <el-tabs v-model="activeTab" class="prediction-tabs">
          <el-tab-pane label="今日预测" name="open">
            <div class="predictions-list" v-if="openPredictions?.length > 0">
              <div class="prediction-card" v-for="pred in openPredictions" :key="pred.id">
                <div class="prediction-header">
                  <div class="prediction-type">
                    <span class="type-badge">{{ getPredictionTypeLabel(pred.prediction_type) }}</span>
                  </div>
                  <div class="prediction-time">
                    <el-icon><Clock /></el-icon>
                    <span>预测日期：{{ pred.target_date }}</span>
                  </div>
                </div>

                <div class="prediction-info">
                  <h3 class="prediction-title">{{ pred.title }}</h3>
                  <p class="prediction-desc">{{ pred.description }}</p>
                </div>

                <div class="voting-section" v-if="!pred.user_vote">
                  <div class="voting-options">
                    <div 
                      class="option-item" 
                      v-for="(option, index) in pred.options" 
                      :key="index"
                      :class="{ selected: selectedOption[pred.id] === pred.option_values?.[index] }"
                      @click="selectOption(pred.id, pred.option_values?.[index])"
                    >
                      <span class="option-text">{{ option }}</span>
                      <div 
                        class="option-percent" 
                        v-if="pred.vote_distribution && pred.total_votes > 0"
                      >
                        {{ getVotePercent(pred.vote_distribution[pred.option_values?.[index]], pred.total_votes) }}%
                      </div>
                    </div>
                  </div>

                  <div class="voting-actions">
                    <div class="confidence-selector">
                      <span class="selector-label">信心值：</span>
                      <el-slider 
                        v-model="confidenceLevel[pred.id]" 
                        :min="10" 
                        :max="100" 
                        :step="10"
                        :show-tooltip="false"
                      >
                        <template #default="{ value }">
                          <span class="confidence-value">{{ value }}%</span>
                        </template>
                      </el-slider>
                    </div>
                    <el-button 
                      type="primary" 
                      :loading="votingPrediction === pred.id"
                      :disabled="!selectedOption[pred.id]"
                      @click="castVote(pred)"
                      class="vote-btn"
                    >
                      确认投票
                    </el-button>
                  </div>
                </div>

                <div class="voted-section" v-else>
                  <div class="voted-indicator">
                    <el-icon size="20"><Checked /></el-icon>
                    <span>已投票</span>
                  </div>
                  <div class="my-vote">
                    <span class="vote-label">我的选择：</span>
                    <span class="vote-value">{{ getSelectedOptionLabel(pred) }}</span>
                  </div>
                  <div class="vote-stats">
                    <div class="stat">
                      <span class="stat-label">信心值</span>
                      <span class="stat-value">{{ pred.user_vote.confidence }}%</span>
                    </div>
                    <div class="stat">
                      <span class="stat-label">当前支持率</span>
                      <span class="stat-value">
                        {{ getVotePercent(pred.vote_distribution?.[pred.user_vote.selected_option], pred.total_votes) }}%
                      </span>
                    </div>
                  </div>

                  <div class="vote-distribution" v-if="pred.vote_distribution && pred.total_votes > 0">
                    <div class="distribution-item" v-for="(option, index) in pred.options" :key="index">
                      <div class="distribution-label">
                        <span class="option-name">{{ option }}</span>
                        <span class="option-count">{{ pred.vote_distribution?.[pred.option_values?.[index]] || 0 }} 票</span>
                      </div>
                      <el-progress 
                        :percentage="getVotePercent(pred.vote_distribution?.[pred.option_values?.[index]], pred.total_votes)" 
                        :stroke-width="6"
                        :color="pred.user_vote?.selected_option === pred.option_values?.[index] ? '#a78bfa' : 'rgba(255,255,255,0.2)'"
                      />
                    </div>
                  </div>

                  <div class="voting-total">
                    <span class="total-label">总投票数：</span>
                    <span class="total-value">{{ pred.total_votes || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="empty-state" v-else>
              <el-icon size="64"><Search /></el-icon>
              <h3>今日暂无开放预测</h3>
              <p>明日预测将于今日晚些时候开放，敬请期待</p>
            </div>
          </el-tab-pane>

          <el-tab-pane label="我的预测" name="history">
            <div class="history-list" v-if="myHistory?.length > 0">
              <div class="history-card" v-for="item in myHistory" :key="item.prediction?.id">
                <div class="history-header">
                  <div class="history-type">
                    <span class="type-badge">{{ getPredictionTypeLabel(item.prediction?.prediction_type) }}</span>
                    <span class="pred-date">{{ item.prediction?.target_date }}</span>
                  </div>
                  <div class="history-status" :class="getStatusClass(item)">
                    <template v-if="item.prediction?.is_resolved">
                      <el-icon v-if="item.vote?.is_correct"><Checked /></el-icon>
                      <el-icon v-else-if="item.vote?.is_correct === false"><Close /></el-icon>
                      <span>{{ item.vote?.is_correct ? '猜对了' : '猜错了' }}</span>
                    </template>
                    <template v-else>
                      <el-icon><Clock /></el-icon>
                      <span>等待结算</span>
                    </template>
                  </div>
                </div>

                <div class="history-body">
                  <h4 class="history-title">{{ item.prediction?.title }}</h4>
                  <div class="history-vote">
                    <span class="vote-label">我的选择：</span>
                    <span class="vote-value">{{ getOptionLabelFromPrediction(item.prediction, item.vote?.selected_option) }}</span>
                  </div>
                  <div class="history-actual" v-if="item.prediction?.is_resolved">
                    <span class="actual-label">实际结果：</span>
                    <span class="actual-value">{{ getOptionLabelFromPrediction(item.prediction, item.prediction?.actual_result) }}</span>
                  </div>
                </div>

                <div class="history-footer">
                  <div class="reward-info" v-if="item.vote?.reward_earned > 0">
                    <el-icon><Star /></el-icon>
                    <span class="reward-value">+{{ item.vote?.reward_earned }} 星尘</span>
                    <span class="reward-status" :class="{ claimed: item.vote?.reward_claimed }">
                      {{ item.vote?.reward_claimed ? '已领取' : '未领取' }}
                    </span>
                  </div>
                  <div class="accuracy-info" v-if="item.prediction?.is_resolved">
                    <span class="accuracy-label">社区准确率：</span>
                    <span class="accuracy-value">{{ item.prediction?.accuracy_score || 0 }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="empty-state" v-else>
              <el-icon size="64"><Document /></el-icon>
              <h3>暂无预测记录</h3>
              <p>参与今日预测，开始你的预测之旅</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Search, Trophy, Checked, Star,
  DataAnalysis, Clock, Close, Document
} from '@element-plus/icons-vue'
import { energyCommunityApi } from '@/api'

const router = useRouter()

const activeTab = ref('open')
const openPredictions = ref([])
const myHistory = ref([])
const votingPrediction = ref(null)
const selectedOption = ref({})
const confidenceLevel = ref({})

const myStats = ref({
  totalPredictions: 0,
  correctCount: 0,
  totalRewards: 0,
  accuracyRate: 0
})

const PREDICTION_TYPES = {
  mood: { label: '集体情绪' },
  dominant_planet: { label: '主导行星' },
  social_event: { label: '社交事件' },
  aspect_pattern: { label: '相位格局' }
}

const getStarStyle = (i) => {
  const left = Math.random() * 100
  const top = Math.random() * 100
  const delay = Math.random() * 5
  return {
    left: `${left}%`,
    top: `${top}%`,
    animationDelay: `${delay}s`
  }
}

const getPredictionTypeLabel = (type) => PREDICTION_TYPES[type]?.label || type

const getVotePercent = (votes, total) => {
  if (!total || total === 0) return 0
  return Math.round((votes || 0) / total * 100)
}

const getStatusClass = (item) => {
  if (!item.prediction?.is_resolved) return 'pending'
  if (item.vote?.is_correct) return 'correct'
  return 'wrong'
}

const getSelectedOptionLabel = (prediction) => {
  if (!prediction.user_vote) return ''
  return getOptionLabelFromPrediction(prediction, prediction.user_vote.selected_option)
}

const getOptionLabelFromPrediction = (prediction, optionValue) => {
  if (!prediction || !optionValue) return ''
  const index = prediction.option_values?.indexOf(optionValue)
  if (index >= 0 && prediction.options?.[index]) {
    return prediction.options[index]
  }
  return optionValue
}

const selectOption = (predictionId, optionValue) => {
  selectedOption.value[predictionId] = optionValue
  if (!confidenceLevel.value[predictionId]) {
    confidenceLevel.value[predictionId] = 50
  }
}

const loadOpenPredictions = async () => {
  try {
    const data = await energyCommunityApi.getOpenPredictions()
    openPredictions.value = data?.predictions || []
    
    for (const pred of openPredictions.value) {
      if (pred.user_vote) {
        selectedOption.value[pred.id] = pred.user_vote.selected_option
        confidenceLevel.value[pred.id] = pred.user_vote.confidence
      }
    }
  } catch (error) {
    console.error('加载预测失败:', error)
  }
}

const loadMyHistory = async () => {
  try {
    const data = await energyCommunityApi.getMyPredictionsHistory(50)
    myHistory.value = data?.history || []
    
    let correct = 0
    let total = 0
    let rewards = 0
    
    for (const item of myHistory.value) {
      if (item.prediction?.is_resolved && item.vote) {
        total++
        if (item.vote.is_correct) {
          correct++
          rewards += item.vote.reward_earned || 0
        }
      }
    }
    
    myStats.value.totalPredictions = myHistory.value.length
    myStats.value.correctCount = correct
    myStats.value.totalRewards = rewards
    myStats.value.accuracyRate = total > 0 ? Math.round(correct / total * 100) : 0
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

const castVote = async (prediction) => {
  if (!selectedOption.value[prediction.id]) {
    ElMessage.warning('请选择一个选项')
    return
  }
  
  votingPrediction.value = prediction.id
  try {
    const result = await energyCommunityApi.castVote({
      prediction_id: prediction.id,
      selected_option: selectedOption.value[prediction.id],
      confidence: confidenceLevel.value[prediction.id] || 50,
      stardust_bet: 0
    })
    
    if (result.success || result.vote) {
      ElMessage.success('投票成功！')
      loadOpenPredictions()
    }
  } catch (error) {
    console.error('投票失败:', error)
    ElMessage.error('投票失败，请重试')
  } finally {
    votingPrediction.value = null
  }
}

onMounted(() => {
  loadOpenPredictions()
  loadMyHistory()
})
</script>

<style scoped lang="scss">
.predictions-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
  position: relative;
  overflow-x: hidden;
}

.stars-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.star {
  position: absolute;
  width: 2px;
  height: 2px;
  background: white;
  border-radius: 50%;
  animation: twinkle 3s infinite ease-in-out;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.predictions-main {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;

  .header-back {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 16px;
    transition: color 0.2s;

    &:hover {
      color: #a78bfa;
    }
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 16px;

    .title-icon {
      width: 56px;
      height: 56px;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(139, 92, 246, 0.1));
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #a78bfa;
      border: 1px solid rgba(139, 92, 246, 0.3);
    }

    .title-text {
      h1 {
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin: 0 0 4px;
      }

      p {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0;
      }
    }
  }
}

.stats-header {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;

  .stat-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.2), rgba(167, 139, 250, 0.1));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a78bfa;
    font-size: 20px;

    &.success {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1));
      color: #22c55e;
    }

    &.star {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.1));
      color: #f59e0b;
    }

    &.rate {
      background: linear-gradient(135deg, rgba(96, 165, 250, 0.2), rgba(96, 165, 250, 0.1));
      color: #60a5fa;
    }
  }

  .stat-info {
    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: rgba(255, 255, 255, 0.9);
      margin-bottom: 2px;
    }

    .stat-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.4);
    }
  }
}

.tabs-container {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 24px;
}

:deep(.prediction-tabs) {
  .el-tabs__header {
    margin-bottom: 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .el-tabs__nav-wrap::after {
    display: none;
  }

  .el-tabs__item {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.5);
    font-weight: 500;
    padding: 0 24px 16px;

    &.is-active {
      color: #a78bfa;
      font-weight: 600;
    }
  }

  .el-tabs__active-bar {
    background: linear-gradient(90deg, #a78bfa, #f472b6);
    height: 3px;
    border-radius: 2px;
  }
}

.predictions-list,
.history-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.prediction-card,
.history-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .type-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    background: rgba(167, 139, 250, 0.15);
    color: #a78bfa;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
  }

  .prediction-time {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.prediction-info {
  margin-bottom: 20px;

  .prediction-title {
    font-size: 17px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.95);
    margin: 0 0 4px;
  }

  .prediction-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0;
  }
}

.voting-section {
  .voting-options {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }

  .option-item {
    position: relative;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.03);
    border: 2px solid transparent;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(167, 139, 250, 0.3);
    }

    &.selected {
      background: rgba(167, 139, 250, 0.15);
      border-color: #a78bfa;
    }

    .option-text {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.85);
      font-weight: 500;
    }

    .option-percent {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 13px;
      font-weight: 600;
      color: #a78bfa;
    }
  }
}

.voting-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;

  .confidence-selector {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;

    .selector-label {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
      white-space: nowrap;
    }

    :deep(.el-slider) {
      flex: 1;
      margin: 0;
    }

    .confidence-value {
      font-size: 14px;
      font-weight: 600;
      color: #a78bfa;
      min-width: 40px;
      text-align: right;
    }
  }

  .vote-btn {
    min-width: 100px;
    background: linear-gradient(135deg, #a78bfa, #8b5cf6);
    border: none;

    &:hover {
      background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    }

    &:disabled {
      background: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.3);
    }
  }
}

.voted-section {
  .voted-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 12px;
  }

  .my-vote {
    margin-bottom: 16px;

    .vote-label {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin-right: 6px;
    }

    .vote-value {
      font-size: 14px;
      font-weight: 600;
      color: #a78bfa;
    }
  }

  .vote-stats {
    display: flex;
    gap: 24px;
    margin-bottom: 16px;

    .stat {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .stat-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
      }

      .stat-value {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.85);
      }
    }
  }

  .vote-distribution {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 16px;

    .distribution-item {
      .distribution-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
        font-size: 12px;

        .option-name {
          color: rgba(255, 255, 255, 0.7);
        }

        .option-count {
          color: rgba(255, 255, 255, 0.4);
        }
      }
    }
  }

  .voting-total {
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    font-size: 13px;

    .total-label {
      color: rgba(255, 255, 255, 0.5);
    }

    .total-value {
      color: #a78bfa;
      font-weight: 600;
    }
  }
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .history-type {
    display: flex;
    align-items: center;
    gap: 8px;

    .type-badge {
      padding: 4px 10px;
      background: rgba(167, 139, 250, 0.15);
      color: #a78bfa;
      border-radius: 16px;
      font-size: 11px;
      font-weight: 600;
    }

    .pred-date {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.4);
    }
  }

  .history-status {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;

    &.pending {
      background: rgba(96, 165, 250, 0.15);
      color: #60a5fa;
    }

    &.correct {
      background: rgba(34, 197, 94, 0.15);
      color: #22c55e;
    }

    &.wrong {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
    }
  }
}

.history-body {
  margin-bottom: 12px;

  .history-title {
    font-size: 15px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 8px;
  }

  .history-vote,
  .history-actual {
    font-size: 13px;
    margin-bottom: 4px;

    .vote-label,
    .actual-label {
      color: rgba(255, 255, 255, 0.5);
    }

    .vote-value,
    .actual-value {
      color: rgba(255, 255, 255, 0.85);
      font-weight: 500;
    }
  }

  .actual-value {
    color: #22c55e !important;
    font-weight: 600 !important;
  }
}

.history-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);

  .reward-info {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #f59e0b;

    .el-icon {
      font-size: 14px;
    }

    .reward-value {
      font-weight: 600;
    }

    .reward-status {
      font-size: 11px;
      padding: 2px 8px;
      background: rgba(245, 158, 11, 0.15);
      border-radius: 10px;
      color: #f59e0b;

      &.claimed {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
      }
    }
  }

  .accuracy-info {
    font-size: 12px;

    .accuracy-label {
      color: rgba(255, 255, 255, 0.4);
    }

    .accuracy-value {
      color: rgba(255, 255, 255, 0.7);
      font-weight: 500;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.4);

  .el-icon {
    margin-bottom: 16px;
    opacity: 0.5;
  }

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 8px;
  }

  p {
    font-size: 13px;
    margin: 0;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .stats-header {
    grid-template-columns: repeat(2, 1fr);
  }

  .voting-options {
    grid-template-columns: 1fr !important;
  }

  .voting-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .confidence-selector {
    width: 100%;
  }

  .vote-btn {
    width: 100%;
  }
}
</style>
