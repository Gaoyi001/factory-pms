"""操作日志中间件"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import get_db
from app.models.operation_log import OperationLog


class OperationLogMiddleware(BaseHTTPMiddleware):
    """操作日志中间件 - 记录所有API请求"""

    # 需要记录的操作映射
    ACTION_MAP = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
        "GET": "read",
    }

    # 资源名称映射（按前缀最长匹配）
    RESOURCE_MAP = {
        "/api/v1/projects": "project",
        "/api/v1/experiments": "experiment",
        "/api/v1/bom": "bom",
        "/api/v1/samples": "sample",
        "/api/v1/documents": "document",
        "/api/v1/users": "user",
        "/api/v1/departments": "department",
        "/api/v1/roles": "role",
        "/api/v1/auth": "auth",
        "/api/v1/operation-logs": "operation_log",
    }

    async def dispatch(self, request: Request, call_next):
        # 跳过非API路径和登录/当前用户等敏感路径
        path = request.url.path
        if not path.startswith("/api/v1/") or path in [
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/auth/me/permissions",
        ]:
            return await call_next(request)

        # 权限分配接口已在路由内手动记录审计日志（含 before/after），跳过中间件记录避免重复
        if path.startswith("/api/v1/roles/") and path.endswith("/permissions") and request.method == "POST":
            return await call_next(request)

        response = await call_next(request)

        # 只记录成功的请求
        if 200 <= response.status_code < 300:
            try:
                await self.log_operation(request, response)
            except Exception:
                pass  # 日志记录失败不影响主流程

        return response

    async def log_operation(self, request: Request, response):
        """记录操作"""
        # 获取用户信息（必须存在，否则跳过记录）
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            return  # 未认证成功的请求不记录

        username = getattr(request.state, "username", "unknown")

        # 从请求路径提取资源
        resource = "unknown"
        request_path = request.url.path
        for prefix, name in self.RESOURCE_MAP.items():
            if request_path.startswith(prefix):
                resource = name
                break

        # 提取资源ID（从路径中解析数字ID）
        resource_id = None
        parts = request.url.path.strip("/").split("/")
        for part in parts:
            if part.isdigit():
                resource_id = int(part)
                break

        # 创建并提交日志（注意：不读取 request.body()，避免消耗请求体导致路由处理失败）
        db_gen = get_db()
        db = next(db_gen)
        try:
            log = OperationLog(
                user_id=user_id,
                username=username,
                action=self.ACTION_MAP.get(request.method, "unknown"),
                resource=resource,
                resource_id=resource_id,
                method=request.method,
                path=str(request.url.path),
                ip_address=self.get_client_ip(request),
                user_agent=(request.headers.get("user-agent", "") or "")[:500],
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            try:
                next(db_gen, None)
            except StopIteration:
                pass

    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 优先从 X-Forwarded-For 获取
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 其次从 X-Real-IP 获取
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 最后从直接连接获取
        if request.client:
            return request.client.host
        return "unknown"


def log_file_download(db, user_id: int, username: str, file_name: str, file_size: int, resource: str, resource_id: int, ip_address: str):
    """记录文件下载"""
    log = OperationLog(
        user_id=user_id,
        username=username,
        action="download",
        resource=resource,
        resource_id=resource_id,
        resource_name=file_name,
        is_file_download=True,
        file_name=file_name,
        file_size=file_size,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
