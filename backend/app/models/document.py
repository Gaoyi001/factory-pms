"""文档与知识管理模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    doc_type = Column(String(32), nullable=False, index=True)
    # design / test / process / quality / standard / other

    category_id = Column(Integer, ForeignKey("doc_categories.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)

    current_version = Column(String(20), default="V1.0")
    status = Column(String(32), default="draft")
    # draft -> review -> approved -> archived / obsolete

    tags = Column(JSON, nullable=True)  # 标签列表
    summary = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_module = Column(String(32), default="document", index=True)
    # document=来自新建文档, experiment=来自研发实验

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    approvals = relationship("DocumentApproval", back_populates="document", cascade="all, delete-orphan")
    creator = relationship("app.models.user.User", foreign_keys=[created_by])


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)

    changelog = Column(Text, nullable=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="versions")


class DocumentApproval(Base):
    __tablename__ = "document_approvals"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    step = Column(Integer, default=1)  # 审批步骤
    step_name = Column(String(100), nullable=True)  # 起草/校对/审核/批准
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(String(32), default="pending")
    # pending -> approved -> rejected

    comment = Column(Text, nullable=True)
    signed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="approvals")


class DocCategory(Base):
    __tablename__ = "doc_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("doc_categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=True)  # Markdown 内容
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)

    is_published = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("app.models.user.User")
