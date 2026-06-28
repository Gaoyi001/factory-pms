"""Pydantic Schema 基础定义"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class ResponseBase(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None

    class Config:
        from_attributes = True


def response_schema(data_schema: type):
    """生成标准响应 Schema"""
    class ResponseWrapper(BaseModel):
        code: int = 200
        message: str = "success"
        data: Optional[data_schema] = None

        class Config:
            from_attributes = True
    return ResponseWrapper


# 分页参数
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
