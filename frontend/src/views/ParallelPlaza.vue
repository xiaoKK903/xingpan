<template>
  <div class="parallel-plaza" :class="{ 'plaza-warning': weatherPanel?.has_warning, 'plaza-critical': weatherPanel?.is_critical }">
    <div class="energy-weather-panel" :class="{ 'warning-active': weatherPanel?.has_warning, 'critical-active': weatherPanel?.is_critical }">
      <div class="panel-header">
        <div class="panel-title-section">
          <div class="title-icon">
            <el-icon :size="28"><Sunny /></el-icon>
          </div>
          <div class="title-text">
            <h3 class="panel-title">全局能量气象站</h3>
            <p class="panel-subtitle">实时监测集体场域能量与天象状态</p>
          </div>
        </div>
        
        <div class="panel-actions">
          <el-tag 
            v-if="weatherPanel?.has_warning" 
            :type="weatherPanel?.is_critical ? 'danger' : 'warning'"
            effect="dark"
            class="warning-tag"
          >
            <el-icon><Warning /></el-icon>
            {{ weatherPanel?.is_critical ? '红色预警' : '天象预警' }}
          </el-tag>
          
          <el-button type="primary" link @click="showMissionPanel = true">
            <el-icon><List /></el-icon>
            能量任务
            <el-badge :value="missions.length" :max="99" class="mission-badge" />
          </el-button>
          
          <el-button type="success" link @click="showRewardCenter = true">
            <el-icon><Coin /></el-icon>
            奖励中心
          </el-button>
          
          <el-dropdown @command="handleDropdownCommand" v-if="showDevTools">
            <el-button type="info" link>
              <el-icon><Tools /></el-icon>
              测试工具
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="simulate_mars">
                  <el-icon><WarningFilled /></el-icon>
                  模拟火星逆行(红色预警)
                </el-dropdown-item>
                <el-dropdown-item command="simulate_mercury">
                  <el-icon><Warning /></el-icon>
                  模拟水星逆行
                </el-dropdown-item>
                <el-dropdown-item command="simulate_saturn">
                  <el-icon><Warning /></el-icon>
                  模拟土星逆行
                </el-dropdown-item>
                <el-dropdown-item command="simulate_mars_saturn">
                  <el-icon><WarningFilled /></el-icon>
                  模拟火星四分土星
                </el-dropdown-item>
                <el-dropdown-item divided command="clear_simulate">
                  <el-icon><CircleCheck /></el-icon>
                  清除模拟状态
                </el-dropdown-item>
                <el-dropdown-item command="refresh">
                  <el-icon><Refresh /></el-icon>
                  刷新气象数据
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <div class="panel-content" v-loading="isLoadingWeather">
        <div class="energy-score-section">
          <div class="score-circle" :style="getScoreCircleStyle">
            <div class="score-value">{{ weatherPanel?.energy_score || 0 }}</div>
            <div class="score-label">场域能量值</div>
          </div>
          <div class="energy-info">
            <div class="mood-info">
              <el-tag :type="getMoodTagType" size="large">
                <el-icon><Mood /></el-icon>
                {{ weatherPanel?.collective_mood_label || '平稳' }}
              </el-tag>
              <span class="mood-text">当前集体情绪</span>
            </div>
            <div class="weather-info">
              <span class="weather-icon">{{ weatherPanel?.weather_icon || '⛅' }}</span>
              <span class="weather-label">{{ weatherPanel?.weather_label || '多云' }}</span>
              <el-tag v-if="weatherPanel?.online_user_count" size="small">
                <el-icon><User /></el-icon>
                在线: {{ weatherPanel.online_user_count }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <div class="dimension-section" v-if="weatherPanel?.dimension_energies?.length">
          <div class="section-title">
            <el-icon><TrendCharts /></el-icon>
            维度能量分布
          </div>
          <div class="dimension-list">
            <div 
              v-for="dim in weatherPanel.dimension_energies" 
              :key="dim.dimension"
              class="dimension-item"
            >
              <div class="dimension-header">
                <span class="dimension-icon" :style="{ color: dim.color }">{{ dim.icon }}</span>
                <span class="dimension-name">{{ dim.name_cn }}</span>
                <span class="dimension-score">{{ dim.score }}</span>
              </div>
              <el-progress 
                :percentage="dim.score" 
                :color="dim.color"
                :stroke-width="8"
              />
              <span class="dimension-level" :style="{ color: dim.color }">{{ dim.level_label }}</span>
            </div>
          </div>
        </div>
        
        <div class="ominous-section" v-if="weatherPanel?.ominous_events?.length > 0">
          <div class="section-title warning-title">
            <el-icon><WarningFilled /></el-icon>
            天象预警
          </div>
          <div class="ominous-list">
            <div 
              v-for="(event, idx) in weatherPanel.ominous_events" 
              :key="idx"
              class="ominous-item"
              :class="{ 'critical-event': event.is_critical }"
            >
              <div class="event-header">
                <span class="event-icon">{{ event.icon }}</span>
                <span class="event-name">{{ event.name }}</span>
                <el-tag 
                  v-if="event.is_critical" 
                  type="danger" 
                  effect="dark"
                  size="small"
                >
                  红色预警
                </el-tag>
                <el-tag 
                  v-else-if="event.is_warning" 
                  type="warning" 
                  effect="dark"
                  size="small"
                >
                  预警
                </el-tag>
              </div>
              <p class="event-desc">{{ event.description }}</p>
              <div class="event-affected" v-if="event.affected_areas?.length">
                <span class="affected-label">影响领域:</span>
                <el-tag 
                  v-for="area in event.affected_areas" 
                  :key="area"
                  size="small"
                  :type="event.is_critical ? 'danger' : 'warning'"
                >
                  {{ area }}
                </el-tag>
              </div>
              <div class="event-recommendations" v-if="event.recommendations?.length">
                <span class="rec-label">建议:</span>
                <ul class="rec-list">
                  <li v-for="(rec, rIdx) in event.recommendations" :key="rIdx">
                    <el-icon><CircleCheck /></el-icon>
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <div class="quick-missions" v-if="missions?.length > 0">
          <div class="section-title">
            <el-icon><MagicStick /></el-icon>
            当前暖心任务
            <el-button type="primary" link size="small" @click="showMissionPanel = true">
              查看全部
            </el-button>
          </div>
          <div class="quick-mission-list">
            <div 
              v-for="(mission, idx) in missions.slice(0, 3)" 
              :key="mission.id"
              class="quick-mission-item"
              :class="{ 'mission-completed': mission.is_completed, 'bonus-mission': mission.is_bonus }"
              @click="handleMissionClick(mission)"
            >
              <div class="mission-icon" :class="getMissionIconClass(mission.type)">
                <el-icon><Promotion /></el-icon>
              </div>
              <div class="mission-info">
                <span class="mission-title">
                  {{ mission.title }}
                  <el-tag v-if="mission.is_bonus" type="danger" size="small" effect="dark">
                    +50% 加成
                  </el-tag>
                  <el-tag v-if="mission.is_completed" type="success" size="small">
                    已完成
                  </el-tag>
                </span>
                <span class="mission-desc">{{ mission.description }}</span>
              </div>
              <div class="mission-reward">
                <span class="reward-icon">✨</span>
                <span class="reward-amount">{{ mission.base_reward }}</span>
                <span class="reward-label">星元碎片</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="plaza-header">
      <h1 class="plaza-title">
        <el-icon :size="32"><Star /></el-icon>
        平行人生广场
      </h1>
      <p class="plaza-subtitle">拖动两个虚拟化身相遇，探索星盘相位带来的剧情冲突</p>
    </div>
    
    <div class="plaza-controls">
      <el-card class="control-card">
        <template #header>
          <div class="card-header">
            <span>角色配置</span>
            <el-select v-model="selectedStyle" class="style-select" placeholder="选择剧情风格">
              <el-option label="现代都市" value="modern" />
              <el-option label="中世纪" value="medieval" />
              <el-option label="古风" value="ancient" />
              <el-option label="科幻" value="scifi" />
            </el-select>
          </div>
        </template>
        
        <div class="character-configs">
          <div class="character-config">
            <h4>角色 A</h4>
            <el-form :model="characterA" label-width="80px" size="small">
              <el-form-item label="名称">
                <el-input v-model="characterA.name" placeholder="输入角色名称" />
              </el-form-item>
              <el-form-item label="出生日期">
                <el-date-picker
                  v-model="characterA.birthDate"
                  type="date"
                  placeholder="选择出生日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>
              <el-form-item label="出生时间">
                <el-time-picker
                  v-model="characterA.birthTime"
                  placeholder="选择出生时间"
                  format="HH:mm"
                  value-format="HH:mm"
                />
              </el-form-item>
              <el-form-item label="出生地点">
                <el-input
                  v-model="characterA.birthPlace"
                  placeholder="输入城市名称"
                  @input="searchCity('A', characterA.birthPlace)"
                />
                <el-autocomplete
                  v-if="citySuggestionsA.length > 0"
                  v-model="characterA.birthPlace"
                  :fetch-suggestions="fetchCitySuggestionsA"
                  @select="handleCitySelect('A', $event)"
                  placeholder="选择城市"
                  style="width: 100%; margin-top: 4px;"
                />
              </el-form-item>
            </el-form>
          </div>
          
          <div class="character-config">
            <h4>角色 B</h4>
            <el-form :model="characterB" label-width="80px" size="small">
              <el-form-item label="名称">
                <el-input v-model="characterB.name" placeholder="输入角色名称" />
              </el-form-item>
              <el-form-item label="出生日期">
                <el-date-picker
                  v-model="characterB.birthDate"
                  type="date"
                  placeholder="选择出生日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>
              <el-form-item label="出生时间">
                <el-time-picker
                  v-model="characterB.birthTime"
                  placeholder="选择出生时间"
                  format="HH:mm"
                  value-format="HH:mm"
                />
              </el-form-item>
              <el-form-item label="出生地点">
                <el-input
                  v-model="characterB.birthPlace"
                  placeholder="输入城市名称"
                  @input="searchCity('B', characterB.birthPlace)"
                />
                <el-autocomplete
                  v-if="citySuggestionsB.length > 0"
                  v-model="characterB.birthPlace"
                  :fetch-suggestions="fetchCitySuggestionsB"
                  @select="handleCitySelect('B', $event)"
                  placeholder="选择城市"
                  style="width: 100%; margin-top: 4px;"
                />
              </el-form-item>
            </el-form>
          </div>
        </div>
        
        <div class="action-buttons">
          <el-button type="primary" @click="useTestData" :loading="isTesting">
            <el-icon><MagicStick /></el-icon>
            使用测试数据
          </el-button>
          <el-button type="success" @click="analyzeConflict" :loading="isAnalyzing">
            <el-icon><Search /></el-icon>
            分析相位冲突
          </el-button>
          <el-button type="warning" @click="generateStory" :loading="isGenerating">
            <el-icon><EditPen /></el-icon>
            生成剧情对话
          </el-button>
        </div>
      </el-card>
    </div>
    
    <div class="plaza-arena">
      <div class="arena-header">
        <h3>虚拟广场</h3>
        <p class="arena-hint">拖动两个头像使其相遇，触发相遇剧情</p>
      </div>
      
      <div 
        ref="arenaRef"
        class="arena-container"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
      >
        <div class="arena-background">
          <div class="ground-pattern"></div>
          <div class="plaza-center">
            <el-icon :size="60"><Location /></el-icon>
          </div>
        </div>
        
        <div
          ref="avatarARef"
          class="avatar"
          :class="{ 'avatar-dragging': draggingAvatar === 'A', 'avatar-colliding': isColliding }"
          :style="{ left: avatarA.position.x + 'px', top: avatarA.position.y + 'px' }"
          @mousedown="startDragging('A', $event)"
        >
          <div class="avatar-inner">
            <div class="avatar-image">
              <el-avatar :size="80" :src="avatarA.avatarUrl">
                <el-icon :size="40"><User /></el-icon>
              </el-avatar>
            </div>
            <div class="avatar-label">
              <span class="avatar-name">{{ characterA.name || '角色A' }}</span>
              <span class="avatar-sign" v-if="avatarA.sunSign">{{ avatarA.sunSign }}</span>
            </div>
          </div>
          <div class="avatar-glow"></div>
        </div>
        
        <div
          ref="avatarBRef"
          class="avatar"
          :class="{ 'avatar-dragging': draggingAvatar === 'B', 'avatar-colliding': isColliding }"
          :style="{ left: avatarB.position.x + 'px', top: avatarB.position.y + 'px' }"
          @mousedown="startDragging('B', $event)"
        >
          <div class="avatar-inner">
            <div class="avatar-image">
              <el-avatar :size="80" :src="avatarB.avatarUrl">
                <el-icon :size="40"><UserFilled /></el-icon>
              </el-avatar>
            </div>
            <div class="avatar-label">
              <span class="avatar-name">{{ characterB.name || '角色B' }}</span>
              <span class="avatar-sign" v-if="avatarB.sunSign">{{ avatarB.sunSign }}</span>
            </div>
          </div>
          <div class="avatar-glow"></div>
        </div>
        
        <div v-if="isColliding" class="collision-effect">
          <div class="sparkles">
            <el-icon :size="30"><Lightning /></el-icon>
          </div>
          <div class="collision-text">相遇了！</div>
        </div>
      </div>
    </div>
    
    <el-dialog
      v-model="showEncounterDialog"
      title="相遇剧情"
      width="800px"
      :close-on-click-modal="false"
      class="encounter-dialog"
    >
      <div v-if="conflictAnalysis" class="conflict-analysis-section">
        <h4>
          <el-icon><Compass /></el-icon>
          相位冲突分析
        </h4>
        
        <div class="conflict-intensity">
          <el-tag :type="getIntensityTagType(conflictAnalysis.intensity.conflict_level_code)">
            关系强度: {{ conflictAnalysis.intensity.conflict_level }}
          </el-tag>
          <span class="intensity-detail">
            平均严重度: {{ conflictAnalysis.intensity.average_severity }}
          </span>
        </div>
        
        <div v-if="conflictAnalysis.conflicts.length > 0" class="conflict-list">
          <div 
            v-for="(conflict, index) in conflictAnalysis.conflicts" 
            :key="index"
            class="conflict-item"
            :class="{ 'conflict-harmonious': conflict.is_harmonious }"
          >
            <div class="conflict-header">
              <span class="conflict-pair">{{ conflict.planet_pair }}</span>
              <el-tag :type="conflict.is_harmonious ? 'success' : 'danger'" size="small">
                {{ conflict.aspect_type }}
              </el-tag>
              <span class="conflict-severity">
                严重度: {{ conflict.severity }}
              </span>
            </div>
            <div class="conflict-theme">
              <el-icon><Brush /></el-icon>
              戏剧主题: {{ conflict.drama_theme }}
            </div>
            <div class="conflict-atmosphere">
              <el-icon><ChatDotRound /></el-icon>
              氛围: {{ conflict.atmosphere }}
            </div>
            <div class="conflict-tags">
              <el-tag 
                v-for="(tag, tagIndex) in conflict.conflict_tags" 
                :key="tagIndex"
                size="small"
                :type="conflict.is_harmonious ? 'success' : 'warning'"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <div v-else class="no-conflict">
          <el-empty description="未检测到明显的相位冲突，关系基础和谐">
            <el-button type="primary" @click="generateStory">
              继续生成温馨剧情
            </el-button>
          </el-empty>
        </div>
      </div>
      
      <div v-if="storyData" class="story-section">
        <h4>
          <el-icon><Film /></el-icon>
          相遇剧情
        </h4>
        
        <div class="scene-description">
          <el-icon><Camera /></el-icon>
          <p>{{ storyData.scene_description }}</p>
        </div>
        
        <div class="dialogue-container">
          <div 
            v-for="(dialogue, index) in storyData.dialogues" 
            :key="index"
            class="dialogue-item"
            :class="{ 'dialogue-left': dialogue.speaker === (characterA.name || '角色A'), 'dialogue-right': dialogue.speaker === (characterB.name || '角色B') }"
          >
            <div class="dialogue-speaker">
              <el-avatar :size="32">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="speaker-name">{{ dialogue.speaker }}</span>
              <span v-if="dialogue.emotion" class="speaker-emotion">
                ({{ dialogue.emotion }})
              </span>
            </div>
            <div class="dialogue-bubble">
              <p>{{ dialogue.line }}</p>
              <p v-if="dialogue.inner_thought" class="inner-thought">
                <el-icon><ChatLineRound /></el-icon>
                内心: {{ dialogue.inner_thought }}
              </p>
            </div>
          </div>
        </div>
        
        <div v-if="storyData.atmosphere_summary" class="atmosphere-summary">
          <h5>氛围总结</h5>
          <p>{{ storyData.atmosphere_summary }}</p>
        </div>
        
        <div v-if="storyData.conflict_hint" class="conflict-hint">
          <h5>相位冲突暗示</h5>
          <p>{{ storyData.conflict_hint }}</p>
        </div>
      </div>
      
      <div v-if="isGenerating && !storyData" class="generating-section">
        <el-empty description="正在生成剧情对话...">
          <el-progress type="circle" :percentage="50" :status="'exception'" />
        </el-empty>
      </div>
      
      <template #footer>
        <el-button @click="showEncounterDialog = false">关闭</el-button>
        <el-button type="primary" @click="regenerateStory" :loading="isGenerating">
          重新生成
        </el-button>
        <el-button type="success" @click="generateStory">
          生成更多剧情
        </el-button>
        <el-button type="warning" @click="openBossSelection" :loading="isInvitingToTeam">
          <el-icon><UserFilled /></el-icon>
          邀请组队挑战BOSS
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showStoryDialog"
      title="剧情生成"
      width="800px"
    >
      <div v-if="isGenerating" class="generating-status">
        <el-steps :active="generatingStep" align-center>
          <el-step title="分析相位冲突" />
          <el-step title="调用AI生成" />
          <el-step title="生成对话" />
        </el-steps>
        
        <div class="generating-text">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>{{ generatingMessage }}</span>
        </div>
      </div>
      
      <div v-else-if="storyData" class="story-preview">
        <pre>{{ JSON.stringify(storyData, null, 2) }}</pre>
      </div>
    </el-dialog>
    
    <el-dialog
      v-model="showBossSelectDialog"
      title="选择星象BOSS"
      width="900px"
      class="boss-select-dialog"
    >
      <div v-if="isGettingBosses" class="loading-bosses">
        <el-empty description="正在加载BOSS列表...">
          <el-progress type="circle" :percentage="50" :status="'exception'" />
        </el-empty>
      </div>
      
      <div v-else-if="activeBosses.length === 0" class="no-bosses">
        <el-empty description="当前没有活跃的星象BOSS" />
      </div>
      
      <div v-else class="boss-list">
        <div
          v-for="boss in activeBosses"
          :key="boss.boss_id"
          class="boss-card"
          @click="selectBoss(boss)"
        >
          <div class="boss-header">
            <h3 class="boss-name">{{ boss.name }}</h3>
            <el-tag :type="getBossDifficultyTag(boss.fluctuation_value)" size="small">
              波动值: {{ boss.fluctuation_value }}
            </el-tag>
          </div>
          <p class="boss-title">{{ boss.title }}</p>
          <p class="boss-description">{{ boss.description }}</p>
          
          <div class="boss-stats">
            <div class="stat-item">
              <span class="stat-label">生命值</span>
              <el-progress 
                :percentage="boss.health_percentage" 
                :color="getBossHealthColor(boss.health_percentage)"
                :stroke-width="10"
              />
              <span class="stat-value">{{ boss.current_health }} / {{ boss.max_health }}</span>
            </div>
            
            <div class="element-info">
              <div class="weakness">
                <span class="label">弱点:</span>
                <span class="element-value weakness-element">
                  {{ boss.weakness_symbol }} {{ boss.weakness_element }}
                </span>
              </div>
              <div class="resistance">
                <span class="label">抵抗:</span>
                <span class="element-value resistance-element">
                  {{ boss.resistance_symbol }} {{ boss.resistance_element }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="boss-trigger">
            <el-tag size="small" type="info">
              触发天象: {{ boss.trigger_event }}
            </el-tag>
            <span v-if="boss.planet_involved" class="planet-info">
              涉及行星: {{ boss.planet_involved }}
            </span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showBossSelectDialog = false">取消</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showTeamResultDialog"
      title="队伍创建成功"
      width="700px"
      class="team-result-dialog"
    >
      <div v-if="currentTeam" class="team-result">
        <div class="team-header">
          <h3>{{ currentTeam.team_name }}</h3>
          <el-tag :type="currentTeam.status === 'ready' ? 'success' : 'warning'">
            {{ currentTeam.status === 'ready' ? '准备就绪' : '招募中' }}
          </el-tag>
        </div>
        
        <div class="team-members">
          <h4>队伍成员</h4>
          <div class="member-list">
            <div
              v-for="member in currentTeam.members"
              :key="member.member_id"
              class="member-item"
              :class="{ 'leader': member.is_leader }"
            >
              <el-avatar :size="50">
                <el-icon :size="24"><User /></el-icon>
              </el-avatar>
              <div class="member-info">
                <div class="member-name">
                  {{ member.name }}
                  <el-tag v-if="member.is_leader" type="primary" size="small">队长</el-tag>
                </div>
                <div class="member-element">
                  <span class="element-symbol">{{ member.element_symbol }}</span>
                  <span>{{ member.element }}象</span>
                </div>
                <div class="member-power">
                  战力: {{ member.combat_power }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="team-status">
          <div class="status-item">
            <span class="status-label">元素覆盖:</span>
            <div class="element-checks">
              <span 
                v-for="e in ['火', '土', '风', '水']" 
                :key="e"
                class="element-check"
                :class="{ 'present': currentTeam.elements_present.includes(e) }"
              >
                <span class="symbol">{{ e === '火' ? '🔥' : e === '土' ? '🪨' : e === '风' ? '🌪️' : '💧' }}</span>
                <span class="name">{{ e }}</span>
                <span class="check">{{ currentTeam.elements_present.includes(e) ? '✓' : '✗' }}</span>
              </span>
            </div>
          </div>
          
          <div class="status-item">
            <span class="status-label">队伍总能量:</span>
            <span class="status-value highlight">{{ currentTeam.total_energy }}</span>
          </div>
        </div>
        
        <div v-if="!currentTeam.has_all_elements" class="missing-elements-warning">
          <el-alert
            title="元素不完整"
            :description="`缺少元素: ${currentTeam.missing_elements.join(', ')}。需要招募对应元素的队员才能开战。`"
            type="warning"
            :closable="false"
            show-icon
          />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showTeamResultDialog = false">关闭</el-button>
        <el-button 
          v-if="currentTeam?.has_all_elements" 
          type="primary" 
          @click="startBattleFromTeam"
          :loading="isInvitingToTeam"
        >
          开战！
        </el-button>
        <el-button 
          v-else 
          type="warning" 
          disabled
        >
          需要补齐元素
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showMissionPanel"
      title="能量任务中心"
      width="800px"
      class="mission-panel-dialog"
    >
      <div v-loading="isLoadingMissions" class="mission-panel-content">
        <div v-if="missions.length === 0" class="no-missions">
          <el-empty description="当前没有可用的能量任务" />
        </div>
        
        <div v-else class="mission-list">
          <div
            v-for="mission in missions"
            :key="mission.id"
            class="mission-card"
            :class="{ 
              'mission-completed': mission.is_completed, 
              'bonus-mission': mission.is_bonus,
              'mission-selected': selectedMission?.id === mission.id
            }"
            @click="selectMission(mission)"
          >
            <div class="mission-header">
              <div class="mission-icon" :class="getMissionIconClass(mission.type)">
                <el-icon><Promotion /></el-icon>
              </div>
              <div class="mission-title-section">
                <h4 class="mission-title">
                  {{ mission.title }}
                  <el-tag v-if="mission.is_bonus" type="danger" size="small" effect="dark">
                    +50% 加成
                  </el-tag>
                  <el-tag v-if="mission.is_completed" type="success" size="small">
                    已完成
                  </el-tag>
                </h4>
                <div class="mission-meta">
                  <el-tag size="small" :type="getDifficultyTagType(mission.difficulty)">
                    {{ mission.difficulty_label }}
                  </el-tag>
                  <span v-if="mission.duration_minutes" class="mission-duration">
                    <el-icon><Timer /></el-icon>
                    {{ mission.duration_minutes }} 分钟
                  </span>
                  <span v-if="mission.mood_trigger" class="mission-mood">
                    <el-tag size="small">
                      {{ mission.mood_trigger === 'challenging' ? '挑战期特护' : mission.mood_trigger === 'tense' ? '紧张期关怀' : mission.mood_trigger === 'harmonious' ? '和谐期互动' : '日常任务' }}
                    </el-tag>
                  </span>
                </div>
              </div>
              <div class="mission-reward">
                <span class="reward-icon">✨</span>
                <span class="reward-amount">{{ mission.base_reward }}</span>
                <span class="reward-label">星元碎片</span>
              </div>
            </div>
            
            <p class="mission-description">{{ mission.description }}</p>
            
            <div v-if="mission.is_bonus && mission.bonus_reason" class="bonus-hint">
              <el-icon><Star /></el-icon>
              {{ mission.bonus_reason }}
            </div>
            
            <div class="mission-actions">
              <el-button
                v-if="!mission.is_completed"
                type="primary"
                @click.stop="completeMission(mission)"
                :loading="completingMissionId === mission.id"
              >
                完成任务
              </el-button>
              <el-button
                v-else
                type="success"
                disabled
              >
                已领取奖励
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="mission-footer">
          <div class="footer-info">
            <span>
              <el-tag type="info">星元碎片</el-tag>
              完成任务获得，用于星能共鸣池
            </span>
          </div>
          <el-button @click="showMissionPanel = false">关闭</el-button>
          <el-button type="primary" @click="refreshMissions">
            <el-icon><Refresh /></el-icon>
            刷新任务
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showRewardCenter"
      title="奖励中心"
      width="700px"
      class="reward-center-dialog"
    >
      <div class="reward-center-content">
        <div class="balance-section">
          <div class="balance-card fragment-balance">
            <div class="balance-icon">
              <el-icon :size="32"><Coin /></el-icon>
            </div>
            <div class="balance-info">
              <span class="balance-label">星元碎片</span>
              <span class="balance-amount">{{ userAssets?.stardust_fragment_balance || 0 }}</span>
              <span class="balance-desc">任务奖励获得，用于星能共鸣池</span>
            </div>
          </div>
          
          <div class="balance-card point-balance">
            <div class="balance-icon">
              <el-icon :size="32"><Wallet /></el-icon>
            </div>
            <div class="balance-info">
              <span class="balance-label">星尘积分</span>
              <span class="balance-amount">{{ userAssets?.stardust_point_balance || 0 }}</span>
              <span class="balance-desc">消耗型货币，用于能量注入</span>
            </div>
          </div>
        </div>
        
        <el-tabs v-model="rewardTab" class="reward-tabs">
          <el-tab-pane label="完成记录" name="completions">
            <div v-loading="isLoadingCompletions" class="completions-list">
              <div v-if="completions.length === 0" class="no-completions">
                <el-empty description="还没有完成任何任务" />
              </div>
              <div v-else>
                <div
                  v-for="completion in completions"
                  :key="completion.id"
                  class="completion-item"
                >
                  <div class="completion-info">
                    <span class="completion-title">{{ completion.mission_title }}</span>
                    <span class="completion-time">
                      {{ formatCompletionTime(completion.created_at) }}
                    </span>
                  </div>
                  <div class="completion-reward">
                    <span class="reward-icon">✨</span>
                    <span class="reward-amount">+{{ completion.reward_amount }}</span>
                    <el-tag v-if="completion.is_bonus" type="danger" size="small">加成</el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="交易记录" name="transactions">
            <div v-loading="isLoadingTransactions" class="transactions-list">
              <div v-if="transactions.length === 0" class="no-transactions">
                <el-empty description="还没有交易记录" />
              </div>
              <div v-else>
                <div
                  v-for="tx in transactions"
                  :key="tx.id"
                  class="transaction-item"
                  :class="{ 'tx-positive': tx.amount > 0, 'tx-negative': tx.amount < 0 }"
                >
                  <div class="transaction-info">
                    <span class="transaction-description">{{ tx.description }}</span>
                    <span class="transaction-time">
                      {{ formatCompletionTime(tx.created_at) }}
                    </span>
                    <el-tag size="small">
                      {{ tx.currency_type === 'fragment' ? '星元碎片' : '星尘积分' }}
                    </el-tag>
                  </div>
                  <div class="transaction-amount">
                    <span class="amount-number" :class="{ 'positive': tx.amount > 0, 'negative': tx.amount < 0 }">
                      {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
                    </span>
                    <span class="balance-change">
                      {{ tx.balance_before }} → {{ tx.balance_after }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <el-button @click="showRewardCenter = false">关闭</el-button>
        <el-button type="primary" @click="refreshRewardCenter">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Star, MagicStick, Search, EditPen, User, UserFilled, 
  Location, Lightning, Compass, Brush, ChatDotRound, 
  Film, Camera, ChatLineRound, Loading, ArrowDown,
  Sunny, Warning, List, Coin, Tools, ArrowDown as ArrowDownIcon,
  Refresh, WarningFilled, CircleCheck, Promotion,
  Timer, Wallet, TrendCharts, Star as StarIcon,
  Moon as Mood
} from '@element-plus/icons-vue'
import { geoApi, plazaApi, bossBattleApi, energyWeatherApi } from '@/api'

const ZODIAC_ELEMENT_MAP = {
  '白羊座': '火',
  '狮子座': '火',
  '射手座': '火',
  '金牛座': '土',
  '处女座': '土',
  '摩羯座': '土',
  '双子座': '风',
  '天秤座': '风',
  '水瓶座': '风',
  '巨蟹座': '水',
  '天蝎座': '水',
  '双鱼座': '水'
}

const getElementFromSunSign = (sunSign) => {
  if (!sunSign) return null
  return ZODIAC_ELEMENT_MAP[sunSign] || null
}

const arenaRef = ref(null)
const avatarARef = ref(null)
const avatarBRef = ref(null)

const selectedStyle = ref('modern')
const isTesting = ref(false)
const isAnalyzing = ref(false)
const isGenerating = ref(false)
const generatingStep = ref(0)
const generatingMessage = ref('准备中...')

const showEncounterDialog = ref(false)
const showStoryDialog = ref(false)

const draggingAvatar = ref(null)
const dragOffset = reactive({ x: 0, y: 0 })
const isColliding = ref(false)

const characterA = reactive({
  name: '夜行者',
  birthDate: '1988-10-25',
  birthTime: '22:30',
  birthPlace: '北京',
  latitude: 39.9042,
  longitude: 116.4074
})

const characterB = reactive({
  name: '光明使者',
  birthDate: '1990-07-15',
  birthTime: '08:15',
  birthPlace: '上海',
  latitude: 31.2304,
  longitude: 121.4737
})

const avatarA = reactive({
  position: { x: 100, y: 200 },
  avatarUrl: '',
  sunSign: ''
})

const avatarB = reactive({
  position: { x: 400, y: 200 },
  avatarUrl: '',
  sunSign: ''
})

const citySuggestionsA = ref([])
const citySuggestionsB = ref([])

const conflictAnalysis = ref(null)
const storyData = ref(null)
const encounterResult = ref(null)

const showBossSelectDialog = ref(false)
const showTeamResultDialog = ref(false)
const isInvitingToTeam = ref(false)
const isGettingBosses = ref(false)
const isStartingBattle = ref(false)
const battlePollingId = ref(null)

const activeBosses = ref([])
const selectedBoss = ref(null)
const currentTeam = ref(null)
const lastBattleResult = ref(null)
const currentBattleId = ref(null)

const showMissionPanel = ref(false)
const showRewardCenter = ref(false)
const rewardTab = ref('completions')

const isLoadingWeather = ref(false)
const isLoadingMissions = ref(false)
const isLoadingCompletions = ref(false)
const isLoadingTransactions = ref(false)
const completingMissionId = ref(null)

const showDevTools = ref(true)

const weatherPanel = ref(null)
const missions = ref([])
const selectedMission = ref(null)
const completions = ref([])
const transactions = ref([])
const userAssets = ref({
  stardust_fragment_balance: 0,
  stardust_point_balance: 0
})

const characterPanels = ref({
  person_a: null,
  person_b: null
})

const getIntensityTagType = (code) => {
  const types = ['success', 'info', 'warning', 'danger', 'danger']
  return types[code] || 'info'
}

const getBossDifficultyTag = (fluctuation) => {
  if (fluctuation >= 80) return 'danger'
  if (fluctuation >= 70) return 'warning'
  if (fluctuation >= 60) return 'info'
  return 'success'
}

const getBossHealthColor = (percentage) => {
  if (percentage >= 70) return '#22c55e'
  if (percentage >= 40) return '#eab308'
  return '#ef4444'
}

const getScoreCircleStyle = computed(() => {
  const score = weatherPanel.value?.energy_score || 50
  let color = '#22c55e'
  if (score >= 80) color = '#22c55e'
  else if (score >= 60) color = '#eab308'
  else if (score >= 40) color = '#f97316'
  else color = '#ef4444'
  
  return {
    borderColor: color,
    boxShadow: `0 0 30px ${color}40`
  }
})

const getMoodTagType = computed(() => {
  const mood = weatherPanel.value?.collective_mood || 'neutral'
  const moodMap = {
    'harmonious': 'success',
    'neutral': 'info',
    'tense': 'warning',
    'challenging': 'danger'
  }
  return moodMap[mood] || 'info'
})

const getMissionIconClass = (type) => {
  const typeMap = {
    'connection': 'icon-connection',
    'self-reflection': 'icon-self-reflection',
    'action': 'icon-action',
    'social': 'icon-social',
    'creative': 'icon-creative',
    'healing': 'icon-healing'
  }
  return typeMap[type] || 'icon-default'
}

const getDifficultyTagType = (difficulty) => {
  const diffMap = {
    'easy': 'success',
    'medium': 'info',
    'hard': 'warning'
  }
  return diffMap[difficulty] || 'info'
}

const handleMissionClick = (mission) => {
  if (!mission.is_completed) {
    selectMission(mission)
    showMissionPanel.value = true
  }
}

const selectMission = (mission) => {
  selectedMission.value = mission
}

const handleDropdownCommand = async (command) => {
  try {
    switch (command) {
      case 'simulate_mars':
        await plazaApi.simulateOminous('mars_retrograde')
        ElMessage.success('已模拟触发火星逆行（红色预警）')
        await loadWeatherPanel()
        await loadMissions()
        break
      case 'simulate_mercury':
        await plazaApi.simulateOminous('mercury_retrograde')
        ElMessage.success('已模拟触发水星逆行')
        await loadWeatherPanel()
        await loadMissions()
        break
      case 'simulate_saturn':
        await plazaApi.simulateOminous('saturn_retrograde')
        ElMessage.success('已模拟触发土星逆行')
        await loadWeatherPanel()
        await loadMissions()
        break
      case 'simulate_mars_saturn':
        await plazaApi.simulateOminous('mars_square_saturn')
        ElMessage.success('已模拟触发火星四分土星（红色预警）')
        await loadWeatherPanel()
        await loadMissions()
        break
      case 'clear_simulate':
        await plazaApi.clearSimulatedOminous()
        ElMessage.success('已清除模拟凶星状态')
        await loadWeatherPanel()
        await loadMissions()
        break
      case 'refresh':
        await loadWeatherPanel()
        await loadMissions()
        ElMessage.success('气象数据已刷新')
        break
    }
  } catch (error) {
    console.error('测试工具操作失败:', error)
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

const loadWeatherPanel = async () => {
  isLoadingWeather.value = true
  try {
    const result = await plazaApi.getWeatherPanel()
    weatherPanel.value = result
    
    if (result.user_assets) {
      userAssets.value = result.user_assets
    }
  } catch (error) {
    console.error('加载气象面板失败:', error)
  } finally {
    isLoadingWeather.value = false
  }
}

const loadMissions = async () => {
  isLoadingMissions.value = true
  try {
    const result = await plazaApi.getPlazaMissions()
    if (result && result.missions) {
      missions.value = result.missions || []
    } else if (Array.isArray(result)) {
      missions.value = result
    } else {
      missions.value = []
    }
  } catch (error) {
    console.error('加载任务失败:', error)
    missions.value = []
  } finally {
    isLoadingMissions.value = false
  }
}

const refreshMissions = async () => {
  await loadMissions()
  ElMessage.success('任务已刷新')
}

const completeMission = async (mission) => {
  if (completingMissionId.value) return
  if (mission.is_completed) return
  
  completingMissionId.value = mission.id
  
  try {
    const result = await energyWeatherApi.completeMission(mission.id)
    
    if (result.success) {
      ElMessage.success(`任务完成！获得 ${result.reward_amount} 星元碎片`)
      
      mission.is_completed = true
      
      if (result.new_balance !== undefined) {
        userAssets.value.stardust_fragment_balance = result.new_balance
      }
      
      await loadMissions()
      await loadCompletions()
    }
  } catch (error) {
    console.error('完成任务失败:', error)
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      if (detail.error_code === 'MISSION_NOT_FOUND') {
        ElMessage.error('任务不存在')
      } else if (detail.error_code === 'MISSION_ALREADY_COMPLETED') {
        ElMessage.warning('您已完成过此任务，无法重复领取奖励')
        mission.is_completed = true
      } else {
        ElMessage.error(detail.message || '完成任务失败')
      }
    } else {
      ElMessage.error('完成任务失败: ' + (error.message || '未知错误'))
    }
  } finally {
    completingMissionId.value = null
  }
}

const loadCompletions = async () => {
  isLoadingCompletions.value = true
  try {
    const result = await energyWeatherApi.getMissionCompletions({ limit: 20 })
    completions.value = result.items || []
  } catch (error) {
    console.error('加载完成记录失败:', error)
    completions.value = []
  } finally {
    isLoadingCompletions.value = false
  }
}

const loadTransactions = async () => {
  isLoadingTransactions.value = true
  try {
    const result = await energyWeatherApi.getTransactionHistory({ limit: 20 })
    transactions.value = result.items || []
  } catch (error) {
    console.error('加载交易记录失败:', error)
    transactions.value = []
  } finally {
    isLoadingTransactions.value = false
  }
}

const formatCompletionTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const refreshRewardCenter = async () => {
  await Promise.all([
    loadWeatherPanel(),
    loadCompletions(),
    loadTransactions()
  ])
  ElMessage.success('奖励中心已刷新')
}

watch(showMissionPanel, (val) => {
  if (val) {
    loadMissions()
  }
})

watch(showRewardCenter, (val) => {
  if (val) {
    loadCompletions()
    loadTransactions()
  }
})

const startDragging = (avatar, event) => {
  draggingAvatar.value = avatar
  const avatarRef = avatar === 'A' ? avatarARef.value : avatarBRef.value
  const rect = avatarRef.getBoundingClientRect()
  
  dragOffset.x = event.clientX - rect.left
  dragOffset.y = event.clientY - rect.top
}

const handleMouseMove = (event) => {
  if (!draggingAvatar.value || !arenaRef.value) return
  
  const arenaRect = arenaRef.value.getBoundingClientRect()
  const avatarSize = 120
  
  let newX = event.clientX - arenaRect.left - dragOffset.x
  let newY = event.clientY - arenaRect.top - dragOffset.y
  
  newX = Math.max(0, Math.min(arenaRect.width - avatarSize, newX))
  newY = Math.max(0, Math.min(arenaRect.height - avatarSize, newY))
  
  if (draggingAvatar.value === 'A') {
    avatarA.position.x = newX
    avatarA.position.y = newY
  } else {
    avatarB.position.x = newX
    avatarB.position.y = newY
  }
  
  checkCollision()
}

const handleMouseUp = () => {
  if (draggingAvatar.value && isColliding.value) {
    handleEncounter()
  }
  draggingAvatar.value = null
}

const checkCollision = () => {
  const centerAx = avatarA.position.x + 60
  const centerAy = avatarA.position.y + 60
  const centerBx = avatarB.position.x + 60
  const centerBy = avatarB.position.y + 60
  
  const distance = Math.sqrt(
    Math.pow(centerAx - centerBx, 2) + 
    Math.pow(centerAy - centerBy, 2)
  )
  
  const collisionThreshold = 100
  
  isColliding.value = distance < collisionThreshold
}

const handleEncounter = async () => {
  if (!conflictAnalysis.value && !storyData.value) {
    await generateStory()
    return
  }
  
  showEncounterDialog.value = true
}

const searchCity = async (character, query) => {
  if (!query || query.length < 2) return
  
  try {
    const results = await geoApi.searchCity(query)
    const suggestions = results.map(city => ({
      value: city.name,
      ...city
    }))
    
    if (character === 'A') {
      citySuggestionsA.value = suggestions
    } else {
      citySuggestionsB.value = suggestions
    }
  } catch (error) {
    console.error('搜索城市失败:', error)
  }
}

const fetchCitySuggestionsA = (queryString, cb) => {
  cb(citySuggestionsA.value)
}

const fetchCitySuggestionsB = (queryString, cb) => {
  cb(citySuggestionsB.value)
}

const handleCitySelect = (character, city) => {
  if (character === 'A') {
    characterA.birthPlace = city.name
    characterA.latitude = city.latitude
    characterA.longitude = city.longitude
    citySuggestionsA.value = []
  } else {
    characterB.birthPlace = city.name
    characterB.latitude = city.latitude
    characterB.longitude = city.longitude
    citySuggestionsB.value = []
  }
}

const useTestData = async () => {
  isTesting.value = true
  
  characterA.name = '夜行者'
  characterA.birthDate = '1988-10-25'
  characterA.birthTime = '22:30'
  characterA.birthPlace = '北京'
  characterA.latitude = 39.9042
  characterA.longitude = 116.4074
  
  characterB.name = '光明使者'
  characterB.birthDate = '1990-07-15'
  characterB.birthTime = '08:15'
  characterB.birthPlace = '上海'
  characterB.latitude = 31.2304
  characterB.longitude = 121.4737
  
  avatarA.position = { x: 150, y: 180 }
  avatarB.position = { x: 350, y: 180 }
  isColliding.value = false
  
  ElMessage.success('已加载测试数据')
  isTesting.value = false
}

const analyzeConflict = async () => {
  if (!validateCharacters()) return
  
  isAnalyzing.value = true
  generatingStep.value = 1
  generatingMessage.value = '正在分析相位冲突...'
  
  try {
    const requestData = {
      person_a: {
        name: characterA.name,
        birth_date: characterA.birthDate,
        birth_time: characterA.birthTime,
        birth_place: characterA.birthPlace,
        latitude: characterA.latitude,
        longitude: characterA.longitude,
        house_system: 'placidus'
      },
      person_b: {
        name: characterB.name,
        birth_date: characterB.birthDate,
        birth_time: characterB.birthTime,
        birth_place: characterB.birthPlace,
        latitude: characterB.latitude,
        longitude: characterB.longitude,
        house_system: 'placidus'
      }
    }
    
    const result = await plazaApi.analyzeConflict(requestData)
    conflictAnalysis.value = result.conflict_analysis
    
    if (result.basic_info) {
      avatarA.sunSign = result.basic_info.person_a.sun_sign
      avatarB.sunSign = result.basic_info.person_b.sun_sign
    }
    
    ElMessage.success('相位冲突分析完成')
    showEncounterDialog.value = true
    
  } catch (error) {
    ElMessage.error('分析失败: ' + (error.message || '未知错误'))
  } finally {
    isAnalyzing.value = false
  }
}

const generateStory = async () => {
  if (!validateCharacters()) return
  
  isGenerating.value = true
  generatingStep.value = 1
  generatingMessage.value = '正在分析相位冲突...'
  
  try {
    const requestData = {
      person_a: {
        name: characterA.name,
        birth_date: characterA.birthDate,
        birth_time: characterA.birthTime,
        birth_place: characterA.birthPlace,
        latitude: characterA.latitude,
        longitude: characterA.longitude,
        house_system: 'placidus'
      },
      person_b: {
        name: characterB.name,
        birth_date: characterB.birthDate,
        birth_time: characterB.birthTime,
        birth_place: characterB.birthPlace,
        latitude: characterB.latitude,
        longitude: characterB.longitude,
        house_system: 'placidus'
      },
      style: selectedStyle.value,
      location: '神秘广场',
      generate_story: true
    }
    
    generatingStep.value = 2
    generatingMessage.value = '正在调用AI生成剧情...'
    
    const result = await plazaApi.encounter(requestData)
    
    generatingStep.value = 3
    generatingMessage.value = '正在生成对话...'
    
    conflictAnalysis.value = result.conflict_analysis
    storyData.value = result.story
    
    if (result.basic_info) {
      avatarA.sunSign = result.basic_info.person_a.sun_sign
      avatarB.sunSign = result.basic_info.person_b.sun_sign
    }
    
    ElMessage.success('剧情生成完成')
    showEncounterDialog.value = true
    
  } catch (error) {
    ElMessage.error('生成失败: ' + (error.message || '未知错误'))
  } finally {
    isGenerating.value = false
  }
}

const regenerateStory = async () => {
  storyData.value = null
  await generateStory()
}

const validateCharacters = () => {
  if (!characterA.birthDate || !characterA.birthTime) {
    ElMessage.warning('请填写角色A的出生日期和时间')
    return false
  }
  if (!characterB.birthDate || !characterB.birthTime) {
    ElMessage.warning('请填写角色B的出生日期和时间')
    return false
  }
  return true
}

const getActiveBosses = async () => {
  isGettingBosses.value = true
  try {
    const result = await bossBattleApi.getActiveBosses()
    activeBosses.value = result.bosses || []
    console.log(`获取到 ${activeBosses.value.length} 个活跃BOSS`)
  } catch (error) {
    console.error('获取BOSS列表失败:', error)
    ElMessage.error('获取BOSS列表失败: ' + (error.message || '未知错误'))
  } finally {
    isGettingBosses.value = false
  }
}

const openBossSelection = async () => {
  if (!encounterResult.value && !conflictAnalysis.value) {
    ElMessage.warning('请先完成偶遇分析')
    return
  }
  
  await getActiveBosses()
  
  if (activeBosses.value.length === 0) {
    ElMessage.warning('当前没有活跃的星象BOSS')
    return
  }
  
  showBossSelectDialog.value = true
}

const selectBoss = (boss) => {
  selectedBoss.value = boss
  showBossSelectDialog.value = false
  inviteToTeam(boss)
}

const buildMemberData = (characterPanel, characterInfo, sunSign = '', isInviter = false) => {
  if (!characterPanel) {
    const elementFromSign = getElementFromSunSign(sunSign)
    
    console.log(`⚠️ [buildMemberData] characterPanel为空，使用传入的 sunSign:`, {
      sunSign,
      elementFromSign,
      finalElement: elementFromSign || '火'
    })
    
    return {
      member_id: `member_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: characterInfo?.name || '未知角色',
      element: elementFromSign || '火',
      combat_power: 100,
      stats: {},
      passives: [],
      avatar_data: {
        sun_sign: sunSign
      }
    }
  }
  
  const panelSunSign = characterPanel.zodiac?.sun || ''
  const elementFromSign = getElementFromSunSign(panelSunSign)
  const element = characterPanel.element || elementFromSign || '火'
  
  console.log(`✅ [buildMemberData] 角色: ${characterPanel.name || '未知'}`, {
    panelSunSign,
    elementFromSign,
    characterPanelElement: characterPanel.element,
    finalElement: element
  })
  
  return {
    member_id: `member_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    name: characterPanel.name || characterInfo?.name || '未知角色',
    element: element,
    combat_power: characterPanel.stats?.combat_power || 100,
    stats: characterPanel.stats || {},
    passives: characterPanel.passives || [],
    avatar_data: {
      sun_sign: panelSunSign,
      moon_sign: characterPanel.zodiac?.moon || '',
      ascendant: characterPanel.zodiac?.ascendant || ''
    }
  }
}

const inviteToTeam = async (boss) => {
  isInvitingToTeam.value = true
  
  try {
    let panelA = characterPanels.value.person_a
    let panelB = characterPanels.value.person_b
    
    if (!panelA && encounterResult.value?.character_panels) {
      panelA = encounterResult.value.character_panels.person_a
      panelB = encounterResult.value.character_panels.person_b
    }
    
    console.log('================================')
    console.log('🚀 开始组队流程')
    console.log('================================')
    console.log('📋 characterPanels.person_a:', characterPanels.value.person_a)
    console.log('📋 characterPanels.person_b:', characterPanels.value.person_b)
    console.log('📋 encounterResult.character_panels:', encounterResult.value?.character_panels)
    console.log('📋 最终使用的 panelA:', panelA)
    console.log('📋 最终使用的 panelB:', panelB)
    console.log('================================')
    console.log('☀️ avatarA.sunSign:', avatarA.sunSign)
    console.log('☀️ avatarB.sunSign:', avatarB.sunSign)
    console.log('================================')
    
    const inviterData = buildMemberData(panelA, characterA, avatarA.sunSign, true)
    const inviteeData = buildMemberData(panelB, characterB, avatarB.sunSign, false)
    
    console.log('================================')
    console.log('📦 邀请者数据 (inviter_data):')
    console.log('  - name:', inviterData.name)
    console.log('  - element:', inviterData.element)
    console.log('  - avatar_data.sun_sign:', inviterData.avatar_data?.sun_sign)
    console.log('================================')
    console.log('📦 被邀请者数据 (invitee_data):')
    console.log('  - name:', inviteeData.name)
    console.log('  - element:', inviteeData.element)
    console.log('  - avatar_data.sun_sign:', inviteeData.avatar_data?.sun_sign)
    console.log('================================')
    console.log('⚠️ 元素检查:', {
      inviter_element: inviterData.element,
      invitee_element: inviteeData.element,
      are_same: inviterData.element === inviteeData.element
    })
    console.log('================================')
    
    const requestData = {
      encounter_session_id: encounterResult.value?.session_id || `enc_${Date.now()}`,
      boss_id: boss.boss_id,
      team_name: `${characterA.name}与${characterB.name}的队伍`,
      inviter_data: inviterData,
      invitee_data: inviteeData
    }
    
    const result = await bossBattleApi.inviteFromEncounter(requestData)
    
    currentTeam.value = result.team
    ElMessage.success('邀请组队成功！')
    
    showEncounterDialog.value = false
    showTeamResultDialog.value = true
    
  } catch (error) {
    console.error('邀请组队失败:', error)
    ElMessage.error('邀请组队失败: ' + (error.message || '未知错误'))
  } finally {
    isInvitingToTeam.value = false
  }
}

const goToBattleHall = () => {
  showTeamResultDialog.value = false
  ElMessage.info('正在跳转到副本大厅...')
}

const startBattleFromTeam = async () => {
  if (!currentTeam.value) {
    ElMessage.warning('没有可用的队伍')
    return
  }
  
  if (!currentTeam.value.has_all_elements) {
    const missing = currentTeam.value.missing_elements || []
    ElMessage.warning(`队伍元素不完整，缺少: ${missing.join(', ')}。需要包含火、土、风、水四种元素才能开战。`)
    return
  }
  
  if (isStartingBattle.value) {
    return
  }
  
  isStartingBattle.value = true
  
  try {
    const result = await bossBattleApi.startBattle({
      team_id: currentTeam.value.team_id
    })
    
    if (result.battle_id) {
      currentBattleId.value = result.battle_id
      ElMessage.info('战斗已开始，正在生成史诗剧情...')
      
      await pollBattleResult(result.battle_id)
    }
    
  } catch (error) {
    console.error('开始战斗失败:', error)
    ElMessage.error('开始战斗失败: ' + (error.message || '未知错误'))
  } finally {
    isStartingBattle.value = false
  }
}

const pollBattleResult = async (battleId) => {
  if (battlePollingId.value) {
    clearTimeout(battlePollingId.value)
  }
  
  const poll = async () => {
    try {
      const result = await bossBattleApi.getBattleResult(battleId)
      
      if (result.status === 'processing') {
        battlePollingId.value = setTimeout(poll, 2000)
        return
      }
      
      lastBattleResult.value = result
      showTeamResultDialog.value = false
      
      const victory = result.battle_result?.victory
      
      ElMessage({
        message: victory ? '战斗胜利！' : '战斗失败...',
        type: victory ? 'success' : 'warning',
        duration: 3000
      })
      
      if (victory && result.team?.rewards_earned) {
        ElMessage.success(`获得星尘积分: ${result.team.rewards_earned.per_member_stardust || 0}`)
      }
      
    } catch (error) {
      console.error('获取战斗结果失败:', error)
      ElMessage.error('获取战斗结果失败: ' + (error.message || '未知错误'))
    }
  }
  
  battlePollingId.value = setTimeout(poll, 2000)
}

onMounted(async () => {
  checkCollision()
  
  try {
    await Promise.all([
      loadWeatherPanel(),
      loadMissions()
    ])
  } catch (error) {
    console.error('初始化数据加载失败:', error)
  }
})
</script>

<style lang="scss" scoped>
.parallel-plaza {
  width: 100%;
  min-height: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.plaza-header {
  text-align: center;
  margin-bottom: 20px;
  
  .plaza-title {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-size: 32px;
    font-weight: 700;
    color: #e0e0ff;
    margin: 0 0 10px 0;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .plaza-subtitle {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }
}

.plaza-controls {
  margin-bottom: 20px;
  
  .control-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(139, 92, 246, 0.2);
    backdrop-filter: blur(10px);
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .style-select {
        width: 150px;
      }
    }
    
    .character-configs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
      
      .character-config {
        padding: 15px;
        background: rgba(139, 92, 246, 0.1);
        border-radius: 12px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        
        h4 {
          margin: 0 0 15px 0;
          color: #c4b5fd;
          font-size: 16px;
        }
      }
    }
    
    .action-buttons {
      display: flex;
      gap: 12px;
      justify-content: center;
    }
  }
}

.plaza-arena {
  .arena-header {
    text-align: center;
    margin-bottom: 15px;
    
    h3 {
      margin: 0 0 5px 0;
      color: #e0e0ff;
      font-size: 20px;
    }
    
    .arena-hint {
      margin: 0;
      color: rgba(255, 255, 255, 0.6);
      font-size: 14px;
    }
  }
  
  .arena-container {
    position: relative;
    width: 100%;
    height: 400px;
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.1) 0%, rgba(96, 165, 250, 0.1) 100%);
    border: 2px solid rgba(139, 92, 246, 0.3);
    border-radius: 20px;
    overflow: hidden;
    cursor: grab;
    
    &:active {
      cursor: grabbing;
    }
    
    .arena-background {
      position: absolute;
      inset: 0;
      
      .ground-pattern {
        position: absolute;
        inset: 0;
        background-image: 
          radial-gradient(circle at 25% 25%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
          radial-gradient(circle at 75% 75%, rgba(96, 165, 250, 0.1) 0%, transparent 50%);
      }
      
      .plaza-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: rgba(139, 92, 246, 0.2);
      }
    }
    
    .avatar {
      position: absolute;
      width: 120px;
      height: 120px;
      cursor: grab;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      z-index: 10;
      
      &:hover {
        transform: scale(1.05);
      }
      
      &.avatar-dragging {
        cursor: grabbing;
        transform: scale(1.1);
        z-index: 100;
        
        .avatar-glow {
          animation: pulse-glow 0.5s ease-in-out infinite alternate;
        }
      }
      
      &.avatar-colliding {
        .avatar-glow {
          animation: collision-glow 0.3s ease-in-out infinite alternate;
        }
      }
      
      .avatar-inner {
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        
        .avatar-image {
          position: relative;
          
          :deep(.el-avatar) {
            border: 3px solid rgba(139, 92, 246, 0.5);
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
          }
        }
        
        .avatar-label {
          position: absolute;
          bottom: -25px;
          text-align: center;
          width: 100%;
          
          .avatar-name {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #e0e0ff;
            white-space: nowrap;
          }
          
          .avatar-sign {
            display: block;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 2px;
          }
        }
      }
      
      .avatar-glow {
        position: absolute;
        inset: -10px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
        pointer-events: none;
      }
    }
    
    .collision-effect {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      pointer-events: none;
      z-index: 50;
      
      .sparkles {
        color: #fbbf24;
        animation: sparkle 0.5s ease-in-out infinite alternate;
      }
      
      .collision-text {
        font-size: 18px;
        font-weight: 700;
        color: #fbbf24;
        margin-top: 10px;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
      }
    }
  }
}

.conflict-analysis-section {
  h4 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 15px 0;
    font-size: 18px;
    color: #333;
  }
  
  .conflict-intensity {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 15px;
    
    .intensity-detail {
      font-size: 14px;
      color: #666;
    }
  }
  
  .conflict-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .conflict-item {
      padding: 15px;
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(251, 191, 36, 0.05) 100%);
      border: 1px solid rgba(239, 68, 68, 0.2);
      border-radius: 12px;
      
      &.conflict-harmonious {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%);
        border-color: rgba(34, 197, 94, 0.2);
      }
      
      .conflict-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
        
        .conflict-pair {
          font-weight: 600;
          font-size: 16px;
          color: #333;
        }
        
        .conflict-severity {
          margin-left: auto;
          font-size: 13px;
          color: #666;
        }
      }
      
      .conflict-theme,
      .conflict-atmosphere {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        color: #555;
        margin-bottom: 8px;
      }
      
      .conflict-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
      }
    }
  }
  
  .no-conflict {
    padding: 30px;
  }
}

.story-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  
  h4 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 15px 0;
    font-size: 18px;
    color: #333;
  }
  
  .scene-description {
    display: flex;
    gap: 8px;
    padding: 15px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(96, 165, 250, 0.05) 100%);
    border-radius: 12px;
    margin-bottom: 20px;
    
    p {
      margin: 0;
      color: #555;
      line-height: 1.6;
    }
  }
  
  .dialogue-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-bottom: 20px;
    
    .dialogue-item {
      display: flex;
      flex-direction: column;
      max-width: 80%;
      
      &.dialogue-left {
        align-self: flex-start;
      }
      
      &.dialogue-right {
        align-self: flex-end;
      }
      
      .dialogue-speaker {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        
        .speaker-name {
          font-weight: 600;
          color: #333;
        }
        
        .speaker-emotion {
          font-size: 13px;
          color: #999;
          font-style: italic;
        }
      }
      
      .dialogue-bubble {
        padding: 12px 18px;
        background: #f5f5f5;
        border-radius: 16px;
        
        p {
          margin: 0;
          color: #333;
          line-height: 1.6;
        }
        
        .inner-thought {
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid rgba(0, 0, 0, 0.1);
          font-size: 13px;
          color: #888;
          font-style: italic;
          display: flex;
          align-items: center;
          gap: 4px;
        }
      }
      
      &.dialogue-right .dialogue-bubble {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(96, 165, 250, 0.1) 100%);
      }
    }
  }
  
  .atmosphere-summary,
  .conflict-hint {
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    
    h5 {
      margin: 0 0 8px 0;
      font-size: 14px;
      color: #666;
    }
    
    p {
      margin: 0;
      color: #555;
      line-height: 1.6;
    }
  }
  
  .atmosphere-summary {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
  }
  
  .conflict-hint {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.05) 0%, rgba(245, 158, 11, 0.05) 100%);
  }
}

.generating-section {
  text-align: center;
  padding: 40px;
}

.generating-status {
  .generating-text {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 30px;
    font-size: 16px;
    color: #666;
    
    .loading-icon {
      animation: spin 1s linear infinite;
    }
  }
}

@keyframes pulse-glow {
  from {
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
  }
  to {
    box-shadow: 0 0 40px rgba(139, 92, 246, 0.6);
  }
}

@keyframes collision-glow {
  from {
    box-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
  }
  to {
    box-shadow: 0 0 50px rgba(251, 191, 36, 0.6);
  }
}

@keyframes sparkle {
  from {
    transform: scale(1);
    opacity: 0.7;
  }
  to {
    transform: scale(1.2);
    opacity: 1;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

:deep(.el-dialog) {
  .el-dialog__header {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(96, 165, 250, 0.1) 100%);
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  }
}

.story-preview {
  max-height: 500px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 15px;
  
  pre {
    margin: 0;
    color: #d4d4d4;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
  }
}

.loading-bosses,
.no-bosses {
  padding: 40px;
  text-align: center;
}

.boss-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 10px;
  
  .boss-card {
    padding: 20px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%);
    border: 2px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: rgba(139, 92, 246, 0.5);
      box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15);
      transform: translateY(-2px);
    }
    
    .boss-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .boss-name {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
    
    .boss-title {
      margin: 0 0 12px 0;
      font-size: 14px;
      color: #6b7280;
      font-style: italic;
    }
    
    .boss-description {
      margin: 0 0 16px 0;
      font-size: 13px;
      color: #4b5563;
      line-height: 1.6;
    }
    
    .boss-stats {
      margin-bottom: 16px;
      
      .stat-item {
        margin-bottom: 12px;
        
        .stat-label {
          display: block;
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
        }
        
        .stat-value {
          display: block;
          font-size: 12px;
          color: #4b5563;
          margin-top: 4px;
          text-align: right;
        }
      }
      
      .element-info {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        
        .weakness,
        .resistance {
          display: flex;
          align-items: center;
          gap: 6px;
          
          .label {
            font-size: 12px;
            color: #6b7280;
          }
          
          .element-value {
            font-size: 13px;
            font-weight: 600;
          }
          
          .weakness-element {
            color: #22c55e;
          }
          
          .resistance-element {
            color: #ef4444;
          }
        }
      }
    }
    
    .boss-trigger {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(139, 92, 246, 0.1);
      
      .planet-info {
        font-size: 12px;
        color: #6b7280;
      }
    }
  }
}

.team-result {
  .team-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 2px solid rgba(139, 92, 246, 0.2);
    
    h3 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      background: linear-gradient(135deg, #8b5cf6 0%, #60a5fa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
  
  .team-members {
    margin-bottom: 20px;
    
    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      color: #374151;
    }
    
    .member-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
      
      .member-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(96, 165, 250, 0.05) 100%);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        transition: all 0.3s ease;
        
        &.leader {
          background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
          border-color: rgba(251, 191, 36, 0.3);
        }
        
        .member-info {
          flex: 1;
          
          .member-name {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
            font-size: 15px;
            font-weight: 600;
            color: #1f2937;
          }
          
          .member-element {
            display: flex;
            align-items: center;
            gap: 4px;
            margin-bottom: 4px;
            font-size: 13px;
            color: #6b7280;
            
            .element-symbol {
              font-size: 16px;
            }
          }
          
          .member-power {
            font-size: 12px;
            color: #8b5cf6;
            font-weight: 600;
          }
        }
      }
    }
  }
  
  .team-status {
    margin-bottom: 20px;
    padding: 20px;
    background: rgba(139, 92, 246, 0.05);
    border-radius: 12px;
    
    .status-item {
      display: flex;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 16px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .status-label {
        font-size: 14px;
        color: #6b7280;
        min-width: 80px;
      }
      
      .status-value {
        font-size: 14px;
        color: #374151;
        
        &.highlight {
          font-size: 24px;
          font-weight: 700;
          color: #8b5cf6;
        }
      }
      
      .element-checks {
        display: flex;
        gap: 16px;
        
        .element-check {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 8px 12px;
          border-radius: 8px;
          background: rgba(0, 0, 0, 0.05);
          transition: all 0.3s ease;
          
          &.present {
            background: rgba(34, 197, 94, 0.1);
          }
          
          .symbol {
            font-size: 20px;
          }
          
          .name {
            font-size: 12px;
            color: #6b7280;
          }
          
          .check {
            font-size: 14px;
            font-weight: 700;
            
            .present & {
              color: #22c55e;
            }
            
            &:not(.present) & {
              color: #ef4444;
            }
          }
        }
      }
    }
  }
  
  .missing-elements-warning {
    margin-top: 16px;
  }
}

.parallel-plaza {
  &.plaza-warning {
    .plaza-header {
      background: linear-gradient(135deg, rgba(234, 179, 8, 0.1) 0%, rgba(249, 115, 22, 0.1) 100%);
    }
  }
  
  &.plaza-critical {
    .plaza-header {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
    }
  }
}

.energy-weather-panel {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(96, 165, 250, 0.1) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #8b5cf6, #60a5fa, #34d399);
  }
  
  &.warning-active {
    background: linear-gradient(135deg, rgba(234, 179, 8, 0.1) 0%, rgba(249, 115, 22, 0.1) 100%);
    border-color: rgba(234, 179, 8, 0.4);
    
    &::before {
      background: linear-gradient(90deg, #eab308, #f97316, #ef4444);
    }
  }
  
  &.critical-active {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%);
    border-color: rgba(239, 68, 68, 0.5);
    animation: criticalPulse 2s ease-in-out infinite;
    
    &::before {
      background: linear-gradient(90deg, #ef4444, #dc2626, #ef4444);
    }
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    
    .panel-title-section {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .title-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #8b5cf6 0%, #60a5fa 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
      }
      
      .title-text {
        .panel-title {
          margin: 0;
          font-size: 20px;
          font-weight: 700;
          background: linear-gradient(135deg, #e0e0ff 0%, #c4b5fd 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .panel-subtitle {
          margin: 4px 0 0 0;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
        }
      }
    }
    
    .panel-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .warning-tag {
        animation: tagPulse 1.5s ease-in-out infinite;
      }
      
      .mission-badge {
        margin-left: 8px;
      }
    }
  }
  
  .panel-content {
    .energy-score-section {
      display: flex;
      align-items: center;
      gap: 30px;
      margin-bottom: 24px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      
      .score-circle {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        border: 4px solid #22c55e;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        
        .score-value {
          font-size: 32px;
          font-weight: 700;
          color: #e0e0ff;
        }
        
        .score-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
        }
      }
      
      .energy-info {
        flex: 1;
        
        .mood-info {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
          
          .mood-text {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.7);
          }
        }
        
        .weather-info {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .weather-icon {
            font-size: 28px;
          }
          
          .weather-label {
            font-size: 14px;
            font-weight: 600;
            color: #e0e0ff;
          }
        }
      }
    }
    
    .dimension-section {
      margin-bottom: 24px;
      
      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 600;
        color: #e0e0ff;
        margin-bottom: 12px;
      }
      
      .dimension-list {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        
        .dimension-item {
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          padding: 12px;
          
          .dimension-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            
            .dimension-icon {
              font-size: 18px;
            }
            
            .dimension-name {
              flex: 1;
              font-size: 13px;
              font-weight: 600;
              color: #e0e0ff;
            }
            
            .dimension-score {
              font-size: 14px;
              font-weight: 700;
              color: #22c55e;
            }
          }
          
          .dimension-level {
            display: block;
            font-size: 11px;
            margin-top: 4px;
            text-align: right;
          }
        }
      }
    }
    
    .ominous-section {
      margin-bottom: 24px;
      
      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 600;
        color: #e0e0ff;
        margin-bottom: 12px;
        
        &.warning-title {
          color: #ef4444;
          animation: titlePulse 1.5s ease-in-out infinite;
        }
      }
      
      .ominous-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
        
        .ominous-item {
          background: rgba(234, 179, 8, 0.1);
          border: 1px solid rgba(234, 179, 8, 0.3);
          border-radius: 10px;
          padding: 14px;
          
          &.critical-event {
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.4);
            animation: itemPulse 2s ease-in-out infinite;
          }
          
          .event-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
            
            .event-icon {
              font-size: 24px;
            }
            
            .event-name {
              flex: 1;
              font-size: 14px;
              font-weight: 600;
              color: #e0e0ff;
            }
          }
          
          .event-desc {
            margin: 0 0 10px 0;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.5;
          }
          
          .event-affected {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            flex-wrap: wrap;
            
            .affected-label {
              font-size: 12px;
              color: rgba(255, 255, 255, 0.6);
            }
          }
          
          .event-recommendations {
            .rec-label {
              display: block;
              font-size: 12px;
              color: rgba(255, 255, 255, 0.6);
              margin-bottom: 4px;
            }
            
            .rec-list {
              margin: 0;
              padding-left: 16px;
              
              li {
                font-size: 12px;
                color: rgba(255, 255, 255, 0.7);
                margin-bottom: 4px;
                display: flex;
                align-items: center;
                gap: 4px;
              }
            }
          }
        }
      }
    }
    
    .quick-missions {
      .section-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        
        > span:first-child {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 15px;
          font-weight: 600;
          color: #e0e0ff;
        }
      }
      
      .quick-mission-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
        
        .quick-mission-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          border: 1px solid rgba(139, 92, 246, 0.2);
          cursor: pointer;
          transition: all 0.3s ease;
          
          &:hover {
            background: rgba(139, 92, 246, 0.1);
            border-color: rgba(139, 92, 246, 0.4);
          }
          
          &.mission-completed {
            opacity: 0.6;
            cursor: default;
          }
          
          &.bonus-mission {
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.05);
          }
          
          .mission-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: linear-gradient(135deg, #8b5cf6 0%, #60a5fa 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            flex-shrink: 0;
          }
          
          .mission-info {
            flex: 1;
            min-width: 0;
            
            .mission-title {
              display: block;
              font-size: 14px;
              font-weight: 600;
              color: #e0e0ff;
              margin-bottom: 4px;
              
              .el-tag {
                margin-left: 8px;
              }
            }
            
            .mission-desc {
              display: block;
              font-size: 12px;
              color: rgba(255, 255, 255, 0.6);
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
          }
          
          .mission-reward {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 6px 12px;
            background: rgba(34, 197, 94, 0.1);
            border-radius: 8px;
            
            .reward-icon {
              font-size: 16px;
            }
            
            .reward-amount {
              font-size: 16px;
              font-weight: 700;
              color: #22c55e;
            }
            
            .reward-label {
              font-size: 11px;
              color: rgba(255, 255, 255, 0.5);
            }
          }
        }
      }
    }
  }
}

.mission-panel-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
  }
  
  .mission-panel-content {
    padding: 20px;
    max-height: 60vh;
    overflow-y: auto;
  }
  
  .mission-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .mission-card {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      border-color: #8b5cf6;
    }
    
    &.mission-completed {
      opacity: 0.7;
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%);
    }
    
    &.bonus-mission {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(249, 115, 22, 0.05) 100%);
      border-color: rgba(239, 68, 68, 0.3);
    }
    
    &.mission-selected {
      border-color: #8b5cf6;
      box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
    }
    
    .mission-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
      
      .mission-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #8b5cf6 0%, #60a5fa 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        flex-shrink: 0;
      }
      
      .mission-title-section {
        flex: 1;
        
        .mission-title {
          margin: 0;
          font-size: 15px;
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 6px;
          
          .el-tag {
            margin-left: 8px;
          }
        }
        
        .mission-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .mission-duration,
          .mission-mood {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: #6b7280;
          }
        }
      }
      
      .mission-reward {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px 16px;
        background: rgba(34, 197, 94, 0.1);
        border-radius: 10px;
        
        .reward-icon {
          font-size: 20px;
        }
        
        .reward-amount {
          font-size: 18px;
          font-weight: 700;
          color: #22c55e;
        }
        
        .reward-label {
          font-size: 11px;
          color: #6b7280;
        }
      }
    }
    
    .mission-description {
      margin: 0 0 12px 0;
      font-size: 13px;
      color: #4b5563;
      line-height: 1.5;
    }
    
    .bonus-hint {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      background: rgba(239, 68, 68, 0.1);
      border-radius: 8px;
      margin-bottom: 12px;
      font-size: 12px;
      color: #dc2626;
    }
    
    .mission-actions {
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .mission-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .footer-info {
      font-size: 13px;
      color: #6b7280;
    }
  }
}

.reward-center-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
  }
  
  .reward-center-content {
    max-height: 60vh;
    overflow-y: auto;
  }
  
  .balance-section {
    display: flex;
    gap: 16px;
    padding: 20px;
    background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
    border-bottom: 1px solid #e5e7eb;
    
    .balance-card {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: white;
      border-radius: 12px;
      border: 1px solid #e5e7eb;
      
      &.fragment-balance {
        border-color: rgba(34, 197, 94, 0.3);
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%);
        
        .balance-icon {
          background: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
        }
        
        .balance-amount {
          color: #22c55e;
        }
      }
      
      &.point-balance {
        border-color: rgba(139, 92, 246, 0.3);
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(96, 165, 250, 0.05) 100%);
        
        .balance-icon {
          background: linear-gradient(135deg, #8b5cf6 0%, #60a5fa 100%);
        }
        
        .balance-amount {
          color: #8b5cf6;
        }
      }
      
      .balance-icon {
        width: 52px;
        height: 52px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        flex-shrink: 0;
      }
      
      .balance-info {
        flex: 1;
        
        .balance-label {
          display: block;
          font-size: 13px;
          color: #6b7280;
          margin-bottom: 4px;
        }
        
        .balance-amount {
          display: block;
          font-size: 28px;
          font-weight: 700;
          margin-bottom: 2px;
        }
        
        .balance-desc {
          display: block;
          font-size: 11px;
          color: #9ca3af;
        }
      }
    }
  }
  
  .reward-tabs {
    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0 20px;
      background: white;
    }
  }
  
  .completions-list,
  .transactions-list {
    padding: 16px 20px;
  }
  
  .completion-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: #f9fafb;
    border-radius: 10px;
    margin-bottom: 8px;
    
    .completion-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .completion-title {
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
      }
      
      .completion-time {
        font-size: 12px;
        color: #9ca3af;
      }
    }
    
    .completion-reward {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .reward-icon {
        font-size: 16px;
      }
      
      .reward-amount {
        font-size: 16px;
        font-weight: 600;
        color: #22c55e;
      }
    }
  }
  
  .transaction-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: #f9fafb;
    border-radius: 10px;
    margin-bottom: 8px;
    
    &.tx-positive {
      background: rgba(34, 197, 94, 0.05);
    }
    
    &.tx-negative {
      background: rgba(239, 68, 68, 0.05);
    }
    
    .transaction-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .transaction-description {
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
      }
      
      .transaction-time {
        font-size: 12px;
        color: #9ca3af;
      }
    }
    
    .transaction-amount {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 2px;
      
      .amount-number {
        font-size: 16px;
        font-weight: 600;
        
        &.positive {
          color: #22c55e;
        }
        
        &.negative {
          color: #ef4444;
        }
      }
      
      .balance-change {
        font-size: 11px;
        color: #9ca3af;
      }
    }
  }
}

@keyframes criticalPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.2);
  }
  50% {
    box-shadow: 0 0 20px 5px rgba(239, 68, 68, 0.15);
  }
}

@keyframes tagPulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes titlePulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes itemPulse {
  0%, 100% {
    border-color: rgba(239, 68, 68, 0.4);
  }
  50% {
    border-color: rgba(239, 68, 68, 0.7);
  }
}
</style>