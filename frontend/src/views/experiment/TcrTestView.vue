<template>
  <div class="tcr-test-page">
    <!-- 顶部信息 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回实验</el-button>
        <h2 style="margin:0 0 0 12px">温漂（TCR）测试</h2>
        <el-tag v-if="experiment" type="info" size="large" style="margin-left:12px">
          {{ experiment.code }} · {{ experiment.name }}
        </el-tag>
      </div>
    </div>
    <el-alert v-if="experiment && experiment.status !== 'in_progress'" type="warning" :closable="false" style="margin-bottom:12px">
      <template #title>
        实验当前状态为「{{ experiment.status === 'draft' ? '草稿' : experiment.status === 'completed' ? '已完成' : '已取消' }}」，
        仅「进行中」状态可录入测试记录。请先返回列表将状态切换为进行中。
      </template>
    </el-alert>

    <el-row :gutter="16">
      <!-- 左侧：参数与录入 -->
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">基础信息</span></template>
          <el-form :model="form" label-width="100px" size="default">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="批次号">
                  <el-input v-model="form.batch_no" placeholder="请输入批次号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="样品编号">
                  <el-input v-model="form.sample_code" placeholder="请输入样品编号" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="执行人">
                  <el-select v-model="form.executor_id" placeholder="留空则默认当前用户" clearable style="width:100%">
                    <el-option v-for="u in userOptions" :key="u.id" :label="u.name" :value="u.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="执行日期">
                  <el-date-picker v-model="form.executed_at" type="date" style="width:100%" value-format="YYYY-MM-DD" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-top:12px">
          <template #header><span style="font-weight:600">温度采样设置</span></template>
          <el-form :model="tempConfig" label-width="100px">
            <el-row :gutter="12">
              <el-col :span="6">
                <el-form-item label="起始温度">
                  <el-input-number v-model="tempConfig.start" :step="5" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="结束温度">
                  <el-input-number v-model="tempConfig.end" :step="5" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="采样间隔">
                  <el-input-number v-model="tempConfig.step" :step="5" :min="1" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="参考温度">
                  <el-input-number v-model="tempConfig.ref" :step="5" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <div style="text-align:right">
              <el-button type="primary" @click="generatePoints">
                <el-icon><Refresh /></el-icon> 生成采样点
              </el-button>
              <el-button @click="clearPoints">清空</el-button>
            </div>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-top:12px">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600">温度-阻值录入</span>
              <span style="color:#909399;font-size:12px">共 {{ points.length }} 个采样点，参考温度 {{ tempConfig.ref }}°C</span>
            </div>
          </template>
          <el-table :data="points" size="small" border empty-text="请先生成采样点" max-height="420">
            <el-table-column label="#" type="index" width="50" />
            <el-table-column label="温度 (°C)" width="110">
              <template #default="{ row }">
                <span :style="{ color: row.temperature === tempConfig.ref ? '#409eff' : '', fontWeight: row.temperature === tempConfig.ref ? 600 : 400 }">
                  {{ row.temperature }}
                  <el-tag v-if="row.temperature === tempConfig.ref" size="small" type="primary" style="margin-left:4px">参考</el-tag>
                </span>
              </template>
            </el-table-column>
            <el-table-column label="阻值 (Ω)" min-width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.resistance" :precision="6" :step="0.001" :min="0" controls-position="right" size="small" style="width:100%" @input="recalculate" />
              </template>
            </el-table-column>
            <el-table-column label="ΔT (°C)" width="100">
              <template #default="{ row }">{{ (row.temperature - tempConfig.ref).toFixed(1) }}</template>
            </el-table-column>
            <el-table-column label="ΔR (Ω)" width="120">
              <template #default="{ row }">
                <span v-if="refResistance != null && row.resistance != null">
                  {{ (row.resistance - refResistance).toFixed(6) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="TCR (ppm/°C)" width="150">
              <template #default="{ row }">
                <span v-if="row.tcr != null" :style="{ color: tcrColor(row.tcr), fontWeight: 600 }">
                  {{ row.tcr.toFixed(2) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：计算结果与曲线 -->
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">计算结果</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="参考温度阻值">
              <span style="color:#409eff;font-weight:600">{{ refResistance != null ? refResistance + ' Ω' : '未录入' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="阻值范围">
              {{ resistanceRange || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="阻值变化量 ΔR">
              {{ deltaR != null ? deltaR.toFixed(6) + ' Ω' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="平均 TCR">
              <span :style="{ color: tcrColor(avgTcr), fontWeight: 600 }">
                {{ avgTcr != null ? avgTcr.toFixed(2) + ' ppm/°C' : '-' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="最大 TCR">
              <span :style="{ color: tcrColor(maxTcr) }">{{ maxTcr != null ? maxTcr.toFixed(2) + ' ppm/°C' : '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="最小 TCR">
              <span :style="{ color: tcrColor(minTcr) }">{{ minTcr != null ? minTcr.toFixed(2) + ' ppm/°C' : '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="有效采样点">
              {{ validPointCount }} / {{ points.length }}
            </el-descriptions-item>
          </el-descriptions>

          <div style="margin-top:16px">
            <el-form-item label="结论" label-width="60px">
              <el-select v-model="form.conclusion" clearable style="width:100%">
                <el-option v-for="c in CONCLUSION_OPTS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="摘要" label-width="60px">
              <el-input v-model="form.result_summary" type="textarea" :rows="2" placeholder="自动生成或手动填写" />
            </el-form-item>
            <el-form-item label="异常" label-width="60px">
              <el-switch v-model="form.is_abnormal" />
            </el-form-item>
            <el-form-item v-if="form.is_abnormal" label="异常描述" label-width="60px">
              <el-input v-model="form.abnormal_desc" type="textarea" :rows="2" />
            </el-form-item>
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top:12px">
          <template #header><span style="font-weight:600">温度-阻值曲线</span></template>
          <div ref="chartRef" style="width:100%;height:340px"></div>
        </el-card>

        <div style="margin-top:16px;text-align:right">
          <el-button @click="handleCancel">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            <el-icon><Check /></el-icon> 提交测试记录
          </el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Refresh, Check } from '@element-plus/icons-vue'
import { experimentApi, userApi } from '@/api'
import { CONCLUSION_OPTS } from '@/types/experiment'
import { useAutoSave } from '@/composables/useAutoSave'

const route = useRoute()
const router = useRouter()
const experimentId = Number(route.params.id)

const experiment = ref<any>(null)
const userOptions = ref<{ id: number; name: string }[]>([])
const submitting = ref(false)

const form = reactive({
  batch_no: '',
  sample_code: '',
  executor_id: null as number | null,
  executed_at: '',
  conclusion: '',
  result_summary: '',
  is_abnormal: false,
  abnormal_desc: '',
})

const tempConfig = reactive({
  start: -55,
  end: 125,
  step: 10,
  ref: 25,
})

interface SamplePoint {
  temperature: number
  resistance: number | null
  tcr: number | null
}

const points = ref<SamplePoint[]>([])

// 参考温度阻值
const refResistance = computed(() => {
  const refPoint = points.value.find(p => p.temperature === tempConfig.ref)
  return refPoint?.resistance ?? null
})

const validPoints = computed(() => points.value.filter(p => p.resistance != null))
const validPointCount = computed(() => validPoints.value.length)

const resistanceRange = computed(() => {
  if (!validPoints.value.length) return ''
  const resistances = validPoints.value.map(p => p.resistance as number)
  const min = Math.min(...resistances)
  const max = Math.max(...resistances)
  return `${min.toFixed(6)} ~ ${max.toFixed(6)} Ω`
})

const deltaR = computed(() => {
  if (!validPoints.value.length || refResistance.value == null) return null
  const resistances = validPoints.value.map(p => p.resistance as number)
  const max = Math.max(...resistances)
  const min = Math.min(...resistances)
  // 最大变化量（相对参考）
  const maxDelta = Math.max(
    Math.abs(max - refResistance.value),
    Math.abs(min - refResistance.value)
  )
  return maxDelta
})

const tcrValues = computed(() => validPoints.value.map(p => p.tcr).filter((v): v is number => v != null))
const avgTcr = computed(() => tcrValues.value.length ? tcrValues.value.reduce((a, b) => a + b, 0) / tcrValues.value.length : null)
const maxTcr = computed(() => tcrValues.value.length ? Math.max(...tcrValues.value) : null)
const minTcr = computed(() => tcrValues.value.length ? Math.min(...tcrValues.value) : null)

const tcrColor = (v: number | null) => {
  if (v == null) return ''
  const abs = Math.abs(v)
  if (abs <= 50) return '#67c23a'
  if (abs <= 100) return '#e6a23c'
  return '#f56c6c'
}

// ===== 采样点生成 =====
const generatePoints = () => {
  const { start, end, step, ref } = tempConfig
  if (step <= 0) { ElMessage.warning('采样间隔必须大于 0'); return }
  if (start > end) { ElMessage.warning('起始温度不能大于结束温度'); return }
  if (ref < start || ref > end) { ElMessage.warning('参考温度必须在温度范围内'); return }

  const arr: SamplePoint[] = []
  // 确保参考温度点存在
  const temps = new Set<number>()
  for (let t = start; t <= end + 0.0001; t += step) {
    temps.add(Math.round(t))
  }
  temps.add(ref)
  const sorted = Array.from(temps).sort((a, b) => a - b)
  for (const t of sorted) {
    arr.push({ temperature: t, resistance: null, tcr: null })
  }
  points.value = arr
  ElMessage.success(`已生成 ${arr.length} 个采样点`)
  recalculate()
}

const clearPoints = () => {
  points.value = []
}

// ===== 重新计算 TCR =====
const recalculate = () => {
  const refR = refResistance.value
  const refT = tempConfig.ref
  for (const p of points.value) {
    if (p.resistance != null && refR != null && p.temperature !== refT) {
      const dT = p.temperature - refT
      if (dT !== 0 && refR !== 0) {
        // TCR (ppm/°C) = (R - R_ref) / (R_ref × ΔT) × 10^6
        p.tcr = ((p.resistance - refR) / (refR * dT)) * 1e6
      } else {
        p.tcr = null
      }
    } else {
      p.tcr = null
    }
  }
  autoFillSummary()
}

const autoFillSummary = () => {
  const parts: string[] = []
  if (refResistance.value != null) parts.push(`参考阻值 ${refResistance.value.toFixed(6)}Ω`)
  if (avgTcr.value != null) parts.push(`平均TCR ${avgTcr.value.toFixed(2)}ppm/°C`)
  if (deltaR.value != null) parts.push(`最大变化量 ${deltaR.value.toFixed(6)}Ω`)
  if (parts.length) form.result_summary = `温漂测试：${parts.join('，')}，采样点 ${validPointCount.value}/${points.value.length}`
}

// ===== echarts 图表（懒加载）=====
const chartRef = ref<HTMLDivElement | null>(null)
const chartInstance = shallowRef<any>(null)
let echartsModule: any = null

const initChart = async () => {
  if (!chartRef.value) return
  if (!echartsModule) echartsModule = await import('echarts')
  // 先清理旧实例防止内存泄漏
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
  chartInstance.value = echartsModule.init(chartRef.value)
  renderChart()
}

const renderChart = () => {
  if (!chartInstance.value) return
  const valid = validPoints.value.slice().sort((a, b) => a.temperature - b.temperature)
  const option: any = {
    tooltip: { trigger: 'axis', formatter: (params: any) => {
      const p = params[0]
      return `温度: ${p.axisValue}°C<br/>阻值: ${p.data} Ω`
    }},
    grid: { left: 60, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      name: '温度 (°C)',
      data: valid.map(p => String(p.temperature)),
      axisLine: { lineStyle: { color: '#909399' } },
    },
    yAxis: {
      type: 'value',
      name: '阻值 (Ω)',
      axisLine: { lineStyle: { color: '#909399' } },
      axisLabel: { formatter: (v: number) => v.toFixed(4) },
    },
    series: [{
      name: '阻值',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: valid.map(p => p.resistance),
      lineStyle: { width: 2, color: '#409eff' },
      itemStyle: { color: '#409eff' },
      markPoint: {
        data: [
          { type: 'min', name: '最小值' },
          { type: 'max', name: '最大值' },
        ],
      },
      markLine: {
        data: [{ type: 'average', name: '平均值' }],
      },
    }],
  }
  chartInstance.value.setOption(option, true)
}

// 图表渲染防抖：避免每次录入阻值触发多次 renderChart
let renderChartTimer: ReturnType<typeof setTimeout> | null = null
watch([points, refResistance], () => {
  if (renderChartTimer) clearTimeout(renderChartTimer)
  renderChartTimer = setTimeout(() => {
    nextTick(renderChart)
    renderChartTimer = null
  }, 200)
}, { deep: true })

const handleResize = () => chartInstance.value?.resize()
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (renderChartTimer) clearTimeout(renderChartTimer)
  chartInstance.value?.dispose()
})

// ===== 数据加载 =====
const loadExperiment = async () => {
  try {
    const data = await experimentApi.get(experimentId)
    experiment.value = data
  } catch {
    ElMessage.error('实验不存在或无权访问')
    router.push('/experiments')
  }
}

const loadUsers = async () => {
  try {
    const res = await userApi.simpleList()
    userOptions.value = (res || []).map((u: any) => ({ id: u.id, name: u.real_name || u.username }))
  } catch {}
}

// ===== 提交 =====
const handleSubmit = async () => {
  if (!experiment.value) { ElMessage.warning('实验信息加载失败'); return }
  // 二次校验状态：专用测试页仅允许进行中的实验录入
  if (experiment.value.status !== 'in_progress') {
    ElMessage.error(`实验当前状态为「${experiment.value.status}」，仅「进行中」可录入测试记录`)
    return
  }
  if (!validPoints.value.length) { ElMessage.warning('请至少录入一个温度点的阻值'); return }
  if (refResistance.value == null) { ElMessage.warning('请录入参考温度点的阻值'); return }
  submitting.value = true
  try {
    const sorted = validPoints.value.slice().sort((a, b) => a.temperature - b.temperature)
    const param_values = {
      test_type: 'tcr',
      temp_config: { ...tempConfig },
      ref_resistance: refResistance.value,
      sample_points: sorted.map(p => ({
        temperature: p.temperature,
        resistance: p.resistance,
        tcr: p.tcr,
      })),
    }
    const result_data = {
      avg_tcr: avgTcr.value,
      max_tcr: maxTcr.value,
      min_tcr: minTcr.value,
      delta_r: deltaR.value,
      resistance_range: resistanceRange.value,
      valid_point_count: validPointCount.value,
      total_point_count: points.value.length,
      curve: sorted.map(p => ({ temperature: p.temperature, resistance: p.resistance })),
    }
    const payload: any = {
      batch_no: form.batch_no || null,
      sample_code: form.sample_code || null,
      executor_id: form.executor_id || null,
      param_values,
      result_data,
      result_summary: form.result_summary || null,
      conclusion: form.conclusion || null,
      is_abnormal: form.is_abnormal,
      abnormal_desc: form.is_abnormal ? (form.abnormal_desc || null) : null,
      executed_at: form.executed_at || null,
      experiment_id: experimentId,
    }
    await experimentApi.createRecord(payload)
    clearDraft()
    ElMessage.success('温漂测试记录已提交')
    router.push('/experiments')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  } finally { submitting.value = false }
}

const goBack = () => router.push('/experiments')

// 取消按钮：若有录入数据则二次确认
const handleCancel = async () => {
  if (validPoints.value.length) {
    try {
      await ElMessageBox.confirm('已录入的采样点数据将丢失，确定取消吗？', '提示', { type: 'warning' })
    } catch {
      return
    }
  }
  goBack()
}

// ===== 自动保存草稿 =====
const draftKey = `tcr_${experimentId}`
const draftData = computed(() => ({
  form: { ...form },
  tempConfig: { ...tempConfig },
  points: points.value,
}))
const { restore: restoreDraft, clear: clearDraft } = useAutoSave(draftKey, draftData, 2000)

onMounted(async () => {
  await loadExperiment()
  await loadUsers()
  // 恢复草稿
  const draft = restoreDraft()
  if (draft) {
    if (draft.form) Object.assign(form, draft.form)
    if (draft.tempConfig) Object.assign(tempConfig, draft.tempConfig)
    if (draft.points) points.value = draft.points
    ElMessage.info('已恢复未提交的草稿数据')
  }
  await nextTick()
  await initChart()
  window.addEventListener('resize', handleResize)
  // 不自动生成采样点：用户可能要先调整温度范围/参考温度再生成
})
</script>

<style scoped>
.tcr-test-page { padding: 0 0 16px 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.header-left { display: flex; align-items: center; }
</style>
