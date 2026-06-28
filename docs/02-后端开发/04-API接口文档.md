# API 接口文档

## 一、接口规范

### 1.1 基础信息

- **Base URL**: `/api/v1`
- **协议**: HTTPS / HTTP
- **数据格式**: JSON (UTF-8)
- **认证方式**: Bearer Token (JWT)

### 1.2 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 1.3 分页响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 1.4 认证

请求头中携带 JWT Token：

```http
Authorization: Bearer <access_token>
```

---

## 二、认证模块

**前缀**: `/api/v1/auth`

### 2.1 登录

| 项目 | 说明 |
|------|------|
| 方法 | `POST` |
| 路径 | `/login` |
| 认证 | 否 |
| 权限 | - |

**请求体：**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应 data：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**定义位置：** [auth.py:13-23](file:///g:/资料/code/factory-pms/backend/app/api/v1/auth.py#L13-L23)

---

### 2.2 注册

| 项目 | 说明 |
|------|------|
| 方法 | `POST` |
| 路径 | `/register` |
| 认证 | 否 |
| 权限 | - |

**请求体：**

```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "real_name": "string",
  "role": "member",
  "dept_id": 1
}
```

**响应 data：**

```json
{
  "user_id": 1
}
```

**定义位置：** [auth.py:26-44](file:///g:/资料/code/factory-pms/backend/app/api/v1/auth.py#L26-L44)

---

### 2.3 获取当前用户

| 项目 | 说明 |
|------|------|
| 方法 | `GET` |
| 路径 | `/me` |
| 认证 | 是 |
| 权限 | 所有登录用户 |

**响应 data：**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@factory-pms.com",
  "real_name": "系统管理员",
  "role": "admin",
  "dept_id": 1,
  "is_active": true,
  "last_login_at": "2024-01-01T00:00:00",
  "department": { "id": 1, "name": "管理层" }
}
```

**定义位置：** [auth.py:47-60](file:///g:/资料/code/factory-pms/backend/app/api/v1/auth.py#L47-L60)

---

## 三、用户管理模块

**前缀**: `/api/v1/users`

| 接口 | 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|------|
| 用户列表 | GET | `/list` | 分页查询用户列表 | 是 |
| 简易列表 | GET | `/simple-list` | 下拉用用户列表 | 是 |
| 创建用户 | POST | `/create` | 创建新用户 | 是 (admin) |
| 更新用户 | PUT | `/{id}` | 更新用户信息 | 是 (admin) |
| 删除用户 | DELETE | `/{id}` | 删除用户 | 是 (admin) |
| 部门列表 | GET | `/departments` | 获取部门列表 | 是 |

---

## 四、项目管理模块

**前缀**: `/api/v1/projects`

### 4.1 项目类型

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 项目类型列表 | GET | `/types` | 获取所有启用的项目类型 |

**定义位置：** [projects.py:22-24](file:///g:/资料/code/factory-pms/backend/app/api/v1/projects.py#L22-L24)

---

### 4.2 项目 CRUD

| 接口 | 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|------|
| 项目列表 | GET | `/list` | 分页查询项目 | 登录用户 |
| 创建项目 | POST | `/create` | 创建新项目 | 登录用户 |
| 项目详情 | GET | `/{project_id}` | 获取项目详情 | 登录用户 |
| 更新项目 | PUT | `/{project_id}` | 更新项目信息 | admin/manager |
| 删除项目 | DELETE | `/{project_id}` | 取消项目（软删除） | admin |

**项目列表查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| page_size | int | 每页大小，默认 20 |
| status | string | 项目状态筛选 |
| owner_id | int | 负责人筛选 |
| keyword | string | 名称/编号模糊搜索 |

**定义位置：** [projects.py:28-91](file:///g:/资料/code/factory-pms/backend/app/api/v1/projects.py#L28-L91)

---

### 4.3 任务管理

| 接口 | 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|------|
| 任务列表 | GET | `/{project_id}/tasks` | 获取项目任务列表 | 登录用户 |
| 创建任务 | POST | `/{project_id}/tasks` | 创建新任务 | 登录用户 |
| 更新任务 | PUT | `/tasks/{task_id}` | 更新任务 | 登录用户 |
| 删除任务 | DELETE | `/tasks/{task_id}` | 删除任务 | admin/manager |

**定义位置：** [projects.py:95-139](file:///g:/资料/code/factory-pms/backend/app/api/v1/projects.py#L95-L139)

---

### 4.4 需求管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 需求列表 | GET | `/{project_id}/requirements` | 获取项目需求列表 |
| 创建需求 | POST | `/{project_id}/requirements` | 创建新需求 |

**定义位置：** [projects.py:143-159](file:///g:/资料/code/factory-pms/backend/app/api/v1/projects.py#L143-L159)

---

## 五、实验管理模块

**前缀**: `/api/v1/experiments`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 实验列表 | GET | `/list` | 分页查询实验 |
| 创建实验 | POST | `/create` | 创建新实验 |
| 实验详情 | GET | `/{id}` | 获取实验详情 |
| 更新实验 | PUT | `/{id}` | 更新实验信息 |
| 记录列表 | GET | `/{exp_id}/records` | 获取实验记录列表 |
| 创建记录 | POST | `/records` | 创建实验记录 |

---

## 六、BOM 管理模块

**前缀**: `/api/v1/bom`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 物料列表 | GET | `/materials` | 分页查询物料 |
| 创建物料 | POST | `/materials` | 创建新物料 |
| 物料详情 | GET | `/materials/{id}` | 获取物料详情 |
| BOM 列表 | GET | `/headers` | 分页查询 BOM |
| 创建 BOM | POST | `/headers` | 创建新 BOM |
| BOM 详情 | GET | `/headers/{id}` | 获取 BOM 详情 |
| 更新 BOM | PUT | `/headers/{id}` | 更新 BOM 信息 |
| 创建变更 | POST | `/changes` | 创建 BOM 变更 |

---

## 七、样品试产模块

**前缀**: `/api/v1/samples`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 样品列表 | GET | `/samples` | 分页查询样品 |
| 创建样品 | POST | `/samples` | 创建新样品 |
| 样品详情 | GET | `/samples/{id}` | 获取样品详情 |
| 更新样品 | PUT | `/samples/{id}` | 更新样品信息 |
| 检验列表 | GET | `/samples/{sample_id}/inspections` | 获取样品检验记录 |
| 创建检验 | POST | `/inspections` | 创建检验记录 |
| 试产列表 | GET | `/trials` | 分页查询试产工单 |
| 创建试产 | POST | `/trials` | 创建试产工单 |

---

## 八、文档知识模块

**前缀**: `/api/v1/documents`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 文档列表 | GET | `/list` | 分页查询文档 |
| 创建文档 | POST | `/create` | 创建新文档 |
| 文档详情 | GET | `/{id}` | 获取文档详情 |
| 更新文档 | PUT | `/{id}` | 更新文档信息 |
| 上传版本 | POST | `/{id}/upload` | 上传文档新版本 |
| 知识列表 | GET | `/knowledge/list` | 获取知识文章列表 |
| 创建文章 | POST | `/knowledge` | 创建知识文章 |
| 文章详情 | GET | `/knowledge/{id}` | 获取文章详情 |

---

## 九、API 文档访问

启动后端服务后，可通过以下地址访问交互式 API 文档：

| 文档类型 | 地址 |
|---------|------|
| Swagger UI | `http://localhost:8000/api/v1/docs` |
| ReDoc | `http://localhost:8000/api/v1/redoc` |
| OpenAPI JSON | `http://localhost:8000/api/v1/openapi.json` |
