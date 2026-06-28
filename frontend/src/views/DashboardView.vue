<template>
  <div>
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="label">项目总数</div>
        <div><span class="value">{{ stats.projectCount }}</span><span class="unit">个</span></div>
      </div>
      <div class="stat-card">
        <div class="label">进行中项目</div>
        <div><span class="value" style="color:var(--primary)">{{ stats.activeProject }}</span><span class="unit">个</span></div>
      </div>
      <div class="stat-card">
        <div class="label">实验总数</div>
        <div><span class="value" style="color:var(--warning)">{{ stats.experimentCount }}</span><span class="unit">个</span></div>
      </div>
      <div class="stat-card">
        <div class="label">样品/试产</div>
        <div><span class="value" style="color:var(--success)">{{ stats.sampleCount }}</span><span class="unit">个</span></div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="card">
      <div class="card-title">快捷操作</div>
      <el-row :gutter="16">
        <el-col :span="6" v-for="act in quickActions" :key="act.path">
          <div class="quick-action" @click="$router.push(act.path)">
            <el-icon :size="28" :color="act.color"><component :is="act.icon" /></el-icon>
            <span>{{ act.label }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 最近项目 -->
    <div class="card">
      <div class="card-title">最近项目</div>
      <el-table :data="recentProjects" size="small" empty-text="暂无项目">
        <el-table-column prop="code" label="编号" width="140" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :stroke-width="8" />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Files, Reading, Box, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { projectApi, experimentApi, sampleApi } from '@/api'
import type { ProjectOut } from '@/types/project'

const stats = ref({ projectCount: 0, activeProject: 0, experimentCount: 0, sampleCount: 0 })
const recentProjects = ref<ProjectOut[]>([])

const quickActions = [
  { label: '新建项目', path: '/projects', icon: Files, color: '#409eff' },
  { label: '研发实验', path: '/experiments', icon: Reading, color: '#e6a23c' },
  { label: 'BOM管理', path: '/bom', icon: Box, color: '#67c23a' },
  { label: '文档知识', path: '/documents', icon: Document, color: '#909399' },
]

const statusType = (s: string) => ({ draft: 'info', active: 'success', on_hold: 'warning', completed: '', cancelled: 'danger' }[s] || 'info')
const statusLabel = (s: string) => ({ draft: '草稿', active: '进行中', on_hold: '暂停', completed: '已完成', cancelled: '已取消' }[s] || s)

onMounted(async () => {
  try {
    const [pRes, pActiveRes, eRes, sRes] = await Promise.all([
      projectApi.list({ page: 1, page_size: 5 }),
      projectApi.list({ page: 1, page_size: 1, status: 'active' }),
      experimentApi.list({ page: 1, page_size: 1 }),
      sampleApi.listSamples({ page: 1, page_size: 1 }),
    ])
    recentProjects.value = pRes.items || []
    stats.value = {
      projectCount: pRes.total || 0,
      activeProject: pActiveRes.total || 0,
      experimentCount: eRes.total || 0,
      sampleCount: sRes.total || 0,
    }
  } catch (e) {
    console.error('[Dashboard] 加载统计数据失败', e)
    ElMessage.warning('部分统计数据加载失败')
  }
})
</script>

<style scoped>
.quick-action {
  display: flex; align-items: center; gap: 10px;
  padding: 16px; border: 1px solid #e4e7ed; border-radius: 8px;
  cursor: pointer; transition: all .2s; font-size: 14px;
}
.quick-action:hover { border-color: var(--primary); color: var(--primary); background: #ecf5ff; }
</style>
