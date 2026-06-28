<template>
  <slot v-if="!hasError" />
  <div v-else class="error-boundary">
    <div class="error-boundary__card">
      <el-icon class="error-boundary__icon" :size="48">
        <WarningFilled />
      </el-icon>
      <h2 class="error-boundary__title">页面出现异常</h2>
      <p class="error-boundary__desc">
        抱歉，当前页面发生了未预期的错误。您可以尝试刷新页面，或返回首页。
      </p>
      <div v-if="showDetail && error" class="error-boundary__detail">
        <pre>{{ error.message || '未知错误' }}</pre>
      </div>
      <div class="error-boundary__actions">
        <el-button type="primary" @click="handleRefresh">刷新页面</el-button>
        <el-button @click="handleGoHome">返回首页</el-button>
        <el-button link type="info" @click="showDetail = !showDetail">
          {{ showDetail ? '收起' : '查看详情' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { WarningFilled } from '@element-plus/icons-vue'

const router = useRouter()
const hasError = ref(false)
const error = ref<Error | null>(null)
const showDetail = ref(false)

onErrorCaptured((err: Error, instance, info) => {
  console.error('[ErrorBoundary] 组件渲染错误:', err, info)
  hasError.value = true
  error.value = err
  // 阻止错误继续向上传播到全局处理器
  return false
})

function handleRefresh() {
  window.location.reload()
}

function handleGoHome() {
  router.push('/').then(() => {
    window.location.reload()
  })
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 40px;
}

.error-boundary__card {
  text-align: center;
  max-width: 480px;
  padding: 48px 32px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.error-boundary__icon {
  color: #e6a23c;
  margin-bottom: 16px;
}

.error-boundary__title {
  font-size: 20px;
  color: #303133;
  margin: 0 0 12px;
}

.error-boundary__desc {
  font-size: 14px;
  color: #909399;
  margin: 0 0 24px;
  line-height: 1.6;
}

.error-boundary__detail {
  text-align: left;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px 16px;
  margin-bottom: 24px;
  max-height: 200px;
  overflow: auto;
}

.error-boundary__detail pre {
  margin: 0;
  font-size: 12px;
  color: #f56c6c;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-boundary__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
</style>
