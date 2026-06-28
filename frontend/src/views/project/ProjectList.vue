<!-- src/views/project/ProjectList.vue -->
<template>
  <div>
    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="left">
        <el-button v-if="canOperate('project:create')" type="primary" @click="showForm()">
          <el-icon><Plus /></el-icon> 新建项目
        </el-button>
        <el-select v-model="filter.status" placeholder="项目状态" clearable style="width:140px" @change="onFilterChange">
          <el-option v-for="s in statusOpts" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
      </div>
      <div class="right">
        <el-input v-model="filter.keyword" placeholder="搜索项目编号/名称" clearable style="width:220px" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button @click="load">查询</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="tableData.items" v-loading="loading" stripe size="small" empty-text="暂无项目">
      <el-table-column prop="code" label="项目编号" width="150" />
      <el-table-column prop="name" label="项目名称" min-width="180" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="90">
        <template #default="{ row }">
          <el-rate :model-value="row.priority" disabled :max="5" :colors="['#f56c6c','#e6a23c','#409eff']" />
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.progress || 0" :stroke-width="8" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link @click="$router.push(`/projects/${row.id}`)">详情</el-button>
              <el-button v-if="canOperate('project:update')" link type="primary" @click="showForm(row)">编辑</el-button>
              <el-button v-if="canOperate('project:delete')" link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
      :total="tableData.total" layout="total, sizes, prev, pager, next" @change="load"
      style="margin-top:16px;justify-content:flex-end" />

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="formMode==='create'?'新建项目':'编辑项目'" width="640px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称（2-50个字符）" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入项目描述" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-rate v-model="form.priority" :max="5" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner_id">
          <el-select v-model="form.owner_id" placeholder="请选择负责人" clearable style="width:100%">
            <el-option v-for="u in userOptions" :key="u.id" :label="u.real_name||u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划周期" prop="plan_range">
          <el-date-picker v-model="form.plan_range" type="daterange" range-separator="至"
            start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible=false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, inject } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { projectApi, userApi } from '@/api'
import type { ProjectOut } from '@/types/project'

const canOperate = inject<(perm: string) => boolean>('canOperate', () => true)

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const formVisible = ref(false)
const formMode = ref<'create'|'edit'>('create')
const tableData = reactive<{ items: ProjectOut[]; total: number }>({ items: [], total: 0 })
const userOptions = ref<{ id: number; username: string; real_name?: string }[]>([])
const pagination = reactive({ page: 1, page_size: 20 })
const filter = reactive({ status: '', keyword: '' })

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '项目名称长度为 2-50 个字符', trigger: 'blur' },
  ],
  priority: [
    { required: true, message: '请设置优先级', trigger: 'change' },
  ],
}

const statusOpts = [
  { label: '草稿', value: 'draft' },
  { label: '进行中', value: 'active' },
  { label: '暂停', value: 'on_hold' },
  { label: '已完成', value: 'completed' },
]

const form = reactive({
  id: 0, name: '', description: '', priority: 3,
  owner_id: null as number|null, plan_range: null as [string, string]|null,
})

const statusTag = (s: string) => ({ draft: 'info', active: 'success', on_hold: 'warning', completed: '', cancelled: 'danger' }[s] || 'info')
const statusLabel = (s: string) => ({ draft: '草稿', active: '进行中', on_hold: '暂停', completed: '已完成', cancelled: '已取消' }[s] || s)

const load = async () => {
  loading.value = true
  try {
    const res = await projectApi.list({ ...pagination, status: filter.status || undefined, keyword: filter.keyword || undefined })
    tableData.items = res.items || []
    tableData.total = res.total || 0
  } finally { loading.value = false }
}

const onFilterChange = () => {
  pagination.page = 1
  load()
}

const showForm = async (row?: ProjectOut) => {
  if (!userOptions.value.length) {
    try {
      const res = await userApi.simpleList()
      userOptions.value = res || []
    } catch {}
  }
  if (row) {
    formMode.value = 'edit'
    Object.assign(form, { id: row.id, name: row.name, description: row.description || '', priority: row.priority, owner_id: row.owner_id, plan_range: row.plan_start && row.plan_end ? [row.plan_start, row.plan_end] : null })
  } else {
    formMode.value = 'create'
    Object.assign(form, { id: 0, name: '', description: '', priority: 3, owner_id: null, plan_range: null })
  }
  // 清除上次的表单校验状态
  formRef.value?.clearValidate()
  formVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return // 表单校验不通过
  }

  submitting.value = true
  try {
    const payload: any = { name: form.name.trim(), description: form.description?.trim(), priority: form.priority, owner_id: form.owner_id || undefined }
    if (form.plan_range) {
      payload.plan_start = form.plan_range[0]
      payload.plan_end = form.plan_range[1]
    }
    if (formMode.value === 'create') {
      await projectApi.create(payload)
      ElMessage.success('创建成功')
    } else {
      await projectApi.update(form.id, payload)
      ElMessage.success('更新成功')
    }
    formVisible.value = false
    load()
  } catch (err: any) {
    // 提取后端错误消息显示给用户
    const msg = err?.response?.data?.detail || err?.message || '操作失败'
    ElMessage.error(msg)
  } finally { submitting.value = false }
}

const handleDelete = async (row: ProjectOut) => {
  await ElMessageBox.confirm('确定要删除该项目吗？', '提示', { type: 'warning' })
  await projectApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
