"""样品与试产管理模型"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    sample_no = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    version = Column(String(20), default="V1.0")
    status = Column(String(32), default="draft")
    # draft -> making -> testing -> passed / failed / rework

    sample_type = Column(String(32), default="development")
    # development / verification / pre_production

    quantity = Column(Integer, default=1)
    maker_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    plan_finish = Column(Date, nullable=True)
    actual_finish = Column(Date, nullable=True)

    test_result = Column(String(32), nullable=True)
    # pending / pass / fail / conditional_pass

    remark = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("app.models.project.Project", back_populates="samples")
    inspections = relationship("SampleInspection", back_populates="sample", cascade="all, delete-orphan")


class SampleInspection(Base):
    __tablename__ = "sample_inspections"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False, index=True)

    inspect_no = Column(String(64), unique=True, nullable=False)
    inspect_type = Column(String(32), nullable=False)
    # dimension / performance / appearance / reliability / full

    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspected_at = Column(Date, nullable=True)

    result = Column(String(32), nullable=True)
    # pass / fail / conditional

    dimension_data = Column(JSON, nullable=True)   # 尺寸检测数据
    performance_data = Column(JSON, nullable=True)  # 性能检测数据
    appearance_desc = Column(Text, nullable=True)   # 外观检查描述

    failure_desc = Column(Text, nullable=True)  # 不合格描述
    disposition = Column(String(32), nullable=True)
    # accept / rework / scrap / use_as_is

    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sample = relationship("Sample", back_populates="inspections")
    items = relationship("SampleInspectionItem", back_populates="inspection", cascade="all, delete-orphan")


class SampleInspectionItem(Base):
    __tablename__ = "sample_inspection_items"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("sample_inspections.id"), nullable=False, index=True)

    item_name = Column(String(200), nullable=False)  # 检测项目
    standard = Column(String(500), nullable=True)     # 标准要求
    actual_value = Column(String(200), nullable=True) # 实测值
    unit = Column(String(32), nullable=True)
    is_pass = Column(Boolean, nullable=True)

    remark = Column(String(500), nullable=True)

    inspection = relationship("SampleInspection", back_populates="items")


class TrialProduction(Base):
    __tablename__ = "trial_productions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    trial_no = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)

    bom_id = Column(Integer, ForeignKey("bom_headers.id"), nullable=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=True)

    status = Column(String(32), default="planned")
    # planned -> in_progress -> completed / aborted

    plan_qty = Column(Integer, default=0)
    actual_qty = Column(Integer, default=0)
    pass_qty = Column(Integer, default=0)
    fail_qty = Column(Integer, default=0)

    plan_start = Column(Date, nullable=True)
    plan_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)

    workshop = Column(String(100), nullable=True)
    line_no = Column(String(50), nullable=True)
    foreman_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    process_params = Column(JSON, nullable=True)  # 工艺参数记录
    issue_desc = Column(Text, nullable=True)      # 试产问题记录

    yield_rate = Column(Float, nullable=True)      # 良率
    conclusion = Column(String(32), nullable=True)
    # ready_for_mass / need_improvement / fail

    remark = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
