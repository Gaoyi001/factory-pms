"""研发实验管理 Service 层

将业务逻辑从路由层分离，提升可测试性和可复用性。
"""

import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from typing import Optional, List

from app.models.experiment import Experiment, ExperimentRecord, ExperimentAttachment
from app.models.user import User


# 实验类型简称映射
TYPE_ABBR = {
    "performance": "PERF", "reliability": "RELI", "environment": "ENV",
    "material": "MATL", "process": "PROC", "other": "OTHR",
}

# 状态流转规则
STATUS_TRANSITIONS = {
    "start": {"from": ("draft",), "to": "in_progress", "set_actual_start": True},
    "complete": {"from": ("in_progress",), "to": "completed", "set_actual_end": True},
    "cancel": {"from": ("draft", "in_progress"), "to": "cancelled", "set_actual_end": True},
}


class ExperimentService:
    """实验管理服务"""

    def __init__(self, db: Session):
        self.db = db

    # ===== 实验编码生成 =====
    def generate_code(self, exp_type: str) -> str:
        """生成实验编码: EXP-{TYPE}-{YYYYMM}-{SEQ:04d}"""
        now = datetime.datetime.now()
        prefix = f"EXP-{TYPE_ABBR.get(exp_type, 'OTHR')}-{now.strftime('%Y%m')}-"
        count = self.db.query(Experiment).filter(
            Experiment.code.like(f"{prefix}%")
        ).count()
        return f"{prefix}{count + 1:04d}"

    # ===== 访问控制 =====
    @staticmethod
    def check_access(exp: Experiment, user: User) -> None:
        """数据隔离：非 admin/manager 只能看自己设计或执行的实验"""
        if user.role not in ("admin", "manager") \
                and exp.designer_id != user.id \
                and exp.executor_id != user.id:
            raise HTTPException(403, "无权访问此实验")

    @staticmethod
    def check_editable(exp: Experiment) -> None:
        """校验实验是否可新增/修改记录"""
        if exp.status in ("cancelled", "completed"):
            label = "取消" if exp.status == "cancelled" else "完成"
            raise HTTPException(400, f"实验已{label}，不可操作记录")

    # ===== 实验 CRUD =====
    def get_or_404(self, experiment_id: int, user: User) -> Experiment:
        """获取实验并校验访问权"""
        exp = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise HTTPException(404, "实验不存在")
        self.check_access(exp, user)
        return exp

    def list_experiments(
        self, user: User,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        exp_type: Optional[str] = None,
        keyword: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        offset: int = 0, limit: int = 20,
    ):
        """查询实验列表"""
        q = self.db.query(Experiment)
        if user.role not in ("admin", "manager"):
            q = q.filter(
                (Experiment.designer_id == user.id) | (Experiment.executor_id == user.id)
            )
        if project_id:
            q = q.filter(Experiment.project_id == project_id)
        if status:
            q = q.filter(Experiment.status == status)
        if exp_type:
            q = q.filter(Experiment.exp_type == exp_type)
        if keyword:
            q = q.filter(
                Experiment.name.contains(keyword) | Experiment.code.contains(keyword)
            )
        if date_from:
            q = q.filter(Experiment.plan_start >= date_from)
        if date_to:
            q = q.filter(Experiment.plan_end <= date_to)
        total = q.count()
        items = q.order_by(Experiment.id.desc()).offset(offset).limit(limit).all()
        return items, total

    def change_status(self, exp: Experiment, action: str) -> Experiment:
        """状态流转"""
        rule = STATUS_TRANSITIONS.get(action)
        if not rule:
            raise HTTPException(400, f"不支持的动作: {action}")
        if exp.status not in rule["from"]:
            raise HTTPException(400, f"当前状态「{exp.status}」不允许执行 {action} 操作")
        exp.status = rule["to"]
        today = datetime.date.today()
        if rule.get("set_actual_start") and not exp.actual_start:
            exp.actual_start = today
        if rule.get("set_actual_end") and not exp.actual_end:
            exp.actual_end = today
        exp.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        self.db.refresh(exp)
        return exp

    # ===== 实验记录 =====
    def get_record_or_404(self, record_id: int, user: User) -> ExperimentRecord:
        """获取记录并校验访问权（经 experiment 关联）"""
        rec = self.db.query(ExperimentRecord).filter(ExperimentRecord.id == record_id).first()
        if not rec:
            raise HTTPException(404, "实验记录不存在")
        self.check_access(rec.experiment, user)
        return rec

    def extract_test_type(self, param_values) -> str:
        """从 param_values JSON 中提取 test_type"""
        pv = param_values or {}
        if isinstance(pv, dict):
            return pv.get("test_type", "normal")
        return "normal"

    def refresh_actual_dates(self, experiment_id: int) -> None:
        """根据实验记录自动维护 actual_start / actual_end"""
        result = self.db.query(
            func.min(ExperimentRecord.executed_at),
            func.max(ExperimentRecord.executed_at),
        ).filter(
            ExperimentRecord.experiment_id == experiment_id,
            ExperimentRecord.executed_at.isnot(None),
        ).first()
        if not result or not result[0]:
            return
        exp = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            return
        exp.actual_start = result[0]
        exp.actual_end = result[1]
        self.db.commit()
