"""研发库存管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta, timezone
from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.bom import Material
from app.models.inventory import InventoryItem, InventoryTransaction, InventoryApproval, InventoryAlert, Warehouse
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemOut, InventoryItemQuery,
    InventoryTransactionCreate, InventoryTransactionOut, TransactionQuery,
    ApprovalCreate, ApprovalAction, ApprovalOut, AlertOut,
    InventoryStatsOut, WarehouseStatsOut, TurnoverReport,
    WarehouseCreate, WarehouseUpdate, WarehouseOut,
)
from app.schemas.common import ResponseBase, PaginationResponse

router = APIRouter()

# 交易类型中文映射
TX_TYPE_MAP = {
    "inbound": "入库", "outbound": "出库", "borrow": "领用",
    "return_transfer": "归还", "check": "盘点",
    "transfer_in": "调拨入库", "transfer_out": "调拨出库", "adjust": "调整",
}

# ===== 工具函数 =====
def _generate_tx_no(tx_type: str, db: Session) -> str:
    """生成交易单号: INV{类型缩写}{日期}{序号}（使用原子锁避免并发重复）"""
    prefix_map = {"inbound": "IN", "outbound": "OUT", "borrow": "BRW", "return_transfer": "RTN",
                  "check": "CHK", "transfer_in": "TIN", "transfer_out": "TOU", "adjust": "ADJ"}
    prefix = prefix_map.get(tx_type, "TXN")
    today = datetime.now().strftime("%Y%m%d")

    # 使用 FOR UPDATE 锁定查询防止并发重复
    count = db.query(InventoryTransaction).filter(
        InventoryTransaction.transaction_no.like(f"{prefix}{today}%")
    ).with_for_update().count()
    return f"{prefix}{today}{count + 1:04d}"


def _check_low_stock(item: InventoryItem):
    """检查并更新库存状态"""
    if item.quantity <= 0:
        item.status = "out_of_stock"
    elif item.safety_stock > 0 and item.quantity <= item.safety_stock:
        item.status = "low_stock"
    elif item.expiry_date and item.expiry_date <= date.today():
        item.status = "expired"
    else:
        item.status = "normal"


def _create_alert(db: Session, item: InventoryItem, alert_type: str):
    """创建库存预警"""
    material_name = item.material.name if item.material else f"物料#{item.material_id}"
    msgs = {
        "low_stock": f"「{material_name}」库存不足：当前{item.quantity}{item.unit or '个'}，安全库存{item.safety_stock}{item.unit or '个'}",
        "out_of_stock": f"「{material_name}」库存已耗尽，请及时补货",
        "expiry": f"「{material_name}」已过保质期（{item.expiry_date}），请检查处理",
    }
    alert = InventoryAlert(
        inventory_item_id=item.id,
        alert_type=alert_type,
        message=msgs.get(alert_type, f"库存预警: {material_name}"),
    )
    db.add(alert)


def _enrich_tx(tx: InventoryTransaction) -> dict:
    """补充交易记录中的物料和仓库信息"""
    item = tx.inventory_item
    result = {
        "id": tx.id, "transaction_no": tx.transaction_no,
        "inventory_item_id": tx.inventory_item_id,
        "transaction_type": tx.transaction_type,
        "quantity": tx.quantity, "before_qty": tx.before_qty, "after_qty": tx.after_qty,
        "source_warehouse": tx.source_warehouse, "target_warehouse": tx.target_warehouse,
        "related_project_id": tx.related_project_id,
        "related_project_name": tx.related_project.name if tx.related_project else None,
        "related_department_id": tx.related_department_id,
        "related_department_name": tx.related_department.name if tx.related_department else None,
        "operator_id": tx.operator_id,
        "operator_name": tx.operator.real_name if tx.operator else None,
        "borrower_id": tx.borrower_id, "borrower_name": tx.borrower_name,
        "expected_return_date": tx.expected_return_date,
        "actual_return_date": tx.actual_return_date,
        "approval_status": tx.approval_status,
        "remark": tx.remark, "created_at": tx.created_at,
        "material_code": item.material.code if item and item.material else None,
        "material_name": item.material.name if item and item.material else None,
        "warehouse": item.warehouse if item else None,
        "unit": item.unit if item else None,
    }
    return result


# ==================== 仓库管理 ====================

@router.get("/warehouses/list", response_model=ResponseBase)
def list_all_warehouses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """仓库管理列表（完整信息）"""
    whs = db.query(Warehouse).order_by(Warehouse.id).all()
    return ResponseBase(data=[WarehouseOut.model_validate(w).model_dump() for w in whs])


@router.post("/warehouses/create", response_model=ResponseBase)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db),
                     _: User = Depends(require_permission("warehouse", "create"))):
    """新增仓库"""
    if db.query(Warehouse).filter(Warehouse.code == data.code).first():
        raise HTTPException(400, f"仓库编码「{data.code}」已存在")
    if db.query(Warehouse).filter(Warehouse.name == data.name).first():
        raise HTTPException(400, f"仓库名称「{data.name}」已存在")
    wh = Warehouse(**data.model_dump())
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return ResponseBase(data={"id": wh.id, "msg": "仓库创建成功"})


@router.put("/warehouses/{wh_id}", response_model=ResponseBase)
def update_warehouse(wh_id: int, data: WarehouseUpdate, db: Session = Depends(get_db),
                     _: User = Depends(require_permission("warehouse", "update"))):
    """编辑仓库"""
    wh = db.query(Warehouse).filter(Warehouse.id == wh_id).first()
    if not wh:
        raise HTTPException(404, "仓库不存在")

    update_data = data.model_dump(exclude_unset=True)

    # 唯一性检查
    if "name" in update_data and update_data["name"] != wh.name:
        if db.query(Warehouse).filter(Warehouse.name == update_data["name"]).first():
            raise HTTPException(400, f"仓库名称「{update_data['name']}」已存在")
    if "code" in update_data and update_data["code"] != wh.code:
        if db.query(Warehouse).filter(Warehouse.code == update_data["code"]).first():
            raise HTTPException(400, f"仓库编码「{update_data['code']}」已存在")

    old_name = wh.name
    for field, value in update_data.items():
        setattr(wh, field, value)
    wh.updated_at = datetime.utcnow()

    # 如果仓库名称变更，同步更新关联数据中的仓库名
    new_name = wh.name
    if old_name != new_name:
        # 更新 InventoryItem 中的 warehouse 字段
        db.query(InventoryItem).filter(
            InventoryItem.warehouse == old_name
        ).update({InventoryItem.warehouse: new_name}, synchronize_session=False)
        # 更新 InventoryTransaction 中的 source_warehouse
        db.query(InventoryTransaction).filter(
            InventoryTransaction.source_warehouse == old_name
        ).update({InventoryTransaction.source_warehouse: new_name}, synchronize_session=False)
        # 更新 InventoryTransaction 中的 target_warehouse
        db.query(InventoryTransaction).filter(
            InventoryTransaction.target_warehouse == old_name
        ).update({InventoryTransaction.target_warehouse: new_name}, synchronize_session=False)

    db.commit()
    return ResponseBase(data={"msg": "更新成功"})


@router.delete("/warehouses/{wh_id}", response_model=ResponseBase)
def delete_warehouse(wh_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_permission("warehouse", "delete"))):
    """删除仓库（需先清空该仓库下的库存）"""
    wh = db.query(Warehouse).filter(Warehouse.id == wh_id).first()
    if not wh:
        raise HTTPException(404, "仓库不存在")

    # 检查库存记录
    item_count = db.query(InventoryItem).filter(InventoryItem.warehouse == wh.name).count()
    if item_count > 0:
        raise HTTPException(400, f"仓库「{wh.name}」下还有 {item_count} 条库存记录，请先处理后再删除")

    # 检查交易记录中的仓库引用
    tx_src = db.query(InventoryTransaction).filter(
        InventoryTransaction.source_warehouse == wh.name
    ).count()
    tx_tgt = db.query(InventoryTransaction).filter(
        InventoryTransaction.target_warehouse == wh.name
    ).count()
    if tx_src > 0 or tx_tgt > 0:
        raise HTTPException(400, f"仓库「{wh.name}」关联了 {tx_src + tx_tgt} 条交易记录，请先处理后再删除")

    db.delete(wh)
    db.commit()
    return ResponseBase(data={"msg": "已删除"})


# ==================== 库存管理 ====================

@router.get("/list", response_model=ResponseBase)
def list_inventory(query: InventoryItemQuery = Depends(), db: Session = Depends(get_db),
                   _: User = Depends(get_current_user)):
    """库存列表"""
    q = db.query(InventoryItem)

    # 统一 join Material（仅当需要时）
    need_material = bool(query.keyword) or bool(query.material_type)
    if need_material:
        q = q.join(Material, InventoryItem.material_id == Material.id)

    if query.keyword:
        q = q.filter(or_(Material.code.contains(query.keyword), Material.name.contains(query.keyword)))
    if query.warehouse:
        q = q.filter(InventoryItem.warehouse == query.warehouse)
    if query.status:
        q = q.filter(InventoryItem.status == query.status)
    if query.low_stock_only:
        q = q.filter(InventoryItem.status.in_(["low_stock", "out_of_stock"]))
    if query.material_type:
        q = q.filter(Material.material_type == query.material_type)

    total = q.count()
    items = q.order_by(InventoryItem.id.desc()).offset(query.offset).limit(query.limit).all()

    result = []
    for item in items:
        mat = item.material
        creator = item.creator
        result.append(InventoryItemOut(
            id=item.id, material_id=item.material_id, warehouse=item.warehouse,
            location=item.location, quantity=item.quantity, reserved_qty=item.reserved_qty,
            safety_stock=item.safety_stock, max_stock=item.max_stock,
            unit=item.unit, status=item.status,
            shelf_life_days=item.shelf_life_days, expiry_date=item.expiry_date,
            remark=item.remark, created_at=item.created_at, updated_at=item.updated_at,
            material_code=mat.code if mat else None,
            material_name=mat.name if mat else None,
            material_spec=mat.spec if mat else None,
            material_type=mat.material_type if mat else None,
            creator_name=creator.real_name if creator else None,
        ).model_dump())

    return ResponseBase(data=PaginationResponse(
        items=result, total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.get("/warehouses", response_model=ResponseBase)
def list_warehouses_legacy(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """仓库列表（去重，旧接口兼容）"""
    warehouses = db.query(InventoryItem.warehouse).distinct().all()
    return ResponseBase(data=[w[0] for w in warehouses if w[0]])


@router.post("/create", response_model=ResponseBase)
def create_inventory(data: InventoryItemCreate, db: Session = Depends(get_db),
                     current: User = Depends(require_permission("inventory", "create"))):
    """创建库存记录（含初始入库交易）"""
    if not db.query(Material).filter(Material.id == data.material_id).first():
        raise HTTPException(400, "物料不存在")

    # 校验仓库是否存在且启用
    wh = db.query(Warehouse).filter(Warehouse.name == data.warehouse, Warehouse.is_active == True).first()
    if not wh:
        raise HTTPException(400, f"仓库「{data.warehouse}」不存在或已停用")

    # 检查同物料同仓库是否已存在
    existing = db.query(InventoryItem).filter(
        InventoryItem.material_id == data.material_id,
        InventoryItem.warehouse == data.warehouse,
    ).first()
    if existing:
        raise HTTPException(400, f"该物料在仓库「{data.warehouse}」已存在库存记录")

    item = InventoryItem(
        material_id=data.material_id, warehouse=data.warehouse,
        location=data.location, quantity=data.quantity,
        reserved_qty=0.0,
        safety_stock=data.safety_stock, max_stock=data.max_stock,
        unit=data.unit, shelf_life_days=data.shelf_life_days,
        expiry_date=data.expiry_date, remark=data.remark,
        created_by=current.id,
    )
    _check_low_stock(item)
    db.add(item)
    db.flush()

    # 如果有初始数量，创建入库交易记录
    if data.quantity > 0:
        tx = InventoryTransaction(
            transaction_no=_generate_tx_no("inbound", db),
            inventory_item_id=item.id,
            transaction_type="inbound",
            quantity=data.quantity,
            before_qty=0,
            after_qty=data.quantity,
            operator_id=current.id,
            approval_status="completed",
            remark="初始库存入库",
        )
        db.add(tx)

    db.commit()
    db.refresh(item)
    return ResponseBase(data={"id": item.id, "msg": "库存创建成功"})

# ==================== 库存操作 ====================

def _do_transaction_inner(
    db: Session, item_id: int, tx_type: str, quantity: float,
    operator_id: int, approval_required: bool = False,
    **kwargs
) -> InventoryTransaction:
    """交易执行内部函数：仅 flush 不 commit，由调用方决定提交时机
    使用 FOR UPDATE 行锁 + 原子更新库存（MySQL 生效；SQLite 静默忽略）
    """
    # SELECT ... FOR UPDATE 防止并发竞态
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(404, "库存记录不存在")

    old_qty = item.quantity
    new_qty = old_qty + quantity
    if new_qty < 0:
        raise HTTPException(400, f"库存不足：当前{item.quantity}{item.unit or ''}，本次操作{abs(quantity)}{item.unit or ''}")

    # 原子更新库存
    item.quantity = new_qty
    if tx_type in ("borrow",):
        item.reserved_qty = (item.reserved_qty or 0) + abs(quantity)
    elif tx_type in ("return_transfer",):
        item.reserved_qty = max(0, (item.reserved_qty or 0) - abs(quantity))

    _check_low_stock(item)

    # 生成交易单号
    tx_no = _generate_tx_no(tx_type, db)

    # 审批状态
    approval_status = "pending" if approval_required else "completed"

    tx = InventoryTransaction(
        transaction_no=tx_no,
        inventory_item_id=item_id,
        transaction_type=tx_type,
        quantity=quantity,
        before_qty=old_qty,
        after_qty=new_qty,
        operator_id=operator_id,
        approval_status=approval_status,
        **kwargs,
    )
    db.add(tx)
    db.flush()

    # 低库存/缺货预警
    if item.status in ("low_stock", "out_of_stock"):
        _create_alert(db, item, item.status)

    return tx


def _do_transaction(
    db: Session, item_id: int, tx_type: str, quantity: float,
    operator_id: int, approval_required: bool = False,
    **kwargs
) -> InventoryTransaction:
    """通用交易执行：单步操作自动 commit（入库/出库/领用/归还/盘点等使用）
    调拨等多步操作应调用 _do_transaction_inner 并由调用方统一 commit
    """
    tx = _do_transaction_inner(
        db, item_id, tx_type, quantity, operator_id, approval_required, **kwargs
    )
    db.commit()
    return tx


@router.post("/inbound", response_model=ResponseBase)
def inbound(data: InventoryTransactionCreate, db: Session = Depends(get_db),
            current: User = Depends(require_permission("inventory", "create"))):
    """入库 — 增加库存"""
    if data.quantity <= 0:
        raise HTTPException(400, "入库数量必须大于0")
    tx = _do_transaction(
        db, data.inventory_item_id, "inbound", abs(data.quantity),
        current.id, approval_required=data.approval_required,
        related_project_id=data.related_project_id,
        remark=data.remark,
    )
    return ResponseBase(data={"id": tx.id, "transaction_no": tx.transaction_no, "msg": "入库成功"})


@router.post("/outbound", response_model=ResponseBase)
def outbound(data: InventoryTransactionCreate, db: Session = Depends(get_db),
             current: User = Depends(require_permission("inventory", "update"))):
    """出库 — 减少库存"""
    if data.quantity <= 0:
        raise HTTPException(400, "出库数量必须大于0")
    tx = _do_transaction(
        db, data.inventory_item_id, "outbound", -abs(data.quantity),
        current.id, approval_required=data.approval_required,
        related_project_id=data.related_project_id,
        related_department_id=data.related_department_id,
        remark=data.remark,
    )
    return ResponseBase(data={"id": tx.id, "transaction_no": tx.transaction_no, "msg": "出库成功"})


@router.post("/borrow", response_model=ResponseBase)
def borrow(data: InventoryTransactionCreate, db: Session = Depends(get_db),
           current: User = Depends(require_permission("inventory", "update"))):
    """领用 — 减少可用库存，增加预留"""
    if data.quantity <= 0:
        raise HTTPException(400, "领用数量必须大于0")
    tx = _do_transaction(
        db, data.inventory_item_id, "borrow", -abs(data.quantity),
        current.id, approval_required=data.approval_required,
        borrower_id=data.borrower_id or current.id,
        borrower_name=data.borrower_name or current.real_name,
        expected_return_date=data.expected_return_date,
        related_project_id=data.related_project_id,
        related_department_id=data.related_department_id,
        remark=data.remark,
    )
    return ResponseBase(data={"id": tx.id, "transaction_no": tx.transaction_no, "msg": "领用成功"})


@router.post("/return", response_model=ResponseBase)
def return_transfer(data: InventoryTransactionCreate, db: Session = Depends(get_db),
                    current: User = Depends(require_permission("inventory", "update"))):
    """归还 — 增加库存，减少预留"""
    if data.quantity <= 0:
        raise HTTPException(400, "归还数量必须大于0")
    tx = _do_transaction(
        db, data.inventory_item_id, "return_transfer", abs(data.quantity),
        current.id,
        borrower_id=data.borrower_id or current.id,
        borrower_name=data.borrower_name or current.real_name,
        actual_return_date=date.today(),
        remark=data.remark,
    )
    return ResponseBase(data={"id": tx.id, "transaction_no": tx.transaction_no, "msg": "归还成功"})


@router.post("/check", response_model=ResponseBase)
def check_inventory(data: InventoryTransactionCreate, db: Session = Depends(get_db),
                    current: User = Depends(require_permission("inventory", "update"))):
    """盘点 — 差异调整"""
    item = db.query(InventoryItem).filter(InventoryItem.id == data.inventory_item_id).first()
    if not item:
        raise HTTPException(404, "库存记录不存在")

    diff = data.quantity - item.quantity  # data.quantity 是盘点数量
    if diff == 0:
        return ResponseBase(data={"msg": "盘点一致，无需调整"})

    old_qty = item.quantity
    item.quantity = data.quantity
    _check_low_stock(item)

    tx_no = _generate_tx_no("check", db)
    tx = InventoryTransaction(
        transaction_no=tx_no, inventory_item_id=data.inventory_item_id,
        transaction_type="check", quantity=diff,
        before_qty=old_qty, after_qty=data.quantity,
        operator_id=current.id, approval_status="completed",
        remark=f"盘点调整: {data.remark or ''}",
    )
    db.add(tx)

    if item.status in ("low_stock", "out_of_stock"):
        _create_alert(db, item, item.status)

    db.commit()
    msg = f"盘点调整：{'盘盈' if diff > 0 else '盘亏'}{abs(diff)}{item.unit or ''}"
    return ResponseBase(data={"id": tx.id, "transaction_no": tx_no, "msg": msg})


@router.post("/transfer", response_model=ResponseBase)
def transfer(data: InventoryTransactionCreate, db: Session = Depends(get_db),
             current: User = Depends(require_permission("inventory", "update"))):
    """调拨 — 从一个仓库转移到另一个（同一事务保证原子性）"""
    if not data.source_warehouse or not data.target_warehouse:
        raise HTTPException(400, "请指定来源仓库和目标仓库")
    if data.source_warehouse == data.target_warehouse:
        raise HTTPException(400, "来源仓库和目标仓库不能相同")
    if data.quantity <= 0:
        raise HTTPException(400, "调拨数量必须大于0")

    # 校验目标仓库存在
    tgt_wh = db.query(Warehouse).filter(
        Warehouse.name == data.target_warehouse, Warehouse.is_active == True
    ).first()
    if not tgt_wh:
        raise HTTPException(400, f"目标仓库「{data.target_warehouse}」不存在或已停用")

    src_item = db.query(InventoryItem).filter(
        InventoryItem.id == data.inventory_item_id
    ).with_for_update().first()
    if not src_item:
        raise HTTPException(404, "来源库存记录不存在")

    qty = abs(data.quantity)

    # 整个调拨操作在一个事务中：先出库、后查找/创建目标库存、再入库，统一 commit
    try:
        # 出库（仅 flush 不 commit，确保后续失败可回滚）
        tx_out = _do_transaction_inner(
            db, data.inventory_item_id, "transfer_out", -qty,
            current.id, source_warehouse=data.source_warehouse,
            target_warehouse=data.target_warehouse,
            remark=f"调拨至 {data.target_warehouse}: {data.remark or ''}",
        )

        # 查找或创建目标仓库的库存记录
        tgt_item = db.query(InventoryItem).filter(
            InventoryItem.material_id == src_item.material_id,
            InventoryItem.warehouse == data.target_warehouse,
        ).with_for_update().first()
        if not tgt_item:
            tgt_item = InventoryItem(
                material_id=src_item.material_id, warehouse=data.target_warehouse,
                unit=src_item.unit, safety_stock=src_item.safety_stock,
                created_by=current.id,
            )
            db.add(tgt_item)
            db.flush()

        # 入库（仅 flush 不 commit）
        tx_in = _do_transaction_inner(
            db, tgt_item.id, "transfer_in", qty,
            current.id, source_warehouse=data.source_warehouse,
            target_warehouse=data.target_warehouse,
            remark=f"从 {data.source_warehouse} 调入: {data.remark or ''}",
        )

        # 两步都成功后统一提交
        db.commit()
        return ResponseBase(data={
            "out_id": tx_out.id, "out_no": tx_out.transaction_no,
            "in_id": tx_in.id, "in_no": tx_in.transaction_no,
            "msg": f"调拨完成: {data.source_warehouse} → {data.target_warehouse}, 数量{qty}",
        })
    except Exception:
        db.rollback()
        raise


# ==================== 交易记录 ====================

@router.get("/transactions", response_model=ResponseBase)
def list_transactions(query: TransactionQuery = Depends(), db: Session = Depends(get_db),
                      _: User = Depends(get_current_user)):
    """交易记录列表"""
    q = db.query(InventoryTransaction)
    if query.inventory_item_id:
        q = q.filter(InventoryTransaction.inventory_item_id == query.inventory_item_id)
    if query.transaction_type:
        q = q.filter(InventoryTransaction.transaction_type == query.transaction_type)
    if query.approval_status:
        q = q.filter(InventoryTransaction.approval_status == query.approval_status)
    if query.related_project_id:
        q = q.filter(InventoryTransaction.related_project_id == query.related_project_id)
    if query.keyword:
        q = q.join(InventoryItem).join(Material).filter(
            or_(Material.code.contains(query.keyword), Material.name.contains(query.keyword))
        )
    if query.date_from:
        q = q.filter(InventoryTransaction.created_at >= query.date_from)
    if query.date_to:
        q = q.filter(InventoryTransaction.created_at <= query.date_to + timedelta(days=1))

    total = q.count()
    txs = q.order_by(InventoryTransaction.id.desc()).offset(query.offset).limit(query.limit).all()
    result = [_enrich_tx(tx) for tx in txs]

    return ResponseBase(data=PaginationResponse(
        items=result, total=total, page=query.page, page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size,
    ).model_dump())


@router.get("/transactions/{tx_id}", response_model=ResponseBase)
def get_transaction(tx_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tx = db.query(InventoryTransaction).filter(InventoryTransaction.id == tx_id).first()
    if not tx:
        raise HTTPException(404, "交易记录不存在")
    result = _enrich_tx(tx)
    # 附加审批记录
    approvals = db.query(InventoryApproval).filter(
        InventoryApproval.transaction_id == tx_id
    ).order_by(InventoryApproval.approval_level).all()
    result["approvals"] = [
        {"id": a.id, "approval_level": a.approval_level, "approver_name": a.approver_name,
         "status": a.status, "comment": a.comment, "created_at": str(a.created_at),
         "approved_at": str(a.approved_at) if a.approved_at else None}
        for a in approvals
    ]
    return ResponseBase(data=result)


# ==================== 审批 ====================

@router.post("/approvals/{tx_id}/submit", response_model=ResponseBase)
def submit_approval(tx_id: int, data: ApprovalCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_permission("inventory", "update"))):
    """提交审批"""
    tx = db.query(InventoryTransaction).filter(InventoryTransaction.id == tx_id).first()
    if not tx:
        raise HTTPException(404, "交易记录不存在")
    if tx.approval_status != "pending":
        raise HTTPException(400, "该交易当前状态不可提交审批")

    approval = InventoryApproval(
        transaction_id=tx_id, approval_level=data.approval_level,
        approver_id=data.approver_id, approver_name=data.approver_name,
    )
    db.add(approval)
    db.commit()
    return ResponseBase(data={"id": approval.id, "msg": "审批已提交"})


@router.put("/approvals/{approval_id}/action", response_model=ResponseBase)
def handle_approval(approval_id: int, data: ApprovalAction, db: Session = Depends(get_db),
                    current: User = Depends(require_permission("inventory", "approve"))):
    """审批操作"""
    approval = db.query(InventoryApproval).filter(InventoryApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(404, "审批记录不存在")
    if approval.status != "pending":
        raise HTTPException(400, "该审批已处理")

    approval.status = data.status
    approval.approved_at = datetime.utcnow()
    if data.comment:
        approval.comment = data.comment

    tx = db.query(InventoryTransaction).filter(InventoryTransaction.id == approval.transaction_id).first()
    if data.status == "approved":
        tx.approval_status = "approved"
    elif data.status == "rejected":
        tx.approval_status = "rejected"
        # 回滚库存（加行锁防止并发，MySQL 生效）
        item = db.query(InventoryItem).filter(
            InventoryItem.id == tx.inventory_item_id
        ).with_for_update().first()
        if item:
            item.quantity -= tx.quantity
            if tx.transaction_type in ("borrow",):
                item.reserved_qty = max(0, (item.reserved_qty or 0) - abs(tx.quantity))
            _check_low_stock(item)

    db.commit()
    return ResponseBase(data={"msg": "审批完成"})


@router.get("/approvals/pending", response_model=ResponseBase)
def list_pending_approvals(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """待审批列表"""
    txs = db.query(InventoryTransaction).filter(
        InventoryTransaction.approval_status == "pending"
    ).order_by(InventoryTransaction.created_at.desc()).all()
    result = [_enrich_tx(tx) for tx in txs]
    return ResponseBase(data=result)


# ==================== 预警 ====================

@router.get("/alerts", response_model=ResponseBase)
def list_alerts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """预警列表"""
    alerts = db.query(InventoryAlert).order_by(InventoryAlert.id.desc()).limit(200).all()
    result = []
    for a in alerts:
        item = a.inventory_item
        mat = item.material if item else None
        result.append({
            "id": a.id, "inventory_item_id": a.inventory_item_id,
            "alert_type": a.alert_type, "message": a.message,
            "is_read": a.is_read, "is_resolved": a.is_resolved,
            "created_at": str(a.created_at),
            "material_code": mat.code if mat else None,
            "material_name": mat.name if mat else None,
            "warehouse": item.warehouse if item else None,
        })
    return ResponseBase(data=result)


@router.put("/alerts/{alert_id}/read", response_model=ResponseBase)
def mark_alert_read(alert_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("inventory", "update"))):
    alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "预警记录不存在")
    alert.is_read = 1
    db.commit()
    return ResponseBase(data={"msg": "已标记已读"})


@router.put("/alerts/{alert_id}/resolve", response_model=ResponseBase)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("inventory", "update"))):
    alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "预警记录不存在")
    alert.is_resolved = 1
    alert.is_read = 1
    db.commit()
    return ResponseBase(data={"msg": "已处理"})


@router.get("/alerts/summary", response_model=ResponseBase)
def alert_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """预警汇总"""
    unread = db.query(InventoryAlert).filter(InventoryAlert.is_read == 0).count()
    unresolved = db.query(InventoryAlert).filter(InventoryAlert.is_resolved == 0).count()
    return ResponseBase(data={
        "unread": unread, "unresolved": unresolved,
        "total": db.query(InventoryAlert).count(),
    })


# ==================== 统计分析 ====================

@router.get("/stats/overview", response_model=ResponseBase)
def inventory_overview(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """库存总览"""
    items = db.query(InventoryItem).all()
    total_items = len(items)
    total_qty = sum(i.quantity for i in items)
    normal = sum(1 for i in items if i.status == "normal")
    low = sum(1 for i in items if i.status == "low_stock")
    out = sum(1 for i in items if i.status == "out_of_stock")
    expired = sum(1 for i in items if i.status == "expired")

    return ResponseBase(data={
        "total_items": total_items, "total_quantity": round(total_qty, 2),
        "normal_count": normal, "low_stock_count": low,
        "out_of_stock_count": out, "expired_count": expired,
    })


@router.get("/stats/by-warehouse", response_model=ResponseBase)
def stats_by_warehouse(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """按仓库统计"""
    rows = db.query(
        InventoryItem.warehouse,
        func.count(InventoryItem.id).label("item_count"),
        func.sum(InventoryItem.quantity).label("total_qty"),
    ).group_by(InventoryItem.warehouse).all()

    result = []
    for r in rows:
        low_count = db.query(InventoryItem).filter(
            InventoryItem.warehouse == r[0],
            InventoryItem.status.in_(["low_stock", "out_of_stock"])
        ).count()
        result.append({
            "warehouse": r[0], "item_count": r[1],
            "total_quantity": round(float(r[2] or 0), 2),
            "low_stock_count": low_count,
        })

    return ResponseBase(data=result)


@router.get("/stats/turnover", response_model=ResponseBase)
def turnover_report(days: int = 30, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """周转分析（默认最近30天）"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    items = db.query(InventoryItem).all()
    result = []

    for item in items:
        txs = db.query(InventoryTransaction).filter(
            InventoryTransaction.inventory_item_id == item.id,
            InventoryTransaction.created_at >= cutoff,
            InventoryTransaction.approval_status.in_(["completed", "approved"]),
        ).all()

        period_in = sum(t.quantity for t in txs if t.quantity > 0)
        period_out = sum(abs(t.quantity) for t in txs if t.quantity < 0)
        begin_qty = item.quantity + period_out - period_in
        end_qty = item.quantity
        avg_qty = (begin_qty + end_qty) / 2 if (begin_qty + end_qty) > 0 else 1
        turnover = period_out / avg_qty if avg_qty > 0 else 0

        mat = item.material
        result.append({
            "material_code": mat.code if mat else "",
            "material_name": mat.name if mat else "",
            "warehouse": item.warehouse,
            "period_in": round(period_in, 2), "period_out": round(period_out, 2),
            "begin_qty": round(begin_qty, 2), "end_qty": round(end_qty, 2),
            "avg_qty": round(avg_qty, 2),
            "turnover_rate": round(turnover, 2),
        })

    # 按周转率降序
    result.sort(key=lambda x: x["turnover_rate"], reverse=True)
    return ResponseBase(data={"days": days, "items": result})


# ==================== 单条 CRUD（必须放在所有具体路由之后，避免 /{item_id} 拦截 /stats/* 等） ====================

@router.get("/{item_id}", response_model=ResponseBase)
def get_inventory(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "库存记录不存在")
    mat = item.material
    return ResponseBase(data={
        "id": item.id, "material_id": item.material_id, "warehouse": item.warehouse,
        "location": item.location, "quantity": item.quantity, "reserved_qty": item.reserved_qty,
        "safety_stock": item.safety_stock, "max_stock": item.max_stock,
        "unit": item.unit, "status": item.status,
        "shelf_life_days": item.shelf_life_days, "expiry_date": item.expiry_date,
        "remark": item.remark, "created_at": str(item.created_at), "updated_at": str(item.updated_at),
        "material_code": mat.code if mat else None,
        "material_name": mat.name if mat else None,
        "material_spec": mat.spec if mat else None,
        "material_type": mat.material_type if mat else None,
    })


@router.put("/{item_id}", response_model=ResponseBase)
def update_inventory(item_id: int, data: InventoryItemUpdate, db: Session = Depends(get_db),
                     _: User = Depends(require_permission("inventory", "update"))):
    """更新库存元数据（禁止直接修改数量——数量变更必须通过交易接口）"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "库存记录不存在")

    update_data = data.model_dump(exclude_unset=True)

    # 禁止直接修改 quantity —— 必须通过交易接口
    if "quantity" in update_data and update_data["quantity"] != item.quantity:
        raise HTTPException(400, "禁止直接修改库存数量，请使用入库/出库/盘点接口")

    for field, value in update_data.items():
        setattr(item, field, value)
    _check_low_stock(item)
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    return ResponseBase(data={"msg": "更新成功"})


@router.delete("/{item_id}", response_model=ResponseBase)
def delete_inventory(item_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_permission("inventory", "delete"))):
    """删除库存记录 — 仅当无库存且无交易记录时允许"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "库存记录不存在")
    if item.quantity > 0:
        raise HTTPException(400, f"该物料当前库存为{item.quantity}，请先清空库存后再删除")

    # 检查是否存在交易记录
    tx_count = db.query(InventoryTransaction).filter(
        InventoryTransaction.inventory_item_id == item_id
    ).count()
    if tx_count > 0:
        raise HTTPException(400, f"该库存记录关联了 {tx_count} 条交易记录，建议归档而非删除")

    db.delete(item)
    db.commit()
    return ResponseBase(data={"msg": "已删除"})
