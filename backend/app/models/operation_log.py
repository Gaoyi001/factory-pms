"""操作日志模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    resource = Column(String(32), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)
    resource_name = Column(String(200), nullable=True)
    
    # 请求信息
    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # 支持IPv6
    user_agent = Column(String(500), nullable=True)
    
    # 变更详情
    detail = Column(Text, nullable=True)
    before_value = Column(Text, nullable=True)
    after_value = Column(Text, nullable=True)
    
    # 文件下载记录
    is_file_download = Column(Boolean, default=False)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id])
