<template>
  <div class="report-shop-container">
    <div class="shop-header">
      <div class="header-left">
        <span class="shop-icon">📄</span>
        <span class="shop-title">星盘报告商城</span>
      </div>
      <div class="header-info" v-if="isVip">
        <span class="vip-free-info">
          ⭐ 本月免费报告剩余 {{ freeReportsRemaining }} 份
        </span>
      </div>
    </div>

    <div class="shop-tabs">
      <div
        class="tab-item"
        :class="{ 'tab-active': activeTab === 'all' }"
        @click="activeTab = 'all'"
      >
        全部报告
      </div>
      <div
        class="tab-item"
        :class="{ 'tab-active': activeTab === 'purchased' }"
        @click="activeTab = 'purchased'"
      >
        已购买
      </div>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'all'" class="all-reports">
        <div class="reports-grid">
          <div
            class="report-card"
            v-for="report in reports"
            :key="report.id"
          >
            <div class="report-header" :class="'report-' + report.category">
              <span class="report-icon">{{ report.icon }}</span>
              <span class="report-category">{{ getCategoryName(report.category) }}</span>
            </div>
            <div class="report-body">
              <h3 class="report-title">{{ report.name }}</h3>
              <p class="report-desc">{{ report.description }}</p>
              <div class="report-features">
                <span class="feature-tag" v-for="(tag, index) in report.tags" :key="index">
                  {{ tag }}
                </span>
              </div>
            </div>
            <div class="report-footer">
              <div class="report-price">
                <span class="price-symbol">¥</span>
                <span class="price-value" :class="{ 'price-discount': report.discount_price }">
                  {{ report.discount_price || report.price }}
                </span>
                <span class="price-original" v-if="report.discount_price">
                  ¥{{ report.price }}
                </span>
              </div>
              <el-button
                type="primary"
                size="small"
                :disabled="isReportPurchased(report)"
                @click="purchaseReport(report)"
              >
                {{ isReportPurchased(report) ? '已购买' : (useFreeReportAvailable(report) ? '免费领取' : '立即购买') }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'purchased'" class="purchased-reports">
        <el-empty v-if="purchasedReports.length === 0" description="您还没有购买过报告">
          <template #image>
            <span class="empty-emoji">📄</span>
          </template>
        </el-empty>
        <div class="purchased-list" v-else>
          <div class="purchased-item" v-for="item in purchasedReports" :key="item.id">
            <div class="purchased-icon">
              <span class="report-icon">{{ getReportIcon(item.product_key) }}</span>
            </div>
            <div class="purchased-info">
              <h4 class="purchased-title">{{ item.product_name }}</h4>
              <div class="purchased-meta">
                <span class="purchase-date">购买时间：{{ formatDate(item.purchased_at) }}</span>
                <span class="view-count">已查看 {{ item.view_count || 0 }} 次</span>
              </div>
              <div class="purchased-status" v-if="item.expires_at">
                <span :class="item.is_expired ? 'expired' : 'valid'">
                  {{ item.is_expired ? '已过期' : `有效期至 ${formatDate(item.expires_at)}` }}
                </span>
              </div>
            </div>
            <div class="purchased-actions">
              <el-button
                type="primary"
                size="small"
                :disabled="item.is_expired"
                @click="viewReport(item)"
              >
                {{ item.is_expired ? '已过期' : '查看报告' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <el-dialog
    v-model="purchaseDialogVisible"
    title="购买确认"
    width="400px"
  >
    <div class="purchase-confirm">
      <div class="confirm-header">
        <span class="confirm-icon">{{ selectedReport?.icon }}</span>
        <div class="confirm-info">
          <h3 class="confirm-title">{{ selectedReport?.name }}</h3>
          <p class="confirm-desc">{{ selectedReport?.description }}</p>
        </div>
      </div>

      <div class="confirm-price">
        <div class="price-row" v-if="useFreeReportForSelected">
          <span class="free-label">使用免费报告权益</span>
          <span class="free-value">0元</span>
        </div>
        <div class="price-row" v-else>
          <span class="price-label">应付金额</span>
          <div class="price-value-wrapper">
            <span class="price-symbol">¥</span>
            <span class="price-value">{{ selectedReport?.discount_price || selectedReport?.price }}</span>
          </div>
        </div>
      </div>

      <div class="confirm-notice" v-if="!isLoggedIn">
        <el-alert
          title="您还未登录"
          type="warning"
          :closable="false"
          show-icon
        >
          登录后即可购买报告，已登录用户请忽略此提示
        </el-alert>
      </div>
    </div>

    <template #footer>
      <el-button @click="purchaseDialogVisible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="purchasing"
        @click="confirmPurchase"
      >
        确认{{ useFreeReportForSelected ? '领取' : '购买' }}
      </el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="reportViewerVisible"
    title="查看报告"
    width="800px"
    class="report-viewer-dialog"
  >
    <div class="report-viewer" v-if="currentReportContent">
      <div class="viewer-header">
        <h2 class="viewer-title">{{ currentReportContent.title }}</h2>
        <span class="viewer-subtitle">{{ currentReportContent.subtitle }}</span>
      </div>
      <div class="viewer-content">
        <div class="content-section" v-for="(section, index) in currentReportContent.sections" :key="index">
          <h3 class="section-title">{{ section.title }}</h3>
          <div class="section-content">
            <p v-for="(para, pIndex) in section.paragraphs" :key="pIndex" class="section-para">
              {{ para }}
            </p>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="viewer-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <p>加载报告内容...</p>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { reportShopApi, paymentApi } from '@/api'

const props = defineProps({
  isVip: {
    type: Boolean,
    default: false
  },
  freeReportsRemaining: {
    type: Number,
    default: 0
  },
  isLoggedIn: {
    type: Boolean,
    default: false
  }
})

const activeTab = ref('all')
const reports = ref([])
const purchasedReports = ref([])

const purchaseDialogVisible = ref(false)
const selectedReport = ref(null)
const purchasing = ref(false)

const reportViewerVisible = ref(false)
const currentReportContent = ref(null)
const viewingPurchaseId = ref(null)

const useFreeReportForSelected = computed(() => {
  return props.isVip && props.freeReportsRemaining > 0 && selectedReport.value?.is_allow_free
})

const useFreeReportAvailable = (report) => {
  return props.isVip && props.freeReportsRemaining > 0 && report.is_allow_free
}

onMounted(async () => {
  await loadReports()
  await loadPurchasedReports()
})

function getCategoryName(category) {
  const names = {
    'single': '单人星盘',
    'synastry': '双人合盘',
    'forecast': '年度预测',
    'group': '群组分析'
  }
  return names[category] || category
}

function getReportIcon(productKey) {
  const icons = {
    'deep_single_chart': '🔮',
    'synastry_analysis': '💕',
    'yearly_forecast': '📅',
    'group_energy': '👥'
  }
  return icons[productKey] || '📄'
}

async function loadReports() {
  try {
    const response = await reportShopApi.getShop()
    reports.value = response.products || []
  } catch (error) {
    console.error('加载报告失败:', error)
  }
}

async function loadPurchasedReports() {
  if (!props.isLoggedIn) return
  try {
    const response = await reportShopApi.getPurchased(20, 0)
    purchasedReports.value = response.items || []
  } catch (error) {
    console.error('加载已购买报告失败:', error)
  }
}

function isReportPurchased(report) {
  return purchasedReports.value.some(p => 
    p.product_key === report.product_key && !p.is_expired
  )
}

function purchaseReport(report) {
  if (isReportPurchased(report)) {
    ElMessage.info('您已经购买过该报告')
    return
  }
  selectedReport.value = report
  purchaseDialogVisible.value = true
}

async function confirmPurchase() {
  purchasing.value = true
  try {
    const useFree = useFreeReportForSelected.value
    
    const response = await reportShopApi.purchaseReport({
      product_id: selectedReport.value.id,
      use_free_vip: useFree
    })

    if (useFree) {
      ElMessage.success('报告领取成功！')
      purchaseDialogVisible.value = false
      await loadPurchasedReports()
      return
    }

    if (response.payment_url) {
      const win = window.open(response.payment_url, '_blank', 'width=600,height=700')
      
      const checkInterval = setInterval(async () => {
        try {
          const orderResult = await paymentApi.getOrder(response.order_no)
          if (orderResult.status === 'paid') {
            clearInterval(checkInterval)
            ElMessage.success('购买成功！')
            purchaseDialogVisible.value = false
            await loadPurchasedReports()
          }
        } catch (e) {
          console.error('检查订单状态失败:', e)
        }
      }, 3000)
      
      setTimeout(() => {
        clearInterval(checkInterval)
      }, 120000)
    }
  } catch (error) {
    console.error('购买失败:', error)
    ElMessage.error(error.response?.data?.detail || '购买失败，请稍后重试')
  } finally {
    purchasing.value = false
  }
}

async function viewReport(item) {
  viewingPurchaseId.value = item.id
  reportViewerVisible.value = true
  currentReportContent.value = null
  
  try {
    const response = await reportShopApi.viewReport(item.id)
    
    currentReportContent.value = {
      title: response.product_name,
      subtitle: response.ai_analysis?.subtitle || '星盘深度分析报告',
      sections: response.ai_analysis?.sections || generateMockSections(response.product_key)
    }
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error('加载报告失败')
    currentReportContent.value = {
      title: item.product_name,
      subtitle: '星盘深度分析报告',
      sections: generateMockSections(item.product_key)
    }
  }
}

function generateMockSections(productKey) {
  const sectionsMap = {
    'deep_single_chart': [
      {
        title: '🌞 太阳星座深度解析',
        paragraphs: [
          '您的太阳星座代表着您的核心自我、人生目标和基本性格特征。太阳在您的星盘中的位置揭示了您最真实的自我表达。',
          '通过深度分析，我们可以看到您在追求目标时展现出的独特能量模式，以及您在社交场合中自然流露的个性特质。',
          '理解太阳星座的力量，可以帮助您更好地认识自己，在人生的道路上做出更符合内心真实需求的选择。'
        ]
      },
      {
        title: '🌙 月亮星座情感剖析',
        paragraphs: [
          '月亮星座揭示了您的内心世界、情感需求和潜意识反应。它代表着您在情感层面如何感知和回应世界。',
          '您的月亮位置影响着您对安全感的需求、对亲密关系的态度，以及在压力情境下的应对机制。',
          '深入了解月亮星座，可以帮助您更好地理解自己的情绪模式，建立更健康的情感关系。'
        ]
      },
      {
        title: '⭐ 上升星座人生面具',
        paragraphs: [
          '上升星座代表您给他人的第一印象，以及您在面对外部世界时展现的"面具"或保护色。',
          '它影响着您的行为方式、社交风格，以及他人对您的初始认知。上升星座往往决定了您在新环境中的表现模式。',
          '认识到上升星座的影响，可以帮助您更好地理解自己在不同情境下的行为差异，以及他人眼中的您。'
        ]
      },
      {
        title: '🔗 关键相位能量整合',
        paragraphs: [
          '星盘中的相位关系展示了不同行星能量之间的互动模式。和谐相位带来能量的顺畅流动，挑战相位则激发成长的动力。',
          '通过分析您星盘中的关键相位，我们可以看到您性格中不同面向之间的相互作用，以及可能存在的内在冲突或优势组合。',
          '理解这些相位的意义，可以帮助您更好地整合自身的能量，将挑战转化为成长的契机。'
        ]
      }
    ],
    'synastry_analysis': [
      {
        title: '💕 合盘基础能量',
        paragraphs: [
          '双人合盘分析通过比较两个人的星盘，揭示双方关系中的能量互动模式、互补之处和潜在挑战。',
          '太阳、月亮、金星等个人行星之间的相位关系，是理解两人情感连接的关键。',
          '通过合盘分析，您可以更好地理解这段关系的本质，以及如何在其中实现双方的成长。'
        ]
      },
      {
        title: '💫 情感契合度',
        paragraphs: [
          '情感契合度主要通过月亮、金星和火星的位置来分析。月亮代表情感需求，金星代表爱的表达，火星代表行动力和欲望。',
          '当双方的月亮位置和谐时，彼此更容易理解对方的情感需求；金星的良好互动则带来浪漫和吸引力。',
          '理解这些能量的互动，可以帮助双方更好地满足彼此的情感需求，建立更深的情感连接。'
        ]
      },
      {
        title: '⚡ 沟通与互动模式',
        paragraphs: [
          '水星在合盘中的位置影响着双方的沟通方式和思维模式。良好的水星相位促进理解和表达，困难的相位则可能带来误解。',
          '第七宫（伙伴关系宫）的行星和交点也是分析关系长期发展的重要参考。',
          '认识到沟通模式的特点，可以帮助双方找到更有效的交流方式，减少不必要的误会。'
        ]
      }
    ],
    'yearly_forecast': [
      {
        title: '📅 年度主题预测',
        paragraphs: [
          '年度预测基于太阳返照盘和主要行星运行轨迹，分析未来一年您人生中可能遇到的关键主题和发展机遇。',
          '通过观察木星、土星等外行星的位置变化，我们可以看到这一年中哪些生活领域将迎来重大变化。',
          '了解年度主题，可以帮助您在正确的时间做出正确的决策，把握机遇，应对挑战。'
        ]
      },
      {
        title: '🌊 季度运势分析',
        paragraphs: [
          '将年度运势划分为四个季度，可以更清晰地看到不同时期的能量变化和机遇窗口。',
          '每个季度都有其独特的能量特征，有的适合积极行动，有的适合反思规划。',
          '理解季度能量的变化，可以帮助您更好地规划时间和精力，在合适的时机采取行动。'
        ]
      },
      {
        title: '🌟 关键机遇期',
        paragraphs: [
          '通过分析木星、金星等吉星的运行轨迹，我们可以识别出年度中最有利于发展的机遇窗口期。',
          '这些时期可能适合开展新项目、建立新关系、或者推动重要事务的进展。',
          '同时，我们也会关注土星、冥王星等行星带来的挑战期，帮助您做好准备。'
        ]
      }
    ],
    'group_energy': [
      {
        title: '👥 群组能量场域',
        paragraphs: [
          '群组能量分析通过整合多位成员的星盘信息，揭示整个群体的能量特征、互动模式和整体动力。',
          '一个群体的能量场域由所有成员的星盘共同塑造，既有协同增效的部分，也有需要调和的冲突。',
          '理解群组能量，可以帮助团队成员更好地协作，发挥各自的优势，共同达成目标。'
        ]
      },
      {
        title: '🎯 团队优势识别',
        paragraphs: [
          '通过分析每位成员的星盘特点，我们可以识别出团队中自然涌现的优势领域。',
          '有的成员可能在创意方面表现突出，有的可能擅长执行和落地，有的则善于协调和沟通。',
          '认识到团队的优势分布，可以帮助更合理地分配角色和任务，实现最佳的团队效能。'
        ]
      },
      {
        title: '⚖️ 潜在挑战与调和',
        paragraphs: [
          '每个群体都可能存在能量冲突的地方。这些冲突可能表现为沟通障碍、目标分歧或性格摩擦。',
          '通过星盘分析，我们可以提前识别这些潜在的挑战点，并提供调和建议。',
          '理解这些挑战的能量本质，可以帮助团队成员以更包容的心态看待差异，找到共同前进的方式。'
        ]
      }
    ]
  }
  
  return sectionsMap[productKey] || [
    {
      title: '📄 报告内容',
      paragraphs: [
        '这是一份完整的星盘分析报告，包含了您星盘中的关键信息和深度解读。',
        '报告内容基于专业占星学理论，为您提供个性化的星盘洞察。'
      ]
    }
  ]
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.report-shop-container {
  background: linear-gradient(145deg, rgba(20, 20, 50, 0.95), rgba(15, 15, 35, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  overflow: hidden;
}

.shop-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.1), transparent);
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.shop-icon {
  font-size: 1.2rem;
}

.shop-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.vip-free-info {
  padding: 4px 12px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
}

.shop-tabs {
  display: flex;
  padding: 12px 20px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.tab-item {
  padding: 10px 20px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
  
  &:hover {
    color: rgba(255, 255, 255, 0.8);
  }
  
  &.tab-active {
    color: #a78bfa;
    border-bottom-color: #a78bfa;
  }
}

.tab-content {
  padding: 20px;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.report-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.3);
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
  }
}

.report-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  
  &.report-single {
    background: linear-gradient(90deg, rgba(167, 139, 250, 0.2), transparent);
  }
  
  &.report-synastry {
    background: linear-gradient(90deg, rgba(244, 114, 182, 0.2), transparent);
  }
  
  &.report-forecast {
    background: linear-gradient(90deg, rgba(251, 191, 36, 0.2), transparent);
  }
  
  &.report-group {
    background: linear-gradient(90deg, rgba(96, 165, 250, 0.2), transparent);
  }
}

.report-icon {
  font-size: 1.3rem;
}

.report-category {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.report-body {
  padding: 16px;
}

.report-title {
  margin: 0 0 8px;
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.report-desc {
  margin: 0 0 12px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.5;
}

.report-features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.feature-tag {
  padding: 2px 8px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 4px;
  font-size: 0.7rem;
  color: #a78bfa;
}

.report-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.1);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.report-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.price-symbol {
  font-size: 0.8rem;
  color: #a78bfa;
}

.price-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #a78bfa;
  
  &.price-discount {
    color: #fbbf24;
  }
}

.price-original {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.3);
  text-decoration: line-through;
}

.purchased-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.purchased-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.purchased-icon {
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
}

.purchased-info {
  flex: 1;
  min-width: 0;
}

.purchased-title {
  margin: 0 0 6px;
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.purchased-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 6px;
}

.purchased-status {
  font-size: 0.75rem;
  
  .valid {
    color: #4ade80;
  }
  
  .expired {
    color: #f87171;
  }
}

.purchased-actions {
  flex-shrink: 0;
}

.empty-emoji {
  font-size: 3rem;
}

.purchase-confirm {
  .confirm-header {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
    background: rgba(139, 92, 246, 0.05);
    border-radius: 12px;
    margin-bottom: 20px;
  }
  
  .confirm-icon {
    font-size: 2.5rem;
  }
  
  .confirm-info {
    flex: 1;
  }
  
  .confirm-title {
    margin: 0 0 4px;
    font-size: 1.1rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .confirm-desc {
    margin: 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .confirm-price {
    padding: 16px;
    background: rgba(251, 191, 36, 0.05);
    border-radius: 12px;
    margin-bottom: 16px;
  }
  
  .price-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .price-label,
  .free-label {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .free-value {
    font-size: 1.2rem;
    font-weight: 700;
    color: #4ade80;
  }
  
  .price-value-wrapper {
    display: flex;
    align-items: baseline;
    gap: 2px;
  }
  
  .price-symbol {
    font-size: 0.9rem;
    color: #a78bfa;
  }
  
  .price-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #a78bfa;
  }
}

.report-viewer {
  .viewer-header {
    text-align: center;
    padding: 20px;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  }
  
  .viewer-title {
    margin: 0 0 8px;
    font-size: 1.5rem;
    font-weight: 700;
    color: #fff;
  }
  
  .viewer-subtitle {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .viewer-content {
    max-height: 500px;
    overflow-y: auto;
    padding: 0 20px;
  }
  
  .content-section {
    margin-bottom: 24px;
  }
  
  .section-title {
    margin: 0 0 12px;
    font-size: 1.1rem;
    font-weight: 600;
    color: #a78bfa;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  }
  
  .section-para {
    margin: 0 0 12px;
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.8;
    text-align: justify;
  }
}

.viewer-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
  
  .loading-icon {
    font-size: 2rem;
    margin-bottom: 16px;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .reports-grid {
    grid-template-columns: 1fr;
  }
}
</style>