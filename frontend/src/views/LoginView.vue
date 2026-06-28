<template>
  <div class="login-page">
    <div class="login-card">
      <h1>🏭 工厂研发管理系统</h1>
      <p class="subtitle">研发项目全生命周期管理平台</p>
      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password>
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width:100%">
            {{ loading ? '登录中...' : '登  录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align:center;color:#909399;font-size:13px;margin-top:8px;">
        {{ demoHint }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { LoginParams } from '@/types/user'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref()
const form = reactive<LoginParams>({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 演示模式提示 — 仅在开发环境通过环境变量控制
const demoHint = computed(() => {
  if (import.meta.env.DEV && import.meta.env.VITE_DEMO_HINT === 'true') {
    return '演示账号：请联系管理员获取'
  }
  return ''
})

const handleLogin = async () => {
  // 表单校验
  try {
    await formRef.value?.validate()
  } catch {
    return // 校验未通过，Element Plus 会自动显示提示
  }
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.response?.data?.detail || err?.message || '登录失败，请重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>
