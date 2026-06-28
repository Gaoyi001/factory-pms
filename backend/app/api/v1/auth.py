"""认证 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user, require_role
from app.core.rate_limit import login_rate_limiter
from app.models.user import User, Department
from app.models.role import Role, Permission, role_permission_table
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserOut
from app.schemas.common import ResponseBase

router = APIRouter()


@router.post("/login", response_model=ResponseBase)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    # 速率限制：每个 IP 每分钟最多 5 次登录尝试
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = login_rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"登录尝试过于频繁，请 60 秒后再试"
        )

    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    user.last_login_at = __import__('datetime').datetime.utcnow()
    db.commit()
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return ResponseBase(data=TokenResponse(access_token=token).model_dump())


@router.post("/register", response_model=ResponseBase)
def register(data: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_role("admin"))):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    user = User(
        username=data.username,
        email=data.email,
        password_hash=get_password_hash(data.password),
        real_name=data.real_name,
        role=data.role,
        dept_id=data.dept_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ResponseBase(data={"user_id": user.id})


@router.get("/me", response_model=ResponseBase)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == current_user.dept_id).first()
    return ResponseBase(data=UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        real_name=current_user.real_name,
        role=current_user.role,
        dept_id=current_user.dept_id,
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
        department=dept,
    ).model_dump())


@router.get("/me/permissions", response_model=ResponseBase)
def get_my_permissions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的权限码列表，供前端做菜单/路由权限控制"""
    # admin 拥有所有权限
    if current_user.role == "admin":
        all_perms = db.query(Permission).all()
        return ResponseBase(data={
            "role": current_user.role,
            "permissions": [p.code for p in all_perms],
            "is_admin": True,
        })

    # 查找当前用户角色对应的权限
    role = db.query(Role).filter(Role.code == current_user.role, Role.is_active == True).first()
    if not role:
        return ResponseBase(data={"role": current_user.role, "permissions": [], "is_admin": False})

    perms = db.query(Permission).join(
        role_permission_table,
        Permission.id == role_permission_table.c.permission_id
    ).filter(role_permission_table.c.role_id == role.id).all()

    return ResponseBase(data={
        "role": current_user.role,
        "permissions": [p.code for p in perms],
        "is_admin": False,
    })
