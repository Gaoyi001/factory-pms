import request from '@/utils/request'
import type { LoginParams } from '@/types/user'
import type {
  ExperimentOut, ExperimentAttachmentOut, ExperimentRecordOut,
  ExperimentStatus,
} from '@/types/experiment'

export const authApi = {
  login: (data: LoginParams) => request.post('/auth/login', data),
  logout: () => request.post('/auth/logout'),
  getMe: () => request.get('/auth/me'),
  getMyPermissions: () => request.get('/auth/me/permissions'),
}

// ===== 用户 API =====
export const userApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string }) =>
    request.get('/users/list', { params }),
  simpleList: () => request.get('/users/simple-list'),
  create: (data: any) => request.post('/users/create', data),
  update: (id: number, data: any) => request.put(`/users/${id}`, data),
  remove: (id: number) => request.delete(`/users/${id}`),
  departments: () => request.get('/users/departments'),
}

// ===== 项目 API =====
export const projectApi = {
  types: () => request.get('/projects/types'),
  list: (params: { page?: number; page_size?: number; status?: string; owner_id?: number; keyword?: string }) =>
    request.get('/projects/list', { params }),
  create: (data: any) => request.post('/projects/create', data),
  get: (id: number) => request.get(`/projects/${id}`),
  update: (id: number, data: any) => request.put(`/projects/${id}`, data),
  remove: (id: number) => request.delete(`/projects/${id}`),
  // 任务
  getTasks: (projectId: number, params?: any) => request.get(`/projects/${projectId}/tasks`, { params }),
  createTask: (projectId: number, data: any) => request.post(`/projects/${projectId}/tasks`, data),
  updateTask: (taskId: number, data: any) => request.put(`/tasks/${taskId}`, data),
  deleteTask: (taskId: number) => request.delete(`/tasks/${taskId}`),
  // 需求
  getRequirements: (projectId: number) => request.get(`/projects/${projectId}/requirements`),
  createRequirement: (projectId: number, data: any) => request.post(`/projects/${projectId}/requirements`, data),
  updateRequirement: (reqId: number, data: any) => request.put(`/projects/requirements/${reqId}`, data),
  deleteRequirement: (reqId: number) => request.delete(`/projects/requirements/${reqId}`),
}

// ===== 实验 API =====
export interface ExperimentListParams {
  page?: number; page_size?: number; project_id?: number
  status?: ExperimentStatus; exp_type?: string; keyword?: string
  date_from?: string; date_to?: string
}
export interface RecordListParams {
  page?: number; page_size?: number; batch_no?: string
  sample_code?: string; conclusion?: string; is_abnormal?: boolean
  date_from?: string; date_to?: string
}

export const experimentApi = {
  list: (params: ExperimentListParams) =>
    request.get('/experiments/list', { params }),
  create: (data: Record<string, unknown>) =>
    request.post('/experiments/create', data),
  get: (id: number): Promise<ExperimentOut> =>
    request.get(`/experiments/${id}`).then(r => r.data),
  update: (id: number, data: Record<string, unknown>) =>
    request.put(`/experiments/${id}`, data),
  remove: (id: number) =>
    request.delete(`/experiments/${id}`),
  // 状态流转：start | complete | cancel
  changeStatus: (id: number, action: 'start' | 'complete' | 'cancel') =>
    request.post(`/experiments/${id}/status`, { action }),
  // 实验记录（支持分页与筛选参数）
  getRecords: (expId: number, params?: RecordListParams) =>
    request.get(`/experiments/${expId}/records`, { params }),
  getRecord: (recordId: number): Promise<ExperimentRecordOut> =>
    request.get(`/experiments/records/${recordId}`).then(r => r.data),
  createRecord: (data: Record<string, unknown>) =>
    request.post('/experiments/records', data),
  updateRecord: (id: number, data: Record<string, unknown>) =>
    request.put(`/experiments/records/${id}`, data),
  deleteRecord: (id: number) =>
    request.delete(`/experiments/records/${id}`),
  batchDeleteRecords: (ids: number[]) =>
    request.post('/experiments/records/batch-delete', { ids }),
  // 导出实验记录 Excel
  exportRecords: (expId: number) => {
    return fetch(`/api/v1/experiments/${expId}/records/export`, {
      credentials: 'include',
    }).then(async (res) => {
      if (!res.ok) throw new Error('导出失败')
      const blob = await res.blob()
      const disposition = res.headers.get('content-disposition')
      let filename = `experiment_${expId}_records.xlsx`
      if (disposition) {
        const m = disposition.match(/filename\*=UTF-8''([^;]+)/i)
        if (m) filename = decodeURIComponent(m[1])
      }
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      a.click()
      URL.revokeObjectURL(a.href)
    })
  },
  // 实验附件
  listAttachments: (recordId: number) => request.get(`/experiments/records/${recordId}/attachments`),
  uploadAttachment: (recordId: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post(`/experiments/records/${recordId}/attachments`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  deleteAttachment: (id: number) => request.delete(`/experiments/attachments/${id}`),
  // 下载附件：inline=true 预览，false 下载
  downloadAttachment: async (attachmentId: number, inline: boolean = false) => {
    const url = `/api/v1/experiments/attachments/${attachmentId}/download?inline=${inline ? 'true' : 'false'}`
    const res = await fetch(url, { credentials: 'include' })
    if (!res.ok) throw new Error('下载失败')
    if (inline) {
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, '_blank')
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)
      return
    }
    const blob = await res.blob()
    const disposition = res.headers.get('content-disposition')
    let filename = 'attachment'
    if (disposition) {
      const m = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (m) filename = decodeURIComponent(m[1].replace(/['"]/g, ''))
    }
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
    URL.revokeObjectURL(a.href)
  },
}

// ===== BOM API =====
export const bomApi = {
  // 物料
  listMaterials: (params: any) => request.get('/bom/materials', { params }),
  createMaterial: (data: any) => request.post('/bom/materials', data),
  getMaterial: (id: number) => request.get(`/bom/materials/${id}`),
  updateMaterial: (id: number, data: any) => request.put(`/bom/materials/${id}`, data),
  deleteMaterial: (id: number) => request.delete(`/bom/materials/${id}`),
  batchDeleteMaterials: (ids: number[]) => request.post('/bom/materials/batch-delete', { ids }),
  // BOM
  listBoms: (params: any) => request.get('/bom/headers', { params }),
  createBom: (data: any) => request.post('/bom/headers', data),
  getBom: (id: number) => request.get(`/bom/headers/${id}`),
  updateBom: (id: number, data: any) => request.put(`/bom/headers/${id}`, data),
  deleteBom: (id: number) => request.delete(`/bom/headers/${id}`),
  // BomItem
  getBomItems: (bomId: number) => request.get(`/bom/headers/${bomId}/items`),
  addBomItem: (bomId: number, data: any) => request.post(`/bom/headers/${bomId}/items`, data),
  updateBomItem: (bomId: number, itemId: number, data: any) => request.put(`/bom/headers/${bomId}/items/${itemId}`, data),
  deleteBomItem: (bomId: number, itemId: number) => request.delete(`/bom/headers/${bomId}/items/${itemId}`),
  batchDeleteBomItems: (ids: number[]) => request.post('/bom/items/batch-delete', { ids }),
  // BomChange
  listChanges: (params: any) => request.get('/bom/changes', { params }),
  createChange: (data: any) => request.post('/bom/changes', data),
  getChange: (id: number) => request.get(`/bom/changes/${id}`),
  updateChange: (id: number, data: any) => request.put(`/bom/changes/${id}`, data),
  deleteChange: (id: number) => request.delete(`/bom/changes/${id}`),
}

// ===== 样品试产 API =====
export const sampleApi = {
  listSamples: (params: any) => request.get('/samples/samples', { params }),
  createSample: (data: any) => request.post('/samples/samples', data),
  getSample: (id: number) => request.get(`/samples/samples/${id}`),
  updateSample: (id: number, data: any) => request.put(`/samples/samples/${id}`, data),
  deleteSample: (id: number) => request.delete(`/samples/samples/${id}`),
  listInspections: (sampleId: number) => request.get(`/samples/samples/${sampleId}/inspections`),
  createInspection: (data: any) => request.post('/samples/inspections', data),
  deleteInspection: (id: number) => request.delete(`/samples/inspections/${id}`),
  listTrials: (params: any) => request.get('/samples/trials', { params }),
  createTrial: (data: any) => request.post('/samples/trials', data),
  getTrial: (id: number) => request.get(`/samples/trials/${id}`),
  updateTrial: (id: number, data: any) => request.put(`/samples/trials/${id}`, data),
  deleteTrial: (id: number) => request.delete(`/samples/trials/${id}`),
}

// ===== 文档知识 API =====
export const documentApi = {
  // 文档
  listDocs: (params: any) => request.get('/documents/list', { params }),
  createDoc: (data: any) => request.post('/documents/create', data),
  getDoc: (id: number) => request.get(`/documents/${id}`),
  updateDoc: (id: number, data: any) => request.put(`/documents/${id}`, data),
  deleteDoc: (id: number) => request.delete(`/documents/${id}`),
  uploadVersion: (docId: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post(`/documents/${docId}/upload`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getVersions: (docId: number) => request.get(`/documents/${docId}/versions`),
  // 下载 / 预览
  downloadDoc: async (docId: number, versionId?: number, inline: boolean = false) => {
    const params = new URLSearchParams()
    if (versionId) params.set('version_id', String(versionId))
    if (inline) params.set('inline', 'true')
    const url = `/api/v1/documents/${docId}/download?${params.toString()}`
    const res = await fetch(url, {
      credentials: 'include'
    })
    if (!res.ok) throw new Error('Download failed')
    if (inline) {
      // 预览：在新窗口打开（浏览器支持的格式如 PDF 会直接显示）
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, '_blank')
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)
      return
    }
    // 下载
    const blob = await res.blob()
    const disposition = res.headers.get('content-disposition')
    let filename = 'download'
    if (disposition) {
      const m = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (m) filename = decodeURIComponent(m[1].replace(/['"]/g, ''))
    }
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
    URL.revokeObjectURL(a.href)
  },
  // 知识库（统一返回 Document 列表，含版本信息）
  listKnowledgeDocs: (params: any) => request.get('/documents/knowledge/list', { params }),
  // 研发实验上传文档
  createFromExperiment: (expId: number, title: string, file: File, docType: string = 'test') => {
    const fd = new FormData()
    fd.append('title', title)
    fd.append('doc_type', docType)
    fd.append('file', file)
    return request.post(`/documents/from-experiment/${expId}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}

// ===== 部门 API =====
export const departmentApi = {
  tree: () => request.get('/departments/tree'),
  list: () => request.get('/departments/list'),
  get: (id: number) => request.get(`/departments/${id}`),
  create: (data: any) => request.post('/departments/create', data),
  update: (id: number, data: any) => request.put(`/departments/${id}`, data),
  remove: (id: number) => request.delete(`/departments/${id}`),
}

// ===== 角色 API =====
export const roleApi = {
  list: () => request.get('/roles/list'),
  get: (id: number) => request.get(`/roles/${id}`),
  create: (data: any) => request.post('/roles/create', data),
  update: (id: number, data: any) => request.put(`/roles/${id}`, data),
  remove: (id: number) => request.delete(`/roles/${id}`),
  listPermissions: () => request.get('/roles/permissions/list'),
  createPermission: (data: any) => request.post('/roles/permissions/create', data),
  assignPermissions: (roleId: number, permissionIds: number[]) =>
    request.post(`/roles/${roleId}/permissions`, permissionIds),
}

// ===== 操作日志 API =====
export const operationLogApi = {
  list: (params: any) => request.get('/operation-logs/list', { params }),
  listDownloads: (params: any) => request.get('/operation-logs/download-logs', { params }),
}

// ===== 用户增强 API =====
export const userEnhanceApi = {
  changePassword: (data: { user_id?: number; old_password?: string; new_password: string }) =>
    request.post('/users/change-password', data),
  batchEnable: (userIds: number[]) => request.post('/users/batch-enable', userIds),
  batchDisable: (userIds: number[]) => request.post('/users/batch-disable', userIds),
}

// ===== 库存管理 API =====
export const inventoryApi = {
  // 库存
  list: (params: any) => request.get('/inventory/list', { params }),
  warehouses: () => request.get('/inventory/warehouses'),
  get: (id: number) => request.get(`/inventory/${id}`),
  create: (data: any) => request.post('/inventory/create', data),
  update: (id: number, data: any) => request.put(`/inventory/${id}`, data),
  remove: (id: number) => request.delete(`/inventory/${id}`),
  // 操作
  inbound: (data: any) => request.post('/inventory/inbound', data),
  outbound: (data: any) => request.post('/inventory/outbound', data),
  borrow: (data: any) => request.post('/inventory/borrow', data),
  return: (data: any) => request.post('/inventory/return', data),
  check: (data: any) => request.post('/inventory/check', data),
  transfer: (data: any) => request.post('/inventory/transfer', data),
  // 交易记录
  transactions: (params: any) => request.get('/inventory/transactions', { params }),
  getTransaction: (id: number) => request.get(`/inventory/transactions/${id}`),
  // 审批
  submitApproval: (txId: number, data: any) => request.post(`/inventory/approvals/${txId}/submit`, data),
  handleApproval: (approvalId: number, data: any) => request.put(`/inventory/approvals/${approvalId}/action`, data),
  pendingApprovals: () => request.get('/inventory/approvals/pending'),
  // 预警
  alerts: () => request.get('/inventory/alerts'),
  alertSummary: () => request.get('/inventory/alerts/summary'),
  markAlertRead: (id: number) => request.put(`/inventory/alerts/${id}/read`),
  resolveAlert: (id: number) => request.put(`/inventory/alerts/${id}/resolve`),
  // 统计
  overview: () => request.get('/inventory/stats/overview'),
  byWarehouse: () => request.get('/inventory/stats/by-warehouse'),
  turnover: (days?: number) => request.get('/inventory/stats/turnover', { params: { days: days || 30 } }),
  // 仓库管理
  warehouseList: () => request.get('/inventory/warehouses/list'),
  warehouseCreate: (data: any) => request.post('/inventory/warehouses/create', data),
  warehouseUpdate: (id: number, data: any) => request.put(`/inventory/warehouses/${id}`, data),
  warehouseDelete: (id: number) => request.delete(`/inventory/warehouses/${id}`),
}
