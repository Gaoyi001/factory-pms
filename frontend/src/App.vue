<template>
  <ErrorBoundary>
    <router-view />
  </ErrorBoundary>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const authStore = useAuthStore()

// 应用启动时：从 localStorage 恢复用户信息
authStore.initFromStorage()

// 如果已登录，异步刷新权限（确保最新，不阻塞渲染）
onMounted(async () => {
  if (authStore.isAuthenticated) {
    try {
      await authStore.fetchPermissions()
    } catch (e) {
      console.error('[App] 权限加载失败', e)
      ElMessage.warning('权限加载失败，部分功能可能不可用')
    }
  }
})
</script>
