"""FastAPI 主入口"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import logging
import os
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.core.config import settings
from app.api.v1 import auth, users, projects, experiments, bom, samples, documents, departments, roles, operation_logs, inventory


def setup_logging():
    """配置日志输出：同时输出到控制台和文件"""
    log_level = logging.INFO if not settings.DEBUG else logging.DEBUG

    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：开发环境自动建表，生产环境建议使用 Alembic 迁移"""
    auto_create = os.getenv("DB_AUTO_CREATE", "true").lower() == "true"
    if auto_create:
        logger.info("Creating database tables if not exists (auto-create mode)...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ready")
    else:
        logger.info("DB auto-create disabled, expecting Alembic migration to manage schema")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="工厂研发项目管理系统 API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)


# ===== 全局异常处理器 =====

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数验证错误"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "参数验证失败",
            "detail": errors if len(errors) > 1 else str(errors[0]) if errors else "无效的参数"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail if isinstance(exc.detail, str) else "请求处理失败",
            "detail": exc.detail if not isinstance(exc.detail, str) else None
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_exception_handler(request: Request, exc: ValidationError):
    """Pydantic模型验证错误"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "数据验证失败",
            "detail": errors
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库操作错误"""
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败，请稍后重试",
            "detail": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理（兜底）"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误，请稍后重试",
            "detail": None
        }
    )


# ===== 中间件 =====

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    import time
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"{request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.2f}ms"
        )
        raise


# ===== CORS =====
# 安全策略：禁止使用 ["*"] 通配，必须指定具体来源
cors_origins = settings.CORS_ORIGINS
if "*" in cors_origins:
    # 兜底：若配置了通配，降级为仅本地开发来源
    logger.warning("CORS_ORIGINS 包含 '*'，已降级为仅允许本地开发来源")
    cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# ===== 操作日志中间件 =====
from app.core.operation_log import OperationLogMiddleware
app.add_middleware(OperationLogMiddleware)

# 注册路由
v1_prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=f"{v1_prefix}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{v1_prefix}/users", tags=["用户管理"])
app.include_router(departments.router, prefix=f"{v1_prefix}/departments", tags=["部门管理"])
app.include_router(roles.router, prefix=f"{v1_prefix}/roles", tags=["角色管理"])
app.include_router(operation_logs.router, prefix=f"{v1_prefix}/operation-logs", tags=["操作日志"])
app.include_router(projects.router, prefix=f"{v1_prefix}/projects", tags=["项目管理"])
app.include_router(experiments.router, prefix=f"{v1_prefix}/experiments", tags=["实验管理"])
app.include_router(bom.router, prefix=f"{v1_prefix}/bom", tags=["BOM管理"])
app.include_router(samples.router, prefix=f"{v1_prefix}/samples", tags=["样品试产"])
app.include_router(documents.router, prefix=f"{v1_prefix}/documents", tags=["文档知识"])
app.include_router(inventory.router, prefix=f"{v1_prefix}/inventory", tags=["库存管理"])


@app.get("/health")
def health():
    return {"status": "ok"}


# ===== 前端静态文件托管 =====
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index_path)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index_path)
