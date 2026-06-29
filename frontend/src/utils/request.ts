// Axios 实例 & 通用请求封装
import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_BASE || '/api/v1'

const formatDate = (date: Date): string => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const cleanData = (data: any): any => {
  if (data === null || data === undefined) return data
  if (data instanceof Date) return formatDate(data)
  if (typeof data !== 'object') return data
  if (Array.isArray(data)) return data.map(cleanData)
  const result: any = {}
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined) continue
    if (value === null) {
      result[key] = null
      continue
    }
    if (value instanceof Date) {
      result[key] = formatDate(value)
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      result[key] = cleanData(value)
    } else {
      result[key] = value
    }
  }
  return result
}

// 401 防抖标志 — 防止多个并发的 401 响应触发多次跳转
let isRedirecting = false

// 错误消息映射，避免重复显示
const showError = (msg: string, isSilent = false) => {
  if (isSilent) return
  ElMessage.error(msg)
}

// 后端字段名 -> 中文名映射，用于把 422 校验错误转成用户可读的提示
const FIELD_NAME_MAP: Record<string, string> = {
  username: '用户名', password: '密码', new_password: '新密码', old_password: '旧密码',
  email: '邮箱', real_name: '姓名', role: '角色', dept_id: '部门', is_active: '状态',
  name: '名称', code: '编码', description: '描述', status: '状态', priority: '优先级',
  progress: '进度', parent_id: '上级', sort_order: '排序',
  title: '标题', content: '内容', category: '分类', summary: '摘要',
  project_id: '项目', owner_id: '负责人', plan_start: '计划开始日期', plan_end: '计划结束日期',
  budget: '预算', material_id: '物料', material_type: '物料类型', unit: '单位',
  spec: '规格', supplier: '供应商', brand: '品牌', quantity: '数量', line_no: '行号',
  loss_rate: '损耗率', level: '层级', version: '版本', product_code: '产品编码',
  bom_id: 'BOM', change_type: '变更类型', reason: '原因',
  experiment_id: '实验', exp_type: '实验类型', designer_id: '设计者', executor_id: '执行者',
  batch_no: '批次号', sample_code: '样品编码', conclusion: '结论', cpk: 'CPK',
  sample_id: '样品', sample_type: '样品类型', inspect_type: '检验类型', result: '结果',
  inspect_no: '检验单号', item_name: '检验项', standard: '标准', actual_value: '实测值',
  trial_no: '试产单号', plan_qty: '计划数量', workshop: '车间', foreman_id: '班组长',
  yield_rate: '良率', pass_qty: '合格数', fail_qty: '不合格数', actual_qty: '实际数量',
  warehouse: '仓库', location: '库位', safety_stock: '安全库存', max_stock: '最大库存',
  inventory_item_id: '库存项', transaction_type: '交易类型', source_warehouse: '源仓库',
  target_warehouse: '目标仓库', borrower_id: '借用人', borrower_name: '借用人姓名',
  expected_return_date: '预计归还日期', approval_required: '需要审批',
  approver_id: '审批人', approver_name: '审批人姓名', approval_level: '审批层级',
  doc_type: '文档类型', tags: '标签', file: '文件', is_published: '是否发布',
  is_key: '是否关键件', is_abnormal: '是否异常', abnormal_desc: '异常描述',
  retention_days: '保留天数', ids: 'ID列表',
}

/** 将后端返回的字段路径（如 "body.username"）转换为可读中文名 */
const translateField = (loc: any[] | string | undefined): string => {
  if (!loc) return '参数'
  const parts = Array.isArray(loc) ? loc : [loc]
  // 跳过 "body"/"query"/"path" 等位置前缀，取实际字段名
  const fieldPart = parts.filter((p) => !['body', 'query', 'path', 'json'].includes(String(p)))
  const last = fieldPart[fieldPart.length - 1]
  if (last && FIELD_NAME_MAP[String(last)]) return FIELD_NAME_MAP[String(last)]
  return fieldPart.length ? fieldPart.join('.') : '参数'
}

/** 把英文 Pydantic 校验消息翻译为中文（覆盖常见模式，未命中则原样返回） */
const translateMsg = (raw: string): string => {
  if (!raw) return raw
  const s = raw.trim()
  const map: [RegExp, string | ((m: RegExpMatchArray) => string)][] = [
    [/^Field required$/i, '为必填项'],
    [/^field required$/i, '为必填项'],
    [/^missing$/i, '为必填项'],
    [/^string should have at least (\d+) characters?$/i, (m) => `至少需要 ${m[1]} 个字符`],
    [/^string should have at most (\d+) characters?$/i, (m) => `不能超过 ${m[1]} 个字符`],
    [/^should have at least (\d+) characters?$/i, (m) => `至少需要 ${m[1]} 个字符`],
    [/^should have at most (\d+) characters?$/i, (m) => `不能超过 ${m[1]} 个字符`],
    [/^value should be a valid integer$/i, '需为整数'],
    [/^value should be a valid number$/i, '需为数字'],
    [/^value should be a valid email$/i, '邮箱格式不正确'],
    [/^value is not a valid email$/i, '邮箱格式不正确'],
    [/^input should be a valid integer$/i, '需为整数'],
    [/^input should be a valid number$/i, '需为数字'],
    [/^input should be a valid email$/i, '邮箱格式不正确'],
    [/^(\w+) should be greater than or equal to (\d+)$/i, (m) => `不能小于 ${m[2]}`],
    [/^(\w+) should be less than or equal to (\d+)$/i, (m) => `不能大于 ${m[2]}`],
    [/^greater than or equal to (\d+)$/i, (m) => `不能小于 ${m[1]}`],
    [/^less than or equal to (\d+)$/i, (m) => `不能大于 ${m[1]}`],
    [/^greater than (\d+)$/i, (m) => `需大于 ${m[1]}`],
    [/^less than (\d+)$/i, (m) => `需小于 ${m[1]}`],
    [/^string does not match pattern/i, '格式不正确'],
    [/^value error,?\s*/i, ''],  // 去掉 "Value error," 前缀（自定义校验消息本身已是中文）
  ]
  for (const [re, rep] of map) {
    if (re.test(s)) {
      return typeof rep === 'function' ? rep(s.match(re)!) : rep
    }
  }
  return s
}

/**
 * 解析 422 校验错误详情，兼容两种格式：
 * 1. 标准 FastAPI 对象数组：[{ loc: ['body','username'], msg: 'Field required' }]
 * 2. 后端自定义字符串数组：['body.username: Field required']
 * 返回最多 3 条中文提示，用分号分隔
 */
const formatValidationError = (detail: any): string => {
  if (!detail) return '参数验证失败'
  // 字符串：可能是单条错误或带字段前缀
  if (typeof detail === 'string') {
    const idx = detail.indexOf(':')
    if (idx > 0) {
      const fieldRaw = detail.slice(0, idx).trim()
      const msgRaw = detail.slice(idx + 1).trim()
      const fieldName = fieldRaw.split('.').filter((p) => !['body', 'query', 'path'].includes(p)).pop() || fieldRaw
      return `${FIELD_NAME_MAP[fieldName] || fieldName}: ${translateMsg(msgRaw)}`
    }
    return translateMsg(detail)
  }
  // 数组
  if (Array.isArray(detail)) {
    const msgs = detail.map((d: any) => {
      // 对象格式（标准 FastAPI）
      if (d && typeof d === 'object' && d.loc) {
        return `${translateField(d.loc)}: ${translateMsg(d.msg || '')}`
      }
      // 字符串格式（后端自定义）
      if (typeof d === 'string') {
        const idx = d.indexOf(':')
        if (idx > 0) {
          const fieldRaw = d.slice(0, idx).trim()
          const msgRaw = d.slice(idx + 1).trim()
          const fieldName = fieldRaw.split('.').filter((p) => !['body', 'query', 'path'].includes(p)).pop() || fieldRaw
          return `${FIELD_NAME_MAP[fieldName] || fieldName}: ${translateMsg(msgRaw)}`
        }
        return translateMsg(d)
      }
      return String(d)
    })
    return msgs.slice(0, 3).join('; ')
  }
  return '参数验证失败'
}

const handle401 = (isLoginRequest = false) => {
  // 登录接口的 401 是"用户名或密码错误"，不重定向
  if (isLoginRequest) return
  if (isRedirecting) return
  isRedirecting = true
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  localStorage.removeItem('permissions')
  localStorage.removeItem('isAdmin')
  router.push('/login').finally(() => {
    // 跳转完成后重置标志（路由 afterEach 钩子完成即重置，500ms 兜底）
    setTimeout(() => { isRedirecting = false }, 500)
  })
}

/** 统一处理 401 未授权：登录接口仅传播错误，其他接口触发跳转 */
const handleUnauthorized = (config: any) => {
  const isLoginRequest = config?.url?.includes('/auth/login')
  if (isLoginRequest) {
    // 登录接口让错误正常传播到调用方处理
    return
  }
  showError('登录已过期，请重新登录', true)
  handle401(false)
}

const request: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  if (config.method === 'post' || config.method === 'put') {
    if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
      config.data = cleanData(config.data)
    }
  }
  return config
})

// 响应拦截：统一错误处理
request.interceptors.response.use(
  (res) => {
    const body = res.data
    // 检查业务错误码
    if (body.code && body.code !== 200) {
      const msg = body.message || body.msg || '请求失败'
      if (body.code === 401) {
        handleUnauthorized(res.config)
      } else {
        showError(msg)
      }
      return Promise.reject(new Error(msg))
    }
    // 成功返回：优先返回 data 字段
    return body.data !== undefined ? body.data : body
  },
  (err: AxiosError) => {
    // 请求取消不显示错误
    if (axios.isCancel(err)) {
      return Promise.reject(err)
    }

    let msg = '网络错误，请检查网络连接'
    const status = err.response?.status

    if (err.response) {
      const data = err.response.data as any

      // 业务错误（后端返回的JSON）
      if (data?.message || data?.msg) {
        msg = data.message || data.msg
        // 401 统一通过 handleUnauthorized 处理
        if (status === 401) {
          handleUnauthorized(err.config)
        } else if (status === 403) {
          msg = '权限不足，无法执行此操作'
          showError(msg)
        } else if (status === 404) {
          msg = '请求的资源不存在'
          showError(msg)
        } else if (status === 422) {
          // 参数验证错误：统一解析为中文提示
          msg = formatValidationError(data.detail) || data.message || '参数验证失败'
          showError(msg)
        } else if (status === 500) {
          msg = '服务器错误，请稍后重试'
          showError(msg)
        } else {
          showError(msg)
        }
      } else if (data?.detail) {
        // FastAPI 的 HTTPException detail（可能是字符串、对象数组或字符串数组）
        if (typeof data.detail === 'string') {
          msg = data.detail
        } else if (Array.isArray(data.detail)) {
          msg = formatValidationError(data.detail)
        }
        showError(msg)
      } else {
        msg = `请求失败 (${status})`
        showError(msg)
      }
    } else if (err.request) {
      // 请求已发出但没有收到响应
      msg = '服务器无响应，请检查网络或稍后重试'
      showError(msg)
    } else {
      // 请求配置出错
      msg = err.message || '请求配置错误'
      showError(msg)
    }

    return Promise.reject(err)
  }
)

export default request
