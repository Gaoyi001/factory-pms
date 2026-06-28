"""部门管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut, DepartmentTreeOut
from app.schemas.common import ResponseBase

router = APIRouter()


def build_tree(depts: List[Department], parent_id: Optional[int] = None, depth: int = 0) -> List[DepartmentTreeOut]:
    """递归构建部门树（最多10层防止溢出）"""
    if depth > 10:
        return []
    result = []
    for dept in depts:
        if dept.parent_id == parent_id:
            children = build_tree(depts, dept.id, depth + 1)
            dept_out = DepartmentTreeOut(
                id=dept.id,
                name=dept.name,
                parent_id=dept.parent_id,
                created_at=dept.created_at,
                children=children,
            )
            result.append(dept_out)
    return result


def _is_descendant(dept_id: int, target_id: int, db: Session) -> bool:
    """递归检查 target_id 是否是 dept_id 的后代（防止循环引用）"""
    children = db.query(Department).filter(Department.parent_id == dept_id).all()
    for child in children:
        if child.id == target_id:
            return True
        if _is_descendant(child.id, target_id, db):
            return True
    return False


@router.get("/tree", response_model=ResponseBase)
def get_department_tree(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """获取部门树形结构"""
    depts = db.query(Department).order_by(Department.id).all()
    tree = build_tree(depts)
    return ResponseBase(data=tree)


@router.get("/list", response_model=ResponseBase)
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取部门列表"""
    depts = db.query(Department).order_by(Department.id).all()
    return ResponseBase(data=[DepartmentOut.model_validate(d).model_dump() for d in depts])


@router.get("/{dept_id}", response_model=ResponseBase)
def get_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取部门详情"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    return ResponseBase(data=DepartmentOut.model_validate(dept).model_dump())


@router.post("/create", response_model=ResponseBase)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
):
    """创建部门"""
    if db.query(Department).filter(Department.name == data.name).first():
        raise HTTPException(status_code=400, detail="部门名称已存在")
    
    # 检查父部门
    if data.parent_id:
        parent = db.query(Department).filter(Department.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="父部门不存在")
    
    dept = Department(name=data.name, parent_id=data.parent_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return ResponseBase(data={"id": dept.id})


@router.put("/{dept_id}", response_model=ResponseBase)
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
):
    """更新部门"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    if data.name and data.name != dept.name:
        if db.query(Department).filter(Department.name == data.name, Department.id != dept_id).first():
            raise HTTPException(status_code=400, detail="部门名称已存在")
        dept.name = data.name
    
    if data.parent_id is not None:
        if data.parent_id == dept_id:
            raise HTTPException(status_code=400, detail="不能将自己设为父部门")
        # 防止循环引用：检查目标父部门不是当前部门的后代
        if data.parent_id and _is_descendant(dept_id, data.parent_id, db):
            raise HTTPException(status_code=400, detail="不能将父部门设为自己的子部门（会形成循环）")
        if data.parent_id:
            parent = db.query(Department).filter(Department.id == data.parent_id).first()
            if not parent:
                raise HTTPException(status_code=400, detail="父部门不存在")
        dept.parent_id = data.parent_id
    
    db.commit()
    return ResponseBase(data={"msg": "更新成功"})


@router.delete("/{dept_id}", response_model=ResponseBase)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """删除部门"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 检查是否有子部门
    children = db.query(Department).filter(Department.parent_id == dept_id).count()
    if children > 0:
        raise HTTPException(status_code=400, detail="请先删除子部门")
    
    # 检查是否有用户
    users = db.query(User).filter(User.dept_id == dept_id).count()
    if users > 0:
        raise HTTPException(status_code=400, detail="该部门下有用户，无法删除")
    
    db.delete(dept)
    db.commit()
    return ResponseBase(data={"msg": "已删除"})
