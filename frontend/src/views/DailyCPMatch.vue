<template>
  <div class="daily-cp-match">
    <div class="stars-bg">
      <div v-for="(star, index) in starPositions" :key="index" class="star" :style="getStarStyle(star)"></div>
    </div>

    <div class="match-main">
      <div class="quick-nav">
        <div class="nav-item" @click="goToHoroscope">
          <span class="nav-icon">🌟</span>
          <span class="nav-text">每日星运</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item active">
          <span class="nav-icon">💕</span>
          <span class="nav-text">每日CP匹配</span>
          <span class="nav-arrow">→</span>
        </div>
        <div class="nav-item" @click="goToPhaseConnect">
          <span class="nav-icon">🔗</span>
          <span class="nav-text">相位连连看</span>
          <span class="nav-arrow">→</span>
        </div>
      </div>

      <div class="match-header">
        <div class="header-icon">
          <span class="header-emoji">💕</span>
        </div>
        <div class="header-text">
          <h1 class="main-title">每日CP匹配</h1>
          <p class="subtitle">每日中午12点，为你配对最有缘分的TA</p>
        </div>
      </div>

      <div v-if="loading" class="loading-section">
        <el-icon size="40" class="loading-icon"><Loading /></el-icon>
        <p class="loading-text">正在加载匹配状态...</p>
      </div>

      <div v-else class="match-content">
        <div class="match-status-card">
          <div class="status-header">
            <h3 class="section-title">
              <span class="title-icon">📅</span>
              今日匹配状态
            </h3>
            <span class="match-date">{{ today }}</span>
          </div>
          
          <div class="availability-grid">
            <div class="availability-item">
              <div class="availability-value">
                <span class="value-num">{{ availability.free_matches_remaining }}</span>
                <span class="value-total">/1</span>
              </div>
              <div class="availability-label">免费匹配次数</div>
            </div>
            <div class="availability-item vip">
              <div class="availability-value">
                <span class="value-num">{{ availability.vip_extra_matches_remaining }}</span>
                <span class="value-total">/3</span>
              </div>
              <div class="availability-label">VIP额外次数</div>
              <el-tag v-if="!isVip" size="small" type="info" effect="dark">开通会员</el-tag>
            </div>
          </div>

          <div v-if="todaysMatch" class="today-match-preview" @click="openMatchDetail(todaysMatch)">
            <div class="preview-header">
              <span class="preview-label">今日匹配</span>
              <el-tag 
                :type="getStatusTagType(todaysMatch.my_status)" 
                size="small"
                effect="dark"
              >
                {{ getStatusText(todaysMatch.my_status) }}
              </el-tag>
            </div>
            <div class="preview-match">
              <div class="match-users">
                <div class="user-info">
                  <div class="user-avatar">
                    <span class="avatar-emoji">👤</span>
                  </div>
                  <div class="user-detail">
                    <span class="user-name">{{ currentUser?.username || '你' }}</span>
                    <span class="user-zodiac" v-if="todaysMatch.my_zodiac_sign">{{ todaysMatch.my_zodiac_sign }}</span>
                  </div>
                </div>
                <div class="match-score-circle">
                  <div class="score-number">{{ todaysMatch.compatibility_score }}</div>
                  <div class="score-label">%</div>
                </div>
                <div class="user-info">
                  <div class="user-avatar other">
                    <span class="avatar-emoji">✨</span>
                  </div>
                  <div class="user-detail">
                    <span class="user-name">{{ todaysMatch.other_user_name || '神秘用户' }}</span>
                    <span class="user-zodiac" v-if="todaysMatch.other_zodiac_sign">{{ todaysMatch.other_zodiac_sign }}</span>
                  </div>
                </div>
              </div>
            </div>
            <el-button type="primary" link @click.stop>查看详情 →</el-button>
          </div>

          <div v-else class="no-match-yet">
            <div class="no-match-icon">🎁</div>
            <p class="no-match-text">
              <span v-if="availability.can_match">
                今日匹配还未开启，中午12点准时配对！
              </span>
              <span v-else>
                {{ availability.reason }}
              </span>
            </p>
            <el-button 
              v-if="availability.can_match && !todaysMatch" 
              type="primary" 
              size="large"
              :loading="matching"
              @click="startManualMatch"
              class="match-btn"
            >
              <el-icon><MagicStick /></el-icon>
              立即匹配
            </el-button>
          </div>
        </div>

        <div class="vip-privileges-card" v-if="!isVip">
          <div class="vip-header">
            <span class="vip-icon">💎</span>
            <h3 class="vip-title">VIP专属特权</h3>
          </div>
          <div class="vip-features">
            <div class="feature-item">
              <span class="feature-icon">🎯</span>
              <div class="feature-content">
                <span class="feature-name">定向星座匹配</span>
                <span class="feature-desc">精准匹配你心仪的星座</span>
              </div>
            </div>
            <div class="feature-item">
              <span class="feature-icon">➕</span>
              <div class="feature-content">
                <span class="feature-name">每日额外3次匹配</span>
                <span class="feature-desc">比普通用户更多机会</span>
              </div>
            </div>
            <div class="feature-item">
              <span class="feature-icon">⏰</span>
              <div class="feature-content">
                <span class="feature-name">延长会话至7天</span>
                <span class="feature-desc">更多时间深入了解</span>
              </div>
            </div>
          </div>
          <el-button type="warning" size="large" class="vip-btn" @click="goToVipCenter">
            开通会员
          </el-button>
        </div>

        <div class="active-session-card" v-if="activeSession">
          <h3 class="section-title">
            <span class="title-icon">💬</span>
            活跃会话
          </h3>
          <div class="session-detail" @click="openSessionChat(activeSession)">
            <div class="session-header">
              <div class="session-users">
                <span class="session-avatar">👤</span>
                <span class="session-arrow">↔</span>
                <span class="session-avatar other">✨</span>
              </div>
              <div class="session-info">
                <span class="session-other">{{ activeSession.other_user_name || '神秘用户' }}</span>
                <span class="session-status active">聊天中</span>
              </div>
            </div>
            <div class="session-timer" :class="{'warning': isSessionExpiringSoon(activeSession)}">
              <el-icon v-if="isSessionExpiringSoon(activeSession)" class="warning-icon"><Warning /></el-icon>
              <span class="timer-label">剩余时间:</span>
              <span class="timer-value">{{ formatRemainingTime(activeSession.remaining_seconds) }}</span>
            </div>
            <div class="session-actions">
              <el-button 
                v-if="isSessionExpiringSoon(activeSession)" 
                type="warning" 
                size="small"
                :loading="extending"
                @click.stop="extendSession(activeSession.session_id)"
              >
                <el-icon><Timer /></el-icon>
                延长会话
              </el-button>
              <el-button type="primary" size="small" @click.stop="openSessionChat(activeSession)">
                <el-icon><ChatDotRound /></el-icon>
                发送消息
              </el-button>
            </div>
          </div>
        </div>

        <div class="preference-card" v-if="isVip">
          <h3 class="section-title">
            <span class="title-icon">⚙️</span>
            匹配偏好设置
          </h3>
          <div class="preference-form">
            <div class="form-item">
              <label class="form-label">定向星座匹配</label>
              <el-select 
                v-model="preference.target_zodiac_sign" 
                placeholder="选择目标星座（可选）"
                clearable
                @change="savePreference"
                class="form-select"
              >
                <el-option 
                  v-for="sign in zodiacSigns" 
                  :key="sign" 
                  :label="sign" 
                  :value="sign"
                />
              </el-select>
            </div>
            <div class="form-item">
              <el-checkbox 
                v-model="preference.prefer_harmonious_aspects"
                @change="savePreference"
              >
                优先匹配和谐相位
              </el-checkbox>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showMatchDetail" 
      title="匹配详情" 
      width="600px"
      class="match-detail-dialog"
    >
      <div v-if="currentMatch" class="match-detail-content">
        <div class="detail-header">
          <div class="detail-persons">
            <div class="person-info">
              <div class="person-avatar">
                <span class="avatar-emoji">👤</span>
              </div>
              <div class="person-details">
                <div class="person-name">{{ currentUser?.username || '你' }}</div>
                <div class="person-zodiac" v-if="currentMatch.my_zodiac_sign">
                  星座: {{ currentMatch.my_zodiac_sign }}
                </div>
              </div>
            </div>
            <div class="match-center">
              <div class="compatibility-score">
                <svg class="score-svg" viewBox="0 0 120 120">
                  <circle class="score-bg" cx="60" cy="60" r="50" />
                  <circle 
                    class="score-progress" 
                    cx="60" cy="60" r="50"
                    :style="getScoreStyle(currentMatch.compatibility_score)"
                  />
                </svg>
                <div class="score-text">
                  <span class="score-number">{{ currentMatch.compatibility_score }}</span>
                  <span class="score-unit">%</span>
                </div>
              </div>
              <div class="match-date-label">
                {{ currentMatch.match_date }}
              </div>
            </div>
            <div class="person-info">
              <div class="person-avatar other">
                <span class="avatar-emoji" v-if="currentMatch.is_profile_unlocked">👤</span>
                <span class="avatar-emoji locked" v-else>❓</span>
              </div>
              <div class="person-details">
                <div class="person-name">
                  {{ currentMatch.other_user_name || '神秘用户' }}
                </div>
                <div class="person-zodiac" v-if="currentMatch.other_zodiac_sign">
                  星座: {{ currentMatch.other_zodiac_sign }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section interpretation">
          <h4 class="section-subtitle">💫 合盘解读</h4>
          <div class="interpretation-content">
            <p class="interpretation-text">{{ currentMatch.interpretation || '正在生成合盘解读...' }}</p>
          </div>
        </div>

        <div class="detail-section aspects" v-if="currentMatch.key_aspects && currentMatch.key_aspects.length > 0">
          <h4 class="section-subtitle">✨ 关键相位</h4>
          <div class="aspects-list">
            <div 
              v-for="(aspect, idx) in currentMatch.key_aspects.slice(0, 4)" 
              :key="idx" 
              class="aspect-item"
              :class="aspect.nature || 'neutral'"
            >
              <span class="aspect-planets">{{ aspect.planet_a }} {{ getAspectSymbol(aspect.aspect) }} {{ aspect.planet_b }}</span>
              <span class="aspect-type">{{ getAspectNatureLabel(aspect.nature) }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section status">
          <h4 class="section-subtitle">📊 匹配状态</h4>
          <div class="status-timeline">
            <div class="timeline-item">
              <span class="timeline-label">我的状态</span>
              <el-tag :type="getStatusTagType(currentMatch.my_status)" effect="dark">
                {{ getStatusText(currentMatch.my_status) }}
              </el-tag>
            </div>
            <div class="timeline-item">
              <span class="timeline-label">对方状态</span>
              <el-tag :type="getStatusTagType(currentMatch.other_status)" effect="dark">
                {{ getStatusText(currentMatch.other_status) }}
              </el-tag>
            </div>
            <div class="timeline-item mutual">
              <span class="timeline-label">双向确认</span>
              <el-tag :type="currentMatch.is_mutual_accepted ? 'success' : 'info'" effect="dark">
                {{ currentMatch.is_mutual_accepted ? '已确认 ✓' : '等待中...' }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <template v-if="!currentMatch.is_mutual_accepted">
            <el-button 
              v-if="currentMatch.my_status === 'pending'" 
              type="success" 
              size="large"
              :loading="accepting"
              @click="acceptCurrentMatch"
              class="action-btn"
            >
              <el-icon><CircleCheck /></el-icon>
              接受匹配
            </el-button>
            <el-button 
              v-if="currentMatch.my_status === 'pending'" 
              type="danger" 
              size="large"
              :loading="rejecting"
              @click="rejectCurrentMatch"
              class="action-btn"
            >
              <el-icon><CircleClose /></el-icon>
              拒绝匹配
            </el-button>
          </template>

          <template v-else>
            <el-button 
              v-if="!currentMatch.is_profile_unlocked" 
              type="warning" 
              size="large"
              :loading="unlocking"
              @click="unlockProfile"
              class="action-btn"
            >
              <el-icon><Unlock /></el-icon>
              解锁完整资料
            </el-button>
            <el-button 
              type="primary" 
              size="large"
              @click="startChat"
              class="action-btn"
            >
              <el-icon><ChatDotRound /></el-icon>
              开始聊天
            </el-button>
          </template>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dailyCPMatchApi, privateChatApi, vipApi, userApi } from '@/api'
import { Loading, MagicStick, Warning, Timer, ChatDotRound, CircleCheck, CircleClose, Unlock } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const matching = ref(false)
const accepting = ref(false)
const rejecting = ref(false)
const unlocking = ref(false)
const extending = ref(false)

const currentUser = ref(null)
const todaysMatch = ref(null)
const activeSession = ref(null)
const availability = ref({
  can_match: false,
  reason: '',
  free_matches_remaining: 0,
  vip_extra_matches_remaining: 0
})
const isVip = ref(false)

const preference = reactive({
  target_zodiac_sign: null,
  excluded_zodiac_signs: [],
  prefer_harmonious_aspects: false
})

const showMatchDetail = ref(false)
const currentMatch = ref(null)

const today = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
})

const zodiacSigns = [
  '白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', '处女座',
  '天秤座', '天蝎座', '射手座', '摩羯座', '水瓶座', '双鱼座'
]

const starPositions = computed(() => generateFixedStarPositions())

function generateFixedStarPositions() {
  const positions = []
  const seed = 42
  const modulus = 233280
  const multiplier = 9301
  const increment = 49297
  const starsCount = 80
  
  for (let i = 0; i < starsCount; i++) {
    const pseudoRandom1 = ((seed * (i + 1) * multiplier + increment) % modulus) / modulus
    const pseudoRandom2 = ((seed * (i + 2) * multiplier + increment) % modulus) / modulus
    const pseudoRandom3 = ((seed * (i + 3) * multiplier + increment) % modulus) / modulus
    const pseudoRandom4 = ((seed * (i + 4) * multiplier + increment) % modulus) / modulus
    
    positions.push({
      left: (pseudoRandom1 * 100) + '%',
      top: (pseudoRandom2 * 100) + '%',
      size: pseudoRandom3 * 2 + 1,
      delay: (pseudoRandom4 * 4) + 's',
      opacity: pseudoRandom1 * 0.4 + 0.2
    })
  }
  return positions
}

function getStarStyle(star) {
  return {
    left: star.left,
    top: star.top,
    width: `${star.size}px`,
    height: `${star.size}px`,
    animationDelay: star.delay,
    opacity: star.opacity
  }
}

function getStatusTagType(status) {
  const map = {
    'pending': 'info',
    'accepted': 'success',
    'rejected': 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    'pending': '待确认',
    'accepted': '已接受',
    'rejected': '已拒绝'
  }
  return map[status] || '未知'
}

function getAspectSymbol(aspect) {
  const symbols = {
    '合相': '☌',
    '六分相': '⚹',
    '四分相': '□',
    '三分相': '△',
    '对分相': '☍'
  }
  return symbols[aspect] || aspect
}

function getAspectNatureLabel(nature) {
  const labels = {
    'harmonious': '和谐',
    'challenging': '挑战',
    'neutral': '中性'
  }
  return labels[nature] || '中性'
}

function getScoreStyle(score) {
  const circumference = 2 * Math.PI * 50
  const progress = (score / 100) * circumference
  return {
    strokeDasharray: `${progress} ${circumference}`
  }
}

function formatRemainingTime(seconds) {
  if (!seconds || seconds <= 0) return '已过期'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 24) {
    const days = Math.floor(hours / 24)
    return `${days}天 ${hours % 24}小时`
  }
  
  return `${hours}小时 ${minutes}分钟`
}

function isSessionExpiringSoon(session) {
  if (!session || !session.remaining_seconds) return false
  return session.remaining_seconds < 3600
}

async function loadCurrentUser() {
  try {
    currentUser.value = await userApi.getCurrentUser()
  } catch (e) {
    console.error('加载用户信息失败:', e)
  }
}

async function loadMatchStatus() {
  loading.value = true
  try {
    const result = await dailyCPMatchApi.getStatus()
    
    todaysMatch.value = result.todays_match || null
    activeSession.value = result.active_session || null
    availability.value = result.availability || {
      can_match: false,
      reason: '',
      free_matches_remaining: 0,
      vip_extra_matches_remaining: 0
    }
    
    if (result.preference) {
      Object.assign(preference, result.preference)
    }
  } catch (e) {
    console.error('加载匹配状态失败:', e)
    ElMessage.error('加载匹配状态失败')
  } finally {
    loading.value = false
  }
}

async function loadVipStatus() {
  try {
    const result = await dailyCPMatchApi.getVipPrivileges()
    isVip.value = result.is_vip || false
  } catch (e) {
    console.error('加载VIP状态失败:', e)
  }
}

async function startManualMatch() {
  if (!availability.value.can_match || matching.value) return
  
  matching.value = true
  try {
    const matchType = availability.value.free_matches_remaining > 0 ? 'free_daily' : 'vip_extra'
    
    let targetZodiac = null
    if (isVip.value && preference.target_zodiac_sign) {
      targetZodiac = preference.target_zodiac_sign
    }
    
    const result = await dailyCPMatchApi.manualMatch(matchType, targetZodiac)
    
    if (result && result.match_id) {
      ElMessage.success('匹配成功！')
      await loadMatchStatus()
    }
  } catch (e) {
    console.error('匹配失败:', e)
    ElMessage.error(e.message || '匹配失败，请重试')
  } finally {
    matching.value = false
  }
}

function openMatchDetail(match) {
  currentMatch.value = { ...match }
  showMatchDetail.value = true
}

async function acceptCurrentMatch() {
  if (!currentMatch.value || accepting.value) return
  if (!currentMatch.value.match_id || currentMatch.value.match_id <= 0) {
    ElMessage.warning('匹配ID无效，请刷新页面重试')
    return
  }
  
  accepting.value = true
  try {
    await dailyCPMatchApi.acceptMatch(currentMatch.value.match_id)
    ElMessage.success('已接受匹配！')
    
    currentMatch.value.my_status = 'accepted'
    await loadMatchStatus()
  } catch (e) {
    console.error('接受匹配失败:', e)
    ElMessage.error(e.message || '操作失败')
  } finally {
    accepting.value = false
  }
}

async function rejectCurrentMatch() {
  if (!currentMatch.value || rejecting.value) return
  if (!currentMatch.value.match_id || currentMatch.value.match_id <= 0) {
    ElMessage.warning('匹配ID无效，请刷新页面重试')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要拒绝这个匹配吗？拒绝后将无法恢复。',
      '确认拒绝',
      {
        confirmButtonText: '确定拒绝',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  
  rejecting.value = true
  try {
    await dailyCPMatchApi.rejectMatch(currentMatch.value.match_id)
    ElMessage.success('已拒绝匹配')
    
    currentMatch.value.my_status = 'rejected'
    showMatchDetail.value = false
    await loadMatchStatus()
  } catch (e) {
    console.error('拒绝匹配失败:', e)
    ElMessage.error(e.message || '操作失败')
  } finally {
    rejecting.value = false
  }
}

async function unlockProfile() {
  if (!currentMatch.value || unlocking.value) return
  if (!currentMatch.value.match_id || currentMatch.value.match_id <= 0) {
    ElMessage.warning('匹配ID无效，请刷新页面重试')
    return
  }
  if (!currentMatch.value.other_user_id || currentMatch.value.other_user_id <= 0) {
    ElMessage.warning('目标用户ID无效，请刷新页面重试')
    return
  }
  
  unlocking.value = true
  try {
    const result = await dailyCPMatchApi.unlockProfile(
      currentMatch.value.match_id,
      currentMatch.value.other_user_id
    )
    
    ElMessage.success('已解锁对方完整资料！')
    currentMatch.value.is_profile_unlocked = true
    
    if (result && result.other_user_name) {
      currentMatch.value.other_user_name = result.other_user_name
    }
  } catch (e) {
    console.error('解锁资料失败:', e)
    ElMessage.error(e.message || '解锁失败')
  } finally {
    unlocking.value = false
  }
}

async function extendSession(sessionId) {
  if (!sessionId || sessionId <= 0 || extending.value) {
    if (!sessionId || sessionId <= 0) {
      ElMessage.warning('会话ID无效，请刷新页面重试')
    }
    return
  }
  
  extending.value = true
  try {
    await dailyCPMatchApi.extendSession(sessionId, 168)
    ElMessage.success('会话已延长至7天！')
    await loadMatchStatus()
  } catch (e) {
    console.error('延长会话失败:', e)
    ElMessage.error(e.message || '延长失败')
  } finally {
    extending.value = false
  }
}

async function savePreference() {
  try {
    await dailyCPMatchApi.updatePreference({
      target_zodiac_sign: preference.target_zodiac_sign,
      prefer_harmonious_aspects: preference.prefer_harmonious_aspects
    })
    ElMessage.success('偏好设置已保存')
  } catch (e) {
    console.error('保存偏好失败:', e)
    ElMessage.error('保存偏好失败')
  }
}

function openSessionChat(session) {
  if (!session) return
  if (!session.other_user_id || session.other_user_id <= 0) {
    ElMessage.warning('目标用户ID无效')
    return
  }
  
  router.push({
    path: '/private-chat',
    query: {
      target_user_id: session.other_user_id,
      match_source: 'daily_cp_match',
      compatibility_score: todaysMatch.value?.compatibility_score || 0
    }
  })
}

function startChat() {
  if (!currentMatch.value) return
  if (!currentMatch.value.other_user_id || currentMatch.value.other_user_id <= 0) {
    ElMessage.warning('目标用户ID无效')
    return
  }
  
  showMatchDetail.value = false
  
  router.push({
    path: '/private-chat',
    query: {
      target_user_id: currentMatch.value.other_user_id,
      match_source: 'daily_cp_match',
      compatibility_score: currentMatch.value.compatibility_score || 0
    }
  })
}

function goToHoroscope() {
  router.push('/horoscope')
}

function goToPhaseConnect() {
  router.push('/phase-connect')
}

function goToVipCenter() {
  router.push('/vip-center')
}

onMounted(async () => {
  await loadCurrentUser()
  await loadVipStatus()
  await loadMatchStatus()
})
</script>

<style lang="scss" scoped>
.daily-cp-match {
  height: 100%;
  width: 100%;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 100%);
}

.stars-bg {
  position: fixed;
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

.match-main {
  position: relative;
  z-index: 10;
  min-height: 100vh;
  padding: 20px 24px;
  max-width: 900px;
  margin: 0 auto;
  box-sizing: border-box;
}

.quick-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(20, 20, 50, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.4);
  }

  &.active {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.3) 0%, rgba(139, 92, 246, 0.2) 100%);
    border-color: rgba(236, 72, 153, 0.4);
  }
}

.nav-icon { font-size: 1.1rem; }
.nav-text { font-size: 0.85rem; color: rgba(255, 255, 255, 0.8); }
.nav-arrow { font-size: 0.75rem; color: rgba(255, 255, 255, 0.4); }

.match-header {
  text-align: center;
  margin-bottom: 24px;
}

.header-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(236, 72, 153, 0.25); }
  50% { box-shadow: 0 0 40px rgba(236, 72, 153, 0.4); }
}

.header-emoji { font-size: 2rem; }

.main-title {
  margin: 0 0 6px 0;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.9rem;
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-icon {
  margin-bottom: 16px;
  color: #a78bfa;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.loading-text {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.95rem;
}

.match-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.match-status-card,
.vip-privileges-card,
.active-session-card,
.preference-card {
  background: rgba(18, 18, 40, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.title-icon { font-size: 1.1rem; }

.match-date {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  padding: 4px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 20px;
}

.availability-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.availability-item {
  text-align: center;
  padding: 16px 12px;
  background: rgba(30, 30, 60, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.15);
  
  &.vip {
    border-color: rgba(234, 179, 8, 0.3);
    background: rgba(234, 179, 8, 0.05);
  }
}

.availability-value {
  display: flex;
  justify-content: center;
  align-items: baseline;
  gap: 2px;
  margin-bottom: 4px;
}

.value-num {
  font-size: 1.75rem;
  font-weight: 700;
  color: #a78bfa;
}

.value-total {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.4);
}

.availability-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.today-match-preview {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.12);
    border-color: rgba(139, 92, 246, 0.3);
  }
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.preview-match {
  margin-bottom: 12px;
}

.match-users {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.user-avatar {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.2));
  border-radius: 50%;
  
  &.other {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(236, 72, 153, 0.1));
  }
}

.avatar-emoji {
  font-size: 1.5rem;
}

.user-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.user-zodiac {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.match-score-circle {
  width: 70px;
  height: 70px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(34, 197, 94, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  border: 2px solid rgba(34, 197, 94, 0.4);
}

.score-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #22c55e;
}

.score-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.5);
}

.no-match-yet {
  text-align: center;
  padding: 30px 20px;
}

.no-match-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.no-match-text {
  margin: 0 0 16px 0;
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.9rem;
  line-height: 1.6;
}

.match-btn {
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  border: none;
  
  &:hover:not(:disabled) {
    box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
  }
}

.vip-privileges-card {
  border-color: rgba(234, 179, 8, 0.3);
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.05) 0%, rgba(18, 18, 40, 0.7) 100%);
}

.vip-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.vip-icon { font-size: 1.5rem; }

.vip-title {
  margin: 0;
  font-size: 1rem;
  color: #eab308;
  font-weight: 600;
}

.vip-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(30, 30, 60, 0.4);
  border-radius: 10px;
}

.feature-icon { font-size: 1.25rem; }

.feature-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feature-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.feature-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.vip-btn {
  width: 100%;
  background: linear-gradient(135deg, #eab308 0%, #f59e0b 100%);
  border: none;
  
  &:hover {
    box-shadow: 0 4px 20px rgba(234, 179, 8, 0.4);
  }
}

.active-session-card {
  border-color: rgba(34, 197, 94, 0.3);
}

.session-detail {
  background: rgba(34, 197, 94, 0.05);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.3);
  }
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.session-users {
  display: flex;
  align-items: center;
  gap: 8px;
}

.session-avatar {
  font-size: 1.25rem;
}

.session-arrow {
  color: #22c55e;
  font-weight: bold;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-other {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.session-status {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  
  &.active {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }
}

.session-timer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 8px;
  margin-bottom: 12px;
  
  &.warning {
    background: rgba(249, 115, 22, 0.1);
  }
}

.warning-icon {
  color: #f97316;
  font-size: 1.1rem;
}

.timer-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.timer-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #22c55e;
  
  .warning & {
    color: #f97316;
  }
}

.session-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.preference-card {
  border-color: rgba(139, 92, 246, 0.3);
}

.preference-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.form-select {
  max-width: 200px;
}

.match-detail-dialog :deep(.el-dialog) {
  background: linear-gradient(180deg, #0a0a1a, #1a1a3e);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.match-detail-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  padding-bottom: 16px;
}

.match-detail-dialog :deep(.el-dialog__title) {
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.match-detail-content {
  padding: 0;
}

.detail-header {
  margin-bottom: 24px;
}

.detail-persons {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.person-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.person-avatar {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.2));
  border-radius: 50%;
  
  &.other {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(236, 72, 153, 0.1));
  }
}

.avatar-emoji {
  font-size: 1.75rem;
  
  &.locked {
    filter: grayscale(0.8);
  }
}

.person-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.person-name {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.person-zodiac {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.match-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.compatibility-score {
  position: relative;
  width: 120px;
  height: 120px;
}

.score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-bg {
  fill: none;
  stroke: rgba(139, 92, 246, 0.15);
  stroke-width: 8;
}

.score-progress {
  fill: none;
  stroke: #22c55e;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s ease;
}

.score-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-number {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: #22c55e;
}

.score-unit {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.match-date-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  padding: 4px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 20px;
}

.detail-section {
  background: rgba(30, 30, 60, 0.4);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.section-subtitle {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

.interpretation-text {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.8;
}

.aspects-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.aspect-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 20px;
  border-left: 3px solid transparent;
  
  &.harmonious {
    border-left-color: #22c55e;
    background: rgba(34, 197, 94, 0.08);
  }
  
  &.challenging {
    border-left-color: #f97316;
    background: rgba(249, 115, 22, 0.08);
  }
  
  &.neutral {
    border-left-color: #eab308;
    background: rgba(234, 179, 8, 0.08);
  }
}

.aspect-planets {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.aspect-type {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(139, 92, 246, 0.15);
}

.status-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(30, 30, 60, 0.3);
  border-radius: 8px;
  
  &.mutual {
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.2);
  }
}

.timeline-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.detail-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(139, 92, 246, 0.2);
}

.action-btn {
  min-width: 120px;
}
</style>
