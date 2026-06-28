"""物料与研发BOM管理模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    spec = Column(String(500), nullable=True)  # 规格型号
    material_type = Column(String(32), nullable=False, index=True)
    # raw_material / component / semi_finished / finished / auxiliary

    unit = Column(String(16), default="个")  # 单位：个/米/千克/套
    category = Column(String(100), nullable=True)  # 分类：电子料/结构件/包材
    supplier = Column(String(200), nullable=True)
    brand = Column(String(100), nullable=True)

    status = Column(String(32), default="active")
    # active / inactive / pending

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bom_items = relationship("BomItem", back_populates="material")
    creator = relationship("app.models.user.User", foreign_keys=[created_by])


class BomHeader(Base):
    __tablename__ = "bom_headers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    version = Column(String(20), default="V1.0")
    status = Column(String(32), default="draft")
    # draft -> review -> released -> archived / obsolete

    product_code = Column(String(64), nullable=True)  # 关联产品编码
    remark = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("BomItem", back_populates="bom", cascade="all, delete-orphan")
    change_logs = relationship("BomChange", back_populates="bom", cascade="all, delete-orphan")
    creator = relationship("app.models.user.User", foreign_keys=[created_by])
    approver = relationship("app.models.user.User", foreign_keys=[approved_by])


class BomItem(Base):
    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bom_headers.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)

    line_no = Column(Integer, default=1)  # 行号
    quantity = Column(String(50), nullable=False)  # 用量（支持分数/表达式）
    unit = Column(String(16), nullable=True)
    loss_rate = Column(String(20), default="0")  # 损耗率
    level = Column(Integer, default=1)  # BOM层级
    parent_item_id = Column(Integer, ForeignKey("bom_items.id"), nullable=True)  # 父项

    remark = Column(String(500), nullable=True)
    is_key = Column(Boolean, default=False)  # 是否关键物料

    created_at = Column(DateTime, default=datetime.utcnow)

    bom = relationship("BomHeader", back_populates="items")
    material = relationship("Material", back_populates="bom_items")


class BomChange(Base):
    __tablename__ = "bom_changes"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bom_headers.id"), nullable=False, index=True)
    change_type = Column(String(32), nullable=False)
    # ECR / ECN / manual

    change_no = Column(String(64), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    reason = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    status = Column(String(32), default="draft")
    # draft -> review -> approved -> implemented / rejected

    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    implemented_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bom = relationship("BomHeader", back_populates="change_logs")
