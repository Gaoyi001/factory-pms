# Factory R&D PMS — Code Wiki

> 工厂研发项目管理系统（Factory R&D PMS）完整代码百科文档
> 覆盖项目整体架构、主要模块职责、关键类与函数说明、依赖关系以及项目运行方式

---

## 目录

- [1. 项目概览](#1-项目概览)
  - [1.1 项目简介](#11-项目简介)
  - [1.2 技术栈](#12-技术栈)
  - [1.3 整体架构](#13-整体架构)
- [2. 目录结构](#2-目录结构)
- [3. 后端架构](#3-后端架构)
  - [3.1 后端总览](#31-后端总览)
  - [3.2 核心模块 core](#32-核心模块-core)
  - [3.3 数据模型 models](#33-数据模型-models)
  - [3.4 Schema 层 schemas](#34-schema-层-schemas)
  - [3.5 API 路由层 api](#35-api-路由层-api)
  - [3.6 异常处理与中间件](#36-异常处理与中间件)
- [4. 前端架构](#4-前端架构)
  - [4.1 前端总览](#41-前端总览)
  - [4.2 入口与路由](#42-入口与路由)
  - [4.3 状态管理 stores](#43-状态管理-stores)
  - [4.4 请求层 utils/request](#44-请求层-utilsrequest)
  - [4.5 API 聚合层 api/index](#45-api-聚合层-apiindex)
  - [4.6 视图模块 views](#46-视图模块-views)
  - [4.7 类型定义与常量](#47-类型定义与常量)
- [5. 关键类与函数说明](#5-关键类与函数说明)
- [6. 依赖关系](#6-依赖关系)
  - [6.1 后端依赖](#61-后端依赖)
  - [6.2 前端依赖](#62-前端依赖)
  - [6.3 模块间依赖](#63-模块间依赖)
- [7. 权限体系](#7-权限体系)
- [8. 项目运行方式](#8-项目运行方式)
  - [8.1 本地开发环境](#81-本地开发环境)
  - [8.2 Docker 部署](#82-docker-部署)
  - [8.3 局域网与内网穿透](#83-局域网与内网穿透)
- [9. 工程约定与注意事项](#9-工程约定与注意事项)

---

## 1. 项目概览

### 1.1 项目简介

Factory R&D PMS 是一套面向工厂研发部门的**研发项目管理系统**，覆盖从项目立项、研发实验、BOM 管理、样品试产、文档知识到研发库存的全流程。系统采用前后端分离架构，内置基于 RBAC 的细粒度权限控制、操作日志审计、数据隔离与库存审批工作流。

**核心业务域：**

| 域 | 说明 |
|----|------|
| 项目管理 | 项目立项、任务、需求、进度跟踪 |
| 研发实验 | 实验设计、记录、SPC 指标（Cpk）、实验文档归档 |
| BOM 管理 | 物料主数据、BOM 头/明细、ECN 变更工作流 |
| 样品试产 | 样品、检测、试产记录、良率统计 |
| 文档知识 | 文档版本管理、文件上传/下载/预览、知识库聚合 |
| 库存管理 | 仓库、出入库/领用/归还/盘点/调拨、审批、预警、统计 |
| 系统管理 | 用户、部门（树）、角色、权限、操作日志 |

### 1.2 技术栈

**后端：**

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言/框架 | Python / FastAPI | 3.11+ / 0.110 |
| ORM | SQLAlchemy | 2.0.25 |
| 数据校验 | Pydantic + pydantic-settings | 2.5.3 / 2.1.0 |
| 认证 | PyJWT + bcrypt | 2.9.0 / 4.3.0 |
| 数据库 | SQLite（开发）/ MySQL（生产） | - / 8.0 |
| 可选组件 | Redis、MinIO（对象存储） | 5.0 / 7.2 |
| 文件处理 | python-multipart、xhtml2pdf、polars | - |
| 测试 | pytest + httpx | 9+ |

**前端：**

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3 + TypeScript + Vite | 3.4 / 5.4 / 5.2 |
| 路由/状态 | Vue Router + Pinia | 4.3 / 2.1 |
| UI | Element Plus + icons | 2.7 / 2.3 |
| HTTP | axios | 1.7 |
| 富文本 | @vueup/vue-quill | 1.3 |
| 图表 | echarts | 5.5 |
| 日期 | dayjs | 1.11 |

**部署：**

| 类别 | 技术 |
|------|------|
| 容器化 | Docker + docker-compose |
| 反向代理 | Nginx |

### 1.3 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                         浏览器 (Vue 3 SPA)                      │
│  Vue Router ─ Pinia(auth) ─ axios(请求拦截/401处理) ─ Element Plus │
└───────────────────────────────┬──────────────────────────────┘
                                │ /api/v1/*  (Vite proxy 或 Nginx 代理)
┌───────────────────────────────▼──────────────────────────────┐
│                      FastAPI 后端 (:8000)                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 中间件层: CORS → OperationLogMiddleware → 请求日志        │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ 异常处理: RequestValidationError / HTTPException /        │ │
│  │           ValidationError / SQLAlchemyError / Exception   │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ API 路由 (api/v1): auth users departments roles           │ │
│  │   operation-logs projects experiments bom samples         │ │
│  │   documents inventory                                     │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ 安全层 (core/security): JWT 签发/校验, require_role,      │ │
│  │   require_permission(resource, action) [RBAC]             │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ Schema (Pydantic) ─ Models (SQLAlchemy ORM)               │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────┬─────────────────┬─────────────────┬────────────────┘
           │                 │                 │
      ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
      │ SQLite  │      │   MySQL   │     │  Redis    │  (可选)
      │ /MySQL  │      │  (生产)    │     │  MinIO    │
      └─────────┘      └───────────┘     └───────────┘
```

**请求生命周期：**

1. 前端 axios 请求拦截器注入 `Authorization: Bearer <JWT>`，并清理空值/格式化日期
2. 后端 CORS → 操作日志中间件 → 路由处理
3. `get_current_user` / `require_permission` 解析 JWT、校验角色与权限，并将用户信息注入 `request.state`
4. 路由处理完成后，操作日志中间件记录审计日志（仅 2xx 响应）
5. 响应统一为 `ResponseBase(code, message, data)`
6. 前端响应拦截器统一处理 401（自动跳登录）、403/404/422/500 错误提示

---

## 2. 目录结构

```
factory-pms/
├── backend/                         # 后端 FastAPI 应用
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口（生命周期/异常/中间件/路由注册）
│   │   ├── core/                    # 核心基础设施
│   │   │   ├── config.py            # Settings 配置（pydantic-settings）
│   │   │   ├── database.py          # SQLAlchemy engine/Session/Base
│   │   │   ├── security.py          # JWT/密码哈希/权限守卫
│   │   │   └── operation_log.py     # 操作日志中间件
│   │   ├── models/                  # SQLAlchemy ORM 模型（9 个文件）
│   │   │     ├── __init__.py        # 模型导出注册
│   │   │     ├── user.py             # User / Department
│   │   │     ├── role.py             # Role / Permission
│   │   │     ├── project.py          # Project / ProjectType / Task / Requirement
│   │   │     ├── experiment.py       # Experiment / ExperimentRecord / ExperimentAttachment
│   │   │     ├── bom.py              # Material / BomHeader / BomItem / BomChange
│   │   │     ├── sample.py           # Sample / SampleInspection / SampleInspectionItem / TrialProduction
│   │   │     ├── document.py         # Document / DocumentVersion / DocumentApproval / DocCategory / KnowledgeArticle
│   │   │     ├── inventory.py        # Warehouse / InventoryItem / InventoryTransaction / InventoryApproval / InventoryAlert
│   │   │     └── operation_log.py    # OperationLog
│   │   ├── schemas/                 # Pydantic 数据校验模型（10 个文件）
│   │   │     ├── common.py           # ResponseBase / PaginationParams / PaginationResponse
│   │   │     ├── user.py             # 用户相关 schema
│   │   │     ├── department.py       # 部门相关 schema
│   │   │     ├── role.py            # 角色/权限/操作日志 schema
│   │   │     ├── project.py         # 项目/任务/需求 schema
│   │   │     ├── experiment.py      # 实验/实验记录 schema
│   │   │     ├── bom.py             # 物料/BOM schema
│   │   │     ├── sample.py          # 样品/检测/试产 schema
│   │   │     ├── document.py        # 文档/版本/知识库 schema
│   │   │     └── inventory.py      # 库存/仓库/交易/预警 schema
│   │   └── api/v1/                  # 业务路由（11 个模块）
│   │         ├── auth.py            # 登录/注册/当前用户
│   │         ├── users.py           # 用户管理
│   │         ├── departments.py     # 部门管理
│   │         ├── roles.py           # 角色权限管理
│   │         ├── operation_logs.py  # 操作日志
│   │         ├── projects.py        # 项目管理
│   │         ├── experiments.py     # 研发实验
│   │         ├── bom.py             # BOM管理
│   │         ├── samples.py         # 样品试产
│   │         ├── documents.py       # 文档知识
│   │         └── inventory.py       # 库存管理
│   ├── tests/                       # pytest 测试
│   ├── uploads/documents/           # 文档上传物理目录
│   ├── init_db.py                   # 权限模块初始化脚本
│   ├── rebuild_perms.py             # 重建权限表（破坏性运维脚本）
│   ├── run.py                       # 建表 + 种子数据（角色/权限/管理员）
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env                         # 本地开发环境变量
│   └── factory_pms.db               # SQLite 数据库文件
├── frontend/                        # 前端 Vue 3 应用
│   ├── src/
│   │   ├── main.ts                  # 应用入口（挂载 Pinia/Router/ElementPlus）
│   │   ├── App.vue                  # 根组件（仅 router-view）
│   │   ├── router/index.ts          # 路由表 + 路由守卫（JWT/角色）
│   │   ├── stores/auth.ts           # 认证状态（Pinia）
│   │   ├── api/index.ts             # API 聚合层（全部后端接口）
│   │   ├── utils/
│   │   │   ├── request.ts           # axios 实例 + 拦截器
│   │   │   ├── date.ts              # dayjs 日期格式化工具
│   │   │   └── validators.ts        # 表单验证器
│   │   ├── composables/
│   │   │   └── useRequestCancel.ts  # AbortController 请求取消
│   │   ├── constants/status.ts      # 状态映射常量
│   │   ├── types/                   # TypeScript 类型定义（6 个域）
│   │   │     ├── user.ts
│   │   │     ├── project.ts
│   │   │     ├── bom.ts
│   │   │     ├── experiment.ts
│   │   │     ├── sample.ts
│   │   │     ├── document.ts
│   │   │     └── aecq200.ts
│   │   └── views/                   # 页面视图（按业务域组织）
│   │         ├── LayoutView.vue     # 主框架布局
│   │         ├── LoginView.vue      # 登录页
│   │         ├── DashboardView.vue   # 首页仪表盘
│   │         ├── bom/               # BOM模块
│   │         │   ├── BomList.vue
│   │         │   └── BomDetail.vue
│   │         ├── document/          # 文档模块
│   │         │   └── DocumentList.vue
│   │         ├── experiment/        # 实验模块
│   │         │   ├── ExperimentList.vue
│   │         │   ├── TcrTestView.vue
│   │         │   └── TempRiseTestView.vue
│   │         ├── inventory/        # 库存模块
│   │         │   └── InventoryList.vue
│   │         ├── project/          # 项目模块
│   │         │   ├── ProjectList.vue
│   │         │   └── ProjectDetail.vue
│   │         ├── sample/           # 样品模块
│   │         │   └── SampleList.vue
│   │         └── system/           # 系统管理
│   │             ├── DepartmentView.vue
│   │             ├── OperationLogView.vue
│   │             ├── RoleManageView.vue
│   │             └── UserManageView.vue
│   ├── vite.config.ts               # Vite 配置（代理/allowedHosts）
│   ├── Dockerfile                   # 多阶段构建（node → nginx）
│   ├── nginx.conf                   # 前端容器 Nginx 配置
│   └── package.json
├── deploy/                          # 部署编排
│   ├── docker-compose.yml           # mysql/redis/minio/backend/frontend
│   ├── nginx.conf                   # 生产 Nginx 配置
│   └── .env.example
├── docs/                            # 已有分章节文档
├── start.ps1 / stop.ps1             # Windows 一键启停脚本
├── setup-firewall.bat               # Windows 防火墙规则脚本
└── 启动.bat / 停止服务.bat           # 批处理启动入口
```

---

## 3. 后端架构

### 3.1 后端总览

后端采用经典分层架构：`api（路由） → schemas（校验） → models（ORM） → core（基础设施）`。所有路由统一返回 [ResponseBase](#34-schema-层-schemas)，分页使用 `PaginationResponse`。应用入口 [main.py](file:///d:/code/factory-pms/backend/app/main.py) 负责生命周期建表、异常处理、中间件装配与路由注册。

```
app/
├── main.py            # FastAPI 实例、lifespan 自动建表、5 类异常处理器、2 个中间件
├── core/              # 配置、数据库、安全、操作日志
├── models/            # 9 个模型文件，30+ 张表
├── schemas/          # 10 个 schema 文件
└── api/v1/           # 11 个业务路由模块
```

**路由注册（[main.py#L159-L170](file:///d:/code/factory-pms/backend/app/main.py#L159-L170)）：**

| 模块 | 前缀 | Tag |
|------|------|-----|
| auth | `/api/v1/auth` | 认证 |
| users | `/api/v1/users` | 用户管理 |
| departments | `/api/v1/departments` | 部门管理 |
| roles | `/api/v1/roles` | 角色管理 |
| operation_logs | `/api/v1/operation-logs` | 操作日志 |
| projects | `/api/v1/projects` | 项目管理 |
| experiments | `/api/v1/experiments` | 实验管理 |
| bom | `/api/v1/bom` | BOM 管理 |
| samples | `/api/v1/samples` | 样品试产 |
| documents | `/api/v1/documents` | 文档知识 |
| inventory | `/api/v1/inventory` | 库存管理 |

API 文档：`/api/v1/docs`（Swagger）、`/api/v1/redoc`（ReDoc）。

### 3.2 核心模块 core

#### config.py — [Settings](file:///d:/code/factory-pms/backend/app/core/config.py)

基于 `pydantic-settings.BaseSettings`，从 `.env` 加载配置。

| 配置组 | 关键字段 | 说明 |
|--------|----------|------|
| 应用 | `APP_NAME` / `DEBUG` / `API_V1_PREFIX` | 默认 `/api/v1` |
| 数据库 | `DATABASE_URL` / `MYSQL_*` | 默认 SQLite `sqlite:///./factory_pms.db` |
| Redis | `REDIS_URL` / `REDIS_*` | 可选 |
| JWT | `SECRET_KEY` / `ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` | SECRET_KEY 必填且≥32字符，开发环境自动生成 |
| MinIO | `MINIO_*` | 可选对象存储 |
| CORS | `CORS_ORIGINS` | DEBUG 模式含 `*` 时放通所有来源 |

`get_database_url()` / `get_redis_url()` 提供动态拼接。`SECRET_KEY` 字段校验器强制生产环境显式设置。

#### database.py — [数据库引擎](file:///d:/code/factory-pms/backend/app/core/database.py)

- 自动区分 SQLite / MySQL：SQLite 启用 `check_same_thread=False` + `NullPool`，并设置 `PRAGMA journal_mode=WAL`、`PRAGMA foreign_keys=ON`；MySQL 启用连接池 `pool_pre_ping` + `pool_recycle=3600`
- `SessionLocal`：会话工厂
- `Base = declarative_base()`：所有模型基类
- `get_db()`：FastAPI 依赖注入生成器，自动关闭会话

#### security.py — [认证与权限](file:///d:/code/factory-pms/backend/app/core/security.py)

JWT 认证与 RBAC 权限核心。

| 函数/类 | 职责 |
|---------|------|
| `OptionalHTTPBearer` | 可选 Bearer 认证 scheme，缺失凭证返回 None 而非抛错 |
| `create_access_token(data, expires_delta)` | 签发 JWT，注入 `exp/iat/iss` |
| `verify_password(plain, hashed)` | bcrypt 密码校验 |
| `get_password_hash(password)` | bcrypt 哈希（强制≥6字符） |
| `_parse_token(token)` | 解码并校验 JWT，失败抛 401 |
| `get_current_user(request, credentials, db)` | 核心依赖：解析 token → 查用户 → 校验角色有效 → 注入 `request.state.user_id/username` |
| `require_role(*roles)` | 角色级守卫（基于 `User.role` 字符串），返回依赖函数 |
| `require_permission(resource, action)` | RBAC 细粒度守卫：admin 跳过 → 查 Role → 联表查 Permission(resource, action) |

**权限校验流程（`require_permission`）：**

1. admin 角色直接放行（超级管理员）
2. 根据 `User.role` 查 `Role` 表（须 `is_active`）
3. 通过 `role_permissions` 关联表联查 `Permission(resource, action)`
4. 无权限抛 403，附详细提示

#### operation_log.py — [操作日志中间件](file:///d:/code/factory-pms/backend/app/core/operation_log.py)

`OperationLogMiddleware(BaseHTTPMiddleware)` 自动记录所有 API 请求审计日志。

- `ACTION_MAP`：HTTP 方法 → 操作类型（POST=create, PUT=update, DELETE=delete, GET=read）
- `RESOURCE_MAP`：路径前缀 → 资源名（projects→project 等）
- `dispatch`：跳过非 `/api/v1/` 路径及 `auth/login`、`auth/me`；仅记录 2xx 响应；从 `request.state` 取用户信息
- `log_operation`：从路径解析 `resource_id`，记录 IP/UA/方法/路径
- `get_client_ip`：优先 `X-Forwarded-For` → `X-Real-IP` → `request.client.host`
- `log_file_download(db, ...)`：独立函数，供文档下载接口调用记录文件下载日志

### 3.3 数据模型 models

模型注册集中在 [models/__init__.py](file:///d:/code/factory-pms/backend/app/models/__init__.py)，导入所有模型确保 SQLAlchemy 注册。共 30+ 张表，按业务域分 9 个文件。

#### user.py — 用户与部门

- `Department`：部门（`parent_id` 自引用，支持树形）
- `User`：用户（`username/email` 唯一，`password_hash` bcrypt，`role` 字符串 admin/manager/member/viewer，`dept_id` 外键，`is_active`，`last_login_at`）
- 关系：`User.department`、`User.owned_projects`

#### role.py — 角色与权限

- `role_permission_table`：`role_permissions` 多对多关联表（role_id × permission_id）
- `Role`：角色（`code` 唯一如 admin/manager/member/viewer，`is_active`，`sort_order`，`permissions` 关系）
- `Permission`：权限点（`code` 唯一如 `project:create`，`resource` + `action` 二元组，`roles` 反向关系）

#### project.py — 项目

- `ProjectType`：项目类型
- `Project`：项目（`code` 唯一 PMS+时间戳，`status` 状态机 draft→active→on_hold→completed/cancelled，`priority` 1-5，`owner_id`/`created_by`，计划/实际日期，`progress` 0-100，`budget`）
  - 关系：tasks、requirements、experiments、samples（级联删除）
- `Task`：任务（`parent_id` 自引用支持子任务，`assignee_id`，`status` todo→in_progress→review→done，`plan_hours/actual_hours`，`sort_order`）
- `Requirement`：需求（`code` 唯一，`source` customer/sales/internal/market，`priority` must/should/could/wont，`status` 状态机，`version`）

#### experiment.py — 研发实验

- `Experiment`：实验（`project_id`，`code` 唯一，`exp_type`，`status` draft→planned→running→completed/cancelled，`designer_id`/`executor_id`，`param_template` JSON 实验参数模板）
- `ExperimentRecord`：实验记录（`batch_no`，`sample_code`，`param_values`/`result_data` JSON，`result_summary`，`conclusion` pass/fail/conditional_pass/need_retest，**SPC 指标** `cpk`/`mean_value`/`std_dev`，`is_abnormal`）
- `ExperimentAttachment`：实验记录附件

#### bom.py — 物料与 BOM

- `Material`：物料主数据（`code` 唯一，`material_type` raw_material/component/semi_finished/finished/auxiliary，`unit`，`category`，`supplier`，`brand`，`status` active/inactive/pending）
- `BomHeader`：BOM 表头（`project_id`，`code` 唯一，`version`，`status` draft→review→released→archived/obsolete，`product_code`，`approved_by`，关联 items/change_logs 级联）
- `BomItem`：BOM 明细行（`material_id`，`line_no`，`quantity` 字符串支持分数/表达式，`loss_rate` 损耗率，`level` BOM 层级，`parent_item_id` 父项支持多级，`is_key` 关键物料）
- `BomChange`：ECN 变更单（`change_type` ECR/ECN/manual，`change_no` 唯一，`status` draft→review→approved→implemented/rejected，`applicant_id`/`reviewer_id`）

#### sample.py — 样品与试产

- `Sample`：样品（`project_id`，`sample_no` 唯一，`version`，`status` draft→making→testing→passed/failed/rework，`sample_type` development/verification/pre_production，`quantity`，`maker_id`/`inspector_id`，`test_result`）
- `SampleInspection`：检测单（`inspect_no` 唯一，`inspect_type` dimension/performance/appearance/reliability/full，`result` pass/fail/conditional，`dimension_data`/`performance_data` JSON，`disposition` accept/rework/scrap/use_as_is）
- `SampleInspectionItem`：检测项明细（`item_name`，`standard`，`actual_value`，`is_pass`）
- `TrialProduction`：试产记录（`project_id`，`trial_no` 唯一，`bom_id`/`sample_id` 双向关联，`status` planned→in_progress→completed/aborted，`plan_qty/actual_qty/pass_qty/fail_qty`，`process_params` JSON，`yield_rate` 良率，`conclusion` ready_for_mass/need_improvement/fail）

#### document.py — 文档与知识

- `Document`：文档主数据（`code` 唯一，`doc_type` design/test/process/quality/standard/other，`category_id`/`project_id`，`current_version`，`status` draft→review→approved→archived/obsolete，`tags` JSON，`source_module` 标识来源 document/experiment）
- `DocumentVersion`：文档版本（`version`，`file_name`/`file_path`/`file_size`/`mime_type`，`changelog`，`uploader_id`）
- `DocumentApproval`：文档审批（`step`/`step_name` 起草/校对/审核/批准，`status` pending→approved/rejected，`comment`，`signed_at`）
- `DocCategory`：文档分类（树形 `parent_id`）
- `KnowledgeArticle`：知识文章（Markdown `content`，`tags`，`is_published`，`view_count`）

#### inventory.py — 研发库存

- `Warehouse`：仓库（`name`/`code` 唯一，`location`，`manager`，`contact`，`is_active`）
- `InventoryItem`：库存项（`material_id`，`warehouse`，`location` 库位，`quantity`，`reserved_qty` 已预留，`safety_stock`/`max_stock` 阈值，`status` normal/low_stock/out_of_stock/expired，`shelf_life_days`/`expiry_date` 保质期）
- `InventoryTransaction`：库存交易（`transaction_no` 唯一 INV+类型+日期+序号，`transaction_type` inbound/outbound/borrow/return_transfer/check/transfer_in/transfer_out/adjust，`quantity` 正入负出，`before_qty`/`after_qty`，调拨来源/目标仓库，`approval_status`，领用人/预计归还日期）
- `InventoryApproval`：审批记录（`approval_level` 1=库管员/2=主管，`status` pending/approved/rejected）
- `InventoryAlert`：预警（`alert_type` low_stock/out_of_stock/expiry，`is_read`/`is_resolved`）

#### operation_log.py — 操作日志

- `OperationLog`：审计日志（`user_id`/`username`，`action`/`resource`/`resource_id`/`resource_name`，`method`/`path`/`ip_address`/`user_agent`，`is_file_download`/`file_name`/`file_size`，`created_at` 索引）

### 3.4 Schema 层 schemas

Pydantic v2 模型，负责请求校验与响应序列化。每个业务域对应一个 schema 文件。

- [common.py](file:///d:/code/factory-pms/backend/app/schemas/common.py)：
  - `ResponseBase(code, message, data)`：统一响应结构
  - `response_schema()`：响应 Schema 包装器
  - `PaginationParams`：`page`/`page_size` 计算属性 `offset`/`limit`
  - `PaginationResponse`：分页响应 `items/total/page/page_size/total_pages`

**各域 Schema 文件：**

| 文件 | 主要 Schema |
|------|------------|
| user.py | UserCreate/Update/Login/Out、TokenResponse、DepartmentOut、PasswordChange |
| department.py | DepartmentBase/Create/Update/Out/TreeOut（递归 children） |
| role.py | Role/Permission + **OperationLog 的 Query/Out/BatchDelete/Cleanup** |
| project.py | Project/Task/Requirement 的 Create/Update/Out/Query，含 `VALID_PROJECT_STATUSES` 与日期校验 |
| bom.py | Material/BomHeader/BomItem/BomChange 全套 + BatchDelete |
| experiment.py | Experiment/ExperimentRecord 全套 |
| sample.py | Sample/SampleInspection/TrialProduction 全套 |
| document.py | Document/DocumentVersion/DocumentApproval/DocCategory/KnowledgeArticle |
| inventory.py | InventoryItem/Transaction/Approval/Alert/Statistics/Warehouse + BatchInbound |

> 工程约定：所有可选字段必须设置默认值；查询类 schema 含 `offset`/`limit` 计算属性

### 3.5 API 路由层 api

#### auth.py — [认证](file:///d:/code/factory-pms/backend/app/api/v1/auth.py)

| 接口 | 方法 | 说明 | 守卫 |
|------|------|------|------|
| `/login` | POST | 账号密码登录，校验 `is_active`，更新 `last_login_at`，签发 JWT | 无 |
| `/register` | POST | 注册用户 | `require_role("admin")` |
| `/me` | GET | 获取当前用户信息（含部门） | JWT |

#### users.py — 用户管理

- `GET /list`（admin/manager）、`GET /simple-list`（登录）、`POST /create`（admin）、`PUT /{id}`（admin/自改）、`POST /change-password`（admin 可重置/普通用户校验旧密码）、`DELETE /{id}`（软删除）、`POST /batch-enable`/`batch-disable`（admin）、`GET /departments`
- 越权防护：非 admin 禁止改 role 与禁用自身

#### departments.py — 部门管理

- `GET /tree`（递归建树，深度限制 10 层）、`GET /list`、`GET /{id}`、`POST /create`（admin/manager）、`PUT /{id}`、`DELETE /{id}`（admin）
- `_is_descendant` 防循环引用；删除前校验子部门/下属用户

#### roles.py — 角色权限管理

- 角色 CRUD + 权限 CRUD + `POST /{role_id}/permissions`（整体覆盖分配）
- 全部 `require_role("admin")`；系统内置角色禁止修改/删除

#### operation_logs.py — 操作日志

- `GET /list`（多条件分页）、`GET /download-logs`（文件下载专用）、`DELETE /{id}`、`POST /batch-delete`、`POST /cleanup`（按保留天数清理，默认 90 天）、`GET /stats`（统计聚合）
- 查询类 admin/manager；删除类 `require_permission("log","delete")`

#### projects.py — [项目管理](file:///d:/code/factory-pms/backend/app/api/v1/projects.py)

- 项目类型 + 项目/任务/需求 CRUD
- **数据隔离** `get_user_projects_filter`：admin/manager 看全部，普通成员仅看 `owner_id` 或 `created_by` 是自己的项目
- 编码自动生成 `PMS+时间戳`；删除项目时级联清理文档/BOM 引用、试产记录、操作日志标记

#### experiments.py — 研发实验

- 实验 + 实验记录 CRUD
- **数据隔离**：非 admin/manager 仅看自己作为 designer/executor 的实验（list 与 get 双层校验）
- 编码 `EXP+时间戳`；记录含 SPC 字段

#### bom.py — BOM 管理

- 物料（含批量删除，被引用则只停用）、BOM 头/明细、ECN 变更全套 CRUD
- **ECN 工作流**：released 状态 BOM 禁止直接改/删明细，须走变更流程；reviewing/released 禁止删除
- 删除 BOM 前解除 TrialProduction 引用；删除明细前检查子项引用
- 编码 `BOM+时间戳`、变更单 `ECN+时间戳`

#### samples.py — 样品试产

- 样品/检测/试产 CRUD
- 编码 `SMP+`/`INSP+`/`TR+时间戳`；删除样品前解除 TrialProduction 引用

#### documents.py — 文档知识

- 文档 CRUD + 版本上传/下载/预览 + 知识库聚合 + 实验文档入口
- **文件安全**：`UPLOAD_DIR=backend/uploads/documents`，`MAX_FILE_SIZE=50MB`，MIME/扩展名白名单（含 .dwg/.step 工程图纸），流式分块写入（1MB/块），RFC 2231 文件名编码防注入，`X-Content-Type-Options: nosniff`
- 版本号自增 `V{n}.0`；删除文档同步删物理文件
- `inline=true` 浏览器预览，`false` 下载并调用 `log_file_download` 记录日志
- 知识库 `/knowledge/list` 聚合所有含版本的文档（含 `source_module=experiment`）

#### inventory.py — 库存管理（最复杂模块）

- 仓库 CRUD + 库存项 CRUD + 交易操作（入库/出库/领用/归还/盘点/调拨）+ 交易记录 + 审批 + 预警 + 统计
- **并发安全**：`_generate_tx_no` 用 `with_for_update()` 原子锁生成单号；`_do_transaction` 与 transfer 全程 `SELECT...FOR UPDATE` 行锁防超卖
- **状态机** `_check_low_stock`：quantity≤0→out_of_stock；≤safety_stock→low_stock；过期→expired；否则 normal
- **预警自动生成** `_create_alert`：低库存/缺货/过期自动写 InventoryAlert
- **调拨**：单事务内 transfer_out → 查找/创建目标库存 → transfer_in，异常整体 rollback
- **审批工作流**：拒绝时回滚库存数量
- **统计**：总览、按仓库聚合、周转率分析
- 路由顺序：`/{item_id}` 显式放在所有具名路由之后避免路径冲突

### 3.6 异常处理与中间件

[main.py](file:///d:/code/factory-pms/backend/app/main.py) 注册 5 类全局异常处理器，统一返回 `ResponseBase` 结构：

| 异常 | HTTP 状态 | 说明 |
|------|-----------|------|
| `RequestValidationError` | 422 | 请求参数验证失败，返回字段级错误 |
| `HTTPException` | 动态 | HTTP 异常，区分 str/非 str detail |
| `ValidationError` | 422 | Pydantic 模型验证错误 |
| `SQLAlchemyError` | 500 | 数据库错误（日志记录，不泄露细节） |
| `Exception` | 500 | 兜底通用异常 |

中间件链（注册顺序即执行顺序）：

1. `log_requests`：请求日志（方法/路径/状态/耗时）
2. `CORSMiddleware`：跨域，DEBUG 模式含 `*` 放通
3. `OperationLogMiddleware`：审计日志记录

---

## 4. 前端架构

### 4.1 前端总览

Vue 3 + TypeScript + Vite 单页应用，按业务域组织视图，集中式 API 层与请求拦截。

```
src/
├── main.ts           # 入口：createApp + Pinia + Router + ElementPlus(全量图标注册)
├── App.vue           # 根组件（仅 <router-view/>）
├── router/           # 路由表 + 路由守卫
├── stores/auth.ts    # 认证 store
├── api/index.ts      # 全部后端 API 聚合
├── utils/            # request.ts(axios) + date.ts(dayjs)
├── composables/      # useRequestCancel(AbortController)
├── constants/        # status.ts(状态映射)
├── types/            # 6 个域的 TS 类型
└── views/            # 页面（按域分目录）
```

### 4.2 入口与路由

[main.ts](file:///d:/code/factory-pms/frontend/src/main.ts)：创建 app，注册 Pinia、Router、Element Plus，全量注册 `@element-plus/icons-vue` 图标组件

[router/index.ts](file:///d:/code/factory-pms/frontend/src/router/index.ts)：

- 路由声明 `RouteMeta`：`requiresAuth`、`title`、`roles`、`permission`
- 结构：`/login` 独立；`/` 下 `LayoutView` 嵌套子路由（Dashboard + 8 个业务模块 + 4 个系统管理页）
- **路由守卫** `beforeEach`：
  - `isTokenExpired`：解析 JWT `exp` 判断过期
  - 未登录或 token 过期 → 跳 `/login`；已登录访问 `/login` → 跳 `/`
  - `roles` 元信息校验：无权限跳首页（后端二次校验兜底）
  - 动态设置 `document.title`

| 路径 | 视图 | 角色限制 |
|------|------|----------|
| `/login` | LoginView | 无 |
| `/` | DashboardView | 登录 |
| `/projects` `/projects/:id` | ProjectList / ProjectDetail | 登录 |
| `/experiments` | ExperimentList | 登录 |
| `/bom` `/bom/:id` | BomList / BomDetail | 登录 |
| `/samples` | SampleList | 登录 |
| `/documents` | DocumentList | 登录 |
| `/inventory` | InventoryList | 登录 |
| `/system/users` | UserManageView | admin |
| `/system/departments` | DepartmentView | admin/manager |
| `/system/roles` | RoleManageView | admin |
| `/system/logs` | OperationLogView | admin/manager |

### 4.3 状态管理 stores

[stores/auth.ts](file:///d:/code/factory-pms/frontend/src/stores/auth.ts) — `useAuthStore`（Composition API 风格）：

- 状态：`token`（同步 localStorage）、`user`、`loading`
- 计算属性：`isAuthenticated`、`username`、`userRole`
- 方法：
  - `initFromStorage()`：从 localStorage 恢复用户信息
  - `login(username, password)`：调用 login API → 存 token → 调 getMe → 存 userInfo
  - `fetchUser()`：刷新当前用户，失败则 logout
  - `logout()`：清空 token/userInfo
  - `changePassword(old, new)`：调用改密 API
  - `hasRole(...roles)`：角色判断工具

### 4.4 请求层 utils/request

[utils/request.ts](file:///d:/code/factory-pms/frontend/src/utils/request.ts) — axios 实例与拦截器，是前后端契约的核心。

- `BASE_URL`：`VITE_API_BASE || '/api/v1'`
- `formatDate(date)`：Date → `YYYY-MM-DD` 字符串（解决 Element Plus 日期选择器返回 Date 对象与后端 Pydantic date 类型不兼容问题）
- `cleanData(data)`：递归清理请求数据——Date→格式化字符串、剔除 undefined、保留 null、递归处理对象/数组

**请求拦截器**：注入 `Authorization: Bearer <token>`；POST/PUT 时对非 FormData 数据执行 `cleanData`

**响应拦截器**：
- 成功：检查业务 `code`，非 200 报错；返回 `body.data`（优先）或 `body`
- 401 防抖 `isRedirecting`：登录接口 401 不跳转（用户名密码错误），其他 401 清 token 跳登录
- 错误分类处理：403/404/422（参数验证错误聚合）/500/网络错误/无响应，统一 `ElMessage.error`
- 请求取消（`axios.isCancel`）静默处理
- 422 错误自动翻译为中文提示（内置 FIELD_NAME_MAP + translateMsg + formatValidationError）

[utils/date.ts](file:///d:/code/factory-pms/frontend/src/utils/date.ts) — dayjs 工具：`formatDate`、`formatDateTime`、`formatDateTimeFull`、`fromNow`（相对时间）

[composables/useRequestCancel.ts](file:///d:/code/factory-pms/frontend/src/composables/useRequestCancel.ts) — 封装 `AbortController`：`getSignal()`、`resetController()`、`cancelAll()`，`onUnmounted` 自动取消未完成请求

### 4.5 API 聚合层 api/index

[api/index.ts](file:///d:/code/factory-pms/frontend/src/api/index.ts) — 集中导出所有后端接口，按域分组：

| 导出 | 覆盖接口 |
|------|----------|
| `authApi` | login / getMe / getMyPermissions |
| `userApi` | list / simpleList / create / update / remove / departments |
| `userEnhanceApi` | changePassword / batchEnable / batchDisable |
| `projectApi` | types / list / create / get / update / remove + 任务/需求 |
| `experimentApi` | list / create / get / update / remove + records + 附件/导出 |
| `bomApi` | materials(含批量) / headers / items(含批量) / changes |
| `sampleApi` | samples / inspections / trials |
| `documentApi` | docs / uploadVersion / getVersions / **downloadDoc(fetch+token)** / knowledge / fromExperiment |
| `departmentApi` | tree / list / get / create / update / remove |
| `roleApi` | list / get / create / update / remove + permissions + assignPermissions |
| `operationLogApi` | list / listDownloads |
| `inventoryApi` | list / warehouses / CRUD + inbound/outbound/borrow/return/check/transfer + transactions + approvals + alerts + stats + warehouse CRUD |

> 文档下载/预览因需流式响应，使用原生 `fetch` + `Authorization` 头，不走 axios

### 4.6 视图模块 views

#### 布局与认证

- [LayoutView.vue](file:///d:/code/factory-pms/frontend/src/views/LayoutView.vue)：主框架，三段侧边导航（主导航/核心模块/系统管理），顶栏用户下拉（修改密码/退出），`el-dialog` 改密弹窗。调 `authStore.logout/changePassword`
- [LoginView.vue](file:///d:/code/factory-pms/frontend/src/views/LoginView.vue)：登录卡片，表单校验 + Enter 提交 + loading 态，开发环境演示账号提示

#### 首页

- [DashboardView.vue](file:///d:/code/factory-pms/frontend/src/views/DashboardView.vue)：4 统计卡（Promise.all 并发）+ 4 快捷入口 + 最近 5 项目表格（el-tag 状态、el-progress 进度）

#### 项目模块

- [ProjectList.vue](file:///d:/code/factory-pms/frontend/src/views/project/ProjectList.vue)：筛选/搜索/分页/CRUD，el-rate 优先级、el-progress 进度、daterange 计划周期，负责人懒加载
- [ProjectDetail.vue](file:///d:/code/factory-pms/frontend/src/views/project/ProjectDetail.vue)：el-page-header + el-descriptions + el-tabs（任务管理/需求管理）

#### BOM 模块

- [BomList.vue](file:///d:/code/factory-pms/frontend/src/views/bom/BomList.vue)：双 Tab（物料主数据含批量停用 / BOM 清单）
- [BomDetail.vue](file:///d:/code/factory-pms/frontend/src/views/bom/BomDetail.vue)：BOM 明细（filterable 物料下拉、损耗率实时计算实际需求量）+ ECN 变更记录（create/edit/view 三态）

#### 实验/样品/文档/库存

- [ExperimentList.vue](file:///d:/code/factory-pms/frontend/src/views/experiment/ExperimentList.vue)：实验列表 + 记录弹窗 + 上传实验文档至知识库（el-upload drag）
- [SampleList.vue](file:///d:/code/factory-pms/frontend/src/views/sample/SampleList.vue)：双 Tab（样品含检测记录 / 试产含良率渲染）
- [DocumentList.vue](file:///d:/code/factory-pms/frontend/src/views/document/DocumentList.vue)：双 Tab（新建文档含版本上传/下载/预览 / 知识库聚合含来源标签）
- [InventoryList.vue](file:///d:/code/factory-pms/frontend/src/views/inventory/InventoryList.vue)：4 Tab（库存列表含入库/出库/领用/盘点 / 交易记录 / 统计分析含周转 / 仓库管理），顶部 5 彩色统计卡

#### 系统管理

- [UserManageView.vue](file:///d:/code/factory-pms/frontend/src/views/system/UserManageView.vue)：账号 CRUD + 重置密码 + 启停用（batchEnable/Disable 单 ID）
- [DepartmentView.vue](file:///d:/code/factory-pms/frontend/src/views/system/DepartmentView.vue)：el-tree 部门树 + 自定义节点模板 + CRUD
- [RoleManageView.vue](file:///d:/code/factory-pms/frontend/src/views/system/RoleManageView.vue)：角色 CRUD + **资源×操作权限矩阵**（复选矩阵，全选/清空/行级全选，已选统计）
- [OperationLogView.vue](file:///d:/code/factory-pms/frontend/src/views/system/OperationLogView.vue)：日志查询（关键字/操作类型/daterange），resourceMap 中文化资源名

### 4.7 类型定义与常量

[types/](file:///d:/code/factory-pms/frontend/src/types)：

| 文件 | 主要类型 |
|------|----------|
| user.ts | UserOut / LoginParams / TokenResponse |
| project.ts | ProjectOut / TaskOut / RequirementOut |
| bom.ts | MaterialOut / BomItemOut（嵌套 material）/ BomHeaderOut（嵌套 items） |
| experiment.ts | ExperimentOut / ExperimentRecordOut（含 SPC 字段） |
| sample.ts | SampleOut / TrialProductionOut |
| document.ts | DocumentOut（含 latest_version/version_count）/ KnowledgeDocOut / KnowledgeArticleOut |

[constants/status.ts](file:///d:/code/factory-pms/frontend/src/constants/status.ts)：
- 状态映射常量（`as const`）：PROJECT_STATUS / PROJECT_PRIORITY / EXPERIMENT_STATUS / BOM_STATUS / SAMPLE_STATUS / INVENTORY_STATUS，每项 `{ tag, label }`
- 工具函数：`getStatusTag(map, status)`、`getStatusLabel(map, status)`

---

## 5. 关键类与函数说明

### 后端

| 位置 | 标识 | 说明 |
|------|------|------|
| core/config.py | `Settings` | 全局配置类，`.env` 加载，SECRET_KEY 强制校验 |
| core/database.py | `get_db()` | 请求级数据库会话依赖注入 |
| core/security.py | `create_access_token(data, expires_delta)` | JWT 签发 |
| core/security.py | `get_current_user(...)` | 核心认证依赖，注入 request.state |
| core/security.py | `require_role(*roles)` | 角色级权限守卫 |
| core/security.py | `require_permission(resource, action)` | RBAC 细粒度权限守卫 |
| core/operation_log.py | `OperationLogMiddleware` | 审计日志中间件 |
| core/operation_log.py | `log_file_download(db, ...)` | 文件下载日志记录 |
| main.py | `lifespan(app)` | 启动时 `Base.metadata.create_all` 自动建表 |
| api/v1/projects.py | `get_user_projects_filter(q, current)` | 项目数据隔离过滤 |
| api/v1/inventory.py | `_generate_tx_no(...)` | 行锁原子生成交易单号 |
| api/v1/inventory.py | `_do_transaction(...)` | 库存交易核心（FOR UPDATE 行锁） |
| api/v1/inventory.py | `_check_low_stock(...)` | 库存状态机 |
| api/v1/documents.py | `_send_file_response(...)` | 文件下载/预览响应（防注入） |
| run.py | `seed_roles_and_permissions(db)` | 种子角色/权限/管理员 |
| run.py | `init_db()` | 建表 + 默认部门 + 角色 + admin 账号 |
| rebuild_perms.py | `rebuild_permission_tables()` | 重建权限表（破坏性运维） |

### 前端

| 位置 | 标识 | 说明 |
|------|------|------|
| utils/request.ts | `cleanData(data)` | 递归清理请求数据（Date→字符串、剔除空值） |
| utils/request.ts | `formatDate(date)` | Date → YYYY-MM-DD |
| utils/request.ts | `handle401()` | 401 防抖跳登录 |
| utils/request.ts | `formatValidationError(detail)` | 422 错误转中文提示 |
| router/index.ts | `isTokenExpired(token)` | JWT exp 过期判断 |
| router/index.ts | `router.beforeEach` | 认证 + 角色路由守卫 |
| router/index.ts | `getStoredPermissions()` | 从 localStorage 读取权限码 |
| stores/auth.ts | `useAuthStore` | 认证状态管理 |
| api/index.ts | `documentApi.downloadDoc` | 原生 fetch 流式下载/预览 |
| api/index.ts | `experimentApi.exportRecords` | 原生 fetch 流式导出 Excel |
| composables/useRequestCancel.ts | `useRequestCancel` | AbortController 请求取消 |
| constants/status.ts | `getStatusTag / getStatusLabel` | 状态 tag/label 映射工具 |

---

## 6. 依赖关系

### 6.1 后端依赖

[requirements.txt](file:///d:/code/factory-pms/backend/requirements.txt)：

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | 0.110 | Web 框架 |
| uvicorn[standard] | 0.27.1 | ASGI 服务器 |
| sqlalchemy | 2.0.25 | ORM |
| pymysql | 1.1.0 | MySQL 驱动 |
| pydantic | 2.5.3 | 数据校验 |
| pydantic-settings | 2.1.0 | 配置管理 |
| PyJWT | 2.9.0 | JWT |
| bcrypt | 4.3.0 | 密码哈希 |
| python-multipart | 0.0.6 | 文件上传 |
| alembic | 1.13.1 | 数据库迁移 |
| redis | 5.0.1 | Redis 客户端（可选） |
| minio | 7.2.0 | 对象存储客户端（可选） |
| xhtml2pdf | 0.2.15 | PDF 生成 |
| polars | 0.20.1 | 数据分析 |
| email-validator | 2.1.0 | 邮箱校验 |
| pytest / httpx2 | - | 测试 |

### 6.2 前端依赖

[package.json](file:///d:/code/factory-pms/frontend/package.json)：

| 依赖 | 用途 |
|------|------|
| vue ^3.4 | 框架 |
| vue-router ^4.3 | 路由 |
| pinia ^2.1 | 状态管理 |
| element-plus ^2.7 | UI 库 |
| @element-plus/icons-vue ^2.3 | 图标 |
| axios ^1.7 | HTTP |
| dayjs ^1.11 | 日期处理 |
| echarts ^5.5 | 图表 |
| @vueup/vue-quill ^1.3 | 富文本 |
| vite ^5.2 / vue-tsc ^2.0 / sass ^1.77 / typescript ^5.4 | 开发工具链 |

### 6.3 模块间依赖

**后端调用链：**

```
api/v1/*  →  core/security(认证守卫)  →  core/database(get_db)
         →  schemas/*(校验)  →  models/*(ORM)
         →  core/operation_log(审计)
```

**前端调用链：**

```
views/*  →  stores/auth(认证态)  →  api/index(接口)
        →  utils/request(axios 拦截)  →  后端 /api/v1/*
        →  router(守卫) / constants/status / types/*
```

**跨层契约：**

- 前端 axios 响应拦截器解包 `ResponseBase.data`，视图直接拿到 `data`
- 日期契约：前端必须将 Date 格式化为 `YYYY-MM-DD` 字符串再提交（后端 Pydantic `date` 类型）
- 认证契约：前端 `localStorage.token` + `Bearer` 头；后端 `get_current_user` 解析注入

---

## 7. 权限体系

系统采用**双层权限模型**：

### 7.1 角色级（require_role）

基于 `User.role` 字符串，用于系统管理类接口：

| 角色 | 说明 |
|------|------|
| admin | 系统管理员，全部权限 |
| manager | 主管，可管理项目和数据 |
| member | 普通成员，可创建编辑自己的数据 |
| viewer | 只读用户 |

### 7.2 RBAC 细粒度（require_permission）

基于 `Role ↔ Permission(resource, action)` 关联表，用于业务模块：

- 权限点格式：`{resource}:{action}`，如 `project:create`、`inventory:approve`
- 资源：project / experiment / bom / sample / document / user / department / role / warehouse / inventory / material / log
- 操作：create / read / update / delete / download / upload / approve 等
- admin 跳过细粒度检查（超级管理员）

### 7.3 数据隔离

| 模块 | 隔离策略 |
|------|----------|
| 项目 | admin/manager 看全部；普通成员仅看 `owner_id` 或 `created_by` 是自己的项目 |
| 实验 | 非 admin/manager 仅看自己作为 designer/executor 的实验（list 与 get 双层校验） |
| 库存/文档/BOM/样品 | 按权限码控制读写，未实现行级隔离 |

### 7.4 默认角色权限分配

[run.py](file:///d:/code/factory-pms/backend/run.py) 中 `ROLE_PERMISSIONS_MAP` 定义种子分配（仅角色无权限时填充，不覆盖前端修改）：

| 角色 | 权限 |
|------|------|
| admin | `["*"]` 全部权限 |
| manager | 项目/物料/BOM/样品/文档/实验/库存/仓库的读写 + inventory:approve + user:read + log:read |
| member | 各资源 read + 部分 create（project/bom/sample/document/experiment/inventory/warehouse） |
| viewer | 全部 read + document:download |

### 7.5 权限资源与操作一览

[run.py#L23-65](file:///d:/code/factory-pms/backend/run.py#L23-65) 定义全部权限点：

| 资源 | 操作 |
|------|------|
| project | create / read / update / delete |
| material | create / read / update / delete |
| bom | create / read / update / delete |
| sample | create / read / update / delete |
| document | create / read / update / delete / upload / download |
| experiment | create / read / update / delete |
| user | create / read / update / delete |
| log | read / delete |
| inventory | create / read / update / delete / approve |
| warehouse | create / read / update / delete |

---

## 8. 项目运行方式

### 8.1 本地开发环境

**前置要求：** Python 3.11+、Node.js 18+、npm

**方式 A：一键脚本（Windows，推荐）**

```powershell
# 启动（自动安装依赖 + 初始化数据库 + 启动前后台）
.\start.ps1 start

# 停止
.\start.ps1 stop

# 仅初始化（依赖 + 数据库）
.\start.ps1 init

# 查看状态
.\start.ps1 status
```

或双击 `启动.bat` / `停止服务.bat`

脚本行为（[start.ps1](file:///d:/code/factory-pms/start.ps1)）：

1. 检测/安装后端依赖（`pip install -r requirements.txt`）
2. 检测/安装前端依赖（`npm install`）
3. 初始化数据库（`python run.py`，幂等；默认 `ADMIN_PASSWORD=admin123`）
4. 后台启动后端 `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. 后台启动前端 `npm run dev`（端口 5173）
6. PID 写入 `.runtime/`，日志写入 `.runtime/*.log`

**方式 B：手动分步**

```powershell
# 后端
cd backend
pip install -r requirements.txt
python run.py                         # 建表 + 种子数据（首次）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

**默认账号：** `admin / admin123`（或通过环境变量 `ADMIN_PASSWORD` 自定义）

**访问地址：**

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API 文档 | http://localhost:8000/api/v1/docs |
| 健康检查 | http://localhost:8000/health |

**本地配置（[backend/.env](file:///d:/code/factory-pms/backend/.env)）：** 默认 SQLite，`CORS_ORIGINS=["*"]`，无需 MySQL/Redis/MinIO

### 8.2 Docker 部署

**编排文件：** [deploy/docker-compose.yml](file:///d:/code/factory-pms/deploy/docker-compose.yml)

```bash
cd deploy
cp .env.example .env                  # 修改 SECRET_KEY 等敏感配置
docker-compose up -d                  # 启动全部服务
```

**服务拓扑：**

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| mysql | mysql:8.0 | 3306 | 数据库，持久化卷 mysql_data |
| redis | redis:7-alpine | 6379 | 缓存（可选），持久化卷 redis_data |
| minio | minio/minio | 9000/9001 | 对象存储（可选），持久化卷 minio_data |
| backend | 自构建 python:3.13-slim | 8000 | FastAPI，健康检查，非特权用户 |
| frontend | 自构建 nginx:alpine | 80 | 多阶段构建（node 编译 → nginx 托管） |

**网络：** `pms-net` bridge 网络，前端容器通过 `http://backend:8000` 代理 API

**生产 Nginx（[deploy/nginx.conf](file:///d:/code/factory-pms/deploy/nginx.conf)）：** SPA history fallback + `/api/` 代理后端 + 静态资源 1 年缓存 + gzip

**环境变量（[deploy/.env.example](file:///d:/code/factory-pms/deploy/.env.example)）：** 需修改 `SECRET_KEY`、`MYSQL_*`、`MINIO_*`、`CORS_ORIGINS`、`VITE_API_BASE`

### 8.3 局域网与内网穿透

**Vite 配置（[vite.config.ts](file:///d:/code/factory-pms/frontend/vite.config.ts)）：**

- `host: '0.0.0.0'`：允许局域网访问
- `allowedHosts: ['.cpolar.top', '.trae.cn', 'localhost']`：允许 Cpolar 公网域名访问
- `proxy['/api'] → http://localhost:8000`：前端代理后端，公网仅需穿透前端

**防火墙：** 运行 [setup-firewall.bat](file:///d:/code/factory-pms/setup-firewall.bat)（需管理员）开放 5173（前端）与 8000（后端）入站 TCP，规则名 `Factory PMS`

**访问方案：**

1. **仅穿透前端（推荐）**：Cpolar 穿透 5173，后端本地运行，前端 Vite 代理转发。运行 `启动内网穿透.bat`
2. **仅穿透后端**：需修改前端 `VITE_API_BASE` 指向后端公网地址
3. **不穿透（局域网）**：直接用 `http://<本机IP>:5173` 访问，适合工厂内网

---

## 9. 工程约定与注意事项

### 硬性约束

- **前端日期格式化**：Date 对象必须在请求前格式化为 `YYYY-MM-DD` 字符串（已由 `utils/request.ts` 的 `cleanData` 自动处理）
- **后端响应结构**：统一 `ResponseBase(code, message, data)`，`data` 支持 dict 或 list
- **Vite allowedHosts**：必须包含 `.cpolar.top`、`.trae.cn`、`localhost`，否则公网访问报 `Blocked request`

### 工程约定

- 后端所有可选 schema 字段必须设置默认值
- 前端请求数据须清理空字符串与 undefined（`cleanData` 已实现，保留 null）
- 统一编码生成：业务实体采用 `{前缀}{YYYYMMDDHHMMSS}` 时间戳（PMS/EXP/BOM/ECN/SMP/INSP/TR/DOC），inventory 单号额外带序号
- 软删除：用户删除为软删除（`is_active=False`）；BOM/样品删除前解除 TrialProduction 反向引用；物料被引用则只停用

### 关键设计

- **并发控制**：仅 inventory 模块使用 `SELECT...FOR UPDATE` 行锁防止库存超卖与单号重复
- **文件安全**：documents 模块具备 MIME/扩展名白名单、50MB 大小限制、流式写入、文件名 RFC 2231 编码、`nosniff` 头
- **操作日志**：中间件自动记录 2xx 响应的 API 请求；文件下载单独记录；登录/当前用户接口不记录
- **路由顺序陷阱**：inventory 模块 `/{item_id}` 单条 CRUD 显式放在所有具名路由之后，避免拦截 `/stats/*`、`/approvals/*`

### 运维脚本

| 脚本 | 说明 |
|------|------|
| [run.py](file:///d:/code/factory-pms/backend/run.py) | 幂等建表 + 种子数据，`python run.py reset` 可 drop 所有表（交互确认） |
| [init_db.py](file:///d:/code/factory-pms/backend/init_db.py) | 权限模块独立初始化脚本 |
| [rebuild_perms.py](file:///d:/code/factory-pms/backend/rebuild_perms.py) | **破坏性**重建权限相关表（role_permissions/permissions/roles/operation_logs），仅在表结构损坏时手动执行，会清除数据 |

### 已知未完成功能

- ProjectDetail 中更新/删除需求、ExperimentList 新增实验记录、SampleList 新增检测记录：前端以"开发中"提示，后端接口已就绪
- `constants/status.ts` 提供统一状态映射，但部分视图存在本地内联重复定义，待收敛

---

## 附录

### A. 数据库 ER 关系概览

```
User ──(dept_id)──> Department
User ──(role)──> Role ──(role_permissions)──> Permission

Project ──(owner_id)──> User
Project ──(tasks)──> Task ──(assignee_id)──> User
Project ──(experiments)──> Experiment ──(designer_id/executor_id)──> User
Project ──(samples)──> Sample
Project ──(bom_headers)──> BomHeader
Project ──(documents)──> Document

Experiment ──(records)──> ExperimentRecord
ExperimentRecord ──(attachments)──> ExperimentAttachment

BomHeader ──(items)──> BomItem ──(material_id)──> Material
BomHeader ──(change_logs)──> BomChange

Sample ──(inspections)──> SampleInspection ──(items)──> SampleInspectionItem
Sample ──(trial_productions)──> TrialProduction ──(bom_id)──> BomHeader

Document ──(versions)──> DocumentVersion
Document ──(category_id)──> DocCategory
Document ──(approval_records)──> DocumentApproval

Warehouse
InventoryItem ──(warehouse)──> Warehouse
InventoryItem ──(material_id)──> Material
InventoryItem ──(transactions)──> InventoryTransaction
InventoryTransaction ──(approvals)──> InventoryApproval
InventoryItem ──(alerts)──> InventoryAlert

OperationLog ──(user_id)──> User
```

### B. API 接口速查

| 模块 | 路径 | 主要接口数 |
|------|------|-----------|
| 认证 | /api/v1/auth | 3 |
| 用户 | /api/v1/users | 9 |
| 部门 | /api/v1/departments | 6 |
| 角色 | /api/v1/roles | 7 |
| 操作日志 | /api/v1/operation-logs | 6 |
| 项目 | /api/v1/projects | 12+ |
| 实验 | /api/v1/experiments | 15+ |
| BOM | /api/v1/bom | 15+ |
| 样品 | /api/v1/samples | 9+ |
| 文档 | /api/v1/documents | 10+ |
| 库存 | /api/v1/inventory | 25+ |

---

*本文档由代码分析自动生成，最后更新于 2026-06-28*
