<template>
  <div class="conversations-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">会话列表</span>
          <el-button type="primary" @click="goToChat">
            <el-icon><Plus /></el-icon>
            新建会话
          </el-button>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="conversations"
        style="width: 100%"
        empty-text="暂无会话"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="会话标题" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已结束' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="最后更新" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewConversation(row)">
              查看
            </el-button>
            <el-button type="primary" link @click="editConversation(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="deleteConversation(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog
      v-model="editDialogVisible"
      :title="editingConversation ? '编辑会话' : '新建会话'"
      width="400px"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="会话标题">
          <el-input v-model="editForm.title" placeholder="请输入会话标题" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConversation" :loading="saving">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const conversations = ref([])
const editDialogVisible = ref(false)
const editingConversation = ref(null)
const saving = ref(false)

const editForm = reactive({
  title: ''
})

const formatDateTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

const loadConversations = async () => {
  loading.value = true
  try {
    const res = await conversationApi.getList({ limit: 100 })
    conversations.value = res.items || []
  } catch (error) {
    console.error('加载会话列表失败:', error)
    ElMessage.error('加载会话列表失败')
  } finally {
    loading.value = false
  }
}

const goToChat = () => {
  router.push('/chat')
}

const viewConversation = (row) => {
  router.push(`/chat?conversation_id=${row.id}`)
}

const editConversation = (row) => {
  editingConversation.value = row
  editForm.title = row.title
  editDialogVisible.value = true
}

const deleteConversation = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除会话"${row.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await conversationApi.delete(row.id)
    ElMessage.success('删除成功')
    loadConversations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
    }
  }
}

const saveConversation = async () => {
  if (!editForm.title.trim()) {
    ElMessage.warning('请输入会话标题')
    return
  }
  
  saving.value = true
  try {
    if (editingConversation.value) {
      await conversationApi.update(editingConversation.value.id, {
        title: editForm.title
      })
      ElMessage.success('更新成功')
    } else {
      await conversationApi.create({
        title: editForm.title
      })
      ElMessage.success('创建成功')
    }
    
    editDialogVisible.value = false
    loadConversations()
  } catch (error) {
    console.error('保存会话失败:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConversations()
})
</script>

<style lang="scss" scoped>
.conversations-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .title {
      font-size: 16px;
      font-weight: 500;
    }
  }
}
</style>
