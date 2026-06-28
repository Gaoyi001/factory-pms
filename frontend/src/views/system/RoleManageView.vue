<template>
  <div class="role-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <h2>角色权限管理</h2>
      <div class="toolbar-right">
        <el-button type="primary" @click="showAddRole">
          <el-icon><Plus /></el-icon> 新增角色
        </el-button>
      </div>
    </div>

    <!-- 左右分栏 -->
    <div class="split-layout">
      <!-- 左侧：角色列表 -->
      <aside class="role-list-panel">
        <div class="panel-header">
          <span>角色列表</span>
          <el-tag size="small" type="info">{{ roles.length }}</el-tag>
        </div>
        <div class="role-cards" v-loading="loading">
          <div
            v-for="role in roles"
            :key="role.id"
            class="role-card"
            :class="{
              active: selectedRole?.id === role.id,
              disabled: !role.is_active,
            }"
            @click="selectRole(role)"
          >
            <div class="role-card-header">
              <span class="role-name">{{ role.name }}</span>
              <el-tag v-if="isSystemRole(role)" size="small" type="warning">系统</el-tag>
              <el-tag v-else size="small" type="success">自定义</el-tag>
            </div>
            <div class="role-code">{{ role.code }}</div>
            <div class="role-card-footer">
              <span class="perm-count">
                <el-icon><Key /></el-icon>
                {{ role.permissions?.length || 0 }} 项权限
              </span>
              <el-dropdown trigger="click" @command="(cmd: string) => handleRoleAction(cmd, role)" @click.stop>
                <el-icon class="more-btn" @click.stop><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑角色</el-dropdown-item>
                    <el-dropdown-item v-if="role.code !== 'admin'" command="copy">复制权限</el-dropdown-item>
                    <el-dropdown-item v-if="role.code !== 'admin'" command="delete" divided>删除角色</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <el-empty v-if="!loading && roles.length === 0" description="暂无角色" />
        </div>
      </aside>

      <!-- 右侧：权限矩阵 + 审计 -->
      <section class="role-detail-panel">
        <template v-if="selectedRole">
          <!-- 角色信息条 -->
          <div class="detail-header">
            <div class="detail-title">
              <h3>{{ selectedRole.name }}</h3>
              <el-tag size="small">{{ selectedRole.code }}</el-tag>
              <el-tag v-if="selectedRole.is_active" size="small" type="success">启用</el-tag>
              <el-tag v-else size="small" type="danger">禁用</el-tag>
            </div>
            <div class="detail-desc">{{ selectedRole.description || '无描述' }}</div>
          </div>

          <!-- admin 提示 -->
          <el-alert
            v-if="selectedRole.code === 'admin'"
            title="系统管理员拥有全部权限，无需也无法手动分配"
            type="info"
            :closable="false"
            show-icon
            class="admin-alert"
          />

          <!-- 权限编辑区 -->
          <template v-else>
            <!-- 预设模板 + 工具按钮 -->
            <div class="perm-toolbar">
              <div class="perm-toolbar-left">
                <span class="toolbar-label">快速应用:</span>
                <el-button-group>
                  <el-button size="small" @click="applyTemplate('readonly')">只读模板</el-button>
                  <el-button size="small" @click="applyTemplate('full')">全权限模板</el-button>
                  <el-button size="small" @click="applyTemplate('custom')">清空</el-button>
                </el-button-group>
                <el-divider direction="vertical" />
                <el-select
                  v-model="copyFromId"
                  placeholder="从其他角色复制"
                  size="small"
                  style="width: 180px"
                  @change="copyPermissionsFrom"
                >
                  <el-option
                    v-for="r in roles.filter(x => x.id !== selectedRole.id)"
                    :key="r.id"
                    :label="`${r.name} (${r.permissions?.length || 0}项)`"
                    :value="r.id"
                  />
                </el-select>
              </div>
              <span class="perm-summary">
                已选 <b>{{ selectedCount }}</b> / {{ totalPermCount }} 项
              </span>
            </div>

            <!-- 权限矩阵 - 按模块分组 -->
            <div class="perm-groups" v-loading="permLoading">
              <div
                v-for="group in permGroups"
                :key="group.name"
                class="perm-group"
              >
                <div class="group-header" @click="toggleGroup(group)">
                  <el-icon class="group-arrow" :class="{ expanded: group.expanded }">
                    <ArrowRight />
                  </el-icon>
                  <span class="group-name">{{ group.label }}</span>
                  <el-tag size="small" type="info">
                    {{ group.checkedCount }}/{{ group.totalCount }}
                  </el-tag>
                  <el-checkbox
                    :model-value="group.checkedCount === group.totalCount && group.totalCount > 0"
                    :indeterminate="group.checkedCount > 0 && group.checkedCount < group.totalCount"
                    @change="(val: boolean) => toggleGroupAll(group, val)"
                    @click.stop
                    class="group-all"
                  >全选</el-checkbox>
                </div>
                <el-collapse-transition>
                  <div v-show="group.expanded" class="group-body">
                    <el-table :data="group.rows" border size="small">
                      <el-table-column prop="resourceLabel" label="资源" width="120" fixed>
                        <template #default="{ row }">
                          <span class="resource-name">{{ row.resourceLabel }}</span>
                          <span class="resource-code">{{ row.resource }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column
                        v-for="action in group.actions"
                        :key="action"
                        :label="actionMap[action] || action"
                        min-width="80"
                        align="center"
                      >
                        <template #default="{ row }">
                          <el-checkbox
                            v-if="row.actions[action]"
                            v-model="row.actions[action].checked"
                            @change="updateRowAll(row)"
                          />
                          <span v-else class="no-perm">—</span>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </el-collapse-transition>
              </div>
              <el-empty v-if="permGroups.length === 0 && !permLoading" description="暂无权限定义" />
            </div>

            <!-- 底部固定保存栏 -->
            <div class="save-bar">
              <div class="save-bar-info">
                <el-icon><InfoFilled /></el-icon>
                <span>修改后请点击保存，权限将立即生效</span>
              </div>
              <div class="save-bar-actions">
                <el-button @click="resetPerms">放弃修改</el-button>
                <el-button type="primary" :loading="saving" @click="savePerms">
                  <el-icon><Check /></el-icon> 保存权限
                </el-button>
              </div>
            </div>
          </template>

          <!-- 审计日志 -->
          <div class="audit-section">
            <div class="audit-header">
              <span class="audit-title">
                <el-icon><Clock /></el-icon> 权限变更记录
              </span>
              <el-button link type="primary" size="small" @click="loadAuditLogs" :loading="auditLoading">
                刷新
              </el-button>
            </div>
            <el-timeline v-if="auditLogs.length" class="audit-timeline">
              <el-timeline-item
                v-for="log in auditLogs"
                :key="log.id"
                :timestamp="log.created_at"
                placement="top"
                :type="log.detail === '无变更' ? 'info' : 'primary'"
              >
                <div class="audit-item">
                  <span class="audit-user">{{ log.username }}</span>
                  <span class="audit-action">{{ log.detail || '修改了权限' }}</span>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无变更记录" :image-size="60" />
          </div>
        </template>

        <el-empty v-else description="请从左侧选择一个角色" class="empty-center" />
      </section>
    </div>

    <!-- 新增/编辑角色对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingRole ? '编辑角色' : '新增角色'" width="420px">
      <el-form :model="roleForm" label-width="80px">
        <el-form-item label="角色代码">
          <el-input v-model="roleForm.code" :disabled="!!editingRole" placeholder="如: engineer" />
        </el-form-item>
        <el-form-item label="角色名称">
          <el-input v-model="roleForm.name" placeholder="如: 工程师" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" type="textarea" :rows="2" placeholder="角色描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="roleForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="roleForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Key, MoreFilled, ArrowRight, InfoFilled, Check, Clock,
} from '@element-plus/icons-vue'
import { roleApi, operationLogApi } from '@/api'

// ===== 资源/动作映射 =====
const resourceMap: Record<string, string> = {
  project: '项目管理', experiment: '实验管理', bom: '物料BOM', sample: '样品管理',
  document: '文档管理', user: '用户管理', department: '部门管理', role: '角色管理',
  warehouse: '仓库管理', inventory: '库存管理', material: '物料管理', log: '操作日志',
}
const actionMap: Record<string, string> = {
  create: '创建', read: '查看', update: '更新', delete: '删除', download: '下载',
  export: '导出', import: '导入', approve: '审批', assign: '分配', upload: '上传',
  borrow: '领用', return: '归还',
}

// 模块分组定义：将资源按业务模块归类
const GROUP_DEFS: { name: string; label: string; resources: string[] }[] = [
  { name: 'rd', label: '研发模块', resources: ['project', 'experiment', 'bom', 'sample', 'document'] },
  { name: 'inventory', label: '库存模块', resources: ['material', 'warehouse', 'inventory'] },
  { name: 'system', label: '系统管理', resources: ['user', 'department', 'role', 'log'] },
]

const systemRoles = ['admin', 'member', 'viewer', 'manager']

// ===== 状态 =====
const roles = ref<any[]>([])
const permissions = ref<any[]>([])
const loading = ref(false)
const permLoading = ref(false)
const saving = ref(false)

const selectedRole = ref<any>(null)
const copyFromId = ref<number | null>(null)

const dialogVisible = ref(false)
const editingRole = ref<any>(null)
const roleForm = ref({ code: '', name: '', description: '', sort_order: 0, is_active: true })

// 审计日志
const auditLogs = ref<any[]>([])
const auditLoading = ref(false)

/* ===== 权限矩阵数据结构 ===== */
interface PermCell {
  id: number
  checked: boolean
}
interface PermRow {
  resource: string
  resourceLabel: string
  actions: Record<string, PermCell>
  allChecked: boolean
}
interface PermGroup {
  name: string
  label: string
  resources: string[]
  rows: PermRow[]
  actions: string[]
  expanded: boolean
  checkedCount: number
  totalCount: number
}

// 使用 reactive 让分组内部变更可追踪
const permGroups = reactive<PermGroup[]>([])
// 保存初始权限快照，用于"放弃修改"
let initialSnapshot: number[] = []

const totalPermCount = computed(() => permissions.value.length)

const selectedCount = computed(() => {
  let count = 0
  permGroups.forEach((g) => {
    g.rows.forEach((row) => {
      Object.values(row.actions).forEach((cell) => {
        if (cell.checked) count++
      })
    })
  })
  return count
})

onMounted(() => {
  loadRoles()
  loadPermissions()
})

async function loadRoles() {
  loading.value = true
  try {
    const res = await roleApi.list()
    roles.value = res || []
    // 默认选中第一个非 admin 角色
    if (roles.value.length > 0 && !selectedRole.value) {
      const first = roles.value.find(r => r.code !== 'admin') || roles.value[0]
      selectRole(first)
    }
  } catch {
    ElMessage.error('加载角色失败')
  } finally {
    loading.value = false
  }
}

async function loadPermissions() {
  try {
    const res = await roleApi.listPermissions()
    permissions.value = res || []
  } catch {
    ElMessage.error('加载权限失败')
  }
}

function isSystemRole(role: any) {
  return systemRoles.includes(role.code)
}

/* ===== 选择角色 + 构建权限矩阵 ===== */
function selectRole(role: any) {
  selectedRole.value = role
  copyFromId.value = null
  if (role.code !== 'admin') {
    const selectedIds = (role.permissions || []).map((p: any) => p.id)
    buildPermGroups(selectedIds)
    initialSnapshot = [...selectedIds]
  } else {
    permGroups.splice(0, permGroups.length)
    initialSnapshot = []
  }
  loadAuditLogs()
}

function buildPermGroups(selectedIds: number[]) {
  permLoading.value = true
  permGroups.splice(0, permGroups.length)

  GROUP_DEFS.forEach((gdef) => {
    // 当前组内资源对应的权限
    const groupPerms = permissions.value.filter((p: any) => gdef.resources.includes(p.resource))
    if (groupPerms.length === 0) return

    // 该组涉及的动作
    const groupActions: string[] = []
    const actionSeen = new Set<string>()
    groupPerms.forEach((p) => {
      if (!actionSeen.has(p.action)) {
        actionSeen.add(p.action)
        groupActions.push(p.action)
      }
    })

    // 按资源构建行
    const rows: PermRow[] = gdef.resources
      .filter((res) => groupPerms.some((p) => p.resource === res))
      .map((resource) => {
        const actions: Record<string, PermCell> = {}
        groupPerms
          .filter((p) => p.resource === resource)
          .forEach((p: any) => {
            actions[p.action] = {
              id: p.id,
              checked: selectedIds.includes(p.id),
            }
          })
        return {
          resource,
          resourceLabel: resourceMap[resource] || resource,
          actions,
          allChecked: Object.values(actions).every((c) => c.checked),
        }
      })

    const checkedCount = rows.reduce(
      (sum, r) => sum + Object.values(r.actions).filter((c) => c.checked).length, 0
    )
    const totalCount = rows.reduce(
      (sum, r) => sum + Object.values(r.actions).length, 0
    )

    permGroups.push({
      name: gdef.name,
      label: gdef.label,
      resources: gdef.resources,
      rows,
      actions: groupActions,
      expanded: true,
      checkedCount,
      totalCount,
    })
  })
  permLoading.value = false
}

/* ===== 矩阵交互方法 ===== */
function toggleGroup(group: PermGroup) {
  group.expanded = !group.expanded
}

function toggleGroupAll(group: PermGroup, val: boolean) {
  group.rows.forEach((row) => {
    Object.keys(row.actions).forEach((action) => {
      row.actions[action].checked = val
    })
    row.allChecked = val
  })
  recountGroup(group)
}

function updateRowAll(row: PermRow) {
  row.allChecked = Object.values(row.actions).every((c) => c.checked)
  // 找到所属组并重算
  permGroups.forEach((g) => {
    if (g.rows.includes(row)) recountGroup(g)
  })
}

function recountGroup(group: PermGroup) {
  let checked = 0
  let total = 0
  group.rows.forEach((row) => {
    Object.values(row.actions).forEach((c) => {
      total++
      if (c.checked) checked++
    })
  })
  group.checkedCount = checked
  group.totalCount = total
}

/* ===== 预设模板 ===== */
function applyTemplate(type: 'readonly' | 'full' | 'custom') {
  permGroups.forEach((group) => {
    group.rows.forEach((row) => {
      Object.keys(row.actions).forEach((action) => {
        let val = false
        if (type === 'full') {
          val = true
        } else if (type === 'readonly') {
          // 只读模板：所有 read + download
          val = action === 'read' || action === 'download'
        }
        row.actions[action].checked = val
      })
      row.allChecked = Object.values(row.actions).every((c) => c.checked)
    })
    recountGroup(group)
  })
  const labels = { readonly: '只读模板', full: '全权限模板', custom: '清空' }
  ElMessage.success(`已应用${labels[type]}`)
}

/* ===== 从其他角色复制 ===== */
async function copyPermissionsFrom(roleId: number) {
  if (!roleId) return
  const source = roles.value.find(r => r.id === roleId)
  if (!source) return
  const sourceIds = (source.permissions || []).map((p: any) => p.id)
  permGroups.forEach((group) => {
    group.rows.forEach((row) => {
      Object.keys(row.actions).forEach((action) => {
        row.actions[action].checked = sourceIds.includes(row.actions[action].id)
      })
      row.allChecked = Object.values(row.actions).every((c) => c.checked)
    })
    recountGroup(group)
  })
  ElMessage.success(`已复制「${source.name}」的权限配置，请确认后保存`)
  copyFromId.value = null
}

/* ===== 放弃修改 ===== */
function resetPerms() {
  if (!selectedRole.value) return
  buildPermGroups(initialSnapshot)
  ElMessage.info('已放弃修改')
}

/* ===== 保存权限 ===== */
async function savePerms() {
  if (!selectedRole.value) return
  const selectedIds: number[] = []
  permGroups.forEach((group) => {
    group.rows.forEach((row) => {
      Object.values(row.actions).forEach((cell) => {
        if (cell.checked) selectedIds.push(cell.id)
      })
    })
  })
  saving.value = true
  try {
    await roleApi.assignPermissions(selectedRole.value.id, selectedIds)
    ElMessage.success('权限保存成功')
    initialSnapshot = [...selectedIds]
    await loadRoles()
    // 重新选中当前角色（保持选中状态）
    const updated = roles.value.find(r => r.id === selectedRole.value.id)
    if (updated) {
      selectedRole.value = updated
    }
    loadAuditLogs()
  } catch {
    // 错误已在拦截器中显示
  } finally {
    saving.value = false
  }
}

/* ===== 审计日志 ===== */
async function loadAuditLogs() {
  if (!selectedRole.value) return
  auditLoading.value = true
  try {
    const res: any = await operationLogApi.list({
      resource: 'role',
      resource_id: selectedRole.value.id,
      page: 1,
      page_size: 10,
    })
    auditLogs.value = res?.items || []
  } catch {
    auditLogs.value = []
  } finally {
    auditLoading.value = false
  }
}

/* ===== 角色新增/编辑/删除 ===== */
function showAddRole() {
  editingRole.value = null
  roleForm.value = { code: '', name: '', description: '', sort_order: 0, is_active: true }
  dialogVisible.value = true
}

function handleRoleAction(cmd: string, role: any) {
  if (cmd === 'edit') editRole(role)
  else if (cmd === 'copy') copyFromRole(role)
  else if (cmd === 'delete') deleteRole(role)
}

function editRole(role: any) {
  editingRole.value = role
  roleForm.value = {
    code: role.code,
    name: role.name,
    description: role.description || '',
    sort_order: role.sort_order,
    is_active: role.is_active,
  }
  dialogVisible.value = true
}

function copyFromRole(role: any) {
  if (selectedRole.value?.code === 'admin') {
    ElMessage.warning('admin 角色无法修改权限')
    return
  }
  if (!selectedRole.value) {
    ElMessage.warning('请先在左侧选择目标角色')
    return
  }
  const sourceIds = (role.permissions || []).map((p: any) => p.id)
  permGroups.forEach((group) => {
    group.rows.forEach((row) => {
      Object.keys(row.actions).forEach((action) => {
        row.actions[action].checked = sourceIds.includes(row.actions[action].id)
      })
      row.allChecked = Object.values(row.actions).every((c) => c.checked)
    })
    recountGroup(group)
  })
  ElMessage.success(`已复制「${role.name}」的权限到当前角色，请保存`)
}

async function saveRole() {
  if (!roleForm.value.code || !roleForm.value.name) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    if (editingRole.value) {
      await roleApi.update(editingRole.value.id, roleForm.value)
      ElMessage.success('更新成功')
    } else {
      await roleApi.create(roleForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadRoles()
  } catch {
    // 错误已在拦截器中显示
  }
}

async function deleteRole(role: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除角色「${role.name}」吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await roleApi.remove(role.id)
    ElMessage.success('删除成功')
    if (selectedRole.value?.id === role.id) {
      selectedRole.value = null
    }
    await loadRoles()
  } catch {
    // 用户取消或删除失败
  }
}
</script>

<style scoped>
.role-page {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar h2 {
  margin: 0;
  font-size: 18px;
}
.split-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}
/* 左侧角色列表 */
.role-list-panel {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  background: #fafafa;
}
.role-cards {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.role-card {
  padding: 12px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.2s;
}
.role-card:hover {
  background: #f5f7fa;
}
.role-card.active {
  background: #ecf5ff;
  border-color: #409eff;
}
.role-card.disabled {
  opacity: 0.5;
}
.role-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.role-name {
  font-weight: 600;
  font-size: 14px;
}
.role-code {
  color: #909399;
  font-size: 12px;
  font-family: monospace;
  margin-bottom: 8px;
}
.role-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.perm-count {
  color: #606266;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.more-btn {
  cursor: pointer;
  color: #909399;
  padding: 4px;
  border-radius: 4px;
}
.more-btn:hover {
  background: #ecf5ff;
  color: #409eff;
}
/* 右侧详情 */
.role-detail-panel {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.detail-header {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
}
.detail-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.detail-title h3 {
  margin: 0;
  font-size: 16px;
}
.detail-desc {
  color: #909399;
  font-size: 13px;
  margin-top: 6px;
}
.admin-alert {
  margin: 16px 20px 0;
}
/* 权限工具栏 */
.perm-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 8px;
}
.perm-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.toolbar-label {
  color: #606266;
  font-size: 13px;
}
.perm-summary {
  color: #909399;
  font-size: 13px;
}
.perm-summary b {
  color: #409eff;
  font-size: 15px;
}
/* 权限分组 */
.perm-groups {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}
.perm-group {
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fafafa;
  cursor: pointer;
  user-select: none;
}
.group-arrow {
  transition: transform 0.2s;
  color: #909399;
  font-size: 12px;
}
.group-arrow.expanded {
  transform: rotate(90deg);
}
.group-name {
  font-weight: 600;
  flex: 1;
}
.group-all {
  margin-left: auto;
}
.group-body {
  padding: 8px;
}
.resource-name {
  display: block;
  font-size: 13px;
}
.resource-code {
  display: block;
  font-size: 11px;
  color: #909399;
  font-family: monospace;
}
.perm-groups :deep(.no-perm) {
  color: #c0c4cc;
}
/* 底部保存栏 */
.save-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-top: 1px solid #ebeef5;
  background: #fafafa;
}
.save-bar-info {
  color: #909399;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.save-bar-actions {
  display: flex;
  gap: 8px;
}
/* 审计日志 */
.audit-section {
  border-top: 1px solid #ebeef5;
  padding: 16px 20px;
  max-height: 240px;
  overflow-y: auto;
}
.audit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.audit-title {
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.audit-timeline {
  padding-left: 8px;
}
.audit-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}
.audit-user {
  color: #409eff;
  font-weight: 500;
}
.audit-action {
  color: #606266;
}
.empty-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
