import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    title?: string
    roles?: string[]  // 允许访问的角色列表（粗粒度，兼容旧逻辑）
    permission?: string  // 进入该路由所需的最小权限码，如 'project:read'
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/views/LayoutView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '首页' }
      },
      // 项目管理
      {
        path: 'projects',
        name: 'ProjectList',
        component: () => import('@/views/project/ProjectList.vue'),
        meta: { title: '项目管理', permission: 'project:read' }
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/project/ProjectDetail.vue'),
        meta: { title: '项目详情', permission: 'project:read' }
      },
      // 实验管理
      {
        path: 'experiments',
        name: 'ExperimentList',
        component: () => import('@/views/experiment/ExperimentList.vue'),
        meta: { title: '研发实验', permission: 'experiment:read' }
      },
      {
        path: 'experiments/:id/tcr',
        name: 'ExperimentTcr',
        component: () => import('@/views/experiment/TcrTestView.vue'),
        meta: { title: '温漂测试', permission: 'experiment:read' }
      },
      {
        path: 'experiments/:id/temp-rise',
        name: 'ExperimentTempRise',
        component: () => import('@/views/experiment/TempRiseTestView.vue'),
        meta: { title: '温升测试', permission: 'experiment:read' }
      },
      // BOM管理
      {
        path: 'bom',
        name: 'BomList',
        component: () => import('@/views/bom/BomList.vue'),
        meta: { title: 'BOM管理', permission: 'bom:read' }
      },
      {
        path: 'bom/:id',
        name: 'BomDetail',
        component: () => import('@/views/bom/BomDetail.vue'),
        meta: { title: 'BOM详情', permission: 'bom:read' }
      },
      // 样品试产
      {
        path: 'samples',
        name: 'SampleList',
        component: () => import('@/views/sample/SampleList.vue'),
        meta: { title: '样品与试产', permission: 'sample:read' }
      },
      // 文档知识
      {
        path: 'documents',
        name: 'DocumentList',
        component: () => import('@/views/document/DocumentList.vue'),
        meta: { title: '文档知识', permission: 'document:read' }
      },
      // 库存管理
      {
        path: 'inventory',
        name: 'InventoryList',
        component: () => import('@/views/inventory/InventoryList.vue'),
        meta: { title: '库存管理', permission: 'inventory:read' }
      },
      // 系统管理
      {
        path: 'system/users',
        name: 'UserManage',
        component: () => import('@/views/system/UserManageView.vue'),
        meta: { title: '账号管理', roles: ['admin'], permission: 'user:read' }
      },
      {
        path: 'system/departments',
        name: 'DepartmentManage',
        component: () => import('@/views/system/DepartmentView.vue'),
        meta: { title: '部门管理', roles: ['admin', 'manager'], permission: 'department:read' }
      },
      {
        path: 'system/roles',
        name: 'RoleManage',
        component: () => import('@/views/system/RoleManageView.vue'),
        meta: { title: '角色管理', roles: ['admin'], permission: 'role:read' }
      },
      {
        path: 'system/logs',
        name: 'OperationLog',
        component: () => import('@/views/system/OperationLogView.vue'),
        meta: { title: '操作日志', roles: ['admin', 'manager'], permission: 'log:read' }
      },
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 解析 JWT 中过期时间（兼容 base64url 编码）
function isTokenExpired(token: string): boolean {
  try {
    // JWT 使用 base64url 编码（- 代替 +，_ 代替 /），需先转换为标准 base64
    const part = token.split('.')[1]
    if (!part) return true
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/')
    // 补齐 padding
    const padded = base64 + '==='.slice((base64.length + 3) % 4)
    const payload = JSON.parse(atob(padded))
    if (!payload.exp) return false
    return Date.now() >= payload.exp * 1000
  } catch {
    return true
  }
}

// 从 localStorage 读取权限码（避免在守卫中引用 store 造成循环依赖）
function getStoredPermissions(): { permissions: string[]; isAdmin: boolean } {
  let permissions: string[] = []
  let isAdmin = false
  try {
    permissions = JSON.parse(localStorage.getItem('permissions') || '[]')
    isAdmin = localStorage.getItem('isAdmin') === 'true'
  } catch {
    permissions = []
  }
  return { permissions, isAdmin }
}

// 路由守卫 — JWT 鉴权 + 权限校验
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  // 检查 token 是否存在且未过期
  const validToken = token && !isTokenExpired(token)

  if (to.meta.requiresAuth !== false && !validToken) {
    next('/login')
    return
  }

  if (to.path === '/login' && validToken) {
    next('/')
    return
  }

  // 细粒度权限检查：permission（基于 RBAC）
  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission) {
    const { permissions, isAdmin } = getStoredPermissions()
    const hasAccess = isAdmin || permissions.includes(requiredPermission)
    if (!hasAccess) {
      // 无权限：标记后跳转到首页（LayoutView 会读取并提示）
      sessionStorage.setItem('__no_permission', '1')
      next('/')
      return
    }
  }

  // 兼容旧的角色级检查（roles）
  const requiredRoles = to.meta.roles as string[] | undefined
  if (requiredRoles && requiredRoles.length > 0) {
    let userRole = ''
    try {
      const info = JSON.parse(localStorage.getItem('userInfo') || '{}')
      userRole = info.role || ''
    } catch {
      userRole = ''
    }
    if (!requiredRoles.includes(userRole)) {
      next('/')
      return
    }
  }

  document.title = (to.meta.title as string) || '工厂研发管理系统'
  next()
})

export default router
