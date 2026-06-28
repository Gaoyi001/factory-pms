<template>
  <div>
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/bom' }">BOM管理</el-breadcrumb-item>
      <el-breadcrumb-item>BOM详情</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" style="margin-top:16px" v-loading="loading">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:16px;font-weight:600">{{ bom?.name || '-' }}</span>
          <el-tag :type="statusTag(bom?.status)">{{ statusLabel(bom?.status) }}</el-tag>
        </div>
      </template>
      <el-descriptions :column="4" size="small" border>
        <el-descriptions-item label="BOM编号">{{ bom?.code }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ bom?.version }}</el-descriptions-item>
        <el-descriptions-item label="产品编码">{{ bom?.product_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="所属项目">{{ bom?.project_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ bom?.created_at?.slice(0, 10) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ bom?.updated_at?.slice(0, 16) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ bom?.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" style="margin-top:16px">
      <el-tabs v-model="activeTab">
        <!-- BomItem 管理 -->
        <el-tab-pane label="BOM物料清单" name="items">
          <div class="table-toolbar">
            <div class="left">
              <el-button type="primary" @click="showItemForm()">
                <el-icon><Plus /></el-icon> 添加物料
              </el-button>
              <el-button v-if="itemSelection.length" type="danger" @click="handleBatchDeleteItems">
                批量删除 ({{ itemSelection.length }})
              </el-button>
            </div>
          </div>

          <el-table :data="items" v-loading="itemLoading" stripe size="small" empty-text="暂无物料项"
            @selection-change="(rows: any[]) => itemSelection = rows">
            <el-table-column type="selection" width="45" />
            <el-table-column prop="item_no" label="序号" width="80" />
            <el-table-column prop="material_code" label="物料编码" width="150" />
            <el-table-column prop="material_name" label="物料名称" min-width="160" />
            <el-table-column prop="material_spec" label="规格型号" width="140" />
            <el-table-column prop="quantity" label="用量" width="100" />
            <el-table-column label="损耗率" width="100">
              <template #default="{ row }">
                <span v-if="Number(row.loss_rate) > 0" style="color:#e6a23c">
                  {{ row.loss_rate }}%
                </span>
                <span v-else style="color:#c0c4cc">—</span>
              </template>
            </el-table-column>
            <el-table-column label="实际用量" width="110">
              <template #default="{ row }">
                {{ calcActualQty(row) }}
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="80" />
            <el-table-column prop="remark" label="备注" min-width="120" />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="showItemForm(row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteItem(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- BomChange 管理 -->
        <el-tab-pane label="变更记录" name="changes">
          <div class="table-toolbar">
            <div class="left">
              <el-button type="primary" @click="showChangeForm()">
                <el-icon><Plus /></el-icon> 新建变更
              </el-button>
            </div>
            <div class="right">
              <el-select v-model="changeFilter.status" placeholder="状态" clearable style="width:120px" @change="loadChanges">
                <el-option v-for="s in changeStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
              <el-button @click="loadChanges">刷新</el-button>
            </div>
          </div>

          <el-table :data="changes" v-loading="changeLoading" stripe size="small" empty-text="暂无变更">
            <el-table-column prop="code" label="变更编号" width="160" />
            <el-table-column prop="change_type" label="变更类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="changeTypeTag(row.change_type)">{{ changeTypeLabel(row.change_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="变更原因" min-width="180" show-overflow-tooltip />
            <el-table-column prop="before_version" label="变更前" width="100" />
            <el-table-column prop="after_version" label="变更后" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="changeStatusTag(row.status)">{{ changeStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="showChangeForm(row)">查看</el-button>
                <el-button link type="danger" @click="handleDeleteChange(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination v-if="changeTotal > 20"
            v-model:current-page="changePage" :page-size="20" :total="changeTotal"
            layout="total, prev, pager, next" @change="loadChanges" style="margin-top:16px;justify-content:flex-end" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- BomItem 弹窗 -->
    <el-dialog v-model="itemFormVisible" :title="itemFormMode === 'create' ? '添加物料' : '编辑物料项'" width="560px">
      <el-form :model="itemForm" label-width="90px">
        <el-form-item label="选择物料" required>
          <el-select v-model="itemForm.material_id" placeholder="搜索物料编码/名称" filterable clearable style="width:100%"
            :disabled="itemFormMode === 'edit'">
            <el-option v-for="m in materials" :key="m.id" :label="`${m.code} - ${m.name}`" :value="m.id">
              <span>{{ m.code }}</span>&nbsp;
              <span style="color:#999;font-size:12px">{{ m.name }} {{ m.spec }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="序号">
          <el-input-number v-model="itemForm.item_no" :min="1" />
        </el-form-item>
        <el-form-item label="用量" required>
          <el-input-number v-model="itemForm.quantity" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="损耗率">
          <el-input-number v-model="itemForm.loss_rate" :min="0" :max="100" :precision="2" :step="0.5" style="width:100%">
            <template #suffix>%</template>
          </el-input-number>
          <div style="font-size:12px;color:#909399;line-height:1.6;margin-top:4px">
            实际需求量 = 用量 × (1 + 损耗率%) = <b style="color:#409eff">{{ calcFormActualQty() }}</b>
          </div>
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="itemForm.unit" style="width:50%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="itemForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="itemSubmitting" @click="handleSubmitItem">确定</el-button>
      </template>
    </el-dialog>

    <!-- BomChange 弹窗 -->
    <el-dialog v-model="changeFormVisible" :title="changeFormMode === 'create' ? '新建变更' : '变更详情'" width="640px">
      <el-form :model="changeForm" label-width="90px" :disabled="changeFormMode === 'view'">
        <el-form-item label="变更类型" required>
          <el-select v-model="changeForm.change_type" style="width:100%">
            <el-option v-for="t in changeTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="变更前版本" required>
          <el-input v-model="changeForm.before_version" />
        </el-form-item>
        <el-form-item label="变更后版本" required>
          <el-input v-model="changeForm.after_version" />
        </el-form-item>
        <el-form-item label="变更原因" required>
          <el-input v-model="changeForm.reason" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="状态" v-if="changeFormMode === 'view' || changeForm.id">
          <el-select v-model="changeForm.status" style="width:100%" :disabled="changeFormMode === 'view'">
            <el-option v-for="s in changeStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="changeForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="changeFormVisible = false">关闭</el-button>
        <el-button v-if="changeFormMode !== 'view'" type="primary" :loading="changeSubmitting" @click="handleSubmitChange">
          {{ changeFormMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { bomApi } from '@/api'

const route = useRoute()
const bomId = Number(route.params.id)

const activeTab = ref('items')
const loading = ref(false)
const bom = ref<any>(null)

// BomItems
const items = ref<any[]>([])
const itemLoading = ref(false)
const itemSubmitting = ref(false)
const itemFormVisible = ref(false)
const itemFormMode = ref<'create' | 'edit'>('create')
const itemSelection = ref<any[]>([])
const materials = ref<any[]>([])

const itemForm = reactive({
  id: 0,
  material_id: null as number | null,
  item_no: 10,
  quantity: 1,
  loss_rate: 0,
  unit: '',
  remark: '',
})

// BomChanges
const changes = ref<any[]>([])
const changeLoading = ref(false)
const changeSubmitting = ref(false)
const changeFormVisible = ref(false)
const changeFormMode = ref<'create' | 'edit' | 'view'>('create')
const changeTotal = ref(0)
const changePage = ref(1)
const changeFilter = reactive({ status: '' })

const changeForm = reactive({
  id: 0,
  change_type: 'modify',
  before_version: '',
  after_version: '',
  reason: '',
  status: 'draft',
  remark: '',
})

const statusTag = (s: string) => ({ draft: 'info', reviewing: 'warning', released: 'success', obsolete: 'danger' }[s] || 'info')
const statusLabel = (s: string) => ({ draft: '草稿', reviewing: '审核中', released: '已发布', obsolete: '已作废' }[s] || s)

const changeTypeOpts = [
  { label: '修改', value: 'modify' },
  { label: '新增', value: 'add' },
  { label: '删除', value: 'remove' },
  { label: '替换', value: 'replace' },
]
const changeStatusOpts = [
  { label: '草稿', value: 'draft' },
  { label: '审核中', value: 'reviewing' },
  { label: '已批准', value: 'approved' },
  { label: '已实施', value: 'implemented' },
  { label: '已驳回', value: 'rejected' },
]
const changeTypeTag = (t: string): any => ({ modify: '', add: 'success', remove: 'danger', replace: 'warning' }[t] || '')
const changeTypeLabel = (t: string) => changeTypeOpts.find(o => o.value === t)?.label || t
const changeStatusTag = (s: string): any => ({ draft: 'info', reviewing: 'warning', approved: 'success', implemented: '', rejected: 'danger' }[s] || 'info')
const changeStatusLabel = (s: string) => changeStatusOpts.find(o => o.value === s)?.label || s

// 计算实际用量（表格列）
function calcActualQty(row: any): string {
  const qty = Number(row.quantity) || 0
  const loss = Number(row.loss_rate) || 0
  const actual = qty * (1 + loss / 100)
  return actual.toFixed(2)
}

// 计算表单中的实际用量（实时预览）
function calcFormActualQty(): string {
  const qty = Number(itemForm.quantity) || 0
  const loss = Number(itemForm.loss_rate) || 0
  const actual = qty * (1 + loss / 100)
  return actual.toFixed(2)
}

// Load BOM header
const loadBom = async () => {
  loading.value = true
  try {
    const res: any = await bomApi.getBom(bomId)
    bom.value = res
    changeForm.before_version = res.version
    changeForm.after_version = res.version
  } finally {
    loading.value = false
  }
}

// Load BomItems
const loadItems = async () => {
  itemLoading.value = true
  try {
    const res: any = await bomApi.getBomItems(bomId)
    items.value = res.items || []
  } finally {
    itemLoading.value = false
  }
}

// Load materials for dropdown
const loadMaterials = async () => {
  try {
    const res: any = await bomApi.listMaterials({ page: 1, page_size: 200, status: 'active' })
    materials.value = res.items || []
  } catch { /* ignore */ }
}

// Load BomChanges
const loadChanges = async () => {
  changeLoading.value = true
  try {
    const res: any = await bomApi.listChanges({ bom_header_id: bomId, status: changeFilter.status || undefined, page: changePage.value, page_size: 20 })
    changes.value = res.items || []
    changeTotal.value = res.total || 0
  } finally {
    changeLoading.value = false
  }
}

// --- BomItem handlers ---
const showItemForm = (row?: any) => {
  loadMaterials()
  if (row) {
    itemFormMode.value = 'edit'
    Object.assign(itemForm, {
      id: row.id, material_id: row.material_id, item_no: row.item_no,
      quantity: Number(row.quantity) || 0, loss_rate: Number(row.loss_rate) || 0,
      unit: row.unit, remark: row.remark || '',
    })
  } else {
    itemFormMode.value = 'create'
    Object.assign(itemForm, { id: 0, material_id: null, item_no: (items.value.length + 1) * 10, quantity: 1, loss_rate: 0, unit: '', remark: '' })
  }
  itemFormVisible.value = true
}

const handleSubmitItem = async () => {
  if (!itemForm.material_id) {
    ElMessage.warning('请选择物料')
    return
  }
  itemSubmitting.value = true
  try {
    const payload = {
      material_id: itemForm.material_id,
      item_no: itemForm.item_no,
      quantity: String(itemForm.quantity),
      loss_rate: String(itemForm.loss_rate),
      unit: itemForm.unit,
      remark: itemForm.remark,
    }
    if (itemFormMode.value === 'create') {
      await bomApi.addBomItem(bomId, payload)
      ElMessage.success('添加成功')
    } else {
      await bomApi.updateBomItem(bomId, itemForm.id, payload)
      ElMessage.success('更新成功')
    }
    itemFormVisible.value = false
    loadItems()
  } finally {
    itemSubmitting.value = false
  }
}

const handleDeleteItem = async (row: any) => {
  await ElMessageBox.confirm('确定要删除该物料项吗？', '提示', { type: 'warning' })
  await bomApi.deleteBomItem(bomId, row.id)
  ElMessage.success('已删除')
  loadItems()
}

const handleBatchDeleteItems = async () => {
  const ids = itemSelection.value.map((i: any) => i.id)
  await ElMessageBox.confirm(`确定要批量删除 ${ids.length} 个物料项吗？`, '警告', { type: 'warning' })
  await bomApi.batchDeleteBomItems(ids)
  ElMessage.success('批量删除成功')
  itemSelection.value = []
  loadItems()
}

// --- BomChange handlers ---
const showChangeForm = async (row?: any) => {
  if (row) {
    changeFormMode.value = row.status === 'draft' ? 'edit' : 'view'
    Object.assign(changeForm, {
      id: row.id, change_type: row.change_type,
      before_version: row.before_version, after_version: row.after_version,
      reason: row.reason || '', status: row.status, remark: row.remark || '',
    })
  } else {
    changeFormMode.value = 'create'
    Object.assign(changeForm, {
      id: 0, change_type: 'modify',
      before_version: bom.value?.version || 'V1.0',
      after_version: '',
      reason: '', status: 'draft', remark: '',
    })
  }
  changeFormVisible.value = true
}

const handleSubmitChange = async () => {
  changeSubmitting.value = true
  try {
    const payload = {
      bom_header_id: bomId,
      change_type: changeForm.change_type,
      before_version: changeForm.before_version,
      after_version: changeForm.after_version,
      reason: changeForm.reason,
      status: changeForm.status,
      remark: changeForm.remark,
    }
    if (changeFormMode.value === 'create') {
      await bomApi.createChange(payload)
      ElMessage.success('变更已创建')
    } else {
      await bomApi.updateChange(changeForm.id, payload)
      ElMessage.success('变更已更新')
    }
    changeFormVisible.value = false
    loadChanges()
  } finally {
    changeSubmitting.value = false
  }
}

const handleDeleteChange = async (row: any) => {
  await ElMessageBox.confirm(`确定要删除变更记录 \"${row.code}\" 吗？`, '警告', { type: 'warning' })
  await bomApi.deleteChange(row.id)
  ElMessage.success('已删除')
  loadChanges()
}

onMounted(() => {
  loadBom()
  loadItems()
  loadChanges()
})
</script>
