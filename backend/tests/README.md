# 测试脚本说明文档

本目录包含工厂研发项目管理系统后端的所有自动化测试脚本，使用 `pytest` 框架编写。

## 目录结构

```
backend/
├── tests/
│   ├── conftest.py           # 测试配置与公共 fixtures
│   ├── test_auth.py          # 认证模块测试
│   ├── test_users.py         # 用户管理测试
│   ├── test_roles.py         # 角色权限测试
│   ├── test_departments.py   # 部门管理测试
│   ├── test_bom.py           # BOM 管理测试
│   ├── test_inventory.py     # 库存管理测试
│   ├── test_samples.py       # 样品试产测试
│   ├── test_projects.py      # 项目管理测试
│   ├── test_experiments.py   # 实验管理测试
│   ├── test_documents.py     # 文档知识测试
│   ├── test_integration.py   # 集成测试
│   └── test_core.py          # 核心功能测试
├── run_tests.py              # 一键测试脚本（Python 版本，跨平台）
├── run_tests.ps1             # 一键测试脚本（PowerShell 版本，Windows）
└── pytest.ini                # pytest 配置文件
```

## 环境要求

- Python 3.11+
- pytest 9.x
- 已配置虚拟环境（推荐 `.venv`）

### 安装依赖

```bash
# 激活虚拟环境
.venv\Scripts\activate   # Windows
# 或
source .venv/bin/activate  # Linux/macOS

# 安装测试依赖
pip install pytest pytest-cov pytest-anyio
```

## 快速开始

### 方式一：使用一键测试脚本（推荐）

**Python 版本（跨平台）：**

```bash
# 运行所有测试
python run_tests.py

# 显示帮助
python run_tests.py -h
```

**PowerShell 版本（Windows）：**

```powershell
# 运行所有测试
.\run_tests.ps1

# 显示帮助
.\run_tests.ps1 -h
```

### 方式二：直接使用 pytest

```bash
# 运行所有测试
pytest tests/

# 运行指定模块
pytest tests/test_bom.py

# 运行指定测试用例
pytest tests/test_bom.py::TestBOMCRUD::test_create_material

# 显示详细输出
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 一键测试脚本参数说明

### Python 版本 (`run_tests.py`)

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--verbose` | `-v` | 显示详细输出（每个测试用例的结果） | `python run_tests.py -v` |
| `--quiet` | `-q` | 静默模式，只显示进度条和最终摘要 | `python run_tests.py -q` |
| `--module` | `-m` | 运行指定模块的测试 | `python run_tests.py -m bom` |
| `--keyword` | `-k` | 按关键字过滤测试用例 | `python run_tests.py -k "test_create"` |
| `--help` | `-h` | 显示帮助信息 | `python run_tests.py -h` |

### PowerShell 版本 (`run_tests.ps1`)

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `-Verbose` | Switch | 显示详细输出 | `.\run_tests.ps1 -Verbose` |
| `-Quiet` | Switch | 静默模式 | `.\run_tests.ps1 -Quiet` |
| `-Module` | String | 运行指定模块 | `.\run_tests.ps1 -Module bom` |
| `-Keyword` | String | 按关键字过滤 | `.\run_tests.ps1 -Keyword "test_create"` |

## 可用测试模块

使用 `-m` 参数可指定运行以下模块：

| 模块名 | 测试文件 | 覆盖功能 |
|--------|----------|----------|
| `auth` | `test_auth.py` | 登录、注册、令牌验证 |
| `users` | `test_users.py` | 用户 CRUD、状态管理 |
| `roles` | `test_roles.py` | 角色权限、RBAC |
| `departments` | `test_departments.py` | 部门树、部门管理 |
| `bom` | `test_bom.py` | 物料、BOM 单、BOM 变更 |
| `inventory` | `test_inventory.py` | 仓库、出入库、库存调拨、审批 |
| `samples` | `test_samples.py` | 样品、检验、试产记录 |
| `projects` | `test_projects.py` | 项目、任务、需求 |
| `experiments` | `test_experiments.py` | 实验、实验记录 |
| `documents` | `test_documents.py` | 文档、版本、审批 |
| `integration` | `test_integration.py` | 跨模块集成测试 |

## 测试 Fixtures

`conftest.py` 中提供以下公共 fixtures：

| Fixture 名 | 作用域 | 说明 |
|------------|--------|------|
| `setup_database` | session | 初始化测试数据库，创建所有表 |
| `db` | function | 数据库会话，每个测试后自动回滚 |
| `client` | function | FastAPI TestClient，自动注入测试数据库 |
| `admin_user` | function | 创建管理员用户（admin 角色） |
| `admin_token` | function | 获取管理员登录令牌 |
| `member_user` | function | 创建普通成员用户（member 角色） |
| `member_token` | function | 获取普通成员登录令牌 |
| `test_warehouse` | function | 创建测试仓库 |
| `test_material` | function | 创建测试物料 |

## 测试数据隔离

- 每个测试用例在独立的数据库事务中运行
- 测试结束后事务自动回滚，不会污染数据
- 测试数据库使用 SQLite，文件名为 `test_fixture.db`
- 一键脚本会在运行前自动清理旧的测试数据库

## 常见问题

### 1. 登录测试失败（429 Too Many Requests）

原因：速率限制器在多次测试后被触发。

解决：测试框架已在 `client` fixture 中自动重置速率限制器，如遇问题可手动清除：

```python
from app.core.rate_limit import login_rate_limiter
login_rate_limiter._store.clear()
```

### 2. 数据库锁定或连接问题

原因：SQLite 在多线程环境下可能出现锁问题。

解决：确保使用测试框架提供的 `db` fixture，不要直接创建新的数据库连接。

### 3. 导入错误

原因：Python 路径未正确配置。

解决：确保从 `backend` 目录运行测试，或设置 `PYTHONPATH`：

```bash
set PYTHONPATH=.  # Windows
export PYTHONPATH=.  # Linux/macOS
```

## 编写新测试

1. 在 `tests/` 目录下创建 `test_<模块名>.py` 文件
2. 测试类以 `Test` 开头，测试方法以 `test_` 开头
3. 使用 `client` fixture 调用 API
4. 使用 `admin_token` 或 `member_token` fixture 获取认证令牌
5. 每个测试应独立，不依赖其他测试的执行顺序

示例：

```python
class TestExample:
    def test_something(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/some/endpoint", headers=headers)
        assert response.status_code == 200
        assert "data" in response.json()
```

## 配置文件

`pytest.ini` 配置说明：

```ini
[pytest]
testpaths = tests              # 测试目录
python_files = test_*.py       # 测试文件匹配模式
python_classes = Test*         # 测试类匹配模式
python_functions = test_*      # 测试函数匹配模式
addopts = -v --tb=short --strict-markers --cov=app --cov-report=term-missing
```

默认启用了覆盖率统计，如需禁用可使用 `--no-cov` 参数。
