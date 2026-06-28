export interface DocumentOut {
  id: number
  code: string
  title: string
  doc_type: string
  category_id?: number
  project_id?: number
  current_version: string
  status: string
  tags?: string[]
  summary?: string
  source_module?: string   // document=新建文档, experiment=研发实验
  created_by?: number
  created_at: string
  updated_at: string
  version_count?: number
  latest_version?: {
    version: string
    file_name: string
    file_size: number
    mime_type?: string
    uploaded_at?: string
  }
}

// 知识库条目（即含文件的文档，含版本信息）
export type KnowledgeDocOut = DocumentOut

export interface KnowledgeArticleOut {
  id: number
  title: string
  content?: string
  category?: string
  tags?: string[]
  is_published: boolean
  view_count: number
  author_id?: number
  created_at: string
  updated_at: string
}
