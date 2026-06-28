/** 项目状态映射 */
export const PROJECT_STATUS = {
  draft: { tag: 'info' as const, label: '草稿' },
  active: { tag: 'success' as const, label: '进行中' },
  on_hold: { tag: 'warning' as const, label: '暂停' },
  completed: { tag: '' as const, label: '已完成' },
  cancelled: { tag: 'danger' as const, label: '已取消' },
} as const

/** 项目优先级映射 */
export const PROJECT_PRIORITY = {
  urgent: { tag: 'danger' as const, label: '紧急' },
  high: { tag: 'warning' as const, label: '高' },
  medium: { tag: 'primary' as const, label: '中' },
  low: { tag: 'info' as const, label: '低' },
} as const

/** 实验状态映射 */
export const EXPERIMENT_STATUS = {
  draft: { tag: 'info' as const, label: '草稿' },
  active: { tag: 'primary' as const, label: '进行中' },
  completed: { tag: 'success' as const, label: '已完成' },
  cancelled: { tag: 'danger' as const, label: '已取消' },
} as const

/** BOM状态映射 */
export const BOM_STATUS = {
  draft: { tag: 'info' as const, label: '草稿' },
  active: { tag: 'success' as const, label: '生效中' },
  obsolete: { tag: 'danger' as const, label: '已废弃' },
} as const

/** 样品状态映射 */
export const SAMPLE_STATUS = {
  pending: { tag: 'info' as const, label: '待处理' },
  producing: { tag: 'warning' as const, label: '生产中' },
  testing: { tag: 'primary' as const, label: '检测中' },
  passed: { tag: 'success' as const, label: '通过' },
  failed: { tag: 'danger' as const, label: '未通过' },
} as const

/** 库存状态映射 */
export const INVENTORY_STATUS = {
  normal: { tag: 'success' as const, label: '正常' },
  low_stock: { tag: 'warning' as const, label: '库存不足' },
  out_of_stock: { tag: 'danger' as const, label: '缺货' },
  expired: { tag: 'danger' as const, label: '已过期' },
} as const

/** 通用状态映射工具 */
export function getStatusTag<T extends Record<string, { tag: string; label: string }>>(
  map: T, status: string
): string {
  const entry = (map as any)[status]
  return entry?.tag ?? 'info'
}

export function getStatusLabel<T extends Record<string, { tag: string; label: string }>>(
  map: T, status: string
): string {
  const entry = (map as any)[status]
  return entry?.label ?? status
}
