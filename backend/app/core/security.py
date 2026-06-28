"""JWT 认证与安全工具"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.role import Role, Permission, role_permission_table


class OptionalHTTPBearer(HTTPBearer):
    """可选的HTTP Bearer认证 — 仅捕获缺失凭证的情况，其他异常仍抛出"""
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:
                return None
            raise


oauth2_scheme = OptionalHTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT access_token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "factory-pms",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """密码哈希"""
    if len(password) < 6:
        raise ValueError("密码长度至少6字符")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _parse_token(token: str) -> dict:
    """解析并校验 JWT token（校验签发者 iss）"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            issuer="factory-pms",
            options={"verify_exp": True, "verify_iss": True},
        )
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户，未认证返回 401"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _parse_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效：缺少用户标识",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效：用户标识格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 校验角色是否存在
    if user.role:
        role = db.query(Role).filter(Role.code == user.role, Role.is_active == True).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"角色'{user.role}'已失效，请联系管理员",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 将用户信息注入到 request.state，供操作日志中间件使用
    request.state.user_id = user.id
    request.state.username = user.username
    return user


def require_role(*roles: str):
    """角色级别权限检查（基于 User.role 字符串），用于不需要细粒度 RBAC 的场景"""
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            allowed = "、".join(roles)
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：当前角色「{current_user.role}」无权执行此操作，需要角色：{allowed}"
            )
        return current_user
    return checker


def require_permission(resource: str, action: str):
    """基于 RBAC 的细粒度权限检查：User.role → Role → Permission(resource, action)
    
    检查流程：
    1. 根据 User.role 查找对应 Role
    2. 通过 role_permissions 联表查询该角色是否拥有 (resource, action) 权限
    3. 所有角色（包括 admin）都走统一的权限检查，权限由数据库分配
    """
    async def checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # Admin 角色拥有所有权限（超级管理员，跳过细粒度检查）
        if current_user.role == "admin":
            admin_role = db.query(Role).filter(Role.code == "admin", Role.is_active == True).first()
            if admin_role:
                return current_user
            raise HTTPException(status_code=403, detail="系统管理员角色已被禁用，请联系系统管理员")

        # 查找角色
        role = db.query(Role).filter(Role.code == current_user.role, Role.is_active == True).first()
        if not role:
            raise HTTPException(
                status_code=403,
                detail=f"当前角色「{current_user.role}」未配置或已停用，无法执行操作"
            )

        # 检查具体权限（所有角色统一检查，包括 admin）
        has_perm = db.query(Permission).join(
            role_permission_table,
            Permission.id == role_permission_table.c.permission_id
        ).filter(
            role_permission_table.c.role_id == role.id,
            Permission.resource == resource,
            Permission.action == action,
        ).first()

        if not has_perm:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：角色「{current_user.role}」没有「{resource}:{action}」权限"
            )
        return current_user
    return checker
