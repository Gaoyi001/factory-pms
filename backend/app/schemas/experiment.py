"""研发实验管理 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Any
from enum import Enum
from app.schemas.common import PaginationParams


# ===== 枚举 =====
class ExperimentStatus(str, Enum):
    DRAFT = "draft"               # 草稿
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消


class ExperimentType(str, Enum):
    PERFORMANCE = "performance"   # 性能测试
    RELIABILITY = "reliability"   # 可靠性测试
    ENVIRONMENT = "environment"   # 环境测试
    MATERIAL = "material"         # 材料试验
    PROCESS = "process"           # 工艺验证
    OTHER = "other"               # 其他


class RecordConclusion(str, Enum):
    PASS = "pass"                       # 通过
    FAIL = "fail"                       # 失败
    CONDITIONAL_PASS = "conditional_pass"  # 有条件通过
    NEED_RETEST = "need_retest"         # 需复测


# ===== 参数模板项 =====
class ParamTemplateItem(BaseModel):
    name: str = Field(..., description="参数名称")
    unit: Optional[str] = Field(None, description="单位")
    default: Optional[Any] = Field(None, description="默认值")
    min: Optional[float] = Field(None, description="下限")
    max: Optional[float] = Field(None, description="上限")


# ===== Experiment =====
class ExperimentBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    exp_type: ExperimentType = ExperimentType.PERFORMANCE
    status: ExperimentStatus = ExperimentStatus.DRAFT
    designer_id: Optional[int] = None
    executor_id: Optional[int] = None
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    param_template: Optional[List[ParamTemplateItem]] = None


class ExperimentCreate(ExperimentBase):
    project_id: int


class ExperimentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    exp_type: Optional[ExperimentType] = None
    status: Optional[ExperimentStatus] = None
    executor_id: Optional[int] = None
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    param_template: Optional[List[ParamTemplateItem]] = None


class ExperimentOut(ExperimentBase):
    id: int
    code: str
    project_id: int
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExperimentDetailOut(ExperimentOut):
    """实验详情（含展示字段）"""
    designer_name: Optional[str] = None
    executor_name: Optional[str] = None


# ===== ExperimentRecord =====
class ExperimentRecordBase(BaseModel):
    batch_no: Optional[str] = Field(None, max_length=50)
    sample_code: Optional[str] = Field(None, max_length=50)
    executor_id: Optional[int] = None
    param_values: Optional[dict] = None
    result_data: Optional[dict] = None
    result_summary: Optional[str] = None
    conclusion: Optional[RecordConclusion] = None
    is_abnormal: bool = False
    abnormal_desc: Optional[str] = None
    executed_at: Optional[date] = None


class ExperimentRecordCreate(ExperimentRecordBase):
    experiment_id: int


class ExperimentRecordUpdate(BaseModel):
    batch_no: Optional[str] = Field(None, max_length=50)
    sample_code: Optional[str] = Field(None, max_length=50)
    executor_id: Optional[int] = None
    param_values: Optional[dict] = None
    result_data: Optional[dict] = None
    result_summary: Optional[str] = None
    conclusion: Optional[RecordConclusion] = None
    is_abnormal: Optional[bool] = None
    abnormal_desc: Optional[str] = None
    executed_at: Optional[date] = None


class ExperimentRecordOut(ExperimentRecordBase):
    id: int
    experiment_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExperimentRecordDetailOut(ExperimentRecordOut):
    """记录详情（含展示字段）"""
    executor_name: Optional[str] = None
    attachment_count: int = 0
    attachments: List[Any] = []  # List[ExperimentAttachmentOut]，延迟引用避免循环


# ===== 附件 =====
class ExperimentAttachmentOut(BaseModel):
    id: int
    record_id: int
    file_name: str
    file_path: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# 修正 ExperimentRecordDetailOut.attachments 的类型
ExperimentRecordDetailOut.model_rebuild()


# ===== 状态流转动作 =====
class StatusAction(BaseModel):
    action: str = Field(..., description="start | complete | cancel")


# ===== 查询 =====
class ExperimentQuery(PaginationParams):
    project_id: Optional[int] = None
    status: Optional[ExperimentStatus] = None
    exp_type: Optional[ExperimentType] = None
    keyword: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class RecordQuery(PaginationParams):
    """实验记录查询"""
    batch_no: Optional[str] = None
    sample_code: Optional[str] = None
    conclusion: Optional[RecordConclusion] = None
    is_abnormal: Optional[bool] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class BatchDeleteRecords(BaseModel):
    """批量删除记录"""
    ids: List[int]
