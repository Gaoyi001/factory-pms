"""样品与试产管理 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from app.schemas.common import PaginationParams


# ===== Sample =====
class SampleBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    version: str = Field(default="V1.0", max_length=20)
    status: str = Field(default="draft", max_length=32)
    sample_type: str = Field(default="development", max_length=32)
    quantity: int = 1
    maker_id: Optional[int] = None
    inspector_id: Optional[int] = None
    plan_finish: Optional[date] = None
    test_result: Optional[str] = Field(None, max_length=32)
    remark: Optional[str] = None


class SampleCreate(SampleBase):
    project_id: int


class SampleUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    test_result: Optional[str] = None
    actual_finish: Optional[date] = None
    remark: Optional[str] = None


class SampleOut(SampleBase):
    id: int
    project_id: int
    sample_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== SampleInspection =====
class InspectionItemBase(BaseModel):
    item_name: str = Field(..., max_length=200)
    standard: Optional[str] = None
    actual_value: Optional[str] = None
    unit: Optional[str] = None
    is_pass: Optional[bool] = None
    remark: Optional[str] = None


class SampleInspectionBase(BaseModel):
    inspect_type: str = Field(..., max_length=32)
    inspector_id: Optional[int] = None
    inspected_at: Optional[date] = None
    result: Optional[str] = Field(None, max_length=32)
    dimension_data: Optional[dict] = None
    performance_data: Optional[dict] = None
    appearance_desc: Optional[str] = None
    failure_desc: Optional[str] = None
    disposition: Optional[str] = Field(None, max_length=32)
    remark: Optional[str] = None
    items: Optional[List[InspectionItemBase]] = None


class SampleInspectionCreate(SampleInspectionBase):
    sample_id: int


class SampleInspectionOut(SampleInspectionBase):
    id: int
    sample_id: int
    inspect_no: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== TrialProduction =====
class TrialProductionBase(BaseModel):
    name: str = Field(..., max_length=200)
    bom_id: Optional[int] = None
    sample_id: Optional[int] = None
    status: str = Field(default="planned", max_length=32)
    plan_qty: int = 0
    workshop: Optional[str] = None
    line_no: Optional[str] = None
    foreman_id: Optional[int] = None
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None
    process_params: Optional[dict] = None


class TrialProductionCreate(TrialProductionBase):
    project_id: int


class TrialProductionUpdate(BaseModel):
    status: Optional[str] = None
    actual_qty: Optional[int] = None
    pass_qty: Optional[int] = None
    fail_qty: Optional[int] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    yield_rate: Optional[float] = None
    conclusion: Optional[str] = None
    issue_desc: Optional[str] = None


class TrialProductionOut(TrialProductionBase):
    id: int
    project_id: int
    trial_no: str
    actual_qty: int = 0
    pass_qty: int = 0
    fail_qty: int = 0
    yield_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== 查询 =====
class SampleQuery(PaginationParams):
    project_id: Optional[int] = None
    status: Optional[str] = None
    sample_type: Optional[str] = None
    keyword: Optional[str] = None


class TrialQuery(PaginationParams):
    project_id: Optional[int] = None
    status: Optional[str] = None
