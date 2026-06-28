"""物料与BOM管理 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.schemas.common import PaginationParams


# ===== Material =====
class MaterialBase(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=200)
    spec: Optional[str] = None
    material_type: Optional[str] = Field(default="raw_material", max_length=32)
    unit: str = Field(default="个", max_length=16)
    category: Optional[str] = Field(None, max_length=100)
    supplier: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="active", max_length=32)


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    brand: Optional[str] = None
    status: Optional[str] = None


class MaterialOut(MaterialBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== BomHeader =====
class BomItemBase(BaseModel):
    material_id: int
    line_no: int = 1
    quantity: str = Field(..., max_length=50)
    unit: Optional[str] = Field(None, max_length=16)
    loss_rate: str = Field(default="0", max_length=20)
    level: int = 1
    parent_item_id: Optional[int] = None
    remark: Optional[str] = None
    is_key: bool = False


class BomHeaderBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    version: str = Field(default="V1.0", max_length=20)
    status: str = Field(default="draft", max_length=32)
    product_code: Optional[str] = Field(None, max_length=64)
    remark: Optional[str] = None
    items: Optional[List[BomItemBase]] = None


class BomHeaderCreate(BomHeaderBase):
    project_id: Optional[int] = None


class BomHeaderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    product_code: Optional[str] = None
    remark: Optional[str] = None


class BomItemOut(BomItemBase):
    id: int
    bom_id: int

    class Config:
        from_attributes = True


class BomHeaderOut(BomHeaderBase):
    id: int
    code: str
    project_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[BomItemOut] = []

    class Config:
        from_attributes = True


# ===== BomItem 独立操作 =====
class BomItemCreate(BaseModel):
    material_id: int
    line_no: int = 1
    quantity: str = Field(..., max_length=50)
    unit: Optional[str] = Field(None, max_length=16)
    loss_rate: str = Field(default="0", max_length=20)
    level: int = 1
    parent_item_id: Optional[int] = None
    remark: Optional[str] = None
    is_key: bool = False


class BomItemUpdate(BaseModel):
    material_id: Optional[int] = None
    line_no: Optional[int] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    loss_rate: Optional[str] = None
    level: Optional[int] = None
    parent_item_id: Optional[int] = None
    remark: Optional[str] = None
    is_key: Optional[bool] = None


class BomItemBatchDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1)


class MaterialBatchDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1)
    reason: Optional[str] = None


# ===== BomChange =====
class BomChangeBase(BaseModel):
    change_type: str = Field(..., max_length=32)
    title: str = Field(..., max_length=200)
    reason: Optional[str] = None
    description: Optional[str] = None


class BomChangeCreate(BomChangeBase):
    bom_id: int


class BomChangeUpdate(BaseModel):
    status: Optional[str] = None
    reviewer_id: Optional[int] = None
    reason: Optional[str] = None
    description: Optional[str] = None


class BomChangeOut(BomChangeBase):
    id: int
    bom_id: int
    change_no: str
    status: str
    applicant_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    implemented_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== 查询 =====
class MaterialQuery(PaginationParams):
    material_type: Optional[str] = None
    keyword: Optional[str] = None
    status: Optional[str] = None


class BomQuery(PaginationParams):
    project_id: Optional[int] = None
    status: Optional[str] = None
    keyword: Optional[str] = None


class BomChangeQuery(PaginationParams):
    bom_id: Optional[int] = None
    change_type: Optional[str] = None
    status: Optional[str] = None
    keyword: Optional[str] = None
