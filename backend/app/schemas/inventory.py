"""库存管理 Pydantic Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


# ===== InventoryItem =====
class InventoryItemBase(BaseModel):
    material_id: int
    warehouse: str = Field(..., max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    quantity: float = 0.0
    reserved_qty: float = 0.0
    safety_stock: float = 0.0
    max_stock: float = 0.0
    unit: Optional[str] = Field(None, max_length=20)
    shelf_life_days: Optional[int] = None
    expiry_date: Optional[date] = None
    remark: Optional[str] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    warehouse: Optional[str] = None
    location: Optional[str] = None
    safety_stock: Optional[float] = None
    max_stock: Optional[float] = None
    unit: Optional[str] = None
    shelf_life_days: Optional[int] = None
    expiry_date: Optional[date] = None
    remark: Optional[str] = None


class InventoryItemOut(InventoryItemBase):
    id: int
    status: str = "normal"
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_spec: Optional[str] = None
    material_type: Optional[str] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryItemQuery(BaseModel):
    """库存查询参数"""
    keyword: Optional[str] = None  # 物料编码/名称
    warehouse: Optional[str] = None
    status: Optional[str] = None  # normal/low_stock/out_of_stock/expired
    material_type: Optional[str] = None
    low_stock_only: Optional[bool] = None  # 仅显示低库存
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    @property
    def offset(self):
        return (self.page - 1) * self.page_size

    @property
    def limit(self):
        return self.page_size


# ===== InventoryTransaction =====
class InventoryTransactionCreate(BaseModel):
    """创建交易记录"""
    inventory_item_id: int
    transaction_type: str = Field(..., max_length=32)
    quantity: float = Field(..., description="正数=入库, 负数=出库")
    source_warehouse: Optional[str] = None
    target_warehouse: Optional[str] = None
    related_project_id: Optional[int] = None
    related_department_id: Optional[int] = None
    borrower_id: Optional[int] = None
    borrower_name: Optional[str] = None
    expected_return_date: Optional[date] = None
    approval_required: Optional[bool] = False
    remark: Optional[str] = None


class InventoryTransactionOut(BaseModel):
    id: int
    transaction_no: str
    inventory_item_id: int
    transaction_type: str
    quantity: float
    before_qty: float
    after_qty: float
    source_warehouse: Optional[str] = None
    target_warehouse: Optional[str] = None
    related_project_id: Optional[int] = None
    related_project_name: Optional[str] = None
    related_department_id: Optional[int] = None
    related_department_name: Optional[str] = None
    operator_id: int
    operator_name: Optional[str] = None
    borrower_id: Optional[int] = None
    borrower_name: Optional[str] = None
    expected_return_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    approval_status: str = "completed"
    remark: Optional[str] = None
    created_at: datetime
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    warehouse: Optional[str] = None
    unit: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionQuery(BaseModel):
    """交易记录查询"""
    inventory_item_id: Optional[int] = None
    transaction_type: Optional[str] = None
    approval_status: Optional[str] = None
    related_project_id: Optional[int] = None
    keyword: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    @property
    def offset(self):
        return (self.page - 1) * self.page_size

    @property
    def limit(self):
        return self.page_size


# ===== Approval =====
class ApprovalCreate(BaseModel):
    transaction_id: int
    approval_level: int = 1
    approver_id: int
    approver_name: str


class ApprovalAction(BaseModel):
    """审批操作"""
    status: str = Field(..., description="approved/rejected")
    comment: Optional[str] = None


class ApprovalOut(BaseModel):
    id: int
    transaction_id: int
    approval_level: int
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    status: str
    comment: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Alert =====
class AlertOut(BaseModel):
    id: int
    inventory_item_id: int
    alert_type: str
    message: str
    is_read: int
    is_resolved: int
    created_at: datetime
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    warehouse: Optional[str] = None

    class Config:
        from_attributes = True


# ===== Statistics =====
class InventoryStatsOut(BaseModel):
    """库存统计"""
    total_items: int = 0
    total_quantity: float = 0.0
    normal_count: int = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    expired_count: int = 0
    total_value_estimate: float = 0.0


class WarehouseStatsOut(BaseModel):
    """仓库维度统计"""
    warehouse: str
    item_count: int = 0
    total_quantity: float = 0.0
    low_stock_count: int = 0


class TurnoverReport(BaseModel):
    """周转分析"""
    material_code: str = ""
    material_name: str = ""
    warehouse: str = ""
    period_in: float = 0.0   # 期间入库
    period_out: float = 0.0   # 期间出库
    begin_qty: float = 0.0    # 期初
    end_qty: float = 0.0      # 期末
    avg_qty: float = 0.0      # 平均库存
    turnover_rate: float = 0.0  # 周转率


# ===== 批量入库 =====
class BatchInboundCreate(BaseModel):
    """批量入库"""
    items: list[InventoryItemCreate]


# ===== Warehouse =====
class WarehouseCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    location: Optional[str] = None
    manager: Optional[str] = None
    contact: Optional[str] = None
    is_active: bool = True
    remark: Optional[str] = None


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    manager: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class WarehouseOut(BaseModel):
    id: int
    name: str
    code: str
    location: Optional[str] = None
    manager: Optional[str] = None
    contact: Optional[str] = None
    is_active: bool = True
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
