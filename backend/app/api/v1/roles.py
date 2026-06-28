"""角色管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import List
import json
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.role import Role, Permission
from app.models.operation_log import OperationLog
from app.schemas.role import RoleCreate, RoleUpdate, RoleOut, PermissionCreate, PermissionOut
from app.schemas.common import ResponseBase, PaginationResponse

router = APIRouter()


@router.get("/list", response_model=ResponseBase)
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    roles = db.query(Role).order_by(Role.sort_order, Role.id).all()
    return ResponseBase(data=[RoleOut.model_validate(r).model_dump() for r in roles])


@router.get("/{role_id}", response_model=ResponseBase)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ResponseBase(data=RoleOut.model_validate(role).model_dump())


@router.post("/create", response_model=ResponseBase)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    if db.query(Role).filter(Role.code == data.code).first():
        raise HTTPException(status_code=400, detail="角色代码已存在")
    role = Role(
        code=data.code,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return ResponseBase(data={"id": role.id})


@router.put("/{role_id}", response_model=ResponseBase)
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 不能修改系统角色
    if role.code in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail="系统角色不可修改")
    
    for field in ["name", "description", "is_active", "sort_order"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(role, field, val)
    db.commit()
    return ResponseBase(data={"msg": "更新成功"})


@router.delete("/{role_id}", response_model=ResponseBase)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.code in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail="系统角色不可删除")

    # 检查是否有用户使用此角色（User.role 是字符串字段，非 FK，需要手动检查）
    user_count = db.query(User).filter(User.role == role.code).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"角色「{role.name}」下还有 {user_count} 个用户，请先修改这些用户的角色后再删除"
        )

    db.delete(role)
    db.commit()
    return ResponseBase(data={"msg": "已删除"})


# ===== 权限管理 =====
@router.get("/permissions/list", response_model=ResponseBase)
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    perms = db.query(Permission).order_by(Permission.resource, Permission.action).all()
    return ResponseBase(data=[PermissionOut.model_validate(p).model_dump() for p in perms])


@router.post("/permissions/create", response_model=ResponseBase)
def create_permission(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    if db.query(Permission).filter(Permission.code == data.code).first():
        raise HTTPException(status_code=400, detail="权限代码已存在")
    perm = Permission(**data.model_dump())
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return ResponseBase(data={"id": perm.id})


@router.post("/{role_id}/permissions", response_model=ResponseBase)
def assign_permissions(
    role_id: int,
    request: Request,
    permission_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_role("admin")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 记录变更前的权限码列表
    before_codes = sorted([p.code for p in role.permissions])

    perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    role.permissions = perms
    db.flush()

    after_codes = sorted([p.code for p in role.permissions])

    # 写入操作日志（记录 before/after 变更详情）
    added = sorted(set(after_codes) - set(before_codes))
    removed = sorted(set(before_codes) - set(after_codes))
    detail_parts = []
    if added:
        detail_parts.append(f"新增: {', '.join(added)}")
    if removed:
        detail_parts.append(f"移除: {', '.join(removed)}")
    detail = "; ".join(detail_parts) if detail_parts else "无变更"

    log = OperationLog(
        user_id=current.id,
        username=current.username,
        action="update",
        resource="role",
        resource_id=role.id,
        resource_name=f"{role.name}({role.code})",
        method="POST",
        path=str(request.url.path),
        ip_address=getattr(request, "client", None).host if getattr(request, "client", None) else None,
        detail=detail,
        before_value=json.dumps(before_codes, ensure_ascii=False),
        after_value=json.dumps(after_codes, ensure_ascii=False),
    )
    db.add(log)
    db.commit()
    return ResponseBase(data={"msg": "权限分配成功"})
