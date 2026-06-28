export interface MaterialOut {
  id: number
  code: string
  name: string
  spec?: string
  material_type: string
  unit: string
  category?: string
  supplier?: string
  brand?: string
  status: string
  created_at: string
  updated_at: string
}

export interface BomItemOut {
  id: number
  bom_id: number
  material_id: number
  line_no: number
  quantity: string
  unit?: string
  loss_rate: string
  level: number
  parent_item_id?: number
  remark?: string
  is_key: boolean
  material?: MaterialOut
}

export interface BomHeaderOut {
  id: number
  code: string
  project_id?: number
  name: string
  description?: string
  version: string
  status: string
  product_code?: string
  remark?: string
  created_by?: number
  items: BomItemOut[]
  created_at: string
  updated_at: string
}
