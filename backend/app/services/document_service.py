import os
import hashlib
from pathlib import Path
from typing import Optional, List

from sqlalchemy import or_, func, desc
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentVersion
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentVersionOut


ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/msword',
    'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'text/plain',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/json',
}


MAGIC_BYTES_MAP = {
    b'\x25\x50\x44\x46': 'application/pdf',
    b'\x50\x4B\x03\x04': 'application/vnd.openxmlformats-officedocument',
    b'\xD0\xCF\x11\xE0': 'application/vnd.ms-office',
    b'\xFF\xD8\xFF': 'image/jpeg',
    b'\x89\x50\x4E\x47': 'image/png',
    b'\x47\x49\x46\x38': 'image/gif',
    b'\x5B': 'application/json',
    b'{': 'application/json',
    b'<?xml': 'application/xml',
    b'%PDF': 'application/pdf',
}


def validate_file_magic_bytes(file_content: bytes) -> Optional[str]:
    for magic, mime_type in MAGIC_BYTES_MAP.items():
        if file_content.startswith(magic):
            return mime_type
    return None


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def _save_file(self, file, doc_id: int, version_no: int) -> str:
        upload_dir = Path('uploads') / 'documents' / str(doc_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        original_filename = file.filename or f'document_{version_no}'
        file_ext = Path(original_filename).suffix or '.bin'
        filename = f'version_{version_no}{file_ext}'
        file_path = upload_dir / filename

        content = file.read()

        detected_mime = validate_file_magic_bytes(content)
        if detected_mime:
            if detected_mime not in ALLOWED_MIME_TYPES:
                raise ValueError(f'不支持的文件类型: {detected_mime}')

        with open(file_path, 'wb') as f:
            f.write(content)

        file_hash = hashlib.sha256(content).hexdigest()

        return str(file_path), file_hash

    def get_document(self, doc_id: int) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def list_documents(self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None,
                       doc_type: Optional[str] = None) -> tuple:
        query = self.db.query(Document)

        if keyword:
            query = query.filter(
                or_(
                    Document.title.ilike(f'%{keyword}%'),
                    Document.description.ilike(f'%{keyword}%')
                )
            )

        if doc_type:
            query = query.filter(Document.doc_type == doc_type)

        total = query.count()
        docs = query.order_by(desc(Document.created_at)).offset(
            (page - 1) * page_size).limit(page_size).all()

        return docs, total

    def create_document(self, data: DocumentCreate, current_user_id: int, file=None) -> Document:
        doc = Document(
            title=data.title,
            doc_type=data.doc_type,
            description=data.description,
            owner_id=current_user_id,
            status='active',
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        if file:
            self._create_version(doc.id, file, '初始版本')

        return doc

    def update_document(self, doc_id: int, data: DocumentUpdate) -> Document:
        doc = self.get_document(doc_id)
        if not doc:
            raise ValueError('文档不存在')

        if data.title is not None:
            doc.title = data.title
        if data.description is not None:
            doc.description = data.description
        if data.doc_type is not None:
            doc.doc_type = data.doc_type

        self.db.commit()
        self.db.refresh(doc)

        return doc

    def delete_document(self, doc_id: int) -> bool:
        doc = self.get_document(doc_id)
        if not doc:
            return False

        versions = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc_id).all()

        for version in versions:
            if version.file_path and os.path.exists(version.file_path):
                try:
                    os.remove(version.file_path)
                except Exception:
                    pass

        self.db.delete(doc)
        self.db.commit()

        return True

    def _create_version(self, doc_id: int, file, comment: str = '') -> DocumentVersion:
        doc = self.get_document(doc_id)
        if not doc:
            raise ValueError('文档不存在')

        version_no = self.db.query(func.max(DocumentVersion.version_no)).filter(
            DocumentVersion.document_id == doc_id).scalar() or 0
        version_no += 1

        file_path, file_hash = self._save_file(file, doc_id, version_no)

        version = DocumentVersion(
            document_id=doc_id,
            version_no=version_no,
            file_name=file.filename or f'document_{version_no}',
            file_path=file_path,
            file_hash=file_hash,
            file_size=os.path.getsize(file_path),
            comment=comment,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        doc.current_version_id = version.id
        self.db.commit()

        return version

    def upload_version(self, doc_id: int, file, comment: str = '') -> DocumentVersion:
        return self._create_version(doc_id, file, comment)

    def list_versions(self, doc_id: int) -> List[DocumentVersion]:
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc_id).order_by(
            desc(DocumentVersion.uploaded_at)).all()

    def get_version(self, version_id: int) -> Optional[DocumentVersion]:
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.id == version_id).first()

    def delete_version(self, version_id: int) -> bool:
        version = self.get_version(version_id)
        if not version:
            return False

        doc = self.get_document(version.document_id)
        if doc and doc.current_version_id == version.id:
            latest_version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == doc.id,
                DocumentVersion.id != version.id
            ).order_by(desc(DocumentVersion.version_no)).first()

            if latest_version:
                doc.current_version_id = latest_version.id
            else:
                doc.current_version_id = None

        if version.file_path and os.path.exists(version.file_path):
            try:
                os.remove(version.file_path)
            except Exception:
                pass

        self.db.delete(version)
        self.db.commit()

        return True

    def create_from_experiment(self, exp_id: int, title: str, file, doc_type: str,
                               current_user_id: int) -> Document:
        doc = Document(
            title=title,
            doc_type=doc_type,
            description=f'来自实验 {exp_id}',
            owner_id=current_user_id,
            status='active',
            experiment_id=exp_id,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        self._create_version(doc.id, file, f'来自实验 {exp_id} 的原始文件')

        return doc