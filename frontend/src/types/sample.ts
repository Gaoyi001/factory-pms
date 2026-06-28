export interface SampleOut {
  id: number
  project_id: number
  sample_no: string
  name: string
  description?: string
  version: string
  status: string
  sample_type: string
  quantity: number
  test_result?: string
  plan_finish?: string
  actual_finish?: string
  remark?: string
  created_at: string
  updated_at: string
}

export interface TrialProductionOut {
  id: number
  project_id: number
  trial_no: string
  name: string
  bom_id?: number
  sample_id?: number
  status: string
  plan_qty: number
  actual_qty: number
  pass_qty: number
  fail_qty: number
  yield_rate?: number
  plan_start?: string
  plan_end?: string
  workshop?: string
  line_no?: string
  foreman_id?: number
  process_params?: any
  issue_desc?: string
  conclusion?: string
  remark?: string
  created_by?: number
  created_at: string
  updated_at: string
}
