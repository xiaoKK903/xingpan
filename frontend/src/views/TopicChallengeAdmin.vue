<template>
  <div class="topic-admin-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">话题挑战管理</span>
          <div class="header-actions">
            <el-select 
              v-model="filterStatus" 
              placeholder="筛选状态" 
              clearable
              style="width: 150px"
              @change="loadTopics"
            >
              <el-option label="全部状态" value="" />
              <el-option label="草稿" value="draft" />
              <el-option label="进行中" value="active" />
              <el-option label="已结束" value="ended" />
              <el-option label="已归档" value="archived" />
            </el-select>
            <el-button @click="refreshTopics">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="primary" @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              新建话题
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="topicList"
        style="width: 100%"
        empty-text="暂无话题数据"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="话题标题" min-width="180">
          <template #default="{ row }">
            <div class="topic-info">
              <span class="topic-title">{{ row.title }}</span>
              <el-tag size="small" type="warning" effect="dark" class="topic-tag">{{ row.topic_tag }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" :effect="'dark'">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="参与数据" width="150">
          <template #default="{ row }">
            <div class="stats-info">
              <span class="stat-item">
                <el-icon><User /></el-icon>
                {{ row.participant_count || 0 }} 人
              </span>
              <span class="stat-item">
                <el-icon><Document /></el-icon>
                {{ row.post_count || 0 }} 帖
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">
              详情
            </el-button>
            <el-button type="primary" link size="small" @click="openEditDialog(row)">
              编辑
            </el-button>
            <template v-if="row.status === 'draft'">
              <el-button type="success" link size="small" @click="changeStatus(row, 'active')">
                上线
              </el-button>
            </template>
            <template v-else-if="row.status === 'active'">
              <el-button type="warning" link size="small" @click="changeStatus(row, 'ended')">
                下线
              </el-button>
            </template>
            <template v-else-if="row.status === 'ended' && !row.settled_at">
              <el-button type="success" link size="small" @click="settleRewards(row)">
                结算奖励
              </el-button>
              <el-button type="info" link size="small" @click="changeStatus(row, 'archived')">
                归档
              </el-button>
            </template>
            <template v-else-if="row.status === 'ended' && row.settled_at">
              <el-tag size="small" type="success">已结算</el-tag>
              <el-button type="info" link size="small" @click="changeStatus(row, 'archived')">
                归档
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <el-dialog 
      v-model="formDialogVisible" 
      :title="isEdit ? '编辑话题' : '新建话题'" 
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="formRef"
        :model="topicForm" 
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="话题标题" prop="title">
          <el-input v-model="topicForm.title" placeholder="请输入话题标题" maxlength="100" />
        </el-form-item>
        <el-form-item label="话题标签" prop="topic_tag">
          <el-input v-model="topicForm.topic_tag" placeholder="如：#我的星盘缺什么#" maxlength="50" />
        </el-form-item>
        <el-form-item label="话题描述" prop="description">
          <el-input 
            v-model="topicForm.description" 
            type="textarea"
            :rows="3"
            placeholder="请输入话题描述"
            maxlength="500"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="topicForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="topicForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">奖励配置</el-divider>
        <el-form-item label="奖励规则">
          <div class="reward-config">
            <div class="reward-row" v-for="(reward, index) in topicForm.reward_config" :key="index">
              <span class="reward-rank">第 {{ index + 1 }} 名：</span>
              <el-select v-model="reward.type" placeholder="奖励类型" style="width: 150px">
                <el-option label="星尘" value="stardust" />
                <el-option label="VIP天数" value="vip_days" />
                <el-option label="免费报告" value="free_report" />
              </el-select>
              <el-input-number 
                v-model="reward.value" 
                :min="1" 
                :max="10000"
                placeholder="数量"
                style="width: 120px"
              />
              <span class="reward-unit">
                {{ reward.type === 'stardust' ? '星尘' : reward.type === 'vip_days' ? '天' : '份' }}
              </span>
              <el-button 
                v-if="index >= 3"
                type="danger" 
                link 
                size="small"
                @click="removeReward(index)"
              >
                删除
              </el-button>
            </div>
            <el-button 
              v-if="topicForm.reward_config.length < 10"
              type="primary" 
              link 
              size="small"
              @click="addReward"
            >
              <el-icon><Plus /></el-icon>
              添加奖励
            </el-button>
          </div>
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大参与人数">
              <el-input-number 
                v-model="topicForm.max_participants" 
                :min="0" 
                :max="100000"
                placeholder="不限则留空"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序权重">
              <el-input-number 
                v-model="topicForm.sort_order" 
                :min="0" 
                :max="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="置顶推荐">
          <el-switch v-model="topicForm.is_featured" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitTopic">确认</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="detailDialogVisible" title="话题详情" width="800px">
      <div v-if="currentTopic" class="topic-detail">
        <div class="detail-section">
          <h4>基本信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="话题ID">{{ currentTopic.id }}</el-descriptions-item>
            <el-descriptions-item label="话题标题">{{ currentTopic.title }}</el-descriptions-item>
            <el-descriptions-item label="话题标签">
              <el-tag size="small" type="warning" effect="dark">{{ currentTopic.topic_tag }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <el-tag :type="getStatusType(currentTopic.status)" effect="dark">
                {{ getStatusLabel(currentTopic.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatDateTime(currentTopic.start_time) }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ formatDateTime(currentTopic.end_time) }}</el-descriptions-item>
            <el-descriptions-item label="参与人数">{{ currentTopic.participant_count || 0 }} 人</el-descriptions-item>
            <el-descriptions-item label="帖子数量">{{ currentTopic.post_count || 0 }} 帖</el-descriptions-item>
            <el-descriptions-item label="结算时间" :span="2">
              {{ currentTopic.settled_at ? formatDateTime(currentTopic.settled_at) : '未结算' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="detail-section" v-if="currentTopic.description">
          <h4>话题描述</h4>
          <div class="description-content">{{ currentTopic.description }}</div>
        </div>
        
        <div class="detail-section" v-if="currentTopic.reward_config && currentTopic.reward_config.length > 0">
          <h4>奖励配置</h4>
          <el-table :data="currentTopic.reward_config" size="small" style="width: 100%">
            <el-table-column label="排名" width="100">
              <template #default="{ $index }">
                第 {{ $index + 1 }} 名
              </template>
            </el-table-column>
            <el-table-column label="奖励类型">
              <template #default="{ row }">
                {{ row.type === 'stardust' ? '星尘' : row.type === 'vip_days' ? 'VIP天数' : '免费报告' }}
              </template>
            </el-table-column>
            <el-table-column label="奖励数量">
              <template #default="{ row }">
                {{ row.value }} {{ row.type === 'stardust' ? '星尘' : row.type === 'vip_days' ? '天' : '份' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div class="detail-section" v-if="currentTopic.user_participation">
          <h4>我的参与记录</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="排名">
              #{{ currentTopic.user_participation.final_rank || '未结算' }}
            </el-descriptions-item>
            <el-descriptions-item label="热度值">
              {{ currentTopic.user_participation.hot_score || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="奖励领取">
              <el-tag :type="currentTopic.user_participation.reward_claimed ? 'success' : 'info'" effect="dark">
                {{ currentTopic.user_participation.reward_claimed ? '已领取' : '未领取' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="奖励类型">
              {{ currentTopic.user_participation.reward_type || '无' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { topicChallengeApi } from '@/api'

const loading = ref(false)
const topicList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const formDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const settling = ref(false)

const detailDialogVisible = ref(false)
const currentTopic = ref(null)

const defaultRewardConfig = [
  { type: 'stardust', value: 1000 },
  { type: 'stardust', value: 500 },
  { type: 'stardust', value: 200 },
]

const topicForm = reactive({
  id: null,
  title: '',
  topic_tag: '',
  description: '',
  start_time: null,
  end_time: null,
  reward_config: [...defaultRewardConfig],
  max_participants: null,
  sort_order: 0,
  is_featured: false,
})

const formRules = {
  title: [{ required: true, message: '请输入话题标题', trigger: 'blur' }],
  topic_tag: [{ required: true, message: '请输入话题标签', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
}

function formatDateTime(timeStr) {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  if (isNaN(date.getTime())) {
    return '-'
  }
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

function getStatusType(status) {
  const typeMap = {
    draft: 'info',
    active: 'success',
    ended: 'warning',
    archived: 'info',
  }
  return typeMap[status] || 'info'
}

function getStatusLabel(status) {
  const labelMap = {
    draft: '草稿',
    active: '进行中',
    ended: '已结束',
    archived: '已归档',
  }
  return labelMap[status] || status
}

async function loadTopics() {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    
    const result = await topicChallengeApi.getTopicList(params)
    topicList.value = result.topics || []
    total.value = result.total_count || 0
  } catch (error) {
    console.error('加载话题列表失败:', error)
    ElMessage.error(error.message || '加载话题列表失败')
  } finally {
    loading.value = false
  }
}

function refreshTopics() {
  currentPage.value = 1
  loadTopics()
}

function handleSizeChange(val) {
  pageSize.value = val
  loadTopics()
}

function handleCurrentChange(val) {
  currentPage.value = val
  loadTopics()
}

function resetForm() {
  topicForm.id = null
  topicForm.title = ''
  topicForm.topic_tag = ''
  topicForm.description = ''
  topicForm.start_time = null
  topicForm.end_time = null
  topicForm.reward_config = [...defaultRewardConfig]
  topicForm.max_participants = null
  topicForm.sort_order = 0
  topicForm.is_featured = false
}

function openCreateDialog() {
  resetForm()
  isEdit.value = false
  formDialogVisible.value = true
}

function openEditDialog(row) {
  resetForm()
  isEdit.value = true
  topicForm.id = row.id
  topicForm.title = row.title
  topicForm.topic_tag = row.topic_tag
  topicForm.description = row.description || ''
  topicForm.start_time = row.start_time ? new Date(row.start_time) : null
  topicForm.end_time = row.end_time ? new Date(row.end_time) : null
  topicForm.reward_config = row.reward_config ? JSON.parse(JSON.stringify(row.reward_config)) : [...defaultRewardConfig]
  topicForm.max_participants = row.max_participants || null
  topicForm.sort_order = row.sort_order || 0
  topicForm.is_featured = row.is_featured || false
  formDialogVisible.value = true
}

function addReward() {
  if (topicForm.reward_config.length < 10) {
    topicForm.reward_config.push({ type: 'stardust', value: 100 })
  }
}

function removeReward(index) {
  if (index >= 3) {
    topicForm.reward_config.splice(index, 1)
  }
}

async function submitTopic() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const data = {
        title: topicForm.title,
        topic_tag: topicForm.topic_tag,
        description: topicForm.description || null,
        start_time: topicForm.start_time ? topicForm.start_time.toISOString() : null,
        end_time: topicForm.end_time ? topicForm.end_time.toISOString() : null,
        reward_config: JSON.parse(JSON.stringify(topicForm.reward_config)),
        max_participants: topicForm.max_participants || null,
        sort_order: topicForm.sort_order,
        is_featured: topicForm.is_featured,
      }
      
      if (isEdit.value) {
        await topicChallengeApi.updateTopic(topicForm.id, data)
        ElMessage.success('更新成功')
      } else {
        await topicChallengeApi.createTopic(data)
        ElMessage.success('创建成功')
      }
      
      formDialogVisible.value = false
      loadTopics()
    } catch (error) {
      console.error('提交失败:', error)
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function changeStatus(row, targetStatus) {
  const actionText = targetStatus === 'active' ? '上线' : targetStatus === 'ended' ? '下线' : '归档'
  try {
    await ElMessageBox.confirm(
      `确定要${actionText}话题 "${row.title}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await topicChallengeApi.updateTopic(row.id, { status: targetStatus })
    ElMessage.success(`${actionText}成功`)
    loadTopics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('状态更新失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  }
}

async function settleRewards(row) {
  if (settling.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要结算话题 "${row.title}" 的奖励吗？结算后将根据排行榜发放奖励。`,
      '确认结算',
      {
        confirmButtonText: '确定结算',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    settling.value = true
    const result = await topicChallengeApi.settleRewards(row.id)
    ElMessage.success(`结算成功！共结算 ${result.settled_count} 条记录`)
    loadTopics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('结算失败:', error)
      ElMessage.error(error.message || '结算失败')
    }
  } finally {
    settling.value = false
  }
}

function viewDetail(row) {
  currentTopic.value = row
  detailDialogVisible.value = true
}

onMounted(() => {
  loadTopics()
})
</script>

<style lang="scss" scoped>
.topic-admin-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .title {
      font-size: 16px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .topic-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .topic-title {
      color: rgba(255, 255, 255, 0.9);
    }
    
    .topic-tag {
      width: fit-content;
    }
  }
  
  .stats-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7);
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .reward-config {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .reward-row {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .reward-rank {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.8);
        min-width: 70px;
      }
      
      .reward-unit {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.6);
      }
    }
  }
  
  .topic-detail {
    .detail-section {
      margin-bottom: 20px;
      
      h4 {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 12px;
      }
      
      .description-content {
        padding: 12px;
        background: rgba(139, 92, 246, 0.05);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.75);
        line-height: 1.6;
      }
    }
  }
}

:deep(.el-card) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(139, 92, 246, 0.1);
  
  .el-card__header {
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  }
}

:deep(.el-table) {
  background: transparent;
  
  th {
    background: rgba(139, 92, 246, 0.05) !important;
    color: rgba(255, 255, 255, 0.8) !important;
  }
  
  td {
    background: transparent !important;
    color: rgba(255, 255, 255, 0.7) !important;
    border-bottom: 1px solid rgba(139, 92, 246, 0.08) !important;
  }
  
  tr:hover > td {
    background: rgba(139, 92, 246, 0.05) !important;
  }
}

:deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-select__wrapper),
:deep(.el-date-editor .el-input__wrapper),
:deep(.el-input-number__input) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(139, 92, 246, 0.2) !important;
  color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.el-dialog) {
  background: linear-gradient(180deg, rgba(20, 20, 50, 0.98) 0%, rgba(15, 15, 40, 0.98) 100%);
  border: 1px solid rgba(139, 92, 246, 0.2);
  
  .el-dialog__title {
    color: rgba(255, 255, 255, 0.9);
  }
  
  .el-dialog__headerbtn .el-dialog__close {
    color: rgba(255, 255, 255, 0.6);
  }
}

:deep(.el-divider__text) {
  color: rgba(255, 255, 255, 0.7);
  background: linear-gradient(180deg, rgba(20, 20, 50, 0.98) 0%, rgba(15, 15, 40, 0.98) 100%);
}

:deep(.el-divider) {
  border-top-color: rgba(139, 92, 246, 0.15);
}

:deep(.el-descriptions__label) {
  color: rgba(255, 255, 255, 0.5) !important;
}

:deep(.el-descriptions__content) {
  color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.el-descriptions__cell) {
  border-color: rgba(139, 92, 246, 0.1) !important;
}
</style>
