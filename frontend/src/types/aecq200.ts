/**
 * AEC-Q200 可靠性测试项预设模板
 * 基于 AEC-Q200 Rev D 标准，涵盖温度/机械/焊接/电气四类
 * 每项含标准参数模板与样品结果列定义，用户可在此基础上微调
 */

// 测试项分类
export type AecqCategory = 'temperature' | 'mechanical' | 'solder' | 'electrical'

// 参数模板项（复用实验层 ParamTemplateItem 结构，增加 input_type 便于渲染）
export interface AecqParamDef {
  key: string           // 参数键（存入 param_values.params）
  name: string          // 中文参数名
  unit?: string | null  // 单位
  default?: any         // 默认值
  min?: number | null   // 下限（用于范围校验）
  max?: number | null   // 上限
  input_type?: 'number' | 'text' | 'select'  // 输入类型，默认 number
  options?: string[]    // select 时的选项
}

// 样品结果列定义
export interface AecqSampleColumn {
  key: string           // 列键
  label: string         // 列标题
  unit?: string | null  // 单位（显示在列标题）
  input_type?: 'text' | 'number' | 'select'  // 输入类型，默认 text
  options?: string[]    // select 时的选项
  width?: number        // 列宽
  auto_calc?: boolean   // 是否自动计算（用户不可编辑）
}

// 测试项预设
export interface AecqTestItem {
  code: string          // 测试项代码（TC/HTS/...）
  name: string          // 中文名
  category: AecqCategory
  description?: string  // 测试目的简述
  params: AecqParamDef[]
  sample_columns: AecqSampleColumn[]
  // 自动判定规则说明（仅展示用）
  judge_rule: string
}

// 样品行结构（动态键，列定义决定字段）
export interface AecqSample {
  code: string          // 样品编号
  [key: string]: any
}

// ===== AEC-Q200 标准测试项预设 =====
export const AECQ200_TEST_ITEMS: AecqTestItem[] = [
  // ===== 温度类 =====
  {
    code: 'TC',
    name: '温度循环',
    category: 'temperature',
    description: '考核器件在交替高低温下的抗疲劳失效能力',
    params: [
      { key: 'temp_min', name: '温度下限', unit: '°C', default: -40, min: -70, max: 0, input_type: 'number' },
      { key: 'temp_max', name: '温度上限', unit: '°C', default: 125, min: 50, max: 200, input_type: 'number' },
      { key: 'dwell_time', name: '驻留时间', unit: 'min', default: 15, min: 5, max: 60, input_type: 'number' },
      { key: 'transition_time', name: '转换时间', unit: 'min', default: 5, min: 1, max: 20, input_type: 'number' },
      { key: 'cycles', name: '循环次数', unit: '次', default: 500, min: 100, max: 5000, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前电性能', unit: 'Ω', input_type: 'number', width: 130 },
      { key: 'after', label: '测试后电性能', unit: 'Ω', input_type: 'number', width: 130 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败（电性能变化超规格或外观异常视为失效）',
  },
  {
    code: 'HTS',
    name: '高温存储',
    category: 'temperature',
    description: '考核器件在高温环境下的长期存储稳定性',
    params: [
      { key: 'temp', name: '存储温度', unit: '°C', default: 125, min: 85, max: 200, input_type: 'number' },
      { key: 'duration', name: '存储时长', unit: 'h', default: 1000, min: 168, max: 10000, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'LTS',
    name: '低温存储',
    category: 'temperature',
    description: '考核器件在低温环境下的存储稳定性',
    params: [
      { key: 'temp', name: '存储温度', unit: '°C', default: -40, min: -70, max: 0, input_type: 'number' },
      { key: 'duration', name: '存储时长', unit: 'h', default: 1000, min: 168, max: 10000, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'TH',
    name: '温湿度',
    category: 'temperature',
    description: '考核器件在恒温恒湿环境下的抗潮湿能力',
    params: [
      { key: 'temp', name: '温度', unit: '°C', default: 85, min: 40, max: 150, input_type: 'number' },
      { key: 'humidity', name: '湿度', unit: '%RH', default: 85, min: 50, max: 100, input_type: 'number' },
      { key: 'duration', name: '时长', unit: 'h', default: 1000, min: 168, max: 4000, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'HAST',
    name: '高加速应力测试',
    category: 'temperature',
    description: 'HAST，加速温湿偏压测试，考核器件抗腐蚀能力',
    params: [
      { key: 'temp', name: '温度', unit: '°C', default: 130, min: 110, max: 150, input_type: 'number' },
      { key: 'humidity', name: '湿度', unit: '%RH', default: 85, min: 70, max: 100, input_type: 'number' },
      { key: 'duration', name: '时长', unit: 'h', default: 96, min: 24, max: 500, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'HTOL',
    name: '高温工作寿命',
    category: 'temperature',
    description: 'HTOL，通电状态下的高温寿命测试',
    params: [
      { key: 'temp', name: '环境温度', unit: '°C', default: 125, min: 85, max: 175, input_type: 'number' },
      { key: 'voltage', name: '通电电压', unit: 'V', default: 12, min: 1, max: 100, input_type: 'number' },
      { key: 'duration', name: '时长', unit: 'h', default: 1000, min: 168, max: 8000, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  // ===== 机械类 =====
  {
    code: 'MS',
    name: '机械冲击',
    category: 'mechanical',
    description: '考核器件在机械冲击下的结构完整性',
    params: [
      { key: 'peak_g', name: '峰值加速度', unit: 'G', default: 1500, min: 100, max: 30000, input_type: 'number' },
      { key: 'pulse_width', name: '脉冲宽度', unit: 'ms', default: 0.5, min: 0.1, max: 10, input_type: 'number' },
      { key: 'direction', name: '方向', default: 'X/Y/Z', input_type: 'text' },
      { key: 'shocks', name: '冲击次数', unit: '次', default: 5, min: 1, max: 30, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'VIB',
    name: '振动',
    category: 'mechanical',
    description: '考核器件在随机振动下的抗疲劳能力',
    params: [
      { key: 'freq_min', name: '频率下限', unit: 'Hz', default: 10, min: 5, max: 1000, input_type: 'number' },
      { key: 'freq_max', name: '频率上限', unit: 'Hz', default: 2000, min: 100, max: 10000, input_type: 'number' },
      { key: 'accel', name: '加速度', unit: 'G²/Hz', default: 7.6, min: 0.1, max: 50, input_type: 'number' },
      { key: 'direction', name: '方向', default: 'X/Y/Z', input_type: 'text' },
      { key: 'duration', name: '时长', unit: 'h', default: 4, min: 0.5, max: 48, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'DROP',
    name: '跌落测试',
    category: 'mechanical',
    description: '考核器件在自由跌落下的抗冲击能力',
    params: [
      { key: 'height', name: '跌落高度', unit: 'm', default: 1.0, min: 0.1, max: 5, input_type: 'number' },
      { key: 'drops', name: '跌落次数', unit: '次', default: 10, min: 1, max: 100, input_type: 'number' },
      { key: 'direction', name: '方向', default: '6面', input_type: 'text' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  // ===== 焊接类 =====
  {
    code: 'SOLDER',
    name: '可焊性',
    category: 'solder',
    description: '考核器件端子的可焊性',
    params: [
      { key: 'temp', name: '焊接温度', unit: '°C', default: 245, min: 215, max: 280, input_type: 'number' },
      { key: 'flux', name: '助焊剂类型', default: 'RMA', input_type: 'select', options: ['R', 'RMA', 'RA', '免清洗'] },
      { key: 'dwell', name: '浸润时间', unit: 's', default: 5, min: 1, max: 20, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'coverage', label: '浸润覆盖率', unit: '%', input_type: 'number', width: 130 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['良好', '一般', '差'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '覆盖率≥95% 且外观良好 → 通过；否则失败',
  },
  {
    code: 'RSHT',
    name: '耐焊接热',
    category: 'solder',
    description: '考核器件抵抗焊接热冲击的能力',
    params: [
      { key: 'peak_temp', name: '峰值温度', unit: '°C', default: 260, min: 240, max: 300, input_type: 'number' },
      { key: 'duration', name: '持续时间', unit: 's', default: 10, min: 5, max: 60, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'delta', label: '变化率', unit: '%', auto_calc: true, width: 100 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  {
    code: 'TS',
    name: '端子强度',
    category: 'solder',
    description: '考核器件端子的机械强度',
    params: [
      { key: 'pull_force', name: '拉力', unit: 'N', default: 20, min: 1, max: 200, input_type: 'number' },
      { key: 'push_force', name: '推力', unit: 'N', default: 50, min: 5, max: 500, input_type: 'number' },
      { key: 'hold_time', name: '保持时间', unit: 's', default: 30, min: 5, max: 120, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'max_force', label: '最大承受力', unit: 'N', input_type: 'number', width: 130 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
  // ===== 电气类 =====
  {
    code: 'IR',
    name: '绝缘电阻',
    category: 'electrical',
    description: '考核器件端子间的绝缘性能',
    params: [
      { key: 'voltage', name: '测试电压', unit: 'V', default: 500, min: 10, max: 5000, input_type: 'number' },
      { key: 'duration', name: '加压时间', unit: 's', default: 60, min: 1, max: 300, input_type: 'number' },
      { key: 'temp', name: '温度', unit: '°C', default: 25, min: -40, max: 150, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'ir_value', label: '绝缘电阻', unit: 'MΩ', input_type: 'number', width: 130 },
      { key: 'spec_min', label: '规格下限', unit: 'MΩ', input_type: 'number', width: 120 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '绝缘电阻≥规格下限 → 通过；否则失败',
  },
  {
    code: 'DWV',
    name: '耐电压',
    category: 'electrical',
    description: '考核器件端子间的耐压能力',
    params: [
      { key: 'voltage', name: '测试电压', unit: 'V', default: 1000, min: 100, max: 10000, input_type: 'number' },
      { key: 'duration', name: '加压时间', unit: 's', default: 60, min: 1, max: 300, input_type: 'number' },
      { key: 'leak_limit', name: '漏电流限值', unit: 'mA', default: 1, min: 0.01, max: 10, input_type: 'number' },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'leak_current', label: '漏电流', unit: 'mA', input_type: 'number', width: 120 },
      { key: 'breakdown', label: '是否击穿', input_type: 'select', options: ['否', '是'], width: 100 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '漏电流<限值 且 未击穿 → 通过；否则失败',
  },
  {
    code: 'ESD',
    name: '静电放电',
    category: 'electrical',
    description: 'ESD，考核器件抗静电能力',
    params: [
      { key: 'voltage', name: '放电电压', unit: 'V', default: 4000, min: 500, max: 15000, input_type: 'number' },
      { key: 'strikes', name: '放电次数', unit: '次', default: 3, min: 1, max: 10, input_type: 'number' },
      { key: 'model', name: '放电模式', default: 'HBM', input_type: 'select', options: ['HBM', 'CDM', 'MM'] },
    ],
    sample_columns: [
      { key: 'code', label: '样品编号', width: 120 },
      { key: 'before', label: '测试前', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'after', label: '测试后', unit: 'Ω', input_type: 'number', width: 120 },
      { key: 'appearance', label: '外观', input_type: 'select', options: ['正常', '异常'], width: 90 },
      { key: 'result', label: '判定', input_type: 'select', options: ['pass', 'fail'], width: 90 },
      { key: 'remark', label: '备注', width: 140 },
    ],
    judge_rule: '失效数=0 → 通过；失效数≥1 → 失败',
  },
]

// 测试项分类标签
export const AECQ_CATEGORY_LABEL: Record<AecqCategory, string> = {
  temperature: '温度类',
  mechanical: '机械类',
  solder: '焊接类',
  electrical: '电气类',
}

// 测试项分类颜色（el-tag type）
export const AECQ_CATEGORY_TAG: Record<AecqCategory, string> = {
  temperature: 'danger',
  mechanical: 'warning',
  solder: 'primary',
  electrical: 'success',
}

// 按 code 查找测试项
export const findTestItem = (code: string): AecqTestItem | undefined =>
  AECQ200_TEST_ITEMS.find(t => t.code === code)
