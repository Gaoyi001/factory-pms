<template>
  <div class="temp-rise-page">
    <!-- 顶部信息 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回实验</el-button>
        <h2 style="margin:0 0 0 12px">温升测试</h2>
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
      <el-col :span="16">
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
          <template #header><span style="font-weight:600">功率采样设置</span></template>
          <el-form :model="powerConfig" label-width="100px">
            <el-row :gutter="12">
              <el-col :span="6">
                <el-form-item label="起始功率">
                  <el-input-number v-model="powerConfig.start" :step="0.1" :min="0" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="结束功率">
                  <el-input-number v-model="powerConfig.end" :step="0.1" :min="0" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="采样间隔">
                  <el-input-number v-model="powerConfig.step" :step="0.1" :min="0.01" controls-position="right" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="参考阻值">
                  <el-input-number v-model="powerConfig.ref_resistance" :precision="3" :step="0.1" :min="0.001" controls-position="right" style="width:100%" />
                  <span style="color:#909399;font-size:12px">mΩ</span>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="环境温度">
              <el-input-number v-model="powerConfig.ambient_temp" :precision="1" :step="0.5" controls-position="right" style="width:200px" @input="recalcAllTempRise" />
              <span style="margin-left:8px;color:#909399;font-size:12px">°C（统一环境温度，温升 = 本体温度 - 环境温度）</span>
            </el-form-item>
            <div style="text-align:right">
              <el-button type="primary" @click="generatePoints">
                <el-icon><Refresh /></el-icon> 生成测试点
              </el-button>
              <el-button @click="clearPoints">清空</el-button>
            </div>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-top:12px">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600">功率-参数录入</span>
              <span style="color:#909399;font-size:12px">
                共 {{ points.length }} 个测试点
                <span v-if="powerConfig.ref_resistance" style="margin-left:8px">参考阻值 {{ powerConfig.ref_resistance }}mΩ</span>
                <span v-if="ratedCurrent != null" style="margin-left:8px;color:#409eff">额定电流 {{ ratedCurrent.toFixed(4) }}A</span>
              </span>
            </div>
          </template>
          <el-alert type="info" :closable="false" style="margin-bottom:8px">
            <template #title>
              <span style="font-size:12px">
                换算规则：录入<b>功率</b>自动算电流 I=√(P/R) 和默认电压；录入<b>电流</b>自动算功率 P=I²R 和默认电压；录入<b>电压</b>自动算阻值 R_mΩ = V_mV / I；<b>本体温度=核心温度</b>（热源），电极和PCB为散热路径，录入温度后自动算各段热阻 R_th=(T_核心-T_终点)/P（核心→电极1/电极2/PCB/环境）；录入<b>总热阻</b>反算核心温度。阻值 mΩ，电压 mV。
              </span>
            </template>
          </el-alert>
          <el-table :data="points" size="small" border empty-text="请先生成测试点" max-height="520" style="width:100%">
            <el-table-column label="#" type="index" width="45" fixed="left" />
            <el-table-column label="功率 (W)" width="120" fixed="left">
              <template #default="{ row }">
                <el-input-number v-model="row.power" :precision="4" :step="0.01" :min="0" controls-position="right" size="small" style="width:100%" @input="recalcFromPower(row)" />
              </template>
            </el-table-column>
            <el-table-column label="电流 (A)" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.current" :precision="4" :step="0.01" :min="0" controls-position="right" size="small" style="width:100%" @input="recalcFromCurrent(row)" />
              </template>
            </el-table-column>
            <el-table-column label="电压 (mV)" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.voltage" :precision="4" :step="0.01" :min="0" controls-position="right" size="small" style="width:100%" @input="recalcResistanceFromVoltage(row)" />
              </template>
            </el-table-column>
            <el-table-column label="阻值 (mΩ)" width="130">
              <template #default="{ row }">
                <el-input-number v-model="row.resistance" :precision="3" :step="0.1" :min="0" controls-position="right" size="small" style="width:100%" @input="recalcFromResistance(row)" />
              </template>
            </el-table-column>
            <el-table-column label="本体温度" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.body_temp" :precision="1" :step="0.5" controls-position="right" size="small" style="width:100%" @input="recalculate(row)" />
              </template>
            </el-table-column>
            <el-table-column label="电极温度1" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.electrode_temp_1" :precision="1" :step="0.5" controls-position="right" size="small" style="width:100%" @input="recalculate(row)" />
              </template>
            </el-table-column>
            <el-table-column label="电极温度2" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.electrode_temp_2" :precision="1" :step="0.5" controls-position="right" size="small" style="width:100%" @input="recalculate(row)" />
              </template>
            </el-table-column>
            <el-table-column label="PCB温度" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.pcb_temp" :precision="1" :step="0.5" controls-position="right" size="small" style="width:100%" @input="recalculate(row)" />
              </template>
            </el-table-column>
            <el-table-column label="核心→电极1 (°C/W)" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.rth_core_to_electrode1" :precision="3" :step="0.1" :min="0" controls-position="right" size="small" style="width:100%" disabled />
              </template>
            </el-table-column>
            <el-table-column label="核心→电极2 (°C/W)" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.rth_core_to_electrode2" :precision="3" :step="0.1" :min="0" controls-position="right" size="small" style="width:100%" disabled />
              </template>
            </el-table-column>
            <el-table-column label="核心→PCB (°C/W)" width="130">
              <template #default="{ row }">
                <el-input-number v-model="row.rth_core_to_pcb" :precision="3" :step="0.1" :min="0" controls-position="right" size="small" style="width:100%" disabled />
              </template>
            </el-table-column>
            <el-table-column label="总热阻 核心→环境 (°C/W)" width="160">
              <template #default="{ row }">
                <el-input-number v-model="row.rth_core_to_ambient" :precision="3" :step="0.1" :min="0" controls-position="right" size="small" style="width:100%" @input="recalcThermalFromManual(row)" />
              </template>
            </el-table-column>
            <!-- 自动计算列 -->
            <el-table-column label="温升 ΔT" width="90" fixed="right">
              <template #default="{ row }">
                <span v-if="row.temp_rise != null" :style="{ color: row.temp_rise > 80 ? '#f56c6c' : '#67c23a', fontWeight: 600 }">
                  {{ row.temp_rise.toFixed(1) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="平均电极温度" width="110" fixed="right">
              <template #default="{ row }">
                <span v-if="row.avg_electrode_temp != null">{{ row.avg_electrode_temp.toFixed(1) }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="阻值变化率 (%)" width="120" fixed="right">
              <template #default="{ row }">
                <span v-if="row.resistance_change_rate != null" :style="{ color: changeRateColor(row.resistance_change_rate), fontWeight: 600 }">
                  {{ row.resistance_change_rate.toFixed(4) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" fixed="right">
              <template #default="{ $index }">
                <el-button link type="danger" size="small" @click="points.splice($index, 1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:8px">
            <el-button size="small" @click="addPoint">
              <el-icon><Plus /></el-icon> 追加一行
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：计算结果与曲线 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">汇总计算</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="额定电流">
              <span v-if="ratedCurrent != null" style="color:#409eff;font-weight:600">
                {{ ratedCurrent.toFixed(4) }} A
              </span>
              <span v-else>-</span>
              <span v-if="powerConfig.ref_resistance" style="color:#909399;font-size:12px;margin-left:4px">
                (√(P_max/R), R={{ powerConfig.ref_resistance }}mΩ)
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="额定电压">
              <span v-if="ratedVoltage != null" style="color:#409eff;font-weight:600">
                {{ ratedVoltage.toFixed(2) }} mV
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="功率范围">
              {{ powerConfig.start }} ~ {{ powerConfig.end }} W
            </el-descriptions-item>
            <el-descriptions-item label="电流范围">
              {{ currentRange || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="测试点数">
              {{ validPointCount }} / {{ points.length }}
            </el-descriptions-item>
            <el-descriptions-item label="最大温升">
              <span :style="{ color: maxTempRise != null && maxTempRise > 80 ? '#f56c6c' : '#67c23a', fontWeight: 600 }">
                {{ maxTempRise != null ? maxTempRise.toFixed(1) + ' °C' : '-' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="平均温升">
              {{ avgTempRise != null ? avgTempRise.toFixed(1) + ' °C' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="最大阻值变化率">
              <span :style="{ color: maxChangeRate != null ? changeRateColor(maxChangeRate) : '' }">
                {{ maxChangeRate != null ? maxChangeRate.toFixed(4) + ' %' : '-' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="最大热阻">
              {{ maxThermalResistance != null ? maxThermalResistance.toFixed(3) + ' °C/W' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="最大本体温度">
              {{ maxBodyTemp != null ? maxBodyTemp.toFixed(1) + ' °C' : '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <div style="margin-top:16px">
            <el-form-item label="结论" label-width="60px">
              <el-select v-model="form.conclusion" clearable style="width:100%">
                <el-option v-for="c in CONCLUSION_OPTS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="摘要" label-width="60px">
              <el-input v-model="form.result_summary" type="textarea" :rows="3" placeholder="自动生成或手动填写" />
            </el-form-item>
            <el-form-item label="异常" label-width="60px">
              <el-switch v-model="form.is_abnormal" />
              <el-button v-if="!form.is_abnormal" link type="primary" size="small" style="margin-left:12px" @click="autoJudgeAbnormal">
                智能判断
              </el-button>
            </el-form-item>
            <el-form-item v-if="form.is_abnormal" label="异常描述" label-width="60px">
              <el-input v-model="form.abnormal_desc" type="textarea" :rows="2" />
            </el-form-item>
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top:12px">
          <template #header><span style="font-weight:600">电流-温升/变化率曲线</span></template>
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
import { ArrowLeft, Refresh, Check, Plus } from '@element-plus/icons-vue'
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

const powerConfig = reactive({
  start: 0.5,
  end: 3.0,
  step: 0.5,
  ref_resistance: null as number | null,        // 单位 mΩ
  ambient_temp: 25 as number | null,            // 统一环境温度 °C
})

interface TempRisePoint {
  current: number | null       // A
  voltage: number | null       // mV
  power: number | null         // W
  resistance: number | null    // mΩ
  body_temp: number | null              // 核心温度
  electrode_temp_1: number | null
  electrode_temp_2: number | null
  pcb_temp: number | null
  // 散热路径热阻（自动计算，°C/W）
  rth_core_to_electrode1: number | null  // 核心→电极1
  rth_core_to_electrode2: number | null  // 核心→电极2
  rth_core_to_pcb: number | null         // 核心→PCB
  rth_core_to_ambient: number | null     // 核心→环境（总热阻）
  // 自动计算
  temp_rise: number | null               // 核心 - 环境温度
  avg_electrode_temp: number | null
  resistance_change_rate: number | null
}

const points = ref<TempRisePoint[]>([])

// ===== 自动保存草稿 =====
const draftKey = `tempRise_${experimentId}`
const draftData = computed(() => ({
  form: { ...form },
  powerConfig: { ...powerConfig },
  points: points.value,
}))
const { restore: restoreDraft, clear: clearDraft } = useAutoSave(draftKey, draftData, 2000)

// 单位换算：mΩ → Ω, mV → V
const mOhmToOhm = (m: number) => m / 1000
const mVToV = (m: number) => m / 1000

// ===== 计算属性 =====
// 额定电流 I = √(P/R_Ω)（基于参考阻值，默认按最大功率点估算，此处保留为可选展示）
const ratedCurrent = computed(() => {
  // 取有效点中最大功率对应的电流作为额定电流参考
  if (powerConfig.ref_resistance && powerConfig.ref_resistance > 0) {
    const maxPower = validPoints.value.map(p => p.power).filter((v): v is number => v != null && v > 0)
    if (maxPower.length) {
      const P = Math.max(...maxPower)
      return Math.sqrt(P / mOhmToOhm(powerConfig.ref_resistance))
    }
  }
  return null
})
// 额定电压 V = I × R_Ω（显示为 mV）
const ratedVoltage = computed(() => {
  if (ratedCurrent.value != null && powerConfig.ref_resistance) {
    return ratedCurrent.value * mOhmToOhm(powerConfig.ref_resistance) * 1000  // 转 mV
  }
  return null
})

const validPoints = computed(() => points.value.filter(p =>
  p.power != null || p.current != null || (p.body_temp != null || p.resistance != null || p.voltage != null)
))
const validPointCount = computed(() => validPoints.value.length)

const currentRange = computed(() => {
  const currents = points.value.map(p => p.current).filter((c): c is number => c != null)
  if (!currents.length) return ''
  return `${Math.min(...currents).toFixed(2)} ~ ${Math.max(...currents).toFixed(2)} A`
})

const tempRiseValues = computed(() => validPoints.value.map(p => p.temp_rise).filter((v): v is number => v != null))
const maxTempRise = computed(() => tempRiseValues.value.length ? Math.max(...tempRiseValues.value) : null)
const avgTempRise = computed(() => tempRiseValues.value.length ? tempRiseValues.value.reduce((a, b) => a + b, 0) / tempRiseValues.value.length : null)

const changeRateValues = computed(() => validPoints.value.map(p => p.resistance_change_rate).filter((v): v is number => v != null))
const maxChangeRate = computed(() => changeRateValues.value.length ? Math.max(...changeRateValues.value.map(Math.abs)) : null)

const thermalValues = computed(() => validPoints.value.map(p => p.rth_core_to_ambient).filter((v): v is number => v != null))
const maxThermalResistance = computed(() => thermalValues.value.length ? Math.max(...thermalValues.value) : null)

const bodyTempValues = computed(() => validPoints.value.map(p => p.body_temp).filter((v): v is number => v != null))
const maxBodyTemp = computed(() => bodyTempValues.value.length ? Math.max(...bodyTempValues.value) : null)

const changeRateColor = (v: number | null) => {
  if (v == null) return ''
  const abs = Math.abs(v)
  if (abs <= 1) return '#67c23a'
  if (abs <= 3) return '#e6a23c'
  return '#f56c6c'
}

// ===== 行级计算 =====
// 获取换算用阻值(Ω)：优先本行阻值(mΩ)，其次参考阻值(mΩ)
const getEffResistanceOhm = (row: TempRisePoint): number | null => {
  if (row.resistance != null && row.resistance > 0) return mOhmToOhm(row.resistance)
  if (powerConfig.ref_resistance && powerConfig.ref_resistance > 0) return mOhmToOhm(powerConfig.ref_resistance)
  return null
}

// 根据行内功率、电流、参考阻值计算默认电压(mV)
// 优先级：1) V_mV = I × R_Ω × 1000（有电流和阻值时）
//         2) V_mV = √(P × R_Ω) × 1000（有功率和参考阻值时，因 I=√(P/R)，V=IR=√(PR)）
//         3) V_mV = P / I × 1000（有功率和电流时，V=P/I）
const calcDefaultVoltage = (row: TempRisePoint): number | null => {
  const R_ohm = getEffResistanceOhm(row)  // 优先本行阻值，无则参考阻值
  // 1) 有电流和阻值：V = I × R
  if (row.current != null && row.current > 0 && R_ohm != null && R_ohm > 0) {
    return Math.round(row.current * R_ohm * 1000 * 10000) / 10000
  }
  // 2) 有功率和阻值：V = √(P × R)（因 I=√(P/R)，V=IR=√(PR)）
  if (row.power != null && row.power > 0 && R_ohm != null && R_ohm > 0) {
    return Math.round(Math.sqrt(row.power * R_ohm) * 1000 * 10000) / 10000
  }
  // 3) 有功率和电流：V = P / I
  if (row.power != null && row.power > 0 && row.current != null && row.current > 0) {
    return Math.round((row.power / row.current) * 1000 * 10000) / 10000
  }
  return null
}

// 录入功率 → 自动换算电流 I=√(P/R)，刷新默认电压 V=IR，重算散热路径热阻
const recalcFromPower = (row: TempRisePoint) => {
  recalcFromPowerOnly(row)
  autoFillSummary()
}

// 仅行级计算（不触发汇总重算），供批量生成使用，避免 O(n²)
const recalcFromPowerOnly = (row: TempRisePoint) => {
  const R = getEffResistanceOhm(row)
  if (row.power != null && row.power > 0 && R != null && R > 0) {
    row.current = Math.sqrt(row.power / R)
    // 同步刷新默认电压（V_mV = I × R_Ω × 1000）
    const v = calcDefaultVoltage(row)
    if (v != null && v > 0) row.voltage = v
  }
  // 功率变化后重算散热路径热阻
  recalculate(row)
  recalcChangeRate(row)
}

// 录入电流 → 自动换算功率 P=I²R，刷新默认电压 V=IR，重算散热路径热阻
const recalcFromCurrent = (row: TempRisePoint) => {
  const R = getEffResistanceOhm(row)
  if (row.current != null && row.current > 0 && R != null) {
    row.power = row.current * row.current * R
    // 同步刷新默认电压（V_mV = I × R_Ω × 1000）
    const v = calcDefaultVoltage(row)
    if (v != null && v > 0) row.voltage = v
  }
  // 功率变化后重算散热路径热阻
  recalculate(row)
  recalcChangeRate(row)
  autoFillSummary()
}

// 录入电压(mV) → 根据电流换算阻值 R_mΩ = (V_mV / 1000) / I × 1000 = V_mV / I
const recalcResistanceFromVoltage = (row: TempRisePoint) => {
  if (row.voltage != null && row.current != null && row.current > 0) {
    // R(Ω) = V(V) / I = (V_mV / 1000) / I；R(mΩ) = R(Ω) × 1000 = V_mV / I
    row.resistance = row.voltage / row.current
    recalcChangeRate(row)
  }
  autoFillSummary()
}

// 录入阻值(mΩ) → 根据已有电流或功率重算另一电气量（电压不联动）+ 阻值变化率
const recalcFromResistance = (row: TempRisePoint) => {
  const R = row.resistance != null ? mOhmToOhm(row.resistance) : null
  if (R != null && R > 0) {
    if (row.current != null && row.current > 0) {
      // 已有电流：重算功率（电压不动）
      row.power = row.current * row.current * R
    } else if (row.power != null && row.power > 0) {
      // 已有功率：重算电流（电压不动）
      row.current = Math.sqrt(row.power / R)
    }
  }
  recalcChangeRate(row)
  autoFillSummary()
}

// 温度相关计算（温升、散热路径热阻、平均电极温度）
// 本体温度 = 核心温度（热源）
// 散热路径：核心 → 电极1 / 电极2 / PCB / 环境
// 各段热阻 R_th = (T_核心 - T_终点) / P
// recalculateCore: 不重算 rth_core_to_ambient，避免覆盖用户手动输入值
const recalculateCore = (row: TempRisePoint) => {
  const T_core = row.body_temp
  const T_amb = powerConfig.ambient_temp
  const P = row.power
  const hasPower = P != null && P > 0

  // 温升 = 核心温度 - 环境温度
  if (T_core != null && T_amb != null) {
    row.temp_rise = Math.round((T_core - T_amb) * 10) / 10
  } else {
    row.temp_rise = null
  }

  // 散热路径热阻（°C/W）— 不包含 rth_core_to_ambient
  if (T_core != null && hasPower) {
    row.rth_core_to_electrode1 = row.electrode_temp_1 != null
      ? Math.round(((T_core - row.electrode_temp_1) / (P as number)) * 1000) / 1000 : null
    row.rth_core_to_electrode2 = row.electrode_temp_2 != null
      ? Math.round(((T_core - row.electrode_temp_2) / (P as number)) * 1000) / 1000 : null
    row.rth_core_to_pcb = row.pcb_temp != null
      ? Math.round(((T_core - row.pcb_temp) / (P as number)) * 1000) / 1000 : null
  } else {
    row.rth_core_to_electrode1 = null
    row.rth_core_to_electrode2 = null
    row.rth_core_to_pcb = null
  }

  // 平均电极温度
  const electrodes = [row.electrode_temp_1, row.electrode_temp_2].filter((v): v is number => v != null)
  row.avg_electrode_temp = electrodes.length ? electrodes.reduce((a, b) => a + b, 0) / electrodes.length : null
}

// 完整计算：包含 rth_core_to_ambient（用于温度/电极/PCB 变化时自动算总热阻）
const recalculate = (row: TempRisePoint) => {
  const T_core = row.body_temp
  const T_amb = powerConfig.ambient_temp
  const P = row.power
  const hasPower = P != null && P > 0

  recalculateCore(row)

  // 总热阻 核心→环境（仅在非手动录入场景重算）
  if (T_core != null && T_amb != null && hasPower) {
    row.rth_core_to_ambient = Math.round(((T_core - T_amb) / (P as number)) * 1000) / 1000
  } else if (!hasPower || T_core == null || T_amb == null) {
    row.rth_core_to_ambient = null
  }
  autoFillSummary()
}

// 环境温度变化 → 重算所有行的温升和总热阻（核心→环境）
const recalcAllTempRise = () => {
  points.value.forEach(row => recalculate(row))
}

// 手动录入总热阻（核心→环境）→ 反算核心温度
// 核心温度 = 环境温度 + 总热阻 × 功率
// 反算后用 recalculateCore 避免覆盖用户刚输入的 rth_core_to_ambient
const recalcThermalFromManual = (row: TempRisePoint) => {
  if (row.rth_core_to_ambient != null && row.rth_core_to_ambient > 0
      && row.power != null && row.power > 0
      && powerConfig.ambient_temp != null) {
    row.temp_rise = Math.round(row.rth_core_to_ambient * row.power * 10) / 10
    row.body_temp = Math.round((powerConfig.ambient_temp + row.temp_rise) * 10) / 10
    // 反算核心温度后，仅重算其他路径热阻和温升，不覆盖手动输入的总热阻
    recalculateCore(row)
  }
  autoFillSummary()
}

// 根据参考阻值计算阻值变化率（同单位 mΩ 直接比较）
const recalcChangeRate = (row: TempRisePoint) => {
  if (row.resistance != null && powerConfig.ref_resistance && powerConfig.ref_resistance > 0) {
    row.resistance_change_rate = ((row.resistance - powerConfig.ref_resistance) / powerConfig.ref_resistance) * 100
  } else {
    row.resistance_change_rate = null
  }
}

// ===== 采样点生成（按功率） =====
const generatePoints = () => {
  const { start, end, step } = powerConfig
  if (step <= 0) { ElMessage.warning('采样间隔必须大于 0'); return }
  if (start > end) { ElMessage.warning('起始功率不能大于结束功率'); return }

  const arr: TempRisePoint[] = []
  for (let p = start; p <= end + 0.0001; p += step) {
    const power = Math.round(p * 10000) / 10000  // 保留4位小数避免浮点误差
    arr.push(createEmptyPoint(power))
  }
  points.value = arr
  // 生成后：1) 若有参考阻值，按功率换算电流；2) 根据功率/电流/参考阻值填入默认电压并换算阻值
  // 批量生成时只做行级计算，循环结束后统一汇总一次，避免 O(n²)
  if (powerConfig.ref_resistance && powerConfig.ref_resistance > 0) {
    points.value.forEach(p => recalcFromPowerOnly(p))
  }
  points.value.forEach(p => {
    if (p.voltage == null) {
      const v = calcDefaultVoltage(p)
      if (v != null && v > 0) {
        p.voltage = v
        // 电压默认值不触发阻值反算（阻值由参考阻值或后续手动录入电压时换算）
      }
    }
  })
  ElMessage.success(`已生成 ${arr.length} 个测试点`)
  autoFillSummary()
}

const createEmptyPoint = (power: number): TempRisePoint => ({
  power,
  current: null,
  voltage: null,
  resistance: null,
  body_temp: null,
  electrode_temp_1: null,
  electrode_temp_2: null,
  pcb_temp: null,
  rth_core_to_electrode1: null,
  rth_core_to_electrode2: null,
  rth_core_to_pcb: null,
  rth_core_to_ambient: null,
  temp_rise: null,
  avg_electrode_temp: null,
  resistance_change_rate: null,
})

const addPoint = () => {
  const lastPower = points.value.length && points.value[points.value.length - 1].power != null
    ? points.value[points.value.length - 1].power as number
    : 0
  const newPower = Math.round((lastPower + powerConfig.step) * 10000) / 10000
  const newPoint = createEmptyPoint(newPower)
  if (powerConfig.ref_resistance && powerConfig.ref_resistance > 0) {
    recalcFromPower(newPoint)
  }
  // 根据行内功率/电流/参考阻值计算默认电压
  const v = calcDefaultVoltage(newPoint)
  if (v != null && v > 0) {
    newPoint.voltage = v
  }
  points.value.push(newPoint)
}

const clearPoints = () => {
  points.value = []
}

// ===== 自动摘要 =====
const autoFillSummary = () => {
  const parts: string[] = []
  if (powerConfig.ref_resistance) parts.push(`参考阻值 ${powerConfig.ref_resistance}mΩ`)
  if (ratedCurrent.value != null) parts.push(`额定电流 ${ratedCurrent.value.toFixed(4)}A`)
  if (ratedVoltage.value != null) parts.push(`额定电压 ${ratedVoltage.value.toFixed(2)}mV`)
  if (maxTempRise.value != null) parts.push(`最大温升 ${maxTempRise.value.toFixed(1)}°C`)
  if (avgTempRise.value != null) parts.push(`平均温升 ${avgTempRise.value.toFixed(1)}°C`)
  if (maxChangeRate.value != null) parts.push(`最大阻值变化率 ${maxChangeRate.value.toFixed(4)}%`)
  if (parts.length) form.result_summary = `温升测试：${parts.join('，')}，测试点 ${validPointCount.value}/${points.value.length}`
}

// ===== 智能异常判断 =====
const autoJudgeAbnormal = () => {
  const issues: string[] = []
  if (maxTempRise.value != null && maxTempRise.value > 80) issues.push(`温升过高（最大 ${maxTempRise.value.toFixed(1)}°C > 80°C）`)
  if (maxChangeRate.value != null && maxChangeRate.value > 3) issues.push(`阻值变化率过大（最大 ${maxChangeRate.value.toFixed(4)}%）`)
  if (maxThermalResistance.value != null && maxThermalResistance.value > 100) issues.push(`热阻偏高（最大 ${maxThermalResistance.value}°C/W）`)
  if (maxBodyTemp.value != null && maxBodyTemp.value > 125) issues.push(`本体温度过高（最大 ${maxBodyTemp.value.toFixed(1)}°C）`)

  if (issues.length) {
    form.is_abnormal = true
    form.abnormal_desc = issues.join('；')
    ElMessage.warning(`检测到 ${issues.length} 项异常`)
  } else {
    form.is_abnormal = false
    form.abnormal_desc = ''
    ElMessage.success('未检测到异常')
  }
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
  const valid = validPoints.value.slice().sort((a, b) => (a.power ?? 0) - (b.power ?? 0))
  const powers = valid.map(p => String(p.power))
  const tempRiseData = valid.map(p => p.temp_rise)
  const changeRateData = valid.map(p => p.resistance_change_rate)

  const option: any = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['温升 ΔT (°C)', '阻值变化率 (%)'], top: 0 },
    grid: { left: 60, right: 70, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      name: '功率 (W)',
      data: powers,
      axisLine: { lineStyle: { color: '#909399' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '温升 (°C)',
        position: 'left',
        axisLine: { lineStyle: { color: '#f56c6c' } },
        axisLabel: { formatter: '{value}' },
      },
      {
        type: 'value',
        name: '变化率 (%)',
        position: 'right',
        axisLine: { lineStyle: { color: '#409eff' } },
        axisLabel: { formatter: '{value}' },
      },
    ],
    series: [
      {
        name: '温升 ΔT (°C)',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: tempRiseData,
        lineStyle: { width: 2, color: '#f56c6c' },
        itemStyle: { color: '#f56c6c' },
        markPoint: { data: [{ type: 'max', name: '最大值' }] },
      },
      {
        name: '阻值变化率 (%)',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        yAxisIndex: 1,
        data: changeRateData,
        lineStyle: { width: 2, color: '#409eff' },
        itemStyle: { color: '#409eff' },
      },
    ],
  }
  chartInstance.value.setOption(option, true)
}

// 图表渲染防抖：避免 input-number 每输一个字符触发 renderChart
let renderChartTimer: ReturnType<typeof setTimeout> | null = null
watch([points], () => {
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
  if (!validPoints.value.length) { ElMessage.warning('请至少录入一个测试点的数据'); return }
  submitting.value = true
  try {
    const sorted = validPoints.value.slice().sort((a, b) => (a.power ?? 0) - (b.power ?? 0))
    const param_values = {
      test_type: 'temp_rise',
      power_config: { ...powerConfig, ref_resistance_ohm: powerConfig.ref_resistance ? mOhmToOhm(powerConfig.ref_resistance) : null },
      rated_current: ratedCurrent.value,
      rated_voltage_v: ratedVoltage.value != null ? ratedVoltage.value / 1000 : null,  // mV → V
      sample_points: sorted.map(p => ({
        power: p.power,
        current: p.current,
        voltage_v: p.voltage != null ? mVToV(p.voltage) : null,        // mV → V
        resistance_ohm: p.resistance != null ? mOhmToOhm(p.resistance) : null,  // mΩ → Ω
        resistance_mohm: p.resistance,
        voltage_mv: p.voltage,
        body_temp: p.body_temp,                    // 核心温度
        electrode_temp_1: p.electrode_temp_1,
        electrode_temp_2: p.electrode_temp_2,
        pcb_temp: p.pcb_temp,
        ambient_temp: powerConfig.ambient_temp,    // 全局环境温度
        // 散热路径热阻（°C/W）
        rth_core_to_electrode1: p.rth_core_to_electrode1,
        rth_core_to_electrode2: p.rth_core_to_electrode2,
        rth_core_to_pcb: p.rth_core_to_pcb,
        rth_core_to_ambient: p.rth_core_to_ambient,
        temp_rise: p.temp_rise,
        avg_electrode_temp: p.avg_electrode_temp,
        resistance_change_rate: p.resistance_change_rate,
      })),
    }
    const result_data = {
      rated_current: ratedCurrent.value,
      rated_voltage_v: ratedVoltage.value != null ? ratedVoltage.value / 1000 : null,
      rated_voltage_mv: ratedVoltage.value,
      power_range: `${powerConfig.start} ~ ${powerConfig.end} W`,
      current_range: currentRange.value,
      total_point_count: points.value.length,
      valid_point_count: validPointCount.value,
      max_temp_rise: maxTempRise.value,
      avg_temp_rise: avgTempRise.value,
      max_change_rate: maxChangeRate.value,
      max_thermal_resistance: maxThermalResistance.value,
      max_body_temp: maxBodyTemp.value,
      curve: sorted.map(p => ({
        power: p.power,
        current: p.current,
        temp_rise: p.temp_rise,
        resistance_change_rate: p.resistance_change_rate,
      })),
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
    ElMessage.success('温升测试记录已提交')
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
      await ElMessageBox.confirm('已录入的测试点数据将丢失，确定取消吗？', '提示', { type: 'warning' })
    } catch {
      return
    }
  }
  goBack()
}

onMounted(async () => {
  await loadExperiment()
  await loadUsers()
  // 恢复草稿
  const draft = restoreDraft()
  if (draft) {
    if (draft.form) Object.assign(form, draft.form)
    if (draft.powerConfig) Object.assign(powerConfig, draft.powerConfig)
    if (draft.points) points.value = draft.points
    ElMessage.info('已恢复未提交的草稿数据')
  }
  await nextTick()
  await initChart()
  window.addEventListener('resize', handleResize)
  // 不自动生成采样点：用户可能要先调整功率范围/参考阻值再生成
})
</script>

<style scoped>
.temp-rise-page { padding: 0 0 16px 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.header-left { display: flex; align-items: center; }
</style>
