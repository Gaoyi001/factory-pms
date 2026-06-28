export interface UserOut {
  id: number
  username: string
  email: string
  real_name?: string
  role: string
  dept_id?: number
  is_active: boolean
  last_login_at?: string
  department?: { id: number; name: string; parent_id?: number }
}

export interface LoginParams {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
