<template>
  <div class="page-container">
    <div class="toolbar">
      <h2>部门管理</h2>
      <el-button type="primary" @click="showAddDept">新增部门</el-button>
    </div>

    <el-tree
      :data="deptTree"
      :props="{ label: 'name', children: 'children' }"
      node-key="id"
      default-expand-all
      class="dept-tree"
    >
      <template #default="{ node, data }">
        <span class="tree-node">
          <span>{{ node.label }}</span>
          <span class="actions">
            <el-button link type="primary" size="small" @click="editDept(data)">编辑</el-button>
            <el-button link type="danger" size="small" @click="deleteDept(data.id)">删除</el-button>
          </span>
        </span>
      </template>
    </el-tree>

    <!-- 新增/编辑部门 -->
    <el-dialog v-model="dialogVisible" :title="editingDept ? '编辑部门' : '新增部门'" width="400px">
      <el-form ref="deptFormRef" :model="deptForm" :rules="deptRules" label-width="80px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="deptForm.name" placeholder="请输入部门名称（2-100字符）" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="上级部门" prop="parent_id">
          <el-select v-model="deptForm.parent_id" placeholder="请选择上级部门" clearable>
            <el-option v-for="d in deptList" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDept">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { departmentApi } from '@/api'
import { deptNameRules } from '@/utils/validators'

const deptTree = ref<any[]>([])
const deptList = ref<any[]>([])
const dialogVisible = ref(false)
const editingDept = ref<any>(null)
const deptFormRef = ref<FormInstance>()
const deptForm = ref({ name: '', parent_id: null as number | null })
const deptRules: FormRules = {
  name: deptNameRules,
}

onMounted(() => {
  loadDepts()
})

async function loadDepts() {
  try {
    const [treeRes, listRes] = await Promise.all([
      departmentApi.tree(),
      departmentApi.list(),
    ])
    deptTree.value = treeRes || []
    deptList.value = listRes || []
  } catch {
    ElMessage.error('加载部门失败')
  }
}

function showAddDept() {
  editingDept.value = null
  deptForm.value = { name: '', parent_id: null }
  deptFormRef.value?.clearValidate()
  dialogVisible.value = true
}

function editDept(dept: any) {
  editingDept.value = dept
  deptForm.value = { name: dept.name, parent_id: dept.parent_id }
  deptFormRef.value?.clearValidate()
  dialogVisible.value = true
}

async function saveDept() {
  if (!deptFormRef.value) return
  try {
    await deptFormRef.value.validate()
  } catch {
    return // 表单校验不通过，Element Plus 会自动显示提示
  }
  try {
    if (editingDept.value) {
      await departmentApi.update(editingDept.value.id, deptForm.value)
      ElMessage.success('更新成功')
    } else {
      await departmentApi.create(deptForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadDepts()
  } catch {
    // 错误已在拦截器中显示
  }
}

async function deleteDept(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该部门?', '提示', { type: 'warning' })
    await departmentApi.remove(id)
    ElMessage.success('删除成功')
    loadDepts()
  } catch {
    // 用户取消或删除失败
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
.dept-tree {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}
.tree-node {
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding-right: 20px;
}
.actions {
  display: flex;
  gap: 8px;
}
</style>
