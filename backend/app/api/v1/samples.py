"""样品与试产管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.sample import Sample, SampleInspection, SampleInspectionItem, TrialProduction
from app.schemas.sample import (
    SampleCreate, SampleUpdate, SampleOut,
    SampleInspectionCreate, SampleInspectionOut,
    TrialProductionCreate, TrialProductionUpdate, TrialProductionOut,
    SampleQuery, TrialQuery,
)
from app.schemas.common import ResponseBase, PaginationResponse
import datetime

router = APIRouter()


# ===== 样品 =====
@router.get("/samples", response_model=ResponseBase)
def list_samples(query: SampleQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Sample)
    if query.project_id:
        q = q.filter(Sample.project_id == query.project_id)
    if query.status:
        q = q.filter(Sample.status == query.status)
    if query.sample_type:
        q = q.filter(Sample.sample_type == query.sample_type)
    if query.keyword:
        q = q.filter(Sample.name.contains(query.keyword) | Sample.sample_no.contains(query.keyword))
    total = q.count()
    items = q.order_by(Sample.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[SampleOut.model_validate(s).model_dump() for s in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/samples", response_model=ResponseBase)
def create_sample(data: SampleCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("sample", "create"))):
    sample_no = f"SMP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    s = Sample(
        sample_no=sample_no, project_id=data.project_id, name=data.name,
        description=data.description, version=data.version, status=data.status,
        sample_type=data.sample_type, quantity=data.quantity,
        maker_id=data.maker_id, inspector_id=data.inspector_id,
        plan_finish=data.plan_finish, created_by=current.id,
    )
    db.add(s); db.commit(); db.refresh(s)
    return ResponseBase(data=SampleOut.model_validate(s).model_dump())


@router.get("/samples/{sample_id}", response_model=ResponseBase)
def get_sample(sample_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    s = db.query(Sample).filter(Sample.id == sample_id).first()
    if not s:
        raise HTTPException(404, "样品不存在")
    return ResponseBase(data=SampleOut.model_validate(s).model_dump())


@router.put("/samples/{sample_id}", response_model=ResponseBase)
def update_sample(sample_id: int, data: SampleUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("sample", "update"))):
    s = db.query(Sample).filter(Sample.id == sample_id).first()
    if not s:
        raise HTTPException(404, "样品不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(s, field, value)
    s.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=SampleOut.model_validate(s).model_dump())


@router.delete("/samples/{sample_id}", response_model=ResponseBase)
def delete_sample(sample_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("sample", "delete"))):
    """删除样品（级联删除关联的检测记录和检测项）"""
    s = db.query(Sample).filter(Sample.id == sample_id).first()
    if not s:
        raise HTTPException(404, "样品不存在")
    # 解除试产记录中对本样品的引用
    db.query(TrialProduction).filter(TrialProduction.sample_id == sample_id).update(
        {TrialProduction.sample_id: None}
    )
    db.delete(s)
    db.commit()
    return ResponseBase(data={"msg": "样品已删除"})


# ===== 样品检测 =====
@router.get("/samples/{sample_id}/inspections", response_model=ResponseBase)
def list_inspections(sample_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(SampleInspection).filter(SampleInspection.sample_id == sample_id).order_by(SampleInspection.id.desc()).all()
    return ResponseBase(data=[SampleInspectionOut.model_validate(i).model_dump() for i in items])


@router.post("/inspections", response_model=ResponseBase)
def create_inspection(data: SampleInspectionCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("sample", "create"))):
    inspect_no = f"INSP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    insp = SampleInspection(
        sample_id=data.sample_id, inspect_no=inspect_no,
        inspect_type=data.inspect_type, inspector_id=current.id,
        inspected_at=data.inspected_at, result=data.result,
        dimension_data=data.dimension_data, performance_data=data.performance_data,
        appearance_desc=data.appearance_desc, failure_desc=data.failure_desc,
        disposition=data.disposition, remark=data.remark,
    )
    if data.items:
        for item in data.items:
            insp.items.append(SampleInspectionItem(**item.model_dump()))
    db.add(insp); db.commit()
    return ResponseBase(data={"inspect_no": inspect_no})


@router.delete("/inspections/{inspection_id}", response_model=ResponseBase)
def delete_inspection(inspection_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("sample", "delete"))):
    """删除检测记录（级联删除检测项）"""
    insp = db.query(SampleInspection).filter(SampleInspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(404, "检测记录不存在")
    db.delete(insp)
    db.commit()
    return ResponseBase(data={"msg": "检测记录已删除"})


# ===== 试产 =====
@router.get("/trials", response_model=ResponseBase)
def list_trials(query: TrialQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(TrialProduction)
    if query.project_id:
        q = q.filter(TrialProduction.project_id == query.project_id)
    if query.status:
        q = q.filter(TrialProduction.status == query.status)
    total = q.count()
    items = q.order_by(TrialProduction.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[TrialProductionOut.model_validate(t).model_dump() for t in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/trials", response_model=ResponseBase)
def create_trial(data: TrialProductionCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("sample", "create"))):
    trial_no = f"TR{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    t = TrialProduction(
        trial_no=trial_no, project_id=data.project_id, name=data.name,
        bom_id=data.bom_id, sample_id=data.sample_id, status=data.status,
        plan_qty=data.plan_qty, workshop=data.workshop, line_no=data.line_no,
        foreman_id=data.foreman_id, plan_start=data.plan_start, plan_end=data.plan_end,
        process_params=data.process_params, created_by=current.id,
    )
    db.add(t); db.commit(); db.refresh(t)
    return ResponseBase(data=TrialProductionOut.model_validate(t).model_dump())


@router.get("/trials/{trial_id}", response_model=ResponseBase)
def get_trial(trial_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    t = db.query(TrialProduction).filter(TrialProduction.id == trial_id).first()
    if not t:
        raise HTTPException(404, "试产记录不存在")
    return ResponseBase(data=TrialProductionOut.model_validate(t).model_dump())


@router.put("/trials/{trial_id}", response_model=ResponseBase)
def update_trial(trial_id: int, data: TrialProductionUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("sample", "update"))):
    t = db.query(TrialProduction).filter(TrialProduction.id == trial_id).first()
    if not t:
        raise HTTPException(404, "试产记录不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(t, field, value)
    t.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=TrialProductionOut.model_validate(t).model_dump())


@router.delete("/trials/{trial_id}", response_model=ResponseBase)
def delete_trial(trial_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("sample", "delete"))):
    """删除试产记录"""
    t = db.query(TrialProduction).filter(TrialProduction.id == trial_id).first()
    if not t:
        raise HTTPException(404, "试产记录不存在")
    db.delete(t)
    db.commit()
    return ResponseBase(data={"msg": "试产记录已删除"})
