export interface ProjectOut {
  id: number
  code: string
  name: string
  description?: string
  status: string
  priority: number
  project_type_id?: number
  owner_id: number
  created_by: number
  plan_start?: string
  plan_end?: string
  progress: number
  budget?: string
  created_at: string
  updated_at: string
}

export interface TaskOut {
  id: number
  project_id: number
  parent_id?: number
  title: string
  description?: string
  status: string
  priority: number
  assignee_id?: number
  plan_hours: number
  actual_hours: number
  due_date?: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface RequirementOut {
  id: number
  project_id: number
  code: string
  title: string
  description?: string
  source: string
  priority: string
  status: string
  version: number
  created_at: string
}
