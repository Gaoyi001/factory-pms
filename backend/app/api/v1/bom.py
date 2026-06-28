"""物料与BOM管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.bom import Material, BomHeader, BomItem, BomChange
from app.models.sample import TrialProduction
from app.schemas.bom import (
    MaterialCreate, MaterialUpdate, MaterialOut,
    BomHeaderCreate, BomHeaderUpdate, BomHeaderOut,
    BomItemCreate, BomItemUpdate, BomItemBatchDelete,
    MaterialBatchDelete,
    BomChangeCreate, BomChangeUpdate, BomChangeOut,
    MaterialQuery, BomQuery, BomChangeQuery,
)
from app.schemas.common import ResponseBase, PaginationResponse
import datetime

router = APIRouter()


# ===== 物料 =====
@router.get("/materials", response_model=ResponseBase)
def list_materials(query: MaterialQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Material)
    if query.material_type:
        q = q.filter(Material.material_type == query.material_type)
    if query.status:
        q = q.filter(Material.status == query.status)
    if query.keyword:
        q = q.filter(Material.name.contains(query.keyword) | Material.code.contains(query.keyword))
    total = q.count()
    items = q.order_by(Material.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[MaterialOut.model_validate(m).model_dump() for m in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/materials", response_model=ResponseBase)
def create_material(data: MaterialCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("material", "create"))):
    if db.query(Material).filter(Material.code == data.code).first():
        raise HTTPException(400, "物料编码已存在")
    m = Material(**data.model_dump())
    db.add(m); db.commit(); db.refresh(m)
    return ResponseBase(data=MaterialOut.model_validate(m).model_dump())


@router.get("/materials/{material_id}", response_model=ResponseBase)
def get_material(material_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "物料不存在")
    return ResponseBase(data=MaterialOut.model_validate(m).model_dump())


@router.put("/materials/{material_id}", response_model=ResponseBase)
def update_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("material", "update"))):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "物料不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(m, field, value)
    m.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=MaterialOut.model_validate(m).model_dump())


@router.delete("/materials/{material_id}", response_model=ResponseBase)
def delete_material(material_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("material", "delete"))):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "物料不存在")
    # 检查是否被 BomItem 引用
    ref_count = db.query(BomItem).filter(BomItem.material_id == material_id).count()
    if ref_count > 0:
        referenced_boms = db.query(BomItem).filter(BomItem.material_id == material_id).all()
        bom_ids = list(set([bi.bom_id for bi in referenced_boms]))
        bom_codes = [b.code for b in db.query(BomHeader).filter(BomHeader.id.in_(bom_ids)).all()]
        raise HTTPException(400, f"该物料被 {ref_count} 个BOM引用（{', '.join(bom_codes)}），无法停用，请先从BOM中移除")
    m.status = "inactive"
    m.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data={"msg": "已停用"})


@router.post("/materials/batch-delete", response_model=ResponseBase)
def batch_delete_materials(data: MaterialBatchDelete, db: Session = Depends(get_db), _: User = Depends(require_permission("material", "delete"))):
    """批量停用物料（含被引用检查）"""
    materials = db.query(Material).filter(Material.id.in_(data.ids)).all()
    if not materials:
        raise HTTPException(404, "未找到指定物料")
    # 检查引用
    blocked = []
    blocked_details = []
    for m in materials:
        ref_count = db.query(BomItem).filter(BomItem.material_id == m.id).count()
        if ref_count > 0:
            blocked.append(m.id)
            refs = db.query(BomHeader).filter(
                BomHeader.id.in_(db.query(BomItem.bom_id).filter(BomItem.material_id == m.id))
            ).all()
            blocked_details.append(f"  [{m.code}] {m.name} 被 {len(refs)} 个BOM引用")
    if blocked:
        raise HTTPException(400, "以下物料无法停用，请先从BOM中移除：\n" + "\n".join(blocked_details))
    # 批量停用
    now = datetime.datetime.utcnow()
    db.query(Material).filter(Material.id.in_(data.ids)).update(
        {"status": "inactive", "updated_at": now}, synchronize_session=False
    )
    db.commit()
    return ResponseBase(data={"msg": f"已停用 {len(data.ids)} 个物料"})


# ===== BOM =====
@router.get("/headers", response_model=ResponseBase)
def list_boms(query: BomQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(BomHeader)
    if query.project_id:
        q = q.filter(BomHeader.project_id == query.project_id)
    if query.status:
        q = q.filter(BomHeader.status == query.status)
    if query.keyword:
        q = q.filter(BomHeader.name.contains(query.keyword) | BomHeader.code.contains(query.keyword))
    total = q.count()
    items = q.order_by(BomHeader.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[BomHeaderOut.model_validate(b).model_dump() for b in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.post("/headers", response_model=ResponseBase)
def create_bom(data: BomHeaderCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("bom", "create"))):
    code = f"BOM{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    bom = BomHeader(
        code=code, project_id=data.project_id, name=data.name,
        description=data.description, version=data.version,
        status=data.status, product_code=data.product_code,
        remark=data.remark, created_by=current.id,
    )
    if data.items:
        for item in data.items:
            bom.items.append(BomItem(**item.model_dump()))
    db.add(bom); db.commit(); db.refresh(bom)
    return ResponseBase(data=BomHeaderOut.model_validate(bom).model_dump())


@router.get("/headers/{bom_id}", response_model=ResponseBase)
def get_bom(bom_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    return ResponseBase(data=BomHeaderOut.model_validate(bom).model_dump())


@router.put("/headers/{bom_id}", response_model=ResponseBase)
def update_bom(bom_id: int, data: BomHeaderUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "update"))):
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bom, field, value)
    bom.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=BomHeaderOut.model_validate(bom).model_dump())


@router.delete("/headers/{bom_id}", response_model=ResponseBase)
def delete_bom(bom_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "delete"))):
    """删除BOM（级联删除BOM项和变更记录），已发布/审核中的BOM禁止删除"""
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    if bom.status in ("released", "reviewing"):
        raise HTTPException(400, f"BOM状态为「{bom.status}」，无法删除，请先归档或撤销审核")
    # 解除试产记录中对本BOM的引用
    db.query(TrialProduction).filter(TrialProduction.bom_id == bom_id).update(
        {TrialProduction.bom_id: None}
    )
    db.delete(bom)
    db.commit()
    return ResponseBase(data={"msg": "BOM已删除"})


# ===== BomItem 明细管理 =====
@router.get("/headers/{bom_id}/items", response_model=ResponseBase)
def list_bom_items(bom_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    items = [{
        "id": bi.id, "bom_id": bi.bom_id, "material_id": bi.material_id,
        "line_no": bi.line_no, "quantity": bi.quantity, "unit": bi.unit,
        "loss_rate": bi.loss_rate, "level": bi.level,
        "parent_item_id": bi.parent_item_id, "remark": bi.remark, "is_key": bi.is_key,
        "material_code": bi.material.code if bi.material else "",
        "material_name": bi.material.name if bi.material else "",
        "material_spec": bi.material.spec if bi.material else "",
    } for bi in bom.items]
    return ResponseBase(data={"items": items, "bom_code": bom.code, "bom_name": bom.name})


@router.post("/headers/{bom_id}/items", response_model=ResponseBase)
def add_bom_item(bom_id: int, data: BomItemCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "create"))):
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    if bom.status in ("released",):
        raise HTTPException(400, "BOM已发布，无法直接修改明细，请通过ECN变更流程处理")
    # 验证物料存在
    if not db.query(Material).filter(Material.id == data.material_id).first():
        raise HTTPException(400, f"物料ID {data.material_id} 不存在")
    item = BomItem(bom_id=bom_id, **data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return ResponseBase(data={"id": item.id, "msg": "明细项已添加"})


@router.put("/headers/{bom_id}/items/{item_id}", response_model=ResponseBase)
def update_bom_item(bom_id: int, item_id: int, data: BomItemUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "update"))):
    item = db.query(BomItem).filter(BomItem.id == item_id, BomItem.bom_id == bom_id).first()
    if not item:
        raise HTTPException(404, "BOM明细项不存在")
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if bom and bom.status == "released":
        raise HTTPException(400, "BOM已发布，无法直接修改明细，请通过ECN变更流程处理")
    if data.material_id and not db.query(Material).filter(Material.id == data.material_id).first():
        raise HTTPException(400, f"物料ID {data.material_id} 不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    return ResponseBase(data={"msg": "明细项已更新"})


@router.delete("/headers/{bom_id}/items/{item_id}", response_model=ResponseBase)
def delete_bom_item(bom_id: int, item_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "delete"))):
    """删除单个BOM明细项，含父项引用检查"""
    item = db.query(BomItem).filter(BomItem.id == item_id, BomItem.bom_id == bom_id).first()
    if not item:
        raise HTTPException(404, "BOM明细项不存在")
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if bom and bom.status == "released":
        raise HTTPException(400, "BOM已发布，无法直接删除明细，请通过ECN变更流程处理")
    # 检查是否有子项引用此明细作为父项
    children = db.query(BomItem).filter(BomItem.parent_item_id == item_id).count()
    if children > 0:
        raise HTTPException(400, f"该明细项被 {children} 个子项引用为父项，请先解除子项的父项关联")
    db.delete(item)
    db.commit()
    return ResponseBase(data={"msg": "明细项已删除"})


@router.post("/items/batch-delete", response_model=ResponseBase)
def batch_delete_bom_items(data: BomItemBatchDelete, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "delete"))):
    """批量删除BOM明细项，含关联检查和发布状态检查"""
    items = db.query(BomItem).filter(BomItem.id.in_(data.ids)).all()
    if not items:
        raise HTTPException(404, "未找到指定明细项")
    # 检查发布状态
    bom_ids = list(set([i.bom_id for i in items]))
    released_boms = db.query(BomHeader).filter(
        BomHeader.id.in_(bom_ids), BomHeader.status == "released"
    ).all()
    if released_boms:
        codes = [b.code for b in released_boms]
        raise HTTPException(400, f"以下BOM已发布，无法直接删除明细：{', '.join(codes)}")
    # 检查子项引用
    children = db.query(BomItem).filter(BomItem.parent_item_id.in_(data.ids)).count()
    if children > 0:
        raise HTTPException(400, f"所选明细项中有被 {children} 个子项引用为父项，请先解除关联")
    deleted = db.query(BomItem).filter(BomItem.id.in_(data.ids)).delete(synchronize_session=False)
    db.commit()
    return ResponseBase(data={"msg": f"已删除 {deleted} 个明细项"})


# ===== BOM 变更 =====
@router.get("/changes", response_model=ResponseBase)
def list_bom_changes(query: BomChangeQuery = Depends(), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(BomChange)
    if query.bom_id:
        q = q.filter(BomChange.bom_id == query.bom_id)
    if query.change_type:
        q = q.filter(BomChange.change_type == query.change_type)
    if query.status:
        q = q.filter(BomChange.status == query.status)
    if query.keyword:
        q = q.filter(BomChange.title.contains(query.keyword) | BomChange.change_no.contains(query.keyword))
    total = q.count()
    items = q.order_by(BomChange.id.desc()).offset(query.offset).limit(query.limit).all()
    return ResponseBase(data=PaginationResponse(
        items=[BomChangeOut.model_validate(c).model_dump() for c in items],
        total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.get("/changes/{change_id}", response_model=ResponseBase)
def get_bom_change(change_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    chg = db.query(BomChange).filter(BomChange.id == change_id).first()
    if not chg:
        raise HTTPException(404, "变更记录不存在")
    return ResponseBase(data=BomChangeOut.model_validate(chg).model_dump())


@router.put("/changes/{change_id}", response_model=ResponseBase)
def update_bom_change(change_id: int, data: BomChangeUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "update"))):
    chg = db.query(BomChange).filter(BomChange.id == change_id).first()
    if not chg:
        raise HTTPException(404, "变更记录不存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chg, field, value)
    chg.updated_at = datetime.datetime.utcnow()
    db.commit()
    return ResponseBase(data=BomChangeOut.model_validate(chg).model_dump())


@router.post("/changes", response_model=ResponseBase)
def create_bom_change(data: BomChangeCreate, db: Session = Depends(get_db), current: User = Depends(require_permission("bom", "create"))):
    bom = db.query(BomHeader).filter(BomHeader.id == data.bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    change_no = f"ECN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    chg = BomChange(
        bom_id=data.bom_id, change_type=data.change_type,
        change_no=change_no, title=data.title,
        reason=data.reason, description=data.description,
        applicant_id=current.id,
    )
    db.add(chg); db.commit()
    return ResponseBase(data={"change_no": change_no})


@router.delete("/changes/{change_id}", response_model=ResponseBase)
def delete_bom_change(change_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("bom", "delete"))):
    chg = db.query(BomChange).filter(BomChange.id == change_id).first()
    if not chg:
        raise HTTPException(404, "变更记录不存在")
    if chg.status in ("approved", "implemented"):
        raise HTTPException(400, f"变更状态为「{chg.status}」，无法删除已审批或已实施的变更记录")
    db.delete(chg)
    db.commit()
    return ResponseBase(data={"msg": "变更记录已删除"})
