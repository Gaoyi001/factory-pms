"""文档与知识管理 API——重构版
知识库统一展示所有含文件的文档（来自"新建文档"和"研发实验"两个入口）
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from urllib.parse import quote
from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.document import Document, DocumentVersion, DocumentApproval, DocCategory, KnowledgeArticle
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentOut,
    DocumentVersionOut, DocumentApprovalOut,
    DocCategoryCreate, DocCategoryOut,
    KnowledgeArticleCreate, KnowledgeArticleUpdate, KnowledgeArticleOut,
    DocumentQuery, KnowledgeQuery,
)
from app.schemas.common import ResponseBase, PaginationResponse
from app.core.operation_log import log_file_download
from app.services.document_service import DocumentService
import datetime, os, shutil

router = APIRouter()
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    "text/plain", "text/csv", "text/html", "text/markdown",
    "application/zip", "application/x-rar-compressed",
    "application/json", "application/xml",
}

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".txt", ".csv", ".html", ".md",
    ".zip", ".rar", ".json", ".xml",
    ".dwg", ".dxf", ".step", ".stp", ".igs",
}

DANGEROUS_EXTENSIONS = {".html", ".htm", ".svg", ".js", ".exe", ".bat", ".sh", ".php"}

FILE_MAGIC = {
    b"%PDF": ".pdf",
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG": ".png",
    b"GIF8": ".gif",
    b"PK": (".zip", ".docx", ".xlsx", ".pptx"),
    b"\xd0\xcf\x11\xe0": (".doc", ".xls", ".ppt"),
}


def _validate_upload_file(file: UploadFile) -> str:
    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename or safe_filename in (".", ".."):
        raise HTTPException(400, "无效的文件名")
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型: {ext}")
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"不支持的文件格式: {file.content_type}")
    return safe_filename


def _validate_magic_bytes(file: UploadFile) -> bool:
    content = file.file.read(16)
    file.file.seek(0)

    for magic, expected_ext in FILE_MAGIC.items():
        if content.startswith(magic):
            ext = os.path.splitext(file.filename or "")[1].lower()
            if isinstance(expected_ext, tuple):
                if ext not in expected_ext:
                    raise HTTPException(400, f"文件内容与扩展名不匹配：期望 {expected_ext}")
            else:
                if ext != expected_ext:
                    raise HTTPException(400, f"文件内容与扩展名不匹配：期望 {expected_ext}")
            return True
    return True


async def _stream_write_file(file: UploadFile, file_path: str) -> int:
    file_size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                f.close()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(400, f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)")
            f.write(chunk)
    return file_size


@router.get("/list", response_model=ResponseBase)
def list_documents(query: DocumentQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = DocumentService(db)
    q = db.query(Document)
    if query.doc_type:
        q = q.filter(Document.doc_type == query.doc_type)
    if query.status:
        q = q.filter(Document.status == query.status)
    if query.project_id:
        q = q.filter(Document.project_id == query.project_id)
    if query.keyword:
        q = q.filter(Document.title.contains(query.keyword) | Document.code.contains(query.keyword))
    if query.source_module:
        q = q.filter(Document.source_module == query.source_module)
    total = q.count()
    items = q.order_by(Document.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[DocumentOut.model_validate(d).model_dump() for d in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/create", response_model=ResponseBase)
def create_document(data: DocumentCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("document", "create"))):
    service = DocumentService(db)
    code = f"DOC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    tags = data.tags
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    doc = Document(
        code=code, title=data.title, doc_type=data.doc_type,
        category_id=data.category_id, project_id=data.project_id,
        summary=data.summary, tags=tags, status=data.status,
        created_by=current.id,
        source_module="document",
    )
    db.add(doc); db.commit(); db.refresh(doc)
    return ResponseBase(data=DocumentOut.model_validate(doc).model_dump())


@router.get("/{doc_id}", response_model=ResponseBase)
def get_document(doc_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return ResponseBase(data=DocumentOut.model_validate(doc).model_dump())


@router.put("/{doc_id}", response_model=ResponseBase)
def update_document(doc_id: int, data: DocumentUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("document", "update"))):
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)
    doc.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=DocumentOut.model_validate(doc).model_dump())


@router.delete("/{doc_id}", response_model=ResponseBase)
def delete_document(doc_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("document", "delete"))):
    service = DocumentService(db)
    success = service.delete_document(doc_id)
    if not success:
        raise HTTPException(404, "文档不存在")
    return ResponseBase(data={"msg": "文档已删除"})


@router.post("/{doc_id}/upload", response_model=ResponseBase)
async def upload_document_version(doc_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current: User = Depends(require_permission("document", "upload"))):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "文档不存在")

    safe_filename = _validate_upload_file(file)
    _validate_magic_bytes(file)
    ext = os.path.splitext(safe_filename)[1].lower()

    existing_count = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == doc_id
    ).count()
    version = f"V{existing_count + 1}.0"

    file_path = os.path.join(UPLOAD_DIR, f"{doc.code}_{version}_{safe_filename}")
    file_size = await _stream_write_file(file, file_path)

    dv = DocumentVersion(
        document_id=doc_id, version=version,
        file_name=safe_filename, file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        uploader_id=current.id,
    )
    db.add(dv)
    db.flush()
    doc.current_version = version
    db.commit()
    return ResponseBase(data={"version": version, "version_id": dv.id, "file_size": file_size})


@router.get("/{doc_id}/versions", response_model=ResponseBase)
def list_document_versions(doc_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    versions = service.list_versions(doc_id)
    return ResponseBase(data={
        "document_id": doc_id,
        "document_code": doc.code,
        "document_title": doc.title,
        "current_version": doc.current_version,
        "versions": [{
            "id": v.id, "version": v.version, "file_name": v.file_name,
            "file_size": v.file_size, "mime_type": v.mime_type,
            "uploader_id": v.uploader_id, "uploaded_at": v.uploaded_at.isoformat() if v.uploaded_at else None,
            "changelog": v.changelog,
        } for v in versions],
        "total": len(versions),
    })


def _send_file_response(dv: DocumentVersion, inline: bool = False):
    if not os.path.exists(dv.file_path):
        raise HTTPException(404, "文件已不存在于服务器")
    disposition = "inline" if inline else "attachment"
    encoded_filename = quote(dv.file_name, safe="")
    return FileResponse(
        path=dv.file_path,
        filename=dv.file_name,
        media_type=dv.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_filename}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    version_id: Optional[int] = Query(None, description="指定版本ID，不传则下载最新版本"),
    inline: bool = Query(False, description="true=预览，false=下载"),
    db: Session = Depends(get_db),
    request: Request = None,
    current: User = Depends(require_permission("document", "download")),
):
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")

    if version_id:
        dv = service.get_version(version_id)
        if dv and dv.document_id != doc_id:
            dv = None
    else:
        dv = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc_id,
        ).order_by(DocumentVersion.id.desc()).first()

    if not dv:
        raise HTTPException(404, "没有可下载的文件版本")

    if not inline:
        try:
            ip = request.client.host if request and request.client else "unknown"
        except Exception:
            ip = "unknown"
        log_file_download(db, current.id, current.username, dv.file_name, dv.file_size,
                          "document", doc_id, ip)

    return _send_file_response(dv, inline=inline)


@router.get("/{doc_id}/versions/{version_id}/download")
def download_document_version(
    doc_id: int,
    version_id: int,
    inline: bool = Query(False),
    db: Session = Depends(get_db),
    request: Request = None,
    current: User = Depends(require_permission("document", "download")),
):
    return download_document(doc_id=doc_id, version_id=version_id, inline=inline, db=db, request=request, current=current)


@router.get("/knowledge/list", response_model=ResponseBase)
def list_knowledge_documents(query: KnowledgeQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sq = db.query(DocumentVersion.document_id).distinct().subquery()
    q = db.query(Document).filter(Document.id.in_(sq))

    if query.doc_type:
        q = q.filter(Document.doc_type == query.doc_type)
    if query.source_module:
        q = q.filter(Document.source_module == query.source_module)
    if query.keyword:
        q = q.filter(Document.title.contains(query.keyword) | Document.code.contains(query.keyword))
    if query.category:
        q = q.filter(Document.doc_type == query.category)
    if query.created_from:
        q = q.filter(Document.created_at >= query.created_from)
    if query.created_to:
        q = q.filter(Document.created_at <= query.created_to + " 23:59:59")

    total = q.count()
    items = q.order_by(Document.id.desc()).offset(query.offset).limit(query.limit).all()

    result = []
    for d in items:
        d_dict = DocumentOut.model_validate(d).model_dump()
        latest_ver = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == d.id
        ).order_by(DocumentVersion.id.desc()).first()
        d_dict["latest_version"] = {
            "version": latest_ver.version,
            "file_name": latest_ver.file_name,
            "file_size": latest_ver.file_size,
            "mime_type": latest_ver.mime_type,
            "uploaded_at": latest_ver.uploaded_at.isoformat() if latest_ver.uploaded_at else None,
        } if latest_ver else None
        d_dict["version_count"] = db.query(DocumentVersion).filter(DocumentVersion.document_id == d.id).count()
        result.append(d_dict)

    return ResponseBase(data=PaginationResponse(
        items=result,
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/from-experiment/{exp_id}", response_model=ResponseBase)
async def create_document_from_experiment(
    exp_id: int,
    title: str = Form(...),
    doc_type: str = Form("test"),
    file: UploadFile = File(...),
    summary: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current: User = Depends(require_permission("document", "create")),
):
    from app.models.experiment import Experiment
    exp = db.query(Experiment).filter(Experiment.id == exp_id).first()
    if not exp:
        raise HTTPException(404, "实验不存在")

    _validate_upload_file(file)
    _validate_magic_bytes(file)

    code = f"DOC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    doc = Document(
        code=code, title=title, doc_type=doc_type,
        project_id=exp.project_id,
        summary=summary or f"来自实验：{exp.name}",
        status="released",
        created_by=current.id,
        source_module="experiment",
    )
    db.add(doc)
    db.flush()

    version = "V1.0"
    safe_filename = os.path.basename(file.filename or "")
    file_path = os.path.join(UPLOAD_DIR, f"{doc.code}_{version}_{safe_filename}")
    file_size = await _stream_write_file(file, file_path)

    dv = DocumentVersion(
        document_id=doc.id, version=version,
        file_name=safe_filename, file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        uploader_id=current.id,
    )
    db.add(dv)
    doc.current_version = version
    db.commit()
    db.refresh(doc)
    return ResponseBase(data=DocumentOut.model_validate(doc).model_dump())


@router.get("/knowledge/{article_id}", response_model=ResponseBase)
def get_article(article_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    art = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not art:
        raise HTTPException(404, "文章不存在")
    art.view_count = (art.view_count or 0) + 1
    db.commit()
    return ResponseBase(data=KnowledgeArticleOut.model_validate(art).model_dump())