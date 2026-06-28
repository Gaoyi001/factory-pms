"""研发库存管理模型"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Warehouse(Base):
    """仓库"""
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="仓库名称")
    code = Column(String(50), unique=True, nullable=False, comment="仓库编码")
    location = Column(String(200), nullable=True, comment="仓库位置")
    manager = Column(String(100), nullable=True, comment="负责人")
    contact = Column(String(50), nullable=True, comment="联系电话")
    is_active = Column(Boolean, default=True, comment="是否启用")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InventoryItem(Base):
    """库存物料 — 每个物料在每个仓库中的库存状态"""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    warehouse = Column(String(100), nullable=False, index=True, comment="仓库名称")
    location = Column(String(100), nullable=True, comment="库位编号")
    quantity = Column(Float, default=0.0, comment="当前库存数量")
    reserved_qty = Column(Float, default=0.0, comment="已预留/领用未归还数量")
    safety_stock = Column(Float, default=0.0, comment="安全库存阈值")
    max_stock = Column(Float, default=0.0, comment="最大库存阈值")
    unit = Column(String(20), nullable=True, comment="计量单位")
    status = Column(String(32), default="normal", index=True, comment="normal/low_stock/out_of_stock/expired")
    shelf_life_days = Column(Integer, nullable=True, comment="保质期（天）")
    expiry_date = Column(Date, nullable=True, comment="过期日期")
    remark = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    material = relationship("Material", lazy="joined")
    creator = relationship("app.models.user.User", foreign_keys=[created_by], lazy="joined")


class InventoryTransaction(Base):
    """库存交易记录 — 统一记录所有库存操作"""
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_no = Column(String(64), unique=True, nullable=False, index=True, comment="交易单号")
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    transaction_type = Column(
        String(32), nullable=False, index=True,
        comment="inbound/outbound/borrow/return_transfer/check/transfer_in/transfer_out/adjust"
    )
    quantity = Column(Float, nullable=False, comment="交易数量（正=入库，负=出库）")
    before_qty = Column(Float, default=0.0, comment="交易前库存")
    after_qty = Column(Float, default=0.0, comment="交易后库存")
    source_warehouse = Column(String(100), nullable=True, comment="调拨来源仓库")
    target_warehouse = Column(String(100), nullable=True, comment="调拨目标仓库")
    related_project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, comment="关联项目")
    related_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="关联部门")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="领用人")
    borrower_name = Column(String(100), nullable=True, comment="领用人姓名")
    expected_return_date = Column(Date, nullable=True, comment="预计归还日期")
    actual_return_date = Column(Date, nullable=True, comment="实际归还日期")
    approval_status = Column(String(32), default="completed", index=True, comment="pending/approved/rejected/completed")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory_item = relationship("InventoryItem", backref="transactions", lazy="joined")
    operator = relationship("app.models.user.User", foreign_keys=[operator_id], lazy="joined")
    related_project = relationship("Project", lazy="joined")
    related_department = relationship("Department", lazy="joined")


class InventoryApproval(Base):
    """库存操作审批记录"""
    __tablename__ = "inventory_approvals"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("inventory_transactions.id"), nullable=False, index=True)
    approval_level = Column(Integer, default=1, comment="审批级别 1=库管员, 2=主管")
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approver_name = Column(String(100), nullable=True, comment="审批人姓名")
    status = Column(String(32), default="pending", comment="pending/approved/rejected")
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    transaction = relationship("InventoryTransaction", backref="approvals")


class InventoryAlert(Base):
    """库存预警记录"""
    __tablename__ = "inventory_alerts"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    alert_type = Column(String(32), nullable=False, comment="low_stock/out_of_stock/expiry")
    message = Column(String(500), nullable=False)
    is_read = Column(Integer, default=0, comment="0=未读, 1=已读")
    is_resolved = Column(Integer, default=0, comment="0=未处理, 1=已处理")
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory_item = relationship("InventoryItem", backref="alerts")
