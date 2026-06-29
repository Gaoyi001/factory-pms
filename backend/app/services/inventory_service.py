"""库存管理 Service 层

将业务逻辑从路由层分离，提升可测试性和可复用性。
"""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException

from app.models.inventory import InventoryItem, InventoryTransaction, InventoryAlert, Warehouse
from app.models.bom import Material
from app.models.user import User
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemQuery,
    InventoryTransactionCreate, TransactionQuery,
    WarehouseCreate, WarehouseUpdate,
)
from app.core.constants import (
    InventoryStatus, TransactionType, ApprovalStatus, AlertType,
    TX_TYPE_DISPLAY,
)


class InventoryService:
    """库存管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def _generate_tx_no(self, tx_type: str) -> str:
        """生成交易单号"""
        prefix_map = {"inbound": "IN", "outbound": "OUT", "borrow": "BRW", "return_transfer": "RTN",
                      "check": "CHK", "transfer_in": "TIN", "transfer_out": "TOU", "adjust": "ADJ"}
        prefix = prefix_map.get(tx_type, "TXN")
        today = datetime.now().strftime("%Y%m%d")
        count = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.transaction_no.like(f"{prefix}{today}%")
        ).with_for_update().count()
        return f"{prefix}{today}{count + 1:04d}"

    def _check_low_stock(self, item: InventoryItem):
        """检查并更新库存状态"""
        if item.quantity <= 0:
            item.status = InventoryStatus.OUT_OF_STOCK
        elif item.safety_stock > 0 and item.quantity <= item.safety_stock:
            item.status = InventoryStatus.LOW_STOCK
        elif item.expiry_date and item.expiry_date <= date.today():
            item.status = InventoryStatus.EXPIRED
        else:
            item.status = InventoryStatus.NORMAL

    def _create_alert(self, item: InventoryItem, alert_type: str):
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
        self.db.add(alert)

    def _do_transaction_inner(
        self, item_id: int, tx_type: str, quantity: float,
        operator_id: int, approval_required: bool = False,
        **kwargs
    ) -> InventoryTransaction:
        """交易执行内部函数：仅 flush 不 commit"""
        item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(404, "库存记录不存在")

        old_qty = item.quantity
        new_qty = old_qty + quantity
        if new_qty < 0:
            raise HTTPException(400, f"库存不足：当前{item.quantity}{item.unit or ''}，本次操作{abs(quantity)}{item.unit or ''}")

        old_version = item.version

        item.quantity = new_qty
        item.version = old_version + 1
        if tx_type in ("borrow",):
            item.reserved_qty = (item.reserved_qty or 0) + abs(quantity)
        elif tx_type in ("return_transfer",):
            item.reserved_qty = max(0, (item.reserved_qty or 0) - abs(quantity))

        self._check_low_stock(item)

        tx_no = self._generate_tx_no(tx_type)
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
        self.db.add(tx)

        rows_updated = self.db.query(InventoryItem).filter(
            InventoryItem.id == item_id,
            InventoryItem.version == old_version
        ).update({"quantity": new_qty, "version": old_version + 1, "updated_at": datetime.utcnow()})

        if rows_updated == 0:
            self.db.rollback()
            raise HTTPException(409, "库存数据已被其他操作修改，请刷新后重试")

        self.db.flush()

        if item.status in (InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK):
            self._create_alert(item, item.status)

        return tx

    def _do_transaction(
        self, item_id: int, tx_type: str, quantity: float,
        operator_id: int, approval_required: bool = False,
        **kwargs
    ) -> InventoryTransaction:
        """通用交易执行：单步操作自动 commit"""
        tx = self._do_transaction_inner(
            item_id, tx_type, quantity, operator_id, approval_required, **kwargs
        )
        self.db.commit()
        return tx

    def _enrich_tx(self, tx: InventoryTransaction) -> dict:
        """补充交易记录中的物料和仓库信息"""
        item = tx.inventory_item
        return {
            "id": tx.id, "transaction_no": tx.transaction_no,
            "inventory_item_id": tx.inventory_item_id,
            "transaction_type": tx.transaction_type,
            "quantity": tx.quantity, "before_qty": tx.before_qty, "after_qty": tx.after_qty,
            "source_warehouse_id": tx.source_warehouse_id,
            "source_warehouse_name": tx.source_warehouse.name if tx.source_warehouse else None,
            "target_warehouse_id": tx.target_warehouse_id,
            "target_warehouse_name": tx.target_warehouse.name if tx.target_warehouse else None,
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
            "warehouse_id": item.warehouse_id if item else None,
            "warehouse_name": item.warehouse.name if item and item.warehouse else None,
            "unit": item.unit if item else None,
        }

    # ===== 仓库管理 =====
    def list_warehouses(self):
        return self.db.query(Warehouse).order_by(Warehouse.id).all()

    def create_warehouse(self, data: WarehouseCreate):
        if self.db.query(Warehouse).filter(Warehouse.code == data.code).first():
            raise HTTPException(400, f"仓库编码「{data.code}」已存在")
        if self.db.query(Warehouse).filter(Warehouse.name == data.name).first():
            raise HTTPException(400, f"仓库名称「{data.name}」已存在")
        wh = Warehouse(**data.model_dump())
        self.db.add(wh)
        self.db.commit()
        self.db.refresh(wh)
        return wh

    def update_warehouse(self, wh_id: int, data: WarehouseUpdate):
        wh = self.db.query(Warehouse).filter(Warehouse.id == wh_id).first()
        if not wh:
            raise HTTPException(404, "仓库不存在")

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != wh.name:
            if self.db.query(Warehouse).filter(Warehouse.name == update_data["name"]).first():
                raise HTTPException(400, f"仓库名称「{update_data['name']}」已存在")
        if "code" in update_data and update_data["code"] != wh.code:
            if self.db.query(Warehouse).filter(Warehouse.code == update_data["code"]).first():
                raise HTTPException(400, f"仓库编码「{update_data['code']}」已存在")

        for field, value in update_data.items():
            setattr(wh, field, value)
        wh.updated_at = datetime.utcnow()
        self.db.commit()
        return wh

    def delete_warehouse(self, wh_id: int):
        wh = self.db.query(Warehouse).filter(Warehouse.id == wh_id).first()
        if not wh:
            raise HTTPException(404, "仓库不存在")

        item_count = self.db.query(InventoryItem).filter(InventoryItem.warehouse_id == wh.id).count()
        if item_count > 0:
            raise HTTPException(400, f"仓库「{wh.name}」下还有 {item_count} 条库存记录，请先处理后再删除")

        tx_src = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.source_warehouse_id == wh.id
        ).count()
        tx_tgt = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.target_warehouse_id == wh.id
        ).count()
        if tx_src > 0 or tx_tgt > 0:
            raise HTTPException(400, f"仓库「{wh.name}」关联了 {tx_src + tx_tgt} 条交易记录，请先处理后再删除")

        self.db.delete(wh)
        self.db.commit()
        return wh

    # ===== 库存管理 =====
    def list_inventory(self, query: InventoryItemQuery):
        q = self.db.query(InventoryItem)

        need_material = bool(query.keyword) or bool(query.material_type)
        if need_material:
            q = q.join(Material, InventoryItem.material_id == Material.id)

        if query.keyword:
            q = q.filter(or_(Material.code.contains(query.keyword), Material.name.contains(query.keyword)))
        if query.warehouse_id:
            q = q.filter(InventoryItem.warehouse_id == query.warehouse_id)
        if query.status:
            q = q.filter(InventoryItem.status == query.status)
        if query.low_stock_only:
            q = q.filter(InventoryItem.status.in_([InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK]))
        if query.material_type:
            q = q.filter(Material.material_type == query.material_type)

        total = q.count()
        items = q.order_by(InventoryItem.id.desc()).offset(query.offset).limit(query.limit).all()

        result = []
        for item in items:
            mat = item.material
            creator = item.creator
            wh = item.warehouse
            result.append({
                "id": item.id, "material_id": item.material_id, "warehouse_id": item.warehouse_id,
                "location": item.location, "quantity": item.quantity, "reserved_qty": item.reserved_qty,
                "safety_stock": item.safety_stock, "max_stock": item.max_stock,
                "unit": item.unit, "status": item.status,
                "shelf_life_days": item.shelf_life_days, "expiry_date": item.expiry_date,
                "remark": item.remark, "created_at": item.created_at, "updated_at": item.updated_at,
                "material_code": mat.code if mat else None,
                "material_name": mat.name if mat else None,
                "material_spec": mat.spec if mat else None,
                "material_type": mat.material_type if mat else None,
                "creator_name": creator.real_name if creator else None,
                "warehouse_name": wh.name if wh else None,
                "warehouse_code": wh.code if wh else None,
            })

        return result, total

    def create_inventory(self, data: InventoryItemCreate, current: User):
        if not self.db.query(Material).filter(Material.id == data.material_id).first():
            raise HTTPException(400, "物料不存在")

        wh = self.db.query(Warehouse).filter(Warehouse.id == data.warehouse_id, Warehouse.is_active == True).first()
        if not wh:
            raise HTTPException(400, "仓库不存在或已停用")

        existing = self.db.query(InventoryItem).filter(
            InventoryItem.material_id == data.material_id,
            InventoryItem.warehouse_id == data.warehouse_id,
        ).first()
        if existing:
            raise HTTPException(400, f"该物料在仓库「{wh.name}」已存在库存记录")

        item = InventoryItem(
            material_id=data.material_id, warehouse_id=data.warehouse_id,
            location=data.location, quantity=data.quantity,
            reserved_qty=0.0,
            safety_stock=data.safety_stock, max_stock=data.max_stock,
            unit=data.unit, shelf_life_days=data.shelf_life_days,
            expiry_date=data.expiry_date, remark=data.remark,
            created_by=current.id,
        )
        self._check_low_stock(item)
        self.db.add(item)
        self.db.flush()

        if data.quantity > 0:
            tx = InventoryTransaction(
                transaction_no=self._generate_tx_no("inbound"),
                inventory_item_id=item.id,
                transaction_type="inbound",
                quantity=data.quantity,
                before_qty=0,
                after_qty=data.quantity,
                operator_id=current.id,
                approval_status="completed",
                remark="初始库存入库",
            )
            self.db.add(tx)

        self.db.commit()
        self.db.refresh(item)
        return item

    # ===== 库存操作 =====
    def inbound(self, data: InventoryTransactionCreate, current: User):
        if data.quantity <= 0:
            raise HTTPException(400, "入库数量必须大于0")
        tx = self._do_transaction(
            data.inventory_item_id, "inbound", abs(data.quantity),
            current.id, approval_required=data.approval_required,
            related_project_id=data.related_project_id,
            remark=data.remark,
        )
        return tx

    def outbound(self, data: InventoryTransactionCreate, current: User):
        if data.quantity <= 0:
            raise HTTPException(400, "出库数量必须大于0")
        tx = self._do_transaction(
            data.inventory_item_id, "outbound", -abs(data.quantity),
            current.id, approval_required=data.approval_required,
            related_project_id=data.related_project_id,
            related_department_id=data.related_department_id,
            remark=data.remark,
        )
        return tx

    def borrow(self, data: InventoryTransactionCreate, current: User):
        if data.quantity <= 0:
            raise HTTPException(400, "领用数量必须大于0")
        tx = self._do_transaction(
            data.inventory_item_id, "borrow", -abs(data.quantity),
            current.id, approval_required=data.approval_required,
            borrower_id=data.borrower_id or current.id,
            borrower_name=data.borrower_name or current.real_name,
            expected_return_date=data.expected_return_date,
            related_project_id=data.related_project_id,
            related_department_id=data.related_department_id,
            remark=data.remark,
        )
        return tx

    def return_transfer(self, data: InventoryTransactionCreate, current: User):
        if data.quantity <= 0:
            raise HTTPException(400, "归还数量必须大于0")
        tx = self._do_transaction(
            data.inventory_item_id, "return_transfer", abs(data.quantity),
            current.id,
            borrower_id=data.borrower_id or current.id,
            borrower_name=data.borrower_name or current.real_name,
            actual_return_date=date.today(),
            remark=data.remark,
        )
        return tx

    def check_inventory(self, data: InventoryTransactionCreate, current: User):
        item = self.db.query(InventoryItem).filter(InventoryItem.id == data.inventory_item_id).first()
        if not item:
            raise HTTPException(404, "库存记录不存在")

        diff = data.quantity - item.quantity
        if diff == 0:
            return None, "盘点一致，无需调整"

        old_qty = item.quantity
        item.quantity = data.quantity
        self._check_low_stock(item)

        tx_no = self._generate_tx_no("check")
        tx = InventoryTransaction(
            transaction_no=tx_no, inventory_item_id=data.inventory_item_id,
            transaction_type="check", quantity=diff,
            before_qty=old_qty, after_qty=data.quantity,
            operator_id=current.id, approval_status="completed",
            remark=f"盘点调整: {data.remark or ''}",
        )
        self.db.add(tx)

        if item.status in (InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK):
            self._create_alert(item, item.status)

        self.db.commit()
        msg = f"盘点调整：{'盘盈' if diff > 0 else '盘亏'}{abs(diff)}{item.unit or ''}"
        return tx, msg

    def transfer(self, data: InventoryTransactionCreate, current: User):
        if not data.source_warehouse_id or not data.target_warehouse_id:
            raise HTTPException(400, "请指定来源仓库和目标仓库")
        if data.source_warehouse_id == data.target_warehouse_id:
            raise HTTPException(400, "来源仓库和目标仓库不能相同")
        if data.quantity <= 0:
            raise HTTPException(400, "调拨数量必须大于0")

        src_wh = self.db.query(Warehouse).filter(Warehouse.id == data.source_warehouse_id, Warehouse.is_active == True).first()
        if not src_wh:
            raise HTTPException(400, "来源仓库不存在或已停用")

        tgt_wh = self.db.query(Warehouse).filter(Warehouse.id == data.target_warehouse_id, Warehouse.is_active == True).first()
        if not tgt_wh:
            raise HTTPException(400, "目标仓库不存在或已停用")

        src_item = self.db.query(InventoryItem).filter(
            InventoryItem.id == data.inventory_item_id
        ).first()
        if not src_item:
            raise HTTPException(404, "来源库存记录不存在")

        qty = abs(data.quantity)

        try:
            tx_out = self._do_transaction_inner(
                data.inventory_item_id, "transfer_out", -qty,
                current.id, source_warehouse_id=data.source_warehouse_id,
                target_warehouse_id=data.target_warehouse_id,
                remark=f"调拨至 {tgt_wh.name}: {data.remark or ''}",
            )

            tgt_item = self.db.query(InventoryItem).filter(
                InventoryItem.material_id == src_item.material_id,
                InventoryItem.warehouse_id == data.target_warehouse_id,
            ).first()
            if not tgt_item:
                tgt_item = InventoryItem(
                    material_id=src_item.material_id, warehouse_id=data.target_warehouse_id,
                    unit=src_item.unit, safety_stock=src_item.safety_stock,
                    created_by=current.id,
                    version=0,
                )
                self.db.add(tgt_item)
                self.db.flush()

            tx_in = self._do_transaction_inner(
                tgt_item.id, "transfer_in", qty,
                current.id, source_warehouse_id=data.source_warehouse_id,
                target_warehouse_id=data.target_warehouse_id,
                remark=f"从 {src_wh.name} 调入: {data.remark or ''}",
            )

            self.db.commit()
            return tx_out, tx_in, src_wh.name, tgt_wh.name, qty
        except Exception:
            self.db.rollback()
            raise

    # ===== 交易记录 =====
    def list_transactions(self, query: TransactionQuery):
        q = self.db.query(InventoryTransaction)
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
        result = [self._enrich_tx(tx) for tx in txs]
        return result, total

    def get_transaction(self, tx_id: int):
        tx = self.db.query(InventoryTransaction).filter(InventoryTransaction.id == tx_id).first()
        if not tx:
            raise HTTPException(404, "交易记录不存在")
        result = self._enrich_tx(tx)
        approvals = self.db.query(InventoryAlert).filter(
            InventoryAlert.id == tx_id
        ).order_by(InventoryAlert.id).all()
        result["approvals"] = [
            {"id": a.id, "approval_level": a.id, "approver_name": "",
             "status": "", "comment": a.message, "created_at": str(a.created_at),
             "approved_at": None}
            for a in approvals
        ]
        return result

    # ===== 统计分析 =====
    def inventory_overview(self):
        total_items = self.db.query(func.count(InventoryItem.id)).scalar() or 0
        total_qty = self.db.query(func.sum(InventoryItem.quantity)).scalar() or 0.0
        normal = self.db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == InventoryStatus.NORMAL).scalar() or 0
        low = self.db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == InventoryStatus.LOW_STOCK).scalar() or 0
        out = self.db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == InventoryStatus.OUT_OF_STOCK).scalar() or 0
        expired = self.db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == InventoryStatus.EXPIRED).scalar() or 0

        return {
            "total_items": total_items, "total_quantity": round(total_qty, 2),
            "normal_count": normal, "low_stock_count": low,
            "out_of_stock_count": out, "expired_count": expired,
        }

    def stats_by_warehouse(self):
        rows = self.db.query(
            InventoryItem.warehouse_id,
            Warehouse.name.label("warehouse_name"),
            Warehouse.code.label("warehouse_code"),
            func.count(InventoryItem.id).label("item_count"),
            func.sum(InventoryItem.quantity).label("total_qty"),
        ).join(Warehouse, InventoryItem.warehouse_id == Warehouse.id, isouter=True)\
        .group_by(InventoryItem.warehouse_id, Warehouse.name, Warehouse.code).all()

        result = []
        for r in rows:
            low_count = self.db.query(InventoryItem).filter(
                InventoryItem.warehouse_id == r[0],
                InventoryItem.status.in_([InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK])
            ).count()
            result.append({
                "warehouse_id": r[0], "warehouse_name": r[1], "warehouse_code": r[2],
                "item_count": r[3],
                "total_quantity": round(float(r[4] or 0), 2),
                "low_stock_count": low_count,
            })
        return result

    def turnover_report(self, days: int = 30):
        cutoff = datetime.utcnow() - timedelta(days=days)
        items = self.db.query(InventoryItem).all()
        result = []

        for item in items:
            txs = self.db.query(InventoryTransaction).filter(
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
            wh = item.warehouse
            result.append({
                "material_code": mat.code if mat else "",
                "material_name": mat.name if mat else "",
                "warehouse_id": item.warehouse_id,
                "warehouse_name": wh.name if wh else "",
                "period_in": round(period_in, 2), "period_out": round(period_out, 2),
                "begin_qty": round(begin_qty, 2), "end_qty": round(end_qty, 2),
                "avg_qty": round(avg_qty, 2),
                "turnover_rate": round(turnover, 2),
            })

        result.sort(key=lambda x: x["turnover_rate"], reverse=True)
        return {"days": days, "items": result}

    # ===== 单条 CRUD =====
    def get_inventory(self, item_id: int):
        item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(404, "库存记录不存在")
        mat = item.material
        wh = item.warehouse
        return {
            "id": item.id, "material_id": item.material_id, "warehouse_id": item.warehouse_id,
            "warehouse_name": wh.name if wh else None, "warehouse_code": wh.code if wh else None,
            "location": item.location, "quantity": item.quantity, "reserved_qty": item.reserved_qty,
            "safety_stock": item.safety_stock, "max_stock": item.max_stock,
            "unit": item.unit, "status": item.status,
            "shelf_life_days": item.shelf_life_days, "expiry_date": item.expiry_date,
            "remark": item.remark, "created_at": str(item.created_at), "updated_at": str(item.updated_at),
            "material_code": mat.code if mat else None,
            "material_name": mat.name if mat else None,
            "material_spec": mat.spec if mat else None,
            "material_type": mat.material_type if mat else None,
        }

    def update_inventory(self, item_id: int, data: InventoryItemUpdate):
        item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(404, "库存记录不存在")

        update_data = data.model_dump(exclude_unset=True)

        if "quantity" in update_data and update_data["quantity"] != item.quantity:
            raise HTTPException(400, "禁止直接修改库存数量，请使用入库/出库/盘点接口")

        for field, value in update_data.items():
            setattr(item, field, value)
        self._check_low_stock(item)
        item.updated_at = datetime.now()
        self.db.commit()
        return item

    def delete_inventory(self, item_id: int):
        item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(404, "库存记录不存在")
        if item.quantity > 0:
            raise HTTPException(400, f"该物料当前库存为{item.quantity}，请先清空库存后再删除")

        tx_count = self.db.query(InventoryTransaction).filter(
            InventoryTransaction.inventory_item_id == item_id
        ).count()
        if tx_count > 0:
            raise HTTPException(400, f"该库存记录关联了 {tx_count} 条交易记录，建议归档而非删除")

        self.db.delete(item)
        self.db.commit()
        return item