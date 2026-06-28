"""项目管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.project import Project, Task, Requirement, ProjectType
from app.models.document import Document
from app.models.bom import BomHeader
from app.models.sample import TrialProduction
from app.models.operation_log import OperationLog
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    TaskCreate, TaskUpdate, TaskOut,
    RequirementCreate, RequirementUpdate, RequirementOut,
    ProjectQuery, TaskQuery,
)
from app.schemas.common import ResponseBase, PaginationResponse
import datetime

router = APIRouter()


def get_user_projects_filter(q, current: User):
    """根据用户角色过滤项目"""
    # admin 和 manager 可以看到所有项目
    if current.role in ("admin", "manager"):
        return q
    # 普通成员和查看者只能看到自己负责的项目
    return q.filter(
        (Project.owner_id == current.id) | (Project.created_by == current.id)
    )


# ===== 项目类型 =====
@router.get("/types", response_model=ResponseBase)
def get_project_types(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return ResponseBase(data=[{"id": t.id, "name": t.name} for t in db.query(ProjectType).filter(ProjectType.is_active==True).all()])


# ===== 项目 CRUD =====
@router.get("/list", response_model=ResponseBase)
def list_projects(query: ProjectQuery = Depends(), db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    q = db.query(Project)
    
    # 数据隔离：按角色过滤
    q = get_user_projects_filter(q, current)
    
    if query.status:
        q = q.filter(Project.status == query.status)
    if query.owner_id:
        q = q.filter(Project.owner_id == query.owner_id)
    if query.keyword:
        q = q.filter(Project.name.contains(query.keyword) | Project.code.contains(query.keyword))
    total = q.count()
    items = q.order_by(Project.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[ProjectOut.model_validate(p).model_dump() for p in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/create", response_model=ResponseBase)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("project", "create"))):
    # 验证外键存在性
    if data.project_type_id:
        pt = db.query(ProjectType).filter(ProjectType.id == data.project_type_id, ProjectType.is_active == True).first()
        if not pt:
            raise HTTPException(400, "所选项目类型不存在或已停用")
    if data.owner_id:
        owner = db.query(User).filter(User.id == data.owner_id, User.is_active == True).first()
        if not owner:
            raise HTTPException(400, "指定的负责人不存在或已禁用")

    owner_id = data.owner_id or current.id
    code = f"PMS{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    # 唯一性检查（极端并发场景兜底）
    if db.query(Project).filter(Project.code == code).first():
        code = f"PMS{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    proj = Project(
        code=code, name=data.name, description=data.description,
        status=data.status, priority=data.priority,
        project_type_id=data.project_type_id, owner_id=owner_id,
        created_by=current.id, plan_start=data.plan_start, plan_end=data.plan_end,
        budget=data.budget,
    )
    db.add(proj); db.commit(); db.refresh(proj)
    return ResponseBase(data=ProjectOut.model_validate(proj).model_dump())


@router.get("/{project_id}", response_model=ResponseBase)
def get_project(project_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    # 数据隔离检查
    if current.role not in ("admin", "manager") and proj.owner_id != current.id and proj.created_by != current.id:
        raise HTTPException(403, "无权访问此项目")
    return ResponseBase(data=ProjectOut.model_validate(proj).model_dump())


@router.put("/{project_id}", response_model=ResponseBase)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "update"))):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proj, field, value)
    proj.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=ProjectOut.model_validate(proj).model_dump())


@router.delete("/{project_id}", response_model=ResponseBase)
def delete_project(project_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "delete"))):
    """硬删除项目，级联清理所有关联数据"""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")

    # 1. 清理项目关联的文档（解除关联或删除）
    db.query(Document).filter(Document.project_id == project_id).update(
        {Document.project_id: None}
    )

    # 2. 清理项目关联的 BOM（解除关联或删除）
    db.query(BomHeader).filter(BomHeader.project_id == project_id).update(
        {BomHeader.project_id: None}
    )

    # 3. 删除项目关联的试产记录（TrialProduction 有 FK 到 projects，未在 Project 模型中定义级联）
    db.query(TrialProduction).filter(TrialProduction.project_id == project_id).delete()

    # 4. 清理操作日志中对项目的引用（标记为已删除资源）
    db.query(OperationLog).filter(
        OperationLog.resource == "project",
        OperationLog.resource_id == project_id,
    ).update({
        OperationLog.resource_name: OperationLog.resource_name + " (已删除)"
    }, synchronize_session=False)

    # 5. 硬删除项目（cascade 会自动删除 tasks, requirements, experiments, samples）
    db.delete(proj)
    db.commit()
    return ResponseBase(data={"msg": "项目及关联数据已删除"})


# ===== 任务 CRUD =====
@router.get("/{project_id}/tasks", response_model=ResponseBase)
def list_tasks(project_id: int, query: TaskQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Task).filter(Task.project_id == project_id)
    if query.status:
        q = q.filter(Task.status == query.status)
    if query.assignee_id:
        q = q.filter(Task.assignee_id == query.assignee_id)
    total = q.count()
    items = q.order_by(Task.sort_order, Task.id).all()
    return ResponseBase(data=[TaskOut.model_validate(t).model_dump() for t in items])


@router.post("/{project_id}/tasks", response_model=ResponseBase)
def create_task(project_id: int, data: TaskCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "create"))):
    task = Task(
        project_id=project_id, title=data.title, description=data.description,
        status=data.status, priority=data.priority, assignee_id=data.assignee_id,
        plan_hours=data.plan_hours, due_date=data.due_date,
        parent_id=data.parent_id, sort_order=data.sort_order,
    )
    db.add(task); db.commit(); db.refresh(task)
    return ResponseBase(data=TaskOut.model_validate(task).model_dump())


@router.put("/tasks/{task_id}", response_model=ResponseBase)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "update"))):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=TaskOut.model_validate(task).model_dump())


@router.delete("/tasks/{task_id}", response_model=ResponseBase)
def delete_task(task_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "delete"))):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task); db.commit()
    return ResponseBase(data={"msg": "已删除"})


# ===== 需求 CRUD =====
@router.get("/{project_id}/requirements", response_model=ResponseBase)
def list_requirements(project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    reqs = db.query(Requirement).filter(Requirement.project_id == project_id).order_by(Requirement.id.desc()).all()
    return ResponseBase(data=[RequirementOut.model_validate(r).model_dump() for r in reqs])


@router.post("/{project_id}/requirements", response_model=ResponseBase)
def create_requirement(project_id: int, data: RequirementCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "create"))):
    code = f"REQ{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    req = Requirement(
        project_id=project_id, code=code, title=data.title,
        description=data.description, source=data.source,
        priority=data.priority, status=data.status,
    )
    db.add(req); db.commit(); db.refresh(req)
    return ResponseBase(data=RequirementOut.model_validate(req).model_dump())


@router.put("/requirements/{req_id}", response_model=ResponseBase)
def update_requirement(req_id: int, data: RequirementUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "update"))):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(404, "需求不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req, field, value)
    req.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=RequirementOut.model_validate(req).model_dump())


@router.delete("/requirements/{req_id}", response_model=ResponseBase)
def delete_requirement(req_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("project", "delete"))):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(404, "需求不存在")
    db.delete(req); db.commit()
    return ResponseBase(data={"msg": "已删除"})
