import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(pinia)
app.use(router)

// ===== 全局错误处理 =====

// Vue 渲染级错误捕获
app.config.errorHandler = (err: unknown, instance, info) => {
  const message = err instanceof Error ? err.message : String(err)
  console.error('[GlobalErrorHandler] 未捕获的错误:', message, info)

  // 避免在同一个错误上重复弹框
  if (typeof message === 'string') {
    // 忽略 router 路由重复导航等非致命错误
    if (message.includes('Redirected') || message.includes('NavigationDuplicated')) {
      return
    }
  }

  ElMessage.error(`页面发生错误: ${message}`)
}

// 全局警告处理（开发调试用）
app.config.warnHandler = (msg, instance, trace) => {
  if (import.meta.env.DEV) {
    console.warn(`[Vue Warn] ${msg}`, trace)
  }
}

// 未捕获的 Promise 拒绝（网络请求等异步错误）
window.addEventListener('unhandledrejection', (event) => {
  console.error('[UnhandledRejection]', event.reason)

  // 忽略已处理的路由错误
  const reason = event.reason
  if (reason && typeof reason === 'object') {
    if (
      reason.message?.includes('Redirected') ||
      reason.name === 'NavigationDuplicatedType'
    ) {
      event.preventDefault()
      return
    }
  }

  ElMessage.error('操作失败，请稍后重试')
  // 阻止默认的控制台错误，改用我们的处理
  event.preventDefault()
})

app.mount('#app')
