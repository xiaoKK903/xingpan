<template>
  <div class="group-matrix-container">
    <div class="stars-bg">
      <div v-for="i in 40" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="group-matrix-main">
      <div class="page-header">
        <h1 class="main-title">多人星盘关系矩阵</h1>
        <p class="subtitle">分析团队成员之间的星盘互动，发现隐藏的关系模式</p>
      </div>

      <Transition name="fade">
        <div v-if="!showResult" class="input-section">
          <div class="form-section">
            <div class="section-header">
              <h3 class="section-title">群组信息</h3>
            </div>

            <div class="group-info-form">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">群组名称</label>
                  <input 
                    type="text" 
                    v-model="groupName" 
                    placeholder="例如：创业团队、室友、暧昧小团体"
                    class="form-input"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">群组类型</label>
                  <select v-model="groupType" class="form-input">
                    <option value="team">创业/工作团队</option>
                    <option value="roommates">室友</option>
                    <option value="friends">朋友/社交圈</option>
                    <option value="lovers">暧昧关系</option>
                    <option value="other">其他</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-header">
              <h3 class="section-title">成员信息</h3>
              <button class="add-member-btn" @click="addMember">
                <span class="btn-icon">+</span> 添加成员
              </button>
            </div>

            <div class="members-list">
              <div 
                v-for="(member, index) in members" 
                :key="index"
                class="member-card"
                :class="{ 'is-core': member.isCore }"
                :style="{ borderLeftColor: member.color }"
              >
                <div class="member-header">
                  <div class="member-title">
                    <span class="member-avatar" :style="{ background: member.color }">
                      {{ member.name ? member.name[0] : '?' }}
                    </span>
                    <span class="member-name">{{ member.name || `成员 ${index + 1}` }}</span>
                    <el-tag 
                      v-if="member.isCore" 
                      size="small" 
                      type="warning"
                      effect="dark"
                    >
                      核心成员
                    </el-tag>
                  </div>
                  <div class="member-actions">
                    <button 
                      class="action-btn" 
                      @click="toggleCore(index)"
                      :title="member.isCore ? '取消核心成员' : '设为核心成员'"
                    >
                      ⭐
                    </button>
                    <button 
                      class="action-btn delete" 
                      v-if="members.length > 2"
                      @click="removeMember(index)"
                    >
                      ×
                    </button>
                  </div>
                </div>

                <div class="member-form">
                  <div class="form-row">
                    <div class="form-group">
                      <label class="form-label">姓名</label>
                      <input 
                        type="text" 
                        v-model="member.name" 
                        placeholder="请输入姓名"
                        class="form-input"
                      />
                    </div>
                  </div>

                  <div class="form-row">
                    <div class="form-group">
                      <label class="form-label">出生日期</label>
                      <el-date-picker
                        v-model="member.birthDate"
                        type="date"
                        placeholder="选择日期"
                        format="YYYY年MM月DD日"
                        value-format="YYYY-MM-DD"
                        class="form-input"
                      />
                    </div>
                    <div class="form-group">
                      <label class="form-label">出生时间</label>
                      <el-time-picker
                        v-model="member.birthTime"
                        placeholder="选择时间"
                        format="HH:mm"
                        value-format="HH:mm"
                        class="form-input"
                      />
                    </div>
                  </div>

                  <div class="form-row">
                    <div class="form-group full-width">
                      <label class="form-label">出生城市</label>
                      <el-autocomplete
                        v-model="member.cityInput"
                        :fetch-suggestions="queryCitySuggestions"
                        :trigger-on-focus="true"
                        :clearable="true"
                        @select="(item) => onCitySelect(item, index)"
                        placeholder="输入城市名称"
                        class="form-input"
                      >
                        <template #default="{ item }">
                          <div class="option-content">
                            <span class="option-name">{{ item.name }}</span>
                            <span class="option-location">{{ item.country }}</span>
                          </div>
                        </template>
                      </el-autocomplete>
                    </div>
                  </div>

                  <div class="quick-cities">
                    <button 
                      v-for="city in QUICK_CITIES" 
                      :key="city.id"
                      type="button" 
                      class="city-btn"
                      @click="selectQuickCity(city, index)"
                    >
                      {{ city.name }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="submit-section">
            <button 
              type="button" 
              class="submit-btn"
              :class="{ 'btn-loading': calculating }"
              :disabled="calculating || !isFormValid"
              @click="calculateMatrix"
            >
              <span v-if="!calculating">开始分析关系矩阵</span>
              <span v-else>计算中...</span>
            </button>
            <p class="hint-text" v-if="!isFormValid">请填写所有成员的完整信息（姓名、日期、时间、城市）</p>
          </div>
        </div>

        <div v-else class="result-section">
          <div class="result-header">
            <h2 class="result-title">{{ matrixResult.group_name || '群组关系分析' }}</h2>
            <div class="result-actions">
              <button class="back-btn" @click="resetForm">
                <span class="btn-icon">←</span> 重新输入
              </button>
            </div>
          </div>

          <div class="tabs-section">
            <div class="tabs-header">
              <button 
                v-for="tab in tabs" 
                :key="tab.id"
                class="tab-btn"
                :class="{ active: activeTab === tab.id }"
                @click="activeTab = tab.id"
              >
                {{ tab.icon }} {{ tab.name }}
              </button>
            </div>

            <div class="tab-content">
              <div v-if="activeTab === 'roles'" class="roles-tab">
                <div class="roles-grid">
                  <div 
                    v-for="role in matrixResult.roles" 
                    :key="role.name"
                    class="role-card"
                    :class="{ 'core-highlight': role.is_core }"
                  >
                    <div class="role-header" :style="{ background: role.role_color + '20' }">
                      <span class="role-icon">{{ role.role_icon }}</span>
                      <div class="role-info">
                        <span class="role-name">{{ role.role_name }}</span>
                        <span class="person-name">{{ role.name }}</span>
                      </div>
                      <el-tag 
                        v-if="role.is_core" 
                        size="small" 
                        type="warning"
                        effect="dark"
                      >
                        核心
                      </el-tag>
                    </div>
                    <div class="role-body">
                      <p class="role-description">{{ role.role_description }}</p>
                      <div class="scores-bar">
                        <div class="score-item">
                          <span class="score-label">粘合剂</span>
                          <div class="score-track">
                            <div 
                              class="score-fill glue" 
                              :style="{ width: getScorePercent(role.scores.glue) + '%' }"
                            ></div>
                          </div>
                        </div>
                        <div class="score-item">
                          <span class="score-label">火药桶</span>
                          <div class="score-track">
                            <div 
                              class="score-fill firecracker" 
                              :style="{ width: getScorePercent(role.scores.firecracker) + '%' }"
                            ></div>
                          </div>
                        </div>
                        <div class="score-item">
                          <span class="score-label">愿景导师</span>
                          <div class="score-track">
                            <div 
                              class="score-fill visionary" 
                              :style="{ width: getScorePercent(role.scores.visionary) + '%' }"
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="activeTab === 'topology'" class="topology-tab">
                <div class="team-energy-header">
                  <div class="energy-badge" :style="{ background: matrixResult.topology?.team_energy?.energy_color + '20', borderColor: matrixResult.topology?.team_energy?.energy_color }">
                    <span class="energy-icon">
                      <span v-if="matrixResult.topology?.team_energy?.energy_type === 'harmonious'">😊</span>
                      <span v-else-if="matrixResult.topology?.team_energy?.energy_type === 'turbulent'">😰</span>
                      <span v-else>🤝</span>
                    </span>
                    <span class="energy-name">{{ matrixResult.topology?.team_energy?.energy_label }}</span>
                  </div>
                  <div class="energy-stats">
                    <div class="energy-stat">
                      <span class="stat-label">和谐比例</span>
                      <span class="stat-value" style="color: #22c55e">{{ Math.round((matrixResult.topology?.team_energy?.harmony_ratio || 0) * 100) }}%</span>
                    </div>
                    <div class="energy-stat">
                      <span class="stat-label">紧张比例</span>
                      <span class="stat-value" style="color: #ef4444">{{ Math.round((matrixResult.topology?.team_energy?.conflict_ratio || 0) * 100) }}%</span>
                    </div>
                    <div class="energy-stat">
                      <span class="stat-label">核心成员</span>
                      <span class="stat-value">{{ matrixResult.topology?.team_energy?.core_count || 0 }}人</span>
                    </div>
                  </div>
                </div>

                <div class="topology-container">
                  <div class="topology-svg-wrapper">
                    <svg class="topology-svg" viewBox="-250 -250 500 500">
                      <defs>
                        <filter id="glow-green" x="-50%" y="-50%" width="200%" height="200%">
                          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                          <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                          </feMerge>
                        </filter>
                        <filter id="glow-red" x="-50%" y="-50%" width="200%" height="200%">
                          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                          <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                          </feMerge>
                        </filter>
                        <filter id="glow-purple" x="-50%" y="-50%" width="200%" height="200%">
                          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                          <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                          </feMerge>
                        </filter>
                        <marker id="arrow-harmony" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                          <polygon points="0 0, 10 3, 0 6" fill="#22c55e" />
                        </marker>
                        <marker id="arrow-conflict" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                          <polygon points="0 0, 10 3, 0 6" fill="#ef4444" />
                        </marker>
                      </defs>

                      <g class="links-group">
                        <line
                          v-for="(link, idx) in topologyLinksWithNodes"
                          :key="'link-' + idx"
                          :x1="link.source_node?.topo_position?.x || 0"
                          :y1="link.source_node?.topo_position?.y || 0"
                          :x2="link.target_node?.topo_position?.x || 0"
                          :y2="link.target_node?.topo_position?.y || 0"
                          :class="['link-line', link.relation_type, { 
                            'highlighted': isLinkHighlighted(link),
                            'dimmed': isLinkDimmed(link)
                          }]"
                          :style="getLinkStyle(link)"
                          :stroke="getLinkColor(link)"
                          :stroke-width="getLinkWidth(link)"
                          :stroke-dasharray="link.relation_type === 'conflict' ? '5,5' : 'none'"
                          :filter="getLinkFilter(link)"
                          @mouseenter="hoveredMemberIndex = null; hoverLink(link)"
                          @mouseleave="hoveredMemberIndex = null; clearLinkHover()"
                          @click="clickTopologyLink(link)"
                          style="cursor: pointer;"
                        />
                      </g>

                      <g class="nodes-group">
                        <g
                          v-for="(node, idx) in matrixResult.topology?.nodes || []"
                          :key="'node-' + idx"
                          :transform="`translate(${node.topo_position?.x || 0}, ${node.topo_position?.y || 0})`"
                          class="node-group"
                          :class="{ 
                            'highlighted': highlightedMemberIndex === idx || hoveredMemberIndex === idx || sharedState.focusedMemberIndex === idx,
                            'dimmed': isNodeDimmed(idx)
                          }"
                          @mouseenter="hoveredMemberIndex = idx; highlightMember(idx)"
                          @mouseleave="hoveredMemberIndex = null; clearHighlight()"
                          @click="clickTopologyNode(idx)"
                        >
                          <circle
                            :r="node.is_core ? 28 : 22"
                            :fill="node.role_color || '#64748b'"
                            :stroke="node.is_core ? '#f59e0b' : 'transparent'"
                            :stroke-width="node.is_core ? 3 : 0"
                            class="node-circle"
                            :style="{ filter: `drop-shadow(0 0 ${node.is_core ? 12 : 8}px ${node.role_color || '#64748b'}80)` }"
                          />
                          <circle
                            v-if="node.is_core"
                            r="35"
                            fill="none"
                            stroke="#f59e0b"
                            stroke-width="2"
                            stroke-dasharray="5,3"
                            class="core-orb"
                            style="animation: spin 10s linear infinite;"
                          />
                          <text
                            class="node-avatar"
                            text-anchor="middle"
                            dominant-baseline="central"
                            :y="node.is_core ? 1 : 0"
                            fill="white"
                            font-size="node.is_core ? 18 : 16"
                            font-weight="bold"
                          >
                            {{ node.name ? node.name[0] : '?' }}
                          </text>
                          <text
                            class="node-label"
                            text-anchor="middle"
                            y="48"
                            fill="rgba(255,255,255,0.9)"
                            font-size="12"
                            font-weight="500"
                          >
                            {{ node.name }}
                          </text>
                          <text
                            class="node-role-label"
                            text-anchor="middle"
                            y="64"
                            :fill="node.role_color || '#64748b'"
                            font-size="10"
                          >
                            {{ node.role_icon }} {{ node.role_name }}
                          </text>
                          <text
                            v-if="node.is_core"
                            class="node-core-badge"
                            text-anchor="middle"
                            y="-38"
                            fill="#f59e0b"
                            font-size="10"
                            font-weight="bold"
                          >
                            ⭐ 核心
                          </text>
                        </g>
                      </g>
                    </svg>
                  </div>

                  <div class="topology-legend">
                    <div class="legend-section">
                      <h4 class="legend-title">关系类型</h4>
                      <div class="legend-items">
                        <div class="legend-item">
                          <div class="legend-line harmony"></div>
                          <span class="legend-label">和谐关系</span>
                        </div>
                        <div class="legend-item">
                          <div class="legend-line conflict"></div>
                          <span class="legend-label">紧张关系</span>
                        </div>
                        <div class="legend-item">
                          <div class="legend-line neutral"></div>
                          <span class="legend-label">平淡关系</span>
                        </div>
                      </div>
                    </div>
                    <div class="legend-section">
                      <h4 class="legend-title">角色说明</h4>
                      <div class="legend-items">
                        <div class="legend-item">
                          <div class="legend-dot" style="background: #22c55e"></div>
                          <span class="legend-label">🤝 粘合剂</span>
                        </div>
                        <div class="legend-item">
                          <div class="legend-dot" style="background: #ef4444"></div>
                          <span class="legend-label">💥 火药桶</span>
                        </div>
                        <div class="legend-item">
                          <div class="legend-dot" style="background: #8b5cf6"></div>
                          <span class="legend-label">✨ 愿景导师</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="topology-details" v-if="hoveredLink">
                  <div class="detail-card">
                    <h4 class="detail-title">
                      {{ hoveredLink.source_name }} ↔ {{ hoveredLink.target_name }}
                    </h4>
                    <div class="detail-relation-type" :class="hoveredLink.relation_type">
                      <span v-if="hoveredLink.relation_type === 'harmony'">💚 和谐关系</span>
                      <span v-else-if="hoveredLink.relation_type === 'conflict'">💔 紧张关系</span>
                      <span v-else>⚪ 平淡关系</span>
                    </div>
                    <div class="detail-stats">
                      <div class="detail-stat">
                        <span class="detail-label">总相位</span>
                        <span class="detail-value">{{ hoveredLink.summary?.total || 0 }}</span>
                      </div>
                      <div class="detail-stat harmony">
                        <span class="detail-label">和谐相位</span>
                        <span class="detail-value">{{ hoveredLink.summary?.harmonious || 0 }}</span>
                      </div>
                      <div class="detail-stat conflict">
                        <span class="detail-label">紧张相位</span>
                        <span class="detail-value">{{ hoveredLink.summary?.challenging || 0 }}</span>
                      </div>
                    </div>
                    <div class="detail-aspects" v-if="hoveredLink.aspects?.length > 0">
                      <h5 class="aspects-title">主要相位</h5>
                      <div class="aspects-list">
                        <div 
                          v-for="(aspect, aidx) in hoveredLink.aspects.slice(0, 5)" 
                          :key="aidx"
                          class="aspect-item"
                          :class="aspect.nature"
                        >
                          <span class="aspect-planet">{{ aspect.planet_a }}</span>
                          <span class="aspect-sym">{{ aspect.aspect_symbol }}</span>
                          <span class="aspect-planet">{{ aspect.planet_b }}</span>
                          <span class="aspect-orb">±{{ aspect.orb_arcminutes }}′</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="activeTab === 'matrix'" class="matrix-tab">
                <div class="matrix-summary">
                  <div class="summary-stat">
                    <span class="stat-value">{{ matrixResult.matrix.summary.total_aspects }}</span>
                    <span class="stat-label">总相位</span>
                  </div>
                  <div class="summary-stat harmonious">
                    <span class="stat-value">{{ matrixResult.matrix.summary.harmonious_aspects }}</span>
                    <span class="stat-label">和谐相位</span>
                  </div>
                  <div class="summary-stat challenging">
                    <span class="stat-value">{{ matrixResult.matrix.summary.challenging_aspects }}</span>
                    <span class="stat-label">紧张相位</span>
                  </div>
                  <div class="summary-stat neutral">
                    <span class="stat-value">{{ matrixResult.matrix.summary.neutral_aspects }}</span>
                    <span class="stat-label">中性相位</span>
                  </div>
                </div>

                <div class="relations-list">
                  <h4 class="list-title">关系详情</h4>
                  <div 
                    v-for="(pair, idx) in matrixResult.matrix.pairs" 
                    :key="idx"
                    class="relation-item"
                    :class="[
                      pair.summary.relation_type,
                      { 'highlighted': isPairHighlighted(pair.pair[0], pair.pair[1]) },
                      { 'dimmed': isPairDimmed(pair.pair[0], pair.pair[1]) }
                    ]"
                    @click="clickRelationPair(pair)"
                    style="cursor: pointer;"
                  >
                    <div class="relation-header">
                      <div class="pair-names">
                        <span class="name clickable" @click.stop="clickMatrixMemberName(pair.pair[0])">{{ pair.pair[0] }}</span>
                        <span class="relation-symbol">
                          <span v-if="pair.summary.relation_type === 'harmony'">💚</span>
                          <span v-else-if="pair.summary.relation_type === 'conflict'">💔</span>
                          <span v-else>⚪</span>
                        </span>
                        <span class="name clickable" @click.stop="clickMatrixMemberName(pair.pair[1])">{{ pair.pair[1] }}</span>
                      </div>
                      <div class="relation-scores">
                        <span class="score-tag harmony">和谐 +{{ pair.summary.harmony_score }}</span>
                        <span class="score-tag conflict" v-if="pair.summary.conflict_score > 0">
                          冲突 -{{ pair.summary.conflict_score }}
                        </span>
                      </div>
                    </div>
                    <div class="aspects-preview" v-if="pair.aspects.length > 0">
                      <div 
                        v-for="(aspect, aidx) in pair.aspects.slice(0, 3)" 
                        :key="aidx"
                        class="aspect-badge"
                        :class="aspect.nature"
                      >
                        <span class="aspect-sym">{{ aspect.aspect_symbol }}</span>
                        <span class="aspect-text">{{ aspect.planet_a }} - {{ aspect.planet_b }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="activeTab === 'scenarios'" class="scenarios-tab">
                <div class="scenario-selector">
                  <button 
                    v-for="scenario in Object.keys(matrixResult.scenarios)" 
                    :key="scenario"
                    class="scenario-btn"
                    :class="{ active: activeScenario === scenario }"
                    @click="activeScenario = scenario"
                  >
                    {{ getScenarioName(scenario) }}
                  </button>
                </div>

                <div v-if="currentScenario" class="scenario-detail">
                  <div class="vibe-indicator" :class="currentScenario.overall_vibe">
                    <div class="vibe-icon">
                      <span v-if="currentScenario.overall_vibe === 'harmonious'">😊</span>
                      <span v-else-if="currentScenario.overall_vibe === 'tense'">😰</span>
                      <span v-else>🤝</span>
                    </div>
                    <div class="vibe-info">
                      <span class="vibe-label">整体氛围</span>
                      <span class="vibe-score">
                        得分: {{ currentScenario.vibe_score }}%
                      </span>
                    </div>
                    <div class="vibe-bar">
                      <div 
                        class="vibe-fill" 
                        :class="currentScenario.overall_vibe"
                        :style="{ width: currentScenario.vibe_score + '%' }"
                      ></div>
                    </div>
                  </div>

                  <div class="role-breakdown">
                    <div class="breakdown-column" v-if="currentScenario.dominant_persons.length > 0">
                      <h4 class="column-title">🎯 主导者</h4>
                      <div 
                        v-for="(p, idx) in currentScenario.dominant_persons" 
                        :key="idx"
                        class="person-item dominant"
                      >
                        <span class="person-name clickable" @click="clickScenarioMemberName(p.name)">{{ p.name }}</span>
                        <span class="person-role">{{ p.role }}</span>
                        <p class="person-reason">{{ p.reason }}</p>
                      </div>
                    </div>

                    <div class="breakdown-column" v-if="currentScenario.cooperative_persons.length > 0">
                      <h4 class="column-title">🤝 配合者</h4>
                      <div 
                        v-for="(p, idx) in currentScenario.cooperative_persons" 
                        :key="idx"
                        class="person-item cooperative"
                      >
                        <span class="person-name clickable" @click="clickScenarioMemberName(p.name)">{{ p.name }}</span>
                        <span class="person-role">{{ p.role }}</span>
                        <p class="person-reason">{{ p.reason }}</p>
                      </div>
                    </div>

                    <div class="breakdown-column" v-if="currentScenario.conflict_persons.length > 0">
                      <h4 class="column-title">⚡ 需要注意</h4>
                      <div 
                        v-for="(p, idx) in currentScenario.conflict_persons" 
                        :key="idx"
                        class="person-item conflict"
                      >
                        <span class="person-name clickable" @click="clickScenarioMemberName(p.name)">{{ p.name }}</span>
                        <span class="person-role">{{ p.role }}</span>
                        <p class="person-reason">{{ p.reason }}</p>
                      </div>
                    </div>
                  </div>

                  <div class="suggestions-section" v-if="currentScenario.suggestions.length > 0">
                    <h4 class="section-title">💡 相处建议</h4>
                    <div class="suggestions-list">
                      <div 
                        v-for="(s, idx) in currentScenario.suggestions" 
                        :key="idx"
                        class="suggestion-item"
                        :class="s.type"
                      >
                        <span class="suggestion-text">{{ s.text }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="activeTab === '3d'" class="visualization-tab">
                <div class="visualization-container">
                  <div class="chart-container multi-member-chart">
                    <ThreeAstroSphere 
                      :members="matrixResult.members" 
                      :matrix="matrixResult.matrix"
                      :focused-member-index="sharedState.focusedMemberIndex"
                      :focused-pair="threeDFocusedPair"
                      :size="600" 
                      @member-focus="handle3DMemberFocus"
                      @pair-focus="handle3DPairFocus"
                      @planet-select="handle3DPlanetSelect"
                    />
                  </div>
                </div>
                <div class="member-selector">
                  <button 
                    v-for="(member, idx) in matrixResult.members" 
                    :key="idx"
                    class="member-select-btn"
                    :class="{ 
                      'active': sharedState.focusedMemberIndex === idx,
                      'core': member.isCore,
                      'highlighted': sharedState.focusedMemberIndex === idx || isPairMember(idx),
                      'dimmed': sharedState.focusedMemberIndex !== null && sharedState.focusedMemberIndex !== idx && !isPairMember(idx)
                    }"
                    @click="handle3DSelectorClick(member, idx)"
                  >
                    <span class="select-avatar" :style="{ background: getMemberColor(member.name) }">
                      {{ member.name ? member.name[0] : '?' }}
                    </span>
                    <span class="select-name">{{ member.name }}</span>
                    <span class="select-role">{{ member.role?.role_icon }} {{ member.role?.role_name }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="modal">
        <div v-if="detailModalOpen" class="modal-overlay" @click.self="closeDetailModal">
          <div class="modal-content">
            <div class="modal-header">
              <h3 class="modal-title">
                <span v-if="detailModalData?.type === 'pair'">
                  关系详情：{{ detailModalData?.pair?.pair?.[0] }} ↔ {{ detailModalData?.pair?.pair?.[1] }}
                </span>
              </h3>
              <button class="modal-close" @click="closeDetailModal">×</button>
            </div>
            <div class="modal-body" v-if="detailModalData?.type === 'pair'">
              <div class="detail-type-badge">
                <span 
                  :class="['type-tag', detailModalData?.pair?.summary?.relation_type]"
                >
                  {{ getRelationLabel(detailModalData?.pair?.summary?.relation_type) }}
                </span>
              </div>
              
              <div class="detail-stats">
                <div class="stat-item harmony">
                  <span class="stat-label">和谐相位</span>
                  <span class="stat-num">{{ detailModalData?.pair?.summary?.harmonious || 0 }}</span>
                </div>
                <div class="stat-item conflict">
                  <span class="stat-label">紧张相位</span>
                  <span class="stat-num">{{ detailModalData?.pair?.summary?.challenging || 0 }}</span>
                </div>
                <div class="stat-item neutral">
                  <span class="stat-label">中性相位</span>
                  <span class="stat-num">{{ detailModalData?.pair?.summary?.neutral || 0 }}</span>
                </div>
              </div>
              
              <div class="detail-scores">
                <div class="score-row">
                  <span class="score-label">和谐得分</span>
                  <div class="score-bar-wrapper">
                    <div 
                      class="score-bar harmony" 
                      :style="{ width: Math.min(100, (detailModalData?.pair?.summary?.harmony_score || 0) * 10) + '%' }"
                    ></div>
                  </div>
                  <span class="score-value">+{{ detailModalData?.pair?.summary?.harmony_score || 0 }}</span>
                </div>
                <div class="score-row" v-if="detailModalData?.pair?.summary?.conflict_score > 0">
                  <span class="score-label">冲突得分</span>
                  <div class="score-bar-wrapper">
                    <div 
                      class="score-bar conflict" 
                      :style="{ width: Math.min(100, (detailModalData?.pair?.summary?.conflict_score || 0) * 10) + '%' }"
                    ></div>
                  </div>
                  <span class="score-value">-{{ detailModalData?.pair?.summary?.conflict_score || 0 }}</span>
                </div>
              </div>
              
              <div class="detail-aspects" v-if="detailModalData?.pair?.aspects?.length > 0">
                <h4 class="aspects-title">详细相位列表</h4>
                <div class="aspects-list-full">
                  <div 
                    v-for="(aspect, idx) in detailModalData?.pair?.aspects" 
                    :key="idx"
                    class="aspect-item-full"
                    :class="aspect.nature"
                  >
                    <div class="aspect-left">
                      <span class="planet-name">{{ aspect.planet_a }}</span>
                      <span class="aspect-sym-large">{{ aspect.aspect_symbol }}</span>
                      <span class="planet-name">{{ aspect.planet_b }}</span>
                    </div>
                    <div class="aspect-right">
                      <span class="aspect-type">{{ getAspectNatureLabel(aspect.nature) }}</span>
                      <span class="aspect-orb">容许度 ±{{ aspect.orb_arcminutes }}′</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-view-topology" @click="viewPairInTopology">
                在拓扑图中查看
              </button>
              <button class="btn-view-3d" @click="viewPairIn3D">
                查看3D星盘
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watchEffect } from 'vue'
import { ElMessage } from 'element-plus'
import { groupMatrixApi } from '@/api'
import { CITIES_DB, QUICK_CITIES } from '@/constants/chart'
import ThreeAstroSphere from '@/components/ThreeAstroSphere.vue'

const colors = [
  '#ff8c32', '#50c8ff', '#22c55e', '#ef4444', '#8b5cf6', 
  '#f59e0b', '#06b6d4', '#ec4899', '#6366f1', '#10b981'
]

const calculating = ref(false)
const showResult = ref(false)
const matrixResult = ref(null)
const activeTab = ref('roles')
const activeScenario = ref('meeting')
const selectedMember = ref(null)
const highlightedMemberIndex = ref(null)
const hoveredMemberIndex = ref(null)

const focusedMemberIndex = ref(null)
const focusedLinkPair = ref(null)
const focusedPairAspects = ref(null)
const showMatrixDetail = ref(false)
const detailModalOpen = ref(false)
const detailModalData = ref(null)

const sharedState = reactive({
  focusedMemberIndex: null,
  focusedLink: null,
  focusedPair: null,
  focusSource: null
})

const tabs = [
  { id: 'roles', name: '角色分配', icon: '👥' },
  { id: 'topology', name: '关系拓扑图', icon: '🕸️' },
  { id: 'matrix', name: '关系矩阵', icon: '📊' },
  { id: 'scenarios', name: '场景模拟', icon: '🎭' },
  { id: '3d', name: '多人3D星盘', icon: '🌌' }
]

const groupName = ref('未命名群组')
const groupType = ref('other')

const members = ref([
  createNewMember(0),
  createNewMember(1)
])

function createNewMember(index) {
  return reactive({
    name: '',
    birthDate: '1990-01-01',
    birthTime: '12:00',
    cityInput: '北京',
    birthPlace: '北京',
    latitude: 39.9042,
    longitude: 116.4074,
    houseSystem: 'placidus',
    isCore: false,
    weight: 1.0,
    color: colors[index % colors.length]
  })
}

const isFormValid = computed(() => {
  return members.value.every(m => 
    m.name && 
    m.birthDate && 
    m.birthTime && 
    m.birthPlace
  )
})

const currentScenario = computed(() => {
  if (!matrixResult.value || !matrixResult.value.scenarios) return null
  return matrixResult.value.scenarios[activeScenario.value]
})

const threeDFocusedPair = computed(() => {
  if (!sharedState.focusedPair) return null
  return {
    a: sharedState.focusedPair.source,
    b: sharedState.focusedPair.target
  }
})

function isPairMember(idx) {
  if (!sharedState.focusedPair) return false
  return sharedState.focusedPair.source === idx || sharedState.focusedPair.target === idx
}

function handle3DSelectorClick(member, idx) {
  if (sharedState.focusedMemberIndex === idx) {
    clearGlobalFocus()
  } else {
    focusMember(idx, '3d')
  }
}

function handle3DMemberFocus(memberIdx) {
  if (memberIdx === null) {
    clearGlobalFocus()
  } else {
    focusMember(memberIdx, '3d')
  }
}

function handle3DPairFocus(pairData) {
  if (!pairData) {
    clearGlobalFocus()
  } else {
    focusPairByIndices(pairData.a, pairData.b, '3d')
  }
}

function handle3DPlanetSelect(planetData) {
  if (!planetData) return
  
  if (planetData.memberIndex !== undefined) {
    focusMember(planetData.memberIndex, '3d')
  }
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

function addMember() {
  if (members.value.length >= 10) {
    ElMessage.warning('最多支持10个成员')
    return
  }
  members.value.push(createNewMember(members.value.length))
}

function removeMember(index) {
  if (members.value.length > 2) {
    members.value.splice(index, 1)
    members.value.forEach((m, i) => {
      m.color = colors[i % colors.length]
    })
  }
}

function toggleCore(index) {
  members.value[index].isCore = !members.value[index].isCore
  members.value[index].weight = members.value[index].isCore ? 1.5 : 1.0
}

function queryCitySuggestions(queryString, callback) {
  if (!queryString || queryString.trim().length === 0) {
    callback(CITIES_DB.slice(0, 15))
    return
  }
  
  const q = queryString.toLowerCase()
  const results = CITIES_DB.filter(city => 
    city.name.includes(queryString) || 
    city.name.toLowerCase().includes(q)
  )
  
  callback(results.slice(0, 15))
}

function onCitySelect(item, index) {
  Object.assign(members.value[index], {
    cityInput: item.name,
    birthPlace: item.name,
    latitude: item.latitude,
    longitude: item.longitude
  })
}

function selectQuickCity(city, index) {
  Object.assign(members.value[index], {
    cityInput: city.name,
    birthPlace: city.name,
    latitude: city.latitude,
    longitude: city.longitude
  })
}

async function calculateMatrix() {
  if (!isFormValid.value) {
    ElMessage.warning('请填写所有成员的完整信息')
    return
  }

  calculating.value = true

  try {
    const data = {
      group_name: groupName.value,
      group_type: groupType.value,
      members: members.value.map(m => ({
        name: m.name,
        birth_date: m.birthDate,
        birth_time: m.birthTime,
        birth_place: m.birthPlace,
        latitude: m.latitude,
        longitude: m.longitude,
        house_system: m.houseSystem,
        is_core: m.isCore,
        weight: m.weight
      }))
    }

    const result = await groupMatrixApi.calculate(data)
    matrixResult.value = result
    showResult.value = true
    
    if (result.members && result.members.length > 0) {
      selectedMember.value = result.members[0]
    }
    
    ElMessage.success('关系矩阵计算完成')
  } catch (error) {
    console.error('计算失败:', error)
    ElMessage.error(error.message || '计算失败')
  } finally {
    calculating.value = false
  }
}

function resetForm() {
  showResult.value = false
  matrixResult.value = null
  selectedMember.value = null
  activeTab.value = 'roles'
  activeScenario.value = 'meeting'
}

function getScorePercent(score) {
  const maxScore = 15
  return Math.min(100, (score / maxScore) * 100)
}

function getScenarioName(type) {
  const names = {
    meeting: '团队会议',
    travel: '一起旅行',
    project: '项目合作'
  }
  return names[type] || type
}

function getMemberColor(name) {
  const idx = members.value.findIndex(m => m.name === name)
  if (idx >= 0) {
    return members.value[idx].color
  }
  return colors[0]
}

const hoveredLink = ref(null)
const topologyLinksWithNodes = ref([])

watchEffect(() => {
  if (matrixResult.value?.topology?.links && matrixResult.value?.topology?.nodes) {
    const links = matrixResult.value.topology.links
    const nodes = matrixResult.value.topology.nodes
    
    topologyLinksWithNodes.value = links.map(link => ({
      ...link,
      source_node: nodes[link.source],
      target_node: nodes[link.target]
    }))
  }
})

function getLinkColor(link) {
  const config = {
    harmony: '#22c55e',
    conflict: '#ef4444',
    neutral: '#64748b'
  }
  return config[link.relation_type] || config.neutral
}

function getLinkWidth(link) {
  const baseWidth = {
    harmony: 2,
    conflict: 2.5,
    neutral: 1
  }
  let width = baseWidth[link.relation_type] || 1
  
  const totalAspects = link.summary?.total || 0
  const harmonyScore = link.summary?.harmony_score || 0
  const conflictScore = link.summary?.conflict_score || 0
  const dominantScore = Math.max(harmonyScore, conflictScore)
  
  if (totalAspects > 0) {
    const aspectFactor = Math.min(2.0, 1 + totalAspects * 0.15)
    width *= aspectFactor
  }
  
  if (dominantScore > 0) {
    const scoreFactor = Math.min(1.8, 1 + dominantScore * 0.1)
    width *= scoreFactor
  }
  
  let maxStrength = 0
  if (link.aspects && link.aspects.length > 0) {
    link.aspects.forEach(aspect => {
      const orbRatio = aspect.line_config?.orb_ratio || 0.5
      const strength = 1 - orbRatio + 0.5
      maxStrength = Math.max(maxStrength, strength)
    })
    if (maxStrength > 0) {
      width *= Math.min(1.5, maxStrength)
    }
  }
  
  return Math.max(0.8, Math.min(6, width))
}

function getLinkFilter(link) {
  if (link.relation_type === 'harmony') return 'url(#glow-green)'
  if (link.relation_type === 'conflict') return 'url(#glow-red)'
  return 'url(#glow-purple)'
}

function getLinkStyle(link) {
  let opacity = 0.8
  if (link.relation_type === 'neutral') opacity = 0.5
  
  const focusedIdx = sharedState.focusedMemberIndex !== null ? sharedState.focusedMemberIndex : hoveredMemberIndex.value
  const focusedLnk = sharedState.focusedLink || hoveredLink.value
  
  if (focusedIdx !== null) {
    const isConnected = link.source === focusedIdx || link.target === focusedIdx
    opacity = isConnected ? 1.0 : 0.2
  } else if (focusedLnk) {
    opacity = (focusedLnk.source === link.source && focusedLnk.target === link.target) ||
              (focusedLnk.source === link.target && focusedLnk.target === link.source) ? 1.0 : 0.2
  }
  
  return { opacity }
}

function isLinkHighlighted(link) {
  const focusedLnk = sharedState.focusedLink || hoveredLink.value
  const focusedIdx = sharedState.focusedMemberIndex !== null ? sharedState.focusedMemberIndex : hoveredMemberIndex.value
  
  if (focusedLnk) {
    return (focusedLnk.source === link.source && focusedLnk.target === link.target) ||
           (focusedLnk.source === link.target && focusedLnk.target === link.source)
  }
  if (focusedIdx !== null) {
    return link.source === focusedIdx || link.target === focusedIdx
  }
  return false
}

function isLinkDimmed(link) {
  const focusedLnk = sharedState.focusedLink || hoveredLink.value
  const focusedIdx = sharedState.focusedMemberIndex !== null ? sharedState.focusedMemberIndex : hoveredMemberIndex.value
  
  if (focusedLnk || focusedIdx !== null) {
    return !isLinkHighlighted(link)
  }
  return false
}

function isNodeDimmed(idx) {
  const focusedIdx = sharedState.focusedMemberIndex !== null ? sharedState.focusedMemberIndex : hoveredMemberIndex.value
  const focusedLnk = sharedState.focusedLink || hoveredLink.value
  
  if (focusedIdx !== null) {
    return idx !== focusedIdx
  }
  if (focusedLnk) {
    return idx !== focusedLnk.source && idx !== focusedLnk.target
  }
  return false
}

function hoverLink(link) {
  hoveredLink.value = link
}

function clearLinkHover() {
  hoveredLink.value = null
}

function highlightMember(idx) {
  highlightedMemberIndex.value = idx
}

function clearHighlight() {
  highlightedMemberIndex.value = null
}

function selectMemberByIndex(idx) {
  if (matrixResult.value?.topology?.nodes) {
    const node = matrixResult.value.topology.nodes[idx]
    if (node && matrixResult.value?.members) {
      selectedMember.value = matrixResult.value.members.find(m => m.name === node.name)
      activeTab.value = '3d'
    }
  }
}

function focusMember(idx, source = 'unknown') {
  sharedState.focusedMemberIndex = idx
  sharedState.focusedLink = null
  sharedState.focusedPair = null
  sharedState.focusSource = source
  
  focusedMemberIndex.value = idx
  hoveredMemberIndex.value = idx
  
  if (source !== 'topology') {
    activeTab.value = 'topology'
  }
  
  highlightInMatrix(idx, null)
}

function focusLink(link, source = 'unknown') {
  sharedState.focusedLink = link
  sharedState.focusedMemberIndex = null
  sharedState.focusedPair = { source: link.source, target: link.target }
  sharedState.focusSource = source
  
  hoveredLink.value = link
  hoveredMemberIndex.value = null
  
  if (source !== 'topology') {
    activeTab.value = 'topology'
  }
  
  highlightInMatrix(link.source, link.target)
}

function focusPairByName(name1, name2, source = 'unknown') {
  if (!matrixResult.value?.topology?.nodes) return
  
  const nodes = matrixResult.value.topology.nodes
  const idx1 = nodes.findIndex(n => n.name === name1)
  const idx2 = nodes.findIndex(n => n.name === name2)
  
  if (idx1 >= 0 && idx2 >= 0) {
    const links = matrixResult.value.topology.links
    const link = links.find(l => 
      (l.source === idx1 && l.target === idx2) || 
      (l.source === idx2 && l.target === idx1)
    )
    
    if (link) {
      focusLink(link, source)
    }
  }
}

function highlightInMatrix(rowIdx, colIdx) {
  focusedMemberIndex.value = rowIdx
  focusedLinkPair.value = colIdx !== null ? [rowIdx, colIdx] : null
}

function clearGlobalFocus() {
  sharedState.focusedMemberIndex = null
  sharedState.focusedLink = null
  sharedState.focusedPair = null
  sharedState.focusSource = null
  
  hoveredMemberIndex.value = null
  hoveredLink.value = null
  highlightedMemberIndex.value = null
  focusedMemberIndex.value = null
  focusedLinkPair.value = null
}

function openDetailModal(data) {
  detailModalData.value = data
  detailModalOpen.value = true
}

function closeDetailModal() {
  detailModalOpen.value = false
  detailModalData.value = null
}

function navigateTo3DWithFocus(memberIdx = null, pairIdx = null) {
  if (memberIdx !== null && matrixResult.value?.members) {
    selectedMember.value = matrixResult.value.members[memberIdx]
  }
  activeTab.value = '3d'
  
  if (window.parent || window.top !== window) {
    window.postMessage({
      type: 'ASTRO_3D_FOCUS',
      memberIndex: memberIdx,
      pairIndices: pairIdx
    }, '*')
  }
}

function isCellHighlighted(rowIdx, colIdx) {
  if (sharedState.focusedMemberIndex !== null) {
    return rowIdx === sharedState.focusedMemberIndex || colIdx === sharedState.focusedMemberIndex
  }
  if (sharedState.focusedPair) {
    return (rowIdx === sharedState.focusedPair.source && colIdx === sharedState.focusedPair.target) ||
           (rowIdx === sharedState.focusedPair.target && colIdx === sharedState.focusedPair.source)
  }
  return false
}

function isCellDimmed(rowIdx, colIdx) {
  if (sharedState.focusedMemberIndex !== null || sharedState.focusedPair) {
    return !isCellHighlighted(rowIdx, colIdx)
  }
  return false
}

function clickMatrixCell(rowIdx, colIdx) {
  if (rowIdx === colIdx) return
  
  const links = matrixResult.value?.topology?.links
  if (!links) return
  
  const link = links.find(l => 
    (l.source === rowIdx && l.target === colIdx) || 
    (l.source === colIdx && l.target === rowIdx)
  )
  
  if (link) {
    focusLink(link, 'matrix')
    
    const pair = matrixResult.value?.matrix?.pairs?.find(p => 
      (p.pair[0] === link.source_node?.name && p.pair[1] === link.target_node?.name) ||
      (p.pair[0] === link.target_node?.name && p.pair[1] === link.source_node?.name)
    )
    
    if (pair) {
      openDetailModal({
        type: 'pair',
        pair: pair,
        link: link
      })
    }
  }
}

function clickTopologyNode(idx) {
  focusMember(idx, 'topology')
  navigateTo3DWithFocus(idx, null)
}

function clickTopologyLink(link) {
  focusLink(link, 'topology')
  navigateTo3DWithFocus(null, [link.source, link.target])
  
  const pair = matrixResult.value?.matrix?.pairs?.find(p => 
    (p.pair[0] === link.source_node?.name && p.pair[1] === link.target_node?.name) ||
    (p.pair[0] === link.target_node?.name && p.pair[1] === link.source_node?.name)
  )
  
  if (pair) {
    openDetailModal({
      type: 'pair',
      pair: pair,
      link: link
    })
  }
}

function clickScenarioMemberName(name) {
  if (!matrixResult.value?.topology?.nodes) return
  
  const idx = matrixResult.value.topology.nodes.findIndex(n => n.name === name)
  if (idx >= 0) {
    focusMember(idx, 'scenario')
    navigateTo3DWithFocus(idx, null)
  }
}

function clickScenarioPair(pairNames) {
  if (pairNames && pairNames.length === 2) {
    focusPairByName(pairNames[0], pairNames[1], 'scenario')
    navigateTo3DWithFocus(null, null)
  }
}

function focusPairByIndices(idx1, idx2, source = 'unknown') {
  if (!matrixResult.value?.topology?.links) return
  
  const link = matrixResult.value.topology.links.find(l => 
    (l.source === idx1 && l.target === idx2) || 
    (l.source === idx2 && l.target === idx1)
  )
  
  if (link) {
    focusLink(link, source)
  }
}

function handle3DMessage(event) {
  const data = event.data
  if (!data || data.type !== 'ASTRO_3D_INTERACTION') return
  
  if (data.action === 'focusMember' && data.memberIndex !== undefined) {
    focusMember(data.memberIndex, '3d')
  }
  
  if (data.action === 'focusPair' && data.pairIndices) {
    focusPairByIndices(data.pairIndices[0], data.pairIndices[1], '3d')
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('message', handle3DMessage)
}

function isPairHighlighted(name1, name2) {
  if (sharedState.focusedMemberIndex !== null && matrixResult.value?.topology?.nodes) {
    const focusedName = matrixResult.value.topology.nodes[sharedState.focusedMemberIndex]?.name
    return name1 === focusedName || name2 === focusedName
  }
  if (sharedState.focusedPair && matrixResult.value?.topology?.nodes) {
    const nodes = matrixResult.value.topology.nodes
    const nameA = nodes[sharedState.focusedPair.source]?.name
    const nameB = nodes[sharedState.focusedPair.target]?.name
    return (name1 === nameA && name2 === nameB) || (name1 === nameB && name2 === nameA)
  }
  return false
}

function isPairDimmed(name1, name2) {
  if (sharedState.focusedMemberIndex !== null || sharedState.focusedPair) {
    return !isPairHighlighted(name1, name2)
  }
  return false
}

function clickRelationPair(pair) {
  if (pair && pair.pair && pair.pair.length === 2) {
    focusPairByName(pair.pair[0], pair.pair[1], 'matrix')
    openDetailModal({
      type: 'pair',
      pair: pair,
      link: getLinkByNames(pair.pair[0], pair.pair[1])
    })
  }
}

function clickMatrixMemberName(name) {
  if (!matrixResult.value?.topology?.nodes) return
  
  const idx = matrixResult.value.topology.nodes.findIndex(n => n.name === name)
  if (idx >= 0) {
    focusMember(idx, 'matrix')
    navigateTo3DWithFocus(idx, null)
  }
}

function getLinkByNames(name1, name2) {
  if (!matrixResult.value?.topology?.links || !matrixResult.value?.topology?.nodes) return null
  
  const nodes = matrixResult.value.topology.nodes
  const idx1 = nodes.findIndex(n => n.name === name1)
  const idx2 = nodes.findIndex(n => n.name === name2)
  
  if (idx1 < 0 || idx2 < 0) return null
  
  return matrixResult.value.topology.links.find(l => 
    (l.source === idx1 && l.target === idx2) || 
    (l.source === idx2 && l.target === idx1)
  )
}

function handleMemberSelect(member, idx) {
  selectedMember.value = member
  focusMember(idx, '3d')
}

function getRelationLabel(type) {
  const labels = {
    harmony: '和谐关系',
    conflict: '紧张关系',
    neutral: '平淡关系'
  }
  return labels[type] || '未知'
}

function getAspectNatureLabel(nature) {
  const labels = {
    harmonious: '和谐相位',
    challenging: '紧张相位',
    neutral: '中性相位'
  }
  return labels[nature] || '未知'
}

function viewPairInTopology() {
  if (detailModalData.value?.pair?.pair) {
    closeDetailModal()
    focusPairByName(
      detailModalData.value.pair.pair[0],
      detailModalData.value.pair.pair[1],
      'modal'
    )
  }
}

function viewPairIn3D() {
  if (detailModalData.value?.pair?.pair && matrixResult.value?.members) {
    closeDetailModal()
    const name1 = detailModalData.value.pair.pair[0]
    const member = matrixResult.value.members.find(m => m.name === name1)
    if (member) {
      selectedMember.value = member
      activeTab.value = '3d'
    }
  }
}
</script>

<style lang="scss" scoped>
.group-matrix-container {
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

.group-matrix-main {
  position: relative;
  z-index: 10;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.main-title {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ff8c32 0%, #8b5cf6 50%, #50c8ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 6px;
}

.subtitle {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.form-section {
  background: rgba(12, 12, 28, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.1);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.add-member-btn {
  padding: 8px 16px;
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #c4b5fd;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.3);
    transform: translateY(-1px);
  }
}

.btn-icon {
  font-weight: bold;
  margin-right: 4px;
}

.group-info-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  
  &.full-width {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(20, 20, 40, 0.8);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: rgba(139, 92, 246, 0.5);
    background: rgba(20, 20, 50, 0.9);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }
}

.members-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.member-card {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 16px;
  border-left: 3px solid;
  transition: all 0.2s ease;
  
  &.is-core {
    border-color: rgba(245, 158, 11, 0.4);
    background: rgba(20, 15, 5, 0.4);
  }
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
    transform: translateY(-2px);
  }
}

.member-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.1);
}

.member-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
  font-size: 0.9rem;
}

.member-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.member-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  
  &:hover {
    background: rgba(139, 92, 246, 0.3);
    color: #fff;
  }
  
  &.delete:hover {
    background: rgba(239, 68, 68, 0.3);
  }
}

.member-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-cities {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 4px;
}

.city-btn {
  padding: 4px 10px;
  background: rgba(80, 60, 160, 0.1);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    color: rgba(255, 255, 255, 0.7);
  }
}

.submit-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.submit-btn {
  padding: 14px 48px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  border-radius: 30px;
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.hint-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.result-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.back-btn {
  padding: 8px 16px;
  background: rgba(80, 60, 160, 0.2);
  border: 1px solid rgba(80, 60, 160, 0.3);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(80, 60, 160, 0.3);
    color: #fff;
  }
}

.tabs-section {
  background: rgba(12, 12, 28, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 16px;
  overflow: hidden;
}

.tabs-header {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(20, 15, 40, 0.5);
  border-bottom: 1px solid rgba(80, 60, 160, 0.15);
}

.tab-btn {
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
    color: rgba(255, 255, 255, 0.7);
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
  }
}

.tab-content {
  padding: 20px;
}

.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.role-card {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;
  
  &.core-highlight {
    border-color: rgba(245, 158, 11, 0.4);
  }
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.2);
  }
}

.role-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.role-icon {
  font-size: 2rem;
}

.role-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.role-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.person-name {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.role-body {
  padding: 16px;
  border-top: 1px solid rgba(80, 60, 160, 0.1);
}

.role-description {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 16px;
  line-height: 1.5;
}

.scores-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.score-track {
  height: 6px;
  background: rgba(20, 20, 40, 0.8);
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
  
  &.glue {
    background: linear-gradient(90deg, #22c55e, #16a34a);
  }
  
  &.firecracker {
    background: linear-gradient(90deg, #ef4444, #dc2626);
  }
  
  &.visionary {
    background: linear-gradient(90deg, #8b5cf6, #7c3aed);
  }
}

.matrix-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.summary-stat {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  
  &.harmonious {
    border-color: rgba(34, 197, 94, 0.3);
    background: rgba(20, 35, 20, 0.4);
  }
  
  &.challenging {
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(35, 20, 20, 0.4);
  }
  
  &.neutral {
    border-color: rgba(251, 191, 36, 0.3);
    background: rgba(35, 30, 20, 0.4);
  }
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.stat-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.relations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 8px;
}

.relation-item {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
  
  &.harmony {
    border-color: rgba(34, 197, 94, 0.3);
    background: rgba(20, 35, 20, 0.3);
  }
  
  &.conflict {
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(35, 20, 20, 0.3);
  }
}

.relation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.pair-names {
  display: flex;
  align-items: center;
  gap: 12px;
}

.name {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.relation-symbol {
  font-size: 1.2rem;
}

.relation-scores {
  display: flex;
  gap: 8px;
}

.score-tag {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  
  &.harmony {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }
  
  &.conflict {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
}

.aspects-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.aspect-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(80, 60, 160, 0.1);
  border-radius: 6px;
  font-size: 0.75rem;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
  }
  
  &.challenging {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
  }
  
  &.neutral {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
  }
}

.aspect-sym {
  font-size: 0.9rem;
  font-weight: bold;
}

.aspect-text {
  color: rgba(255, 255, 255, 0.7);
}

.scenario-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.scenario-btn {
  padding: 10px 24px;
  background: rgba(20, 20, 40, 0.8);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    color: rgba(255, 255, 255, 0.8);
  }
  
  &.active {
    background: rgba(139, 92, 246, 0.25);
    border-color: rgba(139, 92, 246, 0.4);
    color: #c4b5fd;
  }
}

.scenario-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.vibe-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: rgba(15, 15, 35, 0.9);
  border-radius: 12px;
  border: 1px solid rgba(80, 60, 160, 0.15);
  
  &.harmonious {
    border-color: rgba(34, 197, 94, 0.3);
  }
  
  &.tense {
    border-color: rgba(239, 68, 68, 0.3);
  }
}

.vibe-icon {
  font-size: 3rem;
}

.vibe-info {
  text-align: center;
}

.vibe-label {
  display: block;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.vibe-score {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.vibe-bar {
  width: 200px;
  height: 8px;
  background: rgba(20, 20, 40, 0.8);
  border-radius: 4px;
  overflow: hidden;
}

.vibe-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
  
  &.harmonious {
    background: linear-gradient(90deg, #22c55e, #16a34a);
  }
  
  &.tense {
    background: linear-gradient(90deg, #ef4444, #dc2626);
  }
  
  &.balanced {
    background: linear-gradient(90deg, #8b5cf6, #6366f1);
  }
}

.role-breakdown {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.breakdown-column {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 16px;
}

.column-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.1);
}

.person-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  &.dominant {
    background: rgba(139, 92, 246, 0.1);
    border-left: 2px solid #8b5cf6;
  }
  
  &.cooperative {
    background: rgba(34, 197, 94, 0.1);
    border-left: 2px solid #22c55e;
  }
  
  &.conflict {
    background: rgba(239, 68, 68, 0.1);
    border-left: 2px solid #ef4444;
  }
}

.person-item .person-name {
  font-weight: 600;
  margin-right: 8px;
}

.person-item .person-role {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.person-reason {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 6px 0 0;
  line-height: 1.4;
}

.suggestions-section {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 16px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 12px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  padding: 12px 16px;
  border-radius: 8px;
  
  &.positive {
    background: rgba(34, 197, 94, 0.1);
    border-left: 3px solid #22c55e;
  }
  
  &.warning {
    background: rgba(245, 158, 11, 0.1);
    border-left: 3px solid #f59e0b;
  }
}

.suggestion-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.visualization-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.visualization-container {
  display: flex;
  justify-content: center;
}

.visualization-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  width: 100%;
  background: rgba(15, 15, 35, 0.9);
  border-radius: 12px;
  border: 1px dashed rgba(80, 60, 160, 0.3);
}

.placeholder-content {
  text-align: center;
}

.placeholder-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 12px;
}

.placeholder-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
}

.chart-container {
  width: 100%;
  max-width: 600px;
}

.member-selector {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.member-select-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 100px;
  
  &:hover {
    transform: translateY(-2px);
    border-color: rgba(139, 92, 246, 0.3);
  }
  
  &.active {
    border-color: rgba(139, 92, 246, 0.5);
    background: rgba(139, 92, 246, 0.15);
  }
  
  &.core {
    border-top: 3px solid #f59e0b;
  }
}

.select-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
}

.select-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.select-role {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-name {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
}

.option-location {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.topology-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.team-energy-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
}

.energy-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border: 2px solid;
  border-radius: 20px;
}

.energy-icon {
  font-size: 1.5rem;
}

.energy-name {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.energy-stats {
  display: flex;
  gap: 24px;
}

.energy-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
}

.energy-stat .stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.energy-stat .stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.topology-container {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 20px;
  align-items: start;
}

.topology-svg-wrapper {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: center;
  min-height: 500px;
}

.topology-svg {
  width: 100%;
  max-width: 500px;
  height: auto;
}

.nodes-group {
  cursor: pointer;
}

.node-group {
  transition: transform 0.3s ease;
  
  &.highlighted {
    filter: drop-shadow(0 0 15px rgba(139, 92, 246, 0.6));
  }
  
  &.dimmed {
    opacity: 0.4;
  }
  
  &:hover {
    .node-circle {
      filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.8));
    }
  }
}

.node-circle {
  transition: all 0.3s ease;
}

.core-orb {
  transform-origin: center;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.node-avatar {
  pointer-events: none;
}

.node-label {
  pointer-events: none;
}

.node-role-label {
  pointer-events: none;
}

.node-core-badge {
  pointer-events: none;
}

.link-line {
  transition: all 0.3s ease;
  cursor: pointer;
  
  &.highlighted {
    stroke-width: 4;
    opacity: 1;
  }
  
  &.dimmed {
    opacity: 0.2;
  }
  
  &:hover {
    stroke-width: 5;
  }
}

.topology-legend {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 160px;
}

.legend-section {
  background: rgba(15, 15, 35, 0.9);
  border: 1px solid rgba(80, 60, 160, 0.15);
  border-radius: 12px;
  padding: 16px;
}

.legend-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.1);
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-line {
  width: 24px;
  height: 3px;
  border-radius: 2px;
  
  &.harmony {
    background: #22c55e;
  }
  
  &.conflict {
    background: #ef4444;
    border: none;
  }
  
  &.neutral {
    background: #64748b;
    opacity: 0.6;
  }
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.topology-details {
  margin-top: 10px;
}

.detail-card {
  background: rgba(15, 15, 35, 0.95);
  border: 1px solid rgba(80, 60, 160, 0.2);
  border-radius: 12px;
  padding: 20px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 12px;
}

.detail-relation-type {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 16px;
  
  &.harmony {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }
  
  &.conflict {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
  
  &.neutral {
    background: rgba(100, 116, 139, 0.2);
    color: #94a3b8;
  }
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.detail-stat {
  text-align: center;
  padding: 10px;
  background: rgba(20, 20, 40, 0.8);
  border-radius: 8px;
  
  &.harmony {
    border-left: 3px solid #22c55e;
  }
  
  &.conflict {
    border-left: 3px solid #ef4444;
  }
}

.detail-stat .detail-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.detail-stat .detail-value {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.detail-aspects {
  margin-top: 16px;
}

.aspects-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 10px;
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.aspect-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.1);
  }
  
  &.challenging {
    background: rgba(239, 68, 68, 0.1);
  }
  
  &.neutral {
    background: rgba(100, 116, 139, 0.1);
  }
}

.aspect-planet {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.aspect-sym {
  font-size: 1rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.7);
}

.aspect-orb {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  margin-left: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 1200px) {
  .role-breakdown {
    grid-template-columns: 1fr;
  }
  
  .matrix-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .members-list {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .tabs-header {
    flex-wrap: wrap;
  }
  
  .roles-grid {
    grid-template-columns: 1fr;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(180deg, #1a1a35 0%, #121228 100%);
  border: 1px solid rgba(80, 60, 160, 0.3);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.15);
  flex-shrink: 0;
}

.modal-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(80, 60, 160, 0.15);
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(80, 60, 160, 0.3);
    color: rgba(255, 255, 255, 0.9);
  }
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex-grow: 1;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(80, 60, 160, 0.15);
  flex-shrink: 0;
  justify-content: flex-end;
}

.btn-view-topology,
.btn-view-3d {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-view-topology {
  background: rgba(80, 60, 160, 0.2);
  color: rgba(255, 255, 255, 0.8);
  
  &:hover {
    background: rgba(80, 60, 160, 0.35);
    color: rgba(255, 255, 255, 0.95);
  }
}

.btn-view-3d {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: #fff;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  }
}

.detail-type-badge {
  margin-bottom: 16px;
}

.type-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  
  &.harmony {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
  }
  
  &.conflict {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  
  &.neutral {
    background: rgba(100, 116, 139, 0.2);
    color: #94a3b8;
    border: 1px solid rgba(100, 116, 139, 0.3);
  }
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 14px 10px;
  background: rgba(20, 20, 40, 0.6);
  border-radius: 10px;
  
  &.harmony {
    border-left: 3px solid #22c55e;
  }
  
  &.conflict {
    border-left: 3px solid #ef4444;
  }
  
  &.neutral {
    border-left: 3px solid #64748b;
  }
}

.stat-item .stat-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.stat-item .stat-num {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.detail-scores {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-row .score-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  min-width: 65px;
}

.score-bar-wrapper {
  flex-grow: 1;
  height: 8px;
  background: rgba(80, 60, 160, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.score-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
  
  &.harmony {
    background: linear-gradient(90deg, #22c55e, #4ade80);
  }
  
  &.conflict {
    background: linear-gradient(90deg, #ef4444, #f87171);
  }
}

.score-row .score-value {
  font-size: 0.85rem;
  font-weight: 600;
  min-width: 45px;
  text-align: right;
  color: rgba(255, 255, 255, 0.85);
}

.detail-aspects {
  margin-top: 8px;
}

.aspects-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(80, 60, 160, 0.1);
}

.aspects-list-full {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-item-full {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  
  &.harmonious {
    background: rgba(34, 197, 94, 0.1);
    border-left: 2px solid #22c55e;
  }
  
  &.challenging {
    background: rgba(239, 68, 68, 0.1);
    border-left: 2px solid #ef4444;
  }
  
  &.neutral {
    background: rgba(100, 116, 139, 0.1);
    border-left: 2px solid #64748b;
  }
}

.aspect-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.planet-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.aspect-sym-large {
  font-size: 1.1rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.75);
}

.aspect-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.aspect-type {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.aspect-item-full.harmonious .aspect-type {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.aspect-item-full.challenging .aspect-type {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.aspect-item-full.neutral .aspect-type {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.aspect-orb {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.clickable {
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: all 0.2s ease;
  
  &:hover {
    text-decoration-color: rgba(139, 92, 246, 0.6);
    color: #8b5cf6;
  }
}

.relation-item {
  &.highlighted {
    border-color: #8b5cf6;
    background: rgba(139, 92, 246, 0.15);
    transform: translateX(4px);
  }
  
  &.dimmed {
    opacity: 0.4;
  }
}

.member-select-btn {
  &.highlighted {
    border-color: #8b5cf6;
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  
  .modal-content {
    transform: scale(0.95) translateY(10px);
  }
}
</style>
