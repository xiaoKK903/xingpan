<template>
  <div class="contribute-page">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>

    <div class="contribute-main">
      <div class="page-header">
        <div class="header-back" @click="router.back()">
          <el-icon><Connection /></el-icon>
          <span>返回</span>
        </div>
        <div class="header-title">
          <div class="title-icon">
            <el-icon size="28"><MagicStick /></el-icon>
          </div>
          <div class="title-text">
            <h1>能量注入中心</h1>
            <p>分享你的行星能量，加持社区整体能量</p>
          </div>
        </div>
      </div>

      <div class="bonus-section">
        <div class="bonus-card">
          <div class="bonus-icon">
            <el-icon size="32"><Sunny /></el-icon>
          </div>
          <div class="bonus-info">
            <div class="bonus-title">社区能量加成</div>
            <div class="bonus-value">
              +{{ Math.round((communityBonus?.bonus_percentage || 0)) }}%
            </div>
          </div>
          <div class="bonus-stats">
            <div class="stat-item">
              <span class="stat-label">已注入能量</span>
              <span class="stat-value">{{ Math.round(communityBonus?.total_energy_contributed || 0) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">活跃贡献</span>
              <span class="stat-value">{{ communityBonus?.active_contribution_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="contribution-types">
        <div class="section-header">
          <span class="section-title">选择你要注入的能量</span>
          <span class="section-hint">每次注入持续 30 分钟，消耗 5 星尘</span>
        </div>

        <div class="contributions-grid">
          <div 
            class="contribution-card" 
            v-for="contrib in availableContributions" 
            :key="contrib.type"
            :class="{ selected: selectedType === contrib.type }"
            @click="selectContribution(contrib)"
          >
            <div class="contrib-icon" :style="{ backgroundColor: contrib.color + '20' }">
              <span class="icon-text" :style="{ color: contrib.color }">
                {{ contrib.planet_icon }}
              </span>
            </div>
            <div class="contrib-info">
              <div class="contrib-name">{{ contrib.name }}</div>
              <div class="contrib-desc">{{ contrib.description }}</div>
              <div class="contrib-targets">
                <span class="target-label">影响维度：</span>
                <span class="target-dims">
                  {{ contrib.target_dimensions?.map(d => getDimensionName(d)).join('、') || '全局' }}
                </span>
              </div>
            </div>
            <div class="contrib-meta">
              <div class="meta-item">
                <span class="meta-icon">⚡</span>
                <span>{{ contrib.base_energy }} 能量</span>
              </div>
              <div class="meta-item">
                <span class="meta-icon">⏱</span>
                <span>{{ contrib.duration_minutes }} 分钟</span>
              </div>
              <div class="meta-item cost">
                <span class="meta-icon">✨</span>
                <span>{{ contrib.cost_stardust }} 星尘</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="inject-section" v-if="selectedType">
        <div class="scope-selector">
          <span class="selector-label">注入范围</span>
          <el-radio-group v-model="injectScope" size="large">
            <el-radio-button value="global">
              <el-icon><MagicStick /></el-icon>
              <span>全站能量</span>
            </el-radio-button>
            <el-radio-button value="local" v-if="currentUserCity">
              <el-icon><Location /></el-icon>
              <span>同城能量 ({{ currentUserCity }})</span>
            </el-radio-button>
          </el-radio-group>
        </div>

        <div class="inject-actions">
          <div class="inject-preview">
            <div class="preview-label">即将注入</div>
            <div class="preview-content">
              <el-avatar 
                :size="40" 
                :style="{ backgroundColor: selectedContribution?.color + '20', color: selectedContribution?.color }"
              >
                <span style="font-size: 20px">{{ selectedContribution?.planet_icon }}</span>
              </el-avatar>
              <div class="preview-info">
                <div class="preview-name">{{ selectedContribution?.name }}</div>
                <div class="preview-detail">
                  <span class="preview-energy">+{{ selectedContribution?.base_energy || 0 }} 能量</span>
                  <span class="preview-separator">·</span>
                  <span class="preview-cost">消耗 {{ selectedContribution?.cost_stardust || 0 }} 星尘</span>
                </div>
              </div>
            </div>
          </div>
          <el-button 
            type="primary" 
            size="large" 
            :loading="injecting"
            @click="handleInject"
            class="inject-btn"
          >
            <el-icon><MagicStick /></el-icon>
            确认注入
          </el-button>
        </div>
      </div>

      <div class="active-contributions-section" v-if="myActiveContributions?.length > 0">
        <div class="section-header">
          <span class="section-title">我的活跃贡献</span>
        </div>

        <div class="active-list">
          <div class="active-item" v-for="contrib in myActiveContributions" :key="contrib.id">
            <div class="active-icon" :style="{ backgroundColor: contrib.color + '20' }">
              <span :style="{ color: contrib.color }">{{ contrib.planet_icon }}</span>
            </div>
            <div class="active-info">
              <div class="active-name">{{ contrib.name }}</div>
              <div class="active-time">
                <span class="remaining">剩余 {{ contrib.remaining_minutes }} 分钟</span>
                <span class="separator">·</span>
                <span class="scope">{{ contrib.target_scope === 'global' ? '全站' : '同城' }}</span>
              </div>
            </div>
            <div class="active-progress">
              <el-progress 
                type="dashboard" 
                :percentage="getRemainingPercentage(contrib)" 
                :width="60"
                :stroke-width="8"
                :color="contrib.color"
              />
            </div>
            <el-button 
              type="danger" 
              :icon="Close" 
              circle 
              size="small"
              @click="handleCancel(contrib)"
            />
          </div>
        </div>
      </div>

      <div class="community-contributions-section">
        <div class="section-header">
          <span class="section-title">社区活跃贡献</span>
          <span class="section-hint" v-if="communityContributions?.contributions?.length > 0">
            共 {{ communityContributions?.contributions?.length }} 个活跃贡献
          </span>
        </div>

        <div class="community-list" v-if="communityContributions?.contributions?.length > 0">
          <div class="community-item" v-for="contrib in communityContributions.contributions.slice(0, 10)" :key="contrib.id">
            <div class="community-icon" :style="{ backgroundColor: contrib.color + '20' }">
              <span :style="{ color: contrib.color }">{{ contrib.planet_icon }}</span>
            </div>
            <div class="community-info">
              <div class="community-name">{{ contrib.name }}</div>
              <div class="community-time">剩余 {{ contrib.remaining_minutes }} 分钟</div>
            </div>
            <div class="community-energy">
              +{{ Math.round(contrib.energy_amount) }}
            </div>
          </div>
        </div>

        <div class="empty-state" v-else>
          <el-icon size="48"><MagicStick /></el-icon>
          <h3>暂无活跃贡献</h3>
          <p>成为第一个为社区注入能量的人吧</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection, MagicStick, Sunny, Location
} from '@element-plus/icons-vue'
import { energyCommunityApi } from '@/api'

const router = useRouter()

const selectedType = ref(null)
const injectScope = ref('global')
const currentUserCity = ref(null)
const availableContributions = ref([])
const myActiveContributions = ref([])
const communityContributions = ref(null)
const communityBonus = ref(null)
const injecting = ref(false)

const DIMENSION_CONFIG = {
  communication: { name: '沟通' },
  social: { name: '社交' },
  career: { name: '事业' },
  wealth: { name: '财运' },
  emotion: { name: '情绪' }
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

const selectedContribution = computed(() => {
  return availableContributions.value.find(c => c.type === selectedType.value)
})

const getDimensionName = (dim) => DIMENSION_CONFIG[dim]?.name || dim

const getRemainingPercentage = (contrib) => {
  if (!contrib.duration_minutes || !contrib.remaining_minutes) return 0
  return Math.round((contrib.remaining_minutes / contrib.duration_minutes) * 100)
}

const selectContribution = (contrib) => {
  selectedType.value = contrib.type
}

const loadData = async () => {
  try {
    const [contribs, myContribs, communityData] = await Promise.all([
      energyCommunityApi.getAvailableContributions(),
      energyCommunityApi.getMyContributions(true),
      energyCommunityApi.getActiveContributions('global', currentUserCity.value)
    ])
    
    availableContributions.value = contribs?.contributions || []
    myActiveContributions.value = myContribs?.contributions || []
    communityContributions.value = communityData
    communityBonus.value = communityData?.bonus
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const handleInject = async () => {
  if (!selectedType.value) {
    ElMessage.warning('请选择要注入的能量类型')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确认注入「${selectedContribution.value?.name}」？将消耗 ${selectedContribution.value?.cost_stardust} 星尘`,
      '确认注入',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  
  injecting.value = true
  try {
    const result = await energyCommunityApi.makeContribution({
      contribution_type: selectedType.value,
      scope: injectScope.value,
      city: injectScope.value === 'local' ? currentUserCity.value : null
    })
    
    if (result.success) {
      ElMessage.success('能量注入成功！社区能量获得加成')
      selectedType.value = null
      loadData()
    }
  } catch (error) {
    console.error('注入失败:', error)
    ElMessage.error('注入失败，请重试')
  } finally {
    injecting.value = false
  }
}

const handleCancel = async (contrib) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消这个能量贡献吗？剩余时间将不会返还星尘。',
      '确认取消',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }
  
  try {
    await energyCommunityApi.deactivateContribution(contrib.id)
    ElMessage.success('已取消能量贡献')
    loadData()
  } catch (error) {
    console.error('取消失败:', error)
    ElMessage.error('取消失败，请重试')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.contribute-page {
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

.contribute-main {
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

.bonus-section {
  margin-bottom: 24px;
}

.bonus-card {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.1));
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 24px;

  .bonus-icon {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(236, 72, 153, 0.3));
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a78bfa;
  }

  .bonus-info {
    .bonus-title {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 4px;
    }

    .bonus-value {
      font-size: 36px;
      font-weight: 800;
      background: linear-gradient(135deg, #a78bfa, #f472b6);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }

  .bonus-stats {
    margin-left: auto;
    display: flex;
    gap: 32px;

    .stat-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .stat-label {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.5);
      }

      .stat-value {
        font-size: 20px;
        font-weight: 700;
        color: #a78bfa;
      }
    }
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }

  .section-hint {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.4);
  }
}

.contribution-types {
  margin-bottom: 24px;

  .contributions-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}

.contribution-card {
  background: rgba(255, 255, 255, 0.03);
  border: 2px solid transparent;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(167, 139, 250, 0.3);
  }

  &.selected {
    background: rgba(167, 139, 250, 0.1);
    border-color: #a78bfa;
  }

  .contrib-icon {
    width: 52px;
    height: 52px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;

    .icon-text {
      font-size: 24px;
    }
  }

  .contrib-info {
    margin-bottom: 12px;

    .contrib-name {
      font-size: 16px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
      margin-bottom: 4px;
    }

    .contrib-desc {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
      margin-bottom: 6px;
    }

    .contrib-targets {
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 4px;

      .target-label {
        color: rgba(255, 255, 255, 0.4);
      }

      .target-dims {
        color: rgba(255, 255, 255, 0.6);
      }
    }
  }

  .contrib-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);

    .meta-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);

      .meta-icon {
        font-size: 14px;
      }

      &.cost {
        margin-left: auto;
        color: #f59e0b;
        font-weight: 600;
      }
    }
  }
}

.inject-section {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
}

.scope-selector {
  margin-bottom: 20px;

  .selector-label {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 12px;
    display: block;
  }

  :deep(.el-radio-group) {
    display: flex;
    gap: 8px;
  }

  :deep(.el-radio-button__inner) {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.7);
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 6px;
    border-radius: 10px !important;
  }

  :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
    background: rgba(167, 139, 250, 0.2);
    border-color: #a78bfa;
    color: #a78bfa;
  }
}

.inject-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.inject-preview {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;

  .preview-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    margin-bottom: 12px;
  }

  .preview-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .preview-info {
    .preview-name {
      font-size: 15px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
      margin-bottom: 2px;
    }

    .preview-detail {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;

      .preview-energy {
        color: #22c55e;
      }

      .preview-separator {
        color: rgba(255, 255, 255, 0.2);
      }

      .preview-cost {
        color: #f59e0b;
      }
    }
  }
}

.inject-btn {
  min-width: 140px;
  height: 48px;
  background: linear-gradient(135deg, #ec4899, #a78bfa);
  border: none;
  font-size: 15px;
  font-weight: 600;

  &:hover {
    background: linear-gradient(135deg, #db2777, #8b5cf6);
  }
}

.active-contributions-section,
.community-contributions-section {
  margin-bottom: 24px;

  .active-list,
  .community-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .active-item,
  .community-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;

    .active-icon,
    .community-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: 20px;
    }

    .active-info,
    .community-info {
      flex: 1;

      .active-name,
      .community-name {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 2px;
      }

      .active-time,
      .community-time {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);

        .separator {
          color: rgba(255, 255, 255, 0.2);
        }
      }
    }

    .active-progress {
      flex-shrink: 0;
    }

    .community-energy {
      font-size: 18px;
      font-weight: 700;
      color: #22c55e;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);

  .el-icon {
    margin-bottom: 12px;
    opacity: 0.5;
  }

  h3 {
    font-size: 15px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 4px;
  }

  p {
    font-size: 12px;
    margin: 0;
  }
}

@media (max-width: 768px) {
  .contributions-grid {
    grid-template-columns: 1fr !important;
  }

  .bonus-card {
    flex-direction: column;
    text-align: center;

    .bonus-stats {
      margin-left: 0;
      margin-top: 16px;
    }
  }

  .inject-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .inject-btn {
    width: 100%;
  }
}
</style>
