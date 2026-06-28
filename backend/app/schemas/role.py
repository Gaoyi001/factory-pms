"""角色与权限 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ---------- 权限 ----------
class PermissionBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=100)
    resource: str
    action: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionOut(PermissionBase):
    id: int

    class Config:
        from_attributes = True


# ---------- 角色 ----------
class RoleBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    is_active: bool = True
    sort_order: int = 0


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class RoleOut(RoleBase):
    id: int
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True


# ---------- 操作日志 ----------
class OperationLogQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    resource_id: Optional[int] = None
    keyword: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class OperationLogOut(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    resource: str
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    ip_address: Optional[str] = None
    detail: Optional[str] = None
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    is_file_download: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogBatchDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1, max_length=1000)
    """批量删除的日志ID列表（最多1000条）"""


class OperationLogCleanup(BaseModel):
    retention_days: int = Field(default=90, ge=7, le=365)
    """保留天数（7-365天，默认90天）"""
