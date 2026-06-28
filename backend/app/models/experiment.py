"""研发实验管理模型"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # 实验类型：工艺验证 / 性能测试 / 材料试验 / 可靠性测试
    exp_type = Column(String(32), nullable=False)
    status = Column(String(32), default="draft")
    # draft -> planned -> running -> completed / cancelled

    designer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    plan_start = Column(Date, nullable=True)
    plan_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)

    # 实验参数模版（JSON 存储）
    param_template = Column(JSON, nullable=True)
    # 示例: [{"name": "温度", "unit": "℃", "default": 180}]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("app.models.project.Project", back_populates="experiments")
    records = relationship("ExperimentRecord", back_populates="experiment", cascade="all, delete-orphan")
    designer = relationship("app.models.user.User", foreign_keys=[designer_id])
    executor = relationship("app.models.user.User", foreign_keys=[executor_id])


class ExperimentRecord(Base):
    __tablename__ = "experiment_records"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False, index=True)

    batch_no = Column(String(50), nullable=True)  # 批次号
    sample_code = Column(String(50), nullable=True)  # 样品编号
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 实验参数值（JSON 存储）
    param_values = Column(JSON, nullable=True)
    # 示例: {"温度": 185, "压力": 12.5, "时间": 30}

    # 实验结果
    result_data = Column(JSON, nullable=True)  # 测试数据
    result_summary = Column(Text, nullable=True)
    conclusion = Column(String(32), nullable=True)
    # 结论: pass / fail / conditional_pass / need_retest

    # SPC 指标
    cpk = Column(Float, nullable=True)
    mean_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)

    is_abnormal = Column(Boolean, default=False)
    abnormal_desc = Column(Text, nullable=True)

    executed_at = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="records")
    attachments = relationship("ExperimentAttachment", back_populates="record", cascade="all, delete-orphan")


class ExperimentAttachment(Base):
    __tablename__ = "experiment_attachments"

    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("experiment_records.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    record = relationship("ExperimentRecord", back_populates="attachments")
