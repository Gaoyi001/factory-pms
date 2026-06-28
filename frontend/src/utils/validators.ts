/**
 * 集中式表单校验规则（配合 Element Plus 的 FormRules 使用）
 * 统一中文异常提示，覆盖项目所有模块的录入校验场景
 */
import type { FormItemRule } from 'element-plus'

// ===== 基础校验器工厂 =====

/** 必填校验 */
export const required = (msg = '此项为必填项'): FormItemRule => ({
  required: true,
  message: msg,
  trigger: 'blur',
})

/** 字符串长度区间校验 */
export const length = (min: number, max: number, msg?: string): FormItemRule => ({
  min,
  max,
  message: msg || `长度需在 ${min}-${max} 个字符之间`,
  trigger: 'blur',
})

/** 最大长度校验 */
export const maxLen = (max: number, msg?: string): FormItemRule => ({
  max,
  message: msg || `不能超过 ${max} 个字符`,
  trigger: 'blur',
})

/** 邮箱格式校验 */
export const email = (msg = '请输入正确的邮箱地址'): FormItemRule => ({
  pattern: /^[\w.+-]+@[\w-]+\.[\w.-]+$/,
  message: msg,
  trigger: 'blur',
})

/** 手机号校验 */
export const phone = (msg = '请输入正确的手机号'): FormItemRule => ({
  pattern: /^1[3-9]\d{9}$/,
  message: msg,
  trigger: 'blur',
})

/** 数字区间校验（用于 number 类型字段） */
export const numberRange = (min: number, max: number, msg?: string): FormItemRule => ({
  validator: (_rule, value, callback) => {
    if (value === null || value === undefined || value === '') return callback()
    const num = Number(value)
    if (Number.isNaN(num)) return callback(new Error('请输入有效数字'))
    if (num < min || num > max) return callback(new Error(msg || `数值需在 ${min}-${max} 之间`))
    callback()
  },
  trigger: 'blur',
})

/** 整数校验 */
export const integer = (msg = '请输入整数'): FormItemRule => ({
  validator: (_rule, value, callback) => {
    if (value === null || value === undefined || value === '') return callback()
    if (!Number.isInteger(Number(value))) return callback(new Error(msg))
    callback()
  },
  trigger: 'blur',
})

/** 正则模式校验 */
export const pattern = (regexp: RegExp, msg: string): FormItemRule => ({
  pattern: regexp,
  message: msg,
  trigger: 'blur',
})

/** 自定义校验函数 */
export const custom = (
  fn: (value: any) => boolean | string,
  trigger: 'blur' | 'change' = 'blur'
): FormItemRule => ({
  validator: (_rule, value, callback) => {
    const result = fn(value)
    if (result === true) return callback()
    callback(new Error(typeof result === 'string' ? result : '校验未通过'))
  },
  trigger,
})

// ===== 预置常用字段规则集 =====

/** 用户名：3-64 字符，字母/数字/下划线 */
export const usernameRules: FormItemRule[] = [
  required('请输入用户名'),
  length(3, 64, '用户名长度为 3-64 个字符'),
  pattern(/^[A-Za-z0-9_]+$/, '用户名仅支持字母、数字和下划线'),
]

/** 密码：至少 6 字符 */
export const passwordRules: FormItemRule[] = [
  required('请输入密码'),
  { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
]

/** 邮箱 */
export const emailRules: FormItemRule[] = [
  required('请输入邮箱'),
  email(),
]

/** 真实姓名：2-50 字符 */
export const realNameRules: FormItemRule[] = [
  required('请输入姓名'),
  length(2, 50, '姓名长度为 2-50 个字符'),
]

/** 部门名称：2-100 字符 */
export const deptNameRules: FormItemRule[] = [
  required('请输入部门名称'),
  length(2, 100, '部门名称长度为 2-100 个字符'),
]

/** 角色编码：2-32 字符 */
export const roleCodeRules: FormItemRule[] = [
  required('请输入角色编码'),
  length(2, 32, '角色编码长度为 2-32 个字符'),
  pattern(/^[A-Za-z0-9_]+$/, '角色编码仅支持字母、数字和下划线'),
]

/** 角色名称：2-100 字符 */
export const roleNameRules: FormItemRule[] = [
  required('请输入角色名称'),
  length(2, 100, '角色名称长度为 2-100 个字符'),
]

/** 通用名称：1-200 字符 */
export const nameRules: FormItemRule[] = [
  required('请输入名称'),
  maxLen(200, '名称不能超过 200 个字符'),
]

/** 项目名称：1-200 字符（部分页面要求 2-50） */
export const projectNameRules: FormItemRule[] = [
  required('请输入项目名称'),
  maxLen(200, '项目名称不能超过 200 个字符'),
]

/** 优先级：1-5 */
export const priorityRules: FormItemRule[] = [
  required('请设置优先级'),
  numberRange(1, 5, '优先级需在 1-5 之间'),
]

/** 进度：0-100 */
export const progressRules: FormItemRule[] = [
  numberRange(0, 100, '进度需在 0-100 之间'),
]

/** 物料编码：1-64 字符 */
export const materialCodeRules: FormItemRule[] = [
  required('请输入物料编码'),
  maxLen(64, '物料编码不能超过 64 个字符'),
]

/** 物料名称：1-200 字符 */
export const materialNameRules: FormItemRule[] = [
  required('请输入物料名称'),
  maxLen(200, '物料名称不能超过 200 个字符'),
]

/** 数量：正整数 */
export const quantityRules: FormItemRule[] = [
  required('请输入数量'),
  integer('数量必须为整数'),
  numberRange(1, 999999, '数量需大于 0'),
]

/** 日期范围校验：开始日期不晚于结束日期 */
export const dateRangeRules = (getField: () => [string | null, string | null]): FormItemRule => ({
  validator: (_rule, _value, callback) => {
    const [start, end] = getField()
    if (start && end && new Date(start) > new Date(end)) {
      return callback(new Error('开始日期不能晚于结束日期'))
    }
    callback()
  },
  trigger: 'change',
})
