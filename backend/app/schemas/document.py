"""文档与知识管理 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.schemas.common import PaginationParams


# ===== Document =====
class DocumentBase(BaseModel):
    title: str = Field(..., max_length=200)
    doc_type: Optional[str] = Field(default="design", max_length=32)
    category_id: Optional[int] = None
    project_id: Optional[int] = None
    summary: Optional[str] = None
    tags: Optional[List[str] | str] = None
    status: str = Field(default="draft", max_length=32)


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    doc_type: Optional[str] = None
    category_id: Optional[int] = None
    project_id: Optional[int] = None
    summary: Optional[str] = None
    tags: Optional[List[str] | str] = None
    status: Optional[str] = None


class DocumentOut(DocumentBase):
    id: int
    code: str
    current_version: str
    source_module: Optional[str] = "document"
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== DocumentVersion =====
class DocumentVersionOut(BaseModel):
    id: int
    document_id: int
    version: str
    file_name: str
    file_size: int = 0
    mime_type: Optional[str] = None
    changelog: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ===== DocumentApproval =====
class DocumentApprovalOut(BaseModel):
    id: int
    document_id: int
    step: int
    step_name: Optional[str] = None
    status: str
    comment: Optional[str] = None
    signed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== DocCategory =====
class DocCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    parent_id: Optional[int] = None
    sort_order: int = 0


class DocCategoryCreate(DocCategoryBase):
    pass


class DocCategoryOut(DocCategoryBase):
    id: int

    class Config:
        from_attributes = True


# ===== KnowledgeArticle =====
class KnowledgeArticleBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str] | str] = None
    is_published: bool = False


class KnowledgeArticleCreate(KnowledgeArticleBase):
    pass


class KnowledgeArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None


class KnowledgeArticleOut(KnowledgeArticleBase):
    id: int
    view_count: int = 0
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== 查询 =====
class DocumentQuery(PaginationParams):
    doc_type: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[int] = None
    keyword: Optional[str] = None
    source_module: Optional[str] = None


class KnowledgeQuery(PaginationParams):
    """知识库查询参数（返回 Document 列表）"""
    doc_type: Optional[str] = None       # 按文档类型筛选
    source_module: Optional[str] = None   # document / experiment / None=全部
    category: Optional[str] = None        # 兼容前端，映射到 doc_type
    keyword: Optional[str] = None
    created_from: Optional[str] = None  # 开始日期 YYYY-MM-DD
    created_to: Optional[str] = None      # 结束日期 YYYY-MM-DD
