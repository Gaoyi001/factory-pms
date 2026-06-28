// 实验状态
export type ExperimentStatus = 'draft' | 'in_progress' | 'completed' | 'cancelled'

// 实验类型
export type ExperimentType = 'performance' | 'reliability' | 'environment' | 'material' | 'process' | 'other'

// 实验结论
export type RecordConclusion = 'pass' | 'fail' | 'conditional_pass' | 'need_retest'

// 参数模板项
export interface ParamTemplateItem {
  name: string
  unit?: string | null
  default?: any
  min?: number | null
  max?: number | null
}

export interface ExperimentOut {
  id: number
  code: string
  project_id: number
  name: string
  description?: string
  exp_type: ExperimentType
  status: ExperimentStatus
  designer_id?: number
  designer_name?: string
  executor_id?: number
  executor_name?: string
  plan_start?: string
  plan_end?: string
  actual_start?: string
  actual_end?: string
  param_template?: ParamTemplateItem[] | any
  created_at: string
  updated_at: string
}

export interface ExperimentAttachmentOut {
  id: number
  record_id: number
  file_name: string
  file_path: string
  file_size: number
  uploaded_at: string
}

export interface ExperimentRecordOut {
  id: number
  experiment_id: number
  batch_no?: string
  sample_code?: string
  executor_id?: number
  executor_name?: string
  param_values?: any
  result_data?: any
  result_summary?: string
  conclusion?: RecordConclusion
  is_abnormal: boolean
  abnormal_desc?: string
  executed_at?: string
  created_at: string
  attachment_count?: number
  attachments?: ExperimentAttachmentOut[]
}

// 状态/类型/结论下拉选项（与后端枚举保持一致）
export const EXPERIMENT_STATUS_OPTS = [
  { label: '草稿', value: 'draft', tag: 'info' as const },
  { label: '进行中', value: 'in_progress', tag: 'warning' as const },
  { label: '已完成', value: 'completed', tag: 'success' as const },
  { label: '已取消', value: 'cancelled', tag: 'danger' as const },
]

export const EXPERIMENT_TYPE_OPTS = [
  { label: '性能测试', value: 'performance' },
  { label: '可靠性测试', value: 'reliability' },
  { label: '环境测试', value: 'environment' },
  { label: '材料试验', value: 'material' },
  { label: '工艺验证', value: 'process' },
  { label: '其他', value: 'other' },
]

export const CONCLUSION_OPTS = [
  { label: '通过', value: 'pass', tag: 'success' as const },
  { label: '有条件通过', value: 'conditional_pass', tag: 'warning' as const },
  { label: '需复测', value: 'need_retest', tag: 'warning' as const },
  { label: '失败', value: 'fail', tag: 'danger' as const },
]

export const statusLabel = (s?: string) =>
  EXPERIMENT_STATUS_OPTS.find(o => o.value === s)?.label || s || '-'
export const statusTag = (s?: string) =>
  EXPERIMENT_STATUS_OPTS.find(o => o.value === s)?.tag || 'info'
export const typeLabel = (t?: string) =>
  EXPERIMENT_TYPE_OPTS.find(o => o.value === t)?.label || t || '-'
export const conclusionLabel = (c?: string) =>
  CONCLUSION_OPTS.find(o => o.value === c)?.label || c || '-'
export const conclusionTag = (c?: string) =>
  CONCLUSION_OPTS.find(o => o.value === c)?.tag || 'info'
