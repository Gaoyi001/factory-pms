<template>
  <div class="page-container">
    <div class="toolbar">
      <h2>操作日志</h2>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索操作人/详情" style="width: 200px; margin-right: 12px;" clearable @change="loadLogs" />
        <el-select v-model="filterAction" placeholder="操作类型" style="width: 120px; margin-right: 12px;" clearable @change="loadLogs">
          <el-option label="查看" value="read" />
          <el-option label="创建" value="create" />
          <el-option label="更新" value="update" />
          <el-option label="删除" value="delete" />
          <el-option label="下载" value="download" />
        </el-select>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
          value-format="YYYY-MM-DD" style="margin-right: 12px;" @change="loadLogs" />
        <el-button @click="loadLogs">刷新</el-button>
      </div>
    </div>

    <el-table :data="logs" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="操作人" width="100" />
      <el-table-column prop="action" label="操作" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.action === 'create'" type="success" size="small">创建</el-tag>
          <el-tag v-else-if="row.action === 'update'" type="warning" size="small">更新</el-tag>
          <el-tag v-else-if="row.action === 'delete'" type="danger" size="small">删除</el-tag>
          <el-tag v-else-if="row.action === 'download'" type="info" size="small">下载</el-tag>
          <el-tag v-else size="small">查看</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resource" label="资源" width="100">
        <template #default="{ row }">
          {{ resourceMap[row.resource] || row.resource }}
        </template>
      </el-table-column>
      <el-table-column prop="resource_name" label="资源名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP地址" width="130" />
      <el-table-column prop="method" label="请求方法" width="80" />
      <el-table-column prop="path" label="请求路径" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="操作时间" width="160">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 16px; justify-content: flex-end;"
      @size-change="loadLogs"
      @current-change="loadLogs"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { operationLogApi } from '@/api'

const resourceMap: Record<string, string> = {
  project: '项目',
  experiment: '实验',
  bom: 'BOM',
  sample: '样品',
  document: '文档',
  user: '用户',
  department: '部门',
  role: '角色',
}

const logs = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
const filterAction = ref('')
const dateRange = ref<[string, string] | null>(null)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

onMounted(() => {
  loadLogs()
})

async function loadLogs() {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      action: filterAction.value || undefined,
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await operationLogApi.list(params)
    logs.value = res.items || []
    total.value = res.total || 0
  } catch {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.toolbar h2 {
  margin: 0;
  font-size: 18px;
}
.toolbar-actions {
  display: flex;
  align-items: center;
}
</style>
