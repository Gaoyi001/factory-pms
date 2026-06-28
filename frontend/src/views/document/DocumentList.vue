<template>
  <div>
    <el-tabs v-model="activeTab">
      <!-- 新建文档 Tab -->
      <el-tab-pane label="文档管理" name="documents">
        <div class="table-toolbar">
          <div class="left">
            <el-button type="primary" @click="showDocForm()">
              <el-icon><Plus /></el-icon> 新建文档
            </el-button>
            <el-select v-model="docFilter.doc_type" placeholder="文档类型" clearable style="width:140px" @change="onDocFilterChange">
              <el-option v-for="t in docTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <el-select v-model="docFilter.status" placeholder="文档状态" clearable style="width:140px" @change="onDocFilterChange">
              <el-option v-for="s in docStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </div>
          <div class="right">
            <el-input v-model="docFilter.keyword" placeholder="搜索编号/标题" clearable style="width:220px" @keyup.enter="loadDocs">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="loadDocs">查询</el-button>
          </div>
        </div>

        <el-table :data="documents.items" v-loading="docLoading" stripe size="small" empty-text="暂无文档">
          <el-table-column prop="code" label="文档编号" width="150" />
          <el-table-column prop="title" label="文档标题" min-width="200" />
          <el-table-column prop="doc_type" label="类型" width="110">
            <template #default="{ row }">
              <el-tag size="small">{{ docTypeLabel(row.doc_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="docStatusTag(row.status)" size="small">{{ docStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="current_version" label="当前版本" width="100" />
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="showUploadDialog(row)">上传</el-button>
              <el-button link @click="showVersions(row)">版本</el-button>
              <el-button link type="success" @click="handleDownload(row)">下载</el-button>
              <el-button link @click="showDocForm(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDeleteDoc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-model:current-page="docPagination.page" v-model:page-size="docPagination.page_size"
          :total="documents.total" layout="total, sizes, prev, pager, next" @change="loadDocs"
          style="margin-top:16px;justify-content:flex-end" />
      </el-tab-pane>

      <!-- 知识库 Tab：统一展示所有含文件的文档 -->
      <el-tab-pane label="知识库" name="knowledge">
        <div class="table-toolbar">
          <div class="left">
            <el-select v-model="kbFilter.doc_type" placeholder="文档类型" clearable style="width:140px" @change="onKbFilterChange">
              <el-option v-for="t in docTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <el-select v-model="kbFilter.source_module" placeholder="来源" clearable style="width:140px" @change="onKbFilterChange">
              <el-option label="新建文档" value="document" />
              <el-option label="研发实验" value="experiment" />
            </el-select>
            <el-date-picker v-model="kbFilter.date_range" type="daterange" range-separator="至"
              start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD"
              @change="onKbFilterChange" style="width:260px" />
          </div>
          <div class="right">
            <el-input v-model="kbFilter.keyword" placeholder="搜索编号/标题" clearable style="width:220px" @keyup.enter="loadKnowledgeDocs">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="loadKnowledgeDocs">查询</el-button>
          </div>
        </div>

        <el-table :data="kbDocs.items" v-loading="kbLoading" stripe size="small" empty-text="暂无文档">
          <el-table-column prop="code" label="文档编号" width="150" />
          <el-table-column prop="title" label="文档标题" min-width="200" />
          <el-table-column prop="doc_type" label="类型" width="110">
            <template #default="{ row }">
              <el-tag size="small">{{ docTypeLabel(row.doc_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="来源" width="100">
            <template #default="{ row }">
              <el-tag :type="row.source_module === 'experiment' ? 'warning' : 'info'" size="small">
                {{ row.source_module === 'experiment' ? '研发实验' : '新建文档' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="文件" min-width="180">
            <template #default="{ row }">
              <span v-if="row.latest_version">
                {{ row.latest_version.file_name }}
                <el-tag size="small" type="info">{{ formatFileSize(row.latest_version.file_size) }}</el-tag>
              </span>
              <span v-else class="text-muted">暂无文件</span>
            </template>
          </el-table-column>
          <el-table-column label="版本数" width="80" align="center">
            <template #default="{ row }">{{ row.version_count || 0 }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="handlePreview(row)">预览</el-button>
              <el-button link type="success" @click="handleDownload(row)">下载</el-button>
              <el-button link type="danger" @click="handleDeleteDoc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination v-model:current-page="kbPagination.page" v-model:page-size="kbPagination.page_size"
          :total="kbDocs.total" layout="total, sizes, prev, pager, next" @change="loadKnowledgeDocs"
          style="margin-top:16px;justify-content:flex-end" />
      </el-tab-pane>
    </el-tabs>

    <!-- 新建/编辑文档对话框 -->
    <el-dialog v-model="docFormVisible" :title="docFormMode === 'create' ? '新建文档' : '编辑文档'" width="600px">
      <el-form ref="docFormRef" :model="docForm" :rules="docFormRules" label-width="90px">
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="docForm.title" />
        </el-form-item>
        <el-form-item label="文档类型">
          <el-select v-model="docForm.doc_type" style="width:100%">
            <el-option v-for="t in docTypeOpts" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="docForm.project_id" placeholder="请选择" clearable style="width:100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="docForm.status" style="width:100%">
            <el-option v-for="s in docStatusOpts" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="docForm.summary" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="docForm.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="docFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="docSubmitting" @click="handleSubmitDoc">确定</el-button>
      </template>
    </el-dialog>

    <!-- 上传文档版本对话框 -->
    <el-dialog v-model="uploadVisible" title="上传文档版本" width="500px">
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、Word、Excel 等格式</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 版本列表弹窗 -->
    <el-dialog v-model="versionVisible" :title="`版本历史 - ${versionDocTitle}`" width="700px">
      <el-table :data="versions" v-loading="versionLoading" size="small" empty-text="暂无版本">
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="上传时间" width="160">
          <template #default="{ row }">{{ row.uploaded_at?.slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row: ver }">
            <el-button link type="primary" @click="handlePreviewVersion(ver)">预览</el-button>
            <el-button link type="success" @click="handleDownloadVersion(ver)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="versionVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, UploadFilled } from '@element-plus/icons-vue'
import { documentApi, projectApi } from '@/api'
import type { DocumentOut } from '@/types/document'

const activeTab = ref('documents')

// —— 新建文档 Tab ——
const docLoading = ref(false)
const docSubmitting = ref(false)
const docFormVisible = ref(false)
const docFormMode = ref<'create' | 'edit'>('create')
const docFormRef = ref<FormInstance>()
const docFormRules: FormRules = {
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
}
const documents = reactive<{ items: DocumentOut[]; total: number }>({ items: [], total: 0 })
const docPagination = reactive({ page: 1, page_size: 20 })
const docFilter = reactive({ doc_type: '', status: '', keyword: '' })
const projectOptions = ref<{ id: number; name: string }[]>([])
const uploadVisible = ref(false)
const uploading = ref(false)
const uploadFile = ref<File | null>(null)
const currentDocId = ref(0)

// —— 知识库 Tab ——
const kbLoading = ref(false)
const kbDocs = reactive<{ items: any[]; total: number }>({ items: [], total: 0 })
const kbPagination = reactive({ page: 1, page_size: 20 })
const kbFilter = reactive({
  doc_type: '',
  source_module: '',
  keyword: '',
  date_range: null as [string, string] | null,
})

// —— 版本弹窗 ——
const versionVisible = ref(false)
const versionLoading = ref(false)
const versionDocTitle = ref('')
const versionDocId = ref(0)
const versions = ref<any[]>([])

// —— 选项 ——
const docTypeOpts = [
  { label: '设计文档', value: 'design' },
  { label: '测试文档', value: 'test' },
  { label: '工艺文档', value: 'process' },
  { label: '质量文档', value: 'quality' },
  { label: '标准规范', value: 'standard' },
  { label: '其他', value: 'other' },
]
const docStatusOpts = [
  { label: '草稿', value: 'draft' },
  { label: '审核中', value: 'reviewing' },
  { label: '已发布', value: 'released' },
  { label: '已作废', value: 'obsolete' },
]

const docTypeLabel = (t: string) => {
  const found = docTypeOpts.find(o => o.value === t)
  return found ? found.label : t
}
const docStatusTag = (s: string) => ({ draft: 'info', reviewing: 'warning', released: 'success', obsolete: 'danger' }[s] || 'info') as any
const docStatusLabel = (s: string) => {
  const found = docStatusOpts.find(o => o.value === s)
  return found ? found.label : s
}

// —— 新建文档表单 ——
const docForm = reactive({
  id: 0, title: '', doc_type: 'design', project_id: null as number | null,
  status: 'draft', summary: '', tags: '',
})

const loadDocs = async () => {
  docLoading.value = true
  try {
    const res = await documentApi.listDocs({ ...docPagination, doc_type: docFilter.doc_type || undefined, status: docFilter.status || undefined, keyword: docFilter.keyword || undefined })
    documents.items = res.items || []
    documents.total = res.total || 0
  } finally { docLoading.value = false }
}

const onDocFilterChange = () => {
  docPagination.page = 1
  loadDocs()
}

const loadKnowledgeDocs = async () => {
  kbLoading.value = true
  try {
    const params: any = {
      ...kbPagination,
      doc_type: kbFilter.doc_type || undefined,
      source_module: kbFilter.source_module || undefined,
      keyword: kbFilter.keyword || undefined,
    }
    if (kbFilter.date_range) {
      params.created_from = kbFilter.date_range[0]
      params.created_to = kbFilter.date_range[1]
    }
    const res = await documentApi.listKnowledgeDocs(params)
    kbDocs.items = res.items || []
    kbDocs.total = res.total || 0
  } finally { kbLoading.value = false }
}

const onKbFilterChange = () => {
  kbPagination.page = 1
  loadKnowledgeDocs()
}

const loadProjects = async () => {
  try {
    const res = await projectApi.list({ page: 1, page_size: 100 })
    projectOptions.value = (res.items || []).map((p: any) => ({ id: p.id, name: p.name }))
  } catch {}
}

const showDocForm = async (row?: DocumentOut) => {
  if (!projectOptions.value.length) await loadProjects()
  if (row) {
    docFormMode.value = 'edit'
    Object.assign(docForm, { id: row.id, title: row.title, doc_type: row.doc_type, project_id: row.project_id, status: row.status, summary: row.summary, tags: row.tags })
  } else {
    docFormMode.value = 'create'
    Object.assign(docForm, { id: 0, title: '', doc_type: 'design', project_id: null, status: 'draft', summary: '', tags: '' })
  }
  docFormVisible.value = true
}

const handleSubmitDoc = async () => {
  if (!docFormRef.value) return
  try { await docFormRef.value.validate() } catch { return }
  docSubmitting.value = true
  try {
    const payload: any = { title: docForm.title, doc_type: docForm.doc_type, project_id: docForm.project_id || undefined, status: docForm.status, summary: docForm.summary, tags: docForm.tags }
    if (docFormMode.value === 'create') {
      await documentApi.createDoc(payload)
      ElMessage.success('创建成功')
    } else {
      await documentApi.updateDoc(docForm.id, payload)
      ElMessage.success('更新成功')
    }
    docFormVisible.value = false
    loadDocs()
  } finally { docSubmitting.value = false }
}

const showUploadDialog = (row: DocumentOut) => {
  currentDocId.value = row.id
  uploadFile.value = null
  uploadVisible.value = true
}

const handleFileChange = (file: any) => {
  uploadFile.value = file.raw
}

const handleUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  uploading.value = true
  try {
    await documentApi.uploadVersion(currentDocId.value, uploadFile.value)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    loadDocs()
  } finally { uploading.value = false }
}

const showVersions = async (row: DocumentOut) => {
  versionDocId.value = row.id
  versionDocTitle.value = row.title
  versionVisible.value = true
  versionLoading.value = true
  try {
    const res: any = await documentApi.getVersions(row.id)
    versions.value = res.versions || []
  } finally {
    versionLoading.value = false
  }
}

const handleDownload = async (row: DocumentOut) => {
  try {
    ElMessage.info('正在下载...')
    await documentApi.downloadDoc(row.id)
  } catch {
    ElMessage.error('下载失败')
  }
}

const handlePreview = async (row: DocumentOut) => {
  try {
    await documentApi.downloadDoc(row.id, undefined, true)
  } catch {
    ElMessage.error('预览失败')
  }
}

const handleDownloadVersion = async (ver: any) => {
  try {
    ElMessage.info('正在下载...')
    await documentApi.downloadDoc(versionDocId.value, ver.id)
  } catch {
    ElMessage.error('下载失败')
  }
}

const handlePreviewVersion = async (ver: any) => {
  try {
    await documentApi.downloadDoc(versionDocId.value, ver.id, true)
  } catch {
    ElMessage.error('预览失败')
  }
}

const handleDeleteDoc = async (row: DocumentOut) => {
  await ElMessageBox.confirm(`确定要删除文档 "${row.title}" 吗？此操作不可恢复！`, '警告', { type: 'warning' })
  await documentApi.deleteDoc(row.id)
  ElMessage.success('已删除')
  loadDocs()
  loadKnowledgeDocs()
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

onMounted(() => {
  loadDocs()
  loadKnowledgeDocs()
})
</script>
