<template>
  <div class="element-quest">
    <div class="stars-bg">
      <div v-for="i in 80" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="quest-main">
      <div class="quick-nav">
        <div class="nav-item" @click="goToResonance">
          <span class="nav-icon">🌌</span>
          <span class="nav-text">星能共鸣池</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item active">
          <span class="nav-icon">🎁</span>
          <span class="nav-text">元素缺角寻宝</span>
          <span class="nav-arrow">→</span>
        </div>
      </div>

      <div class="quest-header">
        <div class="header-icon">
          <span class="header-emoji">🎁</span>
        </div>
        <div class="header-text">
          <h1 class="main-title">元素缺角寻宝</h1>
          <p class="subtitle">基于星盘四元素能量，寻找你的能量互补者</p>
        </div>
        <div class="user-assets" v-if="userAssets">
          <div class="asset-item">
            <span class="asset-icon">💎</span>
            <span class="asset-value">{{ userAssets.stardust_fragment || 0 }}</span>
            <span class="asset-label">星元碎片</span>
          </div>
        </div>
      </div>

      <div v-if="!hasProfile" class="no-profile-section">
        <div class="no-profile-card">
          <div class="no-profile-icon">🔮</div>
          <h3 class="no-profile-title">尚未进行元素分析</h3>
          <p class="no-profile-desc">
            元素缺角寻宝需要先分析您的星盘四元素能量分布，
            <br />找到您的能量缺角，才能匹配到互补的灵魂伴侣。
          </p>
          <el-button 
            type="primary" 
            size="large" 
            :loading="analyzing" 
            @click="analyzeMyElements"
            class="analyze-btn"
          >
            <el-icon><MagicStick /></el-icon>
            开始元素分析
          </el-button>
        </div>
      </div>

      <div v-else class="quest-content">
        <div class="element-profile-card">
          <h3 class="section-title">
            <span class="title-icon">✨</span>
            我的元素画像
          </h3>
          
          <div class="element-chart-section">
            <div class="element-bars">
              <div 
                v-for="elem in sortedElements" 
                :key="elem.element" 
                class="element-bar-row"
              >
                <div class="element-info">
                  <span class="element-symbol">{{ elem.info?.symbol || '?' }}</span>
                  <span class="element-name">{{ elem.info?.name_cn || elem.element }}</span>
                  <span class="element-level" :class="elem.level">
                    {{ elem.level_label }}
                  </span>
                </div>
                <div class="bar-container">
                  <div 
                    class="bar-fill" 
                    :class="`bar-${elem.element}`"
                    :style="{ width: `${elem.percentage}%` }"
                  ></div>
                  <span class="bar-score">{{ elem.score }}</span>
                </div>
              </div>
            </div>
            
            <div class="deficiency-info" v-if="profile.has_deficiency">
              <div class="deficiency-header">
                <span class="deficiency-icon">⚡</span>
                <span class="deficiency-title">能量缺角</span>
              </div>
              <div class="deficiency-content">
                <p class="deficiency-text">
                  你的 <strong class="deficiency-element">
                    {{ deficiencyElementInfo?.name_cn || profile.primary_deficiency }}
                  </strong> 能量需要补充
                </p>
                <p class="deficiency-hint">
                  寻宝匹配将为你寻找能够补充这份能量缺角的伙伴
                </p>
              </div>
            </div>
            
            <div class="dominant-info" v-else>
              <div class="dominant-header">
                <span class="dominant-icon">🌟</span>
                <span class="dominant-title">能量平衡</span>
              </div>
              <div class="dominant-content">
                <p class="dominant-text">你的四元素能量分布较为均衡</p>
              </div>
            </div>
          </div>

          <div class="energy-tags-section" v-if="energyTags.length > 0">
            <h4 class="tags-title">能量标签</h4>
            <div class="tags-list">
              <span 
                v-for="tag in energyTags" 
                :key="tag.id" 
                class="energy-tag"
                :class="`tag-${tag.tag_category}`"
              >
                {{ tag.tag_name }}
              </span>
            </div>
          </div>
        </div>

        <div class="quest-status-card">
          <h3 class="section-title">
            <span class="title-icon">🎯</span>
            今日寻宝状态
          </h3>
          
          <div class="status-grid">
            <div class="status-item">
              <div class="status-value">{{ questStatus.availability?.remaining_count || 0 }}</div>
              <div class="status-label">剩余次数</div>
            </div>
            <div class="status-item">
              <div class="status-value">{{ questStatus.availability?.used_count || 0 }} / {{ questStatus.availability?.max_count || 3 }}</div>
              <div class="status-label">已使用</div>
            </div>
            <div class="status-item">
              <div class="status-value">{{ questStatus.availability?.refresh_remaining || 0 }}</div>
              <div class="status-label">可刷新</div>
            </div>
          </div>

          <div class="quest-actions">
            <el-button 
              type="primary" 
              size="large" 
              :loading="matching" 
              :disabled="!canQuest"
              @click="startBlindBoxMatch"
              class="match-btn"
            >
              <el-icon><Gift /></el-icon>
              开启盲盒寻宝
            </el-button>
            
            <el-button 
              :disabled="!canRefresh"
              @click="showRefreshDialog"
              class="refresh-btn"
            >
              <el-icon><Refresh /></el-icon>
              刷新次数 (20💎)
            </el-button>
          </div>
        </div>

        <div class="blind-boxes-section" v-if="activeBlindBoxes.length > 0">
          <h3 class="section-title">
            <span class="title-icon">📦</span>
            待揭示的盲盒
          </h3>
          
          <div class="blind-boxes-grid">
            <div 
              v-for="box in activeBlindBoxes" 
              :key="box.id" 
              class="blind-box-card"
              @click="openBlindBoxDetail(box.id)"
            >
              <div class="box-icon">
                <span class="box-emoji">🎁</span>
              </div>
              <div class="box-info">
                <div class="box-id">{{ box.blind_box_id }}</div>
                <div class="box-score">
                  匹配度: <span class="score-value">{{ box.complement_score }}</span>
                </div>
                <div class="box-type" :class="box.match_type">
                  {{ box.match_type === 'complementary' ? '能量互补' : '随机匹配' }}
                </div>
              </div>
              <div class="box-action">
                <el-button type="primary" size="small" @click.stop="openBlindBoxDetail(box.id)">
                  查看线索
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="history-section" v-if="questHistory.length > 0">
          <h3 class="section-title">
            <span class="title-icon">📜</span>
            近期寻宝记录
          </h3>
          
          <div class="history-list">
            <div 
              v-for="record in questHistory.slice(0, 5)" 
              :key="record.id" 
              class="history-item"
            >
              <div class="history-date">
                {{ formatDate(record.created_at) }}
              </div>
              <div class="history-type">
                {{ record.quest_type === 'blind_box_match' ? '盲盒寻宝' : record.quest_type }}
              </div>
              <div class="history-reward" v-if="record.reward_earned">
                +{{ record.reward_earned }} 💎
              </div>
              <div class="history-status" :class="record.quest_status">
                {{ record.quest_status === 'completed' ? '已完成' : record.quest_status }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showBlindBoxDetail" 
      title="盲盒详情" 
      width="600px"
      class="blind-box-dialog"
    >
      <div v-if="currentBlindBox" class="blind-box-detail">
        <div class="detail-header">
          <span class="detail-id">{{ currentBlindBox.blind_box_id }}</span>
          <span class="detail-type" :class="currentBlindBox.match_type">
            {{ currentBlindBox.match_type === 'complementary' ? '能量互补匹配' : '随机匹配' }}
          </span>
        </div>

        <div class="clues-section" v-if="currentBlindBox.clues && currentBlindBox.clues.length > 0">
          <h4 class="clues-title">🔍 模糊线索</h4>
          <div class="clues-list">
            <div 
              v-for="(clue, index) in currentBlindBox.clues" 
              :key="index" 
              class="clue-item"
              :class="`clue-${clue.hint_level}`"
            >
              <span class="clue-number">#{{ index + 1 }}</span>
              <span class="clue-text">{{ clue.clue }}</span>
            </div>
          </div>
        </div>

        <div class="completeness-section" v-if="currentBlindBox.completeness_score !== undefined">
          <h4 class="completeness-title">⚡ 缺角补全指数</h4>
          <div class="completeness-bar">
            <div 
              class="completeness-fill"
              :style="{ width: `${currentBlindBox.completeness_score}%` }"
            ></div>
            <span class="completeness-value">{{ currentBlindBox.completeness_score }}%</span>
          </div>
        </div>

        <div class="revealed-section" v-if="currentBlindBox.is_revealed">
          <div class="revealed-header">
            <span class="revealed-icon">✨</span>
            <span class="revealed-title">已揭示</span>
          </div>
          <div class="matched-user-info" v-if="currentBlindBox.matched_user_info">
            <div class="user-avatar">
              <span class="avatar-placeholder">👤</span>
            </div>
            <div class="user-details">
              <div class="user-name">{{ currentBlindBox.matched_user_info.username || '神秘用户' }}</div>
              <div class="user-element-info" v-if="currentBlindBox.matched_user_info.element_profile">
                <span v-if="currentBlindBox.matched_user_info.element_profile.dominant_element">
                  主导: {{ getElementName(currentBlindBox.matched_user_info.element_profile.dominant_element) }}
                </span>
                <span v-if="currentBlindBox.matched_user_info.element_profile.primary_deficiency" class="deficiency-tag">
                  缺角: {{ getElementName(currentBlindBox.matched_user_info.element_profile.primary_deficiency) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button 
            v-if="!currentBlindBox.is_revealed"
            type="primary" 
            size="large"
            :loading="revealing"
            @click="revealBlindBox"
            class="reveal-btn"
          >
            <el-icon><View /></el-icon>
            揭示盲盒
          </el-button>
          
          <el-button 
            v-else-if="!currentBlindBox.is_claimed"
            type="success" 
            size="large"
            :loading="claiming"
            @click="claimReward"
            class="claim-btn"
          >
            <el-icon><Coin /></el-icon>
            领取奖励 (+{{ currentBlindBox.reward_earned || 10 }}💎)
          </el-button>
          
          <el-button 
            v-else
            type="info" 
            size="large"
            disabled
          >
            奖励已领取
          </el-button>
        </div>
      </div>
    </el-dialog>

    <el-dialog 
      v-model="showRefreshConfirm" 
      title="确认刷新" 
      width="400px"
    >
      <div class="refresh-confirm-content">
        <p>确定要消耗 <strong class="cost-highlight">20 星元碎片</strong> 刷新今日寻宝次数吗？</p>
        <p class="refresh-hint">今日剩余刷新次数: {{ questStatus.availability?.refresh_remaining || 0 }}</p>
      </div>
      <template #footer>
        <el-button @click="showRefreshConfirm = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="refreshing"
          @click="confirmRefresh"
        >
          确认刷新
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { elementQuestApi, starResonanceApi } from '@/api'

const router = useRouter()

const analyzing = ref(false)
const matching = ref(false)
const revealing = ref(false)
const claiming = ref(false)
const refreshing = ref(false)

const hasProfile = ref(false)
const profile = ref(null)
const energyTags = ref([])
const userAssets = ref(null)
const questStatus = ref({
  availability: {}
})
const activeBlindBoxes = ref([])
const questHistory = ref([])

const showBlindBoxDetail = ref(false)
const currentBlindBox = ref(null)
const showRefreshConfirm = ref(false)

const ELEMENT_NAMES = {
  fire: '火元素',
  earth: '土元素',
  air: '风元素',
  water: '水元素'
}

const sortedElements = computed(() => {
  if (!profile.value || !profile.value.element_data) return []
  const elements = profile.value.element_data.elements
  if (!elements) return []
  return Object.values(elements).sort((a, b) => b.score - a.score)
})

const deficiencyElementInfo = computed(() => {
  if (!profile.value || !profile.value.primary_deficiency) return null
  const elements = profile.value.element_data?.elements
  if (!elements) return null
  const defElem = elements[profile.value.primary_deficiency]
  return defElem?.info || null
})

const canQuest = computed(() => {
  return questStatus.value.availability?.remaining_count > 0
})

const canRefresh = computed(() => {
  return questStatus.value.availability?.refresh_remaining > 0
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

function getElementName(elementKey) {
  return ELEMENT_NAMES[elementKey] || elementKey
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

function goToResonance() {
  router.push('/star-resonance')
}

async function loadAllData() {
  try {
    const [profileResult, statusResult, assetsResult] = await Promise.all([
      elementQuestApi.getMyProfile().catch(() => ({ has_profile: false })),
      elementQuestApi.getQuestStatus().catch(() => ({})),
      starResonanceApi.getPoolStatus().catch(() => ({ user_assets: {} }))
    ])
    
    if (profileResult.has_profile !== false) {
      hasProfile.value = true
      profile.value = profileResult
      
      if (profileResult.element_data) {
        try {
          profile.value.element_data = typeof profileResult.element_data === 'string' 
            ? JSON.parse(profileResult.element_data) 
            : profileResult.element_data
        } catch (e) {
          console.error('解析元素数据失败:', e)
        }
      }
    }
    
    questStatus.value = statusResult
    activeBlindBoxes.value = statusResult.active_blind_boxes || []
    questHistory.value = statusResult.today_quests || []
    
    userAssets.value = {
      stardust_fragment: assetsResult.user_assets?.stardust_fragment_balance || 
                          assetsResult.user_assets?.stardust_fragment || 0
    }
    
    if (hasProfile.value) {
      try {
        const tagsResult = await elementQuestApi.getMyTags()
        energyTags.value = tagsResult.tags || []
      } catch (e) {
        console.warn('加载能量标签失败:', e)
      }
    }
    
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

async function analyzeMyElements() {
  analyzing.value = true
  try {
    const result = await elementQuestApi.analyzeElements()
    ElMessage.success('元素分析完成！')
    await loadAllData()
  } catch (error) {
    console.error('元素分析失败:', error)
    ElMessage.error(error.message || '分析失败，请确保已创建星盘')
  } finally {
    analyzing.value = false
  }
}

async function startBlindBoxMatch() {
  if (!canQuest.value) {
    ElMessage.warning('今日寻宝次数已用完')
    return
  }
  
  matching.value = true
  try {
    const result = await elementQuestApi.createBlindBox()
    ElMessage.success('盲盒匹配成功！')
    
    showBlindBoxDetail.value = true
    currentBlindBox.value = {
      id: result.db_id,
      blind_box_id: result.blind_box_id,
      complement_score: result.complement_score,
      match_type: result.match_type,
      clues: result.clues || [],
      completeness_score: result.completeness_score,
      is_revealed: false,
      is_claimed: false
    }
    
    await loadAllData()
  } catch (error) {
    console.error('盲盒匹配失败:', error)
    ElMessage.error(error.message || '匹配失败')
  } finally {
    matching.value = false
  }
}

async function openBlindBoxDetail(boxId) {
  try {
    const result = await elementQuestApi.getBlindBoxDetail(boxId)
    currentBlindBox.value = result
    showBlindBoxDetail.value = true
  } catch (error) {
    console.error('获取盲盒详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

async function revealBlindBox() {
  if (!currentBlindBox.value) return
  
  revealing.value = true
  try {
    const result = await elementQuestApi.revealBlindBox(currentBlindBox.value.id)
    ElMessage.success('盲盒已揭示！')
    currentBlindBox.value = {
      ...currentBlindBox.value,
      is_revealed: true,
      matched_user_info: result.matched_user,
      reward_earned: result.reward_earned
    }
    await loadAllData()
  } catch (error) {
    console.error('揭示盲盒失败:', error)
    ElMessage.error(error.message || '揭示失败')
  } finally {
    revealing.value = false
  }
}

async function claimReward() {
  if (!currentBlindBox.value) return
  
  claiming.value = true
  try {
    const result = await elementQuestApi.claimBlindBoxReward(currentBlindBox.value.id)
    ElMessage.success(`领取成功！获得 ${result.reward_amount} 星元碎片`)
    currentBlindBox.value = {
      ...currentBlindBox.value,
      is_claimed: true
    }
    await loadAllData()
  } catch (error) {
    console.error('领取奖励失败:', error)
    ElMessage.error(error.message || '领取失败')
  } finally {
    claiming.value = false
  }
}

function showRefreshDialog() {
  if (!canRefresh.value) {
    ElMessage.warning('今日刷新次数已用完')
    return
  }
  showRefreshConfirm.value = true
}

async function confirmRefresh() {
  refreshing.value = true
  try {
    const result = await elementQuestApi.refreshQuestCount()
    ElMessage.success('刷新成功！')
    showRefreshConfirm.value = false
    await loadAllData()
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error(error.message || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadAllData()
})
</script>

<style lang="scss" scoped>
.element-quest {
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

.quest-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.quick-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  
  .nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(.active) {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.3);
    }
    
    &.active {
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%);
      border-color: rgba(139, 92, 246, 0.4);
    }
  }
  
  .nav-icon {
    font-size: 18px;
  }
  
  .nav-text {
    font-size: 14px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.75);
  }
  
  .nav-arrow {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.quest-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(15, 15, 40, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  
  .header-icon {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
    border-radius: 16px;
    
    .header-emoji {
      font-size: 32px;
    }
  }
  
  .header-text {
    flex: 1;
    
    .main-title {
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 50%, #3B82F6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0 0 4px 0;
    }
    
    .subtitle {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
  }
  
  .user-assets {
    display: flex;
    gap: 20px;
    
    .asset-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      
      .asset-icon {
        font-size: 20px;
      }
      
      .asset-value {
        font-size: 18px;
        font-weight: 700;
        color: #FBBF24;
      }
      
      .asset-label {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
      }
    }
  }
}

.no-profile-section {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
  
  .no-profile-card {
    text-align: center;
    padding: 60px 80px;
    background: rgba(15, 15, 40, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 24px;
    max-width: 500px;
    
    .no-profile-icon {
      font-size: 64px;
      margin-bottom: 20px;
    }
    
    .no-profile-title {
      font-size: 24px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
      margin: 0 0 16px 0;
    }
    
    .no-profile-desc {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.5);
      line-height: 1.8;
      margin: 0 0 32px 0;
    }
    
    .analyze-btn {
      background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #A78BFA 0%, #818CF8 100%);
      }
    }
  }
}

.quest-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  
  .title-icon {
    font-size: 18px;
  }
}

.element-profile-card,
.quest-status-card {
  background: rgba(15, 15, 40, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  padding: 24px;
}

.element-chart-section {
  margin-bottom: 24px;
}

.element-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  
  .element-bar-row {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .element-info {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 140px;
      
      .element-symbol {
        font-size: 20px;
      }
      
      .element-name {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
        min-width: 60px;
      }
      
      .element-level {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 500;
        
        &.abundant {
          background: rgba(34, 197, 94, 0.2);
          color: #22C55E;
        }
        
        &.strong {
          background: rgba(74, 222, 128, 0.2);
          color: #4ADE80;
        }
        
        &.balanced {
          background: rgba(59, 130, 246, 0.2);
          color: #60A5FA;
        }
        
        &.weak {
          background: rgba(251, 191, 36, 0.2);
          color: #FBBF24;
        }
        
        &.deficient {
          background: rgba(239, 68, 68, 0.2);
          color: #F87171;
        }
      }
    }
    
    .bar-container {
      flex: 1;
      height: 24px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      position: relative;
      overflow: hidden;
      
      .bar-fill {
        height: 100%;
        border-radius: 12px;
        transition: width 0.5s ease;
        
        &.bar-fire {
          background: linear-gradient(90deg, #EF4444 0%, #F97316 100%);
        }
        
        &.bar-earth {
          background: linear-gradient(90deg, #A16207 0%, #CA8A04 100%);
        }
        
        &.bar-air {
          background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%);
        }
        
        &.bar-water {
          background: linear-gradient(90deg, #06B6D4 0%, #22D3EE 100%);
        }
      }
      
      .bar-score {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
      }
    }
  }
}

.deficiency-info,
.dominant-info {
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  
  .deficiency-header,
  .dominant-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    
    .deficiency-icon,
    .dominant-icon {
      font-size: 20px;
    }
    
    .deficiency-title,
    .dominant-title {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
  }
  
  .deficiency-content,
  .dominant-content {
    .deficiency-text,
    .dominant-text {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
      margin: 0 0 8px 0;
      
      .deficiency-element {
        color: #F87171;
      }
    }
    
    .deficiency-hint {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.4);
      margin: 0;
    }
  }
}

.deficiency-info {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.dominant-info {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.energy-tags-section {
  .tags-title {
    font-size: 13px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 12px 0;
  }
  
  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    
    .energy-tag {
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 500;
      
      &.tag-dominant {
        background: rgba(34, 197, 94, 0.15);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.2);
      }
      
      &.tag-deficient {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.2);
      }
      
      &.tag-trait {
        background: rgba(139, 92, 246, 0.15);
        color: #A78BFA;
        border: 1px solid rgba(139, 92, 246, 0.2);
      }
    }
  }
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  
  .status-item {
    text-align: center;
    padding: 16px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    
    .status-value {
      font-size: 28px;
      font-weight: 700;
      color: #8B5CF6;
      margin-bottom: 4px;
    }
    
    .status-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }
  }
}

.quest-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .match-btn {
    background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
    border: none;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #A78BFA 0%, #F472B6 100%);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  .refresh-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(139, 92, 246, 0.2);
    color: rgba(255, 255, 255, 0.7);
    height: 40px;
    
    &:hover:not(:disabled) {
      background: rgba(139, 92, 246, 0.1);
      border-color: rgba(139, 92, 246, 0.3);
      color: #A78BFA;
    }
  }
}

.blind-boxes-section,
.history-section {
  grid-column: 1 / -1;
  background: rgba(15, 15, 40, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 20px;
  padding: 24px;
}

.blind-boxes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.blind-box-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(139, 92, 246, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.08);
    border-color: rgba(139, 92, 246, 0.3);
    transform: translateY(-2px);
  }
  
  .box-icon {
    width: 56px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
    border-radius: 12px;
    
    .box-emoji {
      font-size: 28px;
    }
  }
  
  .box-info {
    flex: 1;
    
    .box-id {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.4);
      margin-bottom: 4px;
    }
    
    .box-score {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.7);
      margin-bottom: 4px;
      
      .score-value {
        color: #FBBF24;
        font-weight: 600;
      }
    }
    
    .box-type {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 6px;
      font-weight: 500;
      
      &.complementary {
        background: rgba(34, 197, 94, 0.15);
        color: #4ADE80;
      }
      
      &.random {
        background: rgba(139, 92, 246, 0.15);
        color: #A78BFA;
      }
    }
  }
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .history-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    
    .history-date {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.4);
      min-width: 100px;
    }
    
    .history-type {
      flex: 1;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .history-reward {
      font-size: 13px;
      font-weight: 600;
      color: #FBBF24;
    }
    
    .history-status {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 6px;
      font-weight: 500;
      
      &.completed {
        background: rgba(34, 197, 94, 0.15);
        color: #4ADE80;
      }
    }
  }
}

.blind-box-detail {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
    
    .detail-id {
      font-size: 18px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
    
    .detail-type {
      font-size: 12px;
      padding: 4px 12px;
      border-radius: 8px;
      font-weight: 500;
      
      &.complementary {
        background: rgba(34, 197, 94, 0.15);
        color: #4ADE80;
      }
      
      &.random {
        background: rgba(139, 92, 246, 0.15);
        color: #A78BFA;
      }
    }
  }
  
  .clues-section {
    margin-bottom: 24px;
    
    .clues-title {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.8);
      margin: 0 0 16px 0;
    }
    
    .clues-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      
      .clue-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 14px 16px;
        border-radius: 10px;
        
        &.clue-strong {
          background: rgba(34, 197, 94, 0.1);
          border-left: 3px solid #22C55E;
        }
        
        &.clue-medium {
          background: rgba(139, 92, 246, 0.1);
          border-left: 3px solid #8B5CF6;
        }
        
        &.clue-subtle {
          background: rgba(255, 255, 255, 0.05);
          border-left: 3px solid rgba(255, 255, 255, 0.2);
        }
        
        .clue-number {
          font-size: 12px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.4);
          min-width: 24px;
        }
        
        .clue-text {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.6;
          font-style: italic;
        }
      }
    }
  }
  
  .completeness-section {
    margin-bottom: 24px;
    padding: 16px;
    background: rgba(139, 92, 246, 0.1);
    border-radius: 12px;
    
    .completeness-title {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.8);
      margin: 0 0 12px 0;
    }
    
    .completeness-bar {
      height: 24px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      position: relative;
      overflow: hidden;
      
      .completeness-fill {
        height: 100%;
        background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
        border-radius: 12px;
        transition: width 0.5s ease;
      }
      
      .completeness-value {
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
      }
    }
  }
  
  .revealed-section {
    margin-bottom: 24px;
    padding: 20px;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 12px;
    
    .revealed-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;
      
      .revealed-icon {
        font-size: 20px;
      }
      
      .revealed-title {
        font-size: 14px;
        font-weight: 600;
        color: #4ADE80;
      }
    }
    
    .matched-user-info {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .user-avatar {
        width: 56px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        
        .avatar-placeholder {
          font-size: 28px;
        }
      }
      
      .user-details {
        .user-name {
          font-size: 16px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 8px;
        }
        
        .user-element-info {
          display: flex;
          gap: 12px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          
          .deficiency-tag {
            color: #F87171;
          }
        }
      }
    }
  }
  
  .detail-actions {
    display: flex;
    justify-content: center;
    padding-top: 16px;
    border-top: 1px solid rgba(139, 92, 246, 0.1);
    
    .reveal-btn,
    .claim-btn {
      height: 48px;
      font-size: 16px;
      font-weight: 600;
      padding: 0 32px;
    }
    
    .reveal-btn {
      background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #A78BFA 0%, #818CF8 100%);
      }
    }
    
    .claim-btn {
      background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #4ADE80 0%, #22C55E 100%);
      }
    }
  }
}

.refresh-confirm-content {
  .cost-highlight {
    color: #FBBF24;
    font-weight: 600;
  }
  
  .refresh-hint {
    margin-top: 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

@media (max-width: 768px) {
  .quest-main {
    padding: 16px;
  }
  
  .quest-header {
    flex-direction: column;
    align-items: flex-start;
    
    .user-assets {
      width: 100%;
      justify-content: space-around;
    }
  }
  
  .no-profile-section {
    .no-profile-card {
      padding: 40px 24px;
    }
  }
  
  .quest-content {
    grid-template-columns: 1fr;
  }
  
  .blind-boxes-grid {
    grid-template-columns: 1fr;
  }
}
</style>
