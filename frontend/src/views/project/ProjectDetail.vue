<template>
  <div v-loading="loading">
    <el-page-header @back="$router.back()" content="项目详情">
      <template #content>
        <span style="font-size:18px;font-weight:600">{{ project.name }}</span>
        <el-tag :type="statusTag(project.status)" size="small" style="margin-left:12px">{{ statusLabel(project.status) }}</el-tag>
        <el-button type="primary" size="small" style="margin-left:12px" @click="showProjectForm">编辑项目</el-button>
      </template>
    </el-page-header>

    <el-card style="margin-top:16px" shadow="never">
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="项目编号">{{ project.code }}</el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-rate :model-value="project.priority" disabled :max="5" :colors="['#f56c6c','#e6a23c','#409eff']" />
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          <el-progress :percentage="project.progress || 0" :stroke-width="8" />
        </el-descriptions-item>
        <el-descriptions-item label="计划开始">{{ project.plan_start || '-' }}</el-descriptions-item>
        <el-descriptions-item label="计划结束">{{ project.plan_end || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预算">{{ project.budget || '-' }}</el-descriptions-item>
        <el-descriptions-item label="项目描述" :span="3">{{ project.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-tabs v-model="activeTab" style="margin-top:16px">
      <el-tab-pane label="任务管理" name="tasks">
        <div class="tab-toolbar">
          <el-button type="primary" size="small" @click="showTaskForm()">
            <el-icon><Plus /></el-icon> 新建任务
          </el-button>
          <el-select v-model="taskFilter.status" placeholder="任务状态" clearable size="small" style="width:120px" @change="loadTasks">
            <el-option v-for="s in taskStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </div>
        <el-table :data="tasks" size="small" empty-text="暂无任务">
          <el-table-column prop="title" label="任务名称" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="taskStatusTag(row.status)" size="small">{{ taskStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" width="90">
            <template #default="{ row }">
              <el-rate :model-value="row.priority" disabled :max="5" :colors="['#f56c6c','#e6a23c','#409eff']" />
            </template>
          </el-table-column>
          <el-table-column prop="plan_hours" label="计划工时" width="90" />
          <el-table-column prop="actual_hours" label="实际工时" width="90" />
          <el-table-column prop="due_date" label="截止日期" width="120" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showTaskForm(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDeleteTask(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="需求管理" name="requirements">
        <div class="tab-toolbar">
          <el-button type="primary" size="small" @click="showReqForm()">
            <el-icon><Plus /></el-icon> 新建需求
          </el-button>
        </div>
        <el-table :data="requirements" size="small" empty-text="暂无需求">
          <el-table-column prop="code" label="需求编号" width="140" />
          <el-table-column prop="title" label="需求标题" min-width="200" />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="priority" label="优先级" width="90" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button v-if="projectApi.updateRequirement" link type="primary" size="small" @click="showReqForm(row)">编辑</el-button>
              <el-button v-if="projectApi.deleteRequirement" link type="danger" size="small" @click="handleDeleteReq(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑项目弹窗 -->
    <el-dialog v-model="projectFormVisible" title="编辑项目" width="640px">
      <el-form ref="projectFormRef" :model="projectForm" :rules="projectFormRules" label-width="90px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" placeholder="请输入项目名称（2-50个字符）" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input v-model="projectForm.description" type="textarea" :rows="3" placeholder="请输入项目描述" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-rate v-model="projectForm.priority" :max="5" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="projectForm.status" style="width:100%">
            <el-option label="草稿" value="draft" />
            <el-option label="进行中" value="active" />
            <el-option label="暂停" value="on_hold" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划周期">
          <el-date-picker v-model="projectForm.plan_range" type="daterange" range-separator="至"
            start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="projectSubmitting" @click="handleUpdateProject">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="taskFormVisible" :title="taskFormMode==='create'?'新建任务':'编辑任务'" width="560px">
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskFormRules" label-width="90px">
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="taskForm.status" style="width:100%">
            <el-option v-for="s in taskStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-rate v-model="taskForm.priority" :max="5" />
        </el-form-item>
        <el-form-item label="计划工时">
          <el-input-number v-model="taskForm.plan_hours" :min="0" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="taskForm.due_date" type="date" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="taskSubmitting" @click="handleSubmitTask">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reqFormVisible" :title="reqFormMode==='create'?'新建需求':'编辑需求'" width="560px">
      <el-form ref="reqFormRef" :model="reqForm" :rules="reqFormRules" label-width="90px">
        <el-form-item label="需求标题" prop="title">
          <el-input v-model="reqForm.title" placeholder="请输入需求标题" />
        </el-form-item>
        <el-form-item label="需求描述">
          <el-input v-model="reqForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="reqForm.source" style="width:100%">
            <el-option label="内部" value="internal" />
            <el-option label="客户" value="customer" />
            <el-option label="市场" value="market" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="reqForm.priority" style="width:100%">
            <el-option label="必须" value="must" />
            <el-option label="应该" value="should" />
            <el-option label="可以" value="could" />
            <el-option label="暂不" value="wont" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="reqForm.status" style="width:100%">
            <el-option label="草稿" value="draft" />
            <el-option label="评审中" value="reviewing" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已实现" value="implemented" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reqFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="reqSubmitting" @click="handleSubmitReq">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { projectApi } from '@/api'
import type { ProjectOut, TaskOut, RequirementOut } from '@/types/project'

const route = useRoute()
const projectId = Number(route.params.id)

const loading = ref(false)
const activeTab = ref('tasks')
const project = reactive<Partial<ProjectOut>>({})
const tasks = ref<TaskOut[]>([])
const requirements = ref<RequirementOut[]>([])

const taskFilter = reactive({ status: '' })
const taskStatusOpts = [
  { label: '待办', value: 'todo' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'done' },
  { label: '已取消', value: 'cancelled' },
]

const statusTag = (s?: string) => ({ draft: 'info', active: 'success', on_hold: 'warning', completed: '', cancelled: 'danger' }[s || ''] || 'info') as any
const statusLabel = (s?: string) => ({ draft: '草稿', active: '进行中', on_hold: '暂停', completed: '已完成', cancelled: '已取消' }[s || ''] || (s || '-'))
const taskStatusTag = (s: string) => ({ todo: 'info', in_progress: 'warning', done: 'success', cancelled: 'danger' }[s] || 'info') as any
const taskStatusLabel = (s: string) => ({ todo: '待办', in_progress: '进行中', done: '已完成', cancelled: '已取消' }[s] || s)

const taskFormVisible = ref(false)
const taskFormMode = ref<'create'|'edit'>('create')
const taskFormRef = ref<FormInstance>()
const taskSubmitting = ref(false)
const taskFormRules: FormRules = {
  title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
}
const taskForm = reactive({
  id: 0, title: '', description: '', status: 'todo',
  priority: 3, plan_hours: 0, due_date: '',
})

const reqFormVisible = ref(false)
const reqFormMode = ref<'create'|'edit'>('create')
const reqFormRef = ref<FormInstance>()
const reqSubmitting = ref(false)
const reqFormRules: FormRules = {
  title: [{ required: true, message: '请输入需求标题', trigger: 'blur' }],
}
const reqForm = reactive({
  id: 0, title: '', description: '', source: 'internal',
  priority: 'should', status: 'draft',
})

// ---- 编辑项目 ----
const projectFormRef = ref<FormInstance>()
const projectFormVisible = ref(false)
const projectSubmitting = ref(false)
const projectFormRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '项目名称长度为 2-50 个字符', trigger: 'blur' },
  ],
}
const projectForm = reactive({
  name: '', description: '', priority: 3, status: '' as string,
  plan_range: null as [string, string] | null,
})

const showProjectForm = () => {
  Object.assign(projectForm, {
    name: project.name || '', description: project.description || '',
    priority: project.priority || 3, status: project.status || 'draft',
    plan_range: project.plan_start && project.plan_end ? [project.plan_start, project.plan_end] : null,
  })
  projectFormRef.value?.clearValidate()
  projectFormVisible.value = true
}

const handleUpdateProject = async () => {
  if (!projectFormRef.value) return
  try {
    await projectFormRef.value.validate()
  } catch { return }
  projectSubmitting.value = true
  try {
    const payload: any = {
      name: projectForm.name.trim(),
      description: projectForm.description?.trim(),
      priority: projectForm.priority,
      status: projectForm.status,
    }
    if (projectForm.plan_range) {
      payload.plan_start = projectForm.plan_range[0]
      payload.plan_end = projectForm.plan_range[1]
    }
    await projectApi.update(projectId, payload)
    ElMessage.success('更新成功')
    projectFormVisible.value = false
    loadProject()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '更新失败'
    ElMessage.error(msg)
  } finally { projectSubmitting.value = false }
}

const loadProject = async () => {
  loading.value = true
  try {
    const data = await projectApi.get(projectId)
    Object.assign(project, data)
  } finally { loading.value = false }
}

const loadTasks = async () => {
  try {
    const data = await projectApi.getTasks(projectId, { status: taskFilter.status || undefined })
    tasks.value = data || []
  } catch {}
}

const loadRequirements = async () => {
  try {
    const data = await projectApi.getRequirements(projectId)
    requirements.value = data || []
  } catch {}
}

const showTaskForm = (row?: TaskOut) => {
  if (row) {
    taskFormMode.value = 'edit'
    Object.assign(taskForm, { id: row.id, title: row.title, description: row.description, status: row.status, priority: row.priority, plan_hours: row.plan_hours, due_date: row.due_date })
  } else {
    taskFormMode.value = 'create'
    Object.assign(taskForm, { id: 0, title: '', description: '', status: 'todo', priority: 3, plan_hours: 0, due_date: '' })
  }
  taskFormVisible.value = true
}

const handleSubmitTask = async () => {
  if (!taskFormRef.value) return
  try { await taskFormRef.value.validate() } catch { return }
  taskSubmitting.value = true
  try {
    const payload: any = { title: taskForm.title, description: taskForm.description, status: taskForm.status, priority: taskForm.priority, plan_hours: taskForm.plan_hours, due_date: taskForm.due_date || undefined }
    if (taskFormMode.value === 'create') {
      await projectApi.createTask(projectId, payload)
      ElMessage.success('创建成功')
    } else {
      await projectApi.updateTask(taskForm.id, payload)
      ElMessage.success('更新成功')
    }
    taskFormVisible.value = false
    loadTasks()
  } finally { taskSubmitting.value = false }
}

const handleDeleteTask = async (row: TaskOut) => {
  await ElMessageBox.confirm('确定要删除该任务吗？', '提示', { type: 'warning' })
  await projectApi.deleteTask(row.id)
  ElMessage.success('已删除')
  loadTasks()
}

const showReqForm = (row?: RequirementOut) => {
  if (row) {
    reqFormMode.value = 'edit'
    Object.assign(reqForm, { id: row.id, title: row.title, description: row.description, source: row.source, priority: row.priority, status: row.status })
  } else {
    reqFormMode.value = 'create'
    Object.assign(reqForm, { id: 0, title: '', description: '', source: 'internal', priority: 'should', status: 'draft' })
  }
  reqFormVisible.value = true
}

const handleSubmitReq = async () => {
  if (!reqFormRef.value) return
  try { await reqFormRef.value.validate() } catch { return }
  reqSubmitting.value = true
  try {
    const payload: any = { title: reqForm.title, description: reqForm.description, source: reqForm.source, priority: reqForm.priority, status: reqForm.status }
    if (reqFormMode.value === 'create') {
      await projectApi.createRequirement(projectId, payload)
      ElMessage.success('创建成功')
    } else {
      if (!projectApi.updateRequirement) {
        ElMessage.warning('更新需求接口暂未实现')
        return
      }
      await (projectApi as any).updateRequirement(reqForm.id, payload)
      ElMessage.success('更新成功')
    }
    reqFormVisible.value = false
    loadRequirements()
  } finally { reqSubmitting.value = false }
}

const handleDeleteReq = async (row: RequirementOut) => {
  await ElMessageBox.confirm('确定要删除该需求吗？', '提示', { type: 'warning' })
  if (!(projectApi as any).deleteRequirement) {
    ElMessage.warning('删除需求接口暂未实现')
    return
  }
  await (projectApi as any).deleteRequirement(row.id)
  ElMessage.success('已删除')
  loadRequirements()
}

onMounted(() => {
  loadProject()
  loadTasks()
  loadRequirements()
})
</script>

<style scoped>
.tab-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
</style>
