/**
 * 自定义测试项管理（localStorage 持久化）
 *
 * 用途：让「通用记录」也能像 AEC-Q200 一样使用结构化参数表单 + 批量样品表格，
 * 但测试项由用户自定义，不依赖后端。
 *
 * 存储位置：localStorage key = 'pms:custom_test_items'
 * 数据结构：CustomTestItem[]
 */

// ===== 类型定义（与 AEC-Q200 对齐，便于复用渲染逻辑） =====

// 参数定义
export interface CustomParamDef {
  key: string            // 参数键
  name: string           // 参数名
  unit?: string | null   // 单位
  default?: any          // 默认值
  min?: number | null    // 下限
  max?: number | null    // 上限
  input_type?: 'number' | 'text' | 'select'  // 输入类型，默认 number
  options?: string[]     // select 时的选项
}

// 样品结果列定义
export interface CustomColumnDef {
  key: string            // 列键
  label: string          // 列标题
  unit?: string | null   // 单位
  input_type?: 'text' | 'number' | 'select'  // 输入类型，默认 text
  options?: string[]     // select 时的选项
  width?: number         // 列宽
  auto_calc?: boolean    // 是否自动计算（只读）
  // 自动计算表达式：以 row 为上下文，例如 "row.after - row.before"
  // 为简化使用，仅支持差值；若填 before_key/after_key 则自动算 delta
  before_key?: string    // delta 计算源列 A
  after_key?: string     // delta 计算源列 B
}

// 自定义测试项
export interface CustomTestItem {
  id: string             // 唯一 ID（uuid-like）
  name: string           // 测试项名称
  description?: string   // 描述
  params: CustomParamDef[]
  sample_columns: CustomColumnDef[]
  judge_rule?: string    // 判定规则说明（仅展示）
  created_at: string     // ISO 时间
  updated_at: string     // ISO 时间
}

const STORAGE_KEY = 'pms:custom_test_items'

// ===== CRUD =====

export function listCustomTestItems(): CustomTestItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

export function getCustomTestItem(id: string): CustomTestItem | undefined {
  return listCustomTestItems().find(t => t.id === id)
}

export function saveCustomTestItem(item: CustomTestItem): CustomTestItem {
  const list = listCustomTestItems()
  const now = new Date().toISOString()
  const idx = list.findIndex(t => t.id === item.id)
  if (idx >= 0) {
    list[idx] = { ...item, updated_at: now }
  } else {
    list.push({ ...item, created_at: now, updated_at: now })
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  return list[idx >= 0 ? idx : list.length - 1]
}

export function deleteCustomTestItem(id: string): void {
  const list = listCustomTestItems().filter(t => t.id !== id)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

// 生成唯一 ID
export function genItemId(): string {
  return 'cti_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

// ===== 辅助函数 =====

// 根据参数定义生成空白参数值对象
export function buildEmptyParams(params: CustomParamDef[]): Record<string, any> {
  const obj: Record<string, any> = {}
  params.forEach(p => { obj[p.key] = p.default ?? '' })
  return obj
}

// 根据列定义生成空白样品行
export function buildEmptySample(columns: CustomColumnDef[], code?: string): Record<string, any> {
  const row: Record<string, any> = {}
  columns.forEach(c => {
    if (c.auto_calc) row[c.key] = null
    else row[c.key] = ''
  })
  if (code !== undefined) row.code = code
  return row
}

// 计算 auto_calc 列（当前仅支持 delta: after_key - before_key）
export function recalcSampleRow(row: Record<string, any>, columns: CustomColumnDef[]): Record<string, any> {
  const result = { ...row }
  columns.forEach(c => {
    if (c.auto_calc && c.before_key && c.after_key) {
      const a = Number(row[c.before_key])
      const b = Number(row[c.after_key])
      if (!Number.isNaN(a) && !Number.isNaN(b) && row[c.before_key] !== '' && row[c.after_key] !== '') {
        result[c.key] = Number((b - a).toFixed(6))
      } else {
        result[c.key] = null
      }
    }
  })
  return result
}

// 统计样品结果（若存在 result 列）
export interface SampleStats {
  total: number
  passed: number
  failed: number
  pending: number
  pass_rate: number
  auto_conclusion: 'pass' | 'fail' | 'need_retest'
}

export function calcSampleStats(samples: Record<string, any>[]): SampleStats {
  const total = samples.length
  const failed = samples.filter(s => s.result === 'fail').length
  const passed = samples.filter(s => s.result === 'pass').length
  const pending = total - failed - passed
  const pass_rate = total > 0 ? Math.round((passed / total) * 1000) / 10 : 0
  let auto_conclusion: 'pass' | 'fail' | 'need_retest' = 'need_retest'
  if (total > 0 && pending === 0) {
    auto_conclusion = failed === 0 ? 'pass' : 'fail'
  }
  return { total, passed, failed, pending, pass_rate, auto_conclusion }
}

// 构造空白参数定义（用于「新建测试项」对话框初始行）
export function emptyParamDef(): CustomParamDef {
  return {
    key: '', name: '', unit: '', default: '',
    min: null, max: null, input_type: 'number', options: [],
  }
}

// 构造空白列定义
export function emptyColumnDef(): CustomColumnDef {
  return {
    key: '', label: '', unit: '', input_type: 'text', options: [],
    width: 120, auto_calc: false, before_key: '', after_key: '',
  }
}
