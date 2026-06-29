import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, userEnhanceApi } from '@/api'
import type { UserOut } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserOut | null>(null)
  const loading = ref(false)
  const permissions = ref<string[]>(JSON.parse(localStorage.getItem('permissions') || '[]'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')

  const isAuthenticated = computed(() => !!user.value)
  const username = computed(() => user.value?.real_name || user.value?.username || '用户')
  const userRole = computed(() => user.value?.role || '')

  function initFromStorage() {
    const stored = localStorage.getItem('userInfo')
    if (stored) {
      try {
        user.value = JSON.parse(stored)
      } catch {
        localStorage.removeItem('userInfo')
      }
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.login({ username, password })

      const me = await authApi.getMe()
      user.value = me
      localStorage.setItem('userInfo', JSON.stringify(me))

      await fetchPermissions()
      return me
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    try {
      const me = await authApi.getMe()
      user.value = me
      localStorage.setItem('userInfo', JSON.stringify(me))
    } catch {
      logout()
    }
  }

  async function fetchPermissions() {
    try {
      const res = await authApi.getMyPermissions()
      permissions.value = res.permissions || []
      isAdmin.value = !!res.is_admin
      localStorage.setItem('permissions', JSON.stringify(permissions.value))
      localStorage.setItem('isAdmin', String(isAdmin.value))
    } catch {
      permissions.value = []
      isAdmin.value = false
      localStorage.removeItem('permissions')
      localStorage.removeItem('isAdmin')
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // 忽略登出错误
    }
    user.value = null
    permissions.value = []
    isAdmin.value = false
    localStorage.removeItem('userInfo')
    localStorage.removeItem('permissions')
    localStorage.removeItem('isAdmin')
  }

  async function changePassword(oldPwd: string, newPwd: string) {
    return userEnhanceApi.changePassword({ old_password: oldPwd, new_password: newPwd })
  }

  function hasRole(...roles: string[]): boolean {
    return roles.includes(userRole.value)
  }

  /** 是否拥有某权限码（admin 直接放行） */
  function hasPermission(code: string): boolean {
    if (isAdmin.value) return true
    return permissions.value.includes(code)
  }

  /** 是否拥有任一权限码 */
  function hasAnyPermission(...codes: string[]): boolean {
    if (isAdmin.value) return true
    if (!codes.length) return true
    return codes.some(c => permissions.value.includes(c))
  }

  return {
    token,
    user,
    loading,
    permissions,
    isAdmin,
    isAuthenticated,
    username,
    userRole,
    initFromStorage,
    login,
    fetchUser,
    fetchPermissions,
    logout,
    changePassword,
    hasRole,
    hasPermission,
    hasAnyPermission,
  }
})
