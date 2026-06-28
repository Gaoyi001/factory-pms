<template>
  <div class="page-container">
    <div class="toolbar">
      <h2>账号管理</h2>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索姓名/用户名" style="width: 200px; margin-right: 12px;" clearable @change="loadUsers" />
        <el-select v-model="filterRole" placeholder="角色" style="width: 120px; margin-right: 12px;" clearable @change="loadUsers">
          <el-option label="管理员" value="admin" />
          <el-option label="经理" value="manager" />
          <el-option label="成员" value="member" />
          <el-option label="查看者" value="viewer" />
        </el-select>
        <el-button type="primary" @click="showAddUser">新增账号</el-button>
      </div>
    </div>

    <el-table :data="users" v-loading="loading" @selection-change="handleSelection">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.role === 'admin'" type="danger" size="small">管理员</el-tag>
          <el-tag v-else-if="row.role === 'manager'" type="warning" size="small">经理</el-tag>
          <el-tag v-else-if="row.role === 'member'" size="small">成员</el-tag>
          <el-tag v-else type="info" size="small">查看者</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="department" label="部门" width="120">
        <template #default="{ row }">
          {{ row.department?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login_at" label="最后登录" width="160">
        <template #default="{ row }">
          {{ row.last_login_at ? new Date(row.last_login_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="editUser(row)">编辑</el-button>
          <el-button link type="warning" size="small" @click="resetPassword(row)">重置密码</el-button>
          <el-button link :type="row.is_active ? 'danger' : 'success'" size="small" @click="toggleStatus(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
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
      @size-change="loadUsers"
      @current-change="loadUsers"
    />

    <!-- 新增/编辑用户 -->
    <el-dialog v-model="dialogVisible" :title="editingUser ? '编辑账号' : '新增账号'" width="500px">
      <el-form ref="userFormRef" :model="userForm" :rules="userRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="!!editingUser" placeholder="3-64字符，字母/数字/下划线" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="userForm.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="经理" value="manager" />
            <el-option label="成员" value="member" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门" prop="dept_id">
          <el-select v-model="userForm.dept_id" placeholder="选择部门" clearable style="width: 100%;">
            <el-option v-for="d in deptList" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" placeholder="至少6字符" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="pwdDialogVisible" title="重置密码" width="400px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="80px">
        <el-form-item :label="`新密码`" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" placeholder="至少6字符" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { userApi, userEnhanceApi, departmentApi } from '@/api'
import { usernameRules, emailRules, realNameRules, passwordRules } from '@/utils/validators'

const users = ref<any[]>([])
const deptList = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
const filterRole = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedUsers = ref<any[]>([])

const dialogVisible = ref(false)
const editingUser = ref<any>(null)
const userFormRef = ref<FormInstance>()
const userForm = ref({ username: '', real_name: '', email: '', role: 'member', dept_id: null as number | null, password: '' })
const userRules: FormRules = {
  username: usernameRules,
  real_name: realNameRules,
  email: emailRules,
  password: passwordRules,
}

const pwdDialogVisible = ref(false)
const pwdFormRef = ref<FormInstance>()
const pwdForm = ref({ new_password: '', user_id: null as number | null })
const pwdRules: FormRules = {
  new_password: passwordRules,
}

onMounted(() => {
  loadUsers()
  loadDepts()
})

async function loadUsers() {
  loading.value = true
  try {
    const res = await userApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value,
      role: filterRole.value || undefined,
    })
    users.value = res.items || []
    total.value = res.total || 0
  } catch {
    ElMessage.error('加载用户失败')
  } finally {
    loading.value = false
  }
}

async function loadDepts() {
  const res = await departmentApi.list()
  deptList.value = res || []
}

function handleSelection(val: any[]) {
  selectedUsers.value = val
}

function showAddUser() {
  editingUser.value = null
  userForm.value = { username: '', real_name: '', email: '', role: 'member', dept_id: null, password: '' }
  userFormRef.value?.clearValidate()
  dialogVisible.value = true
}

function editUser(user: any) {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    real_name: user.real_name,
    email: user.email,
    role: user.role,
    dept_id: user.dept_id,
    password: '',
  }
  userFormRef.value?.clearValidate()
  dialogVisible.value = true
}

async function saveUser() {
  if (!userFormRef.value) return
  try {
    await userFormRef.value.validate()
  } catch {
    return // 表单校验不通过，Element Plus 会自动显示提示
  }
  try {
    if (editingUser.value) {
      const { username, password, ...updateData } = userForm.value
      await userApi.update(editingUser.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      await userApi.create(userForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch {
    // 错误已在拦截器中显示
  }
}

function resetPassword(user: any) {
  pwdForm.value = { new_password: '', user_id: user.id }
  pwdFormRef.value?.clearValidate()
  pwdDialogVisible.value = true
}

async function confirmResetPwd() {
  if (!pwdFormRef.value) return
  try {
    await pwdFormRef.value.validate()
  } catch {
    return
  }
  try {
    await userEnhanceApi.changePassword({ user_id: pwdForm.value.user_id!, new_password: pwdForm.value.new_password })
    ElMessage.success('密码已重置')
    pwdDialogVisible.value = false
  } catch {
    // 错误已在拦截器中显示
  }
}

async function toggleStatus(user: any) {
  try {
    if (user.is_active) {
      await userEnhanceApi.batchDisable([user.id])
    } else {
      await userEnhanceApi.batchEnable([user.id])
    }
    ElMessage.success(user.is_active ? '已禁用' : '已启用')
    loadUsers()
  } catch {
    ElMessage.error('操作失败')
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
