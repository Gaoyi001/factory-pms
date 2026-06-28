"""用户管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, get_password_hash, verify_password
from app.models.user import User, Department
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserOutSimple, DepartmentOut, PasswordChange
from app.schemas.common import ResponseBase, PaginationResponse

router = APIRouter()


@router.get("/list", response_model=ResponseBase)
def list_users(
    page: int = 1, page_size: int = 20, keyword: str = "", 
    dept_id: int = None, role: str = None, is_active: bool = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
):
    q = db.query(User)
    if keyword:
        q = q.filter(User.real_name.contains(keyword) | User.username.contains(keyword))
    if dept_id:
        q = q.filter(User.dept_id == dept_id)
    if role:
        q = q.filter(User.role == role)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    total = q.count()
    users = q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    depts = {d.id: d for d in db.query(Department).all()}
    items = [UserOut(
        id=u.id, username=u.username, email=u.email, real_name=u.real_name,
        role=u.role, dept_id=u.dept_id, is_active=u.is_active,
        last_login_at=u.last_login_at,
        department=depts.get(u.dept_id) if u.dept_id else None,
    ) for u in users]
    return ResponseBase(data=PaginationResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    ).model_dump())


@router.get("/simple-list", response_model=ResponseBase)
def simple_list(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    users = db.query(User).filter(User.is_active == True).all()
    return ResponseBase(data=[UserOutSimple(
        id=u.id, username=u.username, real_name=u.real_name, role=u.role
    ) for u in users])


@router.post("/create", response_model=ResponseBase)
def create_user(
    data: UserCreate, db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username, email=data.email,
        password_hash=get_password_hash(data.password),
        real_name=data.real_name, role=data.role,
        dept_id=data.dept_id, is_active=True,
    )
    db.add(user); db.commit(); db.refresh(user)
    return ResponseBase(data={"id": user.id})


@router.put("/{user_id}", response_model=ResponseBase)
def update_user(
    user_id: int, data: UserUpdate, db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")

    # 非 admin 用户不能修改自己的角色或账号状态（防止越权）
    if current.role != "admin" and current.id == user_id:
        if data.role is not None and data.role != current.role:
            raise HTTPException(status_code=403, detail="无权修改自己的角色")
        if data.is_active is not None and not data.is_active:
            raise HTTPException(status_code=403, detail="无权禁用自己的账号")

    for field in ["email", "real_name", "role", "dept_id", "is_active"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(user, field, val)
    if data.password:
        user.password_hash = get_password_hash(data.password)
    db.commit()
    return ResponseBase(data={"msg": "更新成功"})


@router.post("/change-password", response_model=ResponseBase)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """修改密码"""
    # 管理员可以重置任意用户密码
    if data.user_id and current.role == "admin":
        user = db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
    else:
        user = current
        # 验证旧密码
        if not verify_password(data.old_password or "", user.password_hash):
            raise HTTPException(status_code=400, detail="旧密码错误")
    
    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return ResponseBase(data={"msg": "密码修改成功"})


@router.delete("/{user_id}", response_model=ResponseBase)
def delete_user(
    user_id: int, db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    db.commit()
    return ResponseBase(data={"msg": "已禁用"})


@router.post("/batch-enable", response_model=ResponseBase)
def batch_enable(
    user_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_role("admin")),
):
    """批量启用用户"""
    if not user_ids:
        raise HTTPException(status_code=400, detail="请选择要启用的用户")

    # 查找存在的用户
    existing = db.query(User).filter(User.id.in_(user_ids)).all()
    existing_ids = {u.id for u in existing}
    missing_ids = set(user_ids) - existing_ids

    if not existing_ids:
        raise HTTPException(status_code=404, detail="未找到指定的用户")

    # 批量更新
    updated = db.query(User).filter(User.id.in_(list(existing_ids))).update(
        {User.is_active: True}, synchronize_session=False
    )
    db.commit()

    result_msg = f"已启用 {updated} 个用户"
    if missing_ids:
        result_msg += f"，{len(missing_ids)} 个用户不存在（ID: {sorted(missing_ids)}）"
        return ResponseBase(data={"msg": result_msg, "updated": updated, "missing": sorted(missing_ids)})

    return ResponseBase(data={"msg": result_msg, "updated": updated})


@router.post("/batch-disable", response_model=ResponseBase)
def batch_disable(
    user_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_role("admin")),
):
    """批量禁用用户"""
    if not user_ids:
        raise HTTPException(status_code=400, detail="请选择要禁用的用户")

    # 查找存在的用户
    existing = db.query(User).filter(User.id.in_(user_ids)).all()
    existing_ids = {u.id for u in existing}
    missing_ids = set(user_ids) - existing_ids

    if not existing_ids:
        raise HTTPException(status_code=404, detail="未找到指定的用户")

    # 过滤掉当前操作用户（不能禁用自己）
    valid_ids = [uid for uid in existing_ids if uid != current.id]
    self_skipped = current.id in existing_ids

    if not valid_ids:
        raise HTTPException(status_code=400, detail="不能禁用当前登录账号")

    # 批量更新
    updated = db.query(User).filter(User.id.in_(valid_ids)).update(
        {User.is_active: False}, synchronize_session=False
    )
    db.commit()

    result_msg = f"已禁用 {updated} 个用户"
    if self_skipped:
        result_msg += "（已跳过当前登录账号）"
    if missing_ids:
        result_msg += f"，{len(missing_ids)} 个用户不存在（ID: {sorted(missing_ids)}）"
        return ResponseBase(data={
            "msg": result_msg, "updated": updated,
            "missing": sorted(missing_ids), "self_skipped": self_skipped
        })

    return ResponseBase(data={
        "msg": result_msg, "updated": updated, "self_skipped": self_skipped
    })


# ===== 部门 =====
@router.get("/departments", response_model=ResponseBase)
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    depts = db.query(Department).order_by(Department.id).all()
    return ResponseBase(data=[DepartmentOut(
        id=d.id, name=d.name, parent_id=d.parent_id
    ) for d in depts])
