"""项目管理模型"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ProjectType(Base):
    __tablename__ = "project_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    is_active = Column(Boolean, default=True)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(32), default="draft", index=True)
    # 状态: draft -> active -> on_hold -> completed / cancelled
    priority = Column(Integer, default=3)  # 1-5
    project_type_id = Column(Integer, ForeignKey("project_types.id"), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    plan_start = Column(Date, nullable=True)
    plan_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)

    progress = Column(Integer, default=0)  # 0-100
    budget = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    creator = relationship("User", foreign_keys=[created_by])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    experiments = relationship("app.models.experiment.Experiment", back_populates="project", cascade="all, delete-orphan")
    samples = relationship("app.models.sample.Sample", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(32), default="todo", index=True)
    # todo -> in_progress -> review -> done
    priority = Column(Integer, default=3)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    plan_hours = Column(Integer, default=0)
    actual_hours = Column(Integer, default=0)

    due_date = Column(Date, nullable=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    children = relationship("Task", backref="parent", remote_side=[id])


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    code = Column(String(32), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source = Column(String(32), default="internal")
    # customer / sales / internal / market
    priority = Column(String(16), default="should")
    # must / should / could / wont
    status = Column(String(32), default="draft")
    # draft -> review -> approved -> implemented -> verified / rejected
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="requirements")
