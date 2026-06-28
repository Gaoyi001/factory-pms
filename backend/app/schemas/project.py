"""项目管理 Schema"""
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, date
from typing import Optional, List
from app.schemas.common import PaginationParams


# 项目允许的状态值
VALID_PROJECT_STATUSES = {"draft", "active", "on_hold", "completed", "cancelled"}


# ===== Project =====
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="项目名称（必填）")
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field(default="draft", max_length=32)
    priority: int = Field(default=3, ge=1, le=5)
    project_type_id: Optional[int] = Field(None, gt=0)
    owner_id: Optional[int] = Field(None, gt=0)
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    budget: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_dates(self):
        """验证计划日期逻辑：开始日期不能晚于结束日期"""
        if self.plan_start and self.plan_end:
            if self.plan_start > self.plan_end:
                raise ValueError("计划开始日期不能晚于计划结束日期")
        return self

    @model_validator(mode="after")
    def validate_status(self):
        """验证状态值必须在允许范围内"""
        if self.status not in VALID_PROJECT_STATUSES:
            raise ValueError(f"无效的项目状态：{self.status}，有效值：{', '.join(sorted(VALID_PROJECT_STATUSES))}")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, max_length=32)
    priority: Optional[int] = Field(None, ge=1, le=5)
    owner_id: Optional[int] = Field(None, gt=0)
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    budget: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_status(self):
        if self.status is not None and self.status not in VALID_PROJECT_STATUSES:
            raise ValueError(f"无效的项目状态：{self.status}，有效值：{', '.join(sorted(VALID_PROJECT_STATUSES))}")
        return self


class ProjectOut(ProjectBase):
    id: int
    code: str
    created_by: int
    progress: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Task =====
class TaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    status: str = Field(default="todo", max_length=32)
    priority: int = Field(default=3, ge=1, le=5)
    assignee_id: Optional[int] = None
    plan_hours: int = 0
    due_date: Optional[date] = None
    parent_id: Optional[int] = None
    sort_order: int = 0


class TaskCreate(TaskBase):
    project_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=32)
    assignee_id: Optional[int] = None
    plan_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    due_date: Optional[date] = None
    sort_order: Optional[int] = None


class TaskOut(TaskBase):
    id: int
    project_id: int
    actual_hours: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Requirement =====
class RequirementBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    source: str = Field(default="internal", max_length=32)
    priority: str = Field(default="should", max_length=16)
    status: str = Field(default="draft", max_length=32)


class RequirementCreate(RequirementBase):
    project_id: int


class RequirementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=16)
    status: Optional[str] = Field(None, max_length=32)


class RequirementOut(RequirementBase):
    id: int
    project_id: int
    code: str
    version: int = 1
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 查询参数 =====
class ProjectQuery(PaginationParams):
    status: Optional[str] = None
    owner_id: Optional[int] = None
    keyword: Optional[str] = None


class TaskQuery(PaginationParams):
    project_id: Optional[int] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    keyword: Optional[str] = None
