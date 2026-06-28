"""用户 Schema"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# ---------- 基础 ----------
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    real_name: Optional[str] = None
    role: str = Field(default="member", pattern="^(admin|manager|member|viewer)$")
    dept_id: Optional[int] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    real_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|manager|member|viewer)$")
    dept_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- 读取 ----------
class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    real_name: Optional[str] = None
    role: str
    dept_id: Optional[int] = None
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    department: Optional[DepartmentOut] = None

    class Config:
        from_attributes = True


class UserOutSimple(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """密码修改"""
    user_id: Optional[int] = None  # 管理员可指定用户
    old_password: Optional[str] = None  # 用户修改时需提供旧密码
    new_password: str = Field(..., min_length=6)
