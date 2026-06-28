<template>
  <div class="page-container">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>库存管理</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="stats-bar" v-if="statsOverview.total_items > 0">
      <div class="stat-card normal">
        <span class="stat-num">{{ statsOverview.normal_count }}</span>
        <span class="stat-label">正常</span>
      </div>
      <div class="stat-card warning">
        <span class="stat-num">{{ statsOverview.low_stock_count }}</span>
        <span class="stat-label">低库存</span>
      </div>
      <div class="stat-card danger">
        <span class="stat-num">{{ statsOverview.out_of_stock_count }}</span>
        <span class="stat-label">缺货</span>
      </div>
      <div class="stat-card expired">
        <span class="stat-num">{{ statsOverview.expired_count }}</span>
        <span class="stat-label">过期</span>
      </div>
      <div class="stat-card info">
        <span class="stat-num">{{ statsOverview.total_quantity }}</span>
        <span class="stat-label">总库存量</span>
      </div>
    </div>

    <el-card shadow="never" style="margin-top:12px">
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <!-- ========== Tab1: 库存列表 ========== -->
        <el-tab-pane label="库存列表" name="list">
          <div class="table-toolbar">
            <div class="left">
              <el-button type="primary" @click="showCreateInventory"><el-icon><Plus /></el-icon> 新增库存</el-button>
            </div>
            <div class="right">
              <el-select v-model="listFilter.warehouse" placeholder="仓库" clearable style="width:130px" @change="onListFilterChange">
                <el-option v-for="w in warehouseList" :key="w.name" :label="w.name" :value="w.name" />
              </el-select>
              <el-select v-model="listFilter.status" placeholder="状态" clearable style="width:110px" @change="onListFilterChange">
                <el-option label="正常" value="normal" />
                <el-option label="低库存" value="low_stock" />
                <el-option label="缺货" value="out_of_stock" />
                <el-option label="过期" value="expired" />
              </el-select>
              <el-input v-model="listFilter.keyword" placeholder="物料编码/名称" style="width:180px" clearable @keyup.enter="loadInventory" />
              <el-button type="primary" @click="loadInventory">搜索</el-button>
            </div>
          </div>

          <el-table :data="inventoryList" v-loading="listLoading" stripe size="small" empty-text="暂无库存记录">
            <el-table-column prop="material_code" label="物料编码" width="140" />
            <el-table-column prop="material_name" label="物料名称" min-width="160" />
            <el-table-column prop="material_spec" label="规格型号" width="120" />
            <el-table-column prop="warehouse" label="仓库" width="100" />
            <el-table-column label="库存" width="110" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.quantity <= 0 ? '#f56c6c' : row.quantity <= row.safety_stock ? '#e6a23c' : '#303133', fontWeight: 500 }">
                  {{ row.quantity }} {{ row.unit || '' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="safety_stock" label="安全库存" width="90" align="right" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="statusTag(row.status)">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="库位" width="90" />
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="showOpDialog('inbound', row)">入库</el-button>
                <el-button link type="warning" size="small" :disabled="row.quantity <= 0" @click="showOpDialog('outbound', row)">出库</el-button>
                <el-button link type="success" size="small" :disabled="row.quantity <= 0" @click="showOpDialog('borrow', row)">领用</el-button>
                <el-button link type="primary" size="small" @click="showOpDialog('check', row)">盘点</el-button>
                <el-tooltip content="存在库存数量时不可删除" :disabled="row.quantity <= 0">
                  <span><el-button link type="danger" size="small" :disabled="row.quantity > 0" @click="handleDeleteItem(row)">删除</el-button></span>
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination v-if="listTotal > 20" v-model:current-page="listPage" :page-size="20" :total="listTotal"
            layout="total, prev, pager, next" @change="loadInventory" style="margin-top:16px;justify-content:flex-end" />
        </el-tab-pane>

        <!-- ========== Tab2: 交易记录 ========== -->
        <el-tab-pane label="交易记录" name="transactions">
          <div class="table-toolbar">
            <div class="right">
              <el-select v-model="txFilter.type" placeholder="交易类型" clearable style="width:130px" @change="onTxFilterChange">
                <el-option v-for="t in txTypes" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
              <el-date-picker v-model="txFilter.dates" type="daterange" range-separator="至"
                start-placeholder="开始" end-placeholder="结束" style="width:240px" @change="onTxFilterChange" />
              <el-input v-model="txFilter.keyword" placeholder="物料/单号" style="width:150px" clearable @keyup.enter="loadTransactions" />
              <el-button type="primary" @click="loadTransactions">搜索</el-button>
            </div>
          </div>

          <el-table :data="txList" v-loading="txLoading" stripe size="small" empty-text="暂无交易记录">
            <el-table-column prop="transaction_no" label="单号" width="180" />
            <el-table-column label="类型" width="80">
              <template #default="{ row }">{{ txTypeLabel(row.transaction_type) }}</template>
            </el-table-column>
            <el-table-column prop="material_name" label="物料" min-width="140" />
            <el-table-column label="数量" width="100" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.quantity > 0 ? '#67c23a' : '#f56c6c', fontWeight: 500 }">
                  {{ row.quantity > 0 ? '+' : '' }}{{ row.quantity.toFixed(2) }} {{ row.unit || '' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="库存变动" width="140" align="center">
              <template #default="{ row }">{{ row.before_qty }} → {{ row.after_qty }}</template>
            </el-table-column>
            <el-table-column prop="warehouse" label="仓库" width="90" />
            <el-table-column prop="operator_name" label="操作人" width="90" />
            <el-table-column prop="created_at" label="时间" width="150">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16) }}</template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
          </el-table>

          <el-pagination v-if="txTotal > 20" v-model:current-page="txPage" :page-size="20" :total="txTotal"
            layout="total, prev, pager, next" @change="loadTransactions" style="margin-top:16px;justify-content:flex-end" />
        </el-tab-pane>

        <!-- ========== Tab3: 统计分析 ========== -->
        <el-tab-pane label="统计分析" name="stats">
          <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px">
            <div v-for="s in warehouseStats" :key="s.warehouse" class="wh-card">
              <div class="wh-name">{{ s.warehouse }}</div>
              <div class="wh-row"><span>物料数</span><b>{{ s.item_count }}</b></div>
              <div class="wh-row"><span>总库存</span><b>{{ s.total_quantity }}</b></div>
              <div class="wh-row"><span>低库存</span><b :class="{ 'warn': s.low_stock_count > 0 }">{{ s.low_stock_count }}</b></div>
            </div>
          </div>

          <div class="table-toolbar">
            <span style="font-weight:500">周转分析（最近 <el-input-number v-model="turnoverDays" :min="7" :max="180" :step="7" size="small" style="width:100px" @change="loadTurnover" /> 天）</span>
          </div>
          <el-table :data="turnoverList" v-loading="turnoverLoading" stripe size="small" empty-text="暂无数据">
            <el-table-column prop="material_code" label="物料编码" width="130" />
            <el-table-column prop="material_name" label="物料名称" min-width="140" />
            <el-table-column prop="warehouse" label="仓库" width="90" />
            <el-table-column prop="begin_qty" label="期初" width="80" align="right" />
            <el-table-column label="期间入库" width="90" align="right">
              <template #default="{ row }"><span style="color:#67c23a">+{{ row.period_in }}</span></template>
            </el-table-column>
            <el-table-column label="期间出库" width="90" align="right">
              <template #default="{ row }"><span style="color:#f56c6c">-{{ row.period_out }}</span></template>
            </el-table-column>
            <el-table-column prop="end_qty" label="期末" width="80" align="right" />
            <el-table-column prop="avg_qty" label="平均库存" width="90" align="right" />
            <el-table-column label="周转率" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.turnover_rate > 2 ? 'success' : row.turnover_rate > 1 ? '' : 'warning'">
                  {{ row.turnover_rate.toFixed(2) }}x
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ========== Tab4: 仓库管理 ========== -->
        <el-tab-pane label="仓库管理" name="warehouses">
          <div class="table-toolbar">
            <div class="left">
              <el-button type="primary" @click="showCreateWarehouse"><el-icon><Plus /></el-icon> 新增仓库</el-button>
            </div>
          </div>
          <el-table :data="warehouseList" v-loading="whLoading" stripe size="small" empty-text="暂无仓库">
            <el-table-column prop="code" label="编码" width="120" />
            <el-table-column prop="name" label="名称" min-width="140" />
            <el-table-column prop="location" label="位置" width="150" />
            <el-table-column prop="manager" label="负责人" width="100" />
            <el-table-column prop="contact" label="电话" width="120" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="showEditWarehouse(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteWarehouse(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ====== 操作弹窗 ====== -->
    <el-dialog v-model="opDialogVisible" :title="opDialogTitle" width="480px" @close="resetOpForm">
      <el-form :model="opForm" label-width="100px">
        <el-form-item label="物料">
          <el-input :value="opTargetItem?.material_name" disabled />
        </el-form-item>
        <el-form-item label="仓库">
          <el-input :value="`${opTargetItem?.warehouse} · 当前库存 ${opTargetItem?.quantity}`" disabled />
        </el-form-item>
        <el-form-item label="数量" required>
          <el-input-number v-model="opForm.quantity" :min="0.01" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item v-if="opType === 'borrow'" label="预计归还">
          <el-date-picker v-model="opForm.expected_return_date" type="date" placeholder="选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item v-if="opType === 'transfer'" label="目标仓库" required>
          <el-select v-model="opForm.target_warehouse" placeholder="选择目标仓库" style="width:100%" filterable allow-create>
            <el-option v-for="w in warehouseList" :key="w.name" :label="w.name" :value="w.name" :disabled="w.name === opTargetItem?.warehouse" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="opType === 'check'" label="">
          <span style="color:#909399;font-size:12px">填实际盘点数量，系统自动计算差值</span>
        </el-form-item>
        <el-form-item label="关联项目">
          <el-select v-model="opForm.related_project_id" placeholder="可选" clearable style="width:100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="opForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="opDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="opSubmitting" @click="handleOpSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- ====== 新增库存弹窗 ====== -->
    <el-dialog v-model="createDialogVisible" title="新增库存" width="500px" @close="resetCreateForm">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="物料" required>
          <el-select v-model="createForm.material_id" placeholder="搜索物料编码/名称" filterable style="width:100%">
            <el-option v-for="m in materials" :key="m.id" :label="`${m.code} - ${m.name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="仓库" required>
          <el-select v-model="createForm.warehouse" placeholder="选择仓库" filterable style="width:100%">
            <el-option v-for="w in warehouseList" :key="w.name" :label="w.name" :value="w.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="库位">
          <el-input v-model="createForm.location" placeholder="如: A-01-03" />
        </el-form-item>
        <el-form-item label="初始库存">
          <el-input-number v-model="createForm.quantity" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="createForm.unit" style="width:40%" />
        </el-form-item>
        <el-form-item label="安全库存">
          <el-input-number v-model="createForm.safety_stock" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="最大库存">
          <el-input-number v-model="createForm.max_stock" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="保质期(天)">
          <el-input-number v-model="createForm.shelf_life_days" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="过期日期">
          <el-date-picker v-model="createForm.expiry_date" type="date" placeholder="选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="handleCreateInventory">确定</el-button>
      </template>
    </el-dialog>

    <!-- ====== 仓库管理弹窗 ====== -->
    <el-dialog v-model="whDialogVisible" :title="whDialogTitle" width="480px" @close="resetWhForm">
      <el-form :model="whForm" label-width="80px">
        <el-form-item label="编码" required>
          <el-input v-model="whForm.code" :disabled="whEditMode === 'edit'" placeholder="如 WH-01" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="whForm.name" placeholder="如 主仓库" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="whForm.location" placeholder="如 A栋1楼" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="whForm.manager" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="whForm.contact" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="whForm.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="whForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="whDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="whSubmitting" @click="handleWhSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { inventoryApi, projectApi, bomApi } from '@/api'

const activeTab = ref('list')
const projects = ref<any[]>([])
const materials = ref<any[]>([])

// ==== Stats ====
const statsOverview = reactive({ total_items: 0, total_quantity: 0, normal_count: 0, low_stock_count: 0, out_of_stock_count: 0, expired_count: 0 })
const warehouseStats = ref<any[]>([])
const turnoverList = ref<any[]>([])
const turnoverDays = ref(30)
const turnoverLoading = ref(false)

// ==== Inventory List ====
const inventoryList = ref<any[]>([])
const listLoading = ref(false)
const listTotal = ref(0)
const listPage = ref(1)
const listFilter = reactive({ warehouse: '', status: '', keyword: '', page: 1, page_size: 20 })

// ==== Transactions ====
const txList = ref<any[]>([])
const txLoading = ref(false)
const txTotal = ref(0)
const txPage = ref(1)
const txFilter = reactive({ type: '', keyword: '', dates: null as any, page: 1, page_size: 20 })
const txTypes = [
  { label: '入库', value: 'inbound' }, { label: '出库', value: 'outbound' },
  { label: '领用', value: 'borrow' }, { label: '归还', value: 'return_transfer' },
  { label: '盘点', value: 'check' }, { label: '调拨入库', value: 'transfer_in' },
  { label: '调拨出库', value: 'transfer_out' }, { label: '调整', value: 'adjust' },
]

// ==== Operations ====
const opDialogVisible = ref(false)
const opSubmitting = ref(false)
const opType = ref('')
const opDialogTitle = ref('')
const opTargetItem = ref<any>(null)
const opForm = reactive({ quantity: 0, expected_return_date: null as any, target_warehouse: '', related_project_id: null as number | null, remark: '' })

// ==== Create Inventory ====
const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const createForm = reactive({
  material_id: null as number | null, warehouse: '', location: '',
  quantity: 0, unit: '', safety_stock: 0, max_stock: 0,
  shelf_life_days: null as number | null, expiry_date: null as any, remark: '',
})

// ==== Warehouse Management ====
const warehouseList = ref<any[]>([])
const whLoading = ref(false)
const whDialogVisible = ref(false)
const whSubmitting = ref(false)
const whEditMode = ref<'create' | 'edit'>('create')
const whDialogTitle = ref('新增仓库')
const whEditId = ref(0)
const whForm = reactive({
  code: '', name: '', location: '', manager: '', contact: '',
  is_active: true, remark: '',
})

// Helpers
const statusTag = (s: string) => ({ normal: 'success', low_stock: 'warning', out_of_stock: 'danger', expired: 'info' }[s] || 'info')
const statusLabel = (s: string) => ({ normal: '正常', low_stock: '低库存', out_of_stock: '缺货', expired: '过期' }[s] || s)
const txTypeLabel = (t: string) => txTypes.find(x => x.value === t)?.label || t
const opLabelMap: Record<string, string> = {
  inbound: '入库', outbound: '出库', borrow: '领用', check: '盘点', transfer: '调拨',
}

// ===== LOAD =====
async function loadStats() {
  try {
    const res: any = await inventoryApi.overview()
    Object.assign(statsOverview, res)
  } catch { /* */ }
}
async function loadWarehouseStats() {
  try {
    const res: any = await inventoryApi.byWarehouse()
    warehouseStats.value = res || []
  } catch { /* */ }
}
async function loadTurnover() {
  turnoverLoading.value = true
  try {
    const res: any = await inventoryApi.turnover(turnoverDays.value)
    turnoverList.value = res.items || []
  } finally { turnoverLoading.value = false }
}

async function loadInventory() {
  listLoading.value = true
  try {
    const res: any = await inventoryApi.list({ ...listFilter, page: listPage.value, page_size: 20 })
    inventoryList.value = res.items || []
    listTotal.value = res.total || 0
  } finally { listLoading.value = false }
}

const onListFilterChange = () => {
  listPage.value = 1
  loadInventory()
}

async function loadTransactions() {
  txLoading.value = true
  try {
    const params: any = { ...txFilter, page: txPage.value, page_size: 20 }
    if (params.dates) {
      params.date_from = params.dates[0]; params.date_to = params.dates[1]
      delete params.dates
    }
    if (params.type) { params.transaction_type = params.type; delete params.type }
    const res: any = await inventoryApi.transactions(params)
    txList.value = res.items || []
    txTotal.value = res.total || 0
  } finally { txLoading.value = false }
}

const onTxFilterChange = () => {
  txPage.value = 1
  loadTransactions()
}

async function loadWarehouses() {
  try {
    const res: any = await inventoryApi.warehouseList()
    warehouseList.value = res || []
  } catch { /* */ }
}
async function loadProjects() {
  try {
    const res: any = await projectApi.list({ page: 1, page_size: 200 })
    projects.value = res.items || []
  } catch { /* */ }
}
async function loadMaterials() {
  try {
    const res: any = await bomApi.listMaterials({ page: 1, page_size: 500, status: 'active' })
    materials.value = res.items || []
  } catch { /* */ }
}

function handleTabClick() {
  if (activeTab.value === 'stats') { loadWarehouseStats(); loadTurnover() }
  if (activeTab.value === 'transactions') loadTransactions()
  if (activeTab.value === 'warehouses') loadWarehouses()
}

// ===== Create Inventory =====
function showCreateInventory() {
  loadMaterials(); loadWarehouses()
  Object.assign(createForm, { material_id: null, warehouse: '', location: '', quantity: 0, unit: '', safety_stock: 0, max_stock: 0, shelf_life_days: null, expiry_date: null, remark: '' })
  if (warehouseList.value.length > 0) {
    createForm.warehouse = warehouseList.value[0].name
  }
  createDialogVisible.value = true
}
function resetCreateForm() { /* placeholder */ }
async function handleCreateInventory() {
  if (!createForm.material_id || !createForm.warehouse) { ElMessage.warning('请选择物料和仓库'); return }
  createSubmitting.value = true
  try {
    const payload: any = { ...createForm }
    if (payload.expiry_date) payload.expiry_date = new Date(payload.expiry_date).toISOString().slice(0, 10)
    await inventoryApi.create(payload)
    ElMessage.success('库存创建成功')
    createDialogVisible.value = false
    loadInventory(); loadStats()
  } finally { createSubmitting.value = false }
}

// ===== Operations =====
function showOpDialog(type: string, item: any) {
  opType.value = type
  opTargetItem.value = item
  opDialogTitle.value = `${opLabelMap[type]} — ${item.material_name}`
  opForm.quantity = 0
  opForm.expected_return_date = null
  opForm.target_warehouse = ''
  opForm.related_project_id = null
  opForm.remark = ''
  loadProjects()
  if (type === 'transfer') loadWarehouses()
  opDialogVisible.value = true
}
function resetOpForm() { /* */ }
async function handleOpSubmit() {
  if (opForm.quantity <= 0 && opType.value !== 'check') { ElMessage.warning('请填写数量'); return }
  if (opType.value === 'transfer' && !opForm.target_warehouse) { ElMessage.warning('请选择目标仓库'); return }
  opSubmitting.value = true
  try {
    const payload: any = {
      inventory_item_id: opTargetItem.value.id,
      quantity: opForm.quantity,
      related_project_id: opForm.related_project_id || undefined,
      remark: opForm.remark,
    }
    if (opType.value === 'borrow') payload.expected_return_date = opForm.expected_return_date
    if (opType.value === 'transfer') {
      payload.source_warehouse = opTargetItem.value.warehouse
      payload.target_warehouse = opForm.target_warehouse
    }
    const apiMap: Record<string, Function> = {
      inbound: inventoryApi.inbound, outbound: inventoryApi.outbound,
      borrow: inventoryApi.borrow, check: inventoryApi.check, transfer: inventoryApi.transfer,
    }
    const res: any = await apiMap[opType.value](payload)
    ElMessage.success(res.msg || '操作成功')
    opDialogVisible.value = false
    loadInventory(); loadStats()
  } finally { opSubmitting.value = false }
}

// ===== Delete =====
async function handleDeleteItem(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.material_name}」的库存记录吗？`, '警告', { type: 'warning' })
    await inventoryApi.remove(row.id)
    ElMessage.success('删除成功')
    loadInventory(); loadStats()
  } catch { /* */ }
}

// ===== Warehouse Management =====
function showCreateWarehouse() {
  whEditMode.value = 'create'
  whDialogTitle.value = '新增仓库'
  whEditId.value = 0
  Object.assign(whForm, { code: '', name: '', location: '', manager: '', contact: '', is_active: true, remark: '' })
  whDialogVisible.value = true
}
function showEditWarehouse(row: any) {
  whEditMode.value = 'edit'
  whDialogTitle.value = '编辑仓库'
  whEditId.value = row.id
  Object.assign(whForm, {
    code: row.code, name: row.name, location: row.location || '',
    manager: row.manager || '', contact: row.contact || '',
    is_active: row.is_active, remark: row.remark || '',
  })
  whDialogVisible.value = true
}
function resetWhForm() { /* */ }
async function handleWhSubmit() {
  if (!whForm.code || !whForm.name) { ElMessage.warning('请填写编码和名称'); return }
  whSubmitting.value = true
  try {
    if (whEditMode.value === 'create') {
      await inventoryApi.warehouseCreate({ ...whForm })
      ElMessage.success('仓库创建成功')
    } else {
      await inventoryApi.warehouseUpdate(whEditId.value, { ...whForm })
      ElMessage.success('仓库更新成功')
    }
    whDialogVisible.value = false
    loadWarehouses()
  } finally { whSubmitting.value = false }
}
async function handleDeleteWarehouse(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除仓库「${row.name}」吗？（仓库下有库存记录时无法删除）`, '警告', { type: 'warning' })
    await inventoryApi.warehouseDelete(row.id)
    ElMessage.success('删除成功')
    loadWarehouses()
  } catch { /* */ }
}

onMounted(() => {
  loadInventory(); loadStats(); loadWarehouses()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.table-toolbar .left, .table-toolbar .right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.stats-bar { display: flex; gap: 12px; margin-top: 12px; }
.stat-card { flex: 1; background: #f5f7fa; border-radius: 8px; padding: 12px 16px; text-align: center; border-left: 3px solid #dcdfe6; }
.stat-card.normal { border-left-color: #67c23a; }
.stat-card.warning { border-left-color: #e6a23c; }
.stat-card.danger { border-left-color: #f56c6c; }
.stat-card.expired { border-left-color: #909399; }
.stat-card.info { border-left-color: #409eff; }
.stat-num { display: block; font-size: 22px; font-weight: 600; color: #303133; }
.stat-label { display: block; font-size: 12px; color: #909399; margin-top: 2px; }
.wh-card { background: #f5f7fa; border-radius: 8px; padding: 12px 16px; min-width: 150px; }
.wh-name { font-weight: 500; font-size: 14px; margin-bottom: 8px; color: #303133; }
.wh-row { display: flex; justify-content: space-between; font-size: 13px; color: #606266; margin-bottom: 4px; }
.wh-row b { color: #303133; }
.wh-row b.warn { color: #e6a23c; }
</style>
