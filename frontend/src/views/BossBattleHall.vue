<template>
  <div class="boss-hall-page">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="hall-main">
      <div class="page-header">
        <div class="header-back" @click="router.back()">
          <el-icon><Connection /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">
          <div class="title-icon">
            <el-icon size="28"><Lightning /></el-icon>
          </div>
          <div class="title-text">
            <h1>星象BOSS副本大厅</h1>
            <p>挑战天象BOSS，获取星尘奖励</p>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <el-empty description="正在加载副本大厅...">
          <el-progress type="circle" :percentage="50" :status="'exception'" />
        </el-empty>
      </div>

      <div v-else-if="!loading && activeBosses.length === 0" class="empty-state">
        <el-icon size="64"><Star /></el-icon>
        <h3>暂无活跃BOSS</h3>
        <p>系统会根据实时天象自动生成BOSS，请稍后查看</p>
        <el-button type="primary" @click="loadHallData" :loading="refreshing">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <div v-else class="hall-content">
        <div class="element-info-bar">
          <div class="element-title">
            <el-icon><InfoFilled /></el-icon>
            <span>元素平衡规则</span>
          </div>
          <div class="element-cards">
            <div 
              v-for="(info, key) in elementInfo" 
              :key="key" 
              class="element-card"
            >
              <span class="element-symbol">{{ info.symbol }}</span>
              <span class="element-name">{{ key }}</span>
            </div>
          </div>
          <div class="element-hint">
            队伍必须同时包含 <span class="highlight">🔥火</span>、<span class="highlight">🪨土</span>、<span class="highlight">🌪️风</span>、<span class="highlight">💧水</span> 四种元素才能开战
          </div>
        </div>

        <div v-if="currentTransitEvents.length > 0" class="transit-info">
          <div class="transit-title">
            <el-icon><Sunny /></el-icon>
            <span>当前天象</span>
          </div>
          <div class="transit-events">
            <el-tag 
              v-for="event in currentTransitEvents" 
              :key="event" 
              type="danger"
              effect="dark"
              size="large"
            >
              {{ getEventLabel(event) }}
            </el-tag>
          </div>
        </div>

        <div class="bosses-section">
          <div class="section-header">
            <h3>
              <el-icon><VideoCamera /></el-icon>
              活跃BOSS
              <el-tag type="primary" size="small">{{ activeBosses.length }}</el-tag>
            </h3>
            <el-button type="primary" link @click="loadHallData" :loading="refreshing">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <div class="bosses-grid">
            <div 
              v-for="boss in activeBosses" 
              :key="boss.boss_id" 
              class="boss-card"
              :class="{ 'boss-selected': selectedBoss?.boss_id === boss.boss_id }"
              @click="selectBoss(boss)"
            >
              <div class="boss-header">
                <div class="boss-name-section">
                  <h3 class="boss-name">{{ boss.name }}</h3>
                  <p class="boss-title">{{ boss.title }}</p>
                </div>
                <div class="boss-difficulty">
                  <el-tag :type="getDifficultyTag(boss.fluctuation_value)" size="large">
                    <span class="fluctuation-label">波动值</span>
                    <span class="fluctuation-value">{{ boss.fluctuation_value }}</span>
                  </el-tag>
                </div>
              </div>

              <div class="boss-description">
                {{ boss.description }}
              </div>

              <div class="boss-health-section">
                <div class="health-header">
                  <span class="health-label">生命值</span>
                  <span class="health-value">{{ formatNumber(boss.current_health) }} / {{ formatNumber(boss.max_health) }}</span>
                </div>
                <el-progress 
                  :percentage="boss.health_percentage" 
                  :stroke-width="12"
                  :color="getHealthColor(boss.health_percentage)"
                  :show-text="false"
                />
              </div>

              <div class="boss-element-info">
                <div class="element-item weakness">
                  <span class="label">弱点</span>
                  <span class="element-value">
                    <span class="symbol">{{ boss.weakness_symbol }}</span>
                    <span class="name">{{ boss.weakness_element }}</span>
                  </span>
                </div>
                <div class="element-item resistance">
                  <span class="label">抵抗</span>
                  <span class="element-value">
                    <span class="symbol">{{ boss.resistance_symbol }}</span>
                    <span class="name">{{ boss.resistance_element }}</span>
                  </span>
                </div>
                <div class="element-item trigger">
                  <span class="label">触发天象</span>
                  <el-tag size="small" type="info">
                    {{ getEventLabel(boss.trigger_event) }}
                  </el-tag>
                </div>
              </div>

              <div class="boss-stats">
                <div class="stat-item">
                  <span class="stat-label">攻击力</span>
                  <span class="stat-value">{{ boss.current_power }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">技能数</span>
                  <span class="stat-value">{{ boss.skills?.length || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">挑战队伍</span>
                  <span class="stat-value">{{ boss.team_count || 0 }}</span>
                </div>
              </div>

              <div v-if="boss.planet_involved" class="boss-planet">
                <el-icon><Sunny /></el-icon>
                <span>涉及行星: {{ boss.planet_involved }}</span>
              </div>

              <div class="boss-footer">
                <el-button type="primary" @click.stop="viewBossDetail(boss)">
                  查看详情
                </el-button>
                <el-button type="success" @click.stop="openCreateTeam(boss)">
                  组建队伍
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedBoss" class="teams-section">
          <div class="section-header">
            <h3>
              <el-icon><User /></el-icon>
              {{ selectedBoss.name }} - 挑战队伍
              <el-tag v-if="selectedBoss.recruiting_teams?.length > 0" type="warning" size="small">
                {{ selectedBoss.recruiting_teams.length }} 支队伍招募中
              </el-tag>
            </h3>
          </div>

          <div v-if="selectedBoss.recruiting_teams && selectedBoss.recruiting_teams.length > 0" class="teams-list">
            <div 
              v-for="team in selectedBoss.recruiting_teams" 
              :key="team.team_id" 
              class="team-card"
            >
              <div class="team-header">
                <div class="team-name-section">
                  <h4 class="team-name">{{ team.team_name }}</h4>
                  <el-tag :type="team.status === 'ready' ? 'success' : 'warning'" size="small">
                    {{ team.status === 'ready' ? '准备就绪' : '招募中' }}
                  </el-tag>
                </div>
                <div class="team-energy">
                  <span class="energy-label">总能量</span>
                  <span class="energy-value">{{ team.total_energy }}</span>
                </div>
              </div>

              <div class="team-members">
                <div 
                  v-for="member in team.members" 
                  :key="member.member_id" 
                  class="team-member"
                  :class="{ 'leader': member.is_leader }"
                >
                  <el-avatar :size="40">
                    <el-icon :size="20"><User /></el-icon>
                  </el-avatar>
                  <div class="member-info">
                    <div class="member-name">
                      {{ member.name }}
                      <el-tag v-if="member.is_leader" type="primary" size="small" effect="dark">
                        队长
                      </el-tag>
                    </div>
                    <div class="member-element">
                      <span class="symbol">{{ member.element_symbol }}</span>
                      <span>{{ member.element }}象</span>
                    </div>
                    <div class="member-power">
                      战力: {{ member.combat_power }}
                    </div>
                  </div>
                </div>
                <div v-if="team.members.length < 4" class="empty-slot">
                  <el-icon :size="24"><Plus /></el-icon>
                  <span>空位</span>
                </div>
              </div>

              <div class="team-element-check">
                <span class="check-label">元素覆盖:</span>
                <div class="element-checks">
                  <span 
                    v-for="e in ['火', '土', '风', '水']" 
                    :key="e"
                    class="element-check"
                    :class="{ 'present': team.elements_present?.includes(e) }"
                  >
                    <span class="symbol">{{ getElementSymbol(e) }}</span>
                    <span class="name">{{ e }}</span>
                    <span class="check">{{ team.elements_present?.includes(e) ? '✓' : '✗' }}</span>
                  </span>
                </div>
              </div>

              <div v-if="!team.has_all_elements" class="missing-elements">
                <el-alert
                  :title="'缺少元素: ' + (team.missing_elements?.join(', ') || '无')"
                  type="warning"
                  :closable="false"
                  show-icon
                  size="small"
                />
              </div>

              <div class="team-footer">
                <div class="team-status-info">
                  <span>{{ team.members?.length || 0 }}/4 名成员</span>
                </div>
                <el-button-group>
                  <el-button 
                    v-if="!team.has_all_elements && team.members?.length < 4"
                    type="primary"
                    size="small"
                    @click="joinTeam(team)"
                  >
                    加入队伍
                  </el-button>
                  <el-button 
                    v-else-if="team.has_all_elements"
                    type="success"
                    size="small"
                    :disabled="!team.has_all_elements"
                  >
                    队伍完整
                  </el-button>
                  <el-button 
                    v-else
                    type="warning"
                    size="small"
                    disabled
                  >
                    队伍已满
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </div>

          <div v-else class="no-teams">
            <el-empty description="暂无招募中的队伍，快来创建第一支队伍吧！">
              <el-button type="primary" @click="openCreateTeam(selectedBoss)">
                创建队伍
              </el-button>
            </el-empty>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showBossDetailDialog"
      title="BOSS详情"
      width="800px"
      class="boss-detail-dialog"
    >
      <div v-if="detailBoss" class="boss-detail-content">
        <div class="detail-header">
          <div class="detail-name-section">
            <h2 class="detail-name">{{ detailBoss.name }}</h2>
            <p class="detail-title">{{ detailBoss.title }}</p>
          </div>
          <el-tag :type="getDifficultyTag(detailBoss.fluctuation_value)" size="large">
            波动值: {{ detailBoss.fluctuation_value }}
          </el-tag>
        </div>

        <div class="detail-lore">
          <h4>背景故事</h4>
          <p>{{ detailBoss.lore }}</p>
        </div>

        <div class="detail-stats">
          <div class="detail-health">
            <h4>生命值</h4>
            <div class="health-display">
              <span class="health-number">{{ formatNumber(detailBoss.current_health) }}</span>
              <span class="health-divider">/</span>
              <span class="health-number total">{{ formatNumber(detailBoss.max_health) }}</span>
            </div>
            <el-progress 
              :percentage="detailBoss.health_percentage" 
              :stroke-width="16"
              :color="getHealthColor(detailBoss.health_percentage)"
            />
          </div>

          <div class="detail-power">
            <div class="power-item">
              <span class="power-label">攻击力</span>
              <span class="power-value">{{ detailBoss.current_power }}</span>
            </div>
            <div class="power-item">
              <span class="power-label">基础攻击力</span>
              <span class="power-value">{{ detailBoss.base_power }}</span>
            </div>
          </div>
        </div>

        <div class="detail-elements">
          <div class="element-detail weakness">
            <h4>弱点元素</h4>
            <div class="element-display">
              <span class="symbol">{{ detailBoss.weakness_symbol }}</span>
              <span class="name">{{ detailBoss.weakness_element }}</span>
            </div>
            <p class="element-hint">使用该元素攻击可造成 <span class="highlight">30%</span> 额外伤害</p>
          </div>
          <div class="element-detail resistance">
            <h4>抵抗元素</h4>
            <div class="element-display">
              <span class="symbol">{{ detailBoss.resistance_symbol }}</span>
              <span class="name">{{ detailBoss.resistance_element }}</span>
            </div>
            <p class="element-hint">该元素攻击会被抵抗，伤害减少 <span class="highlight">15%</span></p>
          </div>
        </div>

        <div class="detail-skills">
          <h4>BOSS技能</h4>
          <div class="skills-list">
            <div 
              v-for="skill in detailBoss.skills" 
              :key="skill.skill_id" 
              class="skill-card"
              :class="{ 'ultimate': skill.is_ultimate }"
            >
              <div class="skill-header">
                <span class="skill-name">{{ skill.name }}</span>
                <el-tag v-if="skill.is_ultimate" type="danger" size="small" effect="dark">
                  终极技能
                </el-tag>
              </div>
              <p class="skill-description">{{ skill.description }}</p>
              <div class="skill-stats">
                <span class="skill-stat">
                  <span class="stat-label">元素:</span>
                  <span class="symbol">{{ skill.element_symbol }}</span>
                  <span>{{ skill.element }}</span>
                </span>
                <span class="skill-stat">
                  <span class="stat-label">伤害:</span>
                  <span class="damage">{{ skill.base_damage }}</span>
                </span>
                <span class="skill-stat">
                  <span class="stat-label">冷却:</span>
                  <span>{{ skill.cooldown }} 回合</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-timing">
          <h4>出现时间</h4>
          <div class="timing-info">
            <div class="timing-item">
              <span class="timing-label">出现于:</span>
              <span>{{ formatDateTime(detailBoss.spawned_at) }}</span>
            </div>
            <div class="timing-item">
              <span class="timing-label">预计消失:</span>
              <span>{{ formatDateTime(detailBoss.estimated_end_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showBossDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="openCreateTeam(detailBoss)">
          组建队伍挑战
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showCreateTeamDialog"
      title="创建队伍"
      width="600px"
      class="create-team-dialog"
    >
      <el-form :model="createTeamForm" label-width="100px">
        <el-form-item label="队伍名称">
          <el-input v-model="createTeamForm.team_name" placeholder="请输入队伍名称" />
        </el-form-item>
        <el-form-item label="目标BOSS">
          <el-input 
            :value="createBoss?.name || ''" 
            disabled
            placeholder="未选择BOSS"
          />
        </el-form-item>
        <el-form-item label="你的元素">
          <el-select v-model="createTeamForm.element" placeholder="选择你的元素属性" style="width: 100%">
            <el-option 
              v-for="(info, key) in elementInfo" 
              :key="key" 
              :label="`${info.symbol} ${key}象`"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="你的名称">
          <el-input v-model="createTeamForm.name" placeholder="请输入你的名称" />
        </el-form-item>
        <el-form-item label="战力值">
          <el-input-number 
            v-model="createTeamForm.combat_power" 
            :min="50" 
            :max="500"
            :step="10"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <div class="create-team-hint">
        <el-alert
          title="队伍规则"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <ul>
              <li>队伍最多容纳 4 名成员</li>
              <li>队伍必须同时包含 🔥火、🪨土、🌪️风、💧水 四种元素才能开战</li>
              <li>选择 BOSS 的弱点元素可以造成额外伤害</li>
            </ul>
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="showCreateTeamDialog = false">取消</el-button>
        <el-button type="primary" @click="createTeam" :loading="creatingTeam">
          创建队伍
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showBattleResultDialog"
      title="战斗结果"
      width="700px"
      class="battle-result-dialog"
    >
      <div v-if="battleResult" class="battle-result-content">
        <div class="result-header" :class="{ 'victory': battleResult.battle_result?.victory, 'defeat': !battleResult.battle_result?.victory }">
          <div class="result-icon">
            <el-icon v-if="battleResult.battle_result?.victory" :size="48"><Trophy /></el-icon>
            <el-icon v-else :size="48"><Close /></el-icon>
          </div>
          <div class="result-title">
            <h2>{{ battleResult.battle_result?.victory ? '战斗胜利！' : '战斗失败...' }}</h2>
            <p>{{ battleResult.battle_result?.victory ? '恭喜你击败了BOSS！' : '不要气馁，重整旗鼓再战！' }}</p>
          </div>
        </div>

        <div v-if="battleResult.battle_story" class="battle-story">
          <h4>
            <el-icon><Film /></el-icon>
            战斗剧情
          </h4>
          <div v-if="battleResult.battle_story.scene_intro" class="story-intro">
            <p>{{ battleResult.battle_story.scene_intro }}</p>
          </div>
          <div v-if="battleResult.battle_story.battle_phases?.length > 0" class="story-phases">
            <div 
              v-for="(phase, index) in battleResult.battle_story.battle_phases" 
              :key="index" 
              class="story-phase"
            >
              <h5>{{ phase.phase_name }}</h5>
              <p>{{ phase.description }}</p>
              <div v-if="phase.key_actions?.length > 0" class="key-actions">
                <span class="action-label">关键动作:</span>
                <span v-for="(action, ai) in phase.key_actions" :key="ai" class="action-item">
                  {{ action }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="battleResult.battle_story.climax" class="story-climax">
            <h5>高潮</h5>
            <p>{{ battleResult.battle_story.climax }}</p>
          </div>
          <div v-if="battleResult.battle_story.character_highlights?.length > 0" class="story-highlights">
            <h5>角色高光</h5>
            <div 
              v-for="(highlight, hi) in battleResult.battle_story.character_highlights" 
              :key="hi" 
              class="highlight-item"
            >
              <span class="highlight-char">{{ highlight.character }}:</span>
              <span class="highlight-text">{{ highlight.highlight }}</span>
            </div>
          </div>
          <div v-if="battleResult.battle_story.epic_quotes?.length > 0" class="story-quotes">
            <h5>史诗台词</h5>
            <div v-for="(quote, qi) in battleResult.battle_story.epic_quotes" :key="qi" class="quote-item">
              "{{ quote }}"
            </div>
          </div>
        </div>

        <div class="battle-stats">
          <h4>战斗数据</h4>
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-label">队伍能量</span>
              <span class="stat-value">{{ battleResult.battle_result?.team_power || 0 }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">调整后能量</span>
              <span class="stat-value">{{ battleResult.battle_result?.adjusted_team_power || 0 }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">BOSS战力</span>
              <span class="stat-value">{{ battleResult.battle_result?.boss_power || 0 }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">能量比值</span>
              <span class="stat-value">{{ battleResult.battle_result?.power_ratio || 0 }}x</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">造成伤害</span>
              <span class="stat-value damage">{{ formatNumber(battleResult.battle_result?.damage_dealt || 0) }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">承受伤害</span>
              <span class="stat-value received">{{ formatNumber(battleResult.battle_result?.damage_received || 0) }}</span>
            </div>
          </div>
        </div>

        <div v-if="battleResult.team?.rewards_earned" class="battle-rewards">
          <h4>
            <el-icon><Coin /></el-icon>
            获得奖励
          </h4>
          <div class="rewards-display">
            <div class="reward-item stardust">
              <span class="reward-icon">✨</span>
              <div class="reward-info">
                <span class="reward-name">星尘积分</span>
                <span class="reward-value">+{{ battleResult.team.rewards_earned.per_member_stardust || 0 }}</span>
              </div>
            </div>
            <div v-if="battleResult.team.rewards_earned.items?.length > 0" class="reward-items">
              <div 
                v-for="item in battleResult.team.rewards_earned.items" 
                :key="item.item_id" 
                class="reward-item item"
              >
                <span class="reward-icon">🎁</span>
                <div class="reward-info">
                  <span class="reward-name">{{ item.item_name }}</span>
                  <el-tag :type="item.rarity === 'rare' ? 'danger' : 'warning'" size="small">
                    {{ item.rarity === 'rare' ? '稀有' : ' uncommon' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showBattleResultDialog = false">关闭</el-button>
        <el-button type="primary" @click="loadHallData">
          返回大厅
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Connection, Lightning, Star, Refresh, Sunny, VideoCamera, InfoFilled,
  User, Plus, Film, Trophy, Close, Coin
} from '@element-plus/icons-vue'
import { bossBattleApi } from '@/api'

const router = useRouter()

const loading = ref(true)
const refreshing = ref(false)
const creatingTeam = ref(false)

const activeBosses = ref([])
const selectedBoss = ref(null)
const detailBoss = ref(null)
const createBoss = ref(null)
const currentTransitEvents = ref([])
const elementInfo = ref({})
const battleResult = ref(null)

const showBossDetailDialog = ref(false)
const showCreateTeamDialog = ref(false)
const showBattleResultDialog = ref(false)

const createTeamForm = reactive({
  team_name: '',
  element: '火',
  name: '',
  combat_power: 100
})

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

const EVENT_LABELS = {
  'mercury_retrograde': '水星逆行',
  'saturn_retrograde': '土星逆行',
  'full_moon': '满月',
  'new_moon': '新月',
  'mars_square_saturn': '火星刑土星',
  'system_spawn': '系统生成'
}

const getEventLabel = (event) => {
  return EVENT_LABELS[event] || event
}

const getElementSymbol = (element) => {
  const symbols = { '火': '🔥', '土': '🪨', '风': '🌪️', '水': '💧' }
  return symbols[element] || '❓'
}

const getDifficultyTag = (fluctuation) => {
  if (fluctuation >= 80) return 'danger'
  if (fluctuation >= 70) return 'warning'
  if (fluctuation >= 60) return 'info'
  return 'success'
}

const getHealthColor = (percentage) => {
  if (percentage >= 70) return '#22c55e'
  if (percentage >= 40) return '#eab308'
  return '#ef4444'
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadHallData = async () => {
  if (refreshing.value) return
  
  refreshing.value = true
  try {
    const result = await bossBattleApi.getHall()
    
    if (result.active_bosses) {
      activeBosses.value = result.active_bosses
    }
    
    if (result.current_transit_events) {
      currentTransitEvents.value = result.current_transit_events
    }
    
    if (result.element_info) {
      const info = {}
      const elements = result.element_info.elements || []
      const symbols = result.element_info.symbols || {}
      const colors = result.element_info.colors || {}
      
      elements.forEach(e => {
        info[e] = {
          symbol: symbols[e] || '❓',
          color: colors[e] || '#fff'
        }
      })
      elementInfo.value = info
    }
    
  } catch (error) {
    console.error('加载副本大厅失败:', error)
    ElMessage.error('加载副本大厅失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const selectBoss = (boss) => {
  selectedBoss.value = boss
}

const viewBossDetail = async (boss) => {
  try {
    const result = await bossBattleApi.getBossDetail(boss.boss_id)
    detailBoss.value = result.boss
    showBossDetailDialog.value = true
  } catch (error) {
    console.error('获取BOSS详情失败:', error)
    ElMessage.error('获取BOSS详情失败')
  }
}

const openCreateTeam = (boss) => {
  if (!boss) {
    ElMessage.warning('请先选择一个BOSS')
    return
  }
  
  createBoss.value = boss
  createTeamForm.team_name = `挑战${boss.name}队`
  createTeamForm.name = ''
  createTeamForm.element = '火'
  createTeamForm.combat_power = 100
  
  showBossDetailDialog.value = false
  showCreateTeamDialog.value = true
}

const createTeam = async () => {
  if (!createBoss.value) {
    ElMessage.warning('请先选择BOSS')
    return
  }
  
  if (!createTeamForm.name) {
    ElMessage.warning('请输入你的名称')
    return
  }
  
  if (!createTeamForm.element) {
    ElMessage.warning('请选择元素属性')
    return
  }
  
  creatingTeam.value = true
  
  try {
    const leaderData = {
      member_id: `member_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: createTeamForm.name,
      element: createTeamForm.element,
      combat_power: createTeamForm.combat_power,
      stats: {
        fire_power: createTeamForm.element === '火' ? createTeamForm.combat_power : 0,
        earth_power: createTeamForm.element === '土' ? createTeamForm.combat_power : 0,
        air_power: createTeamForm.element === '风' ? createTeamForm.combat_power : 0,
        water_power: createTeamForm.element === '水' ? createTeamForm.combat_power : 0
      },
      passives: [],
      avatar_data: {}
    }
    
    const result = await bossBattleApi.createTeam({
      boss_id: createBoss.value.boss_id,
      team_name: createTeamForm.team_name || '星之队',
      leader_data: leaderData
    })
    
    ElMessage.success('队伍创建成功！')
    showCreateTeamDialog.value = false
    
    await loadHallData()
    
    if (result.team_id) {
      ElMessage.info('正在准备开战...')
      await startBattle(result.team_id)
    }
    
  } catch (error) {
    console.error('创建队伍失败:', error)
    ElMessage.error('创建队伍失败: ' + (error.message || '未知错误'))
  } finally {
    creatingTeam.value = false
  }
}

const joinTeam = async (team) => {
  ElMessage.info('请在偶遇后邀请组队，或创建新队伍')
}

const startBattle = async (teamId) => {
  try {
    const result = await bossBattleApi.startBattle({
      team_id: teamId
    })
    
    battleResult.value = result
    showBattleResultDialog.value = true
    
    if (result.battle_result?.victory) {
      ElMessage.success('战斗胜利！')
    } else {
      ElMessage.warning('战斗失败...')
    }
    
  } catch (error) {
    console.error('开始战斗失败:', error)
    ElMessage.error('开始战斗失败: ' + (error.message || '未知错误'))
  }
}

onMounted(() => {
  loadHallData()
})
</script>

<style lang="scss" scoped>
.boss-hall-page {
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

.hall-main {
  position: relative;
  z-index: 1;
  max-width: 1200px;
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
      background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(236, 72, 153, 0.1));
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ec4899;
      border: 1px solid rgba(236, 72, 153, 0.3);
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

.loading-state,
.empty-state {
  text-align: center;
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
    margin: 0 0 16px;
    text-align: center;
  }
}

.hall-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.element-info-bar {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(96, 165, 250, 0.1));
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 20px;

  .element-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 16px;
  }

  .element-cards {
    display: flex;
    gap: 16px;
    justify-content: center;
    margin-bottom: 12px;

    .element-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 12px 20px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.1);

      .element-symbol {
        font-size: 28px;
      }

      .element-name {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
      }
    }
  }

  .element-hint {
    text-align: center;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);

    .highlight {
      color: #a78bfa;
      font-weight: 600;
    }
  }
}

.transit-info {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(251, 191, 36, 0.1));
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 16px;
  padding: 16px 20px;

  .transit-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 12px;
  }

  .transit-events {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin: 0;
  }
}

.bosses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.boss-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(139, 92, 246, 0.05));
  border: 2px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15);
    transform: translateY(-2px);
  }

  &.boss-selected {
    border-color: rgba(139, 92, 246, 0.6);
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
  }
}

.boss-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;

  .boss-name-section {
    .boss-name {
      margin: 0 0 4px;
      font-size: 20px;
      font-weight: 700;
      background: linear-gradient(135deg, #8b5cf6, #ec4899);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .boss-title {
      margin: 0;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      font-style: italic;
    }
  }

  .boss-difficulty {
    .fluctuation-label {
      font-size: 11px;
      opacity: 0.8;
    }

    .fluctuation-value {
      font-size: 16px;
      font-weight: 700;
      margin-left: 4px;
    }
  }
}

.boss-description {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
  margin-bottom: 16px;
}

.boss-health-section {
  margin-bottom: 16px;

  .health-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .health-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
    }

    .health-value {
      font-size: 12px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

.boss-element-info {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;

  .element-item {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .label {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
    }

    .element-value {
      display: flex;
      align-items: center;
      gap: 4px;

      .symbol {
        font-size: 18px;
      }

      .name {
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
      }
    }

    &.weakness .element-value {
      color: #22c55e;
    }

    &.resistance .element-value {
      color: #ef4444;
    }
  }
}

.boss-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .stat-label {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
    }

    .stat-value {
      font-size: 14px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

.boss-planet {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 12px;
}

.boss-footer {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.teams-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
}

.teams-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.team-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(139, 92, 246, 0.4);
  }
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .team-name-section {
    display: flex;
    align-items: center;
    gap: 8px;

    .team-name {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
  }

  .team-energy {
    display: flex;
    flex-direction: column;
    align-items: flex-end;

    .energy-label {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.4);
    }

    .energy-value {
      font-size: 18px;
      font-weight: 700;
      color: #a78bfa;
    }
  }
}

.team-members {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;

  .team-member {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);

    &.leader {
      background: rgba(251, 191, 36, 0.1);
      border-color: rgba(251, 191, 36, 0.3);
    }

    .member-info {
      .member-name {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 2px;
      }

      .member-element {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 2px;

        .symbol {
          font-size: 14px;
        }
      }

      .member-power {
        font-size: 11px;
        color: #a78bfa;
      }
    }
  }

  .empty-slot {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: 80px;
    height: 80px;
    border: 2px dashed rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    color: rgba(255, 255, 255, 0.3);
    font-size: 11px;
  }
}

.team-element-check {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;

  .check-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }

  .element-checks {
    display: flex;
    gap: 8px;

    .element-check {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      padding: 6px 10px;
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.1);

      .symbol {
        font-size: 16px;
      }

      .name {
        font-size: 10px;
        color: rgba(255, 255, 255, 0.5);
      }

      .check {
        font-size: 11px;
        font-weight: 700;
      }

      &.present {
        background: rgba(34, 197, 94, 0.15);

        .check {
          color: #22c55e;
        }
      }

      &:not(.present) .check {
        color: #ef4444;
      }
    }
  }
}

.missing-elements {
  margin-bottom: 12px;
}

.team-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);

  .team-status-info {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.no-teams {
  padding: 40px;
  text-align: center;
}

.boss-detail-content {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e4e7ed;

    .detail-name-section {
      .detail-name {
        margin: 0 0 4px;
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(135deg, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .detail-title {
        margin: 0;
        font-size: 14px;
        color: #6b7280;
        font-style: italic;
      }
    }
  }

  h4 {
    margin: 0 0 12px;
    font-size: 15px;
    font-weight: 600;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .detail-lore {
    margin-bottom: 20px;
    padding: 16px;
    background: rgba(139, 92, 246, 0.05);
    border-radius: 12px;
    border-left: 3px solid #a78bfa;

    p {
      margin: 0;
      font-size: 13px;
      color: #4b5563;
      line-height: 1.7;
    }
  }

  .detail-stats {
    margin-bottom: 20px;

    .detail-health {
      margin-bottom: 16px;

      .health-display {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 8px;

        .health-number {
          font-size: 24px;
          font-weight: 700;
          color: #22c55e;
        }

        .health-divider {
          font-size: 16px;
          color: #9ca3af;
        }

        .total {
          color: #6b7280;
          font-weight: 500;
        }
      }
    }

    .detail-power {
      display: flex;
      gap: 32px;

      .power-item {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .power-label {
          font-size: 12px;
          color: #6b7280;
        }

        .power-value {
          font-size: 18px;
          font-weight: 600;
          color: #ef4444;
        }
      }
    }
  }

  .detail-elements {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;

    .element-detail {
      padding: 16px;
      border-radius: 12px;

      .element-display {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        .symbol {
          font-size: 32px;
        }

        .name {
          font-size: 18px;
          font-weight: 600;
        }
      }

      .element-hint {
        font-size: 12px;
        color: #6b7280;

        .highlight {
          color: #8b5cf6;
          font-weight: 600;
        }
      }

      &.weakness {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);

        .name {
          color: #22c55e;
        }
      }

      &.resistance {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);

        .name {
          color: #ef4444;
        }
      }
    }
  }

  .detail-skills {
    margin-bottom: 20px;

    .skills-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .skill-card {
      padding: 16px;
      background: rgba(255, 255, 255, 0.5);
      border: 1px solid #e4e7ed;
      border-radius: 12px;

      &.ultimate {
        background: rgba(239, 68, 68, 0.05);
        border-color: rgba(239, 68, 68, 0.3);
      }

      .skill-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        .skill-name {
          font-size: 15px;
          font-weight: 600;
          color: #374151;
        }
      }

      .skill-description {
        margin: 0 0 10px;
        font-size: 13px;
        color: #6b7280;
        line-height: 1.5;
      }

      .skill-stats {
        display: flex;
        gap: 20px;

        .skill-stat {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #6b7280;

          .stat-label {
            color: #9ca3af;
          }

          .symbol {
            font-size: 16px;
          }

          .damage {
            color: #ef4444;
            font-weight: 600;
          }
        }
      }
    }
  }

  .detail-timing {
    .timing-info {
      display: flex;
      gap: 32px;

      .timing-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #6b7280;

        .timing-label {
          color: #9ca3af;
        }
      }
    }
  }
}

.create-team-hint {
  margin-top: 16px;

  ul {
    margin: 8px 0 0;
    padding-left: 20px;

    li {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 4px;
    }
  }
}

.battle-result-content {
  .result-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;

    .result-icon {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .result-title {
      h2 {
        margin: 0 0 4px;
        font-size: 24px;
        font-weight: 700;
      }

      p {
        margin: 0;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.7);
      }
    }

    &.victory {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.15));
      border: 1px solid rgba(34, 197, 94, 0.3);

      .result-icon {
        color: #22c55e;
      }

      .result-title h2 {
        color: #22c55e;
      }
    }

    &.defeat {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(248, 113, 113, 0.15));
      border: 1px solid rgba(239, 68, 68, 0.3);

      .result-icon {
        color: #ef4444;
      }

      .result-title h2 {
        color: #ef4444;
      }
    }
  }

  .battle-story {
    margin-bottom: 20px;
    padding: 16px;
    background: rgba(139, 92, 246, 0.05);
    border-radius: 12px;

    h4 {
      margin: 0 0 12px;
      font-size: 15px;
      font-weight: 600;
      color: #374151;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .story-intro {
      p {
        margin: 0 0 16px;
        font-size: 13px;
        color: #4b5563;
        line-height: 1.7;
      }
    }

    .story-phases {
      margin-bottom: 16px;

      .story-phase {
        margin-bottom: 12px;
        padding: 12px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 8px;

        h5 {
          margin: 0 0 6px;
          font-size: 13px;
          font-weight: 600;
          color: #374151;
        }

        p {
          margin: 0 0 8px;
          font-size: 12px;
          color: #6b7280;
          line-height: 1.6;
        }

        .key-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          align-items: center;

          .action-label {
            font-size: 11px;
            color: #9ca3af;
          }

          .action-item {
            font-size: 11px;
            padding: 2px 8px;
            background: rgba(139, 92, 246, 0.1);
            color: #8b5cf6;
            border-radius: 4px;
          }
        }
      }
    }

    .story-climax {
      margin-bottom: 16px;
      padding: 12px;
      background: rgba(236, 72, 153, 0.05);
      border-radius: 8px;
      border-left: 3px solid #ec4899;

      h5 {
        margin: 0 0 6px;
        font-size: 13px;
        font-weight: 600;
        color: #374151;
      }

      p {
        margin: 0;
        font-size: 12px;
        color: #6b7280;
        line-height: 1.6;
      }
    }

    .story-highlights,
    .story-quotes {
      margin-bottom: 12px;

      h5 {
        margin: 0 0 8px;
        font-size: 13px;
        font-weight: 600;
        color: #374151;
      }

      .highlight-item {
        display: flex;
        gap: 6px;
        margin-bottom: 6px;
        font-size: 12px;

        .highlight-char {
          font-weight: 600;
          color: #8b5cf6;
        }

        .highlight-text {
          color: #6b7280;
        }
      }

      .quote-item {
        padding: 10px 14px;
        background: rgba(139, 92, 246, 0.08);
        border-left: 3px solid #a78bfa;
        border-radius: 4px;
        font-size: 13px;
        color: #4b5563;
        font-style: italic;
        margin-bottom: 6px;
      }
    }
  }

  .battle-stats {
    margin-bottom: 20px;

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;

      .stat-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 12px;
        border: 1px solid #e4e7ed;

        .stat-label {
          font-size: 12px;
          color: #9ca3af;
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 700;
          color: #374151;

          &.damage {
            color: #22c55e;
          }

          &.received {
            color: #ef4444;
          }
        }
      }
    }
  }

  .battle-rewards {
    .rewards-display {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;

      .reward-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(251, 191, 36, 0.1);
        border: 1px solid rgba(251, 191, 36, 0.3);
        border-radius: 12px;

        .reward-icon {
          font-size: 28px;
        }

        .reward-info {
          display: flex;
          flex-direction: column;

          .reward-name {
            font-size: 13px;
            color: #6b7280;
          }

          .reward-value {
            font-size: 18px;
            font-weight: 700;
            color: #f59e0b;
          }
        }

        &.stardust {
          background: rgba(251, 191, 36, 0.1);
          border-color: rgba(251, 191, 36, 0.3);
        }

        &.item {
          background: rgba(139, 92, 246, 0.1);
          border-color: rgba(139, 92, 246, 0.3);
        }
      }
    }
  }
}
</style>