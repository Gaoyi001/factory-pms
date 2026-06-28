<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="样品管理" name="samples">
        <div class="table-toolbar">
          <div class="left">
            <el-button type="primary" @click="showSampleForm()">
              <el-icon><Plus /></el-icon> 新建样品
            </el-button>
            <el-select v-model="sampleFilter.status" placeholder="样品状态" clearable style="width:140px" @change="onSampleFilterChange">
              <el-option v-for="s in sampleStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
            <el-select v-model="sampleFilter.sample_type" placeholder="样品类型" clearable style="width:140px" @change="onSampleFilterChange">
              <el-option v-for="t in sampleTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
          </div>
          <div class="right">
            <el-input v-model="sampleFilter.keyword" placeholder="搜索编号/名称" clearable style="width:220px" @keyup.enter="loadSamples">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="loadSamples">查询</el-button>
          </div>
        </div>

        <el-table :data="samples.items" v-loading="sampleLoading" stripe size="small" empty-text="暂无样品">
          <el-table-column prop="sample_no" label="样品编号" width="150" />
          <el-table-column prop="name" label="样品名称" min-width="180" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="sample_type" label="类型" width="110">
            <template #default="{ row }">
              <el-tag size="small">{{ sampleTypeLabel(row.sample_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="sampleStatusTag(row.status)" size="small">{{ sampleStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="plan_finish" label="计划完成" width="120" />
          <el-table-column prop="test_result" label="检测结果" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.test_result" :type="row.test_result==='pass'?'success':row.test_result==='fail'?'danger':'warning'" size="small">
                {{ testResultLabel(row.test_result) }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link @click="viewInspections(row)">检测</el-button>
              <el-button link type="primary" @click="showSampleForm(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDeleteSample(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-model:current-page="samplePagination.page" v-model:page-size="samplePagination.page_size"
          :total="samples.total" layout="total, sizes, prev, pager, next" @change="loadSamples"
          style="margin-top:16px;justify-content:flex-end" />
      </el-tab-pane>

      <el-tab-pane label="试产管理" name="trials">
        <div class="table-toolbar">
          <div class="left">
            <el-button type="primary" @click="showTrialForm()">
              <el-icon><Plus /></el-icon> 新建试产
            </el-button>
            <el-select v-model="trialFilter.status" placeholder="试产状态" clearable style="width:140px" @change="onTrialFilterChange">
              <el-option v-for="s in trialStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </div>
          <div class="right">
            <el-input v-model="trialFilter.keyword" placeholder="搜索编号/名称" clearable style="width:220px" @keyup.enter="loadTrials">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="loadTrials">查询</el-button>
          </div>
        </div>

        <el-table :data="trials.items" v-loading="trialLoading" stripe size="small" empty-text="暂无试产记录">
          <el-table-column prop="trial_no" label="试产编号" width="150" />
          <el-table-column prop="name" label="试产名称" min-width="180" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="trialStatusTag(row.status)" size="small">{{ trialStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="plan_qty" label="计划数量" width="100" />
          <el-table-column prop="actual_qty" label="实际数量" width="100" />
          <el-table-column prop="pass_qty" label="合格数" width="90" />
          <el-table-column prop="yield_rate" label="良率" width="90">
            <template #default="{ row }">
              {{ row.yield_rate ? (row.yield_rate * 100).toFixed(1) + '%' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="workshop" label="车间" width="100" />
          <el-table-column prop="plan_start" label="计划开始" width="120" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="showTrialForm(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDeleteTrial(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-model:current-page="trialPagination.page" v-model:page-size="trialPagination.page_size"
          :total="trials.total" layout="total, sizes, prev, pager, next" @change="loadTrials"
          style="margin-top:16px;justify-content:flex-end" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="sampleFormVisible" :title="sampleFormMode==='create'?'新建样品':'编辑样品'" width="600px">
      <el-form ref="sampleFormRef" :model="sampleForm" :rules="sampleFormRules" label-width="90px">
        <el-form-item label="样品名称" prop="name">
          <el-input v-model="sampleForm.name" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="sampleForm.project_id" placeholder="请选择" style="width:100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="sampleForm.version" style="width:50%" />
        </el-form-item>
        <el-form-item label="样品类型">
          <el-select v-model="sampleForm.sample_type" style="width:100%">
            <el-option v-for="t in sampleTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="sampleForm.status" style="width:100%">
            <el-option v-for="s in sampleStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="sampleForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="计划完成">
          <el-date-picker v-model="sampleForm.plan_finish" type="date" style="width:100%" />
        </el-form-item>
        <el-form-item label="检测结果">
          <el-select v-model="sampleForm.test_result" clearable style="width:100%">
            <el-option label="通过" value="pass" />
            <el-option label="不通过" value="fail" />
            <el-option label="待检" value="pending" />
            <el-option label="条件通过" value="conditional_pass" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="sampleForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="sampleForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sampleFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="sampleSubmitting" @click="handleSubmitSample">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="trialFormVisible" :title="trialFormMode==='create'?'新建试产':'编辑试产'" width="600px">
      <el-form ref="trialFormRef" :model="trialForm" :rules="trialFormRules" label-width="90px">
        <el-form-item label="试产名称" prop="name">
          <el-input v-model="trialForm.name" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="trialForm.project_id" placeholder="请选择" style="width:100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="trialForm.status" style="width:100%">
            <el-option v-for="s in trialStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划数量">
          <el-input-number v-model="trialForm.plan_qty" :min="0" />
        </el-form-item>
        <el-form-item label="车间">
          <el-input v-model="trialForm.workshop" />
        </el-form-item>
        <el-form-item label="产线">
          <el-input v-model="trialForm.line_no" />
        </el-form-item>
        <el-form-item label="计划周期">
          <el-date-picker v-model="trialForm.plan_range" type="daterange" range-separator="至"
            start-placeholder="开始日期" end-placeholder="结束日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="trialForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="trialFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="trialSubmitting" @click="handleSubmitTrial">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="inspectionVisible" title="样品检测记录" width="800px">
      <el-table :data="inspections" size="small" empty-text="暂无检测记录">
        <el-table-column prop="inspect_no" label="检测单号" width="140" />
        <el-table-column prop="inspect_type" label="检测类型" width="110" />
        <el-table-column prop="inspected_at" label="检测日期" width="120" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.result==='pass'?'success':row.result==='fail'?'danger':'warning'" size="small">
              {{ row.result === 'pass' ? '通过' : row.result === 'fail' ? '不通过' : '待定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="disposition" label="处置" width="100" />
        <el-table-column prop="failure_desc" label="不合格描述" show-overflow-tooltip />
        <el-table-column label="操作" width="80">
          <template #default="{ row: insp }">
            <el-button link type="danger" @click="handleDeleteInspection(insp)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { sampleApi, projectApi } from '@/api'
import type { SampleOut, TrialProductionOut } from '@/types/sample'

const activeTab = ref('samples')

const sampleLoading = ref(false)
const sampleSubmitting = ref(false)
const sampleFormVisible = ref(false)
const sampleFormMode = ref<'create'|'edit'>('create')
const sampleFormRef = ref<FormInstance>()
const sampleFormRules: FormRules = {
  name: [{ required: true, message: '请输入样品名称', trigger: 'blur' }],
}
const samples = reactive<{ items: SampleOut[]; total: number }>({ items: [], total: 0 })
const samplePagination = reactive({ page: 1, page_size: 20 })
const sampleFilter = reactive({ status: '', sample_type: '', keyword: '' })

const trialLoading = ref(false)
const trialSubmitting = ref(false)
const trialFormVisible = ref(false)
const trialFormMode = ref<'create'|'edit'>('create')
const trialFormRef = ref<FormInstance>()
const trialFormRules: FormRules = {
  name: [{ required: true, message: '请输入试产名称', trigger: 'blur' }],
}
const trials = reactive<{ items: TrialProductionOut[]; total: number }>({ items: [], total: 0 })
const trialPagination = reactive({ page: 1, page_size: 20 })
const trialFilter = reactive({ status: '', keyword: '' })

const projectOptions = ref<{ id: number; name: string }[]>([])
const inspectionVisible = ref(false)
const inspections = ref<any[]>([])

const sampleStatusOpts = [
  { label: '草稿', value: 'draft' },
  { label: '制作中', value: 'making' },
  { label: '检测中', value: 'testing' },
  { label: '已通过', value: 'passed' },
  { label: '不合格', value: 'failed' },
  { label: '返工', value: 'rework' },
]
const sampleTypeOpts = [
  { label: '开发样', value: 'development' },
  { label: '验证样', value: 'verification' },
  { label: '试产样', value: 'pre_production' },
]
const trialStatusOpts = [
  { label: '计划中', value: 'planned' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '已中止', value: 'aborted' },
]

const sampleStatusTag = (s: string) => ({ draft: 'info', making: 'warning', testing: 'primary', passed: 'success', failed: 'danger', rework: 'warning' }[s] || 'info') as any
const sampleStatusLabel = (s: string) => {
  const found = sampleStatusOpts.find(o => o.value === s)
  return found ? found.label : s
}
const sampleTypeLabel = (t: string) => {
  const found = sampleTypeOpts.find(o => o.value === t)
  return found ? found.label : t
}
const testResultLabel = (r: string) => ({ pass: '通过', fail: '不通过', pending: '待检', conditional_pass: '条件通过' }[r] || r)
const trialStatusTag = (s: string) => ({ planned: 'info', in_progress: 'warning', completed: 'success', aborted: 'danger' }[s] || 'info') as any
const trialStatusLabel = (s: string) => {
  const found = trialStatusOpts.find(o => o.value === s)
  return found ? found.label : s
}

const sampleForm = reactive({
  id: 0, name: '', description: '', project_id: null as number|null,
  version: 'V1.0', sample_type: 'development', status: 'draft',
  quantity: 1, plan_finish: '', test_result: '', remark: '',
})

const trialForm = reactive({
  id: 0, name: '', project_id: null as number|null, status: 'planned',
  plan_qty: 0, workshop: '', line_no: '',
  plan_range: null as [string, string]|null, remark: '',
})

const loadSamples = async () => {
  sampleLoading.value = true
  try {
    const res = await sampleApi.listSamples({ ...samplePagination, status: sampleFilter.status || undefined, sample_type: sampleFilter.sample_type || undefined, keyword: sampleFilter.keyword || undefined })
    samples.items = res.items || []
    samples.total = res.total || 0
  } finally { sampleLoading.value = false }
}

const onSampleFilterChange = () => {
  samplePagination.page = 1
  loadSamples()
}

const loadTrials = async () => {
  trialLoading.value = true
  try {
    const res = await sampleApi.listTrials({ ...trialPagination, status: trialFilter.status || undefined })
    trials.items = res.items || []
    trials.total = res.total || 0
  } finally { trialLoading.value = false }
}

const onTrialFilterChange = () => {
  trialPagination.page = 1
  loadTrials()
}

const loadProjects = async () => {
  try {
    const res = await projectApi.list({ page: 1, page_size: 100 })
    projectOptions.value = (res.items || []).map((p: any) => ({ id: p.id, name: p.name }))
  } catch {}
}

const showSampleForm = async (row?: SampleOut) => {
  if (!projectOptions.value.length) await loadProjects()
  if (row) {
    sampleFormMode.value = 'edit'
    Object.assign(sampleForm, { id: row.id, name: row.name, description: row.description, project_id: row.project_id, version: row.version, sample_type: row.sample_type, status: row.status, quantity: row.quantity, plan_finish: row.plan_finish, test_result: row.test_result, remark: row.remark })
  } else {
    sampleFormMode.value = 'create'
    Object.assign(sampleForm, { id: 0, name: '', description: '', project_id: null, version: 'V1.0', sample_type: 'development', status: 'draft', quantity: 1, plan_finish: '', test_result: '', remark: '' })
  }
  sampleFormVisible.value = true
}

const handleSubmitSample = async () => {
  if (!sampleFormRef.value) return
  try { await sampleFormRef.value.validate() } catch { return }
  sampleSubmitting.value = true
  try {
    const payload: any = { ...sampleForm, project_id: sampleForm.project_id || undefined }
    if (sampleFormMode.value === 'create') {
      await sampleApi.createSample(payload)
      ElMessage.success('创建成功')
    } else {
      await sampleApi.updateSample(sampleForm.id, payload)
      ElMessage.success('更新成功')
    }
    sampleFormVisible.value = false
    loadSamples()
  } finally { sampleSubmitting.value = false }
}

const showTrialForm = async (row?: TrialProductionOut) => {
  if (!projectOptions.value.length) await loadProjects()
  if (row) {
    trialFormMode.value = 'edit'
    Object.assign(trialForm, { id: row.id, name: row.name, project_id: row.project_id, status: row.status, plan_qty: row.plan_qty, workshop: row.workshop, line_no: row.line_no, plan_range: row.plan_start && row.plan_end ? [row.plan_start, row.plan_end] : null, remark: row.remark })
  } else {
    trialFormMode.value = 'create'
    Object.assign(trialForm, { id: 0, name: '', project_id: null, status: 'planned', plan_qty: 0, workshop: '', line_no: '', plan_range: null, remark: '' })
  }
  trialFormVisible.value = true
}

const handleSubmitTrial = async () => {
  if (!trialFormRef.value) return
  try { await trialFormRef.value.validate() } catch { return }
  trialSubmitting.value = true
  try {
    const payload: any = { name: trialForm.name, project_id: trialForm.project_id, status: trialForm.status, plan_qty: trialForm.plan_qty, workshop: trialForm.workshop, line_no: trialForm.line_no, remark: trialForm.remark }
    if (trialForm.plan_range) {
      payload.plan_start = trialForm.plan_range[0]
      payload.plan_end = trialForm.plan_range[1]
    }
    if (trialFormMode.value === 'create') {
      await sampleApi.createTrial(payload)
      ElMessage.success('创建成功')
    } else {
      await sampleApi.updateTrial(trialForm.id, payload)
      ElMessage.success('更新成功')
    }
    trialFormVisible.value = false
    loadTrials()
  } finally { trialSubmitting.value = false }
}

const viewInspections = async (row: SampleOut) => {
  inspectionVisible.value = true
  try {
    const data = await sampleApi.listInspections(row.id)
    inspections.value = data || []
  } catch { inspections.value = [] }
}

const handleDeleteSample = async (row: SampleOut) => {
  await ElMessageBox.confirm(`确定要删除样品 \"${row.name}\" 吗？此操作不可恢复！`, '警告', { type: 'warning' })
  await sampleApi.deleteSample(row.id)
  ElMessage.success('已删除')
  loadSamples()
}

const handleDeleteTrial = async (row: TrialProductionOut) => {
  await ElMessageBox.confirm(`确定要删除试产记录 \"${row.name}\" 吗？此操作不可恢复！`, '警告', { type: 'warning' })
  await sampleApi.deleteTrial(row.id)
  ElMessage.success('已删除')
  loadTrials()
}

const handleDeleteInspection = async (insp: any) => {
  await ElMessageBox.confirm(`确定要删除检测记录 \"${insp.inspect_no}\" 吗？`, '提示', { type: 'warning' })
  await sampleApi.deleteInspection(insp.id)
  ElMessage.success('已删除')
  // Reload inspections for the current sample
  inspections.value = inspections.value.filter((i: any) => i.id !== insp.id)
}

onMounted(() => {
  loadSamples()
  loadTrials()
})
</script>
