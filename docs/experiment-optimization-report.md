# 研发试验模块优化建议报告

> 审查日期：2026-06-28 | 范围：后端 API + 数据模型 + 前端 Vue 组件

---

## 总览

| 类别 | 问题数 | 严重 | 中等 | 建议 |
|------|--------|------|------|------|
| 架构 | 2 | 1 | 1 | 0 |
| 后端 | 7 | 2 | 3 | 2 |
| 前端 | 8 | 3 | 3 | 2 |
| 数据 | 3 | 1 | 2 | 0 |
| 体验 | 4 | 0 | 2 | 2 |

**共计 24 项改进建议，其中 7 项需立即处理。**

---

## 一、架构层面

### 1.1 【严重】无独立 Service 层，路由文件臃肿

**现状：** `experiments.py` 674 行，所有业务逻辑（校验、状态机、文件处理、日期维护、Excel 导出）全部内联在路由函数中。

**问题：**
- 路由层耦合业务逻辑，无法独立测试
- 代码复用困难（如状态流转逻辑在其他模块无法调用）
- 新增功能时路由文件持续膨胀

**建议：** 拆分 Service 层：

```
backend/app/
  services/
    experiment_service.py    # 实验 CRUD + 状态机 + 权限校验
    record_service.py         # 记录 CRUD + 日期维护 + 批量操作
    attachment_service.py     # 附件上传/下载/校验/清理
    export_service.py         # Excel 导出逻辑
```

```python
# 示例：experiment_service.py
class ExperimentService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ExperimentCreate, user: User) -> Experiment:
        """创建实验，自动生成编码"""
        ...

    def change_status(self, exp: Experiment, action: str) -> Experiment:
        """状态流转：draft → in_progress → completed/cancelled"""
        ...

    def check_access(self, exp: Experiment, user: User) -> bool:
        """数据隔离校验"""
        ...
```

路由函数变为薄层：

```python
@router.post("/create")
def create_experiment(
    data: ExperimentCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    _: bool = Depends(require_permission("experiment", "create")),
):
    svc = ExperimentService(db)
    return success_response(data=svc.create(data, current))
```

### 1.2 【中等】前端组件过大，ExperimentList.vue 2336 行

**问题：**
- 单文件 2336 行，包含 9 个对话框 + 筛选 + 表格 + 所有业务逻辑
- 任何一个子功能的修改都可能影响整个文件
- 新开发者难以理解

**建议：** 拆分为独立组件：

```
src/views/experiment/
  ExperimentList.vue              # 主列表页（~300行）
  components/
    ExperimentTable.vue            # 实验列表表格
    ExperimentFilter.vue           # 筛选栏
    ExperimentFormDialog.vue       # 新建/编辑实验对话框
    RecordManageDialog.vue         # 记录管理对话框（~300行）
    RecordFormDialog.vue           # 记录表单对话框（~400行）
    RecordPreviewDialog.vue        # 记录预览对话框
    AecqTestSection.vue            # AEC-Q200 测试区域
    CustomTestSection.vue          # 自定义测试项区域
    CustomTestManager.vue          # 自定义测试项管理
  composables/
    useExperimentList.ts           # 实验列表逻辑
    useExperimentForm.ts           # 实验表单逻辑
    useRecordManage.ts             # 记录管理逻辑
    useRecordForm.ts               # 记录表单逻辑
    useAecqTest.ts                 # AEC-Q200 逻辑
    useCustomTest.ts               # 自定义测试项逻辑
```

---

## 二、后端优化

### 2.1 【严重】迁移文件使用 `Base.metadata.create_all()` 而非显式 DDL

**现状：** `b1aeef9c142d_initial_migration.py` 直接用 `Base.metadata.create_all()` 建表。

**问题：**
- 无法追踪表结构的精确变更历史
- 后期添加索引、约束、字段时，`autogenerate` 可能产生意外差异
- 生产环境回滚困难

**建议：** 生成新的显式迁移：

```bash
alembic revision --autogenerate -m "explicit_table_definitions"
```

这会让 Alembic 解析当前模型状态并生成显式的 `create_table()` / `add_column()` 语句。

### 2.2 【严重】附件上传路径存在目录遍历风险（低概率）

**现状：** 附件路径由前端上传文件名拼接，虽然后端有扩展名白名单，但未对文件名做规范化处理。

```python
# 当前代码
file_path = os.path.join(UPLOAD_DIR, f"experiment_{record_id}", file.filename)
```

**问题：** 如果攻击者构造 `../../../etc/passwd` 类文件名（虽然前端不太可能），路径拼接可能越界。

**建议：**

```python
import os
from werkzeug.utils import secure_filename

safe_name = secure_filename(file.filename)  # 移除路径分隔符等危险字符
file_path = os.path.join(UPLOAD_DIR, f"experiment_{record_id}", safe_name)
# 二次校验：确保最终路径在 UPLOAD_DIR 内
real_path = os.path.realpath(file_path)
if not real_path.startswith(os.path.realpath(UPLOAD_DIR)):
    raise ValueError("Invalid file path")
```

### 2.3 【中等】批量删除缺少事务原子性保证

**现状：** `batch_delete_records` 逐条删除记录，若中间某条失败，前面已删的不会回滚。

**建议：** 使用 `savepoint` 或整体 try/except + rollback：

```python
@router.post("/records/batch-delete")
def batch_delete_records(data: BatchDeleteRecords, db: Session = Depends(get_db), ...):
    try:
        records = db.query(ExperimentRecord).filter(
            ExperimentRecord.id.in_(data.ids)
        ).all()
        if len(records) != len(data.ids):
            raise HTTPException(400, "部分记录不存在")
        for r in records:
            db.delete(r)
        db.commit()
    except Exception:
        db.rollback()
        raise
```

### 2.4 【中等】Excel 导出缺少数据量限制

**现状：** `export_records` 直接导出指定实验的全部记录，无行数上限。

**问题：** 单次实验可能积累上万条记录，导出可能超时或 OOM。

**建议：** 添加行数上限（如 10000 条），超限时提示用户分批导出。

### 2.5 【中等】缺少实验记录操作日志

**现状：** 实验记录的创建/编辑/删除未写入 `operation_logs` 表。

**建议：** 关键操作（记录创建、结论变更、异常标记、状态流转）记录审计日志。

### 2.6 【建议】参数模板 JSON 无 Schema 校验

**现状：** `param_template` 字段为自由格式 JSON，只在 Pydantic schema 定义了 `List[ParamTemplateItem]`，但数据库层面无约束。

**建议：** 在 Service 层添加 JSON Schema 校验：

```python
PARAM_TEMPLATE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string", "maxLength": 50},
            "unit": {"type": "string", "maxLength": 20},
            "default": {"type": "number"},
            "min": {"type": "number"},
            "max": {"type": "number"},
        }
    }
}
```

### 2.7 【建议】缺少实验编号的数据库级唯一索引

**现状：** `code` 字段标记了 `unique=True`，SQLAlchemy 已创建唯一索引。确认无误。但如果未来改用 MySQL，需要确保 `code` 列的排序规则与索引兼容。

---

## 三、前端优化

### 3.1 【严重】记录表单中 AEC-Q200 / 自定义 / 通用三种模式耦合在同一组件

**现状：** `ExperimentList.vue` 的记录表单（`showRecordForm`）将三种模式的所有字段、校验、交互逻辑揉在一起，通过 `recordMode` ref 做分支。

**问题：**
- 新增第四种模式时需要改动整个表单逻辑
- 字段冲突风险（如 AEC-Q200 的 `samples` 和自定义的 `samples` 虽然同名但结构不同）
- 表单校验逻辑分散在多处

**建议：** 拆分为三个独立子组件，通过动态组件切换：

```vue
<template>
  <component
    :is="recordModeComponent"
    v-model="recordForm"
    :experiment="experiment"
  />
</template>

<script setup>
const recordModeComponent = computed(() => {
  switch (recordMode.value) {
    case 'aecq': return AecqRecordForm
    case 'custom': return CustomRecordForm
    case 'normal': return NormalRecordForm
  }
})
</script>
```

### 3.2 【严重】ECharts 未做实例清理，存在内存泄漏风险

**现状：** `TcrTestView.vue` 和 `TempRiseTestView.vue` 中 ECharts 实例在图表更新时没有调用 `dispose()`，组件卸载时也没有清理。

**建议：**

```typescript
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (chartInstance) chartInstance.dispose()
  const dom = chartRef.value
  if (!dom) return
  chartInstance = echarts.init(dom)
  chartInstance.setOption({...})
}

onUnmounted(() => {
  chartInstance?.dispose()
  window.removeEventListener('resize', handleResize)
})
```

### 3.3 【中等】大量使用 `any` 类型，失去 TypeScript 优势

**现状：** API 调用参数和返回值大量使用 `any`：

```typescript
// 当前
export const experimentApi = {
  list: (params: any) => request.get('/experiments/list', { params }),
  create: (data: any) => request.post('/experiments/create', data),
  ...
}
```

**建议：** 使用 `types/experiment.ts` 中已有的类型：

```typescript
list: (params: ExperimentQuery) =>
  request.get<PaginatedResponse<ExperimentOut>>('/experiments/list', { params }),
create: (data: ExperimentCreate) =>
  request.post<ExperimentOut>('/experiments/create', data),
```

### 3.4 【中等】自定义测试项存 localStorage 不跨设备

**现状：** 自定义测试项定义存储在 `localStorage`，换设备后丢失，无法团队共享。

**建议：** 短期保持 localStorage（快速迭代），中长期增加后端 API 支持团队共享：

```python
# 新增表
class CustomTestTemplate(Base):
    __tablename__ = "custom_test_templates"
    id, name, description, params_schema, columns_schema, judge_rule
    created_by, is_public, team_id, ...
```

### 3.5 【中等】温漂/温升测试页无自动保存/草稿功能

**现状：** 用户在专用测试页录入大量数据后，不小心关闭页面则数据全部丢失。

**建议：**

```typescript
// 使用 useLocalStorage + 防抖自动保存
const draftKey = `tcr_draft_${experimentId}`
const form = useLocalStorage(draftKey, defaultForm)

watch(form, debounce(() => {
  // 自动保存到 localStorage
}, 2000))
```

### 3.6 【建议】缺少批量导入记录功能

**现状：** 只能逐条新增记录或手动在专用测试页逐行录入。

**建议：** 添加 Excel 导入功能：

- 上传 Excel → 解析 → 预览 → 确认导入
- 支持温漂/温升/通用记录三种格式
- 错误行高亮标记，允许跳过或全部回滚

### 3.7 【建议】temperature 单位显示不一致

**现状：** 部分地方用中文 "°C"（温漂页），部分用英文 "C"（数据库存储）。

**建议：** 统一用 `℃` 或保持数据库存数字 + 前端统一格式化。

### 3.8 【严重】状态常量不一致

**现状：** `constants/status.ts` 中使用 `active`，而 `types/experiment.ts` 和后端使用 `in_progress`。

```typescript
// constants/status.ts（旧）
EXPERIMENT_STATUS = {
  active: { tag: 'primary', label: '进行中' },
}

// types/experiment.ts（新）
ExperimentStatus = 'draft' | 'in_progress' | 'completed' | 'cancelled'
```

**建议：** 删除 `constants/status.ts` 中的旧定义，统一使用 `types/experiment.ts` 中的常量。

---

## 四、数据模型优化

### 4.1 【严重】缺少实验编号格式的可配置性

**现状：** 实验编号硬编码为 `EXP{时间戳}`（`EXP1700000000`），无法体现项目/年份/类型信息。

**建议：**

```python
# 可配置编码规则
CODE_FORMAT = {
    "pattern": "{PROJECT_CODE}-{TYPE}-{YYYY}{MM}-{SEQ:04d}",
    # 示例: PRJ01-TCR-202606-0001
}

def generate_experiment_code(db, project, exp_type):
    seq = get_next_sequence(db, project.id, exp_type)
    return f"{project.code}-{TYPE_ABBR[exp_type]}-{date:%Y%m}-{seq:04d}"
```

### 4.2 【中等】`experiment_records` 表缺少 `test_type` 字段

**现状：** 记录的测试类型（温漂/温升/AEC-Q200/自定义/常规）通过 `param_values.test_type` JSON 字段隐式推断，查询和筛选效率低。

**建议：** 添加独立列：

```python
test_type = Column(String(32), nullable=True, index=True,
    comment="测试类型: tcr / temp_rise / aecq200 / custom / normal")
```

并建立数据库迁移：`alembic revision -m "add_test_type_to_records"`

### 4.3 【中等】附件表缺少 hash 去重

**现状：** 同一文件可能被多次上传到不同记录，占用重复存储空间。

**建议：**

```python
file_hash = Column(String(64), nullable=True, index=True,
    comment="SHA-256 文件哈希，用于去重")
```

上传时先算 hash，已有相同文件则直接复用路径。

---

## 五、用户体验优化

### 5.1 实验列表增加甘特图/时间线视图

当前只有表格视图，缺乏时间维度可视化。建议添加甘特图模式，用计划开始/结束时间直观展示实验排期。

### 5.2 记录管理增加批量编辑功能

当前只能逐条编辑记录。对于同时更正多条记录的 "执行人"、"执行日期" 等字段，批量编辑可大幅提升效率。

### 5.3 温漂/温升测试页增加模板保存功能

用户在专用测试页配置的采样参数（温度范围、间隔、参考值）应支持保存为模板，下次同类型实验一键加载。

### 5.4 实验流转增加审批机制（远期规划）

当前状态流转无审批环节。
- `draft → in_progress`：需设计人确认
- `in_progress → completed`：需主管审核
- 可先预留 `approved_by`、`approved_at` 字段，后续接入工作流引擎。

---

## 六、实施优先级

### 第一优先级（立即处理，影响稳定性）

| # | 问题 | 影响 |
|---|------|------|
| 3.1 | 记录表单模式耦合 | 新增功能困难，维护成本高 |
| 3.2 | ECharts 内存泄漏 | 长时间使用导致页面卡顿 |
| 3.8 | 状态常量不一致 | 可能导致状态显示异常 |

### 第二优先级（短期优化，提升质量）

| # | 问题 | 影响 |
|---|------|------|
| 1.1 | 无 Service 层 | 代码可测试性差 |
| 1.2 | 组件过大 | 维护困难 |
| 2.1 | 迁移文件问题 | 数据库变更不可追溯 |
| 2.3 | 批量删除无事务 | 数据不一致风险 |
| 3.3 | any 类型滥用 | 类型安全缺失 |
| 4.1 | 编码格式固化 | 可读性差 |
| 4.2 | 缺 test_type 字段 | 查询效率低 |

### 第三优先级（中期规划，完善功能）

| # | 问题 |
|---|------|
| 2.5 | 操作日志 |
| 2.6 | 参数 JSON Schema |
| 3.4 | 自定义测试项云端存储 |
| 3.5 | 自动保存草稿 |
| 3.6 | 批量导入 |
| 4.3 | 附件去重 |
| 5.1-5.3 | UX 增强 |

---

> 本报告基于 2026-06-28 代码审查生成。建议每季度重新审查一次。
