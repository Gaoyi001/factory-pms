"""操作日志 API"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user, require_role, require_permission
from app.models.user import User
from app.models.operation_log import OperationLog
from app.schemas.role import OperationLogOut, OperationLogQuery, OperationLogBatchDelete, OperationLogCleanup
from app.schemas.common import ResponseBase, PaginationResponse

router = APIRouter()


# ===== 查询 =====
@router.get("/list", response_model=ResponseBase)
def list_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[int] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
):
    """查询操作日志"""
    q = db.query(OperationLog)

    if user_id:
        q = q.filter(OperationLog.user_id == user_id)
    if action:
        q = q.filter(OperationLog.action == action)
    if resource:
        q = q.filter(OperationLog.resource == resource)
    if resource_id:
        q = q.filter(OperationLog.resource_id == resource_id)
    if keyword:
        q = q.filter(
            OperationLog.username.contains(keyword) |
            OperationLog.resource_name.contains(keyword) |
            OperationLog.detail.contains(keyword)
        )
    if start_date:
        q = q.filter(OperationLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        end = datetime.fromisoformat(end_date) + timedelta(days=1)
        q = q.filter(OperationLog.created_at < end)

    total = q.count()
    logs = q.order_by(OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ResponseBase(data=PaginationResponse(
        items=[OperationLogOut.model_validate(log).model_dump() for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    ).model_dump())


@router.get("/download-logs", response_model=ResponseBase)
def list_download_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
):
    """查询文件下载记录"""
    q = db.query(OperationLog).filter(OperationLog.is_file_download == True)
    total = q.count()
    logs = q.order_by(OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ResponseBase(data=PaginationResponse(
        items=[OperationLogOut.model_validate(log).model_dump() for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    ).model_dump())


# ===== 删除 =====
@router.delete("/{log_id}", response_model=ResponseBase)
def delete_operation_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log", "delete")),
):
    """删除单条操作日志"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(404, "日志不存在")
    db.delete(log)
    db.commit()
    return ResponseBase(data={"msg": "日志已删除"})


@router.post("/batch-delete", response_model=ResponseBase)
def batch_delete_operation_logs(
    data: OperationLogBatchDelete,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log", "delete")),
):
    """批量删除操作日志（按ID列表）"""
    deleted = db.query(OperationLog).filter(
        OperationLog.id.in_(data.ids)
    ).delete(synchronize_session=False)
    db.commit()
    return ResponseBase(data={
        "msg": f"已删除 {deleted} 条日志",
        "deleted_count": deleted,
    })


@router.post("/cleanup", response_model=ResponseBase)
def cleanup_operation_logs(
    data: OperationLogCleanup,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log", "delete")),
):
    """自动清理过期日志（按保留天数）

    删除 created_at 早于 (当前时间 - retention_days) 的所有日志。
    默认保留90天，可配置范围 7-365 天。
    """
    cutoff_date = datetime.utcnow() - timedelta(days=data.retention_days)
    deleted = db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_date
    ).delete(synchronize_session=False)
    db.commit()
    return ResponseBase(data={
        "msg": f"已清理 {deleted} 条过期日志（保留 {data.retention_days} 天）",
        "deleted_count": deleted,
        "cutoff_date": cutoff_date.isoformat(),
        "retention_days": data.retention_days,
    })


@router.get("/stats", response_model=ResponseBase)
def get_log_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
):
    """获取日志统计信息"""
    total = db.query(OperationLog).count()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # 按天统计最近7天
    daily_stats = {}
    for i in range(7):
        day_start = today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = db.query(OperationLog).filter(
            OperationLog.created_at >= day_start,
            OperationLog.created_at < day_end,
        ).count()
        daily_stats[day_start.strftime("%Y-%m-%d")] = count

    # 按操作类型统计
    action_stats = {}
    actions = db.query(OperationLog.action, sa_func.count()).group_by(OperationLog.action).all()
    for action, count in actions:
        action_stats[action] = count

    # 按资源类型统计
    resource_stats = {}
    resources = db.query(OperationLog.resource, sa_func.count()).group_by(OperationLog.resource).all()
    for resource, count in resources:
        resource_stats[resource] = count

    # 最老日志日期
    oldest = db.query(OperationLog).order_by(OperationLog.id.asc()).first()
    newest = db.query(OperationLog).order_by(OperationLog.id.desc()).first()

    return ResponseBase(data={
        "total_count": total,
        "daily_stats": daily_stats,
        "action_stats": action_stats,
        "resource_stats": resource_stats,
        "oldest_date": oldest.created_at.isoformat() if oldest else None,
        "newest_date": newest.created_at.isoformat() if newest else None,
    })
