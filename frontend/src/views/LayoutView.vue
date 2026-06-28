<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <el-icon size="20"><Memo /></el-icon>
        工厂研发管理系统
      </div>
      <nav>
        <div class="menu-section">主导航</div>
        <router-link to="/" class="menu-item" :class="{ active: $route.path === '/' }">
          <el-icon><DataLine /></el-icon> 首页看板
        </router-link>

        <div class="menu-section">核心模块</div>
        <router-link v-if="canView('project:read')" to="/projects" class="menu-item" :class="{ active: $route.path.startsWith('/projects') }">
          <el-icon><Files /></el-icon> 项目管理
        </router-link>
        <router-link v-if="canView('experiment:read')" to="/experiments" class="menu-item" :class="{ active: $route.path.startsWith('/experiments') }">
          <el-icon><Reading /></el-icon> 研发实验
        </router-link>
        <router-link v-if="canView('bom:read')" to="/bom" class="menu-item" :class="{ active: $route.path.startsWith('/bom') }">
          <el-icon><Box /></el-icon> 物料BOM
        </router-link>
        <router-link v-if="canView('sample:read')" to="/samples" class="menu-item" :class="{ active: $route.path.startsWith('/samples') }">
          <el-icon><Cpu /></el-icon> 样品试产
        </router-link>
        <router-link v-if="canView('document:read')" to="/documents" class="menu-item" :class="{ active: $route.path.startsWith('/documents') }">
          <el-icon><Document /></el-icon> 文档知识
        </router-link>
        <router-link v-if="canView('inventory:read')" to="/inventory" class="menu-item" :class="{ active: $route.path.startsWith('/inventory') }">
          <el-icon><Goods /></el-icon> 库存管理
        </router-link>

        <template v-if="hasAnySystemMenu">
          <div class="menu-section">系统管理</div>
          <router-link v-if="canView('user:read')" to="/system/users" class="menu-item" :class="{ active: $route.path.startsWith('/system/users') }">
            <el-icon><User /></el-icon> 账号管理
          </router-link>
          <router-link v-if="canView('department:read')" to="/system/departments" class="menu-item" :class="{ active: $route.path.startsWith('/system/departments') }">
            <el-icon><School /></el-icon> 部门管理
          </router-link>
          <router-link v-if="canView('role:read')" to="/system/roles" class="menu-item" :class="{ active: $route.path.startsWith('/system/roles') }">
            <el-icon><Key /></el-icon> 角色权限
          </router-link>
          <router-link v-if="canView('log:read')" to="/system/logs" class="menu-item" :class="{ active: $route.path.startsWith('/system/logs') }">
            <el-icon><Timer /></el-icon> 操作日志
          </router-link>
        </template>
      </nav>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <header class="topbar">
        <span class="page-title">{{ $route.meta.title || '首页' }}</span>
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="28">{{ username?.charAt(0) || 'U' }}</el-avatar>
            <span>{{ username || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="changePwd">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>
      <main class="page-content">
        <router-view />
      </main>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialogVisible" title="修改密码" width="400px">
      <el-form :model="pwdForm" label-width="80px">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmChangePwd">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, provide, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Memo, Files, Reading, Box, Cpu, Document, DataLine, ArrowDown, User, School, Key, Timer, Goods } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const username = authStore.username

const pwdDialogVisible = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })

// 菜单可见性：基于权限码（admin 放行）
const canView = (perm: string) => authStore.hasPermission(perm)

// 提供权限检查函数给子组件
provide('canOperate', canView)

// 检测路由守卫设置的无权限标记，提示用户
onMounted(() => {
  if (sessionStorage.getItem('__no_permission')) {
    sessionStorage.removeItem('__no_permission')
    ElMessage.warning('您没有访问该页面的权限')
  }
})

// 系统管理整组是否至少有一项可见
const hasAnySystemMenu = computed(() =>
  canView('user:read') || canView('department:read') ||
  canView('role:read') || canView('log:read')
)

const handleCommand = (cmd: string) => {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (cmd === 'changePwd') {
    pwdDialogVisible.value = true
  }
}

async function confirmChangePwd() {
  if (!pwdForm.value.new_password || pwdForm.value.new_password.length < 6) {
    ElMessage.warning('新密码至少6字符')
    return
  }
  if (pwdForm.value.new_password !== pwdForm.value.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  try {
    await authStore.changePassword(pwdForm.value.old_password, pwdForm.value.new_password)
    ElMessage.success('密码修改成功')
    pwdDialogVisible.value = false
    pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch {
    // 错误已在拦截器中显示
  }
}
</script>
