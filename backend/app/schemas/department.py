"""部门管理 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    parent_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentTreeOut(DepartmentOut):
    children: List["DepartmentTreeOut"] = []
