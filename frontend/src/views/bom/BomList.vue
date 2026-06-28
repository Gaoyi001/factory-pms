<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="物料管理" name="materials">
        <div class="table-toolbar">
          <div class="left">
            <el-button v-if="canOperate('bom:create')" type="primary" @click="showMaterialForm()">
              <el-icon><Plus /></el-icon> 新建物料
            </el-button>
            <el-button v-if="materialSelection.length" type="danger" @click="handleBatchDeleteMaterials">
              批量停用 ({{ materialSelection.length }})
            </el-button>
            <el-select v-model="materialFilter.material_type" placeholder="物料类型" clearable style="width:140px" @change="onMaterialFilterChange">
              <el-option v-for="t in materialTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
          </div>
          <div class="right">
            <el-input v-model="materialFilter.keyword" placeholder="搜索编码/名称" clearable style="width:220px" @keyup.enter="loadMaterials">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="loadMaterials">查询</el-button>
          </div>
        </div>

        <el-table :data="materials.items" v-loading="materialLoading" stripe size="small" empty-text="暂无物料"
          @selection-change="(rows: MaterialOut[]) => materialSelection = rows">
          <el-table-column type="selection" width="45" />
          <el-table-column prop="code" label="物料编码" width="150" />
          <el-table-column prop="name" label="物料名称" min-width="180" />
          <el-table-column prop="material_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ materialTypeLabel(row.material_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="spec" label="规格型号" width="150" />
          <el-table-column prop="unit" label="单位" width="80" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status==='active'?'success':'info'" size="small">
                {{ row.status === 'active' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canOperate('bom:update')" link type="primary" @click="showMaterialForm(row)">编辑</el-button>
              <el-button v-if="canOperate('bom:update')" link type="danger" @click="handleDeleteMaterial(row)">停用</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-model:current-page="materialPagination.page" v-model:page-size="materialPagination.page_size"
          :total="materials.total" layout="total, sizes, prev, pager, next" @change="loadMaterials"
          style="margin-top:16px;justify-content:flex-end" />
      </el-tab-pane>

      <el-tab-pane label="BOM清单" name="boms">
        <div class="table-toolbar">
          <div class="left">
            <el-button v-if="canOperate('bom:create')" type="primary" @click="showBomForm()">
              <el-icon><Plus /></el-icon> 新建BOM
            </el-button>
            <el-select v-model="bomFilter.status" placeholder="BOM状态" clearable style="width:140px" @change="onBomFilterChange">
              <el-option v-for="s in bomStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </div>
          <div class="right">
            <el-input v-model="bomFilter.keyword" placeholder="搜索编码/名称" clearable style="width:220px" @keyup.enter="loadBoms">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="loadBoms">查询</el-button>
          </div>
        </div>

        <el-table :data="boms.items" v-loading="bomLoading" stripe size="small" empty-text="暂无BOM">
          <el-table-column prop="code" label="BOM编号" width="150" />
          <el-table-column prop="name" label="BOM名称" min-width="180" />
          <el-table-column prop="version" label="版本" width="100" />
          <el-table-column prop="product_code" label="产品编码" width="140" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="bomStatusTag(row.status)" size="small">{{ bomStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canOperate('bom:update')" link type="primary" @click="showBomForm(row)">编辑</el-button>
              <el-button link @click="viewBomDetail(row)">详情</el-button>
              <el-button v-if="canOperate('bom:delete')" link type="danger" @click="handleDeleteBom(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-model:current-page="bomPagination.page" v-model:page-size="bomPagination.page_size"
          :total="boms.total" layout="total, sizes, prev, pager, next" @change="loadBoms"
          style="margin-top:16px;justify-content:flex-end" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="materialFormVisible" :title="materialFormMode==='create'?'新建物料':'编辑物料'" width="560px">
      <el-form ref="materialFormRef" :model="materialForm" :rules="materialFormRules" label-width="90px">
        <el-form-item label="物料编码" prop="code">
          <el-input v-model="materialForm.code" :disabled="materialFormMode==='edit'" />
        </el-form-item>
        <el-form-item label="物料名称" prop="name">
          <el-input v-model="materialForm.name" />
        </el-form-item>
        <el-form-item label="物料类型">
          <el-select v-model="materialForm.material_type" style="width:100%">
            <el-option v-for="t in materialTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格型号">
          <el-input v-model="materialForm.spec" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="materialForm.unit" style="width:50%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="materialForm.status" style="width:100%">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="materialForm.category" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="materialFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="materialSubmitting" @click="handleSubmitMaterial">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="bomFormVisible" :title="bomFormMode==='create'?'新建BOM':'编辑BOM'" width="600px">
      <el-form ref="bomFormRef" :model="bomForm" :rules="bomFormRules" label-width="90px">
        <el-form-item label="BOM名称" prop="name">
          <el-input v-model="bomForm.name" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="bomForm.project_id" placeholder="请选择" style="width:100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="bomForm.version" style="width:50%" />
        </el-form-item>
        <el-form-item label="产品编码">
          <el-input v-model="bomForm.product_code" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="bomForm.status" style="width:100%">
            <el-option v-for="s in bomStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="bomForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bomFormVisible=false">取消</el-button>
        <el-button type="primary" :loading="bomSubmitting" @click="handleSubmitBom">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { bomApi, projectApi } from '@/api'
import type { MaterialOut, BomHeaderOut } from '@/types/bom'

const router = useRouter()
const canOperate = inject<(perm: string) => boolean>('canOperate', () => true)

const activeTab = ref('materials')

const materialLoading = ref(false)
const materialSubmitting = ref(false)
const materialFormVisible = ref(false)
const materialFormMode = ref<'create'|'edit'>('create')
const materialFormRef = ref<FormInstance>()
const materialFormRules: FormRules = {
  code: [{ required: true, message: '请输入物料编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
}
const materials = reactive<{ items: MaterialOut[]; total: number }>({ items: [], total: 0 })
const materialSelection = ref<MaterialOut[]>([])
const materialPagination = reactive({ page: 1, page_size: 20 })
const materialFilter = reactive({ material_type: '', keyword: '' })

const bomLoading = ref(false)
const bomSubmitting = ref(false)
const bomFormVisible = ref(false)
const bomFormMode = ref<'create'|'edit'>('create')
const bomFormRef = ref<FormInstance>()
const bomFormRules: FormRules = {
  name: [{ required: true, message: '请输入BOM名称', trigger: 'blur' }],
}
const boms = reactive<{ items: BomHeaderOut[]; total: number }>({ items: [], total: 0 })
const projectOptions = ref<{ id: number; name: string }[]>([])
const bomPagination = reactive({ page: 1, page_size: 20 })
const bomFilter = reactive({ status: '', keyword: '' })

const materialTypeOpts = [
  { label: '原材料', value: 'raw_material' },
  { label: '半成品', value: 'semi_finished' },
  { label: '成品', value: 'finished' },
  { label: '辅料', value: 'auxiliary' },
  { label: '包材', value: 'packaging' },
  { label: '其他', value: 'other' },
]
const bomStatusOpts = [
  { label: '草稿', value: 'draft' },
  { label: '审核中', value: 'reviewing' },
  { label: '已发布', value: 'released' },
  { label: '已作废', value: 'obsolete' },
]

const materialTypeLabel = (t: string) => {
  const found = materialTypeOpts.find(o => o.value === t)
  return found ? found.label : t
}
const bomStatusTag = (s: string) => ({ draft: 'info', reviewing: 'warning', released: 'success', obsolete: 'danger' }[s] || 'info') as any
const bomStatusLabel = (s: string) => ({ draft: '草稿', reviewing: '审核中', released: '已发布', obsolete: '已作废' }[s] || s)

const materialForm = reactive({
  id: 0, code: '', name: '', material_type: 'raw_material',
  spec: '', unit: '个', status: 'active', category: '',
})

const bomForm = reactive({
  id: 0, name: '', project_id: null as number|null,
  version: 'V1.0', product_code: '', status: 'draft', description: '',
})

const loadMaterials = async () => {
  materialLoading.value = true
  try {
    const res = await bomApi.listMaterials({ ...materialPagination, material_type: materialFilter.material_type || undefined, keyword: materialFilter.keyword || undefined })
    materials.items = res.items || []
    materials.total = res.total || 0
  } finally { materialLoading.value = false }
}

const onMaterialFilterChange = () => {
  materialPagination.page = 1
  loadMaterials()
}

const loadBoms = async () => {
  bomLoading.value = true
  try {
    const res = await bomApi.listBoms({ ...bomPagination, status: bomFilter.status || undefined, keyword: bomFilter.keyword || undefined })
    boms.items = res.items || []
    boms.total = res.total || 0
  } finally { bomLoading.value = false }
}

const onBomFilterChange = () => {
  bomPagination.page = 1
  loadBoms()
}

const loadProjects = async () => {
  try {
    const res = await projectApi.list({ page: 1, page_size: 100 })
    projectOptions.value = (res.items || []).map((p: any) => ({ id: p.id, name: p.name }))
  } catch {}
}

const showMaterialForm = (row?: MaterialOut) => {
  if (row) {
    materialFormMode.value = 'edit'
    Object.assign(materialForm, { id: row.id, code: row.code, name: row.name, material_type: row.material_type, spec: row.spec, unit: row.unit, status: row.status, category: row.category })
  } else {
    materialFormMode.value = 'create'
    Object.assign(materialForm, { id: 0, code: '', name: '', material_type: 'raw_material', spec: '', unit: '个', status: 'active', category: '' })
  }
  materialFormVisible.value = true
}

const handleSubmitMaterial = async () => {
  if (!materialFormRef.value) return
  try { await materialFormRef.value.validate() } catch { return }
  materialSubmitting.value = true
  try {
    const payload: any = { ...materialForm }
    if (materialFormMode.value === 'create') {
      await bomApi.createMaterial(payload)
      ElMessage.success('创建成功')
    } else {
      await bomApi.updateMaterial(materialForm.id, payload)
      ElMessage.success('更新成功')
    }
    materialFormVisible.value = false
    loadMaterials()
  } finally { materialSubmitting.value = false }
}

const handleDeleteMaterial = async (row: MaterialOut) => {
  await ElMessageBox.confirm('确定要停用该物料吗？', '提示', { type: 'warning' })
  await bomApi.deleteMaterial(row.id)
  ElMessage.success('已停用')
  loadMaterials()
}

const showBomForm = async (row?: BomHeaderOut) => {
  if (!projectOptions.value.length) await loadProjects()
  if (row) {
    bomFormMode.value = 'edit'
    Object.assign(bomForm, { id: row.id, name: row.name, project_id: row.project_id, version: row.version, product_code: row.product_code, status: row.status, description: row.description })
  } else {
    bomFormMode.value = 'create'
    Object.assign(bomForm, { id: 0, name: '', project_id: null, version: 'V1.0', product_code: '', status: 'draft', description: '' })
  }
  bomFormVisible.value = true
}

const handleSubmitBom = async () => {
  if (!bomFormRef.value) return
  try { await bomFormRef.value.validate() } catch { return }
  bomSubmitting.value = true
  try {
    const payload: any = { name: bomForm.name, project_id: bomForm.project_id, version: bomForm.version, product_code: bomForm.product_code, status: bomForm.status, description: bomForm.description }
    if (bomFormMode.value === 'create') {
      await bomApi.createBom(payload)
      ElMessage.success('创建成功')
    } else {
      await bomApi.updateBom(bomForm.id, payload)
      ElMessage.success('更新成功')
    }
    bomFormVisible.value = false
    loadBoms()
  } finally { bomSubmitting.value = false }
}

const viewBomDetail = (row: BomHeaderOut) => {
  router.push(`/bom/${row.id}`)
}

const handleDeleteBom = async (row: BomHeaderOut) => {
  await ElMessageBox.confirm(`确定要删除BOM \"${row.name}\"吗？`, '警告', { type: 'warning' })
  await bomApi.deleteBom(row.id)
  ElMessage.success('已删除')
  loadBoms()
}

const handleBatchDeleteMaterials = async () => {
  const ids = materialSelection.value.map(m => m.id)
  await ElMessageBox.confirm(`确定要批量停用 ${ids.length} 个物料吗？`, '警告', { type: 'warning' })
  await bomApi.batchDeleteMaterials(ids)
  ElMessage.success('批量停用成功')
  materialSelection.value = []
  loadMaterials()
}

onMounted(() => {
  loadMaterials()
  loadBoms()
})
</script>
